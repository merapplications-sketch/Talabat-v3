"""Build a READ-ONLY demo copy of the admin panel (or another app) for review, with fake data.
   python3 tools/build_preview.py <out_dir> [admin|customer|merchant|driver]
- The real Supabase client is replaced by an in-memory demo client (the QA fixtures of tools/qa_all.py).
- No request can reach the real database: every network call to Supabase is answered locally.
- Every WRITE is refused: insert / update / upsert / delete, storage uploads and every RPC that is not on the
  read-only list. The page shows a red "preview" strip and a notice for each blocked action.
- The app code (admin.html + talabat-core.js) is the same as the branch; only the client script tag, the
  frame guard (so the page can be shown inside a preview frame) and the CSP connect list differ."""
import os,sys,re
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
out=sys.argv[1];app=(sys.argv[2] if len(sys.argv)>2 else 'admin')
os.makedirs(out,exist_ok=True)
if app=='partner':
    # the public partner page: no Supabase client at all. The server (Edge Function) is answered locally with the reply chosen
    # in the red strip; the "not a robot" box is a stand-in. Nothing is sent anywhere.
    PV=r"""<script>
(function(){
 var Q=new URLSearchParams(location.search);window.__pvPartner={reply:Q.get('reply')||'ok',sent:[]};
 if(Q.get('off')!=='1')window.__pvCfg={fn:'preview://partner-lead',siteKey:'preview-site-key'};
 window.turnstile={_n:0,render:function(el,o){var id=++this._n,b=document.createElement('label');b.id='pv-ts';b.style.cssText='display:flex;align-items:center;gap:10px;border:1px dashed #b42318;border-radius:10px;padding:12px;font:600 14px -apple-system,sans-serif;color:#b42318';
   b.innerHTML='<input type="checkbox" id="pv-ts-cb" style="width:22px;height:22px"> Демо-проверка «я не робот» (в рабочей версии — Cloudflare Turnstile)';el.appendChild(b);
   b.querySelector('input').onchange=function(){if(this.checked)o.callback('pv-token-'+id+'-'+Date.now())};this._o=o;this._el=b;return id},
   reset:function(){if(this._el){var c=this._el.querySelector('input');if(c)c.checked=false}},remove:function(){if(this._el)this._el.remove();this._el=null}};
 var f0=window.fetch;window.fetch=function(u,o){if(String(u).indexOf('preview://')===0){var P=window.__pvPartner,b={};try{b=JSON.parse(o.body)}catch(e){}
   P.sent.push({hasToken:!!b.token,category:b.category});
   return new Promise(function(ok,bad){setTimeout(function(){if(P.reply==='network')return bad(new TypeError('network'));
     var st={ok:200,busy:429,verify_failed:403,bad_phone:400,bad_value:400,unavailable:503}[P.reply]||503;ok(new Response(JSON.stringify({result:P.reply}),{status:st}))},700)})}
   return Promise.reject(new TypeError('preview: no network'))};
 document.addEventListener('DOMContentLoaded',function(){var s=document.createElement('div');s.id='pv-strip';s.style.cssText='background:#b42318;color:#fff;font:700 12px/1.4 -apple-system,sans-serif;padding:6px 10px;text-align:center';
   var opts=[['ok','заявка принята'],['busy','слишком много заявок'],['verify_failed','проверка не пройдена'],['unavailable','сервер недоступен'],['network','нет сети'],['bad_phone','номер отклонён сервером']];
   s.innerHTML='ПРОСМОТР · ничего не отправляется · ответ сервера: <select id="pv-reply" style="font-size:16px;color:#000;border-radius:6px;max-width:100%">'+opts.map(function(x){return '<option value="'+x[0]+'"'+(x[0]===window.__pvPartner.reply?' selected':'')+'>'+x[1]+'</option>'}).join('')+'</select> · <a style="color:#fff" href="?off=1">без настроек</a> · <a style="color:#fff" href="?">с настройками</a>';
   document.body.insertBefore(s,document.body.firstChild);s.querySelector('#pv-reply').onchange=function(){window.__pvPartner.reply=this.value}});
})();
</script>"""
    s=open(os.path.join(root,'partner.html')).read()
    s2=s.replace("const CFG={fn:'',siteKey:''};","const CFG=window.__pvCfg||{fn:'',siteKey:''};")
    assert s2!=s
    s2=s2.replace("<script>if(window.top!==window.self){document.documentElement.style.display='none';try{window.top.location=window.self.location}catch(e){}}</script>",PV)
    s2=s2.replace('<title>','<title>PREVIEW · ',1).replace('href="merchant.html"','href="../merchant/merchant.html"')
    open(os.path.join(out,'partner.html'),'w').write(s2)
    print('preview built in',out);sys.exit(0)
FIX=open(os.path.join(root,'tools','qa_all.py')).read().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE','"%s"'%app).replace('var T={','var T=window.__pvTables={',1)
READ_RPC=['my_perms','store_private','cash_balances','admin_customers','staff_list','contacts_for','admin_search_orders','brand_stats','brand_route',
  'wallet_balance','loyalty_summary','best_dishes','store_speed','delivery_quote','my_offers','my_rating','active_contacts','order_contacts','group_get',
  'happy_hour_pct','promo_guard_version','courier_steps_version','is_admin','owner_info','wallet_room']
GUARD=r"""
(function(){
 /* ---------- READ-ONLY PREVIEW GUARD ---------- */
 var READ=%s;
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
   for(var i=1;i<=62;i++){var id='h'+(1000-i),sub=80+i,dt=new Date(n-(20+i*6)*D).toISOString(),s0=st[i%%6];
     T.orders.push({_hist:true,id:id,store_id:'s1',customer_id:C,driver_id:null,status:s0,subtotal:sub,discount:0,promo_discount:0,delivery_fee:10,driver_payout:10,tip:0,total:sub+10,commission:Math.round(sub*10)/100,commission_pct:10,payment:i%%2?'cash':'apple',address:'ул. Демо 1',lat:38.56,lng:68.78,customer_name:'Демо-клиент · 62 заказа',created_at:dt,done_at:s0==='delivered'?dt:null,wallet_used:0,fee_waived:0});
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
   c.online=window.__pvTick%%2===1;c.last_seen=new Date().toISOString()},10000);
 document.addEventListener('DOMContentLoaded',function(){var b=document.createElement('div');b.id='pv-strip';b.style.cssText='position:relative;z-index:800;background:#b42318;color:#fff;font:700 11.5px/1.35 -apple-system,sans-serif;padding:5px 8px;text-align:center';b.innerHTML='ПРЕВЬЮ · тестовые данные · запись отключена — PREVIEW · <span id="pv-cyc">автообновлений: 0</span> <button id="pv-sim" type="button" style="margin:3px 0 0 4px;border:0;border-radius:999px;padding:3px 9px;background:#fff;color:#b42318;font:700 11px -apple-system,sans-serif">محاكاة حفظ موظف آخر</button>';
   /* preview tool only: as if another staff member saved meanwhile (points settings, banner bn1, first happy hour) — the demo data changes, then the app's normal refresh runs */
   b.querySelector('#pv-sim').onclick=function(){var T=window.__pvTables;if(!T)return;var k=0;T.app_settings.forEach(function(x){if(x.key==='cashback_pct'){x.value=String((+x.value||0)+1);k++}if(x.key==='loyalty_min_order'){x.value=String((+x.value||0)+5);k++}});
     (T.banners||[]).forEach(function(x){if(x.id==='bn1'){x.title=String(x.title).replace(/ · изменено.*$/,'')+' · изменено '+new Date().toLocaleTimeString().slice(0,5);x.sort=(+x.sort||0)+1}});
     if(T.happy_hours&&T.happy_hours[0])T.happy_hours[0].discount_pct=Math.min(90,(+T.happy_hours[0].discount_pct||10)+5);
     document.dispatchEvent(new Event('visibilitychange'));this.textContent='✓ تمت المحاكاة';var me=this;setTimeout(function(){me.textContent='محاكاة حفظ موظف آخر'},2500)};document.body.insertBefore(b,document.body.firstChild);
   var n=0,hook=function(){if(window.TLB&&TLB.on){TLB.on(function(){n++;var e=document.getElementById('pv-cyc');if(e)e.textContent='автообновлений: '+n})}else setTimeout(hook,300)};hook()});
})();
"""%(repr(READ_RPC))
DIAG=r"""
(function(){
 /* ---------- PREVIEW-ONLY diagnostic log: page jumps, reloads, coming back from the background.
    Kept in this browser (localStorage, last 300 lines). No names, phones, typed values, tokens or addresses are recorded. ---------- */
 var PVB='@@BUILD@@';
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
"""
import subprocess
def _build_id():
    try:
        h=subprocess.run(['git','rev-parse','--short=8','HEAD'],capture_output=True,text=True,cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
        d=subprocess.run(['git','status','--porcelain','--','admin.html','merchant.html','talabat-core.js','tools/build_preview.py'],capture_output=True,text=True,cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
        return (h or '?')+(' +local changes' if d else '')
    except Exception: return '?'
open(os.path.join(out,'preview-client.js'),'w').write(FIX+GUARD+DIAG.replace('@@BUILD@@',_build_id()))
s=open(os.path.join(root,app+'.html')).read()
s2=re.sub(r'<script src="https://cdn\.jsdelivr\.net/npm/@supabase/supabase-js@[^"]+"></script>','<script src="preview-client.js"></script>',s)
assert s2!=s,'supabase script tag not found'
s2=s2.replace("<script>if(window.top!==window.self){document.documentElement.style.display='none';try{window.top.location=window.self.location}catch(e){}}</script>","")
s2=s2.replace('<title>','<title>PREVIEW · ',1)
open(os.path.join(out,app+'.html'),'w').write(s2)
open(os.path.join(out,'talabat-core.js'),'w').write(open(os.path.join(root,'talabat-core.js')).read())
print('preview built in',out)
