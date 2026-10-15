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
 setInterval(function(){var T=window.__pvTables;if(!T||document.hidden)return;window.__pvTick++;T.app_settings=(T.app_settings||[]).filter(function(x){return x.key!=='pv_tick'}).concat([{key:'pv_tick',value:String(window.__pvTick)}]);
   /* a demo courier goes online / offline: the counters at the top change, so every screen is really rebuilt */
   var c=(T.profiles||[]).filter(function(x){return x.id==='pv-courier'})[0];if(!c){c={id:'pv-courier',email:'pv@test.com',role:'driver',name:'Демо-курьер',phone:'+992900000077',driver_status:'approved',cash_limit:1000,created_at:new Date().toISOString()};T.profiles.push(c)}
   c.online=window.__pvTick%%2===1;c.last_seen=new Date().toISOString()},10000);
 document.addEventListener('DOMContentLoaded',function(){var b=document.createElement('div');b.id='pv-strip';b.style.cssText='position:sticky;top:0;z-index:99999;background:#b42318;color:#fff;font:700 11.5px/1.35 -apple-system,sans-serif;padding:5px 8px;text-align:center';b.innerHTML='ПРЕВЬЮ · тестовые данные · запись отключена — PREVIEW · <span id="pv-cyc">автообновлений: 0</span> <button id="pv-sim" type="button" style="margin:3px 0 0 4px;border:0;border-radius:999px;padding:3px 9px;background:#fff;color:#b42318;font:700 11px -apple-system,sans-serif">محاكاة حفظ موظف آخر</button>';
   /* preview tool only: as if another staff member saved meanwhile (points settings, banner bn1, first happy hour) — the demo data changes, then the app's normal refresh runs */
   b.querySelector('#pv-sim').onclick=function(){var T=window.__pvTables;if(!T)return;var k=0;T.app_settings.forEach(function(x){if(x.key==='cashback_pct'){x.value=String((+x.value||0)+1);k++}if(x.key==='loyalty_min_order'){x.value=String((+x.value||0)+5);k++}});
     (T.banners||[]).forEach(function(x){if(x.id==='bn1'){x.title=String(x.title).replace(/ · изменено.*$/,'')+' · изменено '+new Date().toLocaleTimeString().slice(0,5);x.sort=(+x.sort||0)+1}});
     if(T.happy_hours&&T.happy_hours[0])T.happy_hours[0].discount_pct=Math.min(90,(+T.happy_hours[0].discount_pct||10)+5);
     document.dispatchEvent(new Event('visibilitychange'));this.textContent='✓ تمت المحاكاة';var me=this;setTimeout(function(){me.textContent='محاكاة حفظ موظف آخر'},2500)};document.body.insertBefore(b,document.body.firstChild);
   var n=0,hook=function(){if(window.TLB&&TLB.on){TLB.on(function(){n++;var e=document.getElementById('pv-cyc');if(e)e.textContent='автообновлений: '+n})}else setTimeout(hook,300)};hook()});
})();
"""%(repr(READ_RPC))
open(os.path.join(out,'preview-client.js'),'w').write(FIX+GUARD)
s=open(os.path.join(root,app+'.html')).read()
s2=re.sub(r'<script src="https://cdn\.jsdelivr\.net/npm/@supabase/supabase-js@[^"]+"></script>','<script src="preview-client.js"></script>',s)
assert s2!=s,'supabase script tag not found'
s2=s2.replace("<script>if(window.top!==window.self){document.documentElement.style.display='none';try{window.top.location=window.self.location}catch(e){}}</script>","")
s2=s2.replace('<title>','<title>PREVIEW · ',1)
open(os.path.join(out,app+'.html'),'w').write(s2)
open(os.path.join(out,'talabat-core.js'),'w').write(open(os.path.join(root,'talabat-core.js')).read())
print('preview built in',out)
