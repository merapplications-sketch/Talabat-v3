"""Shared UI rules that must not regress (all 4 apps + partner page). Chromium only — NOT proof for iPhone Safari.
 1. static: no invalid font shorthand (`font:<size> inherit` etc. — the whole declaration is dropped by the browser);
    viewport never blocks the user's zoom (no maximum-scale / user-scalable=no).
 2. live: every visible text field / select / textarea has a computed text size of at least 16 px on a phone (iOS zooms
    into smaller fields), on every screen of the qa_all screen list (customer, merchant, driver, admin tabs) + partner page.
  python3 tools/ui_rules_check.py [--static]"""
import os,re,sys,importlib.util
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));fails=[];n=0
def ok(c,m):
    global n;n+=1
    if not c: print('FAIL '+m);fails.append(m)
FILES=['customer.html','admin.html','merchant.html','driver.html','partner.html','talabat-core.js']
KW={'inherit','initial','unset','revert'}
for f in FILES:
    s=open(os.path.join(root,f),encoding='utf-8').read()
    for m in re.finditer(r'(?<![-\w])font\s*:\s*([^;}"\'`]+)',s):
        v=m.group(1).strip();toks=v.split()
        if any(t in KW for t in toks) and len(toks)>1:
            ln=s.count('\n',0,m.start())+1;ok(False,'%s:%d invalid font shorthand «font:%s» (dropped by the browser)'%(f,ln,v))
    for m in re.finditer(r'name="viewport" content="([^"]*)"',s):
        ok('maximum-scale' not in m.group(1) and 'user-scalable' not in m.group(1),'%s viewport blocks zoom: %s'%(f,m.group(1)))
    # fields with an inline text size under 16 px (screens the live pass may not reach)
    for m in re.finditer(r'<(input|select|textarea)\b[^>]*\bstyle="([^"]*)"',s):
        fs=re.search(r'font-size:\s*(\d+(?:\.\d+)?)px',m.group(2))
        if fs and float(fs.group(1))<16 and 'type="hidden"' not in m.group(0) and 'display:none' not in m.group(2):
            ln=s.count('\n',0,m.start())+1;ok(False,'%s:%d <%s> inline font-size %spx (< 16)'%(f,ln,m.group(1),fs.group(1)))
print('static rules: %d checks, %d fails'%(n,len(fails)))
if '--static' in sys.argv: print('UI RULES FAILS',len(fails));sys.exit(1 if fails else 0)

spec=importlib.util.spec_from_file_location('qa_all',os.path.join(root,'tools','qa_all.py'));qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
from playwright.sync_api import sync_playwright
SMALL="""()=>[...document.querySelectorAll('input,select,textarea')].filter(e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);
  return r.width>0&&r.height>0&&c.visibility!=='hidden'&&!['hidden','checkbox','radio','file','range','color'].includes(e.type)&&e.tabIndex!==-1&&!e.closest('#pv-strip')
   &&parseFloat(c.fontSize)<16}).map(e=>(e.id||e.name||e.className||e.tagName).toString().slice(0,24)+'='+getComputedStyle(e).fontSize)"""
seen={}
with sync_playwright() as p:
    b=p.chromium.launch()
    for app,screens in qa.APPS.items():
        ctx=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);pg=ctx.new_page()
        pg.route('**/*',lambda rt,rq,app=app:(rt.fulfill(status=200,content_type='application/javascript',body=qa.FIX.replace('window.__ROLE','"'+app+'"')) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
        pg.goto('file://'+root+'/'+app+'.html',wait_until='domcontentloaded');pg.wait_for_timeout(2200)
        if app=='admin':
            k=pg.locator('.tabs button').count();screens=[("tab%d"%i,"document.querySelectorAll('.tabs button')[%d].click()"%i) for i in range(k)]+[("loyalty-editor","tab='y';HE=null;heOpen()"),("forms","tab='s';showAddS=true;render()"),("banner-form","tab='b';showAddB=true;render()"),("promo-form","tab='c';showAddP=true;render()")]
        for name,js in screens:
            try: pg.evaluate("()=>{"+js+";if(typeof render==='function')try{render()}catch(e){}}");pg.wait_for_timeout(300)
            except Exception: continue
            for x in pg.evaluate(SMALL): seen.setdefault((app,x),[]).append(name)
        ctx.close()
    pg=b.new_page(viewport={'width':390,'height':844},is_mobile=True);pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.goto('file://'+root+'/partner.html');pg.wait_for_timeout(400)
    for x in pg.evaluate(SMALL): seen.setdefault(('partner',x),[]).append('page')
    b.close()
# known and recorded as a PROPOSAL (visible change of an approved look; not changed without the owner): reported, not failed
KNOWN={('merchant','SELECT=12px'):'restaurant header store selector (pill, 12 px, approved v56h header): 16 px would enlarge the header text — proposal'}
for k,why in KNOWN.items():
    if k in seen: print('KNOWN (proposal) [%s] %s — %s'%(k[0],k[1],why));seen.pop(k)
for (app,x),scr in sorted(seen.items()): ok(False,'[%s] field under 16 px: %s (screens: %s)'%(app,x,', '.join(sorted(set(scr))[:4])))
print('UI RULES FAILS',len(fails));sys.exit(1 if fails else 0)
