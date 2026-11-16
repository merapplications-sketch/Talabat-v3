// BRIEF-14: no-billing no-key routing readiness. Never calls a provider or Supabase.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {makeHandler} from '../supabase/functions/route/handler.js';
import {navigationConfig} from '../supabase/functions/route/config.js';

const patch=fs.readFileSync(new URL('../sql/proposed/patch40_navigation_budget.sql',import.meta.url),'utf8');
assert.match(patch,/create or replace function public\.navigation_reserve_budget\(/i);
assert.match(patch,/create or replace function public\.navigation_settle_budget\(/i);
assert.match(patch,/revoke all on function public\.navigation_reserve_budget/i);
assert.match(patch,/grant execute on function public\.navigation_reserve_budget.*to service_role/i);
assert.match(patch,/create table if not exists public\.navigation_budget_requests/i);
let fetches=0, reservations=0, settlements=0;
const fakeFetch=async()=>{fetches++;throw Error('No provider access allowed in BRIEF-14')};
const reserveBudget=async()=>{reservations++;return {allowed:false,reason:'quota'}};
const settleBudget=async()=>{settlements++;return {recorded:false}};
const point=[38.56,68.78],to=[38.57,68.79],origin='https://app.example';
const req=()=>new Request('https://test.invalid/route',{method:'POST',headers:{
  authorization:'Bearer LOCAL_FAKE',origin,'content-type':'application/json'},
  body:JSON.stringify({from:point,to})});
const base={NAVIGATION_CONFIG:JSON.stringify({
  provider:'geoapify',internal:false,external:true,externalProviders:['google','yandex','2gis'],
  dailyCredits:0,rps:1}),GEOAPIFY_KEY:'',ALLOWED_ORIGINS:origin};
assert.equal(navigationConfig(base).internal,false);
let handler=makeHandler({fetch:fakeFetch,env:base,getUser:async()=> 'synthetic',reserveBudget,settleBudget});
let r=await (await handler(req())).json();
assert.equal(r.mode,'tracking');assert.equal(r.reason,'disabled');
console.log('NAV_OFF_NO_SUBSCRIPTION_PASS: default config disabled');
handler=makeHandler({fetch:fakeFetch,env:{...base,GEOAPIFY_KEY:'FAKE_DO_NOT_USE'},
  getUser:async()=> 'synthetic',reserveBudget,settleBudget});
r=await (await handler(req())).json();
assert.equal(r.mode,'tracking');assert.equal(r.reason,'disabled');
assert.equal(fetches,0);assert.equal(reservations,0);assert.equal(settlements,0);
console.log('NAV_OFF_FAKE_KEY_PASS: mock key cannot bypass disabled policy; zero provider/budget calls');
handler=makeHandler({fetch:fakeFetch,env:{...base,NAVIGATION_CONFIG:JSON.stringify({
  internal:true,provider:'geoapify',dailyCredits:0,rps:1})},
  getUser:async()=> 'synthetic',reserveBudget,settleBudget});
r=await (await handler(req())).json();
assert.equal(r.mode,'tracking');assert.equal(r.reason,'not_configured');
assert.equal(fetches,0);
console.log('NAV_OFF_NO_REAL_KEY_PASS: missing secret fails closed');
const activated={...base,GEOAPIFY_KEY:'FAKE_DO_NOT_USE',
  NAVIGATION_CONFIG:JSON.stringify({internal:true,provider:'geoapify',dailyCredits:0,rps:1})};
handler=makeHandler({fetch:fakeFetch,env:activated,getUser:async()=> 'synthetic',
  reserveBudget,settleBudget});
r=await (await handler(req())).json();
assert.equal(r.mode,'tracking');assert.equal(r.reason,'quota');assert.equal(fetches,0);
console.log('NAV_OFF_ZERO_CREDITS_PASS: daily budget 0 blocks upstream even with synthetic key');
assert.equal(settlements,0);
console.log('NAV_OFF_SQL_READY_PASS: existing proposed patch40 reserve/settle and service-only grants verified');
