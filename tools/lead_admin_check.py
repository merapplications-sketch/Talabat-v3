"""Admin panel: requests from the partner page (patch 36) on the read-only preview, by real taps — card, badge, contacted /
reject (reason required) call the right server function with the request id, linking is off (button disabled, no call),
stores staff sees no link control, branch requests still shown apart; customer home: the partner banner opens partner.html.
  python3 tools/lead_admin_check.py <admin_preview_dir> <customer_preview_dir>"""
import sys
from playwright.sync_api import sync_playwright
A,Cu=sys.argv[1],sys.argv[2];fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for vw,lang in [((390,844),'ru'),((1366,900),'en')]:
        pg=b.new_page(viewport={'width':vw[0],'height':vw[1]},is_mobile=vw[0]<700,has_touch=vw[0]<700);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
        dialogs=[];pg.on('dialog',lambda d:(dialogs.append(d.message),d.accept()))
        pg.goto('file://'+A+'/admin.html');pg.wait_for_timeout(2500);E=pg.evaluate;E("l=>TLB.setLang(l)",lang);pg.wait_for_timeout(400);tag='[%dx%d %s]'%(vw[0],vw[1],lang)
        badge=E("()=>{const b=document.querySelector('.tabs button[onclick*=\"tab=\\'s\\'\"] em');return b?b.innerText:''}")
        ok(badge=='2',tag+' Stores tab badge = 1 pending branch request + 1 new website request (%s)'%badge)
        pg.locator('.tabs button[onclick*="tab=\'s\'"]').click();pg.wait_for_timeout(500)
        ok(pg.locator('#lead-card').count()==1 and pg.locator('#lead-card .card').count()==2,tag+' website requests card: 2 open (new + contacted)')
        txt=pg.inner_text('#lead-card')
        ok(('подключено' in txt and 'отклонено' in txt) if lang=='ru' else ('connected' in txt and 'rejected' in txt),tag+' closed requests listed under it')
        ok('Новая кофейня' in pg.inner_text('#app') and 'Новая кофейня' not in txt,tag+' the branch request stays in its own card')
        n0=E("()=>__pvBlocked.length")
        pg.locator('#lead-pv-ld1 button:has-text("%s")'%('Связались' if lang=='ru' else 'Contacted')).click();pg.wait_for_timeout(400)
        ok(E("()=>__pvBlocked.slice(-1)[0]")=='rpc lead_set_status' and E("()=>__pvBlocked.length")==n0+1,tag+' «Связались» → lead_set_status called (write refused by the preview)')
        pg.locator('#lead-pv-ld2 button:has-text("%s")'%('Отклонить' if lang=='ru' else 'Reject')).click();pg.wait_for_timeout(300)
        ok(E("()=>__pvBlocked.length")==n0+1 and dialogs,tag+' reject without a reason → asks for it, nothing sent')
        pg.fill('#ldn-pv-ld2','Нет курьеров в районе');pg.locator('#lead-pv-ld2 button:has-text("%s")'%('Отклонить' if lang=='ru' else 'Reject')).click();pg.wait_for_timeout(400)
        ok(E("()=>__pvBlocked.length")==n0+2,tag+' reject with a reason → lead_set_status called')
        lk=pg.locator('#lead-pv-ld1 button:has-text("%s")'%('Привязать' if lang=='ru' else 'Link'))
        ok(lk.count()==1 and lk.is_disabled(),tag+' admin: «Привязать к магазину» shown but disabled (assign_owner not verified)')
        E("()=>leadDo('pv-ld1','link')");pg.wait_for_timeout(200);ok(E("()=>__pvBlocked.length")==n0+2,tag+' link action does nothing while off')
        E("()=>{TLB.isSuper=()=>false;render()}");pg.wait_for_timeout(300)
        ok(pg.locator('#lead-card').count()==1 and pg.locator('#lead-card button:has-text("%s")'%('Привязать' if lang=='ru' else 'Link')).count()==0,tag+' stores staff: card and status buttons, no link control')
        ok(not errs,tag+' no JS errors %s'%errs[:1]);pg.close()
    # a STAFF account (not admin) with only the 'stores' permission: the requests must be loaded for it too (v57c fix)
    import tempfile,shutil,os
    T=tempfile.mkdtemp();shutil.copytree(A,T+'/a');pc=open(T+'/a/preview-client.js').read()
    assert 'var role="admin"' in pc and 'my_perms:null' in pc
    open(T+'/a/preview-client.js','w').write(pc.replace('var role="admin"','var role="customer"',1).replace('my_perms:null',"my_perms:['stores']",1))
    pg=b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.goto('file://'+T+'/a/admin.html');pg.wait_for_timeout(2500);E=pg.evaluate;E("()=>TLB.setLang('ru')");pg.wait_for_timeout(400)
    ok(E("()=>TLB.isSuper()")==False and E("()=>TLB.can('stores')")==True,'staff account: not admin, has «stores»')
    ok(E("()=>TLB.storeRequests().filter(q=>q.kind=='lead').length")==4,'staff with «stores»: the website requests are loaded (%d)'%E("()=>TLB.storeRequests().length"))
    pg.locator('.tabs button[onclick*="tab=\'s\'"]').click();pg.wait_for_timeout(500)
    ok(pg.locator('#lead-card .card').count()==2 and pg.locator('#lead-card button:has-text("Привязать")').count()==0,'staff: card with the 2 open requests, status buttons, no link control')
    ok(not errs,'staff: no JS errors %s'%errs[:1]);pg.close();shutil.rmtree(T)
    # customer: the partner banner at the bottom of the home screen opens the partner page
    pg=b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.goto('file://'+Cu+'/customer.html');pg.wait_for_timeout(3000);E=pg.evaluate
    order=E("()=>[...document.querySelectorAll('#app [onclick^=\"bannerGo\"]')].map(e=>e.getAttribute('onclick'))")
    ok(any('pv-bnp' in x for x in order),'customer home: partner banner shown (%d banners)'%len(order))
    pg.locator('[onclick*="pv-bnp"]').first.scroll_into_view_if_needed();pg.locator('[onclick*="pv-bnp"]').first.click();pg.wait_for_timeout(800)
    ok(pg.url.endswith('/partner.html'),'tap on it opens partner.html (%s)'%pg.url.split('/')[-1])
    ok(not errs,'customer: no JS errors %s'%errs[:1]);b.close()
print('LEAD ADMIN FAILS',len(fails));sys.exit(1 if fails else 0)
