#!/usr/bin/env python3
"""AH-04/05/06: original four-app HTML, synthetic SDK, offline WebKit only.

The login feed is supplied through the public presentation-provider contract.
Authentication still runs through the original controls, core, and app callbacks.
No production service, account, database, or permission change is used.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

import brief31_webkit as prior

ROOT = Path.cwd()
ROLES = ('customer', 'driver', 'merchant', 'admin')
DEFAULT_IDS = ['ah06-fallback-free', 'ah06-fallback-happy', 'ah06-fallback-dineout']
AUTH_SESSION = "getSession:function(){return Promise.resolve({data:{session:{user:user,access_token:'x'}},error:null})}"
AUTH_SIGNIN = "signInWithPassword:function(){return Promise.resolve({error:{message:'x'}})}"

AUTH_EXTRA = r"""
  window.__AH06SessionKey='ah06-fixture-session-'+role;
  window.__AH06SignedIn=!!sessionStorage.getItem(window.__AH06SessionKey);
  window.__AH06DataCalls=[];
  window.__AH06AuthOutcome='success';
  function ah06AuthTrace(kind,email){
    if(window.__ah06AuthTrace)window.__ah06AuthTrace({kind,role,email:email||''});
  }
"""

FORM_OBSERVER = r"""
  window.__AH06OriginalForms=[];
  new MutationObserver(()=>{
    const email=document.getElementById('tlb-em'),go=document.getElementById('tlb-go');
    if(!email||!go||typeof go.onclick!=='function'||
       window.__AH06OriginalForms.some(f=>f.email===email))return;
    const ids=['tlb-t-in','tlb-t-up','tlb-nm','tlb-ph','tlb-em','tlb-pw','tlb-eye','tlb-er','tlb-go'];
    const nodes=ids.map(id=>document.getElementById(id)).filter(Boolean);
    window.__AH06OriginalForms.push({email,card:email.parentElement,nodes,
      attrs:nodes.map(e=>['type','autocomplete','autocapitalize','inputmode','maxlength','data-i18n','data-i18n-ph'].map(a=>e.getAttribute(a))),
      handlers:nodes.map(e=>[e.onclick,e.onkeydown])});
  }).observe(document,{childList:true,subtree:true});
"""


def overlay_sdk(role, mode, extra=''):
    source = prior.sdk(AUTH_EXTRA + extra, role=role)
    assert source.count(AUTH_SESSION) == source.count(AUTH_SIGNIN) == 1
    session = ("getSession:function(){ah06AuthTrace('getSession');return new Promise(function(){})}" if mode == 'loading' else
               "getSession:function(){ah06AuthTrace('getSession');return Promise.resolve({data:{session:window.__AH06SignedIn?{user:user,access_token:'fixture'}:null},error:null})}")
    signin = r"""signInWithPassword:function(args){
      ah06AuthTrace('signIn',args.email);
      if(window.__AH06AuthOutcome==='error')return Promise.resolve({data:{user:null,session:null},error:{message:'Invalid login credentials',code:'invalid_credentials'}});
      window.__AH06SignedIn=true;sessionStorage.setItem(window.__AH06SessionKey,'1');
      return Promise.resolve({data:{user:user,session:{user:user,access_token:'fixture'}},error:null})
    },signUp:function(args){ah06AuthTrace('signUp',args.email);return Promise.resolve({data:{user:user,session:null},error:null})},
    resend:function(){ah06AuthTrace('resend');return Promise.resolve({error:null})}"""
    source = source.replace(AUTH_SESSION, session).replace(AUTH_SIGNIN, signin)
    client = 'createClient:function(){return {auth:'
    assert source.count(client) == 1
    source = source.replace(client, "createClient:function(url,key,options){if(window.__ah06ClientTrace)window.__ah06ClientTrace({role,storageKey:options&&options.auth&&options.auth.storageKey});return {auth:")
    signout = 'signOut:function(){return Promise.resolve({})}'
    assert source.count(signout) == 1
    source = source.replace(signout, "signOut:function(){ah06AuthTrace('signOut');window.__AH06SignedIn=false;sessionStorage.removeItem(window.__AH06SessionKey);return Promise.resolve({error:null})}")
    marker = 'function chain(kind,name){var single=false'
    assert source.count(marker) == 1
    source = source.replace(marker, "function chain(kind,name){window.__AH06DataCalls.push({kind,name,signedIn:window.__AH06SignedIn});var single=false")
    marker = "if(p==='then')return function(ok,bad){var d;"
    assert source.count(marker) == 1
    source = source.replace(marker, marker + "if(!window.__AH06SignedIn)return Promise.resolve({data:null,error:{code:'42501',message:'Fixture denies unauthenticated database access'}}).then(ok,bad);")
    return source


@contextmanager
def overlay_page(run, browser, server, photos, role='customer', lang='ru', width=375,
                 mode='login', reduced=False, query='', extra=''):
    trace = {'case': run.case, 'role': role, 'language': lang, 'width': width, 'mode': mode,
             'blocked': [], 'page_errors': [], 'http_errors': [], 'failed_local_requests': [],
             'navigation_cancellations': [], 'auth': [], 'clients': []}
    context = browser.new_context(viewport={'width': width, 'height': 844 if width >= 390 else 812},
                                  is_mobile=True, has_touch=True, device_scale_factor=1,
                                  service_workers='block', reduced_motion='reduce' if reduced else 'no-preference')
    context.set_default_timeout(7000)
    context.add_init_script('localStorage.setItem("tlb_lang",' + json.dumps(lang) + ');' + FORM_OBSERVER)
    context.expose_function('__ah06AuthTrace', lambda event: trace['auth'].append(event))
    context.expose_function('__ah06ClientTrace', lambda event: trace['clients'].append(event))
    sources = {role: overlay_sdk(role, mode, extra)}

    def route(request):
        url = urlsplit(request.request.url)
        if url.hostname == 'cdn.jsdelivr.net' and 'supabase-js' in url.path:
            # Staff fallback links load the original customer entry document.
            # Each app receives its own signed-out fixture; sessions are never
            # carried across roles by the test transport.
            document_role = urlsplit(request.request.frame.url).path.rsplit('/', 1)[-1].removesuffix('.html')
            fixture_role = document_role if document_role in ROLES else role
            if fixture_role not in sources:
                sources[fixture_role] = overlay_sdk(fixture_role, mode)
            request.fulfill(content_type='application/javascript', body=sources[fixture_role])
        elif url.hostname == '127.0.0.1' and url.port == server.server_port and request.request.method == 'GET':
            if url.path.startswith('/qa-image/'):
                key = url.path.rsplit('/', 1)[1]
                request.fulfill(status=200 if key in photos else 404,
                                content_type='image/jpeg', body=photos.get(key, b''))
            elif url.path.startswith('/qa-public/'):
                request.fulfill(content_type='text/html', body='<title>Offline destination</title><h1 id="qa-destination">Offline destination</h1>')
            else:
                request.continue_()
        else:
            trace['blocked'].append({'method': request.request.method, 'url': request.request.url})
            request.abort('blockedbyclient')

    context.route('**/*', route)
    page = context.new_page()
    page.on('pageerror', lambda error: trace['page_errors'].append(str(error)))
    page.on('response', lambda response: trace['http_errors'].append(
        {'url': response.url, 'status': response.status}) if response.status >= 400 else None)
    page.on('requestfailed', lambda request: trace['failed_local_requests'].append(
        {'url': request.url, 'resource_type': request.resource_type, 'failure': request.failure})
        if request.url.startswith(f'http://127.0.0.1:{server.server_port}/') else None)
    page.clock.install(time=prior.NOW)
    page.goto(f'http://127.0.0.1:{server.server_port}/{role}.html{query}', wait_until='domcontentloaded')
    page.locator('#tlb-boot' if mode == 'loading' else '#tlb-ov').wait_for()
    try:
        yield page, trace
        # The original successful app callback can render Home immediately before
        # ready() performs the requested navigation. WebKit cancels those pending
        # images when it leaves the document. Allow only that transport outcome,
        # with an explicitly expected destination that has actually loaded.
        if (trace.get('expected_destination') == page.url and
                page.locator('#qa-destination').is_visible()):
            trace['navigation_cancellations'] = [
                entry for entry in trace['failed_local_requests']
                if entry['resource_type'] == 'image' and entry['failure'] == 'Load request cancelled']
            trace['failed_local_requests'] = [
                entry for entry in trace['failed_local_requests']
                if entry not in trace['navigation_cancellations']]
        run.check('NETWORK', 'no unexpected external requests', not trace['blocked'], trace['blocked'])
        run.check('NETWORK', 'no JavaScript runtime errors', not trace['page_errors'], trace['page_errors'])
        run.check('NETWORK', 'no HTTP errors', not trace['http_errors'], trace['http_errors'])
        run.check('NETWORK', 'no failed local transport', not trace['failed_local_requests'], trace['failed_local_requests'])
    finally:
        run.contexts.append(trace)
        context.close()


def expected_logo(lang):
    return 'assets/brand/logo-talabot-' + ('en' if lang == 'en' else 'ru') + '.webp'


def check_logo(run, page, selector, lang, item):
    image = page.locator(selector)
    run.equal(item, 'one visible localized logo', image.count(), 1)
    image.evaluate('i=>i.decode()')
    run.equal(item, 'owner logo follows current locale', image.get_attribute('src'), expected_logo(lang))
    run.equal(item, 'brand keeps accessible name', image.get_attribute('alt'), 'Talabot')


def check_pill(run, page, selector, lang):
    pill = page.locator(selector)
    run.equal('AH-05', 'one white brand pill in this host', pill.count(), 1)
    check_logo(run, page, selector + ' > img[data-talabot-logo]', lang, 'AH-05')
    actual = pill.evaluate("""e=>{const s=getComputedStyle(e),i=e.querySelector('img'),r=i.getBoundingClientRect();return {
      background:s.backgroundColor,radius:s.borderRadius,padding:[s.paddingTop,s.paddingRight,s.paddingBottom,s.paddingLeft],
      shadow:s.boxShadow,imageHeight:r.height,ratio:r.width/r.height,naturalRatio:i.naturalWidth/i.naturalHeight}}""")
    run.equal('AH-05', 'pill is white with radius20 and padding12/20',
              [actual['background'], actual['radius'], actual['padding']],
              ['rgb(255, 255, 255)', '20px', ['12px', '20px', '12px', '20px']])
    run.check('AH-05', 'pill has shadow and undistorted44px logo',
              actual['shadow'] != 'none' and abs(actual['imageHeight'] - 44) < .1 and
              abs(actual['ratio'] - actual['naturalRatio']) < .01, actual)


def test_home(run, browser, server, photos, lang, width):
    with run.page(browser, server, photos, lang, width) as page:
        selector = '#app .d6h .d6-hr > img.d6-logo'
        check_logo(run, page, selector, lang, 'AH-04')
        data = page.locator(selector).evaluate("""i=>{const r=i.getBoundingClientRect(),h=i.parentElement,
          c=getComputedStyle(h),a=h.querySelector('.d6-loc'),ar=a.getBoundingClientRect(),sf=document.querySelector('.d6h .d6-sf').getBoundingClientRect();
          return {height:r.height,width:r.width,naturalRatio:i.naturalWidth/i.naturalHeight,rows:c.gridTemplateRows,columns:c.gridTemplateColumns,
            gap:c.columnGap,left:r.left,logoBottom:r.bottom,addressTop:ar.top,addressHeight:ar.height,searchTop:sf.top,searchHeight:sf.height,
            controls:[...h.querySelectorAll('.d6-hib')].map(e=>{const r=e.getBoundingClientRect();return [r.width,r.height]})}}""")
        run.check('AH-04', 'Home logo is36px with natural automatic width',
                  abs(data['height'] - 36) < .1 and abs(data['width'] / data['height'] - data['naturalRatio']) < .01, data)
        run.equal('AH-04', 'only the logo row grows; original header controls keep size and gaps',
                  [data['rows'], data['gap'], data['left'], data['addressHeight'], data['searchHeight'], data['controls']],
                  ['36px 44px', '6px', 16, 44, 50, [[44, 44], [44, 44]]])
        run.check('AH-04', 'larger logo and address do not overlap', data['logoBottom'] <= data['addressTop'] + .1, data)
        run.equal('AH-04', 'Home has no orange/dark-host pill', page.locator('.d6h .d6-hr .talabot-brand-pill').count(), 0)
        prior.no_overflow(run, page, 'AH-04')
        run.capture(page, f'{lang}-{width}-home-logo.webp')


def test_authenticated_brand(run, browser, server, photos, role, lang, width):
    with run.page(browser, server, photos, lang, width, role=role) as page:
        if role == 'driver':
            check_logo(run, page, '.a-header .a-brand img', lang, 'AH-05')
            run.check('AH-05', 'driver white operational header keeps21.8px logo',
                      abs(page.locator('.a-header .a-brand img').evaluate('e=>e.getBoundingClientRect().height') - 21.8) < .1)
            run.equal('AH-05', 'driver white header has no pill', page.locator('.a-header .talabot-brand-pill').count(), 0)
        else:
            page.set_viewport_size({'width': 1440, 'height': 900})
            check_pill(run, page, '.sbrand .talabot-side-pill' if role == 'admin' else '.st-merchant .nav > .talabot-nav-pill', lang)
        prior.no_overflow(run, page, 'AH-05')


def story_ids(page):
    return page.locator('.ah06-slide').evaluate_all('es=>es.map(e=>e.dataset.bannerId)')


def active_id(page):
    return page.locator('.ah06-stories').get_attribute('data-active-id')


def control(page, action):
    # DOM click keeps exact timer tests independent of Playwright's two-frame
    # actionability wait while its clock is intentionally paused.
    page.locator(f'[data-ah06-action="{action}"]').evaluate('e=>e.click()')


def pause_clock(page):
    page.clock.pause_at(page.evaluate('Date.now()/1000') + .01)


def original_form(run, page, signup=False, admin=False):
    expected = (['tlb-nm', 'tlb-ph'] if signup else []) + ['tlb-em', 'tlb-pw']
    run.equal('AH-06', 'original auth fields retain exact order', page.locator('.ah06-sheet input').evaluate_all('es=>es.map(e=>e.id)'), expected)
    run.equal('AH-06', 'admin signup exclusion and other-role tabs remain intact',
              [page.locator('#tlb-t-in').count(), page.locator('#tlb-t-up').count()], [0, 0] if admin else [1, 1])
    data = page.evaluate("""()=>{const em=document.getElementById('tlb-em'),pw=document.getElementById('tlb-pw'),go=document.getElementById('tlb-go');
      const f=window.__AH06OriginalForms.find(x=>x.email===em);return {email:[em.type,em.autocomplete,em.getAttribute('autocapitalize')],
        password:[pw.type,pw.autocomplete],sameCard:!!f&&f.card===document.querySelector('.ah06-sheet'),
        sameNodes:!!f&&f.nodes.every(e=>document.getElementById(e.id)===e),
        sameAttributes:!!f&&f.nodes.every((e,n)=>JSON.stringify(['type','autocomplete','autocapitalize','inputmode','maxlength','data-i18n','data-i18n-ph'].map(a=>e.getAttribute(a)))===JSON.stringify(f.attrs[n])),
        sameHandlers:!!f&&f.nodes.every((e,n)=>e.onclick===f.handlers[n][0]&&e.onkeydown===f.handlers[n][1]),
        actualHandlers:typeof go.onclick==='function'&&typeof em.onkeydown==='function'&&typeof pw.onkeydown==='function'}}""")
    run.equal('AH-06', 'email/password attributes remain the core contract',
              [data['email'], data['password']], [['email', 'username', 'off'], ['password', 'new-password' if signup else 'current-password']])
    run.check('AH-06', 'original core card, controls, and handlers survive decoration',
              all(data[key] for key in ('sameCard', 'sameNodes', 'sameAttributes', 'sameHandlers', 'actualHandlers')), data)
    if signup:
        run.equal('AH-06', 'signup phone/name attributes are preserved', page.evaluate("""()=>{
          const n=document.getElementById('tlb-nm'),p=document.getElementById('tlb-ph');return [n.type,n.maxLength,n.autocomplete,p.type,p.maxLength,p.autocomplete,p.inputMode]}"""),
                  ['text', 40, 'name', 'tel', 17, 'tel', 'tel'])


def test_default_login(run, browser, server, photos, role, lang, width):
    with overlay_page(run, browser, server, photos, role, lang, width) as (page, trace):
        page.locator('#tlb-ov.ah06-auth .ah06-stories').wait_for()
        run.equal('AH-06', 'unconnected provider uses exactly three default offers', story_ids(page), DEFAULT_IDS)
        run.equal('AH-06', 'default feed is identified honestly', page.locator('.ah06-stories').get_attribute('data-mode'), 'fallback')
        control(page, 'pause')
        run.equal('AH-06', 'progress has one segment per story', page.locator('.ah06-progress-step').count(), 3)
        page.locator('.ah06-art img').evaluate_all('es=>Promise.all(es.map(i=>i.decode()))')
        check_pill(run, page, '.ah06-brand-slot .talabot-brand-pill', lang)
        original_form(run, page, admin=role == 'admin')
        geometry = page.evaluate("""()=>{const h=document.querySelector('.ah06-stories').getBoundingClientRect(),s=document.querySelector('.ah06-sheet'),r=s.getBoundingClientRect(),c=getComputedStyle(s);return {
          heroRatio:h.height/innerHeight,sheetTop:r.top,heroBottom:h.bottom,background:c.backgroundColor,corners:[c.borderTopLeftRadius,c.borderTopRightRadius]}}""")
        run.check('AH-06', 'story area occupies roughly upper60percent', .54 <= geometry['heroRatio'] <= .66, geometry)
        run.equal('AH-06', 'original form sits in white sheet with28px top corners',
                  [geometry['background'], geometry['corners']], ['rgb(255, 255, 255)', ['28px', '28px']])
        run.equal('AH-06', 'login decoration performs no database calls', page.evaluate('__AH06DataCalls'), [])
        run.equal('AH-06', 'login decoration never starts sign-in', [x['kind'] for x in trace['auth']], ['getSession'])
        prior.no_overflow(run, page, 'AH-06')
        if role == 'customer':
            run.equal('AH-06', 'first default story starts active', active_id(page), DEFAULT_IDS[0])
            run.capture(page, f'{lang}-{width}-login-story-1.webp')
            control(page, 'next')
            run.equal('AH-06', 'manual next selects second default story', active_id(page), DEFAULT_IDS[1])
            run.capture(page, f'{lang}-{width}-login-story-2.webp')


def test_boot(run, browser, server, photos, role, lang, width):
    with overlay_page(run, browser, server, photos, role, lang, width, mode='loading') as (page, trace):
        check_pill(run, page, '#tlb-boot .talabot-loading-pill', lang)
        metrics = page.locator('#tlb-boot .talabot-loading-pill').evaluate("""e=>{const r=e.getBoundingClientRect(),b=document.getElementById('tlb-boot'),s=getComputedStyle(b);return {
          dx:r.x+r.width/2-innerWidth/2,dy:r.y+r.height/2-innerHeight/2,background:s.backgroundColor,image:s.backgroundImage}}""")
        run.check('AH-06', 'loading logo is centered on neutral background',
                  abs(metrics['dx']) < 1 and abs(metrics['dy']) < 1 and
                  metrics['background'] in ('rgb(246, 246, 248)', 'rgb(245, 246, 248)', 'rgb(255, 255, 255)') and metrics['image'] == 'none', metrics)
        run.equal('AH-06', 'loading does not display login offers', page.locator('.ah06-stories').count(), 0)
        if role == 'customer':
            run.capture(page, f'{lang}-{width}-loading.webp')
        page.clock.fast_forward(12100)
        page.locator('#tlb-rl').wait_for()
        run.equal('AH-06', 'original12second failure keeps reload and signout controls',
                  [page.locator('#tlb-boot').count(), page.locator('#tlb-rl').count(), page.locator('#tlb-rs2').count()], [0, 1, 1])
        run.equal('AH-06', 'boot failure is not converted into a login story form', page.locator('.ah06-stories').count(), 0)
        prior.no_overflow(run, page, 'AH-06')


def feed_for(server, *, interval=5, access='after_auth', url_path='after'):
    origin = f'http://127.0.0.1:{server.server_port}'
    def row(name, sort, **changes):
        value = {'id': name, 'title': 'Legacy fixture title', 'image_url': '/qa-image/ah06-ru',
                 'is_active': True, 'sort': sort, 'presentation': {'placements': ['login'], 'action': 'link',
                 'headline': {'ru': 'Заголовок ' + name, 'en': 'Headline ' + name},
                 'subtitle': {'ru': 'Описание ' + name, 'en': 'Subtitle ' + name},
                 'label': {'ru': 'Открыть ' + name, 'en': 'Open ' + name},
                 'images': {'ru': '/qa-image/ah06-ru', 'en': '/qa-image/ah06-en'},
                 'url': origin + '/qa-public/' + url_path, 'login_access': access}}
        value.update(changes)
        return value
    rows = [row('second', 20), row('first', 10), row('expired', 0, ends_at='2026-11-17T00:00:00Z'),
            row('future', 0, starts_at='2026-11-19T00:00:00Z'), row('inactive', 0, is_active=False)]
    wrong = row('wrong-placement', 0)
    wrong['presentation']['placements'] = ['home_main']
    unsafe = row('unsafe', 0)
    unsafe['presentation']['url'] = 'javascript:window.__AH06Unsafe=true'
    no_action = row('unsupported-action', 0)
    no_action['presentation']['action'] = 'restaurant'
    rows.extend([wrong, unsafe, no_action])
    return {'version': 1, 'banners': rows, 'settings': {'banner_rotation_login_seconds': interval}}


def connect(page, feed, mode='connected'):
    page.evaluate('feed=>TALABOT_LOGIN_BANNERS.connect(async()=>feed)', feed)
    page.wait_for_function('mode=>document.querySelector(".ah06-stories")?.dataset.mode===mode', arg=mode)


def test_provider(run, browser, server, photos, lang, width):
    with overlay_page(run, browser, server, photos, lang=lang, width=width) as (page, trace):
        connect(page, feed_for(server, interval=7))
        run.equal('AH-06', 'public presentation feed filters and sorts valid login links', story_ids(page), ['first', 'second'])
        active = page.locator('.ah06-slide.is-active')
        run.equal('AH-06', 'configured active story has localized headline and subtitle',
                  [active.locator('.ah06-headline').inner_text(), active.locator('.ah06-subtitle').inner_text()],
                  ['Заголовок first', 'Описание first'] if lang == 'ru' else ['Headline first', 'Subtitle first'])
        run.equal('AH-06', 'configured story uses its locale image', active.locator('.ah06-art img').get_attribute('src'), '/qa-image/ah06-' + lang)
        page.locator('#tlb-em').fill('typed@example.test')
        page.locator('#tlb-pw').fill('Fixture-only-123')
        page.locator('#tlb-pw').focus()
        page.evaluate('()=>window.__AH06Focused=document.activeElement')
        next_lang = 'en' if lang == 'ru' else 'ru'
        page.evaluate('lang=>TLB.setLang(lang)', next_lang)
        run.check('AH-06', 'locale update keeps credential values and focused node', page.evaluate("""()=>
          document.activeElement===__AH06Focused&&document.getElementById('tlb-em').value==='typed@example.test'&&document.getElementById('tlb-pw').value==='Fixture-only-123'"""))
        original_form(run, page)
        connect(page, {'version': 1, 'banners': [], 'settings': {}}, mode='empty')
        run.equal('AH-06', 'connected empty feed is neutral with no fallback offers orCTA',
                  [page.locator('.ah06-slide').count(), page.locator('.ah06-cta').count(), page.locator('.ah06-empty').count()], [0, 0, 1])
        run.check('AH-06', 'empty feed keeps original auth card', page.locator('.ah06-sheet #tlb-em').is_visible())
        page.evaluate("()=>TALABOT_LOGIN_BANNERS.connect(async()=>{throw new Error('offline fixture')})")
        page.wait_for_function("()=>document.querySelector('.ah06-stories')?.dataset.mode==='error'")
        run.equal('AH-06', 'provider errors restore honest fallback state', story_ids(page), DEFAULT_IDS)
        run.equal('AH-06', 'provider never requests anonymous account/settings data', page.evaluate('__AH06DataCalls'), [])
        prior.no_overflow(run, page, 'AH-06')


def test_max_copy(run, browser, server, photos, lang, width):
    with overlay_page(run, browser, server, photos, lang=lang, width=width) as (page, trace):
        feed = feed_for(server)
        for row in feed['banners']:
            row['presentation'].update({'headline': {lang: 'H' * 80}, 'subtitle': {lang: 'S' * 160}, 'label': {lang: 'C' * 40}})
        connect(page, feed)
        control(page, 'pause')
        metrics = page.locator('.ah06-slide.is-active').evaluate("""e=>{const hero=e.closest('.ah06-stories').getBoundingClientRect(),
          c=e.querySelector('.ah06-cta'),r=c.getBoundingClientRect();return {
          lengths:['.ah06-headline','.ah06-subtitle','.ah06-cta'].map(s=>e.querySelector(s).textContent.trim().length),
          fits:['.ah06-headline','.ah06-subtitle','.ah06-cta'].every(s=>{const n=e.querySelector(s);return n.scrollWidth<=n.clientWidth+1}),
          hit:document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest('.ah06-cta')===c,
          inside:r.left>=hero.left&&r.right<=hero.right+1&&r.top>=hero.top&&r.bottom<=hero.bottom+1,
          copyBottom:e.querySelector('.ah06-subtitle').getBoundingClientRect().bottom,ctaTop:r.top}}""")
        run.equal('AH-06', 'managed story preserves the full allowed copy lengths', metrics['lengths'], [80, 160, 40])
        run.check('AH-06', 'unbroken maximum copy wraps and leavesCTA reachable',
                  metrics['fits'] and metrics['hit'] and metrics['inside'] and metrics['copyBottom'] <= metrics['ctaTop'] + 1, metrics)
        prior.no_overflow(run, page, 'AH-06')


def progress(page):
    return page.locator('.ah06-slide.is-active').get_attribute('data-banner-id'), page.locator('.ah06-progress-step').evaluate_all("""es=>es.map(e=>{
      const s=getComputedStyle(e.querySelector('i')).transform;return {id:e.dataset.bannerId,value:s==='none'?1:new DOMMatrix(s).a}})""")


def test_timing(run, browser, server, photos):
    with overlay_page(run, browser, server, photos) as (page, trace):
        page.locator('.ah06-stories').wait_for()
        pause_clock(page)
        control(page, 'next')
        first = active_id(page)
        page.clock.run_for(2500)
        _, bars = progress(page)
        current = next(x['value'] for x in bars if x['id'] == first)
        run.check('AH-06', 'default5second timer produces halfway progress', .45 <= current <= .55, bars)
        page.clock.run_for(2400)
        run.equal('AH-06', 'default timer retains slide before5seconds', active_id(page), first)
        page.clock.run_for(150)
        run.check('AH-06', 'default timer advances after5seconds', active_id(page) != first)
        control(page, 'pause')
        held = active_id(page)
        page.clock.run_for(6000)
        run.equal('AH-06', 'manual pause stops autoplay', active_id(page), held)
        run.equal('AH-06', 'pause control announces its state', page.locator('[data-ah06-action="pause"]').get_attribute('aria-pressed'), 'true')
        control(page, 'pause')
        control(page, 'next')
        hero = page.locator('.ah06-stories').bounding_box()
        x, y = hero['x'] + hero['width'] * .8, hero['y'] + hero['height'] * .5
        page.mouse.move(x, y)
        page.mouse.down()
        held = active_id(page)
        page.clock.run_for(6000)
        run.equal('AH-06', 'held pointer pauses beyond a complete interval', active_id(page), held)
        page.mouse.move(hero['x'] + hero['width'] * .2, y, steps=12)
        page.mouse.up()
        page.clock.run_for(32)
        run.check('AH-06', 'real pointer swipe selects another story', active_id(page) != held)
        after_swipe = active_id(page)
        page.clock.run_for(4600)
        run.equal('AH-06', 'swipe starts a fresh interval', active_id(page), after_swipe)
        page.clock.resume()
        connect(page, feed_for(server, interval=7))
        pause_clock(page)
        control(page, 'next')
        first = active_id(page)
        page.clock.run_for(6500)
        run.equal('AH-06', 'configured7second interval is respected', active_id(page), first)
        page.clock.run_for(600)
        run.check('AH-06', 'configured interval advances after its duration', active_id(page) != first)
        page.clock.resume()
        connect(page, feed_for(server, interval=0))
        pause_clock(page)
        control(page, 'next')
        first = active_id(page)
        page.clock.run_for(4900)
        run.equal('AH-06', 'invalid interval falls back to5seconds', active_id(page), first)
        page.clock.run_for(200)
        run.check('AH-06', 'invalid interval does not stall rotation', active_id(page) != first)
        page.clock.resume()
        for seconds, before_ms, after_ms in ((1, 800, 300), (60, 59800, 300), (61, 4800, 300)):
            connect(page, feed_for(server, interval=seconds))
            pause_clock(page)
            control(page, 'next')
            first = active_id(page)
            page.clock.run_for(before_ms)
            run.equal('AH-06', f'interval boundary{seconds} retains current slide before its deadline', active_id(page), first)
            page.clock.run_for(after_ms)
            run.check('AH-06', f'interval boundary{seconds} advances at its valid or default deadline', active_id(page) != first)
            page.clock.resume()


def test_reduced_motion(run, browser, server, photos):
    with overlay_page(run, browser, server, photos, reduced=True) as (page, trace):
        page.locator('.ah06-stories').wait_for()
        first = active_id(page)
        page.clock.fast_forward(16000)
        run.equal('AH-06', 'reduced motion disables automatic slide changes', active_id(page), first)
        control(page, 'next')
        run.check('AH-06', 'reduced motion retains manual navigation', active_id(page) != first)


def test_auth_contract(run, browser, server, photos, role, lang, width):
    with overlay_page(run, browser, server, photos, role, lang, width) as (page, trace):
        page.locator('.ah06-sheet').wait_for()
        original_form(run, page, admin=role == 'admin')
        page.locator('#tlb-em').fill('typed@example.test')
        page.locator('#tlb-pw').fill('Fixture-only-123')
        page.locator('#tlb-pw').focus()
        page.evaluate('()=>window.__AH06Focused=document.activeElement')
        page.clock.fast_forward(5200)
        run.check('AH-06', 'autoplay preserves input focus and typed credentials', page.evaluate("""()=>
          document.activeElement===__AH06Focused&&document.getElementById('tlb-em').value==='typed@example.test'&&document.getElementById('tlb-pw').value==='Fixture-only-123'"""))
        page.locator('#tlb-eye').click()
        run.equal('AH-06', 'original password visibility control still works', page.locator('#tlb-pw').get_attribute('type'), 'text')
        page.locator('#tlb-eye').click()
        page.evaluate("()=>window.__AH06AuthOutcome='error'")
        page.locator('#tlb-pw').press('Enter')
        page.wait_for_function("()=>document.getElementById('tlb-er')?.textContent.length>0")
        run.equal('AH-06', 'Enter invokes exactly one original sign-in request', len([x for x in trace['auth'] if x['kind'] == 'signIn']), 1)
        run.check('AH-06', 'failed sign-in keeps its accessible error in the sheet', page.locator('.ah06-sheet #tlb-er[role="alert"]').is_visible())
        if role != 'admin':
            page.locator('#tlb-t-up').click()
            original_form(run, page, signup=True)
            page.set_viewport_size({'width': width, 'height': 560})
            page.locator('#tlb-nm').fill('Fixture User')
            page.locator('#tlb-ph').fill('+992900000001')
            page.locator('#tlb-em').fill('signup@example.test')
            page.locator('#tlb-pw').fill('Fixture-only-123')
            page.locator('#tlb-go').scroll_into_view_if_needed()
            hit = page.locator('#tlb-go').evaluate("""e=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&
              document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest('#tlb-go')===e}""")
            run.check('AH-06', 'signup submit stays reachable in short viewport', hit)
            page.locator('#tlb-go').click()
            page.locator('#tlb-bk').wait_for()
            run.equal('AH-06', 'original signup reaches confirmation without a new auth implementation', len([x for x in trace['auth'] if x['kind'] == 'signUp']), 1)
            page.locator('#tlb-bk').click()
            page.locator('#tlb-em').wait_for()
            run.equal('AH-06', 'confirmation back returns to original sign-in fields', page.locator('#tlb-nm').count(), 0)
        prior.no_overflow(run, page, 'AH-06')


def test_cta(run, browser, server, photos, access):
    with overlay_page(run, browser, server, photos) as (page, trace):
        trace['expected_destination'] = f'http://127.0.0.1:{server.server_port}/qa-public/{access}'
        feed = feed_for(server, access=access, url_path=access)
        if access == 'after_auth':
            # Omitted access must retain the conservative deferred contract.
            for row in feed['banners']:
                row['presentation'].pop('login_access', None)
        connect(page, feed)
        origin = page.url
        page.locator('.ah06-slide.is-active .ah06-cta').click()
        if access == 'public':
            page.wait_for_url('**/qa-public/public')
            run.equal('AH-06', 'publicCTA reaches its public target without signing in', len([x for x in trace['auth'] if x['kind'] != 'getSession']), 0)
        else:
            run.equal('AH-06', 'default privateCTA waits at login', page.url, origin)
            run.equal('AH-06', 'privateCTA never initiates sign-in on its own', len([x for x in trace['auth'] if x['kind'] != 'getSession']), 0)
            page.locator('#tlb-em').fill('customer@example.test')
            page.locator('#tlb-pw').fill('Fixture-only-123')
            page.evaluate("()=>window.__AH06AuthOutcome='error'")
            page.locator('#tlb-go').click()
            page.wait_for_function("()=>document.getElementById('tlb-er')?.textContent.length>0")
            run.equal('AH-06', 'failed sign-in cannot release deferredCTA', page.url, origin)
            page.evaluate("()=>window.__AH06AuthOutcome='success'")
            page.locator('#tlb-go').click()
            page.wait_for_url('**/qa-public/after_auth')
            run.equal('AH-06', 'real successful core/app callback releasesCTA', len([x for x in trace['auth'] if x['kind'] == 'signIn']), 2)
        run.check('AH-06', 'CTA destination is a loaded offline public document', page.locator('#qa-destination').is_visible())


def test_fallback_destination(run, browser, server, photos, kind):
    with overlay_page(run, browser, server, photos, query='?login_offer=' + kind + '&retained=1') as (page, trace):
        run.equal('AH-06', 'fallback deep link remains inert before authentication', page.locator('#tlb-em').count(), 1)
        page.locator('#tlb-em').fill('customer@example.test')
        page.locator('#tlb-pw').fill('Fixture-only-123')
        page.locator('#tlb-go').click()
        page.locator('#tlb-ov').wait_for(state='detached')
        if kind == 'free':
            page.wait_for_function("()=>S.v==='cat'&&S.catKey==='rest'&&S.srt==='free'&&S.fo===true")
        elif kind == 'happy':
            page.locator('#happy-hour-sheet').wait_for()
        else:
            page.wait_for_function("()=>S.v==='dineAll'")
        run.check('AH-06', 'fallback destination is consumed only after actual authentication', page.evaluate('!!TLB.me()'))
        run.check('AH-06', 'consumer removes only its own query parameter',
                  'login_offer=' not in page.url and 'retained=1' in page.url, page.url)


def test_staff_customer_entry(run, browser, server, photos, role):
    with overlay_page(run, browser, server, photos, role=role, lang='en', width=390) as (page, trace):
        run.equal('AH-06', 'staff default starts with the free-delivery story', active_id(page), DEFAULT_IDS[0])
        run.equal('AH-06', 'staff fallback explicitly names the customer destination',
                  page.locator('.ah06-slide.is-active .ah06-cta').inner_text().strip(), 'Open customer app')
        run.equal('AH-06', 'staff fallback explains the separate customer account',
                  page.locator('.ah06-slide.is-active .ah06-subtitle').inner_text(),
                  'Offers open in the customer app. A customer account is required.')
        page.locator('img').evaluate_all('es=>Promise.all(es.map(i=>i.decode()))')
        page.locator('.ah06-slide.is-active .ah06-cta').click()
        page.wait_for_url('**/customer.html?login_offer=free&lang=en')
        page.locator('#tlb-ov.ah06-auth .ah06-sheet #tlb-em').wait_for()
        destination = urlsplit(page.url)
        run.equal('AH-06', 'staff fallback opens the correct customer offer and locale immediately',
                  [destination.path, parse_qs(destination.query), page.evaluate('TLB.lang()')],
                  ['/customer.html', {'login_offer': ['free'], 'lang': ['en']}, 'en'])
        run.equal('AH-06', 'customer entry uses the original separate auth storage key',
                  trace['clients'], [{'role': role, 'storageKey': 'tlb-auth-' + role},
                                     {'role': 'customer', 'storageKey': 'tlb-auth-customer'}])
        run.equal('AH-06', 'entry navigation requests no staff or customer authentication',
                  [event for event in trace['auth'] if event['kind'] != 'getSession'], [])
        run.check('AH-06', 'customer offer still requires its own original login', page.evaluate("""role=>
          !TLB.me()&&!sessionStorage.getItem('ah06-fixture-session-'+role)&&
          !sessionStorage.getItem('ah06-fixture-session-customer')""", role))
        run.equal('AH-06', 'public entry grants no anonymous data access', page.evaluate('__AH06DataCalls'), [])
        original_form(run, page)


def test_blocked_role_cta(run, browser, server, photos, role):
    extra = ("profiles[0].driver_status='pending';" if role == 'driver' else "profiles[0].role='customer';")
    with overlay_page(run, browser, server, photos, role=role, extra=extra) as (page, trace):
        connect(page, feed_for(server))
        origin = page.url
        page.locator('.ah06-slide.is-active .ah06-cta').click()
        page.locator('#tlb-em').fill(role + '@example.test')
        page.locator('#tlb-pw').fill('Fixture-only-123')
        page.locator('#tlb-go').click()
        page.locator('#tlb-lo').wait_for()
        run.check('AH-06', 'blocked login has a profile but has not passed the role gate', page.evaluate('!!TLB.me()'))
        run.equal('AH-06', 'non-null profile cannot release deferredCTA', page.url, origin)
        run.equal('AH-06', 'blocked overlay is not decorated as a login form', page.locator('.ah06-stories').count(), 0)
        if role == 'admin':
            run.check('AH-06', 'original wrong-role navigation remains available',
                      page.locator('#tlb-go-app').get_attribute('href') == 'customer.html')


def test_new_login_waits(run, browser, server, photos, reentry):
    with overlay_page(run, browser, server, photos) as (page, trace):
        page.locator('#tlb-em').fill('customer@example.test')
        page.locator('#tlb-pw').fill('Fixture-only-123')
        page.locator('#tlb-go').click()
        page.locator('#tlb-ov').wait_for(state='detached')
        page.locator('#app .d6h').wait_for()
        if reentry:
            # This isolated future-core re-entry keeps the module instance alive.
            # Initial readiness came from the real original successful callback;
            # the new login card is again rendered by the unchanged core itself.
            page.evaluate("async()=>{await supabase.createClient().auth.signOut();TLB.start('customer',()=>{})}")
        else:
            # Normal production sign-out reloads the app. The synthetic SDK keeps
            # per-role session state so this exercises that actual core behavior.
            page.evaluate('()=>TLB.logout()')
        page.locator('.ah06-sheet #tlb-em').wait_for()
        connect(page, feed_for(server))
        origin = page.url
        before = len([x for x in trace['auth'] if x['kind'] == 'signIn'])
        page.locator('.ah06-slide.is-active .ah06-cta').click()
        run.equal('AH-06', 'a new original login cannot reuse previous readiness', page.url, origin)
        run.equal('AH-06', 'new privateCTA waits without starting another auth request',
                  len([x for x in trace['auth'] if x['kind'] == 'signIn']), before)
        if not reentry:
            trace['expected_destination'] = f'http://127.0.0.1:{server.server_port}/qa-public/after'
            page.locator('#tlb-em').fill('customer@example.test')
            page.locator('#tlb-pw').fill('Fixture-only-123')
            page.locator('#tlb-go').click()
            page.wait_for_url('**/qa-public/after')
            run.check('AH-06', 'fresh successful login releases new-sessionCTA', page.locator('#qa-destination').is_visible())


def test_admin(run, browser, server, photos, lang, width):
    with run.page(browser, server, photos, lang, width, extra=prior.BANNER_EXTRA, role='admin') as page:
        page.evaluate("()=>{tab='b';openBE('b31-multiple')}")
        run.equal('AH-06', 'admin offers the dedicated eighth Login placement',
                  page.locator('[name="banner-place"]').evaluate_all('es=>es.map(e=>e.value)'),
                  ['home_main', 'home_side', 'dont_miss', 'home_bottom', 'orders', 'restaurants', 'checkout', 'login'])
        run.equal('AH-06', 'loginCTA defaults to after_auth', page.locator('#banner-login_access').input_value(), 'after_auth')
        draft = {}
        for locale in ('ru', 'en', 'tg'):
            for name in ('headline', 'subtitle'):
                value = f'  QA {name} {locale}  '
                page.locator(f'#banner-{name}-{locale}').fill(value)
                draft[f'banner-{name}-{locale}'] = value
        page.locator('#banner-login_access').select_option('public')
        page.locator('#banner-headline-ru').focus()
        page.locator('#banner-headline-ru').evaluate('e=>e.setSelectionRange(3,8)')
        page.evaluate("()=>{TLB.setLang('en');render()}")
        run.equal('AH-06', 'localized login copy and focus survive admin language redraw', page.evaluate("""ids=>({
          values:Object.fromEntries(ids.map(id=>[id,document.getElementById(id).value])),
          focus:document.activeElement.id,selection:[document.activeElement.selectionStart,document.activeElement.selectionEnd]})""", list(draft)),
                  {'values': draft, 'focus': 'banner-headline-ru', 'selection': [3, 8]})
        run.equal('AH-06', 'public access draft survives redraw', page.locator('#banner-login_access').input_value(), 'public')
        for choice in page.locator('[name="banner-place"]').all():
            choice.set_checked(choice.get_attribute('value') == 'login')
        page.evaluate("()=>{window.__AH06Updates=[];TLB.updateBanner=async(id,payload)=>{__AH06Updates.push({id,payload});return {}}}")
        for action, url in [('restaurant', 'https://example.test/offer'), ('link', 'javascript:window.__AH06Unsafe=true'), ('link', 'https://user:pass@example.test/')]:
            page.locator('#banner-action').select_option(action)
            page.locator('#banner-url').fill(url)
            page.once('dialog', lambda dialog: dialog.dismiss())
            page.locator('button[onclick="bannerSave()"]').click()
        run.equal('AH-06', 'invalid login destinations block update before any write', page.evaluate('__AH06Updates.length'), 0)
        page.locator('#banner-url').fill('https://example.test/offer')
        page.locator('button[onclick="bannerSave()"]').click()
        page.wait_for_function('()=>__AH06Updates.length===1')
        saved = page.evaluate('__AH06Updates[0].payload.presentation')
        run.equal('AH-06', 'valid login update serializes placement/access/localized copy',
                  [saved['placements'], saved['login_access'], saved['headline'], saved['subtitle']],
                  [['login'], 'public', {l: f'QA headline {l}' for l in ('ru', 'en', 'tg')},
                   {l: f'QA subtitle {l}' for l in ('ru', 'en', 'tg')}])
        page.locator('#banner-timing summary').click()
        run.equal('AH-06', 'missing login interval key stays disabled at default5seconds',
                  [page.locator('#rotation-login').is_disabled(), page.locator('#rotation-login').input_value()], [True, '5'])
        page.evaluate("""()=>{window.__AH06Timing=[];TLB.setSetting=async(key,value)=>{__AH06Timing.push({key,value});return {}};
          saveBannerRotation('login')}""")
        run.equal('AH-06', 'missing setting cannot be written by a direct save call', page.evaluate('__AH06Timing'), [])
        page.evaluate("""()=>{const settings=TLB.settings.bind(TLB);TLB.settings=()=>({...settings(),banner_rotation_login_seconds:5});
          render();document.getElementById('banner-timing').open=true}""")
        for value in ('0', '61', '2.5'):
            page.locator('#rotation-login').fill(value)
            page.once('dialog', lambda dialog: dialog.dismiss())
            page.locator('button[onclick="saveBannerRotation(\'login\')"]').click()
        run.equal('AH-06', 'invalid admin intervals never write', page.evaluate('__AH06Timing'), [])
        page.locator('#rotation-login').fill('7')
        page.locator('button[onclick="saveBannerRotation(\'login\')"]').click()
        page.wait_for_function('()=>__AH06Timing.length===1')
        run.equal('AH-06', 'valid interval writes only the existing login setting', page.evaluate('__AH06Timing'),
                  [{'key': 'banner_rotation_login_seconds', 'value': 7}])
        page.evaluate("()=>{showAddB=true;bannerCreatePresentation={};window.__AH06Creates=[];TLB.addBanner=async payload=>{__AH06Creates.push(payload);return {}};render()}")
        page.locator('#bt').fill('Login offer fixture')
        for choice in page.locator('[name="banner-place"]').all():
            choice.set_checked(choice.get_attribute('value') == 'login')
        page.locator('#banner-action').select_option('link')
        page.locator('#banner-url').fill('//example.test/offer')
        page.once('dialog', lambda dialog: dialog.dismiss())
        page.locator('button[onclick="addBanner()"]').click()
        run.equal('AH-06', 'unsafe new login offer is blocked before creation', page.evaluate('__AH06Creates.length'), 0)
        page.locator('#banner-url').fill('https://example.test/new-offer')
        page.locator('button[onclick="addBanner()"]').click()
        page.wait_for_function('()=>__AH06Creates.length===1')
        run.equal('AH-06', 'new login offer preserves default deferred access',
                  page.evaluate('[__AH06Creates[0].presentation.placements,__AH06Creates[0].presentation.login_access]'), [['login'], 'after_auth'])
        prior.no_overflow(run, page, 'AH-06')

    legacy = "T.banners=[{id:'legacy',title:'Legacy QA',link_type:'store',link_value:'s1',placement:'top',is_active:true,image_url:'/qa-image/kfc'}];"
    with run.page(browser, server, photos, lang, width, extra=legacy, role='admin') as page:
        page.evaluate("()=>{tab='b';openBE('legacy')}")
        controls = page.locator('[id^="banner-headline-"],[id^="banner-subtitle-"],#banner-login_access,[name="banner-place"][value="login"]')
        run.check('AH-06', 'missing schema leaves new login controls disabled',
                  controls.count() == 8 and controls.evaluate_all('es=>es.every(e=>e.matches(":disabled"))'))
        run.equal('AH-06', 'legacy save omits optional presentation contract', page.evaluate('bannerPresentation()'), {})
        page.evaluate("()=>{window.__AH06Legacy=[];TLB.updateBanner=async(id,payload)=>{__AH06Legacy.push(payload);return {}}}")
        page.locator('button[onclick="bannerSave()"]').click()
        page.wait_for_function('()=>__AH06Legacy.length===1')
        run.check('AH-06', 'legacy save never attempts proposed fields', page.evaluate("!Object.hasOwn(__AH06Legacy[0],'presentation')"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--case', choices=['home', 'brands', 'defaults', 'boot', 'provider', 'timing', 'auth', 'cta', 'staff-entry', 'deep-links', 'admin'])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for key in ('SUPABASE_URL', 'SUPABASE_ACCESS_TOKEN', 'DATABASE_URL', 'SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(key), f'Cloud context forbidden: {key}'
    coverage = {'home': {'AH-04'}, 'brands': {'AH-05'}, 'defaults': {'AH-05', 'AH-06'}, 'boot': {'AH-05', 'AH-06'}}
    prior.EXPECTED_IDS = coverage.get(args.case, {'AH-06'}) if args.case else {'AH-04', 'AH-05', 'AH-06'}
    run = prior.Acceptance(args.output)
    run.provenance['harness_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    run.provenance['harness_dependencies_sha256'] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in ('tools/brief31_webkit.py', 'tools/brief25b_webkit.py', 'tools/qa_all.py')}
    run.provenance['playwright_version'] = importlib.metadata.version('playwright')
    server = prior.prior.qa.serve(ROOT)
    photos = prior.cuisine_photos(prior.prior.fixture_logos(prior.prior.qa.source_photos()))
    photos.update({'ah06-ru': photos['brief30-steak'], 'ah06-en': photos['brief30-plov']})
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            run.provenance['webkit_version'] = browser.version
            for lang, width in (('ru', 375), ('en', 390)):
                if args.case in (None, 'home'):
                    run.run(f'{lang}-home-logo', lambda l=lang, w=width: test_home(run, browser, server, photos, l, w))
                if args.case in (None, 'provider'):
                    run.run(f'{lang}-provider', lambda l=lang, w=width: test_provider(run, browser, server, photos, l, w))
                    run.run(f'{lang}-maximum-copy', lambda l=lang, w=width: test_max_copy(run, browser, server, photos, l, w))
                if args.case in (None, 'admin'):
                    run.run(f'{lang}-login-admin', lambda l=lang, w=width: test_admin(run, browser, server, photos, l, w))
                for role in ROLES:
                    if role != 'customer' and args.case in (None, 'brands'):
                        run.run(f'{lang}-{role}-brand', lambda r=role, l=lang, w=width: test_authenticated_brand(run, browser, server, photos, r, l, w))
                    if args.case in (None, 'defaults'):
                        run.run(f'{lang}-{role}-login', lambda r=role, l=lang, w=width: test_default_login(run, browser, server, photos, r, l, w))
                    if args.case in (None, 'boot'):
                        run.run(f'{lang}-{role}-loading', lambda r=role, l=lang, w=width: test_boot(run, browser, server, photos, r, l, w))
                    if args.case in (None, 'auth'):
                        run.run(f'{lang}-{role}-auth', lambda r=role, l=lang, w=width: test_auth_contract(run, browser, server, photos, r, l, w))
            if args.case in (None, 'timing'):
                run.run('rotation-pause-swipe', lambda: test_timing(run, browser, server, photos))
                run.run('reduced-motion', lambda: test_reduced_motion(run, browser, server, photos))
            if args.case in (None, 'cta'):
                for access in ('public', 'after_auth'):
                    run.run('cta-' + access, lambda a=access: test_cta(run, browser, server, photos, a))
                for role in ('driver', 'admin'):
                    run.run('cta-blocked-' + role, lambda r=role: test_blocked_role_cta(run, browser, server, photos, r))
                run.run('cta-after-normal-logout', lambda: test_new_login_waits(run, browser, server, photos, False))
                run.run('cta-after-core-reentry', lambda: test_new_login_waits(run, browser, server, photos, True))
            if args.case in (None, 'cta', 'staff-entry'):
                for role in ('driver', 'merchant', 'admin'):
                    run.run('fallback-customer-entry-' + role,
                            lambda r=role: test_staff_customer_entry(run, browser, server, photos, r))
            if args.case in (None, 'deep-links'):
                for kind in ('free', 'happy', 'dineout'):
                    run.run('fallback-' + kind, lambda k=kind: test_fallback_destination(run, browser, server, photos, k))
            browser.close()
    finally:
        server.shutdown()
    result = run.save()
    result['brief'] = 'BRIEF-31c'
    result['case_selection'] = args.case or 'all'
    (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if not result['pass']:
        raise SystemExit('BRIEF31C_FAIL: see results.json')
    print(f'BRIEF31C_PASS {len(run.assertions)} assertions; {len(run.screenshots)} viewport screenshots', flush=True)


if __name__ == '__main__':
    main()
