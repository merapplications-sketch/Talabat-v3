import os,json
from playwright.sync_api import sync_playwright
exec(open(os.path.join(os.path.dirname(__file__),'smoke.py')).read().split('pages=')[0])
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
JS="""()=>{const out=[];const off=document.getElementById('tlb-off'),bar=document.getElementById('tlb-bar');
 const top=document.querySelector('.hd,.top,#tlb-top');const R=e=>e?e.getBoundingClientRect():null;
 const a=R(off),b=R(bar),h=R(top);
 const ov=(x,y)=>x&&y&&x.width&&y.width&&x.top<y.bottom-1&&y.top<x.bottom-1&&x.left<y.right&&y.left<x.right;
 const sib=[];const hh=document.querySelector('.hd,.top');if(hh){const T=[];const w=document.createTreeWalker(hh,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){if(!n.nodeValue.trim())continue;const g=document.createRange();g.selectNodeContents(n);const pe=n.parentElement,pr=pe.getBoundingClientRect(),clip=getComputedStyle(pe).overflow!='visible';for(const r0 of g.getClientRects()){const r=clip?{left:Math.max(r0.left,pr.left),right:Math.min(r0.right,pr.right),top:r0.top,bottom:r0.bottom,width:Math.min(r0.right,pr.right)-Math.max(r0.left,pr.left),height:r0.height}:r0;if(r.width>1&&r.height>1)T.push({n,r})}}
  for(let i=0;i<T.length;i++)for(let j=i+1;j<T.length;j++){if(T[i].n===T[j].n)continue;const a=T[i].r,b=T[j].r;if(a.left<b.right-2&&b.left<a.right-2&&a.top<b.bottom-2&&b.top<a.bottom-2)sib.push(T[i].n.nodeValue.trim().slice(0,18)+' X '+T[j].n.nodeValue.trim().slice(0,18))}
  T.forEach(x=>{if(x.r.right>innerWidth+1||x.r.left<-1)sib.push('outside:'+x.n.nodeValue.trim().slice(0,18))})}
 return {sib,off:a&&[a.top,a.bottom],bar:b&&[b.top,b.bottom],hd:h&&[Math.round(h.top),Math.round(h.bottom)],ovOffHd:ov(a,h),ovBarHd:ov(b,h),ovOffBar:ov(a,b),sw:document.scrollingElement.scrollWidth}}"""
bad=0
with sync_playwright() as p:
    b=p.chromium.launch()
    for name in ['driver','merchant','customer','admin']:
      for w in (360,390):
        for offline in (False,True):
            ctx=b.new_context(viewport={'width':w,'height':780},device_scale_factor=2);pg=ctx.new_page()
            pg.route('**/*',lambda rt,rq,name=name:(rt.fulfill(status=200,content_type='application/javascript',body=MOCK.replace('window.__ROLE','"'+name+'"').replace('window.__PERMS','null')) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
            pg.goto('file://'+root+'/'+name+'.html',wait_until='domcontentloaded');pg.wait_for_timeout(1500)
            if offline: pg.evaluate("window.dispatchEvent(new Event('offline'))");pg.wait_for_timeout(2800)
            pg.evaluate("document.querySelectorAll('.hd b,.top b').forEach(b=>b.textContent='Муаммад ибни Абдуллоҳ аз Душанбе')")
            r=pg.evaluate(JS);print(name,w,'offline' if offline else 'online',json.dumps(r))
            if r['sib'] or r['ovOffHd'] or r['ovBarHd'] or r['ovOffBar'] or r['sw']>w: bad+=1
            pg.screenshot(path='/tmp/h_%s_%d_%s.png'%(name,w,'off' if offline else 'on'))
print('OVERLAPS',bad)
