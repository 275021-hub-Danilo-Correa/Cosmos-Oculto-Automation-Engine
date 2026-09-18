import io
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
import urllib.parse
import urllib.request

from coae.desktop import main, run_desktop
from coae.runtime import running_server, workspace_lock


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        env = patch.dict(os.environ, {'COAE_ACCESS_TOKEN': 'desktop-test-token'})
        env.start()
        self.addCleanup(env.stop)

    def test_desktop_serves_same_api_and_preserves_projects_on_restart(self):
        urls = []
        with patch('coae.desktop.importlib.import_module') as loader:
            view = loader.return_value
            def opened(title, url, **kwargs):
                urls.append(url)
                self.assertTrue(kwargs['confirm_close'])
            view.create_window.side_effect = opened
            def interact(**kwargs):
                url = urls[-1]
                base, fragment = url.split('#')
                token = urllib.parse.parse_qs(fragment)['token'][0]
                with urllib.request.urlopen(base) as r:
                    self.assertIn(b'html', r.read())
                request = urllib.request.Request(base+'api/action',
                    data=json.dumps({'action': 'create', 'title': 'Desktop test'}).encode(),
                    headers={'X-COAE-Token': token, 'Content-Type': 'application/json'})
                with urllib.request.urlopen(request) as r:
                    self.assertIn('project', json.load(r))
            view.start.side_effect = interact
            run_desktop(self.root, port=0)
            view.start.assert_called_once()
        # The listener is closed and the workspace lock released when the window exits.
        port = urllib.parse.urlparse(urls[0]).port
        with socket.socket() as connection:
            self.assertNotEqual(connection.connect_ex(('127.0.0.1', port)), 0)
        with running_server(self.root, port=0) as server:
            self.assertEqual(server.app.db.one('SELECT title FROM projects')['title'], 'Desktop test')

    def test_gui_failure_releases_workspace_and_port(self):
        with patch('coae.desktop.importlib.import_module') as loader:
            loader.return_value.start.side_effect = RuntimeError('no display')
            with self.assertRaisesRegex(RuntimeError, 'no display'):
                run_desktop(self.root, port=0)
        with running_server(self.root, port=0):
            pass

    def test_missing_dependency_does_not_create_database(self):
        with patch('coae.desktop.importlib.import_module', side_effect=ImportError):
            with self.assertRaisesRegex(RuntimeError, 'INSTALAR_DESKTOP'):
                run_desktop(self.root)
        self.assertFalse((self.root/'data').exists())

    def test_same_workspace_is_rejected_before_opening_application(self):
        with workspace_lock(self.root), patch('coae.runtime.Application') as app:
            with self.assertRaisesRegex(RuntimeError, 'já está aberto'):
                with running_server(self.root, port=0):
                    pass
            app.assert_not_called()
        with workspace_lock(self.root):
            pass

    def test_occupied_port_does_not_touch_database(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            listener.listen()
            with patch('coae.runtime.Application') as app:
                with self.assertRaises(OSError):
                    with running_server(self.root, port=listener.getsockname()[1]):
                        pass
                app.assert_not_called()
        with workspace_lock(self.root):
            pass

    def test_startup_failure_releases_lock(self):
        with patch('coae.runtime.Application', side_effect=ValueError('invalid workspace')):
            with self.assertRaisesRegex(ValueError, 'invalid workspace'):
                with running_server(self.root, port=0):
                    pass
        with running_server(self.root, port=0):
            pass

    def test_cli_reports_failure(self):
        with patch('coae.desktop.load_env'), patch('coae.desktop.run_desktop', side_effect=RuntimeError('no display')), patch('sys.stderr', new_callable=io.StringIO) as output:
            self.assertEqual(main(['--workspace', str(self.root)]), 1)
            self.assertIn('no display', output.getvalue())
