import io
import json
import os
import unittest
from unittest.mock import patch
from PIL import Image
import test_regressions as regression


class ImprovementTests(unittest.TestCase):
    def setUp(self):
        regression.ApplicationTests.setUp(self)
        regression.ApplicationTests.prepared(self)
        p=self.root/'source.png';Image.new('RGB',(320,180),'navy').save(p)
        self.iid=self.app.import_image(self.pid,'SC001',p)['image_id']
        self.issues=[{'code':c,'message':'Corrigir detalhe '+c,'severity':'review'} for c in ('SPEECH_MATCH','MISSING_CONTRADICTORY','SCIENCE','VISUAL_QUALITY','SUGGESTIONS')]
        self.app.store_audit(self.pid,'image',self.iid,self.issues)
        b=io.BytesIO();Image.new('RGB',(320,180),'purple').save(b,format='PNG');self.raw=b.getvalue()
        self.env=patch.dict(os.environ,{'COAE_TEXT_PROVIDER':'ollama','COAE_IMAGE_PROVIDER':'comfyui'});self.env.start()
        self.plan={'prompt':'A sharper stellar field without labels.','improvements':'Melhorar nitidez e composição.'}
    def tearDown(self):
        self.env.stop();regression.ApplicationTests.tearDown(self)
    def fake_generate(self,prompt,ticket,persist):
        persist({'prompt_id':'test-ticket','fingerprint':'fixture'})
        return self.raw,{'provider':'comfyui'}
    def test_revision_uses_audit_preserves_parent_and_is_idempotent(self):
        self.db.execute("UPDATE images SET status='BLOCKED' WHERE id=?",(self.iid,))
        before=self.app.state(self.pid)
        with patch.object(self.app,'remote',return_value=self.plan) as writer,patch('coae.image_improvement.ComfyUI') as factory:
            factory.return_value.generate.side_effect=self.fake_generate
            result=self.app.improve_image(self.pid,self.iid)
            repeated=self.app.improve_image(self.pid,self.iid)
            self.assertEqual(repeated['image_id'],result['image_id']);writer.assert_called_once()
            factory.return_value.generate.assert_called_once()
            context=writer.call_args.args[3]
            self.assertIn('aparência fotográfica realista',writer.call_args.args[2])
            self.assertEqual(context['scene'],before['scenes'][0]);self.assertEqual(context['audit']['issues'],self.issues)
            self.assertEqual(factory.return_value.generate.call_args.args[0],self.plan['prompt'])
        after=self.app.state(self.pid)
        self.assertEqual(after['scenes'],before['scenes']);self.assertEqual(after['stories'],before['stories'])
        self.assertEqual(after['images'][1],before['images'][0]);self.assertEqual(after['images'][0]['status'],'REVIEW_REQUIRED')
        self.assertNotEqual(after['images'][0]['path'],after['images'][1]['path'])
        self.assertEqual(after['events'][0]['action'],'IMAGE_IMPROVED')
    def test_resume_keeps_plan_and_ticket_after_timeout(self):
        def fail(prompt,ticket,persist):
            persist({'prompt_id':'queued'});raise ValueError('timeout')
        with patch.object(self.app,'remote',return_value=self.plan) as writer,patch('coae.image_improvement.ComfyUI') as factory:
            factory.return_value.generate.side_effect=fail
            with self.assertRaisesRegex(ValueError,'timeout'):self.app.improve_image(self.pid,self.iid)
            factory.return_value.generate.side_effect=self.fake_generate
            self.app.improve_image(self.pid,self.iid)
            writer.assert_called_once()
            self.assertEqual(factory.return_value.generate.call_args.args[1],{'prompt_id':'queued'})
    def test_invalid_plan_and_missing_audit_do_not_generate(self):
        with patch.object(self.app,'remote',return_value={'prompt':''}),patch('coae.image_improvement.ComfyUI') as factory:
            with self.assertRaisesRegex(ValueError,'inválido'):self.app.improve_image(self.pid,self.iid)
            factory.assert_not_called()
        self.app.store_audit(self.pid,'image',self.iid,[])
        with self.assertRaisesRegex(ValueError,'parecer visual completo'):self.app.improve_image(self.pid,self.iid)
        self.assertEqual(len(self.app.state(self.pid)['images']),1)
    def test_duplicate_output_cannot_bypass_blocked_image(self):
        self.db.execute("UPDATE images SET status='BLOCKED' WHERE id=?",(self.iid,))
        from pathlib import Path
        self.raw=Path(self.app.state(self.pid)['images'][0]['path']).read_bytes()
        with patch.object(self.app,'remote',return_value=self.plan),patch('coae.image_improvement.ComfyUI') as factory:
            factory.return_value.generate.side_effect=self.fake_generate
            with self.assertRaisesRegex(ValueError,'idêntica'):self.app.improve_image(self.pid,self.iid)
        self.assertEqual(len(self.app.state(self.pid)['images']),1)
        self.assertEqual(self.app.state(self.pid)['images'][0]['status'],'BLOCKED')
    def test_stale_story_or_paid_provider_rejected(self):
        with patch.dict(os.environ,{'COAE_TEXT_PROVIDER':'gemini'}):
            with self.assertRaisesRegex(ValueError,'locais'):self.app.improve_image(self.pid,self.iid)
        self.db.execute("UPDATE storyboards SET status='DRAFT' WHERE project_id=?",(self.pid,))
        with self.assertRaisesRegex(ValueError,'aprove'):self.app.improve_image(self.pid,self.iid)
