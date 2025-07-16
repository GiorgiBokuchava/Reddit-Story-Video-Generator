import os
import asyncio
import edge_tts
from pydub import AudioSegment, silence
from .config import settings

# Read desired speaking rate from env (e.g. "+50%", "-20%", "1.2")
EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "+0%")

async def _synthesize_raw(text: str, mp3_path: str) -> None:
    """
    Synthesize `text` to `mp3_path` using edge-tts at the configured rate.
    """
    communicator = edge_tts.Communicate(
        text=text,
        voice=settings.edge_tts_voice,
        rate=EDGE_TTS_RATE
    )
    await communicator.save(mp3_path)

def _trim_and_pad(
    audio: AudioSegment,
    silence_thresh: int = -50,
    min_silence_len: int = 50,
    pad_ms: int = 50
) -> AudioSegment:
    """
    Remove leading/trailing silence, then add pad_ms of silence at both ends.
    """
    nonsilent_ranges = silence.detect_nonsilent(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )
    if nonsilent_ranges:
        start = nonsilent_ranges[0][0]
        end   = nonsilent_ranges[-1][1]
        core = audio[start:end]
    else:
        core = audio

    pad = AudioSegment.silent(duration=pad_ms, frame_rate=audio.frame_rate)
    return pad + core + pad

def synthesize_sentences(sentences: list[str], out_dir: str) -> list[tuple[str,int]]:
    """
    Generate per-sentence WAVs:
     1. Synthesize to MP3 with edge-tts at EDGE_TTS_RATE
     2. Convert to WAV, trim/pad
    Returns list of (wav_path, duration_ms).
    """
    os.makedirs(out_dir, exist_ok=True)
    results: list[tuple[str,int]] = []

    for i, sent in enumerate(sentences):
        mp3_path = os.path.join(out_dir, f"{i:03d}.mp3")
        # 1) raw TTS with rate control
        asyncio.run(_synthesize_raw(sent, mp3_path))

        # 2) load, trim silence, pad ends
        audio = AudioSegment.from_file(mp3_path)
        trimmed = _trim_and_pad(
            audio,
            silence_thresh=int(audio.dBFS) - 16,
            min_silence_len=40,
            pad_ms=50
        )

        wav_path = os.path.join(out_dir, f"{i:03d}.wav")
        trimmed.export(wav_path, format="wav")

        # 3) record duration
        results.append((wav_path, len(trimmed)))

    return results
