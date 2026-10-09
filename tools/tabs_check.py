import os,json
from playwright.sync_api import sync_playwright
exec(open(os.path.join(os.path.dirname(__file__),'smoke.py')).read().split('pages=')[0])
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
with sync_playwright() as p:
    b=p.chromium.launch()
    for w in (360,390):
        pg=b.new_page(viewport={'width':w,'height':800});errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=MOCK.replace('window.__ROLE','"customer"').replace('window.__PERMS','null')) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
        pg.goto('file://'+root+'/customer.html',wait_until='domcontentloaded');pg.wait_for_timeout(1500)
        r=pg.evaluate("""()=>{
          const st={id:'a',name:'Cafe',category:'rest',description:'Tasty <b>x</b>',address:'Rudaki 1',phone:'+992 900 000 000',lat:38.5,lng:68.7,fee_type:'fixed',fee_base:10,discount_pct:10,is_active:true,is_open:true,rating:4.5,rating_count:12};
          TLB.stores=()=>[st];TLB.allMenus=()=>({Cafe:[]});TLB.isOpen=()=>true;ME.phone='+992900000000';
          syncStores();S.store='Cafe';S.v='menu';S.mtab='info';render();
          const t=document.body.innerText,h=document.body.innerHTML;
          return {info:t.includes('Rudaki 1')&&t.includes('4.5'),tel:h.includes('href="tel:+992900000000"'),map:h.includes('maps/search'),xss:h.includes('<b>x</b>'),bad:/undefined|NaN/.test(t),sw:document.scrollingElement.scrollWidth}}""")
        print(w,json.dumps(r),errs)
        assert not errs and r['info'] and r['tel'] and r['map'] and not r['xss'] and not r['bad'] and r['sw']<=w,r
        if w==390: pg.screenshot(path='/tmp/info.png')
print('TABS OK')
