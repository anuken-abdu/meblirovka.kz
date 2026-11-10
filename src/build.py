# -*- coding: utf-8 -*-
"""Генератор сайта. Запуск: python3 src/build.py  →  dist/
Только стандартная библиотека Python — собирается на Vercel без зависимостей."""
import html, json, os, re, shutil, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"
sys.path.insert(0, str(SRC))
import data as D  # noqa: E402

S = D.SITE
BASE = f"https://www.{S['domain']}"
VER = "1"
ICON_DIR = ROOT / "assets" / "icons"

# ── утилиты ─────────────────────────────────────────────────────────────────
def esc(s): return html.escape(str(s), quote=True)

NB_RE = re.compile(r"(?<![\wА-Яа-яЁё])([А-Яа-яЁёA-Za-z]{1,2}|—)\s+")
def nb(s):
    """Неразрывные пробелы после коротких слов и перед тире, экранирование."""
    s = esc(s)
    s = NB_RE.sub(lambda m: m.group(1) + "\u00a0", s)
    s = re.sub(r"\s+—", "\u00a0—", s)
    s = re.sub(r"(\d)\s+(м²|м|т|₸|см|кг)", "\\1\u00a0\\2", s)
    return s

_icon_cache = {}
def icon(name, cls="i"):
    if name not in _icon_cache:
        p = ICON_DIR / f"{name}.svg"
        svg = p.read_text(encoding="utf-8")
        body = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", svg.strip())
        _icon_cache[name] = body
    return (f'<svg class="{cls}" viewBox="0 0 256 256" fill="currentColor" '
            f'aria-hidden="true" focusable="false">{_icon_cache[name]}</svg>')

def wa_url(text): return f"https://wa.me/{S['wa']}?text={urllib.parse.quote(text)}"
def tel_attrs():
    return (f'href="tel:{S["phone_tel"]}" '
            f'onclick="return gtag_report_conversion(&#39;tel:{S["phone_tel"]}&#39;)"')
def wa_attrs(text):
    return (f'href="{esc(wa_url(text))}" target="_blank" rel="noopener" '
            f'onclick="gtag_report_conversion()"')

def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>~])\s*", r"\1", css)
    css = re.sub(r"\s*:\s*", ":", css)
    css = css.replace(";}", "}").replace(" and(", " and (")
    return css.strip()

def url_of(path): return f"{BASE}{path}"

# ── данные-ссылки ───────────────────────────────────────────────────────────
CATS = D.CATEGORIES
def cat_path(c): return f"/{c['slug']}/"
def work_path(c, w): return f"/{c['slug']}/{w['slug']}/"
def find_by_key(key):
    """'pod-arendu' или 'pod-arendu/posutochno' → (name, path)"""
    parts = key.split("/")
    for c in CATS:
        if c["slug"] == parts[0]:
            if len(parts) == 1: return c["h1"], cat_path(c), c
            for w in c["works"]:
                if w["slug"] == parts[1]: return w["h1"], work_path(c, w), w
    raise KeyError(key)

# ── части страницы ──────────────────────────────────────────────────────────
CSS = minify_css((SRC / "fonts.css").read_text(encoding="utf-8") + (SRC / "styles.css").read_text(encoding="utf-8"))

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
        # заглушка до получения кода конверсии: пишет событие в dataLayer, ссылка работает как обычно
        out.append("<script>window.dataLayer=window.dataLayer||[];function gtag_report_conversion(u){(window.dataLayer=window.dataLayer||[]).push({event:'contact_click',url:u||''});return true;}</script>")
    return "\n".join(out)

def body_tags():
    if S["gtm_id"]:
        return (f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={S["gtm_id"]}" '
                f'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>')
    return ""

def org_ld():
    return {
        "@type": "HomeAndConstructionBusiness",
        "@id": f"{BASE}/#org",
        "name": S["brand"],
        "description": f"{D.TAGLINE} {S['city_in']}: подбор, закупка, доставка, сборка и расстановка мебели, техники и текстиля.",
        "url": f"{BASE}/",
        "telephone": S["phone_tel"],
        "logo": f"{BASE}/assets/logo.svg",
        "image": f"{BASE}/assets/og.png",
        "address": {"@type": "PostalAddress", "addressLocality": S["city"], "addressCountry": "KZ",
                    **({"streetAddress": S["address"]} if S["address"] else {})},
        "areaServed": {"@type": "City", "name": S["city"]},
        "openingHours": S["hours_ld"],
        "sameAs": [],
    }

def crumbs_ld(crumbs):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": url_of(p)} for i, (n, p) in enumerate(crumbs)]}

def faq_ld(faq):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

def logo_html(light=False):
    L = D.LOGO
    f = "logo-light.svg" if light else "logo.svg"
    return f'<img class="logo-img" src="/assets/{f}?v={VER}" width="{L["w"]}" height="{L["h"]}" alt="{esc(S["brand"])}">'

def nav_html():
    drop = []
    for c in CATS:
        items = "".join(f'<li><a href="{work_path(c, w)}">{esc(w["name"])}</a></li>' for w in c["works"])
        drop.append(f'<div class="dd-col"><a class="dd-cat" href="{cat_path(c)}">{icon(c["icon"])}{esc(c["name"])}</a><ul>{items}</ul></div>')
    return f"""<nav class="nav" aria-label="Основное меню">
<ul class="nav-list">
<li class="has-dd"><a href="/#uslugi" class="nav-link" aria-haspopup="true">Услуги{icon("caret-down", "i i-s")}</a><div class="dd">{''.join(drop)}</div></li>
<li><a class="nav-link" href="/rayony/">Районы</a></li>
<li><a class="nav-link" href="/ceny/">Цены</a></li>
<li><a class="nav-link" href="/stati/">Статьи</a></li>
<li><a class="nav-link" href="/kontakty/">Контакты</a></li>
</ul></nav>"""

def mobile_menu(wa_text):
    groups = []
    for c in CATS:
        items = "".join(f'<li><a href="{work_path(c, w)}">{esc(w["name"])}</a></li>' for w in c["works"])
        groups.append(f'<li><a class="mm-cat" href="{cat_path(c)}">{icon(c["icon"])}{esc(c["name"])}</a><ul>{items}</ul></li>')
    return f"""<div class="mm" id="mm" hidden>
<div class="mm-panel" role="dialog" aria-modal="true" aria-label="Меню">
<div class="mm-top"><span class="mm-title">Меню</span><button class="icon-btn mm-close" type="button" aria-label="Закрыть меню">{icon("x")}</button></div>
<ul class="mm-list">{''.join(groups)}
<li><a class="mm-link" href="/rayony/">Районы</a></li>
<li><a class="mm-link" href="/ceny/">Цены</a></li>
<li><a class="mm-link" href="/stati/">Статьи</a></li>
<li><a class="mm-link" href="/kontakty/">Контакты</a></li></ul>
<div class="mm-cta"><a class="btn btn-dark" {tel_attrs()}>{icon("phone")}Позвонить</a><a class="btn btn-wa" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}WhatsApp</a></div>
</div></div>"""

def header_html(wa_text):
    return f"""<header class="hdr"><div class="wrap hdr-in">
<a class="logo" href="/" aria-label="{esc(S['brand'])} — на главную">{logo_html()}</a>
{nav_html()}
<div class="hdr-cta">
<a class="hdr-phone" {tel_attrs()} aria-label="Позвонить {esc(S['phone_display'])}">{icon("phone")}<span>{esc(S['phone_display'])}</span></a>
<a class="btn btn-wa btn-sm hdr-wa" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}WhatsApp</a>
<button class="icon-btn burger" type="button" aria-label="Открыть меню" aria-expanded="false" aria-controls="mm">{icon("list")}</button>
</div></div></header>"""

def footer_html():
    cats = "".join(f'<li><a href="{cat_path(c)}">{esc(c["name"])}</a></li>' for c in CATS)
    return f"""<footer class="ftr"><div class="wrap">
<div class="ftr-grid">
<div class="ftr-about"><a class="logo logo--light" href="/" aria-label="{esc(S['brand'])} — на главную">{logo_html(True)}</a>
<p>{nb(D.TAGLINE + ' ' + S['city_in'] + ': подбор, закупка, доставка, сборка и расстановка.')}</p></div>
<div><p class="ftr-h">Услуги</p><ul>{cats}<li><a href="/ceny/">Цены</a></li></ul></div>
<div><p class="ftr-h">Информация</p><ul><li><a href="/rayony/">Районы</a></li><li><a href="/stati/">Статьи</a></li><li><a href="/kontakty/">Контакты</a></li><li><a href="/politika/">Политика</a></li></ul></div>
<div><p class="ftr-h">Связь</p><ul><li><a {tel_attrs()}>{esc(S['phone_display'])}</a></li><li><a {wa_attrs(D.CATEGORIES[0]['wa_text'].replace(' под аренду',''))}>WhatsApp</a></li><li>{esc(S['hours_text'])}</li><li>{esc(S['city'])}</li></ul></div>
</div>
<div class="ftr-bottom"><span>© {esc(S['brand'])}</span><a href="https://www.anuken.kz" target="_blank" rel="noopener">Разработка и продвижение Anuken.kz</a></div>
</div></footer>"""

def floating_html(wa_text):
    return f"""<div class="mbar"><a class="btn btn-dark" {tel_attrs()}>{icon("phone")}Позвонить</a><a class="btn btn-wa" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}WhatsApp</a></div>
<button class="fbtn fbtn-top" type="button" aria-label="Наверх" hidden>{icon("arrow-up")}</button>
<button class="fbtn fbtn-chat" type="button" aria-label="ИИ-консультант">{icon("chat-circle-dots")}</button>"""

def crumbs_html(crumbs):
    items = []
    for i, (n, p) in enumerate(crumbs):
        if i == len(crumbs) - 1:
            items.append(f'<li aria-current="page">{esc(n)}</li>')
        else:
            items.append(f'<li><a href="{p}">{esc(n)}</a></li>')
    return (f'<div class="wrap crumbs-row"><button class="back" type="button" aria-label="Назад">{icon("arrow-left", "i i-s")}Назад</button>'
            f'<nav class="crumbs" aria-label="Хлебные крошки"><ol>{"".join(items)}</ol></nav></div>')

def page(path, title, desc, body, *, crumbs=None, ld=None, wa_text=None, noindex=False, og_type="website"):
    wa_text = wa_text or "Здравствуйте! Нужна меблировка квартиры"
    graph = [org_ld(), {"@type": "WebSite", "@id": f"{BASE}/#site", "url": f"{BASE}/", "name": S["brand"], "inLanguage": "ru-KZ", "publisher": {"@id": f"{BASE}/#org"}}]
    if crumbs: graph.append(crumbs_ld(crumbs))
    graph += (ld or [])
    ldjson = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    canon = url_of(path)
    robots = "noindex,follow" if noindex else "index,follow,max-image-preview:large"
    lat, lon = S["geo_position"].split(";")
    doc = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
{head_tags()}
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{"" if noindex else f'<link rel="canonical" href="{canon}">'}
<meta name="robots" content="{robots}">
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
<link rel="preload" href="/assets/fonts/golos-text-cyrillic-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/lora-cyrillic-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<style>{CSS}</style>
<script type="application/ld+json">{ldjson}</script>
</head>
<body{' class="home"' if path == '/' else ''}>
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
    out = DIST / (path.strip("/") or "") / "index.html" if path != "/404" else DIST / "404.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    if not noindex:
        SITEMAP.append(path)

SITEMAP = []

# ── блоки контента ──────────────────────────────────────────────────────────
def h2(text, sub=None, cls=""):
    s = f'<p class="sec-sub">{nb(sub)}</p>' if sub else ""
    return f'<div class="sec-head {cls}"><h2>{nb(text)}</h2>{s}</div>'

def checklist(items, cls="checks"):
    return f'<ul class="{cls}">' + "".join(f'<li>{icon("check", "i ic")}<span>{nb(x)}</span></li>' for x in items) + "</ul>"

def cta_buttons(wa_text):
    return (f'<div class="cta-row"><a class="btn btn-dark btn-lg" {tel_attrs()}>{icon("phone")}Позвонить</a>'
            f'<a class="btn btn-wa btn-lg" {wa_attrs(wa_text)}>{icon("whatsapp-logo")}Написать в WhatsApp</a></div>')

def faq_html(faq, title="Частые вопросы"):
    items = "".join(f'<details class="faq-i"><summary><h3>{nb(q)}</h3>{icon("caret-down", "i i-s faq-c")}</summary><p>{nb(a)}</p></details>' for q, a in faq)
    return f'<section class="sec" aria-labelledby="faq-h"><div class="wrap narrow"><div class="sec-head"><h2 id="faq-h">{title}</h2></div><div class="faq">{items}</div></div></section>'

def steps_html():
    items = "".join(f'<li class="step">{icon(ic, "i step-i")}<h3>{nb(t)}</h3><p>{nb(d)}</p></li>' for ic, t, d in D.STEPS)
    return f'<section class="sec sec-alt"><div class="wrap">{h2("Как работаем", "От первого сообщения до квартиры, в которой можно жить")}<ol class="steps">{items}</ol></div></section>'

def factors_html(factors=None, title="От чего зависит цена"):
    if factors and isinstance(factors[0], str):
        body = checklist(factors, "checks checks-2")
    else:
        body = '<ul class="cards cards-5">' + "".join(
            f'<li class="card card-f">{icon(ic, "i card-i")}<h3>{nb(t)}</h3><p>{nb(d)}</p></li>' for ic, t, d in D.PRICE_FACTORS) + "</ul>"
    return (f'<section class="sec"><div class="wrap">{h2(title, "Пришлите планировку или фото в WhatsApp — назовём ориентир")}'
            f'{body}<p class="note">{icon("whatsapp-logo", "i ic")}<span>{nb("Цену не называем вслепую: она зависит от квартиры и выбранной мебели.")}</span></p></div></section>')

def split_table_html():
    t = D.SPLIT_TABLE
    th = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in t["head"])
    rows = "".join("<tr>" + f'<th scope="row" data-l="{esc(t["head"][0])}">{esc(r[0])}</th>' +
                   "".join(f'<td data-l="{esc(t["head"][i + 1])}">{nb(c)}</td>' for i, c in enumerate(r[1:])) + "</tr>" for r in t["rows"])
    return (f'<section class="sec sec-alt"><div class="wrap">{h2("Кто что делает", "Ваша часть — согласовать и принять, остальное на нас")}'
            f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table></div></div></section>')

def form_html(selected=""):
    opts = ['<option value="">Выберите</option>']
    for c in CATS:
        for w in c["works"]:
            v = f'{c["name"]}: {w["name"]}'
            sel = " selected" if selected in (c["slug"] + "/" + w["slug"], ) else ""
            opts.append(f'<option{sel}>{esc(v)}</option>')
    opts.append("<option>Полная меблировка под ключ</option>")
    dis = '<option value="">Выберите</option>' + "".join(f'<option>{esc(d["name"])}</option>' for d in D.DISTRICTS)
    return f"""<section class="sec sec-form" id="zayavka" aria-labelledby="form-h"><div class="wrap form-grid">
<div class="form-txt"><h2 id="form-h">{nb("Заявка на меблировку")}</h2>
<p>{nb("Заполните форму — откроется WhatsApp с готовым текстом заявки. Обязателен только телефон.")}</p>
{checklist(["Можно приложить фото и планировку в WhatsApp", "Ответим в рабочее время: " + S["hours_text"].lower()])}</div>
<form class="form" novalidate>
<div class="f-row"><label for="f-work">Вид работы</label><select id="f-work" name="work">{''.join(opts)}</select></div>
<div class="f-row"><label for="f-dis">Район</label><select id="f-dis" name="district">{dis}</select></div>
<div class="f-row f-wide"><label for="f-msg">Описание</label><textarea id="f-msg" name="msg" rows="3" placeholder="Например: студия 32 м², под посуточную аренду"></textarea></div>
<div class="f-row"><label for="f-name">Имя</label><input id="f-name" name="name" autocomplete="name"></div>
<div class="f-row"><label for="f-phone">Телефон *</label><input id="f-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required placeholder="+7 7__ ___ __ __" aria-describedby="f-err"></div>
<p class="f-err" id="f-err" role="alert"></p>
<button class="btn btn-wa btn-lg f-wide" type="submit">{icon("whatsapp-logo")}Отправить в WhatsApp</button>
<p class="f-note f-wide">Отправляя заявку, вы соглашаетесь с <a href="/politika/">политикой конфиденциальности</a>.</p>
</form></div></section>"""

PLAN_SVG = (SRC / "plan.svg").read_text(encoding="utf-8")

def photo_html(slug):
    if slug not in D.PHOTOS or not (ASSETS / "img" / f"{slug}-800.webp").exists(): return ""
    srcset = ", ".join(f"/assets/img/{slug}-{w}.webp {w}w" for w in (480, 800, 1200) if (ASSETS / "img" / f"{slug}-{w}.webp").exists())
    return (f'<div class="hero-photo"><img src="/assets/img/{slug}-800.webp" srcset="{srcset}" '
            f'sizes="(min-width:1024px) 560px, calc(100vw - 40px)" width="800" height="600" '
            f'alt="{esc(D.PHOTOS[slug])}" fetchpriority="high" decoding="async"></div>')

def page_hero(h1, lead, wa_text, points=None, plan=False, photo=""):
    pts = checklist(points, "checks hero-pts") if points else ""
    art = f'<div class="hero-art" aria-hidden="true">{PLAN_SVG}</div>' if plan else photo
    return f"""<section class="hero{' hero-plan' if plan else ' hero-in'}{' hero-ph' if photo else ''}"><div class="wrap hero-grid">
<div class="hero-txt"><h1>{nb(h1)}</h1><p class="lead">{nb(lead)}</p>{cta_buttons(wa_text)}{pts}</div>{art}
</div></section>"""

def cards_works(c, current=None):
    items = []
    for w in c["works"]:
        if current and w["slug"] == current: continue
        items.append(f'<li><a class="card card-link" href="{work_path(c, w)}">{icon(w["icon"], "i card-i")}<span class="card-t">{esc(w["name"])}</span>{icon("caret-right", "i i-s card-arr")}</a></li>')
    return '<ul class="cards cards-links">' + "".join(items) + "</ul>"

def prepare_html(items):
    return f'<section class="sec"><div class="wrap narrow">{h2("Как подготовиться")}{checklist(items)}</div></section>'

# ── страницы ────────────────────────────────────────────────────────────────
def build_home():
    cats = "".join(
        f'<li><a class="card card-svc" href="{cat_path(c)}">{icon(c["icon"], "i card-i")}<h3>{esc(c["name"])}</h3><p>{nb(c["card"])}</p>'
        f'<span class="more">Подробнее{icon("caret-right", "i i-s")}</span></a></li>' for c in CATS)
    aud = "".join(f'<li class="card card-a">{icon(ic, "i card-i")}<h3>{nb(t)}</h3><p>{nb(d)}</p></li>' for ic, t, d in D.AUDIENCE)
    incl = checklist(["Мебель для всех комнат и прихожей", "Бытовая техника", "Шторы, ковры, постельное бельё", "Посуда и всё для кухни", "Свет и мелкий декор", "Доставка, подъём, сборка, расстановка"], "checks checks-2")
    body = page_hero(
        f"Меблировка квартир под ключ {S['city_in']}",
        f"Обставляем квартиры {S['city_in']} под аренду и для жизни: подбираем мебель, технику, текстиль и посуду, закупаем, привозим, собираем и расставляем. Мебель не изготавливаем — подбираем готовую.",
        "Здравствуйте! Нужна меблировка квартиры под ключ",
        ["Подбор, закупка, доставка, сборка", "Мебель, техника, текстиль, посуда", f"Все районы {S['city_gen']}"], plan=True)
    body += f'<section class="sec" id="uslugi"><div class="wrap">{h2("Услуги", "Полная меблировка или только то, чего не хватает")}<ul class="cards cards-3">{cats}</ul></div></section>'
    body += f'<section class="sec sec-alt"><div class="wrap">{h2("Для кого")}<ul class="cards cards-4">{aud}</ul></div></section>'
    body += f'<section class="sec"><div class="wrap">{h2("Что входит в меблировку под ключ")}{incl}</div></section>'
    body += steps_html()
    body += split_table_html()
    body += factors_html()
    body += faq_html(D.FAQ_MAIN)
    body += form_html()
    page("/", f"Меблировка квартир под ключ {S['city_in']} | {S['brand']}",
         f"Меблировка квартир под ключ {S['city_in']}: мебель, техника, текстиль, посуда. Подбор, доставка, сборка. Под аренду и для себя.",
         body, ld=[faq_ld(D.FAQ_MAIN)], wa_text="Здравствуйте! Нужна меблировка квартиры под ключ")

def service_ld(name, desc, path):
    return {"@type": "Service", "name": name, "description": desc, "url": url_of(path),
            "provider": {"@id": f"{BASE}/#org"}, "areaServed": {"@type": "City", "name": S["city"]},
            "serviceType": "Меблировка квартир"}

def build_category(c):
    p = cat_path(c)
    crumbs = [("Главная", "/"), (c["name"], p)]
    body = page_hero(c["h1"], c["lead"], c["wa_text"], photo=photo_html(c["slug"]))
    body += f'<section class="sec"><div class="wrap">{h2("Выберите работу")}{cards_works(c)}</div></section>'
    body += f'<section class="sec sec-alt"><div class="wrap">{h2("Что входит")}{checklist(c["includes"], "checks checks-2")}</div></section>'
    body += factors_html(c["factors"])
    body += steps_html()
    body += prepare_html(c["prepare"])
    body += faq_html(c["faq"])
    body += form_html()
    page(p, c["title"], c["desc"], body, crumbs=crumbs, wa_text=c["wa_text"],
         ld=[service_ld(c["h1"], c["desc"], p), faq_ld(c["faq"])])

def build_work(c, w):
    p = work_path(c, w)
    crumbs = [("Главная", "/"), (c["name"], cat_path(c)), (w["name"], p)]
    body = page_hero(w["h1"], w["lead"], w["wa_text"])
    body += f'<section class="sec"><div class="wrap">{h2("Что входит в работу")}{checklist(w["includes"], "checks checks-2")}</div></section>'
    body += steps_html()
    body += prepare_html(w["prepare"])
    body += factors_html(c["factors"])
    body += faq_html(w["faq"])
    other = cards_works(c, current=w["slug"])
    others_cats = "".join(f'<li><a class="card card-link" href="{cat_path(x)}">{icon(x["icon"], "i card-i")}<span class="card-t">{esc(x["name"])}</span>{icon("caret-right", "i i-s card-arr")}</a></li>' for x in CATS if x is not c)
    body += f'<section class="sec sec-alt"><div class="wrap">{h2("Похожие работы")}{other}<ul class="cards cards-links mt">{others_cats}</ul></div></section>'
    body += form_html(c["slug"] + "/" + w["slug"])
    page(p, w["title"], w["desc"], body, crumbs=crumbs, wa_text=w["wa_text"],
         ld=[service_ld(w["h1"], w["desc"], p), faq_ld(w["faq"])])

def svc_links():
    return '<ul class="cards cards-links">' + "".join(
        f'<li><a class="card card-link" href="{cat_path(c)}">{icon(c["icon"], "i card-i")}<span class="card-t">{esc(c["name"])}</span>{icon("caret-right", "i i-s card-arr")}</a></li>' for c in CATS) + "</ul>"

def build_districts():
    p = "/rayony/"
    crumbs = [("Главная", "/"), ("Районы", p)]
    items = "".join(f'<li><a class="card card-link" href="/rayony/{d["slug"]}/">{icon("map-pin", "i card-i")}<span class="card-t">{esc(d["name"])}</span>{icon("caret-right", "i i-s card-arr")}</a></li>' for d in D.DISTRICTS)
    body = page_hero(f"Меблировка квартир по районам {S['city_gen']}",
                     f"Меблируем квартиры во всех районах {S['city_gen']}: выезжаем на замер, привозим мебель и технику, собираем и расставляем на месте.",
                     "Здравствуйте! Нужна меблировка квартиры")
    body += f'<section class="sec"><div class="wrap">{h2("Районы")}<ul class="cards cards-links cards-4l">{items}</ul></div></section>'
    body += f'<section class="sec sec-alt"><div class="wrap">{h2("Услуги")}{svc_links()}</div></section>'
    body += form_html()
    page(p, f"Меблировка квартир по районам {S['city_gen']} | {S['brand']}",
         f"Меблировка квартир под ключ во всех районах {S['city_gen']}: " + ", ".join(d["name"] for d in D.DISTRICTS) + ".",
         body, crumbs=crumbs)
    for d in D.DISTRICTS:
        dp = f"/rayony/{d['slug']}/"
        cr = [("Главная", "/"), ("Районы", p), (d["name"], dp)]
        h1 = f"Меблировка квартир {d['in']} {S['city_gen']}"
        wa = f"Здравствуйте! Нужна меблировка квартиры, {d['name']} район"
        faq = [
            (f"Работаете {d['in']}?", f"Да, выезжаем на замер и привозим мебель {d['in']} {S['city_gen']}."),
            ("Можно обставить квартиру без моего присутствия?", "Да, по ключам и с фото по ходу работ в WhatsApp."),
            ("Как узнать стоимость?", "Пришлите планировку или фото комнат в WhatsApp — назовём ориентир."),
        ]
        others = "".join(f'<li><a class="card card-link" href="/rayony/{x["slug"]}/">{icon("map-pin", "i card-i")}<span class="card-t">{esc(x["name"])}</span>{icon("caret-right", "i i-s card-arr")}</a></li>' for x in D.DISTRICTS if x is not d)
        body = page_hero(h1, f"Меблировка квартир под ключ {d['in']} {S['city_gen']}: подбор, закупка, доставка, сборка и расстановка мебели, техники и текстиля. {d['note']}", wa)
        body += f'<section class="sec"><div class="wrap">{h2("Услуги " + d["in"])}{svc_links()}</div></section>'
        body += steps_html()
        body += faq_html(faq)
        body += f'<section class="sec"><div class="wrap">{h2("Другие районы")}<ul class="cards cards-links cards-4l">{others}</ul></div></section>'
        body += form_html()
        page(dp, f"Меблировка квартир {d['in']} {S['city_gen']} | {S['brand']}"[:70],
             f"Меблировка квартир под ключ {d['in']} {S['city_gen']}: мебель, техника, текстиль. Подбор, доставка, сборка, расстановка.",
             body, crumbs=cr, wa_text=wa, ld=[faq_ld(faq)])

def build_prices():
    p = "/ceny/"
    crumbs = [("Главная", "/"), ("Цены", p)]
    faq = [D.FAQ_MAIN[2], ("Почему на сайте нет цен?", "Стоимость меблировки зависит от квартиры и выбранной мебели. Любая цифра без этих данных будет неточной, поэтому ориентир называем по фото и планировке."),
           ("Можно уложиться в определённый бюджет?", "Да, назовите сумму — подберём состав меблировки под неё и покажем, на чём можно сэкономить.")]
    body = page_hero(f"Цены на меблировку квартир {S['city_in']}",
                     "Стоимость меблировки зависит от площади, состава и уровня мебели и техники. Пришлите планировку или фото в WhatsApp — назовём ориентир.",
                     "Здравствуйте! Хочу узнать стоимость меблировки квартиры")
    body += factors_html(title="От чего зависит стоимость")
    body += split_table_html()
    body += faq_html(faq)
    body += form_html()
    page(p, f"Цены на меблировку квартир {S['city_in']} | {S['brand']}",
         f"От чего зависит стоимость меблировки квартиры под ключ {S['city_in']}. Ориентир по фото и планировке в WhatsApp.",
         body, crumbs=crumbs, ld=[faq_ld(faq)], wa_text="Здравствуйте! Хочу узнать стоимость меблировки квартиры")

def build_articles():
    p = "/stati/"
    crumbs = [("Главная", "/"), ("Статьи", p)]
    items = "".join(f'<li><a class="card card-art" href="/stati/{a["slug"]}/">{icon("article", "i card-i")}<h3>{esc(a["name"])}</h3><p>{nb(a["desc"])}</p></a></li>' for a in D.ARTICLES)
    body = page_hero("Статьи о меблировке квартир", "Короткие ответы на вопросы, которые задают перед меблировкой: стоимость, состав, посуточная аренда, новостройки.", "Здравствуйте! Есть вопрос по меблировке квартиры")
    body += f'<section class="sec"><div class="wrap"><ul class="cards cards-2">{items}</ul></div></section>'
    page(p, f"Статьи о меблировке квартир | {S['brand']}", "Полезные статьи о меблировке квартир под ключ: стоимость, состав работ, посуточная аренда, новостройки.", body, crumbs=crumbs)
    for a in D.ARTICLES:
        ap = f"/stati/{a['slug']}/"
        cr = [("Главная", "/"), ("Статьи", p), (a["name"], ap)]
        parts = []
        for kind, val in a["blocks"]:
            if kind == "h2": parts.append(f"<h2>{nb(val)}</h2>")
            elif kind == "p": parts.append(f"<p>{nb(val)}</p>")
            elif kind == "ul": parts.append(checklist(val))
        rel = []
        for key in a["related"]:
            n, path, obj = find_by_key(key)
            rel.append(f'<li><a class="card card-link" href="{path}">{icon(obj["icon"], "i card-i")}<span class="card-t">{esc(obj["name"])}</span>{icon("caret-right", "i i-s card-arr")}</a></li>')
        d_txt = a["date"]
        y, m, dd = d_txt.split("-")
        months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
        human = f"{int(dd)} {months[int(m)-1]} {y}"
        body = f"""<article class="sec art"><div class="wrap narrow">
<h1>{nb(a['h1'])}</h1><p class="art-date"><time datetime="{d_txt}">{human}</time></p>
<p class="lead">{nb(a['lead'])}</p>{''.join(parts)}
<div class="art-cta"><p>{nb('Пришлите планировку или фото квартиры — подскажем состав меблировки и ориентир по стоимости.')}</p>{cta_buttons('Здравствуйте! Прочитал статью «' + a['name'] + '», есть вопрос')}</div>
</div></article>
<section class="sec sec-alt"><div class="wrap">{h2('Услуги по теме')}<ul class="cards cards-links">{''.join(rel)}</ul></div></section>"""
        art_ld = {"@type": "Article", "headline": a["h1"], "description": a["desc"], "datePublished": d_txt, "dateModified": d_txt,
                  "mainEntityOfPage": url_of(ap), "image": f"{BASE}/assets/og.png", "inLanguage": "ru-KZ",
                  "author": {"@id": f"{BASE}/#org"}, "publisher": {"@id": f"{BASE}/#org"}}
        page(ap, a["title"], a["desc"], body, crumbs=cr, ld=[art_ld], og_type="article")

def build_contacts():
    p = "/kontakty/"
    crumbs = [("Главная", "/"), ("Контакты", p)]
    rows = [("phone", "Телефон", f'<a {tel_attrs()}>{esc(S["phone_display"])}</a>'),
            ("whatsapp-logo", "WhatsApp", f'<a {wa_attrs("Здравствуйте! Нужна меблировка квартиры")}>Написать</a>'),
            ("clock", "График", esc(S["hours_text"])),
            ("map-pin", "Город", esc(S["city"]) + (", " + esc(S["address"]) if S["address"] else ", выезд по всем районам"))]
    if S["email"]: rows.insert(2, ("chat-circle-text", "Почта", f'<a href="mailto:{esc(S["email"])}">{esc(S["email"])}</a>'))
    items = "".join(f'<li class="card card-c">{icon(ic, "i card-i")}<div><p class="c-l">{l}</p><p class="c-v">{v}</p></div></li>' for ic, l, v in rows)
    body = f'<section class="sec hero-in"><div class="wrap"><h1>{nb("Контакты")}</h1><p class="lead">{nb(D.TAGLINE + " " + S["city_in"] + ". Быстрее всего — написать в WhatsApp и приложить фото или планировку.")}</p><ul class="cards cards-2 mt">{items}</ul></div></section>'
    body += form_html()
    page(p, f"Контакты — {S['brand']}, меблировка квартир {S['city_in']}"[:60],
         f"Телефон и WhatsApp {S['brand']}: меблировка квартир под ключ {S['city_in']}. {S['hours_text']}.", body, crumbs=crumbs)

def build_privacy():
    p = "/politika/"
    crumbs = [("Главная", "/"), ("Политика конфиденциальности", p)]
    paras = [
        ("Какие данные мы получаем", f"Имя, телефон, район и описание задачи, которые вы указываете в форме заявки или в чате на сайте {S['domain']}."),
        ("Как это происходит", "Форма не отправляет данные на сервер: она открывает WhatsApp с готовым текстом, и вы сами решаете, отправлять ли сообщение. Сообщения ИИ-консультанту обрабатываются для ответа и не используются для рекламы."),
        ("Зачем", "Чтобы ответить на заявку, уточнить детали и рассчитать ориентир по стоимости меблировки."),
        ("Аналитика", "Сайт может использовать сервисы Google для подсчёта обращений. Они работают с обезличенными данными о посещениях и нажатиях."),
        ("Передача третьим лицам", "Мы не продаём и не передаём ваши данные третьим лицам, кроме случаев, предусмотренных законодательством Республики Казахстан."),
        ("Удаление данных", "Чтобы удалить переписку и данные, напишите нам в WhatsApp."),
    ]
    body = f'<section class="sec art"><div class="wrap narrow"><h1>Политика конфиденциальности</h1>' + "".join(f"<h2>{nb(h)}</h2><p>{nb(t)}</p>" for h, t in paras) + "</div></section>"
    page(p, f"Политика конфиденциальности | {S['brand']}", f"Как сайт {S['brand']} обрабатывает данные из формы заявки и чата.", body, crumbs=crumbs)

def build_404():
    body = f"""<section class="sec hero-in nf"><div class="wrap narrow"><h1>Страница не найдена</h1>
<p class="lead">{nb("Возможно, адрес изменился. Перейдите на главную или напишите нам — подскажем.")}</p>
<div class="cta-row"><a class="btn btn-dark btn-lg" href="/">{icon("house")}На главную</a><a class="btn btn-wa btn-lg" {wa_attrs("Здравствуйте! Нужна меблировка квартиры")}>{icon("whatsapp-logo")}Написать в WhatsApp</a></div></div></section>"""
    page("/404", f"Страница не найдена | {S['brand']}", "Страница не найдена.", body, noindex=True)

# ── служебные файлы ─────────────────────────────────────────────────────────
def build_kb():
    services = []
    for c in CATS:
        services.append({"name": c["h1"], "short": c["name"], "url": url_of(cat_path(c)), "lead": c["lead"], "includes": c["includes"], "wa": c["wa_text"]})
        for w in c["works"]:
            services.append({"name": w["h1"], "short": w["name"], "url": url_of(work_path(c, w)), "lead": w["lead"], "includes": w["includes"], "wa": w["wa_text"]})
    faq = [{"q": q, "a": a, "url": url_of("/")} for q, a in D.FAQ_MAIN]
    for c in CATS:
        faq += [{"q": q, "a": a, "url": url_of(cat_path(c))} for q, a in c["faq"]]
        for w in c["works"]:
            faq += [{"q": q, "a": a, "url": url_of(work_path(c, w))} for q, a in w["faq"]]
    kb = {
        "brand": S["brand"], "city": S["city"], "city_gen": S["city_gen"], "city_in": S["city_in"], "phone": S["phone_display"], "tel": S["phone_tel"],
        "wa": S["wa"], "hours": S["hours_text"], "tagline": D.TAGLINE, "greeting": D.CHAT_GREETING,
        "not_manufacturing": "Мебель не изготавливаем, подбираем готовую: подбор, закупка, доставка, сборка, расстановка.",
        "price": "Цены на сайте не указаны: стоимость зависит от площади, количества комнат, уровня мебели и того, что уже есть в квартире. Пришлите планировку или фото в WhatsApp — назовём ориентир.",
        "price_factors": [f"{t}: {d}" for _, t, d in D.PRICE_FACTORS],
        "steps": [f"{t}: {d}" for _, t, d in D.STEPS],
        "districts": [d["name"] for d in D.DISTRICTS],
        "services": services, "faq": faq,
    }
    txt = json.dumps(kb, ensure_ascii=False, separators=(",", ":"))
    (DIST / "kb.json").write_text(txt, encoding="utf-8")
    (ROOT / "api").mkdir(exist_ok=True)
    (ROOT / "api" / "kb.json").write_text(txt, encoding="utf-8")

def build_llms():
    L = [f"# {S['brand']} — {D.TAGLINE.lower()} {S['city_in']}", "",
         f"> {S['brand']} обставляет квартиры {S['city_in']} под ключ: подбор, закупка, доставка, сборка и расстановка мебели, бытовой техники, текстиля и посуды. Под посуточную и долгосрочную аренду, для новостроек. Мебель не изготавливаем — подбираем готовую.", "",
         "## Контакты", f"- Телефон: {S['phone_display']}", f"- WhatsApp: https://wa.me/{S['wa']}", f"- График: {S['hours_text']}", f"- Город: {S['city']}, все районы", f"- Сайт: {BASE}/", "",
         "## Услуги"]
    for c in CATS:
        L.append(f"- [{c['h1']}]({url_of(cat_path(c))}): {c['lead']}")
        for w in c["works"]:
            L.append(f"  - [{w['h1']}]({url_of(work_path(c, w))}): {w['lead']}")
    L += ["", "## Цены", f"- [Цены]({url_of('/ceny/')}): на сайте не указаны, ориентир — по планировке или фото в WhatsApp. Зависит от: " + "; ".join(t.lower() for _, t, _ in D.PRICE_FACTORS) + ".", "",
          "## Районы", "- " + ", ".join(f"[{d['name']}]({url_of('/rayony/' + d['slug'] + '/')})" for d in D.DISTRICTS), "",
          "## Как работаем"] + [f"- {t}: {d}" for _, t, d in D.STEPS] + ["", "## Частые вопросы"]
    for q, a in D.FAQ_MAIN: L += [f"- {q} {a}"]
    L += ["", "## Статьи"] + [f"- [{a['h1']}]({url_of('/stati/' + a['slug'] + '/')})" for a in D.ARTICLES]
    (DIST / "llms.txt").write_text("\n".join(L) + "\n", encoding="utf-8")

def build_misc():
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in SITEMAP:
        pr = "1.0" if p == "/" else ("0.8" if p.count("/") == 2 else "0.6")
        sm.append(f"<url><loc>{url_of(p)}</loc><lastmod>2026-11-10</lastmod><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "anthropic-ai", "PerplexityBot", "Perplexity-User",
            "Google-Extended", "Googlebot", "Applebot", "Applebot-Extended", "Bingbot", "YandexBot", "DuckDuckBot", "CCBot", "meta-externalagent", "Amazonbot", "cohere-ai", "MistralAI-User"]
    rb = ["User-agent: *", "Allow: /", "Disallow: /api/", ""] + sum([[f"User-agent: {b}", "Allow: /", ""] for b in bots], []) + [f"Sitemap: {BASE}/sitemap.xml", ""]
    (DIST / "robots.txt").write_text("\n".join(rb), encoding="utf-8")
    man = {"name": f"{S['brand']} — {D.TAGLINE.lower()}", "short_name": S["brand"], "lang": "ru", "start_url": "/", "display": "standalone",
           "background_color": "#F5F0E6", "theme_color": S["theme_color"],
           "icons": [{"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
                     {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
                     {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
    (DIST / "site.webmanifest").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")

def copy_assets():
    dst = DIST / "assets"
    shutil.copytree(ASSETS, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("icons", "orig"))
    shutil.copy(SRC / "app.js", dst / "app.js")
    for f in ("favicon.ico", "apple-touch-icon.png"):
        if (ASSETS / f).exists(): shutil.copy(ASSETS / f, DIST / f)

def main():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir()
    copy_assets()
    build_home()
    for c in CATS:
        build_category(c)
        for w in c["works"]: build_work(c, w)
    build_districts(); build_prices(); build_articles(); build_contacts(); build_privacy(); build_404()
    build_kb(); build_llms(); build_misc()
    print(f"OK: {len(SITEMAP)} страниц в sitemap + 404 → {DIST}")
    if D.PHONE_PLACEHOLDER:
        print("ВНИМАНИЕ: телефон в data.py — заглушка. Замените SITE['phone_*'] и SITE['wa'], поставьте PHONE_PLACEHOLDER = False.")

if __name__ == "__main__":
    main()
