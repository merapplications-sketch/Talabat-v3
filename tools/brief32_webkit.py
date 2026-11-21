#!/usr/bin/env python3
"""BRIEF-32: original app HTML, offline matching-state SDK, no live services.

Primary state matches the owner's reported conditions: two restaurants, no
DineOut eligibility, no admin banners. Names/cuisine descriptions match the
observed public restaurant fields; prices, menu rows, and fixture photographs
remain synthetic QA data. Additional configured-banner cases are labelled.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
import io

import brief31_webkit as prior
import brief31d_webkit as hero_reference
import brief32_login_webkit as login
import brief32_restaurants_webkit as restaurants

ROOT = Path.cwd()
SCOPE_BASE = '1d54020a8a4de60e118b342b19fb8d0c3ab2e876'
MATCHING_EXTRA = r"""
  stores.splice(0,stores.length,...stores.filter(s=>['s1','s2'].includes(s.id)));
  for(const store of stores){
    store.discount_pct=0;
    store.description=store.id==='s2'?'Local & European':'';
  }
  items.splice(0,items.length,...items.filter(i=>stores.some(s=>s.id===i.store_id)));
  T.happy_hours=[];T.banners=[];
"""
TIMER_EXTRA = r"""
  const fixtureBanner=(id,remaining)=>({id,title:'Скидки',image_url:'/qa-image/romant',
    placement:'top',is_active:true,sort:T.banners.length,link_type:'store',link_value:'s2',
    ...(remaining?{ends_at:new Date(Date.UTC(2026,10,18,9)+remaining).toISOString()}:{}),
    presentation:{audience:'orders',placements:['orders','restaurants'],
      action:'campaign',campaign:'discount',label:{ru:'Смотреть',en:'View'}}});
  T.banners.push(fixtureBanner('ai04-long',40*86400000+7*3600000+52*60000+10000));
  T.banners.push(fixtureBanner('ai04-short',7*3600000+52*60000+10000));
  T.banners.push(fixtureBanner('ai04-no-timer',0));
  T.banners.push({...fixtureBanner('ai04-home',40*86400000+7*3600000+52*60000+10000),
    presentation:{action:'campaign',campaign:'discount',label:{ru:'Смотреть',en:'View'}}});
"""


class Acceptance(prior.Acceptance):
    def check(self, item, name, passed, details=None):
        item = {'AI03':'AI-03', 'AI06':'AI-06', 'AI05':'AI-05'}.get(item,item)
        return super().check(item,name,passed,details)


def source_text(ref, path):
    return subprocess.check_output(['git','show',ref+':'+path], text=True)


def section(text, start, end):
    assert text.count(start)==1 and text.count(end)==1, (start,end)
    return text[text.index(start):text.index(end,text.index(start))]


def source_line(text, start):
    lines=[line for line in text.splitlines(keepends=True) if line.startswith(start)]
    assert len(lines)==1, start
    return lines[0]


def test_source_scope(run):
    baseline=source_text(SCOPE_BASE,'customer.html')
    actual=(ROOT/'customer.html').read_text()
    normalized=actual
    # These are the complete approved customer edit regions. No auth, money,
    # card/sheet/group templates, Home section order, or hero selection changes.
    for start,end in (
        ('/* BRIEF-25c Y-10:', 'const bottomBn='),
        ('function ordersAd(', 'function vOrders()'),
        ('/* ---------- RENDER ---------- */', 'function render(){'),
        ('  const D6P=[', '  const _n=document.querySelector'),
    ):
        normalized=normalized.replace(section(actual,start,end),section(baseline,start,end),1)
    for start in ('const managedHappyCountdown=', 'const happyCountdown=', '    }else TALABOT_BANNERS.updateCountdown('):
        previous='    }else timer.textContent=' if start.startswith('    }else') else start
        normalized=normalized.replace(source_line(actual,start),source_line(baseline,previous),1)
    run.equal('SOURCE','all customer bytes outside the seven-item edit regions are frozen',normalized,baseline)
    hero=section(actual,'/* hero carousel:', '/* the last delivered order')
    hero=hero.replace(source_line(actual,'const happyCountdown='),source_line(baseline,'const happyCountdown='),1)
    run.equal('SOURCE','literal BRIEF31d hero except the requested timer formatter',hero,
              section(baseline,'/* hero carousel:','/* the last delivered order'))
    run.provenance['frozen_hero_sha256']=hashlib.sha256(hero.encode()).hexdigest()
    for start in ('const bannersAt=','const inB=','const bannerDeadline=','const managedBannerCountdown='):
        run.equal('SOURCE',start+' retains its eligibility/deadline logic',source_line(actual,start),source_line(baseline,start))
    for start,end in (
        ('const bannerCountdown=', 'function d6Tile('),
        ('function vHome()', 'TLB.addDict(\n  {happyUntil:'),
        ('function openCampaign(', 'if(!window.__hcdTick)'),
        ('const B31_ROT=', '/* ---------- shared view pieces ---------- */'),
    ):
        run.equal('SOURCE',start+' remains unchanged',section(actual,start,end),section(baseline,start,end))
    allowed={
      'customer.html','assets/shared/login-banners-ah06.js','assets/shared/login-banners-ah06.css',
      'assets/shared/banner-system-brief31.js','assets/shared/banner-countdown-brief32.css',
      'assets/customer-c/banners-brief31.css','assets/customer-c/home-brief31.css',
      'assets/customer-c/restaurants-brief30.js','assets/customer-c/restaurants-brief30.css',
      'assets/preview/dineout-demo.json','tools/brief32_webkit.py','tools/brief32_login_webkit.py',
      'tools/brief32_restaurants_webkit.py','tools/brief32_scroll_webkit.py','tools/ci1_fast_webkit.py',
      '.github/workflows/unified-fix-brief15-20261117.yml',
    }
    paths=set(subprocess.check_output(['git','diff','--name-only',SCOPE_BASE],text=True).splitlines())
    paths.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],text=True).splitlines())
    outside=sorted(path for path in paths if path not in allowed and not path.startswith('qa-shots/'))
    run.equal('SOURCE','changed paths stay inside requested product/evidence/CI scope',outside,[])
    for name in set(prior.PRODUCT_PATHS)-allowed:
        frozen=subprocess.check_output(['git','show',SCOPE_BASE+':'+name])
        run.check('SOURCE',name+' is frozen', (ROOT/name).read_bytes()==frozen)
    for name in ('assets/size-brief7/customer.css','assets/customer-c/home-sections.css','assets/shared/safe-toast.js'):
        run.equal('SOURCE',name+' retains approved layout/notice behavior',(ROOT/name).read_text(),source_text(SCOPE_BASE,name))
    forbidden=subprocess.check_output(['git','diff','--name-only',SCOPE_BASE,'--','sql','supabase','talabat-core.js'],text=True).splitlines()
    run.equal('SOURCE','no database, backend, or financial core change',forbidden,[])


def test_frozen_home(run,browser,server,baseline,photos):
    images={};states={}
    for name,source in [('before',baseline),('after',server)]:
        with matching_page(run,browser,source,photos) as page:
            page.evaluate('scrollTo(0,0)')
            hero_reference.prepare(page)
            states[name]=hero_reference.hero_snapshot(page)
            images[name]=Image.open(io.BytesIO(page.locator('.d6-bento').screenshot(animations='disabled'))).convert('RGB')
            run.capture(page,'ru-375-matching-state-home-'+name+'.webp')
    run.equal('SOURCE','Home hero structure/style/geometry stays identical',states['after'],states['before'])
    run.equal('SOURCE','Home hero image dimensions stay identical',images['after'].size,images['before'].size)
    diff=ImageChops.difference(images['after'],images['before'])
    run.check('SOURCE','Home hero remains pixel-identical in primary matching state',diff.getbbox() is None)


@contextmanager
def matching_page(run, browser, server, photos, *, extra='', lang='ru', width=375):
    with run.page(browser, server, photos, lang=lang, width=width,
                  extra=MATCHING_EXTRA + extra) as page:
        page.emulate_media(reduced_motion='reduce')
        yield page


def fixture_state(page):
    return page.evaluate("""()=>({stores:TLB.stores().map(s=>s.name),
      eligible:STORES.filter(s=>s.c==='rest'&&TLB.isOpen(s.n)&&s.disc>0).length,
      banners:TLB.banners().length,menus:Object.keys(TLB.allMenus(true)),
      previewInCore:TLB.stores().some(s=>/demo/i.test(s.name))})""")


@contextmanager
def baseline_checkout():
    local = ROOT.parent / 'home-brief32-base'
    if local.is_dir():
        assert subprocess.check_output(['git','-C',str(local),'rev-parse','HEAD'], text=True).strip() == SCOPE_BASE
        assert not subprocess.check_output(['git','-C',str(local),'status','--porcelain'], text=True).strip()
        yield local
        return
    with tempfile.TemporaryDirectory(prefix='talabot-brief32-base-') as temporary:
        path = Path(temporary) / 'source'
        subprocess.run(['git','worktree','add','--detach',str(path),SCOPE_BASE], check=True)
        try:
            yield path
        finally:
            subprocess.run(['git','worktree','remove','--force',str(path)], check=True)


def popular_snapshot(page):
    return page.locator('[data-section="popular"] + .d6-rl').evaluate("""rail=>{
      const style=e=>{const s=getComputedStyle(e);return Object.fromEntries(['fontSize','fontWeight','lineHeight','color','letterSpacing'].map(k=>[k,s[k]]))};
      return {title:rail.previousElementSibling.outerHTML,
        rows:getComputedStyle(rail).gridTemplateRows.split(' ').length,
        cards:[...rail.children].map(card=>{const box=card.querySelector('.d6-ph').getBoundingClientRect();return {
          html:card.outerHTML,width:box.width,height:box.height,
          texts:[...card.querySelectorAll('.nm,.mt,.pk,.hb,.heart')].map(e=>({text:e.textContent,style:style(e)}))}})};
    }""")


def test_popular(run, browser, server, baseline, photos):
    snapshots = {}
    for label, source in [('before', baseline), ('after', server)]:
        with matching_page(run, browser, source, photos) as page:
            page.locator('[data-section="popular"]').evaluate('e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-150)')
            prior.settle(page)
            snapshots[label] = popular_snapshot(page)
            run.capture(page, 'ai07-ru-375-' + label + '.webp')
    before, after = snapshots['before'], snapshots['after']
    run.equal('AI-07', 'only the two reported restaurants are used for primary proof', len(after['cards']), 2)
    run.equal('AI-07', 'heading remains identical', after['title'], before['title'])
    run.equal('AI-07', 'row count remains identical', after['rows'], before['rows'])
    for index, (old, new) in enumerate(zip(before['cards'], after['cards'])):
        run.equal('AI-07', f'card {index} stays exactly 120px square at375', [new['width'],new['height']], [120,120])
        run.check('AI-07', f'card {index} is smaller than live baseline', new['width'] < old['width'])
        run.equal('AI-07', f'card {index} text styling remains identical', new['texts'], old['texts'])
        run.equal('AI-07', f'card {index} DOM, heart, badge, metadata remain identical', new['html'], old['html'])
    # Geometry only: a third synthetic copy in this isolated case proves the
    # visible rail fraction. It is not added to the matching-state screenshots.
    with matching_page(run, browser, server, photos, extra=r"""
      stores.push({...stores[0],id:'qa-third-restaurant',name:'QA geometry only'});
    """) as page:
        page.locator('[data-section="popular"]').evaluate('e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-150)')
        fraction = page.locator('[data-section="popular"] + .d6-rl').evaluate("""rail=>{
          const r=rail.getBoundingClientRect();return [...rail.children].reduce((n,e)=>{
            const b=e.getBoundingClientRect();return n+Math.max(0,Math.min(r.right,b.right)-Math.max(r.left,b.left))/b.width},0)}""")
        run.check('AI-07', 'approximately 2.7 cards visible with sufficient data', 2.6 <= fraction <= 2.8, fraction)
        run.capture(page, 'ai07-ru-375-three-card-geometry-fixture.webp')


def timer_snapshot(page):
    return page.locator('.hcd[data-end]').evaluate_all("""nodes=>nodes.map(node=>{
      const pill=node.closest('.cd'), cells=node.querySelector('.countdown32-cells');
      const box=pill.getBoundingClientRect(), host=pill.closest('button,.d6-bt').getBoundingClientRect();
      return {end:node.dataset.end,mode:cells?.dataset.mode,label:cells?.getAttribute('aria-label'),
        cells:node.querySelectorAll('.countdown32-cell').length,
        height:box.height,weight:getComputedStyle(node.querySelector('.countdown32-value')).fontWeight,
        white:getComputedStyle(pill).color,gradient:getComputedStyle(pill).backgroundImage,
        contained:box.left>=host.left-1&&box.right<=host.right+1&&box.top>=host.top-1&&box.bottom<=host.bottom+1,
        fits:node.scrollWidth<=node.clientWidth+1};})""")


def test_timers(run, browser, server, baseline, photos):
    with matching_page(run, browser, server, photos) as page:
        page.evaluate("go('orders')")
        run.equal('AI-04', 'no injected admin ad in primary matching state', page.locator('.banner31-order-carousel').count(), 0)
        run.capture(page, 'ai04-ru-375-orders-no-admin-banners.webp')
    visibility = {}
    for label, source in [('before', baseline), ('after', server)]:
        with matching_page(run, browser, source, photos, extra=TIMER_EXTRA) as page:
            page.clock.set_fixed_time(prior.NOW + timedelta(seconds=3))
            counts = {}
            for view, action in [('home', "go('home')"), ('orders', "go('orders')"), ('restaurants', "openCat('rest')")]:
                page.evaluate(action)
                prior.settle(page)
                counts[view] = page.locator('.hcd[data-end]').evaluate_all('es=>es.map(e=>e.dataset.end).sort()')
            visibility[label] = counts
    run.equal('AI-04', 'timer appearance conditions/deadlines unchanged in all banner placements', visibility['after'], visibility['before'])

    with matching_page(run, browser, server, photos, extra=TIMER_EXTRA) as page:
        page.clock.set_fixed_time(prior.NOW + timedelta(seconds=3))
        page.evaluate("go('orders')")
        run.equal('AI-04', 'pause control removed', page.locator('.banner31-rotation-toggle,[data-banner-toggle]').count(), 0)
        run.equal('AI-04', 'cover artwork fills each frame', page.locator('.banner31-order > img').evaluate_all("es=>es.map(e=>({fit:getComputedStyle(e).objectFit,full:Math.abs(e.clientWidth-e.parentElement.clientWidth)<=1&&Math.abs(e.clientHeight-e.parentElement.clientHeight)<=1}))"), [{'fit':'cover','full':True}]*4)
        dots = page.locator('.banner31-dots').bounding_box()
        frame = page.locator('.banner31-order').first.bounding_box()
        run.check('AI-04', 'dots are inside the bottom of the actual frame', dots['y'] >= frame['y'] + frame['height']*.7 and dots['y']+dots['height'] <= frame['y']+frame['height'], {'dots':dots,'frame':frame})
        long_timer = page.locator('[data-banner-id="ai04-long"] .countdown32-cells')
        short_timer = page.locator('[data-banner-id="ai04-short"] .countdown32-cells')
        run.equal('AI-04', 'long countdown has distinct day/hour/minute cells', long_timer.get_attribute('aria-label'), '40 д · 07 ч · 52 м')
        run.equal('AI-04', 'last24h clock has padded HH MM SS cells', short_timer.get_attribute('aria-label'), '07 : 52 : 07')
        run.equal('AI-04', 'no timer without configured deadline', page.locator('[data-banner-id="ai04-no-timer"] .hcd').count(), 0)
        for data in timer_snapshot(page):
            run.equal('AI-04', 'three separate digit cells', data['cells'], 3)
            run.check('AI-04', 'white digits on red-orange gradient', data['white']=='rgb(255, 255, 255)' and 'linear-gradient' in data['gradient'], data)
            run.check('AI-04', 'countdown stays inside banner and does not clip', data['contained'] and data['fits'], data)
            run.check('AI-04', 'compact pill with bold numeric cells', data['height'] <= 34 and int(data['weight']) >= 700, data)
        run.capture(page, 'ai04-ru-375-orders-long-configured-fixture.webp')
        page.evaluate("""()=>{const r=document.querySelector('[data-banner-rail="orders"]');r.scrollLeft=bannerRailStep(r);bannerRailSync(r)}""")
        prior.settle(page)
        run.equal('AI-04', 'swiping rail synchronizes dots', page.locator('.banner31-dots i.on').evaluate('e=>[...e.parentElement.children].indexOf(e)'), 1)
        run.capture(page, 'ai04-ru-375-orders-last24h-configured-fixture.webp')
        page.evaluate("window.__ai04Digits=document.querySelector('[data-banner-id=\"ai04-short\"] .countdown32-cells')")
        page.clock.set_fixed_time(prior.NOW + timedelta(seconds=4))
        page.clock.run_for(1000)
        run.equal('AI-04', 'seconds tick without rebuilding cells', page.evaluate("window.__ai04Digits===document.querySelector('[data-banner-id=\"ai04-short\"] .countdown32-cells')"), True)
        run.equal('AI-04', 'one wall-clock second elapsed', short_timer.get_attribute('aria-label'), '07 : 52 : 06')
        seconds = short_timer.locator('.countdown32-cell').last
        run.equal('AI-04', 'reduced motion stops pulse', seconds.evaluate('e=>getComputedStyle(e).animationName'), 'none')
        page.emulate_media(reduced_motion='no-preference')
        run.equal('AI-04', 'last24h pulse occurs once a second', seconds.evaluate('e=>getComputedStyle(e).animationDuration'), '1s')
        run.equal('AI-04', 'long countdown does not pulse', long_timer.locator('.countdown32-cell').last.evaluate('e=>getComputedStyle(e).animationName'), 'none')
        page.emulate_media(reduced_motion='reduce')
        page.evaluate("openCat('rest')")
        run.capture(page, 'ai04-ru-375-restaurants-configured-fixture.webp')
        for data in timer_snapshot(page):
            run.check('AI-04', 'restaurant timer shares treatment and fits', data['cells']==3 and data['fits'] and data['contained'] and 'linear-gradient' in data['gradient'], data)
        page.evaluate("go('home')")
        run.capture(page, 'ai04-ru-375-home-configured-fixture.webp')
        for data in timer_snapshot(page):
            run.check('AI-04', 'Home timer shares treatment and fits', data['cells']==3 and data['fits'] and data['contained'] and 'linear-gradient' in data['gradient'], data)
        formats = page.evaluate("""()=>[86400001,86400000,86399000,59000].map(ms=>{
          const e=document.createElement('span');e.innerHTML=TALABOT_BANNERS.countdownHTML(ms,'ru');
          return e.firstElementChild.getAttribute('aria-label')})""")
        run.equal('AI-04', '24hour boundary and leading zero formatting', formats, ['1 д · 00 ч · 00 м','24 : 00 : 00','23 : 59 : 59','00 : 00 : 59'])


def test_preview(run, browser, server, photos):
    with matching_page(run, browser, server, photos) as page:
        demo_requests = []
        page.on('request', lambda request: demo_requests.append(request.url)
                if urlsplit(request.url).path.endswith('/assets/preview/dineout-demo.json') else None)
        initial = fixture_state(page)
        run.equal('AI-02', 'two matching-state restaurants', initial['stores'], ['KFC', 'Romant Restaurant'])
        run.equal('AI-02', 'no real DineOut eligible restaurant', initial['eligible'], 0)
        run.equal('AI-02', 'no admin banners', initial['banners'], 0)
        run.equal('AI-02', 'AF06 hides empty DineOut on ordinary host', page.locator('.home-dine-section').count(), 0)
        page.evaluate('scrollTo(0,document.documentElement.scrollHeight)')
        run.capture(page, 'ai02-ru-375-ordinary-host-empty-hidden.webp')

        run.equal('AI-02','ordinary host never loaded the demo JSON',page.evaluate("performance.getEntriesByType('resource').filter(r=>r.name.endsWith('/assets/preview/dineout-demo.json')).length"),0)
        # Evaluate the unchanged loader with plain location/data objects and a
        # fetch stub. Hostnames are string inputs only: no navigation, DNS,
        # cookies, credentials, or HTTP request can leave localhost.
        cases=[
          {'host':'ordinary.invalid','query':'','expected':False},
          {'host':'talabot-gate1-preview-20261116.pages.dev.other.invalid','query':'','expected':False},
          {'host':'ordinary.invalid','query':'?demo=other','expected':False},
          {'host':'talabot-gate1-preview-20261116.pages.dev','query':'','expected':True},
          {'host':'ordinary.invalid','query':'?demo=dineout','expected':True},
        ]
        code=section((ROOT/'customer.html').read_text(),'const dinePreviewEnabled=','function dineH(')
        matrix=page.evaluate("""async ({code,cases,fixture})=>{
          const results=[];
          for(const input of cases){
            const calls=[];
            const fakeFetch=(path,options)=>{calls.push({path,credentials:options.credentials});return Promise.resolve({ok:true,json:()=>Promise.resolve(fixture)})};
            const create=new Function('location','fetch','document',code+'\\nloadDinePreview();return ()=>({enabled:dinePreviewEnabled,state:dinePreviewState,demo:dinePreviewRestaurant});');
            const snapshot=create({hostname:input.host,search:input.query},fakeFetch,{querySelectorAll:()=>[]});
            for(let step=0;step<12;step++)await Promise.resolve();
            results.push({...input,...snapshot(),calls});
          }
          return results;
        }""", {'code':code,'cases':cases,'fixture':json.loads((ROOT/'assets/preview/dineout-demo.json').read_text())})
        for row in matrix:
            name=row['host']+row['query']
            run.equal('AI-02','isolated exact-host/query gate: '+name,row['enabled'],row['expected'])
            run.equal('AI-02','isolated fetch count: '+name,len(row['calls']),int(row['expected']))
            run.equal('AI-02','isolated loader state: '+name,row['state'],'ready' if row['expected'] else 'idle')
            if row['expected']:
                run.equal('AI-02','only a local credential-free JSON path is requested',row['calls'],[{'path':'assets/preview/dineout-demo.json','credentials':'omit'}])
        page.goto(f'http://127.0.0.1:{server.server_port}/customer.html?demo=dineout',wait_until='domcontentloaded')
        page.wait_for_function("document.querySelector('[data-dineout-demo]')&&TLB.stores().length===2")
        page.evaluate('()=>{TLB.speed=()=>({min:20});render()}')
        run.equal('AI-02','localhost opt-in loads the real JSON exactly once',len(demo_requests),1)
        run.equal('AI-02','display data never enters core',fixture_state(page),initial)
        card=page.locator('[data-dineout-demo]')
        run.equal('AI-02','demo has literal Test badge',card.locator('.hb.k').inner_text().strip(),'Тест')
        run.equal('AI-02','demo has no order/cart/store action',
                  card.evaluate("e=>({tag:e.tagName,onclick:e.getAttribute('onclick'),buttons:e.querySelectorAll('button').length})"),
                  {'tag':'ARTICLE','onclick':None,'buttons':0})
        card.scroll_into_view_if_needed()
        run.capture(page,'ai02-ru-375-query-opt-in.webp')
        page.locator('[data-section="dine"] button').click()
        run.equal('AI-02','demo remains display-only on expanded list',page.locator('[data-dineout-demo]').count(),1)
        run.equal('AI-02','expanded demo also leaves core untouched',fixture_state(page),initial)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--case', choices=['source','preview','popular','timers','login','restaurants','scroll'])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for key in ('SUPABASE_URL', 'SUPABASE_ACCESS_TOKEN', 'DATABASE_URL', 'SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(key), 'Cloud context forbidden: ' + key
    coverage={'source':{'SOURCE'},'preview':{'AI-02'},'popular':{'AI-07'},'timers':{'AI-04'},
              'login':{'AI-01'},'restaurants':{'AI-03','AI-06'},'scroll':{'AI-05'}}
    prior.EXPECTED_IDS=coverage.get(args.case,{'SOURCE',*(f'AI-{number:02}' for number in range(1,8))})
    prior.PRODUCT_PATHS += ['assets/preview/dineout-demo.json','assets/shared/banner-countdown-brief32.css']
    run = Acceptance(args.output)
    run.provenance.update({'scope_base': SCOPE_BASE,
        'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'matching_state': '2 restaurants; discount_pct=0; no happy hours; no admin banners; synthetic SDK and fixture photographs'})
    dependencies=['tools/brief31_webkit.py','tools/brief31c_webkit.py','tools/brief31d_webkit.py',
                  'tools/brief32_login_webkit.py','tools/brief32_restaurants_webkit.py','tools/brief32_scroll_webkit.py',
                  'tools/brief25b_webkit.py','qa-fixtures/home-brief25b.json']
    run.provenance['harness_dependencies_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                                for name in dependencies if (ROOT/name).is_file()}
    if args.case in (None,'source'):
        run.run('scoped-source-immutability',lambda:test_source_scope(run))
    photos = prior.cuisine_photos(prior.prior.fixture_logos(prior.prior.qa.source_photos()))
    photos.update({'ah06-ru':photos['brief30-steak'],'ah06-en':photos['brief30-plov']})
    with baseline_checkout() as source, hero_reference.baseline_checkout(None) as original:
        server = prior.prior.qa.serve(ROOT)
        baseline = prior.prior.qa.serve(source)
        original_server=prior.prior.qa.serve(original)
        try:
            with sync_playwright() as pw:
                browser = pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
                run.provenance['webkit_version'] = browser.version
                if args.case in (None,'source'):
                    run.run('matching-state-frozen-Home',lambda:test_frozen_home(run,browser,server,baseline,photos))
                if args.case in (None,'login'):
                    login.run_ai01(run,browser,server,photos,check_source=False)
                if args.case in (None,'restaurants'):
                    restaurants.run_ai03(run,browser,{'baseline':original_server,'candidate':server},photos)
                    restaurants.run_ai06(run,browser,server,photos)
                if args.case in (None, 'preview'):
                    run.run('ai02-preview-gate-and-core-isolation', lambda: test_preview(run, browser, server, photos))
                if args.case in (None, 'popular'):
                    run.run('ai07-popular-only-sizing', lambda: test_popular(run, browser, server, baseline, photos))
                if args.case in (None, 'timers'):
                    run.run('ai04-countdown-and-orders-presentation', lambda: test_timers(run, browser, server, baseline, photos))
                browser.close()
        finally:
            server.shutdown()
            baseline.shutdown()
            original_server.shutdown()
    if args.case in (None,'scroll'):
        command=[os.sys.executable,'tools/brief32_scroll_webkit.py',str(args.output/'ai05-integrated'),'--integrated']
        completed=subprocess.run(command,check=False)
        result_path=args.output/'ai05-integrated'/'results.json'
        scroll_result=json.loads(result_path.read_text()) if result_path.is_file() else {}
        run.run('ai05-integrated-scroll-proof',lambda:run.check('AI-05','focused scroll/identity/focus/expiry checks pass',
          completed.returncode==0 and scroll_result.get('pass'),{'exit_code':completed.returncode,'results':'ai05-integrated/results.json'}))
    result = run.save()
    result['brief'] = 'BRIEF-32'
    result['scope'] = __doc__.strip()
    if hasattr(run,'pixel_comparisons'):result['pixel_comparisons']=run.pixel_comparisons
    (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if not result['pass']:
        raise SystemExit('BRIEF32_FAIL: see results.json')
    print(f'BRIEF32_PASS {len(run.assertions)} assertions; {len(run.screenshots)} screenshots', flush=True)


if __name__ == '__main__':
    main()
