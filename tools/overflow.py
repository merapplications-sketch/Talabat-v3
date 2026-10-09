import os
from playwright.sync_api import sync_playwright
exec(open(os.path.join(os.path.dirname(__file__),'smoke.py')).read().split('pages=')[0])
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,role in [('admin','admin'),('merchant','merchant'),('driver','driver'),('customer','customer')]:
        for w in (360,390,430):
            pg=b.new_page(viewport={'width':w,'height':800})
            pg.route('**/*',lambda rt,rq,role=role:(rt.fulfill(status=200,content_type='application/javascript',body=MOCK.replace('window.__ROLE','"'+role+'"').replace('window.__PERMS','null')) if 'supabase-js' in rt.request.url else (rt.abort() if rt.request.url.startswith('http') else rt.continue_())))
            pg.goto('file://'+root+'/'+name+'.html',wait_until='domcontentloaded');pg.wait_for_timeout(1800)
            r=pg.evaluate("""()=>{const W=innerWidth;let bad=[];document.querySelectorAll('body *').forEach(e=>{const r=e.getBoundingClientRect();if(r.width&&r.right>W+1&&getComputedStyle(e).position!='fixed')bad.push(e.tagName+'.'+(e.className||'')+':'+Math.round(r.right))});return {W,sw:document.documentElement.scrollWidth,bad:bad.slice(0,5)}}""")
            print(name,w,r)
