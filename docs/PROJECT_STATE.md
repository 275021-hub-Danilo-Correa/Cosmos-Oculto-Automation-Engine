# PROJECT STATE

## Concluído

- Estrutura Python inicial com CLI e SQLite persistente em `coae/`.
- Criação, listagem e abertura de projetos persistidos pelos comandos `create-project` e `open-project`.
- Criação da estrutura inicial de diretórios por projeto: `research`, `script`, `audio`, `transcription`, `storyboard`, `exports` e `logs`.
- Importação/salvamento de roteiro editável a partir de arquivo TXT/Markdown pelo comando `save-script`.
- Versionamento básico persistido em `scripts.version`; cada salvamento cria uma nova versão.
- Aprovação explícita pelo comando `approve-script`; apenas uma versão pode ficar aprovada.
- Exportação bloqueada para rascunhos e disponível somente para a versão aprovada.
- Exportação validada de `script_master.md`, `narration_darkplanner.txt` e `narration_clean.txt` pelo comando `export-script`.
- Retomada validada: fechar e reabrir o processo preserva projeto, roteiro, versão e aprovação no SQLite.
- Ingestão real de WAV com preservação do original, cópia de trabalho, duração e SHA-256.
- Contrato de provider de transcrição e leitura de segmentos alinhados em JSON.
- Segmentação com timestamps reais, validação de limites/overlaps e IDs previsíveis `SC001`.
- Persistência de transcrição e versões de storyboard.
- Testes automatizados do núcleo: **6 testes passando**, incluindo versionamento, aprovação, exportação e retomada.
- Smoke test concluído pela CLI para criar projeto, salvar roteiro, abrir estado, aprovar e exportar.
- Dashboard HTTP local funcional para criar projetos, salvar roteiros, aprovar versões e exportar o roteiro aprovado.
- Fluxo HTTP do dashboard coberto por teste automatizado; **7 testes passando**.

## Em desenvolvimento

- Upload de áudio pela interface e visualização/edição do storyboard ainda não estão disponíveis no dashboard.
- Provider local de transcrição usando FFmpeg e Whisper/faster-whisper.
- Auditoria do storyboard e edição manual.

## Próximo passo

1. Adicionar ao dashboard a importação de áudio e a visualização do storyboard persistido.
2. Instalar/configurar FFmpeg e um provider real de transcrição.
3. Executar o fluxo audio-first com áudio real e validar a retomada da transcrição/storyboard.
4. Somente após isso avançar para aprovação de storyboard e prompts visuais.

## Problemas conhecidos

- O ambiente atual não possui FFmpeg; MP3/M4A retornam `UNSUPPORTED_AUDIO` de forma explícita.
- Nenhum engine de transcrição está instalado; sem provider configurado o sistema deve retornar `PROVIDER_NOT_CONFIGURED`.
- O JSON alinhado usado nos testes é entrada de provider, não uma transcrição simulada da aplicação.
- A edição atual é feita por importação de arquivo via CLI; não há frontend de edição ainda.
- Não há servidor web, frontend, API paga ou integração automática com Dark Planner.

## Decisões tomadas

- SQLite e biblioteca padrão do Python nesta primeira fatia, sem dependências obrigatórias externas.
- Áudio importado é a fonte de verdade temporal.
- Cenas usam intervalos fornecidos pela transcrição e não slots fixos.
- O Dark Planner permanece no modo ASSISTED e recebe apenas texto narrável e tags de pausa.
- Exportações só podem ser produzidas a partir da versão de roteiro marcada como aprovada.
- A etapa atual parou no núcleo persistente de projeto/roteiro; imagens, animações, SEO, métricas, Shorts e comunidade ainda não foram implementados.

## Pendências externas

- Instalação local do FFmpeg.
- Escolha e configuração de um provider real de transcrição.