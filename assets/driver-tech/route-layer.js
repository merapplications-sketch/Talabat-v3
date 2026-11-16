/* One navigation controller/view over the existing map and server facade. No order/chat/delivery mutations. */
(function(){
 'use strict';
 if(typeof mapUpd!=='function'||!window.TLB||!window.TALABOT_NAV_MODEL)return;
 const M=window.TALABOT_NAV_MODEL;
 TLB.addDict({nPoint:'Точка из чата',nLinksFail:'Не удалось получить ссылки на карты. Проверьте связь и повторите.',nRetry:'Повторить'},{nPoint:'Point from the chat',nLinksFail:'Could not get the map links. Check the connection and retry.',nRetry:'Retry'});
 TLB.addDict({nChoose:'Навигация',nInternal:'Внутри TALABOT',nExternal:'Внешняя навигация',nWeb:'Ссылка сайта',nApp:'Открыть',nHint:'Ссылка сайта тоже может открыть приложение — это зависит от телефона.',nExternalNote:'Маршрут — во внешней карте · TALABOT отслеживает позицию',nIdle:'Для маршрута выберите «Внутри TALABOT»',nTracking:'Только отслеживание · время прибытия недоступно',nLoading:'Проверяем навигацию…',nQuota:'Лимит маршрутов исчерпан',nDisabled:'Дорожная навигация отключена',nUnavailable:'Маршрут недоступен',nGps:'Нет свежего точного местоположения',nOffRoute:'Вне маршрута · пересчитываем',nNoPin:'Точные координаты назначения отсутствуют',nFollow:'Следовать за мной',nTurn:'Манёвр через',nRemaining:'Осталось примерно',nClose:'Закрыть',nUpdated:'Расчёт маршрута',nFix:'Позиция',nRetry:'Повторить'},
 {nChoose:'Navigation',nInternal:'Inside TALABOT',nExternal:'External navigation',nWeb:'Website link',nApp:'Open',nHint:'A website link may also open the app, depending on your phone.',nExternalNote:'Directions in an external map · TALABOT tracks your position',nIdle:'Choose Inside TALABOT to start routing',nTracking:'Tracking only · arrival time unavailable',nLoading:'Checking navigation…',nQuota:'Route allowance exhausted',nDisabled:'Road navigation disabled',nUnavailable:'Route unavailable',nGps:'No fresh accurate location',nOffRoute:'Off route · recalculating',nNoPin:'Exact destination coordinates missing',nFollow:'Follow me',nTurn:'Maneuver in',nRemaining:'Estimated remaining',nClose:'Close',nUpdated:'Route calculated',nFix:'Position',nRetry:'Retry'});
 
 TLB.addDict({nDefaultTitle:'Приложение для навигации по умолчанию',nDefaultHint:'Выбор сохраняется только на этом устройстве. Его можно изменить здесь.',nDefaultBadge:'По умолчанию',nSetDefault:'По умолчанию',nUseDefault:'Открыть в выбранном приложении'},
 {nDefaultTitle:'Default navigation app',nDefaultHint:'Saved only on this device. Change it here anytime.',nDefaultBadge:'Default',nSetDefault:'Set as default',nUseDefault:'Open in default app'});
 let config=null,configAt=0,configFlight=null,epoch=0,currentKey='',route=null,flight=null,lastAsk=0,retryAt=0,offRouteSince=0;
 let pointTo=null,pointChat=false,linksErr=false,polBusy=false;   // 31 Oct: chat point target + loading / failure states
 let mode='tracking',reason='disabled',following=false,chosen=false,open=false,links=[],linksKey='',linksFlight=null,detail=null,boundMap=null;
 function task(){return typeof aTask==='function'?aTask():null;}
 function stage(x){return typeof aTaskStage==='function'?aTaskStage(x):0;}
 function target(x){return x?M.destination(x,stage(x),storePt(x)):null;}
 function ready(){return window.L&&typeof DM!=='undefined'&&DM&&DM!==1&&DM.getContainer;}
 function active(){return task()&&!document.hidden;}
 function clearLine(){if(ready()&&DM.__route)DM.__route.clearLayers();}
 function reset(){epoch++;if(flight)flight.ctl.abort();flight=null;route=null;detail=null;currentKey='';lastAsk=0;retryAt=0;offRouteSince=0;chosen=false;following=false;mode='tracking';clearLine();}
 async function policy(force){
   if(!force&&configAt&&Date.now()-configAt<(config?.configTtlMs||30000))return config;
   if(configFlight)return configFlight;
   configFlight=TLB.navigation({op:'config'}).then(c=>{
     configAt=Date.now();const prev=config&&JSON.stringify(config);config=c&&Array.isArray(c.providers)?c:null;
     if(prev!==JSON.stringify(config)){epoch++;if(flight)flight.ctl.abort();route=null;clearLine();}
     if(!config||config.mode!=='internal'){mode='tracking';reason=config?.reason||'service_unavailable';route=null;detail=null;clearLine();}
     return config;
   }).finally(()=>{configFlight=null;});return configFlight;
 }
 function label(){
   const el=document.getElementById('a-map-state');if(!el)return;
   if(mode==='internal'&&detail){
     el.hidden=false;const stamp=v=>new Date(v).toLocaleTimeString(TLB.lang()==='ru'?'ru-RU':'en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
     el.textContent=t('nRemaining')+': '+(detail.remainingM/1000).toFixed(1)+' км · ~'+Math.max(1,Math.round(detail.remainingS/60))+' мин'+(detail.step?.instruction?' · '+t('nTurn')+' '+Math.round(detail.turnDistanceM)+' м: '+detail.step.instruction:'')+' · '+t('nUpdated')+' '+stamp(detail.calculatedAt)+' · '+t('nFix')+' '+stamp(detail.fixAt);
   }else if(config?.external&&config.mode!=='internal'){el.textContent=open?'':t('nExternalNote');el.hidden=open;}else{el.hidden=false;const k=reason==='not_started'?'nIdle':reason==='external'?'nExternal':reason==='quota'?'nQuota':reason==='disabled'?'nDisabled':reason==='gps_unavailable'?'nGps':reason==='off_route'?'nOffRoute':reason==='no_pin'?'nNoPin':'nUnavailable';el.textContent=t(k)+' · '+t('nTracking');}
 }
 function renderRoute(){
   if(!ready())return;
   if(!DM.__route)DM.__route=L.layerGroup().addTo(DM);DM.__route.clearLayers();
   if(mode==='internal'&&route){
     if(DM.__l)DM.__l.eachLayer(l=>{if(l instanceof L.Polyline&&!(l instanceof L.Polygon))DM.__l.removeLayer(l);});
     L.polyline(route.coords,{color:'#f1511b',weight:5,interactive:false,className:'a-route'}).addTo(DM.__route);
     if(DM.attributionControl){const at=route.source==='geoapify'?'Powered by <a href="https://www.geoapify.com/" target="_blank" rel="noopener">Geoapify</a>':'';/* fixed text per provider (Geoapify terms: visible follow link near the map); the server string is never inserted as HTML */if(DM.__navAttr!==at){if(DM.__navAttr)DM.attributionControl.removeAttribution(DM.__navAttr);DM.__navAttr=at;if(at)DM.attributionControl.addAttribution(at);}if(DM.attributionControl.getPosition()!=='topright')DM.attributionControl.setPosition('topright');/* bottom corner is under the sheet */}
   }
   if(boundMap!==DM){boundMap=DM;DM.on('dragstart zoomstart',e=>{if(e.originalEvent||e.type==='dragstart')following=false;});DM.getContainer().addEventListener('pointerdown',()=>{following=false;},{passive:true});DM.getContainer().addEventListener('touchstart',()=>{following=false;},{passive:true});DM.getContainer().addEventListener('wheel',()=>{following=false;},{passive:true});}
 }
 function fix(){return {point:[GEO.lat,GEO.lng],accuracy:GEO.acc,at:GEO.at};}
 function update(x){
   const to=target(x),k=M.key(x,stage(x),to);
   if(k!==currentKey){reset();currentKey=k;links=[];linksKey='';}
   if(!k){reason='no_pin';label();return;}
   if(!active()){reset();return;}
   if(!configAt||Date.now()-configAt>=(config?.configTtlMs||30000)){policy().then(()=>{if(active())update(task());});if(!config){reason='service_unavailable';label();return;}}
   if(!chosen||!config||config.mode!=='internal'){mode=mode==='external'?'external':'tracking';detail=null;route=null;reason=mode==='external'?'external':config?.mode==='internal'?'not_started':config?.reason||'service_unavailable';renderRoute();label();return;}
   const f=fix(),d=M.progress(route,f,config,Date.now());
   if(!M.point(f.point)||!Number.isFinite(f.at)||Date.now()-f.at>config.gpsMaxAgeMs||!Number.isFinite(f.accuracy)||f.accuracy>80||GEO.state!=='ok'){mode='tracking';detail=null;reason='gps_unavailable';renderRoute();label();return;}
   if(route&&Date.now()-route.calculated_at>config.refreshMs*2){route=null;detail=null;}
   if(route&&d.mode==='internal'){mode='internal';detail=d;reason=null;}else{mode='tracking';detail=null;reason=d.reason;}
   // Route only on explicit internal mode / confirmed sustained deviation; GPS progress itself is local.
   if(d.reason==='off_route'){if(!offRouteSince)offRouteSince=Date.now();}else offRouteSince=0;
   const needs=!route||(d.reason==='off_route'&&Date.now()-offRouteSince>=config.deviationHoldMs);
   if(needs&&!flight&&Date.now()>=retryAt&&(lastAsk===0||Date.now()-lastAsk>=config.refreshMs))ask(x,to,k,f.point);
   renderRoute();label();
   if(following&&ready()&&mode==='internal'){const box=document.getElementById('a-sheet'),height=DM.getSize().y,visible=Math.max(0,Math.min(height,box?.getBoundingClientRect().top||height));const p=DM.project(f.point,DM.getZoom());DM.panTo(DM.unproject(L.point(p.x,p.y+height/2-visible/2),DM.getZoom()),{animate:false});}
 }
 async function ask(x,to,k,from){
   const own=epoch;lastAsk=Date.now();const token={ctl:new AbortController()};flight=token;
   try{const r=await TLB.navigation({from,to},token.ctl.signal);
     const nowTask=task();if(own!==epoch||!active()||!nowTask||M.key(nowTask,stage(nowTask),target(nowTask))!==k)return;
     if(r.config){config=r.config;configAt=Date.now();}
     if(r.mode==='internal'&&Array.isArray(r.coords)&&r.coords.length>=2&&Number.isFinite(r.calculated_at)){route=r;retryAt=0;}
     else{route=null;detail=null;mode='tracking';reason=r.reason||'upstream';retryAt=Date.now()+Math.max(30000,(+r.retry_after_s||30)*1000);}
   }catch{route=null;detail=null;mode='tracking';reason='upstream';retryAt=Date.now()+30000;}
   finally{if(flight===token)flight=null;if(own===epoch&&active()){renderRoute();label();}}
 }

 // N-01: known external app links require no provider API key or paid routing.
 // Honor explicit server external=false or a server-supplied restricted provider list.
 const NAV_PROVIDERS=['google','2gis','yandex'];
 const NAV_NAMES={google:'Google Maps','2gis':'2GIS',yandex:'Yandex Maps'};
 let ephemeralDefault=null;
 function navKey(){return 'talabot-driver-nav-default-v1:'+(typeof DRV!=='undefined'&&DRV?DRV.id:'guest');}
 function navDefault(){
   try{const id=localStorage.getItem(navKey());if(NAV_PROVIDERS.includes(id))return id;}catch(e){}
   return ephemeralDefault;
 }
 function fallbackLinks(to){
   if(!M.point(to))return [];
   const la=to[0].toFixed(6),ln=to[1].toFixed(6);
   const pair=encodeURIComponent(la+','+ln),xy=ln+','+la;
   const ys=encodeURIComponent('~'+la+','+ln);
   const google='https://www.google.com/maps/dir/?api=1&destination='+pair+'&travelmode=driving&dir_action=navigate';
   const gapp='comgooglemaps://?daddr='+pair+'&directionsmode=driving';
   return [
     {id:'google',name:NAV_NAMES.google,app:gapp,web:google},
     {id:'2gis',name:NAV_NAMES['2gis'],app:'dgis://2gis.ru/routeSearch/rsType/car/to/'+xy,
      web:'https://2gis.ru/directions/tab/car/points/|'+xy},
     {id:'yandex',name:NAV_NAMES.yandex,
      app:'yandexmaps://maps.yandex.ru/?rtext='+ys+'&rtt=auto',
      web:'https://yandex.ru/maps/?rtext='+ys+'&rtt=auto'}
   ];
 }
 function eligibleId(id){return NAV_PROVIDERS.includes(id)&&(config?.external!==false)&&(!Array.isArray(config?.providers)||config.providers.includes(id));}

 // NAV_three_icons_row: exactly three actual branded SVG image sources.
 // NAV_default_green_dot_persisted: only explicit selection is stored.
 // NAV_navigate_opens_default: aNavigationOpen bypasses chooser after explicit selection.
 const NAV_ICONS={google:'assets/driver-tech/map-icons/google-maps.svg',
   '2gis':'assets/driver-tech/map-icons/2gis.svg',
   yandex:'assets/driver-tech/map-icons/yandex-maps.svg'};
 TLB.addDict({nSetDot:'Выбрать карту по умолчанию',nSetHint:'Выберите карту по умолчанию точкой под значком',nSaved:'Выбрано',nAppLaunch:'Открыть карту'},
   {nSetDot:'Set as default map',nSetHint:'Choose a default using the dot under its icon',nSaved:'Selected',nAppLaunch:'Open map'});
 const navIcon=id=>'<img src="'+NAV_ICONS[id]+'" alt="" width="36" height="36" decoding="async">';
 function iconSelect(id){
   const chosen=navDefault()===id;
   return '<button type="button" class="n-map-radio" aria-label="'+esc(t('nSetDot')+' '+NAV_NAMES[id])+
     '" aria-pressed="'+chosen+'" onclick="aNavigationSetDefault(\''+id+'\')">'+
     '<span class="n-map-radio-dot'+(chosen?' is-default':'')+'" aria-hidden="true"></span></button>';
 }
 function iconRows(list){
   return '<div class="n-map-icons" role="group" aria-label="'+esc(t('nChoose'))+'">'+
     list.map(v=>'<div class="n-map-item" data-nav-provider="'+v.id+'">'+
       '<a class="n-map-link" href="'+esc(v.web)+'" aria-label="'+esc(t('nAppLaunch')+' '+v.name)+
         '" onclick="return aNavigationLaunch(\''+v.id+'\')">'+
         '<span class="n-map-icon">'+navIcon(v.id)+
           (navDefault()===v.id?'<span class="n-map-default-indicator" aria-hidden="true"></span>':'')+
         '</span><span class="n-map-label">'+esc(v.name)+'</span></a>'+iconSelect(v.id)+
       '</div>').join('')+'</div>'+
     '<p class="n-map-choice-hint">'+esc(t('nSetHint'))+'</p>';
 }
 function usableLinks(to){
   // The only scheme origins are generated locally from validated numeric coordinates.
   // The server can disable external navigation or restrict these named providers.
   return (config?.external===false?[]:fallbackLinks(to).filter(v=>eligibleId(v.id)));
 }
 function secureLaunch(v){
   if(!v||!NAV_PROVIDERS.includes(v.id))return false;
   const ios=/iPhone|iPad|iPod/i.test(navigator.userAgent||'')||
     (navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
   window.aNavigationExternal();
   open=false;
   const url=ios?v.app:v.web;
   try{window.location.assign(url)}catch(e){try{window.location.assign(v.web)}catch(_){}}
   if(ios&&v.app!==v.web){
     const fallback=v.web;
     // A custom scheme cannot be probed for availability on iOS. If Safari
     // remains foregrounded, attempt the documented HTTPS route as fallback.
     setTimeout(()=>{if(!document.hidden&&document.visibilityState!=='hidden'){
       try{window.location.assign(fallback)}catch(e){}
     }},1100);
   }
   return false; // prevent the anchor's duplicate activation
 }
 window.aNavigationDefault=navDefault;
 window.aNavigationSetDefault=function(id){
   if(!eligibleId(id))return false;
   ephemeralDefault=id;
   try{localStorage.setItem(navKey(),id)}catch(e){}
   if(open||tab==='m')render();
   return true;
 };
 window.aNavigationProfileControl=function(){
   const selected=navDefault();
   return '<section class="card n-default-profile"><h3>'+esc(t('nDefaultTitle'))+'</h3>'+
     '<p class="xs mut">'+esc(t('nDefaultHint'))+'</p>'+
     '<div class="n-map-icons n-profile-map-row">'+NAV_PROVIDERS.filter(eligibleId).map(id=>
       '<button type="button" class="n-profile-map" aria-label="'+esc(t('nSetDot')+' '+NAV_NAMES[id])+
       '" aria-pressed="'+(selected===id)+'" onclick="aNavigationSetDefault(\''+id+'\')">'+
       '<span class="n-map-icon">'+navIcon(id)+(selected===id?'<span class="n-map-default-indicator" aria-hidden="true"></span>':'')+
       '</span><span class="n-map-label">'+esc(NAV_NAMES[id])+'</span></button>').join('')+
       '</div></section>';
 };
 window.aNavigationLaunch=function(id){
   const to=dest(task()),v=usableLinks(to).find(x=>x.id===id);
   return secureLaunch(v);
 };
 async function loadLinks(){
   const x=task(),to=dest(x),k=destKey(x,to);if(!k)return;
   if(linksFlight)return linksFlight;
   linksFlight=TLB.navigation({op:'links',to}).then(r=>{
     const y=task();if(destKey(y,dest(y))===k){linksKey=k;linksErr=!Array.isArray(r.links);
       links=Array.isArray(r.links)?r.links:[];if(r.config){config=r.config;configAt=Date.now();}
       if(open)render();}
   }).catch(()=>{
     const y=task();if(destKey(y,dest(y))===k){linksKey=k;linksErr=true;links=[];if(open)render();}
   }).finally(()=>{linksFlight=null;});
   return linksFlight;
 }
 function dest(x){return pointTo||(x?target(x):null);}
 function destKey(x,to){return pointTo?'pt:'+pointTo.join(','):(x&&to?M.key(x,stage(x),to):null);}
 function openWith(){open=true;links=[];linksKey='';linksErr=false;polBusy=true;render();Promise.resolve(policy(true)).catch(()=>{config=null;configAt=0;reason='service_unavailable';}).then(()=>{polBusy=false;return loadLinks()}).catch(()=>{linksErr=true;linksKey=destKey(task(),dest(task()));}).finally(()=>{polBusy=false;if(open)render()});}
 window.aNavigationOpen=function(){
   pointTo=null;pointChat=false;
   const v=usableLinks(dest(task())).find(x=>x.id===navDefault());
   if(v){secureLaunch(v);return;}
   openWith();
 };
 /* A point sent in the chat (LOC:lat,lng) opens the same chooser for exactly that point — no provider is forced. */
 window.aNavigationOpenPoint=function(lat,lng){const p=[+lat,+lng];if(!M.destination({lat:p[0],lng:p[1]},3,null))return false;pointTo=p;pointChat=!!chatOpen;chatOpen=false;openWith();return true;};
 window.aNavigationRetry=function(){links=[];linksKey='';linksErr=false;render();loadLinks().then(()=>{if(open)render();});};
 window.aNavigationClose=function(){open=false;const back=pointChat;pointTo=null;pointChat=false;if(back)chatOpen=true;render();if(!back)document.querySelector('.a-navigation')?.focus();};
 window.aNavigationInside=function(){open=false;chosen=true;following=true;retryAt=0;lastAsk=0;render();const x=task();if(x)update(x);};
 window.aNavigationExternal=function(){if(flight)flight.ctl.abort();chosen=false;mode='external';detail=null;route=null;epoch++;clearLine();label();};
 window.aNavigationFollow=function(){following=true;const x=task();if(x)update(x);};
 const oldModal=modal;
 modal=function(){
   if(!open||chatOpen||CXL||DV)return oldModal();
   const x=task(),to=dest(x);
   const list=usableLinks(to);
   return '<div class="ov a-aux n-chooser" onclick="aNavigationClose()"><div class="md" role="dialog" aria-modal="true" aria-label="'+esc(t('nChoose'))+'" onclick="event.stopPropagation()">'+
     '<header class="n-heading"><h2>'+esc(t('nChoose'))+'</h2><button type="button" class="round" onclick="aNavigationClose()" aria-label="'+esc(t('nClose'))+'">'+ico('x',20)+'</button></header>'+
     '<div class="n-body">'+
       (!to?'<p role="status">'+esc(t('nNoPin'))+'</p>':
         '<p class="n-destination">'+(pointTo?esc(t('nPoint')+' · '+pointTo.map(v=>v.toFixed(6)).join(', ')):
         esc(stage(x)>=3?x.address:x.store))+'</p>')+
       (to&&!pointTo&&config?.mode==='internal'?'<button type="button" class="b" onclick="aNavigationInside()">'+esc(t('nInternal'))+'</button>':
         '<p class="n-note" role="status">'+esc(t('nExternalNote'))+'</p>')+
       (list.length?iconRows(list):
         to?(polBusy||linksFlight?'<p role="status">'+esc(t('nLoading'))+'</p>':
           '<p role="alert">'+esc(t('nDisabled'))+'</p>'):'')+
       '<p class="n-hint">'+esc(t('nHint'))+'</p></div></div></div>';
 };
 const inner=mapUpd;mapUpd=function(x,force){const v=inner.apply(this,arguments);if(x)update(x);return v;};
 document.addEventListener('keydown',e=>{if(open&&e.key==='Escape'){e.preventDefault();aNavigationClose();}});
 document.addEventListener('visibilitychange',()=>{if(document.hidden){reset();configAt=0;links=[];linksKey='';open=false;}else policy(true).then(()=>{const x=task();if(x)update(x);});});
 window.addEventListener('pagehide',()=>reset());
 // Bounded lifecycle tick: stops provider requests off the mission; checks policy/staleness without creating a GPS watch.
 setInterval(()=>{const x=task();if(!x||document.hidden){if(currentKey)reset();return;}update(x);},1000);
 const css=document.createElement('style');
 css.textContent='.n-map-icons{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;align-items:start;margin:14px 0 4px}.n-map-item{min-width:0;display:flex;flex-direction:column;align-items:center;gap:2px}.n-map-link,.n-profile-map{display:flex;flex-direction:column;align-items:center;gap:4px;width:100%;min-height:78px;text-align:center;color:var(--ink);text-decoration:none;background:transparent;border:0;padding:4px;cursor:pointer}.n-map-icon{display:flex;align-items:center;justify-content:center;width:52px;height:52px;position:relative;border:1px solid var(--line);border-radius:15px;background:#fff}.n-map-icon img{width:36px;height:36px;object-fit:contain}.n-map-default-indicator{position:absolute;top:1px;right:1px;width:12px;height:12px;border:2px solid #fff;border-radius:50%;background:#18864c;box-shadow:0 0 0 1px #18864c}.n-map-label{font-size:12px;line-height:16px;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}.n-map-radio{display:flex;align-items:center;justify-content:center;width:44px;height:44px;border:0;background:none;border-radius:22px;cursor:pointer}.n-map-radio-dot{display:block;width:16px;height:16px;border:2px solid #8d99a2;border-radius:50%;background:#fff}.n-map-radio-dot.is-default{background:#18864c;border:3px solid #fff;box-shadow:0 0 0 2px #18864c}.n-map-choice-hint{margin:2px 0 10px;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:11px;color:var(--mut)}.n-profile-map-row .n-profile-map[aria-pressed=true] .n-map-icon{outline:2px solid #18864c;outline-offset:2px}.n-map-link:focus-visible,.n-map-radio:focus-visible,.n-profile-map:focus-visible{outline:3px solid var(--o);outline-offset:2px}.n-chooser .n-body{overflow-y:auto;overscroll-behavior:contain;max-width:100%}.n-chooser .n-hint{font-size:12px;color:var(--mut)}.a-map-state{max-width:calc(100% - 32px);white-space:normal}@media(max-width:370px){.n-map-icons{gap:4px}.n-map-label{font-size:11px}}';document.head.appendChild(css);
 window.__routeLayer={state:()=>({key:currentKey,hasRoute:!!route,mode,reason,inflight:!!flight,following}),refreshPolicy:()=>policy(true),fallbackLinks:fallbackLinks,getDefault:navDefault,launch:window.aNavigationLaunch};
})();
