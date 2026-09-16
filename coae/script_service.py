from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .errors import ScriptNotApprovedError
from .storage import Database


BREAK_BY_PARAGRAPH = {1: "1.5s", 2: "2s", 3: "3s"}


def clean_narration(body: str) -> str:
    return re.sub(r"<break\s+time=\"[0-9]+(?:\.[0-9]+)?s\"\s*/>", "", body).strip()


def dark_planner_narration(body: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body.strip()) if part.strip()]
    rendered = []
    for index, paragraph in enumerate(paragraphs, 1):
        pause = BREAK_BY_PARAGRAPH.get(index, "1s")
        rendered.append(f'{paragraph} <break time="{pause}"/>')
    return "\n\n".join(rendered)


def save_script(database: Database, project_id: str, title: str, body: str, approved: bool = False) -> int:
    database.get_project(project_id)
    if not title.strip() or not body.strip():
        raise ValueError("Título e roteiro não podem ficar vazios")
    version = database.connection.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 FROM scripts WHERE project_id = ?", (project_id,)
    ).fetchone()[0]
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    database.execute(
        "INSERT INTO scripts (project_id, version, title, body, approved, content_hash) VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, version, title.strip(), body.strip(), int(approved), digest),
    )
    database.update_project_timestamp(project_id)
    return int(version)


def approve_script(database: Database, project_id: str, version: int) -> None:
    database.get_project(project_id)
    script = database.connection.execute(
        "SELECT id FROM scripts WHERE project_id = ? AND version = ?", (project_id, version)
    ).fetchone()
    if script is None:
        raise ValueError(f"Versão de roteiro inexistente: {version}")
    database.execute("UPDATE scripts SET approved = 0 WHERE project_id = ? AND approved = 1", (project_id,))
    database.execute("UPDATE scripts SET approved = 1 WHERE id = ?", (script["id"],))
    database.update_project_timestamp(project_id)


def export_script(database: Database, project_id: str, title: str | None, body: str | None, output_dir: str | Path) -> dict[str, Path]:
    database.get_project(project_id)
    approved = database.connection.execute(
        "SELECT title, body, version FROM scripts WHERE project_id = ? AND approved = 1 ORDER BY version DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    if approved is None:
        raise ScriptNotApprovedError("Aprove uma versão do roteiro antes de exportar")
    if title is not None or body is not None:
        if title != approved["title"] or body.strip() != approved["body"]:
            raise ValueError("Exportação deve usar a versão aprovada persistida")
    title = approved["title"]
    body = approved["body"]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    clean = clean_narration(body)
    dark = dark_planner_narration(clean)
    master = f"# {title}\n\n{body.strip()}\n"
    files = {
        "script_master": output / "script_master.md",
        "narration_darkplanner": output / "narration_darkplanner.txt",
        "narration_clean": output / "narration_clean.txt",
    }
    contents = {"script_master": master, "narration_darkplanner": dark + "\n", "narration_clean": clean + "\n"}
    for kind, path in files.items():
        path.write_text(contents[kind], encoding="utf-8")
        database.execute(
            "INSERT INTO exports (project_id, kind, path, content_hash) VALUES (?, ?, ?, ?)",
            (project_id, kind, str(path), hashlib.sha256(contents[kind].encode()).hexdigest()),
        )
    return files