/* TALABOT BRIEF-30 — RESTAURANTS CATEGORY ONLY. No mutations of Home or core. */
(function(){
'use strict';
TLB.addDict({
  ad30Offers:'Скидки',ad30Free:'Бесплатная доставка',ad30ForYou:'Для вас',
  ad30All:'Все рестораны',ad30Again:'Заказать снова'
},{
  ad30Offers:'Discounts',ad30Free:'Free delivery',ad30ForYou:'For you',
  ad30All:'All restaurants',ad30Again:'Order again'
});
/* AG-03: this rail contains advertisements with their own destinations. */
function bannerItems(){return bannersAt('restaurants')}
function rail(){const banners=bannerItems();return banners.length?'<div class="ad30-banner-row" data-banner-rail="restaurants" aria-label="'+esc(t('d6Partn'))+'">'+banners.map(b=>bannerMarkup(b,'ad30-banner ad30-tone-managed','restaurants')).join('')+'</div>':''}
function search(){
  return '<div class="d6-sf ad30-search" onclick="if(event.target===this)document.getElementById(\'cq\').focus()">'
  +ico('search',20)+'<input type="search" id="cq" value="'+esc(S.cq||'')+'" placeholder="'+esc(ad30Hint())+'" '
  +'oninput="S.cq=this.value;render()" enterkeyhint="search"></div>';
}

/* AD-03: repeat-order carousel of actual delivered restaurant purchases only. */
TLB.addDict({ad30Deal:'Акция'},{ad30Deal:'Offer'});
function againRail(){
  const mine=d6Mine(),last=STORES.filter(s=>s.c==='rest'&&Object.hasOwn(mine,s.n))
    .sort((a,b)=>mine[b.n]-mine[a.n]);
  if(!last.length)return '';
  return '<section class="ad30-again"><h2>'+esc(t('ad30Again'))+'</h2><div class="ad30-again-rail">'
    +last.map(s=>{
      const open=TLB.isOpen(s.n),deal=s.disc>0?'−'+s.disc+'%':hasFreeDelivery(s)?t('ad30Deal'):'';
      const badge=deal?'<span class="ad30-again-badge">'+esc(deal)+'</span>':'';
      return '<button class="ad30-again-item'+(open?'':' closed')+'" type="button" '
        +(open?'onclick="openN('+esc(JSON.stringify(s.n))+')"':'disabled aria-disabled="true"')
        +' aria-label="'+esc(s.n)+'"><span class="ad30-again-logo">'+homeRestaurantImage(s)+'</span>'
        +badge+'<span class="ad30-again-name">'+esc(s.n)+'</span></button>';
    }).join('')+'</div></section>';
}


/* AD-04: cuisine categories derive from existing menu sections and optional admin imagery.
   No fabricated categories: only categories attached to actual menu items appear. */
TLB.addDict({
  ad30Plov:'Плов',ad30Burgers:'Бургеры',ad30Pizza:'Пицца',ad30Shawarma:'Шаурма',
  ad30Sushi:'Суши',ad30Desserts:'Десерты',ad30Drinks:'Напитки'
},{
  ad30Plov:'Pilaf',ad30Burgers:'Burgers',ad30Pizza:'Pizza',ad30Shawarma:'Shawarma',
  ad30Sushi:'Sushi',ad30Desserts:'Desserts',ad30Drinks:'Drinks'
});
const CUISINE_MAP=[
  {id:'plov',test:/плов|pilaf|plov/i,art:'',name:'ad30Plov'},
  {id:'burger',test:/бургер|burger/i,art:'hamburger',name:'ad30Burgers'},
  {id:'pizza',test:/пицц|pizza/i,art:'pizza',name:'ad30Pizza'},
  {id:'shawarma',test:/шаурм|shawarma/i,art:'',name:'ad30Shawarma'},
  {id:'sushi',test:/суши|sushi/i,art:'sushi',name:'ad30Sushi'},
  {id:'dessert',test:/десерт|сладост|торт|dessert|cake/i,art:'shortcake',name:'ad30Desserts'},
  {id:'drinks',test:/напитк|drink|beverage|сок|juice/i,art:'',name:'ad30Drinks'}
];
let chosenCuisine='';
function cuisineSource(){
  const menus=TLB.allMenus(true)||{},seen=new Map();
  for(const store of STORES){
    if(store.c!=='rest')continue;
    for(const item of menus[store.n]||[]){
      const raw=String(item.section||'').trim();
      if(!raw)continue;
      const match=CUISINE_MAP.find(c=>c.test.test(raw));
      const id=match?match.id:'section:'+raw.toLocaleLowerCase();
      if(!seen.has(id))seen.set(id,{id,title:match?t(match.name):raw,art:match?match.art:'',image:'',photos:[],rank:seen.size,stores:new Set()});
      const cuisine=seen.get(id);
      cuisine.stores.add(store.id);
      // allMenus() exposes approved menu image_url values as item.image.
      if(typeof item.image==='string'&&item.image.trim()&&!cuisine.photos.includes(item.image.trim()))cuisine.photos.push(item.image.trim());
    }
  }
  const configured=typeof TLB.restaurantCuisines==='function'?TLB.restaurantCuisines():[];
  if(Array.isArray(configured))for(const item of configured){
    if(!item||!seen.has(item.id))continue;
    const c=seen.get(item.id);
    const title=TLB.lang()==='en'?item.name_en:item.name_ru;
    if(typeof title==='string'&&title.trim())c.title=title.trim().slice(0,32);
    if(typeof item.image_url==='string'&&item.image_url)c.image=item.image_url;
    if(Number.isFinite(+item.sort))c.rank=+item.sort;
  }
  const used=new Set();
  return [...seen.values()].sort((a,b)=>a.rank-b.rank).map(c=>{
    const art=c.art?A3(c.art):'';
    // Keep configured artwork, otherwise semantic 3D art, then the first dish
    // photo in this cuisine. Missing/duplicate imagery stays a text filter.
    const source=[c.image,art,...c.photos].find(src=>src&&!used.has(src)&&!/(^|\/)assets\/3d\/basket\.webp(?:[?#]|$)/i.test(src))||'';
    if(source)used.add(source);
    return {...c,image:source,photo:!!source&&source!==art};
  });
}
function cuisineRail(){
  const types=cuisineSource();if(!types.length)return '';
  return '<div class="ad30-cuisines" aria-label="'+esc(t('sections'))+'">'
    +types.map(c=>'<button type="button" class="ad30-cuisine'+(chosenCuisine===c.id?' on':'')+(c.image?'':' no-image')+'" aria-pressed="'+(chosenCuisine===c.id)+'" '
      +'onclick="TALABOT_RESTAURANTS_BRIEF30.cuisine('+esc(JSON.stringify(c.id))+')">'
      +(c.image?'<span class="ad30-cuisine-circle'+(c.photo?' photo':'')+'"><img src="'+esc(c.image)+'" alt="" loading="lazy" onerror="this.closest(\'button\').classList.add(\'no-image\');this.parentElement.remove()"></span>':'')
      +'<span class="ad30-cuisine-label">'+esc(c.title)+'</span></button>').join('')
    +'</div>';
}
function toggleCuisine(id){
  chosenCuisine=chosenCuisine===id?'':id;render();revealEmptyFilter();
}


/* AD-05: multi-select independent filters and deterministic non-invented data sorting. */
TLB.addDict({
  ad30Sort:'Сортировать',ad30Rec:'Рекомендуемые',ad30RateSort:'По рейтингу',
  ad30FastSort:'Самые быстрые',ad30CheapSort:'Дешёвая доставка',
  ad30Discount:'Скидки',ad30Rate:'Рейтинг 4.0+',
  ad30Quick:'Быстрая доставка',ad30NoFee:'Бесплатная доставка',
  ad30NoFilterResults:'Нет ресторанов по этому фильтру',ad30ResetFilters:'Сбросить фильтры'
},{
  ad30Sort:'Sort',ad30Rec:'Recommended',ad30RateSort:'By rating',
  ad30FastSort:'Fastest',ad30CheapSort:'Lowest delivery fee',
  ad30Discount:'Discounts',ad30Rate:'Rating 4.0+',
  ad30Quick:'Fast delivery',ad30NoFee:'Free delivery',
  ad30NoFilterResults:'No restaurants match this filter',ad30ResetFilters:'Reset filters'
});
let sortMode='recommended',sortOpen=false,localFilter={disc:false,rate:false,fast:false,free:false},legacyRoute='';
function syncLegacyRoute(){
  const route=S.srt==='disc'||S.srt==='free'?S.srt:'';
  if(legacyRoute===route)return;
  if(route){localFilter={disc:false,rate:false,fast:false,free:false};localFilter[route]=true;}
  else if(legacyRoute){localFilter={disc:false,rate:false,fast:false,free:false};}
  legacyRoute=route;
}
function setSort(mode){
  if(!['recommended','rating','fastest','cheap'].includes(mode))return;
  sortMode=mode;sortOpen=false;render();
}
function toggleFilter(key){
  if(!Object.hasOwn(localFilter,key))return;
  syncLegacyRoute();localFilter[key]=!localFilter[key];
  S.srt='';S.fo=false;legacyRoute='';render();revealEmptyFilter();
}
function resetFilters(){
  chosenCuisine='';sortMode='recommended';sortOpen=false;
  localFilter={disc:false,rate:false,fast:false,free:false};legacyRoute='';
  S.cq='';S.srt='';S.fo=false;render();
}
function emptyFilter(){
  return '<div class="empty ad30-empty"><span class="eic" aria-hidden="true">'+ico('search',22)+'</span>'
    +'<p role="status">'+esc(t('ad30NoFilterResults'))+'</p>'
    +'<button type="button" class="btn s ad30-reset" onclick="TALABOT_RESTAURANTS_BRIEF30.reset()">'
    +esc(t('ad30ResetFilters'))+'</button></div>';
}
function revealEmptyFilter(){
  requestAnimationFrame(()=>{
    const empty=document.querySelector('#app .ad30-empty');
    if(!empty)return;
    let edge=innerHeight;
    for(const anchor of document.querySelectorAll('#app .nav,#app .bar'))edge=Math.min(edge,anchor.getBoundingClientRect().top);
    const covered=empty.getBoundingClientRect().bottom-(edge-12);
    if(covered>0)window.scrollBy(0,Math.ceil(covered));
  });
}
function speedMinutes(s){
  const measured=TLB.speed?.(s.id);
  if(!measured||!(+measured.min>0))return null;
  const km=kmOf(s);
  return +measured.min+(km==null?10:Math.round(km*10)/10*3+5);
}
function sortAndFilter(list){
  syncLegacyRoute();
  let result=list.filter(({s})=>(!localFilter.disc||s.disc>0)
    &&(!localFilter.rate||s.rt>=4)
    &&(!localFilter.free||hasFreeDelivery(s))
    &&(!localFilter.fast||(speedMinutes(s)!=null&&speedMinutes(s)<=30)));
  const openOrder=(a,b)=>Number(TLB.isOpen(b.s.n))-Number(TLB.isOpen(a.s.n));
  const recommended=(a,b)=>((b.s.rt*Math.log(2+b.s.rc))-(a.s.rt*Math.log(2+a.s.rc)))||((kmOf(a.s)??99)-(kmOf(b.s)??99));
  const sorters={
    recommended:recommended,
    rating:(a,b)=>b.s.rt-a.s.rt||recommended(a,b),
    fastest:(a,b)=>(speedMinutes(a.s)??Infinity)-(speedMinutes(b.s)??Infinity)||recommended(a,b),
    cheap:(a,b)=>(Number.isFinite(a.s.fee)?a.s.fee:Infinity)-(Number.isFinite(b.s.fee)?b.s.fee:Infinity)||recommended(a,b)
  };
  return result.slice().sort((a,b)=>openOrder(a,b)||(sorters[sortMode]||recommended)(a,b));
}
function filtersView(){
  const button=(key,label)=>'<button type="button" class="ad30-filter'+(localFilter[key]?' on':'')+'" '
    +'aria-pressed="'+localFilter[key]+'" onclick="TALABOT_RESTAURANTS_BRIEF30.filter(\''+key+'\')">'+esc(t(label))+'</button>';
  const selected={recommended:'ad30Rec',rating:'ad30RateSort',fastest:'ad30FastSort',cheap:'ad30CheapSort'}[sortMode];
  return '<div class="ad30-filters"><button class="ad30-sort" type="button" '
    +'onclick="TALABOT_RESTAURANTS_BRIEF30.sortOpen()" aria-haspopup="dialog" aria-expanded="'+sortOpen+'" aria-label="'+esc(t('ad30Sort')+(sortMode==='recommended'?'':': '+t(selected)))+'">'
    +'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 19V5m-4 4 4-4 4 4M16 5v14m-4-4 4 4 4-4"/></svg>'
    +(sortMode==='recommended'?'':'<span class="ad30-sort-dot" aria-hidden="true"></span>')+'</button>'
    +button('disc','ad30Discount')+button('rate','ad30Rate')
    +button('fast','ad30Quick')+button('free','ad30NoFee')+'</div>';
}
function sortSheet(){
  if(!sortOpen)return '';
  const modes=[['recommended','ad30Rec'],['rating','ad30RateSort'],['fastest','ad30FastSort'],['cheap','ad30CheapSort']];
  return '<div class="ad30-sort-overlay" onclick="TALABOT_RESTAURANTS_BRIEF30.sortClose()" role="presentation">'
    +'<section class="ad30-sort-sheet" role="dialog" aria-modal="true" aria-labelledby="ad30-sort-title" onclick="event.stopPropagation()">'
    +'<div class="ad30-sort-header"><h2 id="ad30-sort-title">'+esc(t('ad30Sort'))+'</h2>'
    +'<button type="button" class="ad30-sort-x" aria-label="'+esc(t('back'))+'" onclick="TALABOT_RESTAURANTS_BRIEF30.sortClose()">'+ico('x',18)+'</button></div>'
    +modes.map(([id,key])=>'<button type="button" class="ad30-sort-choice'+(sortMode===id?' active':'')+'" '
        +'aria-pressed="'+(sortMode===id)+'" onclick="TALABOT_RESTAURANTS_BRIEF30.sort('+esc(JSON.stringify(id))+')">'
        +esc(t(key))+(sortMode===id?ico('check',17):'')+'</button>').join('')
    +'</section></div>';
}


/* AD-06: 96px logo-first list cards, with safe cover fallback and closed at end. */
function restaurantCard({s,h,sponsored}){
  const open=TLB.isOpen(s.n);
  const name=esc(s.n),logo=homeRestaurantImage(s);
  const photo='<span class="ad30-card-logo">'+(logo||'<span class="ad30-card-photo-empty"></span>')+heart(s)+'</span>';
  const meta=[d6Rt(s),etaOf(s)?'<span>'+esc(etaOf(s))+'</span>':'',
    '<span>'+esc(delTxt(s))+'</span>'].filter(Boolean).join('<span class="ad30-dot">·</span>');
  const hasPromo=s.disc>0||s.ft==='free'||s.ffd||s.fdm>0;
  const offer=hasPromo?'<span class="ad30-card-offer">'
    +esc(s.disc>0?'−'+s.disc+'%':s.ft==='free'?t('free'):s.ffd?t('freeFirst'):t('hFreeFromL').replace('{n}',s.fdm))
    +'</span>':'';
  return '<article class="ad30-card'+(open?'':' closed')+'" role="'+(open?'button':'group')+'" '
    +(open?'tabindex="0" '+storeTap(s)+' onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();openN('+esc(JSON.stringify(s.n))+')}"':'aria-disabled="true"')
    +'>'+photo+'<span class="ad30-card-copy"><strong class="ad30-card-name">'+name+'</strong>'
    +'<span class="ad30-card-meta">'+meta+'</span>'
    +(sponsored?homeAdBadge():'')+(h?'<span class="ad30-card-dish">'+esc(h.name)+'</span>':'')
    +offer+(!open?'<span class="ad30-card-closed">'+esc(t('closedStoreBadge'))+'</span>':'')
    +'</span></article>';
}

function rows(){
  const q=String(S.cq||'').trim().toLowerCase(),mine=d6Mine();
  let list=matches(TLB.allMenus(true),q).filter(({s})=>s.c==='rest');
  if(chosenCuisine){const allowed=cuisineSource().find(c=>c.id===chosenCuisine)?.stores;
    list=list.filter(({s})=>allowed&&allowed.has(s.id));}
  if(S.fo)list=list.filter(({s})=>TLB.isOpen(s.n));
  if(S.srt==='free')list=list.filter(({s})=>hasFreeDelivery(s));
  if(S.srt==='disc')list=list.filter(({s})=>s.disc>0);
  if(S.srt==='rate')list=list.slice().sort((a,b)=>b.s.rt-a.s.rt);
  if(S.srt==='mine')list=list.filter(({s})=>s.n in mine).sort((a,b)=>mine[b.s.n]-mine[a.s.n]);
  list=rankedSearch(sortAndFilter(list));
  const filtered=q||chosenCuisine||S.fo||['free','disc','mine'].includes(S.srt)||Object.values(localFilter).some(Boolean);
  return list.length?list.map(restaurantCard).join(''):
    filtered?emptyFilter():emptyV(t('noRes'),t('emNoResS'),'','search');
}

/* AD-07: W-10 sponsored ranking is the existing rankedSearch() contract.
   Floating campaign only exists when an explicit manager field is present. */
let lastFloatScroll=0,floatFrame=0,floatObserver=null,floatObserved=null;
function floatingCampaign(){
  const selected=bannersAt('restaurants').find(b=>{
    const cfg=bannerConfig(b);
    return (cfg.floating===true||b.placement==='restaurants_float')
      &&(cfg.action==='campaign'||cfg.campaign);
  });
  if(!selected)return '';
  const text=selected.presentation?.floating_text?.[TLB.lang()]
    ||selected.title||'';
  if(!text)return '';
  return '<button type="button" class="ad30-float" '
    +'onclick="TALABOT_RESTAURANTS_BRIEF30.banner('+esc(JSON.stringify(selected.id))+')" '
    +'aria-label="'+esc(text)+'"><img src="'+A3('party-popper')+'" alt="" width="22" height="22">'
    +'<span>'+esc(text)+'</span></button>';
}
function layoutFloatingCampaign(){
  const button=document.querySelector('#app .ad30-float');
  if(!button){floatObserver?.disconnect();floatObserver=null;floatObserved=null;return;}
  const nav=document.querySelector('#app .nav'),bar=document.querySelector('#app .bar');
  if(floatObserved!==button){
    floatObserver?.disconnect();floatObserved=button;
    if(window.ResizeObserver){
      floatObserver=new ResizeObserver(queueFloatingLayout);
      for(const anchor of [nav,bar])if(anchor)floatObserver.observe(anchor);
    }
  }
  button.classList.remove('ready');button.style.display='';
  const edge=Math.min(nav?nav.getBoundingClientRect().top:innerHeight,bar?bar.getBoundingClientRect().top:innerHeight);
  button.style.bottom=Math.max(12,innerHeight-edge+12)+'px';
  const width=button.offsetWidth,height=button.offsetHeight;
  // Campaign authors supply the short floating_text. Never cut its copy in UI;
  // oversized copy remains available in the regular campaign banner instead.
  if(width>innerWidth*.92+1||button.scrollWidth>button.clientWidth+1){button.style.display='none';return;}
  const content=document.querySelector('#app .ad30-list .c01-list-content');
  content?.style.setProperty('--ad30-float-reserve',(height+12)+'px');
  const box={left:(innerWidth-width)/2,right:(innerWidth+width)/2,bottom:edge-12,top:edge-12-height};
  // Bottom padding gives scrolling room; this first-paint/scroll gate also
  // protects text mid-list without changing the accepted window scroll model.
  const collision=[...document.querySelectorAll('#app .ad30-card-copy,#app .ad30-list .empty')].some(node=>{
    const r=node.getBoundingClientRect();
    return box.left<r.right+4&&box.right>r.left-4&&box.top<r.bottom+4&&box.bottom>r.top-4;
  });
  button.classList.toggle('occluded',collision);button.classList.add('ready');
}
function queueFloatingLayout(){
  if(floatFrame)return;
  floatFrame=requestAnimationFrame(()=>{floatFrame=0;layoutFloatingCampaign()});
}
function onRestaurantScroll(){
  if(S.v!=='cat'||S.catKey!=='rest'){lastFloatScroll=scrollY||0;return;}
  const button=document.querySelector('#app .ad30-float');
  if(!button)return;
  const y=window.scrollY||document.documentElement.scrollTop||0;
  const diff=y-lastFloatScroll;
  if(Math.abs(diff)>8){button.classList.toggle('hidden',diff>0&&y>60);lastFloatScroll=y;}
  queueFloatingLayout();
}
window.addEventListener('scroll',onRestaurantScroll,{passive:true});
window.addEventListener('resize',queueFloatingLayout,{passive:true});
window.visualViewport?.addEventListener('resize',queueFloatingLayout,{passive:true});

function renderRestaurants(){
  lastFloatScroll=window.scrollY||0;
  queueFloatingLayout();
  return ad30Header(curAddr())+search()+rail()+againRail()
    +'<section class="ad30-list"><h2>'+esc(t('ad30All'))+'</h2>'+cuisineRail()+filtersView()+'<div class="pg c01-list-content">'+rows()+'</div></section>'+sortSheet()+floatingCampaign();
}
window.TALABOT_RESTAURANTS_BRIEF30={
  render:renderRestaurants,
  banner:function(id){bannerGo(id)},
  cuisine:toggleCuisine,
  filter:toggleFilter,
  reset:resetFilters,
  sort:setSort,
  sortOpen:function(){sortOpen=true;render()},
  sortClose:function(){sortOpen=false;render()}
};
})();
