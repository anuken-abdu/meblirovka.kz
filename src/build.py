# -*- coding: utf-8 -*-
"""Генератор сайта. Запуск: python3 src/build.py  →  dist/
Только стандартная библиотека Python — собирается на Vercel без зависимостей."""
import html, json, re, shutil, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"
sys.path.insert(0, str(SRC))
import data as D  # noqa: E402

S = D.SITE
BASE = f"https://www.{S['domain']}"
VER = "2"
ICON_DIR = ASSETS / "icons"
CATS = D.CATEGORIES

# ── утилиты ─────────────────────────────────────────────────────────────────
def esc(s): return html.escape(str(s), quote=True)

NB_RE = re.compile(r"(?<![\wА-Яа-яЁё])([А-Яа-яЁёA-Za-z]{1,2})\s+")
def nb(s):
    """Неразрывные пробелы после коротких слов и перед тире + экранирование."""
    s = esc(s)
    s = NB_RE.sub(lambda m: m.group(1) + "\u00a0", s)
    s = re.sub(r"\s+—", "\u00a0—", s)
    s = re.sub(r"(\d)\s+(м²|м|см|кг)", "\\1\u00a0\\2", s)
    return s

_icons = {}
def icon(name, cls="i"):
    if name not in _icons:
        svg = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
        _icons[name] = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", svg.strip())
    return f'<svg class="{cls}" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true" focusable="false">{_icons[name]}</svg>'

def wa_url(text): return f"https://wa.me/{S['wa']}?text={urllib.parse.quote(text)}"
def tel_attrs():
    return f'href="tel:{S["phone_tel"]}" onclick="return gtag_report_conversion(&#39;tel:{S["phone_tel"]}&#39;)"'
def wa_attrs(text):
    return f'href="{esc(wa_url(text))}" target="_blank" rel="noopener" onclick="gtag_report_conversion()"'

def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>~])\s*", r"\1", css)
    css = re.sub(r"\s*:\s*", ":", css)
    return css.replace(";}", "}").replace(" and(", " and (").strip()

def url_of(p): return f"{BASE}{p}"
def cat_path(c): return f"/{c['slug']}/"
def work_path(c, w): return f"/{c['slug']}/{w['slug']}/"
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
    return {
        "@type": "FurnitureStore", "@id": f"{BASE}/#org", "name": S["brand"],
        "description": f"{D.TAGLINE} {S['city_in']}. {D.ABOUT}",
        "url": f"{BASE}/", "telephone": S["phone_tel"],
        "logo": f"{BASE}/assets/logo.svg", "image": f"{BASE}/assets/og.png",
        "address": {"@type": "PostalAddress", "addressLocality": S["city"], "addressCountry": "KZ",
                    **({"streetAddress": S["address"]} if S["address"] else {})},
        "areaServed": {"@type": "City", "name": S["city"]},
        "openingHours": S["hours_ld"],
        "makesOffer": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": c["h1"], "url": url_of(cat_path(c))}} for c in CATS],
    }
def crumbs_ld(cr): return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": url_of(p)} for i, (n, p) in enumerate(cr)]}
def faq_ld(faq): return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
def service_ld(name, desc, p):
    return {"@type": "Service", "name": name, "description": desc, "url": url_of(p), "provider": {"@id": f"{BASE}/#org"},
            "areaServed": {"@type": "City", "name": S["city"]}, "serviceType": "Меблировка квартир и мебель на заказ"}

# ── шапка, меню, подвал ─────────────────────────────────────────────────────
def logo_img(light=False):
    L = D.LOGO; f = "logo-light.svg" if light else "logo.svg"
    return f'<img class="logo-img" src="/assets/{f}?v={VER}" width="{L["w"]}" height="{L["h"]}" alt="{esc(S["brand"])}">'

def nav_html():
    cols = []
    for c in CATS:
        items = "".join(f'<li><a href="{work_path(c, w)}">{esc(w["name"])}</a></li>' for w in c["works"])
        cols.append(f'<div class="dd-col{' dd-wide' if len(c['works']) > 3 else ''}"><a class="dd-cat" href="{cat_path(c)}">{esc(c["name"])}</a><ul>{items}</ul></div>')
    return f"""<nav class="nav" aria-label="Основное меню"><ul class="nav-list">
<li class="has-dd"><a href="/#uslugi" class="nav-link" aria-haspopup="true">Услуги{icon("caret-down", "i i-s")}</a><div class="dd">{''.join(cols)}</div></li>
<li><a class="nav-link" href="/#process">Как работаем</a></li>
<li><a class="nav-link" href="/ceny/">Цены</a></li>
<li><a class="nav-link" href="/stati/">Статьи</a></li>
<li><a class="nav-link" href="/kontakty/">Контакты</a></li>
</ul></nav>"""

def mobile_menu(wa_text):
    groups = "".join(
        f'<li><a class="mm-cat" href="{cat_path(c)}">{esc(c["name"])}</a><ul>' +
        "".join(f'<li><a href="{work_path(c, w)}">{esc(w["name"])}</a></li>' for w in c["works"]) + "</ul></li>" for c in CATS)
    return f"""<div class="mm" id="mm" hidden><div class="mm-panel" role="dialog" aria-modal="true" aria-label="Меню">
<div class="mm-top"><span class="mm-title">Меню</span><button class="icon-btn mm-close" type="button" aria-label="Закрыть меню">{icon("x")}</button></div>
<ul class="mm-list">{groups}
<li><a class="mm-link" href="/#process">Как работаем</a></li><li><a class="mm-link" href="/ceny/">Цены</a></li>
<li><a class="mm-link" href="/rayony/">Районы</a></li><li><a class="mm-link" href="/stati/">Статьи</a></li><li><a class="mm-link" href="/kontakty/">Контакты</a></li></ul>
<div class="mm-cta"><a class="btn btn-dark" {tel_attrs()}>{icon("phone")}Позвонить</a><a class="btn btn-wa" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}WhatsApp</a></div>
</div></div>"""

def header_html(wa_text):
    return f"""<header class="hdr"><div class="wrap hdr-in">
<a class="logo" href="/" aria-label="{esc(S['brand'])} — на главную">{logo_img()}</a>
{nav_html()}
<div class="hdr-cta">
<a class="hdr-phone" {tel_attrs()} aria-label="Позвонить {esc(S['phone_display'])}">{icon("phone")}<span>{esc(S['phone_display'])}</span></a>
<a class="btn btn-wa btn-sm hdr-wa" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}WhatsApp</a>
<button class="icon-btn burger" type="button" aria-label="Открыть меню" aria-expanded="false" aria-controls="mm">{icon("list")}</button>
</div></div></header>"""

def footer_html():
    cats = "".join(f'<li><a href="{cat_path(c)}">{esc(c["name"])}</a></li>' for c in CATS)
    return f"""<footer class="ftr"><div class="wrap">
<div class="ftr-top"><a class="logo" href="/" aria-label="{esc(S['brand'])} — на главную">{logo_img(True)}</a>
<p class="ftr-claim">{nb(D.STATEMENT)}</p></div>
<div class="ftr-grid">
<div><p class="ftr-h">Услуги</p><ul>{cats}</ul></div>
<div><p class="ftr-h">Компания</p><ul><li><a href="/#process">Как работаем</a></li><li><a href="/ceny/">Цены</a></li><li><a href="/rayony/">Районы</a></li><li><a href="/stati/">Статьи</a></li></ul></div>
<div><p class="ftr-h">Связь</p><ul><li><a {tel_attrs()}>{esc(S['phone_display'])}</a></li><li><a {wa_attrs("Здравствуйте! Нужна меблировка квартиры")}>WhatsApp</a></li><li>{esc(S['hours_text'])}</li><li>{esc(S['city'])}</li></ul></div>
</div>
<div class="ftr-bottom"><span>© {esc(S['brand'])}</span><a href="/politika/">Политика конфиденциальности</a><a href="https://www.anuken.kz" target="_blank" rel="noopener">Разработка и продвижение Anuken.kz</a></div>
</div></footer>"""

def floating_html(wa_text):
    return f"""<div class="mbar"><a class="btn btn-dark" {tel_attrs()}>{icon("phone")}Позвонить</a><a class="btn btn-wa" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}WhatsApp</a></div>
<button class="fbtn fbtn-top" type="button" aria-label="Наверх" hidden>{icon("arrow-up")}</button>
<button class="fbtn fbtn-chat" type="button" aria-label="ИИ-консультант">{icon("chat-circle-dots")}</button>"""

def crumbs_html(cr):
    items = "".join(f'<li aria-current="page">{esc(n)}</li>' if i == len(cr) - 1 else f'<li><a href="{p}">{esc(n)}</a></li>' for i, (n, p) in enumerate(cr))
    return (f'<div class="wrap crumbs-row"><button class="back" type="button" aria-label="Назад">{icon("arrow-left", "i i-s")}Назад</button>'
            f'<nav class="crumbs" aria-label="Хлебные крошки"><ol>{items}</ol></nav></div>')

SITEMAP = []
def page(path, title, desc, body, *, crumbs=None, ld=None, wa_text=None, noindex=False, og_type="website", preload_img=None):
    wa_text = wa_text or "Здравствуйте! Нужна меблировка квартиры"
    graph = [org_ld(), {"@type": "WebSite", "@id": f"{BASE}/#site", "url": f"{BASE}/", "name": S["brand"], "inLanguage": "ru-KZ", "publisher": {"@id": f"{BASE}/#org"}}]
    if crumbs: graph.append(crumbs_ld(crumbs))
    graph += (ld or [])
    ldjson = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    canon = url_of(path)
    lat, lon = S["geo_position"].split(";")
    pre = f'\n<link rel="preload" as="image" href="{preload_img[0]}" imagesrcset="{preload_img[1]}" imagesizes="{preload_img[2]}" fetchpriority="high">' if preload_img else ""
    doc = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
{head_tags()}
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{"" if noindex else f'<link rel="canonical" href="{canon}">'}
<meta name="robots" content="{"noindex,follow" if noindex else "index,follow,max-image-preview:large"}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(S['brand'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{BASE}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="ru_KZ">
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
<link rel="preload" href="/assets/fonts/manrope-cyrillic-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/cormorant-garamond-cyrillic-500-normal.woff2" as="font" type="font/woff2" crossorigin>{pre}
<style>{CSS}</style>
<script type="application/ld+json">{ldjson}</script>
</head>
<body>
{body_tags()}
<a class="skip" href="#main">К содержимому</a>
{header_html(wa_text)}
{mobile_menu(wa_text)}
<main id="main">
{crumbs_html(crumbs) if crumbs else ''}
{body}
</main>
{footer_html()}
{floating_html(wa_text)}
<script src="/assets/app.js?v={VER}" defer></script>
</body>
</html>
"""
    out = DIST / "404.html" if path == "/404" else DIST / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    if not noindex: SITEMAP.append(path)

# ── блоки ───────────────────────────────────────────────────────────────────
def sec_head(title, sub=None, hid=None):
    i = f' id="{hid}"' if hid else ""
    s = f'<p class="sec-sub">{nb(sub)}</p>' if sub else ""
    return f'<div class="sec-head"><h2{i}>{nb(title)}</h2>{s}</div>'

def cta_buttons(wa_text):
    return (f'<div class="cta-row"><a class="btn btn-dark btn-lg" {tel_attrs()}>{icon("phone")}Позвонить</a>'
            f'<a class="btn btn-wa btn-lg" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}Написать в WhatsApp</a></div>')

def photo(key, sizes):
    """<img> из assets/img/<key>-*.webp или '' если фото ещё нет. Возвращает (html, preload)."""
    if key not in D.PHOTOS or not (ASSETS / "img" / f"{key}-800.webp").exists(): return "", None
    ws = [w for w in (480, 800, 1200) if (ASSETS / "img" / f"{key}-{w}.webp").exists()]
    srcset = ", ".join(f"/assets/img/{key}-{w}.webp {w}w" for w in ws)
    src = f"/assets/img/{key}-800.webp"
    return (f'<img src="{src}" srcset="{srcset}" sizes="{sizes}" width="800" height="1000" alt="{esc(D.PHOTOS[key])}" fetchpriority="high" decoding="async">',
            (src, srcset, sizes))

def work_photo(w, sizes):
    key = w["slug"]
    if not (ASSETS / "img" / f"{key}-800.webp").exists(): return "", None
    ws = [x for x in (480, 800, 1200) if (ASSETS / "img" / f"{key}-{x}.webp").exists()]
    srcset = ", ".join(f"/assets/img/{key}-{x}.webp {x}w" for x in ws)
    return (f'<img src="/assets/img/{key}-800.webp" srcset="{srcset}" sizes="{sizes}" width="800" height="1000" alt="{esc(w["name"])} на заказ" loading="lazy" decoding="async">',
            (f"/assets/img/{key}-800.webp", srcset, sizes))

def wd_grid(c):
    """«Что делаем»: сетка направлений, фото или линейная иконка."""
    items = []
    for w in c["works"]:
        img, _ = work_photo(w, "(min-width:1024px) 30vw, (min-width:600px) 45vw, 100vw")
        vis = f'<span class="wd-ph">{img}</span>' if img else f'<span class="wd-ic">{icon(w["icon"], "i")}</span>'
        items.append(f'<li><a class="wd{" wd-p" if img else ""}" href="{work_path(c, w)}">{vis}<h3>{esc(w["name"])}</h3><p>{nb(w["card"])}</p></a></li>')
    return '<ul class="wds">' + "".join(items) + "</ul>"

def hero(h1_html, lead, wa_text, visual="", cls=""):
    vis = f'<div class="hero-vis">{visual}</div>' if visual else ""
    return f"""<section class="hero {cls}{' hero-2' if visual else ''}"><div class="wrap hero-grid">
<div class="hero-txt"><h1>{h1_html}</h1><p class="lead">{nb(lead)}</p>{cta_buttons(wa_text)}</div>{vis}
</div></section>"""

def spec_list(items):
    return '<ul class="spec">' + "".join(f"<li>{nb(x)}</li>" for x in items) + "</ul>"

def svc_rows(cats=CATS):
    rows = []
    for c in cats:
        ws = c["works"] if len(c["works"]) <= 3 else c["works"][:4]
        works = "".join(f'<li><a href="{work_path(c, w)}">{esc(w["name"])}</a></li>' for w in ws)
        if len(c["works"]) > 3: works += f'<li><a href="{cat_path(c)}">Все направления</a></li>'
        rows.append(f'<li class="svc"><h3><a href="{cat_path(c)}">{esc(c["name"])}{icon("arrow-up-right", "i svc-arr")}</a></h3>'
                    f'<p>{nb(c["card"])}</p><ul class="svc-works">{works}</ul></li>')
    return '<ul class="svcs">' + "".join(rows) + "</ul>"

def link_rows(items):
    """items: [(title, href, text|None)] — строки-ссылки с волосяными линиями."""
    out = []
    for t, h, d in items:
        dd = f'<span class="lr-d">{nb(d)}</span>' if d else ""
        out.append(f'<li><a class="lr" href="{h}"><span class="lr-t">{esc(t)}</span>{dd}{icon("arrow-right", "i lr-a")}</a></li>')
    return '<ul class="lrs">' + "".join(out) + "</ul>"

def steps_html(title="Как мы работаем", hid="process"):
    rows = "".join(f'<li><h3>{nb(t)}</h3><p>{nb(d)}</p></li>' for t, d in D.STEPS)
    return f'<section class="sec" id="{hid}"><div class="wrap">{sec_head(title, "Один исполнитель от замера до сервиса после сдачи")}<ol class="steps">{rows}</ol></div></section>'

def factors_html(factors=None, title="От чего зависит стоимость"):
    if factors:
        body = spec_list(factors)
    else:
        body = '<dl class="facts">' + "".join(f"<div><dt>{nb(t)}</dt><dd>{nb(d)}</dd></div>" for t, d in D.PRICE_FACTORS) + "</dl>"
    return (f'<section class="sec sec-alt"><div class="wrap">{sec_head(title, "Точную стоимость считаем после замера и 3D-проекта. Ориентир — по планировке в WhatsApp.")}'
            f'{body}</div></section>')

def faq_html(faq, title="Вопросы"):
    items = "".join(f'<details class="faq-i"><summary><h3>{nb(q)}</h3>{icon("caret-down", "i faq-c")}</summary><p>{nb(a)}</p></details>' for q, a in faq)
    return f'<section class="sec"><div class="wrap faq-wrap">{sec_head(title)}<div class="faq">{items}</div></div></section>'

def promises_html():
    items = "".join(f'<li><h3>{nb(t)}</h3><p>{nb(d)}</p></li>' for t, d in D.PROMISES)
    return f'<section class="sec sec-dark"><div class="wrap">{sec_head("За что мы отвечаем")}<ul class="proms">{items}</ul></div></section>'

def materials_html():
    sw = "".join(f'<li><span class="sw {cls}" aria-hidden="true"></span><span class="sw-n">{esc(n)}</span></li>' for cls, n in D.MATERIALS)
    return (f'<section class="sec"><div class="wrap mat">{sec_head("Отбор материалов", "Корпус, фасады, столешницы и фурнитуру подбираем под задачу, нагрузку и бюджет — и показываем в 3D-проекте до изготовления.")}'
            f'<ul class="sws">{sw}</ul></div></section>')

def intro_html(text):
    return f'<section class="sec sec-intro"><div class="wrap"><p class="intro">{nb(text)}</p></div></section>'

def form_html(selected=""):
    opts = ['<option value="">Выберите</option>']
    for c in CATS:
        for w in c["works"]:
            sel = " selected" if selected == f'{c["slug"]}/{w["slug"]}' else ""
            opts.append(f'<option{sel}>{esc(c["name"] + ": " + w["name"])}</option>')
    opts.append("<option>Меблировка под ключ целиком</option>")
    dis = '<option value="">Выберите</option>' + "".join(f'<option>{esc(d["name"])}</option>' for d in D.DISTRICTS)
    return f"""<section class="sec sec-form" id="zayavka" aria-labelledby="form-h"><div class="wrap form-grid">
<div class="form-txt"><h2 id="form-h">{nb("Обсудим вашу квартиру")}</h2>
<p>{nb("Опишите задачу — откроется WhatsApp с готовым текстом. Приложите планировку или фото, и мы предложим время замера.")}</p>
<p class="form-alt">Или позвоните: <a {tel_attrs()}>{esc(S['phone_display'])}</a></p></div>
<form class="form" novalidate>
<div class="f-row"><label for="f-work">Что нужно</label><select id="f-work" name="work">{''.join(opts)}</select></div>
<div class="f-row"><label for="f-dis">Район</label><select id="f-dis" name="district">{dis}</select></div>
<div class="f-row f-wide"><label for="f-msg">Описание</label><textarea id="f-msg" name="msg" rows="3" placeholder="Например: двухкомнатная квартира в новостройке, кухня и шкафы"></textarea></div>
<div class="f-row"><label for="f-name">Имя</label><input id="f-name" name="name" autocomplete="name"></div>
<div class="f-row"><label for="f-phone">Телефон *</label><input id="f-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required placeholder="+7 7__ ___ __ __" aria-describedby="f-err"></div>
<p class="f-err" id="f-err" role="alert"></p>
<button class="btn btn-light btn-lg f-wide" type="submit">{icon("whatsapp-logo")}Отправить в WhatsApp</button>
<p class="f-note f-wide">Отправляя заявку, вы соглашаетесь с <a href="/politika/">политикой конфиденциальности</a>.</p>
</form></div></section>"""

def accent_h1(text):
    """Курсивный акцент на «под ключ» / «на заказ» в заголовке первого экрана."""
    t = nb(text)
    for k in ("под ключ", "на заказ", "под\u00a0ключ", "на\u00a0заказ"):
        if k in t: return t.replace(k, f"<em>{k}</em>", 1)
    return t

# ── страницы ────────────────────────────────────────────────────────────────
def build_home():
    img, pre = photo("home", "(min-width:1024px) 46vw, calc(100vw - 40px)")
    visual = img or f'<div class="plan-wrap" aria-hidden="true">{PLAN_SVG}</div>'
    body = hero(accent_h1(f"Меблировка квартир под ключ {S['city_in']}"), D.ABOUT,
                "Здравствуйте! Нужна меблировка квартиры под ключ", visual, "hero-home")
    mz = CATS[0]
    body += f'<section class="sec" id="chto-delaem"><div class="wrap">{sec_head("Что делаем", "Корпусная мебель любой сложности по размерам вашей квартиры. Выберите направление — ответим в WhatsApp.")}{wd_grid(mz)}</div></section>'
    body += f'<section class="sec sec-statement"><div class="wrap"><p class="statement">{nb(D.STATEMENT)}</p></div></section>'
    body += f'<section class="sec" id="uslugi"><div class="wrap">{sec_head("Услуги", "Мебель на заказ и меблировка целиком — или только то, что нужно")}{svc_rows()}</div></section>'
    body += steps_html()
    body += materials_html()
    body += promises_html()
    body += faq_html(D.FAQ_MAIN)
    body += form_html()
    page("/", f"Меблировка квартир под ключ {S['city_in']} | {S['brand']}",
         f"Меблировка квартир под ключ {S['city_in']}: 3D-проект, мебель на заказ, замер, монтаж, техника и текстиль. Гарантия и сервис.",
         body, ld=[faq_ld(D.FAQ_MAIN)], wa_text="Здравствуйте! Нужна меблировка квартиры под ключ", preload_img=pre)

def build_category(c):
    p = cat_path(c); cr = [("Главная", "/"), (c["name"], p)]
    img, pre = photo(c["slug"], "(min-width:1024px) 46vw, calc(100vw - 40px)")
    body = hero(accent_h1(c["h1"]), c["lead"], c["wa_text"], img)
    body += intro_html(c["intro"])
    body += f'<section class="sec"><div class="wrap split">{sec_head("Что входит")}{spec_list(c["includes"])}</div></section>'
    body += f'<section class="sec"><div class="wrap">{sec_head("Что делаем" if len(c["works"]) > 3 else "Направления")}{wd_grid(c) if len(c["works"]) > 3 else link_rows([(w["name"], work_path(c, w), ", ".join(w["includes"][:3])) for w in c["works"]])}</div></section>'
    body += steps_html()
    body += factors_html(c["factors"])
    body += faq_html(c["faq"])
    body += form_html()
    page(p, c["title"], c["desc"], body, crumbs=cr, wa_text=c["wa_text"], preload_img=pre,
         ld=[service_ld(c["h1"], c["desc"], p), faq_ld(c["faq"])])

def build_work(c, w):
    p = work_path(c, w); cr = [("Главная", "/"), (c["name"], cat_path(c)), (w["name"], p)]
    img, pre = work_photo(w, "(min-width:1024px) 46vw, calc(100vw - 40px)")
    body = hero(accent_h1(w["h1"]), w["lead"], w["wa_text"], img.replace(' loading="lazy"', ' fetchpriority="high"'))
    body += f'<section class="sec"><div class="wrap split">{sec_head("Что входит")}{spec_list(w["includes"])}</div></section>'
    body += steps_html()
    body += factors_html(c["factors"])
    body += faq_html(w["faq"])
    rel = [(x["name"], work_path(c, x), None) for x in c["works"] if x is not w] + [(x["name"], cat_path(x), None) for x in CATS if x is not c]
    body += f'<section class="sec"><div class="wrap">{sec_head("Смотрите также")}{link_rows(rel)}</div></section>'
    body += form_html(f'{c["slug"]}/{w["slug"]}')
    page(p, w["title"], w["desc"], body, crumbs=cr, wa_text=w["wa_text"], preload_img=pre, ld=[service_ld(w["h1"], w["desc"], p), faq_ld(w["faq"])])

def build_districts():
    p = "/rayony/"; cr = [("Главная", "/"), ("Районы", p)]
    body = hero(nb(f"Меблировка квартир по районам {S['city_gen']}"),
                f"Работаем во всех районах {S['city_gen']}: выезжаем на замер, изготавливаем мебель, привозим и монтируем на месте.",
                "Здравствуйте! Нужна меблировка квартиры")
    body += f'<section class="sec"><div class="wrap">{link_rows([(d["name"], "/rayony/" + d["slug"] + "/", d["note"]) for d in D.DISTRICTS])}</div></section>'
    body += f'<section class="sec"><div class="wrap">{sec_head("Услуги")}{svc_rows()}</div></section>'
    body += form_html()
    page(p, f"Меблировка квартир по районам {S['city_gen']} | {S['brand']}",
         f"Меблировка квартир и мебель на заказ во всех районах {S['city_gen']}: " + ", ".join(d["name"] for d in D.DISTRICTS) + ".", body, crumbs=cr)
    for d in D.DISTRICTS:
        dp = f"/rayony/{d['slug']}/"; crd = [("Главная", "/"), ("Районы", p), (d["name"], dp)]
        wa = f"Здравствуйте! Нужна меблировка квартиры, район {d['name']}"
        faq = [(f"Работаете {d['in']}?", f"Да, выезжаем на замер и монтаж {d['in']} {S['city_gen']}."),
               ("Можно меблировать квартиру удалённо?", "Да, 3D-проект согласуем в WhatsApp, ход работ показываем на фото."),
               ("Как узнать стоимость?", "Пришлите планировку в WhatsApp — назовём ориентир, точную стоимость — после замера.")]
        body = hero(accent_h1(f"Меблировка квартир {d['in']} {S['city_gen']}"),
                    f"Мебель на заказ и меблировка под ключ {d['in']} {S['city_gen']}: замер, 3D-проект, изготовление, монтаж, наполнение. {d['note']}", wa)
        body += f'<section class="sec"><div class="wrap">{sec_head("Услуги")}{svc_rows()}</div></section>'
        body += steps_html()
        body += faq_html(faq)
        body += f'<section class="sec"><div class="wrap">{sec_head("Другие районы")}{link_rows([(x["name"], "/rayony/" + x["slug"] + "/", None) for x in D.DISTRICTS if x is not d])}</div></section>'
        body += form_html()
        page(dp, f"Меблировка квартир {d['in']} {S['city_gen']} | {S['brand']}",
             f"Мебель на заказ и меблировка квартир под ключ {d['in']} {S['city_gen']}: замер, 3D-проект, изготовление, монтаж.",
             body, crumbs=crd, wa_text=wa, ld=[faq_ld(faq)])

def build_prices():
    p = "/ceny/"; cr = [("Главная", "/"), ("Цены", p)]
    faq = [D.FAQ_MAIN[1],
           ("Почему на сайте нет цен?", "Мебель изготавливается под конкретную квартиру: размеры, материалы и фурнитура у каждого проекта свои. Цифра без них была бы неточной."),
           ("Можно уложиться в бюджет?", "Да. Назовите сумму — подберём материалы и состав работ под неё и покажем варианты в 3D-проекте.")]
    body = hero(accent_h1(f"Стоимость меблировки квартир {S['city_in']}"),
                "Стоимость зависит от объёма мебели, материалов, фурнитуры и наполнения квартиры. Ориентир назовём по планировке, точную цену — после замера и 3D-проекта.",
                "Здравствуйте! Хочу узнать стоимость меблировки квартиры")
    body += factors_html()
    body += steps_html()
    body += faq_html(faq)
    body += form_html()
    page(p, f"Стоимость меблировки квартир {S['city_in']} | {S['brand']}",
         f"От чего зависит стоимость меблировки и мебели на заказ {S['city_in']}. Ориентир по планировке, точная цена после замера и 3D-проекта.",
         body, crumbs=cr, ld=[faq_ld(faq)], wa_text="Здравствуйте! Хочу узнать стоимость меблировки квартиры")

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
def build_articles():
    p = "/stati/"; cr = [("Главная", "/"), ("Статьи", p)]
    body = hero(nb("Статьи о меблировке квартир"), "Коротко о том, что стоит знать до замера: стоимость, этапы, новостройки и квартиры под аренду.",
                "Здравствуйте! Есть вопрос по меблировке квартиры")
    body += f'<section class="sec"><div class="wrap">{link_rows([(a["name"], "/stati/" + a["slug"] + "/", a["lead"]) for a in D.ARTICLES])}</div></section>'
    page(p, f"Статьи о меблировке квартир | {S['brand']}", "Статьи о меблировке квартир и мебели на заказ: стоимость, этапы, новостройки, квартиры под аренду.", body, crumbs=cr)
    for a in D.ARTICLES:
        ap = f"/stati/{a['slug']}/"; cra = [("Главная", "/"), ("Статьи", p), (a["name"], ap)]
        parts = "".join(f"<h2>{nb(v)}</h2>" if k == "h2" else f"<p>{nb(v)}</p>" for k, v in a["blocks"])
        rel = []
        for key in a["related"]:
            path, obj = find_by_key(key); rel.append((obj["name"], path, None))
        y, m, dd = a["date"].split("-")
        body = f"""<article class="sec art"><div class="wrap narrow">
<p class="art-date"><time datetime="{a['date']}">{int(dd)} {MONTHS[int(m) - 1]} {y}</time></p>
<h1>{nb(a['h1'])}</h1><p class="lead">{nb(a['lead'])}</p>{parts}
<div class="art-cta"><p>{nb('Пришлите планировку квартиры — подскажем решения и ориентир по стоимости.')}</p>{cta_buttons('Здравствуйте! Прочитал статью «' + a['name'] + '», есть вопрос')}</div>
</div></article>
<section class="sec"><div class="wrap">{sec_head('Услуги по теме')}{link_rows(rel)}</div></section>"""
        art_ld = {"@type": "Article", "headline": a["h1"], "description": a["desc"], "datePublished": a["date"], "dateModified": a["date"],
                  "mainEntityOfPage": url_of(ap), "image": f"{BASE}/assets/og.png", "inLanguage": "ru-KZ",
                  "author": {"@id": f"{BASE}/#org"}, "publisher": {"@id": f"{BASE}/#org"}}
        page(ap, a["title"], a["desc"], body, crumbs=cra, ld=[art_ld], og_type="article")

def build_contacts():
    p = "/kontakty/"; cr = [("Главная", "/"), ("Контакты", p)]
    rows = [("Телефон", f'<a {tel_attrs()}>{esc(S["phone_display"])}</a>'),
            ("WhatsApp", f'<a {wa_attrs("Здравствуйте! Нужна меблировка квартиры")}>Написать</a>'),
            ("График", esc(S["hours_text"])),
            ("Город", esc(S["city"]) + (", " + esc(S["address"]) if S["address"] else ", выезд на замер по всем районам"))]
    if S["email"]: rows.insert(2, ("Почта", f'<a href="mailto:{esc(S["email"])}">{esc(S["email"])}</a>'))
    dl = '<dl class="facts contacts">' + "".join(f"<div><dt>{l}</dt><dd>{v}</dd></div>" for l, v in rows) + "</dl>"
    body = f'<section class="hero"><div class="wrap"><h1>Контакты</h1><p class="lead">{nb("Быстрее всего — написать в WhatsApp и приложить планировку или фото квартиры.")}</p></div></section>'
    body += f'<section class="sec"><div class="wrap">{dl}</div></section>' + form_html()
    page(p, f"Контакты | {S['brand']} — меблировка квартир {S['city_in']}"[:60],
         f"Телефон и WhatsApp {S['brand']}: мебель на заказ и меблировка квартир под ключ {S['city_in']}. {S['hours_text']}.", body, crumbs=cr)

def build_privacy():
    p = "/politika/"; cr = [("Главная", "/"), ("Политика конфиденциальности", p)]
    paras = [
        ("Какие данные мы получаем", f"Имя, телефон, район и описание задачи, которые вы указываете в форме заявки или в чате на сайте {S['domain']}."),
        ("Как это происходит", "Форма не отправляет данные на сервер: она открывает WhatsApp с готовым текстом, и вы сами решаете, отправлять ли сообщение. Сообщения ИИ-консультанту обрабатываются только для ответа."),
        ("Зачем", "Чтобы ответить на заявку, договориться о замере и рассчитать стоимость."),
        ("Аналитика", "Сайт может использовать сервисы Google для подсчёта обращений. Они работают с обезличенными данными о посещениях и нажатиях."),
        ("Передача третьим лицам", "Мы не продаём и не передаём ваши данные третьим лицам, кроме случаев, предусмотренных законодательством Республики Казахстан."),
        ("Удаление данных", "Чтобы удалить переписку и данные, напишите нам в WhatsApp."),
    ]
    body = '<section class="sec art"><div class="wrap narrow"><h1>Политика конфиденциальности</h1>' + "".join(f"<h2>{nb(h)}</h2><p>{nb(t)}</p>" for h, t in paras) + "</div></section>"
    page(p, f"Политика конфиденциальности | {S['brand']}", f"Как сайт {S['brand']} обрабатывает данные из формы заявки и чата.", body, crumbs=cr)

def build_404():
    body = f"""<section class="hero"><div class="wrap"><h1>Страница не найдена</h1>
<p class="lead">{nb("Возможно, адрес изменился. Перейдите на главную или напишите нам.")}</p>
<div class="cta-row"><a class="btn btn-dark btn-lg" href="/">{icon("house")}На главную</a><a class="btn btn-wa btn-lg" {wa_attrs("Здравствуйте! Нужна меблировка квартиры")}>{icon("whatsapp-logo")}Написать в WhatsApp</a></div></div></section>"""
    page("/404", f"Страница не найдена | {S['brand']}", "Страница не найдена.", body, noindex=True)

# ── служебные файлы ─────────────────────────────────────────────────────────
def build_kb():
    services, faq = [], [{"q": q, "a": a, "url": url_of("/")} for q, a in D.FAQ_MAIN]
    for c in CATS:
        services.append({"name": c["h1"], "short": c["name"], "url": url_of(cat_path(c)), "lead": c["lead"], "includes": c["includes"], "wa": c["wa_text"]})
        faq += [{"q": q, "a": a, "url": url_of(cat_path(c))} for q, a in c["faq"]]
        for w in c["works"]:
            services.append({"name": w["h1"], "short": w["name"], "url": url_of(work_path(c, w)), "lead": w["lead"], "includes": w["includes"], "wa": w["wa_text"]})
            faq += [{"q": q, "a": a, "url": url_of(work_path(c, w))} for q, a in w["faq"]]
    kb = {"brand": S["brand"], "city": S["city"], "city_gen": S["city_gen"], "city_in": S["city_in"], "phone": S["phone_display"], "tel": S["phone_tel"],
          "wa": S["wa"], "hours": S["hours_text"], "tagline": D.TAGLINE, "greeting": D.CHAT_GREETING, "about": D.ABOUT,
          "price": "Цены на сайте не указаны: стоимость считаем после замера и 3D-проекта, она зависит от объёма мебели, материалов, фурнитуры и наполнения. Пришлите планировку в WhatsApp — назовём ориентир.",
          "price_factors": [f"{t}: {d}" for t, d in D.PRICE_FACTORS],
          "promises": [f"{t}: {d}" for t, d in D.PROMISES],
          "materials": [n for _, n in D.MATERIALS],
          "steps": [f"{t}: {d}" for t, d in D.STEPS],
          "districts": [d["name"] for d in D.DISTRICTS], "services": services, "faq": faq}
    txt = json.dumps(kb, ensure_ascii=False, separators=(",", ":"))
    (DIST / "kb.json").write_text(txt, encoding="utf-8")
    (ROOT / "api").mkdir(exist_ok=True); (ROOT / "api" / "kb.json").write_text(txt, encoding="utf-8")

def build_llms():
    L = [f"# {S['brand']} — {D.TAGLINE.lower()} {S['city_in']}", "", f"> {D.ABOUT} Работаем {S['city_in']}, все районы.", "",
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
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in SITEMAP:
        pr = "1.0" if p == "/" else ("0.8" if p.count("/") == 2 else "0.6")
        sm.append(f"<url><loc>{url_of(p)}</loc><lastmod>2026-11-10</lastmod><priority>{pr}</priority></url>")
    (DIST / "sitemap.xml").write_text("\n".join(sm + ["</urlset>"]) + "\n", encoding="utf-8")
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "anthropic-ai", "PerplexityBot", "Perplexity-User",
            "Google-Extended", "Googlebot", "Applebot", "Applebot-Extended", "Bingbot", "YandexBot", "DuckDuckBot", "CCBot", "meta-externalagent", "Amazonbot", "cohere-ai", "MistralAI-User"]
    rb = ["User-agent: *", "Allow: /", "Disallow: /api/", ""] + sum([[f"User-agent: {b}", "Allow: /", ""] for b in bots], []) + [f"Sitemap: {BASE}/sitemap.xml", ""]
    (DIST / "robots.txt").write_text("\n".join(rb), encoding="utf-8")
    man = {"name": f"{S['brand']} — {D.TAGLINE.lower()}", "short_name": S["brand"], "lang": "ru", "start_url": "/", "display": "standalone",
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

def main():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(); copy_assets()
    build_home()
    for c in CATS:
        build_category(c)
        for w in c["works"]: build_work(c, w)
    build_districts(); build_prices(); build_articles(); build_contacts(); build_privacy(); build_404()
    build_kb(); build_llms(); build_misc()
    print(f"OK: {len(SITEMAP)} страниц в sitemap + 404 → {DIST}")
    if D.PHONE_PLACEHOLDER: print("ВНИМАНИЕ: телефон в data.py — заглушка.")

if __name__ == "__main__":
    main()
