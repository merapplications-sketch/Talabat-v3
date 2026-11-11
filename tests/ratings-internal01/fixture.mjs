// Synthetic read adapter ONLY: models immutable snapshots, not DB/RLS correctness.
export function memoryAdapter(input,{onPage}={}){
 let rows=structuredClone(input),revision=1;const calls=[];
 return {calls,append(row){rows.push(structuredClone(row));revision++;},
 async open(storeIds){const selected=rows.filter(r=>storeIds.includes(r.store_id)).sort((a,b)=>a.order_id.localeCompare(b.order_id));
  const snapshot=structuredClone(selected),version='synthetic-'+revision;let closed=false;
  return {version,scope:[...storeIds],coverage:'complete_internal_history',source:'talabot',total_rows:snapshot.length,
   async page({after,limit,signal}){calls.push({after,limit});if(onPage)await onPage({after,limit,signal});if(closed)throw Error('closed');
    const start=after===null?0:snapshot.findIndex(r=>r.order_id===after)+1;
    const items=snapshot.slice(start,start+limit);return {version,rows:items,has_more:start+items.length<snapshot.length};},
   async close(){closed=true;}};
 }};
}
