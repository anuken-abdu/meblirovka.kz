# -*- coding: utf-8 -*-
"""Логотипы SVG (текст в кривых), фавиконы, иконки и превью og.png 1200×630.
Запускать локально (нужны fontTools, brotli, Pillow, Playwright): python3 src/og.py
Результат кладётся в assets/ и коммитится — на Vercel этот скрипт не нужен."""
import base64, io, sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "assets"
sys.path.insert(0, str(ROOT / "src"))
import data as D  # noqa

INK, PAPER, ACC, PRIMARY = "#1B1A18", "#F3EFE9", "#8A6A42", "#1E1D1B"

def text_path(text, font_file, size):
    f = TTFont(font_file); gs = f.getGlyphSet(); cmap = f.getBestCmap()
    upm = f["head"].unitsPerEm; sc = size / upm; x = 0; pen = SVGPathPen(gs)
    for ch in text:
        g = cmap[ord(ch)]
        tp = TransformPen(pen, (sc, 0, 0, -sc, x, 0))
        gs[g].draw(tp); x += gs[g].width * sc
    return pen.getCommands(), x

def mark(stroke, bg, acc):
    return (f'<rect x="3" y="3" width="34" height="34" rx="3" fill="none" stroke="{stroke}" stroke-width="3"/>'
            f'<path d="M3 26h9" stroke="{bg}" stroke-width="4"/>'
            f'<path d="M12 26a9 9 0 0 0-9-9" fill="none" stroke="{stroke}" stroke-width="1.6"/>'
            f'<rect x="18" y="9" width="13" height="16" rx="2" fill="{acc}"/>')

def logos():
    """ВРЕМЕННЫЙ текстовый логотип до получения логотипа клиента."""
    d, w = text_path(D.SITE["brand"], ROOT / "assets/fonts/cormorant-garamond-latin-600-normal.woff2", 32)
    W = w + 2
    for name, ink in (("logo.svg", INK), ("logo-light.svg", "#FFFFFF")):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} 30" width="{W:.0f}" height="30">'
               f'<path transform="translate(1 23)" fill="{ink}" d="{d}"/></svg>')
        (A / name).write_text(svg, encoding="utf-8")
    m, mw = text_path("M", ROOT / "assets/fonts/cormorant-garamond-latin-600-normal.woff2", 34)
    icon = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="8" fill="{PRIMARY}"/>'
            f'<path transform="translate({(40-mw)/2:.2f} 30)" fill="#FFFFFF" d="{m}"/></svg>')
    print(f"logo.svg: {W:.0f}×30")
    (A / "icon.svg").write_text(icon, encoding="utf-8")
    return icon

def render(page, html, w, h, out):
    page.set_viewport_size({"width": w, "height": h})
    page.set_content(html, wait_until="load")
    page.evaluate("document.fonts.ready")
    page.screenshot(path=str(out), omit_background=False)

def font_face():
    css = ""
    for fam, f, wt in (("Corm", "cormorant-garamond-cyrillic-500-normal", 500), ("Man", "manrope-cyrillic-400-normal", 400), ("Man", "manrope-cyrillic-600-normal", 600)):
        b = base64.b64encode((A / "fonts" / f"{f}.woff2").read_bytes()).decode()
        css += f"@font-face{{font-family:{fam};font-weight:{wt};src:url(data:font/woff2;base64,{b}) format('woff2')}}"
    b = base64.b64encode((A / "fonts" / "cormorant-garamond-cyrillic-500-italic.woff2").read_bytes()).decode()
    css += f"@font-face{{font-family:Corm;font-style:italic;font-weight:500;src:url(data:font/woff2;base64,{b}) format('woff2')}}"
    return css

def main():
    icon = logos()
    from playwright.sync_api import sync_playwright
    plan = (ROOT / "src/plan.svg").read_text(encoding="utf-8")
    logo = (A / "logo.svg").read_text(encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        # иконки
        big = f'<html><body style="margin:0">{icon.replace("<svg ", "<svg width=512 height=512 ")}</body></html>'
        render(pg, big, 512, 512, A / "icon-512.png")
        im = Image.open(A / "icon-512.png").convert("RGBA")
        im.resize((192, 192), Image.LANCZOS).save(A / "icon-192.png")
        im.resize((180, 180), Image.LANCZOS).save(A / "apple-touch-icon.png")
        im.save(A / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
        # превью 1200×630 со стилями (шрифты встроены)
        css = f"""{font_face()}
body{{margin:0;width:1200px;height:630px;background:{PAPER};font-family:Man;color:{INK};display:flex;overflow:hidden}}
.l{{width:640px;padding:62px 0 58px 72px;display:flex;flex-direction:column}}
.l .lg svg{{height:34px;width:auto}}
h1{{font:500 82px/1.0 Corm;margin:auto 0 26px;letter-spacing:-.01em}}
h1 em{{font-style:italic;color:{ACC}}}
p{{font-size:24px;line-height:1.4;color:#5B564F;margin:0}}
.r{{flex:1;margin:40px 40px 40px 0;border:1px solid #D9D1C5;background:#FAF8F5;display:flex;align-items:center;justify-content:center;padding:36px}}
.pl-floor{{fill:none}}.pl-f{{fill:none;stroke:{INK};stroke-width:1.1}}.pl-thin{{stroke-width:.7;fill:none}}
.pl-dash{{stroke-dasharray:3 5;stroke:#5B564F}}.pl-soft{{fill:none}}.pl-rug{{fill:none;stroke-dasharray:2 4;stroke:#5B564F}}
.pl-acc{{fill:rgba(138,106,66,.16);stroke:{ACC}}}.pl-acc2{{fill:{ACC};stroke:{ACC}}}.pl-w{{stroke:{INK};stroke-width:5;fill:none}}
.pl-door{{stroke:#5B564F;stroke-width:.9;fill:none}}.pl-win{{stroke:#FAF8F5;stroke-width:3}}.pl-d{{stroke:{ACC};stroke-width:.8;fill:none}}
.pl-t{{font:600 11px Man;fill:#5B564F;text-anchor:middle;letter-spacing:.18em;text-transform:uppercase}}"""
        html = f"""<html><head><style>{css}</style></head><body>
<div class="l"><div class="lg">{logo}</div><h1>Меблировка квартир <em>под ключ</em></h1>
<p>Мебель на заказ, 3D-проект, монтаж и гарантия. {D.SITE['city']}</p></div>
<div class="r">{plan}</div></body></html>"""
        render(pg, html, 1200, 630, A / "og.png")
        b.close()
    Image.open(A / "og.png").convert("RGB").save(A / "og.png", optimize=True)
    print("OK: logo.svg, logo-light.svg, icon.svg, favicon.ico, icons, og.png")

if __name__ == "__main__":
    main()
