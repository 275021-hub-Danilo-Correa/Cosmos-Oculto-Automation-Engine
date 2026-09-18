# Capacidades efetivas · v0.2

| Provider | Uso | Situação |
| --- | --- | --- |
| Dark Planner / ElevenLabs | Voz feita externamente pelo usuário | Assistido; sem API TTS no COAE |
| faster-whisper | Reconhecimento local pt-BR por palavra | Implementado; depende de instalação/download; sem teste com voz real nesta entrega |
| JSON alinhado | Importação de transcrição externa | Implementado/testado; não é reconhecimento do áudio |
| Google Gemini texto | Roteiro, auditoria, agrupamento e descrições | Alternativo; exige chave/modelos/cota; modelo antigo pode retornar 404 |
| Google Gemini imagem | Geração 16:9 via `generate_content` | Alternativo; cota de imagem da conta testada retornou 429 |
| Gemini multimodal | Auditoria de imagens | Implementado; não certifica precisão científica |
| Flow / Veo / Runway | Animação | Não implementado |
| CapCut | Montagem manual | Guias JSON/CSV/SRT/VTT; sem projeto nativo ou automação de interface |
| YouTube | Publicação/SEO/métricas | Não implementado |

A configuração não garante disponibilidade ou gratuidade de modelos. Limites controlam chamadas, não valores monetários. Chamadas com falha desconhecida são contabilizadas e não repetidas automaticamente.

## Perfil local (2026-09-18)

- Ollama: texto JSON para roteiro, auditoria e storyboard; visão opcional com modelo
  capaz explicitamente configurado. Modelos locais, sem download automático.
- ComfyUI local: workflow API com nós nativos SD/SDXL, imagem única 16:9, ticket
  persistido e retomada por prompt_id. Nós pagos/customizados não aceitos neste perfil.
- Auditoria padrão das imagens locais: arquivo/proporção + revisão humana obrigatória.
- Adaptadores testados por fixtures HTTP. GPU AMD/Windows e qualidade ainda não validadas.
- Ver `docs/LOCAL_AI.md` para configuração, limitações e continuação no PC do usuário.
- Neste Codespace nenhum serviço Ollama/ComfyUI está instalado ou executando.
- A validação local atual cobre protocolo, autenticação, persistência e retomada;
  não comprova velocidade, qualidade visual ou aceleração na RX 7800 XT.
