"""Admin sign-in path (v81), mocked Supabase auth (no real accounts, no passwords of real people).

  no session -> sign-in screen (no sign-up tab for admin) -> bad email / wrong password messages -> 5 failures lock
  -> correct admin signs in -> admin panel with all sections -> sign out -> session per app (admin session does not
  sign in the customer app) -> a customer account in the admin app is refused with a button to its own app
  -> a staff account with server permissions (my_perms) gets only its sections.
  python3 tools/admin_login_check.py"""
import os,sys,json
here=os.path.dirname(os.path.abspath(__file__))
SRC=open(os.path.join(here,'flow_check.py')).read()
exec(compile(SRC.split('shots=[]')[0],os.path.join(here,'flow_check.py'),'exec'))
ACC={'admin@test.com':('Adm1n-test-pass',U['admin']),'customer@test.com':('Cust0mer-pass',U['customer']),'staff@test.com':('Staff-pass-01','c0000000-0000-4000-8000-000000000009')}
PERMS={'c0000000-0000-4000-8000-000000000009':['orders','support']}
AUTH="""(function(){var KEY='tlb-mock-session-'+location.pathname;
 function cur(){try{return JSON.parse(localStorage.getItem(window.__SK||'x'))}catch(e){return null}}
 window.__mockAuth={signIn:function(e,p){return window.__auth(e,p)}};
})();"""
MOCKA=MOCK.replace("auth:{getSession:function(){return Promise.resolve({data:{session:{user:user,access_token:'x'}},error:null})},signOut:function(){return Promise.resolve({})},signInWithPassword:function(){return Promise.resolve({error:{message:'x'}})}",
 "auth:{getSession:function(){var s=null;try{s=JSON.parse(localStorage.getItem('mock-sess-'+(arguments[0]||window.__APPROLE)))}catch(e){}if(s){uid=s.id;user=s}return Promise.resolve({data:{session:s?{user:s,access_token:'x'}:null},error:null})},"
 "signOut:function(){localStorage.removeItem('mock-sess-'+window.__APPROLE);return Promise.resolve({error:null})},"
 "signInWithPassword:function(c){return window.__auth(c.email,c.password).then(function(r){if(r.error)return {data:{user:null,session:null},error:{message:r.error,status:400}};user={id:r.id,email:c.email};uid=r.id;localStorage.setItem('mock-sess-'+window.__APPROLE,JSON.stringify(user));return {data:{user:user,session:{user:user,access_token:'x'}},error:null}})}")
assert MOCKA!=MOCK
# the mock chain reads uid/role from closure variables: make them assignable
MOCKA=MOCKA.replace("var role=window.__ROLE,uid=window.__UID,user={id:uid,email:role+'@test.com'};","var role=window.__ROLE,uid=null,user=null;")
assert 'uid=null' in MOCKA
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();tmp=b.new_page();T=base_tables(tmp);tmp.close()
    T['profiles'].append({'id':'c0000000-0000-4000-8000-000000000009','email':'staff@test.com','role':'customer','name':'Оператор','phone':'+992900000009','created_at':now()})
    db=DB(T);_h=DB.handle
    def handle(s,q):
        if q.get('kind')=='rpc' and q['name']=='my_perms': return PERMS.get(q['uid'],[])
        return _h(s,q)
    def auth(e,pw):
        a=ACC.get(str(e).lower())
        return {'id':a[1]} if a and a[0]==pw else {'error':'Invalid login credentials'}
    ctx=b.new_context(viewport={'width':390,'height':844});ERR=[];DLG=[]
    ctx.expose_function('__db',lambda q:handle(db,q));ctx.expose_function('__auth',auth)
    ctx.add_init_script("window.__APPROLE=location.pathname.split('/').pop().replace('.html','')")
    ctx.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=MOCKA) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
    pg=ctx.new_page();pg.on('pageerror',lambda e:ERR.append(str(e)));pg.on('dialog',lambda d:(DLG.append(d.message),d.accept()))
    def go(app): pg.goto('file://'+root+'/'+app+'.html',wait_until='domcontentloaded');pg.wait_for_timeout(1800)
    go('admin')
    ok(pg.locator('#tlb-em').count()==1 and pg.locator('#tlb-pw').count()==1,'admin: no session -> sign-in screen')
    ok(pg.locator('#tlb-t-up').count()==0 and pg.locator('#tlb-nm').count()==0,'admin: no sign-up on the admin sign-in')
    def login(e,pw):
        pg.fill('#tlb-em',e);pg.fill('#tlb-pw',pw);pg.click('#tlb-go');pg.wait_for_timeout(1200)
    err=lambda:pg.evaluate("()=>{const e=document.getElementById('tlb-er');return e?e.textContent:''}")
    login('admin@','x');ok(bool(err()),'admin: bad email refused before sending (%s)'%err())
    login('admin@test.com','wrong-pass');ok(bool(err()) and pg.locator('#tlb-em').count()==1,'admin: wrong password -> message, stays on sign-in (%s)'%err())
    login('admin@test.com','Adm1n-test-pass');pg.wait_for_timeout(1500)
    ok(pg.locator('#tlb-ov').count()==0 and pg.evaluate("()=>typeof TLB!='undefined'&&!!TLB.me()&&TLB.me().email=='admin@test.com'&&typeof vStores=='function'&&!!document.querySelector('.tabs')"),'admin: correct admin password -> admin panel')
    tabs=pg.evaluate("()=>TABS.filter(x=>tabOk(x[0])).map(x=>x[0])")
    ok(len(tabs)>=10,'admin: all sections available to the admin (%s)'%','.join(tabs))
    go('admin');ok(pg.locator('#tlb-ov').count()==0 and pg.evaluate("()=>!!TLB.me()"),'admin: session kept after reload')
    go('customer');ok(pg.locator('#tlb-em').count()==1 or pg.evaluate("()=>!TLB.me()||TLB.me().role!='admin'"),'customer app: the admin session does not sign in the customer app (own session per app)')
    go('admin');pg.evaluate("()=>{const b=document.getElementById('tlb-out');if(b)b.click();else TLB.logout&&TLB.logout()}");pg.wait_for_timeout(1500)
    go('admin');ok(pg.locator('#tlb-em').count()==1,'admin: sign out -> sign-in screen again')
    login('customer@test.com','Cust0mer-pass')
    ok(pg.locator('#tlb-go-app').count()==1 and 'customer.html' in (pg.get_attribute('#tlb-go-app','href') or ''),'admin: a customer account is refused, with a button to the customer app')
    pg.evaluate("()=>document.getElementById('tlb-lo').click()");pg.wait_for_timeout(1500);go('admin')
    login('staff@test.com','Staff-pass-01')
    tabs=pg.evaluate("()=>typeof TABS=='undefined'?null:TABS.filter(x=>tabOk(x[0])).map(x=>x[0])")
    ok(pg.locator('#tlb-ov').count()==0 and tabs is not None and 0<len(tabs)<10,'admin: staff account (my_perms orders, support) gets only its sections (%s)'%tabs)
    pg.evaluate("()=>{const b=document.getElementById('tlb-out');if(b)b.click();else TLB.logout&&TLB.logout()}");pg.wait_for_timeout(1200);go('admin')
    for i in range(6): login('admin@test.com','bad-%d'%i)
    ok('30' in err() or 'Подожд' in err() or 'Wait' in err() or 'сек' in err(),'admin: 5 wrong passwords -> short lock (%s)'%err())
    ok(not ERR,'no JS errors %s'%ERR[:2])
    b.close()
print('\nADMIN LOGIN CHECK %s'%('FAILS %d'%len(fails) if fails else 'OK'));sys.exit(1 if fails else 0)
