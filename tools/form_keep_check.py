"""Automatic refreshes must not wipe admin forms or move the page (UAT, iPhone report 15 Oct).
Runs on a read-only preview built by tools/build_preview.py (demo data; the preview "changes" its data every 10 s like a busy day).
  python3 tools/form_keep_check.py <preview_dir> [--quick]
Part A: real refresh pipeline (core polling -> TLB.on -> redraw), 3 cycles, promo form.
Part B: every form, 5 forced automatic redraws each (the same handler the data events call), values + scroll position checked.
Part C: a field in use (date picker open) and a finger on the screen postpone the redraw."""
import os,sys
from playwright.sync_api import sync_playwright
d=os.path.abspath(sys.argv[1]);quick='--quick' in sys.argv;fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
FORMS=[ # name, how to open, [(selector, value)], fields read back
 ('promo (new)',"tab='c';showAddP=true;render()",[('#pcode','SALE10'),('#pkind','fixed'),('#pval','15'),('#pmin','100'),('#pmax','50'),('#pfr','2026-10-20'),('#pto','2026-10-30')]),
 ('banner (new)',"tab='b';BE=null;BD=null;showAddB=true;render()",[('#bt','Скидка выходного дня'),('#bpl','bottom'),('#bfr','2026-10-21'),('#bto','2026-11-05'),('#bo','3')]),
 ('banner (edit)',"tab='b';render();openBE('bn1')",[('#app input[type=text]','Новый заголовок'),('#app input[type=date] >> nth=0','2026-10-22'),('#app input[type=date] >> nth=1','2026-11-06')]),
 ('happy hour (new)',"tab='y';HE=null;render();heOpen()",[('#he_t','Обеденный час'),('#app input[type=time] >> nth=0','12:30'),('#app input[type=time] >> nth=1','15:45'),('#app input[min="1"][max="90"]','35')]),
 ('happy hour (edit)',"tab='y';HE=null;render();heOpen(TLB.happyHours()[0]&&TLB.happyHours()[0].id)",[('#he_t','Вечер'),('#app input[type=time] >> nth=0','18:10'),('#app input[min="1"][max="90"]','25')]),
 ('loyalty settings',"tab='y';HE=null;render()",[('#ly_cashback_pct','4.5'),('#ly_loyalty_min_order','77')]),
]
def run(pg,E):
    E("()=>{window.__r=0;const R=render;window.render=function(){window.__r++;return R.apply(this,arguments)}}")
    # ---------- A. real pipeline ----------
    E("()=>{tab='c';showAddP=true;render()}")
    for s,v in FORMS[0][2]:
        (pg.select_option(s,v) if s=='#pkind' else pg.fill(s,v))
    E("()=>document.activeElement&&document.activeElement.blur()");pg.mouse.wheel(0,300);pg.wait_for_timeout(300)
    y0=E("()=>scrollY");f0=E("()=>window.__pvTick");r0=E("()=>window.__r")
    if not quick:
        pg.wait_for_timeout(44000)
        cyc=E("()=>window.__pvTick")-f0;rr=E("()=>window.__r")-r0
        vals=[E("s=>document.querySelector(s).value",s) for s,_ in FORMS[0][2]]
        ok(cyc>=3 and rr>=3,'A: %d data refresh cycles reached the app and redrew the screen %d times'%(cyc,rr))
        ok(vals==[v for _,v in FORMS[0][2]],'A: promo form kept every value through the real refreshes %s'%vals)
        ok(abs(E("()=>scrollY")-y0)<=1,'A: page did not move (scrollY %s -> %s)'%(y0,E("()=>scrollY")))
    # ---------- B. every form, 5 forced automatic redraws ----------
    for name,open_js,fields in FORMS:
        E("()=>{"+open_js+"}");pg.wait_for_timeout(150)
        for s,v in fields:
            el=pg.locator(s).first
            if el.evaluate("e=>e.tagName")=='SELECT': el.select_option(v)
            else: el.fill(v)
        E("()=>document.activeElement&&document.activeElement.blur()")
        E("()=>{const m=document.documentElement.scrollHeight-innerHeight;scrollTo(0,Math.min(260,m))}");y0=E("()=>scrollY")
        r0=E("()=>window.__r")
        for i in range(5): E("()=>{lastTouch=0;autoR()}")
        got=[pg.locator(s).first.input_value() for s,_ in fields]
        ok(E("()=>window.__r")-r0==5,'B %s: 5 automatic redraws really happened'%name)
        ok(got==[v for _,v in fields],'B %s: values kept %s'%(name,got))
        ok(abs(E("()=>scrollY")-y0)<=1,'B %s: scroll kept (%s -> %s)'%(name,y0,E("()=>scrollY")))
    # the new-banner picture preview survives too
    E("()=>{tab='b';BE=null;BD=null;showAddB=true;bimg='data:image/gif;base64,R0lGODlhAQABAAAAACw=';render();lastTouch=0;autoR()}")
    ok(E("()=>{const i=$('bp');return !!i&&i.style.display=='block'&&i.src.startsWith('data:')}"),'B banner (new): chosen picture still shown after a redraw')
    E("()=>{bimg='';showAddB=false;render()}")
    # a value changed on the server meanwhile wins over the stale screen (no silent overwrite of someone else's save)
    E("()=>{tab='y';HE=null;render()}");pg.fill('#ly_cashback_pct','9');E("()=>document.activeElement.blur()")
    E("()=>{const s=TLB.settings();s.cashback_pct=2;lastTouch=0;autoR()}")
    ok(pg.input_value('#ly_cashback_pct')=='2','B loyalty: when the saved value itself changed, the screen shows the new saved value')
    # ---------- C. postpone while in use ----------
    E("()=>{tab='c';showAddP=true;render()}");pg.fill('#pcode','KEEP1')
    pg.focus('#pfr');r0=E("()=>window.__r");E("()=>{lastTouch=0;autoR()}")
    ok(E("()=>window.__r")==r0,'C: no redraw while the date field is open (picker on iPhone)')
    E("()=>document.activeElement.blur()");pg.wait_for_timeout(1700)
    ok(E("()=>window.__r")>r0 and pg.input_value('#pcode')=='KEEP1','C: redraw done after the field closed, input kept')
    r0=E("()=>window.__r");E("()=>{document.dispatchEvent(new Event('touchstart'));autoR()}")
    ok(E("()=>window.__r")==r0,'C: no redraw while a finger is on the screen / scrolling')
    pg.wait_for_timeout(1400);ok(E("()=>window.__r")>r0,'C: redraw done 1.2 s after the finger stopped')
with sync_playwright() as p:
    b=p.chromium.launch()
    for vw in [(390,844),(360,780)]:
        pg=b.new_page(viewport={'width':vw[0],'height':vw[1]},is_mobile=True,has_touch=True,device_scale_factor=2);errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda x:x.accept())
        pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
        pg.goto('file://'+d+'/admin.html');pg.wait_for_timeout(2500)
        print('--- viewport %dx%d (portrait)'%vw);run(pg,pg.evaluate)
        ok(not errs,'no JS errors '+str(errs[:2]));pg.close();quick=True   # the slow real-pipeline part once is enough
    b.close()
print('FORM FAILS',len(fails));sys.exit(1 if fails else 0)
