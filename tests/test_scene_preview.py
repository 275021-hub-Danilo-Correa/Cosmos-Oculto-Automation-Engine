import array
import json
import math
import shutil
import subprocess
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import test_regressions as regression
from coae.audio import file_sha256
from coae.scene_preview import frame_interval, render, probe
from coae.server import Server


class TimingTests(unittest.TestCase):
    def test_absolute_boundaries_do_not_accumulate_rounding(self):
        boundaries = [0, 7.38, 16.84, 20.055, 24.071, 30.014]
        intervals = [frame_interval(a, b, boundaries[-1]) for a, b in zip(boundaries, boundaries[1:])]
        self.assertEqual(intervals[0], (0, 221))
        self.assertTrue(all(a[1] == b[0] for a, b in zip(intervals, intervals[1:])))
        self.assertEqual(sum(b-a for a, b in intervals), intervals[-1][1])
        for start, end in ((-1, 1), (2, 1), (0, 21), (0, float('nan')), (0, .001)):
            with self.assertRaises(ValueError): frame_interval(start, end, 20)


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg necessário')
class PreviewTests(unittest.TestCase):
    def setUp(self):
        regression.ApplicationTests.setUp(self)
        regression.ApplicationTests.prepared(self)
        self.image = self.root / 'input.png'
        Image.new('RGB', (320, 180), 'navy').save(self.image)
        self.iid = self.app.import_image(self.pid, 'SC001', self.image)['image_id']

    def tearDown(self):
        regression.ApplicationTests.tearDown(self)

    def test_preview_preserves_originals_and_approval_and_creates_unique_files(self):
        before = self.app.state(self.pid)
        hashes = {p: file_sha256(Path(p)) for p in [before['images'][0]['path'], before['audios'][0]['original_path']]}
        self.db.execute("UPDATE images SET status='BLOCKED' WHERE id=?", (self.iid,))
        first = self.app.preview_scene(self.pid, self.iid)
        second = self.app.preview_scene(self.pid, self.iid)
        self.assertNotEqual(first['path'], second['path'])
        self.assertEqual(first['frame_count'], 129)
        self.assertAlmostEqual(first['duration'], 4.3)
        after = self.app.state(self.pid)
        self.assertEqual(after['scenes'], before['scenes'])
        self.assertEqual(after['stories'], before['stories'])
        self.assertEqual(after['images'][0]['status'], 'BLOCKED')
        self.assertEqual(len(after['previews']), 2)
        for path, sha in hashes.items():self.assertEqual(file_sha256(Path(path)), sha)
        clip = self.app.file(self.pid, first['path'])
        self.assertEqual(probe(clip)['streams'][0]['codec_name'], 'h264')
        metadata = json.loads(clip.with_suffix('.json').read_text(encoding='utf-8'))
        self.assertEqual(metadata['original_audio'], Path(before['audios'][0]['original_path']).relative_to(self.app.folder(self.pid)).as_posix())

    def test_changed_original_or_wrong_version_rejected(self):
        audio = self.app.audio(self.pid)
        Path(audio['original_path']).write_bytes(b'changed')
        with patch('coae.scene_preview.render') as encode:
            with self.assertRaisesRegex(ValueError, 'original alterado'):
                self.app.preview_scene(self.pid, self.iid)
            encode.assert_not_called()
        self.db.execute('UPDATE images SET storyboard_id=NULL WHERE id=?', (self.iid,))
        with self.assertRaisesRegex(ValueError, 'versão atual'):
            self.app.preview_scene(self.pid, self.iid)

    def test_nonzero_cut_keeps_audio_pitch_and_frame_precision(self):
        source = self.root / 'tones.wav'
        samples = array.array('h', [round(12000 * math.sin(2 * math.pi * (220 if n < 48000 else 880) * n / 48000)) for n in range(96000)])
        with wave.open(str(source), 'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(samples.tobytes())
        output = self.root / 'test.mp4'
        result = render(self.image, source, output, 1.123, 1.787, 2)
        self.assertEqual(result['frame_count'], 20)
        decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-vn', '-f', 's16le', '-ac', '1', '-ar', '48000', '-'], capture_output=True, check=True).stdout
        pcm = array.array('h');pcm.frombytes(decoded)
        # Ignore AAC edges; 880 Hz proves a nonzero cut and unchanged pitch/speed.
        middle = pcm[4800:24000]
        crossings = sum(a <= 0 < b for a, b in zip(middle, middle[1:]))
        self.assertAlmostEqual(crossings / (len(middle)/48000), 880, delta=5)
        self.assertLessEqual(abs(result['rendered_start'] - 1.123), 1/60)

    def test_encoder_failure_leaves_no_export_or_temp_media(self):
        with patch('coae.scene_preview.subprocess.run', side_effect=subprocess.TimeoutExpired('ffmpeg', 1800)):
            with self.assertRaisesRegex(ValueError, 'Falha técnica'):
                self.app.preview_scene(self.pid, self.iid)
        self.assertEqual(self.db.one("SELECT COUNT(*) FROM exports WHERE kind='scene_preview'")[0], 0)
        self.assertEqual(list(self.app.folder(self.pid).rglob('*.mp4')), [])

    def test_authenticated_http_generation_and_mp4_download(self):
        server = Server(('127.0.0.1', 0), self.app)
        thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        headers = {'X-COAE-Token': server.token, 'Content-Type': 'application/json'}
        try:
            body = json.dumps({'action': 'preview_scene', 'project': self.pid, 'image_id': self.iid}).encode()
            with urllib.request.urlopen(urllib.request.Request(base+'/api/action', data=body, headers=headers)) as r:
                jid = json.load(r)['job']
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                job = self.db.one('SELECT * FROM jobs WHERE id=?', (jid,))
                if job['status'] != 'RUNNING':break
                time.sleep(.05)
            self.assertEqual(job['status'], 'DONE', job['result'])
            path = json.loads(job['result'])['path']
            url = base+'/api/file?'+urllib.parse.urlencode({'project': self.pid, 'path': path})
            with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(url)
            self.assertEqual(error.exception.code, 401);error.exception.close()
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
                self.assertEqual(r.headers['Content-Type'], 'video/mp4')
                self.assertEqual(r.read(), self.app.file(self.pid, path).read_bytes())
        finally:
            server.shutdown();server.server_close();thread.join();server.temp.cleanup()
