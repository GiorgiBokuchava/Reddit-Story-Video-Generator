import os
import re
import html
import json
import random
import wave
import urllib.request
import zipfile
import io
import praw
import asyncio
import edge_tts
import subprocess
from dotenv import load_dotenv
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer

load_dotenv()

# THIS IS OLD CODE, NO LONGER IN USE

# Configuration
CLIENT_ID     = os.getenv('REDDIT_CLIENT_ID')
CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
USER_AGENT    = os.getenv('REDDIT_USER_AGENT')

VOICE = os.getenv('EDGE_TTS_VOICE', 'en-US-JennyNeural')
TTS_RATE   = os.getenv('EDGE_TTS_RATE', '+10%')

TEMPLATE_ASS = 'captions/captions.ass'
OUTPUT_ASS   = 'captions/captions_karaoke.ass'
VIDEO_DIR    = 'assets/video'
FONTS_DIR = 'assets/font'
VIDEO_FILES  = [
    os.path.join(VIDEO_DIR, f)
    for f in os.listdir(VIDEO_DIR)
    if f.lower().endswith(('.mp4', '.mkv'))
]
AUDIO_MP3 = 'output/combined.mp3'
AUDIO_WAV = 'output/combined.wav'
VIDEO_OUT = 'output/final_9x16.mp4'
MODEL_DIR = 'model'

ABBREVIATIONS = {
    r'\bTIFU\b': 'Today I Effed Up',
    r'\bTIL\b':  'Today I Learned',
    r'\bAMA\b':  'Ask Me Anything',
    r'\bELI5\b': "Explain Like I'm Five",
    r'\bIDK\b':  "I don't know",
    r'\bIMO\b':  "in my opinion",
    r'\bIMHO\b': "in my honest opinion",
    r'\bFYI\b':  "for your information",
    r'\bBTW\b':  "by the way",
    r'\bASAP\b': "as soon as possible",
    r'\bGTG\b':  "got to go",
    r'\bICYMI\b': "in case you missed it",
    r'\bSMH\b':  "shaking my head",
    r'\bAFAIK\b': "as far as I know",
    r'\bOP\b':   "original poster",
    r'\bNSFW\b': "not safe for work",
    r'\bFOMO\b': "fear of missing out",
    r'\bYOLO\b': "you only live once",
    r'\bIRL\b':  "in real life",
    r'\bJK\b':   "just kidding",
    r'\bNVM\b':  "never mind",
    r'\bTBA\b':  "to be announced",
    r'\bTBD\b':  "to be determined",
    r'\bRN\b':   "right now",
    r'\bICYDK\b': "in case you didn't know",
    r'\bBFF\b':  "best friends forever",
    r'\bIDK\b':  "I don't know",
    r'\bIDC\b':  "I don't care",
    r'\bIDGAF\b': "I don't give an F",
    r'\bJS\b':   "just saying",
    r'\bjs\b':   "just",
    r'\bbc\b':   "because",
}

# Helpers
def log(msg):
    print(f"[+] {msg}", flush=True)

def init_reddit():
    log("Init Reddit")
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT
    )

def translate_phrases(text):
    for pat, full in ABBREVIATIONS.items():
        text = re.sub(pat, full, text, flags=re.IGNORECASE)
    return text

def clean_markdown(text):
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'(\*{1,3}|_{1,3})(.*?)\1', r'\2', text)
    text = re.sub(r'(?m)^>\s*', '', text)
    return html.unescape(text).strip()

def split_sentences(text):
    parts = re.split(r'(?:(?<=[\.!?])|(?<=  ))\s+', text.strip())
    parts = [p for p in parts if re.search(r'\w', p)]
    log(f"  -> {len(parts)} sentences")
    return parts

async def tts_and_duration(txt, mp3_path):
    log(f"TTS: {txt[:30]}… -> {mp3_path}")
    await edge_tts.Communicate(txt, VOICE, rate=TTS_RATE).save(mp3_path)
    dur = len(AudioSegment.from_file(mp3_path))
    log(f"  -> {dur}ms")
    return dur

def ensure_vosk_model():
    if not os.path.isdir(MODEL_DIR):
        log("Downloading Vosk model…")
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        resp = urllib.request.urlopen(url)
        with zipfile.ZipFile(io.BytesIO(resp.read())) as zf:
            zf.extractall(".")
        os.rename("vosk-model-small-en-us-0.15", MODEL_DIR)
        log("Model ready")

def transcribe_free(wav_path, model):
    """Run Vosk free‐form mode to get every word timestamp."""
    wf = wave.open(wav_path, 'rb')
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    out = []
    while True:
        data = wf.readframes(4000)
        if not data: break
        if rec.AcceptWaveform(data):
            chunk = json.loads(rec.Result()).get('result', [])
            out.extend(chunk)

    final_chunk = json.loads(rec.FinalResult()).get('result', [])
    
    if (out and final_chunk and 
            final_chunk[0]['word'].strip('.,!?;:').lower() == out[-1]['word'].strip('.,!?;:').lower()):
        final_chunk = final_chunk[1:]

    out.extend(final_chunk)
    return out

def format_ts(ms: float) -> str:
    # Convert milliseconds to H:MM:SS.cs for ASS.
    cs = int(ms // 10)
    h  = cs // 360000
    m  = (cs // 6000) % 60
    s  = (cs // 100) % 60
    c  = cs % 100
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"

def build_header():
    log("Writing ASS header")
    with open(TEMPLATE_ASS, encoding='utf-8') as fin, \
         open(OUTPUT_ASS,   'w', encoding='utf-8') as fout:
        for line in fin:
            fout.write(line)
            if line.strip() == '[Events]':
                break
        fout.write(
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n\n"
        )

def build_karaoke(all_words):
    # Build karaoke windows per sentence so no window ever spills into
    # the next sentence. When a sentence runs out of 25 chars, it breaks.
    MAX_CHARS = 15
    COLORS = ['&H0000FF&','&H00FF00&','&H00FFFF&']

    with open(OUTPUT_ASS, 'a', encoding='utf-8') as fout:
        # group by sentence id
        by_sent = {}
        for w in all_words:
            by_sent.setdefault(w['sid'], []).append(w)
        for sid in sorted(by_sent):
            words = by_sent[sid]
            # build windows within this sentence only
            windows = []
            cur, length = [], 0
            for i, w in enumerate(words):
                tok = w['word']
                add = len(tok) + (1 if cur else 0)
                if length + add > MAX_CHARS:
                    windows.append(cur)
                    cur, length = [], 0
                    add = len(tok)
                cur.append(i)
                length += add
            if cur:
                windows.append(cur)

            # random color per window
            wincols = [random.choice(COLORS) for _ in windows]
            idx2win = {}
            for wi, win in enumerate(windows):
                for idx in win:
                    idx2win[idx] = wi

            # output
            for idx, w in enumerate(words):
                wi   = idx2win[idx]
                win  = windows[wi]
                col  = wincols[wi]
                parts = []
                for j in win:
                    txt = words[j]['word']
                    if j == idx:
                        parts.append(fr'{{\1c{col}}}{txt}')
                        parts.append(r'{\1c&HFFFFFF&}')
                    else:
                        parts.append(txt)
                    parts.append(' ')
                disp = r"{\an5\bord1}" + "".join(parts).strip()
                st   = format_ts(w['start'])
                et   = format_ts(w['end'])
                fout.write(f"Dialogue: 0,{st},{et},Default,,0,0,0,,{disp}\n")

# Main Pipeline
def main():
    reddit = init_reddit()
    url    = input("Reddit post URL: ")
    post   = reddit.submission(url=url)
    log(f"Fetched: {post.title!r}")

    # Fetch & clean text
    raw_text = post.title + "\n\n" + post.selftext
    raw      = clean_markdown(translate_phrases(raw_text)).replace('\n','  ')
    sents    = split_sentences(raw)

    # TTS -> WAV
    os.makedirs('audio_chunks', exist_ok=True)
    durations, wavs = [], []
    for sent in sents:
        i   = len(durations)
        mp3 = f"audio_chunks/{i:03d}.mp3"
        dur = asyncio.run(tts_and_duration(sent, mp3))
        durations.append(dur)
        wav = f"audio_chunks/{i:03d}.wav"
        AudioSegment.from_file(mp3).export(wav, format='wav')
        wavs.append(wav)

    # Combine for final audio
    combo = AudioSegment.empty()
    for wav in wavs:
        seg   = AudioSegment.from_file(wav)
        combo = seg if len(combo)==0 else combo.append(seg, crossfade=0)
    os.makedirs('output', exist_ok=True)
    combo.export(AUDIO_MP3, format='mp3')
    combo.export(AUDIO_WAV, format='wav')
    log("Audio combined")

    # Load Vosk
    ensure_vosk_model()
    model = Model(MODEL_DIR)

    # Align each sentence, keep only timestamps but re-inject our exact text
    all_words = []
    offset    = 0
    for sid, (sent, wav, dur) in enumerate(zip(sents, wavs, durations)):
        raw_ts = transcribe_free(wav, model)
        tokens = re.findall(r"\w+(?:['’]\w+)?[.,!?;:()\"']*", sent)

        labelled = []
        for wi, ts in enumerate(raw_ts):
            text = tokens[wi] if wi < len(tokens) else ts['word']
            labelled.append({
                'word':  text,
                'start': ts['start']*1000 + offset,
                'end':   ts['end']*1000   + offset,
                'sid':   sid
            })
        log(f"  -> Aligned {len(labelled)} words for sentence {sid}")
        all_words.extend(labelled)
        offset += dur

    # Build ASS and burn in
    build_header()
    build_karaoke(all_words)

    log("Burning subtitles & muxing")
    vf = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"ass={OUTPUT_ASS}:fontsdir={FONTS_DIR}"
    )
    subprocess.run([
        'ffmpeg','-y',
        '-i', random.choice(VIDEO_FILES),
        '-i', AUDIO_MP3,
        '-vf', vf,
        '-map','0:v','-map','1:a',
        '-c:v','libx264','-preset','ultrafast',
        '-c:a','aac','-shortest','-movflags','+faststart',
        VIDEO_OUT
    ], check=True)
    log(f"Done: {VIDEO_OUT}")

    # Cleanup
    try:
        import shutil
        shutil.rmtree('audio_chunks')
        os.remove(AUDIO_MP3)
        os.remove(AUDIO_WAV)
    except Exception as e:
        log(f"Cleanup skipped: {e}")

if __name__ == '__main__':
    main()
