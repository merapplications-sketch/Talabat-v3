#!/usr/bin/env python3
"""AI-05: original customer HTML, identical two-restaurant input, offline WebKit.

The baseline must reproduce the lost viewport anchor/full redraw. Candidate
checks use the same real clicks, source assets, input rows and browser. Videos
and per-frame pixel metrics are evidence; WebKit has no LayoutShift/CLS API.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlsplit

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

import brief31_webkit as prior

ROOT = Path.cwd()
BASELINE = '99db45a7f713615468e7ce9f2cb3c5493826a4e3'
NOW = datetime(2026, 11, 18, 9, tzinfo=timezone.utc)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def fixture_sdk():
    catalog = json.loads((ROOT / 'qa-fixtures/home-brief25b.json').read_text())
    catalog['stores'] = [row for row in catalog['stores'] if row['id'] in ('s1', 's2')]
    for row in catalog['stores']:
        row.update(is_open=True, discount_pct=0,
                   description='' if row['id'] == 's1' else 'Local & European')
    seed = 'const catalog=' + json.dumps(catalog, ensure_ascii=False) + ';\n'
    seed += prior.prior.SEED + '\nwindow.__AI05Tables=T;\n'
    source = prior.prior.FIX.replace(prior.prior.qa.FINISH_SEED, seed + prior.prior.qa.FINISH_SEED)
    return source.replace('window.__ROLE', '"customer"'), catalog


INSTRUMENT = r"""()=>{
  window.__ai05={writes:0,frames:[],samples:[]};
  const descriptor=Object.getOwnPropertyDescriptor(Element.prototype,'innerHTML');
  Object.defineProperty(Element.prototype,'innerHTML',{...descriptor,set(value){
    if(this.id==='app')__ai05.writes++;
    descriptor.set.call(this,value);
  }});
  const rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {
    x:r.x,y:r.y,width:r.width,height:r.height}};
  window.__ai05Snapshot=()=>({
    scrollY,documentHeight:document.documentElement.scrollHeight,
    anchor:rect(document.querySelector(__ai05.selector)),
    hero:rect(document.querySelector('.d6-bento')),
    photos:[...document.querySelectorAll('.home-meals .d6-pt .d6-ph,.d6m .d6-mi .d6-ph')].map(rect),
    rails:[...document.querySelectorAll('.d6-rl,.d6-rail,#hsc')].map(e=>e.scrollLeft),
    toastCount:document.querySelectorAll('#app .t15-flow-toast').length,
    cart:JSON.parse(JSON.stringify(S.cart)),bar:document.querySelector('#app > .bar')?.innerText||'',
    sameHero:!__ai05.hero||__ai05.hero.isConnected,
    samePhoto:!__ai05.photo||__ai05.photo.isConnected,
    sameMenu:!__ai05.menu||__ai05.menu.isConnected
  });
  window.__ai05Begin=selector=>{
    __ai05.selector=selector;__ai05.writes=0;__ai05.frames=[];
    __ai05.hero=document.querySelector('.d6-bento');
    __ai05.photo=document.querySelector('.home-meals .d6-pt .d6-ph > img,.d6m .d6-mi .d6-ph > img');
    __ai05.menu=document.querySelector('.d6m');
    __ai05.before=__ai05Snapshot();__ai05.recording=true;
    const tick=()=>{if(!__ai05.recording)return;__ai05.frames.push(__ai05Snapshot());requestAnimationFrame(tick)};
    requestAnimationFrame(tick);
  };
  window.__ai05End=()=>{__ai05.recording=false;return {before:__ai05.before,
    after:__ai05Snapshot(),frames:__ai05.frames,appWrites:__ai05.writes}};
}"""


def stable(page):
    prior.settle(page)


def image_sizes(page):
    return page.evaluate("""()=>[...document.querySelectorAll('.d6-bento,.d6-bento img,.home-meals .d6-pt .d6-ph,.home-meals .d6-pt .d6-ph > img')].map(e=>{
      const r=e.getBoundingClientRect();return {tag:e.tagName,cls:e.className,width:r.width,height:r.height};})""")


def measure(page, name, anchor, action, wait_ms=300):
    page.evaluate('__ai05Begin', anchor)
    action()
    page.wait_for_timeout(wait_ms)
    stable(page)
    result = page.evaluate('__ai05End')
    result['name'] = name
    before = result['before']
    result['anchor_delta_px'] = result['after']['anchor']['y'] - before['anchor']['y']
    result['scroll_delta_px'] = result['after']['scrollY'] - before['scrollY']
    result['max_anchor_drift_px'] = max([abs(frame['anchor']['y'] - before['anchor']['y'])
                                       for frame in result['frames'] if frame['anchor']] + [0])
    result['max_scroll_delta_px'] = max([abs(frame['scrollY'] - before['scrollY'])
                                       for frame in result['frames']] + [0])
    result['ui'] = page.evaluate("""()=>({
      favouriteState:['s1','s2'].map(id=>TLB.isFav(id)),
      hearts:[...document.querySelectorAll('.hrt,.d6m .d6-act > .d6-circ[aria-pressed]')].map(e=>({
        color:e.style.color,pressed:e.getAttribute('aria-pressed'),svg:e.innerHTML})),
      quantities:[...document.querySelectorAll('.d75-qty')].map(e=>e.textContent),
      reward:document.querySelector('.d71-reward-copy')?.textContent||'',
      headerCart:document.querySelector('.d6-hh .d6-hr > .d6-hib:last-child')?.outerHTML||'',
      menuSpacer:document.querySelector('.d6m > div[style^="height:"]')?.getAttribute('style')||''
    })""")
    return result


def exercise_scroll(page):
    """Exported focused real-click scenario for the consolidated BRIEF-32 QA."""
    results = []
    anchor = '.home-meals .d6-pt'
    page.locator(anchor).first.evaluate('e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-230)')
    stable(page)
    cases = [
        ('first-add', '.home-meals .d6-pa', {'hot': 1}, '85.5 TJS'),
        ('repeat-plus', '.home-meals .d75-qty button:last-child', {'hot': 2}, '171 TJS'),
        ('minus', '.home-meals .d75-qty button:first-child', {'hot': 1}, '85.5 TJS'),
        ('remove-final-item', '.home-meals .d75-qty button:first-child', {}, ''),
    ]
    for name, button, cart, price in cases:
        result = measure(page, name, anchor, lambda selector=button: page.locator(selector).first.click())
        result['expected_cart'] = cart
        result['expected_bar_price'] = price
        results.append(result)
    # A new toast is allowed to exist for its original 2.3-second lifetime.
    # This press happens across expiry, without altering the production timer.
    results.append(measure(page, 're-add', anchor, lambda: page.locator('.home-meals .d6-pa').first.click()))
    page.wait_for_timeout(1750)
    results.append(measure(page, 'plus-across-toast-expiry', anchor,
                           lambda: page.locator('.home-meals .d75-qty button:last-child').first.click(), 700))
    favourite = '[data-section="popular"] + .d6-rl button[onclick*="toggleFav"]'
    page.locator(favourite).first.evaluate('e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-260)')
    stable(page)
    results.append(measure(page, 'favourite', '[data-section="popular"]',
                           lambda: page.locator(favourite).first.click(), 450))
    page.evaluate("openN('KFC')")
    stable(page)
    assert page.evaluate('scrollY') == 0, 'Normal view navigation still starts at the top'
    menu = '.d6-list .d6-mi'
    page.locator(menu).last.evaluate('e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-280)')
    stable(page)
    results.append(measure(page, 'menu-plus', menu + ':last-child',
                           lambda: page.locator(menu).last.locator('.d75-qty button:last-child,.d6-add').last.click()))
    results.append(measure(page, 'menu-minus', menu + ':last-child',
                           lambda: page.locator(menu).last.locator('.d75-qty button:first-child').click()))
    return results


def exercise_active_countdown(page):
    """Changing timer display is small; changing its deadline/offer is not."""
    anchor = '.home-meals .d6-pt'
    page.locator(anchor).first.evaluate('e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-230)')
    page.evaluate("""()=>{window.__ai05Timer=document.querySelector('.d6-bento .hcd[data-end]');window.__ai05TimerText=__ai05Timer.textContent;
      window.__ai05Cells=__ai05Timer.querySelector('.countdown32-cells');
      window.__ai05Digits=[...__ai05Timer.querySelectorAll('.countdown32-value')];}""")
    first = measure(page, 'active-timer-first-add', anchor,
                    lambda: page.locator('.home-meals .d6-pa').first.click(), 150)
    page.clock.run_for(1100)
    second = measure(page, 'active-timer-second-add', anchor,
                     lambda: page.locator('.home-meals .d75-qty button:last-child').first.click(), 200)
    live = page.evaluate("""()=>({sameNode:__ai05Timer.isConnected,
      displayAdvanced:document.querySelector('.d6-bento .hcd').textContent!==__ai05TimerText,
      deadline:document.querySelector('.d6-bento .hcd').dataset.end,
      formatterAvailable:typeof TALABOT_BANNERS.countdownHTML==='function'&&typeof TALABOT_BANNERS.updateCountdown==='function',
      segmentedValues:__ai05Digits.length,sameCells:!__ai05Cells||__ai05Cells.isConnected,
      sameDigits:__ai05Digits.every(node=>node.isConnected)})""")
    page.evaluate("""()=>{
      window.__ai05OldTimer=document.querySelector('.d6-bento .hcd');__ai05.writes=0;
      const end=new Date(Date.now()+5*3600000+5000);
      TLB.happyHours()[0].end_time=[end.getUTCHours(),end.getUTCMinutes(),end.getUTCSeconds()].map(x=>String(x).padStart(2,'0')).join(':');
      syncStores();render();
    }""")
    stable(page)
    changed = page.evaluate("""()=>({appWrites:__ai05.writes,oldNodeConnected:__ai05OldTimer.isConnected,
      deadline:document.querySelector('.d6-bento .hcd').dataset.end})""")
    page.evaluate('__ai05.writes=0')
    page.clock.fast_forward(6500)
    stable(page)
    expired = page.evaluate("""()=>({appWrites:__ai05.writes,
      activeOffers:TLB.hhActive().length,timers:document.querySelectorAll('.d6-bento .hcd').length})""")
    return {'first':first,'second':second,'live':live,'deadline_change':changed,'expiry':expired}


def exercise_keyboard_focus(page):
    anchor = '.home-meals .d6-pt'
    page.locator(anchor).first.evaluate('e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-230)')
    page.locator('.home-meals .d6-pa').first.focus()
    first = measure(page, 'keyboard-add', anchor, lambda: page.keyboard.press('Enter'), 150)
    add_to_plus = page.evaluate("document.activeElement===document.querySelector('.home-meals .d75-qty button:last-child')")
    page.locator('.home-meals .d75-qty button:first-child').first.focus()
    last = measure(page, 'keyboard-final-minus', anchor, lambda: page.keyboard.press('Enter'), 150)
    minus_to_add = page.evaluate("document.activeElement===document.querySelector('.home-meals .d6-pa')")
    return {'first':first,'last':last,'add_to_plus':add_to_plus,'minus_to_add':minus_to_add}


def exercise_flow_notice_anchor(page, mode):
    """Preserve the current reading position without relying on native anchoring."""
    if mode == 'none':
        page.add_style_tag(content='html{overflow-anchor:none}')
    support=page.evaluate("({supported:CSS.supports('overflow-anchor','none'),computed:getComputedStyle(document.documentElement).getPropertyValue('overflow-anchor')})")
    anchor='.home-meals .d6-pt'
    page.locator(anchor).first.evaluate('e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-230)')
    stable(page)
    first=measure(page, mode+'-notice-insert', anchor,
                  lambda: page.locator('.home-meals .d6-pa').first.click(), 150)
    repeated=measure(page, mode+'-notice-repeat-plus', anchor,
                     lambda: page.locator('.home-meals .d75-qty button:last-child').first.click(), 150)
    page.evaluate('scrollBy(0,80)');stable(page)
    expiry=measure(page, mode+'-notice-expiry-after-user-scroll', anchor, lambda: None, 2400)
    # A real navigation replaces the old notice's host. Its later native timeout
    # must not move the new page or restore a stale Home reading position.
    page.evaluate("TLB.toast('AI05 navigation notice')")
    stable(page)
    page.locator('.nav > div').nth(1).click()
    stable(page)
    navigation=measure(page, mode+'-navigation-before-expiry', '.d76-orders .chips', lambda: None, 2400)
    navigation['view']=page.evaluate('S.v')
    return {'mode':mode,'native_css':support,'first':first,'repeated':repeated,'expiry':expiry,'navigation':navigation}


def exercise_flow_notice_boundaries(page):
    """Top-of-page notices stay visible; staff paths and open dialogs retain their original path."""
    page.add_style_tag(content='html{overflow-anchor:none}')
    page.evaluate('scrollTo(0,0)');stable(page)
    page.locator('.d6-hh .d6-hr > .d6-hib').last.click()
    stable(page)
    top=page.evaluate("""()=>{const notice=document.querySelector('#app > .t15-flow-toast'),r=notice.getBoundingClientRect();
      return {scrollY,visible:r.top>=0&&r.bottom<=innerHeight,text:notice.textContent}}""")
    page.wait_for_timeout(2400);stable(page)
    top['afterExpiry']=page.evaluate("({scrollY,notices:document.querySelectorAll('#app > .t15-flow-toast').length})")
    excluded=[]
    for path in ('driver.html','merchant.html','admin.html'):
        result=page.evaluate("""path=>{
          history.replaceState(history.state,'',path);TLB.toast('AI05 staff path notice');
          return new Promise(resolve=>requestAnimationFrame(()=>{const notice=document.querySelector('#app > .t15-flow-toast');
            const result={path,ownRemove:Object.hasOwn(notice,'remove'),flow:getComputedStyle(notice).position};
            notice.remove();history.replaceState(history.state,'','customer.html');resolve(result)}));
        }""",path)
        excluded.append(result)
    dialog=page.evaluate("""()=>{
      const dialog=document.createElement('dialog');dialog.innerHTML='<button>AI05 modal focus</button>';document.body.append(dialog);dialog.showModal();
      const focused=document.activeElement;TLB.toast('AI05 modal notice');
      return new Promise(resolve=>requestAnimationFrame(()=>{const notice=document.querySelector('#app > .t15-flow-toast');
        const result={ownRemove:Object.hasOwn(notice,'remove'),focusRetained:document.activeElement===focused,open:dialog.open};
        notice.remove();dialog.close();dialog.remove();resolve(result)}));
    }""")
    page.evaluate("openN('KFC')");stable(page)
    anchor='.d6-list .d6-mi:last-child'
    page.locator(anchor).evaluate('e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-280)');stable(page)
    menu=measure(page,'menu-notice-insert',anchor,lambda: page.evaluate("TLB.toast('AI05 menu notice')"),150)
    menu_expiry=measure(page,'menu-notice-expiry',anchor,lambda: None,2400)
    return {'top':top,'staff':excluded,'dialog':dialog,'menu':menu,'menu_expiry':menu_expiry}


def exercise_segmented_comparison(page):
    """Known timer shapes exercise the real updater; merged runs use the actual AI-04 formatter."""
    return page.evaluate("""()=>{
      const actual=typeof TALABOT_BANNERS.countdownHTML==='function',saved={...smallViewRender},cases=[];
      const literal=(mode,values)=>'<span class="countdown32-cells" data-mode="'+mode+'" data-lang="ru" role="timer" aria-live="off" aria-label="'+values.join(' : ')+'">'+values.map((value,index)=>(index?'<span class="countdown32-separator" aria-hidden="true">:</span>':'')+'<span class="countdown32-cell" aria-hidden="true"><span class="countdown32-value">'+value+'</span></span>').join('')+'</span>';
      try{
        for(const sample of [{mode:'clock',before:3599000,after:3598000,old:['00','59','59'],next:['00','59','58']},
                             {mode:'days',before:90120000,after:90060000,old:['1','01','02'],next:['1','01','01']}]){
          const old=actual?TALABOT_BANNERS.countdownHTML(sample.before,'ru'):literal(sample.mode,sample.old),
            next=actual?TALABOT_BANNERS.countdownHTML(sample.after,'ru'):literal(sample.mode,sample.next),
            wrap=(body,end='2000000000000')=>'<span class="hcd" data-end="'+end+'">'+body+'</span>',host=document.createElement('div');
          host.innerHTML=wrap(old);const timer=host.firstElementChild,cells=timer.firstElementChild,digits=[...timer.querySelectorAll('.countdown32-value')];
          smallViewRender.key='home';smallViewRender.html=wrap(old);
          const accepted=updateSmallView(host,wrap(next),'home'),retained=host.firstElementChild===timer&&timer.firstElementChild===cells&&digits.every(node=>timer.contains(node));
          const deadlineRejected=!updateSmallView(host,wrap(next,'2000000001000'),'home');
          const outerAttributeRejected=!updateSmallView(host,wrap(next).replace('class="hcd"','class="hcd changed"'),'home');
          const shapeRejected=!updateSmallView(host,wrap('<em>different timer structure</em>'),'home');
          cases.push({mode:sample.mode,accepted,retained,deadlineRejected,outerAttributeRejected,shapeRejected,values:digits.length,
            displayActuallyDiffers:old!==next,actualShape:cells.matches('span.countdown32-cells')&&cells.dataset.mode===sample.mode&&cells.dataset.lang==='ru'});
        }
      }finally{Object.assign(smallViewRender,saved)}
      return {actualFormatter:actual,cases};
    }""")


@contextmanager
def original_page(browser, server, photos, sdk, output, label, *, delay_images=False, record_video=True):
    trace = {'page_errors': [], 'blocked': [], 'http_errors': [], 'failed_requests': []}
    pending = []
    context = browser.new_context(viewport={'width': 375, 'height': 812}, is_mobile=True,
                                  has_touch=True, device_scale_factor=1, service_workers='block',
                                  record_video_dir=str(output / 'videos') if record_video and not delay_images else None,
                                  record_video_size={'width': 375, 'height': 812} if record_video and not delay_images else None)
    context.set_default_timeout(8000)
    context.add_init_script("localStorage.setItem('tlb_lang','ru')")
    cached = {}

    def source(path):
        if label == 'baseline':
            if path not in cached:
                cached[path] = subprocess.check_output(['git', 'show', BASELINE + ':' + path], stderr=subprocess.DEVNULL)
            return cached[path]
        return (ROOT / path).read_bytes()

    def route(request):
        parsed = urlsplit(request.request.url)
        if parsed.hostname == 'cdn.jsdelivr.net' and 'supabase-js' in parsed.path:
            request.fulfill(content_type='application/javascript', body=sdk)
        elif parsed.hostname == '127.0.0.1' and parsed.port == server.server_port and request.request.method == 'GET':
            path = unquote(parsed.path).lstrip('/')
            if path.startswith('qa-image/'):
                key = path.rsplit('/', 1)[1]
                body, mime = photos[key], 'image/jpeg'
            else:
                body, mime = source(path), mimetypes.guess_type(path)[0] or 'application/octet-stream'
            if delay_images and request.request.resource_type == 'image':
                pending.append((request, body, mime))
            else:
                request.fulfill(content_type=mime, body=body)
        else:
            trace['blocked'].append(request.request.url)
            request.abort('blockedbyclient')

    context.route('**/*', route)
    page = context.new_page()
    page.on('pageerror', lambda error: trace['page_errors'].append(str(error)))
    page.on('requestfailed', lambda request: trace['failed_requests'].append({'url': request.url, 'failure': request.failure}))
    page.on('response', lambda response: trace['http_errors'].append({'url': response.url, 'status': response.status}) if response.status >= 400 else None)
    page.clock.install(time=NOW)
    page.goto(f'http://127.0.0.1:{server.server_port}/customer.html', wait_until='domcontentloaded')
    page.wait_for_function("typeof ME!=='undefined'&&ME.phone&&document.querySelector('.home-meals .d6-pa')")
    page.emulate_media(reduced_motion='reduce')
    page.evaluate('()=>{TLB.speed=()=>({min:20});render()}')
    stable(page)
    if not delay_images:
        page.evaluate("()=>{document.querySelectorAll('img').forEach(i=>i.loading='eager');return Promise.all([...document.images].map(i=>i.decode().catch(()=>null)))}")
    page.evaluate(INSTRUMENT)
    try:
        yield page, trace, pending
        page.wait_for_load_state('networkidle')
    finally:
        video = page.video
        context.close()
        if video:
            video.save_as(output / (label + '-ru375-clicks.webm'))
            video.delete()


def run_variant(browser, server, photos, sdk, output, label):
    with original_page(browser, server, photos, sdk, output, label) as (page, trace, _):
        inventory = page.evaluate("({stores:TLB.stores().map(s=>({id:s.id,name:s.name,open:s.is_open,discount:s.discount_pct,description:s.description})),banners:TLB.banners().length,happy:TLB.happyHours().length,dine:document.querySelectorAll('.home-dine .d6-dc').length,foods:TLB.allMenus(true)})")
        page.screenshot(path=str(output / (label + '-ru375-home.png')), full_page=False)
        metrics = exercise_scroll(page)
    with original_page(browser, server, photos, sdk, output, label, delay_images=True) as (page, image_trace, pending):
        before = image_sizes(page)
        while pending:
            request, body, mime = pending.pop(0)
            request.fulfill(content_type=mime, body=body)
        page.evaluate("()=>Promise.all([...document.images].filter(i=>i.loading!=='lazy'||i.getBoundingClientRect().top<innerHeight).map(i=>i.decode().catch(()=>null)))")
        stable(page)
        after = image_sizes(page)
    active_sdk = sdk.replace(prior.prior.qa.FINISH_SEED, """
      T.happy_hours=[{id:'ai05-timed-offer',title:'Happy Hours',store_id:'s1',days:[1,2,3,4,5,6,7],
        start_time:'00:00:00',end_time:'23:59:00',discount_pct:25,active:true}];
    """ + prior.prior.qa.FINISH_SEED)
    with original_page(browser, server, photos, active_sdk, output, label, record_video=False) as (page, timer_trace, _):
        active = exercise_active_countdown(page)
    with original_page(browser, server, photos, sdk, output, label, record_video=False) as (page, focus_trace, _):
        focus = exercise_keyboard_focus(page)
        segmented = exercise_segmented_comparison(page) if label == 'candidate' else None
    notice_modes=[];notice_traces=[];notice_boundaries=None
    if label == 'candidate':
        for mode in ('auto','none'):
            with original_page(browser, server, photos, sdk, output, label, record_video=False) as (page, notice_trace, _):
                notice_modes.append(exercise_flow_notice_anchor(page,mode));notice_traces.append(notice_trace)
        with original_page(browser, server, photos, sdk, output, label, record_video=False) as (page, notice_trace, _):
            notice_boundaries=exercise_flow_notice_boundaries(page);notice_traces.append(notice_trace)
    return {'label': label, 'metrics': metrics, 'inventory': inventory, 'trace': trace,
            'delayed_images': {'before': before, 'after': after, 'trace': image_trace},
            'active_countdown':active,'timer_trace':timer_trace,'keyboard_focus':focus,'focus_trace':focus_trace,
            'segmented_comparison':segmented,'notice_modes':notice_modes,'notice_boundaries':notice_boundaries,'notice_traces':notice_traces}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--baseline-only', action='store_true')
    parser.add_argument('--integrated', action='store_true',
                        help='skip only isolated source-scope pins; the master BRIEF-32 harness owns combined scope')
    args = parser.parse_args()
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=True)
    sdk, catalog = fixture_sdk()
    photos = prior.prior.fixture_logos(prior.prior.qa.source_photos())
    server = prior.prior.qa.serve(ROOT)
    provenance = {'baseline': subprocess.check_output(['git', 'rev-parse', BASELINE], text=True).strip(),
                  'candidate_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  'candidate_customer_sha256': sha((ROOT / 'customer.html').read_bytes()),
                  'candidate_safe_toast_sha256': sha((ROOT / 'assets/shared/safe-toast.js').read_bytes()),
                  'harness_sha256': sha(Path(__file__).read_bytes()), 'sdk_sha256': sha(sdk.encode()),
                  'catalog': catalog, 'viewport': {'width': 375, 'height': 812}, 'integrated':args.integrated,
                  'physical_phone_tested': False, 'production_tested': False,
                  'cls_supported': False, 'metric': 'WebKit per-frame viewport-anchor and scroll deltas; source videos'}
    variants = []
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            provenance['webkit_version'] = browser.version
            for label in ['baseline'] if args.baseline_only else ['baseline', 'candidate']:
                variant = run_variant(browser, server, photos, sdk, output, label)
                variants.append(variant)
                for result in variant['metrics']:
                    print('AI05_METRIC', label, result['name'], 'app_writes='+str(result['appWrites']),
                          'anchor_drift='+str(result['max_anchor_drift_px']), 'scroll_delta='+str(result['scroll_delta_px']), flush=True)
            browser.close()
    finally:
        server.shutdown()
    assertions = []
    def check(name, condition, details=None):
        assertions.append({'name': name, 'pass': bool(condition), 'details': details})
    check('candidate source stayed fixed throughout the run',
          sha((ROOT/'customer.html').read_bytes())==provenance['candidate_customer_sha256'] and
          sha((ROOT/'assets/shared/safe-toast.js').read_bytes())==provenance['candidate_safe_toast_sha256'])
    if not args.integrated:
        approved=subprocess.check_output(['git','show',BASELINE+':customer.html'],text=True)
        actual=(ROOT/'customer.html').read_text()
        def outside_render(source):
            start=source.index('/* ---------- RENDER ---------- */')
            end=source.index('/* a happy hour starts or ends with no data event:')
            return source[:start]+source[end:]
        check('isolated customer source changes only the RENDER section', outside_render(actual)==outside_render(approved))
        names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],text=True).splitlines()
        protected=[name for name in names if name.startswith(('assets/','sql/','supabase/')) or
                   ('/' not in name and name.endswith(('.html','.js','.css')) and name!='customer.html')]
        changed=[name for name in protected if (ROOT/name).read_bytes()!=subprocess.check_output(['git','show',BASELINE+':'+name])]
        check('isolated change keeps all other product files unchanged', not changed, changed)
    baseline = variants[0]
    check('baseline reproduces the real repeat-plus anchor jump',
          any(r['name']=='repeat-plus' and r['max_anchor_drift_px']>=50 and r['appWrites']>0 for r in baseline['metrics']))
    for variant in variants:
        check(variant['label']+' has no runtime/network errors', not any(variant['trace'].values()), variant['trace'])
        check(variant['label']+' delayed images have no runtime/network errors',
              not any(variant['delayed_images']['trace'].values()), variant['delayed_images']['trace'])
        check(variant['label']+' uses exactly the agreed empty-DineOut input',
              [row['id'] for row in variant['inventory']['stores']]==['s1','s2'] and
              not any(variant['inventory'][key] for key in ('banners','happy','dine')) and
              sum(len(items) for items in variant['inventory']['foods'].values())==4,
              variant['inventory'])
        check(variant['label']+' reserves identical image/hero sizes before decode',
              variant['delayed_images']['before']==variant['delayed_images']['after'], variant['delayed_images'])
        check(variant['label']+' timer/focus cases have no runtime/network errors',
              not any(variant['timer_trace'].values()) and not any(variant['focus_trace'].values()),
              {'timer':variant['timer_trace'],'focus':variant['focus_trace']})
        if variant['label'] != 'candidate':
            continue
        check('notice anchor scenarios have no runtime/network errors',
              not any(any(trace.values()) for trace in variant['notice_traces']),variant['notice_traces'])
        for mode in variant['notice_modes']:
            for name in ('first','repeated','expiry','navigation'):
                case=mode[name]
                check(case['name']+' keeps the current viewport anchor',case['max_anchor_drift_px']<=1,case['max_anchor_drift_px'])
                check(case['name']+' avoids whole-app replacement',case['appWrites']==0,case['appWrites'])
            check(mode['mode']+' notice remains on the original native lifetime',
                  mode['first']['after']['toastCount']==1 and mode['expiry']['after']['toastCount']==0)
            check(mode['mode']+' expiry after navigation does not move the new page',
                  mode['navigation']['view']=='orders' and mode['navigation']['scroll_delta_px']==0)
        boundary=variant['notice_boundaries']
        check('top-of-page flow notice remains visible without forced scrolling',boundary['top']['scrollY']==0 and boundary['top']['visible'],boundary['top'])
        check('top-of-page notice expiry retains the document top',boundary['top']['afterExpiry']=={'scrollY':0,'notices':0},boundary['top']['afterExpiry'])
        check('staff paths retain native removal and flow styling',
              all(not row['ownRemove'] and row['flow']=='static' for row in boundary['staff']),boundary['staff'])
        check('open body dialog retains focus and the original notice path',
              boundary['dialog']=={'ownRemove':False,'focusRetained':True,'open':True},boundary['dialog'])
        for name in ('menu','menu_expiry'):
            check(boundary[name]['name']+' keeps current menu position',boundary[name]['max_anchor_drift_px']<=1,boundary[name]['max_anchor_drift_px'])
        timer=variant['active_countdown']
        check('active countdown advances its original live text', timer['live']['displayAdvanced'], timer['live'])
        check('quantity taps more than one second apart keep the active timer node', timer['live']['sameNode'], timer['live'])
        check('existing countdown child nodes are retained', timer['live']['sameCells'] and timer['live']['sameDigits'], timer['live'])
        if args.integrated:
            check('integrated timer exercises the actual segmented AI-04 renderer',
                  timer['live']['formatterAvailable'] and timer['live']['segmentedValues']==3, timer['live'])
        for case in ('first','second'):
            check('active countdown '+case+' tap avoids whole-app replacement', timer[case]['appWrites']==0, timer[case]['appWrites'])
            check('active countdown '+case+' tap keeps viewport anchor', timer[case]['max_anchor_drift_px']<=1, timer[case]['max_anchor_drift_px'])
        check('changed deadline still triggers full rendering', timer['deadline_change']['appWrites']>0 and
              not timer['deadline_change']['oldNodeConnected'] and timer['deadline_change']['deadline']!=timer['live']['deadline'], timer['deadline_change'])
        check('expired offer still triggers full rendering and removes its timer', timer['expiry']['appWrites']>0 and
              timer['expiry']['activeOffers']==0 and timer['expiry']['timers']==0, timer['expiry'])
        focus=variant['keyboard_focus']
        check('keyboard Add hands focus to the new plus button', focus['add_to_plus'])
        check('keyboard final decrement hands focus to the replacement Add button', focus['minus_to_add'])
        for case in ('first','last'):
            check('keyboard '+case+' transition avoids whole-app replacement', focus[case]['appWrites']==0, focus[case]['appWrites'])
            check('keyboard '+case+' transition keeps viewport anchor', focus[case]['max_anchor_drift_px']<=1, focus[case]['max_anchor_drift_px'])
        segmented=variant['segmented_comparison']
        if args.integrated:
            check('integrated shape comparison uses the actual AI-04 formatter', segmented['actualFormatter'])
        for case in segmented['cases']:
            check(case['mode']+' segmented display accepts only a live text update',
                  case['accepted'] and case['retained'] and case['displayActuallyDiffers'] and case['actualShape'] and case['values']==3, case)
            check(case['mode']+' segmented comparison keeps deadline, outer attributes and shape guards',
                  case['deadlineRejected'] and case['outerAttributeRejected'] and case['shapeRejected'], case)
        for result in variant['metrics']:
            old = next(row for row in baseline['metrics'] if row['name']==result['name'])
            check(result['name']+' keeps the original control output', result['ui']==old['ui'],
                  {'baseline':old['ui'],'candidate':result['ui']})
            check(result['name']+' preserves the viewport anchor', result['max_anchor_drift_px']<=1, result['max_anchor_drift_px'])
            check(result['name']+' avoids whole-app replacement', result['appWrites']==0, result['appWrites'])
            check(result['name']+' preserves existing hero/photo/menu nodes',
                  all(result['after'][k] for k in ('sameHero','samePhoto','sameMenu')))
            if 'expected_cart' in result:
                check(result['name']+' keeps exact quantity logic', result['after']['cart']==result['expected_cart'], result['after']['cart'])
                check(result['name']+' keeps exact cart price', result['expected_bar_price'] in result['after']['bar'] if result['expected_bar_price'] else not result['after']['bar'], result['after']['bar'])
    if not args.baseline_only:
        before=Image.open(output/'baseline-ru375-home.png').convert('RGB')
        after=Image.open(output/'candidate-ru375-home.png').convert('RGB')
        check('initial Home remains pixel-identical', before.size==after.size and ImageChops.difference(before,after).getbbox() is None)
    report = {'provenance': provenance, 'variants': variants, 'assertions': assertions,
              'pass': all(row['pass'] for row in assertions)}
    (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('AI05_'+('PASS' if report['pass'] else 'FAIL'), len(assertions), 'checks', flush=True)
    raise SystemExit(0 if report['pass'] else 1)


if __name__ == '__main__':
    main()
