from __future__ import annotations
import json
from pathlib import Path
from .audio import verified_audio,file_sha256
from .segmentation import segment_scenes
from .storyboard import save_storyboard
from .transcription import validate_segments

def transcribe_and_build_storyboard(database,project_id,audio_id,audio_path=None,audio_duration=None,provider=None):
    from .transcription import FasterWhisperProvider
    row=verified_audio(database,project_id,audio_id)
    if audio_duration is not None and abs(audio_duration-row['duration'])>.025:raise ValueError('Duração informada diverge do áudio medido.')
    if audio_path is not None:
        path=Path(audio_path)
        if not path.is_file() or file_sha256(path)!=row['sha256']:raise ValueError('Arquivo fornecido não corresponde ao áudio cadastrado.')
    provider=provider or FasterWhisperProvider()
    segments=provider.transcribe(row['working_path'])
    validate_segments(segments,row['duration'])
    # Recheck in case input was changed while recognition was running.
    verified_audio(database,project_id,audio_id)
    payload=json.dumps([s.__dict__ for s in segments],ensure_ascii=False,allow_nan=False)
    scenes=segment_scenes(segments,row['duration'])
    with database.transaction():
        cursor=database.execute('INSERT INTO transcriptions(project_id,audio_id,provider,source_hash,payload) VALUES(?,?,?,?,?)',(project_id,audio_id,provider.name,row['sha256'],payload))
        save_storyboard(database,project_id,scenes,audio_id,cursor.lastrowid)
    return scenes
