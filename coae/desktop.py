"""Optional native window; the application and its HTTP API remain shared."""
import argparse
import importlib
import sys

from .runtime import running_server
from .server import BASE, load_env


def run_desktop(workspace, port=8765):
    try:
        webview = importlib.import_module('webview')
    except ImportError as exc:
        raise RuntimeError(
            'Desktop requer pywebview. Execute INSTALAR_DESKTOP_WINDOWS.bat ou '
            'python -m pip install -r requirements-desktop.txt. '
            'A versão web continua disponível com python iniciar.py.'
        ) from exc
    with running_server(workspace, port=port) as server:
        url = f'http://127.0.0.1:{server.server_port}/#token={server.token}'
        webview.settings['ALLOW_DOWNLOADS'] = True
        webview.settings['ALLOW_FILE_URLS'] = False
        webview.create_window(
            'Cosmos Oculto', url, width=1280, height=850,
            min_size=(900, 600), text_select=True, confirm_close=True,
        )
        print('COAE Desktop. Aguarde as tarefas terminarem antes de fechar.\n'
              'Acesso opcional no navegador: ' + url, flush=True)
        # GUI event loops must run on the main thread. No JS-to-Python bridge needed.
        webview.start(gui='edgechromium' if sys.platform == 'win32' else None)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Cosmos Oculto — janela desktop')
    parser.add_argument('--workspace', default=str(BASE))
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    load_env()
    try:
        run_desktop(args.workspace, args.port)
    except (Exception, KeyboardInterrupt) as exc:
        if isinstance(exc, KeyboardInterrupt):
            return 0
        print(f'Não foi possível abrir o desktop: {exc}\n'
              'No Windows, confira o WebView2 Runtime. Em ambiente sem tela, '
              'use python iniciar.py --no-browser.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
