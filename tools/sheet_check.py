import os,json
from playwright.sync_api import sync_playwright
exec(open(os.path.join(os.path.dirname(__file__),'smoke.py')).read().split('pages=')[0])
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':700});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=MOCK.replace('window.__ROLE','"customer"').replace('window.__PERMS','null')) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
    pg.goto('file://'+root+'/customer.html',wait_until='domcontentloaded');pg.wait_for_timeout(1500)
    r=pg.evaluate("""()=>{
      const gs=[1,2,3,4,5].map(n=>({id:'g'+n,name:'Group '+n,required:n==1||n==5,max:n==2?3:1,options:[1,2,3,4,5,6].map(k=>({id:'o'+n+k,name:'Opt '+n+k,price:k}))}));
      const it={id:'i1',name:'Burger',price:30,image:'',discount:0,hasOpts:true,popular:false,available:true};
      TLB.optionsOf=()=>gs;TLB.isOpen=()=>true;
      TLB.allMenus=()=>({X:[it]});ME.phone='+992900000000';
      syncStores();S.store='X';S.v='menu';S.sh={id:'i1',sel:{},q:1,keep:true};
      try{render()}catch(e){return {err:String(e)}}
      const o=document.querySelector('.osh');if(!o)return {err:'no sheet'};
      o.scrollTop=400;const before=o.scrollTop;
      shPick('g3','o31',1);
      const after=document.querySelector('.osh').scrollTop;
      shAdd();
      const miss=!!document.querySelector('.og.miss');
      const lock=document.documentElement.classList.contains('shopen');
      const cnt=document.body.innerText.includes('0/3');
      return {before,after,miss,lock,cnt}}""")
    print(json.dumps(r),errs)
    assert not errs and r.get('before')>0 and abs(r['after']-r['before'])<3 and r['miss'] and r['lock'] and r['cnt'],r
    pg.screenshot(path='/tmp/sheet.png');print('SHEET OK')
