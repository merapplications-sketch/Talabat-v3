"""Cart + checkout behaviour (v42): cart survives a reload, unavailable lines block checkout,
a retried order reuses the same idempotency key (no duplicate order), totals ignore unavailable lines."""
import os,json,sys
from playwright.sync_api import sync_playwright
here=os.path.dirname(os.path.abspath(__file__));root=os.path.abspath(os.path.join(here,'..'))
FIX=open(os.path.join(here,'qa_all.py')).read().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE','"customer"').replace('var groups=',"items.push({id:PLOV,store_id:'s1',name:'Плов',price:40,image_url:'',popular:false,available:true,approved:true,section:'Салаты',discount_pct:0,created_at:iso(1)});var groups=",1).replace('(function(){',"(function(){var PLOV='11111111-1111-4111-8111-111111111111';",1)
# capture place_order calls; window.__fail>0 makes the next call fail like a dropped connection
SPY="""(function(){var cc=window.supabase.createClient;window.__rpcs=[];window.__fail=0;
 window.supabase.createClient=function(){var c=cc.apply(this,arguments),r=c.rpc;c.rpc=function(n,a){if(n==='place_order'){window.__rpcs.push(a);
  if(window.__fail>0){window.__fail--;return Promise.reject(new TypeError('Failed to fetch'))}return Promise.resolve({data:777,error:null})}return r.call(c,n,a)};return c}})();"""
fails=[]
def ok(cond,msg):
    print(('PASS ' if cond else 'FAIL ')+msg)
    if not cond: fails.append(msg)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780});pg=ctx.new_page();errs=[];dlg=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('dialog',lambda d:(dlg.append(d.message),d.accept()))
    pg.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=FIX+SPY) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
    def load():
        pg.goto('file://'+root+'/customer.html',wait_until='domcontentloaded');pg.wait_for_timeout(2200)
    load()
    # 1) persistence
    r=pg.evaluate("""()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={i2:2,['i1~o11']:1};S.cartStore=s.n;S.note='без лука';S.tip=5;go('cart');
      const btn=[...document.querySelectorAll('.fbar .btn')].pop();
      return {saved:localStorage.getItem('tlb-cart-'+TLB.me().id),btn:btn.textContent,dis:btn.disabled,sub:calc().sub}}""")
    d=json.loads(r['saved'] or 'null') or {}
    ok(d.get('sid')=='s1' and d.get('cart',{}).get('i2')==2,'cart saved to the device')
    ok('TJS' in r['btn'] and not r['dis'],'continue button shows the amount: '+r['btn'].strip())
    sub=r['sub'];load()
    r=pg.evaluate("()=>({cart:S.cart,store:(ALLS.find(x=>x.n==S.cartStore)||{}).id,note:S.note,tip:S.tip,bar:!!document.querySelector('.bar')})")
    ok(r['cart']=={'i2':2,'i1~o11':1} and r['store']=='s1' and r['note']=='без лука' and r['tip']==5,'cart restored after reload')
    ok(r['bar'],'cart bar visible on home after reload')
    # an old (25 h) saved cart is ignored
    pg.evaluate("()=>{const k='tlb-cart-'+TLB.me().id,d=JSON.parse(localStorage.getItem(k));d.at=Date.now()-25*3600e3;localStorage.setItem(k,JSON.stringify(d))}")
    load();ok(pg.evaluate("()=>Object.keys(S.cart).length")==0,'cart older than 24 h is not restored')
    # 2) unavailable lines (deleted dish + option that no longer exists)
    r=pg.evaluate("""()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={i2:2,['i1~o11']:1,ixx:1,['i1~zz']:1};S.cartStore=s.n;go('cart');
      const btn=[...document.querySelectorAll('.fbar .btn')].pop();const r={gone:!!document.getElementById('cgone'),grey:document.querySelectorAll('.ci.gone').length,dis:btn.disabled,sub:calc().sub,bad:badKeys().length};
      go('pay');r.payRedirect=S.v;return r}""")
    ok(r['gone'] and r['grey']==2 and r['bad']==2,'unavailable lines flagged (%d greyed)'%r['grey'])
    ok(r['dis'],'continue disabled while unavailable lines are in the cart')
    ok(pg.evaluate("()=>{const c=S.cart;S.cart={i4:1};const n=badKeys().length;S.cart=c;return n}")==1,'dish switched off by the restaurant is flagged too')
    ok(abs(r['sub']-sub)<0.001,'totals ignore unavailable lines')
    ok(r['payRedirect']=='cart','payment page sends you back to the cart')
    n0=pg.evaluate("async()=>{await place();return window.__rpcs.length}")
    ok(n0==0,'no order is sent while unavailable lines exist')
    r=pg.evaluate("()=>{rmBad();return {keys:Object.keys(S.cart).sort(),gone:!!document.getElementById('cgone')}}")
    ok(r['keys']==['i1~o11','i2'] and not r['gone'],'"remove unavailable" keeps the good lines')
    # 3) dropped connection then retry -> same key; success clears everything
    pg.evaluate("()=>{S.cart={['11111111-1111-4111-8111-111111111111']:2};render()}")
    r=pg.evaluate("""async()=>{go('pay');await quoteNow();window.__fail=1;await place();
      const a={n:window.__rpcs.length,key:S.okey,busy:S.busy,v:S.v,saved:JSON.parse(localStorage.getItem('tlb-cart-'+TLB.me().id)).key};
      await place();const k1=window.__rpcs[0].p_key,k2=window.__rpcs[1]&&window.__rpcs[1].p_key;
      return Object.assign(a,{n2:window.__rpcs.length,k1,k2,v2:S.v,tid:S.tid,okey:S.okey,cart:Object.keys(S.cart).length,left:localStorage.getItem('tlb-cart-'+TLB.me().id)})}""")
    ok(r['n']==1 and not r['busy'] and r['v']=='pay','failed send: stays on payment, button usable again')
    ok(any('Ошибка' in m or 'wrong' in m for m in dlg),'failed send shows an error message')
    ok(r['key'] and r['saved']==r['key'],'order key kept (also on the device) for the retry')
    ok(r['n2']==2 and r['k1']==r['k2'] and r['k1'],'retry sends the SAME key → the server returns the same order, no duplicate')
    ok(r['v2']=='track' and r['tid']==777 and r['okey'] is None and r['cart']==0 and r['left'] is None,'success: tracking page, cart + saved cart cleared')
    r=pg.evaluate("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={['11111111-1111-4111-8111-111111111111']:1};S.cartStore=s.n;go('pay');await quoteNow();await place();return {k:window.__rpcs[2].p_key,k1:window.__rpcs[0].p_key}}""")
    ok(r['k'] and r['k']!=r['k1'],'next order gets a new key')
    # 3b) v50: order wishes reach the server; points switch is OFF by default
    r=pg.evaluate("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={['11111111-1111-4111-8111-111111111111']:1};S.cartStore=s.n;S.door=true;S.subst='replace';S.gift={name:'Мадина',phone:'+992901112233'};go('pay');await quoteNow();
      const off=!S.usePts;await place();const a=window.__rpcs[window.__rpcs.length-1];return {off,ex:a.p_extra,pts:a.p_points,reset:!S.gift&&!S.door&&S.subst=='call'}}""")
    ok(r['off'] and r['pts'] is None,'points switch is OFF by default, no points sent')
    ok(r['ex']=={'door':True,'subst':'replace','gift':{'name':'Мадина','phone':'+992901112233'}},'order wishes sent: '+json.dumps(r['ex'],ensure_ascii=False))
    ok(r['reset'],'wishes cleared after the order')
    n0=pg.evaluate("()=>window.__rpcs.length");dlg.clear()
    pg.evaluate("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={['11111111-1111-4111-8111-111111111111']:1};S.cartStore=s.n;S.gift={name:'М',phone:'123'};go('pay');await quoteNow();await place()}""")
    ok(pg.evaluate("()=>window.__rpcs.length")==n0 and dlg,'gift without a valid phone: clear message, nothing sent')
    pg.evaluate("()=>{S.gift=null}")
    # 3c) v51: scheduled time, free delivery above the restaurant threshold, group order
    r=pg.evaluate("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={['11111111-1111-4111-8111-111111111111']:1};S.cartStore=s.n;go('pay');await quoteNow();
      whenSet(true);const at=S.at;await place();const a=window.__rpcs[window.__rpcs.length-1];return {at,sent:a.p_extra.at,fee:a.p_fee,reset:S.at===null}}""")
    ok(r['sent'] and abs(pg.evaluate("(x)=>Date.parse(x)",r['sent'])-r['at'])<1000 and r['reset'],'scheduled time sent (first slot ≥ 45 min) and cleared after the order')
    ok(r['fee']==12,'below the free-delivery threshold the normal fee is sent: %s'%r['fee'])
    n0=pg.evaluate("()=>window.__rpcs.length");dlg.clear()
    pg.evaluate("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={['11111111-1111-4111-8111-111111111111']:1};S.cartStore=s.n;go('pay');await quoteNow();S.at=Date.now()+20*60000;await place()}""")
    ok(pg.evaluate("()=>window.__rpcs.length")==n0 and dlg and pg.evaluate("()=>S.at")is None,'a time that became too close is refused before sending')
    r=pg.evaluate("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={['11111111-1111-4111-8111-111111111111']:8};S.cartStore=s.n;go('pay');await quoteNow();const c=calc();await place();const a=window.__rpcs[window.__rpcs.length-1];return {fw:c.fw,fee:c.fee,sent:a.p_fee,row:true}}""")
    ok(r['fw']==12 and r['fee']==0 and r['sent']==0,'dishes ≥ threshold (150): delivery is free and 0 is sent: %s'%r)
    r=pg.evaluate("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={i2:1};S.cartStore=s.n;const P='11111111-1111-4111-8111-111111111111';S.gid=window.__GRP.id;S.grp=Object.assign({},window.__GRP,{status:'closed',items:[{id:1,user_name:'Зарина',mine:true,item_id:P,qty:2,options:[]},{id:2,user_name:'Бахромджон',mine:false,item_id:P,qty:1,options:[],note:'без лука'}]});go('group');await grpCheckout();
      const k=Object.keys(S.cart).sort(),v=S.v,keep=S.gKeep&&Object.keys(S.gKeep.cart);await quoteNow();await place();const a=window.__rpcs[window.__rpcs.length-1];
      return {v,k,keep,grp:a.p_extra.group,notes:a.p_items.map(x=>x.note||''),after:{gid:S.gid,cart:Object.keys(S.cart),v:S.v}}}""")
    ok(r['v']=='pay' and r['k']==['11111111-1111-4111-8111-111111111111'] and pg.evaluate("()=>1"),'group checkout: same dish from two people = one line: %s'%r['k'])
    ok(r['grp']==pg.evaluate("()=>window.__GRP.id"),'the order is sent as the group order')
    ok(r['notes']==['Зарина ×2; Бахромджон ×1 (без лука)'],'each line keeps who ordered it: %s'%r['notes'])
    ok(r['after']['gid'] is None and r['after']['cart']==['i2'] and r['after']['v']=='track','after the group order: own cart is back, group closed on this phone')
    # 4) busy label
    t=pg.evaluate("()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={i2:1};S.cartStore=s.n;S.busy=true;go('pay');const t=document.querySelector('.fbar .btn').textContent;S.busy=false;render();return t}")
    ok('…' in t,'placing state shows "sending…": '+t)
    ok(not errs,'no JS errors '+str(errs[:2]))
    b.close()
print('CART FAILS',len(fails));sys.exit(1 if fails else 0)
