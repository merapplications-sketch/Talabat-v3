"""T4 (v82): driver logic carried over from v58 / v56 onto driver A — mock only (shared in-memory DB of flow_check, Chromium).
  one delivery confirmation at a time (modal, direct, repeated taps), failure frees it again; driver A chat: a quick reply
  does not overwrite or clear the typed draft, a late success never clears newer typing; OSM tiles send the site origin.
  python3 tools/driver_t4_check.py"""
import os,sys,json
here=os.path.dirname(os.path.abspath(__file__))
SRC=open(os.path.join(here,'flow_check.py')).read()
exec(compile(SRC.split('shots=[]')[0],os.path.join(here,'flow_check.py'),'exec'))
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();tmp=b.new_page();T=base_tables(tmp);tmp.close()
    st=T['stores'][0]
    def mk(oid,pay,door):
        return {'id':oid,'store_id':st['id'],'customer_id':U['customer'],'driver_id':U['driver'],'driver_name':'Фаррух','status':'pickedup','subtotal':100,'discount':0,'promo_discount':0,
          'delivery_fee':10,'driver_payout':15,'tip':0,'total':110,'commission':10,'commission_pct':10,'payment':pay,'address':'ул. Рудаки 1','lat':38.56,'lng':68.78,
          'customer_name':'Зарина','created_at':now(),'done_at':None,'wallet_used':0,'arrived_store_at':now(),'arrived_cust_at':now(),'leave_at_door':door,'prep_time':15}
    T['orders']=[mk(5001,'card',False)]
    db=DB(T);calls=[];slow={'fail':False}
    _h=DB.handle
    def handle(s,q):
        if q.get('kind')=='rpc' and q['name']=='deliver_order':
            calls.append(q['args'])
            if slow['fail']: return {'__err':'generic'}
        if q.get('kind')=='from' and q['name']=='order_chat' and q.get('op')=='insert':
            calls.append(('chat',q['payload']));return {'__err':'slow'} if slow.get('chatfail') else _h(s,q)
        return _h(s,q)
    ctx=b.new_context(viewport={'width':390,'height':844});ERR=[]
    ctx.expose_function('__db',lambda q:handle(db,q))
    ctx.add_init_script("window.__ROLE='driver';window.__UID=%s"%json.dumps(U['driver']))
    ctx.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=MOCK) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
    pg=ctx.new_page();pg.on('pageerror',lambda e:ERR.append(str(e)));DLG=[];pg.on('dialog',lambda d:(DLG.append(d.message),d.accept()))
    pg.goto('file://'+root+'/driver.html',wait_until='domcontentloaded');pg.wait_for_timeout(2000);E=pg.evaluate
    ok(E("()=>typeof aChatSend=='function'&&!!document.querySelector('link[href*=\"driver-a.css\"]')"),'driver A layer loaded on top of the driver controller')
    # 1) online-paid order: direct path, two taps in the same moment -> one server call
    slow['fail']=True
    E("()=>{deliverClick(5001);deliverClick(5001);deliverClick(5001)}");pg.wait_for_timeout(800)
    n1=len([c for c in calls if isinstance(c,dict)])
    ok(n1==1,'direct path: 3 taps at once -> 1 delivery request (%d)'%n1)
    ok(E("()=>!DLV[5001]") and any(DLG),'failed confirmation frees the action again and shows the error')
    slow['fail']=False;E("()=>{deliverClick(5001)}");pg.wait_for_timeout(800)
    ok(len([c for c in calls if isinstance(c,dict)])==2 and next(o for o in db.T['orders'] if o['id']==5001)['status']=='delivered','retry after the failure delivers once')
    # 2) cash order via the modal: confirm twice -> one call
    db.T['orders'].append(mk(5002,'cash',False));E("()=>TLB.reload()");pg.wait_for_timeout(700)
    E("()=>{deliverClick(5002);DV.amt=String(DV.total)}");before=len([c for c in calls if isinstance(c,dict)])
    E("()=>{confirmDeliver();confirmDeliver();deliverClick(5002)}");pg.wait_for_timeout(800)
    ok(len([c for c in calls if isinstance(c,dict)])-before==1,'modal path: confirm twice + another tap -> 1 delivery request')
    # 3) driver A chat drafts
    E("()=>{ADrafts[5002]='код домофона 45';}")
    E("()=>aChatSend(5002,t('q1t'))");pg.wait_for_timeout(500)
    ok(E("()=>ADrafts[5002]")=='код домофона 45','quick reply: the typed draft is kept')
    slow['chatfail']=True;E("()=>aChatSend(5002)");pg.wait_for_timeout(500)
    ok(E("()=>ADrafts[5002]")=='код домофона 45' and E("()=>!!AChatErrors[5002]"),'failed send: draft kept, error shown')
    slow['chatfail']=False
    r=E("async()=>{const p=aChatSend(5002);ADrafts[5002]='код домофона 45, второй подъезд';await p;return ADrafts[5002]}")
    ok(r=='код домофона 45, второй подъезд','late success does not clear newer typing')
    r=E("async()=>{await aChatSend(5002);return ADrafts[5002]}")
    ok(r=='','success clears the sent draft')
    # 4) OSM tiles send the site origin (the 403 «Access blocked» fix of v56)
    src=open(os.path.join(root,'driver.html')).read()+open(os.path.join(root,'talabat-core.js')).read()
    ok(src.count("tile.openstreetmap.org")==src.count("referrerPolicy")>=3,'every OSM tile layer sends the site origin (referrerPolicy)')
    ok(not ERR,'no JS errors %s'%ERR[:2])
    b.close()
print('\nDRIVER T4 CHECK %s'%('FAILS %d'%len(fails) if fails else 'OK'));sys.exit(1 if fails else 0)
