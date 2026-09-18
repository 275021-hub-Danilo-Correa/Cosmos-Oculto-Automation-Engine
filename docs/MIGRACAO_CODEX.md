# Migração para Codex — 18/09/2026

Fonte analisada: `aquivos-externos/COAE_Agentes_Codex.zip`.
Integrados seis perfis TOML, exemplo opcional de concorrência, `AGENTS.md` e guia
`docs/AGENTES.md`. README, PROJECT_STATE e handoff de LOCAL_AI apontam para Codex.
Os arquivos antigos de Copilot permanecem como legado, sem remoção automática.

Ajustes ao pacote: validação de TOML (não YAML), transferência para o outro PC,
recriação do ambiente Python, separação entre máquina de desenvolvimento e máquina
com GPU e remoção da suposição de que a nova sessão ocorrerá no computador atual.
Nenhum código Python/JS, `.env`, banco, mídia ou modelo foi alterado.

Validação: seis nomes únicos, campos obrigatórios, TOML da configuração opcional,
referências locais e `git diff --check`. A suite de aplicação não foi repetida por
ser uma alteração de documentação/perfis. Nenhum subagente ou modelo foi iniciado.
O executável Codex não está disponível neste terminal; carregamento nativo deve
ser conferido em uma nova sessão no outro PC, conforme `docs/AGENTES.md`.

Não houve commit/push nesta etapa. Preserve dados locais e leve também `.codex/`
ao transferir o projeto. Não reaplique o ZIP original por cima desta adaptação.
