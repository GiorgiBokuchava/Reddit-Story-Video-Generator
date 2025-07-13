import os
<<<<<<< HEAD
from pathlib import Path
from dotenv import load_dotenv

from .reddit_client import init_reddit
from .post_finder import find_next_post
from .text_processing import translate_phrases, clean_markdown, split_sentences
from .audio import combine_wavs, cleanup as audio_cleanup
from .ass_builder import write_karaoke_ass
from .thumbnail_generator import generate_svg
from .svg_raster import svg_to_card_png
from .video_mux import burn_and_mux
from .tts_elevenlabs import synthesize_with_elevenlabs
from .tts_edge import synthesize_sentences as synthesize_with_edge
from .tts_whisper import synthesize_with_whisper
from .youtube_uploader import upload_to_youtube
from .config import settings
from googleapiclient.errors import HttpError

load_dotenv()

def main():
    # 1) Pick next post
    reddit = init_reddit()
    submission = find_next_post(reddit)
    print(f"[+] r/{submission.subreddit.display_name} • {submission.id}")
    print(f"    Title: {submission.title!r}")
    print(f"    URL:   https://reddit.com{submission.permalink}\n")

    # 2) TTS -> audio + (optional) word timings
    raw = submission.title + "\n\n" + submission.selftext
    text = clean_markdown(translate_phrases(raw))
    sentences = split_sentences(text)

    provider = settings.tts_provider.lower()
    if provider == "elevenlabs":
        wav_infos, all_words = synthesize_with_elevenlabs(sentences, out_dir="audio_chunks")
    elif provider == "edge":
        wav_infos = synthesize_with_edge(sentences, out_dir="audio_chunks")
        all_words  = []
    elif provider == "whisper":
        wav_infos, all_words = synthesize_with_whisper(sentences, out_dir="audio_chunks")
    else:
        raise ValueError(f"Unknown TTS_PROVIDER: {settings.tts_provider}")

    # 3) Combine audio and write ASS subtitles
    combine_wavs(wav_infos, settings.audio_mp3, settings.audio_wav)
    write_karaoke_ass(all_words)

    # 4) Generate & populate the SVG template
    tpl_svg = settings.thumbnail_template_svg
    pop_svg = settings.thumbnail_populated_svg
    generate_svg(
        template_svg = tpl_svg,
        output_svg = pop_svg,
        subreddit = submission.subreddit.display_name,
        title = submission.title,
        verified = False,
        font_path = settings.thumbnail_font_path,
        sub_font_size = settings.thumbnail_sub_font_size,
        title_font_size = settings.thumbnail_title_font_size,
        padding_px = settings.thumbnail_padding,
    )
    print(f"[+] Populated SVG written -> {pop_svg}")

    # 5) Rasterize & crop/round to PNG
    card_png = settings.thumbnail_output_png
    svg_to_card_png(
        svg_path = pop_svg,
        out_png = card_png,
        crop_x = 13,
        crop_y = 0,
        crop_w = 1444,
        crop_h = 820,
        target_w = 1080,
        corner_radius = 50
    )
    print(f"[+] Generated card PNG -> {card_png}")

    # 6) First-sentence duration
    _, first_ms = wav_infos[0]
    first_dur   = first_ms / 1000.0

    # 7) Burn & mux: overlay card then subtitles
    drive_id, final_video = burn_and_mux(
        card_png = card_png,
        ass_path = settings.output_ass,
        first_dur = first_dur
    )
    if settings.upload_to_drive and drive_id:
        print(f"[+] Drive URL: https://drive.google.com/file/d/{drive_id}/view")
    else:
        print("[*] Skipped Drive upload")
    print(f"[+] Final video -> {final_video}")

    # 8) Upload to YouTube
    if settings.upload_to_youtube:
        try:
            yt_id = upload_to_youtube(
                final_video,
                title=submission.title,
                description=(
                    "Enjoy this reading of a top Reddit story—\n"
                    "narrated with voice and subtitles. Subscribe for more daily tales!\n\n"
                    + " ".join(settings.youtube_video_tags)
                ),
                thumbnail_path=card_png
            )
            print(f"[+] YouTube URL: https://youtu.be/{yt_id}")
        except HttpError as e:
            print(f"[!] Warning: upload succeeded but thumbnail set failed: {e}")
    else:
        print("[*] Skipped YouTube upload")

    # 9) Cleanup audio intermediates + generated SVG/PNG/MP4
    audio_cleanup("audio_chunks", settings.audio_mp3, settings.audio_wav)

    # remove the temporary title‐card SVG, PNG, and final video
    for path in (
        settings.thumbnail_populated_svg,
        settings.thumbnail_output_png,
        final_video,
    ):
        try:
            os.remove(path)
            print(f"[+] Removed {path}")
        except OSError:
            pass

    print("\n[+] Done.\n")


if __name__ == "__main__":
    main()
=======
import re
from vosk import Model, SetLogLevel

from src.post_finder import find_next_post
from .reddit_client import init_reddit
from .text_processing import translate_phrases, clean_markdown, split_sentences
from .tts import synthesize_sentences
from .audio import combine_wavs, cleanup
from .transcription import ensure_model, transcribe_free
from .ass_builder import write_karaoke_ass
from .video_mux import burn_and_mux
from src.youtube_uploader import upload_to_youtube
from .config import settings

def main():
    # Silence all Vosk INFO logs
    SetLogLevel(-1)

    # Init and auto-pick next post
    reddit = init_reddit()
    submission = find_next_post(reddit)

    # Log which post was selected
    print(f"[+] Selected r/{submission.subreddit.display_name} • {submission.id}")
    print(f"    Title: {submission.title!r}")
    print(f"    URL:   https://reddit.com{submission.permalink}\n")

    # Prepare text
    raw = submission.title + "\n\n" + submission.selftext
    text = clean_markdown(translate_phrases(raw))

    # TTS
    sents = split_sentences(text)
    wav_infos = synthesize_sentences(sents, out_dir="audio_chunks")

    # Combine audio
    combine_wavs(wav_infos, settings.audio_mp3, settings.audio_wav)

    # Align words
    ensure_model()
    model = Model(settings.model_dir)
    all_words, offset = [], 0
    for sid, (wav, dur) in enumerate(wav_infos):
        ts = transcribe_free(wav, model)
        tokens = re.findall(r"\w+(?:['’]\w+)?[.,!?;:()\"']*", sents[sid])
        for wi, info in enumerate(ts):
            w = tokens[wi] if wi < len(tokens) else info["word"]
            all_words.append({
                "word":  w,
                "start": info["start"]*1000 + offset,
                "end":   info["end"]*1000 + offset,
                "sid":   sid
            })
        offset += dur

    # Subtitles
    write_karaoke_ass(all_words)

    # Video → Drive & keep local file
    drive_id, local_video = burn_and_mux()
    if settings.upload_to_drive:
        print(f"[+] Drive URL: https://drive.google.com/file/d/{drive_id}/view")
    else:
        print("[*] Skipped Drive upload (UPLOAD_DRIVE=false)")

    # Optionally upload to YouTube
    if settings.upload_to_youtube:
        yt_id = upload_to_youtube(
            local_video,
            title=submission.title,
            description=(
                "Enjoy this reading of a top Reddit TIFU story—"
                "narrated with voice and subtitles. Subscribe for more daily tales!"
            )
        )
        print(f"[+] YouTube URL: https://youtu.be/{yt_id}")
    else:
        print("[*] Skipped YouTube upload (UPLOAD_YT=false)")

    # Cleanup audio files
    cleanup("audio_chunks", settings.audio_mp3, settings.audio_wav)

    # Remove the local video file
    try:
        os.remove(local_video)
        print(f"[+] Removed temp file {local_video}")
    except OSError:
        pass

    # Final report
    print("\n[+] Done! All uploads complete (or were skipped).\n")

if __name__ == "__main__":
    main()

    # TODO try replacing TTS and captions with elevenlabs, cos captions suck without timestamps
    # TODO if not that, then use GTT or something else, to transcribe outputted mp3 (cos I think google's transcribtion works better)
>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790
