#!/usr/bin/env python3
"""BRIEF-31d: restore only the approved Home hero, using original offline apps.

The primary comparison has no Happy Hours schedule. A separate identical
schedule checks the baseline's original countdown without changing its logic.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import timedelta
import difflib
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

import brief31_webkit as prior
import brief31c_webkit as login

ROOT = Path.cwd()
BASELINE = '8cd90a8ac14ff01413b63f79c5db676c0081d34d'
SCOPE_BASE = '81ddd9c6f2cfce9fae8a30c3401ad1615006e839'
LOCAL_BASELINE = ROOT.parent / 'home-8cd90a8a'
PROOF_EXTRA = r"""
  T.happy_hours=[];
  T.banners=[{id:'hero-proof',title:'Обед в ресторане',placement:'top',is_active:true,
    link_type:'store',link_value:'s1',sort:1,image_url:'/qa-image/kfc',
    presentation:{action:'restaurant',label:{ru:'Открыть ресторан',en:'Open restaurant'}}}];
"""
SIDE_ART_EXTRA = PROOF_EXTRA + r"""
  for(const [id,image,sort] of [['side-a','romant',2],['side-b','kfc',3]])
    T.banners.push({id,title:id,placement:'top',is_active:true,sort,
      link_type:'store',link_value:'s2',image_url:'/qa-image/'+image});
"""
HAPPY_EXTRA = PROOF_EXTRA + r"""
  T.happy_hours=[{id:'schedule-proof',title:'Happy Hours',store_id:'s1',
    days:[1,2,3,4,5,6,7],start_time:'00:00:00',end_time:'23:59:00',discount_pct:25,active:true}];
  T.banners.push({id:'happy-proof',title:'Счастливые часы',placement:'happy_hour',
    is_active:true,link_type:'happy_hour',image_url:'/qa-image/romant',sort:2});
"""
CONTINUATION_EXTRA = r"""
  T.happy_hours=[];
  const put=(id,audience,store,label)=>T.banners.push({id,title:id,placement:'top',is_active:true,
    link_type:'store',link_value:store,sort:T.banners.length,image_url:'/qa-image/kfc',
    presentation:{audience,placements:[audience],action:'restaurant',label:{ru:label,en:label}}});
  put('orders-plain','orders','s1','');
  put('orders-label','orders','s2','Открыть ресторан');
  put('restaurants-label','restaurants','s2','Смотреть');
"""


def git_text(ref, name):
    return subprocess.check_output(['git', 'show', ref + ':' + name], text=True)


def section(source, start, end):
    assert source.count(start) == 1 and source.count(end) == 1, (start, end)
    return source[source.index(start):source.index(end, source.index(start))]


def source_line(source, start):
    lines = [line for line in source.splitlines(keepends=True) if line.startswith(start)]
    assert len(lines) == 1, start
    return lines[0]


def replace_once(source, old, new):
    assert source.count(old) == 1, old[:100]
    return source.replace(old, new, 1)


def test_source_scope(run):
    approved = git_text(BASELINE, 'customer.html')
    previous = git_text(SCOPE_BASE, 'customer.html')
    actual = (ROOT / 'customer.html').read_text()
    hero_start, hero_end = '/* hero carousel:', '/* the last delivered order'
    approved_hero = section(approved, hero_start, hero_end)
    run.equal('SOURCE', 'entire hero HTML/CSS-facing markup and JavaScript are literal baseline bytes',
              section(actual, hero_start, hero_end), approved_hero)
    run.provenance['literal_hero_sha256'] = hashlib.sha256(approved_hero.encode()).hexdigest()

    # Reconstruct only the explicitly authorized restoration and preservation
    # aliases from the two immutable source revisions. Any other customer byte
    # change, including Home headers, auth, or unrelated views, fails this guard.
    expected = previous
    expected = replace_once(expected, source_line(previous, 'const bannersAt='),
        "const bannersAt=place=>['orders','restaurants','login'].includes(place)?TALABOT_BANNERS.list(TLB.banners(),place,TLB.settings()):[];\n")
    expected = replace_once(expected, source_line(previous, 'const inB='), source_line(approved, 'const inB='))
    old_labels = source_line(previous, 'const bannerConfig=') + source_line(previous, 'const bannerLabel=')
    labels = section(approved, 'const bannerConfig=', 'function openBannerList(')
    expected = replace_once(expected, old_labels, labels + old_labels.replace('bannerConfig', 'managedBannerConfig').replace('bannerLabel', 'managedBannerLabel'))
    old_actions = section(previous, 'function bannerGo(', '/* ---------- auto-rotating ads')
    actions = section(approved, 'function bannerGo(', '/* ---------- auto-rotating ads')
    managed_actions = old_actions.replace('bannerGo', 'managedBannerGo').replace('bannerConfig', 'managedBannerConfig').replace('bannerAction', 'managedBannerAction')
    expected = replace_once(expected, old_actions, actions + managed_actions)
    old_clock = source_line(previous, 'const cdTxt=')
    expected = replace_once(expected, old_clock, source_line(approved, 'const cdTxt=') + old_clock.replace('cdTxt', 'managedCdTxt'))
    expected = replace_once(expected, 'sp.textContent=cdTxt(end-Date.now())', 'sp.textContent=managedCdTxt(end-Date.now())')
    managed_countdown = source_line(previous, 'const happyCountdown=').replace('happyCountdown', 'managedHappyCountdown').replace('cdTxt', 'managedCdTxt')
    managed_countdown += source_line(previous, 'const bannerCountdown=').replace('bannerCountdown', 'managedBannerCountdown').replace('happyCountdown', 'managedHappyCountdown')
    markup = section(previous, 'function bannerMarkup(', 'function d6Tile(')
    markup = markup.replace('bannerLabel(b)', 'managedBannerLabel(b)').replace('bannerAction(b)', 'managedBannerAction(b)').replace('bannerCountdown(b)', 'managedBannerCountdown(b)')
    expected = replace_once(expected, section(previous, hero_start, hero_end), managed_countdown + markup + approved_hero)
    for old, new in (
        ("for(const ad of inB('dont_miss'))", "for(const ad of bannersAt('dont_miss'))"),
        ('Array.isArray(bannerConfig(b).placements)', 'Array.isArray(managedBannerConfig(b).placements)'),
        ("const bb=inB('bottom')", "const bb=bannersAt('home_bottom')"),
        ('${end?happyCountdown(end)+', '${end?managedHappyCountdown(end)+'),
        ('timer.textContent=cdTxt(remaining);', "timer.textContent=timer.closest('.d6-bento')?cdTxt(remaining):managedCdTxt(remaining);"),
    ):
        expected = replace_once(expected, old, new)
    differences = list(difflib.unified_diff(expected.splitlines(), actual.splitlines(), fromfile='authorized restoration', tofile='candidate'))
    run.check('SOURCE', 'all customer bytes outside the literal restore and named preservation aliases stay unchanged',
              expected == actual, differences[:80])

    restaurant_path = 'assets/customer-c/restaurants-brief30.js'
    restaurant = git_text(SCOPE_BASE, restaurant_path).replace('bannerConfig(b)', 'managedBannerConfig(b)').replace('bannerGo(id)', 'managedBannerGo(id)')
    run.equal('SOURCE', 'Restaurants changes only the two existing managed-helper references',
              (ROOT / restaurant_path).read_text(), restaurant)
    styles = ('assets/size-brief7/customer.css', 'assets/customer-c/home-sections.css')
    for name in styles:
        run.equal('SOURCE', name + ' remains byte-identical to the approved hero baseline',
                  (ROOT / name).read_text(), git_text(BASELINE, name))
    run.equal('SOURCE', 'inline hero style block remains literal baseline CSS',
              section(actual, '/* bento */', '/* categories: one row of six */'),
              section(approved, '/* bento */', '/* categories: one row of six */'))
    for name in sorted(set(prior.PRODUCT_PATHS + list(styles)) - {'customer.html', restaurant_path}):
        current = (ROOT / name).read_bytes()
        frozen = subprocess.check_output(['git', 'show', SCOPE_BASE + ':' + name])
        run.check('SOURCE', name + ' is unchanged from the pre-restoration source', current == frozen)


@contextmanager
def baseline_checkout(requested):
    path = requested or (LOCAL_BASELINE if LOCAL_BASELINE.is_dir() else None)
    if path is not None:
        path = path.resolve(strict=True)
        actual = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
        assert actual == BASELINE, ('Wrong hero baseline', actual)
        assert not subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain'], text=True).strip(), 'Baseline must be clean'
        yield path
        return
    with tempfile.TemporaryDirectory(prefix='talabot-hero-baseline-') as temp:
        path = Path(temp) / 'source'
        subprocess.run(['git', 'worktree', 'add', '--detach', str(path), BASELINE], check=True)
        try:
            yield path
        finally:
            subprocess.run(['git', 'worktree', 'remove', '--force', str(path)], check=True)


def prepare(page):
    page.emulate_media(reduced_motion='reduce')
    page.evaluate("""()=>{
      scrollTo(0,0);
      document.querySelectorAll('.d6-bento img').forEach(i=>i.loading='eager');
      return Promise.all([...document.querySelectorAll('.d6-bento img')].map(i=>i.decode()));
    }""")
    prior.settle(page)


def hero_snapshot(page):
    return page.locator('.d6-bento').evaluate("""root=>{
      const base=root.getBoundingClientRect();
      const rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {
        x:r.x-base.x,y:r.y-base.y,width:r.width,height:r.height}};
      const style=e=>{if(!e)return null;const s=getComputedStyle(e);return Object.fromEntries([
        'display','position','borderRadius','paddingTop','paddingRight','paddingBottom','paddingLeft',
        'gap','fontSize','lineHeight','fontWeight','backgroundImage','backgroundColor','color',
        'objectFit','objectPosition','overflow','gridTemplateColumns','gridTemplateRows'
      ].map(k=>[k,s[k]]))};
      const classes=e=>e.className.split(/\\s+/).filter(Boolean).sort();
      const tile=e=>({tag:e.tagName,classes:classes(e),rect:rect(e),style:style(e),
        children:[...e.children].map(c=>({tag:c.tagName,classes:classes(c),style:style(c)}))});
      const main=root.querySelector(':scope > .d6-bm'),rail=main?.querySelector(':scope > #hsc.d6-bsc');
      const sides=[...root.querySelectorAll(':scope > button.d6-bt')],dots=main?.querySelector(':scope > .hdt');
      return {root:{rect:{width:base.width,height:base.height},style:style(root)},
        directChildren:[...root.children].map(e=>({tag:e.tagName,classes:classes(e)})),
        main:main?{rect:rect(main),style:style(main),railStyle:style(rail),slides:[...rail.children].map(tile)}:null,
        sides:sides.map(tile),dots:dots?{rect:rect(dots),style:style(dots),count:dots.children.length}:null};
    }""")


def compare_values(expected, actual, path='', differences=None):
    differences = differences if differences is not None else []
    if isinstance(expected, dict) and isinstance(actual, dict):
        if expected.keys() != actual.keys():
            differences.append({'path': path, 'expected_keys': list(expected), 'actual_keys': list(actual)})
        for key in expected.keys() & actual.keys():
            compare_values(expected[key], actual[key], path + '.' + key, differences)
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            differences.append({'path': path, 'expected_length': len(expected), 'actual_length': len(actual)})
        for index, (left, right) in enumerate(zip(expected, actual)):
            compare_values(left, right, path + '[' + str(index) + ']', differences)
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if abs(expected - actual) > .75:
            differences.append({'path': path, 'expected': expected, 'actual': actual})
    elif expected != actual:
        differences.append({'path': path, 'expected': expected, 'actual': actual})
    return differences


def record_image(run, filename, image, kind):
    image.save(run.output / filename, 'PNG' if filename.endswith('.png') else 'WEBP', **({} if filename.endswith('.png') else {'lossless': True}))
    run.screenshots.append({'file': filename, 'width': image.width, 'height': image.height, 'kind': kind,
                            'sha256': hashlib.sha256((run.output / filename).read_bytes()).hexdigest()})


def capture_hero(run, page, name):
    image = Image.open(io.BytesIO(page.locator('.d6-bento').screenshot(animations='disabled'))).convert('RGB')
    record_image(run, name, image, 'original hero element screenshot')


def capture_pair(run, lang, width, scene='home'):
    extension = 'webp' if scene == 'home' else 'png'
    names = [f'{lang}-{width}-{scene}-baseline.{extension}', f'{lang}-{width}-{scene}-candidate.{extension}']
    images = [Image.open(run.output / name).convert('RGB') for name in names]
    gap, header = 12, 32
    result = Image.new('RGB', (sum(i.width for i in images) + gap, max(i.height for i in images) + header), 'white')
    draw = ImageDraw.Draw(result)
    x = 0
    for label, image in zip(('8cd90a8a approved baseline', 'BRIEF-31d candidate'), images):
        draw.text((x + 8, 10), label, fill='black')
        result.paste(image, (x, header))
        x += image.width + gap
    filename = f'{lang}-{width}-{scene}-baseline-candidate.webp'
    record_image(run, filename, result, 'unaltered source screenshots, side by side')
    if scene != 'home':
        comparison = {'scene': scene, 'size_equal': images[0].size == images[1].size}
        if comparison['size_equal']:
            difference = ImageChops.difference(*images)
            red, green, blue = difference.split()
            changed = ImageChops.lighter(ImageChops.lighter(red, green), blue)
            comparison.update({'different_pixels': difference.width * difference.height - changed.histogram()[0],
                               'difference_bbox': difference.getbbox()})
        run.pixel_comparisons.append(comparison)


def check_dots_and_cta(run, page):
    layout = page.locator('.d6-bm').evaluate("""main=>{
      const m=main.getBoundingClientRect(),d=main.querySelector('.hdt')?.getBoundingClientRect(),
        c=main.querySelector('.d6-bsc > .d6-bt .cta')?.getBoundingClientRect();
      const inside=r=>!!r&&r.left>=m.left-.5&&r.right<=m.right+.5&&r.top>=m.top-.5&&r.bottom<=m.bottom+.5;
      return {dotsInside:inside(d),ctaInside:inside(c),separate:!!c&&!!d&&
        (c.bottom<=d.top||d.bottom<=c.top||c.right<=d.left||d.right<=c.left)};
    }""")
    run.check('AB-01', 'main dots and CTA stay inside the tile without overlap', all(layout.values()), layout)


def test_primary(run, browser, servers, photos, lang='ru', width=375, capture=True):
    snapshots = {}
    for label, server in servers.items():
        with run.page(browser, server, photos, lang, width, extra=PROOF_EXTRA) as page:
            prepare(page)
            run.equal('COUNTDOWN', label + ' primary proof contains no expiry and no timers', page.evaluate("""()=>[
              TLB.banners(true).some(b=>!!b.ends_at),document.querySelectorAll('.d6-bento .hcd[data-end]').length]"""), [False, 0])
            snapshots[label] = hero_snapshot(page)
            check_dots_and_cta(run, page)
            if capture:
                run.capture(page, f'{lang}-{width}-home-{label}.webp')
                capture_hero(run, page, f'{lang}-{width}-hero-{label}.png')
            prior.no_overflow(run, page, 'AB-02')
    if capture:
        capture_pair(run, lang, width)
        capture_pair(run, lang, width, 'hero')
    run.measurements.append({'case': run.case, 'sources': snapshots})
    baseline, candidate = snapshots['baseline'], snapshots['candidate']
    run.equal('AB-02', 'real baseline fixture has one large tile and two direct side tiles', len(baseline['sides']), 2)
    run.check('AB-01', 'real baseline fixture has multiple main slides and interior dots',
              len(baseline['main']['slides']) > 1 and baseline['dots']['count'] == len(baseline['main']['slides']), baseline)
    run.equal('AB-02', 'candidate preserves the two direct side slots', len(candidate['sides']), 2)
    sides = candidate['sides']
    run.check('AB-02', 'equal side rows align with the spanning main tile',
              abs(sides[0]['rect']['height'] - sides[1]['rect']['height']) < .75 and
              abs(sides[0]['rect']['y'] - candidate['main']['rect']['y']) < .75 and
              abs(sides[1]['rect']['y'] + sides[1]['rect']['height'] -
                  candidate['main']['rect']['y'] - candidate['main']['rect']['height']) < .75, candidate)
    differences = compare_values(baseline, candidate)
    run.check('AB-02', 'hero DOM classes, geometry and visual styles match the real baseline', not differences, differences)
    run.equal('AB-01', 'candidate dots correspond to the original main carousel',
              candidate['dots']['count'], len(candidate['main']['slides']))


def test_side_images(run, browser, servers, photos):
    snapshots = {}
    for label, server in servers.items():
        with run.page(browser, server, photos, 'ru', 375, extra=SIDE_ART_EXTRA) as page:
            prepare(page)
            images = page.locator('.d6-bento > button.d6-bt.img > img')
            run.equal('AB-03', label + ' has two original direct side image tiles', images.count(), 2)
            data = images.evaluate_all("""es=>es.map(e=>{const r=e.getBoundingClientRect(),p=e.parentElement.getBoundingClientRect(),s=getComputedStyle(e);return {
              fit:s.objectFit,position:s.objectPosition,fills:Math.abs(r.x-p.x)<.5&&Math.abs(r.y-p.y)<.5&&
              Math.abs(r.width-p.width)<.5&&Math.abs(r.height-p.height)<.5}})""")
            run.check('AB-03', label + ' side artwork covers its tile from left center',
                      all(d['fit'] == 'cover' and d['position'] == '0% 50%' and d['fills'] for d in data), data)
            snapshots[label] = hero_snapshot(page)
    differences = compare_values(snapshots['baseline'], snapshots['candidate'])
    run.check('AB-03', 'original side-image layout and styles match the baseline', not differences, differences)
    run.measurements.append({'case': run.case, 'sources': snapshots})


def test_original_countdown(run, browser, servers, photos):
    snapshots, timers = {}, {}
    for label, server in servers.items():
        with run.page(browser, server, photos, 'ru', 375, extra=HAPPY_EXTRA) as page:
            page.clock.set_fixed_time(prior.NOW)
            page.evaluate('()=>render()')
            prepare(page)
            timers[label] = page.locator('.d6-bento .hcd[data-end]').evaluate_all(
                'es=>es.map(e=>({end:e.dataset.end,text:e.textContent}))')
            run.equal('COUNTDOWN', label + ' retains the original scheduled Happy Hours countdown', len(timers[label]), 1)
            snapshots[label] = hero_snapshot(page)
            capture_hero(run, page, f'ru-375-happy-hero-{label}.png')
    run.equal('COUNTDOWN', 'countdown deadline and displayed text equal the original baseline', timers['candidate'], timers['baseline'])
    differences = compare_values(snapshots['baseline'], snapshots['candidate'])
    run.check('AB-02', 'Happy Hours artwork and countdown keep the original geometry', not differences, differences)
    capture_pair(run, 'ru', 375, 'happy-hero')
    run.measurements.append({'case': run.case, 'timers': timers, 'sources': snapshots})


def test_original_long_countdown_tick(run, browser, servers, photos):
    extra = PROOF_EXTRA + """
      T.banners[0].presentation={action:'campaign',campaign:'discount'};
      T.banners[0].ends_at='2026-11-20T14:10:30Z';
    """
    timers = {}
    for label, server in servers.items():
        with run.page(browser, server, photos, 'ru', 375, extra=extra) as page:
            page.clock.set_fixed_time(prior.NOW)
            page.evaluate('()=>render()')
            prepare(page)
            timer = page.locator('.d6-bento .hcd[data-end]')
            run.equal('COUNTDOWN', label + ' has one explicit campaign timer', timer.count(), 1)
            before = timer.inner_text()
            page.clock.set_fixed_time(prior.NOW + timedelta(seconds=2))
            page.clock.run_for(1100)
            timers[label] = {'before': before, 'after': timer.inner_text(), 'end': timer.get_attribute('data-end')}
            run.equal('COUNTDOWN', label + ' original interval updates hours beyond one day',
                      [timers[label]['before'], timers[label]['after']], ['53:10:30', '53:10:28'])
    run.equal('COUNTDOWN', 'candidate keeps the baseline long-duration formatter on the actual timer tick', timers['candidate'], timers['baseline'])
    run.measurements.append({'case': run.case, 'timers': timers})


def test_continuation(run, browser, server, photos):
    with run.page(browser, server, photos, 'ru', 375, extra=CONTINUATION_EXTRA) as page:
        prepare(page)
        run.equal('CONTINUITY', 'Orders single-banner component stays absent from Home', page.locator('.banner31-order-carousel').count(), 0)
        page.evaluate("()=>go('orders')")
        rail = page.locator('[data-banner-rail="orders"]')
        run.equal('CONTINUITY', 'Orders still renders its two configured slides', rail.locator('[data-banner-id]').count(), 2)
        run.equal('CONTINUITY', 'blank managed CTA remains absent outside the restored hero', rail.locator('[data-banner-id="orders-plain"] .banner31-cta').count(), 0)
        run.equal('CONTINUITY', 'configured Orders CTA remains its own label',
                  ' '.join(rail.locator('[data-banner-id="orders-label"] .banner31-cta').inner_text().split()), 'Открыть ресторан')
        geometry = rail.evaluate("""e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e),cards=[...e.children].map(c=>{
          const b=c.getBoundingClientRect();return {width:b.width,left:b.left,fit:getComputedStyle(c.querySelector('img')).objectFit}});
          return {width:r.width-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight),right:r.right-parseFloat(s.paddingRight),cards}}""")
        run.check('CONTINUITY', 'Orders retains one full-width uncropped image at a time',
                  all(abs(c['width'] - geometry['width']) < 1 and c['fit'] == 'contain' for c in geometry['cards']) and
                  geometry['cards'][1]['left'] >= geometry['right'] - 1, geometry)
        rail.locator('[data-banner-id="orders-plain"]').click()
        run.check('CONTINUITY', 'original Orders banner destination still opens', page.evaluate("S.v==='menu'&&S.store==='KFC'"))
        page.evaluate("()=>go('cat',{catKey:'rest',cq:'',srt:'',fo:false})")
        page.locator('.ad30-head').wait_for()
        restaurant = page.locator('[data-banner-rail="restaurants"] [data-banner-id="restaurants-label"]')
        run.equal('CONTINUITY', 'Restaurants keeps its configured banner placement', restaurant.count(), 1)
        restaurant.click()
        run.check('CONTINUITY', 'Restaurants banner keeps its original destination', page.evaluate("S.v==='menu'&&S.store==='Romant Restaurant'"))
        prior.no_overflow(run, page, 'CONTINUITY')
    with login.overlay_page(run, browser, server, photos) as (page, trace):
        page.locator('.ah06-auth .ah06-stories').wait_for()
        run.equal('CONTINUITY', 'AH-06 login retains its original three default stories', login.story_ids(page), login.DEFAULT_IDS)
        run.equal('CONTINUITY', 'login retains the original email and password fields',
                  page.locator('.ah06-sheet input').evaluate_all('es=>es.map(e=>e.id)'), ['tlb-em', 'tlb-pw'])
        login.original_form(run, page)
        run.equal('CONTINUITY', 'login presentation performs no sign-in request', [event['kind'] for event in trace['auth']], ['getSession'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--case', choices=['source', 'primary', 'side-images', 'countdown', 'continuity'])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for key in ('SUPABASE_URL', 'SUPABASE_ACCESS_TOKEN', 'DATABASE_URL', 'SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(key), 'Cloud context forbidden: ' + key
    coverage = {'source': {'SOURCE'}, 'primary': {'AB-01', 'AB-02', 'COUNTDOWN'}, 'side-images': {'AB-03'},
                'countdown': {'AB-02', 'COUNTDOWN'}, 'continuity': {'CONTINUITY'}}
    prior.EXPECTED_IDS = coverage.get(args.case, {'SOURCE', 'AB-01', 'AB-02', 'AB-03', 'COUNTDOWN', 'CONTINUITY'})
    run = prior.Acceptance(args.output)
    run.measurements = []
    run.pixel_comparisons = []
    run.provenance.update({'baseline': BASELINE, 'scope_base': SCOPE_BASE,
        'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'playwright_version': importlib.metadata.version('playwright')})
    dependencies = ('tools/brief31_webkit.py', 'tools/brief31c_webkit.py', 'tools/brief30_webkit.py',
                    'tools/brief25b_webkit.py', 'tools/brief24_webkit.py', 'tools/brief23_webkit.py',
                    'tools/brief22_webkit.py', 'tools/brief21_webkit.py', 'tools/qa_all.py',
                    'qa-fixtures/home-brief25b.json')
    run.provenance['harness_dependencies_sha256'] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in dependencies}
    if args.case in (None, 'source'):
        run.run('literal-source-and-scope', lambda: test_source_scope(run))
    photos = prior.cuisine_photos(prior.prior.fixture_logos(prior.prior.qa.source_photos()))
    with baseline_checkout(args.baseline) as baseline:
        servers = {'baseline': prior.prior.qa.serve(baseline), 'candidate': prior.prior.qa.serve(ROOT)}
        try:
            with sync_playwright() as pw:
                browser = pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
                run.provenance['webkit_version'] = browser.version
                if args.case in (None, 'primary'):
                    run.run('ru-375-primary-baseline-comparison', lambda: test_primary(run, browser, servers, photos))
                    run.run('ru-430-primary-baseline-comparison', lambda: test_primary(run, browser, servers, photos, width=430, capture=False))
                if args.case in (None, 'side-images'):
                    run.run('ru-375-original-side-artwork', lambda: test_side_images(run, browser, servers, photos))
                if args.case in (None, 'countdown'):
                    run.run('ru-375-original-happy-countdown', lambda: test_original_countdown(run, browser, servers, photos))
                    run.run('original-long-countdown-tick', lambda: test_original_long_countdown_tick(run, browser, servers, photos))
                if args.case in (None, 'continuity'):
                    run.run('orders-restaurants-login-continuation', lambda: test_continuation(run, browser, servers['candidate'], photos))
                browser.close()
        finally:
            for server in servers.values():
                server.shutdown()
    result = run.save()
    result['brief'] = 'BRIEF-31d'
    result['scope'] = 'Home hero only / original baseline and candidate HTML / synthetic SDK / offline WebKit'
    result['case_selection'] = args.case or 'all'
    result['hero_measurements'] = run.measurements
    result['pixel_comparisons'] = run.pixel_comparisons
    (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if not result['pass']:
        raise SystemExit('BRIEF31D_FAIL: see results.json')
    print(f'BRIEF31D_PASS {len(run.assertions)} assertions; {len(run.screenshots)} screenshot artifacts', flush=True)


if __name__ == '__main__':
    main()
