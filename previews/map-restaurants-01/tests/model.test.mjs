import test from 'node:test';
import assert from 'node:assert/strict';
import {stores} from '../dist/data.mjs';
import {eligible,rating,filterStores,internalReviews,restoreState,DEFAULT_FILTERS} from '../dist/model.mjs';
test('pins include only active food venues with valid numeric coordinates',()=>{
  const s=stores[0];assert.equal(eligible(s),true);
  for(const bad of [{is_active:false},{lat:null},{lng:181},{lat:NaN},{category:'pharmacy'},{category:'unknown'}])assert.equal(eligible({...s,...bad}),false);
});
test('closed active branch remains discoverable; open filter excludes it',()=>{
  assert.equal(filterStores(stores,DEFAULT_FILTERS).length,6);
  assert.equal(filterStores(stores,{...DEFAULT_FILTERS,openOnly:true}).length,4);
});
test('search, category, minimum rating and open filters intersect',()=>{
  assert.deepEqual(filterStores(stores,{query:'safran',category:'restaurant',minRating:4.5,openOnly:true}).map(s=>s.id),['demo-safran-center']);
  assert.deepEqual(filterStores(stores,{...DEFAULT_FILTERS,query:'Север'}).map(s=>s.id),['demo-safran-north']);
  assert.equal(filterStores(stores,{...DEFAULT_FILTERS,query:'not-found'}).length,0);
});
test('small internal review counts are valid, no five-review threshold',()=>{
  assert.deepEqual(rating(stores[0]),{state:'ready',average:4.7,count:3});
  assert.deepEqual(rating(stores[1]),{state:'ready',average:4,count:2});
});
test('empty and unavailable differ; Google fields never supply a fallback',()=>{
  assert.deepEqual(rating({...stores[4],rating:5,rating_count:10000}),{state:'empty',average:null,count:0});
  for(const r of [undefined,{...stores[0].talabot_rating,source:'google'},{...stores[0].talabot_rating,rating_average:7},{...stores[0].talabot_rating,store_id:'another-branch'}])assert.equal(rating({...stores[0],talabot_rating:r,rating:5,rating_count:10000}).state,'unavailable');
});
test('review projection rejects driver subjects and different branch IDs',()=>{
  const s=stores[0],valid=s.reviews[0];assert.equal(internalReviews({...s,reviews:[valid,{...valid,store_id:'wrong'},{...valid,subject:'driver'},{...valid,source:'google'}]}).length,1);
});
test('fixtures totals and averages come from matching restaurant-only comments',()=>{
  for(const s of stores){const rs=internalReviews(s),r=rating(s);assert.equal(r.count,rs.length);assert.equal(r.average,rs.length?Math.round(rs.reduce((n,r)=>n+r.stars,0)/rs.length*10)/10:null)}
});
test('map state round-trips center, zoom, filters, selection and list scroll',()=>{
  const expected={center:[38.57,68.79],zoom:16,filters:{query:'safran',category:'restaurant',minRating:4,openOnly:false},selected:'demo-safran-north',listScroll:120};
  assert.deepEqual(restoreState(JSON.parse(JSON.stringify(expected)),stores),expected);
});
test('bad session state cannot introduce invalid center or hidden selection',()=>{
  const s=restoreState({center:[Infinity,null],zoom:99,filters:{category:'pharmacy',openOnly:true,minRating:5.5},selected:'demo-safran-north',listScroll:-5},stores);
  assert.deepEqual(s.center,[38.575,68.786]);assert.equal(s.zoom,19);assert.equal(s.filters.category,'');assert.equal(s.selected,null);assert.equal(s.listScroll,0);
});
