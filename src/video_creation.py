import os
import subprocess
import tempfile
from .asset_manager import choose_and_stream_video
from .drive_utils import upload_to_drive
from .config import settings

def burn_and_mux(
    card_png: str,
    ass_path: str,
    first_dur: float,
    bg_video: str | None = None,
    bg_music: str | None = None
):
    """
    Stream background clip (or use bg_video if provided), loop it if needed,
    scale/pad to 1080x1920, burn subtitles, overlay card,
    optionally mix in background music, and either upload to Drive or save locally under output/.
    """
    # Determine background source and looping
    if bg_video:
        bg_path = bg_video
        loop_args = ["-stream_loop", "-1"]
        print(f"[+] Using background asset (looped): {bg_path}")
    else:
        tmp_bg = choose_and_stream_video()
        bg_path = tmp_bg.name
        loop_args = ["-stream_loop", "-1"]
        print(f"[+] Using streamed background asset (looped): {bg_path}")

    # Ensure output/ exists
    os.makedirs("output", exist_ok=True)

    # Create a temp output file inside output/
    out_tmp = tempfile.NamedTemporaryFile(
        prefix="out_",
        suffix=".mp4",
        delete=False,
        dir="output"
    )
    out_tmp.close()

    # Build FFmpeg filter graph for burning subtitles and overlay
    vf = (
        "[0:v]"
        "scale=1080:1920:force_original_aspect_ratio=decrease,"  # fit video
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black[bg];"
        f"[bg]subtitles={ass_path}:fontsdir={settings.fonts_dir}[sub];"
        f"[2:v]scale=1000:-1[card];"
        f"[sub][card]overlay=40:(H-h)/2:enable='lte(t,{first_dur})'[outv]"
    )

    # First stage: burn subtitles and overlay card on looping background
    cmd = [
        "ffmpeg", "-y",
        *loop_args,
        "-i", bg_path,
        "-i", settings.audio_mp3,
        "-i", card_png,
        "-filter_complex", vf,
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-shortest", "-movflags", "+faststart",
        out_tmp.name
    ]

    print(f"[+] Running FFmpeg stage1 (burn & mux): {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    final_path = out_tmp.name

    # Second stage: optionally mix background music
    if bg_music:
        if not os.path.isfile(bg_music):
            raise FileNotFoundError(f"Background music not found: {bg_music}")

        mixed_out = tempfile.NamedTemporaryFile(
            prefix="out_music_", suffix=".mp4", delete=False, dir="output"
        )
        mixed_out.close()

        mix_cmd = [
            "ffmpeg", "-y",
            "-i", final_path,     # narration track
            "-stream_loop", "-1",
            "-i", bg_music,       # background music
            "-filter_complex",
            # keep narration at full volume [0:a]
            # drop music to 30% [1:a]volume=0.3
            # mix them together
            "[0:a]volume=1.0[aud0];"
            "[1:a]volume=0.3[aud1];"
            "[aud0][aud1]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            mixed_out.name
        ]
        print(f"[+] Running FFmpeg stage2 (add bg music): {' '.join(mix_cmd)}")
        subprocess.run(mix_cmd, check=True)

        # use mixed output as final
        final_path = mixed_out.name

    # Upload or return local path
    if settings.upload_to_drive:
        drive_id = upload_to_drive(final_path)
        return drive_id, final_path
    else:
        print(f"[+] Saved video locally to {final_path} (DRIVE upload disabled)")
        return None, final_path
