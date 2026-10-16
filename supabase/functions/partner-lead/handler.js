/* partner-lead — server side of the public partner page (partner.html). NOT DEPLOYED.
   1. only POST from the allowed site origins, small JSON body
   2. Cloudflare Turnstile token checked HERE with the secret key (single use, action, hostname)
   3. phone normalized; phone and client address turned into keyed hashes (HMAC-SHA256, secret LEAD_HASH_KEY)
   4. lead_submit() called with the service role (the database refuses it from anon / signed-in users)
   Missing settings or a failed check = refused; never a success the server did not confirm.
   Logs: only the result code (no name, phone, token, address or key).
   Plain JS (runs in Deno and in Node 22 for the tests). */
const CATS = ['rest', 'grocery', 'pharmacy', 'beauty', 'flowers', 'gifts', 'shops', 'sweets'];
const NEED = ['TURNSTILE_SECRET_KEY', 'LEAD_HASH_KEY', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'PARTNER_ORIGINS'];

export function normPhone(v) {
  const d = String(v == null ? '' : v).replace(/\D/g, '');
  if (/^992[0-9]{9}$/.test(d)) return '+' + d;
  if (/^[0-9]{9}$/.test(d)) return '+992' + d;
  if (/^0[0-9]{9}$/.test(d)) return '+992' + d.slice(1);
  return null;
}

async function hmac(key, text) {
  const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(key), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = new Uint8Array(await crypto.subtle.sign('HMAC', k, new TextEncoder().encode(text)));
  return Array.from(sig, (b) => b.toString(16).padStart(2, '0')).join('');
}

export function makeHandler(env, deps) {
  const doFetch = (deps && deps.fetch) || fetch;
  const log = (deps && deps.log) || ((o) => console.log(JSON.stringify(o)));
  const list = (v) => String(v || '').split(',').map((x) => x.trim()).filter(Boolean);
  const origins = list(env.PARTNER_ORIGINS);
  const hosts = list(env.TURNSTILE_HOSTNAMES).length ? list(env.TURNSTILE_HOSTNAMES) : origins.map((o) => { try { return new URL(o).hostname; } catch (e) { return ''; } }).filter(Boolean);
  const missing = NEED.filter((k) => !env[k]).concat(String(env.LEAD_HASH_KEY || '').length < 32 ? ['LEAD_HASH_KEY (32+ chars)'] : []);

  return async function handle(req) {
    const origin = req.headers.get('origin') || '';
    const allowed = origins.includes(origin);
    const cors = allowed ? { 'Access-Control-Allow-Origin': origin, 'Vary': 'Origin', 'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'content-type, apikey, authorization, x-client-info', 'Access-Control-Max-Age': '600' } : { 'Vary': 'Origin' };
    const out = (status, result) => { log({ fn: 'partner-lead', result }); return new Response(JSON.stringify({ result }), { status, headers: Object.assign({ 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }, cors) }); };

    if (req.method === 'OPTIONS') return new Response(null, { status: allowed ? 204 : 403, headers: cors });
    if (!allowed) return out(403, 'origin');
    if (req.method !== 'POST') return out(405, 'method');
    if (missing.length) return out(503, 'unavailable');           // settings missing → refuse, no fake success

    let body;
    try {
      const raw = await req.text();
      if (raw.length > 4096) return out(400, 'bad_value');
      body = JSON.parse(raw);
    } catch (e) { return out(400, 'bad_value'); }
    if (!body || typeof body !== 'object') return out(400, 'bad_value');
    const name = String(body.name || '').replace(/\s+/g, ' ').trim(), cat = String(body.category || ''), phone = normPhone(body.phone), token = String(body.token || '');
    if (name.length < 2 || name.length > 80 || !CATS.includes(cat)) return out(400, 'bad_value');
    if (!phone) return out(400, 'bad_phone');
    if (body.website) return out(403, 'verify_failed');            // hidden field filled = not a person; refused like a failed check
    if (!token || token.length > 2048) return out(403, 'verify_failed');

    const ip = (req.headers.get('cf-connecting-ip') || (req.headers.get('x-forwarded-for') || '').split(',')[0] || req.headers.get('x-real-ip') || '').trim() || 'unknown';
    let v;
    try {
      const r = await doFetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST',
        body: new URLSearchParams({ secret: env.TURNSTILE_SECRET_KEY, response: token, remoteip: ip === 'unknown' ? '' : ip }) });
      if (!r.ok) return out(503, 'unavailable');
      v = await r.json();
    } catch (e) { return out(503, 'unavailable'); }
    if (!v || v.success !== true || v.action !== 'partner_lead' || !hosts.includes(String(v.hostname || ''))) return out(403, 'verify_failed');

    let ans;
    try {
      const key = env.SUPABASE_SERVICE_ROLE_KEY, h = { 'Content-Type': 'application/json', apikey: key };
      if (/^eyJ/.test(key)) h.Authorization = 'Bearer ' + key;     // legacy JWT key; the new sb_secret_ key goes in apikey only
      const r = await doFetch(String(env.SUPABASE_URL).replace(/\/$/, '') + '/rest/v1/rpc/lead_submit', { method: 'POST', headers: h,
        body: JSON.stringify({ p_name: name, p_category: cat, p_phone: phone, p_phone_key: await hmac(env.LEAD_HASH_KEY, 'phone:' + phone),
          p_client_key: await hmac(env.LEAD_HASH_KEY, 'ip:' + ip) }) });
      if (!r.ok) return out(503, 'unavailable');
      ans = await r.json();
    } catch (e) { return out(503, 'unavailable'); }
    if (ans === 'ok') return out(200, 'ok');                       // new, duplicate or phone limit: the same answer
    if (ans === 'busy') return out(429, 'busy');
    if (ans === 'bad_value') return out(400, 'bad_value');
    return out(503, 'unavailable');
  };
}
