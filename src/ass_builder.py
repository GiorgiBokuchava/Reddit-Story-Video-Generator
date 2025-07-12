import random
from .config import settings

def format_ts(ms: float) -> str:
    cs = int(ms // 10)
    h = cs // 360000
    m = (cs // 6000) % 60
    s = (cs // 100) % 60
    c = cs % 100
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"

def write_karaoke_ass(all_words: list[dict]):
    # header
    with open(settings.template_ass, encoding='utf-8') as fin, \
         open(settings.output_ass, 'w', encoding='utf-8') as fout:
        for line in fin:
            fout.write(line)
            if line.strip() == "[Events]":
                break
        fout.write("Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n\n")

    # body
    MAX_CHARS = 15
    COLORS = ['&H0000FF&','&H00FF00&','&H00FFFF&']
    by_sent = {}
    for w in all_words:
        by_sent.setdefault(w['sid'], []).append(w)

    with open(settings.output_ass, 'a', encoding='utf-8') as fout:
        for sid, words in sorted(by_sent.items()):
            # build windows
            windows, cur, length = [], [], 0
            for idx, w in enumerate(words):
                tok = w['word']
                add = len(tok) + (1 if cur else 0)
                if length + add > MAX_CHARS:
                    windows.append(cur); cur, length = [], 0; add = len(tok)
                cur.append(idx); length += add
            if cur: windows.append(cur)

            wincols = [random.choice(COLORS) for _ in windows]
            idx2win = {idx: wi for wi, win in enumerate(windows) for idx in win}

            for idx, w in enumerate(words):
                wi = idx2win[idx]; col = wincols[wi]
                parts = []
                for j in windows[wi]:
                    txt = words[j]['word']
                    if j == idx:
                        parts += [fr'{{\1c{col}}}{txt}', r'{\1c&HFFFFFF&}']
                    else:
                        parts.append(txt)
                    parts.append(' ')
                disp = r"{\an5\bord1}" + "".join(parts).strip()
                st = format_ts(w['start']); et = format_ts(w['end'])
                fout.write(f"Dialogue: 0,{st},{et},Default,,0,0,0,,{disp}\n")
