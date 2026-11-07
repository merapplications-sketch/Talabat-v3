const fs=require('node:fs'),vm=require('node:vm');
const root=process.argv[2],s=fs.readFileSync(root+'/public/talabat-core.js','utf8');
const err=s.slice(s.indexOf('  function errKey('),s.indexOf('  /* Versioned fulfillment'));
const done=s.slice(s.indexOf('  function done('),s.indexOf('  function storeByName('));
const logs=[],marker='SYNTHETIC_PRIVATE_MARKER';let refreshes=0;
const c={console:{error:(...a)=>logs.push(a)},toast:()=>{},t:x=>x,refresh:async()=>{refreshes++;}};vm.createContext(c);vm.runInContext(err+done,c);
(async()=>{const rejected=c.done({error:{message:marker,details:marker,token:marker}});const accepted=await c.done({data:{ok:true}});console.log(JSON.stringify({raw_marker_logged:JSON.stringify(logs).includes(marker),rejected,accepted,refreshes,logs},null,2));})();
