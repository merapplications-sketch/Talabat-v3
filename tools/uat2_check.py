"""Batch UAT2-1 (v58): customer cancel waits for the server (UAT002), chat drafts per order until sent (UAT003, customer +
courier), one delivery confirmation at a time (UAT004), hold-2-seconds order confirmation + two-step keyboard path.
Real taps / pointer / keyboard on the read-only previews; the server answers are replaced by controllable promises
(delay, failure, late answers). Chromium only — not proof for iPhone Safari, and not proof of server-side duplicate refusal.
  python3 tools/uat2_check.py <customer_preview_dir> <driver_preview_dir>"""
import sys
from playwright.sync_api import sync_playwright
CU,DR=sys.argv[1],sys.argv[2];fails=[];n=0
def ok(c,m):
    global n;n+=1;print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
# controllable server: window.__q[name] = list of pending calls {args,res,rej}; __calls[name] = count
CTL="""(names)=>{window.__q={};window.__calls={};names.forEach(n=>{window.__q[n]=[];window.__calls[n]=0;
  TLB[n]=function(){const a=[...arguments];window.__calls[n]++;return new Promise((res,rej)=>window.__q[n].push({a,res,rej}))}})}"""
def page(b,d,app,mobile=True,w=390):
    pg=b.new_page(viewport={'width':w,'height':844},is_mobile=mobile,has_touch=mobile);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.on('dialog',lambda dg:dg.accept())
    pg.goto('file://'+d+'/'+app+'.html');pg.wait_for_timeout(2500);pg.evaluate("()=>TLB.setLang('ru')");pg.wait_for_timeout(300);return pg,errs
with sync_playwright() as p:
    b=p.chromium.launch()
    # ================= customer: cancel (UAT002) =================
    pg,errs=page(b,CU,'customer');E=pg.evaluate
    E(CTL,['setStatus']);E("()=>{go('track',{tid:'ord0'})}");pg.wait_for_timeout(300)
    pg.click('#cxbtn');pg.wait_for_timeout(150);pg.locator('#cxbtn').click(force=True);pg.wait_for_timeout(150)
    ok(E("()=>__calls.setStatus")==1,'cancel: two taps while waiting → ONE request (%d)'%E("()=>__calls.setStatus"))
    ok(pg.locator('#cxbtn').is_disabled() and 'Отменяем' in pg.inner_text('#cxbtn'),'cancel: button disabled «Отменяем…» while waiting')
    ok(E("()=>S.v")=='track','cancel: stays on the order until the server answers (no optimistic leave)')
    E("()=>__q.setStatus[0].res({data:null})");pg.wait_for_timeout(300)
    ok(E("()=>S.v")=='orders','cancel: success → orders list')
    # race: the restaurant accepted meanwhile
    E("()=>{window.__pvTables.orders.find(o=>o.id=='ord0').status='pending';go('track',{tid:'ord0'})}");E(CTL,['setStatus']);pg.wait_for_timeout(200)
    pg.click('#cxbtn');pg.wait_for_timeout(100);E("()=>{window.__pvTables.orders.find(o=>o.id=='ord0').status='preparing'}")
    E("()=>__q.setStatus[0].res({error:'bad_transition'})");pg.wait_for_timeout(1200)
    t=pg.inner_text('#cxerr') if pg.locator('#cxerr').count() else ''
    ok(E("()=>S.v")=='track' and 'не отменён' in t and E("()=>t('trk_preparing')") in t,'cancel race (restaurant accepted): reason + REAL status shown «%s»'%t[:70])
    ok(pg.locator('#cxbtn').count()==0,'cancel race: the cancel button is gone (order no longer pending; rule unchanged)')
    # connection lost: request and status check both fail
    E("()=>{window.__pvTables.orders.find(o=>o.id=='ord0').status='pending';go('track',{tid:'ord0'})}");pg.wait_for_timeout(300);E(CTL,['setStatus'])
    E("()=>{window.__rl=TLB.reload;TLB.reload=()=>Promise.reject(new Error('offline'))}")
    pg.click('#cxbtn');pg.wait_for_timeout(100);E("()=>__q.setStatus[0].rej(new TypeError('Failed to fetch'))");pg.wait_for_timeout(400)
    t=pg.inner_text('#cxerr') if pg.locator('#cxerr').count() else ''
    ok('Нет связи' in t and not pg.locator('#cxbtn').is_disabled(),'cancel offline: «no connection, status unknown» and the button usable again «%s»'%t[:60])
    E("()=>{TLB.reload=window.__rl}")
    # still pending + refused for another reason
    E(CTL,['setStatus']);pg.click('#cxbtn');pg.wait_for_timeout(100);E("()=>__q.setStatus[0].res({error:'generic'})");pg.wait_for_timeout(1200)
    ok('Попробуйте ещё раз' in pg.inner_text('#cxerr'),'cancel refused, order still pending → «not cancelled, try again»')
    ok(not errs,'customer cancel: no JS errors %s'%errs[:1])
    # ================= customer: chat drafts (UAT003) =================
    E("()=>{window.__pvTables.orders.find(o=>o.id=='ord1').status='pickedup';go('track',{tid:'ord1'})}");pg.wait_for_timeout(400)
    has_ci=pg.locator('#ci').count()==1;ok(has_ci,'chat input on a live order')
    E(CTL,['chat'])
    pg.fill('#ci','Здравствуйте, я у подъезда');pg.click('#cisend');pg.wait_for_timeout(100);pg.locator('#cisend').click(force=True);pg.wait_for_timeout(100)
    ok(E("()=>__calls.chat")==1 and pg.locator('#cisend').is_disabled(),'chat: two taps while sending → ONE send, button disabled')
    ok(pg.input_value('#ci')=='Здравствуйте, я у подъезда','chat: text stays in the field while sending')
    E("()=>render()");ok(pg.input_value('#ci')=='Здравствуйте, я у подъезда','chat: an automatic redraw keeps the unsent text')
    pg.fill('#ci','Здравствуйте, я у подъезда, 3 этаж')
    E("()=>__q.chat[0].res({ok:true})");pg.wait_for_timeout(200)
    ok(pg.input_value('#ci')=='Здравствуйте, я у подъезда, 3 этаж','chat: the late answer does not clear the newer text')
    pg.fill('#ci','Где вы?');pg.click('#cisend');pg.wait_for_timeout(100);E("()=>__q.chat[1].res({error:'generic'})");pg.wait_for_timeout(200)
    ok(pg.input_value('#ci')=='Где вы?' and pg.locator('#cierr').count()==1 and not pg.locator('#cisend').is_disabled(),'chat failed: text kept, message shown, can retry')
    pg.click('#cisend');pg.wait_for_timeout(100);ok(E("()=>__calls.chat")==3 and E("()=>__q.chat[2].a[2]")=='Где вы?','chat retry sends the same text')
    # per order: a late success for order 1 while order 3 is open does not touch order 3's text
    E("()=>{window.__pvTables.orders.find(o=>o.id=='ord3').status='pickedup';go('track',{tid:'ord3'})}");pg.wait_for_timeout(300)
    pg.fill('#ci','Текст для другого заказа');E("()=>__q.chat[2].res({ok:true})");pg.wait_for_timeout(200)
    ok(pg.input_value('#ci')=='Текст для другого заказа','chat: a late answer for another order leaves this order\'s text')
    E("()=>go('track',{tid:'ord1'})");pg.wait_for_timeout(300)
    ok(pg.input_value('#ci')=='','chat: back on order 1 → its sent text was cleared (only after the server confirmed)')
    ok(not errs,'customer chat: no JS errors %s'%errs[:1]);pg.close()
    # ================= customer: hold to confirm =================
    pg,errs=page(b,CU,'customer',mobile=False);E=pg.evaluate
    E("()=>{S.cart={i2:2};S.cartStore=STORES[0].n;go('pay')}");pg.wait_for_timeout(1200)
    E(CTL,['placeOrder'])
    hb=pg.locator('#hbtn');ok(hb.count()==1 and 'Удерживайте' in hb.inner_text() and 'TJS' in hb.inner_text(),'pay: the order button says «hold» and shows the total «%s»'%(hb.inner_text() if hb.count() else ''))
    box=hb.bounding_box();cx,cy=box['x']+box['width']/2,box['y']+box['height']/2
    pg.mouse.click(cx,cy);pg.wait_for_timeout(200)
    ok(E("()=>__calls.placeOrder")==0 and 'удерживайте' in pg.inner_text('#hmsg').lower(),'pay: a normal tap does NOT order (hint shown)')
    pg.mouse.move(cx,cy);pg.mouse.down();pg.wait_for_timeout(800);pg.mouse.up();pg.wait_for_timeout(300)
    ok(E("()=>__calls.placeOrder")==0 and 'раньше' in pg.inner_text('#hmsg'),'pay: released after 0.8 s → no order, «released too early»')
    pg.mouse.move(cx,cy);pg.mouse.down();pg.wait_for_timeout(1000)
    w=E("()=>parseFloat(document.querySelector('#hbtn .hp').style.width)||0")
    pg.wait_for_timeout(1300);pg.mouse.up();pg.wait_for_timeout(600)
    ok(40<=w<=70,'pay: progress shown while holding (%.0f %% at 1 s)'%w)
    ok(E("()=>__calls.placeOrder")==1,'pay: held 2 s → exactly ONE order request (%d)'%E("()=>__calls.placeOrder"))
    key1=E("()=>__q.placeOrder[0].a[0].key")
    ok(E("()=>S.busy")==True and pg.locator('#hbtn').is_disabled(),'pay: busy while the server answers (button disabled)')
    pg.mouse.move(cx,cy);pg.mouse.down();pg.wait_for_timeout(2300);pg.mouse.up();pg.wait_for_timeout(200)
    ok(E("()=>__calls.placeOrder")==1,'pay: holding again while busy → still one request')
    E("()=>__q.placeOrder[0].res({error:'generic'})");pg.wait_for_timeout(400)
    pg.mouse.move(cx,cy);pg.mouse.down();pg.wait_for_timeout(2300);pg.mouse.up();pg.wait_for_timeout(400)
    ok(E("()=>__calls.placeOrder")==2 and E("()=>__q.placeOrder[1].a[0].key")==key1,'pay: after a failure the retry keeps the SAME one-time order key')
    E("()=>__q.placeOrder[1].res({error:'generic'})");pg.wait_for_timeout(400)
    # the amount changes while holding
    pg.mouse.move(cx,cy);pg.mouse.down();pg.wait_for_timeout(600);E("()=>{S.cart.i2=3}");pg.wait_for_timeout(300);pg.mouse.up();pg.wait_for_timeout(300)
    t=pg.inner_text('#hmsg') if pg.locator('#hmsg').count() else ''
    ok(E("()=>__calls.placeOrder")==2 and 'Сумма изменилась' in t and '→' in t,'pay: cart / amount changed while holding → cancelled, new total must be confirmed «%s»'%t[:70])
    # touch cancelled / page hidden / page left
    pg.mouse.move(cx,cy);pg.mouse.down();pg.wait_for_timeout(500);E("()=>document.dispatchEvent(new PointerEvent('pointercancel',{bubbles:true}))");pg.wait_for_timeout(2000);pg.mouse.up()
    ok(E("()=>__calls.placeOrder")==2,'pay: touch cancelled by the system → no order')
    pg.mouse.move(cx,cy);pg.mouse.down();pg.wait_for_timeout(500)
    E("()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))}");pg.wait_for_timeout(2000);pg.mouse.up()
    E("()=>{delete document.hidden}");pg.wait_for_timeout(100)
    ok(E("()=>__calls.placeOrder")==2,'pay: app went to the background while holding → no order')
    pg.mouse.move(cx,cy);pg.mouse.down();pg.wait_for_timeout(500);E("()=>go('cart')");pg.wait_for_timeout(2000);pg.mouse.up()
    ok(E("()=>__calls.placeOrder")==2,'pay: left the page while holding → no order')
    # keyboard / assistive technology: two steps
    E("()=>go('pay')");pg.wait_for_timeout(500)
    pg.focus('#hbtn');pg.keyboard.press('Enter');pg.wait_for_timeout(300)
    ok(pg.locator('#hcfok').count()==1 and E("()=>document.activeElement.id")=='hcfok' and E("()=>__calls.placeOrder")==2,'keyboard: Enter on the button → step 1 (question with the total), focus on «Подтвердить заказ», nothing sent')
    ok('TJS' in pg.inner_text('#hcfq'),'keyboard: the question shows the total «%s»'%pg.inner_text('#hcfq'))
    pg.keyboard.press('Enter');pg.wait_for_timeout(400)
    ok(E("()=>__calls.placeOrder")==3,'keyboard: step 2 «Подтвердить заказ» → one order request')
    E("()=>__q.placeOrder[2].res({error:'generic'})");pg.wait_for_timeout(400)
    E("()=>holdAsk()");pg.wait_for_timeout(200);E("()=>{S.cart.i2=4}");pg.click('#hcfok');pg.wait_for_timeout(300)
    ok(E("()=>__calls.placeOrder")==3 and 'Сумма изменилась' in pg.inner_text('#hmsg'),'two steps: amount changed between the steps → refused, new total to confirm')
    ok(pg.locator('#hsk').count()==1 and E("()=>{const e=document.getElementById('hsk');return e.getBoundingClientRect().width<=1}"),'the two-step button exists for assistive tech, hidden until focused')
    pg.focus('#hsk');ok(E("()=>document.getElementById('hsk').getBoundingClientRect().width>1"),'… and visible when focused with the keyboard')
    ok(not errs,'pay: no JS errors %s'%errs[:1]);pg.close()
    # ================= courier: delivery guard (UAT004) + chat =================
    pg,errs=page(b,DR,'driver');E=pg.evaluate
    E("()=>{const a=mine();a.status='pickedup';a.arrivedStoreAt=Date.now();a.arrivedCustAt=Date.now();a.payment='card';a.leaveAtDoor=false;render()}");pg.wait_for_timeout(300)
    E(CTL,['deliver']);direct=E("()=>!TLB.isCash(mine())")
    E("()=>{const id=mine().id;deliverClick(id);deliverClick(id);swDo();finish(id,null,null,null)}");pg.wait_for_timeout(300)
    ok(direct and E("()=>__calls.deliver")==1,'courier direct delivery (no modal): 4 attempts at once → ONE request (%d)'%E("()=>__calls.deliver"))
    ok('Подтверждаем' in pg.inner_text('#swp'),'courier: the swipe shows «Подтверждаем доставку…» and cannot be swiped')
    E("()=>__q.deliver[0].res({error:'generic'})");pg.wait_for_timeout(400)
    E("()=>deliverClick(mine().id)");pg.wait_for_timeout(200)
    ok(E("()=>__calls.deliver")==2,'courier: after a failure a new confirmation is possible')
    E("()=>__q.deliver[1].res({data:null})");pg.wait_for_timeout(300)
    # modal path (cash)
    E("()=>{const a=TLB.orders(o=>o.driver==DRV.id&&o.status!='delivered')[0]||mine();}")
    E("()=>{const a=mine();if(a){a.status='pickedup';a.payment='cash';a.arrivedCustAt=Date.now()}render()}");pg.wait_for_timeout(200)
    E(CTL,['deliver']);E("()=>deliverClick(mine().id)");pg.wait_for_timeout(300)
    if pg.locator('#dvok').count():
        pg.click('#dvok');pg.wait_for_timeout(100);pg.locator('#dvok').click(force=True);pg.wait_for_timeout(100)
        ok(E("()=>__calls.deliver")==1 and pg.locator('#dvok').is_disabled() and 'Подтверждаем' in pg.inner_text('#dvok'),'courier modal (cash): two taps on «Подтвердить» → ONE request, button disabled')
        E("()=>{swDo();deliverClick(mine().id)}");pg.wait_for_timeout(100);ok(E("()=>__calls.deliver")==1,'courier: swipe / direct path while the modal confirmation runs → still one')
        E("()=>__q.deliver[0].res({data:null})");pg.wait_for_timeout(300)
    else: ok(False,'courier modal not shown')
    # chat
    E("()=>{DV=null;const a=mine()||TLB.orders(o=>o.driver==DRV.id)[0];a.status='pickedup';chatOpen=true;render()}");pg.wait_for_timeout(300)
    E(CTL,['chat'])
    if pg.locator('#ci').count():
        pg.fill('#ci','Я у двери');pg.click('#cisend');pg.wait_for_timeout(100);pg.locator('#cisend').click(force=True);pg.wait_for_timeout(100)
        ok(E("()=>__calls.chat")==1 and pg.input_value('#ci')=='Я у двери','courier chat: two taps → one send, text kept while sending')
        pg.locator('.qrow .chip').first.click();pg.wait_for_timeout(100);ok(E("()=>__calls.chat")==1,'courier chat: a quick reply while sending is not sent twice over it')
        E("()=>__q.chat[0].res({error:'generic'})");pg.wait_for_timeout(200)
        ok(pg.input_value('#ci')=='Я у двери' and pg.locator('#cierr').count()==1,'courier chat failed: text kept, message shown')
        pg.click('#cisend');pg.wait_for_timeout(100);E("()=>__q.chat[1].res({ok:true})");pg.wait_for_timeout(200)
        ok(pg.input_value('#ci')=='','courier chat: cleared only after the server confirmed')
    else: ok(False,'courier chat input not found')
    ok(not errs,'courier: no JS errors %s'%errs[:1]);pg.close()
    b.close()
print('UAT2 PASS',n-len(fails),'FAILS',len(fails));sys.exit(1 if fails else 0)
