// TALABOT — Edge Function «route», SINGLE FILE for the dashboard editor. GENERATED from index.ts + handler.js + config.js +
// providers.js (same code) — edit those, then regenerate. Prepared for review — NOT deployed.
// TALABOT navigation facade (same Edge Function name). Prepared, NOT deployed.
// Selected provider: Geoapify. Set policy/key and deploy only in the separately authorized activation step.
// SUPABASE_URL and the project's public key (SUPABASE_ANON_KEY or SUPABASE_PUBLISHABLE_KEYS) are provided by Supabase.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.45.4';

// ---- config.js
// One server-owned policy; no navigation provider key or editable policy in browser storage.
const EXTERNAL_IDS = ['yandex', '2gis', 'google'];
function navigationConfig(env) {
  let x = {}; try { x = JSON.parse(env.NAVIGATION_CONFIG || '{}'); } catch { return { invalid: true, internal: false, external: false, providers: [], provider: 'none', revision: 'invalid' }; }
  const bounded = (v, def, lo, hi) => Number.isFinite(v) ? Math.max(lo, Math.min(hi, v)) : def;
  const providers = EXTERNAL_IDS.filter(id => !Array.isArray(x.externalProviders) || x.externalProviders.includes(id));
  return {
    revision: String(x.revision || 'navigation-v1'), provider: String(x.provider || 'geoapify'),
    internal: x.internal === true, external: x.external !== false, providers,
    defaultExternal: providers.includes(x.defaultExternal) ? x.defaultExternal : providers[0],
    dailyCredits: bounded(x.dailyCredits, 2400, 0, 3000), accountCredits: 3000,
    // Credits per request: routeCredits() below. Old `reservationCredits` / `detailsCredits` keys are ignored (no `details`
    // option is requested any more, so no unpublished surcharge exists to estimate).
    rps: bounded(x.rps, 4, 1, 4),
    maxStraightKm: bounded(x.maxStraightKm, 60, 1, 60), cacheMs: 60000, timeoutMs: 7000,
    configTtlMs: 30000, refreshMs: 120000, deviationM: 60, deviationHoldMs: 5000, gpsMaxAgeMs: 30000,
  };
}
function publicConfig(c, reason = null) {
  return { revision: c.revision, provider: c.provider, internal: c.internal && !c.invalid,
    external: c.external, providers: c.providers, defaultExternal: c.defaultExternal,
    configTtlMs: c.configTtlMs || 30000, refreshMs: c.refreshMs || 120000,
    deviationM: c.deviationM || 60, deviationHoldMs: c.deviationHoldMs || 5000, gpsMaxAgeMs: c.gpsMaxAgeMs || 30000,
    mode: c.internal && !reason ? 'internal' : 'tracking', reason };
}
function validPoint(p) {
  return Array.isArray(p) && p.length === 2 && p.every(v => typeof v === 'number' && Number.isFinite(v)) &&
    Math.abs(p[0]) <= 90 && Math.abs(p[1]) <= 180 && !(p[0] === 0 && p[1] === 0);
}
function externalLinks(c, to) {
  if (!c.external || !validPoint(to)) return [];
  const ll = to.join(','), xy = [to[1], to[0]].join(',');
  // Provider-documented coordinates: Yandex/Google lat,lng; 2GIS lng,lat. Never text search.
  const urls = {
    yandex: { name: 'Yandex Maps', app: 'yandexmaps://maps.yandex.ru/?rtext=' + encodeURIComponent('~' + ll) + '&rtt=auto', web: 'https://yandex.ru/maps/?rtext=' + encodeURIComponent('~' + ll) + '&rtt=auto' },
    '2gis': { name: '2GIS', app: 'https://2gis.ru/directions/tab/car/points/|' + xy, web: 'https://2gis.ru/directions/tab/car/points/|' + xy },
    google: { name: 'Google Maps', app: 'https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(ll) + '&travelmode=driving&dir_action=navigate', web: 'https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(ll) + '&travelmode=driving&dir_action=navigate' },
  };
  return c.providers.map(id => ({ id, ...urls[id] }));
}

// Geoapify Routing credits for the ONE restricted request this function sends (providers.js): exactly 2 waypoints (one pair),
// mode=drive, lang=ru, no `details` (route_details / elevation add credits; instruction_details has no published price) and
// no other option. Official rule (apidocs.geoapify.com/docs/routing, «Pricing»): 1 credit per waypoint pair, «1 credit for every
// 500 km (or partial 500 km) of route distance»; published example: a 630 340 m route costs 2 credits.
// -> one pair costs max(1, ceil(km / 500)). Before the call the road length is unknown and Geoapify has no maximum-length
// option, so the only documented pre-call amount is the 1-credit minimum; it is NOT a ceiling (see plan section 11).
const REQUEST_PAIRS = 1;
function routeCredits(distanceM) {
  const km = Math.max(0, +distanceM || 0) / 1000;
  return REQUEST_PAIRS * Math.max(1, Math.ceil(km / 500));
}

// ---- providers.js
// Only the selected upstream is implemented. Future adapters implement calculate(ctx) -> normalized route.
// No secondary provider / paid fallback. Existing ORS integration is retained in Git history, not called implicitly.
const geoapify = {
  configured: env => !!env.GEOAPIFY_KEY,
  async calculate({ from, to, env, fetch, signal, now }) {
    const url = new URL('https://api.geoapify.com/v1/routing');
    // Restricted request with a published price (config.js routeCredits): 2 waypoints, drive, ru, NO `details` option.
    // Steps keep text instructions and indices by default; the maneuver type (instruction_details) is not requested.
    url.search = new URLSearchParams({ waypoints: from.join(',') + '|' + to.join(','), mode: 'drive', lang: 'ru', apiKey: env.GEOAPIFY_KEY }).toString();
    const r = await fetch(url.toString(), { signal, headers: { Accept: 'application/geo+json' } });
    if (r.status === 429) throw new Error('quota');
    if (r.status === 401 || r.status === 403) throw new Error('provider_denied');
    if (!r.ok) throw new Error('upstream');
    const g = await r.json(), f = g?.features?.[0], p = f?.properties, geom = f?.geometry;
    const lines = geom?.type === 'MultiLineString' ? geom.coordinates : geom?.type === 'LineString' ? [geom.coordinates] : [];
    if (!p || !Number.isFinite(p.distance) || p.distance < 0 || !Number.isFinite(p.time) || p.time < 0 || !lines.length) throw new Error('no_route');
    const coords = [], steps = [];
    lines.forEach((line, leg) => {
      if (!Array.isArray(line) || line.length < 2 || line.some(v => !Array.isArray(v) || !validPoint([v[1], v[0]]))) throw new Error('no_route');
      if(coords.length + line.length > 30000) throw new Error('no_route');
      const offset = coords.length;
      coords.push(...line.map(v => [v[1], v[0]]));
      (p.legs?.[leg]?.steps || []).forEach(s => {
        if (!Number.isInteger(s.from_index) || !Number.isInteger(s.to_index) || s.from_index < 0 || s.to_index < s.from_index || s.to_index >= line.length) throw new Error('no_route');
        if(!Number.isFinite(s.time)||s.time<0||!Number.isFinite(s.distance)||s.distance<0)throw new Error('no_route');
        steps.push({ from: offset + s.from_index, to: offset + s.to_index, distanceM: +s.distance || 0,
          durationS: +s.time || 0, instruction: String(s.instruction?.text || ''), maneuver: String(s.instruction?.type || '') });
      });
    });
    // Do not thin original geometry: maneuver indices must continue to address the same points.
    if (coords.length > 30000 || steps.length > 5000) throw new Error('no_route');
    return { coords, distance_m: Math.round(p.distance), duration_s: Math.round(p.time), steps,
      source: 'geoapify', attribution: 'Powered by Geoapify | © OpenStreetMap contributors', calculated_at: now() };
  },
};
const providers = Object.freeze({ geoapify });

const defaultProviders = providers;
// ---- handler.js
// Prepared, NOT deployed. Authenticated navigation policy + one upstream behind a uniform contract.
const LIMITS = { maxStraightKm: 60, perUserPerMinute: 12, timeoutMs: 7000 };
function km(a,b) { const r=v=>v*Math.PI/180, h=Math.sin(r(b[0]-a[0])/2)**2+Math.cos(r(a[0]))*Math.cos(r(b[0]))*Math.sin(r(b[1]-a[1])/2)**2; return 6371*2*Math.asin(Math.sqrt(Math.min(1,h))); }
function makeHandler({ fetch, env, getUser, reserveBudget, settleBudget, now = () => Date.now(), providers = defaultProviders }) {
  const cache = new Map(), hits = new Map();
  return async req => {
    // Origins compared as the browser sends them (scheme://host[:port]): spaces, quotes, a trailing «/» or a full page URL
    // pasted into the secret are reduced to that origin.
    const asOrigin=v=>{v=v.trim().replace(/^["']+|["']+$/g,'');try{return new URL(v).origin;}catch{return v.replace(/\/+$/,'');}};
    const c = navigationConfig(env), allowed = String(env.ALLOWED_ORIGINS || '').split(',').map(asOrigin).filter(v=>v&&v!=='null');
    const origin = req.headers.get('origin') || '';
    const headers = { 'Access-Control-Allow-Origin': allowed.includes(origin) ? origin : (allowed[0] || 'null'),
      'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type', 'Access-Control-Allow-Methods': 'POST, OPTIONS', Vary: 'Origin', 'Content-Type': 'application/json', 'Cache-Control': 'no-store' };
    const out = (status,body)=>new Response(JSON.stringify(body),{status,headers});
    // A preflight from a non-allowed origin answers 403 (was 200 with another origin's header: the browser then silently
    // dropped the POST and the log showed only «OPTIONS 200»).
    // Limited diagnostic on refusal only: received Origin + parsed allow-list (origins only — no headers, keys, sessions, body).
    const refuse=()=>{console.warn(JSON.stringify({route_cors:'refused',method:req.method,origin:JSON.stringify(origin).slice(0,200),allowed}));return out(403,{error:'origin'});};
    if(req.method==='OPTIONS') return allowed.length&&origin&&!allowed.includes(origin)?refuse():out(200,{});
    if(req.method!=='POST') return out(405,{error:'method'});
    if(allowed.length && origin && !allowed.includes(origin)) return refuse();
    const user=await getUser(req.headers.get('authorization')||'').catch(()=>null);
    if(!user) return out(401,{error:'auth'});
    let b; try { b=await req.json(); } catch { return out(400,{error:'bad_value'}); }
    const adapter=Object.prototype.hasOwnProperty.call(providers,c.provider) ? providers[c.provider] : null;
    const reason=c.invalid?'invalid_config':!c.internal?'disabled':!adapter?'unsupported_provider':!adapter.configured(env)?'not_configured':null;
    const config=publicConfig(c,reason), fallback=(why,retry=30)=>out(200,{mode:'tracking',reason:why,retry_after_s:retry,config:{...config,mode:'tracking',reason:why}});
    if(b?.op==='config') return out(200,config);
    if(b?.op==='links') return validPoint(b.to)?out(200,{config,links:externalLinks(c,b.to)}):out(400,{error:'bad_value'});
    if(!validPoint(b?.from)||!validPoint(b?.to)) return out(400,{error:'bad_value'});
    if(reason) return fallback(reason);
    if(km(b.from,b.to)>c.maxStraightKm) return fallback('too_far');
    const t=now(), hk=user+':'+Math.floor(t/60000), n=(hits.get(hk)||0)+1;
    hits.set(hk,n); if(hits.size>5000) hits.clear();
    if(n>LIMITS.perUserPerMinute) return fallback('rate',60);
    // Exact coordinates: rounded cache keys must not silently reuse a different customer pin.
    const ck=JSON.stringify([c.revision,c.provider,b.from,b.to]), hit=cache.get(ck);
    // Always check the global ledger, even cache hits: exhaustion/disable must not show an apparently current ETA.
    // Both ledger calls must be bound: an upstream call is only made when its cost can be recorded afterwards.
    if(!reserveBudget||!settleBudget) return fallback('budget_unavailable');
    const cached=hit&&t-hit.at<c.cacheMs;
    // ONE id per route call: the reservation and its settlement are the same ledger row.
    const requestId=crypto.randomUUID();
    let reservation;
    const reserved=cached?0:routeCredits(0);           // documented minimum (1); not a ceiling — see config.js
    try { reservation=await reserveBudget({ provider:c.provider, credits:reserved,
      dailyCap:c.dailyCredits, rps:c.rps, requestId }); } catch { return fallback('budget_unavailable'); }
    if(reservation?.allowed!==true) return fallback(reservation?.reason==='rate'?'rate':reservation?.reason==='quota'?'quota':'budget_unavailable',Math.min(300,Math.max(1,+reservation?.retryAfterS||30)));
    if(cached) return out(200,{...hit.data,mode:'internal',config});
    const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),c.timeoutMs);
    let data=null,failure=null;
    try { data=await adapter.calculate({from:b.from,to:b.to,env,fetch,signal:ctl.signal,now}); }
    catch(e) { failure=e; }
    finally { clearTimeout(timer); }
    // Settle EVERY upstream call before anything else (also before the config_changed check): total = real cost from the
    // returned length; on failure / timeout the reservation is kept (no refund). Same id, idempotent, so retries are safe.
    // Only {recorded:true} counts. Unconfirmed -> no route is returned; the row stays «unsettled» and, once older than 60 s,
    // the ledger refuses every further request (all instances) until it is settled — no further unrecorded upstream use.
    const total=data?routeCredits(data.distance_m):reserved;
    let recorded=false;
    for(let i=0;i<3&&!recorded;i++){
      let s=null; try { s=await settleBudget({ provider:c.provider, requestId, credits:total }); } catch { s=null; }
      if(s?.recorded===true) recorded=true; else if(s&&['conflict','unknown_request','bad_value'].includes(s.reason)) break;
    }
    if(!recorded) return fallback('budget_unavailable');
    if(failure) return fallback(['quota','provider_denied','no_route'].includes(failure?.message)?failure.message:'upstream');
    // Configuration can be revoked while an upstream request is pending. Never return its old policy result.
    const next=navigationConfig(env);
    if(JSON.stringify(next)!==JSON.stringify(c)) return fallback('config_changed',1);
    cache.set(ck,{at:now(),data}); if(cache.size>500)cache.delete(cache.keys().next().value);
    return out(200,{...data,mode:'internal',config});
  };
}

// ---- index.ts

// Server-only configuration; defaults keep internal routing disabled until explicitly activated.
const env = {
  NAVIGATION_CONFIG: Deno.env.get('NAVIGATION_CONFIG') ?? '',
  GEOAPIFY_KEY: Deno.env.get('GEOAPIFY_KEY') ?? '',
  ALLOWED_ORIGINS: Deno.env.get('ALLOWED_ORIGINS') ?? '',
};

// The project uses the new publishable key; SUPABASE_ANON_KEY is the legacy name. Use whichever Supabase provides.
function publicKey(): string {
  const legacy = Deno.env.get('SUPABASE_ANON_KEY');
  if (legacy) return legacy;
  const raw = Deno.env.get('SUPABASE_PUBLISHABLE_KEYS') ?? '';
  try { const v = JSON.parse(raw); const first = typeof v === 'string' ? v : Object.values(v ?? {})[0]; if (typeof first === 'string') return first; } catch { /* plain value */ }
  return raw;
}

async function getUser(authorization: string): Promise<string | null> {
  if (!authorization.startsWith('Bearer ')) return null;
  const sb = createClient(Deno.env.get('SUPABASE_URL')!, publicKey(), {
    global: { headers: { Authorization: authorization } },
  });
  const { data, error } = await sb.auth.getUser();
  return error || !data?.user ? null : data.user.id;
}

// Bound to patch 40 `navigation_reserve_budget` (proposed, applied only after approval). Missing RPC / key / timeout /
// malformed answer -> tracking-only, never unmetered upstream calls.
// Service key under either name (legacy service_role / new secret keys). Server-side only; never sent to the browser.
function serviceKey(): string {
  const legacy = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if (legacy) return legacy;
  const raw = Deno.env.get('SUPABASE_SECRET_KEYS') ?? '';
  try { const v = JSON.parse(raw); const first = typeof v === 'string' ? v : Object.values(v ?? {})[0]; if (typeof first === 'string') return first; } catch { /* plain value */ }
  return raw;
}

async function reserveBudget(v: { provider: string; credits: number; dailyCap: number; rps: number; requestId: string }) {
  const key = serviceKey();
  if (!key) throw new Error('budget_unavailable');
  const sb = createClient(Deno.env.get('SUPABASE_URL')!, key, { auth: { persistSession: false } });
  const result = await sb.rpc('navigation_reserve_budget', {
    p_provider: v.provider, p_credits: v.credits, p_daily_cap: v.dailyCap, p_rps: v.rps, p_request_id: v.requestId,
  }).abortSignal(AbortSignal.timeout(3000));
  if (result.error) throw new Error('budget_unavailable');
  return result.data;
}
// Settlement of ONE route call (same request id as its reservation). Any RPC error / timeout -> throw (the handler retries
// with the same id, then withholds the route); the answer is returned as is and only {recorded:true} counts.
async function settleBudget(v: { provider: string; credits: number; requestId: string }) {
  const key = serviceKey();
  if (!key) throw new Error('budget_unavailable');
  const sb = createClient(Deno.env.get('SUPABASE_URL')!, key, { auth: { persistSession: false } });
  const result = await sb.rpc('navigation_settle_budget', { p_provider: v.provider, p_request_id: v.requestId, p_total_credits: v.credits })
    .abortSignal(AbortSignal.timeout(3000));
  if (result.error) throw new Error('budget_unavailable');
  return result.data;
}
Deno.serve(makeHandler({ fetch, env, getUser, reserveBudget, settleBudget }));
