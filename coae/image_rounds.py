"""Persistent image variation rounds, serialized through one local GPU queue."""
from __future__ import annotations
import json
from pathlib import Path
import secrets
import threading
import time
import uuid

from .audio import file_sha256
from .local_ai import ComfyUI, backend
from .visual_style import CHANNEL_AUDIT_INSTRUCTION, CHANNEL_GENERATION_RULES, CHANNEL_NEGATIVE


GPU_QUEUE = threading.Lock()


def _write(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)


def _new_seed(db):
    for _ in range(100):
        seed=secrets.randbelow(2**63-1)
        if not db.one('SELECT id FROM image_candidates WHERE seed=?',(seed,)):return seed
    raise ValueError('Não foi possível reservar seeds distintas para a rodada.')


def create_round(app,pid,scene_id,count,reason=''):
    if backend('image')!='comfyui':raise ValueError('Rodadas de variações exigem o ComfyUI local.')
    if type(count) is not int or not 1<=count<=4:raise ValueError('Escolha entre 1 e 4 variações.')
    if not isinstance(reason,str) or len(reason)>2000:raise ValueError('Motivo de reprovação inválido.')
    story,scenes=app.story(pid,approved=True)
    scene=next((s for s in scenes if s.scene_id==scene_id),None)
    if scene is None:raise ValueError('Cena inexistente.')
    client=ComfyUI();meta=client.metadata();base=app.prompt(scene)
    prior=app.db.one('SELECT * FROM image_rounds WHERE storyboard_id=? AND scene_id=? ORDER BY round_number DESC LIMIT 1',(story['id'],scene_id))
    number=(prior['round_number'] if prior else 0)+1
    problems=[]
    if prior:
        for row in app.db.rows('SELECT image_id FROM image_candidates WHERE round_id=? AND image_id IS NOT NULL',(prior['id'],)):
            audit=app.db.one("SELECT report FROM audit_runs WHERE project_id=? AND kind='image' AND reference=? ORDER BY id DESC LIMIT 1",(pid,str(row['image_id'])))
            if audit:
                issues=json.loads(audit['report']).get('issues',[])
                problems.extend(i['message'] for i in issues if i.get('severity') in ('error','warning'))
    adjustment=''
    if reason.strip() or problems:
        adjustment=' Corrija nesta nova rodada, sem mudar a fala nem os tempos: '+reason.strip()
        if problems:adjustment+=' Problemas da auditoria anterior: '+' | '.join(problems[:10])
    prompt=base+adjustment
    with app.db.transaction():
        if prior:
            app.db.execute("UPDATE image_rounds SET status='REJECTED',completed_at=COALESCE(completed_at,CURRENT_TIMESTAMP) WHERE id=?",(prior['id'],))
            app.db.execute("UPDATE images SET status='REJECTED' WHERE id IN (SELECT image_id FROM image_candidates WHERE round_id=? AND image_id IS NOT NULL) AND status!='APPROVED'",(prior['id'],))
            app.db.event(pid,'IMAGE_ROUND_REJECTED',{'round_id':prior['id'],'reason':reason.strip() or 'Nenhum motivo informado.'})
        rid=app.db.execute('INSERT INTO image_rounds(project_id,storyboard_id,scene_id,round_number,requested,rejection_reason) VALUES(?,?,?,?,?,?)',(pid,story['id'],scene_id,number,count,reason.strip())).lastrowid
        for n in range(1,count+1):
            app.db.execute('INSERT INTO image_candidates(round_id,candidate_number,seed,prompt,workflow,model) VALUES(?,?,?,?,?,?)',(rid,n,_new_seed(app.db),prompt,meta['workflow'],meta['model']))
        app.db.event(pid,'IMAGE_ROUND_QUEUED',{'round_id':rid,'scene_id':scene_id,'round':number,'variations':count})
    return rid


def cancel_round(app,pid,round_id):
    row=app.db.one('SELECT * FROM image_rounds WHERE id=? AND project_id=?',(round_id,pid))
    if not row:raise ValueError('Rodada inexistente.')
    if row['status'] in ('DONE','FAILED','CANCELLED','REJECTED'):raise ValueError('Esta rodada já terminou.')
    app.db.execute('UPDATE image_rounds SET cancel_requested=1,status=? WHERE id=?',('CANCELLING',round_id))
    app.db.event(pid,'IMAGE_ROUND_CANCEL_REQUESTED',{'round_id':round_id})
    return {'message':'Cancelamento solicitado. Candidatas concluídas serão preservadas.'}


def _cancelled(app,rid):
    row=app.db.one('SELECT cancel_requested FROM image_rounds WHERE id=?',(rid,))
    return not row or bool(row['cancel_requested'])


def _candidate_update(app,cid,status,stage,progress=None,error=None,prompt_id=None,image_id=None,audit_id=None):
    app.db.execute('UPDATE image_candidates SET status=?,stage=?,progress=?,error=?,prompt_id=COALESCE(?,prompt_id),image_id=COALESCE(?,image_id),audit_id=COALESCE(?,audit_id),updated_at=CURRENT_TIMESTAMP WHERE id=?',(status,stage,progress,error,prompt_id,image_id,audit_id,cid))


def _plan_prompt(app,row,scene):
    previous=app.db.one('SELECT id FROM image_rounds WHERE storyboard_id=? AND scene_id=? AND round_number<? ORDER BY round_number DESC LIMIT 1',(row['storyboard_id'],row['scene_id'],row['round_number']))
    issues=[]
    if previous:
        for image in app.db.rows('SELECT image_id FROM image_candidates WHERE round_id=? AND image_id IS NOT NULL',(previous['id'],)):
            audit=app.db.one("SELECT report FROM audit_runs WHERE project_id=? AND kind='image' AND reference=? ORDER BY id DESC LIMIT 1",(row['project_id'],str(image['image_id'])))
            if audit:issues.extend(i['message'] for i in json.loads(audit['report']).get('issues',[]) if i.get('severity') in ('error','warning'))
    task=('Prepare um prompt curto para SDXL. Retorne JSON {positive_prompt,negative_prompt}. positive_prompt deve estar em inglês, '
          'ter no máximo 60 palavras, uma composição única e coerente, sem instruções conflitantes. negative_prompt deve ser '
          'uma lista em inglês com no máximo 35 termos. A fala e a ideia têm precedência sobre a descrição visual. Não inclua '
          'objetos presentes apenas na descrição. Para visual_function ESTABLISH, estabeleça assunto e atmosfera; não tente '
          'demonstrar todos os conceitos nem use diagrama/infográfico. Aplique literalmente as regras editoriais fornecidas.')
    value=app.remote(row['project_id'],'writer',task,{'speech':scene.transcript_reference,'intent':scene.semantic_summary,
        'visual_description_advisory':scene.visual_description,'visual_function':scene.visual_function,
        'correction':row['rejection_reason'],'previous_problems':issues[:8],
        'editorial_rules':CHANNEL_GENERATION_RULES,'avoid':CHANNEL_NEGATIVE})
    if not isinstance(value,dict):raise ValueError('Planejamento visual local devolveu estrutura inválida.')
    positive=value.get('positive_prompt');negative=value.get('negative_prompt')
    if isinstance(negative,list) and all(isinstance(x,str) for x in negative):negative=', '.join(negative)
    if not isinstance(positive,str) or not isinstance(negative,str) or not positive.strip():
        raise ValueError('Planejamento visual local devolveu prompts inválidos.')
    positive=' '.join((CHANNEL_GENERATION_RULES+', '+positive).split()[:60])
    intent=(scene.transcript_reference+' '+scene.semantic_summary).lower()
    terms=[x.strip() for x in (negative+','+CHANNEL_NEGATIVE).split(',') if x.strip()]
    if 'planet' not in intent:terms+=['planet','planetary body']
    unique=[]
    for term in terms:
        if term.lower() not in {x.lower() for x in unique}:unique.append(term)
    return positive.strip(),', '.join(unique[:45])


def _recommend(app,round_row,candidates):
    _story,scenes=app.story(round_row['project_id'],approved=True)
    scene=next(s for s in scenes if s.scene_id==round_row['scene_id'])
    choices=[]
    for candidate in candidates:
        if not candidate['image_id'] or candidate['status']!='DONE':continue
        audit=app.db.one("SELECT report FROM audit_runs WHERE project_id=? AND kind='image' AND reference=? ORDER BY id DESC LIMIT 1",(round_row['project_id'],str(candidate['image_id'])))
        if audit:choices.append({'candidate':candidate['candidate_number'],'image_id':candidate['image_id'],'audit':json.loads(audit['report'])})
    if not choices:return None,'Nenhuma candidata concluiu geração e auditoria; é necessária nova rodada.'
    eligible=[c for c in choices if not any(i.get('severity')=='error' for i in c['audit'].get('issues',[]))]
    if not eligible:return None,'Nenhuma candidata é adequada: todas têm problema bloqueante na auditoria.'
    task=('Compare as auditorias visuais de candidatas da mesma cena com a fala, intenção e função narrativa fornecidas. Considere correspondência, contradições, '
          'artefatos, realismo fotográfico e estilo do canal. Para ESTABLISH, avalie se a imagem estabelece visualmente o assunto e a atmosfera; '
          'não exija demonstração de todas as fases ou processos citados e nunca rejeite somente por essa ausência. Se nenhuma for adequada, explique os defeitos '
          'visíveis reais de cada candidata, em vez de exigir que a abertura ilustre todos os conceitos. Retorne JSON '
          '{recommended_candidate: inteiro ou null, summary: explicação em português com no máximo duas frases}. '
          'Recomendação não é aprovação humana.')
    value=app.remote(round_row['project_id'],'auditor',task,{
        'speech':scene.transcript_reference,'intent':scene.semantic_summary,'visual_function':scene.visual_function,
        'editorial_rules':CHANNEL_AUDIT_INSTRUCTION,'candidates':eligible})
    selected=value.get('recommended_candidate') if isinstance(value,dict) else None
    summary=value.get('summary') if isinstance(value,dict) else None
    valid={c['candidate'] for c in eligible}
    if selected is not None and (type(selected) is not int or selected not in valid):raise ValueError('A IA recomendou uma candidata inelegível.')
    if not isinstance(summary,str) or not summary.strip():raise ValueError('A IA não explicou a recomendação da rodada.')
    image_id=next((c['image_id'] for c in eligible if c['candidate']==selected),None)
    return image_id,summary.strip()


def process_round(app,round_id):
    row=app.db.one('SELECT * FROM image_rounds WHERE id=?',(round_id,))
    if not row:raise ValueError('Rodada inexistente.')
    if row['cancel_requested']:
        app.db.execute("UPDATE image_candidates SET status='CANCELLED',stage='Cancelada',updated_at=CURRENT_TIMESTAMP WHERE round_id=? AND status='QUEUED'",(round_id,))
        app.db.execute("UPDATE image_rounds SET status='CANCELLED',completed_at=CURRENT_TIMESTAMP WHERE id=?",(round_id,))
        return {'message':'Rodada cancelada antes de usar a GPU; candidatas concluídas foram preservadas.','round_id':round_id}
    pid=row['project_id'];client=ComfyUI();story,scenes=app.story(pid,approved=True)
    scene=next(s for s in scenes if s.scene_id==row['scene_id'])
    try:positive,negative=_plan_prompt(app,row,scene)
    except Exception:
        app.db.execute("UPDATE image_rounds SET status='FAILED',completed_at=CURRENT_TIMESTAMP WHERE id=?",(round_id,))
        raise
    app.db.execute('UPDATE image_candidates SET prompt=?,negative_prompt=?,updated_at=CURRENT_TIMESTAMP WHERE round_id=?',(positive,negative,round_id))
    while not GPU_QUEUE.acquire(timeout=.5):
        if _cancelled(app,round_id):
            app.db.execute("UPDATE image_rounds SET status='CANCELLED',completed_at=CURRENT_TIMESTAMP WHERE id=?",(round_id,))
            return {'message':'Rodada cancelada antes de usar a GPU.','round_id':round_id}
    try:
        app.db.execute("UPDATE image_rounds SET status='GENERATING' WHERE id=?",(round_id,))
        candidates=app.db.rows('SELECT * FROM image_candidates WHERE round_id=? ORDER BY candidate_number',(round_id,))
        for candidate in candidates:
            if candidate['status']=='DONE':continue
            if _cancelled(app,round_id):break
            cid=candidate['id'];number=candidate['candidate_number']
            ticket_path=app.folder(pid)/'logs'/'image_rounds'/f'round_{round_id}_candidate_{number}.json'
            ticket=json.loads(ticket_path.read_text(encoding='utf-8')) if ticket_path.exists() else None
            def persist(value):_write(ticket_path,value)
            preview_path=app.folder(pid)/'previews'/'live'/f'round_{round_id}_candidate_{number}.jpg'
            def progress(stage,value,prompt_id,preview=None):
                if preview:
                    try:
                        from PIL import Image
                        import io
                        with Image.open(io.BytesIO(preview)) as image:
                            output=io.BytesIO();image.convert('RGB').save(output,format='JPEG',quality=80)
                        preview_path.parent.mkdir(parents=True,exist_ok=True);preview_path.write_bytes(output.getvalue())
                        app.db.execute('UPDATE image_candidates SET preview_path=? WHERE id=?',(str(preview_path),cid))
                    except Exception:pass
                _candidate_update(app,cid,'GENERATING',stage,value,prompt_id=prompt_id)
            _candidate_update(app,cid,'GENERATING',f'Gerando variação {number} de {row["requested"]}')
            try:
                raw,usage=client.generate(candidate['prompt'],ticket,persist,seed=candidate['seed'],progress=progress,cancelled=lambda:_cancelled(app,round_id),negative_extra=candidate['negative_prompt'])
                temp=app.folder(pid)/'images'/('temp_'+uuid.uuid4().hex+'.png')
                try:
                    temp.parent.mkdir(exist_ok=True);temp.write_bytes(raw)
                    iid=app.import_image(pid,row['scene_id'],temp)['image_id']
                finally:temp.unlink(missing_ok=True)
                _candidate_update(app,cid,'AUDITING','Auditando imagem real',1.0,image_id=iid,prompt_id=usage.get('prompt_id'))
                try:
                    report=app.image_audit(pid,iid)
                except ValueError as exc:
                    _candidate_update(app,cid,'AUDIT_FAILED','Falha técnica na auditoria',1.0,error=str(exc),image_id=iid)
                    continue
                rejected=report.get('decision')=='BLOCKED'
                _candidate_update(app,cid,'REJECTED' if rejected else 'DONE','Reprovada' if rejected else 'Aguardando escolha',1.0,image_id=iid,audit_id=report.get('id'))
                app.db.event(pid,'IMAGE_CANDIDATE_DONE',{'round_id':round_id,'candidate':number,'image_id':iid,'seed':candidate['seed'],'prompt_id':usage.get('prompt_id')})
            except InterruptedError:
                _candidate_update(app,cid,'CANCELLED','Cancelada',None)
                break
            except Exception as exc:
                _candidate_update(app,cid,'FAILED','Falha técnica',None,error=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        fresh=app.db.rows('SELECT * FROM image_candidates WHERE round_id=? ORDER BY candidate_number',(round_id,))
        if _cancelled(app,round_id):
            app.db.execute("UPDATE image_candidates SET status='CANCELLED',stage='Cancelada',updated_at=CURRENT_TIMESTAMP WHERE round_id=? AND status='QUEUED'",(round_id,))
            app.db.execute("UPDATE image_rounds SET status='CANCELLED',completed_at=CURRENT_TIMESTAMP WHERE id=?",(round_id,))
            return {'message':'Rodada cancelada; candidatas concluídas foram preservadas.','round_id':round_id}
        try:
            image_id,summary=_recommend(app,row,[dict(c) for c in fresh])
            app.db.execute("UPDATE image_rounds SET status='DONE',recommendation_image_id=?,recommendation_summary=?,completed_at=CURRENT_TIMESTAMP WHERE id=?",(image_id,summary,round_id))
        except ValueError as exc:
            app.db.execute("UPDATE image_rounds SET status='FAILED',recommendation_summary=?,completed_at=CURRENT_TIMESTAMP WHERE id=?",('Falha técnica na recomendação: '+str(exc),round_id))
        app.db.event(pid,'IMAGE_ROUND_DONE',{'round_id':round_id,'recommended_image_id':image_id if 'image_id' in locals() else None})
        return {'message':'Rodada concluída. Compare as candidatas e registre sua escolha.','round_id':round_id}
    finally:GPU_QUEUE.release()
