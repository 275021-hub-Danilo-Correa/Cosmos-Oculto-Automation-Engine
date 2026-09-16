# Capacidades dos providers

## Disponível nesta fase

| Provider | Capacidade | Modo | Observação |
| --- | --- | --- | --- |
| `JsonTranscriptProvider` | Lê segmentos já alinhados com `start`, `end` e `text` | ASSISTED | Não transcreve áudio; recebe resultado produzido por outro motor |
| WAV local | Mede duração, calcula SHA-256 e cria cópia de trabalho | OFFLINE | Usa a biblioteca padrão do Python |

## Dependências externas

| Capacidade | Estado |
| --- | --- |
| MP3/M4A, normalização e inspeção via FFmpeg | Requer instalação local do FFmpeg |
| Whisper/faster-whisper/WhisperX | Provider ainda não configurado |
| Dark Planner | Fluxo ASSISTED; não há automação de interface nem API presumida |