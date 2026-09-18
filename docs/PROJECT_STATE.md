# Atualização 2026-09-18 — integração local preparada

## Direção atual

O próximo ambiente-alvo é o PC de casa com Windows, RX 7800 XT 16 GB, Ryzen 5600X e 32 GB de RAM. O Codespace atual serve para desenvolvimento e testes de protocolo; não deve receber modelos grandes nem instalações de GPU.

O caminho recomendado deixou de depender de cotas Gemini: Ollama fornece texto/descrições e ComfyUI fornece imagens locais. Gemini permanece como alternativa configurável, sem fallback automático.

## Concluído nesta etapa

- Providers configuráveis: Ollama para texto e ComfyUI local para imagens; sem fallback pago.
- Descrições em lotes de quatro cenas no modo local, preservando tempos e cenas já preenchidas.
- Workflow API SDXL de exemplo; requer checkpoint instalado/configurado pelo usuário.
- Tickets persistidos antes do envio, retomada por prompt_id, preservação das imagens prontas.
- Revisão humana obrigatória das imagens locais; auditoria visual IA opcional com modelo capaz.
- Diagnóstico dos serviços na aba Auditorias e tarefas; rótulos mostram o provider selecionado.
- Perfil de configuração e handoff em docs/LOCAL_AI.md.
- README remodelado para apresentar o fluxo local como caminho principal e Gemini como alternativa.

## Validação desta etapa

67 testes Python passaram, incluindo 13 testes com servidores HTTP simulados:
JSON inválido, preservação de timestamps/descrições, imagem persistida, retomada,
envio incerto, bloqueio de cloud, visão indisponível, nós não permitidos, diagnóstico,
autenticação HTTP e preservação de bloqueio de auditoria. Nenhum modelo real foi chamado.
Compilação Python, sintaxe JS e git diff --check passaram. Smoke test JSDOM + HTTP
confirmou abertura das sete abas, criação de projeto/roteiro, botão ComfyUI local e
diagnóstico de serviço indisponível. JSDOM não é revisão visual de navegador completo.

## Pendências externas e próximo passo

Não instalar Ollama, ComfyUI ou modelos grandes neste Codespace. Validar os serviços e uma imagem no Windows com RX 7800 XT 16 GB, Ryzen 5600X,
32 GB RAM. Nenhum download de modelo nem teste real AMD/GPU ocorreu nesta entrega.
Geração de vídeo/thumbnail, autocorreção visual local e fila global de GPU não foram
implementadas. A fila é sequencial por projeto; não executar vários projetos na GPU
simultaneamente durante a validação inicial. Tickets sem confirmação exigem reconciliação.

As mudanças foram integradas localmente, mas ainda não foram publicadas no GitHub. No PC de casa, preserve `.env`, `data/` e `projects/`, confira a branch e execute os testes antes de instalar serviços. Siga docs/LOCAL_AI.md.

---

O registro abaixo é histórico da versão anterior. Suas validações pertencem às
respectivas sessões e não substituem as limitações explicitadas acima.

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
- Completar descrições do storyboard corrigido: `gemini-2.5-flash` retornava `404`; escritor e auditor agora usam `gemini-3.1-flash-lite-preview`, validado com resposta JSON.
- Indisponibilidade temporária `503` agora recebe mensagem específica, sem retry automático.
- Histórico do storyboard agora permite restaurar uma versão anterior em nova versão, sem reaproveitar aprovação/imagens.
- Storyboard agora permite desmembrar localmente por frases e pausas usando a transcrição salva, sem nova transcrição ou chamada Gemini.
- Alterações de storyboard validam versão em tela, áudio/transcrição compatíveis e tarefas concorrentes antes de criar revisão.

## Validação realizada

FFmpeg 6.1.1/ffprobe foram instalados no ambiente Linux. O `.venv` do projeto foi criado com `faster-whisper 1.2.1` e `Pillow 12.3.0`.

54 testes Python passaram no workspace Linux **sem skips**, incluindo MP3 real via FFmpeg, o fluxo assistido com imagens de teste, a validação do snapshot SQLite no bundle, as regressões do preflight Gemini, os diagnósticos de modelos 404/503 e o histórico/restauração/divisão do storyboard.

O provider `FasterWhisperProvider` foi executado com o modelo `tiny` em áudio falado sintético em português: carregou o modelo e produziu 9 segmentos com timestamps reais para um arquivo de 3,49 s. O texto reconhecido apresentou erros esperados da voz sintetizada; este teste valida a integração técnica, não a qualidade editorial da transcrição.

O smoke test HTTP local confirmou startup do servidor, carregamento do HTML do dashboard, bloqueio de `/api/state` sem token (`401`) e leitura autenticada do estado (`configured=false`, `ffprobe=false`). A compilação Python passou e os diagnósticos do workspace não apontaram erros.

O teste de MP3 real via FFmpeg foi reproduzido com sucesso. A importação e a análise de áudio real de usuário ainda não foram executadas; nenhum modelo Whisper foi baixado durante esta etapa.

O teste de bundle confirmou que o snapshot SQLite é legível e contém o projeto persistido. O bundle é uma cópia para análise/continuidade; ao mover o projeto para outra pasta, caminhos absolutos registrados no SQLite podem exigir rebase ou reimportação dos arquivos.

O projeto `COAE-BA0592A3` continua preservado no banco local. A atualização não restaura nem desmembra automaticamente o storyboard real; a operação deve ser feita na aba Storyboard, com confirmação do usuário.

O preflight Gemini foi validado sem chamadas pagas: configuração ausente ou em branco, orçamento inválido/zerado/esgotado e SDK ausente preservam o banco e não iniciam transcrição. A rota HTTP também preserva o upload quando a validação falha.

Uma tentativa real de geração de imagem respondeu `429 RESOURCE_EXHAUSTED`: a cota gratuita da conta está em zero para o modelo de imagem. O sistema agora informa explicitamente cota excedida e não repete automaticamente a chamada.

As tentativas de completar descrições registraram `404` porque `gemini-2.5-flash` deixou de estar disponível para novos usuários. O modelo de texto alternativo foi testado com sucesso; a geração de imagens continua sujeita à cota específica do modelo de imagem.

Não foram executadas chamadas pagas de IA, download/execução real de modelo de fala, Windows ou revisão visual com navegador completo. Não confundir testes de contrato, fixtures e dados sintéticos com aprovação de qualidade audiovisual.

## Próximas etapas concretas

1. Validar o faster-whisper com um áudio humano real de 2–3 minutos do usuário; o modelo `tiny` já está disponível no cache, e modelos maiores poderão ser baixados conforme a configuração.
2. Ajustar reconhecimento e limites semânticos após comparar as cenas com a escuta.
3. Validar instalação Windows e o fluxo de áudio no Windows.
4. Validar um modelo de imagem da conta do usuário com um pequeno lote e avaliar custo/qualidade.
5. Evoluir formatos editoriais configuráveis, ingestão dos documentos de regras, SEO e exportação/renderização de movimento, conforme prioridades.

A especificação COAE_SPEC.md preservada descreve também funcionalidades futuras. Os estados e capacidades efetivamente disponíveis são os deste documento e do README.
