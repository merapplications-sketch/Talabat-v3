// ASSETS is generated from public/ at build time. No network, bindings or runtime secrets.
const BASE_HEADERS = {
 'Content-Security-Policy': "frame-ancestors 'none'",
 'X-Frame-Options': 'DENY',
 'Strict-Transport-Security': 'max-age=86400',
 'X-Content-Type-Options': 'nosniff',
};
function reply(body, status, headers = {}) {
 return new Response(body, {status, headers: {...BASE_HEADERS, ...headers}});
}
function own(key) { return Object.prototype.hasOwnProperty.call(ASSETS,key); }
export default {
 async fetch(request) {
  if(request.method !== 'GET' && request.method !== 'HEAD') return reply(null,405,{Allow:'GET, HEAD'});
  const url=new URL(request.url);
  let pathname;
  try { pathname=decodeURIComponent(url.pathname); } catch { return reply(null,400); }
  // Match current Sites clean HTML URLs and preserve query parameters.
  let canonical=pathname;
  if(pathname.endsWith('/index.html') && own(pathname)) canonical=pathname.slice(0,-10) || '/';
  else if(pathname.endsWith('.html') && own(pathname)) canonical=pathname.slice(0,-5);
  else if(pathname !== '/' && pathname.endsWith('/') && own(pathname.slice(0,-1)+'.html')) canonical=pathname.slice(0,-1);
  if(canonical!==pathname) return reply(null,307,{Location:encodeURI(canonical)+url.search});
  let key=pathname;
  if(pathname==='/') key='/index.html';
  else if(!own(key) && own(key+'.html')) key+='.html';
  else if(!own(key) && own(key+'/index.html')) key+='/index.html';
  if(!own(key)) return reply(request.method==='HEAD'?null:'Not Found',404,{'Content-Type':'text/plain; charset=utf-8'});
  const asset=ASSETS[key];
  const headers={'Content-Type':asset.type,'Content-Security-Policy':asset.csp,'Cache-Control':'no-cache'};
  if(request.method==='HEAD') return reply(null,200,headers);
  return reply(Uint8Array.from(atob(asset.body),c=>c.charCodeAt(0)),200,headers);
 }
};
