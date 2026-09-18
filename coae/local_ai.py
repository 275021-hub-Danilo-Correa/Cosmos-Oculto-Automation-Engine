"""Explicit local HTTP adapters; no model downloads or cloud fallback."""
from __future__ import annotations
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
from .provider import SYSTEM


def backend(kind):
    value = os.getenv(f'COAE_{kind.upper()}_PROVIDER', 'gemini').strip().lower()
    allowed = ('gemini', 'ollama') if kind == 'text' else ('gemini', 'comfyui')
    if value not in allowed:
        raise ValueError(f'COAE_{kind.upper()}_PROVIDER deve ser ' + ' ou '.join(allowed))
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Serviço local tentou redirecionar a conexão.')


class LocalHTTP:
    def __init__(self, url):
        p = urllib.parse.urlsplit(url)
        if (p.scheme != 'http' or p.hostname not in ('localhost', '127.0.0.1', '::1')
                or p.username or p.password or p.path not in ('', '/') or p.query or p.fragment):
            raise ValueError('Use endereço HTTP local: http://127.0.0.1:PORTA. Não exponha o serviço.')
        self.url = url.rstrip('/')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, route, data=None, timeout=10, binary=False):
        body = None if data is None else json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
        req = urllib.request.Request(self.url + route, data=body, headers={'Content-Type': 'application/json'})
        try:
            with self.opener.open(req, timeout=timeout) as r:
                raw = r.read(32 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as exc:
            raise ValueError(f'Serviço local respondeu HTTP {exc.code}. Confira modelo/workflow e o terminal do serviço.') from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ValueError('Serviço local indisponível ou tempo esgotado. Inicie o serviço neste computador e confira a porta.') from None
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError('Resposta local excedeu 32 MB.')
        if binary:
            return raw
        try:
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except (ValueError, UnicodeDecodeError):
            raise ValueError('Serviço local devolveu JSON inválido.') from None


def timeout_seconds():
    try:
        value = int(os.getenv('COAE_LOCAL_TIMEOUT', '600'))
    except ValueError:
        raise ValueError('COAE_LOCAL_TIMEOUT deve ser inteiro entre 10 e 3600.') from None
    if not 10 <= value <= 3600:
        raise ValueError('COAE_LOCAL_TIMEOUT deve estar entre 10 e 3600 segundos.')
    return value


class Ollama:
    def __init__(self):
        self.http = LocalHTTP(os.getenv('COAE_OLLAMA_URL', 'http://127.0.0.1:11434'))
        self.writer = os.getenv('COAE_LOCAL_WRITER_MODEL', '').strip()
        self.auditor = os.getenv('COAE_LOCAL_AUDITOR_MODEL', '').strip() or self.writer
        self.vision = os.getenv('COAE_LOCAL_VISION_MODEL', '').strip()
        self.timeout = timeout_seconds()
        if not self.writer:
            raise ValueError('Configure COAE_LOCAL_WRITER_MODEL com o nome de um modelo instalado no Ollama.')

    def check(self, vision=False):
        tags = self.http.request('/api/tags')
        names = {r.get('name') for r in tags.get('models', []) if isinstance(r, dict)}
        selected = {self.vision} if vision else {self.writer, self.auditor}
        for name in selected:
            if not name or (name not in names and name + ':latest' not in names):
                raise ValueError('Modelo local não instalado. Confira os nomes COAE_LOCAL_* no .env e ollama list.')
            # Cloud models can appear in local Ollama. Reject explicitly.
            info = self.http.request('/api/show', {'model': name})
            if info.get('remote_host') or info.get('remote_model') or 'cloud' in name.lower():
                raise ValueError('Este perfil aceita somente modelos locais, sem encaminhamento cloud.')
            if vision and 'vision' not in info.get('capabilities', []):
                raise ValueError('O modelo escolhido não declara capacidade visual.')
        return {'message': 'Ollama acessível; modelos instalados. Geração e GPU ainda precisam de teste real.'}

    def call(self, task, payload, audit=False, image=None):
        self.check(vision=bool(image))
        content = json.dumps({'task': task, 'data': payload}, ensure_ascii=False)
        if len(content) > 180000:
            raise ValueError('Entrada excede 180 mil caracteres. Divida o trabalho.')
        message = {'role': 'user', 'content': content}
        if image:
            if len(image[0]) > 10 * 1024 * 1024:
                raise ValueError('Imagem excede 10 MB para auditoria.')
            message['images'] = [base64.b64encode(image[0]).decode('ascii')]
        result = self.http.request('/api/chat', {
            'model': self.vision if image else self.auditor if audit else self.writer,
            'messages': [{'role': 'system', 'content': SYSTEM}, message],
            'format': 'json', 'stream': False, 'keep_alive': 0,
            'options': {'temperature': .2 if audit else .6},
        }, timeout=self.timeout)
        try:
            if not result.get('done') or result.get('done_reason') == 'length':
                raise ValueError()
            value = json.loads(result['message']['content'])
            if not isinstance(value, dict):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            raise ValueError('Ollama devolveu resposta incompleta ou JSON inválido; versão anterior preservada.') from None
        return value, {'provider': 'ollama', 'input_tokens': result.get('prompt_eval_count'),
                       'output_tokens': result.get('eval_count')}


class ComfyUI:
    # Deliberately restrict the first integration to native local SD/SDXL nodes.
    ALLOWED = {'CheckpointLoaderSimple', 'CLIPTextEncode', 'EmptyLatentImage',
               'KSampler', 'VAEDecode', 'SaveImage'}

    def __init__(self):
        self.http = LocalHTTP(os.getenv('COAE_COMFYUI_URL', 'http://127.0.0.1:8188'))
        self.timeout = timeout_seconds()
        path = os.getenv('COAE_COMFYUI_WORKFLOW', '').strip()
        if not path:
            raise ValueError('Configure COAE_COMFYUI_WORKFLOW com um workflow JSON no formato API.')
        p = Path(path)
        if not p.is_absolute():
            p = Path(__file__).resolve().parents[1] / p
        try:
            self.workflow = json.loads(p.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            raise ValueError('Workflow ComfyUI ausente ou JSON inválido.') from None
        if not isinstance(self.workflow, dict) or not self.workflow:
            raise ValueError('Workflow deve ser um objeto de nós no formato API.')
        for node in self.workflow.values():
            if not isinstance(node, dict) or node.get('class_type') not in self.ALLOWED or not isinstance(node.get('inputs'), dict):
                raise ValueError('Este perfil aceita somente os nós locais do exemplo SDXL. Nós de API e customizados não são aceitos.')
        self.positive = os.getenv('COAE_COMFYUI_PROMPT_NODE', '6')
        self.output = os.getenv('COAE_COMFYUI_OUTPUT_NODE', '9')
        if self.workflow.get(self.positive, {}).get('class_type') != 'CLIPTextEncode' or self.workflow.get(self.output, {}).get('class_type') != 'SaveImage':
            raise ValueError('Confira COAE_COMFYUI_PROMPT_NODE e COAE_COMFYUI_OUTPUT_NODE.')
        for node in self.workflow.values():
            if node['class_type'] == 'EmptyLatentImage':
                inputs = node['inputs']
                w, h = inputs.get('width'), inputs.get('height')
                if type(w) is not int or type(h) is not int or not (64 <= w <= 2048 and 64 <= h <= 2048) or abs(w / h - 16 / 9) > .04 or inputs.get('batch_size') != 1:
                    raise ValueError('Use uma imagem por execução, 16:9, dimensões entre 64 e 2048 pixels.')

    def check(self):
        self.http.request('/system_stats')
        info = self.http.request('/object_info')
        for node in self.workflow.values():
            if node['class_type'] not in info:
                raise ValueError('Workflow usa um nó não disponível neste ComfyUI.')
            if node['class_type'] == 'CheckpointLoaderSimple':
                choices = info[node['class_type']]['input']['required']['ckpt_name'][0]
                if node['inputs'].get('ckpt_name') not in choices:
                    raise ValueError('Checkpoint do workflow não instalado. Ajuste ckpt_name para um arquivo disponível no ComfyUI.')
        return {'message': 'ComfyUI acessível e checkpoint encontrado. Ainda é necessário gerar uma imagem para validar a GPU.'}

    def generate(self, prompt, ticket, persist):
        workflow = json.loads(json.dumps(self.workflow))
        workflow[self.positive]['inputs']['text'] = prompt
        # Fingerprint binds resumed output to both server and exact workflow.
        fingerprint = hashlib.sha256(json.dumps([self.http.url, workflow], sort_keys=True).encode()).hexdigest()
        if ticket:
            if ticket.get('fingerprint') != fingerprint:
                raise ValueError('Configuração mudou durante uma geração pendente. Reconcilie o ticket em logs/local_images antes de continuar.')
            if not ticket.get('prompt_id'):
                raise ValueError('Envio anterior sem confirmação. Confira a fila do ComfyUI e o ticket em logs/local_images; não será reenviado automaticamente.')
        else:
            self.check()
            ticket = {'fingerprint': fingerprint, 'status': 'SUBMITTING'}
            persist(ticket)  # Mark before submitting: no duplicate after ambiguous failure.
            result = self.http.request('/prompt', {'prompt': workflow})
            if result.get('error') or result.get('node_errors') or not isinstance(result.get('prompt_id'), str):
                raise ValueError('ComfyUI rejeitou o workflow. Confira os nós no ComfyUI e reconcilie o ticket.')
            ticket.update(prompt_id=result['prompt_id'], status='QUEUED')
            persist(ticket)
        prompt_id = ticket['prompt_id']
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            history = self.http.request('/history/' + urllib.parse.quote(prompt_id, safe=''))
            result = history.get(prompt_id)
            if result:
                status = result.get('status', {})
                if status.get('status_str') == 'error':
                    ticket['status'] = 'FAILED'; persist(ticket)
                    raise ValueError('ComfyUI falhou. Confira memória, checkpoint e terminal. Ticket preservado para diagnóstico.')
                outputs = result.get('outputs', {}).get(self.output, {}).get('images', [])
                if status.get('completed') and outputs:
                    desc = outputs[0]
                    if not isinstance(desc, dict) or not desc.get('filename') or desc.get('type') != 'output':
                        raise ValueError('ComfyUI não retornou uma imagem de saída válida.')
                    raw = self.http.request('/view?' + urllib.parse.urlencode({k: desc.get(k, '') for k in ('filename', 'subfolder', 'type')}), binary=True)
                    from PIL import Image
                    try:
                        with Image.open(io.BytesIO(raw)) as im:
                            if abs(im.width / im.height - 16/9) > .04:
                                raise ValueError('Imagem gerada não está em 16:9.')
                            out = io.BytesIO(); im.save(out, format='PNG')
                    except (OSError, SyntaxError):
                        raise ValueError('ComfyUI retornou um arquivo de imagem inválido.') from None
                    ticket['status'] = 'DONE'; persist(ticket)
                    return out.getvalue(), {'provider': 'comfyui', 'prompt_id': prompt_id}
                if status.get('completed'):
                    raise ValueError('Workflow terminou sem imagem no nó de saída configurado.')
            time.sleep(1)
        raise ValueError('Tempo de espera esgotado; a tarefa pode continuar no ComfyUI. Clique novamente para consultar o mesmo ticket sem reenviar.')


def diagnostics():
    results = []
    for label, enabled, factory in [('Texto', backend('text') == 'ollama', Ollama),
                                    ('Imagens', backend('image') == 'comfyui', ComfyUI)]:
        if not enabled:
            results.append({'service': label, 'status': 'NOT_SELECTED', 'message': 'Serviço local não selecionado no .env.'})
            continue
        try:
            results.append({'service': label, 'status': 'READY_TO_TEST', **factory().check()})
        except (ValueError, KeyError, TypeError) as exc:
            results.append({'service': label, 'status': 'UNAVAILABLE', 'message': str(exc)})
    return {'services': results, 'message': ' | '.join(r['service'] + ': ' + r['message'] for r in results)}
