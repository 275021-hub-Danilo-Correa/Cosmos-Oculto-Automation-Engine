import json
from pathlib import Path
import tempfile
import unittest
import urllib.request

from coae.runtime import running_server
from coae.script_service import format_dark_planner, save_script


class ScriptFormatTests(unittest.TestCase):
    def test_normalizes_whitespace_and_preserves_pauses(self):
        draft = '  Texto.  \r\n\r\n\r\nOutra fala. <break time="1.5s"/>  \r\n'
        result = format_dark_planner(draft)
        self.assertEqual(result, 'Texto.\n\nOutra fala. <break time="1.5s"/>')
        self.assertEqual(format_dark_planner(result), result)

    def test_rejects_invalid_narration_without_inventing_content(self):
        for draft in ('', '# Título\nTexto', '<break time="8s"/>', '<script>texto</script>'):
            with self.subTest(draft=draft), self.assertRaises(ValueError):
                format_dark_planner(draft)

    def test_groups_narration_at_transitions_without_pausing_every_sentence(self):
        draft = ('Observamos estrelas. Tudo começa em uma nuvem. A gravidade concentra gás. '
                 'Nasce uma estrela. Mas sua massa determina seu destino.')
        result = format_dark_planner(draft)
        self.assertIn('Observamos estrelas. <break time="1.5s"/>\n\nTudo começa', result)
        self.assertIn('nuvem. A gravidade', result)
        self.assertIn('estrela. <break time="2s"/>\n\nMas', result)
        self.assertEqual(format_dark_planner(result), result)
        import re
        self.assertEqual(re.sub(r'\s+', ' ', re.sub(r'<break[^>]+/>', '', result)).strip(), draft)

    def test_questions_decimals_and_abbreviations(self):
        result = format_dark_planner('O Dr. Silva mede 1.5 metros. Por quê? Agora seguimos.')
        self.assertIn('Dr. Silva mede 1.5 metros. Por quê? <break time="2s"/>', result)
        self.assertIn('\n\nAgora seguimos.', result)

    def test_http_formats_unsaved_draft_without_approval_or_database_changes(self):
        with tempfile.TemporaryDirectory() as folder, running_server(folder, port=0) as server:
            app = server.app
            pid = app.create('Teste')['project']
            save_script(app.db, pid, 'Teste', 'Texto salvo.')
            before = app.db.connection.total_changes
            request = urllib.request.Request(
                f'http://127.0.0.1:{server.server_port}/api/action',
                data=json.dumps({'action': 'format_dark_planner', 'project': pid,
                                 'body': '  Rascunho ainda não salvo.  '}).encode(),
                headers={'X-COAE-Token': server.token, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(request) as response:
                self.assertEqual(json.load(response)['body'], 'Rascunho ainda não salvo. <break time="1.5s"/>')
            self.assertEqual(app.db.connection.total_changes, before)
            self.assertEqual(app.script(pid)['body'], 'Texto salvo.')
            self.assertFalse(app.script(pid)['approved'])
            self.assertFalse(list(Path(folder).rglob('narration_darkplanner.txt')))
