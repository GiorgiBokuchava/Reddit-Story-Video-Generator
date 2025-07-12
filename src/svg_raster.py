import asyncio, base64, tempfile, os
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw

async def _render_svg_to_png(svg_path: str, out_png: str,
                             width: int, height: int):
    raw = Path(svg_path).read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    data_uri = f"data:image/svg+xml;base64,{b64}"

    html = f"""
    <!doctype html>
        <html><body style="margin:0;padding:0;overflow:hidden">
            <img src="{data_uri}"
                width="{width}" height="{height}"
                style="display:block;object-fit:none"/>
        </body></html>"""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.set_content(html)
        await page.wait_for_selector("img")
        await page.screenshot(path=out_png, omit_background=False)
        await browser.close()

def render_full_svg(svg_path: str, temp_png: str,
                    width: int = 1457, height: int = 820):
    asyncio.run(_render_svg_to_png(svg_path, temp_png, width, height))

def svg_to_card_png(svg_path: str, out_png: str,
                    crop_x: int = 13, crop_y: int = 0,
                    crop_w: int = 1444, crop_h: int = 820,
                    target_w: int = 1080,
                    corner_radius: int = 50):
    """
    1) Render full SVG -> temp.png
    2) Crop the card
    3) Resize to target_w
    4) Apply rounded corners (corner_radius)
    5) Save final PNG
    """
    # 1) temp render
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    try:
        render_full_svg(svg_path, tmp.name, width=crop_x+crop_w, height=crop_h)

        # 2) crop
        img = Image.open(tmp.name).convert("RGBA")
        card = img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))

        # 3) resize
        scale = target_w / crop_w
        new_h = int(crop_h * scale)
        card = card.resize((target_w, new_h), Image.LANCZOS)

        # 4) rounded mask
        mask = Image.new("L", card.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            [(0, 0), card.size],
            radius=int(corner_radius * (target_w / crop_w)),
            fill=255
        )
        card.putalpha(mask)

        # 5) save
        Path(out_png).parent.mkdir(parents=True, exist_ok=True)
        card.save(out_png, "PNG")

    finally:
        try:
            os.unlink(tmp.name)
        except:
            pass
