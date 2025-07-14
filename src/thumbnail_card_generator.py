#!/usr/bin/env python3
import os
import base64
import xml.etree.ElementTree as ET
from PIL import ImageFont, ImageDraw, Image

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ns = {"svg": SVG_NS}


def generate_svg(
    template_svg: str,
    output_svg: str,
    subreddit: str,
    title: str,
    verified: bool,
    font_path: str,
    sub_font_size: int = 56,
    title_font_size: int = 68,
    padding_px: int = 32
):
    # 1) parse the SVG
    tree = ET.parse(template_svg)
    root = tree.getroot()

    # 2) embed the font via base64 @font-face so viewers will render it
    font_data = base64.b64encode(open(font_path, "rb").read()).decode("ascii")
    fam = os.path.splitext(os.path.basename(font_path))[0]
    css = (
        f"@font-face{{"
        f"  font-family:'{fam}';"
        f"  src:url('data:font/truetype;base64,{font_data}') format('truetype');"
        f"}}"
    )
    defs = root.find("svg:defs", ns)
    if defs is None:
        defs = ET.SubElement(root, "defs")
    style = ET.SubElement(defs, "style", {"type": "text/css"})
    style.text = css

    # 3) locate key elements
    card_el = root.find(".//svg:rect[@id='card']", ns)
    sub_el = root.find(".//svg:text[@id='subreddit']", ns)
    title_el = root.find(".//svg:text[@id='posttitle']", ns)
    chk_el = root.find(".//svg:rect[@id='checkmark']", ns)

    # 4) determine card right edge for wrapping
    cx = float(card_el.get("x", "0"))
    cw = float(card_el.get("width", str(cx)))
    card_end = cx + cw

    # 5) replace subreddit text tspan
    orig = sub_el.find("svg:tspan", ns)
    sx, sy = float(orig.get("x")), float(orig.get("y"))
    for c in list(sub_el):
        sub_el.remove(c)
    new_sub = ET.SubElement(sub_el, "tspan", {
        "x": str(sx),
        "y": str(sy),
        "font-family": fam,
        "font-size":   str(sub_font_size),
    })
    new_sub.text = f"r/{subreddit}"

    # 6) wrap & write post title tspans
    orig = title_el.find("svg:tspan", ns)
    tx, ty = float(orig.get("x")), float(orig.get("y"))
    for c in list(title_el):
        title_el.remove(c)

    max_w = card_end - tx - padding_px
    dummy = Image.new("RGB", (1,1))
    draw = ImageDraw.Draw(dummy)
    ftitle = ImageFont.truetype(font_path, title_font_size)

    words, line, lines = title.split(), "", []
    for w in words:
        test = (line + " " + w) if line else w
        bb   = draw.textbbox((0,0), test, font=ftitle)
        if bb[2] - bb[0] <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)

    line_h = title_font_size * 1.2
    for i, ln in enumerate(lines):
        y = ty + i * line_h
        ET.SubElement(title_el, "tspan", {
            "x": str(tx),
            "y": str(y),
            "font-family": fam,
            "font-size": str(title_font_size),
        }).text = ln

    # 7) reposition checkmark horizontally
    fsub = ImageFont.truetype(font_path, sub_font_size)
    bsub = draw.textbbox((0,0), new_sub.text, font=fsub)
    wsub = bsub[2] - bsub[0]
    if chk_el is not None:
        if verified:
            chk_el.set("x", str(sx + wsub + padding_px))
        else:
            grp = root.find(".//svg:g[@id='Reddit Thumbnail']", ns)
            if grp is not None:
                grp.remove(chk_el)

    # 8) dynamically grow card and shift footer if title is long
    THRESHOLD = 120
    if len(title) > THRESHOLD:
        extra_lines = (len(title) - 1) // THRESHOLD
        extra_h = extra_lines * line_h

        # a) grow SVG canvas
        svg_w = float(root.get("width"))
        svg_h = float(root.get("height"))
        new_h = svg_h + extra_h
        root.set("height", str(new_h))
        vb = root.get("viewBox").split()
        root.set("viewBox", f"{vb[0]} {vb[1]} {vb[2]} {new_h}")

        # b) grow card rectangle
        card_h = float(card_el.get("height"))
        card_el.set("height", str(card_h + extra_h))

        # c) shift likes & shares up by extra_h
        for fid in ("likes","shares"):
            el = root.find(f".//svg:rect[@id='{fid}']", ns)
            if el is not None:
                y = float(el.get("y"))
                el.set("y", str(y + extra_h))

    # 9) write out
    os.makedirs(os.path.dirname(output_svg), exist_ok=True)
    tree.write(output_svg, xml_declaration=True, encoding="utf-8")
    print(f"✔ Populated SVG written to {output_svg}")


if __name__ == "__main__":
    # Configuration (edit here)
    TEMPLATE_SVG    = "assets/Reddit Thumbnail.svg"
    OUTPUT_SVG      = "output/populated.svg"
    SUBREDDIT       = "TIFU"
    TITLE_TEXT      = "TIFU by thinking I could power through Norovirus and instead became a human Slip 'N Slide Slide Slide Slide Slide Slidee"
    VERIFIED_BADGE  = True
    FONT_FILE       = "assets/fonts/Inter_18pt-Bold.ttf"
    SUB_SIZE        = 56
    TITLE_SIZE      = 68
    PADDING         = 32

    generate_svg(
        template_svg    = TEMPLATE_SVG,
        output_svg      = OUTPUT_SVG,
        subreddit       = SUBREDDIT,
        title           = TITLE_TEXT,
        verified        = VERIFIED_BADGE,
        font_path       = FONT_FILE,
        sub_font_size   = SUB_SIZE,
        title_font_size = TITLE_SIZE,
        padding_px      = PADDING,
    )
