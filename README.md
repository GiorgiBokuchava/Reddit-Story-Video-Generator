# Reddit Story Video Generator

**Reddit Story Video Generator** is a Python tool that automates turning Reddit posts into vertical videos with AI voice-over, dynamic karaoke-style subtitles, and Drive-hosted background videos.

It fetches Reddit submissions, cleans and expands the text, generates audio narration via TTS, aligns word timings with Vosk ASR, burns karaoke subtitles, and produces a final MP4—all without leaving large media on your local disk.

## ✨ Features

* Fetches Reddit posts using **PRAW**
* Cleans and expands text (Markdown -> plain, abbreviations expanded)
* Text-to-speech via **Microsoft Edge TTS**
* Word-level timestamp alignment via **Vosk ASR**
* Karaoke-style ASS subtitles with word highlighting
* Video composition via **FFmpeg**
* Streams a **single random background clip** from a Google Drive folder
* Uploads final videos directly into a Drive outputs folder
* Cleans up all temporary files locally

## ⚙️ How It Works

1. **Input** Prompt for a Reddit post URL.
2. **Fetch & Preprocess** Download title & body -> clean Markdown -> expand abbreviations -> split into sentences.
3. **TTS & Audio** Synthesize each sentence to MP3 -> WAV, collect durations -> combine into one MP3/WAV.
4. **Transcription** Use Vosk to align words -> build `{word, start_ms, end_ms}` list.
5. **Subtitle Generation** Write an ASS file with karaoke windows.
6. **Background Selection** List files in your **Drive backgrounds** folder -> pick one at random -> stream-download into a temp file.
7. **Burn & Mux** Run FFmpeg (scale->pad->ASS subtitles) -> produce a temp MP4.
8. **Upload & Cleanup** Upload the MP4 to your **Drive outputs** folder -> delete all temp files.

## 📦 Requirements

* **Python 3.8+**
* **FFmpeg** (in your PATH)
* **Google Cloud**
   * A Drive API-enabled project with an OAuth **Desktop app** client
   * `credentials.json` & `token.json` in your project root
* **Python packages** (via `requirements.txt`):

```
praw edge-tts vosk pydub python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib requests
```

* **Assets** (hosted on Drive):
   * **Background clips** in a Drive folder
   * **Outputs** folder on Drive for final videos
* **Local templates**:
   * `captions/captions.ass` (ASS subtitle template)
   * `.env` containing your API keys & folder IDs

## 🔧 Setup

1. **Clone & install**

```bash
git clone https://github.com/GiorgiBokuchava/Reddit-Story-Video-Generator.git
cd Reddit-Story-Video-Generator
python -m venv env
source env/bin/activate  # or .\env\Scripts\activate on Windows
pip install --upgrade pip
pip install -r requirements.txt
```

2. **OAuth Credentials**
   * Create a Google Cloud project -> **APIs & Services -> OAuth consent screen** -> set User Type to **External**, add your email as a **Test user**.
   * **Credentials -> Create Credentials -> OAuth client ID -> Desktop app** -> download JSON -> save as `credentials.json` in repo root.

3. **Generate `token.json`**

```bash
rm token.json  # if it exists
python scripts/drive_quickstart.py
```

Sign in with the same Gmail you added as a Test user; consent to both Drive **file** and **readonly** scopes.

4. **Configure `.env`**

Copy `.env.example` -> `.env`, then set:

```ini
REDDIT_CLIENT_ID=…
REDDIT_CLIENT_SECRET=…
REDDIT_USER_AGENT=…
EDGE_TTS_VOICE=en-US-JennyNeural
EDGE_TTS_RATE=+10%
DRIVE_BACKGROUNDS_FOLDER_ID=your_background_folder_id
DRIVE_OUTPUTS_FOLDER_ID=your_outputs_folder_id
```

5. **Ignore secrets**

Add to `.gitignore`:

```
credentials.json
token.json
assets/video/  # if you used any legacy local videos
output/
audio_chunks/
model/
```

## 🚀 Usage

From project root, with your venv active:

```bash
python run.py
```

Or:

```bash
python -m src.main
```

Enter a Reddit URL when prompted. The tool will:
* Fetch & process text
* Generate and align audio/subtitles
* Stream one Drive clip, burn subtitles, mux
* Upload final MP4 to Drive
* Clean up locals

## 🛠️ Customization

* **Voices**: change `EDGE_TTS_VOICE` / `EDGE_TTS_RATE` in `.env`
* **Subtitle style**: edit `captions/captions.ass`
* **FFmpeg filters**: adjust in `src/video_mux.py`
* **Backgrounds**: add/remove clips in your Drive backgrounds folder
