"""Staff look (admin panel + restaurant app) on read-only previews: every menu entry reachable by a real tap, the side menu on wide
screens, no sideways page scroll, icon-only buttons named, no emoji left in fixed labels, and the restaurant app patches its page on
automatic refreshes (typed text kept). Chromium, not Safari.
  python3 tools/staff_ui_check.py <admin_preview_dir> <merchant_preview_dir>"""
import os,sys,re
from playwright.sync_api import sync_playwright
A=os.path.abspath(sys.argv[1]);M=os.path.abspath(sys.argv[2]);fails=[];n=0
def ok(c,m):
    global n
    print(('PASS ' if c else 'FAIL ')+m);n+=1
    if not c: fails.append(m)
EMO=r'[\U0001F300-\U0001FAFF✅❌⚠⛔⏱⏳➕]'
def page(b,d,app,vw,lang):
    pg=b.new_page(viewport={'width':vw[0],'height':vw[1]},is_mobile=vw[0]<700,has_touch=vw[0]<700);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.goto('file://'+d+'/'+app+'.html');pg.wait_for_timeout(2500);pg.evaluate("l=>TLB.setLang(l)",lang);pg.wait_for_timeout(1500)
    return pg,errs
def common(pg,tag):
    E=pg.evaluate
    ok(E("()=>document.documentElement.scrollWidth<=innerWidth+1"),tag+' no sideways page scroll (%s/%s)'%(E("()=>document.documentElement.scrollWidth"),E("()=>innerWidth")))
    bad=E("()=>[...document.querySelectorAll('#app button,#app [role=button]')].filter(b=>b.offsetParent&&!b.innerText.trim()&&!b.getAttribute('aria-label')).map(b=>(b.getAttribute('onclick')||'').slice(0,40))")
    ok(not bad,tag+' icon-only buttons have a name %s'%bad[:3])
    em=re.findall(EMO,E("()=>[...document.querySelectorAll('#app button,#app h1,#app h3,#app .card>b,#app .alh,#app .tabs,#app .nav')].map(e=>e.innerText).join(' ')"))
    ok(not em,tag+' no emoji in controls and headings %s'%em[:5])
with sync_playwright() as p:
    b=p.chromium.launch()
    # ---------------- admin ----------------
    for vw,lang in [((390,844),'ru'),((844,390),'en'),((1366,900),'ru'),((1024,768),'en'),((360,780),'en')]:
        pg,errs=page(b,A,'admin',vw,lang);E=pg.evaluate;tag='[admin %dx%d %s]'%(vw[0],vw[1],lang)
        tabs=E("()=>[...document.querySelectorAll('.tabs button')].length")
        ok(tabs==12,tag+' all 12 menu entries present (%d)'%tabs)
        wide=vw[0]>=1024
        side=E("()=>{const s=document.querySelector('.side');const r=s.getBoundingClientRect();return [getComputedStyle(s).position,Math.round(r.width),getComputedStyle(s).backgroundColor]}")
        ok((side[0]=='fixed' and side[1]>=200) if wide else side[0]!='fixed',tag+' menu: %s'%side)
        if wide: ok(E("()=>$('app').getBoundingClientRect().left")>=side[1],tag+' content starts right of the side menu')
        for i in range(tabs):
            loc=pg.locator('.tabs button').nth(i);loc.scroll_into_view_if_needed();loc.click();pg.wait_for_timeout(250)
            common(pg,tag+' tab '+E("()=>tab"))
        pg.locator('.tabs button').first.click();pg.wait_for_timeout(200)
        ok(not errs,tag+' no JS errors '+str(errs[:2]));pg.close()
    # ---------------- restaurant app ----------------
    for vw,lang in [((390,844),'ru'),((844,390),'en'),((1366,900),'ru'),((360,780),'en')]:
        pg,errs=page(b,M,'merchant',vw,lang);E=pg.evaluate;tag='[merchant %dx%d %s]'%(vw[0],vw[1],lang)
        wide=vw[0]>=1024;nav=E("()=>{const s=document.querySelector('.nav');const r=s.getBoundingClientRect();return [Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)]}")
        ok((nav[1]==0 and nav[2]<300 and nav[3]>=vw[1]-1) if wide else (nav[3]<120 and nav[1]>vw[1]-130),tag+' menu %s'%nav)
        for k in ['o','m','s','p']:
            pg.locator('.nav [onclick="setTab(\'%s\')"]'%k).click();pg.wait_for_timeout(300)
            ok(E("()=>tab")==k,tag+' tap menu → '+k);common(pg,tag+' tab '+k)
        ok(not errs,tag+' no JS errors '+str(errs[:2]));pg.close()
    # restaurant: automatic refresh patches the page, the typed search stays and the field is the same element
    pg,errs=page(b,M,'merchant',(390,844),'ru');E=pg.evaluate
    pg.locator('.nav [onclick="setTab(\'m\')"]').click();pg.wait_for_timeout(300)
    pg.fill('#mqs','плов');E("()=>{document.activeElement.blur();document.getElementById('mqs').__mk=1}")
    E("()=>{const T=window.__pvTables;T.stores[0].description=(T.stores[0].description||'')+' ·';document.dispatchEvent(new Event('visibilitychange'))}");pg.wait_for_timeout(3000)
    ok(pg.input_value('#mqs')=='плов' and E("()=>document.getElementById('mqs').__mk===1"),'[merchant] automatic refresh: search text kept, same field (page patched, not rebuilt)')
    pg.locator('.nav [onclick="setTab(\'o\')"]').click();pg.wait_for_timeout(300)
    ok(E("()=>window.scrollY")==0 and E("()=>tab")=='o','[merchant] switching tab still starts a fresh screen at the top')
    ok(not errs,'[merchant] no JS errors '+str(errs[:2]));b.close()
print('STAFF UI PASS',n-len(fails),'FAILS',len(fails));sys.exit(1 if fails else 0)
