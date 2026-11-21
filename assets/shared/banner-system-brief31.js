/* BRIEF-31: presentation of existing banner rows; no database or core mutation. */
(function(root){
  'use strict';
  const places=Object.freeze(['home_main','home_side','dont_miss','home_bottom','orders','restaurants','checkout','login']);
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
  function headline(b,lang){return (text(config(b).headline?.[lang])||text(b?.title)).slice(0,80);}
  function subtitle(b,lang){return text(config(b).subtitle?.[lang]).slice(0,160);}
  function loginAccess(b){return config(b).login_access==='public'?'public':'after_auth';}
  function safeLink(value){
    const raw=text(value);if(!raw)return '';
    try{const url=new URL(raw);return ['http:','https:'].includes(url.protocol)&&!url.username&&!url.password?url.href:'';}catch{return '';}
  }
  function rotationMs(place,settings={}){
    const seconds=Number(settings['banner_rotation_'+place+'_seconds']);
    return Number.isFinite(seconds)&&seconds>=1&&seconds<=60?seconds*1000:place==='login'?5000:3000;
  }
  /* BRIEF-32 AI-04: format existing timers only; callers retain their deadlines/visibility. */
  function countdownParts(ms,lang){
    if(!Number.isFinite(ms)||ms<=0)return null;
    const total=Math.floor(ms/1000),hours=Math.floor(total/3600),minutes=Math.floor(total%3600/60);
    const days=ms>86400000,units=days?(lang==='ru'?['д','ч','м']:lang==='tg'?['р','с','д']:['d','h','m']):['','',''];
    const values=(days?[Math.floor(hours/24),hours%24,minutes]:[hours,minutes,total%60])
      .map((value,index)=>String(value).padStart(days&&index===0?1:2,'0'));
    const separator=days?'·':':';
    return {mode:days?'days':'clock',values,units,separator,
      label:values.map((value,index)=>value+(units[index]?' '+units[index]:'')).join(' '+separator+' ')};
  }
  function countdownHTML(ms,lang){
    lang=['ru','en','tg'].includes(lang)?lang:'ru';
    const parts=countdownParts(ms,lang);if(!parts)return '';
    return `<span class="countdown32-cells" data-mode="${parts.mode}" data-lang="${lang}" role="timer" aria-live="off" aria-label="${parts.label}">${parts.values.map((value,index)=>
      `${index?`<span class="countdown32-separator" aria-hidden="true">${parts.separator}</span>`:''}<span class="countdown32-cell" aria-hidden="true"><span class="countdown32-value">${value}</span>${parts.units[index]?`<small>${parts.units[index]}</small>`:''}</span>`).join('')}</span>`;
  }
  function updateCountdown(node,ms,lang){
    lang=['ru','en','tg'].includes(lang)?lang:'ru';
    const parts=countdownParts(ms,lang);if(!parts)return;
    const cells=node.firstElementChild;
    if(!cells||cells.dataset.mode!==parts.mode||cells.dataset.lang!==lang){node.innerHTML=countdownHTML(ms,lang);return;}
    cells.setAttribute('aria-label',parts.label);
    cells.querySelectorAll('.countdown32-value').forEach((digit,index)=>{
      if(digit.textContent!==parts.values[index])digit.textContent=parts.values[index];
    });
  }
  root.TALABOT_BANNERS=Object.freeze({places,config,placements,list,image,label,headline,subtitle,loginAccess,safeLink,rotationMs,countdownHTML,updateCountdown});
})(window);
