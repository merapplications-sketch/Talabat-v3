/* One navigation controller/view over the existing map and server facade. No order/chat/delivery mutations. */
(function(){
 'use strict';
 if(typeof mapUpd!=='function'||!window.TLB||!window.TALABOT_NAV_MODEL)return;
 const M=window.TALABOT_NAV_MODEL;
 TLB.addDict({nChoose:'Навигация',nInternal:'Внутри TALABOT',nExternal:'Внешняя навигация',nWeb:'Веб-ссылка',nApp:'Открыть приложение',nHint:'Если приложение не установлено или не открылось — откройте в браузере. Можно выбрать другую карту.',nIdle:'Для маршрута выберите «Внутри TALABOT»',nTracking:'Только отслеживание · время прибытия недоступно',nLoading:'Проверяем навигацию…',nQuota:'Лимит маршрутов исчерпан',nDisabled:'Дорожная навигация отключена',nUnavailable:'Маршрут недоступен',nGps:'Нет свежего точного местоположения',nOffRoute:'Вне маршрута · пересчитываем',nNoPin:'Точные координаты назначения отсутствуют',nFollow:'Следовать за мной',nTurn:'Манёвр через',nRemaining:'Осталось примерно',nClose:'Закрыть',nUpdated:'Расчёт маршрута',nFix:'Позиция',nRetry:'Повторить'},
 {nChoose:'Navigation',nInternal:'Inside TALABOT',nExternal:'External navigation',nWeb:'Web link',nApp:'Open app',nHint:'If the app is missing or did not open, use the browser link. You can choose another map.',nIdle:'Choose Inside TALABOT to start routing',nTracking:'Tracking only · arrival time unavailable',nLoading:'Checking navigation…',nQuota:'Route allowance exhausted',nDisabled:'Road navigation disabled',nUnavailable:'Route unavailable',nGps:'No fresh accurate location',nOffRoute:'Off route · recalculating',nNoPin:'Exact destination coordinates missing',nFollow:'Follow me',nTurn:'Maneuver in',nRemaining:'Estimated remaining',nClose:'Close',nUpdated:'Route calculated',nFix:'Position',nRetry:'Retry'});
 let config=null,configAt=0,configFlight=null,epoch=0,currentKey='',route=null,flight=null,lastAsk=0,retryAt=0,offRouteSince=0;
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
     const stamp=v=>new Date(v).toLocaleTimeString(TLB.lang()==='ru'?'ru-RU':'en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
     el.textContent=t('nRemaining')+': '+(detail.remainingM/1000).toFixed(1)+' км · ~'+Math.max(1,Math.round(detail.remainingS/60))+' мин'+(detail.step?.instruction?' · '+t('nTurn')+' '+Math.round(detail.turnDistanceM)+' м: '+detail.step.instruction:'')+' · '+t('nUpdated')+' '+stamp(detail.calculatedAt)+' · '+t('nFix')+' '+stamp(detail.fixAt);
   }else{const k=reason==='not_started'?'nIdle':reason==='external'?'nExternal':reason==='quota'?'nQuota':reason==='disabled'?'nDisabled':reason==='gps_unavailable'?'nGps':reason==='off_route'?'nOffRoute':reason==='no_pin'?'nNoPin':'nUnavailable';el.textContent=t(k)+' · '+t('nTracking');}
 }
 function renderRoute(){
   if(!ready())return;
   if(!DM.__route)DM.__route=L.layerGroup().addTo(DM);DM.__route.clearLayers();
   if(mode==='internal'&&route){
     if(DM.__l)DM.__l.eachLayer(l=>{if(l instanceof L.Polyline&&!(l instanceof L.Polygon))DM.__l.removeLayer(l);});
     L.polyline(route.coords,{color:'#f1511b',weight:5,interactive:false,className:'a-route'}).addTo(DM.__route);
     if(DM.attributionControl&&DM.__navAttr!==route.attribution){if(DM.__navAttr)DM.attributionControl.removeAttribution(DM.__navAttr);DM.__navAttr=route.attribution;DM.attributionControl.addAttribution(DM.__navAttr);}
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
 async function loadLinks(){
   const x=task(),to=x&&target(x),k=x&&M.key(x,stage(x),to);if(!k)return;
   if(linksFlight)return linksFlight;
   linksFlight=TLB.navigation({op:'links',to}).then(r=>{const y=task();if(y&&M.key(y,stage(y),target(y))===k){linksKey=k;links=Array.isArray(r.links)?r.links:[];if(r.config){config=r.config;configAt=Date.now();}if(open)render();}}).finally(()=>{linksFlight=null;});return linksFlight;
 }
 window.aNavigationOpen=function(){open=true;links=[];linksKey='';render();policy(true).then(()=>loadLinks()).then(()=>{if(open)render();});};
 window.aNavigationClose=function(){open=false;render();};
 window.aNavigationInside=function(){open=false;chosen=true;following=true;retryAt=0;lastAsk=0;render();const x=task();if(x)update(x);};
 window.aNavigationExternal=function(){if(flight)flight.ctl.abort();chosen=false;mode='external';detail=null;route=null;epoch++;clearLine();label();};
 window.aNavigationFollow=function(){following=true;const x=task();if(x)update(x);};
 const oldModal=modal;
 modal=function(){
   if(!open||chatOpen||CXL||DV)return oldModal();
   const x=task(),to=x&&target(x),k=x&&M.key(x,stage(x),to);
   const safeLink=u=>typeof u==='string'&&/^(https:\/\/(www\.google\.com\/maps\/dir\/|yandex\.ru\/maps\/|2gis\.ru\/directions\/)|yandexmaps:\/\/maps\.yandex\.com\/)/.test(u);
   const list=linksKey===k?links.filter(v=>config?.external&&config.providers.includes(v.id)&&safeLink(v.app)&&safeLink(v.web)):[];
   return '<div class="ov a-aux" onclick="aNavigationClose()"><div class="md" role="dialog" aria-modal="true" aria-label="'+t('nChoose')+'" onclick="event.stopPropagation()"><h2>'+t('nChoose')+'</h2>'+(!to?'<p>'+t('nNoPin')+'</p>':'<p>'+esc(stage(x)>=3?x.address:x.store)+'</p>')+
    (to&&config?.mode==='internal'?'<button type="button" class="b" onclick="aNavigationInside()">'+t('nInternal')+'</button>':'<p role="status">'+t('nTracking')+'</p>')+
    '<h3>'+t('nExternal')+'</h3>'+list.map(v=>'<section class="n-provider"><b>'+esc(v.name)+'</b><div><a class="b s" href="'+esc(v.app)+'" target="_blank" rel="noopener noreferrer" onclick="aNavigationExternal()">'+t('nApp')+'</a><a class="b s" href="'+esc(v.web)+'" target="_blank" rel="noopener noreferrer" onclick="aNavigationExternal()">'+t('nWeb')+'</a></div></section>').join('')+
    (!config?'<p>'+t('nUnavailable')+'</p>':!list.length&&to?'<p>'+t('nDisabled')+'</p>':'')+'<p class="xs">'+t('nHint')+'</p><button type="button" class="b s" onclick="aNavigationClose()">'+t('nClose')+'</button></div></div>';
 };
 const inner=mapUpd;mapUpd=function(x,force){const v=inner.apply(this,arguments);if(x)update(x);return v;};
 document.addEventListener('visibilitychange',()=>{if(document.hidden){reset();configAt=0;links=[];linksKey='';open=false;}else policy(true).then(()=>{const x=task();if(x)update(x);});});
 window.addEventListener('pagehide',()=>reset());
 // Bounded lifecycle tick: stops provider requests off the mission; checks policy/staleness without creating a GPS watch.
 setInterval(()=>{const x=task();if(!x||document.hidden){if(currentKey)reset();return;}update(x);},1000);
 const css=document.createElement('style');css.textContent='.n-provider{margin:12px 0}.n-provider>div{display:flex;gap:8px;margin-top:6px}.n-provider a{min-height:44px;flex:1;font-size:13px}.a-map-state{max-width:calc(100% - 32px);white-space:normal}.a-tools .a-navigation{border:1px solid #ffd8c3;color:inherit;font:inherit;cursor:pointer}';document.head.appendChild(css);
 window.__routeLayer={state:()=>({key:currentKey,hasRoute:!!route,mode,reason,inflight:!!flight,following}),refreshPolicy:()=>policy(true)};
})();
