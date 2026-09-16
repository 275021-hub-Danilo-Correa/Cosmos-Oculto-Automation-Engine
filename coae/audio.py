from __future__ import annotations

import hashlib
import shutil
import wave
from pathlib import Path

from .errors import UnsupportedAudioError
from .storage import Database


SUPPORTED_FORMATS = {".mp3", ".wav", ".m4a"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as source:
        frame_rate = source.getframerate()
        if frame_rate <= 0:
            raise UnsupportedAudioError("WAV sem taxa de amostragem válida")
        return source.getnframes() / frame_rate


def import_audio(database: Database, project_id: str, source_path: str | Path, project_dir: str | Path) -> int:
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    extension = source.suffix.lower()
    if extension not in SUPPORTED_FORMATS:
        raise UnsupportedAudioError(f"Formato não suportado: {extension or '<sem extensão>'}")
    if extension != ".wav":
        raise UnsupportedAudioError(
            "FFmpeg é necessário para medir e normalizar MP3/M4A; instale-o antes da importação"
        )
    duration = wav_duration(source)
    if duration <= 0:
        raise UnsupportedAudioError("O áudio precisa ter duração positiva")
    project_audio = Path(project_dir) / "audio"
    original_dir = project_audio / "originals"
    working_dir = project_audio / "working"
    original_dir.mkdir(parents=True, exist_ok=True)
    working_dir.mkdir(parents=True, exist_ok=True)
    original = original_dir / source.name
    working = working_dir / source.name
    shutil.copy2(source, original)
    shutil.copy2(source, working)
    cursor = database.execute(
        "INSERT INTO audio_files (project_id, original_path, working_path, format, duration, sha256) VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, str(original), str(working), extension[1:], duration, file_sha256(source)),
    )
    return int(cursor.lastrowid)