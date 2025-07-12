import os
import zipfile
import io
import urllib.request
import json
import wave
from vosk import Model, KaldiRecognizer
from .config import settings

def ensure_model():
    if not os.path.isdir(settings.model_dir):
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        resp = urllib.request.urlopen(url)
        with zipfile.ZipFile(io.BytesIO(resp.read())) as zf:
            zf.extractall(".")
        os.rename("vosk-model-small-en-us-0.15", settings.model_dir)

def transcribe_free(wav_path: str, model: Model):
    wf = wave.open(wav_path, 'rb')
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    out = []
    while True:
        data = wf.readframes(4000)
        if not data: break
        if rec.AcceptWaveform(data):
            out.extend(json.loads(rec.Result()).get('result', []))
    out.extend(json.loads(rec.FinalResult()).get('result', []))
    return out