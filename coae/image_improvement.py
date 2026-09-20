"""One explicit local revision from a saved visual audit, with resumable tickets."""
from dataclasses import asdict
import json
from pathlib import Path
import uuid

from .audio import file_sha256
from .local_ai import backend, ComfyUI
from .visual_style import REALISM_INSTRUCTION


def improve_image(app, pid, iid):
    from .application import atomic, dump
    if backend('text') != 'ollama' or backend('image') != 'comfyui':
        raise ValueError('Refazer com melhoria exige Ollama e ComfyUI locais configurados.')
    story, scenes = app.story(pid, approved=True)
    source = app.db.one('SELECT * FROM images WHERE id=? AND project_id=?', (iid, pid))
    if not source or source['storyboard_id'] != story['id']:
        raise ValueError('Selecione uma imagem do storyboard atual aprovado.')
    source_path = app.file(pid, source['path'])
    if file_sha256(source_path) != source['sha256']:
        raise ValueError('Imagem original alterada; audite uma imagem íntegra antes de refazer.')
    scene = next(s for s in scenes if s.scene_id == source['scene_id'])
    audit = app.db.one("SELECT * FROM audit_runs WHERE project_id=? AND kind='image' AND reference=? ORDER BY id DESC LIMIT 1", (pid, str(iid)))
    if not audit:
        raise ValueError('Audite esta imagem com IA antes de pedir melhorias.')
    report = json.loads(audit['report'])
    issues = app.remote_issues(report)
    required = {'SPEECH_MATCH', 'MISSING_CONTRADICTORY', 'SCIENCE', 'VISUAL_QUALITY', 'SUGGESTIONS'}
    if not required.issubset({i['code'] for i in issues}):
        raise ValueError('Audite esta imagem com IA para obter um parecer visual completo antes de refazer.')
    operation = f'image_{iid}_audit_{audit["id"]}'
    # A second click on the same source/audit resumes or returns its child.
    for row in app.db.rows("SELECT payload FROM events WHERE project_id=? AND action='IMAGE_IMPROVED' ORDER BY id DESC", (pid,)):
        event = json.loads(row['payload'])
        if event.get('operation') == operation:
            child = app.db.one('SELECT * FROM images WHERE id=? AND project_id=?', (event['image_id'], pid))
            if not child or not Path(child['path']).is_file() or file_sha256(Path(child['path'])) != child['sha256']:
                raise ValueError('A versão melhorada já foi registrada, mas seu arquivo está ausente ou alterado. Confira o histórico.')
            return {'message': 'A melhoria desta auditoria já foi gerada; versão existente preservada.', 'image_id': child['id']}
    folder = app.folder(pid) / 'logs' / 'image_improvements'
    plan_path = folder / (operation + '.plan.json')
    ticket_path = folder / (operation + '.ticket.json')
    context = {'source_image_id': iid, 'source_sha256': source['sha256'],
               'audit_id': audit['id'], 'storyboard_id': story['id'], 'scene': asdict(scene), 'audit': report}
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        if plan.get('context') != context:
            raise ValueError('Contexto mudou durante a melhoria; plano e ticket preservados para conferência.')
    else:
        task = (REALISM_INSTRUCTION+'Transforme o parecer de auditoria visual em um novo prompt de imagem SDXL. '
                'Retorne somente JSON {"prompt":"prompt detalhado em inglês", "improvements":"explicação concreta em português"}. '
                'Use a fala, ideia principal e descrição visual da cena como limites. Corrija os problemas observados '
                'e explique quais sugestões aplicou ou adaptou. A auditoria é falível: não invente ciência ou fatos '
                'para satisfazer críticas. Brilho aparente sozinho não comprova idade ou estágio evolutivo. '
                'Não acrescente localização, escala temporal ou detalhes não sustentados pela cena. '
                'Adapte sugestões de legendas/diagramas para soluções visuais sem texto: nunca peça letras, '
                'números, rótulos, marcas ou logos. Mantenha composição documental cinematográfica 16:9. '
                'Não altere fala, tempos ou storyboard. Isto é uma nova geração, não edição pixel a pixel. '
                'O prompt deve incorporar correções específicas, não apenas repetir o plano anterior; '
                'improvements não deve afirmar que a correção já foi comprovada.')
        value = app.remote(pid, 'writer', task, context)
        if (not isinstance(value, dict) or any(not isinstance(value.get(k), str) or not value[k].strip()
                for k in ('prompt', 'improvements')) or len(value['prompt']) > 12000 or len(value['improvements']) > 6000):
            raise ValueError('Ollama devolveu plano de melhoria inválido; imagem anterior preservada.')
        plan = {'context': context, 'prompt': value['prompt'].strip(), 'improvements': value['improvements'].strip()}
        atomic(plan_path, dump(plan))
    ticket = json.loads(ticket_path.read_text(encoding='utf-8')) if ticket_path.exists() else None
    client = ComfyUI()
    raw, usage = client.generate(plan['prompt'], ticket, lambda value: atomic(ticket_path, dump(value)))
    temporary = app.folder(pid) / 'images' / ('improvement_' + uuid.uuid4().hex + '.png')
    try:
        atomic(temporary, raw)
        sha = file_sha256(temporary)
        old_hashes = {r['sha256'] for r in app.db.rows('SELECT sha256 FROM images WHERE project_id=? AND storyboard_id=? AND scene_id=?', (pid, story['id'], scene.scene_id))}
        if sha in old_hashes:
            raise ValueError('A geração devolveu uma imagem idêntica a uma versão existente; nenhuma aprovação ou versão foi alterada.')
        with app.db.transaction():
            result = app.import_image(pid, scene.scene_id, temporary)
            app.db.event(pid, 'IMAGE_IMPROVED', dict(usage, operation=operation, source_image_id=iid,
                         audit_id=audit['id'], image_id=result['image_id'], improvements=plan['improvements'],
                         plan=plan_path.relative_to(app.folder(pid)).as_posix()))
    finally:
        temporary.unlink(missing_ok=True)
    return {'message': 'Nova imagem gerada a partir do parecer. Original preservada. Audite a nova versão e revise antes de aprovar.',
            **result, 'improvements': plan['improvements']}
