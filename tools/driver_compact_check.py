"""COMPACT-01 (31 Oct): affected checks for the compact driver card that replaced the draggable panel.
Actual driver.html + talabat-core.js with the existing isolated service doubles (tools/driver_a_fixture.py).
Chromium (Playwright) with an iPhone user agent and touch — NOT Safari/WebKit and NOT a real iPhone.
No live services, no order/account writes outside the in-page double. MAP_LEAFLET points to local Leaflet dist.
Screenshots at width 390: waiting, offer, active order, details (+ pickup confirmation).
"""
from pathlib import Path
import os, sys, subprocess, json, time, base64, ast
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('COMPACT_OUT', '/tmp/talabot-compact')); OUT.mkdir(exist_ok=True)
SHOTS = Path(os.environ.get('COMPACT_SHOTS', str(OUT)))
subprocess.run([sys.executable, str(ROOT / 'tools/driver_a_fixture.py'), str(OUT)], check=True, capture_output=True)
FIX = (OUT / 'review-fixture.js').read_text()
tree = ast.parse((ROOT / 'tools/driver_polish_preview.py').read_text())
WRAP = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'WRAP' for t in n.targets))
LEAF = Path(os.environ['MAP_LEAFLET'])
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
results = []
def check(v, msg):
    if not v: raise AssertionError(msg)
    results.append(msg); print('PASS', msg, flush=True)
def wait(p, fn, t=12):
    end = time.monotonic() + t
    while time.monotonic() < end:
        if p.evaluate(fn): return
        p.wait_for_timeout(60)
    raise AssertionError('timeout: ' + fn)
SPY = """()=>{window.__calls={};for(const k of ['driverAccept','driverArrived','setStatus','deliver','decline']){const f=TLB[k];TLB[k]=async(...a)=>{__calls[k]=(__calls[k]||0)+1;return f.apply(TLB,a)}}}"""
def boot(b, case, w=390, h=760, query=''):
    ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=True, has_touch=True, device_scale_factor=2,
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1')
    ctx.add_init_script("window.__UI_CASE=" + json.dumps(case) + ";localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.reject(Error('isolated UI'));")
    reqs = []
    def route(r):
        u = r.request.url; reqs.append(u)
        if 'supabase-js' in u: r.fulfill(content_type='application/javascript', body=FIX + '\n' + WRAP)
        elif 'leaflet.js' in u: r.fulfill(content_type='application/javascript', body=(LEAF / 'leaflet.js').read_text())
        elif 'leaflet.css' in u: r.fulfill(content_type='text/css', body=(LEAF / 'leaflet.css').read_text())
        elif 'tile.openstreetmap.org' in u: r.fulfill(content_type='image/png', body=PNG)
        elif u.startswith('http'): r.abort()
        else: r.continue_()
    ctx.route('**/*', route); p = ctx.new_page(); errors = []; p.on('pageerror', lambda e: errors.append(str(e)))
    p.goto((ROOT / 'driver.html').as_uri() + query); wait(p, '()=>!!DRV')
    p.evaluate("async()=>{Object.assign(GEO,{state:'ok',lat:38.56,lng:68.78,acc:10,at:Date.now()});const x=__UI_TABLES.orders.find(x=>x.id==='ord1');x.lat=38.58;x.lng=68.80;x.delivery_km=2.4;online=true;await TLB.reload();render()}")
    p.evaluate(SPY); p.wait_for_timeout(300)
    return ctx, p, errors, reqs
def no_drag(p, tag):
    check(p.evaluate("()=>!document.querySelector('#a-grip,.a-grip,#a-mode-toggle,.a-panel-top,#swk,#swp,.a-swipe-help,#w-grip,.w-grip')"), tag + ': no grip, no Работа/Карта toggle, no swipe track')
    check(p.evaluate("()=>!document.querySelector('script[src*=\"grip-debug\"]')&&!/GRIP DEBUG/.test(document.body.innerText)"), tag + ': grip diagnostics not loaded')
def shot(p, name): p.screenshot(path=str(SHOTS / name)); print('SHOT', name)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    # 1 waiting
    ctx, p, errors, reqs = boot(b, 'empty')
    p.wait_for_selector('#w-sheet'); p.wait_for_timeout(300)
    no_drag(p, 'waiting')
    r = p.evaluate("()=>{const s=$('w-sheet').getBoundingClientRect(),n=document.querySelector('.nav').getBoundingClientRect();return {top:s.top,bottom:s.bottom,nav:n.top,h:innerHeight}}")
    check(abs(r['bottom'] - r['nav']) <= 1 and r['bottom'] - r['top'] < 0.35 * r['h'], 'waiting: small bar sits on the nav and takes < 35%% of the height (%d px)' % (r['bottom'] - r['top']))
    check('Наличные' in p.inner_text('#w-sheet'), 'waiting: cash on hand stays visible in the bar')
    p.evaluate("()=>{TLB.myCash=()=>9999;render()}"); p.wait_for_timeout(150)
    check(p.locator('#w-sheet .warn.r').count() == 1, 'waiting: cash over the limit shows a red alert in the bar')
    ctx.close(); ctx, p, errors, reqs = boot(b, 'empty'); p.wait_for_selector('#w-sheet'); p.wait_for_timeout(400)
    shot(p, '01-waiting-390.png')
    check(not errors, 'waiting: no page errors')
    ctx.close()
    # 2 offer
    ctx, p, errors, reqs = boot(b, 'offer', query='?debug=grip')
    p.evaluate("async()=>{__UI_OFFER[0].dist_km=1.2;__UI_OFFER[0].mode='single';__UI_OFFER[0].secs_left=30;await TLB.reload();render()}"); p.wait_for_selector('.k-offer'); p.wait_for_timeout(200)
    no_drag(p, 'offer (even with ?debug=grip)')
    check(not any('grip-debug' in u for u in reqs), 'offer: ?debug=grip no longer requests grip-debug.js')
    txt = p.inner_text('#a-sheet')
    check('Ваш заработок' in txt and 'Демо-ресторан' in txt and '82-й микрорайон' in txt, 'offer: earnings, restaurant and destination on the compact card')
    check('по прямой' in txt and 'оценка' in txt and '≈' in txt, 'offer: distances are labelled as estimates (≈ … по прямой / оценка)')
    check(not any(k in txt for k in ['мин', 'прибыт', 'ETA']), 'offer: no arrival time is shown')
    check(p.inner_text('#k-main').strip() == 'Принять заказ' and p.locator('.k-decline').count() == 1, 'offer: «Принять заказ» and the existing decline')
    shot(p, '02-offer-390.png')
    p.evaluate("()=>{const b=$('k-main');b.click();b.click();kAct();kAct()}"); wait(p, "()=>!AFlight&&!!mine()")
    check(p.evaluate('__calls.driverAccept') == 1, 'offer: accept is one tap; repeated taps call the server once')
    check(p.evaluate("()=>!!document.querySelector('.k-active')"), 'offer: after the server result the card moves to the active stage')
    check(not errors, 'offer: no page errors')
    ctx.close()
    # 2b offer timeout keeps working
    ctx, p, errors, reqs = boot(b, 'offer')
    p.evaluate("async()=>{__UI_OFFER[0].mode='single';__UI_OFFER[0].secs_left=1;await TLB.reload();render()}"); p.wait_for_timeout(1800); p.evaluate('render()')
    check(p.locator('.k-offer').count() == 0, 'offer: the existing offer timeout removes the card')
    ctx.close()
    # 3 active order: stage 2 (at restaurant, ready) -> pickup needs explicit confirm
    ctx, p, errors, reqs = boot(b, 'pickup')
    p.wait_for_selector('.k-active'); p.wait_for_timeout(300)
    no_drag(p, 'active')
    txt = p.inner_text('#a-sheet')
    check('Этап 2 из 4' in txt and 'Демо-ресторан' in txt and 'проспект Рудаки' in txt, 'active: stage, restaurant name and short address on the card')
    check(all(k in txt for k in ['Навигация', 'Позвонить', 'Чат', 'Детали']), 'active: Навигация / Позвонить / Чат / Детали buttons')
    check('Получить от клиента' in txt and '120,00' in txt, 'active: amount to collect on the card (cash order)')
    check('Товары' not in txt and 'Итого' not in txt, 'active: invoice is not on the card (moved to details)')
    shot(p, '03-active-390.png')
    p.click('.k-act-chat'); p.wait_for_selector('.a-chat-modal')
    check(p.locator('.a-chat-modal .qrow .chip').count() >= 2 and p.locator('.a-chat-modal #ci').count() == 1, 'chat: «Чат» opens the existing chat with stage quick replies and input')
    p.evaluate('chatOpen=false;render()'); p.wait_for_timeout(100)
    p.click('#k-main'); p.wait_for_selector('.k-ask')
    check(p.evaluate('__calls.setStatus||0') == 0, 'pickup: first tap only opens an explicit confirmation')
    shot(p, '05-pickup-confirm-390.png')
    p.click('.k-ask .b.s'); p.wait_for_timeout(150)
    check(p.locator('.k-ask').count() == 0 and p.evaluate('__calls.setStatus||0') == 0, 'pickup: «Отмена» closes without calling the server')
    p.click('#k-main'); p.wait_for_selector('.k-ask'); p.evaluate("()=>{const y=document.querySelector('.k-yes');y.click();y.click()}")
    wait(p, "()=>!AFlight&&mine()&&mine().status==='pickedup'")
    check(p.evaluate('__calls.setStatus') == 1, 'pickup: confirmed once → setStatus(pickedup) once, after the server result the stage advances')
    check(not errors, 'active: no page errors')
    ctx.close()
    # 3b stage 2 while the restaurant is still cooking: button locked with the existing reason
    ctx, p, errors, reqs = boot(b, 'pickup')
    p.evaluate("async()=>{__UI_TABLES.orders.find(x=>x.id==='ord1').status='preparing';await TLB.reload();render()}"); p.wait_for_timeout(200)
    check(p.locator('#k-main').is_disabled() and 'ещё готовит' in p.inner_text('#k-main'), 'pickup: locked while preparing (existing availability rule)')
    ctx.close()
    # 4 details: scrollable modal with close, no drag
    ctx, p, errors, reqs = boot(b, 'pickup', h=640)
    p.wait_for_selector('.k-active'); p.click('.k-act-details'); p.wait_for_selector('.k-dialog')
    body = p.evaluate("()=>{const b=document.querySelector('.k-dialog .a-dialog-body');return {sh:b.scrollHeight,ch:b.clientHeight,ov:getComputedStyle(b).overflowY,t:b.innerText}}")
    check(body['ov'] == 'auto' and body['sh'] > body['ch'], 'details: long content scrolls inside the modal (%d > %d)' % (body['sh'], body['ch']))
    check(all(k in body['t'] for k in ['Счёт', 'Итого', 'проспект Рудаки', '82-й микрорайон']), 'details: invoice, full addresses and next stop are in details')
    ctx.close(); ctx, p, errors, reqs = boot(b, 'pickup'); p.wait_for_selector('.k-active'); p.click('.k-act-details'); p.wait_for_selector('.k-dialog'); p.wait_for_timeout(150)
    shot(p, '04-details-390.png')
    p.click('.k-dialog .a-dialog-head .round'); p.wait_for_timeout(150)
    check(p.locator('.k-dialog').count() == 0, 'details: close button closes the modal')
    # map pan still works over the free map area
    c0 = p.evaluate('()=>DM.getCenter()'); box = p.evaluate("()=>{const r=$('a-sheet').getBoundingClientRect();return {y:r.top}}")
    p.mouse.move(195, box['y'] / 2); p.mouse.down(); p.mouse.move(120, box['y'] / 2 + 60, steps=8); p.mouse.up(); p.wait_for_timeout(200)
    c1 = p.evaluate('()=>DM.getCenter()')
    check(abs(c0['lat'] - c1['lat']) + abs(c0['lng'] - c1['lng']) > 1e-5, 'map: pan above the card still moves the map')
    check(not errors, 'details: no page errors')
    ctx.close()
    # 5 delivery: non-cash needs explicit confirm; cash keeps the existing amount confirmation (DV)
    ctx, p, errors, reqs = boot(b, 'noncash')
    p.wait_for_selector('.k-active'); check('Этап 4 из 4' in p.inner_text('#a-sheet') and 'Оплачено онлайн' in p.inner_text('#a-sheet'), 'delivery (card): stage 4 and «Оплачено онлайн» on the card')
    p.click('#k-main'); p.wait_for_selector('.k-ask'); check(p.evaluate('__calls.deliver||0') == 0, 'delivery (card): first tap only opens an explicit confirmation')
    p.evaluate("()=>{const y=document.querySelector('.k-yes');y.click();y.click()}"); wait(p, "()=>!AFlight&&TLB.order('ord1')?.status==='delivered'")
    check(p.evaluate('__calls.deliver') == 1, 'delivery (card): confirmed once → deliver once')
    check(not errors, 'delivery (card): no page errors')
    ctx.close()
    ctx, p, errors, reqs = boot(b, 'delivery')
    p.wait_for_selector('.k-active'); p.click('#k-main'); p.wait_for_timeout(200)
    check(p.evaluate('!!DV') and p.evaluate('__calls.deliver||0') == 0, 'delivery (cash): tap opens the existing amount confirmation, nothing sent yet')
    check(not errors, 'delivery (cash): no page errors')
    ctx.close()
    b.close()
(OUT / 'compact-results.json').write_text(json.dumps({'checks': len(results), 'results': results, 'engine': 'chromium (iPhone UA)', 'webkit': False, 'real_device': False}, ensure_ascii=False, indent=2))
print('TOTAL', len(results))
