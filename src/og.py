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

INK, PAPER, ACC, PRIMARY = "#1F2B27", "#F5F0E6", "#A3451D", "#2C4339"

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
    d, w = text_path(D.SITE["brand"].lower(), ROOT / "assets/fonts/lora-cyrillic-600-normal.woff2", 30)
    W = 40 + 10 + w + 2
    for name, ink, bg in (("logo.svg", INK, PAPER), ("logo-light.svg", "#FFFFFF", INK)):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} 40" width="{W:.0f}" height="40">'
               f'{mark(ink, bg, ACC)}<path transform="translate(50 29)" fill="{ink}" d="{d}"/></svg>')
        (A / name).write_text(svg, encoding="utf-8")
    icon = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="8" fill="{PAPER}"/>'
            f'<g transform="translate(5 5) scale(.75)">{mark(INK, PAPER, ACC)}</g></svg>')
    (A / "icon.svg").write_text(icon, encoding="utf-8")
    return icon

def render(page, html, w, h, out):
    page.set_viewport_size({"width": w, "height": h})
    page.set_content(html, wait_until="load")
    page.evaluate("document.fonts.ready")
    page.screenshot(path=str(out), omit_background=False)

def font_face():
    css = ""
    for fam, f, wt in (("Lora", "lora-cyrillic-600-normal", 600), ("Golos", "golos-text-cyrillic-400-normal", 400), ("Golos", "golos-text-cyrillic-600-normal", 600)):
        b = base64.b64encode((A / "fonts" / f"{f}.woff2").read_bytes()).decode()
        css += f"@font-face{{font-family:{fam};font-weight:{wt};src:url(data:font/woff2;base64,{b}) format('woff2')}}"
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
body{{margin:0;width:1200px;height:630px;background:{PAPER};font-family:Golos;color:{INK};display:flex;overflow:hidden;
background-image:linear-gradient(#ECE4D4 1px,transparent 1px),linear-gradient(90deg,#ECE4D4 1px,transparent 1px);background-size:28px 28px}}
.l{{width:600px;padding:64px 0 60px 70px;display:flex;flex-direction:column}}
.l .lg svg{{height:46px;width:auto}}
h1{{font:600 64px/1.08 Lora;margin:56px 0 22px;letter-spacing:-.02em}}
p{{font-size:27px;line-height:1.35;color:#4B5651;margin:0}}
.b{{margin-top:auto;font:600 24px Golos;color:{PRIMARY};display:flex;gap:14px;align-items:center}}
.b i{{display:block;width:44px;height:2px;background:{ACC}}}
.r{{flex:1;padding:50px 50px 50px 10px;display:flex;align-items:center}}
.r .c{{background:#FBF8F2;border:1px solid #D5C9B4;border-radius:20px;padding:18px;width:100%}}
.pl-floor{{fill:#FBF8F2}}.pl-f{{fill:{PAPER};stroke:{INK};stroke-width:1.6}}.pl-thin{{stroke-width:1;fill:none}}
.pl-dash{{stroke-dasharray:4 5;stroke:#4B5651}}.pl-soft{{fill:#ECE4D4}}.pl-rug{{fill:none;stroke-dasharray:6 5;stroke:#4B5651}}
.pl-acc{{fill:#E8C9B5}}.pl-acc2{{fill:{ACC};stroke:{ACC}}}.pl-w{{stroke:{INK};stroke-width:7;fill:none}}
.pl-door{{stroke:#4B5651;stroke-width:1.3;fill:none}}.pl-win{{stroke:#FBF8F2;stroke-width:4}}.pl-d{{stroke:#4B5651;fill:none}}
.pl-t{{font:600 13px Golos;fill:#4B5651;text-anchor:middle;letter-spacing:.06em}}"""
        html = f"""<html><head><style>{css}</style></head><body>
<div class="l"><div class="lg">{logo}</div><h1>Меблировка квартир под ключ</h1>
<p>Мебель, техника, текстиль и посуда. Подбор, доставка, сборка и расстановка.</p>
<div class="b"><i></i>{D.SITE['city']}</div></div>
<div class="r"><div class="c">{plan}</div></div></body></html>"""
        render(pg, html, 1200, 630, A / "og.png")
        b.close()
    Image.open(A / "og.png").convert("RGB").save(A / "og.png", optimize=True)
    print("OK: logo.svg, logo-light.svg, icon.svg, favicon.ico, icons, og.png")

if __name__ == "__main__":
    main()
