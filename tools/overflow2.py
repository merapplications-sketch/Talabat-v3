import os
from playwright.sync_api import sync_playwright
exec(open(os.path.join(os.path.dirname(__file__),'smoke.py')).read().split('pages=')[0])
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
bad=0
with sync_playwright() as p:
    b=p.chromium.launch()
    for name in ['admin','merchant','driver','customer']:
        for w in (360,390,430):
            pg=b.new_page(viewport={'width':w,'height':800})
            pg.route('**/*',lambda rt,rq,name=name:(rt.fulfill(status=200,content_type='application/javascript',body=MOCK.replace('window.__ROLE','"'+name+'"').replace('window.__PERMS','null')) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
            pg.goto('file://'+root+'/'+name+'.html',wait_until='domcontentloaded');pg.wait_for_timeout(1500)
            r=pg.evaluate("""()=>{const d=document.createElement('div');d.style.cssText='width:900px;height:20px;background:red';d.textContent='x'.repeat(300);document.body.appendChild(d);
              const i=document.createElement('input');i.style.width='900px';document.body.appendChild(i);
              const s=document.scrollingElement;s.scrollLeft=500;return {W:innerWidth,sw:s.scrollWidth,sl:s.scrollLeft}}""")
            ok=r['sw']<=w and r['sl']==0;bad+=0 if ok else 1
            print(name,w,r,'OK' if ok else 'FAIL')
print('FAILS',bad)
