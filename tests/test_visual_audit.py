from unittest.mock import patch
import base64
import json
import os
import unittest
from PIL import Image
import test_regressions as regression
from coae.local_ai import Ollama, VISUAL_AUDIT_SCHEMA


class VisualAuditTests(unittest.TestCase):
    def setUp(self):
        regression.ApplicationTests.setUp(self)
        regression.ApplicationTests.prepared(self)
        self.path = self.root / 'image.png'
        Image.new('RGB', (320, 180), 'navy').save(self.path)
        self.iid = self.app.import_image(self.pid, 'SC001', self.path)['image_id']

    def tearDown(self):
        regression.ApplicationTests.tearDown(self)

    def response(self, severity='review'):
        return {
            'observation': {'summary': 'Imagem azul sem texto.', 'visible_elements': ['fundo azul'], 'uncertainties': ''},
            'judgment': {field: {'message': 'Julgamento de teste em português.', 'severity': severity}
                         for field in ('speech_match', 'missing_contradictory', 'science', 'visual_quality', 'suggestions')},
        }

    def test_real_image_and_scene_context_sent_without_changing_media(self):
        before = self.app.state(self.pid)['scenes'][0]
        with patch.object(self.app, 'remote', return_value=self.response()) as remote:
            report = self.app.image_audit(self.pid, self.iid)
        self.assertEqual(report['decision'], 'REVIEW_REQUIRED')
        self.assertEqual(remote.call_args.args[3]['transcript_reference'], before['transcript_reference'])
        for field in ('semantic_summary', 'visual_description'):
            self.assertEqual(remote.call_args.args[3][field], before[field])
        self.assertEqual(remote.call_args.args[3]['image_id'], self.iid)
        self.assertEqual(remote.call_args.args[3]['scene_id'], 'SC001')
        self.assertEqual(remote.call_args.args[3]['storyboard_version'], self.db.one('SELECT version FROM storyboards WHERE id=(SELECT storyboard_id FROM images WHERE id=?)', (self.iid,))[0])
        self.assertEqual(remote.call_args.args[3]['image_sha256'], self.db.one('SELECT sha256 FROM images WHERE id=?', (self.iid,))[0])
        self.assertEqual(remote.call_args.kwargs['image'][0], self.path.read_bytes())
        self.assertIn('erro bloqueante',remote.call_args.args[2])
        self.assertIn('realismo',remote.call_args.args[2])
        self.assertEqual(self.app.state(self.pid)['scenes'][0], before)

    def test_technical_failure_preserves_approval_and_previous_report(self):
        self.db.execute("UPDATE images SET status='APPROVED' WHERE id=?", (self.iid,))
        before = self.db.one('SELECT COUNT(*) FROM audit_runs')[0]
        for result in ({'issues': []}, None):
            with patch.object(self.app, 'remote', return_value=result, side_effect=ValueError('offline') if result is None else None):
                with self.assertRaisesRegex(ValueError, 'Falha técnica'):
                    self.app.image_audit(self.pid, self.iid)
            self.assertEqual(self.db.one('SELECT status FROM images WHERE id=?', (self.iid,))[0], 'APPROVED')
            self.assertEqual(self.db.one('SELECT COUNT(*) FROM audit_runs')[0], before)

    def test_duplicate_or_extra_audit_categories_are_technical_failure(self):
        self.db.execute("UPDATE images SET status='APPROVED' WHERE id=?", (self.iid,))
        malformed=self.response()
        malformed['judgment']['extra']={'message':'Campo indevido.', 'severity':'review'}
        before=self.db.one('SELECT COUNT(*) FROM audit_runs')[0]
        with patch.object(self.app, 'remote', return_value=malformed):
            with self.assertRaisesRegex(ValueError, 'Falha técnica'):
                self.app.image_audit(self.pid, self.iid)
        self.assertEqual(self.db.one('SELECT status FROM images WHERE id=?', (self.iid,))[0], 'APPROVED')
        self.assertEqual(self.db.one('SELECT COUNT(*) FROM audit_runs')[0], before)

    def test_observation_is_saved_separately_from_judgment(self):
        with patch.object(self.app, 'remote', return_value=self.response()):
            result=self.app.image_audit(self.pid,self.iid)
        self.assertEqual(result['observation']['summary'], 'Imagem azul sem texto.')
        self.assertEqual(len(result['issues']), 6)  # Five judgments plus human-review notice.

    def test_valid_blocking_report_is_not_technical_failure(self):
        with patch.object(self.app, 'remote', return_value=self.response('error')):
            result = self.app.image_audit(self.pid, self.iid)
        self.assertEqual(result['decision'], 'BLOCKED')

    def test_ollama_receives_image_and_enforces_visual_schema(self):
        with patch.dict(os.environ, {'COAE_LOCAL_WRITER_MODEL': 'text', 'COAE_LOCAL_VISION_MODEL': 'vision'}):
            adapter = Ollama()
        raw = self.path.read_bytes()
        with patch.object(adapter, 'check'), patch.object(adapter.http, 'request', return_value={
                'done': True, 'message': {'content': json.dumps(self.response())}}) as request:
            adapter.call('Examine a imagem', {'transcript_reference': 'Fala da cena'}, audit=True, image=(raw, 'image/png'))
        body = request.call_args.args[1]
        self.assertEqual(body['model'], 'vision')
        self.assertEqual(body['format'], VISUAL_AUDIT_SCHEMA)
        self.assertEqual(base64.b64decode(body['messages'][1]['images'][0]), raw)
        self.assertIn('Fala da cena', body['messages'][1]['content'])
