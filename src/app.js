/* Meblirovka — меню, «Назад», «Наверх», форма, ИИ-чат (ru/kk). Без зависимостей. */
(function () {
  'use strict';
  var d = document, w = window, body = d.body;
  var LANG = d.documentElement.lang === 'kk' ? 'kk' : 'ru';
  var UI = {};
  try { UI = JSON.parse(d.getElementById('ui-json').textContent); } catch (e) {}
  function $(s, c) { return (c || d).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }
  function conv(url) { try { if (typeof w.gtag_report_conversion === 'function') w.gtag_report_conversion(url); } catch (e) {} }
  function openWa(phone, text) {
    var u = 'https://wa.me/' + phone + '?text=' + encodeURIComponent(text);
    var win = w.open(u, '_blank', 'noopener');
    if (!win) w.location.href = u;
  }

  /* ── Мобильное меню ── */
  var mm = $('#mm'), burger = $('.burger'), lastFocus = null;
  function openMenu() {
    if (!mm) return;
    lastFocus = d.activeElement;
    mm.hidden = false; body.classList.add('lock');
    burger && burger.setAttribute('aria-expanded', 'true');
    var c = $('.mm-close', mm); c && c.focus();
  }
  function closeMenu() {
    if (!mm || mm.hidden) return;
    mm.hidden = true; body.classList.remove('lock');
    burger && burger.setAttribute('aria-expanded', 'false');
    lastFocus && lastFocus.focus && lastFocus.focus();
  }
  burger && burger.addEventListener('click', openMenu);
  if (mm) {
    $('.mm-close', mm).addEventListener('click', closeMenu);
    mm.addEventListener('click', function (e) {
      if (e.target === mm) closeMenu();
      if (e.target.closest('a')) closeMenu();
    });
  }

  /* ── Выпадающее меню на ПК: тач и клавиатура ── */
  $$('.has-dd').forEach(function (li) {
    var a = $('.nav-link', li);
    a.addEventListener('click', function (e) {
      if (w.matchMedia('(hover: none)').matches && !li.classList.contains('open')) { e.preventDefault(); li.classList.add('open'); }
    });
    d.addEventListener('click', function (e) { if (!li.contains(e.target)) li.classList.remove('open'); });
  });

  d.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeMenu(); closeChat();
      $$('.has-dd.open').forEach(function (li) { li.classList.remove('open'); });
    }
  });

  /* ── Назад: история этого сайта или главная ── */
  var back = $('.fbtn-back');
  if (back) back.addEventListener('click', function () {
    var ref = d.referrer, same = false;
    try { same = ref && new URL(ref).host === location.host; } catch (e) {}
    if (same && history.length > 1) history.back(); else location.href = LANG === 'kk' ? '/kz/' : '/';
  });

  /* ── Наверх ── */
  var top = $('.fbtn-top'), ticking = false;
  function onScroll() { ticking = false; if (top) top.hidden = w.scrollY < 600; }
  w.addEventListener('scroll', function () { if (!ticking) { ticking = true; w.requestAnimationFrame(onScroll); } }, { passive: true });
  top && top.addEventListener('click', function () {
    var smooth = !w.matchMedia('(prefers-reduced-motion: reduce)').matches;
    w.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' });
  });

  /* ── Форма: проверка телефона → WhatsApp с заявкой ── */
  var WA = null;
  function waNumber() {
    if (WA) return WA;
    var a = $('a[href^="https://wa.me/"]');
    WA = a ? a.getAttribute('href').split('wa.me/')[1].split('?')[0] : '';
    return WA;
  }
  $$('.form').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var ph = f.phone, err = $('.f-err', f), digits = (ph.value || '').replace(/\D/g, '');
      if (digits.length < 10) {
        ph.classList.add('invalid'); ph.setAttribute('aria-invalid', 'true');
        err.textContent = UI.f_err; ph.focus(); return;
      }
      ph.classList.remove('invalid'); ph.removeAttribute('aria-invalid'); err.textContent = '';
      var lines = [UI.f_head];
      if (f.work.value) lines.push(UI.f_work + ': ' + f.work.value);
      if (f.district.value) lines.push(UI.f_dis + ': ' + f.district.value);
      if (f.msg.value.trim()) lines.push(UI.f_msg + ': ' + f.msg.value.trim());
      if (f.name.value.trim()) lines.push(UI.f_name + ': ' + f.name.value.trim());
      lines.push(UI.f_phone + ': ' + ph.value.trim());
      lines.push(UI.f_page + ': ' + location.pathname);
      conv();
      openWa(waNumber(), lines.join('\n'));
    });
    f.phone.addEventListener('input', function () { if (this.classList.contains('invalid') && this.value.replace(/\D/g, '').length >= 10) { this.classList.remove('invalid'); $('.f-err', f).textContent = ''; } });
  });

  /* ── ИИ-чат: окно строится только при открытии ── */
  var chatBtn = $('.fbtn-chat'), chat = null, kb = null, hist = [], busy = false;
  function el(tag, cls, txt) { var e = d.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  var ICON = {
    x: '<svg class="i" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/></svg>',
    send: '<svg class="i" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M231.4,44.34s0,.1,0,.15l-58.2,191.94a15.88,15.88,0,0,1-14,11.51q-.69.06-1.38.06a15.86,15.86,0,0,1-14.42-9.15L107,164.15a4,4,0,0,1,.77-4.58l57.92-57.92a8,8,0,0,0-11.31-11.31L96.43,148.26a4,4,0,0,1-4.58.77L17.08,112.64a16,16,0,0,1,2.49-29.8l191.94-58.2.15,0A16,16,0,0,1,231.4,44.34Z"/></svg>'
  };
  function loadKb() {
    if (kb) return Promise.resolve(kb);
    return fetch(LANG === 'kk' ? '/kb-kk.json' : '/kb.json').then(function (r) { return r.json(); }).then(function (j) { kb = j; return kb; });
  }
  function buildChat() {
    chat = el('div', 'chat'); chat.setAttribute('role', 'dialog'); chat.setAttribute('aria-label', UI.title);
    var h = el('div', 'chat-h');
    h.innerHTML = '<img src="/assets/chat-bot-64.webp" width="36" height="36" alt="">';
    var t = el('p', null, UI.title); t.appendChild(el('small', null, UI.sub)); h.appendChild(t);
    var x = el('button', 'icon-btn chat-x'); x.type = 'button'; x.setAttribute('aria-label', UI.close); x.innerHTML = ICON.x; h.appendChild(x);
    chat.appendChild(h);
    var b = el('div', 'chat-b'); b.setAttribute('aria-live', 'polite'); chat.appendChild(b);
    var f = el('form', 'chat-f');
    var inp = el('input'); inp.id = 'chat-in'; inp.setAttribute('aria-label', UI.ph); inp.placeholder = UI.ph; inp.autocomplete = 'off'; inp.maxLength = 500;
    var sb = el('button'); sb.type = 'submit'; sb.setAttribute('aria-label', UI.send); sb.innerHTML = ICON.send;
    f.appendChild(inp); f.appendChild(sb); chat.appendChild(f);
    body.appendChild(chat);
    x.addEventListener('click', closeChat);
    f.addEventListener('submit', function (e) { e.preventDefault(); ask(inp.value); inp.value = ''; });
    loadKb().then(function () {
      botMsg(kb.greeting, null, true);
      var chips = el('div', 'chips');
      UI.chips.forEach(function (q) {
        var c = el('button', 'chip', q); c.type = 'button'; c.addEventListener('click', function () { chips.remove(); ask(q); }); chips.appendChild(c);
      });
      b.appendChild(chips);
    }).catch(function () { botMsg(UI.err_load, UI.wa_q); });
  }
  function openChat() { if (!chat) buildChat(); chat.hidden = false; $('.fl-r').style.visibility = 'hidden'; setTimeout(function () { var i = $('#chat-in'); i && i.focus(); }, 30); }
  function closeChat() { if (chat && !chat.hidden) { chat.hidden = true; $('.fl-r').style.visibility = ''; chatBtn.focus(); } }
  chatBtn && chatBtn.addEventListener('click', openChat);

  function scrollDown() { var b = $('.chat-b', chat); b.scrollTop = b.scrollHeight; }
  function userMsg(t) { $('.chat-b', chat).appendChild(el('div', 'msg msg-u', t)); scrollDown(); }
  function botMsg(t, waText, noActions) {
    var m = el('div', 'msg msg-b'); m.appendChild(d.createTextNode(t));
    if (!noActions && kb) {
      var act = el('div', 'msg-act');
      var call = el('a', 'btn btn-dark'); call.href = 'tel:' + kb.tel; call.textContent = UI.call;
      call.addEventListener('click', function () { conv(); });
      var wa = el('a', 'btn btn-wa'); wa.href = 'https://wa.me/' + kb.wa + '?text=' + encodeURIComponent(waText || UI.wa_q); wa.target = '_blank'; wa.rel = 'noopener'; wa.textContent = UI.wa;
      wa.addEventListener('click', function () { conv(); });
      act.appendChild(call); act.appendChild(wa); m.appendChild(act);
    }
    $('.chat-b', chat).appendChild(m); scrollDown();
  }

  /* Встроенный автоответчик по базе знаний (работает без ключа), ru + kk */
  function norm(s) { return (s || '').toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-яәғқңөұүһі0-9\s]/g, ' '); }
  var STOP = { 'и': 1, 'в': 1, 'на': 1, 'с': 1, 'по': 1, 'для': 1, 'а': 1, 'ли': 1, 'вы': 1, 'мы': 1, 'у': 1, 'не': 1, 'как': 1, 'что': 1, 'это': 1, 'или': 1, 'же': 1, 'мне': 1, 'нужна': 1, 'нужно': 1, 'можно': 1, 'ма': 1, 'ме': 1, 'бе': 1, 'па': 1, 'пе': 1, 'бар': 1, 'және': 1, 'керек': 1 };
  function stems(s) { return norm(s).split(/\s+/).filter(function (x) { return x.length > 2 && !STOP[x]; }).map(function (x) { return x.slice(0, 5); }); }
  function fill(s, o) { return s.replace(/\{(\w+)\}/g, function (_, k) { return o[k] != null ? o[k] : ''; }); }
  function localAnswer(q) {
    var n = norm(q), wa = UI.wa_q + q;
    if (/(цен|стои|сколько|прайс|бюджет|дорог|дешев|баға|баға|қанша|құн|тұрад)/.test(n))
      return { t: kb.price + '\n\n' + UI.factors + kb.price_factors.map(function (x) { return x.split(':')[0].toLowerCase(); }).join(', ') + '.', wa: UI.wa_price + q };
    if (/(изготов|сделает|делаете мебел|производ|на заказ|фабрик|сами|дайында|жасайсыз|тапсырыс|өндіріс|өзіңіз|өздеріңіз)/.test(n))
      return { t: kb.about + '\n\n' + UI.dirs + kb.services.filter(function (s) { return s.custom; }).map(function (s) { return s.short.toLowerCase(); }).join(', ') + '.', wa: wa };
    if (/(гарант|сервис|обслуж|ремонт мебел|сломал|регулир|кепіл|қызмет көрсет|жөнде)/.test(n))
      return { t: kb.promises.filter(function (p, i) { return i >= 2; }).join('\n'), wa: wa };
    if (/(3d|3д|проект|дизайн|визуал|эскиз|жоба)/.test(n)) return { t: kb.promises[1] + '\n\n' + kb.steps.slice(0, 3).join('\n'), wa: wa };
    if (/(материал|фасад|мдф|лдсп|шпон|массив|камен|фурнитур|қасбет|ағаш|тас)/.test(n)) return { t: fill(UI.mat, { m: kb.materials.join(', ').toLowerCase() }), wa: wa };
    if (/(замер|выезд|өлше)/.test(n)) return { t: kb.steps[0] + UI.zamer, wa: UI.wa_zamer };
    var dHit = kb.districts.filter(function (x) { return n.indexOf(norm(x).slice(0, 4)) > -1; })[0];
    if (dHit || /(район|адрес|где вы|выезж|приезж|город|аудан|қала|қайда)/.test(n))
      return { t: (dHit ? fill(UI.dist_yes, { d: dHit }) : '') + fill(UI.dist_all, { city: kb.city_gen }) + kb.districts.join(', ') + '.', wa: wa };
    if (/(телефон|номер|связ|позвон|whatsapp|ватсап|график|время работ|часы|байланыс|қоңырау|уақыт)/.test(n)) return { t: fill(UI.contact, { phone: kb.phone, hours: kb.hours }), wa: wa };
    if (/(этап|как работ|порядок|процесс|шаг|кезең|қалай жұмыс)/.test(n)) return { t: UI.steps + '\n' + kb.steps.join('\n'), wa: wa };
    var qs = stems(q); if (!qs.length) return null;
    function score(text) { var t = stems(text), s = 0; qs.forEach(function (x) { if (t.indexOf(x) > -1) s++; }); return s; }
    var best = null, bs = 0;
    kb.faq.forEach(function (f) { var s = score(f.q) * 2 + score(f.a); if (s > bs) { bs = s; best = { t: f.a + '\n\n' + UI.more + f.url, wa: wa }; } });
    kb.services.forEach(function (sv) { var s = score(sv.name) * 2 + score(sv.includes.join(' ')); if (s > bs) { bs = s; best = { t: sv.lead + '\n\n' + UI.incl + sv.includes.join('; ').toLowerCase() + '.\n\n' + UI.more + sv.url, wa: sv.wa }; } });
    return bs >= 2 ? best : null;
  }
  function fallback(q) { return { t: UI.fallback, wa: UI.wa_q + q }; }

  function ask(q) {
    q = (q || '').trim(); if (!q || busy) return;
    userMsg(q); busy = true;
    var typing = el('div', 'typing', UI.typing); $('.chat-b', chat).appendChild(typing); scrollDown();
    hist.push({ role: 'user', content: q }); hist = hist.slice(-8);
    var done = function (a) { typing.remove(); busy = false; botMsg(a.t, a.wa); hist.push({ role: 'assistant', content: a.t }); };
    var ctrl = w.AbortController ? new AbortController() : null, timer = setTimeout(function () { ctrl && ctrl.abort(); }, 15000);
    loadKb().then(function () {
      return fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages: hist, lang: LANG }), signal: ctrl ? ctrl.signal : undefined });
    }).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (j) {
      clearTimeout(timer);
      if (!j || !j.reply) throw 0;
      done({ t: j.reply, wa: UI.wa_q + q });
    }).catch(function () {
      clearTimeout(timer);
      if (!kb) { done(fallback(q)); return; }
      done(localAnswer(q) || fallback(q));
    });
  }
})();
