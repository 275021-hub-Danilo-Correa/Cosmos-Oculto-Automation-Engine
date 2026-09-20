# Trazer projetos de outro computador

No COAE de origem, abra o projeto e vá a **Montagem e arquivos → Baixar projeto completo**.
No computador de destino, abra **Meus projetos → Importar projeto**, selecione o ZIP e
clique em **Importar ZIP**. O limite é 256 MB para envio e 2 GB descompactados.

A importação cria uma cópia com novo ID. Não substitui o banco nem os projetos atuais.
Roteiros, aprovações registradas, áudios, transcrições, versões de storyboard, imagens
e histórico são transferidos do snapshot do banco. Os caminhos dos materiais e os
vínculos entre registros são adaptados ao novo computador. Arquivos ausentes ou hashes
divergentes impedem a importação. Confira o player e as cenas antes de continuar.

Eventos e arquivos históricos mantêm referências da origem; o evento `PROJECT_IMPORTED`
registra o mapeamento de IDs. Tarefas em execução tornam-se interrompidas/incertas.
Tickets de geração ficam arquivados: não são retomados automaticamente em outro serviço.
Modelos e configurações privadas de serviços não são instalados por esse processo.

## Quando só a pasta está disponível

Também é possível selecionar um ZIP dessa pasta no botão **Importar ZIP**.
Quando faltam o banco e o snapshot de estado, o COAE pede confirmação para
recuperar apenas o roteiro como rascunho e copiar todos os materiais. Cancelar
não cadastra projeto; aceitar cria uma cópia independente. Se o ZIP não contém
roteiro exportado, ele é recusado com uma mensagem específica.

Se a pasta está em `projects/COAE-...`, mas não aparece no aplicativo, abra
**Recuperar pasta já presente neste computador** na tela inicial. Selecione a pasta
e clique em **Recuperar roteiro da pasta**.

Essa opção cadastra o projeto e recupera os textos `exports/script_v*/narration_darkplanner.txt`
como rascunhos. Os arquivos existentes permanecem no lugar e aparecem em **Montagem e arquivos**.
Ela não reconstrói aprovações, cenas ou vínculos temporais sem o banco original.
Para continuar a produção, revise o roteiro e reimporte o áudio; para retomar o histórico
completo, traga o ZIP exportado no computador de origem.

Uploads e extração usam `workspace/uploads` e `workspace/imports` no disco do projeto.

## Excluir e restaurar

Em **Meus projetos**, clique em **Excluir projeto** no cartão e confirme.
O projeto sai da lista principal e aparece em **Lixeira de projetos**, com o
botão **Restaurar**. A exclusão é lógica: banco, arquivos, histórico e aprovações
continuam preservados, sem liberar espaço no disco. Projetos com tarefa em
execução não podem ser excluídos. Não há remoção física definitiva nesta opção.
