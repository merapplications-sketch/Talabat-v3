// Prepared, NOT deployed. Authenticated navigation policy + one upstream behind a uniform contract.
import { navigationConfig, publicConfig, externalLinks, validPoint, routeCredits } from './config.js';
import { providers as defaultProviders } from './providers.js';
export const LIMITS = { maxStraightKm: 60, perUserPerMinute: 12, timeoutMs: 7000 };
function km(a,b) { const r=v=>v*Math.PI/180, h=Math.sin(r(b[0]-a[0])/2)**2+Math.cos(r(a[0]))*Math.cos(r(b[0]))*Math.sin(r(b[1]-a[1])/2)**2; return 6371*2*Math.asin(Math.sqrt(Math.min(1,h))); }
export function makeHandler({ fetch, env, getUser, reserveBudget, settleBudget, now = () => Date.now(), providers = defaultProviders }) {
  const cache = new Map(), hits = new Map();
  return async req => {
    const c = navigationConfig(env), allowed = String(env.ALLOWED_ORIGINS || '').split(',').map(s=>s.trim()).filter(Boolean);
    const origin = req.headers.get('origin') || '';
    const headers = { 'Access-Control-Allow-Origin': allowed.includes(origin) ? origin : (allowed[0] || 'null'),
      'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type', 'Access-Control-Allow-Methods': 'POST, OPTIONS', Vary: 'Origin', 'Content-Type': 'application/json', 'Cache-Control': 'no-store' };
    const out = (status,body)=>new Response(JSON.stringify(body),{status,headers});
    if(req.method==='OPTIONS') return out(200,{});
    if(req.method!=='POST') return out(405,{error:'method'});
    if(allowed.length && origin && !allowed.includes(origin)) return out(403,{error:'origin'});
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
    if(!reserveBudget) return fallback('budget_unavailable');
    const cached=hit&&t-hit.at<c.cacheMs;
    let reservation;
    const reserved=cached?0:routeCredits({ waypoints:2, distanceM:0, detailsCredits:c.detailsCredits });
    try { reservation=await reserveBudget({ provider:c.provider, credits:reserved,
      dailyCap:c.dailyCredits, rps:c.rps, requestId:crypto.randomUUID() }); } catch { return fallback('budget_unavailable'); }
    if(reservation?.allowed!==true) return fallback(reservation?.reason==='rate'?'rate':reservation?.reason==='quota'?'quota':'budget_unavailable',Math.min(300,Math.max(1,+reservation?.retryAfterS||30)));
    if(cached) return out(200,{...hit.data,mode:'internal',config});
    const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),c.timeoutMs);
    try {
      const data=await adapter.calculate({from:b.from,to:b.to,env,fetch,signal:ctl.signal,now});
      // Configuration can be revoked while an upstream request is pending. Never return its old policy result.
      const next=navigationConfig(env);
      if(JSON.stringify(next)!==JSON.stringify(c)) return fallback('config_changed',1);
      // Real cost after the response (length surcharge > 500 km): book the excess truthfully, even above the cap.
      const actual=routeCredits({ waypoints:2, distanceM:data.distance_m, detailsCredits:c.detailsCredits });
      if(actual>reserved){ try{ await settleBudget?.({ provider:c.provider, credits:actual-reserved, requestId:crypto.randomUUID() }); }catch{} }
      cache.set(ck,{at:now(),data}); if(cache.size>500)cache.delete(cache.keys().next().value);
      return out(200,{...data,mode:'internal',config});
    } catch(e) { return fallback(['quota','provider_denied','no_route'].includes(e?.message)?e.message:'upstream'); }
    finally { clearTimeout(timer); }
  };
}
