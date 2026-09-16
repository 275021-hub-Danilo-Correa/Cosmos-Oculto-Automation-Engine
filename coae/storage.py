from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .errors import ProjectNotFoundError


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(id),
    version INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    approved INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, version)
);
CREATE TABLE IF NOT EXISTS audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(id),
    original_path TEXT NOT NULL,
    working_path TEXT NOT NULL,
    format TEXT NOT NULL,
    duration REAL NOT NULL,
    sha256 TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'IMPORTED',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS transcriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(id),
    audio_id INTEGER NOT NULL REFERENCES audio_files(id),
    provider TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS scenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(id),
    scene_id TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    payload TEXT NOT NULL,
    storyboard_version INTEGER NOT NULL,
    UNIQUE(project_id, storyboard_version, scene_id)
);
CREATE TABLE IF NOT EXISTS exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(id),
    kind TEXT NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        cursor = self.connection.execute(sql, parameters)
        self.connection.commit()
        return cursor

    def create_project(self, project_id: str, title: str) -> None:
        self.execute("INSERT INTO projects (id, title) VALUES (?, ?)", (project_id, title))

    def get_project(self, project_id: str) -> sqlite3.Row:
        project = self.connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if project is None:
            raise ProjectNotFoundError(f"Projeto inexistente: {project_id}")
        return project

    def list_projects(self) -> list[sqlite3.Row]:
        return self.connection.execute("SELECT * FROM projects ORDER BY updated_at DESC, id").fetchall()

    def update_project_timestamp(self, project_id: str) -> None:
        self.get_project(project_id)
        self.execute("UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))

    def save_scene(self, project_id: str, scene: Any, version: int) -> None:
        self.execute(
            "INSERT INTO scenes (project_id, scene_id, start_time, end_time, payload, storyboard_version) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, scene.scene_id, scene.start_time, scene.end_time, json.dumps(scene.__dict__), version),
        )