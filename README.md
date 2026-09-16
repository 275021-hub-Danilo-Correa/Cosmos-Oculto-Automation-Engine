# COAE

Cosmos Oculto Automation Engine: núcleo local para projetos documentais com roteiro, exportação para Dark Planner, ingestão de áudio e storyboard orientado por timestamps reais.

## Requisitos

- Python 3.12 ou superior
- FFmpeg para MP3/M4A e transcrição local que o utilize

O núcleo atual não depende de pacotes Python externos. O ambiente sem FFmpeg ainda permite executar o fluxo completo com WAV e um provider de transcrição alinhada.

## Executar

```bash
python3 -m unittest discover -s tests -v
python3 -m coae.cli --database data/coae.sqlite3 create-project "Buracos negros"
```

O comando de criação imprime o ID persistido do projeto e cria sua estrutura inicial de diretórios. Liste ou abra projetos já existentes com:

```bash
python3 -m coae.cli --database data/coae.sqlite3 open-project
python3 -m coae.cli --database data/coae.sqlite3 open-project COAE-XXXXXXXX
```

Salve uma nova versão editável do roteiro a partir de um arquivo de texto ou Markdown:

```bash
python3 -m coae.cli --database data/coae.sqlite3 save-script \
	COAE-XXXXXXXX "Buracos negros" roteiro.txt
python3 -m coae.cli --database data/coae.sqlite3 approve-script COAE-XXXXXXXX 1
```

Somente uma versão aprovada pode ser exportada:

```bash
python3 -m coae.cli --database data/coae.sqlite3 export-script \
	COAE-XXXXXXXX --output exports/COAE-XXXXXXXX
```

São gerados `script_master.md`, `narration_darkplanner.txt` com tags `<break time="..."/>` e `narration_clean.txt` sem tags técnicas.

Importe um WAV aprovado:

```bash
python3 -m coae.cli --database data/coae.sqlite3 import-audio \
	COAE-XXXXXXXX narracao.wav --project-dir projects/COAE-XXXXXXXX
```

O original é preservado, uma cópia de trabalho é criada, a duração é medida localmente e o SHA-256 é salvo no SQLite. MP3/M4A retornam erro explícito até FFmpeg estar instalado.

Para testar o alinhamento sem fingir uma transcrição, forneça um JSON produzido por um provider real:

```json
{"segments": [{"start": 0.0, "end": 2.4, "text": "Uma estrela colapsa."}]}
```

```bash
python3 -m coae.cli --database data/coae.sqlite3 transcribe \
	COAE-XXXXXXXX 1 transcript.json --audio-duration 2.4 --audio-path narracao.wav
```

## Estado atual

O SQLite persiste projetos, versões de roteiro, exports, áudios, transcrições e versões de storyboard. Fechar e reabrir o processo preserva o estado do projeto, rascunhos, aprovação e exports. A segmentação valida limites, duração positiva e overlaps; não existe regra de slots fixos de oito segundos.

A transcrição automática ainda é um provider externo/local a configurar. Imagens, movimentos, timeline, legendas e frontend ficam deliberadamente fora desta primeira fatia.
