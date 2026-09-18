# COAE desktop e web

## Instalação Windows

1. Atualize o repositório e feche servidores COAE antigos.
2. Instale Python >=3.12. Python 3.12 é o ponto inicial para testar dependências
   nativas; a instalação completa em Windows ainda precisa ser validada.
3. Execute `INSTALAR_DESKTOP_WINDOWS.bat`. Ele reutiliza o instalador existente e
   acrescenta `requirements-desktop.txt` ao `.venv`.
4. Confira o [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/).
   O desktop Windows solicita explicitamente o renderer Edge Chromium.
5. Abra `INICIAR_DESKTOP_WINDOWS.bat`. O token é enviado automaticamente à tela.
   Use `INICIAR_WINDOWS.bat` quando preferir iniciar apenas a versão web.

O terminal permanece aberto para mensagens de erro. Não feche o terminal antes da
janela. A confirmação de saída é genérica: não salva texto ainda não enviado pelos
botões do estúdio. Espere gerações/uploads concluírem antes de sair.

## Dados e serviços

Ambos os modos usam por padrão a raiz deste repositório, preservando os projetos
existentes. Não copie `.venv` entre PCs. Preserve `.env`, `data/` e `projects/`.
`--workspace CAMINHO` muda a pasta dos dados; o `.env` continua sendo lido da raiz
do código, como no modo web. Use o mesmo caminho ao alternar entre modos.

A porta padrão é 8765, restrita a loopback no desktop. O link mostrado no terminal
permite usar o navegador enquanto o desktop está aberto. Não inicie dois servidores
para o mesmo workspace, mesmo em portas diferentes. `.coae.lock` pode permanecer no
disco após a saída: a trava é do sistema operacional, não da existência do arquivo.
Nunca apague a trava enquanto o aplicativo estiver aberto.

Fechar a janela encerra o servidor depois das requisições aceitas. Ollama e ComfyUI
são serviços externos e continuam sob controle do usuário. Esta entrega não gera
voz, instala modelos nem muda os providers configurados.

## Outros ambientes

O modo web permanece sem dependência de pywebview. Em computador com ambiente
gráfico, instale `requirements-desktop.txt` e siga as dependências de sistema da
[documentação pywebview](https://pywebview.flowrl.com/guide/installation).
Depois execute `python iniciar_desktop.py`. Linux pode precisar de GTK/Qt; macOS
usa suas bibliotecas nativas. Codespaces sem tela deve usar o modo web.

A API segue o modelo de janela e loop principal documentado no
[pywebview](https://pywebview.flowrl.com/api/), com servidor COAE em outra thread.
Downloads são habilitados para as exportações já existentes. Não há ponte Python
exposta ao JavaScript nem um segundo backend.

## Validação no PC

- Abrir a janela, criar projeto, salvar roteiro e reabrir no modo web: mesmos dados.
- Importar áudio pelo seletor nativo e testar o player.
- Exportar TXT e ZIP, verificando a caixa de download e os arquivos salvos.
- Fechar/reabrir: token fixo continua funcionando e a porta é liberada.
- Tentar outra instância no mesmo workspace: deve recusar sem alterar tarefas.

Os testes automatizados exercitam HTTP/SQLite reais com uma janela simulada,
persistência, falhas de abertura, porta ocupada, trava e limpeza. Não substituem
inspeção visual, downloads/player no WebView2 nem execução dos BATs no Windows.
Não foi produzido um executável Windows independente neste ambiente Linux.
