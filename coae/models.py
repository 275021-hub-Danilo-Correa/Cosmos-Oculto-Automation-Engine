from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TranscriptSegment:
    start:float
    end:float
    text:str
    @property
    def duration(self):return self.end-self.start

@dataclass(frozen=True)
class Scene:
    scene_id:str
    start_time:float
    end_time:float
    transcript_reference:str
    semantic_summary:str
    visual_description:str
    visual_function:str='EXPLAIN'
    camera_direction:str='STATIC'
    movement:str='STATIC'
    transition:str='NONE'
    continuity_reference:str|None=None
    generation_status:str='PENDING'
    audit_status:str='PENDING'
    first_segment:int=0
    last_segment:int=0
    speech_start:float=0
    speech_end:float=0
    @property
    def duration(self):return self.end_time-self.start_time
