"""Core contracts C-1 / C-2 / C-3 / C-5 (27 Oct work list, log §33) — LOCAL only: repo customer fixture, isolated services,
no project, no account. Real Chromium; the QR is decoded back with jsQR and the decoded link is opened.
  python3 tools/core_contracts_check.py <dir with node_modules/{qrcode-generator@1.4.4,jsqr}>
NOT proof of: the live order_events permission (owner's read-only query), Safari / iPhone, the published host."""
import json, re, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]; NM = Path(sys.argv[1]) / 'node_modules'
QR = (NM / 'qrcode-generator/qrcode.js').read_bytes(); JSQR = NM / 'jsqr/dist/jsQR.js'
UUID = '3f1c2a9e-7b4d-4c1e-9a2b-5d6e7f8a9b0c'
fails = []
def ok(c, m): print(('PASS ' if c else 'FAIL ') + m, flush=True); (None if c else fails.append(m))
subprocess.run([sys.executable, str(ROOT / 'tools/ui_hc_fixture.py'), '/tmp/core-contracts-fixture'], check=True, capture_output=True)
FIX = Path('/tmp/core-contracts-fixture/customer-fixture.js').read_text().replace("'s1'", "'%s'" % UUID)
# failure switches over the fixture client: orders query / order_events read
WRAP = r"""(function(){const orig=supabase.createClient;supabase.createClient=function(){const c=orig.apply(this,arguments),from=c.from.bind(c);
 const fail=()=>{const p=new Proxy(function(){},{get:(t,k)=>k==='then'?(ok,bad)=>Promise.resolve({data:null,error:{message:'timeout'}}).then(ok,bad):()=>p});return p};
 window.__EV_CALLS=0;c.from=n=>{if(n==='orders'&&window.__FAIL_ORDERS)return fail();if(n==='order_events'){window.__EV_CALLS++;if(window.__EV_ERR)return fail()}return from(n)};return c}})();"""
def boot(b, scene, url_extra='', qr_body=QR):
    ctx = b.new_context(viewport={'width': 390, 'height': 760}); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script("window.__C_SCENE=%s;localStorage.setItem('tlb_lang','ru');" % json.dumps(scene))
    def route(r):
        u = r.request.url
        if 'supabase-js' in u: r.fulfill(content_type='application/javascript', body=FIX + '\n' + WRAP)
        elif 'qrcode-generator@1.4.4/qrcode.js' in u: r.fulfill(content_type='application/javascript', body=qr_body, headers={'Access-Control-Allow-Origin': '*'})
        elif u.startswith('http'): r.abort()
        else: r.continue_()
    ctx.route('**/*', route); pg.goto((ROOT / 'customer.html').as_uri() + url_extra)
    pg.wait_for_function('()=>window.TLB&&TLB.order&&TLB.order("ord1")', timeout=20000)
    return ctx, pg, errs
def reload(pg): pg.evaluate('()=>TLB.reload()'); pg.wait_for_timeout(400)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    # ---------- C-1 orders health ----------
    ctx, pg, errs = boot(b, 'preparing')
    h0 = pg.evaluate('TLB.ordersHealth()'); o0 = pg.evaluate('(({total,status,driver,payment})=>({total,status,driver,payment}))(TLB.order("ord1"))')
    ok(h0['failing'] is False and h0['lastOkAt'] and h0['failures'] == 0, 'C-1 healthy after load: %s' % h0)
    pg.evaluate("window.__FAIL_ORDERS=true;window.__C_TABLES.orders[0].total=999;window.__C_TABLES.orders[0].status='ready'"); reload(pg)
    h1 = pg.evaluate('TLB.ordersHealth()'); o1 = pg.evaluate('(({total,status,driver,payment})=>({total,status,driver,payment}))(TLB.order("ord1"))')
    ok(h1['failing'] and h1['failures'] >= 1 and h1['lastFailAt'] and h1['lastOkAt'] == h0['lastOkAt'], 'C-1 failed refresh reported separately: %s' % h1)
    ok(o1 == o0 and o0['total'] is not None, 'C-1 last trusted amount / status / driver / payment kept on failure: %s' % o1)
    ts1 = pg.evaluate('TLB.trackStatus(TLB.order("ord1"))')
    ok(ts1['stale'] and ts1['courier']['key'] == 'jcAssignedEarlier' and ts1['restaurant']['key'] == 'jrPreparing', 'C-3 while stale: last known states kept and marked (%s / %s)' % (ts1['restaurant']['key'], ts1['courier']['key']))
    pg.evaluate('window.__FAIL_ORDERS=false'); reload(pg)
    h2 = pg.evaluate('TLB.ordersHealth()'); st2 = pg.evaluate('TLB.order("ord1").status')
    ok(not h2['failing'] and h2['lastOkAt'] > h0['lastOkAt'] and st2 == 'ready', 'C-1 recovery clears the flag and loads the new data (status %s)' % st2)
    # ---------- C-2 status time ----------
    pg.evaluate("window.__C_TABLES.orders[0].status='preparing'"); reload(pg)
    a = pg.evaluate('TLB.statusAt("ord1")')
    ok(a['state'] in ('loading', 'ok'), 'C-2 first call starts the events read (%s)' % a['state'])
    pg.wait_for_timeout(300); a = pg.evaluate('TLB.statusAt("ord1")')
    ev = pg.evaluate("Date.parse(window.__C_TABLES.order_events.filter(e=>e.order_id==='ord1'&&e.kind==='preparing').pop().at)")
    ok(a['source'] == 'event' and a['at'] == ev, 'C-2 preparing time = the preparing event (%s == %s)' % (a['at'], ev))
    h = pg.evaluate('TLB.ordersHealth()'); pos = pg.evaluate('Date.now()')
    ok(a['at'] not in (h['lastOkAt'], h['lastFailAt']) and pos - a['at'] > 60000, 'C-2 not the refresh time nor the phone clock')
    pg.evaluate("window.__C_TABLES.orders[0].status='ready'"); reload(pg); pg.evaluate('TLB.statusAt("ord1")'); pg.wait_for_timeout(300)
    a = pg.evaluate('TLB.statusAt("ord1")'); ev = pg.evaluate("Date.parse(window.__C_TABLES.order_events.filter(e=>e.order_id==='ord1'&&e.kind==='ready').pop().at)")
    ok(a['status'] == 'ready' and a['at'] == ev, 'C-2 status change re-reads the events: ready time = the ready event')
    n = pg.evaluate('__EV_CALLS'); [pg.evaluate('TLB.statusAt("ord1")') for _ in range(20)]
    ok(pg.evaluate('__EV_CALLS') == n, 'C-2 no repeated reads while the status is unchanged')
    pg.evaluate("window.__C_TABLES.orders[0].status='pickedup'"); reload(pg); pg.evaluate('TLB.statusAt("ord1")'); pg.wait_for_timeout(300)
    a = pg.evaluate('TLB.statusAt("ord1")')
    ok(a['at'] is None and a['state'] == 'none', 'C-2 no pickedup event -> unknown (not the courier position / refresh time): %s' % a)
    pg.evaluate("window.__C_TABLES.orders[0].status='pending'"); reload(pg); pg.wait_for_timeout(300)
    a = pg.evaluate('TLB.statusAt("ord1")'); ca = pg.evaluate('TLB.order("ord1").createdAt')
    ok(a['at'] in (ca,) or a['source'] == 'event', 'C-2 pending: its own event or the order placement time (%s)' % a['source'])
    ok(not errs, 'no page errors %s' % errs[:2]); ctx.close()
    ctx, pg, errs = boot(b, 'preparing'); pg.evaluate('window.__EV_ERR=true;TLB.statusAt("ord1")'); pg.wait_for_timeout(400)
    a = pg.evaluate('TLB.statusAt("ord1")')
    ok(a['at'] is None and a['state'] == 'unreadable', 'C-2 events not readable (e.g. no customer permission) -> «unreadable», no substitute time')
    ctx.close()
    # ---------- C-3 mapping ----------
    ctx, pg, errs = boot(b, 'preparing')
    table = pg.evaluate("""()=>{const r={};for(const s of ['pending','preparing','ready','pickedup','delivered','cancelled'])for(const d of [null,'drv']){const x=TLB.trackStatus({status:s,driver:d});r[s+'/'+(d?'D':'-')]=[x.restaurant.key,x.courier&&x.courier.key,x.ended]}return r}""")
    want = {'pending/-': ['jrPending', None, None], 'preparing/-': ['jrPreparing', 'jcSearching', None], 'preparing/D': ['jrPreparing', 'jcAssigned', None],
            'ready/-': ['jrReady', 'jcSearching', None], 'ready/D': ['jrReady', 'jcAssigned', None], 'pickedup/D': ['jrHanded', 'jcOnWay', None],
            'delivered/D': ['jrHanded', 'jcDelivered', 'delivered'], 'cancelled/-': ['jrEnded', None, 'cancelled']}
    ok(all(table[k] == v for k, v in want.items()), 'C-3 mapping (driver assigned never = ready): ' + json.dumps({k: table[k] for k in want}, ensure_ascii=False))
    ok(pg.evaluate("TLB.trackStatus({status:'preparing',driver:'d'}).courier.label") == 'Назначен', 'C-3 labels from the dictionary (RU)')
    # ---------- C-6 payment parts (31 Oct): order 9115 values as seen on the phone; stored values only ----------
    pp = pg.evaluate("TLB.paymentParts({total:315,walletUsed:153.52,payment:'cash',pointsValue:0})")
    ok(pp == {'total': 315, 'wallet': 153.52, 'rest': 161.48, 'method': 'cash', 'restCash': True, 'mixed': True, 'points': 0},
       'C-6 order 9115 shape: wallet 153.52 + cash to the courier 161.48 = total 315, mixed: %s' % pp)
    drv = pg.evaluate("Math.max(0,Math.round(((315)-(153.52))*100)/100)")
    ok(pp['rest'] == drv, 'C-6 rest equals the driver app due() rule (%s)' % drv)
    full = pg.evaluate("TLB.paymentParts({total:120,walletUsed:120,payment:'wallet'})"); cash = pg.evaluate("TLB.paymentParts({total:120,walletUsed:0,payment:'cash'})")
    ok(full['rest'] == 0 and not full['mixed'] and not full['restCash'] and cash['rest'] == 120 and not cash['mixed'] and cash['restCash'],
       'C-6 wallet-only and cash-only orders are not «mixed»')
    # ---------- C-5 store link + QR ----------
    link = pg.evaluate('TLB.storeLink(%s)' % json.dumps(UUID.upper()))
    u = pg.evaluate('location.href')
    ok(link == (ROOT / 'customer.html').as_uri() + '?store=' + UUID, 'C-5 link = customer app next to the page + ?store=<id>: %s' % link)
    ctx.close()
    ctx, pg, errs = boot(b, 'preparing', '?g=abc&token=SECRET&access_token=x#hash')
    link = pg.evaluate('TLB.storeLink(%s)' % json.dumps(UUID))
    q = dict(re.findall(r'[?&]([^=&#]+)=([^&#]*)', link))
    ok(list(q) == ['store'] and 'SECRET' not in link and '#' not in link, 'C-5 no session / query / hash of the current page carried: %s' % link)
    ok(pg.evaluate("TLB.storeLink('s1')") is None and pg.evaluate("TLB.storeLink('x',null)") is None, 'C-5 invalid store id -> null')
    pub = pg.evaluate('TLB.storeLink(%s,"https://merapplications-sketch.github.io/Talabat-v3/customer.html?old=1")' % json.dumps(UUID))
    ok(pub == 'https://merapplications-sketch.github.io/Talabat-v3/customer.html?store=' + UUID, 'C-5 explicit app URL: %s' % pub)
    svg = pg.evaluate('TLB.qrSvg(%s)' % json.dumps(pub))
    ok(svg.startswith('<svg') and 'script' not in svg.lower(), 'C-5 QR rendered as SVG (pinned qrcode-generator 1.4.4, SRI)')
    pg.add_script_tag(path=str(JSQR))
    dec = pg.evaluate("""svg=>new Promise(res=>{const i=new Image();i.onload=()=>{const c=document.createElement('canvas');c.width=i.width*2;c.height=i.height*2;const x=c.getContext('2d');
      x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);x.drawImage(i,0,0,c.width,c.height);const d=x.getImageData(0,0,c.width,c.height);const r=jsQR(d.data,c.width,c.height);res(r&&r.data)};
      i.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg)})""", svg)
    ok(dec == pub, 'C-5 QR decodes back to exactly the link: %s' % dec)
    ctx.close()
    ctx, pg, errs = boot(b, 'preparing', qr_body=QR + b'\n/*tampered*/')
    r = pg.evaluate('TLB.qrSvg("x").then(()=>"ok",e=>String(e.message))')
    ok(r == 'qr_unavailable', 'C-5 a changed library is refused by Subresource Integrity (%s)' % r)
    ctx.close()
    # the decoded link opens the right store in the customer app
    ctx, pg, errs = boot(b, 'preparing', '?store=' + UUID)
    pg.wait_for_function('()=>typeof S!=="undefined"&&S.store', timeout=15000)
    name = pg.evaluate("(window.__C_TABLES.stores.find(s=>s.id===%s)||{}).name" % json.dumps(UUID))
    ok(pg.evaluate('S.store') == name and 'store=' not in pg.evaluate('location.href'), 'C-5 the link opens that store (%s…) and the id is removed from the address bar' % (name or '')[:24])
    ok(not errs, 'no page errors %s' % errs[:2]); ctx.close()
    b.close()
print('\nCORE CONTRACTS CHECK %s' % ('FAILS %d' % len(fails) if fails else 'OK')); sys.exit(1 if fails else 0)
