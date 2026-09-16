from __future__ import annotations

import json
import tempfile
import unittest
import wave
from pathlib import Path

from coae.audio import import_audio
from coae.models import TranscriptSegment
from coae.pipeline import transcribe_and_build_storyboard
from coae.script_service import approve_script, export_script, save_script
from coae.segmentation import segment_scenes
from coae.storage import Database
from coae.transcription import JsonTranscriptProvider


class CoreWorkflowTests(unittest.TestCase):
    def test_script_exports_are_distinct_and_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = Database(root / "coae.sqlite3")
            database.create_project("COAE-TEST", "Buracos negros")
            version = save_script(database, "COAE-TEST", "Buracos negros", "Primeiro parágrafo.\n\nSegundo parágrafo.")
            with self.assertRaises(Exception):
                export_script(database, "COAE-TEST", None, None, root / "exports")
            approve_script(database, "COAE-TEST", version)
            files = export_script(database, "COAE-TEST", None, None, root / "exports")
            self.assertIn('<break time="1.5s"/>', files["narration_darkplanner"].read_text())
            self.assertNotIn("<break", files["narration_clean"].read_text())
            self.assertEqual(database.connection.execute("SELECT COUNT(*) FROM scripts").fetchone()[0], 1)

    def test_project_and_script_state_can_be_reopened(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "coae.sqlite3"
            first = Database(database_path)
            first.create_project("COAE-REOPEN", "Projeto retomável")
            save_script(first, "COAE-REOPEN", "Roteiro", "Versão inicial")
            first.close()
            reopened = Database(database_path)
            project = reopened.get_project("COAE-REOPEN")
            script = reopened.connection.execute("SELECT body, approved FROM scripts WHERE project_id = ?", (project["id"],)).fetchone()
            self.assertEqual(script["body"], "Versão inicial")
            self.assertEqual(script["approved"], 0)

    def test_only_approved_script_version_is_exported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = Database(root / "coae.sqlite3")
            database.create_project("COAE-VERSIONS", "Versionamento")
            first = save_script(database, "COAE-VERSIONS", "Roteiro", "Versão um")
            second = save_script(database, "COAE-VERSIONS", "Roteiro", "Versão dois")
            approve_script(database, "COAE-VERSIONS", second)
            rows = database.connection.execute(
                "SELECT version, approved FROM scripts WHERE project_id = ? ORDER BY version", ("COAE-VERSIONS",)
            ).fetchall()
            self.assertEqual(first, 1)
            self.assertEqual(second, 2)
            self.assertEqual([(row["version"], row["approved"]) for row in rows], [(1, 0), (2, 1)])
            files = export_script(database, "COAE-VERSIONS", None, None, root / "exports")
            self.assertIn("Versão dois", files["narration_clean"].read_text(encoding="utf-8"))

    def test_wav_import_preserves_original_and_measures_duration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "narration.wav"
            with wave.open(str(source), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(8000)
                audio.writeframes(b"\0\0" * 8000)
            database = Database(root / "coae.sqlite3")
            database.create_project("COAE-TEST", "Teste")
            audio_id = import_audio(database, "COAE-TEST", source, root / "project")
            row = database.connection.execute("SELECT * FROM audio_files WHERE id = ?", (audio_id,)).fetchone()
            self.assertAlmostEqual(row["duration"], 1.0)
            self.assertTrue(Path(row["original_path"]).exists())
            self.assertTrue(Path(row["working_path"]).exists())

    def test_transcription_to_storyboard_uses_real_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transcript = root / "transcript.json"
            transcript.write_text(json.dumps({"segments": [{"start": 0.0, "end": 2.4, "text": "Uma estrela colapsa."}, {"start": 2.4, "end": 7.1, "text": "A luz deixa de escapar."}]}), encoding="utf-8")
            segments = JsonTranscriptProvider(transcript).transcribe(root / "audio.wav")
            scenes = segment_scenes(segments, 7.1)
            self.assertAlmostEqual(scenes[0].duration, 2.4)
            self.assertAlmostEqual(scenes[1].duration, 4.7)
            database = Database(root / "coae.sqlite3")
            database.create_project("COAE-TEST", "Teste")
            audio_id = database.execute(
                "INSERT INTO audio_files (project_id, original_path, working_path, format, duration, sha256) VALUES (?, ?, ?, ?, ?, ?)",
                ("COAE-TEST", "original.wav", "working.wav", "wav", 7.1, "hash"),
            ).lastrowid
            transcribe_and_build_storyboard(database, "COAE-TEST", audio_id, root / "audio.wav", 7.1, JsonTranscriptProvider(transcript))
            self.assertEqual(database.connection.execute("SELECT COUNT(*) FROM transcriptions").fetchone()[0], 1)
            self.assertEqual(database.connection.execute("SELECT COUNT(*) FROM scenes").fetchone()[0], 2)

    def test_scene_bounds_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            segment_scenes([TranscriptSegment(0, 9, "fora")], 8)


if __name__ == "__main__":
    unittest.main()