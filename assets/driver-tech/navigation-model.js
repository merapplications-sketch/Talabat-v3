/* Provider-neutral presentation model. Pure, no order mutations, SDK, network or location watch. */
(function(root){
  'use strict';
  function point(p){return Array.isArray(p)&&p.length===2&&p.every(v=>typeof v==='number'&&Number.isFinite(v))&&Math.abs(p[0])<=90&&Math.abs(p[1])<=180&&!(p[0]===0&&p[1]===0);}
  function meters(a,b){const r=v=>v*Math.PI/180,h=Math.sin(r(b[0]-a[0])/2)**2+Math.cos(r(a[0]))*Math.cos(r(b[0]))*Math.sin(r(b[1]-a[1])/2)**2;return 12742000*Math.asin(Math.sqrt(Math.min(1,h)));}
  function destination(task,stage,store){const p=stage>=3?[task?.lat,task?.lng]:store;return point(p)?p:null;}
  function key(task,stage,to){return task&&to?JSON.stringify([String(task.id),stage>=3?'customer':'restaurant',to]):'';}
  function progress(route,fix,policy,now){
    if(!fix||!point(fix.point)||!Number.isFinite(fix.at)||now-fix.at>policy.gpsMaxAgeMs||fix.at>now+1000||!Number.isFinite(fix.accuracy)||fix.accuracy>80)return {mode:'tracking',reason:'gps_unavailable'};
    if(!route||!Array.isArray(route.coords)||route.coords.length<2||route.coords.some(p=>!point(p))||!Number.isFinite(route.distance_m)||!Number.isFinite(route.duration_s))return {mode:'tracking',reason:'no_route'};
    const line=route.coords,lens=[],prefix=[0];let total=0,best={distance:Infinity,index:0,fraction:0};
    for(let i=0;i<line.length-1;i++){
      const a=line[i],b=line[i+1],scale=Math.cos(fix.point[0]*Math.PI/180),x=(b[1]-a[1])*scale,y=b[0]-a[0],dx=(fix.point[1]-a[1])*scale,dy=fix.point[0]-a[0];
      const f=Math.max(0,Math.min(1,(dx*x+dy*y)/(x*x+y*y||1))),p=[a[0]+f*y,a[1]+f*(b[1]-a[1])],dist=meters(fix.point,p),len=meters(a,b);
      lens.push(len);total+=len;prefix.push(total);if(dist<best.distance)best={distance:dist,index:i,fraction:f};
    }
    if(best.distance>Math.max(policy.deviationM,fix.accuracy*2))return {mode:'tracking',reason:'off_route'};
    const passed=prefix[best.index]+lens[best.index]*best.fraction,remainingM=Math.max(0,route.distance_m*(1-passed/(total||1)));
    const steps=Array.isArray(route.steps)?route.steps:[],current=steps.find(s=>prefix[s.from]>passed+5)||(passed<5?steps[0]:null);
    let remainingS=route.duration_s*(1-passed/(total||1));
    if(steps.length&&steps.every(s=>Number.isFinite(s.durationS)&&prefix[s.to]!=null&&prefix[s.from]!=null))remainingS=steps.reduce((n,s)=>{const len=prefix[s.to]-prefix[s.from];return n+s.durationS*(len>0?Math.max(0,Math.min(1,(prefix[s.to]-passed)/len)):0);},0);
    return {mode:'internal',remainingM,remainingS,step:current||null,turnDistanceM:current?Math.max(0,(prefix[current.from]||0)-passed):null,offRouteM:best.distance,calculatedAt:route.calculated_at,fixAt:fix.at};
  }
  root.TALABOT_NAV_MODEL={point,meters,destination,key,progress};
})(typeof window==='undefined'?globalThis:window);
