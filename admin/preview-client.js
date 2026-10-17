
(function(){
 var role="admin",now=Date.now(),iso=function(m){return new Date(now-m*60000).toISOString()};
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
 var orders=st.map(function(s,i){return {id:'ord'+i,store_id:'s1',customer_id:U,driver_id:U,status:s,subtotal:120+i,discount:10,promo_discount:0,delivery_fee:10,driver_payout:20,tip:5,total:125+i,commission:10,commission_pct:10,payment:i%2?'cash':'wallet',leave_at_door:i==3,is_gift:i==3,substitution:['call','replace','remove'][i%3],address:'ул. Рудаки 100, подъезд 2, этаж 5, кв. 45, Душанбе',lat:38.56,lng:68.78,customer_name:'Муаммад ибни Абдуллоҳ аз Душанбе',scheduled_for:i==0?new Date(now+3*3600e3).toISOString():null,group_id:i==1?'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa':null,fee_waived:i==4?10:0,cancel_reason:i==6?'out_of_stock':null,cancel_note:i==6?'закончился плов, приносим извинения':null,cancelled_by:i==6?'store':null,arrived_store_at:i==1?iso(5):null,delivery_photo:i==4?U+'/ord4/abcdefgh12.jpg':null,created_at:iso(30+i*50),done_at:i>3?iso(10+i):null,wallet_used:0}});
 /* UAT samples: free delivery paid by the restaurant (like #9097), cancelled online order with wallet + points returned, rejected after acceptance with a tip (like #9098) */
 Object.assign(orders[4],{subtotal:440,discount:0,promo_discount:25,promo_code:'SALE25',delivery_fee:0,fee_waived:22,delivery_base:10,delivery_extra:12,delivery_km:5.2,tip:0,total:415});
 Object.assign(orders[5],{payment:'apple',wallet_used:20,wallet_returned_at:iso(200),points_used:1000,points_value:1,points_returned_at:iso(200),total:129});
 /* like #9098: items 440, delivery 0, tip 10 → total 450; commission 5% of 440 = 22 */
 Object.assign(orders[6],{payment:'apple',subtotal:440,discount:0,delivery_fee:0,tip:10,total:450,commission:22,commission_pct:5});
 var evs=[];[['ord1',[['pending',0],['preparing',61.4],['driver_assigned',125.9],['at_store',300.2],['ready',420.7]]],['ord4',[['pending',0],['preparing',59.6],['driver_assigned',121.2],['at_store',260.8],['pickedup',400.4],['at_customer',1210.9],['delivered',1290.1],['mystery_kind',1300]]]].forEach(function(x){var b=now-3*3600e3;x[1].forEach(function(e,k){evs.push({id:x[0]+k,order_id:x[0],kind:e[0],at:new Date(b+e[1]*1000).toISOString()})})});
 var chats=[{id:901,order_id:'ord1',sender_id:U,body:'Здравствуйте! Подъезд с обратной стороны дома, позвоните, когда будете рядом. ОченьДлинноеСловоБезПробеловКотороеДолжноПереноситься',created_at:iso(20)},{id:902,order_id:'ord1',sender_id:'u2',body:'LOC:38.560000,68.780000',created_at:iso(19)}];
 var rts=[];[[5,5,0],[5,4,0],[4,4,0],[4,5,0],[3,4,0],[1,2,1],[2,3,1],[5,5,1],[4,4,1],[3,3,1],[2,1,1]].forEach(function(r,k){rts.push({id:k+1,order_id:'ord'+(k%7),customer_id:U,store_id:'s1',driver_id:U,store_stars:r[0],driver_stars:r[1],comment:k%2?'[Холодная еда] долго ждали':'',created_at:iso(100+k),handled_at:r[2]?iso(50+k):null,handled_note:r[2]?'Связались с клиентом':null})});
 orders.forEach(function(o){if(o.payment==='wallet')o.wallet_used=o.total});
 /* commission exactly as place_order computes it (patch 31-33): (items − store discount − happy-hour discount) × commission % ; promo and points do not reduce it */
 orders.forEach(function(o){o.commission=Math.round((o.subtotal-(o.discount||0)-(o.hh_discount||0))*o.commission_pct)/100});   /* paid fully from the wallet = wallet_used equals the total (as place_order records it) */
 var oitems=[];orders.forEach(function(o,i){oitems.push({id:'oi'+i,order_id:o.id,item_id:'i1',name:'Очень длинное название блюда с несколькими ингредиентами',price:o.subtotal/2,qty:2,note:'без лука, пожалуйста, очень острый соус отдельно',options:[{id:'o11',g:'Размер',n:'Средний',p:5}]})});
 var banners=[{id:'bn1',title:'Скидка 20% на всё',image_url:'',placement:'top',link_type:'store',link_value:'s1',active:true,sort:1,created_at:iso(1)},{id:'bn2',title:'Бесплатная доставка',image_url:'',placement:'bottom',active:true,sort:2,created_at:iso(1)}];
 var addrs=[{id:'a1',user_id:U,label:'home',street:'пр. Рудаки',house:'100',entrance:'2',floor:'5',apartment:'45',details:'',note:'домофон не работает',lat:38.56,lng:68.78,is_default:true}];
 var profiles=[{id:U,email:user.email,role:role,name:'Муаммад ибни Абдуллоҳ аз Душанбе',phone:'+992900000000',driver_status:'approved',cash_limit:1000,created_at:iso(1000)},{id:'u2',email:'driver2@test.com',role:'driver',name:'Водитель',phone:'+992900000009',driver_status:'pending',created_at:iso(5)},{id:'u3',email:'c@test.com',role:'customer',name:'Клиент',phone:'+992900000008',created_at:iso(5)}];
 var T=window.__pvTables={stores:stores,menu_items:items,item_option_groups:groups,item_options:opts,orders:orders,order_items:oitems,banners:banners,addresses:addrs,brands:[{id:'b1',name:'Дар-ул-Хилоф',owner_id:U}],profiles:profiles,
  promo_codes:[{id:'p1',code:'WELCOME10',kind:'percent',value:10,min_order:50,max_uses:100,active:true,created_at:iso(1)}],favorites:[{user_id:U,store_id:'s1'}],wallet_entries:[{id:'w1',user_id:U,amount:50,kind:'refund',note:'Пополнение',created_at:iso(5)}],
  support_tickets:[{id:'t1',user_id:U,customer_id:U,subject:'Не приехал заказ',reason:'late',order_id:'ord1',status:'open',created_at:iso(20),updated_at:iso(2)}],ticket_messages:[{id:'tm1',ticket_id:'t1',sender_id:U,body:'Здравствуйте, где мой заказ?',created_at:iso(20)}],
  order_chat:chats,order_offers:[],ratings:rts,store_requests:[{id:'r1',user_id:U,name:'Новая кофейня',category:'rest',phone:'+992900000005',address:'ул. 1',status:'pending',created_at:iso(3)}],audit_log:[],app_texts:[],app_settings:[{key:'delivery_free_km',value:3},{key:'delivery_step_km',value:0.5},{key:'delivery_step_price',value:2},{key:'delivery_max_km',value:15},{key:'delivery_road_factor',value:1.3},{key:'loyalty_earn_per_tjs',value:10},{key:'loyalty_points_per_tjs',value:1000},{key:'loyalty_min_redeem',value:1000},{key:'loyalty_expiry_days',value:90},{key:'cashback_pct',value:0},{key:'loyalty_voucher_points',value:1000},{key:'loyalty_min_order',value:30},{key:'loyalty_rate_reward',value:10}],order_recipient:[{order_id:'ord3',name:'Мадина Рахимова',phone:'+992901112233'}],happy_hours:[{id:1,title:'Счастливые часы обеда для всех',store_id:null,days:[1,2,3,4,5,6,7],start_time:'00:00:00',end_time:'23:59:00',discount_pct:25,active:true},{id:2,title:'Ночь',store_id:'s1',days:[6,7],start_time:'22:00:00',end_time:'02:00:00',discount_pct:30,active:false}],loyalty_ledger:[{id:1,user_id:U,points:1250,kind:'earn',order_id:'ord4',created_at:iso(60)},{id:2,user_id:U,points:-1000,kind:'spend',order_id:'ord1',created_at:iso(30)}],app_pages:[{slug:'about',body_ru:'Талабот — сервис доставки еды и товаров в Душанбе. (демо-текст)',body_en:'Talabot is a food and goods delivery service in Dushanbe. (demo text)'},{slug:'privacy',body_ru:'Мы храним только данные, нужные для доставки заказа. (демо-текст)',body_en:'We keep only the data needed to deliver an order. (demo text)'}],order_events:evs,client_errors:[],drivers:[]};
 if(window.__EMPTY)Object.keys(T).forEach(function(k){if(k!=='profiles'&&!(role==='merchant'&&(k==='stores'||k==='brands')))T[k]=[]});
 function res(d){return {data:d,error:null}}
 function chain(kind,name){var single=false,eqs=[],rng=null,cnt=false,ins=null;
  var c=new Proxy(function(){},{get:function(t,p){
   if(p==='then')return function(ok,bad){var d;
     if(kind==='rpc'){var R={my_perms:null,wallet_balance:50,store_private:stores.map(function(s){return {id:s.id,owner_id:U,commission_pct:10,max_discount_pct:30}}),cash_balances:[],admin_customers:profiles.filter(function(x){return x.role=='customer'}).map(function(x){return Object.assign({orders_count:3,total_spent:250.5},x)}),staff_list:[],my_offers:[],my_rating:null,brand_stats:[{store_id:'s1',name:'x',branch_name:'Центр',orders:12,delivered:10,cancelled:2,revenue:1500.5}],brand_route:[],active_contacts:[],contacts_for:[],delivery_quote:{fee:12,fee_full:12,base:10,extra:2,km:4.2,steps:1,step_km:1,free_km:3,first_free:false},check_promo:null,loyalty_summary:{balance:2850,next_exp_at:new Date(now+86400000*12).toISOString(),next_exp_pts:1250,earn_per_tjs:10,points_per_tjs:100,min_redeem:1000,expiry_days:90,cashback_pct:0,voucher_points:1000,min_order:30,rate_reward:10},best_dishes:[{item_id:'i1',store_id:'s1',cnt:40},{item_id:'i2',store_id:'s1',cnt:22},{item_id:'i33',store_id:'s3',cnt:9}],store_speed:[{store_id:'s1',avg_min:11.5,n:14},{store_id:'s3',avg_min:25,n:6}],group_get:GRP,group_create:GRP,group_add:GRP,group_set:GRP,group_remove:GRP};d=R.hasOwnProperty(name)?R[name]:null}
     else{var rows=T[name]||[];
       /* rows marked _hist = an old order outside the newest ones the panel loads: only paged reads and reads by id see them (preview sample) */
       if(rows.some(function(r){return r._hist})){if(ins)rows=rows.filter(function(r){return !r._hist||ins[1].some(function(v){return v==r[ins[0]]})});else if(!rng)rows=rows.filter(function(r){return !r._hist})}
       d=single?(name==='profiles'?profiles[0]:rows[0]||null):rows}
     /* paged reads (.range) — only the admin's customer history uses them: filter by .eq, newest first, page, exact count */
     if(kind==='from'&&rng){var f=(T[name]||[]).filter(function(r){return eqs.every(function(e){return r[e[0]]==e[1]})}).slice().sort(function(a,b){return Date.parse(b.created_at)-Date.parse(a.created_at)});return Promise.resolve({data:f.slice(rng[0],rng[1]+1),error:null,count:cnt?f.length:null}).then(ok,bad)}
     return Promise.resolve(res(d)).then(ok,bad)};
   if(p==='eq')return function(a,b){eqs.push([a,b]);return c};
   if(p==='range')return function(a,b){rng=[a,b];return c};
   if(p==='in')return function(a,v){ins=[a,v||[]];return c};
   if(p==='select')return function(cols,o){if(o&&o.count)cnt=true;return c};
   if(p==='single'||p==='maybeSingle'){single=true;return function(){return c}}
   return function(){return c}}});return c}
 window.supabase={createClient:function(){return {auth:{getSession:function(){return Promise.resolve({data:{session:{user:user,access_token:'x'}},error:null})},signOut:function(){return Promise.resolve({})},signInWithPassword:function(){return Promise.resolve({error:{message:'x'}})},onAuthStateChange:function(){return {data:{subscription:{unsubscribe:function(){}}}}}},
  from:function(n){return chain('from',n)},rpc:function(n){return chain('rpc',n)},channel:function(){var ch={on:function(){return ch},subscribe:function(){return ch},unsubscribe:function(){}};return ch},removeChannel:function(){},storage:{from:function(){return {upload:function(){return Promise.resolve({})},getPublicUrl:function(){return {data:{publicUrl:''}}}}}}};}};
})();

(function(){
 /* ---------- READ-ONLY PREVIEW GUARD ---------- */
 var READ=['my_perms', 'store_private', 'cash_balances', 'admin_customers', 'staff_list', 'contacts_for', 'admin_search_orders', 'brand_stats', 'brand_route', 'wallet_balance', 'loyalty_summary', 'best_dishes', 'store_speed', 'delivery_quote', 'my_offers', 'my_rating', 'active_contacts', 'order_contacts', 'group_get', 'happy_hour_pct', 'promo_guard_version', 'courier_steps_version', 'is_admin', 'owner_info', 'wallet_room'];
 function note(what){try{var d=document.getElementById('pv-note');if(!d){d=document.createElement('div');d.id='pv-note';d.style.cssText='position:fixed;left:12px;right:12px;bottom:16px;z-index:100000;background:#b42318;color:#fff;font:600 13px -apple-system,sans-serif;padding:12px 14px;border-radius:12px;text-align:center;box-shadow:0 8px 24px #0005';document.body.appendChild(d)}
   d.textContent='Режим просмотра: запись отключена ('+what+') · Preview: writing is disabled';clearTimeout(window.__pvT);window.__pvT=setTimeout(function(){d.remove()},3500)}catch(e){}}
 window.__pvBlocked=[];
 function blocked(what){window.__pvBlocked.push(what);note(what);return Promise.resolve({data:null,error:{message:'preview_readonly: '+what,code:'PREVIEW'}})}
 /* the demo search answers like patch 35: order number, customer name or phone digits */
 var make=window.supabase.createClient;
 window.supabase.createClient=function(){var c=make.apply(this,arguments),from=c.from,rpc=c.rpc;
  c.from=function(table){var ch=from.call(c,table),w=null;
    return new Proxy(ch,{get:function(t,p){if(p==='insert'||p==='update'||p==='upsert'||p==='delete'){return function(){w=p;return this}.bind(new Proxy(ch,{get:function(tt,pp){if(pp==='then')return function(ok,bad){return blocked(w+' '+table).then(ok,bad)};return function(){return this}}}))}
      var v=t[p];return v}})};
  c.rpc=function(n,a){if(READ.indexOf(n)<0)return blocked('rpc '+n);
    if(n==='admin_search_orders'){var q=String((a&&a.p_q)||'').trim().toLowerCase().replace(/^#/,''),d=q.replace(/\D/g,'');
      return c.from('orders').select('*').then(function(r){var ids=(r.data||[]).filter(function(o){return String(o.id).toLowerCase()==q||(q.length>=2&&String(o.customer_name||'').toLowerCase().indexOf(q)>=0)||(d.length>=4&&'992900000000'.indexOf(d)>=0)}).filter(function(o){return !a.p_status||o.status==a.p_status}).map(function(o){return {id:o.id}});return {data:ids,error:null}})}
    if(n==='contacts_for')return Promise.resolve({data:((a&&a.p_ids)||[]).map(function(i){return {order_id:i,customer_phone:'+992900000000',driver_phone:'+992900000009'}}),error:null});
    return rpc.call(c,n,a)};
  c.storage={from:function(b){return {upload:function(){return blocked('upload '+b)},getPublicUrl:function(){return {data:{publicUrl:''}}},createSignedUrl:function(){return Promise.resolve({data:null,error:{message:'preview'}})}}}};
  return c};
 /* nothing may reach the real servers */
 var f0=window.fetch;window.fetch=function(u,o){if(/supabase\.co/.test(String(u)))return Promise.resolve(new Response('',{status:200}));return f0.apply(this,arguments)};
 /* like a busy real day: the demo data "changes" every 10 s, so the screen goes through the same automatic refresh as production
    (an invisible settings row ticks; the strip counts the refreshes the app really received) */
 window.__pvTick=0;
 (function(){var T=window.__pvTables;if(T&&T.profiles)T.profiles.push({id:'pv-courier',email:'pv@test.com',role:'driver',name:'Демо-курьер',phone:'+992900000077',driver_status:'approved',cash_limit:1000,online:false,last_seen:null,created_at:new Date().toISOString()})})();
 /* preview sample for the customer card: one demo customer with 62 OLD orders (beyond the newest ones the panel loads),
    so «показано 50 из 62», «Показать ещё», opening an old order and «Назад» can be tried by hand. Invented data only. */
 (function(){var T=window.__pvTables;if(!T||!T.profiles||!/admin/.test(location.pathname))return;var C='pv-cust62',D=86400000,n=Date.now(),st=['delivered','delivered','delivered','cancelled','delivered','rejected'];
   T.profiles.push({id:C,email:'demo62@test.com',role:'customer',name:'Демо-клиент · 62 заказа',phone:'+992900000062',created_at:new Date(n-500*D).toISOString()});
   for(var i=1;i<=62;i++){var id='h'+(1000-i),sub=80+i,dt=new Date(n-(20+i*6)*D).toISOString(),s0=st[i%6];
     T.orders.push({_hist:true,id:id,store_id:'s1',customer_id:C,driver_id:null,status:s0,subtotal:sub,discount:0,promo_discount:0,delivery_fee:10,driver_payout:10,tip:0,total:sub+10,commission:Math.round(sub*10)/100,commission_pct:10,payment:i%2?'cash':'apple',address:'ул. Демо 1',lat:38.56,lng:68.78,customer_name:'Демо-клиент · 62 заказа',created_at:dt,done_at:s0==='delivered'?dt:null,wallet_used:0,fee_waived:0});
     T.order_items.push({_hist:true,id:'hi'+i,order_id:id,item_id:'i1',name:'Демо-блюдо',price:sub,qty:1,note:'',options:[]})}})();
 /* preview sample (v57): requests from the public partner page, one per state. Invented names, demo phones. */
 (function(){var T=window.__pvTables;if(!T||!T.store_requests||!/admin/.test(location.pathname))return;var H=3600000,n=Date.now(),iso=function(h){return new Date(n-h*H).toISOString()};
   T.store_requests.push({id:'pv-ld1',kind:'lead',status:'new',name:'Демо-кафе «Чинор»',category:'rest',phone:'+992900000101',created_at:iso(1)},
     {id:'pv-ld2',kind:'lead',status:'contacted',name:'Демо-пекарня',category:'sweets',phone:'+992900000102',admin_note:'Перезвонить в понедельник',created_at:iso(26)},
     {id:'pv-ld3',kind:'lead',status:'converted',name:'Демо-аптека',category:'pharmacy',phone:'+992900000103',store_id:'s1',created_at:iso(80),decided_at:iso(30)},
     {id:'pv-ld4',kind:'lead',status:'rejected',name:'Демо-магазин',category:'shops',phone:'+992900000104',admin_note:'Вне зоны доставки',created_at:iso(90),decided_at:iso(40)})})();
 (function(){var T=window.__pvTables;if(!T||!T.banners||!/customer/.test(location.pathname))return;
   var svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="400"><rect width="1200" height="400" fill="#1c1c21"/><rect x="0" y="0" width="14" height="400" fill="#f1511b"/><text x="70" y="170" font-family="Arial" font-size="64" font-weight="700" fill="#fff">Ваше заведение в TALABOT</text><text x="70" y="250" font-family="Arial" font-size="38" fill="#f6b59b">Заявка на подключение</text></svg>';
   T.banners.push({id:'pv-bnp',title:'Подключите своё заведение',image_url:'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg),placement:'bottom',link_type:'partner',link_value:null,active:true,is_active:true,sort:9,created_at:new Date().toISOString()})})();
 setInterval(function(){var T=window.__pvTables;if(!T||document.hidden)return;window.__pvTick++;T.app_settings=(T.app_settings||[]).filter(function(x){return x.key!=='pv_tick'}).concat([{key:'pv_tick',value:String(window.__pvTick)}]);
   /* a demo courier goes online / offline: the counters at the top change, so every screen is really rebuilt */
   var c=(T.profiles||[]).filter(function(x){return x.id==='pv-courier'})[0];if(!c){c={id:'pv-courier',email:'pv@test.com',role:'driver',name:'Демо-курьер',phone:'+992900000077',driver_status:'approved',cash_limit:1000,created_at:new Date().toISOString()};T.profiles.push(c)}
   c.online=window.__pvTick%2===1;c.last_seen=new Date().toISOString()},10000);
 document.addEventListener('DOMContentLoaded',function(){var b=document.createElement('div');b.id='pv-strip';b.style.cssText='position:relative;z-index:800;background:#b42318;color:#fff;font:700 11.5px/1.35 -apple-system,sans-serif;padding:5px 8px;text-align:center';b.innerHTML='ПРЕВЬЮ · тестовые данные · запись отключена — PREVIEW · <span id="pv-cyc">автообновлений: 0</span> <button id="pv-sim" type="button" style="margin:3px 0 0 4px;border:0;border-radius:999px;padding:3px 9px;background:#fff;color:#b42318;font:700 11px -apple-system,sans-serif">محاكاة حفظ موظف آخر</button>';
   /* preview tool only: as if another staff member saved meanwhile (points settings, banner bn1, first happy hour) — the demo data changes, then the app's normal refresh runs */
   b.querySelector('#pv-sim').onclick=function(){var T=window.__pvTables;if(!T)return;var k=0;T.app_settings.forEach(function(x){if(x.key==='cashback_pct'){x.value=String((+x.value||0)+1);k++}if(x.key==='loyalty_min_order'){x.value=String((+x.value||0)+5);k++}});
     (T.banners||[]).forEach(function(x){if(x.id==='bn1'){x.title=String(x.title).replace(/ · изменено.*$/,'')+' · изменено '+new Date().toLocaleTimeString().slice(0,5);x.sort=(+x.sort||0)+1}});
     if(T.happy_hours&&T.happy_hours[0])T.happy_hours[0].discount_pct=Math.min(90,(+T.happy_hours[0].discount_pct||10)+5);
     document.dispatchEvent(new Event('visibilitychange'));this.textContent='✓ تمت المحاكاة';var me=this;setTimeout(function(){me.textContent='محاكاة حفظ موظف آخر'},2500)};document.body.insertBefore(b,document.body.firstChild);
   var n=0,hook=function(){if(window.TLB&&TLB.on){TLB.on(function(){n++;var e=document.getElementById('pv-cyc');if(e)e.textContent='автообновлений: '+n})}else setTimeout(hook,300)};hook()});
})();

(function(){
 /* ---------- PREVIEW-ONLY diagnostic log: page jumps, reloads, coming back from the background.
    Kept in this browser (localStorage, last 300 lines). No names, phones, typed values, tokens or addresses are recorded. ---------- */
 var PVB='2ef990bd';
 var DK='pv-diag',HK='pv-hid',EK='pv-end',lastIn=0,lastRs=0,lastY=window.scrollY||0,lastRsLog=0;
 function rd(){try{return JSON.parse(localStorage.getItem(DK)||'[]')}catch(e){return []}}
 function ctx(){var vv=window.visualViewport,o=(screen.orientation&&screen.orientation.type)||(window.orientation!=null?'deg'+window.orientation:'');
   return innerWidth+'x'+innerHeight+(vv?' vv'+Math.round(vv.width)+'x'+Math.round(vv.height)+' z'+(Math.round(vv.scale*100)/100)+' t'+Math.round(vv.offsetTop):'')+' y'+Math.round(window.scrollY)+'/'+Math.max(0,Math.round(document.documentElement.scrollHeight-innerHeight))+' '+o}
 function log(ev,info){try{var a=rd();a.push(new Date().toTimeString().slice(0,8)+' '+ev+(info?' · '+info:'')+' · '+ctx());while(a.length>300)a.shift();localStorage.setItem(DK,JSON.stringify(a))}catch(e){}}
 window.__pvLog=log;
 function rinfo(){try{if(typeof RINFO!=='undefined'&&RINFO.t)return 'last redraw '+(Date.now()-RINFO.t)+'ms ago '+(RINFO.auto?'auto':'by tap')+' '+RINFO.mode}catch(e){}return 'no redraw yet'}
 function act(){var a=document.activeElement;return a&&a!==document.body?'focus '+a.tagName.toLowerCase()+(a.id?'#'+a.id:'')+(a.type?'['+a.type+']':''):'no focus'}
 /* how did this page start? */
 try{var nv=performance.getEntriesByType('navigation')[0],hid=+localStorage.getItem(HK)||0,end=localStorage.getItem(EK)||'none';
   log('PAGE LOAD','build '+PVB+' · type '+(nv?nv.type:'?')+(document.wasDiscarded?' discarded':'')+(hid?' · was in background '+Math.round((Date.now()-hid)/1000)+'s':'')+' · previous page ended: '+end);localStorage.removeItem(EK)}catch(e){}
 window.addEventListener('pageshow',function(e){log('pageshow',e.persisted?'from back-forward cache (no reload)':'')});
 window.addEventListener('pagehide',function(e){var w=window.TLB_SIGNING_OUT?'sign-out':(e.persisted?'pagehide (kept in cache)':'pagehide');try{localStorage.setItem(EK,w+' at '+new Date().toTimeString().slice(0,8))}catch(_){}log('pagehide',w)});
 document.addEventListener('visibilitychange',function(){if(document.hidden){try{localStorage.setItem(HK,String(Date.now()))}catch(e){}log('went to background')}else{var h=0;try{h=+localStorage.getItem(HK)||0;localStorage.removeItem(HK)}catch(e){}log('came back',h?'away '+Math.round((Date.now()-h)/1000)+'s, page NOT reloaded':'')}});
 ['touchstart','touchmove','touchend','wheel','keydown','pointerdown'].forEach(function(ev){document.addEventListener(ev,function(){lastIn=Date.now()},{passive:true,capture:true})});
 function rs(kind){lastRs=Date.now();if(Date.now()-lastRsLog>400){lastRsLog=Date.now();log(kind)}trace(kind)}
 /* ROTATION / RESIZE TRACE: what moved the page? Samples every frame for 1.5 s after a resize and compares with the last calm state:
    page height (layout reflow), text size (iOS text inflation), the anchor element at the top of the screen, app scrollTo calls, redraws.
    Only numbers and element positions are recorded (no text, no values). */
 var calm=null,tr=null,appMoves=0;
 var PR=null;function sz(){try{if(!PR){PR=document.createElement('span');PR.setAttribute('aria-hidden','true');PR.textContent='Проверка размера текста 0123456789';PR.style.cssText='position:absolute;left:-9999px;top:0;font-size:13px;white-space:nowrap;visibility:hidden';document.body.appendChild(PR)}
   return Math.round(parseFloat(getComputedStyle(PR).fontSize)*100)/100+'/'+Math.round(PR.getBoundingClientRect().width)}catch(x){return '?'}}
 function anchor(){try{var el=document.elementFromPoint(Math.round(innerWidth/2),90),p=[],n=el;while(n&&n.id!=='app'&&n.parentElement&&p.length<8){p.unshift([].indexOf.call(n.parentElement.children,n));n=n.parentElement}return n&&n.id==='app'?{p:p.join('.'),top:Math.round(el.getBoundingClientRect().top)}:null}catch(x){return null}}
 function byPath(pp){try{var n=document.getElementById('app');pp.split('.').forEach(function(i){n=n&&n.children[+i]});return n}catch(x){return null}}
 function snap(){return {t:Date.now(),y:Math.round(scrollY),h:Math.round(document.documentElement.scrollHeight),w:innerWidth,vh:innerHeight,fs:sz(),a:anchor(),rn:(typeof RINFO!=='undefined'&&RINFO?RINFO.n:0)}}
 setInterval(function(){if(!tr&&Date.now()-lastRs>1500&&Date.now()-lastIn>300)calm=snap()},300);
 function trace(kind){if(tr)return;var b=calm||snap(),m0=appMoves,fr=[],t0=Date.now(),tin=lastIn;tr=1;
   (function step(){var s=snap();fr.push(s);if(Date.now()-t0<1500)return requestAnimationFrame(step);tr=null;
     var e=fr[fr.length-1],mx0=b.h-b.vh,mx1=e.h-e.vh,ya=null;if(b.a){var el=byPath(b.a.p);if(el)ya=Math.round(el.getBoundingClientRect().top)}
     var why=[];if(e.fs!==b.fs)why.push('probe text size/width changed '+b.fs+' → '+e.fs+' (text rendered at another size)');
     if(Math.abs(e.h-b.h)>40)why.push('page height '+b.h+'→'+e.h+' (layout reflow)');
     if(appMoves>m0)why.push('the APP called scrollTo '+(appMoves-m0)+'×');
     if(e.rn>b.rn)why.push('app redraw ×'+(e.rn-b.rn));
     if(e.y===0&&b.y>50&&mx1>50)why.push('page reached the top with no app scrollTo although it could stay (mover not identified)');
     if(b.y>mx1+2)why.push('old position beyond the new end of page (clamp)');
     var yp=fr.map(function(f){return f.y}),ch=[];yp.forEach(function(v,i){if(i&&v!==yp[i-1])ch.push(Math.round((fr[i].t-t0))+'ms:'+v)});
     log('TRACE '+kind,'before y'+b.y+' h'+b.h+' '+b.w+'x'+b.vh+' text '+b.fs+' | after y'+e.y+' h'+e.h+' '+e.w+'x'+e.vh+' text '+e.fs+' | anchor '+(b.a?('top '+b.a.top+'→'+(ya==null?'gone':ya)):'none')+' | y changes '+(ch.slice(0,6).join(' ')||'none')+' | '+(why.join('; ')||'no cause seen')+' | '+(tin?'touch '+(t0-tin)+'ms before':'no touch before')+(lastIn>t0?', touch during the 1.5 s':', no touch during the 1.5 s'))})()}
 window.addEventListener('resize',function(){rs('resize')});window.addEventListener('orientationchange',function(){rs('rotation')});
 if(window.visualViewport)visualViewport.addEventListener('resize',function(){rs('visual viewport resize (keyboard/zoom)')});
 /* a jump = the page moved more than 150 px in one step with no finger/key in the last 1 s */
 window.addEventListener('scroll',function(){var y=window.scrollY,d=y-lastY;if(Math.abs(d)>150&&Date.now()-lastIn>1000)log('JUMP '+Math.round(lastY)+' -> '+Math.round(y),rinfo()+' · last resize '+(lastRs?Date.now()-lastRs+'ms ago':'never')+' · '+act()+' · '+touch());lastY=y},{passive:true});
 /* caller names from a stack: Chrome has an "Error" first line and "at f (url)" frames, Safari has no first line and "f@url"
    frames. Frames are kept in order, the first one (this wrapper) is dropped; anonymous frames show as "?" so nothing is skipped. */
 function callers(st){try{var fr=String(st||'').split('\n').filter(function(l){return /^\s*at |@/.test(l)}).map(function(l){var m=l.match(/^\s*at (?:async )?([^\s(]+) \(/)||l.match(/^\s*([^@\s]*)@/);return m&&m[1]?m[1].replace(/^HTMLButtonElement\./,''):'?'});fr=fr.slice(1).map(function(n){return n.replace(/^window\./,'')}).filter(function(n,i,a){return !i||n!==a[i-1]});return fr.slice(0,3).join('<')}catch(e){return '?'}}
 window.__pvCallers=callers;
 function touch(){return lastIn?'last touch '+(Date.now()-lastIn)+'ms ago':'no touch yet'}
 /* SECTION TAP (admin menu strip): from / to section code, strip place, page offset before the tap, after the redraw, after the
    strip keep step, strip sideways offset, page height, extra height kept for a short section, then the page offset per frame for 0.8 s */
 var NV=null;
 function navHook(){if(typeof window.tabTop!=='function'||typeof window.tabKeep!=='function'){if(document.readyState!=='complete'||!navHook.n||navHook.n<40){navHook.n=(navHook.n||0)+1;setTimeout(navHook,250)}return}
   var tt=window.tabTop,tk=window.tabKeep,strip=function(){return document.querySelector('.tabs')};
   window.tabTop=function(){var s=strip();NV={from:typeof tab!=='undefined'?tab:'?',y0:Math.round(scrollY),h0:document.documentElement.scrollHeight,sl0:s?Math.round(s.scrollLeft):null,t:Date.now()};return tt.apply(this,arguments)};
   window.tabKeep=function(t0){var n=NV;NV=null;var s=strip(),y1=Math.round(scrollY),r=tk.apply(this,arguments);
     if(!n)return r;s=strip();var ap=document.getElementById('app'),y2=Math.round(scrollY),st=s?Math.round(s.getBoundingClientRect().top):null,fr=[],t1=Date.now();
     var base=(typeof tab!=='undefined'?n.from+'→'+tab:'?')+' · strip '+(t0==null?'fixed side menu':Math.round(t0)+'→'+st)+' · y before '+n.y0+' / after redraw '+y1+' / after keep '+y2+
       ' · strip sideways '+n.sl0+'→'+(s?Math.round(s.scrollLeft):null)+' · page h '+n.h0+'→'+document.documentElement.scrollHeight+(ap&&ap.style.minHeight?' · short section kept tall '+ap.style.minHeight:'');
     (function f(){fr.push([Date.now()-t1,Math.round(scrollY),s?Math.round(s.getBoundingClientRect().top):null,s?Math.round(s.scrollLeft):null]);if(Date.now()-t1<800)return requestAnimationFrame(f);
       var ch=[];fr.forEach(function(v,i){if(i&&(v[1]!==fr[i-1][1]||v[2]!==fr[i-1][2]))ch.push(v[0]+'ms:y'+v[1]+'/strip'+v[2])});
       log('SECTION TAP',base+' · 0.8 s after: '+(ch.slice(0,6).join(' ')||'no move')+' · '+touch())})();
     return r}}
 setTimeout(navHook,300);
 /* who asked the page to move */
 var st=window.scrollTo;window.scrollTo=function(x,y){var to=typeof x==='object'&&x?x.top:y;if(to!=null&&Math.abs(to-window.scrollY)>80){appMoves++;var who='';try{who=callers(new Error().stack)}catch(e){}log('app scrollTo '+Math.round(window.scrollY)+' -> '+Math.round(to),(who||'?')+' · '+rinfo()+' · '+touch())}return st.apply(window,arguments)};
 var al=window.alert;window.alert=function(m){log('alert',/бездейств|inactivity/i.test(String(m))?'INACTIVITY SIGN-OUT (30 min rule)':String(m).slice(0,60));return al.apply(window,arguments)};
 window.addEventListener('error',function(e){log('JS error',String(e.message||'').slice(0,100))});
 var tries=0,w=function(){tries++;try{if(typeof UIR!=='undefined'&&UIR){log('screen restore after load',JSON.stringify(UIR));return}}catch(e){}if(tries<40)setTimeout(w,250)};setTimeout(w,500);
 /* panel */
 function panel(){var p=document.getElementById('pv-dp');if(p){p.remove();return}p=document.createElement('div');p.id='pv-dp';p.dir='ltr';
   p.style.cssText='position:fixed;left:8px;right:8px;top:8px;bottom:8px;z-index:100001;background:#fff;border-radius:14px;box-shadow:0 10px 40px #0007;display:flex;flex-direction:column;padding:10px;font:12px -apple-system,sans-serif';
   var ua=navigator.userAgent,os=(ua.match(/OS (\d+[_\d]*)/)||[])[1],sv=(ua.match(/Version\/([\d.]+)/)||[])[1],cr=(ua.match(/(CriOS|Chrome)\/([\d.]+)/)||[])[2];
   var head='Talabot admin PREVIEW · '+(window.TLB&&TLB.version||'')+' · build '+PVB+' · '+(/iPhone|iPad/.test(ua)?'iOS '+String(os||'?').replace(/_/g,'.'):'')+(sv?' Safari '+sv:'')+(cr?' Chrome '+cr:'')+' · now: '+ctx();
   var ta=document.createElement('textarea');ta.readOnly=true;ta.style.cssText='flex:1;width:100%;box-sizing:border-box;font:11px/1.4 ui-monospace,Menlo,monospace;border:1px solid #ddd;border-radius:8px;padding:6px';ta.value=head+'\n'+rd().join('\n');
   var row=document.createElement('div');row.style.cssText='display:flex;gap:6px;margin-top:8px';
   function bt(t,f){var x=document.createElement('button');x.type='button';x.textContent=t;x.style.cssText='flex:1;border:0;border-radius:10px;padding:10px;font:700 13px -apple-system,sans-serif;background:#f1f1f4';x.onclick=f;row.appendChild(x);return x}
   var cp=bt('نسخ السجل',function(){var v=ta.value;function ok(){cp.textContent='✓ تم النسخ'}if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(v).then(ok,function(){ta.select();try{document.execCommand('copy');ok()}catch(e){}});else{ta.select();try{document.execCommand('copy');ok()}catch(e){}}});
   cp.style.background='#b42318';cp.style.color='#fff';
   bt('مسح السجل',function(){try{localStorage.removeItem(DK)}catch(e){}ta.value=head+'\n'});bt('إغلاق',function(){p.remove()});
   p.appendChild(ta);p.appendChild(row);document.body.appendChild(p)}
 document.addEventListener('DOMContentLoaded',function(){var s=document.getElementById('pv-strip');if(!s)return;var x=document.createElement('button');x.type='button';x.textContent='سجل التشخيص';
   x.style.cssText='margin:3px 0 0 4px;border:0;border-radius:999px;padding:3px 9px;background:#fff;color:#b42318;font:700 11px -apple-system,sans-serif';x.onclick=panel;s.appendChild(x)});
})();
/* v60c preview sample (PREVIEW ONLY, demo numbers from the local test example; nothing is sent anywhere):
   store s2 = cash only + «platform settles»; store s1 = «courier pays the store»; order ord2 = courier-pays order in «ready». */
(function(){var T=window.__pvTables;if(!T)return;
 (T.stores||[]).forEach(function(s){if(s.id==='s2'){s.accept_online=false;s.settle_method='platform_settles'}if(s.id==='s1'){s.settle_method='driver_pays'}});
 (T.orders||[]).forEach(function(o){if(o.store_id==='s1')o.pay_rules={accept_online:true,allow_wallet:true,allow_points:true,settle_method:'driver_pays'}});
 var now=new Date().toISOString(),pds=[{id:2,direction:'driver_to_platform',amount:60,before_amount:110,after_amount:50,reference:'KASSA-7',note:'smena',recorded_by_name:'Finance Farhod',recorded_at:now},
   {id:1,direction:'platform_to_driver',amount:15,before_amount:40,after_amount:25,reference:'PAY-1',recorded_by_name:'Finance Farhod',recorded_at:now}];
 var dsp=[{id:3,order_id:'ord1',amount:100,reference:'CHK-A',status:'confirmed',decided_by_name:'Owner Muso',recorded_at:now},{id:2,order_id:'ord2',amount:100,reference:'CHK-B',status:'claimed',recorded_at:now}];
 var pss=[{id:2,method:'online',amount:40,before_amount:40,after_amount:0,reference:'ON-1',status:'done',recorded_by_name:'Finance Farhod',status_by_name:'Finance Farhod',recorded_at:now},
   {id:1,method:'bank',amount:50,before_amount:90,after_amount:40,reference:'BANK-55',status:'done',recorded_by_name:'Finance Farhod',status_by_name:'Finance Farhod',recorded_at:now}];
 window.addEventListener('load',function(){var t=setInterval(function(){if(!window.TLB||!TLB.moneyRecords)return;clearInterval(t);
   TLB.driverPosition=function(){return Promise.resolve({collected:410,paid_to_stores_confirmed:300,paid_to_stores_claimed:0,handed_to_platform:60,cash_held:50,earned:40,earnings_paid:15,earnings_due:25})};
   TLB.storePosition=function(id){return Promise.resolve(id==='s2'?{gross:100,commission:10,store_funded:0,net_due:90,paid_by_drivers:0,paid_by_platform:90,balance:0,paid_on_undelivered:0,claimed_unconfirmed:0}
     :{gross:300,commission:30,store_funded:0,net_due:270,paid_by_drivers:400,paid_by_platform:0,balance:-130,paid_on_undelivered:100,claimed_unconfirmed:0})};
   TLB.moneyRecords=function(k,by){var L=k==='pds'?pds:k==='pss'?pss:dsp.filter(function(x){return !by||!by.order_id||x.order_id===by.order_id});return Promise.resolve({rows:L,more:false})};
 },100)});
})();
