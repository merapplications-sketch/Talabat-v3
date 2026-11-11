// Test-only read candidate. No application imports, network or writes.
const results=new WeakMap();
const fail=reason=>{throw Object.assign(new Error(reason),{readReason:reason});};
const positive=n=>Number.isSafeInteger(n)&&n>0;
const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
export async function readInternalRatings(adapter,options){
 const {storeIds,pageSize,maxRows,maxPages,timeoutMs,signal}=options;
 if(!Array.isArray(storeIds)||!storeIds.length||storeIds.some(s=>typeof s!=='string'||!s)||new Set(storeIds).size!==storeIds.length||![pageSize,maxRows,maxPages,timeoutMs].every(positive))throw Error('invalid_test_read_contract');
 const ids=[...storeIds],controller=new AbortController();let abortReason='cancelled',session,timer;
 const cancel=()=>controller.abort();if(signal?.aborted)cancel();else signal?.addEventListener('abort',cancel,{once:true});
 timer=setTimeout(()=>{abortReason='timeout';controller.abort();},timeoutMs);
 const wait=operation=>new Promise((resolve,reject)=>{
  const abort=()=>reject(Object.assign(new Error(abortReason),{readReason:abortReason}));
  if(controller.signal.aborted){abort();return;}
  controller.signal.addEventListener('abort',abort,{once:true});
  Promise.resolve().then(operation).then(resolve,reject).finally(()=>controller.signal.removeEventListener('abort',abort));
 });
 const unavailable=reason=>freeze({state:'unavailable',reason,source:'talabot',subject:'restaurant',snapshot:null,rows_read:null,stores:ids.map(store_id=>({store_id,source:'talabot',subject:'restaurant',state:'unavailable',rating_count:null,average:null}))});
 try{
  session=await wait(async()=>{
   const opened=await adapter.open([...ids],{signal:controller.signal});
   if(controller.signal.aborted&&opened?.close)Promise.resolve().then(()=>opened.close()).catch(()=>{});
   return opened;
  });
  if(!session||session.source!=='talabot'||session.coverage!=='complete_internal_history'||typeof session.version!=='string'||!session.version||!Array.isArray(session.scope)||JSON.stringify(session.scope)!==JSON.stringify(ids)||!Number.isSafeInteger(session.total_rows)||session.total_rows<0||typeof session.page!=='function')fail('unverified_source');
  // Copy metadata once; mutable adapter objects cannot move the goalposts mid-read.
  const version=session.version,total=session.total_rows;
  if(total>maxRows)fail('resource_limit');
  const stats=new Map(ids.map(id=>[id,{sum:0n,count:0n}])),seen=new Set();let after=null,pages=0;
  for(;;){
   if(++pages>maxPages)fail('resource_limit');
   const page=await wait(()=>session.page({after,limit:pageSize,signal:controller.signal}));
   if(!page||page.version!==version)fail('snapshot_changed');
   if(!Array.isArray(page.rows)||page.rows.length>pageSize||typeof page.has_more!=='boolean')fail('invalid_page');
   for(const row of page.rows){
    if(!row||typeof row.order_id!=='string'||!row.order_id||seen.has(row.order_id)||after!==null&&row.order_id<=after||!stats.has(row.store_id))fail('invalid_history');
    if(!Object.hasOwn(row,'store_stars')||row.store_stars!==null&&(!Number.isInteger(row.store_stars)||row.store_stars<1||row.store_stars>5))fail('invalid_history');
    if(row.store_stars===null&&(!Number.isInteger(row.driver_stars)||row.driver_stars<1||row.driver_stars>5))fail('invalid_history');
    seen.add(row.order_id);after=row.order_id;if(seen.size>maxRows)fail('resource_limit');if(seen.size>total)fail('incomplete_history');
    if(row.store_stars!==null){const stat=stats.get(row.store_id);stat.sum+=BigInt(row.store_stars);stat.count++;}
   }
   if(!page.has_more){if(seen.size!==total)fail('incomplete_history');break;}
   if(!page.rows.length||seen.size>=total)fail('incomplete_history');
  }
  const stores=ids.map(store_id=>{const {sum,count}=stats.get(store_id);return{store_id,source:'talabot',subject:'restaurant',state:count?'ready':'empty',rating_count:Number(count),average:count?Number((20n*sum+count)/(2n*count))/10:null};});
  const result=freeze({state:'ready',source:'talabot',subject:'restaurant',snapshot:version,rows_read:seen.size,stores});results.set(result,new Set());return result;
 }catch(e){return unavailable(['cancelled','timeout','unverified_source','resource_limit','snapshot_changed','invalid_page','invalid_history','incomplete_history'].includes(e?.readReason)?e.readReason:'read_failed');}
 finally{
  clearTimeout(timer);signal?.removeEventListener('abort',cancel);
  // Adapter must release snapshot resources on cancellation. No writes or retries here.
  if(session?.close)Promise.resolve().then(()=>session.close()).catch(()=>{});
 }
}
export function selectPage(result,{sort=null,minAverage=null,limit,cursor=null}={}){
 if(!positive(limit)||![null,'average-desc','count-desc'].includes(sort)||minAverage!==null&&(typeof minAverage!=='number'||!Number.isFinite(minAverage)||minAverage<0||minAverage>5))throw Error('invalid_test_query');
 if(result.state==='unavailable')return freeze({state:'unavailable',items:null,total:null,next:null});
 const cursors=results.get(result);if(!cursors)throw Error('unrecognized_read_result');
 const key=JSON.stringify([sort,minAverage,limit]);
 if(cursor&&(!cursors.has(cursor)||cursor.query!==key))throw Error('cursor_scope_mismatch');
 let rows=result.stores.filter(s=>minAverage===null||s.state==='ready'&&s.average>=minAverage);
 // Preserve input order on ties, and do not manufacture zero for an unrated branch.
 if(sort)rows=rows.map((s,i)=>({s,i})).sort((a,b)=>{
  if(a.s.state!==b.s.state)return a.s.state==='ready'?-1:1;
  const field=sort==='average-desc'?'average':'rating_count';return (b.s[field]??0)-(a.s[field]??0)||a.i-b.i;
 }).map(x=>x.s);
 const start=cursor?.index||0,end=Math.min(start+limit,rows.length);let next=null;
 if(end<rows.length){next=freeze({query:key,index:end});cursors.add(next);}
 return freeze({state:'ready',snapshot:result.snapshot,items:rows.slice(start,end),total:rows.length,next});
}
export function commentsProjection(){return {state:'withheld',reason:'publication_contract_pending',reviews:null,review_count:null};}
