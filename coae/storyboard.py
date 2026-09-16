from __future__ import annotations

import json

from .models import Scene
from .storage import Database


def save_storyboard(database: Database, project_id: str, scenes: list[Scene]) -> int:
    version = database.connection.execute(
        "SELECT COALESCE(MAX(storyboard_version), 0) + 1 FROM scenes WHERE project_id = ?", (project_id,)
    ).fetchone()[0]
    for scene in scenes:
        database.save_scene(project_id, scene, version)
    return int(version)


def storyboard_json(scenes: list[Scene]) -> str:
    return json.dumps([scene.__dict__ | {"duration": scene.duration} for scene in scenes], ensure_ascii=False, indent=2)