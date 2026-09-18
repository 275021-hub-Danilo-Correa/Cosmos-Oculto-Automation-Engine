# COAE: agentes para Codex

Esta edição substitui a orientação anterior baseada nos perfis do Copilot.
O fluxo de desenvolvimento usa o Codex; o produto continua usando Ollama/ComfyUI
para IA local e Dark Planner para a voz externa.

## Agentes registrados

| Nome no Codex | Papel |
|---|---|
| coae_builder | Coordenação e integração; a sessão principal já pode exercer esse papel |
| coae_core_script | Projetos, persistência, roteiro e exportação |
| coae_audio | Importação, hashes, transcrição e timestamps |
| coae_storyboard | Segmentação, versões e aprovação das cenas |
| coae_local_ai | Ollama, ComfyUI e tickets de geração |
| coae_qa | Revisão de código e evidências; solicita sandbox de leitura |

Os arquivos nativos estão em `.codex/agents/*.toml`. `AGENTS.md` contém as regras
comuns. Não há dependência de .github/agents, handoffs, ferramentas ou cota do Copilot.
Não é necessário apagar os arquivos antigos para usar o Codex; evite mantê-los como
segunda fonte ativa de instruções.

## Preparar o outro PC para programar

1. Leve a versão atualizada deste repositório ao outro PC, incluindo a pasta oculta
   `.codex/`, `AGENTS.md` e `docs/`. A integração do ZIP já foi feita nesta cópia.
   Se usar Git, mudanças locais precisam ser commitadas e transferidas primeiro;
   baixar a versão remota não inclui arquivos ainda não publicados.
2. Abra a pasta local no VS Code com a extensão **Codex** e autentique sua conta.
   Confirme sistema operacional, branch e alterações locais. Recrie o ambiente
   Python nessa máquina conforme o README; não copie `.venv` entre computadores.
   Preserve `.env`, `data/` e `projects/` existentes; não os publique no Git.
3. Se já existir `.codex/config.toml`, preserve-a. O arquivo
   `.codex/config.coae.example.toml` é apenas um exemplo opcional: para limitar
   concorrência, integre sua seção `[agents]` sem duplicar uma tabela existente.
   Não é preciso mudar modelo, credenciais ou permissões para esta conversão.
4. Inicie uma nova sessão Codex na raiz do projeto para carregar as instruções.
5. Peça: “Confira AGENTS.md e se os agentes coae_* estão disponíveis nesta instalação.
   Não gere imagens nem baixe modelos. Informe quais configurações foram carregadas”.
6. Para testar a descoberta sem alterar código, peça uma inspeção curta delegada ao
   `coae_qa`. Verifique se aparece uma execução separada. Isso usa o Codex, sem API
   Gemini, mas não é um teste gratuito/ilimitado de uso do assistente.

Se a instalação não reconhecer agentes customizados, confira/atualize o cliente de
acordo com a documentação oficial. Enquanto isso, o Codex pode ler o campo
`developer_instructions` do arquivo TOML e trabalhar na sessão principal. Não
confundir essa leitura com um subagente efetivamente iniciado.

## Desenvolvimento no outro computador

Prefira a sessão principal para uma tarefa simples. Não abra os seis especialistas
para cada correção. Para o estágio atual, use o domínio `coae_local_ai`; QA entra
quando há uma entrega concreta para revisar. Não repetir leitura integral de todos
os documentos ou testes completos quando uma alteração pequena não os exige.

Mensagem para começar sem delegação:

> Leia AGENTS.md, docs/PROJECT_STATE.md e as developer_instructions de
> .codex/agents/coae_local_ai.toml. Continue na sessão principal. Confira o código
> e identifique a próxima pendência testável da integração local. Confira o
> ambiente deste PC; não presuma que tem a RX 7800 XT. Não instale GPU/modelos
> grandes e não faça chamadas pagas.
> Preserve minhas alterações e registre somente resultados observados.

Quando quiser usar um agente separado:

> Delegue a tarefa delimitada ao coae_local_ai. Aguarde a entrega, confira o diff e
> peça ao coae_qa uma revisão de leitura. Integre as correções sequencialmente.
> Não acione os outros especialistas nem crie agentes recursivamente.

## Regras da conversão

- Nomes, descrições e instruções foram convertidos para TOML, sem ferramentas YAML
  do Copilot. Modelo e esforço não são fixados: herdam a seleção do cliente.
- QA solicita `sandbox_mode = "read-only"`; políticas e overrides da sessão ainda
  podem prevalecer. Não prometa isolamento absoluto pelo nome do perfil.
- Subagentes não devem editar os mesmos arquivos simultaneamente. Preserve banco,
  mídia, .env e histórico do usuário. Nunca versionar segredos.
- Esta mudança não altera o programa nem implementa agentes de produção no backend.
- Sem executável Codex disponível no terminal desta revisão: TOML e referências foram validados,
  mas descoberta e execução nativa precisam de teste no seu VS Code/CLI.
- Esta entrega não altera nem garante limites do seu plano Codex. A migração não
  transfere cota do Copilot e não torna inferência de desenvolvimento local.

## Evidências e referências

Seis TOMLs verificados com `tomllib` do Python, campos obrigatórios, nomes únicos,
referências e configuração opcional. Não foram executadas chamadas de modelo,
subagentes nativos, GPU ou testes de geração nesta atualização documental.

Formato conferido na documentação oficial em 18/09/2026:
[Agentes próprios do Codex](https://developers.openai.com/codex/subagents/) e
[instruções AGENTS.md](https://developers.openai.com/codex/guides/agents-md/).
