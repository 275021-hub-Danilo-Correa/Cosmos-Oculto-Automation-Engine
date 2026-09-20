"""Protocol fixtures only: no real AI, GPU, models or paid API calls."""
import io
import json
import os
from pathlib import Path
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from PIL import Image
import test_regressions as regression
from coae.local_ai import LocalHTTP, Ollama, ComfyUI, diagnostics
from coae.server import Server


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def handle_request(self):
        raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        data = json.loads(raw) if raw else None
        self.server.calls.append((self.path, data))
        if self.path == '/api/tags': value = {'models': [{'name': 'fixture:latest'}]}
        elif self.path == '/api/show': value = self.server.info
        elif self.path == '/api/chat':
            if self.server.bad_json:
                value = {'done': True, 'message': {'content': 'not json'}}
            else:
                scenes = json.loads(data['messages'][1]['content'])['data'].get('scenes', [])
                value = {'done': True, 'message': {'content': json.dumps({'scenes': [dict(
                    scene_id=s['scene_id'], semantic_summary='Teste de protocolo',
                    visual_description='Campo estelar sem rótulos, plano amplo documental.',
                    visual_function='ESTABLISH', camera_direction='WIDE', movement='STATIC') for s in scenes]})}}
        elif self.path == '/system_stats': value = {}
        elif self.path == '/object_info':
            value = {name: {} for name in ComfyUI.ALLOWED}
            value['CheckpointLoaderSimple'] = {'input': {'required': {'ckpt_name': [['SEU_CHECKPOINT_SDXL.safetensors']]}}}
        elif self.path == '/prompt': value = {'prompt_id': 'fixture-job', 'node_errors': {}}
        elif self.path.startswith('/history/'):
            value = {'fixture-job': {'status': {'completed': True, 'status_str': 'success'},
                     'outputs': {'9': {'images': [{'filename': 'fixture.png', 'subfolder': '', 'type': 'output'}]}}}}
        elif self.path.startswith('/view?'):
            b = io.BytesIO(); Image.new('RGB', (320, 180)).save(b, format='PNG')
            self.send_response(200);self.end_headers();self.wfile.write(b.getvalue());return
        else: value = {}
        self.send_response(200);self.end_headers();self.wfile.write(json.dumps(value).encode())


class LocalTests(unittest.TestCase):
    # Reuse only fixture helpers; do not inherit its entire test suite.
    def setUp(self):
        regression.ApplicationTests.setUp(self)
        self.service = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
        self.service.calls = [];self.service.info = {'capabilities': ['completion', 'vision']};self.service.bad_json = False
        self.thread = threading.Thread(target=self.service.serve_forever, daemon=True);self.thread.start()
        self.url = f'http://127.0.0.1:{self.service.server_port}'
        self.env = patch.dict(os.environ, {
            'COAE_TEXT_PROVIDER':'ollama','COAE_IMAGE_PROVIDER':'comfyui',
            'COAE_LOCAL_WRITER_MODEL':'fixture','COAE_LOCAL_AUDITOR_MODEL':'',
            'COAE_LOCAL_VISION_MODEL':'','COAE_OLLAMA_URL':self.url,
            'COAE_COMFYUI_URL':self.url,'COAE_MAX_CALLS_PER_PROJECT':'0',
            'COAE_COMFYUI_WORKFLOW':str(Path(__file__).resolve().parents[1]/'workflows/sdxl_api.example.json')})
        self.env.start()
    def tearDown(self):
        self.env.stop();self.service.shutdown();self.service.server_close();self.thread.join()
        regression.ApplicationTests.tearDown(self)

    def test_descriptions_preserve_times_and_do_not_call_gemini(self):
        self.app.analyze(self.pid, transcript_path=self.trans)
        before=self.app.state(self.pid)['scenes']
        with patch('coae.provider.Gemini', side_effect=AssertionError('Cloud forbidden')):
            self.app.describe_scenes(self.pid)
        after=self.app.state(self.pid)['scenes']
        self.assertEqual([(s['start_time'],s['end_time']) for s in before],[(s['start_time'],s['end_time']) for s in after])
        self.assertTrue(all(s['visual_description'] for s in after))
        self.assertEqual(self.db.one('SELECT COUNT(*) FROM api_calls')[0],0)
        chats=[d for p,d in self.service.calls if p=='/api/chat']
        self.assertEqual(chats[0]['keep_alive'],0)

    def test_invalid_json_preserves_story(self):
        self.app.analyze(self.pid,transcript_path=self.trans)
        before=self.app.state(self.pid)['stories'][0]['version'];self.service.bad_json=True
        with self.assertRaisesRegex(ValueError,'JSON inválido'):self.app.describe_scenes(self.pid)
        self.assertEqual(self.app.state(self.pid)['stories'][0]['version'],before)

    def test_manual_description_is_preserved(self):
        self.app.analyze(self.pid,transcript_path=self.trans)
        state=self.app.state(self.pid);state['scenes'][0].update(semantic_summary='Minha ideia',visual_description='Minha descrição')
        self.app.save_story(self.pid,state['stories'][0]['version'],state['scenes'])
        self.app.describe_scenes(self.pid)
        self.assertEqual(self.app.state(self.pid)['scenes'][0]['visual_description'],'Minha descrição')

    def test_images_are_persisted_review_required_and_not_regenerated(self):
        regression.ApplicationTests.prepared(self)
        with patch('coae.provider.Gemini',side_effect=AssertionError('Cloud forbidden')):
            self.assertEqual(self.app.generate_images(self.pid,'SC001')['generated'],1)
            self.assertEqual(self.app.generate_images(self.pid,'SC001')['generated'],0)
        image=self.app.state(self.pid)['images'][0]
        self.assertEqual(image['status'],'REVIEW_REQUIRED');self.assertTrue(Path(image['path']).exists())
        self.assertEqual(sum(p=='/prompt' for p,d in self.service.calls),1)
        self.assertEqual(self.db.one('SELECT COUNT(*) FROM api_calls')[0],0)

    def test_blocked_image_cannot_be_reimported_to_bypass_audit(self):
        regression.ApplicationTests.prepared(self)
        self.app.generate_images(self.pid,'SC001')
        iid=self.app.state(self.pid)['images'][0]['id']
        self.db.execute("UPDATE images SET status='BLOCKED' WHERE id=?",(iid,))
        with self.assertRaisesRegex(ValueError,'bloqueada'):
            self.app.generate_images(self.pid,'SC001')
        self.assertEqual(len(self.app.state(self.pid)['images']),1)
        self.assertEqual(self.app.state(self.pid)['images'][0]['status'],'BLOCKED')

    def test_submitted_ticket_resumes_without_post(self):
        client=ComfyUI();saved=[]
        raw,usage=client.generate('A star.',None,lambda x:saved.append(dict(x)))
        count=sum(p=='/prompt' for p,d in self.service.calls)
        resumed,_=client.generate('A star.',saved[-1],lambda x:None)
        self.assertEqual(raw,resumed)
        self.assertEqual(sum(p=='/prompt' for p,d in self.service.calls),count)
        with self.assertRaisesRegex(ValueError,'Configuração mudou'):
            client.generate('A planet.',saved[-1],lambda x:None)

    def test_realistic_style_and_actual_negative_conditioning_preserve_workflow(self):
        from coae.visual_style import REALISTIC_STYLE, NON_REALISTIC_NEGATIVE
        client=ComfyUI();original=json.loads(json.dumps(client.workflow))
        client.generate('A star.',None,lambda x:None)
        submitted=next(d['prompt'] for p,d in self.service.calls if p=='/prompt')
        self.assertTrue(submitted[client.positive]['inputs']['text'].startswith(REALISTIC_STYLE))
        for node in submitted.values():
            if node['class_type']=='KSampler':
                key=node['inputs']['negative'][0]
                self.assertIn(NON_REALISTIC_NEGATIVE,submitted[key]['inputs']['text'])
                self.assertIn(original[key]['inputs']['text'],submitted[key]['inputs']['text'])
        self.assertEqual(client.workflow,original)

    def test_negative_must_not_reuse_positive_encoder(self):
        client=ComfyUI()
        for node in client.workflow.values():
            if node['class_type']=='KSampler':node['inputs']['negative']=[client.positive,0]
        with self.assertRaisesRegex(ValueError,'negativo separado'):
            client.generate('A star.',None,lambda x:None)
        self.assertFalse(any(p=='/prompt' for p,d in self.service.calls))

    def test_unknown_submission_is_not_repeated(self):
        client=ComfyUI();saved=[];original=client.http.request
        def fail(route,*args,**kwargs):
            if route=='/prompt':raise ValueError('Lost response')
            return original(route,*args,**kwargs)
        with patch.object(client.http,'request',side_effect=fail):
            with self.assertRaises(ValueError):client.generate('A star.',None,lambda x:saved.append(dict(x)))
        with self.assertRaisesRegex(ValueError,'sem confirmação'):
            client.generate('A star.',saved[-1],lambda x:None)
        self.assertFalse(any(p=='/prompt' for p,d in self.service.calls))

    def test_vision_requires_capable_model(self):
        with self.assertRaises(ValueError):Ollama().call('Audit',{},image=(b'fake','image/png'))
        with patch.dict(os.environ,{'COAE_LOCAL_VISION_MODEL':'fixture'}):
            self.service.info={'capabilities':['completion']}
            with self.assertRaisesRegex(ValueError,'capacidade visual'):Ollama().check(vision=True)

    def test_cloud_models_rejected(self):
        self.service.info={'remote_host':'https://cloud.example'}
        with self.assertRaisesRegex(ValueError,'cloud'):Ollama().check()
        self.assertFalse(any(p=='/api/chat' for p,d in self.service.calls))

    def test_diagnostic_no_generation_and_unavailable_error(self):
        result=diagnostics();self.assertTrue(all(r['status']=='READY_TO_TEST' for r in result['services']))
        self.assertFalse(any(p in ('/prompt','/api/chat') for p,d in self.service.calls))
        with patch.dict(os.environ,{'COAE_LOCAL_WRITER_MODEL':'missing'}):
            self.assertEqual(diagnostics()['services'][0]['status'],'UNAVAILABLE')

    def test_only_loopback_urls(self):
        for url in ('https://cloud.example','http://192.168.1.1:8188','http://127.0.0.1@cloud.example','http://localhost:8188/redirect'):
            with self.assertRaises(ValueError):LocalHTTP(url)

    def test_paid_or_custom_workflow_rejected(self):
        f=self.root/'bad.json';f.write_text(json.dumps({'1':{'class_type':'PaidAPINode','inputs':{}}}))
        with patch.dict(os.environ,{'COAE_COMFYUI_WORKFLOW':str(f)}):
            with self.assertRaisesRegex(ValueError,'Nós de API'):ComfyUI()

    def test_http_health_job_requires_auth_and_finishes(self):
        import urllib.request
        import urllib.error
        import time
        server=Server(('127.0.0.1',0),self.app)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            url=f'http://127.0.0.1:{server.server_port}/api/action'
            body=json.dumps({'action':'diagnose_local','project':self.pid}).encode()
            with self.assertRaises(urllib.error.HTTPError) as error:
                opener.open(urllib.request.Request(url,data=body))
            self.assertEqual(error.exception.code,401)
            req=urllib.request.Request(url,data=body,headers={'X-COAE-Token':server.token,'Content-Type':'application/json'})
            with opener.open(req) as r:jid=json.load(r)['job']
            for _ in range(100):
                row=self.db.one('SELECT * FROM jobs WHERE id=?',(jid,))
                if row['status']!='RUNNING':break
                time.sleep(.02)
            self.assertEqual(row['status'],'DONE')
            self.assertIn('READY_TO_TEST',row['result'])
        finally:server.shutdown();server.server_close();server.temp.cleanup();thread.join()

if __name__=='__main__':unittest.main()
