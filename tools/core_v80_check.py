"""T2 (v81b): the three core functions customer v80 already calls — pointsSnapshot, pointsAbandon, orderWallet.
Mock only (qa_all fixture in memory; Chromium). Checks that v80 now uses them and that a late / failed read never
overwrites newer data. python3 tools/core_v80_check.py"""
import os,sys,json
from playwright.sync_api import sync_playwright
here=os.path.dirname(os.path.abspath(__file__));root=os.path.abspath(os.path.join(here,'..'))
FIX=open(os.path.join(here,'qa_all.py')).read().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE','"customer"')
# spy (test only): record the filters the core puts on wallet_entries reads (the qa fixture mock ignores eq outside ranges)
SPY="""(function(){var cc=window.supabase.createClient;window.__weq=[];
 function wrap(ch,rec){return new Proxy(ch,{get:function(t,p){var v=t[p];if(p==='then'||typeof v!=='function')return v;
   return function(){var a=[].slice.call(arguments);if(p==='eq'||p==='gt')rec.push([p].concat(a));var r=v.apply(t,a);return r&&(typeof r==='object'||typeof r==='function')?wrap(r,rec):r}}})}
 window.supabase.createClient=function(){var c=cc.apply(this,arguments),f=c.from;
  c.from=function(n){var ch=f.call(c,n);if(n!=='wallet_entries')return ch;var rec=[];window.__weq.push(rec);return wrap(ch,rec)};return c}})();"""
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=FIX+SPY) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
    pg.goto('file://'+root+'/customer.html',wait_until='domcontentloaded');pg.wait_for_timeout(2500);E=pg.evaluate
    ok(E("()=>['pointsSnapshot','pointsAbandon','orderWallet'].every(k=>typeof TLB[k]=='function')"),'core: the 3 functions v80 calls exist')
    r=E("async()=>{const x=await TLB.pointsSnapshot();return x&&{n:x.rows.length,bal:x.balance,cons:x.consistent,same:JSON.stringify(TLB.points())==JSON.stringify(x.rows)}}")
    ok(r and r['n']>0 and r['same'] and r['bal'] is not None,'pointsSnapshot: history + balance read together and stored (%s)'%r)
    r=E("async()=>{const a=TLB.pointsSnapshot();TLB.pointsAbandon();return await a}")
    ok(r is None,'pointsAbandon: a reply that arrives after abandon is ignored (returns null, nothing overwritten)')
    r=E("async()=>{const a=TLB.pointsSnapshot(),b2=TLB.pointsSnapshot();const [x,y]=await Promise.all([a,b2]);return [x===null,!!y]}")
    ok(r==[True,True],'pointsSnapshot: an older call never overwrites a newer one')
    E("()=>{go('wallet');render()}");pg.wait_for_timeout(800)
    ok(E("()=>document.querySelectorAll('.dr').length")>0,'customer v80 wallet: points history rows shown')
    r=E("async()=>{const o=TLB.orders().find(x=>x.status=='delivered');window.__weq=[];const l=await TLB.orderWallet(o.id);return {ok:Array.isArray(l),id:o.id,q:window.__weq}}")
    ok(r['ok'] and any(['eq','order_id',r['id']] in q for q in r['q']),'orderWallet: reads wallet_entries filtered by this order id (%s)'%r['q'][:2])
    E("()=>{const o=TLB.orders().find(x=>x.status=='delivered');TLB.proofUrl=()=>Promise.resolve(null);go('track',{tid:o.id});render()}");pg.wait_for_timeout(900)
    ok(E("()=>S.ow!==null&&S.ow!=='err'&&S.ow!==undefined"),'customer v80 order details: wallet records loaded (no «err» state)')
    ok(not errs,'no JS errors %s'%errs[:2])
    b.close()
print('\nCORE V80 CHECK %s'%('FAILS %d'%len(fails) if fails else 'OK'));sys.exit(1 if fails else 0)
