import re
import html

# regex matching all emoji ranges
_EMOJI_PATTERN = re.compile(
    r"["
    r"\U0001F600-\U0001F64F"
    r"\U0001F300-\U0001F5FF"
    r"\U0001F680-\U0001F6FF"
    r"\U0001F1E0-\U0001F1FF"
    r"\u2600-\u26FF"
    r"\u2700-\u27BF"
    r"]+",
    flags=re.UNICODE
)

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
    r'\bIDC\b':  "I don't care",
    r'\bIDGAF\b': "I don't give an F",
    r'\bJS\b':   "just saying",
    r'\bjs\b':   "just",
    r'\bbc\b':   "because",
}

def remove_emojis(text: str) -> str:
    return _EMOJI_PATTERN.sub("", text)


def translate_phrases(text: str) -> str:
    for pat, full in ABBREVIATIONS.items():
        text = re.sub(pat, full, text, flags=re.IGNORECASE)
    return text


def clean_markdown(text: str) -> str:
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'(\*{1,3}|_{1,3})(.*?)\1', r'\2', text)
    text = re.sub(r'(?m)^>\s*', '', text)
    text = html.unescape(text).strip()
    # remove emojis after markdown clean
    return remove_emojis(text)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r'(?:(?<=[\.!?])|(?<=  ))\s+', text.replace('\n','  ').strip())
    return [p for p in parts if re.search(r'\w', p)]
