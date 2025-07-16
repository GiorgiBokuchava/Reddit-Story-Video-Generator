import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables (expects GEMINI_API_KEY)
load_dotenv()

# Fetch API key once
_GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not _GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set or empty.")

# Hashtag extraction logic
MOOD_MAP = {
    'happy':   ['happy', 'joy', 'upbeat', 'cheerful'],
    'sad':     ['sad', 'melancholy', 'sorrowful', 'calm'],
    'tense':   ['tense', 'suspense', 'dramatic'],
    'relaxed': ['relaxed', 'ambient', 'soft'],
    'neutral': ['neutral', 'background'],
}

AUDIO_ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'audio')


def generate_with_gemini(prompt: str) -> str:
    """
    Call Gemini and return the raw generated text.
    Raises RuntimeError if the API request fails or key is invalid.
    """
    try:
        client = genai.Client(api_key=_GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=128,
                temperature=0.1,
            ),
        )
        return response.text
    except Exception as e:
        raise RuntimeError(f"Gemini generation failed: {e}")


def extract_hashtags(text: str, max_tags: int = 4) -> list[str]:
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
    raw = generate_with_gemini(prompt).strip().lower()
    return raw if raw in MOOD_MAP else 'neutral'


def detect_gender(text: str) -> str:
    """
    Ask Gemini to determine the author’s likely gender based on writing style.
    Responds 'male' or 'female'.
    """
    prompt = (
        "Based on the writing style and content, is the author male or female?"
        f"\nText: {text}\n"
        "Respond with exactly one word: male or female."
    )
    raw = generate_with_gemini(prompt).strip().lower()
    return raw if raw in ('male', 'female') else 'female'


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


# CLI for testing Gemini outputs
def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.ai_utils <description-or-text-file>")
        sys.exit(1)
    arg = sys.argv[1]
    if os.path.isfile(arg):
        with open(arg, encoding='utf-8') as f:
            description = f.read().strip()
    else:
        description = arg

    print("\n--- GEMINI OUTPUTS ---")
    print("Hashtags:")
    print(suggest_hashtags(description))
    print("Mood:", detect_mood(description))
    print("Gender:", detect_gender(description))

if __name__ == "__main__":
    main()
