# Correção Gemini integrada

Após atualizar o código, reinicie o servidor para carregar os módulos novos:

```bash
.venv/bin/python iniciar.py --host 0.0.0.0 --port 8765 --no-browser
```

Sem Gemini configurado, deixe a opção Gemini desmarcada em **Áudio** para usar a análise local. Se a opção Gemini for marcada, o COAE valida antes da análise:

- `GEMINI_API_KEY`;
- `COAE_WRITER_MODEL`;
- `COAE_AUDITOR_MODEL`;
- `COAE_MAX_CALLS_PER_PROJECT` com saldo disponível;
- SDK local instalado.

Falhas nessa validação não criam job, não alteram o storyboard e não consomem upload de transcrição. Nenhuma chamada paga é feita durante o preflight.

Para completar descrições de um storyboard já existente, use **Storyboard → Completar descrições com Gemini**, depois salve, audite e revise antes de gerar imagens.

Validação atual: 43 testes passam sem skips.