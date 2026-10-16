"""Restaurant «Аналитика» must use what was RECORDED on each order (commission, happy-hour discount, points, cashback, free delivery
paid by the restaurant) — never today's store %. Demo data is changed inside the read-only preview only.
  python3 tools/merchant_stats_check.py <merchant_preview_dir>"""
import sys
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.goto('file://'+sys.argv[1]+'/merchant.html');pg.wait_for_timeout(2500);E=pg.evaluate;E("()=>TLB.setLang('ru')")
    def stat():
        E("()=>{setTab('s');per='dD';render()}");pg.wait_for_timeout(400)
        return E("()=>[...document.querySelectorAll('#app .k b')].map(x=>x.innerText)"),E("()=>$('app').innerText")
    def change(js): E("()=>{const o=window.__pvTables.orders.find(x=>x.id=='ord4');"+js+";document.dispatchEvent(new Event('visibilitychange'))}");pg.wait_for_timeout(2500)
    k,_=stat();ok(k==['1','440','374'],'A as recorded (10 %%, commission 44, free delivery 22): 1 / 440 / 374 → %s'%k)
    change("o.commission_pct=8;o.commission=35.2");k,_=stat()
    ok(k==['1','440','382.8'],'B order recorded at 8 %% (35.20), store now 10 %%: 440 − 35.20 − 22 = 382.80 → %s'%k)
    change("o.hh_discount=40;o.commission=32");k,_=stat()
    ok(k==['1','400','346'],'C + happy hour 40, recorded commission 32: revenue 400, net 400 − 32 − 22 = 346 → %s'%k)
    change("o.commission=null");k,tx=stat()
    ok(k[2]=='—' and 'без записанной комиссии' in tx,'D commission not recorded: no guess, «—» and a note → %s'%k)
    ok(not errs,'no JS errors '+str(errs[:2]));b.close()
print('STATS FAILS',len(fails));sys.exit(1 if fails else 0)
