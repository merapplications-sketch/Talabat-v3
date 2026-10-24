// TALABOT — Edge Function «route» logic (batch B, prepared for review, NOT deployed).
// Server-side proxy to OpenRouteService directions: the key stays in the function secret ORS_KEY, never in the app.
// Only signed-in users of this project; only plausible city trips; small per-instance cache and per-user rate limit
// to stay inside the free Standard quota (2 000 directions / day, 40 / minute).
// Pure module: dependencies are injected so it can be checked locally without Deno or a network.

export const LIMITS = { maxStraightKm: 60, perUserPerMinute: 12, cacheMs: 5 * 60 * 1000, timeoutMs: 7000, maxPoints: 400 };
const ORS_URL = 'https://api.openrouteservice.org/v2/directions/driving-car/geojson';

function valid(p) {
  return Array.isArray(p) && p.length === 2 && p.every((v) => typeof v === 'number' && Number.isFinite(v)) &&
    Math.abs(p[0]) <= 90 && Math.abs(p[1]) <= 180 && !(p[0] === 0 && p[1] === 0);
}
function km(a, b) {
  const R = 6371, r = (v) => v * Math.PI / 180, dl = r(b[0] - a[0]), dn = r(b[1] - a[1]);
  const h = Math.sin(dl / 2) ** 2 + Math.cos(r(a[0])) * Math.cos(r(b[0])) * Math.sin(dn / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
function thin(coords, max) {           // keep the line light for phones: at most `max` points, first and last kept
  if (coords.length <= max) return coords;
  const step = (coords.length - 1) / (max - 1), out = [];
  for (let i = 0; i < max; i++) out.push(coords[Math.round(i * step)]);
  return out;
}

export function makeHandler({ fetch, env, getUser, now = () => Date.now() }) {
  const cache = new Map(), hits = new Map();
  const allowed = String(env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean);
  return async function handle(req) {
    const origin = req.headers.get('origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': allowed.includes(origin) ? origin : (allowed[0] || 'null'),
      'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Vary': 'Origin',
    };
    const out = (status, body) => new Response(JSON.stringify(body), { status, headers: { ...cors, 'Content-Type': 'application/json' } });
    if (req.method === 'OPTIONS') return new Response('ok', { headers: cors });
    if (req.method !== 'POST') return out(405, { error: 'method' });
    if (allowed.length && origin && !allowed.includes(origin)) return out(403, { error: 'origin' });
    if (!env.ORS_KEY) return out(503, { error: 'not_configured' });
    const user = await getUser(req.headers.get('authorization') || '').catch(() => null);
    if (!user) return out(401, { error: 'auth' });
    let body; try { body = await req.json(); } catch { return out(400, { error: 'bad_value' }); }
    const from = body && body.from, to = body && body.to;
    if (!valid(from) || !valid(to)) return out(400, { error: 'bad_value' });
    if (km(from, to) > LIMITS.maxStraightKm) return out(422, { error: 'too_far' });
    const t = now(), minute = Math.floor(t / 60000), hk = user + ':' + minute, n = (hits.get(hk) || 0) + 1;
    hits.set(hk, n); if (hits.size > 5000) hits.clear();
    if (n > LIMITS.perUserPerMinute) return out(429, { error: 'rate' });
    const ck = [from, to].map((p) => p.map((v) => v.toFixed(4)).join(',')).join('|'), hit = cache.get(ck);
    if (hit && t - hit.at < LIMITS.cacheMs) return out(200, hit.data);
    const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), LIMITS.timeoutMs);
    let res;
    try {
      res = await fetch(ORS_URL, {
        method: 'POST', signal: ctl.signal,
        headers: { 'Authorization': env.ORS_KEY, 'Content-Type': 'application/json', 'Accept': 'application/geo+json' },
        body: JSON.stringify({ coordinates: [[from[1], from[0]], [to[1], to[0]]] }),   // ORS wants [lng, lat]
      });
    } catch { clearTimeout(timer); return out(502, { error: 'upstream' }); }
    clearTimeout(timer);
    if (res.status === 429 || res.status === 403) return out(503, { error: 'quota' });
    if (!res.ok) return out(502, { error: 'upstream' });
    const g = await res.json().catch(() => null), f = g && g.features && g.features[0];
    const sum = f && f.properties && f.properties.summary, line = f && f.geometry && f.geometry.coordinates;
    if (!sum || !Array.isArray(line) || line.length < 2) return out(502, { error: 'no_route' });
    const data = {
      coords: thin(line.map((c) => [c[1], c[0]]), LIMITS.maxPoints),
      distance_m: Math.round(sum.distance || 0), duration_s: Math.round(sum.duration || 0),
      source: 'openrouteservice', attribution: '© openrouteservice.org by HeiGIT | Map data © OpenStreetMap contributors',
    };
    cache.set(ck, { at: t, data }); if (cache.size > 500) cache.delete(cache.keys().next().value);
    return out(200, data);
  };
}
