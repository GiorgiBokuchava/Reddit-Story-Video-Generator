import re
import html

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
    return html.unescape(text).strip()

def split_sentences(text: str) -> list[str]:
    parts = re.split(r'(?:(?<=[\.!?])|(?<=  ))\s+', text.replace('\n','  ').strip())
    return [p for p in parts if re.search(r'\w', p)]
