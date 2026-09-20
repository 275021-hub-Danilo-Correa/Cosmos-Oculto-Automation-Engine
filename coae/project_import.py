"""Import project backups without replacing the workspace database."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import stat
import tempfile
import uuid
import zipfile

from .audio import file_sha256
from .script_service import save_script

TABLES = ('scripts', 'audio_files', 'transcriptions', 'storyboards', 'scenes',
          'images', 'exports', 'audit_runs', 'events', 'jobs', 'api_calls')
LINKS = {'audio_files': {'script_id': 'scripts'},
         'transcriptions': {'audio_id': 'audio_files'},
         'storyboards': {'audio_id': 'audio_files', 'transcription_id': 'transcriptions'},
         'images': {'storyboard_id': 'storyboards'}}


def local_candidates(app):
    root = app.root / 'projects'
    registered = {p['id'] for p in app.db.rows('SELECT id FROM projects')}
    return sorted(p.name for p in root.iterdir()
                  if p.is_dir() and not p.is_symlink() and p.resolve().is_relative_to(app.root)
                  and p.name not in registered
                  and re.fullmatch(r'COAE-[A-Za-z0-9_-]+', p.name)) if root.exists() else []


def recover_local(app, name):
    if name not in local_candidates(app):
        raise ValueError('Pasta local indisponível para recuperação.')
    root = app.root / 'projects' / name
    scripts = sorted(root.glob('exports/script_v*/narration_darkplanner.txt'))
    if not scripts:
        raise ValueError('Pasta sem roteiro exportado. Importe o ZIP completo do computador de origem.')
    for path in scripts:
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Roteiro fora da pasta do projeto.')
    with app.db.transaction():
        app.db.create_project(name, 'Projeto recuperado ' + name)
        app.db.execute('UPDATE projects SET root_path=? WHERE id=?', (str(root), name))
        for path in scripts:
            save_script(app.db, name, 'Projeto recuperado ' + name, path.read_text(encoding='utf-8'))
        app.db.event(name, 'PROJECT_RECOVERED', {'source': name, 'lineage': 'unavailable'})
    return {'project': name, 'message': 'Roteiro recuperado como rascunho. Materiais preservados em Montagem e arquivos. Reimporte o áudio e revise; histórico e aprovações exigem o ZIP com banco original.'}


def import_bundle(app, archive, allow_partial=False):
    staging = app.root / 'workspace' / 'imports'
    staging.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=staging) as temp:
        unpacked = Path(temp)
        try:
            with zipfile.ZipFile(archive) as z:
                entries = z.infolist()
                if len(entries) > 20000 or sum(i.file_size for i in entries) > 2 * 1024**3:
                    raise ValueError('Pacote excede 20 mil arquivos ou 2 GB descompactados.')
                seen = set()
                for entry in entries:
                    name = entry.filename.replace('\\', '/')
                    parts = PurePosixPath(name).parts
                    if (not parts or name.startswith('/') or any(
                        p in ('.', '..') or ':' in p or p.endswith((' ', '.')) or
                        re.fullmatch(r'(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', p)
                        for p in parts) or stat.S_ISLNK(entry.external_attr >> 16)):
                        raise ValueError('Caminho inseguro no ZIP.')
                    key = '/'.join(parts).casefold()
                    if key in seen:
                        raise ValueError('Arquivo duplicado no ZIP.')
                    seen.add(key)
                    target = unpacked.joinpath(*parts)
                    if entry.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with z.open(entry) as source, target.open('wb') as output:
                            shutil.copyfileobj(source, output)
        except zipfile.BadZipFile as exc:
            raise ValueError('ZIP inválido.') from exc
        roots = list(unpacked.iterdir())
        if len(roots) != 1 or not roots[0].is_dir():
            raise ValueError('Selecione um ZIP de um único projeto, gerado por Baixar projeto completo.')
        source = roots[0]
        snapshot = source / 'data' / 'coae.sqlite3'
        if not snapshot.exists() and not (source / 'project_state.json').exists():
            if not list(source.glob('exports/script_v*/narration_darkplanner.txt')):
                raise ValueError('ZIP sem banco e sem roteiro exportado para recuperar.')
            if not allow_partial:
                return {'requires_confirmation': True, 'message': 'Este ZIP contém apenas arquivos, sem o banco original. Recuperar o roteiro como rascunho e guardar os demais materiais? Aprovações e vínculos de áudio/cenas não serão reconstruídos.'}
            pid = 'COAE-' + uuid.uuid4().hex[:8].upper()
            destination = app.root / 'projects' / pid
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.mkdir()
            try:
                with app.db.transaction():
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                    return recover_local(app, pid)
            finally:
                if app.db.one('SELECT id FROM projects WHERE id=?', (pid,)) is None:
                    if destination.resolve().parent == (app.root / 'projects').resolve():
                        shutil.rmtree(destination)
        if not snapshot.is_file() or not (source / 'project_state.json').is_file():
            raise ValueError('ZIP sem banco/histórico. Use Baixar projeto completo no COAE de origem.')
        return _merge(app, source, snapshot)


def trash_project(app, pid):
    with app.db.transaction():
        project = app.db.get_project(pid)
        if app.db.one("SELECT id FROM jobs WHERE project_id=? AND status='RUNNING'", (pid,)):
            raise ValueError('Aguarde a tarefa em execução antes de excluir.')
        if project['status'] != 'TRASHED':
            app.db.event(pid, 'PROJECT_TRASHED', {'previous_status': project['status']})
            app.db.execute("UPDATE projects SET status='TRASHED',updated_at=CURRENT_TIMESTAMP WHERE id=?", (pid,))
    return {'message': 'Projeto movido para a lixeira. Arquivos e histórico preservados.'}


def restore_project(app, pid):
    with app.db.transaction():
        if app.db.get_project(pid)['status'] != 'TRASHED':
            raise ValueError('O projeto não está na lixeira.')
        event = app.db.one("SELECT payload FROM events WHERE project_id=? AND action='PROJECT_TRASHED' ORDER BY id DESC LIMIT 1", (pid,))
        status = json.loads(event['payload']).get('previous_status', 'PENDING') if event else 'PENDING'
        app.db.execute('UPDATE projects SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?', (status, pid))
        app.db.event(pid, 'PROJECT_RESTORED', {})
    return {'project': pid, 'message': 'Projeto restaurado com seus arquivos e histórico.'}


def _merge(app, source, snapshot):
    connection = sqlite3.connect(snapshot.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute('PRAGMA trusted_schema=OFF')
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not set(TABLES + ('projects',)).issubset(tables):
            raise ValueError('Versão do backup incompatível: faltam tabelas do projeto.')
        project = connection.execute('SELECT * FROM projects WHERE id=?', (source.name,)).fetchone()
        if project is None:
            raise ValueError('Projeto não encontrado no banco do ZIP.')
        project = dict(project)
        rows = {t: [dict(r) for r in connection.execute(f'SELECT * FROM {t} WHERE project_id=? ORDER BY id', (source.name,))] for t in TABLES}
    except sqlite3.DatabaseError as exc:
        raise ValueError('Banco de backup inválido ou incompatível.') from exc
    finally:
        connection.close()
    # Always import as a separate copy, even if the source ID already exists.
    pid = 'COAE-' + uuid.uuid4().hex[:8].upper()
    destination = app.root / 'projects' / pid
    old_root = (project.get('root_path') or '').replace('\\', '/').rstrip('/')

    def relative(value):
        value = value.replace('\\', '/')
        if old_root and value.startswith(old_root + '/'):
            value = value[len(old_root) + 1:]
        elif f'projects/{source.name}/' in value:
            value = value.split(f'projects/{source.name}/', 1)[1]
        parts = PurePosixPath(value).parts
        if not parts or value.startswith('/') or any(p in ('..', '.') or ':' in p for p in parts):
            raise ValueError('Arquivo do banco fora do projeto de origem.')
        if not source.joinpath(*parts).is_file():
            raise ValueError('Backup incompleto: falta um arquivo referenciado pelo banco.')
        return Path(*parts)

    for table, columns in (('audio_files', ('original_path', 'working_path')), ('images', ('path',)), ('exports', ('path',))):
        for row in rows[table]:
            for column in columns:
                rel = relative(row[column])
                expected = row.get('sha256') if table in ('audio_files', 'images') else row.get('content_hash')
                actual = (hashlib.sha256((source / rel).read_text(encoding='utf-8').encode()).hexdigest()
                          if table == 'exports' and row['kind'] in ('script_master', 'narration_darkplanner', 'narration_clean')
                          else file_sha256(source / rel))
                if expected and actual != expected:
                    raise ValueError('Hash divergente em arquivo do backup; importação cancelada.')
                row[column] = str(destination / rel)
    created = False
    try:
        with app.db.transaction():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.mkdir()  # Refuse collisions; never overwrite existing media.
            created = True
            shutil.copytree(source, destination, dirs_exist_ok=True,
                            ignore=lambda folder, names: {'data', 'project_state.json', 'BACKUP_README.txt'}
                            if Path(folder) == source else set())
            # Tickets refer to jobs on another service. Archive, never resume them.
            tickets = destination / 'logs' / 'local_images'
            if tickets.exists():
                tickets.rename(destination / 'logs' / ('imported_tickets_' + uuid.uuid4().hex[:8]))
            app.db.create_project(pid, project['title'])
            app.db.execute('UPDATE projects SET root_path=? WHERE id=?', (str(destination), pid))
            mapping = {}
            for table in TABLES:
                mapping[table] = {}
                allowed = {r[1] for r in app.db.rows(f'PRAGMA table_info({table})')}
                for row in rows[table]:
                    old_id = row['id']
                    data = {k: v for k, v in row.items() if k in allowed and k != 'id'}
                    data['project_id'] = pid
                    for column, target_table in LINKS.get(table, {}).items():
                        if data.get(column) is not None:
                            data[column] = mapping[target_table][data[column]]
                    if table == 'audit_runs':
                        target = {'script': 'scripts', 'audio': 'audio_files', 'storyboard': 'storyboards', 'image': 'images'}.get(data['kind'])
                        if target:
                            data['reference'] = str(mapping[target][int(data['reference'])])
                    if table == 'exports' and data.get('source_ref') and data['kind'] in ('script_master', 'narration_darkplanner', 'narration_clean'):
                        data['source_ref'] = str(mapping['scripts'][int(data['source_ref'])])
                    if table in ('jobs', 'api_calls') and data['status'] == 'RUNNING':
                        data['status'] = 'INTERRUPTED' if table == 'jobs' else 'UNKNOWN_REMOTE_RESULT'
                    columns = ','.join(data)
                    cursor = app.db.execute(f'INSERT INTO {table}({columns}) VALUES({",".join("?" for _ in data)})', tuple(data.values()))
                    mapping[table][old_id] = cursor.lastrowid
            app.db.event(pid, 'PROJECT_IMPORTED', {'source_project': source.name, 'id_mapping': mapping,
                         'note': 'Arquivos e eventos históricos preservam referências da origem. Tickets arquivados.'})
        return {'project': pid, 'message': 'Projeto importado como cópia independente. Confira áudio, cenas e imagens antes de continuar.'}
    except (KeyError, TypeError) as exc:
        raise ValueError('Backup com vínculos inconsistentes.') from exc
    finally:
        if created and app.db.one('SELECT id FROM projects WHERE id=?', (pid,)) is None:
            if destination.resolve().parent == (app.root / 'projects').resolve():
                shutil.rmtree(destination)
