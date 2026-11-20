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
function rows(){
  const q=String(S.cq||'').trim().toLowerCase(),mine=d6Mine();
  let list=matches(TLB.allMenus(true),q).filter(({s})=>s.c==='rest');
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
  return ad30Header(curAddr())+search()+rail()
    +'<section class="ad30-list"><h2>'+esc(t('ad30All'))+'</h2><div class="pg c01-list-content">'+rows()+'</div></section>';
}
window.TALABOT_RESTAURANTS_BRIEF30={
  render:renderRestaurants,
  banner:function(id){bannerGo(id)}
};
})();
