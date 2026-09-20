# COAE — instruções comuns de desenvolvimento

Estas regras orientam o Codex. Os agentes próprios deste projeto ficam em
`.codex/agents/*.toml`; não dependem do Copilot e não são agentes executados pelo
backend COAE. Arquivos antigos em `.github/agents/` são legado de outro cliente,
não são a fonte dos perfis Codex. Não conceda permissões adicionais por causa deles.

## Contexto e precedência

- Respeite primeiro as instruções da sessão e as políticas da ferramenta.
- Leia `docs/PROJECT_STATE.md`, `docs/LOCAL_AI.md` para tarefas de IA local, e apenas
  as seções pertinentes de `docs/COAE_SPEC.md`. A especificação inclui roadmap:
  não é prova de que uma capacidade já funciona. Confirme no código e nos testes.
- Decisões atuais registradas e instruções do usuário prevalecem sobre regras
  históricas incompatíveis. Não reinicie fases concluídas só porque o perfil tem número.
- Mapeamento: `coae_builder` coordena; `coae_core_script` cuida de projetos/roteiro;
  `coae_audio` de áudio; `coae_storyboard` de cenas; `coae_local_ai` dos serviços;
  `coae_qa` revisa. Veja `docs/AGENTES.md`.
- Por padrão, trabalhe na sessão principal usando apenas as instruções do domínio
  necessário. Quando o usuário pedir delegação/especialistas, use os agentes nativos
  disponíveis. Criar os arquivos não autoriza iniciar os seis a cada tarefa.
- Se a instalação não carregar agentes próprios, leia o `developer_instructions`
  do TOML pertinente e execute na sessão principal, informando essa limitação.

## Regras do produto

- Imagens devem ter aparência fotográfica realista. Não aceitar desenho, cartoon,
  anime, pintura, ilustração ou estética de animação/3D estilizado, inclusive em
  regenerações. Visualizações científicas fotorrealistas não são fotografias reais.
  Aplicar a regra nos prompts e na auditoria; a saída do modelo exige conferência.
- Narração final é externa no Dark Planner; não adicionar TTS interno.
- Tags `<break>` são pausas de narração, nunca timestamps finais de cenas.
- Áudio importado é a fonte temporal; preservar original, hash e linhagem.
- Timestamps reconhecidos precisam de conferência: ASR não comprova alinhamento
  perfeito com o roteiro. Nunca substituir tempos por estimativa de palavras.
- Cenas têm duração variável. Revisões invalidam aprovações e derivados pertinentes;
  histórico e materiais anteriores devem permanecer recuperáveis.
- Imagens dependem de storyboard aprovado. Auditoria de arquivo/proporção, auditoria
  de conteúdo por IA e revisão humana são verificações distintas.
- Prioridade atual: serviços locais. Nenhum fallback automático para Gemini pago.
  Vídeo animado, SEO e thumbnails dedicadas exigem trabalho específico futuro.

## Ambiente e dados

- Confira sistema operacional, branch e `git status --short` antes de editar.
- Preserve mudanças do usuário. Não use reset/clean destrutivos nem restaure banco
  real para fazer teste passar. Use diretórios temporários e bancos de teste.
- Nunca versionar `.env`, credenciais, modelos, SQLite ou mídia gerada. Arquivos de
  exemplo sem segredos podem ser versionados. Não remova materiais já versionados
  como parte de uma limpeza não solicitada.
- Ambiente atual: preparar código e testes, sem modelos grandes/pacotes GPU.
- O desenvolvimento com Codex continuará em outro PC. Confira o ambiente dessa
  máquina antes de executar comandos; não presuma caminhos, dependências ou GPU.
  Desenvolvimento não exige Ollama/ComfyUI ativos; use fixtures quando necessário.
- PC-alvo de IA local informado anteriormente (confirmar ao chegar): Windows, RX 7800 XT 16 GB, Ryzen 5600X, RAM 32 GB; HD com espaço, SSD cheio.
  Instalação/versões AMD devem ser conferidas na documentação oficial atual. Não
  instalar CUDA na AMD. Serviços de IA ficam separados do ambiente Python do COAE.
- Downloads grandes e chamadas pagas não estão autorizados por estas instruções.
  Considere autorizações já dadas na sessão; não peça novamente sem necessidade.

## Edição e coordenação

- Trabalhe em uma tarefa delimitada até concluir implementação e validação possível.
  O escopo permite pequenos ajustes necessários em rotas/interface; não é motivo
  para abandonar uma entrega pela metade.
- `application.py`, `server.py`, `web/app.js`, `storage.py`, `models.py` e
  `docs/PROJECT_STATE.md` são compartilhados. Um responsável por vez na mesma árvore.
- Não iniciar automaticamente os cinco especialistas. Passagens de contexto são
  explícitas; não usar botões de handoff do Copilot como mecanismo no Codex. Se houver trabalho paralelo explicitamente solicitado, separar branches/
  worktrees, declarar arquivos e contratos, e integrar sequencialmente.
- Registre na passagem: objetivo, branch/commit (se houver), arquivos, comportamento,
  testes/resultados, limitações e próxima ação. Não invente versão aprovada ou commit.
- O responsável ativo atualiza fatos verificados em PROJECT_STATE. Em revisão sem
  edição, devolva a atualização sugerida ao Builder. Não afirmar push sem comprovação.

## Validação proporcional

- Use Python >=3.12. Execute testes relevantes às mudanças. Para integração/release:
  `python -m unittest discover -s tests -v` e `python -m compileall -q coae`.
- Se JavaScript mudou: `node --check coae/web/app.js`; se há Git: `git diff --check`.
- Documentação/perfis: validar TOML, referências e coerência; não executar toda a
  produção nem baixar modelos apenas para testar texto de configuração.
- Não enfraquecer teste ou portão para obter aprovação. Reproduza falhas, corrija o
  motivo e registre comandos/resultados, incluindo skips e testes não executados.
- Identifique evidência: inspeção, fixture, integração HTTP, execução real do modelo,
  GPU e revisão humana. Nunca converter fixture em prova de qualidade audiovisual.
- Autoauditoria de desenvolvimento não aprova o conteúdo do usuário e não substitui
  as auditorias implementadas em Python. Notas de IA não certificam ciência.

## Entrega

Responda em português: resultado, arquivos, validação, limitações e próximo passo.
Use `CONCLUÍDO NO ESCOPO`, `PARCIAL` ou `BLOQUEADO POR DEPENDÊNCIA`, justificando
pelo que foi executado. Não declare o produto inteiro pronto por uma tarefa isolada.
