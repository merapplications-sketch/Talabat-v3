"""Local customer fixture for the affected C/H checks; not imported by the application."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
s=(root/'tools/qa_all.py').read_text().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE','"customer"')
s=s.replace(' if(window.__EMPTY)',"""
 window.__C_TABLES=T;window.__C_CALLS=[];window.__C_MODE='point';window.__C_DELAY=0;window.__C_AGE=2;
 T.orders=T.orders.filter(o=>o.id==='ord1');Object.assign(T.orders[0],{status:'pickedup',driver_id:U,prep_time:18});
 if(window.__C_SCENE==='browseMulti')T.orders.push(Object.assign({},T.orders[0],{id:'ord-extra',status:'preparing'}));
 if(window.__C_SCENE==='preparing')T.orders[0].status='preparing';
 if(window.__C_SCENE==='ready')T.orders[0].status='ready';
 if(window.__C_SCENE==='browseNone')T.orders[0].status='delivered';
 if(window.__C_SCENE==='none')window.__C_MODE='none';
 if(window.__C_SCENE==='loading')window.__C_DELAY=120000;
 if(window.__C_SCENE==='older')window.__C_AGE=15;
 if(window.__C_SCENE==='mapFail')window.__C_MAPFAIL=true;
 if(window.__C_SCENE==='missing')window.__C_MODE='missing';
 if(window.__C_SCENE==='invalid')window.__C_MODE='invalid';
 if(window.__C_SCENE==='error')window.__C_MODE='error';
 if(window.__EMPTY)""",1)
s+='''
(function(){const orig=supabase.createClient;supabase.createClient=function(){const c=orig.apply(this,arguments),rpc=c.rpc;c.rpc=function(n,a){if(n!=='order_courier_position')return rpc.call(c,n,a);window.__C_CALLS.push({name:n,args:a,at:Date.now()});const mode=window.__C_MODE,age=window.__C_AGE;let timer,finish;const result=new Promise(resolve=>{finish=resolve;timer=setTimeout(()=>resolve(mode==='error'?{data:null,error:{message:'fixture rejection'}}:{error:null,data:mode==='none'?null:[{lat:mode==='invalid'?99:38.56,lng:68.78,acc:15,updated_at:mode==='missing'?null:new Date(Date.now()-age*60000).toISOString()}]}),window.__C_DELAY)});result.abortSignal=signal=>{signal.addEventListener('abort',()=>{clearTimeout(timer);window.__C_ABORTS=(window.__C_ABORTS||0)+1;finish({data:null,error:{message:'aborted'}})},{once:true});return result};return result};return c}})();
'''
(out/'customer-fixture.js').write_text(s)
