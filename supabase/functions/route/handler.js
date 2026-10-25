// Prepared, NOT deployed. Authenticated navigation policy + one upstream behind a uniform contract.
import { navigationConfig, publicConfig, externalLinks, validPoint, routeCredits } from './config.js';
import { providers as defaultProviders } from './providers.js';
export const LIMITS = { maxStraightKm: 60, perUserPerMinute: 12, timeoutMs: 7000 };
function km(a,b) { const r=v=>v*Math.PI/180, h=Math.sin(r(b[0]-a[0])/2)**2+Math.cos(r(a[0]))*Math.cos(r(b[0]))*Math.sin(r(b[1]-a[1])/2)**2; return 6371*2*Math.asin(Math.sqrt(Math.min(1,h))); }
export function makeHandler({ fetch, env, getUser, reserveBudget, settleBudget, now = () => Date.now(), providers = defaultProviders }) {
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
