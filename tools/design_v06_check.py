"""Design v06.1 — batch 1 (store page → dish sheet → cart) on the real customer.html with the qa_all fixture (mocked
Supabase; place_order is captured, nothing is sent anywhere). Chromium only — NOT proof for iPhone Safari.
  A. behaviour: cart line = dish + options + request (note); same dish with other options / notes stays apart; quantity,
     remove and «Вернуть» keep the note; saved cart (reload) keeps it; the notes reach place_order and group_add; the
     restaurant comment goes on the first line without its own request and is never cut; add button states (white + →
     orange ✓ only after the dish is really in the cart; options open the sheet first; required choice blocks the add).
  B. layout at 360 / 390 / 430, RU and EN: no horizontal overflow, targets ≥ 44, fields ≥ 16 px, sheet ≤ min(560, 66 % of
     the screen), title + quantity / add outside the options scroll, the request field reachable on a small screen and with
     a keyboard-sized screen, no tabs, no demo values, no raw text keys.
  C. batches 2–3 (10 pages: Home B, search, list, «for you», checkout, order details, wallet, profile, address) at
     360 / 390 / 430, RU and EN, with and without photos: no overflow, targets ≥ 44, fields ≥ 16 px, no raw keys / demo
     values / design pictures, photo slots; Home: original logo, 6 categories in one row, every admin banner kept,
     Home B order, sections without data hidden; list: every store once, «Для вас» = your stores.
  python3 tools/design_v06_check.py"""
import os, sys, json, re
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..'))
P1, P2 = '11111111-1111-4111-8111-111111111111', '22222222-2222-4222-8222-222222222222'
FIX = open(os.path.join(here, 'qa_all.py')).read().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE', '"customer"').replace(
    'var groups=', "items.push({id:'%s',store_id:'s1',name:'Плов',price:40,image_url:'',popular:false,available:true,approved:true,section:'Салаты',discount_pct:0,created_at:iso(1)});"
                   "items.push({id:'%s',store_id:'s1',name:'Чай',price:10,image_url:'',popular:false,available:true,approved:true,section:'Салаты',discount_pct:0,created_at:iso(1)});var groups=" % (P1, P2), 1)
SPY = """(function(){var cc=window.supabase.createClient;window.__rpcs=[];window.__gadd=[];
 window.supabase.createClient=function(){var c=cc.apply(this,arguments),r=c.rpc;c.rpc=function(n,a){if(n==='place_order'){window.__rpcs.push(a);return Promise.resolve({data:777,error:null})}
  if(n==='group_add'){window.__gadd.push(a);return Promise.resolve({data:Object.assign({},window.__GRP,{items:[]}),error:null})}return r.call(c,n,a)};return c}})();"""
fails = []; n = 0
def ok(c, m):
    global n; n += 1; print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
def page(b, w, h=844, lang='ru'):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=True, has_touch=True); pg = ctx.new_page(); errs = []; dlg = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: (dlg.append(d.message), d.accept()))
    pg.route('**/*', lambda rt, rq: (rt.fulfill(status=200, content_type='application/javascript', body=FIX + SPY) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
    pg.goto('file://' + root + '/customer.html', wait_until='domcontentloaded'); pg.wait_for_timeout(2200); pg.evaluate("(l)=>TLB.setLang(l)", lang); return ctx, pg, errs, dlg

with sync_playwright() as p:
    b = p.chromium.launch()
    # ======================= A. behaviour =======================
    ctx, pg, errs, dlg = page(b, 390); E = pg.evaluate
    r = E("""()=>{const weird=`без лука, "острый" ~ ^ % 'x' (2) 🌶 <b>`;const k=lk('i1',['o12','o11'],weird),p=pk(k);
      return {k,id:p.id,ops:p.ops,note:p.note,weird:weird.replace(/\\s+/g,' ').trim(),plain:lk('i1',[],''),safe:/^[A-Za-z0-9%._~^,-]+$/.test(k),old:JSON.stringify(pk('i1~o11'))}}""")
    ok(r['id'] == 'i1' and r['ops'] == ['o11', 'o12'] and r['note'] == r['weird'], 'key round trip: dish + options + request (quotes, ~ ^ %%, emoji, tags) → %s' % r['note'])
    ok(r['safe'], 'key holds only safe characters (it is used inside onclick=\'…\'): %s' % r['k'][:60])
    ok(r['plain'] == 'i1' and r['old'] == '{"id":"i1","ops":["o11"],"note":""}', 'old keys (no request) read exactly as before')
    # the same dish: plain / other options / other requests stay separate lines
    r = E("""()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;S.store=s.n;go('menu',{store:s.n});
      const put=(ops,note,q)=>{openItem('i1');S.sh.sel={};ops.forEach(o=>{const g=TLB.optionsOf('i1').find(g=>g.options.some(x=>x.id==o));shPick(g.id,o,g.max)});S.sh.note=note;S.sh.q=q;shAdd()};
      put(['o11'],'',1);put(['o12'],'',1);put(['o11'],'без лука',2);put(['o11'],'острее',1);put(['o11'],'без лука',1);
      return {keys:Object.keys(S.cart),q:Object.values(S.cart),total:qtyOf('i1')}}""")
    ok(len(r['keys']) == 4 and r['q'] == [1, 1, 3, 1] and r['total'] == 6, 'same dish: other options / other requests = separate lines; the same request again adds to its line: %s' % r['q'])
    keys = r['keys']
    r = E("""(ks)=>{go('cart');add(ks[2],1);add(ks[2],-1);const q1=S.cart[ks[2]];delLine(ks[2]);const gone=!(ks[2] in S.cart),undo=!!document.getElementById('cundo');
      undoLine();const back=Object.keys(S.cart);return {q1,gone,undo,back,q:S.cart[ks[2]],note:pk(back[2]).note,shown:document.body.innerText.includes('без лука')}}""", keys)
    ok(r['q1'] == 3 and r['gone'] and r['undo'], 'quantity +/− keeps the line; remove shows «Вернуть»')
    ok(r['back'] == keys and r['q'] == 3 and r['note'] == 'без лука' and r['shown'], '«Вернуть» brings the same line back: same place, quantity 3, request kept and shown')
    r = E("""()=>{const k=Object.keys(S.cart)[3];delLine(k);const keep=JSON.stringify(S.cartUndo&&S.cartUndo.key);go('menu',{store:S.cartStore});go('cart');return {undo:!!document.getElementById('cundo'),keep}}""")
    ok(not r['undo'], 'leaving the cart drops the pending «Вернуть» (no stale card later)')
    # last line removed: the cart stays open with «Вернуть»; the comment comes back too
    r = E("""()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;S.cart[lk('i2',[],'хорошо прожарить')]=1;S.note='позвонить у двери';go('cart');
      delLine(Object.keys(S.cart)[0]);const v=S.v,undo=!!document.getElementById('cundo'),note0=S.note;undoLine();return {v,undo,note0,keys:Object.keys(S.cart),note:S.note}}""")
    ok(r['v'] == 'cart' and r['undo'] and r['keys'] == [E("()=>lk('i2',[],'хорошо прожарить')")] and r['note'] == 'позвонить у двери',
       'last line removed: the cart stays with «Вернуть»; undo restores the line and the restaurant comment')
    # saved cart (reload) keeps the request lines
    E("""()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;S.cart[lk('i1',['o11'],'без лука')]=2;S.cart[lk('i1',['o11'],'')]=1;S.note='';go('cart')}""")
    want = E("()=>Object.keys(S.cart)")
    pg.goto('file://' + root + '/customer.html', wait_until='domcontentloaded'); pg.wait_for_timeout(2200)
    ok(E("()=>Object.keys(S.cart)") == want and E("()=>Object.values(S.cart)") == [2, 1], 'saved cart (reload) keeps both lines and the request')
    # requests reach place_order; the comment goes on the first line without its own request
    r = E("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;S.cart[lk('%s',[],'без лука')]=1;S.cart[lk('%s',[],'')]=2;S.cart[lk('%s',[],'с лимоном')]=1;
      S.note='код домофона 12';go('pay');await quoteNow();await place();const a=window.__rpcs[window.__rpcs.length-1];return a.p_items.map(x=>[x.qty,x.note])}""" % (P1, P1, P2))
    ok(r == [[1, 'без лука'], [2, 'код домофона 12'], [1, 'с лимоном']], 'place_order: each line carries its request; the comment rides on the first line without one: %s' % r)
    r = E("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;S.cart[lk('%s',[],'без лука')]=1;S.note='код 12';go('pay');await quoteNow();await place();
      return window.__rpcs[window.__rpcs.length-1].p_items.map(x=>x.note)}""" % P1)
    ok(r == ['без лука · код 12'], 'every line has a request → the comment is joined to the first one: %s' % r)
    r = E("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;S.cart[lk('%s',[],'%s')]=1;go('cart');const cap=+document.getElementById('nt').maxLength;
      S.note='%s';const n0=window.__rpcs.length;go('pay');await quoteNow();await place();return {cap,sent:window.__rpcs.length-n0,v:S.v}}""" % (P1, 'х' * 110, 'к' * 20))
    ok(r['cap'] == 7 and r['sent'] == 0 and r['v'] == 'cart' and any('не помещается' in m for m in dlg),
       'no silent cut: the comment field is capped (7 left) and an over-long joined note is refused before sending (%s)' % r)
    r = E("""async()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;S.cart[lk('%s',[],'без лука')]=1;S.cart[lk('%s',[],'')]=1;S.note='для офиса';
      S.gid=window.__GRP.id;S.grp=window.__GRP;await grpPush(true);return window.__gadd.map(a=>a.p_note)}""" % (P1, P2))
    ok(r == ['без лука', 'для офиса'], 'group order: each line keeps its request, the comment on the first free line: %s' % r)
    E("()=>{S.gid=null;S.grp=null;try{localStorage.removeItem(GK())}catch(e){}}")
    # re-order keeps today's behaviour (old notes are not copied: the old comment was stored as a line note)
    r = E("()=>{reorder('ord4');return S.ro&&S.ro.lines.map(l=>l.key)}")
    ok(r and all('^' not in k for k in r), 're-order: line keys without old notes (unchanged behaviour)')
    E("()=>{S.ro=null}")
    # add control states
    r = E("""()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;go('menu',{store:s.n});const q=id=>[...document.querySelectorAll('.d6-add')].filter(b=>b.getAttribute('aria-label').includes(menuOf(s.n).find(i=>i.id==id).name));
      const before=q('i2').map(b=>b.className);addFrom('i2');const after=q('i2').map(b=>b.className+'|'+(b.querySelector('b')||{}).textContent);
      openItem('i1');const sheet=!!S.sh,cart1=Object.keys(S.cart).length;shAdd();const miss=!!document.querySelector('.og.miss'),cart2=Object.keys(S.cart).length;
      return {before,after,sheet,cart1,cart2,miss}}""")
    ok(all(c == 'd6-add' for c in r['before']) and r['before'], 'add button: white + while the dish is not in the cart (%d buttons)' % len(r['before']))
    ok(any(a.startswith('d6-add on|1') for a in r['after']), 'add button: orange ✓ with the quantity only after the dish is really in the cart: %s' % r['after'][:2])
    ok(r['sheet'] and r['cart1'] == r['cart2'] and r['miss'], 'dish with options: + opens the sheet; with a required choice missing the add is refused (cart unchanged, group marked)')
    r = E("""()=>{const g=TLB.optionsOf('i1').find(g=>g.required);shPick(g.id,g.options[0].id,g.max);shAdd();return {sh:S.sh,on:[...document.querySelectorAll('.d6-add.on')].length}}""")
    ok(r['sh'] is None and r['on'] >= 2, 'after the required choice the dish is added, the sheet closes, both dishes show ✓')
    ok(not errs, 'behaviour: no JS errors %s' % errs[:2])
    ctx.close()
    # ======================= B. layout =======================
    for lang in ('ru', 'en'):
        for w in (360, 390, 430):
            ctx, pg, errs, dlg = page(b, w, 844 if w != 360 else 780, lang); E = pg.evaluate; tag = '%s %d' % (lang.upper(), w)
            E("""()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;go('menu',{store:s.n});addFrom('i2')}"""); pg.wait_for_timeout(300)
            r = E("""()=>{const W=document.documentElement.clientWidth,over=[...document.querySelectorAll('.d6 *')].filter(e=>{const b=e.getBoundingClientRect();return b.width&&b.right>W+1&&!e.closest('.d6-rail,.d6-ofs,.brw')}).map(e=>e.className).slice(0,3);
              const small=[...document.querySelectorAll('.d6-add,.d6-circ,.d6-more,.d6-q button,.d6-cbar')].filter(e=>{const b=e.getBoundingClientRect();return b.width&&(b.width<43.5||b.height<43.5)}).length;
              const fld=[...document.querySelectorAll('.d6 input,.d6 textarea')].filter(e=>parseFloat(getComputedStyle(e).fontSize)<16).length;
              const txt=document.body.innerText;return {over,small,fld,tabs:!!document.querySelector('.d6 .tabs,.d6 [role=tablist]'),secs:document.querySelectorAll('.msec').length,
                demo:/Демо|Demo|McDonald|Биг Мак|Big Mac|Мин\\. заказ|Min\\. order|Комбо|Combo/.test(txt),raw:(txt.match(/\\bd6[A-Z][A-Za-z]*\\b/)||[''])[0],
                imgs:[...document.querySelectorAll('.d6 img')].map(i=>i.getAttribute('src')).filter(s=>/Assets\\/|raster-|windows\\//.test(s)).length,
                cols:document.querySelectorAll('.d6-stat').length,sx:document.documentElement.scrollWidth>W+1}}""")
            ok(not r['over'] and not r['sx'], '%s store page: no horizontal overflow %s' % (tag, r['over']))
            ok(r['small'] == 0 and r['fld'] == 0, '%s store page: every target ≥ 44 px, fields ≥ 16 px' % tag)
            ok(not r['tabs'] and r['secs'] > 1, '%s store page: one vertical scroll with section titles, no tabs' % tag)
            ok(not r['demo'] and not r['raw'] and r['imgs'] == 0, '%s store page: no demo values / design pictures / raw keys %s' % (tag, r['raw']))
            ok(r['cols'] == 2, '%s info card: only real columns (time + delivery; no minimum order)' % tag)
            # dish sheet
            for h in ((844 if w != 360 else 780), 560, 420):
                pg.set_viewport_size({'width': w, 'height': h}); E("()=>{openItem('i1')}"); pg.wait_for_timeout(250)
                r = E("""(h)=>{const P=document.querySelector('.d6s-p').getBoundingClientRect(),O=document.querySelector('.osh'),F=document.querySelector('.oshf').getBoundingClientRect(),I=document.querySelector('.d6s-in').getBoundingClientRect();
                  const lim=h>560?Math.min(560,h*0.66):h-56;   /* ≤ 560 px high (keyboard open / small screen): screen − 56 so nothing is cut */O.scrollTop=O.scrollHeight;const T=document.getElementById('shn').getBoundingClientRect(),Ob=O.getBoundingClientRect();
                  const add=document.querySelector('.oshf .btn').getBoundingClientRect();
                  return {ph:Math.round(P.height),lim:Math.round(lim),inside:F.bottom<=h+0.5&&F.top>=P.top,title:I.top>=P.top-1&&I.bottom<=Ob.top+1,
                    note:T.top>=Ob.top-1&&T.bottom<=Ob.bottom+1,addv:add.bottom<=h+0.5&&add.height>=51,scroll:O.scrollHeight>O.clientHeight}}""", h)
                ok(r['ph'] <= r['lim'] + 1 and r['inside'] and r['addv'] and r['title'],
                   '%s sheet %dpx high: panel %d ≤ %d; title above and quantity / add below the options scroll, add visible' % (tag, h, r['ph'], r['lim']))
                ok(r['note'], '%s sheet %dpx high: the options scroll reaches the request field (nothing cut)' % (tag, h))
                E("()=>{shClose()}")
            pg.set_viewport_size({'width': w, 'height': 844 if w != 360 else 780})
            # cart
            E("""()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};S.cartStore=s.n;S.cart[lk('i1',['o11'],'без лука и очень длинная просьба про соус и подачу блюда')]=2;S.cart.i2=1;go('cart')}"""); pg.wait_for_timeout(300)
            r = E("""()=>{const W=document.documentElement.clientWidth,over=[...document.querySelectorAll('.d6 *')].filter(e=>{const b=e.getBoundingClientRect();return b.width&&b.right>W+1&&!e.closest('.d6-rail')}).length;
              const small=[...document.querySelectorAll('.d6-add,.d6-circ,.d6-q button,.d6-undo,.fbar .btn')].filter(e=>{const b=e.getBoundingClientRect();return b.width&&(b.width<43.5||b.height<43.5)}).length;
              const fld=[...document.querySelectorAll('.d6 input,.d6 textarea')].filter(e=>parseFloat(getComputedStyle(e).fontSize)<16).length;
              const last=document.querySelector('.d6-cmt').getBoundingClientRect().bottom+scrollY,dock=document.querySelector('.fbar').getBoundingClientRect().height;
              return {over,small,fld,reach:document.documentElement.scrollHeight>=last+dock-1,txt:document.body.innerText}}""")
            ok(r['over'] == 0 and r['small'] == 0 and r['fld'] == 0, '%s cart: no overflow, targets ≥ 44, fields ≥ 16 px' % tag)
            ok(r['reach'], '%s cart: the comment can be scrolled above the fixed buttons' % tag)
            want = ('Особые пожелания' if lang == 'ru' else 'Special requests')
            ok(want in r['txt'] and not re.search(r'\bd6[A-Z]', r['txt']), '%s cart: request shown with its label, no raw keys' % tag)
            ok(not errs, '%s: no JS errors %s' % (tag, errs[:1]))
            ctx.close()

    # ======================= C. batches 2–3: Home B, list, checkout, order details, wallet, profile, address =======================
    PIC = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='40'%3E%3Crect width='60' height='40' fill='%23c86'/%3E%3C/svg%3E"
    VIEWS = [('home', "S.q='';go('home')"), ('home search', "S.q='пл';go('home')"), ('list', "S.q='';S.srt='';S.fo=false;S.cq='';go('cat',{catKey:'rest'})"),
             ('list all', "go('cat',{catKey:'*'})"), ('list «for you»', "S.srt='mine';render()"),
             ('checkout', "S.srt='';S.cart={i2:2};S.cartStore=ALLS.find(x=>x.id=='s1').n;go('pay')"), ('order details', "TLB.proofUrl=()=>Promise.resolve(null);go('track',{tid:'ord4'})"),
             ('wallet', "go('wallet')"), ('profile', "go('me')"), ('address', "editAddr(addrs()[0].id)")]
    for lang in ('ru', 'en'):
        for w in (360, 390, 430):
            for photos in (False, True):
                ctx, pg, errs, dlg = page(b, w, 844 if w != 360 else 780, lang); E = pg.evaluate; tag = '%s %d %s' % (lang.upper(), w, 'photos' if photos else 'no photos')
                if photos:
                    E("""(P)=>{ALLS.forEach(s=>{s.i=P;s.lg=P});const f=TLB.allMenus;TLB.allMenus=function(){const o=f.apply(this,arguments);Object.values(o).forEach(l=>l.forEach(i=>{i.image=P}));return o};render()}""", PIC)
                bad = []
                for name, js in VIEWS:
                    E("()=>{" + js + ";render();scrollTo(0,0)}"); pg.wait_for_timeout(250)
                    r = E("""()=>{const W=document.documentElement.clientWidth,R='.d6-rl,.d6-nr,.d6-bsc,.chips,.bbs,.d6-rail,.hs';
                      const over=[...document.querySelectorAll('#app *')].filter(e=>{const b=e.getBoundingClientRect();return b.width&&b.right>W+1&&!e.closest(R)&&getComputedStyle(e).position!='fixed'}).map(e=>e.className||e.tagName).slice(0,3);
                      /* .vh = screen-reader-only alternative to the 2-second hold (not a visible tap target) */const small=[...document.querySelectorAll('.d6 button:not(.vh),.d6 [role=button],.d6 a[href],.nav>div')].filter(e=>{const b=e.getBoundingClientRect();return b.width&&(b.width<43.5||b.height<43.5)}).map(e=>(e.className||e.tagName)+':'+Math.round(e.getBoundingClientRect().width)+'x'+Math.round(e.getBoundingClientRect().height)).slice(0,3);
                      const fld=[...document.querySelectorAll('#app input,#app textarea,#app select')].filter(e=>e.type!='hidden'&&e.getBoundingClientRect().width&&parseFloat(getComputedStyle(e).fontSize)<16).length;
                      const txt=document.getElementById('app').innerText;
                      return {over,small,fld,sx:document.documentElement.scrollWidth>W+1,wrap:!!document.querySelector('#app>.d6'),
                        raw:(txt.match(/\\bd6[A-Z][A-Za-z_]*\\b|\\bundefined\\b|\\bNaN\\b|\\{[a-z]\\}/)||[''])[0],
                        demo:(txt.match(/Демо|ДЕМО|DEMO|Demo|Dubai|Дубай|Аль Барша|Pizza Hut|KFC|Carrefour|Burger House|SushiArt|Basilico|Burger Lab|Мин\\. заказ|Min\\. order/)||[''])[0],
                        dimg:[...document.querySelectorAll('#app img')].map(i=>i.getAttribute('src')||'').filter(s=>/Assets\\/|raster-|windows\\/|References\\//.test(s)).length,
                        none:document.querySelectorAll('.d6 .d6-ph.none').length,pics:[...document.querySelectorAll('.d6 .d6-ph>img')].filter(i=>i.complete&&i.naturalWidth>0).length}}""")
                    if r['over'] or r['sx']: bad.append('%s overflow %s' % (name, r['over']))
                    if r['small']: bad.append('%s small targets %s' % (name, r['small']))
                    if r['fld']: bad.append('%s field < 16 px' % name)
                    if not r['wrap']: bad.append('%s not in the design layer' % name)
                    if r['raw'] or r['demo'] or r['dimg']: bad.append('%s raw/demo %s %s %d' % (name, r['raw'], r['demo'], r['dimg']))
                    if name in ('home', 'list'):
                        if photos and (r['none'] or not r['pics']): bad.append('%s photos: %d empty slots, %d shown' % (name, r['none'], r['pics']))
                        if not photos and (r['pics'] or not r['none']): bad.append('%s no photos: %d pictures, %d «no photo» slots' % (name, r['pics'], r['none']))
                ok(not bad, '%s: 10 pages — no overflow, targets ≥ 44, fields ≥ 16 px, design layer, no raw keys / demo values / design pictures, photo slots %s' % (tag, bad[:3]))
                ok(not errs, '%s: no JS errors %s' % (tag, errs[:1]))
                if w == 390 and not photos:
                    E("()=>{S.q='';go('home');render()}")
                    r = E("""()=>{const H=document.querySelector('.d6h');const ord=[...H.querySelectorAll('.d6-hh,.d6-bento,.d6-cats,.d6-sh h2,.d6-dn')].map(e=>e.className||e.textContent.trim());
                      return {logo:(H.querySelector('.d6-logo')||{}).getAttribute?H.querySelector('.d6-logo').getAttribute('src'):'',logoOk:H.querySelector('.d6-logo').naturalWidth>0,
                        cats:H.querySelectorAll('.d6-cats .d6-ct').length,catsRow:new Set([...H.querySelectorAll('.d6-cats .d6-ct')].map(e=>Math.round(e.getBoundingClientRect().top))).size,
                        bn:TLB.banners().filter(b=>(b.placement||'top')=='top').length,bnIn:H.querySelectorAll('.d6-bento [onclick^="bannerGo"]').length,
                        bot:TLB.banners().filter(b=>b.placement=='bottom').length,botIn:H.querySelectorAll('.bbs [onclick^="bannerGo"]').length,
                        ord,heads:[...H.querySelectorAll('.d6-sh h2')].map(e=>e.textContent.trim()),sq:!!document.getElementById('sq'),bell:!!H.querySelector('[onclick^="S.ntf=true"]'),
                        reo:H.querySelectorAll('.d6-lo [onclick^="reorder("]').length,del:TLB.orders().filter(o=>o.status=='delivered'&&o.items&&o.items.length).length}}""")
                    ok(r['logo'] == 'assets/brand/talabot-ru.png' and r['logoOk'], '%s Home: the original logo file is shown (%s)' % (tag, r['logo']))
                    ok(r['cats'] == 6 and r['catsRow'] == 1, '%s Home: the six categories in one row' % tag)
                    ok(r['bnIn'] == r['bn'] and r['botIn'] == r['bot'], '%s Home: every admin banner kept — top %d/%d in the bento, partners %d/%d' % (tag, r['bnIn'], r['bn'], r['botIn'], r['bot']))
                    ok(r['sq'] and r['bell'] and r['reo'] == min(10, r['del']), '%s Home: search, notifications, «order again» on each delivered order (%d)' % (tag, r['reo']))
                    want = ['Ваши любимые снова', 'Лучшие предложения', 'Популярные рестораны', 'Рекомендуем для вас'] if lang == 'ru' else ['Your favourites again', 'Best offers', 'Popular restaurants', 'Recommended for you']
                    hs = r['heads']; ok(all(x in hs for x in want) and [hs.index(x) for x in want] == sorted(hs.index(x) for x in want), '%s Home: Home B order %s' % (tag, hs))
                    ok(not any(re.search(x, ' '.join(hs)) for x in ('Флеш', 'Flash', 'Смотрите', 'Discover')), '%s Home: no section without data (flash sale by category, editorial)' % tag)
                    # list: every store of the category exactly once, sections, «for you» = stores you ordered from
                    r = E("""()=>{S.srt='';S.fo=false;S.cq='';go('cat',{catKey:'*'});render();const ids=[...document.querySelectorAll('.d6l .d6-sr')].map(e=>e.getAttribute('onclick'));
                      const n=STORES.length,u=new Set(ids).size;S.srt='mine';render();const mine=[...document.querySelectorAll('.d6l .d6-sr .nt')].map(e=>e.textContent),want=[...new Set(TLB.orders().filter(o=>o.status=='delivered').map(o=>o.store))].filter(x=>STORES.some(s=>s.n==x));
                      S.srt='';render();document.querySelector('.d6-l3 .a').click();const disc=S.srt;go('home');return {n,len:ids.length,u,mine:mine.sort(),want:want.sort(),disc}}""")
                    ok(r['len'] == r['n'] and r['u'] == r['n'], '%s list: every store shown exactly once across the sections (%d/%d)' % (tag, r['u'], r['n']))
                    ok(r['mine'] == r['want'] and r['disc'] == 'disc', '%s list: «Для вас» = the stores of your delivered orders %s; «Скидки» tile = the discount filter' % (tag, r['mine']))
                ctx.close()
    b.close()
print('\nDESIGN v06 CHECK %d/%d' % (n - len(fails), n)); sys.exit(1 if fails else 0)
