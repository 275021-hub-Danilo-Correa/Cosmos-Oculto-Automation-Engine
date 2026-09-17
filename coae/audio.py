from __future__ import annotations
import hashlib
import json
import math
import os
import shutil
import subprocess
import uuid
import wave
from pathlib import Path
from .errors import UnsupportedAudioError
from .storage import Database
SUPPORTED_FORMATS={'.mp3','.wav','.m4a'}

def file_sha256(path:Path)->str:
    result=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()

def wav_duration(path:Path)->float:
    with wave.open(str(path),'rb') as f:
        return f.getnframes()/f.getframerate()

def media_duration(path:Path)->float:
    if path.suffix.lower()=='.wav':
        try:duration=wav_duration(path)
        except (wave.Error,EOFError,ZeroDivisionError):duration=None
    else:duration=None
    if duration is None:
        if not shutil.which('ffprobe'):
            raise UnsupportedAudioError('Instale FFmpeg e coloque ffprobe no PATH. WAV PCM funciona sem FFmpeg.')
        try:
            p=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True,check=True,timeout=60)
            info=json.loads(p.stdout)
            if not any(s.get('codec_type')=='audio' for s in info['streams']):raise ValueError()
            duration=float(info['format']['duration'])
        except (ValueError,KeyError,subprocess.SubprocessError):raise UnsupportedAudioError('Arquivo de áudio inválido ou sem duração.') from None
    if not math.isfinite(duration) or duration<=0:raise UnsupportedAudioError('Duração do áudio deve ser positiva e finita.')
    return duration

def import_audio(database:Database,project_id:str,source_path:str|Path,project_dir:str|Path)->int:
    database.get_project(project_id)
    source=Path(source_path).resolve()
    if not source.is_file():raise FileNotFoundError(source)
    ext=source.suffix.lower()
    if ext not in SUPPORTED_FORMATS:raise UnsupportedAudioError('Formato não suportado.')
    duration=media_duration(source);sha=file_sha256(source)
    script=database.one('SELECT id FROM scripts WHERE project_id=? AND approved=1 ORDER BY version DESC LIMIT 1',(project_id,))
    script_id=script['id'] if script else None
    old=database.one('SELECT * FROM audio_files WHERE project_id=? AND sha256=? AND script_id IS ? ORDER BY id DESC LIMIT 1',(project_id,sha,script_id))
    if old and old['status'] not in ('STALE','SUPERSEDED') and Path(old['working_path']).exists() and file_sha256(Path(old['working_path']))==sha:return old['id']
    # Unique revision paths: repeated filenames cannot overwrite originals.
    token=uuid.uuid4().hex[:12];base=Path(project_dir).resolve()/'audio'
    original=base/'originals'/f'{sha[:16]}_{token}{ext}'
    working=base/'working'/f'{sha[:16]}_{token}{ext}'
    written=[]
    try:
        for target in (original,working):
            target.parent.mkdir(parents=True,exist_ok=True)
            temp=target.with_suffix(target.suffix+'.tmp');shutil.copy2(source,temp)
            if file_sha256(temp)!=sha:raise ValueError('O arquivo mudou durante a cópia.')
            os.replace(temp,target);written.append(target)
        with database.transaction():
            database.execute("UPDATE audio_files SET status='SUPERSEDED' WHERE project_id=?",(project_id,))
            cursor=database.execute('INSERT INTO audio_files(project_id,original_path,working_path,format,duration,sha256,script_id) VALUES(?,?,?,?,?,?,?)',(project_id,str(original),str(working),ext[1:],duration,sha,script_id))
            database.invalidate(project_id,'Novo áudio importado')
            database.event(project_id,'AUDIO_IMPORTED',{'audio_id':cursor.lastrowid,'duration':duration,'sha256':sha})
        return int(cursor.lastrowid)
    except Exception:
        for p in written:p.unlink(missing_ok=True)
        raise

def verified_audio(database,project_id,audio_id):
    row=database.one('SELECT * FROM audio_files WHERE id=? AND project_id=?',(audio_id,project_id))
    if row is None:raise ValueError('Áudio inexistente ou pertencente a outro projeto.')
    path=Path(row['working_path'])
    if not path.is_file() or file_sha256(path)!=row['sha256']:raise ValueError('Áudio ausente ou alterado. Reimporte o arquivo.')
    if abs(media_duration(path)-row['duration'])>.025:raise ValueError('Duração armazenada não corresponde ao áudio.')
    if row['status'] in ('STALE','SUPERSEDED'):raise ValueError('Áudio desatualizado; importe a narração atual.')
    if row['script_id']:
        script=database.one('SELECT approved FROM scripts WHERE id=?',(row['script_id'],))
        if not script or not script['approved']:raise ValueError('Áudio ligado a roteiro que não está mais aprovado.')
    return row
