"""Restaurant app: every order button works by a real tap with text ids (preview) — production ids are numbers.
History row → order details → close (back to the same list and place); order card buttons: reject sheet, prep time, accept/ready
(writes are refused in the preview; only JS errors are checked). python3 tools/merchant_ids_check.py <merchant_preview_dir>"""
import sys
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for vw in [(390,844),(1366,900)]:
        pg=b.new_page(viewport={'width':vw[0],'height':vw[1]},is_mobile=vw[0]<700,has_touch=vw[0]<700);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
        pg.goto('file://'+sys.argv[1]+'/merchant.html');pg.wait_for_timeout(2500);E=pg.evaluate;E("()=>TLB.setLang('ru')");pg.wait_for_timeout(300);tag='[%dx%d]'%vw
        pg.locator('.nav [onclick="setTab(\'s\')"]').click();pg.wait_for_timeout(400)
        rows=pg.locator('#app [onclick^="OD="]');n=rows.count()
        ok(n>=3,tag+' Аналитика → История has %d order rows'%n)
        for i in range(n):
            r=rows.nth(i);r.scroll_into_view_if_needed();y0=E("()=>Math.round(scrollY)");label=r.inner_text().split('\n')[0]
            r.click();pg.wait_for_timeout(400)
            opened=E("()=>OD!=null&&!!TLB.order(OD)")
            ok(opened and not errs,tag+' tap «%s» opens the order details %s'%(label,errs[:1]))
            pg.locator('.ov .md button[onclick="OD=null;render()"]').first.click();pg.wait_for_timeout(300)
            ok(E("()=>OD==null&&tab=='s'") and abs(E("()=>Math.round(scrollY)")-y0)<=2,tag+' close → back to the same history list and place (%s→%s)'%(y0,E("()=>Math.round(scrollY)")))
        pg.locator('.nav [onclick="setTab(\'o\')"]').click();pg.wait_for_timeout(400)
        for sel,lbl in [('#app [onclick^="rjOpen("]','«Отклонить» opens the reason sheet'),('#app [onclick^="TLB.patch("]','prep-time chip'),('#app [onclick^="st("]','accept / ready')]:
            loc=pg.locator(sel);c=loc.count()
            if c: loc.first.scroll_into_view_if_needed();loc.first.click(force=True);pg.wait_for_timeout(400)
            ok(c>0 and not errs,tag+' %s (%d buttons) %s'%(lbl,c,errs[:1]))
            if 'rjOpen' in sel: ok(E("()=>!!RJ&&TLB.order(RJ.id)!=null"),tag+' reason sheet is for the tapped order');E("()=>{RJ=null;render()}")
        ok(not errs,tag+' no JS errors '+str(errs[:2]));pg.close()
    b.close()
print('MERCHANT IDS FAILS',len(fails));sys.exit(1 if fails else 0)
