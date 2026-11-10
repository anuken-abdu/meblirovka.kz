// ИИ-консультант: серверная функция Vercel. Ключ — только в Environment Variables:
// Vercel → Settings → Environment Variables → ANTHROPIC_API_KEY.
// Без ключа отвечает 503, и сайт сам переключается на встроенный автоответчик.
const KB = { ru: require('./kb.json'), kk: require('./kb-kk.json') };

const MODEL = process.env.CHAT_MODEL || 'claude-haiku-5-5';

function systemPrompt(kb) {
  const services = kb.services.map(s => `- ${s.name} (${s.url}): ${s.lead} Входит: ${s.includes.join('; ')}.`).join('\n');
  const faq = kb.faq.map(f => `В: ${f.q}\nО: ${f.a}`).join('\n');
  return `Ты — ИИ-консультант сайта «${kb.brand}»: ${kb.tagline.toLowerCase()}, ${kb.city}.
${kb.ai_lang}, коротко (2–4 предложения), дружелюбно, без эмодзи и markdown. Если пользователь пишет на другом языке (русский или казахский), отвечай на его языке.
Отвечай ТОЛЬКО по базе знаний ниже. Не придумывай цены, сроки изготовления, сроки гарантии, скидки, отзывы, адреса — их нет в базе.
Если вопрос о цене: ${kb.price}
Если ответа нет в базе — предложи написать в WhatsApp или позвонить: ${kb.phone}, ${kb.hours}.
Где уместно, дай ссылку на страницу услуги.

О компании: ${kb.about}
Гарантии и сервис: ${kb.promises.join('; ')}.
Материалы: ${kb.materials.join(', ')}.
Районы: ${kb.districts.join(', ')}.
Как работаем: ${kb.steps.join('; ')}.
От чего зависит цена: ${kb.price_factors.join('; ')}.

Услуги:
${services}

Частые вопросы:
${faq}`;
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') { res.status(405).json({ error: 'method' }); return; }
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) { res.status(503).json({ error: 'no_key' }); return; }
  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = {}; } }
  const kb = KB[(body && body.lang) === 'kk' ? 'kk' : 'ru'];
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = {}; } }
  const msgs = Array.isArray(body && body.messages) ? body.messages : [];
  const clean = msgs
    .filter(m => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
    .slice(-8)
    .map(m => ({ role: m.role, content: m.content.slice(0, 600) }));
  while (clean.length && clean[0].role !== 'user') clean.shift();
  if (!clean.length) { res.status(400).json({ error: 'empty' }); return; }
  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
      body: JSON.stringify({ model: MODEL, max_tokens: 400, system: systemPrompt(kb), messages: clean })
    });
    if (!r.ok) { res.status(502).json({ error: 'upstream' }); return; }
    const j = await r.json();
    const reply = (j.content || []).filter(c => c.type === 'text').map(c => c.text).join('\n').trim();
    if (!reply) { res.status(502).json({ error: 'empty_reply' }); return; }
    res.setHeader('Cache-Control', 'no-store');
    res.status(200).json({ reply });
  } catch (e) {
    res.status(502).json({ error: 'fail' });
  }
};
