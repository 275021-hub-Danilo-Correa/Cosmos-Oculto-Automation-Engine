# COAE — GitHub Copilot Repository Instructions

Este repositório contém o **COAE — Cosmos Oculto Automation Engine**.

O COAE é um sistema de produção audiovisual assistida por IA para criação de documentários científicos do canal **Cosmos Oculto | Documentários do Universo**.

## Fonte de verdade

Antes de implementar ou alterar funcionalidades relevantes, consulte:

`docs/COAE_SPEC.md`

Esse arquivo contém a especificação oficial do produto, arquitetura, módulos, regras de negócio, pipeline audiovisual e critérios de aceite.

Consulte também:

`docs/PROJECT_STATE.md`

Esse arquivo registra o estado atual do desenvolvimento, funcionalidades concluídas, trabalho em andamento, próximos passos, problemas conhecidos e decisões técnicas.

Em caso de conflito entre uma implementação antiga e `docs/COAE_SPEC.md`, a especificação atual prevalece, exceto quando houver uma decisão técnica posterior explicitamente documentada.

## Forma de trabalho

Não produza apenas pseudocódigo ou exemplos quando for possível implementar a funcionalidade real.

Ao receber uma tarefa de desenvolvimento:

1. Inspecione o código existente relacionado.
2. Consulte `docs/COAE_SPEC.md`.
3. Consulte `docs/PROJECT_STATE.md`.
4. Preserve funcionalidades já operacionais.
5. Implemente a menor solução completa e coerente.
6. Execute os testes relevantes.
7. Execute lint, type checking ou validações existentes quando aplicável.
8. Corrija erros encontrados.
9. Faça um smoke test do fluxo alterado quando possível.
10. Atualize `docs/PROJECT_STATE.md` quando houver avanço significativo, decisão arquitetural ou problema conhecido.

Nunca declare uma funcionalidade como concluída ou funcionando apenas porque o código foi escrito.

Teste-a quando houver meios locais para isso.

## Desenvolvimento incremental

Não tente implementar todo o COAE de uma única vez.

Priorize fatias verticais funcionais.

A prioridade inicial do produto é:

Projeto
→ persistência
→ roteiro
→ exportação para Dark Planner
→ importação de áudio
→ transcrição
→ timestamps reais
→ segmentação semântica
→ storyboard editável
→ persistência
→ retomada do projeto.

Somente após esse núcleo estar funcional e testado, avance progressivamente para geração de imagens, movimentos, timeline, legendas, exportação audiovisual, SEO, métricas e aprendizado.

## Regra Audio-First

Depois que o usuário importar o áudio aprovado, o áudio passa a ser a **fonte de verdade temporal**.

Não utilize estimativas de duração como timestamps finais.

Storyboard, cenas, legendas, movimentos e timeline devem utilizar tempos derivados do áudio real.

## Cenas com duração variável

Nunca imponha duração fixa de oito segundos às cenas.

A duração deve ser determinada por:

* conteúdo falado;
* semântica;
* ritmo narrativo;
* mudança de assunto;
* mudança visual;
* intenção emocional;
* continuidade;
* timestamps reais do áudio.

## Dark Planner

O COAE não deve depender de TTS interno para a narração final.

O fluxo previsto é:

COAE cria o roteiro
→ usuário exporta o texto
→ usuário gera a narração externamente
→ usuário importa o áudio no COAE
→ COAE analisa o áudio
→ COAE cria storyboard e produção visual sincronizados.

O sistema deverá produzir, quando aplicável:

`script_master.md`

`narration_darkplanner.txt`

`narration_clean.txt`

`narration_darkplanner.txt` deve conter somente o texto destinado à narração e as marcações de pausa compatíveis com o fluxo utilizado pelo projeto.

Exemplos:

```text
<break time="1s"/>
<break time="1.5s"/>
<break time="2s"/>
<break time="3s"/>
```

Essas tags são pausas de narração.

Elas NÃO são timestamps audiovisuais.

Não confunda:

```text
<break time="1.5s"/>
```

com:

```text
00:42.381 → 00:49.724
```

O primeiro controla uma pausa da narração.

O segundo representa tempo real obtido posteriormente através da análise do áudio.

## Arquitetura

Mantenha separação clara de responsabilidades.

Evite lógica de negócio espalhada pela interface, rotas ou componentes.

Integrações externas devem ser abstraídas através de providers ou adapters sempre que apropriado.

Exemplos conceituais:

```text
TextProvider
ResearchProvider
TranscriptionProvider
AlignmentProvider
ImageProvider
VideoProvider
AuditProvider
```

Não acople o núcleo permanentemente a um único serviço externo.

## Persistência

Processos importantes não devem depender exclusivamente de memória RAM.

Estados importantes devem ser persistidos.

O sistema deve conseguir identificar trabalho interrompido e, quando seguro, continuar ou reconciliar o estado ao reiniciar.

Não sobrescreva silenciosamente versões importantes de artefatos.

## Banco de dados

A implementação inicial utiliza SQLite quando compatível com a especificação.

Mantenha o acesso aos dados organizado para facilitar evolução futura.

Mudanças de schema devem ser realizadas de maneira controlada.

## Jobs

Operações demoradas ou potencialmente falhas devem possuir estado explícito quando fizer sentido.

Exemplos:

```text
PENDING
QUEUED
RUNNING
WAITING_USER
COMPLETED
FAILED
CANCELLED
```

Não crie loops infinitos de retry.

## Hashes e dependências

Utilize hashes e metadados quando forem necessários para rastrear alterações em artefatos.

Quando um artefato de origem mudar, seus derivados podem precisar ser marcados como desatualizados.

Não apague automaticamente derivados anteriores apenas porque ficaram desatualizados.

## Segurança

Nunca coloque tokens, senhas, credenciais ou chaves de API diretamente no código.

Utilize variáveis de ambiente.

Mantenha `.env` fora do Git.

Forneça `.env.example` somente com nomes de variáveis e valores fictícios.

Nunca registre segredos nos logs.

## Código

Prefira:

* código legível;
* nomes descritivos;
* funções pequenas;
* tipagem quando disponível;
* baixo acoplamento;
* tratamento explícito de erros;
* componentes reutilizáveis quando realmente necessários;
* testes para regras críticas;
* configuração externa em vez de valores secretos ou ambientais hardcoded.

Evite overengineering.

Não crie abstrações sem necessidade real.

## Erros

Não esconda falhas.

Quando uma integração não estiver configurada, apresente erro ou estado explícito.

Exemplos conceituais:

```text
PROVIDER_NOT_CONFIGURED
MANUAL_EXTERNAL_STEP_REQUIRED
REVIEW_REQUIRED
```

Não apresente mocks como se fossem resultados reais.

## Testes

Adicione ou atualize testes sempre que uma alteração introduzir lógica relevante.

Dê atenção especial a:

* persistência;
* importação de áudio;
* timestamps;
* segmentação;
* banco de dados;
* retomada de jobs;
* invalidação de dependências;
* storyboard;
* providers;
* tratamento de falhas.

Para cenas consecutivas, valide quando aplicável:

```text
scene.start_time >= 0
scene.end_time > scene.start_time
scene.end_time <= audio.duration
```

Detecte overlaps e gaps inesperados quando eles não forem intencionais.

## Autoauditoria

Para operações críticas, favoreça o processo:

```text
GERAR
→ VALIDAR
→ AUDITAR
→ CORRIGIR
→ TESTAR NOVAMENTE
```

Gerador e auditor não devem ser tratados como a mesma responsabilidade lógica quando a separação trouxer benefício real.

Evite ciclos infinitos de autocorreção.

## Interface

A interface deve priorizar:

* clareza;
* simplicidade;
* estado visível;
* feedback de operações;
* recuperação após erros;
* controle humano;
* continuidade de trabalho.

Não sacrifique usabilidade apenas para adicionar automação.

## Controle humano

O usuário deve manter controle sobre decisões editoriais e audiovisuais importantes.

Automação auxilia.

O usuário aprova.

Não execute operações potencialmente caras em massa sem uma ação clara do usuário ou uma regra explicitamente aprovada.

## Documentação

Decisões arquiteturais importantes podem ser registradas em:

`docs/adr/`

Mantenha `docs/PROJECT_STATE.md` atualizado durante a evolução do projeto.

Não crie documentação fictícia afirmando suporte a APIs, integrações ou funcionalidades que ainda não existem.

## Estado do projeto

Ao terminar uma etapa significativa, atualize `docs/PROJECT_STATE.md` usando aproximadamente:

```text
Concluído
Em desenvolvimento
Próximo passo
Problemas conhecidos
Decisões tomadas
Pendências externas
```

O objetivo é permitir que uma nova sessão de agente compreenda rapidamente onde o desenvolvimento parou.

## Prioridades

Quando houver conflito entre objetivos, utilize esta ordem:

```text
1. Correção
2. Integridade dos dados
3. Persistência
4. Sincronização audiovisual
5. Usabilidade
6. Qualidade do conteúdo
7. Automação
8. Velocidade de desenvolvimento
```

## Regra final

Este é um produto real, não uma demonstração.

Não simule conclusão.

Não esconda limitações.

Não substitua funcionalidade real por mock fora dos contextos apropriados de teste.

Implemente incrementalmente.

Execute.

Teste.

Corrija.

Documente.

E preserve a continuidade do projeto.
