const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(process.argv[2],'utf8');
const start=source.indexOf('      sb.auth.onAuthStateChange(function (event)');
const code=source.slice(start,source.indexOf('      sb.auth.getSession()',start));
let callback,proofClears=0,loginCalls=0,reloads=0;
const app={textContent:'SYNTHETIC_PRIVATE_ORDER_MARKER'};
const ctx={ME:{id:'synthetic'},DB:{orders:[{note:'SYNTHETIC_PRIVATE_NOTE'}]},ORD:[{id:99}],document:{getElementById:()=>app},$:()=>app,sb:{auth:{onAuthStateChange:fn=>callback=fn}},clearProofUrls:()=>proofClears++,showLogin:()=>loginCalls++,location:{reload:()=>reloads++},setTimeout:()=>{},showPasswordRecovery:()=>{},recoveryPending:false};
vm.createContext(ctx);vm.runInContext(code,ctx);callback('SIGNED_OUT',null);
console.log(JSON.stringify({proofClears,loginCalls,reloads,appStillContainsPrivateData:app.textContent.includes('SYNTHETIC_PRIVATE_ORDER_MARKER'),cachedIdentityPresent:!!ctx.ME,cachedOrders:ctx.DB.orders.length,derivedOrders:ctx.ORD.length},null,2));
