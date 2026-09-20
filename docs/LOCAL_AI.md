# Continuação: IA local no COAE

## Regra obrigatória de aparência realista

Gerações iniciais e melhorias devem ter aparência fotográfica realista. Desenho,
cartoon, anime, pintura, ilustração e estética de animação/3D estilizado não são aceitos.
O adaptador ComfyUI aplica orientação positiva e exclusões negativas em memória,
preservando os arquivos de workflow. O auditor deve bloquear estilos proibidos
observados; em dúvida, exige revisão humana. Prompts não garantem o estilo final.
Visualizações científicas fotorrealistas não constituem fotografias ou evidência científica.
Imagens anteriores permanecem preservadas e não são reavaliadas automaticamente.

## Refazer imagem com melhoria

Após uma auditoria visual completa, a aba Imagens oferece **Refazer imagem com melhoria**.
Ollama transforma o parecer, a fala, a ideia e a descrição em outro prompt; ComfyUI
gera uma imagem nova, mantendo a anterior e suas auditorias/aprovações. A nova imagem
fica em REVIEW_REQUIRED. O texto da melhoria é uma proposta do modelo: não comprova
que os defeitos foram corrigidos nem que afirmações científicas estão corretas.
Use **Auditar com IA** na nova imagem e faça a revisão humana antes de aprovar.

É uma nova geração pelo workflow local existente, não edição pixel a pixel da imagem
anterior. Não altera storyboard, fala, áudio, tempos ou prévias já produzidas.
O fluxo exige Ollama/ComfyUI locais e storyboard atual aprovado, sem fallback pago.
Sugestões de legendas/diagramas são instruídas a virar soluções sem texto; conclusões
do auditor são tratadas como falíveis. Cumprimento visual/científico exige conferência.

Plano e ticket ficam em `logs/image_improvements/`, vinculados à imagem e auditoria.
Um clique repetido na mesma origem/parecer retoma o ticket ou retorna a versão já
gerada, sem duplicar a submissão. Para outro ciclo, audite a imagem nova e use o botão
nela. Eventos IMAGE_IMPROVED registram origem, auditoria, nova imagem e proposta.
JSON inválido não gera imagem; resultado idêntico a uma versão existente é recusado,
sem contornar bloqueios ou conceder aprovação. Falhas/timeout preservam plano e ticket.

## Visão local e prévia estática — 19/09/2026

Modelo visual: `gemma3:4b`, 3,3 GB conforme [catálogo oficial](https://ollama.com/library/gemma3:4b),
com entrada de imagem e texto. Usa termos Gemma; requer Ollama 0.6 ou posterior.
Ollama instalado 0.13.5, armazenamento persistente do usuário `OLLAMA_MODELS=D:\IA\Ollama`.
Modelo de texto `qwen2.5:7b` e integração ComfyUI preservados. A configuração privada
`COAE_LOCAL_VISION_MODEL=gemma3:4b` seleciona o auditor visual separadamente do textual.
O modelo foi baixado explicitamente nesta etapa, nunca automaticamente pelo COAE.

Antes da auditoria, fila ComfyUI conferida vazia e modelos liberados via `/free`;
serviço e workflow preservados. Auditoria real SC001, projeto COAE-B89D2A1D,
job 14 concluído, chamada Ollama em 13,535 s. Logs `workspace/validation/ollama-local.stderr.log`
confirmam ROCm, 35/35 camadas offloaded, pesos GPU 3,1 GiB e CPU 525 MiB.
Ollama descarrega o modelo depois da chamada (`keep_alive=0`).

O primeiro retorno era JSON válido, porém fora do contrato de auditoria. A correção
usa [saída estruturada oficial com visão](https://docs.ollama.com/capabilities/structured-outputs)
e valida os cinco códigos obrigatórios. Imagem real em base64, fala, ideia principal
e descrição visual são enviados juntos. O parecer aparece em português, sem nota:
correspondência, ausências/contradições, ciência/limites, qualidade e sugestões.
Falha de serviço/JSON incompleto mantém estado e parecer anteriores; um parecer
válido pode apontar problema bloqueante. Nenhuma dessas verificações certifica ciência.
Resultado real: REVIEW_REQUIRED, imagem original intacta, sem aprovação automática.

Na aba Imagens, “Gerar prévia estática” cria MP4 separado usando imagem selecionada
e áudio original da cena atual; depois aparecem “Reproduzir prévia” e “Baixar MP4”.
FFmpeg usa CPU/libx264, AAC e 30 fps. Não requer modelo, GPU ou API.
Os limites absolutos do storyboard são arredondados ao quadro mais próximo; cortes
compartilhados não divergem por soma de durações. A voz mantém velocidade 1×.
Áudio em 48 kHz, recorte por amostras com `atrim` e reinício dos timestamps com `asetpts`;
até meio quadro de silêncio pode completar a última borda do áudio. Os originais são
conferidos por hash antes/depois. JSON ao lado do MP4 registra toda a linhagem.
Para montagem final, usar o áudio original contínuo, não concatenar AAC das prévias.
Referência: [filtros FFmpeg](https://ffmpeg.org/ffmpeg-filters.html#atrim).

SC001: storyboard 0–7,38 s, prévia 0–7,366667 s (221 quadros), 1024×576,
gerada em 1,263 s, 376.553 bytes:
`projects/COAE-B89D2A1D/previews/story_v005/SC001_image1_bc0eaa0273f3.mp4`.
Download HTTP autenticado e decodificação integral conferidos; imagem, áudio, cenas
e aprovações preservados. Reprodução no navegador exige conferência do usuário;
controles de interface validados por smoke Node, não por inspeção audiovisual.

## ComfyUI real no Windows — 18/09/2026

Instalação AMD AI Bundle existente reaproveitada de
`C:\Users\Danilo\AppData\Local\AMD\AI_Bundle\ComfyUI` para `D:\IA\ComfyUI`.
Original preservado. A cópia inicial excluiu links de runtime: 30 arquivos
DLL/PYD/ZIP correspondentes foram materializados na cópia, e `pyvenv.cfg` aponta
para D:. Foi instalada somente a dependência ausente `requests` e dependências
leves no ambiente do ComfyUI. Nenhuma instalação de CUDA, atualização de driver
ou alteração das dependências Python do COAE.

- ComfyUI 0.3.68; Python 3.12.0 próprio; PyTorch 2.9.0+rocmsdk20251116;
  ROCm/HIP 7.1.52802; RX 7800 XT gfx1101; driver Windows 32.0.31041.1004.
- Iniciar: `D:\IA\ComfyUI\INICIAR_COMFYUI_LOCAL.bat`.
  Servidor `http://127.0.0.1:8188`, confirmado somente em loopback.
  Nós personalizados e nós de APIs externos desabilitados; temporários e caches em D:.
  O BAT mantém o terminal aberto; Ctrl+C encerra o serviço.
- Checkpoint único: SDXL Base 1.0 oficial Stability AI,
  `D:\IA\ComfyUI\ComfyUI\models\checkpoints\sd_xl_base_1.0.safetensors`.
  Tamanho 6.938.078.334 bytes; licença CreativeML Open RAIL++-M, cópia em
  `SDXL_LICENSE.md` junto ao checkpoint.
  SHA256 conferido: `31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b`.
- Teste direto: 1024×576, batch 1, seed 42, Euler, 20 passos, CFG 7.
  Arquivo `D:\IA\ComfyUI\ComfyUI\output\COAE_install_test_00001_.png`;
  51,91 s medidos da submissão à conclusão, incluindo carga inicial.
- Teste pelo COAE: projeto COAE-B89D2A1D, storyboard v5 já APPROVED,
  SC001, job 9 DONE, uma imagem. Execução ComfyUI 6,902 s com modelo carregado,
  medida pelos timestamps do history; log confirma 6,90 s.
  Arquivo `projects/COAE-B89D2A1D/images/SC001_005_fc7b246cd5.png`,
  1024×576, status REVIEW_REQUIRED. Sem aprovação automática. Comparação confirmou
  cenas e storyboard preservados. Inspeção visual técnica confirmou imagem legível;
  não substitui revisão humana editorial/científica.
- Evidência GPU: logs em `D:\IA\ComfyUI\logs\server2.stderr.log` identificam
  RX 7800 XT/gfx1101/ROCm 7.1 e `loaded diffusion model directly to GPU`;
  cerca de 4.897 MB do modelo de difusão carregados. `/system_stats` reportou
  alocação Torch de aproximadamente 7,4 GB após o primeiro teste. A nomenclatura
  `cuda:0` é a interface PyTorch usada pelo backend HIP; `torch.version.cuda=None`.
- `.env`: image provider comfyui, URL local, workflow API `workflows/sdxl_local.json`,
  prompt node 6, output node 9. Configuração Ollama qwen2.5:7b e token preservados.
  Ollama descarregado antes da geração. Duas imagens sequenciais no total;
  nenhum lote paralelo, serviço pago ou alteração de funcionalidades.
- D: livre antes 538,1 GiB; depois 518,2 GiB. Evidências HTTP privadas em
  `workspace/validation/comfy-install-result.json` e `comfy-coae-result.json`.
  Apenas configuração/instalação/documentação nesta etapa; `git diff --check` passou,
  sem repetir suíte de código não alterado. Próximo passo: revisão humana da SC001.

Documentação oficial consultada: [instalação ComfyUI](https://docs.comfy.org/installation/manual_install),
[PyTorch AMD](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html),
[checkpoint, tamanho e hash](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/sd_xl_base_1.0.safetensors),
[licença](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md).

## Teste real no Windows — 18/09/2026

Nesta sessão foi autorizado o download de um modelo de texto, sem serviços pagos.
`OLLAMA_MODELS` foi persistido no ambiente do usuário como `D:\IA\Ollama`, e o
serviço Ollama instalado foi reiniciado com esse caminho. Espaço livre em D:
542,5 GiB antes; 538,1 GiB depois. Modelo instalado: `qwen2.5:7b`, Q4_K_M,
4.683.087.332 bytes segundo `/api/tags` (4,7 GB anunciados no catálogo).
Ollama 0.13.5; Windows; Radeon RX 7800 XT; driver Windows 32.0.31041.1004.

Inferência curta real retornou JSON válido em português em 46,6 s, incluindo
carregamento inicial. `ollama ps`: 100% GPU, contexto 4096, cerca de 4,9 GB.
`/api/ps`: size = size_vram = 4.924.207.104 bytes; log: ROCm/gfx1101,
RX 7800 XT, 29/29 camadas na GPU. Isso valida esta execução de texto, não imagens.

`.env` privado: texto `ollama`, URL `http://127.0.0.1:11434`, escritor e auditor
`qwen2.5:7b`. Token e demais configurações preservados; provedor de imagens não
alterado. Nenhuma chamada Gemini, API paga ou instalação CUDA.

Teste delimitado usou `Ollama.call` e a rota versionada `save_story` do COAE para
preencher somente SC001 de COAE-B89D2A1D: v1 → v2, 0–7,38 s. Comparação integral
confirmou preservação de todos os campos fora dos cinco campos descritivos dessa
cena, incluindo fala, tempos e outras sete cenas. Histórico v1 preservado.
Resposta: 564 tokens de entrada e 217 de saída. O script de validação inicialmente
tratou o retorno `(valor, metadados)` como objeto; foi corrigido e reutilizou a
resposta já gerada, sem nova inferência nem mutação durante a falha.

A auditoria permanece BLOCKED apenas pelas descrições ausentes de SC002–SC008,
além da revisão humana de tempos/rigor. O resultado é evidência funcional, não
aprovação editorial: descrição gerada precisa ser revisada. Evidências privadas
em `workspace/validation/ollama-gpu-test.json` e `ollama-scene-result.json`.
O adaptador libera o modelo após responder (`keep_alive=0`); `ollama ps` vazio
depois do teste não significa que ele rodou na CPU.

Referências oficiais consultadas: [modelo e tamanho](https://ollama.com/library/qwen2.5:7b),
[variáveis Windows e diagnóstico de GPU](https://docs.ollama.com/faq),
[suporte de hardware](https://docs.ollama.com/gpu).

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

Leia `AGENTS.md`, `docs/AGENTES.md`, `docs/PROJECT_STATE.md` e este documento.
Para programar no outro PC, siga primeiro `docs/AGENTES.md`; a validação com GPU
é uma etapa separada, no computador com os serviços locais instalados.
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
