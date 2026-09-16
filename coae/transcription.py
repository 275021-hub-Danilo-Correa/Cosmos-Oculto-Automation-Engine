from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .errors import InvalidTranscriptError, ProviderNotConfiguredError
from .models import TranscriptSegment


class TranscriptionProvider(Protocol):
    name: str

    def transcribe(self, audio_path: str | Path) -> list[TranscriptSegment]:
        ...


class JsonTranscriptProvider:
    name = "json-aligned-transcript"

    def __init__(self, transcript_path: str | Path):
        self.transcript_path = Path(transcript_path)

    def transcribe(self, audio_path: str | Path) -> list[TranscriptSegment]:
        del audio_path
        try:
            payload = json.loads(self.transcript_path.read_text(encoding="utf-8"))
            segments = payload["segments"]
            result = [TranscriptSegment(float(item["start"]), float(item["end"]), item["text"].strip()) for item in segments]
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise InvalidTranscriptError("Transcrição alinhada inválida") from exc
        if not result or any(segment.end <= segment.start or not segment.text for segment in result):
            raise InvalidTranscriptError("Cada segmento precisa ter texto e end > start")
        return result


class UnconfiguredTranscriptionProvider:
    name = "unconfigured"

    def transcribe(self, audio_path: str | Path) -> list[TranscriptSegment]:
        del audio_path
        raise ProviderNotConfiguredError(
            "Nenhum provider de transcrição foi configurado; instale/configure um provider local ou externo"
        )