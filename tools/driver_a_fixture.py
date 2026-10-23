from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'driver-a-qa'
OUT.mkdir(parents=True,exist_ok=True)
base=(ROOT/'tools/qa_all.py').read_text().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE','"driver"')
# Extend only the existing repository's test fixture; nothing from this file enters driver.html.
setup='''
 window.__UI_TABLES=T;window.__UI_USER=U;window.__UI_RPCS=[];window.__UI_UPLOADS=[];window.__UI_FAIL='';window.__UI_DELAY=40;
 var caseName=window.__UI_CASE||'pickup';var main=T.orders.find(o=>o.id==='ord1');
 T.orders=T.orders.filter(o=>o.id==='ord1'||o.id==='ord4');T.order_items=T.order_items||[];
 Object.assign(main,{subtotal:100,discount:0,promo_discount:0,delivery_fee:20,tip:0,total:120,driver_payout:20,payment:'cash',wallet_used:0,points_value:0,points_used:0,leave_at_door:false,address:'82-й микрорайон, дом 1, подъезд 2, этаж 3',customer_name:'Демо-клиент',status:'ready',lat:null,lng:null,arrived_store_at:iso(5),arrived_cust_at:null,substitution:'call',is_gift:false});
 T.stores[0].name='Демо-ресторан';T.stores[0].address='проспект Рудаки, 82';T.profiles[0].name='Демо-курьер';
 if(caseName==='offer'||caseName==='orders'||caseName==='shift'||caseName==='empty'){main.driver_id=null;main.arrived_store_at=null;main.status='ready'}
 if(caseName==='delivery'||caseName==='noncash'||caseName==='photo'||caseName==='chat'){main.status='pickedup';main.arrived_cust_at=iso(1)}
 if(caseName==='noncash')main.payment='card';if(caseName==='photo')main.leave_at_door=true;
 if(caseName==='phone')T.profiles[0].phone='';if(caseName==='apply')T.profiles[0].role='customer';if(caseName==='access')T.profiles[0].driver_status='pending';
 if(caseName==='cancelled'){main.status='cancelled';main.cancel_reason='too_busy'}
 window.__UI_OFFER=(caseName==='offer'||caseName==='orders')?[{order_id:'ord1',mode:'broadcast',rank:1,dist_km:null,secs_left:3600}]:[];
'''
base=base.replace(' if(window.__EMPTY)',setup+'\n if(window.__EMPTY)',1)
base+='''
(function(){var old=window.supabase.createClient;window.supabase.createClient=function(){var c=old.apply(this,arguments),rpc=c.rpc,from=c.from;
 c.rpc=function(name,args){window.__UI_RPCS.push([name,args]);var T=window.__UI_TABLES;
 if(name==='my_offers')return Promise.resolve({data:window.__UI_OFFER,error:null});
 if(name==='active_contacts'||name==='contacts_for')return Promise.resolve({data:[{order_id:'ord1',customer_phone:'+992900000001',driver_phone:'+992900000002'}],error:null});
 if(['driver_accept','driver_decline','driver_arrived','set_order_status','deliver_order'].includes(name))return new Promise(function(resolve){setTimeout(function(){if(window.__UI_FAIL===name)return resolve({data:null,error:{message:'bad_transition'}});var o=T.orders.find(x=>x.id===args.p_id);if(!o)return resolve({data:null,error:{message:'not_found'}});
 if(name==='driver_accept'){o.driver_id=window.__UI_USER;window.__UI_OFFER=[]}
 if(name==='driver_decline')window.__UI_OFFER=[];
 if(name==='driver_arrived')o[args.p_where==='store'?'arrived_store_at':'arrived_cust_at']=new Date().toISOString();
 if(name==='set_order_status')o.status=args.p_to;
 if(name==='deliver_order'){o.status='delivered';o.done_at=new Date().toISOString();o.cash_collected=args.p_cash}
 resolve({data:name==='driver_accept'?true:null,error:null})},window.__UI_DELAY)});
 return rpc.call(c,name,args)};
 c.from=function(name){if(name==='order_chat')return {insert:function(v){window.__UI_RPCS.push(['chat',v]);return new Promise(function(resolve){setTimeout(function(){if(window.__UI_FAIL==='chat')return resolve({error:{message:'demo-error'}});window.__UI_TABLES.order_chat.push({id:Date.now(),order_id:v.order_id,sender_id:v.sender_id,body:v.body,created_at:new Date().toISOString()});resolve({error:null})},window.__UI_DELAY)})},select:function(){return from.call(c,name).select.apply(from.call(c,name),arguments)}};return from.call(c,name)};
 c.storage={from:function(bucket){return {upload:function(p){window.__UI_UPLOADS.push([bucket,p]);return Promise.resolve({data:{path:p},error:null})},createSignedUrl:function(){return Promise.resolve({data:{signedUrl:'x'},error:null})}}}};
 if(window.__UI_CASE==='login'||window.__UI_CASE==='signup'||window.__UI_CASE==='email')c.auth.getSession=function(){return Promise.resolve({data:{session:null},error:null})};
 return c}})();
'''
(OUT/'review-fixture.js').write_text(base)
print('Review-only fixture written; production core untouched')
