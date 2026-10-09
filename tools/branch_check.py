import json,os,re
from playwright.sync_api import sync_playwright
exec(open(os.path.join(os.path.dirname(__file__),'smoke.py')).read().split('pages=')[0])
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':800});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda r:(r.fulfill(status=200,content_type='application/javascript',body=MOCK.replace('window.__ROLE','"customer"').replace('window.__PERMS','null')) if 'supabase' in r.request.url and r.request.url.endswith('.js') or 'supabase-js' in r.request.url else r.continue_()))
    pg.goto('file://'+root+'/customer.html');pg.wait_for_timeout(2000)
    r=pg.evaluate("""()=>{
      const mk=(id,name,bid,bn,la)=>({id,name,category:'rest',fee_type:'fixed',fee_base:10,discount_pct:0,is_active:true,is_open:true,lat:la,lng:68.7,brand_id:bid,branch_name:bn});
      const L=[mk('a','Solo','', '',38.5),mk('b','Burger','B1','Main',38.9),mk('c',"Burger · O'Hara",'B1',"O'Hara",38.55)];
      TLB.stores=()=>L;TLB.brands=()=>[{id:'B1',name:'Burger',owner_id:'x'}];TLB.isOpen=n=>true;
      syncStores();const out={all:ALLS.length,cards:STORES.map(s=>s.n)};
      S.store="Burger · O'Hara";out.chips=brChips(storeOf(S.store));
      return out}""")
    print(json.dumps(r,ensure_ascii=False));print('ERR',errs)
    assert r['all']==3 and len(r['cards'])==2 and 'brc' in r['chips'] and 'brGo(' in r['chips'] and not errs
    print('BRANCH OK')
