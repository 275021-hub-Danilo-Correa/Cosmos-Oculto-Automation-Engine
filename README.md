# Cosmos Oculto — continuação do projeto enviado · v0.2

Estúdio local em Python para **roteiro → voz feita por você no Dark Planner → áudio importado → cenas pela fala → imagens → pacote de edição**.

Esta versão continua o pacote `coae` do ZIP original. Não gera voz, não exige cenas de oito segundos e não publica no YouTube. A interface abre no navegador do seu computador.

## Abrir no Windows

1. Extraia TODO o ZIP para uma pasta. Não execute de dentro do arquivo compactado.
2. Instale Python **3.12 ou superior**, com a opção **Add Python to PATH**.
3. Abra `INSTALAR_WINDOWS.bat`. Ele cria `.venv` e instala reconhecimento de voz, tratamento de imagens e integração Gemini. Precisa de internet e espaço para as dependências.
4. Abra `INICIAR_WINDOWS.bat`. Mantenha o terminal aberto; o navegador mostra o estúdio. Se necessário, copie o endereço completo mostrado no terminal.
5. Para importar MP3/M4A, instale FFmpeg e inclua sua pasta `bin` no PATH. `ffprobe -version` deve funcionar em um terminal novo. WAV PCM permite começar sem essa instalação.

O programa não é um `.exe` independente. Os `.bat` iniciam o código Python. O instalador Windows foi inspecionado, mas não executado em Windows neste ambiente Linux.

## Seu fluxo de produção

1. **Roteiro:** crie um projeto, cole fontes e referências, escreva/importe o texto ou use Gemini. Audite, revise e aprove. A exportação preserva as pausas `<break time="1s"/>` existentes, sem inventar outras.
2. **Dark Planner:** use o TXT exportado para produzir a voz por sua conta. Baixe o áudio.
3. **Áudio:** importe WAV, MP3 ou M4A, escute no player e aprove.
4. **Análise:** clique em **Analisar áudio e criar cenas**. O faster-whisper reconhece a fala localmente com tempos por palavra. Na primeira execução, baixa o modelo; isso pode demorar. Com Gemini habilitado, o sistema agrupa ideias e escreve descrições visuais. Sem Gemini, a divisão inicial usa frases e pausas, e você completa as descrições.
5. **Storyboard:** escute os trechos; ajuste início/fim, divida ou una cenas; confira a ideia e a imagem necessária. Audite e aprove. As imagens ocupam a timeline inteira, incluindo pausas. Tempos de reconhecimento são estimativas a revisar, não precisão garantida.
6. **Imagens:** gere por cena ou em lote com Gemini, ou importe imagens 16:9 produzidas em outra ferramenta. A geração usa a descrição visual ligada à fala. A auditoria de visão aponta defeitos; a correção automática tenta até três novas gerações. A aprovação final fica com você.
7. **Exportar:** gere timeline JSON/CSV, legendas SRT/VTT e baixe o pacote com áudio e imagens. Use os tempos para montar no editor.

**Cenas nesta versão são unidades de planejamento e montagem com imagens estáticas.** Movimentos são sugestões. Não há geração automática de clipes animados nem renderização de vídeo final, e os arquivos não são projetos nativos do CapCut.

## Configurar a IA opcional

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

É possível trabalhar sem Gemini: roteiro manual, transcrição local, descrição visual manual e importação de imagens. Nenhuma integração TTS é utilizada.

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

O ZIP de download de um projeto contém mídia, exports e um retrato JSON do estado, **não um backup restaurável do banco inteiro**. Para backup completo, feche o estúdio e copie `data/` e `projects/` juntos.

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

**34 testes passaram**: CLI, persistência, áudio WAV/MP3, integridade, isolamento entre projetos, versões, bloqueios, orçamento por chamadas e fluxo assistido até timeline. Também houve teste HTTP/DOM da autenticação, criação de projeto, salvamento de roteiro e sete áreas da interface.

Os testes usam áudio sintético e transcrição alinhada de teste. Não houve reconhecimento de uma narração real nem chamadas pagas de Gemini nesta entrega. A interface foi testada funcionalmente com JSDOM; não houve inspeção visual em navegador completo. SEO automático, animação, renderização final, pesquisa científica automática e formatos editoriais configuráveis ainda não estão implementados. O gerador de roteiro atual solicita vídeo regular de 20–25 minutos, sem certificação automática da duração narrada.

Veja `docs/ANALISE_DO_PROJETO.md` para os problemas encontrados no original e `docs/PROJECT_STATE.md` para o estado atualizado. A especificação original permanece em `docs/COAE_SPEC.md` como roteiro de evolução, não como lista de funcionalidades concluídas.
