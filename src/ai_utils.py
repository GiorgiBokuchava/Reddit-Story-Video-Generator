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
    # resp.text holds the generated output
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


if __name__ == "__main__":
    sample_desc = ("TIFU by buying a cheap swimsuit and flashing everyone on a kayak tour I was on vacation in the Turkish Riviera and didn’t pack a bathing suit since I didn’t have room, thinking I’d just buy one when I got there. Instead of going to a proper store, I got lazy and grabbed one from the convenience store next to my hotel. During a group kayak tour to see some sunken cities and an old Turkish castle, I stretched to step into the kayak that was on a dock and the swimsuit completely split open. I mean full rip. Thankfully I was the last one to get into a kayak so. The only one to maybe get a view of the initial tear was one unfortunate guide. I panicked, tied my shirt around my waist to cover up, and forgot to grab my water bottle off the dock. I was stuck like that for six hours in the sun, paddling around in 90 degree heat. I was so preoccupied I didn’t even put sunscreen on the rest of me, just my arms and face. I ended up with the worst sunburn of my life. TLDR: Bought a $5 swimsuit, maybe flashed strangers, forgot my water, and got the worst sunburn of my life. Edit: a lot of people are hung up on the fact that I couldn’t fit the swimsuit. I was traveling to Europe for 3 weeks and I only travel with carry ons so something had to be sacrificed and since we were only on the coast for 3 days I figured I could just buy a swimsuit and then throw it away when we left.")
    print("Description:\n", sample_desc, "\n")
    tags = suggest_hashtags(sample_desc)
    print("Generated Hashtags:", tags)
