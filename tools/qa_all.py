"""Comprehensive visual QA: every screen of the 4 apps, rich fixtures, 360/390/430, online+offline.
Checks per screen: text covered by another element, text-vs-text overlap, horizontal overflow,
raw i18n keys, undefined/NaN/[object, JS errors. Exit code 1 if anything is found."""
import os,json,re,sys
from playwright.sync_api import sync_playwright
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
FIX="""
(function(){
 var role=window.__ROLE,now=Date.now(),iso=function(m){return new Date(now-m*60000).toISOString()};
 var U='00000000-0000-0000-0000-000000000001',user={id:U,email:role+'@test.com'};
 var LONG='Ресторан «Дар-ул-Хилоф Шарқи Бузург» (центральный филиал на проспекте Рудаки)';
 var stores=[
  {id:'s1',free_delivery_min:150,earn_per_tjs:20,name:LONG,category:'rest',description:'Самые вкусные бургеры и шашлык в городе, доставка по всему Душанбе',logo_url:'',cover_url:'',address:'пр. Рудаки 100, Душанбе, Таджикистан',lat:38.56,lng:68.78,fee_type:'fixed',fee_base:10,fee_per_km:2,fee_free_km:3,discount_pct:15,is_open:true,is_active:true,is_featured:true,created_at:iso(100),phone:'+992900000001',free_first_delivery:true,rating:4.6,rating_count:1250,app_rating:4.7,app_rating_count:40,brand_id:'b1',branch_name:'Центр',owner_id:U,commission_pct:10,max_discount_pct:30},
  {id:'s2',name:LONG+' · Сино',category:'rest',description:'Филиал',address:'ул. Сино 5',lat:38.58,lng:68.75,fee_type:'fixed',fee_base:12,discount_pct:0,is_open:false,is_active:true,created_at:iso(90),phone:'+992900000002',rating:0,rating_count:0,brand_id:'b1',branch_name:'Сино',owner_id:U,commission_pct:10},
  {id:'s3',name:'Аптека',category:'pharmacy',description:'',address:'',lat:38.5,lng:68.7,fee_type:'free',fee_base:0,discount_pct:0,is_open:true,is_active:true,created_at:iso(5),phone:'+992900000003',rating:3.9,rating_count:3},
  {id:'s4',name:'Gul',category:'flowers',description:'x',address:'a',lat:38.5,lng:68.7,fee_type:'fixed',fee_base:8,discount_pct:5,is_open:true,is_active:false,created_at:iso(500000),phone:'+992900000004',rating:5,rating_count:900000}];
 var items=[],k=0;['s1','s2','s3'].forEach(function(s){['Бургеры','Напитки','Десерты и сладости для всей семьи','Салаты'].forEach(function(sec,si){for(var j=0;j<4;j++){k++;items.push({id:'i'+k,store_id:s,name:j==0?'Очень длинное название блюда с несколькими ингредиентами и соусом '+k:'Блюдо '+k,price:15+j*7.5,image_url:'',popular:j==1,available:j!=3,approved:true,section:sec,discount_pct:j==2?10:0,created_at:iso(k)})}})});
 var groups=[{id:'g1',item_id:'i1',name:'Размер порции (обязательно выбрать)',required:true,max_sel:1,sort:1,created_at:iso(1)},{id:'g2',item_id:'i1',name:'Добавки',required:false,max_sel:3,sort:2,created_at:iso(1)}];
 var opts=[];['Маленький','Средний','Большой'].forEach(function(n,i){opts.push({id:'o1'+i,group_id:'g1',name:n,price_delta:i*5,available:true,sort:i})});['Сыр','Бекон','Халапеньо','Соус'].forEach(function(n,i){opts.push({id:'o2'+i,group_id:'g2',name:n,price_delta:3,available:true,sort:i})});
 var GRP=window.__GRP={id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',store_id:'s1',host_id:U,is_host:true,host_name:'Зарина',status:'open',expires_at:new Date(now+3*3600e3).toISOString(),order_id:null,items:[{id:1,user_name:'Зарина',mine:true,item_id:'i2',qty:2,options:[],note:null},{id:2,user_name:'Бахромджон Абдулхамидов из отдела продаж',mine:false,item_id:'i1',qty:1,options:['o11','o20'],note:'без лука, пожалуйста, и соус отдельно'},{id:3,user_name:'Мадина',mine:false,item_id:'i3',qty:3,options:[],note:null}]};
 var st=['pending','preparing','ready','pickedup','delivered','cancelled','rejected'];
 var orders=st.map(function(s,i){return {id:'ord'+i,store_id:'s1',customer_id:U,driver_id:U,status:s,subtotal:120+i,discount:10,promo_discount:0,delivery_fee:10,driver_payout:20,tip:5,total:125+i,commission:10,commission_pct:10,payment:i%2?'cash':'wallet',leave_at_door:i==3,is_gift:i==3,substitution:['call','replace','remove'][i%3],address:'ул. Рудаки 100, подъезд 2, этаж 5, кв. 45, Душанбе',lat:38.56,lng:68.78,customer_name:'Муаммад ибни Абдуллоҳ аз Душанбе',scheduled_for:i==0?new Date(now+3*3600e3).toISOString():null,group_id:i==1?'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa':null,fee_waived:i==4?10:0,created_at:iso(30+i*50),done_at:i>3?iso(10+i):null,wallet_used:0}});
 var oitems=[];orders.forEach(function(o,i){oitems.push({id:'oi'+i,order_id:o.id,item_id:'i1',name:'Очень длинное название блюда с несколькими ингредиентами',price:40,qty:2,note:'без лука, пожалуйста, очень острый соус отдельно',options:[{id:'o11',g:'Размер',n:'Средний',p:5}]})});
 var banners=[{id:'bn1',title:'Скидка 20% на всё',image_url:'',placement:'top',link_type:'store',link_value:'s1',active:true,sort:1,created_at:iso(1)},{id:'bn2',title:'Бесплатная доставка',image_url:'',placement:'bottom',active:true,sort:2,created_at:iso(1)}];
 var addrs=[{id:'a1',user_id:U,label:'home',street:'пр. Рудаки',house:'100',entrance:'2',floor:'5',apartment:'45',details:'',note:'домофон не работает',lat:38.56,lng:68.78,is_default:true}];
 var profiles=[{id:U,email:user.email,role:role,name:'Муаммад ибни Абдуллоҳ аз Душанбе',phone:'+992900000000',driver_status:'approved',cash_limit:1000,created_at:iso(1000)},{id:'u2',email:'driver2@test.com',role:'driver',name:'Водитель',phone:'+992900000009',driver_status:'pending',created_at:iso(5)},{id:'u3',email:'c@test.com',role:'customer',name:'Клиент',phone:'+992900000008',created_at:iso(5)}];
 var T={stores:stores,menu_items:items,item_option_groups:groups,item_options:opts,orders:orders,order_items:oitems,banners:banners,addresses:addrs,brands:[{id:'b1',name:'Дар-ул-Хилоф',owner_id:U}],profiles:profiles,
  promo_codes:[{id:'p1',code:'WELCOME10',kind:'percent',value:10,min_order:50,max_uses:100,active:true,created_at:iso(1)}],favorites:[{user_id:U,store_id:'s1'}],wallet_entries:[{id:'w1',user_id:U,amount:50,kind:'refund',note:'Пополнение',created_at:iso(5)}],
  support_tickets:[{id:'t1',user_id:U,subject:'Не приехал заказ',reason:'late',order_id:'ord1',status:'open',created_at:iso(20),updated_at:iso(2)}],ticket_messages:[{id:'tm1',ticket_id:'t1',sender_id:U,body:'Здравствуйте, где мой заказ?',created_at:iso(20)}],
  order_chat:[],order_offers:[],ratings:[],store_requests:[{id:'r1',user_id:U,name:'Новая кофейня',category:'rest',phone:'+992900000005',address:'ул. 1',status:'pending',created_at:iso(3)}],audit_log:[],app_texts:[],app_settings:[{key:'delivery_free_km',value:3},{key:'delivery_step_km',value:0.5},{key:'delivery_step_price',value:2},{key:'delivery_max_km',value:15},{key:'delivery_road_factor',value:1.3},{key:'loyalty_earn_per_tjs',value:10},{key:'loyalty_points_per_tjs',value:1000},{key:'loyalty_min_redeem',value:1000},{key:'loyalty_expiry_days',value:90},{key:'cashback_pct',value:0},{key:'loyalty_voucher_points',value:1000},{key:'loyalty_min_order',value:30},{key:'loyalty_rate_reward',value:10}],order_recipient:[{order_id:'ord3',name:'Мадина Рахимова',phone:'+992901112233'}],happy_hours:[{id:1,title:'Счастливые часы обеда для всех',store_id:null,days:[1,2,3,4,5,6,7],start_time:'00:00:00',end_time:'23:59:00',discount_pct:25,active:true},{id:2,title:'Ночь',store_id:'s1',days:[6,7],start_time:'22:00:00',end_time:'02:00:00',discount_pct:30,active:false}],loyalty_ledger:[{id:1,user_id:U,points:1250,kind:'earn',order_id:'ord4',created_at:iso(60)},{id:2,user_id:U,points:-1000,kind:'spend',order_id:'ord1',created_at:iso(30)}],app_pages:[],order_events:[],client_errors:[],drivers:[]};
 if(window.__EMPTY)Object.keys(T).forEach(function(k){if(k!=='profiles'&&!(role==='merchant'&&(k==='stores'||k==='brands')))T[k]=[]});
 function res(d){return {data:d,error:null}}
 function chain(kind,name){var single=false;
  var c=new Proxy(function(){},{get:function(t,p){
   if(p==='then')return function(ok,bad){var d;
     if(kind==='rpc'){var R={my_perms:null,wallet_balance:50,store_private:stores.map(function(s){return {id:s.id,owner_id:U,commission_pct:10,max_discount_pct:30}}),cash_balances:[],admin_customers:profiles.filter(function(x){return x.role=='customer'}).map(function(x){return Object.assign({orders_count:3,total_spent:250.5},x)}),staff_list:[],my_offers:[],my_rating:null,brand_stats:[{store_id:'s1',name:'x',branch_name:'Центр',orders:12,delivered:10,cancelled:2,revenue:1500.5}],brand_route:[],active_contacts:[],contacts_for:[],delivery_quote:{fee:12,fee_full:12,base:10,extra:2,km:4.2,steps:1,step_km:1,free_km:3,first_free:false},check_promo:null,loyalty_summary:{balance:2850,next_exp_at:new Date(now+86400000*12).toISOString(),next_exp_pts:1250,earn_per_tjs:10,points_per_tjs:100,min_redeem:1000,expiry_days:90,cashback_pct:0,voucher_points:1000,min_order:30,rate_reward:10},best_dishes:[{item_id:'i1',store_id:'s1',cnt:40},{item_id:'i2',store_id:'s1',cnt:22},{item_id:'i33',store_id:'s3',cnt:9}],store_speed:[{store_id:'s1',avg_min:11.5,n:14},{store_id:'s3',avg_min:25,n:6}],group_get:GRP,group_create:GRP,group_add:GRP,group_set:GRP,group_remove:GRP};d=R.hasOwnProperty(name)?R[name]:null}
     else{var rows=T[name]||[];d=single?(name==='profiles'?profiles[0]:rows[0]||null):rows}
     return Promise.resolve(res(d)).then(ok,bad)};
   if(p==='single'||p==='maybeSingle'){single=true;return function(){return c}}
   return function(){return c}}});return c}
 window.supabase={createClient:function(){return {auth:{getSession:function(){return Promise.resolve({data:{session:{user:user,access_token:'x'}},error:null})},signOut:function(){return Promise.resolve({})},signInWithPassword:function(){return Promise.resolve({error:{message:'x'}})},onAuthStateChange:function(){return {data:{subscription:{unsubscribe:function(){}}}}}},
  from:function(n){return chain('from',n)},rpc:function(n){return chain('rpc',n)},channel:function(){var ch={on:function(){return ch},subscribe:function(){return ch},unsubscribe:function(){}};return ch},removeChannel:function(){},storage:{from:function(){return {upload:function(){return Promise.resolve({})},getPublicUrl:function(){return {data:{publicUrl:''}}}}}}};}};
})();
"""
CHECK="""(mode)=>{
 const W=innerWidth,H=innerHeight,out=[];
 const isFix=e=>{for(let x=e;x&&x!==document.documentElement;x=x.parentElement){const p=getComputedStyle(x).position;if(p=='fixed'||p=='sticky')return x}return null};
 const ovs=[...document.querySelectorAll('.ov,.sheet,#tlb-ov')].filter(e=>{const r=e.getBoundingClientRect();return r.width>W*0.8&&r.height>H*0.5&&getComputedStyle(e).position=='fixed'});const modal=ovs.length?ovs[ovs.length-1]:null;
 const tn=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
 while(n=w.nextNode()){const tx=n.nodeValue.trim();if(!tx)continue;const pe=n.parentElement;if(!pe||['SCRIPT','STYLE','OPTION','NOSCRIPT'].includes(pe.tagName))continue;if(modal&&!modal.contains(pe))continue;
  const cs=getComputedStyle(pe);if(cs.visibility=='hidden'||cs.display=='none'||+cs.opacity==0)continue;
  const g=document.createRange();g.selectNodeContents(n);const pr=pe.getBoundingClientRect();
  let clipEl=pe,cl=null;while(clipEl&&clipEl!==document.body){const c=getComputedStyle(clipEl);if(c.overflowX!='visible'||c.overflowY!='visible'){const r=clipEl.getBoundingClientRect();cl=cl?{left:Math.max(cl.left,r.left),right:Math.min(cl.right,r.right),top:Math.max(cl.top,r.top),bottom:Math.min(cl.bottom,r.bottom)}:{left:r.left,right:r.right,top:r.top,bottom:r.bottom}}clipEl=clipEl.parentElement}
  for(const r0 of g.getClientRects()){let r={left:r0.left,right:r0.right,top:r0.top,bottom:r0.bottom};if(cl){r={left:Math.max(r.left,cl.left),right:Math.min(r.right,cl.right),top:Math.max(r.top,cl.top),bottom:Math.min(r.bottom,cl.bottom)}}
   r.width=r.right-r.left;r.height=r.bottom-r.top;let sc=false;for(let q=pe;q&&q!==document.body;q=q.parentElement){const o=getComputedStyle(q).overflowX;if(o=='auto'||o=='scroll'){sc=true;break}}if(!sc&&r.width<2&&r0.width>8&&r.height>=2&&r0.left>=0&&r0.right<=W+400)out.push('INVISIBLE «'+tx.slice(0,20)+'»');if(r.width<2||r.height<2)continue;tn.push({n,r,tx:tx.slice(0,24),pe})}}
 // 1) text sticking out of the viewport horizontally
 tn.forEach(x=>{if(x.r.right>W+1||x.r.left<-1)out.push('OUT-X «'+x.tx+'»')});
 // 2) text overlapping other text
 for(let i=0;i<tn.length;i++)for(let j=i+1;j<tn.length;j++){const a=tn[i],b=tn[j];if(a.n===b.n)continue;if(isFix(a.pe)!==isFix(b.pe))continue;
  const ox=Math.min(a.r.right,b.r.right)-Math.max(a.r.left,b.r.left),oy=Math.min(a.r.bottom,b.r.bottom)-Math.max(a.r.top,b.r.top);
  if(ox>3&&oy>3)out.push('TEXT-OVERLAP «'+a.tx+'» × «'+b.tx+'»')}
 // 3) visible text covered by an unrelated element (e.g. under a header/bar)
 tn.forEach(x=>{const cx=(x.r.left+x.r.right)/2,cy=(x.r.top+x.r.bottom)/2;if(cx<0||cx>W||cy<0||cy>H)return;const e=document.elementFromPoint(cx,cy);if(!e)return;
  if(x.pe===e||x.pe.contains(e)||e.contains(x.pe))return;
  // allow same-card siblings with pointer-events none / transparent overlays
  if(getComputedStyle(e).pointerEvents=='none')return;if(e.parentElement===document.body&&!e.id&&!e.className&&getComputedStyle(e).position=='fixed')return;if(modal&&modal.contains(e))return;const fx=isFix(e);if(fx){const fr=fx.getBoundingClientRect(),bottom=fr.top>H*0.4;if(mode==='top'&&bottom)return;if(mode==='end'&&!bottom)return}out.push('COVERED «'+x.tx+'» by '+(e.id?'#'+e.id:(e.className&&e.className.baseVal===undefined?'.'+String(e.className).split(' ')[0]:e.tagName)))});
 const t=document.body.innerText;
 (t.match(/\\b[a-z]{1,6}[A-Z][A-Za-z]{0,12}\\b/g)||[]).forEach(w=>{if(!['iPhone','iOS','YouTube','TikTok','WhatsApp','PayPal'].includes(w))out.push('RAWKEY '+w)});
 document.querySelectorAll('svg').forEach(v=>{const r=v.getBoundingClientRect();if(r.width>0&&!v.querySelector('path,circle,rect,line,polyline,polygon,ellipse,g'))out.push('EMPTY-ICON '+(v.parentElement.getAttribute('aria-label')||v.parentElement.className||v.parentElement.tagName))});
 (t.match(/\\b(?!schema_)[a-z]{1,5}[A-Z]?_[a-z][a-z_]+\\b/g)||[]).forEach(w=>out.push('RAWKEY '+w));
 ['undefined','NaN','[object','null'].forEach(b=>{if(t.includes(b))out.push('BAD '+b)});
 if(document.scrollingElement.scrollWidth>W+1)out.push('PAGE-OVERFLOW '+document.scrollingElement.scrollWidth);
 return [...new Set(out)].slice(0,12)}"""
APPS={
 'customer':[("home","S.v='home'"),("cat","go('cat',{catKey:'rest'})"),("menu","go('menu',{store:STORES[0].n})"),("menu-closed","go('menu',{store:ALLS[1].n})"),("menu-search","S.msearch=true;S.msq='бур';go('menu',{store:STORES[0].n})"),
   ("item-sheet","S.msq='';S.msearch=false;go('menu',{store:STORES[0].n});openItem('i1')"),("cart","S.sh=null;S.cart={i2:2,['i1~o11']:1};S.cartStore=STORES[0].n;go('cart')"),("pay","go('pay')"),("cart-gone","S.cart=Object.assign({},S.cart,{ixx:1});go('cart')"),("pay-busy","delete S.cart.ixx;S.busy=true;go('pay')"),("pay-sched","S.busy=false;S.at=slotsAll()[3];go('pay')"),("cart-fd","S.at=null;S.cart={i2:8};go('cart')"),("group","S.cart={i2:2,['i1~o11']:1};S.gid=window.__GRP.id;S.grp=window.__GRP;go('group')"),("group-member","S.grp=Object.assign({},window.__GRP,{is_host:false});render()"),("group-closed","S.grp=Object.assign({},window.__GRP,{is_host:false,status:'closed'});render()"),("group-cart","S.grp=window.__GRP;go('cart')"),("group-pay","grpCheckout()"),("home-group","grpBackPay();go('home')"),("addr","S.busy=false;go('addr')"),("addrForm","go('addrForm')"),
   ("orders","go('orders')"),("track","go('track',{tid:'ord1'})"),("track2","go('track',{tid:'ord4'})"),("fav","go('fav')"),("promo","go('promo')"),("offer","go('offer',{oid:'s1'})"),("me","go('me')"),("settings","go('settings')"),("about","go('about')"),("privacy","go('privacy')"),("wallet","go('wallet')"),("support","go('support')"),("ticket","go('ticket',{tkid:'t1'})")],
 'merchant':[("orders","setTab('o')"),("menu","setTab('m')"),("stats","setTab('s')"),("profile","setTab('p')"),("item-new","setTab('m');openSheet()"),("item-edit","openSheet('i1')"),("req-sheet","SH=null;rqOpen()"),("req-list","RQ=null;RL=true;render()"),("branch-sheet","RL=false;brOpen('b1')")],
 'driver':[("home","document.querySelectorAll('.nav div')[0].click()"),("history","document.querySelectorAll('.nav div')[1].click()"),("profile","document.querySelectorAll('.nav div')[2].click()")],
 'admin':[("tab%d","")],
}
# every list with NO data: the screen must show a proper empty state (checked by the same rules + EMPTY-STATE: no visible text in the page body)
EMPTY={
 'customer':[("home","S.v='home'"),("cat","go('cat',{catKey:'rest'})"),("cart","S.cart={};go('cart')"),("orders","go('orders')"),("fav","go('fav')"),("promo","go('promo')"),("wallet","go('wallet')"),("support","go('support')"),("addr","go('addr')"),("me","go('me')")],
 'merchant':[("orders","setTab('o')"),("menu","setTab('m')"),("stats","setTab('s')"),("profile","setTab('p')"),("req-list","RQ=null;RL=true;render()")],
 'driver':[("home","document.querySelectorAll('.nav div')[0].click()"),("history","document.querySelectorAll('.nav div')[1].click()")],
 'admin':[("tab%d","")],
}
def run():
    bad=0;rows=[]
    with sync_playwright() as p:
        b=p.chromium.launch()
        for app,screens in APPS.items():
            if os.environ.get('QA_APPS') and app not in os.environ['QA_APPS'].split(','): continue
            for w in tuple(int(x) for x in os.environ.get('QA_W','360,390,430').split(',')):
                for offline in (False,True):
                    ctx=b.new_context(viewport={'width':w,'height':780},device_scale_factor=1);pg=ctx.new_page();errs=[]
                    pg.on('pageerror',lambda e,errs=errs:errs.append(str(e)))
                    pg.route('**/*',lambda rt,rq,app=app:(rt.fulfill(status=200,content_type='application/javascript',body=FIX.replace('window.__ROLE','"'+app+'"')) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
                    pg.goto('file://'+root+'/'+app+'.html',wait_until='domcontentloaded');pg.wait_for_timeout(2200)
                    if offline: pg.evaluate("window.dispatchEvent(new Event('offline'))");pg.wait_for_timeout(2800)
                    if app=='admin':
                        n=pg.locator('.tabs button').count();screens=[("tab%d"%i,"document.querySelectorAll('.tabs button')[%d].click()"%i) for i in range(n)]+[("loyalty-editor","tab='y';HE=null;heOpen()"),("loyalty-stores","HE=null;LYS=true"),("close-editor","HE=null;LYS=false;tab='o'")]
                    if app=='driver':
                        pg.evaluate("(()=>{try{document.querySelector('.hd')}catch(e){}})()")
                    for name,js in screens:
                        try: pg.evaluate("()=>{"+js+";if(typeof render==='function')try{render()}catch(e){}}");pg.wait_for_timeout(350)
                        except Exception as e: rows.append((app,w,offline,name,['EVAL-ERR '+str(e)[:80]]));bad+=1;continue
                        for scroll in (0,'end'):
                            pg.evaluate("window.scrollTo(0,%s)"%('0' if scroll==0 else 'document.body.scrollHeight'));pg.wait_for_timeout(120)
                            iss=pg.evaluate(CHECK,'top' if scroll==0 else 'end')
                            if iss: bad+=1;rows.append((app,w,offline,name+('@end' if scroll else ''),iss));pg.screenshot(path='/tmp/qa_%s_%d_%s_%s%s.png'%(app,w,'off' if offline else 'on',name,'_end' if scroll else ''))
                    if errs: bad+=1;rows.append((app,w,offline,'JS',errs[:3]))
                    ctx.close()
        if not os.environ.get('QA_NOEMPTY'):
          for app,screens in EMPTY.items():
            if os.environ.get('QA_APPS') and app not in os.environ['QA_APPS'].split(','): continue
            for w in tuple(int(x) for x in os.environ.get('QA_W','360,390,430').split(',')):
                ctx=b.new_context(viewport={'width':w,'height':780},device_scale_factor=1);pg=ctx.new_page();errs=[];pg.add_init_script("window.__EMPTY=1")
                pg.on('pageerror',lambda e,errs=errs:errs.append(str(e)))
                pg.route('**/*',lambda rt,rq,app=app:(rt.fulfill(status=200,content_type='application/javascript',body=FIX.replace('window.__ROLE','"'+app+'"')) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
                pg.goto('file://'+root+'/'+app+'.html',wait_until='domcontentloaded');pg.wait_for_timeout(2200)
                sc=screens
                if app=='admin':
                    n=pg.locator('.tabs button').count();sc=[("tab%d"%i,"document.querySelectorAll('.tabs button')[%d].click()"%i) for i in range(n)]
                for name,js in sc:
                    try: pg.evaluate("()=>{"+js+";if(typeof render==='function')try{render()}catch(e){}}");pg.wait_for_timeout(300)
                    except Exception as e: rows.append((app,w,False,'EMPTY:'+name,['EVAL-ERR '+str(e)[:80]]));bad+=1;continue
                    iss=pg.evaluate(CHECK,'top')
                    if iss: bad+=1;rows.append((app,w,False,'EMPTY:'+name,iss));pg.screenshot(path='/tmp/qa_empty_%s_%d_%s.png'%(app,w,name))
                if errs: bad+=1;rows.append((app,w,False,'EMPTY:JS',errs[:3]))
                ctx.close()
    for r in rows: print(r[0],r[1],'OFF' if r[2] else 'on',r[3],'|',' ; '.join(r[4]))
    print('QA ISSUES',bad);return bad
if __name__=='__main__': sys.exit(1 if run() else 0)
