import server,threading,json,uuid,concurrent.futures,pathlib,base64,zlib,os
from playwright.sync_api import sync_playwright
lab=server.lab
result={'source':os.environ.get('GITHUB_SHA'),'synthetic_provider':True,'live':False,'checks':[]}
def check(v,label):
    assert v,label
    result['checks'].append(label);print('PASS '+label,flush=True)
def count():
    with lab.db() as c:return lab.q(c,'select count(*) from orders')
try:
    server.setup()
    result['prior_payment_guards']='passed in 42124389687; ATTEMPT-1.json; not rerun'
    http=server.ThreadingHTTPServer(('127.0.0.1',8088),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start()
    with sync_playwright() as p:
        b=p.chromium.launch();page=b.new_page(viewport={'width':1100,'height':900});page.goto('http://127.0.0.1:8088')
        page.get_by_role('button',name='طلب جديد ودفع إلكتروني اختباري',exact=True).click()
        page.get_by_role('button',name='تأكيد نجاح الدفع من مزوّد الاختبار',exact=True).last.click()
        page.locator('[data-order]').wait_for();oid=int(page.locator('[data-order]').first.get_attribute('data-order'))
        check(count()==1,'server-confirmed UI payment creates one order')
        result['merchant_after_payment']=server.state('merchant')
        print('MERCHANT_STATE '+json.dumps(result['merchant_after_payment'],default=str),flush=True)
        page.get_by_role('button',name='إعادة إشعار الدفع نفسه',exact=True).click()
        page.get_by_role('button',name='المطعم',exact=True).click();page.get_by_role('button',name='قبول وبدء التحضير',exact=True).click()
        page.get_by_role('button',name='الإدارة',exact=True).click();page.get_by_role('button',name='تعيين السائق',exact=True).click()
        page.get_by_role('button',name='المطعم',exact=True).click();page.get_by_role('button',name='الطلب جاهز للاستلام',exact=True).click()
        page.get_by_role('button',name='السائق',exact=True).click();page.get_by_role('button',name='استلام الطلب المدفوع',exact=True).click()
        page.get_by_role('button',name='تأكيد التسليم دون قبض نقدي',exact=True).click()
        page.wait_for_function("document.querySelector('[data-order]')?.textContent.includes('delivered')")
        page.screenshot(path=str(server.ROOT/'journey-driver.png'),full_page=True)
        for r in ['الزبون','المطعم','الإدارة']:
            page.get_by_role('button',name=r,exact=True).click();page.wait_for_function("document.querySelector('[data-order]')?.textContent.includes('delivered')")
        page.screenshot(path=str(server.ROOT/'journey-admin.png'),full_page=True)
        check(not page.locator('#error').inner_text(),'four role screens complete delivery without errors');b.close()
    with lab.db() as c:
        iid=lab.q(c,'select id from electronic_test.intents where order_id=%s',(oid,))
        row=c.execute('select status,payment,cash_collected from orders where id=%s',(oid,)).fetchone()
        check(row==('delivered','card',None),'delivered prepaid order collects no customer cash')
        check(lab.q(c,'select count(*) from return_private.cases')==0,'no driver restaurant advance or return claim')
        check(lab.q(c,'select count(*) from finance_private.commands')==0,'no financial settlement command')
    signed=server.event(str(iid),'succeeded')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:ids=list(pool.map(lambda _:server.confirm(*signed),range(6)))
    check(ids==[oid]*6 and count()==1,'concurrent replay and lost response return same order')
    check(server.confirm(*server.event(str(iid),'failed'))==oid,'late failure does not undo confirmed order')
    # Concurrent first confirmation tests transaction-level uniqueness, not just cached replay.
    fresh=server.intent(str(uuid.uuid4()));signed=server.event(str(fresh['id']),'succeeded')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:ids=list(pool.map(lambda _:server.confirm(*signed),range(6)))
    check(len(set(ids))==1 and count()==2,'concurrent first success creates exactly one order')
    check(server.state('merchant')['orders'] and all(o['payment']=='card' for o in server.state('merchant')['orders']),'merchant sees confirmed payments only')
    result['pass']=True
except Exception as e:
    try: result['ui_error']=page.locator('#error').inner_text();result['ui_content']=page.locator('#content').inner_text()[:1500]
    except Exception: pass
    result['pass']=False;result['error']=str(e)[:500];raise
finally:
    lab.save(server.ROOT/'result.json',result)
    print('ELECTRONIC_RESULT='+base64.b64encode(zlib.compress(json.dumps(result).encode())).decode(),flush=True)
