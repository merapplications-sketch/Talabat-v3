"""Map tiles must reach OpenStreetMap with a Referer (OSM blocks tiles without one: 403 "Access blocked. Referer is required").
The pages themselves keep <meta name="referrer" content="no-referrer"> (nothing else is sent anywhere); only the tile requests send the
site ORIGIN (no path, no query), as the OSM tile policy asks.
  python3 tools/map_tile_check.py <preview_dir> <leaflet_dist_dir>
The preview is served on http://127.0.0.1 so the browser has a real origin; Leaflet is served from <leaflet_dist_dir>; tile requests are
answered locally with a 1-pixel image and their Referer header is recorded. Chromium, not Safari."""
import os,sys,threading,http.server,functools,base64
from playwright.sync_api import sync_playwright
d=os.path.abspath(sys.argv[1]);lf=os.path.abspath(sys.argv[2]);fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
H=functools.partial(http.server.SimpleHTTPRequestHandler,directory=d);H.log_message=lambda self,*a:None
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),H);port=srv.server_address[1];threading.Thread(target=srv.serve_forever,daemon=True).start()
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});tiles=[];other=[];errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    def route(rt,rq):
        u=rq.url
        if 'tile.openstreetmap.org' in u: tiles.append(rq.headers.get('referer'));return rt.fulfill(status=200,content_type='image/png',body=PNG)
        if 'leaflet@1.9.4/dist/' in u:
            f=os.path.join(lf,u.split('/dist/')[1].split('?')[0])
            return rt.fulfill(path=f) if os.path.exists(f) else rt.abort()
        if u.startswith('http://127.0.0.1'): return rt.continue_()
        if u.startswith('http'): other.append((u.split('/')[2],rq.headers.get('referer')));return rt.abort()
        return rt.continue_()
    pg.route('**/*',route)
    pg.goto('http://127.0.0.1:%d/admin.html'%port);pg.wait_for_timeout(2500);E=pg.evaluate
    ok(E("()=>document.querySelector('meta[name=referrer]').content")=='no-referrer','pages still send no Referer by default')
    E("()=>{tab='d';render()}");pg.wait_for_timeout(300)
    E("()=>openMap()");pg.wait_for_timeout(2500)
    ok(len(tiles)>0,'courier/store map asked for %d tiles'%len(tiles))
    exp='http://127.0.0.1:%d/'%port
    ok(tiles and all(t==exp for t in tiles),'every tile request carries only the site origin as Referer (%s)'%sorted(set(map(str,tiles)))[:3])
    ok(not [o for o in other if o[1]],'no other request sends a Referer %s'%[o for o in other if o[1]][:3])
    E("()=>{MAPO=false;render()}")
    # the address/location picker (customer, merchant and admin use it)
    n0=len(tiles);E("()=>TLB.pickLocation&&TLB.pickLocation(null,()=>{})");pg.wait_for_timeout(2000)
    ok(len(tiles)>n0 and all(t==exp for t in tiles[n0:]),'location picker tiles carry the origin (%d tiles)'%(len(tiles)-n0))
    ok(not errs,'no JS errors '+str(errs[:2]));b.close()
srv.shutdown()
print('MAP FAILS',len(fails));sys.exit(1 if fails else 0)
