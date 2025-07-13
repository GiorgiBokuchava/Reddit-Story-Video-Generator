import asyncio
import edge_tts
from pydub import AudioSegment
from .config import settings

async def _synthesize(text: str, mp3_path: str) -> int:
    await edge_tts.Communicate(text, settings.edge_tts_voice, rate=settings.edge_tts_rate)\
                  .save(mp3_path)
    return len(AudioSegment.from_file(mp3_path))

def synthesize_sentences(sentences: list[str], out_dir: str) -> list[tuple[str,int]]:
    # Return list of (wav_path, duration_ms)
    import os
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for i, sent in enumerate(sentences):
        mp3 = f"{out_dir}/{i:03d}.mp3"
        dur = asyncio.run(_synthesize(sent, mp3))
        wav = f"{out_dir}/{i:03d}.wav"
        AudioSegment.from_file(mp3).export(wav, format="wav")
        results.append((wav, dur))
    return results
