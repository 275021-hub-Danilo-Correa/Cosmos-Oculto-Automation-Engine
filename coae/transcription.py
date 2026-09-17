from __future__ import annotations
import json
import math
import os
from pathlib import Path
from typing import Protocol
from .errors import InvalidTranscriptError,ProviderNotConfiguredError
from .models import TranscriptSegment

class TranscriptionProvider(Protocol):
    name:str
    def transcribe(self,audio_path:str|Path)->list[TranscriptSegment]:...

def validate_segments(segments,duration=None):
    if not segments:raise InvalidTranscriptError('Transcrição vazia.')
    last=0
    for s in segments:
        if not math.isfinite(s.start) or not math.isfinite(s.end) or s.start<0 or s.end<=s.start or s.start<last-.001 or not s.text.strip():
            raise InvalidTranscriptError('Timestamps inválidos, sobrepostos ou texto vazio.')
        if duration is not None and s.end>duration+.025:raise InvalidTranscriptError('Transcrição ultrapassa a duração real do áudio.')
        last=s.end
    return segments

class JsonTranscriptProvider:
    name='json-aligned-transcript'
    def __init__(self,transcript_path):self.transcript_path=Path(transcript_path)
    def transcribe(self,audio_path):
        try:
            payload=json.loads(self.transcript_path.read_text(encoding='utf-8'))
            result=[TranscriptSegment(float(i['start']),float(i['end']),str(i['text']).strip()) for i in payload['segments']]
        except (OSError,KeyError,TypeError,ValueError,AttributeError) as exc:raise InvalidTranscriptError('Transcrição JSON inválida.') from exc
        return validate_segments(result)

class FasterWhisperProvider:
    name='faster-whisper-local'
    def transcribe(self,audio_path):
        try:from faster_whisper import WhisperModel
        except ImportError:raise ProviderNotConfiguredError('Instale requirements-audio.txt para transcrição automática local. Não há geração de voz.') from None
        model=WhisperModel(os.getenv('COAE_WHISPER_MODEL','small'),device='cpu',compute_type='int8')
        segments,_=model.transcribe(str(audio_path),language='pt',word_timestamps=True,vad_filter=True)
        words=[]
        for segment in segments:
            for w in segment.words or []:
                start=max(float(w.start),words[-1].end if words else 0)
                if w.word.strip() and w.end>start:words.append(TranscriptSegment(start,float(w.end),w.word.strip()))
        return validate_segments(words)

class UnconfiguredTranscriptionProvider:
    name='unconfigured'
    def transcribe(self,audio_path):raise ProviderNotConfiguredError('Provider de transcrição não configurado.')
