ЗАПУСК САЙТА «ОБЖИТО» — меблировка квартир под ключ (Алматы)
Разработка и продвижение: Anuken.kz

ПЕРЕД ЗАПУСКОМ ЗАМЕНИТЬ В src/data.py
- SITE: brand — если название другое (затем python3 src/og.py — перерисует логотип и превью)
- SITE: gtm_id, aw_id, aw_label — теги Google (метку конверсии копировать текстом)
- SITE: hours_text / hours_ld — график клиента
- DISTRICTS: строки note — сверить микрорайоны
- REVIEWS — только настоящие отзывы (пусто = блока нет)
После правок: python3 src/build.py (Vercel делает это сам при каждом пуше)

СТРУКТУРА
src/data.py        все данные: телефон, услуги, районы, FAQ, статьи, теги
src/build.py       генератор страниц, sitemap, robots, llms.txt, kb.json для чата
src/styles.css     стили (встраиваются в каждую страницу при сборке)
src/fonts.css      свои шрифты Lora + Golos Text (woff2, без Google Fonts)
src/app.js         меню, Назад/Наверх, форма → WhatsApp, ИИ-чат, конверсии
src/plan.svg       иллюстрация первого экрана (план квартиры с мебелью)
src/images.py      фото из assets/orig → WebP 480/800/1200 без EXIF (локально)
src/og.py          логотипы SVG, фавиконы, иконки, превью og.png (локально)
src/ads.py         файлы Google Ads → google-ads/ (локально)
api/chat.js        серверная функция ИИ-чата
assets/            шрифты, иконки, логотипы, превью
dist/              готовый сайт (собирается автоматически)

VERCEL
1. Импортировать репозиторий GitHub в Vercel. Настройки берутся из vercel.json
   (buildCommand: python3 src/build.py, outputDirectory: dist).
2. Settings → Environment Variables → ANTHROPIC_API_KEY — ключ для ИИ-чата.
   Без ключа чат работает встроенным автоответчиком по базе сайта.

ДОМЕН
1. Vercel → проект → Settings → Domains: добавить www.meblirovka.kz (основной)
   и meblirovka.kz с редиректом на www.
2. У регистратора: A-запись @ → 76.76.21.21, CNAME www → cname.vercel-dns.com.
   Старые A и AAAA для @ и www удалить. MX, TXT (SPF, DKIM) не трогать.
3. Редирект www ↔ без www — только в Vercel → Domains, не в vercel.json.

ПОСЛЕ ЗАПУСКА
- Search Console: добавить ресурс, отправить sitemap.xml, запросить индексирование
  главной и страниц услуг.
- Google Business Profile, 2ГИС, Instagram, WhatsApp Business — ссылка на сайт,
  название и телефон в одном формате с сайтом.
- Проверка скорости живого сайта с тегами: https://www.anuken.kz/skorost.html
- Google Ads: файлы в google-ads/, порядок — в 6-teksty-i-nastroyki.txt.

ФОТО
Положить реальные фото работ в assets/orig/ и запустить python3 src/images.py —
появятся WebP без EXIF и GPS в assets/img/.
