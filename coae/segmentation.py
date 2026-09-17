from __future__ import annotations
import math
import re
from .models import Scene,TranscriptSegment
from .transcription import validate_segments

def sentence_boundaries(segments):
    ends=[]
    for i,s in enumerate(segments):
        last=i==len(segments)-1
        pause=not last and segments[i+1].start-s.end>=.65
        if last or pause or re.search(r'[.!?…][\"\u201d\u2019\')\]]*$',s.text.strip()):ends.append(i)
    return ends

def segment_scenes(segments:list[TranscriptSegment],audio_duration:float,boundaries=None)->list[Scene]:
    if not math.isfinite(audio_duration) or audio_duration<=0:raise ValueError('Duração inválida.')
    validate_segments(segments,audio_duration)
    ends=sentence_boundaries(segments) if boundaries is None else boundaries
    if not isinstance(ends,list) or not ends or any(type(i)is not int for i in ends) or ends[0]<0 or ends[-1]!=len(segments)-1 or any(b<=a for a,b in zip(ends,ends[1:])):raise ValueError('Grupos precisam cobrir todos os segmentos uma única vez, em ordem.')
    scenes=[];first=0
    for index,last in enumerate(ends,1):
        start=0 if index==1 else segments[first].start
        end=audio_duration if last==len(segments)-1 else segments[last+1].start
        text=' '.join(s.text.strip() for s in segments[first:last+1])
        scenes.append(Scene(scene_id=f'SC{index:03d}',start_time=start,end_time=end,transcript_reference=text,
                            semantic_summary='',visual_description='',visual_function='ESTABLISH' if index==1 else 'EXPLAIN',
                            continuity_reference=f'SC{index-1:03d}' if index>1 else None,first_segment=first,last_segment=last,
                            speech_start=segments[first].start,speech_end=segments[last].end))
        first=last+1
    return scenes
