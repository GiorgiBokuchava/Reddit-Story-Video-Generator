import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables (expects GEMINI_API_KEY)
load_dotenv()

def generate_with_gemini(
    prompt: str,
) -> str:
    # Call Gemini and return the raw generated text.
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=128,
            temperature=0.1,
        ),
    )
    return response.text

def extract_hashtags(text: str, max_tags: int = 4) -> list[str]:
    # Regex out #words, dedupe, and trim to max_tags
    tags = re.findall(r"#\w+", text)
    seen = set()
    out = []
    for tag in tags:
        low = tag.lower()
        if low not in seen:
            seen.add(low)
            out.append(tag)
            if len(out) >= max_tags:
                break
    return out

def suggest_hashtags(description: str, max_tags: int = 4) -> list[str]:
    prompt = (
        "Here is a YouTube video description:\n"
        f"{description}\n\n"
        f"Suggest up to {max_tags} relevant hashtags (include the #):\n"
    )
    raw = generate_with_gemini(prompt)
    return extract_hashtags(raw, max_tags)


# MOOD-BASED AUDIO SELECTION

# Map moods to keyword labels
MOOD_MAP = {
    'happy':   ['happy', 'joy', 'upbeat', 'cheerful'],
    'sad':     ['sad', 'melancholy', 'sorrowful', 'calm'],
    'tense':   ['tense', 'suspense', 'dramatic'],
    'relaxed': ['relaxed', 'ambient', 'soft'],
    'neutral': ['neutral', 'background'],
}

# Root of your audio assets
AUDIO_ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'audio')

def detect_mood(text: str) -> str:
    """
    Ask Gemini to pick one of our defined moods.
    Falls back to 'neutral' if the response isn't one of the keys.
    """
    prompt = (
        "Classify the mood of this text as one of: "
        + ", ".join(MOOD_MAP.keys())
        + ".\n"
        f"Text: {text}\n"
        "Respond with exactly one mood word."
    )
    resp = generate_with_gemini(prompt).strip().lower()
    return resp if resp in MOOD_MAP else 'neutral'

def select_sound_for_mood(mood: str) -> str | None:
    """
    From assets/audio/{mood}/ pick the first supported file.
    If none, falls back to assets/audio/neutral/.
    """
    mood_dir = os.path.join(AUDIO_ROOT, mood)
    if not os.path.isdir(mood_dir):
        mood_dir = os.path.join(AUDIO_ROOT, 'neutral')

    for fname in os.listdir(mood_dir):
        if fname.lower().endswith(('.mp3', '.wav', '.aac')):
            return os.path.abspath(os.path.join(mood_dir, fname))
    return None

# QUICK-TEST CLI

if __name__ == "__main__":
    # Usage:
    #   python -m src.gemini_client "Your video description here…"
    import sys
    desc = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not desc:
        print("Provide a description on the command line.")
        sys.exit(1)

    mood = detect_mood(desc)
    sound = select_sound_for_mood(mood)
    print(f"Detected mood: {mood}")
    if sound:
        print(f"Selected audio file: {sound}")
    else:
        print("No audio found for that mood.")
