"""Batch C core API (prepared; needs proposed SQL patch 39): TLB.courierPosition(orderId) — LOCAL mock only.
The RPC answer is stubbed; the server rule itself (own order, status pickedup only) is in sql/proposed/patch39 and is
NOT applied / not proven. python3 tools/courier_position_check.py"""
import os, sys
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..'))
FIX = open(os.path.join(here, 'qa_all.py')).read().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE', '"customer"')
STUB = """(function(){var cc=window.supabase.createClient;window.supabase.createClient=function(){var c=cc.apply(this,arguments),r=c.rpc;
 c.rpc=function(n,a){if(n!=='order_courier_position')return r.apply(this,arguments);window.__cp=(window.__cp||[]).concat([a]);var m=window.__cpMode;
  if(m==='row')return Promise.resolve({data:[{lat:41.3,lng:69.24,acc:18,updated_at:'2026-10-24T10:00:00Z'}],error:null});
  if(m==='none')return Promise.resolve({data:[],error:null});if(m==='missing')return Promise.resolve({data:null,error:{code:'PGRST202',message:'not found'}});
  return Promise.reject(new Error('net'))};return c}})();"""
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.route('**/*', lambda rt, rq: rt.fulfill(status=200, content_type='application/javascript', body=FIX + STUB) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.goto('file://' + root + '/customer.html', wait_until='domcontentloaded'); pg.wait_for_timeout(2000)
    r = pg.evaluate("async()=>{window.__cpMode='row';return await TLB.courierPosition(1001)}")
    ok(r == {'lat': 41.3, 'lng': 69.24, 'acc': 18, 'at': 1792836000000} and pg.evaluate("()=>window.__cp[0].p_order") == 1001, 'row: last position + its time (%s)' % r)
    for m in ('none', 'missing', 'net'):
        ok(pg.evaluate("async(m)=>{window.__cpMode=m;return await TLB.courierPosition(1001)}", m) is None, '%s: null (not on the way / function not applied / offline) — nothing invented' % m)
    b.close()
print('\nCOURIER POSITION CHECK %s' % ('FAILS %d' % len(fails) if fails else 'OK')); sys.exit(1 if fails else 0)
