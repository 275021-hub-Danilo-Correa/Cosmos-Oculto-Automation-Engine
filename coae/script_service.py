from __future__ import annotations
import hashlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from .errors import ScriptNotApprovedError
from .storage import Database

BREAK=re.compile(r'<break\s+time=[\"\']([0-9]+(?:\.[0-9]+)?)s[\"\']\s*/>')

def validate_narration(body):
    try:
        root=ET.fromstring('<speak>'+body+'</speak>')
        for node in root.iter():
            if node is root:continue
            if node.tag!='break' or set(node.attrib)!={'time'} or node.text or len(node):raise ValueError('Use apenas texto e tags break.')
            match=re.fullmatch(r'(\d+(?:\.\d+)?)s',node.attrib['time'])
            if not match or not 0<float(match[1])<=3:raise ValueError('Pausas devem estar entre 0 e 3 segundos.')
    except ET.ParseError:raise ValueError('SSML inválido. Use <break time="1s"/> e escape & como &amp;.') from None
    if re.search(r'^\s*(#{1,6}\s|```|\[CENA|CÂMERA:|CAMERA:)',body,re.M|re.I):raise ValueError('Remova cabeçalhos/instruções técnicas do texto narrado.')

def clean_narration(body):
    return BREAK.sub('',body).strip()

def dark_planner_narration(body):
    # Preserve approved pauses verbatim. No positional pause insertion.
    validate_narration(body)
    return body.strip()

def save_script(database,project_id,title,body,approved=False):
    database.get_project(project_id)
    if not title.strip() or not body.strip():raise ValueError('Título e roteiro não podem ficar vazios.')
    title=title.strip();body=body.strip();sha=hashlib.sha256(body.encode()).hexdigest()
    with database.transaction():
        last=database.one('SELECT * FROM scripts WHERE project_id=? ORDER BY version DESC LIMIT 1',(project_id,))
        if last and last['body']==body and last['title']==title:return last['version']
        version=last['version']+1 if last else 1
        database.execute('INSERT INTO scripts(project_id,version,title,body,approved,content_hash,updated_at) VALUES(?,?,?,?,0,?,CURRENT_TIMESTAMP)',(project_id,version,title,body,sha))
        database.update_project_timestamp(project_id)
        database.event(project_id,'SCRIPT_SAVED',{'version':version})
        if approved:approve_script(database,project_id,version)
    return version

def approve_script(database,project_id,version):
    database.get_project(project_id)
    script=database.one('SELECT * FROM scripts WHERE project_id=? AND version=?',(project_id,version))
    if not script:raise ValueError('Versão inexistente.')
    validate_narration(script['body'])
    with database.transaction():
        previous=database.one('SELECT id FROM scripts WHERE project_id=? AND approved=1',(project_id,))
        database.execute('UPDATE scripts SET approved=0 WHERE project_id=?',(project_id,))
        database.execute('UPDATE scripts SET approved=1 WHERE id=?',(script['id'],))
        if previous and previous['id']!=script['id']:
            database.execute("UPDATE audio_files SET status='STALE' WHERE project_id=?",(project_id,))
            database.invalidate(project_id,'Outra versão de roteiro aprovada')
        database.update_project_timestamp(project_id)
        database.event(project_id,'SCRIPT_APPROVED',{'version':version})

def export_script(database,project_id,title,body,output_dir):
    database.get_project(project_id)
    row=database.one('SELECT * FROM scripts WHERE project_id=? AND approved=1 ORDER BY version DESC LIMIT 1',(project_id,))
    if not row:raise ScriptNotApprovedError('Aprove uma versão antes de exportar.')
    if title is not None or body is not None:
        if title!=row['title'] or body is None or body.strip()!=row['body']:raise ValueError('Use a versão aprovada persistida.')
    validate_narration(row['body'])
    output=Path(output_dir)/f'script_v{row["version"]:03d}';output.mkdir(parents=True,exist_ok=True)
    contents={'script_master':f'# {row["title"]}\n\n{row["body"]}\n','narration_darkplanner':dark_planner_narration(row['body'])+'\n','narration_clean':clean_narration(row['body'])+'\n'}
    files={}
    for kind,content in contents.items():
        path=output/(kind+('.md' if kind=='script_master' else '.txt'))
        if path.exists() and path.read_text(encoding='utf-8')!=content:raise ValueError('Exportação versionada já existe com outro conteúdo; preserve o arquivo e escolha outra pasta.')
        path.write_text(content,encoding='utf-8');files[kind]=path
        database.execute('INSERT INTO exports(project_id,kind,path,content_hash,source_ref) VALUES(?,?,?,?,?)',(project_id,kind,str(path.resolve()),hashlib.sha256(content.encode()).hexdigest(),str(row['id'])))
    return files
