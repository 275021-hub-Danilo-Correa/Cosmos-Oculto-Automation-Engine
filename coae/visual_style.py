"""Mandatory documentary realism, shared by initial and revised generations."""

REALISTIC_STYLE = ('Photorealistic scientific documentary imagery, realistic photographic appearance, '
                   'natural lighting, physically plausible materials, lifelike textures and proportions. ')
NON_REALISTIC_NEGATIVE = ('drawing, cartoon, anime, manga, illustration, sketch, painting, watercolor, '
                         'comic book, cel shading, animated movie style, stylized 3D, plastic CGI, '
                         'toy-like, game art, fantasy art')
REALISM_INSTRUCTION = ('Regra obrigatória: aparência fotográfica realista. Nunca desenho, cartoon, anime, '
                      'pintura, ilustração ou estética de animação/3D estilizado. Fenômenos não fotografáveis '
                      'podem ser visualizações científicas fotorrealistas, sem apresentá-las como fotografias reais. ')
CHANNEL_GENERATION_RULES = ('cinematic dark scientific documentary, one dominant subject, coherent wide composition, '
                            'deep black and navy palette, restrained blue and amber accents, low-key natural lighting, '
                            'clear scale and depth, uncluttered negative space, no visible text or interface')
CHANNEL_NEGATIVE = ('typography, letters, captions, subtitles, labels, diagram, infographic, chart, graph, '
                    'user interface, split screen, collage, excessive neon, clutter')
CHANNEL_AUDIT_INSTRUCTION = ('Aplique o guia do canal: assunto dominante ligado à fala, composição legível, escala e profundidade, '
                             'baixa luminosidade com detalhes visíveis, preto/azul com acentos contidos, sem texto, interface, '
                             'infográfico, neon excessivo ou objetos não pedidos. Considere visual_function: ESTABLISH estabelece '
                             'atmosfera e assunto e não precisa demonstrar todos os conceitos da fala; EXPLAIN exige relação mais '
                             'direta. Visualização científica deve ser distinguida de fotografia. ')


def realistic_prompt(description):
    return description if description.startswith(REALISTIC_STYLE) else REALISTIC_STYLE + description
