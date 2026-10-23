"""Preview diagnostic log (admin): caller names read the same from Chrome and Safari stack formats, every menu section tap writes
one «SECTION TAP» line (from/to section, strip place, page offsets, strip sideways offset, page height, 0.8 s follow-up, touch time),
the build id is in the log, and no personal data is recorded. Chromium only.  python3 tools/diag_check.py <admin_preview_dir>"""
import sys,json,re
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':430,'height':815},is_mobile=True,has_touch=True);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.goto('file://'+sys.argv[1]+'/admin.html');pg.wait_for_timeout(2500);E=pg.evaluate;E("()=>TLB.setLang('ru')");pg.wait_for_timeout(800)
    C=lambda st:E("s=>__pvCallers(s)",st)
    ok(C('@file:///p.js:1:2\ntabKeep@file:///admin.html:686:9\nonclick@file:///admin.html:1:30')=='tabKeep<onclick','Safari stack (no first line): tabKeep<onclick')
    ok(C('@file:///p.js:1:2\nrender@file:///a.html:697:1\ncuLoad@file:///a.html:900:1\nonclick@file:///a.html:1:3')=='render<cuLoad<onclick','Safari stack: render<cuLoad<onclick')
    ok(C('Error\n    at window.scrollTo (file:///p.js:1:2)\n    at tabKeep (file:///a.html:686:9)\n    at HTMLButtonElement.onclick (file:///a.html:1:3)')=='tabKeep<onclick','Chrome stack: tabKeep<onclick')
    E("()=>window.scrollTo(0,329)");pg.wait_for_timeout(300)
    seq=['s','o','d','u','h']
    for k in seq:
        pg.locator('.tabs button[onclick*="tab=\'%s\'"]'%k).click(position={'x':12,'y':32});pg.wait_for_timeout(1100)
    L=json.loads(E("()=>localStorage.getItem('pv-diag')"))
    nav=[l for l in L if ' SECTION TAP ' in l]
    ok(len(nav)==len(seq),'one SECTION TAP line per tap (%d/%d)'%(len(nav),len(seq)))
    pat=re.compile(r'SECTION TAP · (\w)→(\w) · strip -?\d+→-?\d+ · y before \d+ / after redraw \d+ / after keep \d+ · strip sideways \d+→\d+ · page h \d+→\d+.* · 0\.8 s after: .* · last touch \d+ms ago')
    pairs=list(zip(['o']+seq,seq))
    for l,(a,c) in zip(nav,pairs):
        m=pat.search(l);ok(bool(m) and m.group(1)==a and m.group(2)==c,'line %s→%s has every field: %s'%(a,c,l[9:150]))
    ok(any('tabKeep<onclick' in l for l in L if 'app scrollTo' in l),'app scrollTo by the strip keep step is named tabKeep<onclick')
    ok(any('PAGE LOAD · build ' in l for l in L),'build id in PAGE LOAD')
    txt=' '.join(L)
    names=E("()=>[...new Set((window.__pvTables.profiles||[]).flatMap(p=>[p.full_name,p.phone]).filter(Boolean))]")
    leak=[n for n in names if n and len(n)>3 and n in txt]
    ok(not leak and not re.search(r'\+?992\d{6,}',txt),'no names or phones in the log %s'%leak[:3])
    ok(not errs,'no JS errors %s'%errs[:2]);b.close()
print('DIAG FAILS',len(fails));sys.exit(1 if fails else 0)
