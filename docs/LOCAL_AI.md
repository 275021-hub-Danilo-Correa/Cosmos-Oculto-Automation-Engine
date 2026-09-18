# Continuação: IA local no COAE

## Estado desta entrega

O COAE agora pode usar Ollama para texto/descrições e ComfyUI para imagens, sem
fallback para Gemini. São adaptadores HTTP reais, testados com servidores de
protocolo simulados. **Nenhum modelo ou GPU foi executado nesta entrega.**
A compatibilidade de instalação, a velocidade e a qualidade na RX 7800 XT ainda
precisam ser verificadas no Windows do usuário. Não instale CUDA nessa placa AMD.
Não instalar dependências de GPU dentro do ambiente Python do COAE; os serviços
Ollama e ComfyUI devem ter instalações próprias.

O alvo informado é RX 7800 XT (16 GB), Ryzen 5600X, 32 GB RAM, Windows, espaço em
HD e SSD cheio. Não há exigência de comprar hardware nesta etapa. Escolha os
modelos e o caminho de instalação após conferir suporte AMD na documentação
atual dos serviços e espaço disponível. O workflow incluído é um **exemplo SDXL**,
não um modelo baixado ou uma promessa de desempenho.

## Aplicar a atualização em outro computador

Esta entrega foi feita sobre o commit `be94c377622b6c05a94a52e9c020bd6eb2c11951`.
O patch inclui apenas código, testes, configuração de exemplo e documentação.
Não altera `.env`, banco de dados, áudios ou imagens existentes.

Se recebeu `COAE_IA_Local.patch`, abra o terminal na pasta do repositório:

```bash
git status
git switch -c feat/local-ai
git apply --check CAMINHO/COAE_IA_Local.patch
git apply CAMINHO/COAE_IA_Local.patch
python -m unittest discover -s tests -v
```

Se houver conflito, peça ao Codex para integrar as mudanças preservando as edições
atuais; não substitua arquivos de trabalho à força. Depois faça commit/push da
branch na conta com permissão de escrita. O patch **não já está no GitHub**.

## Configurar em casa

1. Atualize a branch no PC de casa. Preserve o workspace e os backups existentes.
2. Instale e valide os serviços locais separadamente, seguindo suas instruções
   atuais para AMD/Windows. Baixe somente modelos escolhidos e compatíveis.
3. No Ollama, confira o nome exato do modelo instalado com `ollama list`.
4. No ComfyUI, teste uma imagem manualmente. O perfil inicial do COAE aceita nós
   nativos SD/SDXL: CheckpointLoaderSimple, CLIPTextEncode, EmptyLatentImage,
   KSampler, VAEDecode e SaveImage. Nós customizados e APIs pagas são rejeitados.
5. Copie `workflows/sdxl_api.example.json` para `workflows/sdxl_local.json` e substitua
   `SEU_CHECKPOINT_SDXL.safetensors` pelo nome real do checkpoint. O exemplo usa
   1024×576, batch 1, seed 42, 20 passos. Esses parâmetros são ponto de partida;
   desempenho e qualidade ainda não foram medidos. Não use o JSON da interface
   visual: a integração espera **formato API**.
6. Configure o `.env` (o arquivo `.env.local.example` contém o perfil completo):

```dotenv
COAE_TEXT_PROVIDER=ollama
COAE_IMAGE_PROVIDER=comfyui
COAE_OLLAMA_URL=http://127.0.0.1:11434
COAE_LOCAL_WRITER_MODEL=NOME_EXATO_DO_MODELO_INSTALADO
COAE_LOCAL_AUDITOR_MODEL=
COAE_LOCAL_VISION_MODEL=
COAE_COMFYUI_URL=http://127.0.0.1:8188
COAE_COMFYUI_WORKFLOW=workflows/sdxl_local.json
COAE_COMFYUI_PROMPT_NODE=6
COAE_COMFYUI_OUTPUT_NODE=9
COAE_LOCAL_TIMEOUT=600
COAE_MAX_CALLS_PER_PROJECT=0
```

7. Inicie os dois serviços e reinicie o COAE com `python iniciar.py`. Na aba
   **Auditorias e tarefas**, clique em **Verificar serviços locais**. O diagnóstico
   não gera conteúdo, não baixa modelos e não comprova aceleração por GPU.
8. Abra um projeto com áudio e transcrição já salvos. Em Storyboard, clique em
   **Completar descrições com Ollama local**. Isso não retranscreve nem muda os tempos.
9. Confira as descrições e aprove o storyboard. Em Imagens, gere **uma cena** com
   ComfyUI local. Confira a utilização da GPU no serviço, tempo, qualidade e memória.
10. Só depois teste três cenas pendentes e a retomada. Não comece com episódio inteiro.

Os serviços precisam estar no mesmo computador que o backend Python do COAE.
`127.0.0.1` dentro do Codespaces aponta para o Codespaces, não para seu PC de casa.
Esta versão não aceita endereços remotos, túneis nem redirecionamentos.

## Auditoria e preservação

- Tempos continuam vindo do áudio importado, sem slots de oito segundos; a voz
  continua externa no Dark Planner.
- Descrições locais usam lotes de até quatro cenas. Cenas já completamente descritas
  são preservadas. Cada lote válido cria uma versão; respostas inválidas não são salvas.
- Ollama recebe pedidos JSON, usa escritor/auditor configurados e solicita liberação
  do modelo ao terminar (`keep_alive=0`). Nenhum resultado concede aprovação sozinho.
- Sem um modelo visual local configurado, a imagem passa por verificação de arquivo
  e proporção, fica em `REVIEW_REQUIRED` e exige revisão humana. Isso **não equivale**
  a auditoria científica automática. Para auditoria visual por IA, configure
  `COAE_LOCAL_VISION_MODEL` instalado e com capacidade `vision`; use **Auditar com IA**.
- Auditoria visual bloqueante continua impedindo aprovação. Não há regeneração
  corretiva automática no perfil local nesta etapa. O ciclo limitado de correção
  textual existente pode usar Ollama.
- Chamadas locais ficam em Eventos e não gastam o contador reservado ao Gemini.
- Modelos Ollama identificados como cloud/remotos são rejeitados. Não há instalação
  automática de modelos nem fallback pago. O controle não substitui a configuração
  correta dos próprios serviços locais.

## Fila, interrupção e recuperação

O COAE processa cenas sequencialmente por projeto e mantém as imagens prontas.
Uma tentativa ComfyUI gera um ticket em `projects/ID/logs/local_images/` antes do
POST. Quando recebe `prompt_id`, salva-o e consulta `/history/{prompt_id}`.

- Timeout com `prompt_id`: clique novamente em Gerar; consulta o mesmo job sem reenviar.
- Imagem íntegra já aguardando revisão/aprovada: a cena é pulada.
- `SUBMITTING` sem ID: o resultado do envio é incerto; não reenviar automaticamente.
  Confira a fila/histórico no ComfyUI. Se encontrar a imagem, importe manualmente
  na cena. Caso confirme que não existe trabalho em andamento nem resultado a
  aproveitar, arquive o ticket fora de `logs/local_images/` antes de tentar de novo.
- Job com falha: corrija no ComfyUI (memória, modelo, workflow), confirme que terminou
  e arquive o ticket para permitir uma nova tentativa. Preserve o arquivo para análise.
- Histórico apagado no ComfyUI ou configuração alterada: exige reconciliação humana;
  não há como garantir recuperação automática do resultado perdido.

Não execute gerações em vários projetos simultaneamente durante o teste inicial:
o limite de uma tarefa é por projeto, não um bloqueio global da GPU. Vídeos animados,
Veo, thumbnails dedicadas e renderização final **não foram implementados** aqui.

## Handoff ao Codex do PC de casa

Leia `.github/copilot-instructions.md`, `docs/PROJECT_STATE.md` e este documento.
Confira a branch antes de editar. Preserve dados locais e nunca envie `.env`, modelos
ou bancos ao GitHub. Teste a instalação AMD/Windows dos serviços sem usar instruções
CUDA. Não considere fixtures de teste como evidência de qualidade de IA. Configure
os modelos reais, valide uma imagem e depois três cenas vinculadas à narração.
Registre versões, uso de GPU, tempo por imagem e problemas reais neste documento.

## Protocolos consultados

- [Ollama chat](https://docs.ollama.com/api/chat): JSON, mensagens/imagens e descarregamento.
- [Ollama modelos instalados](https://docs.ollama.com/api/tags).
- [ComfyUI local HTTP](https://docs.comfy.org/development/comfyui-server/comms_routes):
  envio, histórico e leitura de saídas. Não usamos a API Cloud.
