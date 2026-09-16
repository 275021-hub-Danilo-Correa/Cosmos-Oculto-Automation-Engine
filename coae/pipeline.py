from __future__ import annotations

import json
from pathlib import Path

from .models import TranscriptSegment
from .segmentation import segment_scenes
from .storage import Database
from .storyboard import save_storyboard
from .transcription import TranscriptionProvider


def transcribe_and_build_storyboard(
    database: Database,
    project_id: str,
    audio_id: int,
    audio_path: str | Path,
    audio_duration: float,
    provider: TranscriptionProvider,
) -> list:
    segments = provider.transcribe(audio_path)
    payload = json.dumps([segment.__dict__ for segment in segments], ensure_ascii=False)
    audio_row = database.connection.execute("SELECT sha256 FROM audio_files WHERE id = ?", (audio_id,)).fetchone()
    if audio_row is None:
        raise ValueError(f"Áudio inexistente: {audio_id}")
    database.execute(
        "INSERT INTO transcriptions (project_id, audio_id, provider, source_hash, payload) VALUES (?, ?, ?, ?, ?)",
        (project_id, audio_id, provider.name, audio_row["sha256"], payload),
    )
    scenes = segment_scenes(segments, audio_duration)
    save_storyboard(database, project_id, scenes)
    return scenes