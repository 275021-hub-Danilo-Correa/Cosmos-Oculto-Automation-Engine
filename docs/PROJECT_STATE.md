# Estado do projeto · v0.2

## Implementado

- Pacote externo `Cosmos_Oculto_GitHub_Continuacao.zip` integrado como nova base do repositório.
- Pacote `coae`, CLI e entidades originais preservados e atualizados de forma aditiva.
- Migração aditiva SQLite, integridade, versionamento e invalidação de dependências.
- Interface local em sete áreas: visão geral, roteiro, áudio, storyboard, imagens, exportação e auditorias.
- Roteiro editável, fontes fornecidas pelo usuário, auditoria e correção limitada opcional com Gemini.
- Exportação para Dark Planner com pausas preservadas. Nenhuma geração de voz.
- Ingestão real WAV/MP3/M4A, duração medida, originais preservados e vínculo ao roteiro.
- Provider local faster-whisper com timestamps de palavras; importação assistida de JSON também disponível.
- Propostas locais por frase/pausa; agrupamento semântico opcional por Gemini, com tempos definidos pelo código.
- Edição, divisão/união e aprovação de storyboard; timeline visual contínua sem duração fixa.
- Descrições visuais, geração Gemini, importação de imagens, auditoria multimodal e correção limitada.
- Exportação de prompts, imagens, áudio, timeline JSON/CSV e legendas SRT/VTT para montagem manual.
- Histórico de tarefas/auditorias, limites por chamada e retomada de resultados persistidos.
- Bundle de projeto inclui snapshot consistente de `data/coae.sqlite3`, `BACKUP_README.txt`, artefatos e `project_state.json`.
- Preflight Gemini integrado antes da análise: valida variáveis, orçamento e SDK sem enviar chamada paga.
- Rotas `analyze` e `import_transcript` rejeitam Gemini inválido antes de criar job ou consumir upload.
- Análise local continua funcionando sem Gemini.
- Erros remotos Gemini agora distinguem cota `429`, credencial/permissão `401/403` e requisição inválida `400`.

## Validação realizada

FFmpeg 6.1.1/ffprobe foram instalados no ambiente Linux. O `.venv` do projeto foi criado com `faster-whisper 1.2.1` e `Pillow 12.3.0`.

43 testes Python passaram no workspace Linux **sem skips**, incluindo MP3 real via FFmpeg, o fluxo assistido com imagens de teste, a validação do snapshot SQLite no bundle e as regressões do preflight Gemini. O pacote externo foi executado isoladamente antes da integração e passou pela suíte anterior.

O provider `FasterWhisperProvider` foi executado com o modelo `tiny` em áudio falado sintético em português: carregou o modelo e produziu 9 segmentos com timestamps reais para um arquivo de 3,49 s. O texto reconhecido apresentou erros esperados da voz sintetizada; este teste valida a integração técnica, não a qualidade editorial da transcrição.

O smoke test HTTP local confirmou startup do servidor, carregamento do HTML do dashboard, bloqueio de `/api/state` sem token (`401`) e leitura autenticada do estado (`configured=false`, `ffprobe=false`). A compilação Python passou e os diagnósticos do workspace não apontaram erros.

O teste de MP3 real via FFmpeg foi reproduzido com sucesso. A importação e a análise de áudio real de usuário ainda não foram executadas; nenhum modelo Whisper foi baixado durante esta etapa.

O teste de bundle confirmou que o snapshot SQLite é legível e contém o projeto persistido. O bundle é uma cópia para análise/continuidade; ao mover o projeto para outra pasta, caminhos absolutos registrados no SQLite podem exigir rebase ou reimportação dos arquivos.

O preflight Gemini foi validado sem chamadas pagas: configuração ausente ou em branco, orçamento inválido/zerado/esgotado e SDK ausente preservam o banco e não iniciam transcrição. A rota HTTP também preserva o upload quando a validação falha.

Uma tentativa real de geração de imagem respondeu `429 RESOURCE_EXHAUSTED`: a cota gratuita da conta está em zero para o modelo de imagem. O sistema agora informa explicitamente cota excedida e não repete automaticamente a chamada.

Não foram executadas chamadas pagas de IA, download/execução real de modelo de fala, Windows ou revisão visual com navegador completo. Não confundir testes de contrato, fixtures e dados sintéticos com aprovação de qualidade audiovisual.

## Próximas etapas concretas

1. Validar o faster-whisper com um áudio humano real de 2–3 minutos do usuário; o modelo `tiny` já está disponível no cache, e modelos maiores poderão ser baixados conforme a configuração.
2. Ajustar reconhecimento e limites semânticos após comparar as cenas com a escuta.
3. Validar instalação Windows e o fluxo de áudio no Windows.
4. Validar um modelo de imagem da conta do usuário com um pequeno lote e avaliar custo/qualidade.
5. Evoluir formatos editoriais configuráveis, ingestão dos documentos de regras, SEO e exportação/renderização de movimento, conforme prioridades.

A especificação COAE_SPEC.md preservada descreve também funcionalidades futuras. Os estados e capacidades efetivamente disponíveis são os deste documento e do README.
