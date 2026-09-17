import json
import unittest
from unittest.mock import patch
import test_regressions as fixtures

class StoryHistoryTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.ApplicationTests();self.fixture.setUp()
        self.app=self.fixture.app;self.db=self.fixture.db;self.pid=self.fixture.pid
        self.fixture.prepared()
        self.source=self.app.story(self.pid)[0]['version']
        self.original=[dict(r) for r in self.db.rows('SELECT * FROM scenes WHERE project_id=? AND storyboard_version=?',(self.pid,self.source))]
        self.app.merge_scene(self.pid,self.source,'SC001')
        self.app.merge_scene(self.pid,self.source+1,'SC001')
        self.current=self.source+2
    def tearDown(self):self.fixture.tearDown()
    def snapshot(self):return '\n'.join(self.db.connection.iterdump())
    def test_restore_preserves_history_and_needs_approval(self):
        with patch.object(self.app,'remote',side_effect=AssertionError('No API')):
            result=self.app.restore_story(self.pid,self.current,self.source)
        self.assertEqual(result['version'],self.current+1)
        self.assertEqual(result['scene_count'],3)
        self.assertNotEqual(self.app.story(self.pid)[0]['status'],'APPROVED')
        self.assertEqual(self.original,[dict(r) for r in self.db.rows('SELECT * FROM scenes WHERE project_id=? AND storyboard_version=?',(self.pid,self.source))])
        self.assertEqual(self.db.one('SELECT COUNT(*) FROM transcriptions')[0],1)
        self.assertEqual(self.db.one('SELECT COUNT(*) FROM api_calls')[0],0)
    def test_restore_stale_screen_no_mutations(self):
        before=self.snapshot()
        with self.assertRaises(ValueError):self.app.restore_story(self.pid,self.source,self.source-1)
        self.assertEqual(before,self.snapshot())
    def test_invalid_source_no_mutations(self):
        before=self.snapshot()
        for version in (0,999,self.current,True):
            with self.assertRaises(ValueError):self.app.restore_story(self.pid,self.current,version)
        self.assertEqual(before,self.snapshot())
    def test_restore_other_audio_rejected(self):
        self.db.execute('UPDATE storyboards SET audio_id=NULL WHERE project_id=? AND version=?',(self.pid,self.source))
        before=self.snapshot()
        with self.assertRaises(ValueError):self.app.restore_story(self.pid,self.current,self.source)
        self.assertEqual(before,self.snapshot())
    def test_invalid_transcription_link_rejected(self):
        self.db.execute('UPDATE transcriptions SET source_hash=?',('wrong',))
        before=self.snapshot()
        with self.assertRaises(ValueError):self.app.split_story_by_speech(self.pid,self.current)
        self.assertEqual(before,self.snapshot())
    def test_split_reuses_timing_and_clears_old_description(self):
        with patch.object(self.app,'remote',side_effect=AssertionError('No API')),patch('coae.application.transcribe_and_build_storyboard',side_effect=AssertionError('No ASR')):
            result=self.app.split_story_by_speech(self.pid,self.current)
        _,scenes=self.app.story(self.pid)
        self.assertEqual([(s.start_time,s.end_time) for s in scenes],[(0,4.3),(4.3,16.1),(16.1,20)])
        self.assertTrue(all(s.visual_description=='' for s in scenes))
        self.assertEqual(result['audit']['decision'],'BLOCKED')
        self.assertEqual(self.db.one('SELECT COUNT(*) FROM transcriptions')[0],1)
        before=self.snapshot()
        again=self.app.split_story_by_speech(self.pid,result['version'])
        self.assertEqual(again['version'],result['version']);self.assertEqual(before,self.snapshot())
    def test_busy_project_rejected(self):
        self.db.execute("INSERT INTO jobs(project_id,action,status) VALUES(?,'describe','RUNNING')",(self.pid,))
        before=self.snapshot()
        with self.assertRaises(ValueError):self.app.restore_story(self.pid,self.current,self.source)
        self.assertEqual(before,self.snapshot())
    def test_history_counts_and_image_invalidation(self):
        current=self.app.story(self.pid)[0]
        self.db.execute("INSERT INTO images(project_id,storyboard_id,scene_id,path,sha256,status) VALUES(?,?,'SC001','fixture','fixture','APPROVED')",(self.pid,current['id']))
        self.app.restore_story(self.pid,self.current,self.source)
        self.assertEqual(self.db.one('SELECT status FROM images')[0],'STALE')
        state=self.app.state(self.pid)
        self.assertEqual(state['stories'][0]['scene_count'],3)
        self.assertEqual(state['stories'][1]['scene_count'],1)
