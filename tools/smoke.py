import sys,json
from playwright.sync_api import sync_playwright
MOCK="""
(function(){
 var role=window.__ROLE;
 var user={id:'00000000-0000-0000-0000-000000000001',email:role+'@test.com'};
 function res(d){return {data:d,error:null}}
 function chain(kind,name){
  var single=false;
  var c=new Proxy(function(){}, {
   get:function(t,p){
    if(p==='then'){return function(ok,bad){var d=[];
       if(kind==='from'&&name==='profiles'&&single)d={id:user.id,email:user.email,role:role,name:'Test '+role,phone:'+992900000000',driver_status:'approved'};
       else if(kind==='rpc'){d=null}
       return Promise.resolve(res(d)).then(ok,bad)}}
    if(p==='single'||p==='maybeSingle'){single=true;return function(){return c}}
    return function(){return c}
   }});
  return c}
 window.supabase={createClient:function(){return {
   auth:{getSession:function(){return Promise.resolve({data:{session:{user:user,access_token:'x'}},error:null})},
         signOut:function(){return Promise.resolve({})},signInWithPassword:function(){return Promise.resolve({error:{message:'x'}})},
         onAuthStateChange:function(){return {data:{subscription:{unsubscribe:function(){}}}}}},
   from:function(n){return chain('from',n)},rpc:function(n){return chain('rpc',n)},
   channel:function(){var ch={on:function(){return ch},subscribe:function(){return ch},unsubscribe:function(){}};return ch},
   removeChannel:function(){},storage:{from:function(){return {upload:function(){return Promise.resolve({})},getPublicUrl:function(){return {data:{publicUrl:''}}}}}}};}};
})();
"""
pages=[('admin','admin'),('merchant','merchant'),('driver','driver'),('customer','customer')]
with sync_playwright() as p:
    b=p.chromium.launch();bad=0
    for name,role in pages:
        pg=b.new_page(viewport={'width':390,'height':800});errs=[]
        pg.on('pageerror',lambda e,errs=errs:errs.append(str(e)))
        pg.on('console',lambda m,errs=errs:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'net::' not in m.text else None)
        pg.route('**/*',lambda r:(r.fulfill(status=200,content_type='application/javascript',body=MOCK.replace('window.__ROLE','"'+role+'"')) if 'supabase-js' in r.request.url else (r.abort() if r.request.url.startswith('http') else r.continue_())))
        pg.goto('file://'+__import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..',name+'.html')));pg.wait_for_timeout(2500)
        import re
        seen=set()
        def scan(tag):
            t=pg.evaluate("document.body.innerText")
            for w in re.findall(r"[A-Za-z_]\w*",t):
                if re.fullmatch(r"[a-z]{1,6}[A-Z][A-Za-z]{1,12}",w) and w not in ('iPhone',): seen.add((tag,w))
            for bad_ in ('undefined','NaN','[object','null'):
                if bad_ in t: seen.add((tag,bad_))
        scan('home')
        sel={'admin':'.tabs button','merchant':'.tabs button','driver':'.nav div','customer':'.nav *[onclick]'}[name]
        n=pg.locator(sel).count()
        for i in range(n):
            try:
                pg.locator(sel).nth(i).click(timeout=1500);pg.wait_for_timeout(300);scan('tab%d'%i)
            except Exception as e: pass
        print(name,'tabs',n,'suspicious',sorted(seen)[:12])
        txt=pg.evaluate("document.body.innerText.length")
        print(name,'textlen',txt,'errors',errs[:4]);bad+=len(errs)
        pg.screenshot(path='/tmp/smoke_%s.png'%name)
    b.close();print('TOTAL ERR',bad)
