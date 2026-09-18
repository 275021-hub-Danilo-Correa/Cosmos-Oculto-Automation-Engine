from __future__ import annotations
import argparse
import json
import mimetypes
import os
from pathlib import Path
import secrets
import tempfile
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .application import Application,dump
from .errors import CoaeError
from .script_service import save_script,export_script

BASE=Path(__file__).resolve().parents[1]

def load_env():
    file=BASE/'.env'
    if file.exists():
        for line in file.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k,v=line.split('=',1)
                if k.strip().startswith(('COAE_','GEMINI_')):os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,app):
        token=os.environ.get('COAE_ACCESS_TOKEN','').strip()
        if token and any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in token):
            raise ValueError('COAE_ACCESS_TOKEN deve conter apenas letras ASCII, números, hífen ou sublinhado.')
        self.app=app;self.token=token or secrets.token_urlsafe(32);self.uploads={};self.temp=tempfile.TemporaryDirectory(prefix='coae-upload-');self.command_lock=threading.RLock()
        try:
            super().__init__(address,Handler)
        except BaseException:
            self.temp.cleanup()
            raise

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,data,status=200,mime='application/json; charset=utf-8',filename=None):
        data=data if isinstance(data,bytes) else dump(data).encode()
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
        self.end_headers();self.wfile.write(data)
    def auth(self):return secrets.compare_digest(self.headers.get('X-COAE-Token',''),self.server.token)
    def do_GET(self):
        parsed=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(parsed.query)
        if parsed.path in ('/','/app.js','/style.css'):
            path=Path(__file__).parent/'web'/({'/':'index.html'}.get(parsed.path,parsed.path.lstrip('/')))
            return self.send(path.read_bytes(),mime={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[parsed.path])
        if not self.auth():return self.send({'error':'Abra o endereço com #token mostrado no terminal.'},401)
        try:
            pid=q.get('project',[None])[0]
            if parsed.path=='/api/state':return self.send(self.server.app.state(pid))
            if parsed.path=='/api/download':return self.send(self.server.app.bundle(pid),mime='application/zip',filename=pid+'.zip')
            if parsed.path=='/api/file':
                p=self.server.app.file(pid,q.get('path',[''])[0]);return self.send(p.read_bytes(),mime=mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
            return self.send({'error':'Não encontrado.'},404)
        except (ValueError,CoaeError) as exc:self.send({'error':str(exc)},400)
    def do_POST(self):
        if not self.auth():return self.send({'error':'Não autorizado.'},401)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if self.path=='/api/upload':
                if not 0<size<=256*1024*1024:raise ValueError('Envie um arquivo de até 256 MB.')
                ext=Path(urllib.parse.unquote(self.headers.get('X-Filename',''))).suffix.lower()
                if ext not in ('.mp3','.m4a','.wav','.png','.jpg','.jpeg','.webp','.json'):raise ValueError('Tipo de arquivo não permitido.')
                uid=secrets.token_hex(16);path=Path(self.server.temp.name)/(uid+ext);remaining=size
                with path.open('wb') as f:
                    while remaining:
                        chunk=self.rfile.read(min(1024*1024,remaining))
                        if not chunk:raise ValueError('Upload interrompido.')
                        f.write(chunk);remaining-=len(chunk)
                self.server.uploads[uid]=path;return self.send({'upload':uid})
            if self.path!='/api/action' or not 0<size<4*1024*1024:raise ValueError('Requisição inválida.')
            d=json.loads(self.rfile.read(size));action=d.get('action');pid=d.get('project');app=self.server.app
            with self.server.command_lock:
                if pid and app.db.one("SELECT id FROM jobs WHERE project_id=? AND status='RUNNING'",(pid,)):raise ValueError('Aguarde a tarefa em execução antes de alterar este projeto.')
                if action in ('analyze','import_transcript'):
                    app.preflight_analysis(pid,d.get('semantic',False))
                if action=='diagnose_local':
                    from .local_ai import diagnostics
                    result=app.job(pid,action,diagnostics)
                elif action=='create':result=app.create(d['title'])
                elif action=='save_script':result={'version':save_script(app.db,pid,d['title'],d['body'])}
                elif action=='sources':result=app.save_sources(pid,d['text'])
                elif action=='audit_script':result=app.job(pid,action,lambda:app.audit_script(pid,d.get('remote',False)))
                elif action=='repair_script':result=app.job(pid,action,lambda:app.repair_script(pid))
                elif action=='generate_script':result=app.job(pid,action,lambda:app.generate_script(pid))
                elif action=='approve_script':result=app.approve_script(pid,d['version'],d['note'])
                elif action=='export_script':result={'files':[str(p.relative_to(app.folder(pid))) for p in export_script(app.db,pid,None,None,app.folder(pid)/'exports').values()]}
                elif action in ('import_audio','import_image','import_transcript'):
                    path=self.server.uploads.pop(d['upload'],None)
                    if path is None:raise ValueError('Envie o arquivo primeiro.')
                    if action=='import_transcript':
                        def imported():
                            try:return app.analyze(pid,d.get('semantic',False),path)
                            finally:path.unlink(missing_ok=True)
                        result=app.job(pid,action,imported)
                    else:
                        try:result=app.import_audio(pid,path) if action=='import_audio' else app.import_image(pid,d['scene_id'],path)
                        finally:path.unlink(missing_ok=True)
                elif action=='approve_audio':result=app.approve_audio(pid,d['audio_id'],d['note'])
                elif action=='analyze':result=app.job(pid,action,lambda:app.analyze(pid,d.get('semantic',False)))
                elif action=='semantic':result=app.job(pid,action,lambda:app.semantic_storyboard(pid))
                elif action=='describe':result=app.job(pid,action,lambda:app.describe_scenes(pid))
                elif action=='save_story':result=app.save_story(pid,d['version'],d['scenes'])
                elif action=='restore_story':result=app.restore_story(pid,d['version'],d['source_version'])
                elif action=='split_story':result=app.split_story_by_speech(pid,d['version'])
                elif action=='split':result=app.split_scene(pid,d['version'],d['scene_id'])
                elif action=='merge':result=app.merge_scene(pid,d['version'],d['scene_id'])
                elif action=='audit_story':result=app.audit_story(pid)
                elif action=='approve_story':result=app.approve_story(pid,d['version'],d['note'])
                elif action=='generate_images':result=app.job(pid,action,lambda:app.generate_images(pid,d.get('scene_id')))
                elif action=='audit_image':result=app.job(pid,action,lambda:app.image_audit(pid,d['image_id']))
                elif action=='approve_image':result=app.approve_image(pid,d['image_id'],d['note'])
                elif action=='prompts':result=app.export_prompts(pid)
                elif action=='timeline':result=app.export_timeline(pid)
                else:raise ValueError('Ação desconhecida.')
            self.send(result)
        except (ValueError,KeyError,TypeError,CoaeError) as exc:self.send({'error':str(exc)},400)
        except Exception as exc:
            import traceback
            traceback.print_exc();self.send({'error':f'Falha interna ({type(exc).__name__}). Detalhes no terminal.'},500)

def main():
    load_env();parser=argparse.ArgumentParser(description='Estúdio local Cosmos Oculto')
    parser.add_argument('--port',type=int,default=8765);parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--workspace',default=str(BASE));parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    from .runtime import running_server
    try:
        with running_server(args.workspace, args.host, args.port) as server:
            url=f'http://localhost:{server.server_port}/#token={server.token}'
            print('\nCOSMOS OCULTO — narração externa, cenas pela fala\nAbra: '+url+'\nMantenha este terminal aberto. Ctrl+C para encerrar.\n',flush=True)
            if not args.no_browser:webbrowser.open(url)
            threading.Event().wait()
    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(1, f'Não foi possível iniciar o COAE: {exc}\n')

if __name__=='__main__':main()
