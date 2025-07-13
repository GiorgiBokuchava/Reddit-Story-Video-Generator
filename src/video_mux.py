<<<<<<< HEAD
# src/video_mux.py

import os
import subprocess
import tempfile
from .asset_manager import choose_and_stream_video
from .drive_utils import upload_to_drive
from .config import settings

def burn_and_mux(card_png: str, ass_path: str, first_dur: float):
    """
    Stream background clip
    Scale/pad to 1080x1920
    Burn subtitles into that
    Scale card to 1000px wide, overlay at 40px from left/center vertically for t<=first_dur
    Upload to Drive or save locally
    """
    bg_tmp = choose_and_stream_video()
    out_tmp = tempfile.NamedTemporaryFile(prefix="out_", suffix=".mp4", delete=False)
    out_tmp.close()

    # filter chain:
    # scale+pad => [bg]
    # subtitles (all) => [sub]
    # load and scale card PNG => [card]
    # overlay card atop subtitles for t<=first_dur => [outv]
    vf = (
        "[0:v]"
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black"
        "[bg];"
        f"[bg]subtitles={ass_path}:fontsdir={settings.fonts_dir}[sub];"
        f"[2:v]scale=1000:-1[card];"
        f"[sub][card]overlay=40:(H-h)/2:enable='lte(t,{first_dur})'[outv]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", bg_tmp.name,        # background clip
        "-i", settings.audio_mp3, # audio track
        "-i", card_png,           # card image
        "-filter_complex", vf,
        "-map", "[outv]",         # video from our chain
        "-map", "1:a",            # map audio
=======
import os
import subprocess
import tempfile
from dotenv import load_dotenv

from .asset_manager import choose_and_stream_video
from .drive_utils   import upload_to_drive
from .config        import settings

load_dotenv()

def burn_and_mux():
    # Stream one random background clip into a temp file
    bg_tmp = choose_and_stream_video()

    # Create a temp file for the FFmpeg output
    out_tmp = tempfile.NamedTemporaryFile(prefix="out_", suffix=".mp4", delete=False)
    out_tmp.close()

    # Build FFmpeg video filter (scale, pad, burn ASS subtitles)
    vf = ",".join([
        "scale=1080:1920:force_original_aspect_ratio=decrease",
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black",
        f"ass={settings.output_ass}:fontsdir={settings.fonts_dir}"
    ])

    cmd = [
        "ffmpeg", "-y",
        "-i", bg_tmp.name,
        "-i", settings.audio_mp3,
        "-vf", vf,
        "-map", "0:v", "-map", "1:a",
>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-shortest", "-movflags", "+faststart",
        out_tmp.name
    ]
<<<<<<< HEAD

    print(f"[+] Running FFmpeg:\n    {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    if settings.upload_to_drive:
        drive_id = upload_to_drive(out_tmp.name)
        return drive_id, out_tmp.name
    else:
        os.makedirs("output", exist_ok=True)
        final = os.path.join("output", os.path.basename(out_tmp.name))
        os.replace(out_tmp.name, final)
        print(f"[+] Saved video locally to {final} (DRIVE upload disabled)")
        return None, final
=======
    print(f"[+] Running FFmpeg:\n    {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Upload to Drive and keep the local MP4 around
    drive_file_id = upload_to_drive(out_tmp.name)

    # Return both so caller can upload to YouTube before cleanup
    return drive_file_id, out_tmp.name
>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790
