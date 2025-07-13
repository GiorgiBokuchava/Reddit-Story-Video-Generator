from pydub import AudioSegment
import os, shutil

def combine_wavs(wav_infos: list[tuple[str,int]], mp3_out: str, wav_out: str):
    combo = AudioSegment.empty()
    for wav, _ in wav_infos:
        seg = AudioSegment.from_file(wav)
        combo = seg if len(combo)==0 else combo.append(seg, crossfade=0)
    os.makedirs(os.path.dirname(mp3_out), exist_ok=True)
    combo.export(mp3_out, format="mp3")
    combo.export(wav_out, format="wav")

def cleanup(dir: str, *files: str):

    # Remove the chunk directory if it exists
    if os.path.isdir(dir):
        try:
            shutil.rmtree(dir)
        except Exception:
            pass

    # Remove any other files if they exist
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
