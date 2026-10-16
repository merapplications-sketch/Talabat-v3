"""Admin menu (phone): tapping sections keeps the tab strip at a steady place, the section starts right under it, no late jump,
the page never scrolls sideways (only the strip may). Real taps, with real automatic refreshes running.
  python3 tools/tab_nav_check.py <admin_preview_dir>"""
import sys
from playwright.sync_api import sync_playwright
fails=[];rows=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
SEQ=['s','d','u','o']*3
with sync_playwright() as p:
    b=p.chromium.launch()
    for lang in ['ru','en']:
        pg=b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
        pg.goto('file://'+sys.argv[1]+'/admin.html');pg.wait_for_timeout(2500);E=pg.evaluate;E("l=>TLB.setLang(l)",lang);pg.wait_for_timeout(1500)
        # a real data change on the demo server every 4 s (on top of the 10 s demo courier): automatic refreshes keep happening
        E("()=>setInterval(()=>{const o=window.__pvTables.orders.find(x=>x.id=='ord1');o.status=o.status=='preparing'?'ready':'preparing';document.dispatchEvent(new Event('visibilitychange'))},4000)")
        top=lambda:E("()=>Math.round(document.querySelector('.tabs').getBoundingClientRect().top)")
        n0=E("()=>RINFO.n")
        for i,k in enumerate(SEQ):
            if i%4==1: E("()=>window.scrollBy(0,180)");pg.wait_for_timeout(200)   # sometimes the page is scrolled before the tap
            t0=top();pg.locator('.tabs button[onclick*="tab=\'%s\'"]'%k).click();pg.wait_for_timeout(60);t1=top()
            pg.wait_for_timeout(1800);t2=top()
            first=E("()=>{const s=document.querySelector('.tabs');let n=s.closest('nav').nextElementSibling;while(n&&!n.offsetHeight)n=n.nextElementSibling;return n?Math.round(n.getBoundingClientRect().top-s.getBoundingClientRect().bottom):null}")
            sx=E("()=>[window.scrollX,document.scrollingElement.scrollLeft,document.documentElement.scrollWidth-innerWidth]")
            rows.append((lang,k,t0,t1,t2,first,sx))
            # it may only move when the page physically cannot be scrolled to keep it there (not enough page above / below)
            need=E("()=>scrollY")+(t1-t0);mx=E("()=>document.documentElement.scrollHeight-innerHeight")
            ok(t1==t0 or need<0 or need>mx,'[%s] tap %s: strip stays where it was (%s → %s)%s'%(lang,k,t0,t1,'' if t1==t0 else ' — could it be kept? need %d, max %d'%(need,mx)))
            ok(abs(t2-t1)<=2,'[%s] tap %s: no late jump 1.8 s later (%s → %s)'%(lang,k,t1,t2))
            ok(t1>=0 and t1<=844-60,'[%s] tap %s: strip visible on screen (%s)'%(lang,k,t1))
            ok(first is not None and 0<=first<=40,'[%s] tap %s: section starts right under the strip (gap %s px)'%(lang,k,first))
            ok(sx[0]==0 and sx[1]==0 and sx[2]<=1,'[%s] tap %s: page never scrolls sideways %s'%(lang,k,sx))
        ok(E("()=>RINFO.n")-n0>len(SEQ),'[%s] automatic refreshes happened during the taps (%d redraws)'%(lang,E("()=>RINFO.n")-n0))
        ok(not errs,'[%s] no JS errors %s'%(lang,errs[:2]));pg.close()
    b.close()
for r in rows: print('  ',r)
print('TAB NAV FAILS',len(fails));sys.exit(1 if fails else 0)
