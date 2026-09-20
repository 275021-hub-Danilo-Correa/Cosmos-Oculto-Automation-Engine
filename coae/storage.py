from __future__ import annotations
import json
import re
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from .errors import ProjectNotFoundError

SCHEMA = '''
CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,title TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS scripts(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL REFERENCES projects(id),version INTEGER NOT NULL,title TEXT NOT NULL,body TEXT NOT NULL,approved INTEGER NOT NULL DEFAULT 0,content_hash TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,UNIQUE(project_id,version));
CREATE TABLE IF NOT EXISTS audio_files(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL REFERENCES projects(id),original_path TEXT NOT NULL,working_path TEXT NOT NULL,format TEXT NOT NULL,duration REAL NOT NULL,sha256 TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'IMPORTED',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS transcriptions(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL REFERENCES projects(id),audio_id INTEGER NOT NULL REFERENCES audio_files(id),provider TEXT NOT NULL,source_hash TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS scenes(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL REFERENCES projects(id),scene_id TEXT NOT NULL,start_time REAL NOT NULL,end_time REAL NOT NULL,payload TEXT NOT NULL,storyboard_version INTEGER NOT NULL,UNIQUE(project_id,storyboard_version,scene_id));
CREATE TABLE IF NOT EXISTS exports(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL REFERENCES projects(id),kind TEXT NOT NULL,path TEXT NOT NULL,content_hash TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS storyboards(id INTEGER PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id),version INTEGER NOT NULL,audio_id INTEGER REFERENCES audio_files(id),transcription_id INTEGER REFERENCES transcriptions(id),status TEXT NOT NULL DEFAULT 'DRAFT',created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(project_id,version));
CREATE TABLE IF NOT EXISTS images(id INTEGER PRIMARY KEY,project_id TEXT REFERENCES projects(id),storyboard_id INTEGER REFERENCES storyboards(id),scene_id TEXT NOT NULL,path TEXT NOT NULL,sha256 TEXT NOT NULL,status TEXT DEFAULT 'REVIEW_REQUIRED',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS audit_runs(id INTEGER PRIMARY KEY,project_id TEXT REFERENCES projects(id),kind TEXT NOT NULL,reference TEXT NOT NULL,report TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,project_id TEXT REFERENCES projects(id),action TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY,project_id TEXT REFERENCES projects(id),action TEXT NOT NULL,status TEXT NOT NULL,result TEXT DEFAULT '{}',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE UNIQUE INDEX IF NOT EXISTS one_running_job ON jobs(project_id) WHERE status='RUNNING';
CREATE TABLE IF NOT EXISTS api_calls(id INTEGER PRIMARY KEY,project_id TEXT REFERENCES projects(id),role TEXT,status TEXT,metadata TEXT DEFAULT '{}',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS image_rounds(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL REFERENCES projects(id),storyboard_id INTEGER NOT NULL REFERENCES storyboards(id),scene_id TEXT NOT NULL,round_number INTEGER NOT NULL,requested INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'QUEUED',rejection_reason TEXT NOT NULL DEFAULT '',recommendation_image_id INTEGER REFERENCES images(id),recommendation_summary TEXT NOT NULL DEFAULT '',cancel_requested INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,completed_at TEXT,UNIQUE(storyboard_id,scene_id,round_number));
CREATE TABLE IF NOT EXISTS image_candidates(id INTEGER PRIMARY KEY AUTOINCREMENT,round_id INTEGER NOT NULL REFERENCES image_rounds(id),candidate_number INTEGER NOT NULL,image_id INTEGER REFERENCES images(id),audit_id INTEGER REFERENCES audit_runs(id),seed INTEGER NOT NULL,prompt TEXT NOT NULL,negative_prompt TEXT NOT NULL DEFAULT '',workflow TEXT NOT NULL,model TEXT NOT NULL,prompt_id TEXT,preview_path TEXT,status TEXT NOT NULL DEFAULT 'QUEUED',stage TEXT NOT NULL DEFAULT 'Na fila',progress REAL,error TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,UNIQUE(round_id,candidate_number));
CREATE INDEX IF NOT EXISTS image_round_project ON image_rounds(project_id,storyboard_id,scene_id,id);
CREATE UNIQUE INDEX IF NOT EXISTS image_seed_once ON image_candidates(seed);
'''

class Database:
    def __init__(self,path: str|Path):
        self.path=Path(path).resolve();self.path.parent.mkdir(parents=True,exist_ok=True)
        self.connection=sqlite3.connect(self.path,timeout=30,check_same_thread=False)
        self.connection.row_factory=sqlite3.Row
        self.lock=threading.RLock();self.depth=0
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.connection.executescript(SCHEMA)
        # Additive migration from the uploaded 0.1 schema; do not delete user data.
        with self.transaction():
            additions={'projects':{'root_path':'TEXT'},'scripts':{'updated_at':'TEXT'},'audio_files':{'script_id':'INTEGER REFERENCES scripts(id)'},'exports':{'source_ref':'TEXT'},'image_candidates':{'audit_id':'INTEGER REFERENCES audit_runs(id)','negative_prompt':"TEXT NOT NULL DEFAULT ''",'preview_path':'TEXT'}}
            for table,columns in additions.items():
                current={r[1] for r in self.connection.execute(f'PRAGMA table_info({table})')}
                for name,kind in columns.items():
                    if name not in current:self.connection.execute(f'ALTER TABLE {table} ADD COLUMN {name} {kind}')
            self.connection.execute('UPDATE scripts SET updated_at=created_at WHERE updated_at IS NULL')
            # Old scenes have no provable audio/version lineage: retain, require regeneration.
            self.connection.execute("INSERT OR IGNORE INTO storyboards(project_id,version,status) SELECT project_id,storyboard_version,'STALE' FROM scenes GROUP BY project_id,storyboard_version")
            self.connection.execute('PRAGMA user_version=2')
    @contextmanager
    def transaction(self):
        with self.lock:
            outer=self.depth==0
            if outer:self.connection.execute('BEGIN IMMEDIATE')
            self.depth+=1
            try:
                yield
                if outer:self.connection.commit()
            except BaseException:
                if outer:self.connection.rollback()
                raise
            finally:self.depth-=1
    def close(self):
        with self.lock:self.connection.close()
    def execute(self,sql,parameters=()):
        with self.lock:
            cursor=self.connection.execute(sql,parameters)
            if not self.depth:self.connection.commit()
            return cursor
    def rows(self,sql,parameters=()):
        with self.lock:return self.connection.execute(sql,parameters).fetchall()
    def one(self,sql,parameters=()):
        with self.lock:return self.connection.execute(sql,parameters).fetchone()
    def create_project(self,project_id,title):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',project_id) or not title.strip():
            raise ValueError('ID deve conter somente letras, números, hífen ou sublinhado; título obrigatório.')
        self.execute('INSERT INTO projects(id,title) VALUES(?,?)',(project_id,title.strip()))
    def get_project(self,project_id):
        row=self.one('SELECT * FROM projects WHERE id=?',(project_id,))
        if row is None:raise ProjectNotFoundError(f'Projeto inexistente: {project_id}')
        return row
    def list_projects(self):return self.rows("SELECT * FROM projects WHERE status!='TRASHED' ORDER BY updated_at DESC,id")
    def update_project_timestamp(self,project_id):
        self.get_project(project_id);self.execute('UPDATE projects SET updated_at=CURRENT_TIMESTAMP WHERE id=?',(project_id,))
    def save_scene(self,project_id,scene,version):
        self.execute('INSERT INTO scenes(project_id,scene_id,start_time,end_time,payload,storyboard_version) VALUES(?,?,?,?,?,?)',(project_id,scene.scene_id,scene.start_time,scene.end_time,json.dumps(scene.__dict__,ensure_ascii=False,allow_nan=False),version))
    def event(self,project_id,action,payload):
        self.execute('INSERT INTO events(project_id,action,payload) VALUES(?,?,?)',(project_id,action,json.dumps(payload,ensure_ascii=False,allow_nan=False)))
    def invalidate(self,project_id,reason):
        self.execute("UPDATE storyboards SET status='STALE' WHERE project_id=?",(project_id,))
        self.execute("UPDATE images SET status='STALE' WHERE project_id=?",(project_id,))
        self.event(project_id,'DEPENDENCIES_INVALIDATED',{'reason':reason})
