from __future__ import annotations
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import threading
import uuid
import zipfile
from dataclasses import asdict,fields,replace
from .errors import CoaeError
from .audio import import_audio,verified_audio,file_sha256
from .models import Scene,TranscriptSegment
from .pipeline import transcribe_and_build_storyboard
from .script_service import save_script,approve_script,export_script,validate_narration,clean_narration
from .segmentation import segment_scenes
from .storage import Database
from .storyboard import audit_scenes,save_storyboard,storyboard_json
from .transcription import JsonTranscriptProvider

FOLDERS=('research','script','audio','transcription','storyboard','images','motion','timeline','subtitles','seo','exports','audits','logs')

def dump(value):return json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)

def atomic(path,content):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temp.write_bytes(content if isinstance(content,bytes) else content.encode('utf-8'));os.replace(temp,path)
    finally:temp.unlink(missing_ok=True)

class Application:
    def __init__(self,root):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.db=Database(self.root/'data'/'coae.sqlite3')
        self._normalize_legacy_paths()
        self.db.execute("UPDATE jobs SET status='INTERRUPTED',result=? WHERE status='RUNNING'",(dump({'message':'Aplicação interrompida; resultados preservados. Revise chamadas remotas antes de continuar.'}),))
        self.db.execute("UPDATE api_calls SET status='UNKNOWN_REMOTE_RESULT' WHERE status='RUNNING'")
    def _normalize_legacy_paths(self):
        # The original CLI stored paths relative to its workspace.
        with self.db.transaction():
            for table,columns in (('audio_files',('original_path','working_path')),('exports',('path',))):
                for row in self.db.rows(f'SELECT * FROM {table}'):
                    for column in columns:
                        path=Path(row[column])
                        if not path.is_absolute():
                            candidate=(self.root/path).resolve()
                            if candidate.is_relative_to(self.root):
                                self.db.execute(f'UPDATE {table} SET {column}=? WHERE id=?',(str(candidate),row['id']))

    def folder(self,pid):
        p=self.db.get_project(pid)
        target=Path(p['root_path']).resolve() if p['root_path'] else (self.root/'projects'/pid).resolve()
        if not target.is_relative_to(self.root):raise ValueError('Projeto fora da pasta de trabalho. Migre os arquivos primeiro.')
        return target
    def create(self,title):
        pid='COAE-'+uuid.uuid4().hex[:8].upper();self.db.create_project(pid,title)
        root=self.folder(pid)
        for folder in FOLDERS:(root/folder).mkdir(parents=True,exist_ok=True)
        self.db.execute('UPDATE projects SET root_path=? WHERE id=?',(str(root),pid))
        self.db.event(pid,'PROJECT_CREATED',{})
        return {'project':pid}
    def script(self,pid,approved=False):
        clause=' AND approved=1' if approved else ''
        row=self.db.one('SELECT * FROM scripts WHERE project_id=?'+clause+' ORDER BY version DESC LIMIT 1',(pid,))
        if row is None:raise ValueError('Salve e aprove o roteiro primeiro.' if approved else 'Salve um roteiro primeiro.')
        return row
    def audio(self,pid):
        row=self.db.one('SELECT * FROM audio_files WHERE project_id=? ORDER BY id DESC LIMIT 1',(pid,))
        if row is None:raise ValueError('Importe a narração do Dark Planner.')
        return verified_audio(self.db,pid,row['id'])
    def story(self,pid,approved=False):
        row=self.db.one('SELECT * FROM storyboards WHERE project_id=? ORDER BY version DESC LIMIT 1',(pid,))
        if not row:raise ValueError('Analise o áudio para criar o storyboard.')
        if row['status']=='STALE':raise ValueError('Storyboard desatualizado. Analise o áudio atual novamente.')
        verified_audio(self.db,pid,row['audio_id'])
        if approved and row['status']!='APPROVED':raise ValueError('Revise e aprove o storyboard antes de gerar imagens.')
        scenes=[Scene(**json.loads(r['payload'])) for r in self.db.rows('SELECT payload FROM scenes WHERE project_id=? AND storyboard_version=? ORDER BY start_time,scene_id',(pid,row['version']))]
        return row,scenes
    def store_audit(self,pid,kind,ref,issues):
        report={'decision':'BLOCKED' if any(i['severity']=='error' for i in issues) else 'REVIEW_REQUIRED','issues':issues}
        self.db.execute('INSERT INTO audit_runs(project_id,kind,reference,report) VALUES(?,?,?,?)',(pid,kind,str(ref),dump(report)))
        atomic(self.folder(pid)/'audits'/f'{kind}_{ref}_{uuid.uuid4().hex[:8]}.json',dump(report))
        return report
    @staticmethod
    def remote_issues(value):
        if not isinstance(value,dict) or not isinstance(value.get('issues'),list):raise ValueError('Auditor devolveu estrutura inválida; nenhuma aprovação concedida.')
        for i in value['issues']:
            if not isinstance(i,dict) or i.get('severity') not in ('error','review','warning') or not all(isinstance(i.get(k),str) for k in ('code','message')):raise ValueError('Critério de auditoria inválido.')
        return value['issues']
    def source_text(self,pid):
        file=self.folder(pid)/'research'/'sources.txt'
        return file.read_text(encoding='utf-8') if file.exists() else ''
    def save_sources(self,pid,text):
        if len(text)>100000:raise ValueError('Use até 100 mil caracteres de referências/trechos.')
        old=self.source_text(pid)
        atomic(self.folder(pid)/'research'/'sources.txt',text)
        if text!=old:
            self.db.execute('UPDATE scripts SET approved=0 WHERE project_id=?',(pid,))
            self.db.execute("UPDATE audio_files SET status='STALE' WHERE project_id=?",(pid,))
            self.db.invalidate(pid,'Referências alteradas; revisar ciência e roteiro')
        return {'message':'Referências salvas. Alterações exigem reaprovação do roteiro.'}
    def audit_script(self,pid,remote=False):
        row=self.script(pid);issues=[]
        try:validate_narration(row['body'])
        except ValueError as exc:issues.append({'code':'NARRATION','severity':'error','message':str(exc)})
        if not self.source_text(pid).strip():issues.append({'code':'SOURCES','severity':'review','message':'Cadastre e confira as fontes científicas. Não há pesquisa automática nesta versão.'})
        issues.append({'code':'EDITORIAL','severity':'review','message':'Confira ciência, promessa, progressão, pronúncias e encerramento.'})
        if remote:
            value=self.remote(pid,'auditor','Audite o roteiro: afirmações, evidências fornecidas, hipóteses, clareza, progressão, repetições e gancho. Não afirme que URLs foram verificadas. Retorne {issues:[{code,message,severity:"error|review|warning"}]}.',{'script':dict(row),'evidence':self.source_text(pid)})
            issues+=self.remote_issues(value)
        if any(i['severity']=='error' for i in issues) and row['approved']:
            self.db.execute('UPDATE scripts SET approved=0 WHERE id=?',(row['id'],))
            self.db.execute("UPDATE audio_files SET status='STALE' WHERE project_id=?",(pid,))
            self.db.invalidate(pid,'Auditoria encontrou erro bloqueante no roteiro aprovado')
        return self.store_audit(pid,'script',row['id'],issues)
    def approve_script(self,pid,version,note):
        row=self.script(pid)
        if row['version']!=version:raise ValueError('A versão mudou; revise o roteiro atual.')
        report=self.db.one("SELECT report FROM audit_runs WHERE project_id=? AND kind='script' AND reference=? ORDER BY id DESC LIMIT 1",(pid,str(row['id'])))
        if not report:raise ValueError('Audite o roteiro antes de aprovar.')
        if any(i['severity']=='error' for i in json.loads(report['report'])['issues']):raise ValueError('Corrija os erros apontados e audite novamente.')
        self.note(note);approve_script(self.db,pid,version);self.db.event(pid,'EDITORIAL_REVIEW',{'version':version,'note':note})
        return {'message':'Roteiro aprovado. Exporte o texto para gerar a voz no Dark Planner.'}
    @staticmethod
    def note(note):
        if not isinstance(note,str) or len(note.strip())<10:raise ValueError('Descreva sua revisão em pelo menos 10 caracteres.')
    def repair_script(self,pid):
        steps=[]
        for attempt in range(4):
            report=self.audit_script(pid,remote=True);row=self.script(pid);steps.append(report['decision'])
            errors=[i for i in report['issues'] if i['severity']=='error']
            if not errors or attempt==3:break
            value=self.remote(pid,'writer','Corrija apenas os defeitos indicados. Não invente evidências. Preserve pausas válidas e intenção. Retorne {title,body}; body é só narração pt-BR e break.',{'script':dict(row),'errors':errors,'sources':self.source_text(pid)})
            if not isinstance(value,dict) or not all(isinstance(value.get(k),str) for k in ('title','body')):raise ValueError('Correção inválida da IA.')
            if value['title']==row['title'] and value['body'].strip()==row['body']:break
            save_script(self.db,pid,value['title'],value['body'])
        return {'message':'Ciclo de autoauditoria concluído; consulte pendências.','steps':steps}
    def generate_script(self,pid):
        if not self.source_text(pid).strip():raise ValueError('Cadastre referências antes de gerar o roteiro.')
        value=self.remote(pid,'writer','Escreva roteiro documental científico em pt-BR sobre o tema. Use apenas evidências fornecidas; marque hipóteses. Progresso narrativo e gancho final. Texto para cerca de 20–25 minutos a 135 palavras/minuto, sem repetir para preencher. Retorne {title,body}; body somente conteúdo narrável e pausas break em segundos até 3s. Sem cabeçalhos Markdown.',{'topic':self.db.get_project(pid)['title'],'sources':self.source_text(pid)})
        if not isinstance(value,dict) or not all(isinstance(value.get(k),str) for k in ('title','body')):raise ValueError('Roteiro inválido da IA.')
        save_script(self.db,pid,value['title'],value['body'])
        return self.repair_script(pid)
    def import_audio(self,pid,path):
        self.script(pid,approved=True)
        aid=import_audio(self.db,pid,path,self.folder(pid))
        return {'audio_id':aid,'message':'Áudio preservado. Ouça e aprove para iniciar a análise.'}
    def approve_audio(self,pid,audio_id,note):
        row=self.audio(pid)
        if row['id']!=audio_id:raise ValueError('O áudio mudou. Ouça a versão atual.')
        self.note(note)
        self.db.execute("UPDATE audio_files SET status='APPROVED' WHERE id=?",(audio_id,));self.db.event(pid,'AUDIO_APPROVED',{'audio_id':audio_id,'note':note})
        return {'message':'Áudio aprovado. Use Analisar áudio e criar cenas.'}
    def preflight_gemini(self,pid):
        self.db.get_project(pid)
        required=('GEMINI_API_KEY','COAE_WRITER_MODEL','COAE_AUDITOR_MODEL')
        missing=[name for name in required if not os.getenv(name,'').strip()]
        if missing:
            raise ValueError('Antes de usar Gemini, configure '+', '.join(missing)+' no .env e reinicie o programa. Você também pode desmarcar Gemini para análise local.')
        try:
            limit=int(os.getenv('COAE_MAX_CALLS_PER_PROJECT','0'))
        except ValueError:
            raise ValueError('COAE_MAX_CALLS_PER_PROJECT deve ser um número inteiro positivo.') from None
        used=self.db.one('SELECT COUNT(*) FROM api_calls WHERE project_id=?',(pid,))[0]
        if limit<=0 or used>=limit:
            raise ValueError('Gemini sem chamadas disponíveis: confira COAE_MAX_CALLS_PER_PROJECT no .env e reinicie. O teto é por projeto, não monetário.')
        from .provider import Gemini
        client=Gemini()
        client.close()

    def preflight_analysis(self,pid,semantic=False):
        row=self.audio(pid)
        if row['status']!='APPROVED':raise ValueError('Ouça e aprove o áudio primeiro.')
        if semantic:self.preflight_gemini(pid)
        return row

    def analyze(self,pid,semantic=False,transcript_path=None):
        row=self.preflight_analysis(pid,semantic)
        if row['status']!='APPROVED':raise ValueError('Ouça e aprove o áudio primeiro.')
        transcribe_and_build_storyboard(self.db,pid,row['id'],provider=JsonTranscriptProvider(transcript_path) if transcript_path else None)
        story,scenes=self.story(pid)
        trans=self.db.one('SELECT * FROM transcriptions WHERE id=?',(story['transcription_id'],))
        atomic(self.folder(pid)/'transcription'/f'transcript_{trans["id"]}.json',trans['payload'])
        if semantic:self.semantic_storyboard(pid)
        return self.audit_story(pid)
    def semantic_storyboard(self,pid):
        story,_=self.story(pid);audio=self.audio(pid)
        row=self.db.one('SELECT payload FROM transcriptions WHERE id=?',(story['transcription_id'],))
        segments=[TranscriptSegment(**s) for s in json.loads(row['payload'])];ends=[]
        for start in range(0,len(segments),160):
            batch=segments[start:start+160]
            value=self.remote(pid,'writer','Agrupe a narração em ideias visuais. Cena pode durar qualquer tempo coerente; nunca use 8s fixos. Retorne {end_indices:[índices inteiros do último segmento de cada grupo]}. Preserve ordem, termine no último índice fornecido. Não invente tempos.',{'segments':[asdict(s)|{'index':start+i} for i,s in enumerate(batch)]})
            result=value.get('end_indices') if isinstance(value,dict) else None
            if not isinstance(result,list) or not result or any(type(i)is not int or i<start or i>=start+len(batch) for i in result) or result[-1]!=start+len(batch)-1 or any(b<=a for a,b in zip(result,result[1:])):raise ValueError('Agrupamento inválido. A versão anterior foi preservada.')
            ends.extend(result)
        scenes=segment_scenes(segments,audio['duration'],ends)
        save_storyboard(self.db,pid,scenes,audio['id'],story['transcription_id'])
        return self.describe_scenes(pid)
    def describe_scenes(self,pid):
        story,scenes=self.story(pid)
        payload=[asdict(s) for s in scenes]
        for start in range(0,len(payload),20):
            batch=payload[start:start+20]
            if all(s['visual_description'].strip() and s['semantic_summary'].strip() for s in batch):continue
            value=self.remote(pid,'writer','Planeje imagens cientificamente coerentes com os trechos da fala. Retorne {scenes:[{scene_id,semantic_summary,visual_description,visual_function,camera_direction,movement}]}. Cada descrição é autossuficiente: sujeito, ambiente, escala, composição, luz, câmera e restrições científicas; não copie simplesmente a fala. Estética documental sombria, sem texto ou rótulos. Preserve IDs e ordem. Não altere timestamps.',{'scenes':batch,'topic':self.db.get_project(pid)['title'],'sources':self.source_text(pid)[:20000]})
            rows=value.get('scenes') if isinstance(value,dict) else None
            if not isinstance(rows,list) or [s.get('scene_id') for s in rows]!=[s['scene_id'] for s in batch]:raise ValueError('IA retornou cenas incompatíveis. Lotes anteriores preservados.')
            for target,new in zip(batch,rows):
                for key in ('semantic_summary','visual_description','visual_function','camera_direction','movement'):
                    if not isinstance(new.get(key),str) or not new[key].strip():raise ValueError('Descrição incompleta recebida da IA.')
                    target[key]=new[key]
            save_storyboard(self.db,pid,[Scene(**s) for s in payload],story['audio_id'],story['transcription_id'])
        return self.audit_story(pid)
    def save_story(self,pid,version,data):
        story,_=self.story(pid)
        if version!=story['version']:raise ValueError('Storyboard mudou. Reabra antes de salvar.')
        if not isinstance(data,list):raise ValueError('Cenas devem ser lista.')
        allowed={f.name for f in fields(Scene)}
        scenes=[]
        for s in data:
            if not isinstance(s,dict):raise ValueError('Cena inválida.')
            try:scenes.append(Scene(**{k:v for k,v in s.items() if k in allowed}))
            except TypeError:raise ValueError('Campos de cena inválidos.') from None
        for s in scenes:
            if not isinstance(s.start_time,(int,float)) or not isinstance(s.end_time,(int,float)):raise ValueError('Tempos devem ser números.')
        # Save drafts with editorial problems, but never NaN values.
        json.dumps(data,allow_nan=False)
        version=save_storyboard(self.db,pid,scenes,story['audio_id'],story['transcription_id'])
        return {'version':version,'audit':self.audit_story(pid)}
    def audit_story(self,pid):
        story,scenes=self.story(pid);audio=self.audio(pid)
        report=audit_scenes(scenes,audio['duration'])
        self.store_audit(pid,'storyboard',story['id'],report['issues'])
        self.db.execute('UPDATE storyboards SET status=? WHERE id=?',(report['decision'],story['id']))
        atomic(self.folder(pid)/'storyboard'/f'storyboard_v{story["version"]:03d}.json',storyboard_json(scenes))
        return report
    def approve_story(self,pid,version,note):
        story,scenes=self.story(pid)
        if story['version']!=version:raise ValueError('Versão mudou.')
        report=self.audit_story(pid)
        if report['decision']=='BLOCKED':raise ValueError('Corrija os erros do storyboard antes de aprovar.')
        self.note(note)
        self.db.execute("UPDATE storyboards SET status='APPROVED' WHERE id=?",(story['id'],));self.db.event(pid,'STORYBOARD_APPROVED',{'version':version,'note':note})
        return {'message':'Storyboard aprovado. Agora você pode gerar as imagens.'}
    def _revision_context(self,pid,version):
        current=self.db.one('SELECT * FROM storyboards WHERE project_id=? ORDER BY version DESC LIMIT 1',(pid,))
        if type(version) is not int or not current or current['version']!=version:
            raise ValueError('A versão mudou. Atualize a tela antes de continuar.')
        if self.db.one("SELECT id FROM jobs WHERE project_id=? AND status='RUNNING'",(pid,)):
            raise ValueError('Aguarde a tarefa em execução.')
        audio=self.audio(pid)
        if audio['status']!='APPROVED':raise ValueError('Aprove o áudio atual antes de alterar o storyboard.')
        return current,audio

    def _revision_transcript(self,pid,story,audio):
        if story['audio_id']!=audio['id']:
            raise ValueError('Esta versão pertence a outro áudio. Selecione uma versão do áudio atual.')
        trans=self.db.one('SELECT * FROM transcriptions WHERE id=? AND project_id=? AND audio_id=?',
                          (story['transcription_id'],pid,audio['id']))
        if not trans or trans['source_hash']!=audio['sha256']:
            raise ValueError('A versão não tem transcrição compatível com o áudio atual.')
        return trans

    def _commit_revision(self,pid,scenes,source,action,metadata):
        scenes=[replace(scene,generation_status='PENDING',audit_status='PENDING') for scene in scenes]
        version=save_storyboard(self.db,pid,scenes,source['audio_id'],source['transcription_id'])
        report=self.audit_story(pid)
        self.db.event(pid,action,dict(metadata,new_version=version,scenes=len(scenes)))
        return {'version':version,'scene_count':len(scenes),'audit':report,
                'message':f'Versão {version} criada com {len(scenes)} cenas. Revise as descrições e aprove novamente. Histórico preservado.'}

    def restore_story(self,pid,version,source_version):
        """Copy a historical version; never reactivate old approvals or images."""
        with self.db.transaction():
            current,audio=self._revision_context(pid,version)
            if type(source_version) is not int or source_version>=version:
                raise ValueError('Selecione uma versão anterior à atual.')
            source=self.db.one('SELECT * FROM storyboards WHERE project_id=? AND version=?',(pid,source_version))
            if not source:raise ValueError('Versão anterior inexistente neste projeto.')
            self._revision_transcript(pid,source,audio)
            scenes=[Scene(**json.loads(row['payload'])) for row in self.db.rows(
                'SELECT payload FROM scenes WHERE project_id=? AND storyboard_version=? ORDER BY start_time,scene_id',(pid,source_version))]
            if not scenes:raise ValueError('A versão escolhida não contém cenas.')
            return self._commit_revision(pid,scenes,source,'STORYBOARD_RESTORED',{'source_version':source_version,'previous_version':version})

    def split_story_by_speech(self,pid,version):
        """Rebuild sentence/pause boundaries locally using stored timestamps."""
        with self.db.transaction():
            current,audio=self._revision_context(pid,version)
            trans=self._revision_transcript(pid,current,audio)
            segments=[TranscriptSegment(**row) for row in json.loads(trans['payload'])]
            scenes=segment_scenes(segments,audio['duration'])
            old=[Scene(**json.loads(row['payload'])) for row in self.db.rows(
                'SELECT payload FROM scenes WHERE project_id=? AND storyboard_version=? ORDER BY start_time,scene_id',(pid,version))]
            signature=lambda rows:[(r.start_time,r.end_time,r.first_segment,r.last_segment,r.transcript_reference) for r in rows]
            if signature(old)==signature(scenes):
                return {'version':version,'scene_count':len(old),'message':'As cenas já seguem as frases e pausas reconhecidas. Nenhuma versão criada.'}
            return self._commit_revision(pid,scenes,current,'STORYBOARD_SPLIT_BY_SPEECH',{'previous_version':version})

    def split_scene(self,pid,version,scene_id):
        story,scenes=self.story(pid)
        if story['version']!=version:raise ValueError('A versão mudou.')
        trans=self.db.one('SELECT payload FROM transcriptions WHERE id=?',(story['transcription_id'],))
        segments=[TranscriptSegment(**s) for s in json.loads(trans['payload'])]
        index=next((i for i,s in enumerate(scenes) if s.scene_id==scene_id),None)
        if index is None:raise ValueError('Cena inexistente.')
        scene=scenes[index]
        if scene.first_segment>=scene.last_segment:raise ValueError('Este trecho não possui tempos internos. Use transcrição por palavra para dividir com precisão.')
        middle=(scene.start_time+scene.end_time)/2
        cut=min(range(scene.first_segment+1,scene.last_segment+1),key=lambda i:abs(segments[i].start-middle))
        a=asdict(scene);b=asdict(scene)
        a.update(end_time=segments[cut].start,last_segment=cut-1,speech_end=segments[cut-1].end,transcript_reference=' '.join(x.text for x in segments[scene.first_segment:cut]))
        b.update(start_time=segments[cut].start,first_segment=cut,speech_start=segments[cut].start,transcript_reference=' '.join(x.text for x in segments[cut:scene.last_segment+1]),semantic_summary='',visual_description='')
        out=[asdict(s) for s in scenes];out[index:index+1]=[a,b]
        for i,row in enumerate(out,1):row['scene_id']=f'SC{i:03d}';row['continuity_reference']=f'SC{i-1:03d}' if i>1 else None
        return self.save_story(pid,version,out)

    def merge_scene(self,pid,version,scene_id):
        story,scenes=self.story(pid)
        if story['version']!=version:raise ValueError('A versão mudou.')
        index=next((i for i,s in enumerate(scenes) if s.scene_id==scene_id),None)
        if index is None or index==len(scenes)-1:raise ValueError('Escolha uma cena que tenha sucessora.')
        first,second=scenes[index:index+2];merged=asdict(first)
        merged.update(end_time=second.end_time,last_segment=second.last_segment,speech_end=second.speech_end,transcript_reference=first.transcript_reference+' '+second.transcript_reference,semantic_summary='',visual_description='')
        out=[asdict(s) for s in scenes];out[index:index+2]=[merged]
        for i,row in enumerate(out,1):row['scene_id']=f'SC{i:03d}';row['continuity_reference']=f'SC{i-1:03d}' if i>1 else None
        return self.save_story(pid,version,out)

    def remote(self,pid,role,task,data,image=None):
        from .provider import Gemini
        client=Gemini();callid=None
        try:
            limit=int(os.getenv('COAE_MAX_CALLS_PER_PROJECT','0'))
            with self.db.transaction():
                used=self.db.one('SELECT COUNT(*) FROM api_calls WHERE project_id=?',(pid,))[0]
                if used>=limit:raise ValueError('Chamadas de IA desabilitadas ou teto atingido. Configure .env; o limite é de chamadas, não dinheiro.')
                callid=self.db.execute("INSERT INTO api_calls(project_id,role,status) VALUES(?,?,'RUNNING')",(pid,role)).lastrowid
            try:
                result,usage=client.generate_image(data) if role=='image' else client.call(task,data,audit=role=='auditor',image=image)
            except Exception as exc:
                code=getattr(exc,'code',None)
                if code==429:
                    message='Cota Gemini excedida para este modelo. Verifique faturamento/plano e limites da API; a tentativa foi contabilizada e não será repetida automaticamente.'
                elif code in (401,403):
                    message='Gemini recusou a credencial ou a permissão deste modelo. Verifique GEMINI_API_KEY, projeto e faturamento.'
                elif code==400:
                    message='Gemini rejeitou a requisição. Verifique o modelo, formato da resposta e configuração da geração de imagem.'
                else:
                    message='Chamada Gemini não concluída. Confira modelo, quota e conexão; a tentativa foi contabilizada e não será repetida automaticamente.'
                self.db.execute("UPDATE api_calls SET status='UNKNOWN_REMOTE_RESULT',metadata=? WHERE id=?",(dump({'error_type':type(exc).__name__,'error_code':code}),callid))
                raise ValueError(message) from None
            self.db.execute("UPDATE api_calls SET status='DONE',metadata=? WHERE id=?",(dump(usage),callid));return result
        finally:client.close()
    @staticmethod
    def prompt(scene):
        return scene.visual_description+' Documentário científico cinematográfico, atmosfera cósmica sombria, proporção 16:9. Preserve restrições físicas descritas. Sem texto, números, IDs, rótulos, logos ou marcas visíveis adicionadas.'
    def import_image(self,pid,scene_id,path):
        story,scenes=self.story(pid,approved=True)
        if scene_id not in [s.scene_id for s in scenes]:raise ValueError('Cena inexistente.')
        try:
            from PIL import Image
            with Image.open(path) as im:im.verify()
            with Image.open(path) as im:width,height=im.size
        except ImportError:raise ValueError('Instale requirements-images.txt.') from None
        except Exception:raise ValueError('Imagem inválida.') from None
        if abs(width/height-16/9)>.04:raise ValueError('Use imagem 16:9 neste perfil.')
        sha=file_sha256(Path(path));rel=Path('images')/f'{scene_id}_{story["version"]:03d}_{uuid.uuid4().hex[:10]}{Path(path).suffix.lower()}'
        target=self.folder(pid)/rel;target.parent.mkdir(exist_ok=True);shutil.copy2(path,target)
        iid=self.db.execute('INSERT INTO images(project_id,storyboard_id,scene_id,path,sha256) VALUES(?,?,?,?,?)',(pid,story['id'],scene_id,str(target),sha)).lastrowid
        self.store_audit(pid,'image',iid,[{'code':'VISUAL_REVIEW','severity':'review','message':'Confira relação com a fala, ciência, artefatos, texto e continuidade.'}])
        return {'image_id':iid}
    def image_audit(self,pid,iid):
        image=self.db.one('SELECT * FROM images WHERE id=? AND project_id=?',(iid,pid))
        if not image:raise ValueError('Imagem inexistente.')
        story,scenes=self.story(pid,approved=True)
        if image['storyboard_id']!=story['id'] or file_sha256(Path(image['path']))!=image['sha256']:raise ValueError('Imagem alterada ou de outra versão.')
        scene=next(s for s in scenes if s.scene_id==image['scene_id'])
        raw=Path(image['path']).read_bytes()
        from PIL import Image
        with Image.open(image['path']) as im:mime=Image.MIME[im.format]
        value=self.remote(pid,'auditor','Audite esta imagem contra a fala e o plano visual. Verifique objetos, coerência científica, artefatos, texto indesejado e composição. Retorne {issues:[{code,message,severity:"error|review|warning"}]}.',asdict(scene),image=(raw,mime))
        issues=self.remote_issues(value)+[{'code':'HUMAN_VISUAL','severity':'review','message':'Confira a imagem antes de aprovar.'}]
        report=self.store_audit(pid,'image',iid,issues);self.db.execute('UPDATE images SET status=? WHERE id=?',(report['decision'],iid));return report
    def generate_images(self,pid,scene_id=None):
        story,scenes=self.story(pid,approved=True)
        if scene_id:
            scenes=[s for s in scenes if s.scene_id==scene_id]
            if not scenes:raise ValueError('Cena inexistente.')
        generated=0
        for scene in scenes:
            previous=self.db.one('SELECT * FROM images WHERE storyboard_id=? AND scene_id=? ORDER BY id DESC LIMIT 1',(story['id'],scene.scene_id))
            if previous and previous['status'] in ('APPROVED','REVIEW_REQUIRED') and Path(previous['path']).exists() and file_sha256(Path(previous['path']))==previous['sha256']:continue
            prompt=self.prompt(scene)
            for attempt in range(4):
                raw=self.remote(pid,'image','image',{'prompt':prompt})
                path=self.folder(pid)/'images'/('temp_'+uuid.uuid4().hex+'.png')
                try:
                    atomic(path,raw);iid=self.import_image(pid,scene.scene_id,path)['image_id']
                finally:path.unlink(missing_ok=True)
                report=self.image_audit(pid,iid);generated+=1
                failures=[i for i in report['issues'] if i['severity']=='error']
                if not failures:break
                prompt=self.prompt(scene)+' Corrija estes problemas detectados: '+dump(failures)
        return {'message':f'{generated} imagem(ns) gerada(s). Confira auditorias e revise.','generated':generated}
    def approve_image(self,pid,iid,note):
        story,_=self.story(pid,approved=True);self.note(note)
        image=self.db.one('SELECT * FROM images WHERE id=? AND project_id=?',(iid,pid))
        if not image or image['storyboard_id']!=story['id']:raise ValueError('Imagem de outra versão.')
        if image['status']=='BLOCKED':raise ValueError('Há erro bloqueante na imagem. Corrija e reaudite.')
        if file_sha256(Path(image['path']))!=image['sha256']:raise ValueError('Imagem alterada.')
        self.db.execute("UPDATE images SET status='APPROVED' WHERE id=?",(iid,));self.db.event(pid,'IMAGE_APPROVED',{'id':iid,'note':note});return {'message':'Imagem aprovada.'}
    def export_prompts(self,pid):
        story,scenes=self.story(pid,approved=True);folder=self.folder(pid)/'exports'/f'prompts_v{story["version"]:03d}'
        for offset in range(0,len(scenes),20):
            group=scenes[offset:offset+20]
            lines=[f'{s.scene_id} (referência interna, não renderizar). '+self.prompt(s).replace('\n',' ') for s in group]
            atomic(folder/f'imagens_{offset//20+1:02d}.txt','\n'.join(lines)+'\n')
        atomic(folder/'manifest.json',storyboard_json(scenes))
        return {'message':'Prompts e tempos exportados; disponíveis na aba Arquivos.'}
    def export_timeline(self,pid):
        story,scenes=self.story(pid,approved=True);audio=self.audio(pid);rows=[]
        for s in scenes:
            im=self.db.one("SELECT * FROM images WHERE storyboard_id=? AND scene_id=? AND status='APPROVED' ORDER BY id DESC LIMIT 1",(story['id'],s.scene_id))
            if not im or not Path(im['path']).is_file() or file_sha256(Path(im['path']))!=im['sha256']:raise ValueError(f'Aprove uma imagem íntegra para {s.scene_id}.')
            rows.append({'scene_id':s.scene_id,'start':s.start_time,'end':s.end_time,'duration':s.duration,'image':str(Path(im['path']).relative_to(self.folder(pid))),'narration':s.transcript_reference,'movement':s.movement})
        folder=self.folder(pid)/'exports'/f'editing_v{story["version"]:03d}'
        atomic(folder/'timeline.json',dump({'audio':str(Path(audio['working_path']).relative_to(self.folder(pid))),'audio_hash':audio['sha256'],'scenes':rows}))
        buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);atomic(folder/'timeline.csv',buf.getvalue())
        trans=self.db.one('SELECT payload FROM transcriptions WHERE id=?',(story['transcription_id'],))
        segments=[TranscriptSegment(**s) for s in json.loads(trans['payload'])]
        def timestamp(t,separator=','):
            ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);sec,ms=divmod(ms,1000)
            return f'{h:02d}:{m:02d}:{sec:02d}{separator}{ms:03d}'
        # Sentence caption groups retain speech timestamps, not visual pause coverage.
        captions=segment_scenes(segments,audio['duration'])
        srt='\n\n'.join(f'{i}\n{timestamp(s.speech_start)} --> {timestamp(s.speech_end)}\n{s.transcript_reference}' for i,s in enumerate(captions,1))+'\n'
        vtt='WEBVTT\n\n'+'\n\n'.join(f'{timestamp(s.speech_start,".")} --> {timestamp(s.speech_end,".")}\n{s.transcript_reference}' for s in captions)+'\n'
        atomic(folder/'legendas.srt',srt);atomic(folder/'legendas.vtt',vtt)
        atomic(folder/'MONTAGEM.txt','Importe áudio e imagens no CapCut. Cada imagem ocupa start até end da timeline, sem duração fixa e sem alterar a voz. Os movimentos são sugestões editoriais. CSV/JSON são guias, não projetos nativos CapCut. Revise os tempos e legendas antes de exportar.\n')
        return {'message':'Timeline com imagens, SRT/VTT e instruções exportadas.'}
    def job(self,pid,action,fn):
        self.db.get_project(pid)
        try:jid=self.db.execute("INSERT INTO jobs(project_id,action,status) VALUES(?,?,'RUNNING')",(pid,action)).lastrowid
        except sqlite3.IntegrityError:raise ValueError('Já existe uma tarefa em execução neste projeto.') from None
        def run():
            try:result=fn();status='DONE'
            except Exception as exc:
                result={'error':str(exc) if isinstance(exc,(ValueError,RuntimeError,CoaeError)) else f'{type(exc).__name__}: operação não concluída. Confira instalação e terminal.'};status='FAILED'
            self.db.execute('UPDATE jobs SET status=?,result=? WHERE id=?',(status,dump(result),jid))
        threading.Thread(target=run,daemon=True).start()
        return {'job':jid}
    def file(self,pid,relative):
        root=self.folder(pid);p=(root/relative).resolve()
        if not p.is_relative_to(root) or not p.is_file():raise ValueError('Arquivo fora do projeto ou inexistente.')
        return p
    def state(self,pid=None):
        if not pid:return {'projects':[dict(p) for p in self.db.list_projects()], 'configured':bool(os.getenv('GEMINI_API_KEY') and os.getenv('COAE_WRITER_MODEL') and os.getenv('COAE_AUDITOR_MODEL')),'max_calls':int(os.getenv('COAE_MAX_CALLS_PER_PROJECT','0')),'ffprobe':bool(shutil.which('ffprobe'))}
        project=dict(self.db.get_project(pid));data={'project':project}
        for key,table,order in [('scripts','scripts','version'),('audios','audio_files','id'),('stories','storyboards','version'),('images','images','id'),('audits','audit_runs','id'),('jobs','jobs','id'),('events','events','id'),('calls','api_calls','id')]:
            data[key]=[dict(r) for r in self.db.rows(f'SELECT * FROM {table} WHERE project_id=? ORDER BY {order} DESC',(pid,))]
        for key,field in [('audits','report'),('jobs','result'),('events','payload')]:
            for row in data[key]:row[field]=json.loads(row[field])
        counts={r['storyboard_version']:r['n'] for r in self.db.rows('SELECT storyboard_version,COUNT(*) n FROM scenes WHERE project_id=? GROUP BY storyboard_version',(pid,))}
        for row in data['stories']:row['scene_count']=counts.get(row['version'],0)
        data['scenes']=[]
        if data['stories']:
            data['scenes']=[json.loads(r['payload']) for r in self.db.rows('SELECT payload FROM scenes WHERE project_id=? AND storyboard_version=? ORDER BY start_time,scene_id',(pid,data['stories'][0]['version']))]
        root=self.folder(pid)
        for rows,column in ((data['images'],'path'),(data['audios'],'working_path')):
            for row in rows:
                path=Path(row[column]).resolve()
                row['relative_path']=path.relative_to(root).as_posix() if path.is_relative_to(root) else None
        data['files']=[str(p.relative_to(root)).replace('\\','/') for p in root.rglob('*') if p.is_file()]
        data['sources']=self.source_text(pid)
        return data
    def bundle(self,pid):
        root=self.folder(pid);out=io.BytesIO()
        with tempfile.TemporaryDirectory(prefix='coae-bundle-') as temp:
            snapshot=Path(temp)/'coae.sqlite3'
            connection=sqlite3.connect(snapshot)
            try:
                with self.db.lock:
                    self.db.connection.backup(connection)
            finally:
                connection.close()
            with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
                for p in root.rglob('*'):
                    if p.is_file():z.write(p,str(Path(pid)/p.relative_to(root)))
                z.write(snapshot,f'{pid}/data/coae.sqlite3')
                z.writestr(f'{pid}/project_state.json',dump(self.state(pid)))
                z.writestr(f'{pid}/BACKUP_README.txt','Este bundle inclui os artefatos do projeto e um snapshot consistente de data/coae.sqlite3. Preserve a pasta data/ ao retomar o projeto; os caminhos registrados no banco podem exigir rebase se o projeto for movido para outra pasta.\n')
        return out.getvalue()
