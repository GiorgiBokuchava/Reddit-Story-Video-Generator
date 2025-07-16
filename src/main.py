# src/main.py
import os
from pathlib import Path
import subprocess
from dotenv import load_dotenv

from .reddit_client import init_reddit
from .post_finder import find_next_post
from .text_processing import translate_phrases, clean_markdown, split_sentences
from .audio import combine_wavs, cleanup as audio_cleanup
from .ass_builder import write_karaoke_ass
from .thumbnail_card_generator import generate_svg
from .svg_raster import svg_to_card_png
from .video_creation import burn_and_mux
from .tts_elevenlabs import synthesize_with_elevenlabs
from .tts_edge import synthesize_sentences as synthesize_with_edge
from .tts_whisper import synthesize_with_whisper
from .ai_utils import detect_mood, select_sound_for_mood
from .youtube_uploader import upload_to_youtube
from .config import settings
from googleapiclient.errors import HttpError

load_dotenv()

def main():
    # 1) Fetch next Reddit post
    reddit     = init_reddit()
    submission = find_next_post(reddit)
    post_id    = submission.id
    print(f"[+] r/{submission.subreddit.display_name} • {post_id}")
    print(f"    Title: {submission.title!r}")
    print(f"    URL:   https://reddit.com{submission.permalink}\n")

    # 2) TTS → audio + (optional) word timings
    raw_post  = submission.title + "\n\n" + submission.selftext
    text      = clean_markdown(translate_phrases(raw_post))
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

    combine_wavs(wav_infos, settings.audio_mp3, settings.audio_wav)
    write_karaoke_ass(all_words)

    # 3) Build the thumbnail card
    tpl_svg = settings.thumbnail_template_svg
    pop_svg = settings.thumbnail_populated_svg
    generate_svg(
        template_svg    = tpl_svg,
        output_svg      = pop_svg,
        subreddit       = submission.subreddit.display_name,
        title           = submission.title,
        verified        = False,
        font_path       = settings.thumbnail_font_path,
        sub_font_size   = settings.thumbnail_sub_font_size,
        title_font_size = settings.thumbnail_title_font_size,
        padding_px      = settings.thumbnail_padding,
    )
    print(f"[+] Populated SVG → {pop_svg}")

    card_png = settings.thumbnail_output_png
    svg_to_card_png(
        svg_path      = pop_svg,
        out_png       = card_png,
        crop_x        = 13,
        crop_y        = 0,
        crop_w        = 1444,
        crop_h        = 820,
        target_w      = 1080,
        corner_radius = 50
    )
    print(f"[+] Card PNG → {card_png}")

    # 4) Determine card overlay duration
    _, first_ms = wav_infos[0]
    first_dur   = first_ms / 1000.0

    # 5) Mood → background music
    mood     = detect_mood(raw_post)
    bg_music = select_sound_for_mood(mood)
    if bg_music:
        print(f"[*] Mood-detected '{mood}', using music: {bg_music}")
    else:
        print(f"[*] Mood-detected '{mood}', but no tracks found; proceeding without music.")

    # 6) Burn/subs/card + music
    drive_id, final_video = burn_and_mux(
        card_png   = card_png,
        ass_path   = settings.output_ass,
        first_dur  = first_dur,
        bg_music   = bg_music
    )
    print(f"[+] Final video → {final_video}")

    # 7) Drive upload
    if settings.upload_to_drive and drive_id:
        print(f"[+] Drive URL: https://drive.google.com/file/d/{drive_id}/view")
    else:
        print("[*] Skipped Drive upload")

    # 8) YouTube thumbnail
    thumb_frame = "output/youtube_thumbnail.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", "00:00:01",
        "-i", final_video,
        "-frames:v", "1",
        "-vf", "transpose=1,scale=1280:-1,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        thumb_frame
    ], check=True)
    print(f"[+] Thumbnail → {thumb_frame}")

    # 9) YouTube upload
    if settings.upload_to_youtube:
        try:
            yt_id = upload_to_youtube(
                final_video,
                title=submission.title,
                description=raw_post + "\n\n" + " ".join(settings.youtube_video_tags),
                # thumbnail_path=thumb_frame
            )
            print(f"[+] YouTube URL: https://youtu.be/{yt_id}")
        except HttpError as e:
            print(f"[!] Upload succeeded but thumbnail set failed: {e}")
    else:
        print("[*] Skipped YouTube upload")

    # 10) Cleanup: keep only final_video in output/, then delete it too if we uploaded
    out_dir    = Path("output")
    final_name = Path(final_video).name

    # remove everything except the final video
    for f in out_dir.iterdir():
        if f.is_file() and f.name != final_name:
            try:
                f.unlink()
            except OSError:
                pass
    
    audio_cleanup("audio_chunks", settings.audio_mp3, settings.audio_wav)

    # if we uploaded to Drive or YouTube, also delete the final video
    if settings.upload_to_drive or settings.upload_to_youtube:
        try:
            (out_dir / final_name).unlink()
        except OSError:
            pass

    print("\n[+] Done.\n")


if __name__ == "__main__":
    main()
