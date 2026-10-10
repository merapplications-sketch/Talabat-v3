"""Courier app (v52, batch 2): 4 swipe steps, photo proof for "leave at the door", cash breakdown, cancel alarm.
Runs the real driver.html against the mocked Supabase of qa_all.py and records the RPC calls."""
import os,sys,json,base64
from playwright.sync_api import sync_playwright
here=os.path.dirname(os.path.abspath(__file__));root=os.path.abspath(os.path.join(here,'..'))
FIX=open(os.path.join(here,'qa_all.py')).read().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE','"driver"')
SPY="""(function(){var cc=window.supabase.createClient;window.__rpcs=[];window.__up=[];
 window.supabase.createClient=function(){var c=cc.apply(this,arguments),r=c.rpc;c.rpc=function(n,a){window.__rpcs.push([n,a]);if(/^(driver_arrived|deliver_order|set_order_status)$/.test(n))return Promise.resolve({data:null,error:null});return r.call(c,n,a)};
  c.storage={from:function(b){return {upload:function(p){window.__up.push([b,p]);return Promise.resolve({data:{path:p},error:null})},getPublicUrl:function(){return {data:{publicUrl:''}}},createSignedUrl:function(){return Promise.resolve({data:{signedUrl:'x'}})}}}};return c}})();"""
JPG=base64.b64decode('/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=')
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':360,'height':780});errs=[];dlg=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:(dlg.append(d.message),d.accept()))
    pg.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=FIX+SPY) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
    pg.goto('file://'+root+'/driver.html',wait_until='domcontentloaded');pg.wait_for_timeout(2200)
    def swipe(frac=1.0):
        k=pg.locator('#swk').bounding_box();w=pg.locator('#swp').bounding_box()
        pg.mouse.move(k['x']+20,k['y']+20);pg.mouse.down()
        for i in range(1,11): pg.mouse.move(k['x']+20+(w['width']-k['width'])*frac*i/10,k['y']+20)
        pg.mouse.up();pg.wait_for_timeout(500)
    last=lambda:pg.evaluate("()=>window.__rpcs.filter(x=>/^(driver_arrived|deliver_order|set_order_status)$/.test(x[0])).slice(-1)[0]||null")
    pg.evaluate("()=>{mine().arrivedStoreAt=null;render()}")
    ok(pg.evaluate("()=>document.body.classList.contains('mapmode')&&!!document.querySelector('#swk')"),'active order: map mode with a swipe button')
    swipe(0.5);ok(last() is None,'half a swipe does nothing (no accidental step)')
    swipe();ok(last()==['driver_arrived',{'p_id':'ord1','p_where':'store'}],'step 1 swipe → at the restaurant')
    pg.evaluate("()=>{mine().arrivedStoreAt=Date.now();render()}")
    ok(pg.evaluate("()=>!!document.querySelector('.swp.off')&&!document.querySelector('#swk')"),'step 2 locked while the restaurant is still preparing')
    pg.evaluate("()=>{mine().status='ready';render()}");swipe()
    ok(last()[0]=='set_order_status' and last()[1]['p_to']=='pickedup','step 2 swipe (after ready) → picked up')
    pg.evaluate("()=>{mine().status='pickedup';render()}");swipe()
    ok(last()==['driver_arrived',{'p_id':'ord1','p_where':'customer'}],'step 3 swipe → at the customer')
    pg.evaluate("()=>{const a=mine();a.arrivedCustAt=Date.now();a.leaveAtDoor=true;a.payment='cash';a.total=116;a.pointsValue=4;a.walletUsed=10;render()}")
    t=pg.evaluate("()=>document.querySelector('.cashb').innerText")
    ok('106.00' in t and '120.00' in t and '4.00' in t and '10.00' in t,'cash box: take 106 = order 120 − points 4 − wallet 10: '+t.replace('\n',' | '))
    n0=len(pg.evaluate("()=>window.__rpcs"));swipe()
    ok(pg.evaluate("()=>!!DV&&DV.photo&&DV.cash"),'step 4 swipe opens the photo + cash dialog')
    pg.evaluate("()=>confirmDeliver()");pg.wait_for_timeout(200)
    ok(not any(x[0]=='deliver_order' for x in pg.evaluate("()=>window.__rpcs")[n0:]),'no photo → delivery is not sent')
    pg.set_input_files('input[type=file]',files=[{'name':'door.jpg','mimeType':'image/jpeg','buffer':JPG}]);pg.wait_for_timeout(900)
    up=pg.evaluate("()=>window.__up");ok(up and up[-1][0]=='proofs' and up[-1][1].split('/')[1]=='ord1','photo uploaded to the private bucket, folder <courier>/<order>: %s'%(up[-1:] or ''))
    pg.evaluate("()=>{DV.amt='106';confirmDeliver()}");pg.wait_for_timeout(400)
    d=[x for x in pg.evaluate("()=>window.__rpcs") if x[0]=='deliver_order'][-1:]
    ok(d and d[0][1].get('p_photo')==up[-1][1] and d[0][1]['p_cash']==106,'delivered with the photo path and the cash amount: %s'%(d[0][1] if d else None))
    # cancel alarm: the order disappears from the active list as cancelled
    pg.evaluate("()=>{TLB.orders().forEach(o=>{if(o.id!='ord1'&&['preparing','ready','pickedup'].includes(o.status))o.status='delivered'});DV=null;LASTACT=mine().id;const o=mine();o.status='rejected';o.cancelReason='too_busy';render()}")
    ok(pg.evaluate("()=>!!CXL&&document.body.innerText.includes('отменён')||document.body.innerText.includes('cancelled')"),'cancel alarm shown with the reason')
    ok(pg.evaluate("()=>!document.body.classList.contains('mapmode')"),'map closes after the cancel')
    pg.evaluate("()=>{document.querySelector('.cxl .b').click()}");ok(pg.evaluate("()=>CXL===null"),'courier confirms the alarm')
    ok(not errs,'no JS errors '+str(errs[:2]))
    b.close()
print('COURIER FAILS',len(fails));sys.exit(1 if fails else 0)
