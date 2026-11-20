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
    .sort((a,b)=>(+a.sort||0)-(+b.sort||0)).map(b=>({id:b.id,label:b.title,picture:'',tone:'managed',image:b.image_url,action:'',fallback:false}));
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
  {id:'plov',test:/плов|pilaf|plov/i,art:'basket',name:'ad30Plov'},
  {id:'burger',test:/бургер|burger/i,art:'hamburger',name:'ad30Burgers'},
  {id:'pizza',test:/пицц|pizza/i,art:'pizza',name:'ad30Pizza'},
  {id:'shawarma',test:/шаурм|shawarma/i,art:'bread',name:'ad30Shawarma'},
  {id:'sushi',test:/суши|sushi/i,art:'sushi',name:'ad30Sushi'},
  {id:'dessert',test:/десерт|сладост|торт|dessert|cake/i,art:'shortcake',name:'ad30Desserts'},
  {id:'drinks',test:/напитк|drink|beverage|сок|juice/i,art:'basket',name:'ad30Drinks'}
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
      if(!seen.has(id))seen.set(id,{id,title:match?t(match.name):raw,art:match?match.art:'basket',image:'',rank:seen.size,stores:new Set()});
      seen.get(id).stores.add(store.id);
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
  return [...seen.values()].sort((a,b)=>a.rank-b.rank);
}
function cuisineRail(){
  const types=cuisineSource();if(!types.length)return '';
  return '<div class="ad30-cuisines" aria-label="'+esc(t('sections'))+'">'
    +types.map(c=>'<button type="button" class="ad30-cuisine'+(chosenCuisine===c.id?' on':'')+'" aria-pressed="'+(chosenCuisine===c.id)+'" '
      +'onclick="TALABOT_RESTAURANTS_BRIEF30.cuisine('+esc(JSON.stringify(c.id))+')">'
      +'<span class="ad30-cuisine-circle"><img src="'+esc(c.image||A3(c.art))+'" alt="" loading="lazy" onerror="this.remove()"></span>'
      +'<span class="ad30-cuisine-label">'+esc(c.title)+'</span></button>').join('')
    +'</div>';
}
function toggleCuisine(id){
  chosenCuisine=chosenCuisine===id?'':id;render();
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
  list=rankedSearch(list);
  return list.length?list.map(({s,h,sponsored})=>d6SRow(s,h,mine[s.n]||null,sponsored)).join(''):
    emptyV(t('noRes'),t('emNoResS'),'','search');
}
function renderRestaurants(){
  return ad30Header(curAddr())+search()+rail()+againRail()
    +'<section class="ad30-list"><h2>'+esc(t('ad30All'))+'</h2>'+cuisineRail()+'<div class="pg c01-list-content">'+rows()+'</div></section>';
}
window.TALABOT_RESTAURANTS_BRIEF30={
  render:renderRestaurants,
  banner:function(id){bannerGo(id)},
  cuisine:toggleCuisine
};
})();
