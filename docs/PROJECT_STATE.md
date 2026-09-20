# Referências aprovadas e confiabilidade visual — 2026-09-20

- Pasta efetivamente encontrada: `D:\IA\Referencias` (o caminho fornecido não continha as duas subpastas sublinhadas). Inventário não destrutivo encontrou 2.677 imagens únicas; amostra estratificada de 16 imagens, hashes, metadados e contato visual em `workspace/reference_analysis/visual_audit_validation/`. Seis referências ficaram reservadas para verificação posterior, sem entrar no teste cego.
- Padrões observados: composição cinematográfica escura, espaço negativo, assunto dominante, iluminação azul/prata com âmbar contido e escala legível. Observatórios, pessoas, paisagens e laboratórios aparecem como conteúdo contextual de cenas específicas, não regras universais de estilo. Nomes de arquivo fornecem função em alguns casos; não foram convertidos em fala/prompt inexistente.
- Teste cego real do Ollama visual: candidatas 19/20, duas referências aprovadas do acervo e uma fotografia visualmente boa com fala incompatível. O modelo viu campo/animal e faixas, mas não deu erro bloqueante para a candidata 19; reprovou indevidamente uma referência de laboratório e devolveu categorias incompletas em dois casos. Relatório e saída bruta: `RELIABILITY_REPORT.md` e `blind_audit_first_pass.json`.
- Conclusão: auditor visual é apoio não confiável; revisão humana permanece obrigatória. O caminho de pixels funcionou nesta validação, mas o modelo apresenta falhas de percepção/julgamento e de contrato. Nenhum ajuste foi feito para acomodar as duas candidatas negativas; nenhuma aprovação real, mídia ou lote foi alterado. O workflow ComfyUI segue textual, sem condicionamento visual por referência e sem treinamento automático.

# Diagnóstico das candidatas negativas — 2026-09-19

- A rodada 11 da SC001 foi encerrada como `REJECTED` sem novo lote. As imagens 19 e 20 permanecem no histórico e receberam motivos persistidos: 19 contém moldura, paisagem e animal alheios à fala; 20 contém faixas verticais decorativas incompatíveis com o céu noturno. Nenhuma recomendação ou aprovação automática permanece.
- A auditoria visual agora envia os pixels do arquivo conferido junto de `image_id`, `scene_id`, `storyboard_id`, versão do storyboard e SHA-256. O prompt exige descrição objetiva dos elementos visíveis antes da comparação com fala, intenção e referências; critérios de moldura, faixas, texto ilegível e objetos estranhos são contextuais, não proibições universais.
- Candidatas bloqueadas por auditoria passam a `REJECTED`/`Reprovada` na fila e a interface não oferece aprovação. `100%` aparece apenas como conclusão do processamento, nunca como confiança ou qualidade. Histórico de auditorias anteriores e arquivos originais continuam preservados.
- A pasta de referências aprovadas ainda não foi informada. Nenhuma referência foi inventada, copiada ou usada como treinamento; a integração deverá catalogar arquivos, examinar pixels e enviar somente exemplos explicitamente selecionados quando o caminho for fornecido. Workflow atual aceita texto/negativo e não recebe condicionamento visual de referência; essa limitação deve ser mostrada na próxima etapa.
- Correção de codificação aplicada ao resumo da rodada e aos novos motivos. Testes direcionados de auditoria visual (4) e rodadas (3), compilação Python, sintaxe JavaScript e `git diff --check` passaram. Não houve geração de imagens.

# Identidade visual do canal — 2026-09-19

- Tema do COAE reformulado para a identidade Cosmos Oculto: fundo `#080B12`, sidebar `#0D111A`, painéis `#141B28`, bordas `#293244`, dourado `#D6AA60/#F0CF91` e textos prateados. As cores estão centralizadas em variáveis CSS; verde, âmbar e vermelho permanecem apenas como estados semânticos com texto e ícones.
- Sidebar compacta organizada em Projeto, Preparação, Estúdio, Montagem e Referências. Ação principal usa dourado; secundárias são neutras; rejeição/cancelamento usam tratamento de perigo. Recomendação da IA (`★`) e aprovação humana (`✓`) têm texto, ícone e bordas distintos.
- Marca tipográfica temporária “Cosmos Oculto · Documentários do Universo” aplicada com símbolo orbital simples. Nenhum logo original autorizado foi localizado no projeto ou no acervo pesquisado; a captura do YouTube não foi reutilizada.
- Mídias mantêm 16:9 e `object-fit: contain`, sem filtros. Formulários e grids não receberam fundo estrelado. Foco por teclado está visível e `prefers-reduced-motion` desativa transições. Razões de contraste verificadas: texto principal/fundo 16,36:1; secundário/fundo 8,9:1; dourado/fundo 9,16:1; texto escuro/botão dourado 8,5:1.
- Capturas reais do projeto `COAE-B89D2A1D`, sem dados de teste, em `workspace/validation/ui_theme/`: visão geral, Preparação/Roteiro, Estúdio com duas candidatas e auditoria aberta. Inspeção confirmou legibilidade, duas mídias lado a lado em 1920×1080 e ausência de sobreposição do rodapé. A barra de tarefas do Windows aparece nas capturas por serem validação real de tela.
- Validação: 112 testes Python passaram; `node --check coae/web/app.js`, `compileall`, `git diff --check` e inspeção visual das capturas passaram. Arquivos de interface: `coae/web/index.html`, `coae/web/style.css` e `coae/web/app.js`.

# Diagnóstico de qualidade da SC001 — 2026-09-19

- Imagens 11–14 e históricos reais do ComfyUI foram rastreados. O planeta vinha da descrição visual da SC001, apesar de não estar na fala; pedidos de fases estelares e o bloco corretivo longo favoreciam composição de diagrama. As regras do guia editorial ainda não chegavam ao gerador. O negativo já proibia texto, mas instruções tardias perdiam influência no condicionamento SDXL.
- O planejamento local agora deriva um prompt curto da fala, intenção e função narrativa, trata a descrição anterior como consultiva, inclui regras do guia e envia negativo efetivo contra texto, interface, infográfico, planeta e elementos rejeitados. Prompt positivo, negativo, seed, workflow e modelo ficam registrados por candidata. Fala e tempos da SC001 permanecem 0–7,38 s.
- Rodada 11 produziu somente duas novas candidatas concluídas, imagens 19 e 20, uma por vez. Ambas foram auditadas e nenhuma ficou aprovada. Inspeção direta: a 19 contém uma moldura com paisagem e animal; a 20 contém faixas verticais gráficas com pontos estelares. Comparadas à referência interna CO006/C001, faltam o assunto celeste isolado, o espaço negativo escuro e a composição ampla coerente. A rodada permanece sem recomendação.
- O modelo de visão local não reconheceu esses bloqueios com confiabilidade e chegou a recomendar a imagem 20. A recomendação foi anulada por verificação técnica, sem apagar imagens ou pareceres. O prompt do auditor agora declara que `ESTABLISH` deve estabelecer assunto e atmosfera e não pode ser penalizado por não demonstrar todas as fases; mesmo assim, o limite perceptivo do modelo permanece e exige revisão humana.
- WebSocket real do ComfyUI foi integrado com `client_id`, eventos `executing`/`progress` e prévias binárias. O backend estava com prévia desabilitada por padrão; o inicializador local passou a usar `--preview-method auto --preview-size 512` e saída em `D:\IA\ComfyUI\output`. Na rodada 11 houve percentuais e prévias reais persistidas em `projects/COAE-B89D2A1D/previews/live/`, sem simulação. Recarregar usa banco/ticket e não reenvia o trabalho.
- Arquivos finais: `projects/COAE-B89D2A1D/images/SC001_005_7fc4e0e23f.png` e `projects/COAE-B89D2A1D/images/SC001_005_8a00fca612.png`. Tentativas intermediárias falharam tecnicamente antes de produzir arquivo final, inclusive por diretório de saída do ComfyUI; o histórico foi preservado. Nenhum checkpoint ou modelo foi trocado.

# Rodadas e comparação de imagens — 2026-09-19

- Aba Imagens reorganizada por cena, em ordem do storyboard, com fala e tempos do áudio,
  grid de candidatas, ampliação, resumo de até duas frases e relatórios/histórico
  recolhidos. Recomendação da IA e aprovação humana têm destaques distintos; nenhuma
  recomendação aprova conteúdo.
- Rodadas persistentes aceitam 1–4 variações (padrão 2), seeds globais distintas e
  registram prompt, workflow, checkpoint, prompt_id, auditoria e estados. Uma fila
  compartilhada serializa a GPU. Recarregar a página retoma o acompanhamento pelo
  banco sem reenviar prompts; cancelamento preserva candidatas concluídas.
- Cada candidata concluída é auditada com a imagem real e o contexto da cena. A
  recomendação pode declarar “nenhuma adequada”. Falha de auditoria fica identificada
  como técnica. “Reprovar e gerar novas” cria uma única rodada, preserva arquivos e
  incorpora motivo opcional e problemas anteriores ao prompt. Só uma imagem pode
  permanecer aprovada por cena.
- Teste real COAE-B89D2A1D/SC001: rodada 1 gerou imagens 11 e 12 em sequência; a
  primeira auditoria teve HTTP 500 transitório e foi retentada com sucesso, a segunda
  concluiu, e a IA recomendou nenhuma. Rejeição real criou a rodada 2 com novas seeds
  e imagens 13 e 14; ambas foram auditadas e novamente nenhuma foi recomendada. A 13
  foi bloqueada por estilo/artefatos; a 14 permaneceu revisável, mas não foi aprovada
  por falta de correspondência suficiente. Reinício entre rodadas confirmou retomada
  do histórico sem duplicação. Aprovação/seleção única, cancelamento e reprovação sem
  motivo foram validados com banco e mídia de teste; aprovação real de conteúdo ficou
  pendente porque nenhuma candidata foi adequada.
- A API HTTP do ComfyUI usada pelo adaptador informou fila/execução e conclusão, mas
  não publicou percentual ou prévia intermediária. A interface mostra essa ausência
  explicitamente. Validação final: 112 testes passaram; compilação Python, sintaxe
  JavaScript e verificação do diff também passaram.

# Realismo visual obrigatório — 2026-09-19

- Regra explícita do usuário registrada em AGENTS.md: somente aparência fotográfica realista, sem desenho, cartoon, anime, pintura, ilustração ou estética de animação/3D estilizado. Visualizações científicas não devem ser apresentadas como fotografias reais.
- `coae/visual_style.py` centraliza a regra. Prompt inicial/exportado e chamadas ComfyUI (incluindo melhorias) recebem orientação fotorrealista. O adaptador acrescenta exclusões aos nós negativos efetivamente ligados aos KSampler, preservando negativos existentes e o arquivo do workflow. Rejeita encoder negativo compartilhado com o positivo. A mudança de prompt altera o fingerprint; tickets antigos incompatíveis são preservados e não reenviados silenciosamente.
- Planejamento de melhorias segue a regra; auditor visual é instruído a marcar estilo proibido observado como erro bloqueante em VISUAL_QUALITY. Avisos de geração e revisão humana exibem a exigência. Instrução/prompt não garantem obediência perfeita do modelo: conferência visual continua necessária, sem aprovação automática.
- 109 testes passaram, sem erros/falhas/skips; compilação, sintaxe JS, smoke UI e diff passaram. COAE reiniciado após conferir ausência de tarefas em todos os projetos. Nenhuma imagem regenerada, excluída ou reclassificada automaticamente; áudio, prévias e configurações preservados. Próximo teste: gerar ou refazer uma cena e auditar o realismo do resultado. Sem novo teste de inferência nesta alteração de política.

# Refazer imagem com melhoria — 2026-09-19

- Adicionado botão “Refazer imagem com melhoria” abaixo do parecer visual completo. Requer storyboard aprovado e provedores locais. Ollama usa auditoria, fala, ideia e descrição para propor outro prompt; ComfyUI gera uma nova imagem REVIEW_REQUIRED. Origem e parecer continuam intactos; fala/tempos não são modificados. Proposta em português aparece na nova imagem, com aviso para reauditar antes de aprovar.
- Implementação em `coae/image_improvement.py`, integração em `application.py`, `server.py` e `web/app.js`. Plano/ticket persistidos em `logs/image_improvements/`; evento IMAGE_IMPROVED liga imagem de origem, auditoria e resultado. Repetição retoma ou reutiliza a versão pronta; falhas não duplicam envio. JSON inválido e imagem idêntica a versão existente são recusados. Sem APIs pagas, subagentes, downloads ou alterações de configuração.
- Teste real COAE-B89D2A1D: imagem 1 + auditoria 9 → imagem 9 da SC001, job 17 DONE. Arquivo `projects/COAE-B89D2A1D/images/SC001_005_ab1b75fe37.png`. Ollama qwen2.5:7b levou 51,713 s; ComfyUI registrou 86,83 s incluindo recarga do checkpoint após liberação de memória. Oito imagens anteriores conferidas por registro/hash, storyboard, falas, áudio e prévias preservados. Nova imagem sem aprovação automática.
- A proposta textual do modelo ainda contém relações entre brilho e fase evolutiva que exigem revisão; não comprova melhoria científica. A geração é nova imagem a partir de prompt, não edição pixel a pixel. Nenhuma auditoria da imagem nova foi executada nesta etapa. Próximo passo: comparar visualmente e clicar “Auditar com IA” na imagem 9; novo ciclo de melhoria deve partir do parecer dela.
- Validação: 107 testes Python passaram, zero falhas/erros/skips; testes específicos de preservação, retomada, repetição, JSON inválido, saída duplicada e pré-requisitos locais. Compilação Python, sintaxe JS, diff e smoke Node do botão/vínculos passaram. Teste HTTP real de geração concluído. Sem commit/push; alterações anteriores do usuário preservadas.

# Auditoria visual e prévia de cena — 2026-09-19

- Escopo executado na sessão principal, sem subagentes/APIs pagas, branch `main`, alterações anteriores preservadas. `gemma3:4b` instalado em `D:\IA\Ollama` (3,3 GB); configuração privada `COAE_LOCAL_VISION_MODEL` adicionada, mantendo qwen2.5:7b, ComfyUI e token. D: com 515,08 GiB livres na conferência final.
- Auditoria real de COAE-B89D2A1D/SC001/imagem 1 concluída pelo COAE (job 14 DONE). Envia bytes reais da imagem, fala, ideia principal e descrição visual. Cinco categorias em português, sem nota/certificação científica, mais aviso de revisão humana. Resultado REVIEW_REQUIRED; nenhuma aprovação automática. Imagem, storyboard v5, cenas e áudio preservados.
- Primeiro retorno do modelo tinha JSON fora do contrato; foi tratado como falha técnica, sem reprovar imagem nem substituir parecer. Adaptador visual agora envia JSON Schema ao Ollama; contrato continua validado no backend. Teste corrigido: `/api/chat` 13,535 s, log ROCm confirma 35/35 camadas na GPU e 3,1 GiB de pesos em ROCm0; também registra 525 MiB de pesos em CPU. Parecer sugere que o céu estrelado não demonstra fases evolutivas; conteúdo científico continua sujeito a revisão humana.
- Prévia estática implementada em `coae/scene_preview.py`, integrada em `application.py`, `server.py` e `web/app.js`. Aba Imagens oferece gerar, reproduzir e baixar MP4 por imagem selecionada, sem exigir/aplicar aprovação da imagem. Usa áudio original conferido por hash e cena da versão atual. Saídas novas em `previews/`, com manifesto e vínculo no banco; anteriores/originais preservados.
- Cortes usam limites absolutos quantizados a 30 fps e áudio em 48 kHz, sem acelerar narração. Erro máximo por limite de 16,67 ms; não soma durações arredondadas. Manifesto registra tempos solicitados, quadros, amostras, hashes e versão. Prévia é imagem estática, não animação generativa nem montagem final. Para montagem contínua, usar o áudio original, evitando emendas de AAC independente.
- Teste real único: job 15 DONE, SC001 0–7,38 s → 221 quadros / 7,366667 s, H.264/AAC, 1024×576, geração CPU FFmpeg em 1,263 s. Arquivo `projects/COAE-B89D2A1D/previews/story_v005/SC001_image1_bc0eaa0273f3.mp4` (376.553 bytes). Download autenticado HTTP 200, bytes iguais ao disco; decodificação integral FFmpeg sem erros. Comparação comprovou mídia, fala, tempos, storyboard e status da imagem intactos.
- Validação: 102 testes Python passaram, sem skips; inclui corte não inicial com frequência de áudio preservada, limites adjacentes, proteção de originais, falha técnica, contrato visual e geração/download HTTP autenticado. Compilação Python, sintaxe JS e diff passaram. Smoke Node dos controles de geração/reprodução/download passou com DOM simulado; reprodução audiovisual em navegador e revisão humana ainda pendentes. Evidências em `workspace/validation/`, sem segredos versionados. Sem commit/push.
- Próximo passo do usuário: atualizar a página, abrir Imagens/SC001, ler o parecer e reproduzir a prévia para conferir fala e corte. Nada foi aprovado automaticamente.

# Validação no Windows — 2026-09-18

- ComfyUI local validado com geração real: instalação AMD existente reaproveitada em `D:\IA\ComfyUI`, original preservado. ComfyUI 0.3.68, PyTorch 2.9.0 ROCm 7.1, RX 7800 XT; sem CUDA ou pacotes GPU no COAE. Checkpoint oficial SDXL Base 1.0 de 6,94 GB, licença e SHA256 conferidos. Inicializador `D:\IA\ComfyUI\INICIAR_COMFYUI_LOCAL.bat`, serviço somente `127.0.0.1:8188`, nós de APIs/customizados desabilitados. Dependência requests ausente e links de runtime da cópia foram corrigidos apenas no ambiente separado.
- Integração ComfyUI configurada no `.env` e `workflows/sdxl_local.json`; Ollama e token preservados. Teste direto gerou PNG 1024×576 em 51,91 s incluindo carga inicial. Teste COAE job 9 DONE gerou uma imagem da SC001 no storyboard v5 já aprovado de COAE-B89D2A1D; 6,902 s no ComfyUI, status REVIEW_REQUIRED. Cenas, tempos e storyboard preservados. Arquivo `projects/COAE-B89D2A1D/images/SC001_005_fc7b246cd5.png`. GPU confirmada por logs ROCm/gfx1101 e carregamento direto do modelo na GPU. Duas imagens sequenciais, nenhuma aprovação automática; próximo passo é revisão visual humana. Procedimentos e evidências em `docs/LOCAL_AI.md`; sem mudanças no código de produção ou commit/push nesta etapa.
- Continuação do preenchimento acionada pelo usuário: job 7 (`describe`) de COAE-B89D2A1D estava RUNNING, não havia falhado. Acompanhamento confirmou 4/8 cenas na v3 e conclusão DONE com 8/8 na v4. Comparação v2/v4 confirmou SC001 integralmente preservada e nenhuma mudança em fala, tempos ou campos fora das descrições nas outras cenas. Auditoria final REVIEW_REQUIRED, apenas revisão humana de tempos/rigor; sem erros VISUAL pendentes. Ollama estava 100% GPU; descarregamento entre lotes adicionou carregamentos do HD. Nenhuma tarefa duplicada, reinício ou mudança de código realizada nesta verificação.
- IA local validada com modelo real: `qwen2.5:7b` instalado em `D:\IA\Ollama` (4,7 GB); `OLLAMA_MODELS` persistido no usuário. Ollama 0.13.5 identificou RX 7800 XT via ROCm; teste retornou JSON português, `ollama ps` 100% GPU e 29/29 camadas offloaded. `.env` configurado para texto Ollama, escritor/auditor com o nome exato; token e demais configurações preservados. Sem Gemini, APIs pagas ou CUDA. Nenhuma alteração de código de produção nesta etapa.
- Teste de cena existente: COAE-B89D2A1D/SC001 preenchida via adaptador real e salva pela API COAE, storyboard v1 → v2. Tempos 0–7,38 s, fala, outros campos e sete cenas restantes conferidos como idênticos; histórico preservado. Auditoria ainda BLOCKED por descrições ausentes de SC002–SC008; revisão editorial pendente. Escopo encerrado após uma cena, sem gerar imagens. Evidências e versões em `docs/LOCAL_AI.md`. Validação: inferência real, consultas HTTP, comparação antes/depois e `git diff --check`; suíte unitária não repetida porque apenas configuração e documentação mudaram.
- Validação final de lixeira/ZIP parcial: 92 testes passaram, sem skips, em 143,863 s; compilação Python, sintaxe JS e diff passaram. Smoke Node verificou confirmar/cancelar recuperação; HTTP real confirmou lixeira e recuperação parcial cancelada sem cadastro. Pasta `projects/COAE-BA0592A3` continua não cadastrada e contém 44 arquivos: três exportações de roteiro, um áudio, duas transcrições, 13 storyboards e 25 auditorias. Não contém banco original. Recuperação local de roteiro está disponível; transcrições/storyboards permanecem como arquivos históricos, sem reconstrução automática de vínculos. Próximo teste do usuário: recuperar a pasta na tela inicial e conferir o roteiro; exclusão/restauração também aguardam inspeção visual.
- Exclusão reversível: cartões em Meus projetos têm “Excluir projeto” com confirmação. Status TRASHED oculta o projeto da lista principal, mantendo banco, arquivos e aprovações no lugar; a Lixeira permite restaurar o status anterior. Tarefas ativas bloqueiam exclusão e projetos excluídos não aceitam alterações antes de restaurar. Pastas de projetos na lixeira não aparecem como recuperáveis. Não há remoção física definitiva.
- ZIP de `COAE-BA0592A3`: inspeção identificou pacote só de arquivos, sem SQLite/project_state. Upload HTTP 200 foi reproduzido; o antigo erro de importação era HTTP 400 por ausência do banco. “Failed to fetch” não foi reproduzido; falhas de conexão agora recebem mensagem em português e o tamanho é verificado antes do envio. ZIP sem banco, mas com roteiro exportado, oferece recuperação parcial com confirmação; cancelar limpa o upload sem cadastrar nada. Em banco temporário, o ZIP real recuperou roteiro como rascunho e preservou 44 arquivos. Na instância real, confirmação/cancelamento foram testados sem importar ou excluir projetos do usuário.
- Importação de projetos: tela inicial permite enviar ZIP de “Baixar projeto completo” (até 256 MB; 2 GB descompactados). Importa como novo ID, mesclando apenas os registros do projeto selecionado, remapeando vínculos e caminhos, conferindo hashes e preservando os projetos existentes. Rejeita caminhos inseguros, arquivos duplicados/ausentes e bancos incompatíveis; falhas revertem a cópia e a transação. Tickets de geração são arquivados, sem retomada remota automática. Eventos/artefatos históricos mantêm referências da origem; mapa de IDs no evento PROJECT_IMPORTED.
- Recuperação local disponível para pastas não cadastradas: traz roteiros exportados como rascunhos, preservando arquivos; não reconstrói cenas/aprovações sem banco. HTTP real identificou `COAE-BA0592A3` como recuperável. Nenhum projeto real foi importado/recuperado automaticamente nesta entrega. Uploads e extração ficam em workspace no disco do projeto. Instruções em `docs/IMPORTAR_PROJETOS.md`.
- Validação da importação: suíte de 87 testes passou em 150,424 s, sem skips; após ajustes finais, seis testes de importação e sete de ciclo de vida passaram. Incluem ida/volta do ZIP, IDs/caminhos/vínculos, preservação do destino, rollback, ZIP inseguro, arquivo faltante e upload/ação HTTP. Compilação Python, sintaxe JS e diff passaram. Instância reiniciada sem jobs ativos; interface e candidatos responderam HTTP 200. Revisão visual e migração de projeto real completo continuam pendentes. Arquivos desta etapa: `coae/project_import.py`, `coae/server.py`, `coae/runtime.py`, `coae/web/app.js`, `tests/test_project_import.py` e documentação; alterações anteriores preservadas, sem commit/push.
- Correção posterior do botão Padronizar, confirmada pelo usuário: agora propõe blocos com `<break>` por regras locais de transição explícita, perguntas e parágrafos, mantendo palavras e ordem. Não insere pausa após toda frase; usa 1,5 s para blocos e 2 s para perguntas/contrastes. É uma sugestão editável por heurísticas, não uma análise semântica por modelo. Se já há pausas, preserva-as sem adicionar outras; repetição é idempotente. Não altera automaticamente o roteiro salvo nem seus derivados. Esta regra substitui a limpeza apenas de espaços da entrega anterior.
- Validação da correção: cinco testes de formatação/HTTP e seis de core passaram; compilação Python, sintaxe JS e diff passaram. Instância reiniciada sem tarefas ativas; HTTP real retornou três blocos e três pausas no exemplo de teste. Suíte completa não repetida nesta correção delimitada; 80 testes passaram na etapa anterior. Próximo teste: atualizar a página, padronizar o texto do usuário e revisar as pausas antes de salvar/aprovar.
- Editor: botão “Padronizar para Dark Planner” substitui a exportação TXT na aba Roteiro. Usa o texto atual, inclusive não salvo/não aprovado, normaliza quebras de linha/espaços finais e mantém pausas; conteúdo inválido retorna erro sem substituir o campo. Não salva, aprova ou gera arquivos automaticamente. Salvar uma alteração cria versão que exige revisão. Exportação aprovada via API/CLI permanece disponível.
- Validação desta alteração: 80 testes passaram, sem skips, em 117,987 s; compilação Python, `node --check coae/web/app.js` e `git diff --check` passaram. Arquivos: `coae/script_service.py`, `coae/server.py`, `coae/application.py`, `coae/web/app.js`, `tests/test_script_format.py` e este registro. Alterações anteriores e projeto local preservados; sem commit/push.
- Verificação do erro relatado: banco real tinha roteiro v1 com `approved=0`; a causa histórica não foi determinada e nenhuma aprovação foi forçada. Testes HTTP em workspace temporário confirmam formatação sem mutação do banco. Smoke Node confirma atualização do campo, preservação em falha e proteção contra edição durante a requisição. Instância local reiniciada sem jobs RUNNING; nova rota respondeu HTTP 200 e JavaScript atualizado foi servido. Inspeção visual pelo usuário pendente.
- Continuação: configurado `COAE_ACCESS_TOKEN` fixo no `.env` privado e ignorado pelo Git. Reiniciado apenas o COAE identificado na porta 8765, após confirmar ausência de jobs RUNNING. API autenticada HTTP 200 e abertura do link autenticado no navegador confirmadas; três testes de token passaram. Valor não registrado nesta documentação.
- Sessão principal, sem subagentes; branch `main`, árvore inicialmente limpa.
- `.venv` em D: com Python 3.13.15; `pip check` sem conflitos e imports de Pillow/faster-whisper bem-sucedidos. Python fora do PATH e launcher `py` sem instalações detectadas; usar `.venv\Scripts\python.exe` ou `INICIAR_WINDOWS.bat`.
- FFmpeg e FFprobe 9.0.1 disponíveis. D: com aproximadamente 542,5 GiB livres.
- COAE já estava ativo em `127.0.0.1:8765`: HTML HTTP 200 e API sem token HTTP 401. Solicitada abertura no navegador; processo existente preservado. Acesso autenticado dessa instância e inspeção visual ainda não confirmados.
- Ollama instalado, inicialmente parado; iniciado `ollama serve` em segundo plano, com logs em `workspace/validation/` no D:. API informa versão 0.13.5 e zero modelos instalados. Nenhum download, inferência, geração de imagem ou teste de GPU realizado.
- pywebview não instalado; modo desktop real não validado.
- Primeira suíte: 77 testes, cinco erros de limpeza por conexões SQLite abertas em `tests/test_core.py`. Ajustado fechamento com `ExitStack`/`closing`, preservando as asserções e os dados reais.
- Após a correção: 77 testes passaram, sem skips, em 114,249 s, com temporários em D:. `compileall` e `git diff --check` passaram. Nenhuma alteração no código de produção, commit ou push nesta sessão.
- Próximo teste manual: conferir acesso autenticado no navegador e importar/reproduzir um áudio curto em projeto de teste. Antes de baixar modelos, definir armazenamento em D:.

## Atualização — modos desktop e web

- Janela opcional pywebview em `coae/desktop.py`, com entrada `iniciar_desktop.py`
  e atalhos de instalação/execução Windows. Web permanece em `iniciar.py`.
- Mesmo backend, SQLite e interface. Token automático na janela; token fixo opcional.
- Ciclo compartilhado em `coae/runtime.py`: trava por workspace, porta reservada
  antes de abrir o banco, encerramento aguardando requisições e limpeza de recursos.
- Desktop permite acesso web pelo link do mesmo servidor. Dependências gráficas
  são opcionais; serviços locais de IA continuam separados.
- Testes de ciclo de vida usam HTTP/SQLite reais e GUI simulada. Validação visual,
  seletor de arquivos, áudio/downloads WebView2 e BATs seguem pendentes no Windows.
- Não há executável independente; procedimento em `docs/DESKTOP.md`.
- Validação desta entrega: 77 testes passaram, compilação Python e diff sem erros;
  smoke do comando web confirmou HTTP 200 autenticado, saída e liberação da trava.
  Dois testes HTTP existentes emitiram ResourceWarning de respostas de erro não
  fechadas, sem falhas. Nenhum modelo ou GUI real foi executado.

## Atualização — token de acesso persistente

O servidor aceita `COAE_ACCESS_TOKEN` no `.env` para manter o acesso entre reinícios.
Ausente ou vazio preserva o token aleatório por execução. Use letras ASCII, números,
hífen ou sublinhado; outros caracteres são recusados antes de abrir o servidor.
O valor privado não é versionado. Validação dirigida em `tests/test_server_token.py`.

# Atualização 2026-09-18 — integração local preparada

## Direção atual

O próximo ambiente-alvo é o PC de casa com Windows, RX 7800 XT 16 GB, Ryzen 5600X e 32 GB de RAM. O Codespace atual serve para desenvolvimento e testes de protocolo; não deve receber modelos grandes nem instalações de GPU.

O caminho recomendado deixou de depender de cotas Gemini: Ollama fornece texto/descrições e ComfyUI fornece imagens locais. Gemini permanece como alternativa configurável, sem fallback automático.

## Agentes especializados

O desenvolvimento passa a usar Codex no outro PC, com regras comuns em
`AGENTS.md` e seis perfis nativos em `.codex/agents/`: `coae_builder`,
`coae_core_script`, `coae_audio`, `coae_storyboard`, `coae_local_ai` e `coae_qa`.
Instruções de transferência e uso em `docs/AGENTES.md`. Os perfis do Copilot em
`.github/agents/` são legado; não conduzem o fluxo atual.

A sessão principal executa tarefas simples; delegação somente quando solicitada.
QA usa perfil de leitura. Nenhum modelo ou esforço de raciocínio foi fixado.
O PC de desenvolvimento não precisa ser o PC com GPU; conferir o ambiente ao chegar.
Validação desta migração: TOML e referências locais; descoberta nativa e execução
no Codex do outro PC continuam pendentes. Não houve alteração do backend nesta etapa.

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

# Auditoria visual estruturada — 2026-09-20

- O contrato de imagem mudou de lista de códigos para objeto com observação separada e cinco julgamentos únicos; respostas incompletas continuam falhas técnicas e preservam o estado. Teste unitário específico: 6 passaram.
- Teste real local Qwen em A/C/E: formato 3/3 válido e percepção dos pixels melhor, mas A e E ficaram em warning apesar de exigirem bloqueio; conjunto reservado não foi executado, auditor padrão permanece gemma3:4b e revisão humana obrigatória. Evidências em `workspace/reference_analysis/visual_audit_validation/STRUCTURED_AUDIT_TEST_2026-09-20.md`.
