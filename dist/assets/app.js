/* Meblirovka — меню, «Назад», «Наверх», форма, ИИ-чат. Без зависимостей. */
(function () {
  'use strict';
  var d = document, w = window, body = d.body;
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
  var back = $('.back');
  if (back) back.addEventListener('click', function () {
    var ref = d.referrer, same = false;
    try { same = ref && new URL(ref).host === location.host; } catch (e) {}
    if (same && history.length > 1) history.back(); else location.href = '/';
  });

  /* ── Наверх ── */
  var top = $('.fbtn-top'), ticking = false;
  function onScroll() {
    ticking = false;
    if (top) top.hidden = w.scrollY < 600;
  }
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
        err.textContent = 'Укажите телефон: не меньше 10 цифр';
        ph.focus(); return;
      }
      ph.classList.remove('invalid'); ph.removeAttribute('aria-invalid'); err.textContent = '';
      var lines = ['Здравствуйте! Заявка с сайта на меблировку.'];
      if (f.work.value) lines.push('Вид работы: ' + f.work.value);
      if (f.district.value) lines.push('Район: ' + f.district.value);
      if (f.msg.value.trim()) lines.push('Описание: ' + f.msg.value.trim());
      if (f.name.value.trim()) lines.push('Имя: ' + f.name.value.trim());
      lines.push('Телефон: ' + ph.value.trim());
      lines.push('Страница: ' + location.pathname);
      conv();
      openWa(waNumber(), lines.join('\n'));
    });
    f.phone.addEventListener('input', function () { if (this.classList.contains('invalid') && this.value.replace(/\D/g, '').length >= 10) { this.classList.remove('invalid'); $('.f-err', f).textContent = ''; } });
  });

  /* ── ИИ-чат: окно строится только при открытии ── */
  var chatBtn = $('.fbtn-chat'), chat = null, kb = null, history_ = [], busy = false;
  function el(tag, cls, txt) { var e = d.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  var ICON = {
    x: '<svg class="i" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/></svg>',
    send: '<svg class="i" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M231.4,44.34s0,.1,0,.15l-58.2,191.94a15.88,15.88,0,0,1-14,11.51q-.69.06-1.38.06a15.86,15.86,0,0,1-14.42-9.15L107,164.15a4,4,0,0,1,.77-4.58l57.92-57.92a8,8,0,0,0-11.31-11.31L96.43,148.26a4,4,0,0,1-4.58.77L17.08,112.64a16,16,0,0,1,2.49-29.8l191.94-58.2.15,0A16,16,0,0,1,231.4,44.34Z"/></svg>'
  };
  function loadKb() {
    if (kb) return Promise.resolve(kb);
    return fetch('/kb.json').then(function (r) { return r.json(); }).then(function (j) { kb = j; return kb; });
  }
  function buildChat() {
    chat = el('div', 'chat'); chat.setAttribute('role', 'dialog'); chat.setAttribute('aria-label', 'ИИ-консультант');
    chat.innerHTML = '<div class="chat-h"><p>ИИ-консультант<small>Отвечает по услугам сайта</small></p><button class="icon-btn chat-x" type="button" aria-label="Закрыть чат">' + ICON.x + '</button></div>' +
      '<div class="chat-b" aria-live="polite"></div>' +
      '<form class="chat-f"><input id="chat-in" aria-label="Ваш вопрос" autocomplete="off" placeholder="Ваш вопрос" maxlength="500"><button type="submit" aria-label="Отправить">' + ICON.send + '</button></form>';
    body.appendChild(chat);
    $('.chat-x', chat).addEventListener('click', closeChat);
    $('.chat-f', chat).addEventListener('submit', function (e) { e.preventDefault(); var i = $('#chat-in'); ask(i.value); i.value = ''; });
    loadKb().then(function () {
      botMsg(kb.greeting, null, true);
      var chips = el('div', 'chips');
      ['Делаете мебель на заказ?', 'Сколько стоит?', 'Есть гарантия?', 'Как вы работаете?'].forEach(function (q) {
        var b = el('button', 'chip', q); b.type = 'button'; b.addEventListener('click', function () { chips.remove(); ask(q); }); chips.appendChild(b);
      });
      $('.chat-b', chat).appendChild(chips);
    }).catch(function () { botMsg('Напишите нам в WhatsApp — ответим.', 'Здравствуйте! Вопрос с сайта'); });
  }
  function openChat() { if (!chat) buildChat(); chat.hidden = false; chatBtn.hidden = true; setTimeout(function () { var i = $('#chat-in'); i && i.focus(); }, 30); }
  function closeChat() { if (chat && !chat.hidden) { chat.hidden = true; chatBtn.hidden = false; chatBtn.focus(); } }
  chatBtn && chatBtn.addEventListener('click', openChat);

  function scrollDown() { var b = $('.chat-b', chat); b.scrollTop = b.scrollHeight; }
  function userMsg(t) { $('.chat-b', chat).appendChild(el('div', 'msg msg-u', t)); scrollDown(); }
  function botMsg(t, waText, noActions) {
    var m = el('div', 'msg msg-b'); m.appendChild(d.createTextNode(t));
    if (!noActions && kb) {
      var act = el('div', 'msg-act');
      var call = el('a', 'btn btn-dark'); call.href = 'tel:' + kb.tel; call.textContent = 'Позвонить';
      call.addEventListener('click', function () { conv(); });
      var wa = el('a', 'btn btn-wa'); wa.href = 'https://wa.me/' + kb.wa + '?text=' + encodeURIComponent(waText || 'Здравствуйте!'); wa.target = '_blank'; wa.rel = 'noopener'; wa.textContent = 'В WhatsApp';
      wa.addEventListener('click', function () { conv(); });
      act.appendChild(call); act.appendChild(wa); m.appendChild(act);
    }
    $('.chat-b', chat).appendChild(m); scrollDown();
  }

  /* Встроенный автоответчик по базе знаний (работает без ключа) */
  function norm(s) { return (s || '').toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9әғқңөұүһі\s]/g, ' '); }
  var STOP = { 'и': 1, 'в': 1, 'на': 1, 'с': 1, 'по': 1, 'для': 1, 'а': 1, 'ли': 1, 'вы': 1, 'мы': 1, 'у': 1, 'не': 1, 'как': 1, 'что': 1, 'это': 1, 'или': 1, 'же': 1, 'мне': 1, 'нужна': 1, 'нужно': 1, 'можно': 1 };
  function stems(s) { return norm(s).split(/\s+/).filter(function (x) { return x.length > 2 && !STOP[x]; }).map(function (x) { return x.slice(0, 5); }); }
  function localAnswer(q) {
    var n = norm(q), wa = 'Здравствуйте! Вопрос из чата: ' + q;
    if (/(цен|стои|сколько|прайс|бюджет|дорог|дешев)/.test(n)) return { t: kb.price + '\n\nОт чего зависит: ' + kb.price_factors.map(function (x) { return x.split(':')[0].toLowerCase(); }).join(', ') + '.', wa: 'Здравствуйте! Хочу узнать стоимость меблировки. ' + q };
    if (/(изготов|сделает|делаете мебел|производ|на заказ|фабрик|сами)/.test(n)) return { t: kb.about + '\n\nНаправления: ' + kb.services.filter(function (s) { return s.url.indexOf('/mebel-na-zakaz/') > -1 && s.url.split('/').length > 5; }).map(function (s) { return s.short.toLowerCase(); }).join(', ') + '.', wa: wa };
    if (/(гарант|сервис|обслуж|ремонт мебел|сломал|регулир)/.test(n)) return { t: kb.promises.filter(function (p) { return /^(Гарантия|Сервис)/.test(p); }).join('\n'), wa: wa };
    if (/(3d|3д|проект|дизайн|визуал|эскиз)/.test(n)) return { t: kb.promises[1] + '\n\n' + kb.steps.slice(0, 3).join('\n'), wa: wa };
    if (/(материал|фасад|мдф|лдсп|шпон|массив|камен|фурнитур)/.test(n)) return { t: 'Работаем с материалами: ' + kb.materials.join(', ').toLowerCase() + '. Подбираем под задачу, нагрузку и бюджет и показываем в 3D-проекте до изготовления.', wa: wa };
    if (/(замер|выезд)/.test(n)) return { t: kb.steps[0] + ' Договориться о замере проще всего в WhatsApp.', wa: 'Здравствуйте! Хочу записаться на замер' };
    var dHit = kb.districts.filter(function (x) { return n.indexOf(norm(x).slice(0, 6)) > -1; })[0];
    if (dHit || /(район|адрес|где вы|выезж|приезж|город)/.test(n)) return { t: (dHit ? 'Да, работаем в районе «' + dHit + '». ' : '') + 'Работаем во всех районах ' + (kb.city_gen || kb.city) + ': ' + kb.districts.join(', ') + '.', wa: wa };
    if (/(телефон|номер|связ|позвон|whatsapp|ватсап|график|время работ|часы)/.test(n)) return { t: 'Телефон: ' + kb.phone + '. ' + kb.hours + '. Быстрее всего — написать в WhatsApp и приложить фото или планировку.', wa: wa };
    if (/(этап|как работ|порядок|процесс|шаг)/.test(n)) return { t: 'Как работаем:\n' + kb.steps.join('\n'), wa: wa };
    var qs = stems(q); if (!qs.length) return null;
    function score(text) { var t = stems(text), s = 0; qs.forEach(function (x) { if (t.indexOf(x) > -1) s++; }); return s; }
    var best = null, bs = 0;
    kb.faq.forEach(function (f) { var s = score(f.q) * 2 + score(f.a); if (s > bs) { bs = s; best = { t: f.a + '\n\nПодробнее: ' + f.url, wa: wa }; } });
    kb.services.forEach(function (sv) { var s = score(sv.name) * 2 + score(sv.includes.join(' ')); if (s > bs) { bs = s; best = { t: sv.lead + '\n\nЧто входит: ' + sv.includes.join('; ').toLowerCase() + '.\n\nПодробнее: ' + sv.url, wa: sv.wa }; } });
    return bs >= 2 ? best : null;
  }
  function fallback(q) { return { t: 'Точно на этот вопрос ответит специалист. Напишите в WhatsApp — вопрос уже в сообщении.', wa: 'Здравствуйте! Вопрос из чата: ' + q }; }

  function ask(q) {
    q = (q || '').trim(); if (!q || busy) return;
    userMsg(q); busy = true;
    var typing = el('div', 'typing', 'Печатает…'); $('.chat-b', chat).appendChild(typing); scrollDown();
    history_.push({ role: 'user', content: q }); history_ = history_.slice(-8);
    var done = function (a) { typing.remove(); busy = false; botMsg(a.t, a.wa); history_.push({ role: 'assistant', content: a.t }); };
    var ctrl = w.AbortController ? new AbortController() : null, timer = setTimeout(function () { ctrl && ctrl.abort(); }, 15000);
    loadKb().then(function () {
      return fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages: history_ }), signal: ctrl ? ctrl.signal : undefined });
    }).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (j) {
      clearTimeout(timer);
      if (!j || !j.reply) throw 0;
      done({ t: j.reply, wa: 'Здравствуйте! Вопрос из чата: ' + q });
    }).catch(function () {
      clearTimeout(timer);
      if (!kb) { done(fallback(q)); return; }
      done(localAnswer(q) || fallback(q));
    });
  }
})();
