"""Checks a read-only preview built by tools/build_preview.py: demo data loads, no request leaves for Supabase,
every write path the admin can click is refused. python3 tools/preview_check.py <preview_dir>"""
import os,sys
from playwright.sync_api import sync_playwright
d=os.path.abspath(sys.argv[1]);fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});reqs=[];errs=[];dl=[]
    pg.on('request',lambda r:reqs.append(r.url));pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda x:(dl.append(x.message),x.accept()))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))   # anything external would be visible in reqs
    pg.goto('file://'+d+'/admin.html');pg.wait_for_timeout(2500);E=pg.evaluate
    ok('ПРЕВЬЮ' in E("()=>document.body.innerText") and E("()=>TLB.orders().length")>0,'demo data shown under a PREVIEW strip')
    tries=[("status change","TLB.setStatus('ord0','cancelled')"),("banner save","TLB.updateBanner?TLB.updateBanner('bn1',{title:'x'}):Promise.resolve(null)"),
           ("rating resolve","TLB.resolveRating('ord1','x')"),("store edit","TLB.updateStore('s1',{name:'x',description:'',phone:'+992900000001',address:'',category:'rest',fee_type:'fixed',fee_base:10,discount_pct:0})"),
           ("promo add","TLB.addPromo({code:'ZZZ1',kind:'percent',value:5,min_order:0})"),("settings","TLB.setSetting('delivery_free_km',3)"),
           ("wallet adjust","TLB.walletAdjust('u3',10,'test note')"),("assign driver","TLB.assignDriver('ord1','u2')"),("ticket reply","TLB.ticketStaffReply('t1','hello')"),
           ("happy hour","TLB.saveHH({title:'x',store:'',days:[1],start:'10:00',end:'11:00',pct:10,active:true})"),("delete banner","TLB.deleteBanner('bn1')")]
    for n,js in tries:
        r=E("async()=>{const n0=window.__pvBlocked.length;try{const r=await ("+js+");return [window.__pvBlocked.length-n0,r&&r.error?String(r.error):'']}catch(e){return [window.__pvBlocked.length-n0,'throw '+e.message]}}")
        ok(r[0]>=1 or r[1]=='bad_value','%s → refused %s'%(n,r))
    # a real click in the UI: banner editor save
    E("()=>{tab='b';render();openBE('bn1')}");n0=E("()=>window.__pvBlocked.length")
    E("()=>[...document.querySelectorAll('button')].find(b=>(b.getAttribute('onclick')||'')=='bannerSave()').click()");pg.wait_for_timeout(500)
    ok(E("()=>window.__pvBlocked.length")>n0 and 'запись отключена' in E("()=>document.body.innerText"),'clicking "save banner" is refused with a visible notice')
    ext=[u for u in reqs if u.startswith('http')]
    ok(not [u for u in ext if 'supabase' in u],'no request to Supabase (%d external requests: %s)'%(len(ext),sorted(set(u.split('/')[2] for u in ext))))
    ok(not errs,'no JS errors '+str(errs[:2]))
    b.close()
print('PREVIEW FAILS',len(fails));sys.exit(1 if fails else 0)
