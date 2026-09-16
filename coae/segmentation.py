from __future__ import annotations

import re

from .models import Scene, TranscriptSegment


def _summary(text: str) -> str:
    words = re.findall(r"[\wÀ-ÿ]+", text.lower())
    return " ".join(words[:12])


def segment_scenes(segments: list[TranscriptSegment], audio_duration: float) -> list[Scene]:
    if not segments:
        return []
    scenes: list[Scene] = []
    for index, segment in enumerate(segments, 1):
        if segment.start < 0 or segment.end > audio_duration or segment.end <= segment.start:
            raise ValueError("Segmento fora dos limites do áudio")
        text = segment.text.strip()
        scenes.append(
            Scene(
                scene_id=f"SC{index:03d}",
                start_time=segment.start,
                end_time=segment.end,
                transcript_reference=text,
                semantic_summary=_summary(text),
                visual_description=f"Visual documental para: {_summary(text)}",
                visual_function="ESTABLISH" if index == 1 else "EXPLAIN",
                continuity_reference=f"SC{index - 1:03d}" if index > 1 else None,
            )
        )
    for previous, current in zip(scenes, scenes[1:]):
        if current.start_time < previous.end_time:
            raise ValueError("Cenas sobrepostas")
    return scenes