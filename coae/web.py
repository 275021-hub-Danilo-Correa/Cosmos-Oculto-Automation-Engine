from __future__ import annotations

import html
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from .script_service import approve_script, export_script, save_script
from .storage import Database


def project_directory(project_id: str) -> Path:
    return Path("projects") / project_id


def ensure_project_directories(project_id: str) -> None:
    for folder in ("research", "script", "audio", "transcription", "storyboard", "exports", "logs"):
        (project_directory(project_id) / folder).mkdir(parents=True, exist_ok=True)


def page(title: str, content: str) -> bytes:
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} | COAE</title>
<style>
body {{ font-family: Georgia, serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #17212b; background: #f5f1e8; }}
h1, h2 {{ font-weight: 500; }} a {{ color: #145c63; }}
section, article {{ background: #fffdf8; border: 1px solid #d8d0c2; padding: 1rem; margin: 1rem 0; }}
input, textarea, button {{ font: inherit; padding: .55rem; margin: .25rem 0; }} input, textarea {{ width: 100%; box-sizing: border-box; }}
textarea {{ min-height: 14rem; }} button {{ background: #145c63; color: white; border: 0; cursor: pointer; }}
.muted {{ color: #66727a; }} .row {{ display: flex; gap: 1rem; flex-wrap: wrap; }} .row > * {{ flex: 1; min-width: 14rem; }}
</style></head><body><nav><a href="/">COAE</a></nav>{content}</body></html>""".encode("utf-8")


class CoaeHandler(BaseHTTPRequestHandler):
    database_path: Path

    def database(self) -> Database:
        return Database(self.database_path)

    def send_html(self, body: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        database = self.database()
        try:
            if parsed.path == "/":
                projects = database.list_projects()
                project_list = "".join(
                    f'<li><a href="/projects/{html.escape(project["id"])}">'
                    f'{html.escape(project["title"])} ({html.escape(project["id"])})</a></li>'
                    for project in projects
                ) or "<li>Nenhum projeto criado.</li>"
                content = f"""<h1>Cosmos Oculto Automation Engine</h1>
<section><h2>Novo projeto</h2><form method="post" action="/projects">
<label>Título <input name="title" required></label><button type="submit">Criar projeto</button></form></section>
<section><h2>Projetos</h2><ul>{project_list}</ul></section>"""
                self.send_html(page("Projetos", content))
                return
            if parsed.path.startswith("/projects/"):
                project_id = parsed.path.removeprefix("/projects/").rstrip("/")
                project = database.get_project(project_id)
                scripts = database.connection.execute(
                    "SELECT version, title, body, approved, updated_at FROM scripts WHERE project_id = ? ORDER BY version DESC",
                    (project_id,),
                ).fetchall()
                script_options = "".join(
                    f'<article><h3>Versão {script["version"]}: {html.escape(script["title"])}</h3>'
                    f'<p class="muted">{"APROVADA" if script["approved"] else "RASCUNHO"}</p>'
                    f'<pre>{html.escape(script["body"])}</pre>'
                    f'<form method="post" action="/projects/{html.escape(project_id)}/approve">'
                    f'<input type="hidden" name="version" value="{script["version"]}">'
                    f'<button type="submit">Aprovar esta versão</button></form></article>'
                    for script in scripts
                ) or "<p>Nenhum roteiro salvo.</p>"
                content = f"""<h1>{html.escape(project["title"])}</h1><p class="muted">{html.escape(project_id)}</p>
<section><h2>Novo roteiro</h2><form method="post" action="/projects/{html.escape(project_id)}/scripts">
<label>Título <input name="title" required></label><label>Texto<textarea name="body" required></textarea></label>
<button type="submit">Salvar versão</button></form></section>
<section><h2>Exportação</h2><form method="post" action="/projects/{html.escape(project_id)}/export">
<button type="submit">Exportar roteiro aprovado</button></form></section>
<section><h2>Roteiros</h2>{script_options}</section>"""
                self.send_html(page(project["title"], content))
                return
            self.send_html(page("Não encontrado", "<h1>404</h1>"), HTTPStatus.NOT_FOUND)
        except Exception as error:
            self.send_html(page("Erro", f"<h1>Erro</h1><p>{html.escape(str(error))}</p>"), HTTPStatus.BAD_REQUEST)
        finally:
            database.close()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        database = self.database()
        try:
            if parsed.path == "/projects":
                title = form.get("title", [""])[0]
                project_id = f"COAE-{uuid4().hex[:8].upper()}"
                database.create_project(project_id, title)
                ensure_project_directories(project_id)
                self.redirect(f"/projects/{project_id}")
                return
            project_id = parsed.path.removeprefix("/projects/").split("/", 1)[0]
            database.get_project(project_id)
            if parsed.path.endswith("/scripts"):
                save_script(database, project_id, form.get("title", [""])[0], form.get("body", [""])[0])
            elif parsed.path.endswith("/approve"):
                approve_script(database, project_id, int(form["version"][0]))
            elif parsed.path.endswith("/export"):
                export_script(database, project_id, None, None, project_directory(project_id) / "exports")
            else:
                self.send_html(page("Não encontrado", "<h1>404</h1>"), HTTPStatus.NOT_FOUND)
                return
            self.redirect(f"/projects/{project_id}")
        except Exception as error:
            self.send_html(page("Erro", f"<h1>Erro</h1><p>{html.escape(str(error))}</p>"), HTTPStatus.BAD_REQUEST)
        finally:
            database.close()


def serve(database_path: str | Path, host: str = "127.0.0.1", port: int = 8000) -> None:
    handler = type("ConfiguredCoaeHandler", (CoaeHandler,), {"database_path": Path(database_path)})
    server = HTTPServer((host, port), handler)
    print(f"COAE disponível em http://{host}:{server.server_port}")
    server.serve_forever()