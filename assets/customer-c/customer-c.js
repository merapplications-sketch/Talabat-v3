/* Local proposed delta. No mock data here; consumes the current customer API only. */
(function(){
 'use strict';
 TLB.addDict({cMapTitle:'Курьер в пути',cMapLoading:'Получаем местоположение…',cMapNone:'Местоположение курьера недоступно',cMapAge:'Обновлено {n} мин назад',cMapUnavailable:'Карта недоступна',cMapRetry:'Повторить загрузку карты',cCurrent:'Текущий заказ',cCurrentMany:'Текущие заказы',cOpen:'Открыть'},
 {cMapTitle:'Courier on the way',cMapLoading:'Getting location…',cMapNone:'Courier location unavailable',cMapAge:'Updated {n} min ago',cMapUnavailable:'Map unavailable',cMapRetry:'Retry map',cCurrent:'Current order',cCurrentMany:'Current orders',cOpen:'Open'});
 const ACTIVE=['pending','preparing','ready','pickedup'];
 let root=null,map=null,marker=null,tiles=null,tileReady=false,tileError=false,loadTimer=0,pollTimer=0,deadline=0,ageTimer=0,id=null,epoch=0,busy=false,point=null,lastCall=0,phase='loading',mapLoading=false,layoutObserver=null,basePadding='',mapEpoch=0,controller=null;
 function eligible(){if(!ME?.phone)return null;const o=S.v==='track'&&TLB.order(S.tid);return o&&o.status==='pickedup'&&!document.hidden?String(o.id):null}
 function valid(p){return p&&p.lat!==null&&p.lng!==null&&Number.isFinite(p.lat)&&Math.abs(p.lat)<=90&&Number.isFinite(p.lng)&&Math.abs(p.lng)<=180&&Number.isFinite(p.at)&&p.at>0&&p.at<=Date.now()}
 function mapDestroy(){mapEpoch++;clearTimeout(loadTimer);loadTimer=0;if(map){map.remove();map=null}marker=null;tiles=null;tileReady=false;tileError=false;mapLoading=false}
 function reset(){epoch++;controller?.abort();controller=null;clearTimeout(pollTimer);clearTimeout(deadline);clearInterval(ageTimer);mapDestroy();root?.remove();root=null;point=null;id=null;busy=false;lastCall=0;phase='loading'}
 function create(){root=document.createElement('section');root.className='c-track';root.dataset.c='C1';root.setAttribute('aria-label',t('cMapTitle'));root.innerHTML='<h3></h3><p class="c-track-age" aria-live="polite"></p><div class="c-track-map" role="img"></div><p class="c-track-note" role="status"></p><button type="button" class="c-track-retry" hidden></button>';root.querySelector('button').onclick=()=>{mapDestroy();draw()}}
 function draw(){if(!root)return;root.querySelector('h3').textContent=t('cMapTitle');const area=root.querySelector('.c-track-map'),note=root.querySelector('.c-track-note'),retry=root.querySelector('button');
  root.querySelector('.c-track-age').textContent=phase==='loading'&&!point?t('cMapLoading'):point?t('cMapAge').replace('{n}',Math.max(0,Math.floor((Date.now()-point.at)/60000))):t('cMapNone');
  area.hidden=!point;area.setAttribute('aria-label',t('cMapTitle'));note.hidden=!point||!tileError;note.textContent=t('cMapUnavailable');retry.textContent=t('cMapRetry');retry.hidden=!point||!tileError;
  if(!point){mapDestroy();return}if(map){marker?.setLatLng([point.lat,point.lng]);map.setView([point.lat,point.lng],map.getZoom(),{animate:false});return}if(mapLoading||tileError)return;
  mapLoading=true;const token=epoch,generation=mapEpoch,host=root;loadTimer=setTimeout(()=>{if(epoch===token&&root===host&&!tileReady){tileError=true;mapLoading=false;mapDestroy();tileError=true;drawError()}},8000);
  TLB.leaflet(()=>{if(epoch!==token||generation!==mapEpoch||root!==host||!point||eligible()!==id)return;try{
   map=L.map(area,{zoomControl:false,scrollWheelZoom:false,dragging:false,touchZoom:false,doubleClickZoom:false,boxZoom:false,keyboard:false,tap:false}).setView([point.lat,point.lng],15);
   tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap',referrerPolicy:'strict-origin-when-cross-origin'}).addTo(map);
   tiles.on('tileload',()=>{if(epoch!==token||generation!==mapEpoch)return;clearTimeout(loadTimer);tileReady=true;tileError=false;drawError()});tiles.on('tileerror',()=>{if(epoch!==token||generation!==mapEpoch)return;tileError=true;drawError()});
   marker=L.marker([point.lat,point.lng],{icon:L.divIcon({className:'c-track-pin',html:'<span>'+ico('bike',20)+'</span>',iconSize:[36,36],iconAnchor:[18,18]})}).addTo(map);mapLoading=false;
  }catch(e){clearTimeout(loadTimer);mapDestroy();tileError=true;drawError()}})
 }
 function drawError(){if(!root)return;const note=root.querySelector('.c-track-note'),retry=root.querySelector('button');note.textContent=t('cMapUnavailable');note.hidden=!point||!tileError;retry.textContent=t('cMapRetry');retry.hidden=!point||!tileError}
 async function request(){if(!id||busy||eligible()!==id)return;busy=true;lastCall=Date.now();const token=epoch,order=id;let value=null,timedOut=false;
  const active=controller=new AbortController();let release;
  const stopped=new Promise(resolve=>{release=()=>resolve(null);active.signal.addEventListener('abort',release,{once:true})});
  deadline=setTimeout(()=>{if(token!==epoch)return;timedOut=true;active.abort()},10000);
  try{value=await Promise.race([TLB.courierPosition(order,active.signal),stopped])}catch(e){}finally{active.signal.removeEventListener('abort',release);if(token===epoch){clearTimeout(deadline);busy=false;if(controller===active)controller=null}}
  if(token!==epoch||eligible()!==order)return;point=!timedOut&&valid(value)?value:null;phase='settled';draw();pollTimer=setTimeout(request,Math.max(0,15000-(Date.now()-lastCall)));
 }
 function current(){document.body.style.paddingBottom=basePadding;document.querySelector('.c-current')?.remove();layoutObserver?.disconnect();layoutObserver=null;const views=['home','cat','menu','fav','promo','offer','wallet','me'];
  if(!ME?.phone||!views.includes(S.v)||S.sh||S.sheetAddr||S.ro||S.rep||S.hcf||S.ntf||S.hfs||S.sinfo||S.cxn||TLB.me()?.banned)return;
  const orders=TLB.orders().filter(o=>ACTIVE.includes(o.status));if(!orders.length)return;
  const b=document.createElement('button');b.type='button';b.className='c-current';b.dataset.c='C2';const o=orders[0];
  b.innerHTML='<span class="c-current-ic">'+ico('receipt',20)+'</span><span class="c-current-txt"><strong></strong><small></small></span><span class="c-current-open">'+esc(t('cOpen'))+ico('chev',16)+'</span>';
  b.querySelector('strong').textContent=orders.length===1?t('cCurrent')+' · #'+o.id:t('cCurrentMany')+' · '+orders.length;
  b.querySelector('small').textContent=orders.length===1?t('trk_'+o.status):Array.from(new Set(orders.map(x=>t('trk_'+x.status)))).join(' · ');
  b.onclick=()=>orders.length===1?go('track',{tid:o.id}):go('orders',{ofl:'act'});document.getElementById('app').appendChild(b);
  const base=basePadding||'0px';
  const layout=()=>{if(!b.isConnected)return;const nav=document.querySelector('.nav'),bar=document.querySelector('.bar');let edge=nav?nav.getBoundingClientRect().top:innerHeight; if(bar)edge=Math.min(edge,bar.getBoundingClientRect().top);b.style.bottom=Math.max(8,innerHeight-edge+8)+'px';document.body.style.paddingBottom='calc('+base+' + '+(b.getBoundingClientRect().height+16)+'px)'};
  layout();if(window.ResizeObserver){layoutObserver=new ResizeObserver(layout);layoutObserver.observe(b);for(const el of document.querySelectorAll('.nav,.bar'))layoutObserver.observe(el)}
 }
 function sync(){current();const wanted=eligible();if(!wanted){if(id||root)reset();return}if(wanted!==id){reset();id=wanted;create();ageTimer=setInterval(()=>{if(eligible()!==id){reset();return}if(point)draw()},60000)}
  const summary=document.querySelector('.d6-order-summary');if(summary&&root){summary.after(root);map?.invalidateSize({pan:false})}draw();if(!busy&&!lastCall)request();
 }
 const original=render;render=function(){const oldY=scrollY;if(root?.isConnected)root.remove();original.apply(this,arguments);basePadding=document.body.style.paddingBottom;sync();if(scrollY!==oldY)scrollTo(0,oldY)};
 document.addEventListener('visibilitychange',()=>{if(document.hidden){reset()}else sync()});window.addEventListener('pagehide',reset);window.addEventListener('pageshow',()=>{if(!document.hidden)sync()});window.addEventListener('resize',()=>{current();map?.invalidateSize({pan:false})});
 // Existing state was rendered before this optional module loaded.
 if(typeof ME!=='undefined'&&ME?.phone)render();
})();
