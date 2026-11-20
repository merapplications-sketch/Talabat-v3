/* BRIEF-31 AG-05: presentation-only sheet height; selection/prices stay in the original handlers. */
(function(){
'use strict';
let root=null,active=null,frame=0,animation=0;
const clamp=x=>Math.max(0,Math.min(1,x));
const reduced=()=>window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
function cancelFrame(){if(frame)cancelAnimationFrame(frame);frame=0;if(animation)cancelAnimationFrame(animation);animation=0;}
function dimensions(sheet){
  const height=sheet.clientHeight||window.visualViewport?.height||innerHeight;
  const safe=parseFloat(getComputedStyle(sheet).getPropertyValue('--b31-safe-top'))||0;
  const large=Math.max(112,Math.min(176,height*.22));
  const small=Math.min(large,80+safe);
  return {large,small,travel:Math.max(1,large-small)};
}
function paint(sheet,progress,dims=dimensions(sheet)){
  if(!sheet?.isConnected||!S.sh)return;
  progress=clamp(progress);S.sh.sheetLift=progress;
  sheet.style.setProperty('--b31-photo-height',(dims.large-progress*dims.travel)+'px');
  const handle=sheet.querySelector('[data-dish-handle]');
  if(handle){
    const expanded=progress>=.5;
    handle.setAttribute('aria-expanded',String(expanded));
    handle.setAttribute('aria-label',t(expanded?'b31SheetCollapse':'b31SheetExpand'));
  }
}
function settle(sheet,target,instant=false){
  cancelFrame();if(!sheet?.isConnected||!S.sh)return;
  const state=S.sh,from=Number(state.sheetLift)||0,dims=dimensions(sheet);
  target=clamp(target);
  if(instant||reduced()||Math.abs(from-target)<.01){paint(sheet,target,dims);return;}
  let start;
  const tick=now=>{
    if(!sheet.isConnected||S.sh!==state){animation=0;return;}
    if(start===undefined)start=now;
    const time=Math.min(1,(now-start)/180),ease=1-Math.pow(1-time,3);
    paint(sheet,from+(target-from)*ease,dims);
    if(time<1)animation=requestAnimationFrame(tick);else animation=0;
  };
  animation=requestAnimationFrame(tick);
}
function stopDrag(event,cancelled=false){
  if(!active||event.pointerId!==active.id)return;
  const drag=active;active=null;cancelFrame();
  drag.handle.classList.remove('is-dragging');
  try{if(drag.handle.hasPointerCapture(drag.id))drag.handle.releasePointerCapture(drag.id);}catch(_e){}
  if(drag.moved){
    drag.handle.dataset.dragClick='1';
    const delta=drag.startY-drag.lastY;
    settle(drag.sheet,cancelled?drag.start:Math.abs(delta)>20?(delta>0?1:0):(Number(S.sh?.sheetLift)||0)>=.5?1:0);
  }
}
function bind(sheet,handle){
  handle.addEventListener('click',event=>{
    event.stopPropagation();
    if(handle.dataset.dragClick==='1'&&event.detail!==0){delete handle.dataset.dragClick;return;}
    delete handle.dataset.dragClick;
    if(handle.disabled||active)return;
    settle(sheet,(Number(S.sh?.sheetLift)||0)>=.5?0:1);
  });
  handle.addEventListener('pointerdown',event=>{
    if(event.button!==0||event.isPrimary===false||handle.disabled||!S.sh)return;
    cancelFrame();delete handle.dataset.dragClick;
    active={id:event.pointerId,startY:event.clientY,lastY:event.clientY,start:Number(S.sh.sheetLift)||0,
      sheet,handle,state:S.sh,dims:dimensions(sheet),moved:false};
    handle.setPointerCapture(event.pointerId);
  });
  handle.addEventListener('pointermove',event=>{
    const drag=active;
    if(!drag||event.pointerId!==drag.id||S.sh!==drag.state)return;
    drag.lastY=event.clientY;
    if(Math.abs(drag.startY-event.clientY)>4){drag.moved=true;handle.classList.add('is-dragging');}
    if(!drag.moved)return;
    drag.next=clamp(drag.start+(drag.startY-event.clientY)/drag.dims.travel);
    if(!frame)frame=requestAnimationFrame(()=>{frame=0;if(active===drag)paint(sheet,drag.next,drag.dims);});
  });
  handle.addEventListener('pointerup',event=>stopDrag(event));
  handle.addEventListener('pointercancel',event=>stopDrag(event,true));
  handle.addEventListener('lostpointercapture',event=>stopDrag(event,true));
}
function mount(sheet){
  if(root!==sheet){cancelFrame();active=null;root=sheet;}
  if(!sheet||!S.sh)return;
  const handle=sheet.querySelector('[data-dish-handle]');
  if(!handle)return;
  handle.disabled=sheet.classList.contains('d6-keyboard')||!sheet.querySelector('.d6s-top>img');
  if(!handle.dataset.bound){handle.dataset.bound='1';bind(sheet,handle);}
  if(!active&&!animation)paint(sheet,Number(S.sh.sheetLift)||0);
}
window.TALABOT_DISH_BRIEF31=Object.freeze({mount});
if(typeof dishViewport==='function')dishViewport();
})();
