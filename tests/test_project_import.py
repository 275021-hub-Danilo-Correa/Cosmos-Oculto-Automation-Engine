from contextlib import ExitStack
import io
import json
from pathlib import Path
import tempfile
import unittest
import wave
import urllib.request
import zipfile

from coae.application import Application
from coae.audio import import_audio
from coae.project_import import import_bundle, local_candidates, recover_local, trash_project, restore_project
from coae.script_service import save_script, approve_script, export_script
from coae.runtime import running_server


class ProjectImportTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.source = Application(self.root / 'source')
        self.target = Application(self.root / 'target')
        self.stack.callback(self.source.db.close)
        self.stack.callback(self.target.db.close)
        self.pid = self.source.create('Projeto de origem')['project']
        save_script(self.source.db, self.pid, 'Roteiro', 'Texto narrado.')
        approve_script(self.source.db, self.pid, 1)
        export_script(self.source.db, self.pid, None, None, self.source.folder(self.pid) / 'exports')

    def test_roundtrip_remaps_ids_paths_and_keeps_existing_project(self):
        existing = self.target.create('Já existente')['project']
        save_script(self.target.db, existing, 'Existente', 'Preservar.')
        wav = self.root / 'sample.wav'
        with wave.open(str(wav), 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(b'\0\0' * 8000)
        aid = import_audio(self.source.db, self.pid, wav, self.source.folder(self.pid))
        tid = self.source.db.execute('INSERT INTO transcriptions(project_id,audio_id,provider,source_hash,payload) VALUES(?,?,?,?,?)',
                                    (self.pid, aid, 'fixture', 'hash', '[]')).lastrowid
        self.source.db.execute('INSERT INTO storyboards(project_id,version,audio_id,transcription_id) VALUES(?,?,?,?)',
                               (self.pid, 1, aid, tid))
        self.source.audit_script(self.pid)
        result = import_bundle(self.target, io.BytesIO(self.source.bundle(self.pid)))
        pid = result['project']
        self.assertNotEqual(pid, self.pid)
        script = self.target.script(pid)
        self.assertTrue(script['approved'])
        audio = self.target.audio(pid)
        self.assertEqual(audio['script_id'], script['id'])
        story = self.target.db.one('SELECT * FROM storyboards WHERE project_id=?', (pid,))
        transcription = self.target.db.one('SELECT * FROM transcriptions WHERE project_id=?', (pid,))
        self.assertEqual(story['audio_id'], audio['id'])
        self.assertEqual(story['transcription_id'], transcription['id'])
        self.assertEqual(transcription['audio_id'], audio['id'])
        self.assertTrue(Path(audio['original_path']).is_relative_to(self.target.folder(pid)))
        self.assertEqual(self.target.db.one('SELECT reference FROM audit_runs WHERE project_id=?', (pid,))['reference'], str(script['id']))
        self.assertEqual(self.target.script(existing)['body'], 'Preservar.')
        again = import_bundle(self.target, io.BytesIO(self.target.bundle(pid)))['project']
        self.assertEqual(self.target.script(again)['body'], 'Texto narrado.')
        self.assertEqual(self.target.db.rows('PRAGMA foreign_key_check'), [])

    def test_zip_paths_rejected_without_writes(self):
        for name in ('../escape.txt', 'x/../../escape.txt', 'C:/escape', 'x/CON.txt'):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as z:
                z.writestr(name, 'bad')
            stream.seek(0)
            with self.subTest(name=name), self.assertRaises(ValueError):
                import_bundle(self.target, stream)
        self.assertEqual(self.target.db.list_projects(), [])

    def test_missing_file_rejects_entire_import(self):
        stream = io.BytesIO(self.source.bundle(self.pid))
        broken = io.BytesIO()
        with zipfile.ZipFile(stream) as source, zipfile.ZipFile(broken, 'w') as out:
            for name in source.namelist():
                if not name.endswith('narration_clean.txt'):
                    out.writestr(name, source.read(name))
        broken.seek(0)
        with self.assertRaisesRegex(ValueError, 'incompleto'):
            import_bundle(self.target, broken)
        self.assertEqual(self.target.db.list_projects(), [])

    def test_recover_local_preserves_artifacts_without_false_approval(self):
        root = self.target.root / 'projects' / 'COAE-OLD'
        script = root / 'exports' / 'script_v001' / 'narration_darkplanner.txt'
        script.parent.mkdir(parents=True)
        script.write_text('Roteiro antigo.', encoding='utf-8')
        other = root / 'old-story.json'
        other.write_text('{}')
        self.assertEqual(local_candidates(self.target), ['COAE-OLD'])
        pid = recover_local(self.target, 'COAE-OLD')['project']
        self.assertFalse(self.target.script(pid)['approved'])
        self.assertEqual(other.read_text(), '{}')
        self.assertEqual(local_candidates(self.target), [])
        with self.assertRaises(ValueError):
            recover_local(self.target, '../source')

    def test_invalid_lineage_rolls_back_database_and_copied_files(self):
        self.source.db.execute("UPDATE exports SET source_ref='999999'")
        existing = self.target.create('Preservado')['project']
        with self.assertRaisesRegex(ValueError, 'vínculos'):
            import_bundle(self.target, io.BytesIO(self.source.bundle(self.pid)))
        self.assertEqual([r['id'] for r in self.target.db.list_projects()], [existing])
        self.assertEqual([p.name for p in (self.target.root / 'projects').iterdir()], [existing])

    def test_http_upload_and_import(self):
        with running_server(self.root / 'http', port=0) as server:
            self.assertTrue(Path(server.temp.name).is_relative_to(self.root / 'http'))
            base = f'http://127.0.0.1:{server.server_port}'
            headers = {'X-COAE-Token': server.token, 'X-Filename': 'project.zip'}
            request = urllib.request.Request(base + '/api/upload', data=self.source.bundle(self.pid), headers=headers)
            with urllib.request.urlopen(request) as response:
                upload = json.load(response)['upload']
            request = urllib.request.Request(base + '/api/action',
                data=json.dumps({'action': 'import_project', 'upload': upload}).encode(), headers=headers)
            with urllib.request.urlopen(request) as response:
                pid = json.load(response)['project']
            self.assertEqual(server.app.script(pid)['body'], 'Texto narrado.')
            self.assertNotIn(upload, server.uploads)

    def test_files_only_zip_requires_confirmation_then_recovers_draft(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('COAE-OLD/exports/script_v001/narration_darkplanner.txt', 'Texto antigo.')
            z.writestr('COAE-OLD/audio/working/old.mp3', b'preserve-original-bytes')
        data = stream.getvalue()
        result = import_bundle(self.target, io.BytesIO(data))
        self.assertTrue(result['requires_confirmation'])
        self.assertEqual(self.target.db.list_projects(), [])
        pid = import_bundle(self.target, io.BytesIO(data), allow_partial=True)['project']
        self.assertFalse(self.target.script(pid)['approved'])
        self.assertEqual(self.target.script(pid)['body'], 'Texto antigo.')
        self.assertEqual((self.target.folder(pid) / 'audio/working/old.mp3').read_bytes(), b'preserve-original-bytes')
        self.assertEqual(self.target.state(pid)['audios'], [])

    def test_trash_restore_preserves_files_and_approval(self):
        before = self.source.script(self.pid)['id']
        exported = self.source.folder(self.pid) / 'exports/script_v001/narration_darkplanner.txt'
        content = exported.read_bytes()
        trash_project(self.source, self.pid)
        self.assertEqual(self.source.db.list_projects(), [])
        self.assertNotIn(self.pid, local_candidates(self.source))
        self.assertEqual(exported.read_bytes(), content)
        restore_project(self.source, self.pid)
        self.assertEqual(self.source.script(self.pid)['id'], before)
        self.assertTrue(self.source.script(self.pid)['approved'])
        self.assertEqual(self.source.db.list_projects()[0]['id'], self.pid)

    def test_trash_refuses_running_job(self):
        self.source.db.execute("INSERT INTO jobs(project_id,action,status) VALUES(?, 'test', 'RUNNING')", (self.pid,))
        with self.assertRaisesRegex(ValueError, 'execução'):
            trash_project(self.source, self.pid)
        self.assertEqual(len(self.source.db.list_projects()), 1)

    def test_http_partial_confirmation_retains_upload_until_decision(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('COAE-OLD/exports/script_v001/narration_darkplanner.txt', 'Texto.')
        with running_server(self.root / 'http-partial', port=0) as server:
            base = f'http://127.0.0.1:{server.server_port}'
            headers = {'X-COAE-Token': server.token, 'X-Filename': 'project.zip'}
            def post(path, body):
                request = urllib.request.Request(base + path, data=body, headers=headers)
                with urllib.request.urlopen(request) as response:
                    return json.load(response)
            for accept in (False, True):
                upload = post('/api/upload', stream.getvalue())['upload']
                result = post('/api/action', json.dumps({'action': 'import_project', 'upload': upload}).encode())
                self.assertTrue(result['requires_confirmation'])
                self.assertIn(upload, server.uploads)
                action = 'import_project' if accept else 'discard_upload'
                result = post('/api/action', json.dumps({'action': action, 'upload': upload, 'allow_partial': accept}).encode())
                self.assertNotIn(upload, server.uploads)
                self.assertEqual(len(server.app.db.list_projects()), int(accept))
