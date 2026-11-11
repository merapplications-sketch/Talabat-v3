// MAP-RESTAURANTS-01: public display model; no database client or write path.
export const DEFAULT_FILTERS = {query:'', category:'', minRating:0, openOnly:false};
export function eligible(s) {
  return s.is_active === true && ['restaurant','cafe','fastfood'].includes(s.category)
    && Number.isFinite(s.lat) && Number.isFinite(s.lng)
    && Math.abs(s.lat) <= 90 && Math.abs(s.lng) <= 180;
}
export function rating(s) {
  const r = s.talabot_rating;
  if (!r || r.source !== 'talabot' || r.subject !== 'restaurant' || r.store_id !== s.id)
    return {state:'unavailable', average:null, count:null};
  if (r.rating_count === 0 && r.rating_average === null) return {state:'empty',average:null,count:0};
  if (!Number.isInteger(r.rating_count) || r.rating_count < 1 || !Number.isFinite(r.rating_average)
    || r.rating_average < 1 || r.rating_average > 5) return {state:'unavailable',average:null,count:null};
  return {state:'ready',average:r.rating_average,count:r.rating_count};
}
export function filterStores(stores, filters) {
  const q=filters.query.trim().toLocaleLowerCase();
  return stores.filter(eligible).filter(s =>
    (!q || [s.name.ru,s.name.en,s.branch.ru,s.branch.en,s.address.ru,s.address.en].join(' ').toLocaleLowerCase().includes(q))
    && (!filters.category || s.category === filters.category)
    && (!filters.openOnly || s.is_open === true)
    && (!filters.minRating || (rating(s).state === 'ready' && rating(s).average >= filters.minRating)));
}
export function internalReviews(store) {
  return (store.reviews||[]).filter(r=>r.store_id === store.id && r.source === 'talabot'
    && r.subject === 'restaurant' && Number.isInteger(r.stars) && r.stars >= 1 && r.stars <= 5);
}
export function restoreState(raw, stores) {
  const d={center:[38.575,68.786],zoom:14,filters:{...DEFAULT_FILTERS},selected:null,listScroll:0};
  if (!raw || typeof raw !== 'object') return d;
  if (Array.isArray(raw.center) && raw.center.length===2 && raw.center.every(Number.isFinite)
    && Math.abs(raw.center[0])<=90 && Math.abs(raw.center[1])<=180) d.center=raw.center;
  if (Number.isFinite(raw.zoom)) d.zoom=Math.max(10,Math.min(19,raw.zoom));
  if (raw.filters) d.filters={query:String(raw.filters.query||'').slice(0,150),category:['restaurant','cafe','fastfood'].includes(raw.filters.category)?raw.filters.category:'',minRating:[0,4,4.5].includes(raw.filters.minRating)?raw.filters.minRating:0,openOnly:raw.filters.openOnly===true};
  if (filterStores(stores,d.filters).some(s=>s.id===raw.selected)) d.selected=raw.selected;
  if (Number.isFinite(raw.listScroll)) d.listScroll=Math.max(0,raw.listScroll);
  return d;
}
