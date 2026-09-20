"""Shared lifecycle for the web and desktop entry points."""
from contextlib import contextmanager
from pathlib import Path
import os
import threading

from .application import Application
from .server import Server


@contextmanager
def workspace_lock(workspace):
    root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    # Keep the inode: unlinking a lock file allows another process to bypass it.
    lock = (root / '.coae.lock').open('a+b')
    acquired = False
    try:
        if os.name == 'nt':
            import msvcrt
            lock.seek(0, 2)
            if lock.tell() == 0:
                lock.write(b'0')
                lock.flush()
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError('Este workspace já está aberto. Feche o COAE web/desktop antes de iniciar outro servidor.') from exc
        else:
            import fcntl
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError('Este workspace já está aberto. Feche o COAE web/desktop antes de iniciar outro servidor.') from exc
        acquired = True
        yield root
    finally:
        if acquired:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


@contextmanager
def running_server(workspace, host='127.0.0.1', port=8765):
    with workspace_lock(workspace) as root:
        # Bind before Application: a busy port must not mark persisted jobs interrupted.
        uploads = root / 'workspace' / 'uploads'
        uploads.mkdir(parents=True, exist_ok=True)
        server = Server((host, port), None, upload_dir=uploads)
        server.daemon_threads = False  # Finish accepted requests before closing SQLite.
        app = None
        thread = None
        try:
            app = Application(root)
            server.app = app
            thread = threading.Thread(target=server.serve_forever, name='coae-http', daemon=True)
            thread.start()
            yield server
        finally:
            if thread is not None and thread.is_alive():
                server.shutdown()
                thread.join()
            server.server_close()
            server.temp.cleanup()
            if app is not None:
                app.db.close()
