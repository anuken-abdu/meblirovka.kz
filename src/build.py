# -*- coding: utf-8 -*-
"""Генератор сайта (ru + kk). Запуск: python3 src/build.py  →  dist/
Русская версия — в корне, казахская — в /kz/. Только стандартная библиотека Python."""
import html, json, re, shutil, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"
sys.path.insert(0, str(SRC))
import data as D_RU    # noqa: E402
import data_kz as D_KK  # noqa: E402
import i18n            # noqa: E402

VER = "5"
ICON_DIR = ASSETS / "icons"
LANGS = [("ru", D_RU, i18n.RU, ""), ("kk", D_KK, i18n.KK, "/kz")]

# текущий язык (переключается в main)
D = D_RU; T = i18n.RU; PFX = ""; LANG = "ru"; S = D.SITE; CATS = D.CATEGORIES
BASE = f"https://www.{D_RU.SITE['domain']}"

# ── утилиты ─────────────────────────────────────────────────────────────────
def esc(s): return html.escape(str(s), quote=True)
NB_RE = re.compile(r"(?<![\wА-Яа-яЁё])([А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІіA-Za-z]{1,2})\s+")
def nb(s):
    s = esc(s)
    s = NB_RE.sub(lambda m: m.group(1) + "\u00a0", s)
    s = re.sub(r"\s+—", "\u00a0—", s)
    return re.sub(r"(\d)\s+(м²|м|см|кг)", "\\1\u00a0\\2", s)

def fmt(key, **kw):
    v = T[key]
    base = {"city_in": S["city_in"], "city_gen": S["city_gen"], "city": S["city"], "brand": S["brand"], "domain": S["domain"]}
    base.update(kw)
    return v.format(**base)

_icons = {}
def icon(name, cls="i"):
    if name not in _icons:
        svg = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
        _icons[name] = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", svg.strip())
    return f'<svg class="{cls}" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true" focusable="false">{_icons[name]}</svg>'

def wa_url(text): return f"https://wa.me/{S['wa']}?text={urllib.parse.quote(text)}"
def tel_attrs(): return f'href="tel:{S["phone_tel"]}" onclick="return gtag_report_conversion(&#39;tel:{S["phone_tel"]}&#39;)"'
def wa_attrs(text): return f'href="{esc(wa_url(text))}" target="_blank" rel="noopener" onclick="gtag_report_conversion()"'

def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>~])\s*", r"\1", css)
    css = re.sub(r"\s*:\s*", ":", css)
    return css.replace(";}", "}").replace(" and(", " and (").strip()

def url_of(p): return f"{BASE}{p}"
def P(p): return f"{PFX}{p}"                      # путь с языковым префиксом
def cat_path(c): return P(f"/{c['slug']}/")
def work_path(c, w): return P(f"/{c['slug']}/{w['slug']}/")
def find_by_key(key):
    parts = key.split("/")
    for c in CATS:
        if c["slug"] == parts[0]:
            if len(parts) == 1: return cat_path(c), c
            for w in c["works"]:
                if w["slug"] == parts[1]: return work_path(c, w), w
    raise KeyError(key)

CSS = minify_css((SRC / "fonts.css").read_text(encoding="utf-8") + (SRC / "styles.css").read_text(encoding="utf-8"))
PLAN_SVG = (SRC / "plan.svg").read_text(encoding="utf-8")

# ── <head>: теги Google ─────────────────────────────────────────────────────
def head_tags():
    out = []
    if S["gtm_id"]:
        g = S["gtm_id"]
        out.append(f"""<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{g}');</script>
<!-- End Google Tag Manager -->""")
    if S["aw_id"]:
        a = S["aw_id"]
        out.append(f"""<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={a}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{a}');
</script>""")
    if S["aw_id"] and S["aw_label"]:
        out.append(f"""<!-- Event snippet for conversion page -->
<script>
function gtag_report_conversion(url) {{
  var done = false;
  var callback = function () {{
    if (done) return; done = true;
    if (typeof(url) != 'undefined') {{ window.location = url; }}
  }};
  gtag('event', 'conversion', {{'send_to': '{S["aw_id"]}/{S["aw_label"]}', 'event_callback': callback}});
  setTimeout(callback, 800);
  return false;
}}
</script>""")
    else:
        out.append("<script>window.dataLayer=window.dataLayer||[];function gtag_report_conversion(u){window.dataLayer.push({event:'contact_click',url:u||''});return true;}</script>")
    return "\n".join(out)

def body_tags():
    if not S["gtm_id"]: return ""
    return (f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={S["gtm_id"]}" '
            f'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>')

# ── JSON-LD ─────────────────────────────────────────────────────────────────
def org_ld():
    return {"@type": "FurnitureStore", "@id": f"{BASE}/#org", "name": S["brand"],
            "description": f"{D.TAGLINE} — {S['city']}. {D.ABOUT}", "url": url_of(P("/")), "telephone": S["phone_tel"],
            "logo": f"{BASE}/assets/logo.svg", "image": f"{BASE}/assets/og.png",
            "address": {"@type": "PostalAddress", "addressLocality": S["city"], "addressCountry": "KZ", **({"streetAddress": S["address"]} if S["address"] else {})},
            "areaServed": {"@type": "City", "name": S["city"]}, "openingHours": S["hours_ld"],
            "makesOffer": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": c["h1"], "url": url_of(cat_path(c))}} for c in CATS]}
def crumbs_ld(cr): return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": url_of(p)} for i, (n, p) in enumerate(cr)]}
def faq_ld(faq): return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
def service_ld(name, desc, p):
    return {"@type": "Service", "name": name, "description": desc, "url": url_of(p), "provider": {"@id": f"{BASE}/#org"},
            "areaServed": {"@type": "City", "name": S["city"]}, "serviceType": T["service_type"]}

# ── шапка, меню, подвал ─────────────────────────────────────────────────────
def logo_img(light=False):
    L = D.LOGO; f = "logo-light.svg" if light else "logo.svg"
    return f'<img class="logo-img" src="/assets/{f}?v={VER}" width="{L["w"]}" height="{L["h"]}" alt="{esc(S["brand"])}">'

def other_lang_path(path):
    """Путь этой же страницы на другом языке."""
    bare = path[3:] if path.startswith("/kz") else path
    bare = bare or "/"
    return bare if LANG == "kk" else "/kz" + bare

def lang_switch(path):
    return f'<a class="lang" href="{other_lang_path(path)}" hreflang="{"ru" if LANG == "kk" else "kk"}" aria-label="{T["switch"]} — {T["switch_aria"]}">{T["switch"]}</a>'

def nav_html():
    cols = []
    for c in CATS:
        items = "".join(f'<li><a href="{work_path(c, w)}">{esc(w["name"])}</a></li>' for w in c["works"])
        cols.append(f'<div class="dd-col{" dd-wide" if len(c["works"]) > 3 else ""}"><a class="dd-cat" href="{cat_path(c)}">{esc(c["name"])}</a><ul>{items}</ul></div>')
    return f"""<nav class="nav" aria-label="{T['main_menu']}"><ul class="nav-list">
<li class="has-dd"><a href="{P('/')}#uslugi" class="nav-link" aria-haspopup="true">{T['services']}{icon("caret-down", "i i-s")}</a><div class="dd">{''.join(cols)}</div></li>
<li><a class="nav-link" href="{P('/')}#process">{T['how_nav']}</a></li>
<li><a class="nav-link" href="{P('/ceny/')}">{T['prices']}</a></li>
<li><a class="nav-link" href="{P('/stati/')}">{T['articles']}</a></li>
<li><a class="nav-link" href="{P('/kontakty/')}">{T['contacts']}</a></li>
</ul></nav>"""

def mobile_menu(wa_text, path):
    groups = "".join(f'<li><a class="mm-cat" href="{cat_path(c)}">{esc(c["name"])}</a><ul>' +
                     "".join(f'<li><a href="{work_path(c, w)}">{esc(w["name"])}</a></li>' for w in c["works"]) + "</ul></li>" for c in CATS)
    return f"""<div class="mm" id="mm" hidden><div class="mm-panel" role="dialog" aria-modal="true" aria-label="{T['menu']}">
<div class="mm-top"><span class="mm-title">{T['menu']}</span>{lang_switch(path)}<button class="icon-btn mm-close" type="button" aria-label="{T['menu_close']}">{icon("x")}</button></div>
<ul class="mm-list">{groups}
<li><a class="mm-link" href="{P('/')}#process">{T['how_nav']}</a></li><li><a class="mm-link" href="{P('/ceny/')}">{T['prices']}</a></li>
<li><a class="mm-link" href="{P('/rayony/')}">{T['districts']}</a></li><li><a class="mm-link" href="{P('/stati/')}">{T['articles']}</a></li><li><a class="mm-link" href="{P('/kontakty/')}">{T['contacts']}</a></li></ul>
<div class="mm-cta"><a class="btn btn-dark" {tel_attrs()}>{icon("phone")}{T['call']}</a><a class="btn btn-wa" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}{T['wa']}</a></div>
</div></div>"""

def header_html(wa_text, path):
    return f"""<header class="hdr"><div class="wrap hdr-in">
<a class="logo" href="{P('/')}" aria-label="{esc(S['brand'])} — {T['home_aria']}">{logo_img()}</a>
{nav_html()}
<div class="hdr-cta">
{lang_switch(path)}
<a class="hdr-phone" {tel_attrs()} aria-label="{T['call_aria']} {esc(S['phone_display'])}">{icon("phone")}<span>{esc(S['phone_display'])}</span></a>
<button class="icon-btn burger" type="button" aria-label="{T['menu_open']}" aria-expanded="false" aria-controls="mm">{icon("list")}</button>
</div></div></header>"""

def footer_html():
    cats = "".join(f'<li><a href="{cat_path(c)}">{esc(c["name"])}</a></li>' for c in CATS)
    return f"""<footer class="ftr"><div class="wrap">
<div class="ftr-grid">
<div class="ftr-brand"><a class="logo" href="{P('/')}" aria-label="{esc(S['brand'])} — {T['home_aria']}">{logo_img(True)}</a><p>{nb(D.TAGLINE + ' — ' + S['city'])}</p></div>
<div><p class="ftr-h">{T['services']}</p><ul>{cats}</ul></div>
<div><p class="ftr-h">{T['f_company']}</p><ul><li><a href="{P('/')}#process">{T['how_nav']}</a></li><li><a href="{P('/ceny/')}">{T['prices']}</a></li><li><a href="{P('/rayony/')}">{T['districts']}</a></li><li><a href="{P('/stati/')}">{T['articles']}</a></li></ul></div>
<div><p class="ftr-h">{T['f_contact']}</p><ul><li><a {tel_attrs()}>{esc(S['phone_display'])}</a></li><li><a {wa_attrs(T['wa_default'])}>WhatsApp</a></li><li>{esc(S['hours_text'])}</li><li>{esc(S['city'])}</li></ul></div>
</div>
<div class="ftr-bottom"><span>© {esc(S['brand'])}</span><a href="{P('/politika/')}">{T['privacy']}</a><a href="https://www.anuken.kz" target="_blank" rel="noopener">{T['dev']}</a></div>
</div></footer>"""

def floating_html(wa_text, is_home):
    """Слева: «Назад» над «Наверх». Справа: WhatsApp над ИИ-чатом — под большой палец."""
    back = "" if is_home else f'<button class="fbtn fbtn-back" type="button" aria-label="{T["back"]}">{icon("arrow-left")}</button>'
    return f"""<div class="fl fl-l">{back}<button class="fbtn fbtn-top" type="button" aria-label="{T['top']}" hidden>{icon("arrow-up")}</button></div>
<div class="fl fl-r"><a class="fbtn fbtn-wa" {wa_attrs(wa_text)} aria-label="{T['write_wa']}">{icon("whatsapp-logo")}</a>
<button class="fbtn fbtn-chat" type="button" aria-label="{T['chat']}"><img src="/assets/chat-bot-128.webp" width="34" height="34" alt=""></button></div>"""

def crumbs_html(cr):
    items = "".join(f'<li aria-current="page">{esc(n)}</li>' if i == len(cr) - 1 else f'<li><a href="{p}">{esc(n)}</a></li>' for i, (n, p) in enumerate(cr))
    return f'<div class="wrap crumbs-row"><nav class="crumbs" aria-label="{T["crumbs"]}"><ol>{items}</ol></nav></div>'

SITEMAP = []
def page(path, title, desc, body, *, crumbs=None, ld=None, wa_text=None, noindex=False, og_type="website", preload_img=None):
    wa_text = wa_text or T["wa_default"]
    graph = [org_ld(), {"@type": "WebSite", "@id": f"{BASE}/#site", "url": f"{BASE}/", "name": S["brand"], "inLanguage": ["ru-KZ", "kk-KZ"], "publisher": {"@id": f"{BASE}/#org"}}]
    if crumbs: graph.append(crumbs_ld(crumbs))
    graph += (ld or [])
    ldjson = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    canon = url_of(path)
    ru_p = (path[3:] or "/") if path.startswith("/kz") else path
    alt = "" if noindex else (f'<link rel="alternate" hreflang="ru-KZ" href="{url_of(ru_p)}">\n<link rel="alternate" hreflang="kk-KZ" href="{url_of("/kz" + ru_p)}">\n'
                              f'<link rel="alternate" hreflang="x-default" href="{url_of(ru_p)}">')
    lat, lon = S["geo_position"].split(";")
    if isinstance(preload_img, list): pre = "".join("\n" + x for x in preload_img)
    elif preload_img: pre = f'\n<link rel="preload" as="image" href="{preload_img[0]}" imagesrcset="{preload_img[1]}" imagesizes="{preload_img[2]}" fetchpriority="high">'
    else: pre = ""
    is_home = path in ("/", "/kz/")
    doc = f"""<!DOCTYPE html>
<html lang="{T['html_lang']}">
<head>
<meta charset="utf-8">
{head_tags()}
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{"" if noindex else f'<link rel="canonical" href="{canon}">'}
{alt}
<meta name="robots" content="{"noindex,follow" if noindex else "index,follow,max-image-preview:large"}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(S['brand'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{BASE}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{T['og_locale']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{BASE}/assets/og.png">
<meta name="geo.region" content="{S['geo_region']}">
<meta name="geo.placename" content="{esc(S['city'])}">
<meta name="geo.position" content="{S['geo_position']}">
<meta name="ICBM" content="{lat}, {lon}">
<meta name="theme-color" content="{S['theme_color']}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/assets/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/assets/fonts/onest-cyrillic-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/onest-cyrillic-500-normal.woff2" as="font" type="font/woff2" crossorigin>{pre}
<style>{CSS}</style>
<script type="application/ld+json">{ldjson}</script>
</head>
<body>
{body_tags()}
<a class="skip" href="#main">{T['skip']}</a>
{header_html(wa_text, path)}
{mobile_menu(wa_text, path)}
<main id="main">
{crumbs_html(crumbs) if crumbs else ''}
{body}
</main>
{footer_html()}
{floating_html(wa_text, is_home)}
<script type="application/json" id="ui-json">{json.dumps(T["chat_ui"], ensure_ascii=False, separators=(",", ":"))}</script>
<script src="/assets/app.js?v={VER}" defer></script>
</body>
</html>
"""
    out = DIST / f"{PFX.strip('/')}/404.html".lstrip("/") if path.endswith("/404") else DIST / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    if not noindex: SITEMAP.append(path)

# ── блоки ───────────────────────────────────────────────────────────────────
def sec_head(title, sub=None, hid=None):
    i = f' id="{hid}"' if hid else ""
    s = f'<p class="sec-sub">{nb(sub)}</p>' if sub else ""
    return f'<div class="sec-head"><h2{i}>{nb(title)}</h2>{s}</div>'

def cta_buttons(wa_text):
    return (f'<div class="cta-row"><a class="btn btn-dark btn-lg" {tel_attrs()}>{icon("phone")}{T["call"]}</a>'
            f'<a class="btn btn-wa btn-lg" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}{T["write_wa"]}</a></div>')

def img_set(key, widths):
    return [w for w in widths if (ASSETS / "img" / f"{key}-{w}.webp").exists()]

def photo(key, sizes, alt, lazy=False):
    ws = img_set(key, (480, 800, 1200))
    if 800 not in ws: return "", None
    srcset = ", ".join(f"/assets/img/{key}-{w}.webp {w}w" for w in ws)
    src = f"/assets/img/{key}-800.webp"
    attr = 'loading="lazy"' if lazy else 'fetchpriority="high"'
    return (f'<img src="{src}" srcset="{srcset}" sizes="{sizes}" width="800" height="600" alt="{esc(alt)}" {attr} decoding="async">', (src, srcset, sizes))

def corners(seed):
    """Угловой узор рамкой на фото: верхний левый и нижний правый (зеркально)."""
    n = sum(map(ord, seed)) % 6 + 1
    ss = f"/assets/orn/corner-{n}-160.webp 160w, /assets/orn/corner-{n}-240.webp 240w"
    one = lambda c: f'<img class="crn {c}" src="/assets/orn/corner-{n}-160.webp" srcset="{ss}" sizes="(min-width:1024px) 104px, 68px" width="160" height="155" alt="" aria-hidden="true" loading="lazy" decoding="async">'
    return one("crn-tl") + one("crn-br")

def webp_size(path):
    """Ширина и высота WebP без Pillow (VP8X/VP8L/VP8)."""
    b = path.read_bytes()[:40]
    if b[12:16] == b"VP8X": return int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1
    if b[12:16] == b"VP8L":
        v = int.from_bytes(b[21:25], "little"); return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
    return int.from_bytes(b[26:28], "little") & 0x3FFF, int.from_bytes(b[28:30], "little") & 0x3FFF

def ornament(slug):
    """Узор-разделитель направления (только на странице самого направления)."""
    ws = [w for w in (720, 1280) if (ASSETS / "orn" / f"{slug}-{w}.webp").exists()]
    if not ws: return ""
    w0, h0 = webp_size(ASSETS / "orn" / f"{slug}-{ws[0]}.webp")
    ss = ", ".join(f"/assets/orn/{slug}-{w}.webp {w}w" for w in ws)
    return (f'<div class="orn" aria-hidden="true"><div class="wrap"><img src="/assets/orn/{slug}-{ws[0]}.webp" srcset="{ss}" '
            f'sizes="(min-width:800px) 720px, calc(100vw - 40px)" width="{w0}" height="{h0}" alt="" loading="lazy" decoding="async"></div></div>')

def hero(h1, lead, wa_text, visual="", seed=""):
    vis = f'<div class="hero-vis">{visual}{corners(seed or h1)}</div>' if visual else ""
    return f"""<section class="hero{' hero-2' if visual else ''}"><div class="wrap hero-grid">
<div class="hero-txt"><h1>{nb(h1)}</h1><p class="lead">{nb(lead)}</p>{cta_buttons(wa_text)}</div>{vis}
</div></section>"""

def spec_list(items): return '<ul class="spec">' + "".join(f"<li>{nb(x)}</li>" for x in items) + "</ul>"

def wd_grid(c):
    items = []
    for w in c["works"]:
        img, _ = photo(w["slug"], "(min-width:1024px) 30vw, (min-width:600px) 45vw, 72px", fmt("alt_dir", name=w["name"]), lazy=True)
        vis = f'<span class="wd-ph">{img}</span>' if img else f'<span class="wd-ic">{icon(w.get("icon", "house"), "i")}</span>'
        items.append(f'<li><a class="wd{" wd-p" if img else ""}" href="{work_path(c, w)}">{vis}<span class="wd-t"><h3>{esc(w["name"])}</h3><p>{nb(w["card"])}</p></span></a></li>')
    return '<ul class="wds">' + "".join(items) + "</ul>"

def svc_rows(cats=None):
    rows = []
    for c in (cats or CATS):
        ws = c["works"] if len(c["works"]) <= 3 else c["works"][:4]
        works = "".join(f'<li><a href="{work_path(c, w)}">{esc(w["name"])}</a></li>' for w in ws)
        if len(c["works"]) > 3: works += f'<li><a href="{cat_path(c)}">{T["all_dirs"]}</a></li>'
        rows.append(f'<li class="svc"><h3><a href="{cat_path(c)}">{esc(c["name"])}{icon("arrow-up-right", "i svc-arr")}</a></h3>'
                    f'<p>{nb(c["card"])}</p><ul class="svc-works">{works}</ul></li>')
    return '<ul class="svcs">' + "".join(rows) + "</ul>"

def link_rows(items):
    out = []
    for t, h, d in items:
        dd = f'<span class="lr-d">{nb(d)}</span>' if d else ""
        out.append(f'<li><a class="lr" href="{h}"><span class="lr-t">{esc(t)}</span>{dd}{icon("arrow-right", "i lr-a")}</a></li>')
    return '<ul class="lrs">' + "".join(out) + "</ul>"

def steps_html():
    rows = "".join(f'<li><h3>{nb(t)}</h3><p>{nb(d)}</p></li>' for t, d in D.STEPS)
    return f'<section class="sec" id="process"><div class="wrap">{sec_head(T["how"], T["how_sub"])}<ol class="steps">{rows}</ol></div></section>'

def factors_html(factors=None):
    body = spec_list(factors) if factors else '<dl class="facts">' + "".join(f"<div><dt>{nb(t)}</dt><dd>{nb(d)}</dd></div>" for t, d in D.PRICE_FACTORS) + "</dl>"
    return f'<section class="sec sec-alt"><div class="wrap">{sec_head(T["price_t"], T["price_sub"])}{body}</div></section>'

def faq_html(faq):
    items = "".join(f'<details class="faq-i"><summary><h3>{nb(q)}</h3>{icon("caret-down", "i faq-c")}</summary><p>{nb(a)}</p></details>' for q, a in faq)
    return f'<section class="sec"><div class="wrap faq-wrap">{sec_head(T["faq"])}<div class="faq">{items}</div></div></section>'

def promises_html():
    items = "".join(f'<li><h3>{nb(t)}</h3><p>{nb(d)}</p></li>' for t, d in D.PROMISES)
    return f'<section class="sec sec-dark"><div class="wrap">{sec_head(T["prom"])}<ul class="proms">{items}</ul></div></section>'

def materials_html():
    def sw_item(cls, n, key):
        ws = img_set(key, (400, 800))
        if ws:
            ss = ", ".join(f"/assets/img/{key}-{w}.webp {w}w" for w in ws)
            vis = (f'<span class="sw sw-img"><img src="/assets/img/{key}-{ws[0]}.webp" srcset="{ss}" sizes="(min-width:1024px) 15vw, (min-width:600px) 30vw, 45vw" '
                   f'width="400" height="400" alt="{esc(n)}" loading="lazy" decoding="async"></span>')
        else:
            vis = f'<span class="sw {cls}" aria-hidden="true"></span>'
        return f'<li>{vis}<span class="sw-n">{esc(n)}</span></li>'
    return f'<section class="sec"><div class="wrap">{sec_head(T["mat"], T["mat_sub"])}<ul class="sws">{"".join(sw_item(*m) for m in D.MATERIALS)}</ul></div></section>'

def intro_html(text): return f'<section class="sec sec-intro"><div class="wrap"><p class="intro">{nb(text)}</p></div></section>'

def form_html(selected=""):
    opts = [f'<option value="">{T["select"]}</option>']
    for c in CATS:
        for w in c["works"]:
            sel = " selected" if selected == f'{c["slug"]}/{w["slug"]}' else ""
            opts.append(f'<option{sel}>{esc(c["name"] + ": " + w["name"])}</option>')
    opts.append(f"<option>{T['whole']}</option>")
    dis = f'<option value="">{T["select"]}</option>' + "".join(f'<option>{esc(d["name"])}</option>' for d in D.DISTRICTS)
    return f"""<section class="sec sec-form" id="zayavka" aria-labelledby="form-h"><div class="wrap form-grid">
<div class="form-txt"><h2 id="form-h">{nb(T['form_h'])}</h2><p>{nb(T['form_p'])}</p>
<p class="form-alt">{T['form_alt']} <a {tel_attrs()}>{esc(S['phone_display'])}</a></p></div>
<form class="form" novalidate>
<div class="f-row"><label for="f-work">{T['f_work']}</label><select id="f-work" name="work">{''.join(opts)}</select></div>
<div class="f-row"><label for="f-dis">{T['f_dis']}</label><select id="f-dis" name="district">{dis}</select></div>
<div class="f-row f-wide"><label for="f-msg">{T['f_msg']}</label><textarea id="f-msg" name="msg" rows="3" placeholder="{esc(T['f_msg_ph'])}"></textarea></div>
<div class="f-row"><label for="f-name">{T['f_name']}</label><input id="f-name" name="name" autocomplete="name"></div>
<div class="f-row"><label for="f-phone">{T['f_phone']}</label><input id="f-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required placeholder="+7 7__ ___ __ __" aria-describedby="f-err"></div>
<p class="f-err" id="f-err" role="alert"></p>
<button class="btn btn-light btn-lg f-wide" type="submit">{icon("whatsapp-logo")}{T['f_send']}</button>
<p class="f-note f-wide">{T['f_note']} <a href="{P('/politika/')}">{T['f_note_link']}</a>.</p>
</form></div></section>"""

# ── страницы ────────────────────────────────────────────────────────────────
def hero_bg():
    d, m = img_set("hero-desktop", (1280, 1920, 2560)), img_set("hero-mobile", (540, 810, 1080))
    if not d or not m: return "", None
    dset = ", ".join(f"/assets/img/hero-desktop-{w}.webp {w}w" for w in d)
    mset = ", ".join(f"/assets/img/hero-mobile-{w}.webp {w}w" for w in m)
    pic = (f'<picture class="hero-pic"><source media="(min-width:768px)" srcset="{dset}" sizes="100vw">'
           f'<img src="/assets/img/hero-mobile-{m[len(m) // 2]}.webp" srcset="{mset}" sizes="100vw" width="1080" height="1920" '
           f'alt="{esc(D.PHOTOS["hero"])}" fetchpriority="high" decoding="async"></picture>')
    pre = [f'<link rel="preload" as="image" media="(min-width:768px)" imagesrcset="{dset}" imagesizes="100vw" fetchpriority="high">',
           f'<link rel="preload" as="image" media="(max-width:767.98px)" imagesrcset="{mset}" imagesizes="100vw" fetchpriority="high">']
    return pic, pre

def build_home():
    pic, pre = hero_bg()
    h1 = nb(fmt("home_h1"))
    if pic:
        body = f'<section class="hero hero-bg">{pic}<div class="wrap hero-grid"><div class="hero-txt"><h1>{h1}</h1><p class="lead">{nb(D.ABOUT)}</p></div></div></section>'
    else:
        body = f'<section class="hero hero-2"><div class="wrap hero-grid"><div class="hero-txt"><h1>{h1}</h1><p class="lead">{nb(D.ABOUT)}</p></div><div class="hero-vis"><div class="plan-wrap" aria-hidden="true">{PLAN_SVG}</div></div></div></section>'
    body += f'<section class="sec" id="chto-delaem"><div class="wrap">{sec_head(T["wwd"], T["wwd_sub"])}{wd_grid(CATS[0])}</div></section>'
    body += steps_html()
    body += f'<section class="sec" id="uslugi"><div class="wrap">{sec_head(T["services"], T["svc_sub"])}{svc_rows(CATS[1:])}</div></section>'
    body += materials_html()
    body += promises_html()
    body += faq_html(D.FAQ_MAIN)
    body += form_html()
    page(P("/"), fmt("home_title"), fmt("home_desc"), body, ld=[faq_ld(D.FAQ_MAIN)], wa_text=T["wa_home"], preload_img=pre)

def build_category(c):
    p = cat_path(c); cr = [(T["home"], P("/")), (c["name"], p)]
    img, pre = photo(c["slug"], "(min-width:1024px) 46vw, calc(100vw - 40px)", D.PHOTOS.get(c["slug"], c["name"]))
    body = hero(c["h1"], c["lead"], c["wa_text"], img, seed=c["slug"])
    body += intro_html(c["intro"])
    big = len(c["works"]) > 3
    body += f'<section class="sec"><div class="wrap">{sec_head(T["wwd"] if big else T["directions"])}{wd_grid(c) if big else link_rows([(w["name"], work_path(c, w), ", ".join(w["includes"][:3])) for w in c["works"]])}</div></section>'
    body += f'<section class="sec"><div class="wrap split">{sec_head(T["includes"])}{spec_list(c["includes"])}</div></section>'
    body += steps_html()
    body += factors_html(c["factors"])
    body += faq_html(c["faq"])
    body += form_html()
    page(p, c["title"], c["desc"], body, crumbs=cr, wa_text=c["wa_text"], preload_img=pre, ld=[service_ld(c["h1"], c["desc"], p), faq_ld(c["faq"])])

def build_work(c, w):
    p = work_path(c, w); cr = [(T["home"], P("/")), (c["name"], cat_path(c)), (w["name"], p)]
    img, pre = photo(w["slug"], "(min-width:1024px) 46vw, calc(100vw - 40px)", fmt("alt_dir", name=w["name"]))
    body = hero(w["h1"], w["lead"], w["wa_text"], img, seed=w["slug"])
    if c is CATS[0]: body += ornament(w["slug"])
    body += f'<section class="sec"><div class="wrap split">{sec_head(T["includes"])}{spec_list(w["includes"])}</div></section>'
    body += steps_html()
    body += factors_html(c["factors"])
    body += faq_html(w["faq"])
    rel = [(x["name"], work_path(c, x), None) for x in c["works"] if x is not w] + [(x["name"], cat_path(x), None) for x in CATS if x is not c]
    body += f'<section class="sec"><div class="wrap">{sec_head(T["see_also"])}{link_rows(rel)}</div></section>'
    body += form_html(f'{c["slug"]}/{w["slug"]}')
    page(p, w["title"], w["desc"], body, crumbs=cr, wa_text=w["wa_text"], preload_img=pre, ld=[service_ld(w["h1"], w["desc"], p), faq_ld(w["faq"])])

def build_districts():
    p = P("/rayony/"); cr = [(T["home"], P("/")), (T["districts"], p)]
    body = hero(fmt("dist_h1"), fmt("dist_lead"), T["wa_default"])
    body += f'<section class="sec"><div class="wrap">{link_rows([(d["name"], P("/rayony/" + d["slug"] + "/"), d["note"]) for d in D.DISTRICTS])}</div></section>'
    body += f'<section class="sec"><div class="wrap">{sec_head(T["services"])}{svc_rows()}</div></section>'
    body += form_html()
    page(p, fmt("dist_title"), fmt("dist_desc") + ", ".join(d["name"] for d in D.DISTRICTS) + ".", body, crumbs=cr)
    for d in D.DISTRICTS:
        dp = P(f"/rayony/{d['slug']}/"); crd = [(T["home"], P("/")), (T["districts"], p), (d["name"], dp)]
        wa = fmt("d_wa", name=d["name"])
        faq = [(q.format(d_in=d["in"], city_gen=S["city_gen"]), a.format(d_in=d["in"], city_gen=S["city_gen"])) for q, a in T["d_faq"]]
        faq = [(q[0].upper() + q[1:], a) for q, a in faq]
        body = hero(fmt("d_h1", d_in=d["in"]), fmt("d_lead", d_in=d["in"]) + " " + d["note"], wa)
        body += f'<section class="sec"><div class="wrap">{sec_head(T["services"])}{svc_rows()}</div></section>'
        body += steps_html()
        body += faq_html(faq)
        body += f'<section class="sec"><div class="wrap">{sec_head(T["other_d"])}{link_rows([(x["name"], P("/rayony/" + x["slug"] + "/"), None) for x in D.DISTRICTS if x is not d])}</div></section>'
        body += form_html()
        page(dp, fmt("d_title", d_in=d["in"]), fmt("d_desc", d_in=d["in"]), body, crumbs=crd, wa_text=wa, ld=[faq_ld(faq)])

def build_prices():
    p = P("/ceny/"); cr = [(T["home"], P("/")), (T["prices"], p)]
    faq = [D.FAQ_MAIN[1]] + T["p_faq"]
    body = hero(fmt("p_h1"), T["p_lead"], T["p_wa"])
    body += factors_html() + steps_html() + faq_html(faq) + form_html()
    page(p, fmt("p_title"), fmt("p_desc"), body, crumbs=cr, ld=[faq_ld(faq)], wa_text=T["p_wa"])

def build_articles():
    p = P("/stati/"); cr = [(T["home"], P("/")), (T["articles"], p)]
    body = hero(T["a_h1"], T["a_lead"], T["a_wa"])
    body += f'<section class="sec"><div class="wrap">{link_rows([(a["name"], P("/stati/" + a["slug"] + "/"), a["lead"]) for a in D.ARTICLES])}</div></section>'
    page(p, fmt("a_title"), T["a_desc"], body, crumbs=cr)
    for a in D.ARTICLES:
        ap = P(f"/stati/{a['slug']}/"); cra = [(T["home"], P("/")), (T["articles"], p), (a["name"], ap)]
        parts = "".join(f"<h2>{nb(v)}</h2>" if k == "h2" else f"<p>{nb(v)}</p>" for k, v in a["blocks"])
        rel = []
        for key in a["related"]:
            path, obj = find_by_key(key); rel.append((obj["name"], path, None))
        y, m, dd = a["date"].split("-")
        date_h = f"{int(dd)} {T['months'][int(m) - 1]} {y}" if LANG == "ru" else f"{y} ж. {int(dd)} {T['months'][int(m) - 1]}"
        body = f"""<article class="sec art"><div class="wrap narrow">
<p class="art-date"><time datetime="{a['date']}">{date_h}</time></p>
<h1>{nb(a['h1'])}</h1><p class="lead">{nb(a['lead'])}</p>{parts}
<div class="art-cta"><p>{nb(T['a_cta'])}</p>{cta_buttons(fmt('a_wa_art', name=a['name']))}</div>
</div></article>
<section class="sec"><div class="wrap">{sec_head(T['by_topic'])}{link_rows(rel)}</div></section>"""
        art_ld = {"@type": "Article", "headline": a["h1"], "description": a["desc"], "datePublished": a["date"], "dateModified": a["date"],
                  "mainEntityOfPage": url_of(ap), "image": f"{BASE}/assets/og.png", "inLanguage": T["in_lang"],
                  "author": {"@id": f"{BASE}/#org"}, "publisher": {"@id": f"{BASE}/#org"}}
        page(ap, a["title"], a["desc"], body, crumbs=cra, ld=[art_ld], og_type="article")

def build_contacts():
    p = P("/kontakty/"); cr = [(T["home"], P("/")), (T["contacts"], p)]
    rows = [(T["c_phone"], f'<a {tel_attrs()}>{esc(S["phone_display"])}</a>'),
            ("WhatsApp", f'<a {wa_attrs(T["wa_default"])}>{T["c_write"]}</a>'),
            (T["c_hours"], esc(S["hours_text"])),
            (T["c_city"], esc(S["city"]) + (", " + esc(S["address"]) if S["address"] else ", " + T["c_visit"]))]
    if S["email"]: rows.insert(2, (T["c_mail"], f'<a href="mailto:{esc(S["email"])}">{esc(S["email"])}</a>'))
    dl = '<dl class="facts contacts">' + "".join(f"<div><dt>{l}</dt><dd>{v}</dd></div>" for l, v in rows) + "</dl>"
    body = f'<section class="hero"><div class="wrap"><h1>{T["c_h1"]}</h1><p class="lead">{nb(T["c_lead"])}</p></div></section>'
    body += f'<section class="sec"><div class="wrap">{dl}</div></section>' + form_html()
    page(p, fmt("c_title")[:60], fmt("c_desc") + f" {S['hours_text']}.", body, crumbs=cr)

def build_privacy():
    p = P("/politika/"); cr = [(T["home"], P("/")), (T["privacy"], p)]
    body = f'<section class="sec art"><div class="wrap narrow"><h1>{T["privacy"]}</h1>' + "".join(f"<h2>{nb(h)}</h2><p>{nb(t.format(domain=S['domain']))}</p>" for h, t in T["pr"]) + "</div></section>"
    page(p, fmt("pr_title"), fmt("pr_desc"), body, crumbs=cr)

def build_404():
    body = f"""<section class="hero"><div class="wrap"><h1>{T['nf_h1']}</h1><p class="lead">{nb(T['nf_lead'])}</p>
<div class="cta-row"><a class="btn btn-dark btn-lg" href="{P('/')}">{icon("house")}{T['nf_home']}</a><a class="btn btn-wa btn-lg" {wa_attrs(T['wa_default'])}>{icon("whatsapp-logo")}{T['write_wa']}</a></div></div></section>"""
    page(P("/404"), fmt("nf_title"), T["nf_h1"], body, noindex=True)

# ── служебные файлы ─────────────────────────────────────────────────────────
def build_kb():
    services, faq = [], [{"q": q, "a": a, "url": url_of(P("/"))} for q, a in D.FAQ_MAIN]
    for c in CATS:
        services.append({"name": c["h1"], "short": c["name"], "url": url_of(cat_path(c)), "lead": c["lead"], "includes": c["includes"], "wa": c["wa_text"], "custom": False})
        faq += [{"q": q, "a": a, "url": url_of(cat_path(c))} for q, a in c["faq"]]
        for w in c["works"]:
            services.append({"name": w["h1"], "short": w["name"], "url": url_of(work_path(c, w)), "lead": w["lead"], "includes": w["includes"], "wa": w["wa_text"], "custom": c is CATS[0]})
            faq += [{"q": q, "a": a, "url": url_of(work_path(c, w))} for q, a in w["faq"]]
    kb = {"lang": LANG, "brand": S["brand"], "city": S["city"], "city_gen": S["city_gen"], "city_in": S["city_in"], "phone": S["phone_display"], "tel": S["phone_tel"],
          "wa": S["wa"], "hours": S["hours_text"], "tagline": D.TAGLINE, "greeting": D.CHAT_GREETING, "about": D.ABOUT, "ui": T["chat_ui"], "ai_lang": T["ai_lang"],
          "price": T["price_kb"], "price_factors": [f"{t}: {d}" for t, d in D.PRICE_FACTORS], "promises": [f"{t}: {d}" for t, d in D.PROMISES],
          "materials": [m[1] for m in D.MATERIALS], "steps": [f"{t}: {d}" for t, d in D.STEPS],
          "districts": [d["name"] for d in D.DISTRICTS], "services": services, "faq": faq}
    txt = json.dumps(kb, ensure_ascii=False, separators=(",", ":"))
    name = "kb.json" if LANG == "ru" else "kb-kk.json"
    (DIST / name).write_text(txt, encoding="utf-8")
    (ROOT / "api").mkdir(exist_ok=True); (ROOT / "api" / name).write_text(txt, encoding="utf-8")

def build_llms():
    L = [f"# {S['brand']} — {D.TAGLINE.lower()}, {S['city']}", "", f"> {D.ABOUT}", "", f"Қазақша нұсқа: {BASE}/kz/", "",
         "## Контакты", f"- Телефон: {S['phone_display']}", f"- WhatsApp: https://wa.me/{S['wa']}", f"- График: {S['hours_text']}",
         f"- Город: {S['city']}, все районы", f"- Сайт: {BASE}/", "", "## Услуги"]
    for c in CATS:
        L.append(f"- [{c['h1']}]({url_of(cat_path(c))}): {c['lead']}")
        for w in c["works"]: L.append(f"  - [{w['h1']}]({url_of(work_path(c, w))}): {w['lead']}")
    L += ["", "## Как работаем"] + [f"- {t}: {d}" for t, d in D.STEPS]
    L += ["", "## Гарантии"] + [f"- {t}: {d}" for t, d in D.PROMISES]
    L += ["", "## Цены", f"- [Стоимость]({url_of('/ceny/')}): на сайте не указана, считается после замера и 3D-проекта. Зависит от: " + "; ".join(f"{t.lower()} ({d.lower()})" for t, d in D.PRICE_FACTORS) + "."]
    L += ["", "## Районы", "- " + ", ".join(f"[{d['name']}]({url_of('/rayony/' + d['slug'] + '/')})" for d in D.DISTRICTS)]
    L += ["", "## Частые вопросы"] + [f"- {q} {a}" for q, a in D.FAQ_MAIN]
    L += ["", "## Статьи"] + [f"- [{a['h1']}]({url_of('/stati/' + a['slug'] + '/')})" for a in D.ARTICLES]
    (DIST / "llms.txt").write_text("\n".join(L) + "\n", encoding="utf-8")

def build_misc():
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in SITEMAP:
        ru_p = (p[3:] or "/") if p.startswith("/kz") else p
        pr = "1.0" if ru_p == "/" else ("0.8" if ru_p.count("/") == 2 else "0.6")
        sm.append(f'<url><loc>{url_of(p)}</loc><lastmod>2026-11-10</lastmod><priority>{pr}</priority>'
                  f'<xhtml:link rel="alternate" hreflang="ru-KZ" href="{url_of(ru_p)}"/><xhtml:link rel="alternate" hreflang="kk-KZ" href="{url_of("/kz" + ru_p)}"/></url>')
    (DIST / "sitemap.xml").write_text("\n".join(sm + ["</urlset>"]) + "\n", encoding="utf-8")
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "anthropic-ai", "PerplexityBot", "Perplexity-User",
            "Google-Extended", "Googlebot", "Applebot", "Applebot-Extended", "Bingbot", "YandexBot", "DuckDuckBot", "CCBot", "meta-externalagent", "Amazonbot", "cohere-ai", "MistralAI-User"]
    rb = ["User-agent: *", "Allow: /", "Disallow: /api/", ""] + sum([[f"User-agent: {b}", "Allow: /", ""] for b in bots], []) + [f"Sitemap: {BASE}/sitemap.xml", ""]
    (DIST / "robots.txt").write_text("\n".join(rb), encoding="utf-8")
    man = {"name": f"{S['brand']} — {D_RU.TAGLINE.lower()}", "short_name": S["brand"], "lang": "ru", "start_url": "/", "display": "standalone",
           "background_color": "#F3EFE9", "theme_color": S["theme_color"],
           "icons": [{"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
                     {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
                     {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
    (DIST / "site.webmanifest").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")

def copy_assets():
    shutil.copytree(ASSETS, DIST / "assets", dirs_exist_ok=True, ignore=shutil.ignore_patterns("icons", "orig"))
    shutil.copy(SRC / "app.js", DIST / "assets" / "app.js")
    for f in ("favicon.ico", "apple-touch-icon.png"):
        if (ASSETS / f).exists(): shutil.copy(ASSETS / f, DIST / f)

def use_lang(code, data, t, pfx):
    global D, T, PFX, LANG, S, CATS
    D, T, PFX, LANG, S, CATS = data, t, pfx, code, data.SITE, data.CATEGORIES

def main():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(); copy_assets()
    for code, data, t, pfx in LANGS:
        use_lang(code, data, t, pfx)
        build_home()
        for c in CATS:
            build_category(c)
            for w in c["works"]: build_work(c, w)
        build_districts(); build_prices(); build_articles(); build_contacts(); build_privacy(); build_404()
        build_kb()
    use_lang(*LANGS[0])
    build_llms(); build_misc()
    print(f"OK: {len(SITEMAP)} страниц (ru + kk) в sitemap + 404 → {DIST}")

if __name__ == "__main__":
    main()
