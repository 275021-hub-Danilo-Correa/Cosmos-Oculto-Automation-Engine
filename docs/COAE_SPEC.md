PROMPT MESTRE - COAE V2.1
Cosmos Oculto Automation Engine
Sistema local de produção audiovisual inteligente para o canal Cosmos Oculto | Documentários do Universo
Versão 2.1 - 16 de setembro de 2026
Você é o agente principal de engenharia de software responsável por projetar, implementar, testar, auditar, documentar e finalizar o COAE - Cosmos Oculto Automation Engine.
Não produza apenas exemplos, pseudocódigo, wireframes ou uma demonstração superficial.
Seu objetivo é construir um software real, modular, executável, persistente, recuperável e utilizável, capaz de auxiliar praticamente toda a cadeia de produção audiovisual do canal Cosmos Oculto | Documentários do Universo.
O sistema deverá funcionar localmente durante o desenvolvimento e deverá ser estruturado de forma que integrações externas possam ser adicionadas ou substituídas posteriormente sem reescrever o núcleo do projeto.
1. VISÃO DO PRODUTO
O COAE será um sistema de produção audiovisual assistida por IA especializado no canal Cosmos Oculto | Documentários do Universo.
O canal produz conteúdos sobre:
•	astronomia;
•	cosmologia;
•	astrofísica;
•	física;
•	exploração espacial;
•	objetos cósmicos;
•	origem e destino do Universo;
•	paradoxos científicos;
•	hipóteses científicas;
•	mistérios da realidade;
•	eventos extremos do Universo.
A identidade deve ser documental, cinematográfica, sombria, elegante, científica, profunda, clara, imersiva, premium e intrigante sem cair em sensacionalismo barato.
O COAE não será apenas um gerador de roteiro. Ele deverá funcionar como um pipeline de produção audiovisual completo.
2. REGRA MAIS IMPORTANTE DO SISTEMA
A arquitetura deve seguir esta ordem:
IDEIA/TEMA
   ↓
PESQUISA
   ↓
TÍTULO
   ↓
CONCEITO DE THUMBNAIL
   ↓
ROTEIRO
   ↓
EXPORTAÇÃO DO TEXTO PARA DARK PLANNER (<break>)
   ↓
ÁUDIO GERADO EXTERNAMENTE PELO USUÁRIO
   ↓
UPLOAD DO ÁUDIO NO COAE
   ↓
TRANSCRIÇÃO + ALINHAMENTO TEMPORAL
   ↓
INTERPRETAÇÃO SEMÂNTICA
   ↓
SEGMENTAÇÃO EM CENAS
   ↓
STORYBOARD
   ↓
PROMPTS VISUAIS
   ↓
GERAÇÃO DAS IMAGENS
   ↓
MOVIMENTO / ANIMAÇÃO OPCIONAL
   ↓
PLANO DE EDIÇÃO
   ↓
MASTER
   ↓
SEO
   ↓
PUBLICAÇÃO
   ↓
ANÁLISE DE RESULTADOS
   ↓
APRENDIZADO DO SISTEMA
Esta ordem é obrigatória.
3. REGRA CRÍTICA SOBRE O ÁUDIO
O COAE NÃO deverá possuir TTS obrigatório nem gerar a narração final.
O usuário utilizará externamente o Dark Planner / ElevenLabs para transformar o roteiro produzido pelo COAE em áudio.
O fluxo correto será:
COAE cria roteiro
        ↓
usuário exporta/copia o texto
        ↓
usuário gera o áudio no Dark Planner
        ↓
usuário baixa o áudio
        ↓
usuário envia o áudio ao COAE
        ↓
COAE analisa o áudio
Portanto:
O ÁUDIO APROVADO ENVIADO PELO USUÁRIO É A FONTE DE VERDADE TEMPORAL DA PRODUÇÃO.
Nenhuma etapa visual definitiva deverá ser criada supondo artificialmente a duração da narração.
4. PROIBIDO USAR CENAS FIXAS DE 8 SEGUNDOS
Remova qualquer regra antiga do projeto que determine:
1 cena = 8 segundos
Essa regra está cancelada.
O sistema deve criar cenas baseadas no conteúdo falado, tempo real da fala, significado, mudança de assunto, mudança de objeto, mudança de local, mudança de escala, mudança emocional, revelação, pergunta, comparação e consequência narrativa.
Uma cena poderá durar, por exemplo:
4.3 s
6.7 s
9.1 s
11.8 s
3.6 s
15.2 s
Desde que exista justificativa narrativa e visual. Não arredondar tudo para blocos artificiais.
5. PIPELINE AUDIO-FIRST
Depois que o usuário importar o áudio, execute:
AUDIO INGEST
     ↓
NORMALIZAÇÃO
     ↓
TRANSCRIÇÃO
     ↓
TIMESTAMPS
     ↓
ALINHAMENTO
     ↓
SEGMENTAÇÃO SEMÂNTICA
     ↓
DETECÇÃO DE MUDANÇAS NARRATIVAS
     ↓
PLANEJAMENTO VISUAL
Cada trecho deverá possuir, quando possível:
{
  "start": 12.42,
  "end": 19.83,
  "duration": 7.41,
  "transcript": "texto falado neste momento",
  "idea": "ideia principal",
  "visual_intent": "função da imagem",
  "emotion": "mistério",
  "importance": "high"
}
Utilizar timestamps reais.
6. TRANSCRIÇÃO E ALINHAMENTO
Criar uma camada independente chamada:
audio_alignment
Preferencialmente utilizando soluções locais quando possível. Pode utilizar tecnologias como FFmpeg, faster-whisper, Whisper, WhisperX quando apropriado, VAD, análise de silêncio, análise de timestamps e alinhamento palavra/frase.
Não acoplar o sistema permanentemente a apenas um motor.
Criar interface:
class TranscriptionProvider:
    transcribe(...)
    align(...)
Permitindo trocar o mecanismo posteriormente.
7. INTERPRETAÇÃO DO ÁUDIO
Transcrever não é suficiente. Depois da transcrição o sistema deverá entender semanticamente a narração.
Exemplo de narração:
Imagine uma estrela tão massiva que, depois de morrer, nem mesmo a luz consegue escapar.
O sistema deverá detectar conceitos como:
estrela massiva
morte estelar
colapso
escuridão
buraco negro
gravidade extrema
luz sendo aprisionada
E não simplesmente enviar a frase inteira como prompt de imagem.
8. SEGMENTADOR DE CENAS
Criar:
SceneSegmentationEngine
Ele deverá decidir onde uma cena começa, termina, continua, precisa ser subdividida, deve compartilhar o mesmo visual ou necessita de um novo visual.
Deverá considerar:
timestamps
semântica
ritmo
pausas
pontuação
mudanças narrativas
densidade de informação
importância dramática
continuidade visual
fadiga visual
Nunca cortar uma cena apenas porque determinado número de segundos foi atingido.
9. CENA NÃO É SINÔNIMO DE IMAGEM
Uma cena pode utilizar:
uma imagem
imagem + zoom
imagem + pan
imagem + parallax
imagem + câmera simulada
imagem + partículas
imagem + sobreposição
imagem + gráfico
imagem + texto
animação
vídeo externo
visualização científica
transição controlada
O sistema deverá decidir qual recurso faz sentido.
10. SINCRONIZAÇÃO COM A FALA
Toda cena deverá possuir:
scene_id
start_time
end_time
duration
transcript_reference
semantic_summary
visual_description
visual_function
camera_direction
movement
transition
continuity_reference
generation_status
audit_status
Exemplo:
{
  "scene_id": "SC023",
  "start_time": 91.24,
  "end_time": 98.71,
  "duration": 7.47,
  "transcript_reference": "Mas no centro da galáxia existe algo muito mais assustador.",
  "semantic_summary": "revelação do buraco negro central",
  "visual_function": "revelação",
  "camera_direction": "aproximação lenta em direção ao núcleo galáctico"
}
11. STORYBOARD
Depois da interpretação do áudio criar automaticamente um storyboard completo.
O storyboard deverá mostrar:
Campo	Conteúdo
Cena	SC001
Início	00:00:00.000
Fim	00:00:06.420
Duração	6.42 s
Narração	trecho correspondente
Ideia	significado daquele trecho
Visual	imagem necessária
Função	contextualizar/revelar/comparar/etc
Movimento	pan/zoom/parallax/etc
Transição	quando necessária
Continuidade	relação com cena anterior
Prioridade	baixa/média/alta
Status	pendente/aprovada/etc
O storyboard precisa ser editável manualmente.
12. PORTÃO 4.5 - STORYBOARD
Antes de gerar imagens definitivamente deverá existir:
PORTÃO 4.5 - APROVAÇÃO DO STORYBOARD
O sistema deverá verificar sincronização entre fala e imagem, mudanças excessivas, cenas longas sem justificativa, cenas curtas demais, repetição visual, redundância, falta de função narrativa, incoerência científica, continuidade visual, ritmo, fadiga e variedade.
Se houver falha crítica:
BLOCKED
Não prosseguir automaticamente.
O usuário deverá poder:
APROVAR
EDITAR
REGERAR
RESEGMENTAR
13. GERAÇÃO DE IMAGENS
Depois da aprovação do storyboard o COAE poderá gerar imagens correspondentes às cenas.
Criar camada:
ImageProvider
Nunca acoplar permanentemente o projeto a um único serviço.
Arquitetura:
core
   ↓
ImageProvider interface
   ↓
provider_x
provider_y
provider_local
Cada prompt deverá conter:
subject
environment
composition
camera
lighting
scale
scientific_constraints
cinematic_style
negative_constraints
continuity
14. PROMPT VISUAL
Não criar prompts genéricos como:
beautiful black hole in space cinematic 8k
Criar prompts cinematográficos estruturados.
Exemplo conceitual:
Scientific visualization of a supermassive black hole at the center
of a distant spiral galaxy, viewed from a wide cinematic perspective.

Accretion disk physically plausible, extreme scale emphasized by
surrounding stellar field, subtle gravitational lensing.

Camera slowly approaching the galactic nucleus.

Dark documentary cinematography, restrained lighting,
deep blacks, physically plausible cosmic colors,
high dynamic range.

No text.
No watermark.
No fantasy spacecraft.
No impossible planetary formations.
15. CONTINUIDADE VISUAL
Criar:
VisualContinuityEngine
O sistema deverá evitar que cada imagem pareça pertencer a um vídeo diferente.
Persistir:
paleta
contraste
iluminação
estilo
lente
escala
textura
nível de realismo
direção de luz
linguagem cinematográfica
Permitir referências entre cenas:
SC011 derives visual identity from SC010
16. BLOCO A
Preservar internamente o conceito de:
BLOCO A = componente visual principal
Ele poderá conter:
imagem base
prompt
referência
composição
metadados
seed quando existir
provedor
Não significa duração fixa.
17. BLOCO B
Definir:
BLOCO B = comportamento da cena
Pode incluir:
movimento
zoom
pan
parallax
animação
movimento de câmera
transição
overlays
efeitos
O Bloco B deverá estar relacionado ao Bloco A.
18. ANIMAÇÃO NÃO É OBRIGATÓRIA
Não animar tudo.
O sistema deverá poder decidir:
STATIC
SLOW_ZOOM
PAN
PARALLAX
CAMERA_MOVE
ANIMATION
EXTERNAL_VIDEO
Dependendo da necessidade. Um documentário premium pode utilizar imagens praticamente estáticas quando isso favorecer o momento.
19. ROTEIRO
O módulo de roteiro deverá criar conteúdos documentais longos e estruturados.
Evitar:
frases exageradas
clickbait vazio
repetições
enchimento
afirmações científicas sem suporte
linguagem infantilizada
Utilizar narrativa documental.
Estrutura sugerida:
HOOK
↓
PERGUNTA CENTRAL
↓
CONTEXTUALIZAÇÃO
↓
ESCALADA
↓
DESCOBERTA
↓
COMPLICAÇÃO
↓
IMPLICAÇÕES
↓
CLÍMAX
↓
REFLEXÃO
↓
ENCERRAMENTO
Não transformar isso em fórmula rígida.
20. O ROTEIRO PRECISA SER EDITÁVEL
Antes de gerar o áudio externamente o usuário deverá poder:
editar
regenerar parágrafo
expandir
encurtar
alterar tom
reorganizar
bloquear trechos
marcar como aprovado
Somente roteiro aprovado deverá ser exportado.
21. EXPORTAÇÃO DO ROTEIRO
Criar opções para:
TXT
Markdown
DOCX opcionalmente
clipboard
Criar três representações do roteiro: uma versão editorial mestre, uma versão específica para o Dark Planner com pausas <break time="..."/>, e uma versão limpa sem tags técnicas.
Exemplo:
exports/
   script_master.md
   narration_darkplanner.txt
   narration_clean.txt
script_master.md: versão editorial completa, podendo conter estrutura, capítulos, fontes, intenção narrativa, observações e metadados internos.
narration_darkplanner.txt: somente o texto narrável, com pausas no formato <break time="1.5s"/> e sem timestamps, instruções visuais ou observações técnicas.
narration_clean.txt: a mesma narração, porém sem tags <break> ou outras marcações técnicas.
22. IMPORTAÇÃO DO ÁUDIO
O usuário deverá poder selecionar:
MP3
WAV
M4A
O COAE deverá:
1.	validar arquivo;
2.	verificar duração;
3.	calcular hash;
4.	armazenar metadados;
5.	normalizar cópia de trabalho;
6.	preservar o original;
7.	iniciar transcrição;
8.	alinhar texto e áudio;
9.	apresentar resultado.
23. COMPARAÇÃO ROTEIRO x ÁUDIO
Como o usuário pode alterar algo durante a geração da narração, comparar:
roteiro aprovado
VS
áudio transcrito
Detectar:
frases removidas
frases acrescentadas
alterações
erros de pronúncia relevantes
diferença de sequência
O áudio deverá prevalecer para sincronização. O roteiro continuará sendo referência editorial.
24. MÓDULOS DO COAE
Implementar 13 módulos principais.
M1 - IDENTIDADE E CIÊNCIA
Responsável por:
identidade editorial
tom
linguagem
regras científicas
fontes
nível de certeza
hipóteses
fatos
especulações
M2 - TÍTULOS
Produzir e avaliar títulos considerando:
clareza
curiosidade
promessa
especificidade
força
coerência
risco de clickbait vazio
Guardar histórico.
M3 - THUMBNAILS
Criar conceitos de thumbnail.
Deverá definir:
objeto principal
escala
contraste
composição
emoção
texto opcional
relação com título
Evitar thumbnails genéricas.
M4 - PESQUISA + ROTEIRO
Responsável por:
pesquisa
dossiê
fontes
fact checking
estrutura
roteiro
versões
aprovação
exportação
O roteiro deverá ser criado antes da geração visual definitiva.
M5 - ÁUDIO + STORYBOARD + IMAGENS
Este módulo passa a possuir papel central.
Responsável por:
upload do áudio
transcrição
alinhamento
segmentação
interpretação
storyboard
prompts
imagens
continuidade
M6 - MOVIMENTOS
Responsável pelos Blocos B:
camera movement
zoom
pan
parallax
animation
transition
movement intensity
M7 - EDIÇÃO
Transformar:
áudio
+
storyboard
+
imagens
+
movimentos
em um plano completo de edição. Gerar timeline estruturada.
M8 - SEO
Gerar:
descrição
palavras-chave
capítulos
hashtags
metadados
Sem keyword stuffing.
M9 - SHORTS
Identificar trechos do documentário com potencial para vídeos curtos. Usar os timestamps reais do áudio.
M10 - COMUNIDADE
Criar:
posts
enquetes
perguntas
teasers
Relacionados ao conteúdo.
M11 - MÉTRICAS
Registrar resultados posteriores:
views
CTR
retenção
watch time
likes
comentários
inscritos
impressões
Não inventar integração com YouTube caso ela ainda não exista. Permitir importação manual.
M12 - APRENDIZADO
Utilizar histórico para descobrir:
temas fortes
títulos fortes
estilos de thumbnail
estruturas
quedas de retenção
padrões de audiência
Nunca alterar automaticamente regras fundamentais sem registro.
M13 - ORQUESTRAÇÃO
Responsável por:
pipeline
dependências
jobs
portões
estado
retries
versões
retomada
custos
logs
auditorias
Este é o cérebro operacional do COAE.
25. ARQUITETURA DE SOFTWARE
Utilizar arquitetura modular.
Núcleo recomendado:
Python 3.12+
Estrutura inicial:
coae/
│
├── app/
│   ├── core/
│   ├── modules/
│   ├── providers/
│   ├── pipelines/
│   ├── workers/
│   ├── audit/
│   ├── storage/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── utils/
│
├── frontend/
│
├── projects/
├── exports/
├── cache/
├── data/
├── tests/
├── scripts/
├── docs/
│
├── .env.example
├── README.md
└── pyproject.toml
É permitido melhorar essa estrutura desde que exista justificativa arquitetural.
26. INTERFACE
O COAE deverá possuir interface gráfica.
Prioridades:
clareza
simplicidade
fluxo visual
estado do projeto
controle humano
Dashboard inicial:
Projetos
Novo documentário
Continuar projeto
Projetos recentes
Configurações
Providers
Custos
Auditoria
Dentro de um projeto:
01 Pesquisa
02 Título
03 Thumbnail
04 Roteiro
05 Áudio
06 Storyboard
07 Imagens
08 Movimento
09 Edição
10 SEO
11 Exportação
12 Métricas
Mostrar visualmente qual estágio está:
PENDING
READY
RUNNING
REVIEW_REQUIRED
APPROVED
BLOCKED
FAILED
DONE
27. BANCO DE DADOS
Utilizar inicialmente:
SQLite
Mas abstrair acesso para permitir migração futura.
Persistir no mínimo:
projects
assets
scripts
script_versions
audio_files
transcriptions
segments
scenes
storyboards
image_prompts
generated_images
movement_plans
audit_runs
jobs
provider_runs
cost_records
exports
metrics
28. ESTADO PERSISTENTE
Nenhum processo importante pode depender apenas de memória RAM.
Se o sistema fechar durante:
transcrição
geração
auditoria
processamento
Ao reiniciar deverá identificar o estado anterior.
Criar mecanismo de:
resume
retry
reconcile
29. JOB ENGINE
Criar entidade:
Job
Estados:
PENDING
QUEUED
RUNNING
WAITING_USER
COMPLETED
FAILED
CANCELLED
UNKNOWN_REMOTE_RESULT
Persistir:
input_hash
provider
attempt
started_at
finished_at
error
result_reference
30. HASHES
Calcular hashes para ativos importantes.
Exemplo:
script_hash
audio_hash
storyboard_hash
prompt_hash
image_hash
Utilizar isso para detectar alterações, invalidar derivados, evitar processamento duplicado e garantir rastreabilidade.
31. DEPENDÊNCIAS ENTRE ARTEFATOS
Exemplo:
roteiro mudou
   ↓
áudio anterior pode ficar desatualizado
Porém não apagar automaticamente. Marcar:
OUTDATED
Outro exemplo:
áudio mudou
   ↓
transcrição
segmentação
storyboard
imagens
timeline
podem estar desatualizados.
Criar invalidation graph.
32. AUTOAUDITORIA
Todo módulo importante deverá possuir o ciclo:
GERAR
↓
VALIDAR
↓
AUDITAR
↓
CORRIGIR
↓
AUDITAR NOVAMENTE
↓
APROVAR
Gerador, auditor e corretor devem ser funções logicamente separadas.
Não utilizar:
gerar e imediatamente declarar que está perfeito
33. ESTRUTURA DA AUDITORIA
Resultado mínimo:
{
  "decision": "PASS",
  "criteria": [],
  "scores": {},
  "evidence": [],
  "critical_issues": [],
  "suggested_fixes": [],
  "uncertainties": [],
  "auditor_version": "",
  "input_hashes": {}
}
Decisões:
PASS
PASS_WITH_WARNINGS
REVISION_REQUIRED
BLOCKED
34. LIMITE DE AUTOCORREÇÃO
Máximo padrão:
3 ciclos
Se continuar falhando:
REVIEW_REQUIRED
Nunca ficar preso em loop tentando atingir perfeição.
35. AUDITORIA DO ROTEIRO
Verificar:
hook
promessa
clareza
ritmo
redundância
repetição
progressão
explicação científica
retenção
conclusão
afirmações suspeitas
36. AUDITORIA AUDIOVISUAL
Verificar:
imagem realmente corresponde à fala?
imagem acrescenta algo?
existe repetição?
tempo visual é adequado?
há excesso de cortes?
há cenas longas demais?
há cenas curtas demais?
movimentos fazem sentido?
há coerência estética?
há continuidade?
37. TESTE “PARECE IA?”
Criar avaliação específica:
AI_GENERATED_LOOK_RISK
Detectar:
prompts genéricos
mesma composição repetida
movimento excessivo
transições artificiais
imagens desconectadas
cortes regulares demais
visual aleatório
uso exagerado de partículas
aspecto slideshow
O objetivo é evitar aparência de vídeo industrialmente gerado por IA.
38. FUNÇÃO NARRATIVA VISUAL
Nenhuma cena deverá existir apenas porque:
"precisamos mostrar alguma coisa"
Cada visual deverá possuir visual_function.
Valores possíveis:
ESTABLISH
EXPLAIN
COMPARE
SCALE
REVEAL
BUILD_TENSION
TRANSITION
EVIDENCE
SIMULATION
REFLECTION
EMOTIONAL_PAUSE
39. PESQUISA CIENTÍFICA
O sistema deverá diferenciar:
FACT
CONSENSUS
CURRENT_MODEL
HYPOTHESIS
SPECULATION
UNKNOWN
Afirmações extraordinárias não devem aparecer como fatos. Guardar fontes utilizadas na criação do roteiro.
40. PROVIDERS
Criar adaptadores independentes para:
TextProvider
ResearchProvider
TranscriptionProvider
AlignmentProvider
ImageProvider
VideoProvider
AuditProvider
Não espalhar chamadas de API pelo código.
41. MODOS DO SISTEMA
Preservar:
OFFLINE
ASSISTED
API
OFFLINE
Utilizar apenas capacidades locais disponíveis.
ASSISTED
O COAE gera arquivos/prompts e o usuário realiza determinada etapa externamente.
API
Integração direta quando houver API configurada.
42. DARK PLANNER
O Dark Planner deverá funcionar no modo:
ASSISTED
Fluxo:
COAE gera narration_darkplanner.txt com <break time="..."/>
↓
usuário usa o texto no Dark Planner
↓
usuário gera e baixa o áudio
↓
usuário importa o áudio no COAE
↓
COAE mede os tempos reais e continua
42.1 FORMATO DE NARRAÇÃO PARA DARK PLANNER
O COAE deverá gerar automaticamente uma versão do roteiro especificamente preparada para narração no Dark Planner. O arquivo obrigatório será narration_darkplanner.txt.
As pausas deverão ser inseridas no próprio texto exatamente no formato demonstrado pelo fluxo do usuário:
<break time="1s"/>
<break time="1.5s"/>
<break time="2s"/>
<break time="3s"/>
Essas marcações controlam pausas da narração. Elas NÃO são timestamps de cena e NÃO substituem os tempos medidos posteriormente a partir do áudio real.
O sistema deverá escolher as pausas de forma contextual, considerando ritmo narrativo, mudança de ideia, intensidade emocional, perguntas, revelações, transições, momentos contemplativos e encerramentos de blocos.
Referência geral de uso:
1s   = mudança leve de pensamento ou pequena pausa natural
1.5s = mudança de parágrafo, reflexão, preparação ou pequena revelação
2s   = virada narrativa, pergunta importante, impacto ou mudança significativa
3s   = momento excepcional de forte impacto, conclusão ou encerramento
O sistema poderá utilizar valores intermediários, como 0.8s, 1.2s ou 2.5s, quando houver justificativa narrativa. Não deverá variar os valores sem necessidade e não deverá inserir <break> mecanicamente após toda frase.
Exemplo de saída:
Olhe para uma galáxia distante.

Ela parece uma ilha perdida na escuridão. <break time="1.5s"/>

Agora, afaste-se.

Outras galáxias começam a surgir. Primeiro em pequenos grupos. Depois em aglomerados. <break time="1s"/>

Linhas aparecem.

Nós luminosos se formam.

Regiões imensas ficam quase desertas. <break time="1.5s"/>
O arquivo narration_darkplanner.txt deverá conter somente conteúdo narrável e tags <break>. Não incluir títulos técnicos, nomes de cenas, timestamps, instruções de câmera, prompts de imagem, observações editoriais ou marcações de storyboard.
O arquivo narration_clean.txt deverá preservar o mesmo texto e a mesma ordem, removendo apenas as tags <break> e demais marcações técnicas.
REGRA CRÍTICA DE TEMPO
Nunca confundir pausa de narração com sincronização audiovisual:
<break time="1.5s"/>  = pausa intencional na narração do Dark Planner
00:42.381 -> 00:49.724 = intervalo temporal medido no áudio real
Depois que o usuário importar o áudio produzido no Dark Planner, o áudio passa a ser a fonte de verdade temporal. Storyboard, cenas, imagens, movimentos, legendas e timeline deverão usar os timestamps medidos no áudio, não os valores das tags <break>.
Fluxo obrigatório:
ROTEIRO
↓
COAE insere pausas <break>
↓
narration_darkplanner.txt
↓
usuário gera a voz no Dark Planner
↓
áudio é importado no COAE
↓
COAE mede os tempos reais
↓
timestamps
↓
segmentação
↓
storyboard
↓
cenas
Os <break> ajudam a construir a interpretação vocal. Os timestamps reais do áudio controlam a produção audiovisual.
Não implementar automação frágil clicando automaticamente na interface do Dark Planner. Não declarar que existe integração por API sem documentação real.
43. CAPCUT
Da mesma forma, o COAE poderá inicialmente produzir:
timeline
instruções
assets
nomes organizados
EDL quando possível
JSON próprio
CSV
legendas
Para facilitar a edição. Não alegar integração direta com CapCut sem comprovação.
44. PLANO DE EDIÇÃO
M7 deverá gerar algo semelhante a:
00:00.000 → 00:06.420
SC001
Visual: galáxia distante
Movimento: slow zoom
Narração: ...
Transição: none

00:06.420 → 00:11.830
SC002
Visual: aproximação da galáxia
Movimento: push-in
Narração: ...
Transição: cinematic cut
Tudo baseado no áudio real.
45. LEGENDAS
Gerar automaticamente:
SRT
VTT
Utilizando timestamps do áudio. Permitir revisão antes da exportação.
46. ORGANIZAÇÃO DE ASSETS
Utilizar IDs previsíveis:
SC001
SC002
SC003
Arquivos:
SC001_image.png
SC001_prompt.json
SC001_metadata.json

SC002_image.png
...
Nunca depender somente de nomes descritivos.
47. ESTRUTURA DE PROJETO
Cada produção deverá possuir:
projects/
└── COAE-2026-0001/
    ├── project.json
    ├── research/
    ├── script/
    ├── audio/
    ├── transcription/
    ├── storyboard/
    ├── images/
    ├── motion/
    ├── timeline/
    ├── subtitles/
    ├── seo/
    ├── exports/
    ├── audits/
    └── logs/
48. VERSIONAMENTO INTERNO
Guardar versões.
Exemplo:
script_v001
script_v002
storyboard_v001
storyboard_v002
Não sobrescrever silenciosamente trabalhos anteriores.
49. CUSTOS
Criar módulo de controle de custos de provedores.
Registrar:
provider
operation
estimated_cost
actual_cost
currency
project
asset
timestamp
Antes de operações potencialmente pagas mostrar estimativa.
50. ORÇAMENTO
Permitir orçamento por projeto:
R$ / USD
Estados:
AVAILABLE
RESERVED
SPENT
RELEASED
Nunca disparar dezenas de gerações pagas acidentalmente.
51. RETRIES
Retries somente para erros transitórios.
Utilizar:
exponential backoff
maximum attempts
Nunca repetir infinitamente.
52. SEGREDOS
Nenhuma chave deverá entrar no Git.
Usar:
.env
.env.example
Adicionar .env ao .gitignore.
53. LOGS
Utilizar logs estruturados.
Registrar:
timestamp
project_id
module
job_id
operation
severity
provider
duration
result
error
Não registrar chaves ou segredos.
54. PROVIDER CAPABILITIES
Criar:
docs/provider_capabilities.md
Registrar capacidades reais. Nunca escrever funcionalidades imaginárias.
55. CONFLITOS DE REGRAS
Criar:
docs/rule_conflicts.md
Regra atual que obrigatoriamente deverá constar:
OLD:
Storyboard dividido em slots fixos de 8 segundos.

NEW:
Storyboard orientado pelo áudio real e pela semântica.
Duração variável de cenas.

DECISION:
NEW rule overrides OLD rule.
56. PROJECT STATE
Criar:
docs/PROJECT_STATE.md
Atualizar ao final de cada fase.
Formato:
Concluído
Em desenvolvimento
Próximo passo
Problemas conhecidos
Decisões tomadas
Pendências externas
Isso permitirá que outro agente continue o trabalho.
57. README
O README deverá permitir que alguém clone e execute o COAE.
Incluir:
pré-requisitos
instalação
configuração
banco
execução
frontend
backend
FFmpeg
Whisper
providers
testes
troubleshooting
58. TESTES
Criar testes desde o início.
Testar principalmente:
audio ingestion
timestamps
scene segmentation
database
job resume
hash invalidation
audit pipeline
provider failures
storyboard generation
59. TESTE CRÍTICO DE SINCRONIZAÇÃO
Criar teste automatizado garantindo:
scene[n].end_time <= audio.duration
E:
scene[n].start_time >= previous_scene.end_time
Quando cenas forem consecutivas.
Também detectar:
gaps
overlaps
timestamps inválidos
duração negativa
60. NÃO CRIAR MOCK COMO RESULTADO FINAL
Mocks são permitidos apenas para testes.
A aplicação real deve executar funcionalidades reais sempre que a tecnologia estiver disponível.
Não apresentar:
fake generated image
fake transcription
fake provider result
como integração concluída.
61. ERROS DEVEM SER HONESTOS
Se determinado provider não estiver configurado:
PROVIDER_NOT_CONFIGURED
Se não houver API:
MANUAL_EXTERNAL_STEP_REQUIRED
Nunca mascarar limitações.
62. HUMAN-IN-THE-LOOP
O usuário deverá poder intervir principalmente em:
roteiro
título
thumbnail
transcrição
segmentação
storyboard
imagem
edição
publicação
IA auxilia. Usuário decide.
63. APROVAÇÕES
Criar conceito de portões.
Exemplo:
Gate 0 - projeto criado
Gate 1 - pesquisa
Gate 2 - título
Gate 3 - roteiro
Gate 4 - áudio
Gate 4.5 - storyboard
Gate 5 - imagens
Gate 6 - edição
Gate 7 - exportação
64. AUDITORIA GLOBAL DO EPISÓDIO
Antes da exportação final verificar:
A promessa inicial foi cumprida?
O vídeo progride?
Há trechos mortos?
Há redundância?
As imagens acompanham a narração?
Existe continuidade?
O conteúdo científico está coerente?
Há excesso de movimentos?
Há excesso de transições?
Parece um slideshow?
Parece conteúdo automatizado?
O encerramento é satisfatório?
65. AUTOAUDITORIA DO PRÓPRIO SOFTWARE
Além do conteúdo audiovisual, o COAE deverá possuir ferramentas de diagnóstico da própria aplicação.
Verificar:
banco
pastas
FFmpeg
providers
modelos
configurações
permissões
jobs presos
arquivos órfãos
hashes inconsistentes
dependências
Criar tela:
System Health
66. RECONCILIAÇÃO
Ao iniciar:
scan unfinished jobs
scan orphan assets
check DB references
check files
check provider unknown states
Corrigir apenas quando seguro.
Em caso de dúvida:
REVIEW_REQUIRED
67. NÃO APAGAR AUTOMATICAMENTE
Arquivos antigos ou órfãos deverão ser inicialmente movidos/marcados para revisão. Nunca excluir dados importantes silenciosamente.
68. DESENVOLVIMENTO ORIENTADO A FATIAS VERTICAIS
Não tente construir os 13 módulos simultaneamente.
Primeiro entregue o fluxo funcional:
CRIAR PROJETO
↓
ESCREVER/IMPORTAR ROTEIRO
↓
EXPORTAR ROTEIRO
↓
IMPORTAR ÁUDIO
↓
TRANSCREVER
↓
SEGMENTAR
↓
MOSTRAR STORYBOARD
↓
EDITAR/APROVAR
Esse é o primeiro grande marco.
Depois:
IMAGENS
↓
MOVIMENTOS
↓
EDIÇÃO
Depois:
SEO
MÉTRICAS
APRENDIZADO
69. FASE 0 - BOOTSTRAP
Criar:
estrutura do projeto
Git
ambiente Python
configuração
SQLite
logging
tests
README inicial
PROJECT_STATE
O projeto deverá executar antes de avançar.
70. FASE 1 - PROJECT ENGINE
Implementar:
criar projeto
abrir
salvar
listar
arquivar
estado
diretórios
IDs
71. FASE 2 - ROTEIRO
Implementar:
editor
versionamento
aprovação
exportação
72. FASE 3 - AUDIO INGESTION
Implementar fluxo real:
selecionar arquivo
validar
copiar
hash
FFmpeg
metadata
waveform opcional
73. FASE 4 - TRANSCRIÇÃO
Implementar transcrição real. Priorizar opção local inicialmente. Persistir resultado.
74. FASE 5 - SEGMENTAÇÃO INTELIGENTE
Criar algoritmo híbrido utilizando:
timestamps
pontuação
silêncios
semantic similarity
LLM opcional
regras narrativas
O sistema não pode depender exclusivamente de LLM para algo que pode ser calculado deterministicamente.
75. FASE 6 - STORYBOARD
Criar interface completa de storyboard.
Possibilitar:
split
merge
alterar start/end
editar descrição
trocar função visual
regenerar prompt
bloquear cena
76. FASE 7 - AUDITORIA DO STORYBOARD
Implementar Gate 4.5. Somente depois avançar.
77. FASE 8 - IMAGENS
Implementar sistema de providers e geração.
Permitir geração:
individual
seleção múltipla
fila controlada
Nunca gerar todas as cenas pagas sem confirmação.
78. FASE 9 - MOVIMENTO
Criar recomendações de movimento e animação.
79. FASE 10 - TIMELINE
Construir timeline baseada nos timestamps reais.
80. FASE 11 - EXPORTAÇÃO
Exportar pacote:
audio
images
timeline
subtitles
storyboard
prompts
editing_plan
81. FASE 12 - MÓDULOS EDITORIAIS
Adicionar:
pesquisa
títulos
thumbnail
SEO
Shorts
comunidade
82. FASE 13 - MÉTRICAS E APRENDIZADO
Adicionar M11 e M12.
83. EXPERIÊNCIA DE USO IDEAL
O usuário deverá conseguir:
1. Abrir COAE.

2. Clicar em:
   Novo Documentário.

3. Informar:
   "O que aconteceria se o Sol desaparecesse agora?"

4. COAE pesquisar e ajudar a criar roteiro.

5. Usuário revisar.

6. COAE exportar narration_darkplanner.txt com as pausas <break>.

7. Usuário usar narration_darkplanner.txt para gerar a voz no Dark Planner.

8. Usuário voltar ao COAE.

9. Arrastar narration.mp3.

10. COAE transcrever.

11. COAE sincronizar.

12. COAE compreender a narrativa.

13. COAE criar cenas.

14. Usuário visualizar storyboard.

15. Ajustar cenas se necessário.

16. Aprovar Gate 4.5.

17. COAE gerar prompts.

18. COAE gerar imagens.

19. COAE sugerir movimentos.

20. COAE criar timeline.

21. COAE gerar legendas.

22. COAE preparar pacote de edição.

23. COAE gerar SEO.

24. Usuário finalizar/publicar.

25. Posteriormente registrar métricas.
Esse fluxo deverá ser simples e compreensível.
84. PRINCÍPIO AUDIO-FIRST
A partir da importação do áudio:
TODAS AS DECISÕES DE TEMPO DEVEM SER DERIVADAS DO ÁUDIO REAL.
Nunca calcular duração pela quantidade de caracteres como informação final.
Estimativas podem existir antes do áudio apenas como estimativas. Marcar claramente:
ESTIMATED
Após áudio:
MEASURED
85. PRINCÍPIO SEMANTIC-FIRST
Não utilizar apenas silêncio para separar cenas.
Um narrador pode falar continuamente durante 30 segundos e mencionar quatro conceitos visualmente diferentes. O sistema deverá compreender isso.
Da mesma maneira, uma pausa de 2 segundos não significa obrigatoriamente nova cena.
86. DENSIDADE VISUAL DINÂMICA
A frequência de mudança visual deve variar.
Trechos explicativos densos:
mais mudanças
Trechos contemplativos:
menos mudanças
Revelações:
visual pode permanecer por mais tempo
Não criar ritmo mecânico.
87. PRIORIDADE DO SISTEMA
A ordem de prioridade deverá ser:
1. Correção
2. Integridade dos dados
3. Sincronização
4. Utilidade
5. Qualidade audiovisual
6. Automação
7. Velocidade
Nunca sacrificar os primeiros itens apenas para automatizar mais.
88. ECONOMIA DE TOKENS PARA O AGENTE DE PROGRAMAÇÃO
Durante o desenvolvimento, não fique me explicando conceitos básicos. Não produza textos gigantes a cada arquivo.
Priorize:
implementar
testar
corrigir
documentar resumidamente
continuar
Quando precisar tomar decisão técnica razoável, tome. Não fique perguntando autorização para cada arquivo.
89. COMO VOCÊ DEVE TRABALHAR
Para cada fase:
1. Leia PROJECT_STATE.md.

2. Inspecione código atual.

3. Defina objetivo da fase.

4. Implemente.

5. Execute lint/typecheck quando aplicável.

6. Execute testes.

7. Corrija erros.

8. Faça smoke test.

9. Atualize documentação.

10. Atualize PROJECT_STATE.md.

11. Continue para próxima tarefa lógica.
90. NÃO DECLARE SUCESSO SEM TESTAR
Você não poderá dizer:
"está funcionando"
Apenas porque escreveu os arquivos.
Antes:
instale
execute
teste
inspecione erros
corrija
execute novamente
91. QUANDO ENCONTRAR ERRO
Não abandone imediatamente.
Faça:
diagnóstico
↓
correção
↓
teste
Se ainda falhar:
nova hipótese
↓
nova correção
↓
teste
Somente registrar bloqueio quando existir motivo externo real.
92. NÃO REESCREVER O PROJETO DESNECESSARIAMENTE
Respeitar código funcional existente. Refatorar somente quando houver benefício claro.
93. QUALIDADE DE CÓDIGO
Exigir:
tipagem
funções pequenas
nomes claros
separação de responsabilidades
tratamento de erros
logs
configuração externa
testabilidade
Evitar overengineering.
94. DOCUMENTAÇÃO DE DECISÕES
Decisões importantes deverão gerar ADRs quando apropriado:
docs/adr/
Exemplo:
ADR-001-audio-is-source-of-truth.md
95. ADR OBRIGATÓRIO
Criar:
ADR - Audio as Temporal Source of Truth
Decisão:
Após a importação do áudio aprovado, os timestamps reais da narração substituem qualquer estimativa temporal anterior.
Consequência:
Storyboard, cenas, legendas, imagens, movimentos e timeline utilizam os tempos reais do áudio.
96. OUTRO ADR OBRIGATÓRIO
Criar:
ADR - Variable Duration Scenes
Decisão:
O sistema não utiliza slots fixos de oito segundos.
A cena termina quando a narrativa ou intenção visual indicar, respeitando o áudio.
97. DEFINITION OF DONE
Uma fase somente estará concluída quando:
código existe
+
código executa
+
testes principais passam
+
fluxo principal funciona
+
erros são tratados
+
estado é persistido
+
documentação foi atualizada
98. PRIMEIRO GRANDE CRITÉRIO DE ACEITE
Antes de começar recursos avançados, obrigatoriamente prove este fluxo:
CRIAR PROJETO
↓
ADICIONAR ROTEIRO
↓
EXPORTAR
↓
IMPORTAR MP3
↓
TRANSCREVER
↓
GERAR TIMESTAMPS
↓
SEGMENTAR
↓
GERAR STORYBOARD
↓
MOSTRAR STORYBOARD NA INTERFACE
↓
EDITAR
↓
SALVAR
↓
FECHAR A APLICAÇÃO
↓
ABRIR NOVAMENTE
↓
CONTINUAR DO MESMO PONTO
Se isso não funcionar, não avance para geração massiva de imagens.
99. SEGUNDO GRANDE CRITÉRIO DE ACEITE
Depois implementar:
STORYBOARD APROVADO
↓
GERAR PROMPT DA CENA
↓
GERAR/IMPORTAR IMAGEM
↓
VINCULAR À CENA
↓
VISUALIZAR NA TIMELINE
↓
EXPORTAR PLANO DE EDIÇÃO
100. TERCEIRO GRANDE CRITÉRIO DE ACEITE
Executar um episódio de teste completo e verificar:
nenhuma cena fora da duração do áudio
nenhum timestamp negativo
nenhum overlap não intencional
nenhuma cena sem função visual
nenhum arquivo perdido
nenhuma dependência crítica quebrada
101. NÃO PERDER O OBJETIVO PRINCIPAL
Este sistema existe para transformar:
UMA IDEIA
em uma produção audiovisual organizada.
Mas a automação nunca deverá destruir:
qualidade
coerência
ritmo
intenção narrativa
controle humano
102. RESULTADO ESPERADO
O produto final deverá permitir que uma pessoa produza documentários de alta qualidade com muito menos trabalho operacional.
O COAE deverá cuidar de:
organização
pesquisa
roteiro
controle
interpretação do áudio
sincronização
storyboard
prompts
assets
auditoria
timeline
legendas
SEO
histórico
dados
Enquanto o usuário mantém controle criativo.
103. INSTRUÇÃO DE INÍCIO PARA O AGENTE
Agora comece de verdade.
Antes de gerar código aleatoriamente:
1.	verifique se já existe algum projeto na pasta atual;
2.	leia todos os arquivos existentes;
3.	preserve o que estiver correto;
4.	identifique incompatibilidades com este Prompt Mestre;
5.	atualize docs/rule_conflicts.md;
6.	crie ou atualize docs/PROJECT_STATE.md;
7.	escreva um plano técnico curto;
8.	comece pela primeira fatia vertical funcional.
Se o projeto ainda não existir, inicialize-o.
A primeira meta prática é:
Criar projeto COAE
+
persistência SQLite
+
editor/importação de roteiro
+
exportação do roteiro
+
upload real de áudio
+
FFmpeg
+
transcrição
+
timestamps
+
segmentação
+
storyboard editável
+
persistência e retomada
Não comece pela geração de imagens. Não comece pelo SEO. Não comece tentando construir todos os módulos.
Construa primeiro o núcleo que transforma áudio real em storyboard sincronizado.
Depois que esse fluxo estiver funcional e testado, evolua o sistema incrementalmente.
104. REGRA FINAL
Sempre que houver conflito entre uma implementação antiga e este documento, este Prompt Mestre V2.1 prevalece.
Principalmente:
ÁUDIO EXTERNO
> TTS INTERNO

TIMESTAMPS REAIS
> ESTIMATIVAS

CENAS SEMÂNTICAS
> SLOTS FIXOS

DURAÇÃO VARIÁVEL
> 8 SEGUNDOS FIXOS

STORYBOARD
> GERAÇÃO VISUAL DIRETA

CONTROLE HUMANO
> AUTOMAÇÃO CEGA

TESTE REAL
> DECLARAÇÃO DE SUCESSO

PERSISTÊNCIA
> ESTADO TEMPORÁRIO

NARRAÇÃO DARK PLANNER COM <break>
> TEXTO SEM CONTROLE DE PAUSAS

TIMESTAMPS MEDIDOS DO ÁUDIO
> USAR <break> COMO TIMESTAMP
Você está construindo um produto real, não uma demonstração.
Comece a implementação agora.
