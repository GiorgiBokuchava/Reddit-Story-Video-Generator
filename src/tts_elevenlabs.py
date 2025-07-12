import os
import base64
from elevenlabs import ElevenLabs, VoiceSettings
from pydub import AudioSegment
from .config import settings

def synthesize_with_elevenlabs(sentences: list[str], out_dir: str = "audio_chunks") -> tuple[list[tuple[str,int]], list[dict]]:
    """
    Generates speech via ElevenLabs (with timestamps), saves MP3/WAV,
    and returns both a list of (wav_path, duration_ms) tuples and word-level timing data.
    """
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    os.makedirs(out_dir, exist_ok=True)

    wav_infos = []
    all_words = []
    offset = 0

    for sid, sent in enumerate(sentences):
        # Build SSML-wrapped text if SSML usage is enabled
        if settings.elevenlabs_use_ssml:
            # Wrap each sentence with prosody rate and automatic pause
            text_payload = (
                f"<speak>"
                f"<prosody rate=\"{settings.elevenlabs_prosody_rate}\">{sent}</prosody>"
                f"<break time=\"100ms\"/>"
                f"</speak>"
            )
        else:
            text_payload = sent

        # Prepare voice settings
        vs = VoiceSettings(
            stability=settings.elevenlabs_stability,
            similarity_boost=settings.elevenlabs_similarity_boost
        )

        # Generate audio with timestamps (SSML auto-detected)
        resp = client.text_to_speech.convert_with_timestamps(
            voice_id=settings.elevenlabs_voice_id,
            text=text_payload,
            voice_settings=vs
        )

        # Decode base64-encoded MP3
        audio_bytes = base64.b64decode(resp.audio_base_64)
        mp3_path = os.path.join(out_dir, f"{sid:03d}.mp3")
        with open(mp3_path, "wb") as f:
            f.write(audio_bytes)

        # Convert MP3 to WAV and measure duration
        wav_path = os.path.join(out_dir, f"{sid:03d}.wav")
        AudioSegment.from_file(mp3_path).export(wav_path, format="wav")
        dur = len(AudioSegment.from_file(wav_path))

        # Character-level alignment
        na = resp.normalized_alignment
        chars = na.characters
        starts = na.character_start_times_seconds
        ends = na.character_end_times_seconds

        # Group characters into word timestamps
        word_chars = []
        word_start = None
        for ch, st, et in zip(chars, starts, ends):
            if ch.isspace():
                if word_chars:
                    word = "".join(word_chars)
                    start_ms = word_start * 1000
                    end_ms = prev_end * 1000
                    all_words.append({
                        "word": word,
                        "start": start_ms + offset,
                        "end": end_ms + offset,
                        "sid": sid
                    })
                    word_chars = []
                    word_start = None
                continue
            if word_start is None:
                word_start = st
            word_chars.append(ch)
            prev_end = et

        # Append final word of the sentence
        if word_chars:
            word = "".join(word_chars)
            start_ms = word_start * 1000
            end_ms = prev_end * 1000
            all_words.append({
                "word": word,
                "start": start_ms + offset,
                "end": end_ms + offset,
                "sid": sid
            })

        wav_infos.append((wav_path, dur))
        offset += dur

    return wav_infos, all_words
