const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').resolve(__dirname,'../../../talabat-core.js'),'utf8');
const enterCode=source.slice(source.indexOf('  function enter(user)'),source.indexOf('  /* ---------- API ---------- */'));
const startCode=source.slice(source.indexOf('    start: function (role, cb)'),source.indexOf('    reload: function ()'));
const connection=source.match(/  function isConnectionError\(e\) \{[\s\S]*?\n  \}/)?.[0]||'';
function harness(error,kind){const seen={login:0,recovery:0,ready:0};const sb={from:()=>({select:()=>({eq:()=>({single:async()=>({error,data:!error?{id:'test',role:'customer'}:null})})})}),auth:{onAuthStateChange(){},getSession:async()=>({error,data:{session:null}})}};
const ctx={window:{supabase:{createClient:()=>sb}},location:{hash:''},SB_URL:'test',SB_KEY:'public',connectionFetch(){},sb,ME:null,need:'customer',ALL_PERMS:[],MYPERMS:[],recoveryPending:false,bootShow(){},bootHide(){},bootFail(){seen.recovery++},showLogin(){seen.login++},authErr:()=> 'error',t:x=>x,logoutBtn(){},refresh:async()=>{},finAccess:async()=>{},$:()=>null,subscribeRealtime(){},startScheduler(){},onReady(){seen.ready++},me(){return ctx.ME},console,Promise,setTimeout};vm.createContext(ctx);vm.runInContext(connection+'\n'+enterCode+'\nvar api={'+startCode+'};',ctx);return {ctx,seen};}
(async()=>{
let h=harness({message:'TypeError: Failed to fetch'});await h.ctx.enter({id:'test'});assert.equal(h.seen.recovery,1,'profile network failure must show recovery, not credentials');assert.equal(h.seen.login,0);
h=harness(null);await h.ctx.enter({id:'test'});assert.equal(h.seen.ready,1,'successful profile must still enter app');
h=harness({message:'Failed to fetch'});h.ctx.api.start('customer',()=>{});await new Promise(setImmediate);assert.equal(h.seen.recovery,1,'session network failure must preserve recovery path');assert.equal(h.seen.login,0);
h=harness({code:'refresh_token_not_found',message:'Invalid Refresh Token: Refresh Token Not Found'});h.ctx.api.start('customer',()=>{});await new Promise(setImmediate);assert.equal(h.seen.login,1,'invalid session must still require normal login');assert.equal(h.seen.recovery,0);
console.log('PASS profile/session transport recovery, valid profile and invalid session');
})().catch(e=>{console.error(e);process.exitCode=1});
