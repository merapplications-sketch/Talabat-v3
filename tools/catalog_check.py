"""Catalog path end to end (v81): admin and restaurant save, the customer sees it.

Same shared in-memory database as flow_check (no real Supabase, no RLS / triggers / storage policies — those are checked on
the live database separately with sql/verify_catalog_readonly.sql). Every step uses the handler the real button calls, and
real file inputs for the photos.

  admin:  new store (form) -> edit: cover + logo photos, address -> owner linked to the restaurant account
          -> top banner with photo + bottom banner (form) -> banner edit (title, active)
  restaurant: new dish with photo, section, price -> sizes group (required, 1 of 3, prices) -> extras group (max 2, 2 extras)
  admin:  sees the non-pharmacy dish already approved (live default; pharmacy still requires approval)
  customer: store in the list with its photos, dish with photo in the menu, the sheet shows sizes / extras with prices,
          required size enforced, line price = dish + size + extras, both banners on Home.
DB defaults the mock applies on insert are the ones the live check must confirm (DEFAULTS below).
  python3 tools/catalog_check.py"""
import os,sys,json,re
here=os.path.dirname(os.path.abspath(__file__))
SRC=open(os.path.join(here,'flow_check.py')).read()
exec(compile(SRC.split('shots=[]')[0],os.path.join(here,'flow_check.py'),'exec'))
from PIL import Image
DEFAULTS={'stores':{'is_active':True,'is_open':True},'menu_items':{'available':True,'approved':True},
          'item_option_groups':{'sort':0},'item_options':{'available':True,'sort':0},'banners':{'is_active':True}}
_ins=DB.handle
def handle(s,q):
    if q.get('kind')=='from' and q.get('op') in ('insert','upsert') and q['name'] in DEFAULTS:
        p=q['payload'];p=p if isinstance(p,list) else [p]
        s.seq+=1
        q=dict(q,payload=[dict(DEFAULTS[q['name']],**dict({'id':uu(900000+s.seq*10+k)},**x)) for k,x in enumerate(p)])   # uuid ids like the live tables
    if q.get('kind')=='rpc' and q['name']=='assign_owner':
        a=q.get('args') or {};st=next(x for x in s.T['stores'] if str(x['id'])==str(a.get('p_store')))
        pr=next((x for x in s.T['profiles'] if x['email']==a.get('p_email')),None)
        if not pr: return {'__err':'not_found'}
        st['owner_id']=pr['id'];pr['role']='merchant';return None
    return _ins(s,q)
DB.handle=handle
MOCK2=MOCK.replace("storage:{from:function(){return {upload:function(){return Promise.resolve({})},getPublicUrl:function(){return {data:{publicUrl:''}}}}}}",
  "storage:{from:function(b){return {upload:function(p){window.__up=(window.__up||[]).concat([b+'/'+p]);return Promise.resolve({data:{path:p},error:null})},getPublicUrl:function(p){return {data:{publicUrl:'file://'+window.__IMGDIR+'/dish.jpg?u='+b+'/'+p}}}}}}")
assert MOCK2!=MOCK,'storage mock not patched'
IMG=os.path.join(os.path.abspath(OUT),'catalog_img');os.makedirs(IMG,exist_ok=True)
pics={}
for k,c in (('cover',(200,90,40)),('logo',(240,120,30)),('dish',(120,160,60)),('banner',(60,90,170)),('banner2',(170,60,90))):
    pics[k]=os.path.join(IMG,k+'.jpg');Image.new('RGB',(900,600),c).save(pics[k],quality=80)
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();tmp=b.new_page();db=DB(base_tables(tmp));tmp.close();P={};ERR={};DLG=[]
    db.T.setdefault('banners',[])
    def open_app(role):
        ctx=b.new_context(viewport={'width':W,'height':844});pg=ctx.new_page();ERR[role]=[]
        ctx.expose_function('__db',db.handle)
        pg.add_init_script("window.__ROLE=%s;window.__UID=%s;window.__IMGDIR=%s"%(json.dumps(role),json.dumps(U[role]),json.dumps(IMG)))
        pg.on('pageerror',lambda e,r=role:ERR[r].append(str(e)));pg.on('dialog',lambda d:(DLG.append(d.message),d.accept()))
        pg.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=MOCK2) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
        pg.goto('file://'+root+'/'+role+'.html',wait_until='domcontentloaded');pg.wait_for_timeout(1800);P[role]=pg;return pg
    def sync(*roles):
        for r in roles: P[r].evaluate("()=>TLB.reload&&TLB.reload()");P[r].wait_for_timeout(400);P[r].evaluate("()=>{try{render()}catch(e){}}")
    a=open_app('admin');m=open_app('merchant');c=open_app('customer')
    for pg in (a,m,c): pg.evaluate("()=>TLB.setLang&&TLB.setLang('ru')")
    # ---- admin: new store ----
    a.evaluate("()=>{tab='s';showAddS=true;render()}")
    a.fill('#sn','Тест Плов-Хаус');a.fill('#ss','Плов и самса');a.fill('#sp','+992 90 123 45 67');a.select_option('#sc','rest')
    a.evaluate("()=>{const s=$('sf');s.value=[...s.options].some(o=>o.value=='fixed')?'fixed':s.options[0].value}");a.fill('#sb','8')
    a.evaluate("()=>addStore()");a.wait_for_timeout(600)
    st=next((x for x in db.T['stores'] if x.get('name')=='Тест Плов-Хаус'),None)
    ok(st is not None,'admin: new store saved (%s)'%({k:st.get(k) for k in ('category','phone','fee_type','fee_base','commission_pct')} if st else DLG[-1:]))
    sid=st and st['id']
    # ---- admin: edit — cover, logo, address ----
    a.evaluate("(i)=>{openStoreEdit(i)}",sid);a.wait_for_timeout(300)
    a.set_input_files('input[onchange="edCover(event)"]',pics['cover']);a.set_input_files('input[onchange="edLogo(event)"]',pics['logo']);a.wait_for_timeout(1500)
    a.evaluate("()=>{ED.address='ул. Рудаки 10, Душанбе';ED.lat=38.57;ED.lng=68.79}");a.evaluate("()=>saveStore()");a.wait_for_timeout(700)
    st=next(x for x in db.T['stores'] if x['id']==sid)
    ok(bool(st.get('cover_url')) and bool(st.get('logo_url')),'admin: cover and logo photos saved to the store (%s / %s)'%(str(st.get('cover_url'))[-40:],str(st.get('logo_url'))[-40:]))
    ok(all(u.startswith('media/') for u in a.evaluate("()=>window.__up||[]")) and len(a.evaluate("()=>window.__up||[]"))>=2,'admin: photos go to the storage bucket «media» (not inline)')
    # ---- admin: link the restaurant account ----
    a.evaluate("(i)=>{openStoreEdit(i)}",sid);a.wait_for_timeout(300)
    a.evaluate("()=>{ED.owner='merchant@test.com'}");a.evaluate("()=>edOwner()");a.wait_for_timeout(700)
    st=next(x for x in db.T['stores'] if x['id']==sid)
    ok(st.get('owner_id')==U['merchant'],'admin: store linked to the restaurant account (assign_owner)')
    a.evaluate("()=>{E=null;render()}")
    # ---- admin: banners ----
    a.evaluate("()=>{tab='b';showAddB=true;render()}");a.fill('#bt','Тест: плов −10%')
    a.set_input_files('input[onchange="pickB(event)"]',pics['banner']);a.wait_for_timeout(1200)
    a.evaluate("(i)=>{BL='store:'+i}",sid);a.evaluate("()=>addBanner()");a.wait_for_timeout(600)
    a.evaluate("()=>{showAddB=true;render()}");a.fill('#bt','Тест партнёр');a.select_option('#bpl','bottom')
    a.set_input_files('input[onchange="pickB(event)"]',pics['banner2']);a.wait_for_timeout(1200);a.evaluate("()=>addBanner()");a.wait_for_timeout(600)
    bn=[x for x in db.T['banners'] if str(x.get('title','')).startswith('Тест')]
    ok(len(bn)==2 and all(x.get('image_url') for x in bn),'admin: 2 banners saved with photos (%s)'%[(x.get('title'),x.get('placement'),x.get('link_type'),x.get('link_value')) for x in bn])
    top=next((x for x in bn if x.get('placement')=='top'),{})
    ok(top.get('link_type')=='store' and str(top.get('link_value'))==str(sid),'admin: top banner opens the new store')
    sync('admin');a.evaluate("(i)=>openBE(i)",top.get('id'));a.wait_for_timeout(200)
    a.evaluate("()=>{BD.title='Тест: плов −15%'}");a.evaluate("()=>bannerSave()");a.wait_for_timeout(600)
    top=next((x for x in db.T['banners'] if x.get('id')==top.get('id')),{})
    ok(top.get('title')=='Тест: плов −15%' and top.get('is_active') is True and top.get('image_url'),'admin: banner edit saved (title, still active, photo kept)')
    # ---- restaurant: dish, photo, sizes, extras ----
    sync('merchant');m.evaluate("()=>{setStore('Тест Плов-Хаус')}");m.wait_for_timeout(300)
    ok(m.evaluate("()=>TLB.myStores().some(s=>s.name=='Тест Плов-Хаус')"),'restaurant: the linked store is in its list')
    m.evaluate("()=>{tab='m';render();openSheet()}") if m.evaluate("()=>typeof tab!=='undefined'") else m.evaluate("()=>openSheet()")
    m.wait_for_timeout(200);m.evaluate("()=>{SH.name='Плов чайханский';SH.price='35';SH.section='Плов'}")
    m.set_input_files('input[onchange="shPick(event)"]',pics['dish']);m.wait_for_timeout(1200)
    m.evaluate("()=>saveSheet()");m.wait_for_timeout(700)
    it=next((x for x in db.T['menu_items'] if x.get('name')=='Плов чайханский'),None)
    ok(it is not None and it.get('image_url') and it.get('store_id')==sid and float(it.get('price'))==35 and it.get('section')=='Плов','restaurant: dish saved with photo, price and section (%s)'%({k:(it or {}).get(k) for k in ('price','section','approved','available')}))
    iid=it and it['id']
    sync('merchant');m.evaluate("(i)=>openSheet(i)",iid);m.wait_for_timeout(200)
    m.evaluate("()=>addG()");m.wait_for_timeout(500);sync('merchant');m.evaluate("(i)=>openSheet(i)",iid)
    g1=m.evaluate("(i)=>TLB.optionsOf(i,true)[0].id",iid)
    m.evaluate("(g)=>updG(g,{name:'Размер',required:true,max:1})",g1);m.wait_for_timeout(400)
    for n,pr in (('Обычный',0),('Большой',8),('Семейный',20)):
        m.evaluate("(g)=>addO(g)",g1);m.wait_for_timeout(400);sync('merchant')
        oid=m.evaluate("(g)=>{const x=TLB.optionsOf(%s,true).find(x=>x.id==g).options;return x[x.length-1].id}"%json.dumps(iid),g1)
        m.evaluate("([o,n,p])=>updO(o,{name:n,price:p})",[oid,n,str(pr)]);m.wait_for_timeout(300)
    m.evaluate("()=>addG()");m.wait_for_timeout(500);sync('merchant');m.evaluate("(i)=>openSheet(i)",iid)
    g2=m.evaluate("(i)=>TLB.optionsOf(i,true).find(g=>g.name!='Размер').id",iid)
    m.evaluate("(g)=>updG(g,{name:'Добавки',required:false,max:'2'})",g2);m.wait_for_timeout(400)
    for n,pr in (('Казы',12),('Перепелиное яйцо',5)):
        m.evaluate("(g)=>addO(g)",g2);m.wait_for_timeout(400);sync('merchant')
        oid=m.evaluate("(g)=>{const x=TLB.optionsOf(%s,true).find(x=>x.id==g).options;return x[x.length-1].id}"%json.dumps(iid),g2)
        m.evaluate("([o,n,p])=>updO(o,{name:n,price:p})",[oid,n,str(pr)]);m.wait_for_timeout(300)
    gs=[x for x in db.T['item_option_groups'] if x.get('item_id')==iid];os_=[x for x in db.T['item_options'] if x.get('group_id') in [g['id'] for g in gs]]
    ok(sorted((g['name'],bool(g['required']),int(g['max_sel'])) for g in gs)==[('Добавки',False,2),('Размер',True,1)],'restaurant: sizes (required, 1) and extras (max 2) groups saved %s'%[(g['name'],g.get('required'),g.get('max_sel')) for g in gs])
    ok(sorted((o['name'],float(o['price_delta'])) for o in os_)==sorted([('Обычный',0.0),('Большой',8.0),('Семейный',20.0),('Казы',12.0),('Перепелиное яйцо',5.0)]),'restaurant: 5 options saved with their prices')
    # Live read-only inspection 2026-10-24: default true; item_approval forces false for pharmacy only.
    sync('admin');ok(not a.evaluate("(i)=>TLB.pendingItems().some(x=>x.id==i)",iid),'admin: a restaurant dish follows the existing approved=true default')
    ok(next(x for x in db.T['menu_items'] if x['id']==iid).get('approved') is True,'restaurant dish is approved; no approval-policy changes')
    # ---- customer ----
    sync('customer');c.evaluate("()=>{S.q='';go('home')}");c.wait_for_timeout(500)
    r=c.evaluate("""(sid)=>{const s=ALLS.find(x=>x.id==sid);const bt=TLB.banners().map(b=>b.title);
      const html=document.getElementById('app').innerHTML;return {store:!!s,cover:s&&s.i,logo:s&&s.lg,banners:bt,inPage:html.includes('Тест: плов −15%')||html.includes('?u=media/'),bottom:[...document.querySelectorAll('#app .bb')].some(e=>(e.getAttribute('onclick')||'').includes(String(TLB.banners().find(b=>b.title=='Тест партнёр').id)))}}""",sid)
    ok(r['store'] and r['cover'] and r['logo'],'customer: the new store is listed with its cover and logo')
    ok('Тест: плов −15%' in r['banners'] and 'Тест партнёр' in r['banners'],'customer: both active banners are loaded %s'%r['banners'])
    ok(r['inPage'],'customer Home: the top admin banner is shown (bento)')
    ok(r['bottom'],'customer Home: the bottom partner banner is shown')
    c.evaluate("(sid)=>{const s=ALLS.find(x=>x.id==sid);go('menu',{store:s.n})}",sid);c.wait_for_timeout(500)
    r=c.evaluate("""(i)=>{const it=menuOf(S.store).find(x=>x.id==i);const img=[...document.querySelectorAll('#app img')].some(e=>(e.getAttribute('src')||'').includes('?u=media/'));return {it:!!it,img:it&&it.image,has:it&&it.hasOpts,shown:document.body.innerText.includes('Плов чайханский'),imgs:img}}""",iid)
    ok(r['it'] and r['shown'],'customer: the approved dish is in the store menu')
    ok(bool(r['img']) and r['imgs'],'customer: the dish photo is shown')
    c.evaluate("(i)=>openItem(i)",iid);c.wait_for_timeout(400)
    txt=c.evaluate("()=>document.body.innerText")
    ok(all(x in txt for x in ('Размер','Обычный','Большой','Семейный','Добавки','Казы','Перепелиное яйцо')),'customer sheet: sizes and extras shown')
    ok('+8' in txt and '+20' in txt and '+12' in txt,'customer sheet: option prices shown')
    n0=c.evaluate("()=>cartCount()");c.evaluate("()=>shAdd()");c.wait_for_timeout(300)
    ok(c.evaluate("()=>cartCount()")==n0,'customer: the required size must be chosen first')
    gsc=c.evaluate("(i)=>TLB.optionsOf(i)",iid);gS=[g for g in gsc if g['name']=='Размер'][0];gA=[g for g in gsc if g['name']=='Добавки'][0]
    big=[o for o in gS['options'] if o['name']=='Большой'][0]['id'];kz=[o for o in gA['options'] if o['name']=='Казы'][0]['id'];eg=[o for o in gA['options'] if o['name']=='Перепелиное яйцо'][0]['id']
    c.evaluate("([g,o])=>shPick(g,o,1)",[gS['id'],big]);c.evaluate("([g,o])=>shPick(g,o,2)",[gA['id'],kz]);c.evaluate("([g,o])=>shPick(g,o,2)",[gA['id'],eg]);c.wait_for_timeout(200)
    c.evaluate("()=>shAdd()");c.wait_for_timeout(400)
    ok(c.evaluate("()=>cartCount()")==n0+1,'customer: dish with size + 2 extras added')
    tot=c.evaluate("()=>{const k=Object.keys(S.cart)[0];return typeof lineTotal=='function'?lineTotal(k):null}")
    c.evaluate("()=>go('cart')");c.wait_for_timeout(300)
    ok('60' in c.evaluate("()=>document.getElementById('app').innerText"),'customer cart: line price = 35 + 8 + 12 + 5 = 60 TJS')
    for r_,e in ERR.items(): ok(not e,'%s: no JS errors %s'%(r_,e[:2]))
    b.close()
print('\nCATALOG CHECK %s'%('FAILS %d'%len(fails) if fails else 'OK'));sys.exit(1 if fails else 0)
