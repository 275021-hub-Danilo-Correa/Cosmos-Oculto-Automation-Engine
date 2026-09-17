from __future__ import annotations
import json
import math
from dataclasses import asdict
from .models import Scene

def save_storyboard(database,project_id,scenes,audio_id=None,transcription_id=None):
    database.get_project(project_id)
    with database.transaction():
        version=database.one('SELECT COALESCE(MAX(version),0)+1 FROM storyboards WHERE project_id=?',(project_id,))[0]
        database.invalidate(project_id,'Nova versão de storyboard')
        database.execute('INSERT INTO storyboards(project_id,version,audio_id,transcription_id,status) VALUES(?,?,?,?,?)',(project_id,version,audio_id,transcription_id,'DRAFT' if audio_id else 'STALE'))
        for scene in scenes:database.save_scene(project_id,scene,version)
        database.event(project_id,'STORYBOARD_SAVED',{'version':version,'scenes':len(scenes)})
    return int(version)

def storyboard_json(scenes):return json.dumps([asdict(s)|{'duration':s.duration} for s in scenes],ensure_ascii=False,indent=2,allow_nan=False)

def audit_scenes(scenes,duration):
    issues=[];previous=0;seen=set()
    def add(code,text,severity='error'):issues.append({'code':code,'message':text,'severity':severity})
    if not scenes:add('EMPTY','Storyboard sem cenas.')
    for scene in scenes:
        if scene.scene_id in seen:add('ID','ID de cena repetido.')
        seen.add(scene.scene_id)
        if not all(math.isfinite(v) for v in (scene.start_time,scene.end_time)) or scene.start_time<0 or scene.end_time<=scene.start_time or scene.end_time>duration+.025:add('BOUNDS',f'{scene.scene_id}: intervalo fora do áudio.')
        if abs(scene.start_time-previous)>.025:add('COVERAGE',f'{scene.scene_id}: lacuna ou sobreposição na timeline.')
        if not scene.transcript_reference.strip():add('TEXT',f'{scene.scene_id}: falta o trecho narrado.')
        if not scene.visual_description.strip() or not scene.semantic_summary.strip():add('VISUAL',f'{scene.scene_id}: falta a ideia ou a descrição da imagem.')
        if not scene.visual_function.strip():add('FUNCTION',f'{scene.scene_id}: função visual vazia.')
        if scene.duration>30:add('LONG',f'{scene.scene_id}: cena longa; confira se contém mais de uma ideia.', 'warning')
        previous=scene.end_time
    if abs(previous-duration)>.025:add('END','A timeline não cobre até o fim do áudio.')
    add('TIMING_REVIEW','Ouça os cortes, confira reconhecimento de fala, correspondência visual e rigor científico.','review')
    return {'decision':'BLOCKED' if any(i['severity']=='error' for i in issues) else 'REVIEW_REQUIRED','issues':issues}
