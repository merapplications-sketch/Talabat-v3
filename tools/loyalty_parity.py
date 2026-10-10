"""The app and the database must compute the SAME bill (v46): the customer app shows the total, the points it will
use and the wallet amount; place_order recomputes them and refuses the order if they differ (points_changed /
wallet_changed). This test builds random carts (prices with cents, store/dish discounts, happy hour, points balance
above/below the minimum) and compares the customer app's calc() with place_order in PostgreSQL.

Needs the local test database left by sql/test_patch29.sql:
  PG='host=/tmp/pgtest29 port=5499 user=postgres' python3 tools/loyalty_parity.py
"""
import os,sys,json,random,subprocess
from playwright.sync_api import sync_playwright
here=os.path.dirname(os.path.abspath(__file__));root=os.path.abspath(os.path.join(here,'..'))
PG=os.environ.get('PG','host=/tmp/pgtest29 port=5499 user=postgres')
def sql(q,soft=False):
    r=subprocess.run(['psql',PG,'-At','-v','ON_ERROR_STOP=1','-c',q],capture_output=True,text=True)
    if r.returncode:
        if soft: return 'ERR '+r.stderr.strip().split('\n')[0][:120]
        raise SystemExit('SQL failed: '+r.stderr[:300])
    return r.stdout.strip()
FIX=open(os.path.join(here,'qa_all.py')).read().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE','"customer"')
STORE='50000000-0000-0000-0000-000000000001';CUST='c0000000-0000-0000-0000-000000000002'
random.seed(46);N=int(os.environ.get('N','250'))
PRICES=[12.5,7.3,33.33,18.9,45,9.99,27.75,3.4]
ids=['20000000-0000-0000-0000-%012d'%i for i in range(len(PRICES))]
sql("delete from menu_items where id::text like '20000000-%';"+''.join("insert into menu_items values ('%s','%s','D%d',%s,0);"%(ids[i],STORE,i,p) for i,p in enumerate(PRICES)))
sql("select set_setting('cashback_pct',0) from (select set_config('request.jwt.claim.sub','a0000000-0000-0000-0000-00000000000a',false)) x")
bad=0
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page()
    pg.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=FIX) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
    pg.goto('file://'+root+'/customer.html',wait_until='domcontentloaded');pg.wait_for_timeout(2000)
    for n in range(N):
        sd=random.choice([0,0,10,15]);hh=random.choice([0,0,20,25,40]);disc=[random.choice([0,0,0,5,10,30]) for _ in PRICES]
        cart={ids[i]:random.randint(1,4) for i in random.sample(range(len(PRICES)),random.randint(1,5))}
        bal=random.choice([0,500,999,1000,1234,20000,150000,10**6]);rate=random.choice([1000,100,7,333]);mn=random.choice([0,1000])
        use=random.random()<0.8;tip=random.choice([0,3,5,10])
        # database state
        sql("update stores set discount_pct=%d where id='%s';update menu_items set discount_pct=v.d from (values %s) v(i,d) where id=v.i::uuid;delete from happy_hours;%s"
            %(sd,STORE,','.join("('%s',%d)"%(ids[i],disc[i]) for i in range(len(PRICES))),
              "insert into happy_hours(title,start_time,end_time,discount_pct) values ('t','00:00','23:59:59',%d);"%hh if hh else ''))
        sql("update app_settings set value=%d where key='loyalty_points_per_tjs';update app_settings set value=%d where key='loyalty_min_redeem';delete from loyalty_lots where user_id='%s';%s"
            %(rate,mn,CUST,"insert into loyalty_lots(user_id,points,points_left,expires_at,kind) values ('%s',%d,%d,now()+interval '9 days','earn');"%(CUST,bal,bal) if bal else ''))
        # the app's view of the same state
        c=pg.evaluate("""(a)=>{const items=a.ids.map((id,i)=>({id,name:'D'+i,price:a.prices[i],discount:a.disc[i],available:true,approved:true,image:'',hasOpts:false,optsBlocked:false}));
          TLB.allMenus=()=>({K:items});TLB.optionsOf=()=>[];TLB.isOpen=()=>true;TLB.loyalty=()=>({balance:a.bal,points_per_tjs:a.rate,min_redeem:a.mn,earn_per_tjs:10,cashback_pct:0});
          ALLS=[{id:'k',n:'K',fee:10,rd:a.sd,hh:a.hh,disc:Math.max(a.sd,a.hh),ffd:false,ft:'fixed'}];
          S.cartStore='K';S.cart=a.cart;S.quote=null;S.promo=null;S.useWallet=false;S.usePts=a.use;S.tip=a.tip;
          const c=calc();return {sub:c.sub,d:c.d,h:c.h,pts:c.pts,pv:c.pv,total:c.total}}""",
          {'ids':ids,'prices':PRICES,'disc':disc,'bal':bal,'rate':rate,'mn':mn,'sd':sd,'hh':hh,'cart':cart,'use':use,'tip':tip})
        items=json.dumps([{'item_id':k,'qty':q} for k,q in cart.items()])
        r=sql("select set_config('request.jwt.claim.sub','%s',false);select place_order('%s'::uuid,'%s'::jsonb,%d,'cash','Rudaki 1',38.5,68.7,null,null,10,null,%s)"
              %(CUST,STORE,items,tip,c['pts'] or 'null'),soft=True).split('\n')[-1]
        if not r.isdigit():
            bad+=1;print('FAIL #%d server refused: %s | app %s | sd %s hh %s bal %s rate %s min %s'%(n,r,c,sd,hh,bal,rate,mn));continue
        row=sql("select subtotal,discount,hh_discount,points_used,points_value,total from orders where id=%s"%r).split('|')
        srv=dict(zip(['sub','d','h','pts','pv','total'],[float(x) for x in row]))
        diff={k:(c[k],srv[k]) for k in srv if abs(float(c[k])-srv[k])>0.004}
        if diff: bad+=1;print('FAIL #%d %s | sd %s hh %s disc %s cart %s bal %s rate %s'%(n,diff,sd,hh,disc,cart,bal,rate))
        sql("update orders set status='cancelled', created_at=now()-interval '2 hours' where id=%s"%r)   # points come back; keep the 20-per-hour guard out of the way
    b.close()
sql("delete from happy_hours")
print('PARITY cases',N,'FAILS',bad);sys.exit(1 if bad else 0)
