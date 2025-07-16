import os
import whisper
from .config import settings
from .audio import combine_wavs
from .tts_edge import synthesize_sentences


def synthesize_with_whisper(
    sentences: list[str],
    out_dir: str,
    voice: str
) -> tuple[list[tuple[str, int]], list[dict]]:
    """
    Generate per-sentence wavs via edge_tts (reuse your tts_edge module)
    combine_wavs into settings.audio_wav
    run whisper tiny.en with word_timestamps
    return (wav_infos, all_words) where all_words is same format as ElevenLabs
    """
    os.makedirs(out_dir, exist_ok=True)

    # 1) Make the chunks using Edge TTS with the chosen voice
    wav_infos = synthesize_sentences(sentences, out_dir, voice)

    # 2) Merge into single WAV
    combine_wavs(wav_infos, settings.audio_mp3, settings.audio_wav)

    # 3) Transcribe + align
    model = whisper.load_model("tiny.en")
    result = model.transcribe(
        settings.audio_wav,
        word_timestamps=True,
        verbose=False
    )

    # 4) Flatten to [{word, start (ms), end (ms), sid}, …]
    all_words = []
    for seg in result["segments"]:
        sid = seg["id"]
        for w in seg["words"]:
            all_words.append({
                "word": w["word"].strip(),
                "start": int(w["start"] * 1000),
                "end":   int(w["end"]   * 1000),
                "sid":   sid
            })

    # return both audio file info and word timestamps
    return wav_infos, all_words
