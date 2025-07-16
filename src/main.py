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
from .tts_whisper import synthesize_with_whisper
from .tts_edge import synthesize_sentences as synthesize_with_edge
from .ai_utils import detect_mood, detect_gender, select_sound_for_mood
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

    # 2) Prepare text and split into sentences
    raw_post  = submission.title + "\n\n" + submission.selftext
    text      = clean_markdown(translate_phrases(raw_post))
    sentences = split_sentences(text)

    # 3) Detect author gender and choose Edge voice
    author_gender = detect_gender(raw_post)
    if author_gender == 'male':
        edge_voice = settings.edge_tts_voice_male
    elif author_gender == 'female':
        edge_voice = settings.edge_tts_voice_female
    else:
        edge_voice = settings.edge_tts_voice_female  # fallback
    print(f"[*] Detected gender: {author_gender}, using Edge voice: {edge_voice}")

    # 4) Synthesize per-sentence audio and collect word timings if available
    provider = settings.tts_provider.lower()
    if provider == "elevenlabs":
        wav_infos, all_words = synthesize_with_elevenlabs(sentences, out_dir="audio_chunks")
    elif provider == "whisper":
        # pass voice to whisper synth function
        wav_infos, all_words = synthesize_with_whisper(
            sentences,
            out_dir="audio_chunks",
            voice=edge_voice
        )
    else:
        # Edge TTS: returns list of (wav_path, duration_ms), no timings
        wav_infos = synthesize_with_edge(sentences, out_dir="audio_chunks", voice=edge_voice)
        all_words  = []

    # 5) Combine all chunks into final MP3 and WAV, then write .ass subtitles
    combine_wavs(wav_infos, settings.audio_mp3, settings.audio_wav)
    write_karaoke_ass(all_words)

    # 6) Generate and rasterize the thumbnail card
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

    # 7) Compute first-sentence duration for overlay timing
    _, first_ms = wav_infos[0]
    first_dur   = first_ms / 1000.0

    # 8) Mood detection → pick background music track
    mood     = detect_mood(raw_post)
    bg_music = select_sound_for_mood(mood)
    if bg_music:
        print(f"[*] Mood-detected '{mood}', using music: {bg_music}")
    else:
        print(f"[*] Mood-detected '{mood}', but no tracks found; proceeding without music.")

    # 9) Burn subtitles, overlay card, mix in music, and output video
    drive_id, final_video = burn_and_mux(
        card_png   = card_png,
        ass_path   = settings.output_ass,
        first_dur  = first_dur,
        bg_music   = bg_music
    )
    print(f"[+] Final video → {final_video}")

    # 10) Optionally upload to Google Drive
    if settings.upload_to_drive and drive_id:
        print(f"[+] Drive URL: https://drive.google.com/file/d/{drive_id}/view")
    else:
        print("[*] Skipped Drive upload")

    # 11) Extract a YouTube thumbnail frame
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

    # 12) Optionally upload to YouTube
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

    # 13) Cleanup: retain only the final video in output/, then delete it too if uploaded
    out_dir    = Path("output")
    final_name = Path(final_video).name

    for f in out_dir.iterdir():
        if f.is_file() and f.name != final_name:
            try:
                f.unlink()
            except OSError:
                pass

    if settings.upload_to_drive or settings.upload_to_youtube:
        try:
            (out_dir / final_name).unlink()
        except OSError:
            pass

    # 14) Cleanup audio chunks always
    audio_cleanup("audio_chunks", settings.audio_mp3, settings.audio_wav)

    print("\n[+] Done.\n")


if __name__ == "__main__":
    main()
