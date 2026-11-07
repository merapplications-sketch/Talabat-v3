const fs=require('node:fs'); const assert=require('node:assert/strict');
for(const name of ['talabat-core.js','driver.html']) {
 const src=fs.readFileSync(name,'utf8');
 const layers=[...src.matchAll(/L\.tileLayer\('https:\/\/tile\.openstreetmap\.org\/[^']+',\s*(\{[^}]+\})\)/g)];
 assert.equal(layers.length,name==='driver.html'?1:2);
 for(const [,options] of layers){
  const parsed=Function('return ('+options+')')();
  assert.equal(parsed.referrerPolicy,'origin','OSM requires origin identification without exposing page paths');
  assert.ok(parsed.attribution.includes('OpenStreetMap'));
 }
}
for(const name of ['driver','customer','admin','merchant']) assert.match(fs.readFileSync(name+'.html','utf8'),/<meta name="referrer" content="no-referrer">/,'Other requests retain existing privacy policy');
console.log('PASS: map-origin identification and non-map privacy');
