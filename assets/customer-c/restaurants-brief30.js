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
function bannerItems(){
  const defaults=[
    {id:'disc',label:t('ad30Offers'),picture:'fire',tone:'disc',action:"openBannerList('disc')"},
    {id:'free',label:t('ad30Free'),picture:'motor-scooter',tone:'free',action:"openBannerList('free')"},
    {id:'you',label:t('ad30ForYou'),picture:'hamburger',tone:'you',action:"openBannerList('category','rest')"}
  ].map(x=>({...x,fallback:true}));
  const managed=TLB.banners().filter(b=>bannerConfig(b).audience==='restaurants')
    .sort((a,b)=>(+a.sort||0)-(+b.sort||0)).map(b=>({id:b.id,label:b.title,picture:'hamburger',tone:'managed',image:b.image_url,action:'',fallback:false}));
  return defaults.concat(managed);
}
function rail(){
  return '<div class="ad30-banner-row" aria-label="'+esc(t('d6Partn'))+'">'+bannerItems().map(b=>{
    const tap=b.fallback?'onclick="'+b.action+'"':
      'onclick="TALABOT_RESTAURANTS_BRIEF30.banner('+esc(JSON.stringify(b.id))+')"';
    const art=b.image
      ?'<img class="ad30-banner-img" src="'+esc(b.image)+'" alt="" loading="lazy" onerror="this.remove()">'
      :'<img class="ad30-banner-art" src="'+A3(b.picture)+'" alt="" loading="lazy">';
    return '<button type="button" class="ad30-banner ad30-tone-'+b.tone+'" '+tap+' aria-label="'+esc(b.label)+'">'+art+'<b>'+esc(b.label)+'</b></button>';
  }).join('')+'</div>';
}
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
  chosenCuisine=chosenCuisine===id?'':id;render();
}


/* AD-05: multi-select independent filters and deterministic non-invented data sorting. */
TLB.addDict({
  ad30Sort:'Сортировать',ad30Rec:'Рекомендуемые',ad30RateSort:'По рейтингу',
  ad30FastSort:'Самые быстрые',ad30CheapSort:'Дешёвая доставка',
  ad30Discount:'Скидки',ad30Rate:'Рейтинг 4.0+',
  ad30Quick:'Быстрая доставка',ad30NoFee:'Бесплатная доставка'
},{
  ad30Sort:'Sort',ad30Rec:'Recommended',ad30RateSort:'By rating',
  ad30FastSort:'Fastest',ad30CheapSort:'Lowest delivery fee',
  ad30Discount:'Discounts',ad30Rate:'Rating 4.0+',
  ad30Quick:'Fast delivery',ad30NoFee:'Free delivery'
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
  S.srt='';S.fo=false;legacyRoute='';render();
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
    +'onclick="TALABOT_RESTAURANTS_BRIEF30.sortOpen()" aria-haspopup="dialog">'
    +esc(t('ad30Sort'))+' '+ico('down',14)+'</button>'
    +'<span class="ad30-current-sort">'+esc(t(selected))+'</span>'
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
  return list.length?list.map(restaurantCard).join(''):
    emptyV(t('noRes'),t('emNoResS'),'','search');
}

/* AD-07: W-10 sponsored ranking is the existing rankedSearch() contract.
   Floating campaign only exists when an explicit manager field is present. */
let lastFloatScroll=0;
function floatingCampaign(){
  const selected=TLB.banners().find(b=>{
    const cfg=bannerConfig(b);
    return cfg.audience==='restaurants'&&(cfg.floating===true||b.placement==='restaurants_float')
      &&(cfg.action==='campaign'||cfg.campaign);
  });
  if(!selected)return '';
  const text=selected.presentation?.floating_text?.[TLB.lang()]
    ||selected.title||'';
  if(!text)return '';
  return '<button type="button" class="ad30-float'+(cartCount()?' with-cart':'')+'" '
    +'onclick="TALABOT_RESTAURANTS_BRIEF30.banner('+esc(JSON.stringify(selected.id))+')" '
    +'aria-label="'+esc(text)+'"><img src="'+A3('party-popper')+'" alt="" width="22" height="22">'
    +'<span>'+esc(text)+'</span></button>';
}
function onRestaurantScroll(){
  if(S.v!=='cat'||S.catKey!=='rest'){lastFloatScroll=scrollY||0;return;}
  const button=document.querySelector('#app .ad30-float');
  if(!button)return;
  const y=window.scrollY||document.documentElement.scrollTop||0;
  const diff=y-lastFloatScroll;
  if(Math.abs(diff)>8){button.classList.toggle('hidden',diff>0&&y>60);lastFloatScroll=y;}
}
window.addEventListener('scroll',onRestaurantScroll,{passive:true});

function renderRestaurants(){
  return ad30Header(curAddr())+search()+rail()+againRail()
    +'<section class="ad30-list"><h2>'+esc(t('ad30All'))+'</h2>'+cuisineRail()+filtersView()+'<div class="pg c01-list-content">'+rows()+'</div></section>'+sortSheet()+floatingCampaign();
}
window.TALABOT_RESTAURANTS_BRIEF30={
  render:renderRestaurants,
  banner:function(id){bannerGo(id)},
  cuisine:toggleCuisine,
  filter:toggleFilter,
  sort:setSort,
  sortOpen:function(){sortOpen=true;render()},
  sortClose:function(){sortOpen=false;render()}
};
})();
