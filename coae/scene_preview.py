"""Static scene previews: CPU FFmpeg, original audio, absolute frame boundaries."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

FPS = 30
SAMPLE_RATE = 48000


def frame_interval(start, end, audio_duration):
    try:
        start, end, duration = (Decimal(str(v)) for v in (start, end, audio_duration))
        if not all(v.is_finite() for v in (start, end, duration)) or not 0 <= start < end <= duration:
            raise ValueError()
        first, last = (int((v * FPS).to_integral_value(rounding=ROUND_HALF_UP)) for v in (start, end))
        if last <= first:
            raise ValueError()
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Limites da cena inválidos, fora do áudio ou menores que um quadro.') from None
    # Round absolute boundaries, never each duration: shared cuts stay identical.
    return first, last


def probe(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                             '-of', 'json', str(path)], capture_output=True, timeout=60, check=True)
    return json.loads(result.stdout)


def render(image, original_audio, destination, start, end, audio_duration):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise ValueError('Instale FFmpeg e FFprobe no PATH para gerar a prévia.')
    first, last = frame_interval(start, end, audio_duration)
    count = last - first
    samples_per_frame = SAMPLE_RATE // FPS
    start_sample, end_sample = first * samples_per_frame, last * samples_per_frame
    duration = count / FPS
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.stem + '.' + uuid.uuid4().hex + '.tmp.mp4')
    # Resampling changes the sample grid, not speech speed. Pad only the possible
    # final fractional frame; atrim/asetpts never stretch or accelerate narration.
    audio_filter = (f'aresample={SAMPLE_RATE},atrim=start_sample={start_sample}:end_sample={end_sample},'
                    f'asetpts=PTS-STARTPTS,apad=whole_len={count * samples_per_frame}')
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
               '-loop', '1', '-framerate', str(FPS), '-i', str(image), '-i', str(original_audio),
               '-map', '0:v:0', '-map', '1:a:0', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2,setsar=1',
               '-af', audio_filter, '-t', f'{duration:.9f}',
               '-c:v', 'libx264', '-preset', 'fast', '-tune', 'stillimage', '-crf', '20',
               '-threads', '2', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
               '-ar', str(SAMPLE_RATE), '-movflags', '+faststart', str(temporary)]
    began = time.monotonic()
    try:
        subprocess.run(command, capture_output=True, timeout=1800, check=True)
        info = probe(temporary)
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in info['streams'] if s['codec_type'] == 'audio')
        if (video['codec_name'] != 'h264' or audio['codec_name'] != 'aac'
                or int(video['nb_frames']) != count or video['avg_frame_rate'] != f'{FPS}/1'
                or abs(float(video['duration']) - duration) > .001
                or abs(float(audio['duration']) - duration) > .025):
            raise ValueError('FFmpeg produziu uma prévia com duração ou formato inesperado.')
        if destination.exists():
            raise ValueError('A prévia de destino já existe; nenhum arquivo foi sobrescrito.')
        temporary.rename(destination)
    except (subprocess.SubprocessError, OSError, KeyError, StopIteration) as exc:
        raise ValueError('Falha técnica ao gerar/verificar a prévia com FFmpeg. Originais preservados.') from exc
    finally:
        temporary.unlink(missing_ok=True)
    return {'fps': FPS, 'start_frame': first, 'end_frame_exclusive': last,
            'frame_count': count, 'duration': duration, 'requested_start': start, 'requested_end': end,
            'rendered_start': first / FPS, 'rendered_end': last / FPS,
            'audio_start_sample': start_sample, 'audio_end_sample_exclusive': end_sample,
            'sample_rate': SAMPLE_RATE, 'elapsed_seconds': round(time.monotonic() - began, 3),
            'video_codec': video['codec_name'], 'audio_codec': audio['codec_name'],
            'mode': 'static_image', 'audio_speed': 1,
            'timing_note': 'Limites absolutos arredondados a 30 fps (até 16,67 ms por limite). '
                           'Sem soma de durações arredondadas; na montagem final use o áudio original contínuo.'}
