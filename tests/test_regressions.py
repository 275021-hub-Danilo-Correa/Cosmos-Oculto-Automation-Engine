import json
import io
import math
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import wave
import zipfile
from unittest.mock import patch
from coae.application import Application
from coae.audio import import_audio,file_sha256,verified_audio
from coae.models import TranscriptSegment
from coae.pipeline import transcribe_and_build_storyboard
from coae.script_service import save_script,approve_script,export_script
from coae.segmentation import segment_scenes
from coae.storage import Database
from coae.transcription import JsonTranscriptProvider,InvalidTranscriptError

class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=Database(self.root/'db.sqlite');self.db.create_project('A','A');self.db.create_project('B','B')
    def tearDown(self):self.db.close();self.tmp.cleanup()
    def wav(self,name='in/narracao.wav',seconds=2):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*round(seconds*8000))
        return p
    def test_documented_cli_creates_and_opens_project(self):
        repo=Path(__file__).resolve().parents[1];env=dict(os.environ,PYTHONPATH=str(repo));db=self.root/'cli.db'
        for args in [['create-project','Teste','--project-id','CLI'],['open-project','CLI']]:
            r=subprocess.run([sys.executable,'-m','coae.cli','--database',str(db),*args],cwd=self.root,env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr);self.assertIn('CLI',r.stdout)
        self.assertTrue(db.exists())
    def test_original_pause_preserved(self):
        body='Primeiro. <break time="3s"/>\n\nSegundo. <break time="0.5s"/>'
        v=save_script(self.db,'A','Teste',body);approve_script(self.db,'A',v)
        paths=export_script(self.db,'A',None,None,self.root/'export')
        self.assertEqual(paths['narration_darkplanner'].read_text().strip(),body)
        self.assertNotIn('<break',paths['narration_clean'].read_text())
    def test_two_script_exports_do_not_overwrite(self):
        v=save_script(self.db,'A','T','Original.');approve_script(self.db,'A',v);first=export_script(self.db,'A',None,None,self.root/'exports')
        v=save_script(self.db,'A','T','Novo.');approve_script(self.db,'A',v);second=export_script(self.db,'A',None,None,self.root/'exports')
        self.assertNotEqual(first['script_master'],second['script_master']);self.assertIn('Original.',first['script_master'].read_text())
    def test_same_filename_keeps_original_audio(self):
        aid=import_audio(self.db,'A',self.wav(),self.root/'project');old=dict(self.db.one('SELECT * FROM audio_files WHERE id=?',(aid,)))
        import_audio(self.db,'A',self.wav('other/narracao.wav',3),self.root/'project')
        self.assertEqual(file_sha256(Path(old['original_path'])),old['sha256'])
    def test_foreign_keys_enabled(self):self.assertEqual(self.db.one('PRAGMA foreign_keys')[0],1)
    def test_cross_project_audio_rejected(self):
        aid=import_audio(self.db,'A',self.wav(),self.root/'project')
        with self.assertRaises(ValueError):verified_audio(self.db,'B',aid)
    def test_duration_from_file_not_argument(self):
        source=self.wav();aid=import_audio(self.db,'A',source,self.root/'project')
        with self.assertRaises(ValueError):transcribe_and_build_storyboard(self.db,'A',aid,source,99,None)
    def test_corrupt_audio_rejected(self):
        aid=import_audio(self.db,'A',self.wav(),self.root/'project');row=self.db.one('SELECT * FROM audio_files WHERE id=?',(aid,));Path(row['working_path']).write_bytes(b'corrupt')
        with self.assertRaises(ValueError):verified_audio(self.db,'A',aid)
    def test_invalid_transcription_not_committed(self):
        source=self.wav();aid=import_audio(self.db,'A',source,self.root/'project');p=self.root/'trans.json';p.write_text(json.dumps({'segments':[{'start':0,'end':50,'text':'Fala'}]}))
        with self.assertRaises(ValueError):transcribe_and_build_storyboard(self.db,'A',aid,source,2,JsonTranscriptProvider(p))
        self.assertEqual(self.db.one('SELECT COUNT(*) FROM transcriptions')[0],0)
    def test_finite_times_required(self):
        for v in (float('nan'),float('inf')):
            with self.assertRaises(ValueError):segment_scenes([TranscriptSegment(0,v,'Fala.')],10)
    def test_variable_speech_and_pause_coverage(self):
        scenes=segment_scenes([TranscriptSegment(.2,4.1,'Estrela.'),TranscriptSegment(4.3,15.9,'Buraco negro.'),TranscriptSegment(16.1,19.8,'Fim.')],20)
        self.assertEqual(len(scenes),3)
        self.assertEqual([(s.start_time,s.end_time) for s in scenes],[(0,4.3),(4.3,16.1),(16.1,20)])
        self.assertNotEqual(scenes[1].duration,8)
    def test_word_timing_does_not_make_word_per_scene(self):
        scenes=segment_scenes([TranscriptSegment(0,.4,'Uma'),TranscriptSegment(.4,.8,'estrela'),TranscriptSegment(.8,1.4,'nasce.'),TranscriptSegment(1.5,2,'Fim.')],2)
        self.assertEqual(len(scenes),2);self.assertEqual(scenes[0].transcript_reference,'Uma estrela nasce.')
    def test_overlaps_rejected(self):
        with self.assertRaises(ValueError):segment_scenes([TranscriptSegment(0,3,'A.'),TranscriptSegment(2,4,'B.')],5)
    def test_path_traversal_project_id_rejected(self):
        with self.assertRaises(ValueError):self.db.create_project('../escape','x')
    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg não instalado')
    def test_mp3_real_import(self):
        source=self.wav();mp3=self.root/'voice.mp3'
        subprocess.run(['ffmpeg','-v','error','-i',str(source),'-y',str(mp3)],check=True)
        aid=import_audio(self.db,'A',mp3,self.root/'project');self.assertGreater(self.db.one('SELECT duration FROM audio_files WHERE id=?',(aid,))[0],1.9)

class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.app=Application(self.root);self.pid=self.app.create('Teste')['project'];self.db=self.app.db
        save_script(self.db,self.pid,'Roteiro','Uma estrela surge. Agora um buraco negro. O espaço fica escuro.')
        self.app.audit_script(self.pid);self.app.approve_script(self.pid,1,'Revisão sintética realizada.')
        p=self.root/'voice.wav'
        with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*160000)
        aid=self.app.import_audio(self.pid,p)['audio_id'];self.app.approve_audio(self.pid,aid,'Áudio sintético de teste conferido.')
        self.trans=self.root/'trans.json';self.trans.write_text(json.dumps({'segments':[{'start':0,'end':4.3,'text':'Uma estrela surge.'},{'start':4.3,'end':16.1,'text':'Agora um buraco negro.'},{'start':16.1,'end':20,'text':'O espaço fica escuro.'}]}))
    def tearDown(self):self.db.close();self.tmp.cleanup()
    def prepared(self):
        self.app.analyze(self.pid,transcript_path=self.trans);state=self.app.state(self.pid)
        for s in state['scenes']:s.update(semantic_summary='Cena de teste',visual_description='Representação científica de um campo estelar.')
        self.app.save_story(self.pid,state['stories'][0]['version'],state['scenes']);self.app.approve_story(self.pid,self.app.story(self.pid)[0]['version'],'Falas e visuais de teste conferidos.')
    def test_missing_descriptions_block_storyboard(self):
        self.app.analyze(self.pid,transcript_path=self.trans)
        with self.assertRaises(ValueError):self.app.approve_story(self.pid,1,'Teste de aprovação bloqueada.')
    def test_full_assisted_flow_images_timeline_reopen(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Instale Pillow para teste de mídia.')
        self.prepared();image=self.root/'image.png';Image.new('RGB',(160,90),'#112244').save(image)
        for scene in ('SC001','SC002','SC003'):
            iid=self.app.import_image(self.pid,scene,image)['image_id'];self.app.approve_image(self.pid,iid,'Imagem sintética de teste revisada.')
        self.app.export_timeline(self.pid)
        timeline=next(self.app.folder(self.pid).rglob('timeline.json'));d=json.loads(timeline.read_text())
        for actual,expected in zip([s['duration'] for s in d['scenes']],[4.3,11.8,3.9]):self.assertAlmostEqual(actual,expected)
        self.assertTrue(timeline.with_name('legendas.srt').exists());self.assertTrue(timeline.with_name('legendas.vtt').exists())
        self.db.close();self.app=Application(self.root);self.db=self.app.db
        self.assertEqual(self.app.story(self.pid,approved=True)[0]['status'],'APPROVED')
    def test_audio_changes_invalidate_storyboard(self):
        self.prepared();p=self.root/'another.wav'
        with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*168000)
        self.app.import_audio(self.pid,p)
        with self.assertRaises(ValueError):self.app.story(self.pid,approved=True)
    def test_reimport_same_audio_after_invalidation(self):
        previous=self.app.audio(self.pid)['id']
        self.app.save_sources(self.pid,'Fonte revisada para este teste.')
        self.app.audit_script(self.pid);self.app.approve_script(self.pid,1,'Fontes revisadas novamente.')
        current=self.app.import_audio(self.pid,self.root/'voice.wav')['audio_id']
        self.assertNotEqual(previous,current)
        self.assertEqual(self.app.audio(self.pid)['status'],'IMPORTED')
    def test_legacy_relative_audio_paths_open_in_studio(self):
        row=self.app.audio(self.pid)
        for column in ('original_path','working_path'):
            relative=str(Path(row[column]).relative_to(self.root))
            self.db.execute(f'UPDATE audio_files SET {column}=? WHERE id=?',(relative,row['id']))
        self.db.close();self.app=Application(self.root);self.db=self.app.db
        self.assertTrue(self.app.state(self.pid)['audios'][0]['relative_path'])
        self.assertEqual(self.app.audio(self.pid)['id'],row['id'])
    def test_project_bundle_contains_database_snapshot(self):
        bundle=self.app.bundle(self.pid)
        with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
            names=archive.namelist()
            self.assertIn(f'{self.pid}/data/coae.sqlite3',names)
            self.assertIn(f'{self.pid}/BACKUP_README.txt',names)
            snapshot_path=self.root/'bundle.sqlite3'
            snapshot_path.write_bytes(archive.read(f'{self.pid}/data/coae.sqlite3'))
            snapshot=sqlite3.connect(snapshot_path)
            self.assertEqual(snapshot.execute('SELECT COUNT(*) FROM projects').fetchone()[0],1)
            snapshot.close()
    def assert_preflight_preserves_project(self,environment,client_error=None):
        self.prepared()
        before='\n'.join(self.db.connection.iterdump())
        with patch.dict(os.environ,environment,clear=True), patch('coae.provider.Gemini') as client, patch('coae.application.transcribe_and_build_storyboard') as transcribe:
            if client_error:client.side_effect=client_error
            with self.assertRaises(ValueError):self.app.analyze(self.pid,semantic=True)
            transcribe.assert_not_called()
            client.return_value.call.assert_not_called()
        self.assertEqual(before,'\n'.join(self.db.connection.iterdump()))

    def test_missing_gemini_config_preserves_approved_storyboard(self):
        self.assert_preflight_preserves_project({})

    def test_blank_gemini_key_preserves_approved_storyboard(self):
        self.assert_preflight_preserves_project({'GEMINI_API_KEY':'   ','COAE_WRITER_MODEL':'writer','COAE_AUDITOR_MODEL':'auditor','COAE_MAX_CALLS_PER_PROJECT':'10'})

    def test_invalid_or_zero_budget_prevents_transcription(self):
        for budget in ('invalid','0','-1'):
            with self.subTest(budget=budget):
                self.assert_preflight_preserves_project({'GEMINI_API_KEY':'test','COAE_WRITER_MODEL':'writer','COAE_AUDITOR_MODEL':'auditor','COAE_MAX_CALLS_PER_PROJECT':budget})

    def test_exhausted_budget_prevents_transcription(self):
        self.db.execute("INSERT INTO api_calls(project_id,role,status) VALUES(?,'writer','DONE')",(self.pid,))
        self.assert_preflight_preserves_project({'GEMINI_API_KEY':'test','COAE_WRITER_MODEL':'writer','COAE_AUDITOR_MODEL':'auditor','COAE_MAX_CALLS_PER_PROJECT':'1'})

    def test_missing_sdk_prevents_transcription(self):
        self.assert_preflight_preserves_project({'GEMINI_API_KEY':'test','COAE_WRITER_MODEL':'writer','COAE_AUDITOR_MODEL':'auditor','COAE_MAX_CALLS_PER_PROJECT':'10'},ValueError('Instale requirements-api.txt'))

    def test_valid_preflight_runs_no_remote_request(self):
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test','COAE_WRITER_MODEL':'writer','COAE_AUDITOR_MODEL':'auditor','COAE_MAX_CALLS_PER_PROJECT':'10'},clear=True),patch('coae.provider.Gemini') as client:
            self.app.preflight_analysis(self.pid,True)
            client.assert_called_once();client.return_value.close.assert_called_once()
            client.return_value.call.assert_not_called()
        self.assertEqual(self.db.one('SELECT COUNT(*) FROM api_calls')[0],0)

    def test_local_analysis_does_not_require_gemini(self):
        with patch.dict(os.environ,{},clear=True),patch('coae.provider.Gemini') as client:
            self.app.analyze(self.pid,False,self.trans)
            client.assert_not_called()
        self.assertTrue(self.app.story(self.pid)[1])

    def test_http_preflight_rejects_before_job_or_upload_consumption(self):
        import threading
        import urllib.request
        import urllib.error
        from coae.server import Server
        self.prepared()
        server=Server(('127.0.0.1',0),self.app)
        server.uploads['fixture']=self.trans
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        before='\n'.join(self.db.connection.iterdump())
        try:
            with patch.dict(os.environ,{},clear=True):
                for action in ('analyze','import_transcript'):
                    request=urllib.request.Request(f'http://127.0.0.1:{server.server_port}/api/action',data=json.dumps({'action':action,'project':self.pid,'semantic':True,'upload':'fixture'}).encode(),headers={'Content-Type':'application/json','X-COAE-Token':server.token})
                    with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(request)
                    self.assertEqual(caught.exception.code,400)
                    self.assertIn('GEMINI_API_KEY',caught.exception.read().decode())
            self.assertEqual(before,'\n'.join(self.db.connection.iterdump()))
            self.assertIn('fixture',server.uploads)
        finally:
            server.shutdown();thread.join();server.server_close();server.temp.cleanup()
    def test_invalid_ai_output_never_approves(self):
        self.app.remote=lambda *a,**k:{'approved':True}
        with self.assertRaises(ValueError):self.app.audit_script(self.pid,remote=True)
    def test_zero_budget_no_api_call(self):
        with patch('coae.provider.Gemini') as provider,patch.dict(os.environ,{'COAE_MAX_CALLS_PER_PROJECT':'0'}):
            with self.assertRaises(ValueError):self.app.remote(self.pid,'writer','test',{})
            provider.return_value.call.assert_not_called()
    def test_failed_call_counted_without_auto_retry(self):
        with patch('coae.provider.Gemini') as provider,patch.dict(os.environ,{'COAE_MAX_CALLS_PER_PROJECT':'1'}):
            provider.return_value.call.side_effect=TimeoutError()
            with self.assertRaises(ValueError):self.app.remote(self.pid,'writer','test',{})
            with self.assertRaises(ValueError):self.app.remote(self.pid,'writer','test',{})
            self.assertEqual(provider.return_value.call.call_count,1)
            self.assertEqual(self.db.one('SELECT status FROM api_calls')[0],'UNKNOWN_REMOTE_RESULT')

    def test_quota_error_is_reported_without_retry(self):
        class QuotaError(Exception):
            code=429
        with patch('coae.provider.Gemini') as provider,patch.dict(os.environ,{'COAE_MAX_CALLS_PER_PROJECT':'1'}):
            provider.return_value.generate_image.side_effect=QuotaError()
            with self.assertRaisesRegex(ValueError,'Cota Gemini excedida'):
                self.app.remote(self.pid,'image','image',{'prompt':'teste'})
            with self.assertRaises(ValueError):
                self.app.remote(self.pid,'image','image',{'prompt':'teste'})
            row=self.db.one('SELECT status,metadata FROM api_calls ORDER BY id DESC LIMIT 1')
            self.assertEqual(row['status'],'UNKNOWN_REMOTE_RESULT')
            self.assertIn('429',row['metadata'])
    def test_no_image_before_storyboard_approval(self):
        self.app.analyze(self.pid,transcript_path=self.trans)
        with self.assertRaises(ValueError):self.app.import_image(self.pid,'SC001',self.root/'missing.png')
    def test_sources_change_invalidates_approval(self):
        self.prepared();self.app.save_sources(self.pid,'Outra evidência.')
        self.assertEqual(self.app.script(self.pid)['approved'],0)
        with self.assertRaises(ValueError):self.app.story(self.pid,approved=True)
    def test_story_overlap_blocks_approval(self):
        self.prepared();state=self.app.state(self.pid);state['scenes'][1]['start_time']=1
        out=self.app.save_story(self.pid,state['stories'][0]['version'],state['scenes'])
        self.assertEqual(out['audit']['decision'],'BLOCKED')
    def test_merge_creates_revision_requiring_visual_review(self):
        self.prepared();version=self.app.story(self.pid)[0]['version'];self.app.merge_scene(self.pid,version,'SC001')
        st,scenes=self.app.story(self.pid)
        self.assertEqual(len(scenes),2);self.assertEqual(st['status'],'BLOCKED');self.assertEqual(scenes[0].end_time,16.1)
    def test_split_uses_actual_word_boundary(self):
        payload={'segments':[{'start':0,'end':2,'text':'Uma'},{'start':2,'end':4.3,'text':'estrela.'},{'start':4.3,'end':20,'text':'Fim.'}]}
        self.trans.write_text(json.dumps(payload));self.app.analyze(self.pid,transcript_path=self.trans)
        self.app.split_scene(self.pid,self.app.story(self.pid)[0]['version'],'SC001')
        _,scenes=self.app.story(self.pid);self.assertEqual(scenes[0].end_time,2);self.assertEqual(scenes[1].start_time,2)

if __name__=='__main__':unittest.main()
