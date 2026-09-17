from __future__ import annotations

import argparse
from pathlib import Path
from uuid import uuid4

from .audio import import_audio
from .pipeline import transcribe_and_build_storyboard
from .script_service import approve_script, export_script, save_script
from .storage import Database
from .transcription import JsonTranscriptProvider
from .web import serve


def main() -> None:
    parser = argparse.ArgumentParser(prog="coae")
    parser.add_argument("--database", default="data/coae.sqlite3")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create-project")
    create.add_argument("title")
    create.add_argument("--project-id", default=None)
    open_project = subparsers.add_parser("open-project")
    open_project.add_argument("project_id", nargs="?")
    save = subparsers.add_parser("save-script")
    save.add_argument("project_id")
    save.add_argument("title")
    save.add_argument("body_file", type=Path)
    script = subparsers.add_parser("export-script")
    script.add_argument("project_id")
    script.add_argument("--output", default=None, type=Path)
    approve = subparsers.add_parser("approve-script")
    approve.add_argument("project_id")
    approve.add_argument("version", type=int)
    audio = subparsers.add_parser("import-audio")
    audio.add_argument("project_id")
    audio.add_argument("audio_file", type=Path)
    audio.add_argument("--project-dir", default=None, type=Path)
    transcribe = subparsers.add_parser("transcribe")
    transcribe.add_argument("project_id")
    transcribe.add_argument("audio_id", type=int)
    transcribe.add_argument("transcript_file", type=Path)
    transcribe.add_argument("--audio-duration", required=True, type=float)
    transcribe.add_argument("--audio-path", required=True, type=Path)
    web = subparsers.add_parser("serve")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    database = Database(args.database)
    try:
        if args.command == "create-project":
            project_id = args.project_id or f"COAE-{uuid4().hex[:8].upper()}"
            database.create_project(project_id, args.title)
            for folder in ("research", "script", "audio", "transcription", "storyboard", "exports", "logs"):
                (Path("projects") / project_id / folder).mkdir(parents=True, exist_ok=True)
            print(project_id)
        elif args.command == "open-project":
            if args.project_id:
                project = database.get_project(args.project_id)
                scripts = database.connection.execute(
                    "SELECT version, title, approved, updated_at FROM scripts WHERE project_id = ? ORDER BY version DESC",
                    (args.project_id,),
                ).fetchall()
                print(dict(project))
                for script_row in scripts:
                    print(dict(script_row))
            else:
                for project in database.list_projects():
                    print(dict(project))
        elif args.command == "save-script":
            version = save_script(database, args.project_id, args.title, args.body_file.read_text(encoding="utf-8"))
            print(version)
        elif args.command == "approve-script":
            approve_script(database, args.project_id, args.version)
            print(f"approved: {args.version}")
        elif args.command == "export-script":
            output = args.output or Path("exports") / args.project_id
            files = export_script(database, args.project_id, None, None, output)
            print("\n".join(str(path) for path in files.values()))
        elif args.command == "import-audio":
            project_dir = args.project_dir or Path("projects") / args.project_id
            print(import_audio(database, args.project_id, args.audio_file, project_dir))
        elif args.command == "transcribe":
            row = database.connection.execute("SELECT working_path FROM audio_files WHERE id = ?", (args.audio_id,)).fetchone()
            audio_path = args.audio_path if row is None else row["working_path"]
            scenes = transcribe_and_build_storyboard(
                database,
                args.project_id,
                args.audio_id,
                audio_path,
                args.audio_duration,
                JsonTranscriptProvider(args.transcript_file),
            )
            print(f"storyboard scenes: {len(scenes)}")
        elif args.command == "serve":
            database.close()
            serve(args.database, args.host, args.port)
            return
    finally:
        database.close()


if __name__ == "__main__":
    main()