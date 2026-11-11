// PRICE01 evidence representation only; never rounds or rewrites an old payload.
function priceValid01(v){
 const obj=x=>x&&typeof x==='object'&&!Array.isArray(x),keys=(x,a)=>obj(x)&&Object.keys(x).sort().join('|')===a.slice().sort().join('|');
 const id=x=>typeof x==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(x);
 const dec=x=>typeof x==='string'&&x.length<=128&&/^-?(0|[1-9][0-9]*)(\.[0-9]+)?$/.test(x);
 const amounts=['base_price','unit_price','restaurant_discount','happy_hour_discount','net_items'];
 const totals=['subtotal','restaurant_discount','happy_hour_discount','promo_discount','points_value','delivery_fee','tip','wallet_used','cash_due','total'];
 try{return keys(v,['version','lines','totals'])&&v.version===1&&JSON.stringify(v).length<=524288&&Array.isArray(v.lines)&&v.lines.length>=1&&v.lines.length<=60&&v.lines.every(l=>keys(l,['item_id','qty','options',...amounts])&&id(l.item_id)&&Number.isInteger(l.qty)&&l.qty>=1&&l.qty<=50&&amounts.every(k=>dec(l[k]))&&Array.isArray(l.options)&&l.options.length<=40&&l.options.every(o=>keys(o,['id','price_delta'])&&id(o.id)&&dec(o.price_delta)))&&keys(v.totals,totals)&&totals.every(k=>dec(v.totals[k]));}catch(e){return false;}
}
function priceCopy01(v){return JSON.parse(JSON.stringify(v));}
function priceSelection01(a,b){return priceValid01(a)&&priceValid01(b)&&JSON.stringify(a.lines.map(l=>[l.item_id,l.qty,l.options.map(o=>o.id)]))===JSON.stringify(b.lines.map(l=>[l.item_id,l.qty,l.options.map(o=>o.id)]));}
