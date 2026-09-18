import os
import unittest
from unittest.mock import patch

from coae.server import Server, Handler


class TokenTests(unittest.TestCase):
    def server(self):
        with patch('coae.server.ThreadingHTTPServer.__init__', return_value=None):
            server = Server(('127.0.0.1', 0), None)
        self.addCleanup(server.temp.cleanup)
        return server

    def test_fixed_token_survives_restart_and_authenticates(self):
        with patch.dict(os.environ, {'COAE_ACCESS_TOKEN': 'fixed-test_token-123'}):
            first, second = self.server(), self.server()
        self.assertEqual(first.token, 'fixed-test_token-123')
        self.assertEqual(first.token, second.token)
        handler = object.__new__(Handler)
        handler.server = second
        for value, expected in [(second.token, True), ('wrong', False), ('', False)]:
            handler.headers = {'X-COAE-Token': value}
            self.assertEqual(handler.auth(), expected)

    def test_missing_or_blank_uses_random_token(self):
        for value in (None, '', '   '):
            with self.subTest(value=value), patch.dict(os.environ, {}, clear=True):
                if value is not None:
                    os.environ['COAE_ACCESS_TOKEN'] = value
                first, second = self.server(), self.server()
                self.assertTrue(first.token)
                self.assertNotEqual(first.token, second.token)

    def test_invalid_token_is_rejected(self):
        for value in ('with space', 'a#b', 'á', 'a\nb'):
            with self.subTest(value=value), patch.dict(os.environ, {'COAE_ACCESS_TOKEN': value}):
                with self.assertRaisesRegex(ValueError, 'COAE_ACCESS_TOKEN'):
                    self.server()
