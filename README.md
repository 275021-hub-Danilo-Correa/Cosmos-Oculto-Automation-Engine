# Cosmos Oculto Automation Engine

Estúdio local para **roteiro → Dark Planner → áudio importado → cenas pela fala → descrições locais → imagens locais → pacote de edição**.

O caminho recomendado para o PC de casa é Ollama para texto e ComfyUI para imagens. O COAE não baixa modelos, não instala drivers de GPU e não faz fallback automático para APIs pagas. Gemini continua disponível como modo alternativo.

O COAE não gera voz, não exige cenas de oito segundos e não publica no YouTube. A interface abre no navegador do computador onde o backend e os serviços locais estão executando.

## Estado desta adaptação

- Suporte opcional a `COAE_TEXT_PROVIDER=ollama`.
- Suporte opcional a `COAE_IMAGE_PROVIDER=comfyui`.
- Serviços locais aceitam somente `127.0.0.1`/`localhost` por segurança.
- Descrições são geradas em lotes de até quatro cenas, preservando tempos e campos já preenchidos.
- Imagens locais usam workflow API SDXL, tickets persistidos e retomada por `prompt_id`.
- Imagens locais ficam em `REVIEW_REQUIRED` e exigem revisão humana.
- Vídeo, Veo, thumbnails dedicadas e renderização final ainda não fazem parte desta adaptação.

Consulte [docs/LOCAL_AI.md](docs/LOCAL_AI.md) para o procedimento completo no PC de casa.

## Programar com Codex no outro PC

Os seis perfis de desenvolvimento ficam em `.codex/agents/`, com instruções comuns
em [AGENTS.md](AGENTS.md). Siga [docs/AGENTES.md](docs/AGENTES.md) para transferir
esta versão, preparar o ambiente e iniciar a sessão no outro computador.
Desenvolver com Codex e executar Ollama/ComfyUI na GPU são etapas separadas.

## Abrir no Windows

1. Extraia TODO o repositório para uma pasta. Não execute de dentro do arquivo compactado.
2. Instale Python **3.12 ou superior**, com a opção **Add Python to PATH**.
3. Abra `INSTALAR_WINDOWS.bat`. Ele cria `.venv` e instala as dependências Python do COAE. Ollama, ComfyUI, modelos e drivers são instalados separadamente.
4. Instale e teste Ollama e ComfyUI separadamente, depois abra `INICIAR_WINDOWS.bat`. Mantenha o terminal aberto; o navegador mostra o estúdio.
5. Para importar MP3/M4A, instale FFmpeg e inclua sua pasta `bin` no PATH. `ffprobe -version` deve funcionar em um terminal novo. WAV PCM permite começar sem essa instalação.

O programa não é um `.exe` independente. Os `.bat` iniciam o código Python. O instalador Windows foi inspecionado, mas não executado em Windows neste ambiente Linux.

### Restaurar ou desmembrar o storyboard

Na aba **Storyboard**, a área **Restaurar uma versão anterior** mostra o histórico e a quantidade de cenas de cada versão. Selecione uma versão anterior e confirme para criar uma nova versão, preservando o histórico e exigindo nova aprovação.

O botão **Desmembrar por frases e pausas** recalcula as divisões localmente usando a transcrição já salva. Não chama Gemini, não transcreve novamente e reinicia as descrições visuais porque os trechos podem mudar.

## Fluxo recomendado em casa

1. **Roteiro:** crie um projeto, cole fontes e referências, escreva/importe o texto ou use Gemini. Audite, revise e aprove. A exportação preserva as pausas `<break time="1s"/>` existentes, sem inventar outras.
2. **Dark Planner:** use o TXT exportado para produzir a voz por sua conta. Baixe o áudio.
3. **Áudio:** importe WAV, MP3 ou M4A, escute no player e aprove.
4. **Análise:** clique em **Analisar áudio e criar cenas**. O faster-whisper reconhece a fala localmente com tempos por palavra. A divisão inicial usa frases e pausas.
5. **Storyboard:** escute os trechos; ajuste início/fim, divida ou una cenas; confira a ideia e a imagem necessária. Audite e aprove. As imagens ocupam a timeline inteira, incluindo pausas. Tempos de reconhecimento são estimativas a revisar, não precisão garantida.
6. **Descrições e imagens:** em modo local, use **Completar descrições com Ollama local** e depois gere uma cena por vez com ComfyUI. A imagem é importada para o projeto e fica aguardando revisão humana. Também é possível importar imagens 16:9 produzidas em outra ferramenta.
7. **Exportar:** gere timeline JSON/CSV, legendas SRT/VTT e baixe o pacote com áudio e imagens. Use os tempos para montar no editor.

**Cenas nesta versão são unidades de planejamento e montagem com imagens estáticas.** Movimentos são sugestões. Não há geração automática de clipes animados nem renderização de vídeo final, e os arquivos não são projetos nativos do CapCut.

## Configuração de IA local

No PC de casa, copie `.env.local.example` para os valores do seu `.env` e preencha o nome exato dos modelos instalados:

```ini
COAE_TEXT_PROVIDER=ollama
COAE_IMAGE_PROVIDER=comfyui
COAE_OLLAMA_URL=http://127.0.0.1:11434
COAE_LOCAL_WRITER_MODEL=nome-exato-do-modelo
COAE_LOCAL_AUDITOR_MODEL=
COAE_LOCAL_VISION_MODEL=
COAE_COMFYUI_URL=http://127.0.0.1:8188
COAE_COMFYUI_WORKFLOW=workflows/sdxl_local.json
COAE_COMFYUI_PROMPT_NODE=6
COAE_COMFYUI_OUTPUT_NODE=9
COAE_LOCAL_TIMEOUT=600
COAE_MAX_CALLS_PER_PROJECT=0
```

Use `ollama list` para confirmar o modelo. No ComfyUI, copie `workflows/sdxl_api.example.json` para `workflows/sdxl_local.json` e substitua o checkpoint pelo arquivo real. Não use o JSON visual do ComfyUI; a integração espera o formato API.

Não instale CUDA na RX 7800 XT. Instale Ollama e ComfyUI conforme o suporte AMD/Windows atual, em instalações próprias e separadas do `.venv` do COAE. Nenhum modelo é baixado automaticamente.

## Gemini alternativo

Copie `.env.example` para `.env`, na pasta de `iniciar.py`. Preencha:

```ini
GEMINI_API_KEY=sua_chave
COAE_WRITER_MODEL=modelo_de_texto_disponivel_na_sua_conta
COAE_AUDITOR_MODEL=modelo_multimodal_disponivel_na_sua_conta
COAE_IMAGE_MODEL=modelo_gemini_que_gera_imagens
COAE_MAX_CALLS_PER_PROJECT=20
COAE_WHISPER_MODEL=small
```

Use IDs de modelos disponíveis na sua conta e compatíveis com cada função. O gerador implementado usa `generate_content` com saída de imagem do Gemini; não aceita um ID arbitrário de Imagen. Nenhuma chave acompanha o projeto. Não publique seu `.env`.

O limite padrão é **zero**: nenhuma chamada remota habilitada. O teto é acumulado por projeto e contabiliza tentativas, inclusive falhas de resultado desconhecido. **Não é um teto de dinheiro.** Geração em lote e correções usam várias chamadas; confira cobrança e limites do provedor antes de habilitar. Reinicie o programa após editar `.env`.

O modo Gemini pode continuar sendo usado com `COAE_TEXT_PROVIDER=gemini` e `COAE_IMAGE_PROVIDER=gemini`, mas depende de chave, modelos disponíveis, faturamento e cotas específicas. Não há fallback automático entre Gemini e os serviços locais.

## Como funciona a autoauditoria

- Código verifica arquivos, hashes, duração real, vínculo entre projeto/roteiro/áudio, intervalos e cobertura da timeline.
- Gemini pode revisar roteiro e imagens; respostas inválidas são rejeitadas.
- Correções de roteiro e imagens têm limite de três tentativas adicionais; erros não são convertidos em aprovação por uma nota arbitrária.
- Pendências, versões, tarefas e chamadas ficam no SQLite e nos arquivos de auditoria.
- Trocar áudio, aprovar outro roteiro, mudar fontes ou criar outro storyboard invalida materiais dependentes.
- Imagens existentes válidas não são recriadas pelo lote; lotes de descrição já persistidos podem ser retomados. Transcrição interrompida precisa ser executada novamente; não há checkpoint palavra a palavra.
- Revisão científica, escuta e aprovação continuam necessárias. A IA não certifica fatos nem verifica automaticamente as URLs fornecidas.

## Atualizar uma cópia antiga

Feche o programa e faça cópia de segurança da pasta inteira, principalmente `data/` e `projects/`. Copie o código novo para a pasta do projeto antigo, preservando essas duas pastas e seu `.env`.

O estúdio utiliza `data/coae.sqlite3` e `projects/` ao lado de `iniciar.py`, como o CLI original. A migração é aditiva: preserva registros e acrescenta colunas/tabelas. Caminhos relativos de áudio são resolvidos nessa pasta. Storyboards antigos sem vínculo comprovável ao áudio são mantidos como desatualizados e precisam de nova análise. Se arquivos estavam fora da pasta do projeto, reimporte-os.

O ZIP de download de um projeto contém mídia, exports, um retrato JSON do estado e um snapshot consistente de `data/coae.sqlite3`. Preserve o arquivo `data/coae.sqlite3` ao retomar o projeto; se mover a pasta para outro caminho, confira os caminhos registrados no banco. Para backup integral de vários projetos, feche o estúdio e copie `data/` e `projects/` juntos.

## Linux / macOS e comandos

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-audio.txt -r requirements-images.txt -r requirements-api.txt
.venv/bin/python iniciar.py
```

Pasta alternativa e porta:

```bash
python iniciar.py --workspace /caminho/para/pasta --port 8766
```

O servidor escuta apenas em `127.0.0.1` por padrão; destina-se a uso local. O CLI original permanece disponível:

```bash
python -m coae.cli --help
python -m coae.cli --database data/coae.sqlite3 open-project
python -m unittest discover -s tests -v
```

## Validação e limites desta entrega

**67 testes passaram**: CLI, persistência, áudio WAV/MP3, storyboard, histórico, bundle SQLite, preflight Gemini e adaptadores locais Ollama/ComfyUI com servidores de protocolo simulados. Nenhum modelo local ou GPU foi executado nesta entrega.

Os testes usam áudio sintético e transcrição alinhada de teste. Não houve reconhecimento de uma narração real nem chamadas pagas de Gemini nesta entrega. A interface foi testada funcionalmente com JSDOM; não houve inspeção visual em navegador completo. SEO automático, animação, renderização final, pesquisa científica automática e formatos editoriais configuráveis ainda não estão implementados. O gerador de roteiro atual solicita vídeo regular de 20–25 minutos, sem certificação automática da duração narrada.

Veja [docs/LOCAL_AI.md](docs/LOCAL_AI.md) para instalação e handoff, [docs/ANALISE_DO_PROJETO.md](docs/ANALISE_DO_PROJETO.md) para o histórico técnico e [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md) para o estado atual. A especificação em `docs/COAE_SPEC.md` continua sendo o roteiro de evolução, não uma lista de funcionalidades concluídas.
