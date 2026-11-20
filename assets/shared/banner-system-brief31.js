/* BRIEF-31: presentation of existing banner rows; no database or core mutation. */
(function(root){
  'use strict';
  const places=Object.freeze(['home_main','home_side','dont_miss','home_bottom','orders','restaurants','checkout']);
  const config=b=>b&&b.presentation&&typeof b.presentation==='object'&&!Array.isArray(b.presentation)?b.presentation:{};
  const text=x=>typeof x==='string'?x.trim():'';
  function placements(b,settings={}){
    const p=config(b);
    if(Array.isArray(p.placements))return [...new Set(p.placements.filter(x=>places.includes(x)))];
    if(p.audience==='orders')return ['orders'];
    if(p.audience==='restaurants')return ['restaurants'];
    if(b.placement==='bottom')return ['home_bottom'];
    if(b.placement==='dont_miss')return ['dont_miss'];
    if(b.placement==='happy_hour')return ['home_side'];
    return ['home_main','checkout',...(Number(settings.orders_banner_mode)===1?[]:['orders'])];
  }
  function list(rows,place,settings={},now=Date.now()){
    if(!places.includes(place))return [];
    return (Array.isArray(rows)?rows:[]).filter(b=>b&&b.is_active!==false&&
      (!b.starts_at||Date.parse(b.starts_at)<=now)&&(!b.ends_at||Date.parse(b.ends_at)>now)&&
      placements(b,settings).includes(place)).slice().sort((a,b)=>(Number(a.sort)||0)-(Number(b.sort)||0));
  }
  function image(b,lang){return text(config(b).images?.[lang])||text(b.image_url);}
  function label(b,lang){return text(config(b).label?.[lang]).slice(0,40);}
  function safeLink(value){
    const raw=text(value);if(!raw)return '';
    try{const url=new URL(raw);return ['http:','https:'].includes(url.protocol)&&!url.username&&!url.password?url.href:'';}catch{return '';}
  }
  root.TALABOT_BANNERS=Object.freeze({places,config,placements,list,image,label,safeLink});
})(window);
