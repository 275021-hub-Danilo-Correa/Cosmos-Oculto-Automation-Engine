# Capacidades efetivas · v0.2

| Provider | Uso | Situação |
| --- | --- | --- |
| Dark Planner / ElevenLabs | Voz feita externamente pelo usuário | Assistido; sem API TTS no COAE |
| faster-whisper | Reconhecimento local pt-BR por palavra | Implementado; depende de instalação/download; sem teste com voz real nesta entrega |
| JSON alinhado | Importação de transcrição externa | Implementado/testado; não é reconhecimento do áudio |
| Google Gemini texto | Roteiro, auditoria, agrupamento e descrições | Adapter implementado; exige chave/modelos/limite; sem chamadas reais nesta entrega |
| Google Gemini imagem | Geração 16:9 via generate_content | Implementado; requer modelo compatível; sem teste na conta do usuário |
| Gemini multimodal | Auditoria de imagens | Implementado; não certifica precisão científica |
| Flow / Veo / Runway | Animação | Não implementado |
| CapCut | Montagem manual | Guias JSON/CSV/SRT/VTT; sem projeto nativo ou automação de interface |
| YouTube | Publicação/SEO/métricas | Não implementado |

A configuração não garante disponibilidade ou gratuidade de modelos. Limites controlam chamadas, não valores monetários. Chamadas com falha desconhecida são contabilizadas e não repetidas automaticamente.
