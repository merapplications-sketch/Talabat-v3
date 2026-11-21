#!/usr/bin/env python3
"""AI-01b: original four-app login DOM, offline SDK and audited banner artwork.

This focused suite does not access a production account, database, or endpoint.
It exports run_ai01(run, browser, server, photos) for the BRIEF-32 master gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess

from playwright.sync_api import sync_playwright

import brief31c_webkit as login

prior = login.prior
ROOT = Path.cwd()
BASE = '7cc3136280b491cf23c4bf7e8f723d48ccfb10ce'
ITEM = 'AI-01'
DEFAULT_IDS = login.DEFAULT_IDS
ARTWORK = {
    'free': {'path': 'assets/shared/login-free-delivery-ai01b.png', 'size': [1514, 1039],
             'sha256': '6a9ca929a0abec75ed9aacd7082c59cbb21d6d6a14470837ce73238b1a5dd009'},
    'happy': {'path': 'assets/shared/login-burger-ai01b.png', 'size': [1298, 1212],
              'sha256': '1869136642bdbb3597682b6ee1e6f61f1096d3229918c3fcc1fb7dc5fff2a928'},
    'dineout-ru': {'path': 'assets/customer-c/dineout-header-ru.webp', 'size': [1200, 400],
                   'sha256': '6d17335f4cb7b5cd219a2dc7bd710c0be873108c3070b7807595028b0efc4c09'},
    'dineout-en': {'path': 'assets/customer-c/dineout-header-en.webp', 'size': [1200, 400],
                   'sha256': '345da3771866be9d6207b2a4fa97540aebb2d6ccf53e7d4414e8214434ec0d9a'},
}
OLD_IMAGE_EXPRESSION = """        image: kind === 'dineout' ? 'assets/customer-c/dineout-header-' + (lang === 'en' ? 'en' : 'ru') + '.webp' :
          'assets/3d/' + (kind === 'free' ? 'motor-scooter' : 'hamburger') + '.webp'};
"""
OLD_RADIUS = '  border-radius: 50% 50% 0 0 / var(--ah06-arc) var(--ah06-arc) 0 0 !important;\n'
NEW_RADIUS = '  border-radius: 32px 32px 0 0 !important;\n'
OLD_FOCAL_SELECTOR = '.ah06-slide--dineout:not(.ah06-slide--managed) .ah06-art img { object-position: right center; }\n'
NEW_FOCAL_SELECTOR = '.ah06-slide--free:not(.ah06-slide--managed) .ah06-art img,\n' + OLD_FOCAL_SELECTOR
WORKFLOW = '.github/workflows/unified-fix-brief15-20261117.yml'
OLD_WORKFLOW_ALLOWLINE = ('              tools/brief32_webkit.py|tools/brief32_login_webkit.py|tools/brief32_restaurants_webkit.py|'
                          'tools/brief32_scroll_webkit.py|assets/shared/banner-countdown-brief32.css|assets/preview/dineout-demo.json) ;;\n')


def artwork_paths():
    return [row['path'] for row in ARTWORK.values()]


def expected_artwork(lang):
    assert set(ARTWORK) == {'free', 'happy', 'dineout-ru', 'dineout-en'}, 'Audited original photo pins are required'
    return [ARTWORK['free'], ARTWORK['happy'], ARTWORK['dineout-en' if lang == 'en' else 'dineout-ru']]


def approved_image_expression():
    free, happy, _ = expected_artwork('ru')
    return ("        image: kind === 'dineout' ? 'assets/customer-c/dineout-header-' + (lang === 'en' ? 'en' : 'ru') + '.webp' :\n"
            "          (kind === 'free' ? " + json.dumps(free['path']) + ' : ' + json.dumps(happy['path']) + ')};\n')


class ItemAssertions:
    """Reuse the original-auth assertions under this item's evidence id."""
    def __init__(self, run):
        self.parent = run

    def __getattr__(self, name):
        return getattr(self.parent, name)

    def check(self, _item, *args, **kwargs):
        return self.parent.check(ITEM, *args, **kwargs)

    def equal(self, _item, *args, **kwargs):
        return self.parent.equal(ITEM, *args, **kwargs)


def test_source_scope(run):
    expected_artwork('ru')
    allowed = {
        'assets/shared/login-banners-ah06.js', 'assets/shared/login-banners-ah06.css',
        'tools/brief32_login_webkit.py', 'tools/brief32_webkit.py', WORKFLOW, *artwork_paths(),
    }
    paths = set(subprocess.check_output(['git', 'diff', '--name-only', BASE], text=True).splitlines())
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    paths.update(path for path in untracked if not path.startswith('qa-artifacts/ci1-fast/'))
    outside = sorted(path for path in paths if path not in allowed and
                     not path.startswith('qa-shots/unified-fix/brief32/ai01b/'))
    run.equal(ITEM, 'AI-01b freezes all unrelated product, workflow and prior evidence paths', outside, [])
    for name, substitutions in (
        ('assets/shared/login-banners-ah06.js', [(OLD_IMAGE_EXPRESSION, approved_image_expression())]),
        ('assets/shared/login-banners-ah06.css', [(OLD_RADIUS, NEW_RADIUS), (OLD_FOCAL_SELECTOR, NEW_FOCAL_SELECTOR)]),
    ):
        previous = subprocess.check_output(['git', 'show', BASE + ':' + name])
        expected = previous
        for old, new in substitutions:
            run.equal(ITEM, name + ' has exactly one authorized original expression', previous.count(old.encode()), 1)
            expected = expected.replace(old.encode(), new.encode(), 1)
        run.equal(ITEM, name + ' changes only the exact authorized image, corner or focal selector expressions',
                  hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), hashlib.sha256(expected).hexdigest())
    previous = subprocess.check_output(['git', 'show', BASE + ':' + WORKFLOW])
    run.equal(ITEM, 'H-01 workflow has exactly one original BRIEF32 allowlist line',
              previous.count(OLD_WORKFLOW_ALLOWLINE.encode()), 1)
    updated_line = OLD_WORKFLOW_ALLOWLINE.replace(') ;;\n',
        '|' + ARTWORK['free']['path'] + '|' + ARTWORK['happy']['path'] + ') ;;\n')
    expected = previous.replace(OLD_WORKFLOW_ALLOWLINE.encode(), updated_line.encode(), 1)
    run.equal(ITEM, 'H-01 workflow only adds the two exact audited image paths',
              hashlib.sha256((ROOT / WORKFLOW).read_bytes()).hexdigest(), hashlib.sha256(expected).hexdigest())
    for row in ARTWORK.values():
        run.equal(ITEM, row['path'] + ' matches the audited original bytes',
                  hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])


def active(page):
    return page.locator('.ah06-slide.is-active')


def edge(page, direction):
    return page.locator('.ah06-edge[data-ah06-action="' + direction + '"]')


def scene_geometry(page):
    return page.evaluate("""()=>{
      const story=document.querySelector('.ah06-stories'),h=story.getBoundingClientRect(),
        sheet=document.querySelector('.ah06-sheet'),s=sheet.getBoundingClientRect(),sc=getComputedStyle(sheet),
        slide=document.querySelector('.ah06-slide.is-active'),img=slide.querySelector('.ah06-art img'),
        i=img.getBoundingClientRect(),ic=getComputedStyle(img),
        title=slide.querySelector('.ah06-headline'),tc=getComputedStyle(title),
        subtitle=slide.querySelector('.ah06-subtitle'),sub=getComputedStyle(subtitle),
        cta=slide.querySelector('.ah06-cta'),c=cta.getBoundingClientRect(),cc=getComputedStyle(cta);
      const center=document.elementFromPoint(s.x+s.width/2,s.top+3),
        left=document.elementFromPoint(s.x+3,s.top+3),right=document.elementFromPoint(s.right-3,s.top+3);
      return {story:{x:h.x,y:h.y,width:h.width,height:h.height,bottom:h.bottom},
        image:{x:i.x,y:i.y,width:i.width,height:i.height,fit:ic.objectFit,natural:[img.naturalWidth,img.naturalHeight]},
        sheet:{top:s.top,bottom:s.bottom,background:sc.backgroundColor,
          corners:[sc.borderTopLeftRadius,sc.borderTopRightRadius,sc.borderBottomLeftRadius,sc.borderBottomRightRadius],
          shadow:sc.boxShadow,center:!!center?.closest('.ah06-sheet'),
          flatTop:[40,s.width/2,s.width-40].map(x=>document.elementFromPoint(s.x+x,s.top+1)?.closest('.ah06-sheet')===sheet),
          clearCorners:!left?.closest('.ah06-sheet')&&!right?.closest('.ah06-sheet')},
        title:{color:tc.color,size:parseFloat(tc.fontSize)},subtitle:{color:sub.color,size:parseFloat(sub.fontSize)},
        cta:{left:c.left,right:c.right,top:c.top,bottom:c.bottom,width:c.width,height:c.height,color:cc.color,
          background:cc.backgroundColor,hit:document.elementFromPoint(c.x+c.width/2,c.y+c.height/2)?.closest('.ah06-cta')===cta},
        edges:[...document.querySelectorAll('.ah06-edge')].map(e=>{const r=e.getBoundingClientRect();return {
          width:r.width,height:r.height,text:e.textContent,background:getComputedStyle(e).backgroundColor,label:e.getAttribute('aria-label')}})};
    }""")


def test_default(run, browser, server, photos, role, lang, width, capture=True):
    with login.overlay_page(run, browser, server, photos, role, lang, width, reduced=True) as (page, trace):
        page.locator('.ah06-stories').wait_for()
        page.locator('.ah06-art img').evaluate_all('es=>Promise.all(es.map(i=>i.decode()))')
        run.equal(ITEM, 'exactly three existing default stories', login.story_ids(page), DEFAULT_IDS)
        run.equal(ITEM, 'only story bars remain at the upper edge',
                  [page.locator('.ah06-progress-step').count(), page.locator('.ah06-count,.ah06-controls,.ah06-control,[data-ah06-action="pause"]').count()], [3, 0])
        run.equal(ITEM, 'two transparent edge tap controls replace visible arrows', edge(page, 'prev').count() + edge(page, 'next').count(), 2)
        login.original_form(ItemAssertions(run), page, admin=role == 'admin')
        login.check_pill(ItemAssertions(run), page, '.ah06-brand-slot .talabot-brand-pill', lang)
        expected = expected_artwork(lang)
        images = page.locator('.ah06-slide .ah06-art img').evaluate_all("""es=>es.map(i=>{
          const r=i.getBoundingClientRect(),s=i.closest('.ah06-slide').getBoundingClientRect(),
            h=i.closest('.ah06-stories').getBoundingClientRect(),css=getComputedStyle(i);
          return {src:i.getAttribute('src'),size:[i.naturalWidth,i.naturalHeight],decoded:i.complete&&i.naturalWidth>0&&i.naturalHeight>0,
            position:css.objectPosition,
            cover:css.objectFit==='cover'&&['x','y','width','height'].every(k=>Math.abs(r[k]-s[k])<1)&&
              ['width','height'].every(k=>Math.abs(s[k]-h[k])<1)};
        })""")
        run.equal(ITEM, 'all three default stories use the exact audited localized sources',
                  [row['src'] for row in images], [row['path'] for row in expected])
        run.equal(ITEM, 'all three default images retain the audited natural dimensions',
                  [row['size'] for row in images], [row['size'] for row in expected])
        run.equal(ITEM, 'scooter and DineOut retain right-center focal crops while burger stays centered',
                  [row['position'] for row in images], ['100% 50%', '50% 50%', '100% 50%'])
        run.check(ITEM, 'all three real story images decode and cover the full story frame',
                  len(images) == 3 and all(row['decoded'] and row['cover'] for row in images), images)
        metrics = scene_geometry(page)
        image, hero = metrics['image'], metrics['story']
        run.check(ITEM, 'actual story image covers the complete upper story area',
                  image['fit'] == 'cover' and image['natural'][0] > 0 and
                  all(abs(image[key] - hero[key]) < 1 for key in ('x', 'y', 'width', 'height')), metrics)
        run.check(ITEM, 'white sheet has a straight top edge and exactly 32px top corners',
                  metrics['sheet']['background'] == 'rgb(255, 255, 255)' and
                  metrics['sheet']['corners'] == ['32px', '32px', '0px', '0px'] and all(metrics['sheet']['flatTop']) and
                  metrics['sheet']['center'] and metrics['sheet']['clearCorners'] and
                  metrics['sheet']['shadow'] != 'none' and abs(hero['bottom'] - metrics['sheet']['top'] - 60) < 1, metrics)
        run.check(ITEM, 'large white headline and readable white subtitle overlay artwork',
                  metrics['title']['color'] == metrics['subtitle']['color'] == 'rgb(255, 255, 255)' and
                  metrics['title']['size'] >= 32 and metrics['subtitle']['size'] >= 14, metrics)
        run.check(ITEM, 'compact dark CTA remains an unobstructed touch target',
                  metrics['cta']['width'] < width * .78 and metrics['cta']['height'] >= 44 and metrics['cta']['hit'] and
                  metrics['cta']['bottom'] < metrics['sheet']['top'], metrics)
        run.equal(ITEM, 'default CTA uses the requested short localized label', active(page).locator('.ah06-cta').inner_text(), 'Смотреть' if lang == 'ru' else 'View')
        run.check(ITEM, 'edge controls remain accessible without visible decorations', all(
            e['width'] >= 44 and e['height'] >= 44 and not e['text'] and e['label'] and
            e['background'] == 'rgba(0, 0, 0, 0)' for e in metrics['edges']), metrics['edges'])
        run.equal(ITEM, 'decoration makes no unauthenticated data request', page.evaluate('__AH06DataCalls'), [])
        run.equal(ITEM, 'decoration does not initiate authentication', [x['kind'] for x in trace['auth']], ['getSession'])
        prior.no_overflow(run, page, ITEM)
        if capture:
            run.capture(page, f'{lang}-{width}-{role}-login-story-1.webp')
        edge(page, 'next').click()
        run.equal(ITEM, 'right-edge tap selects the next story', login.active_id(page), DEFAULT_IDS[1])
        if capture and role == 'customer':
            run.capture(page, f'{lang}-{width}-{role}-login-story-2.webp')
        edge(page, 'next').click()
        run.equal(ITEM, 'right-edge tap reaches the restaurant story', login.active_id(page), DEFAULT_IDS[2])
        if capture and role == 'customer':
            run.capture(page, f'{lang}-{width}-{role}-login-story-3.webp')
        edge(page, 'prev').click()
        run.equal(ITEM, 'left-edge tap returns to the previous story', login.active_id(page), DEFAULT_IDS[1])
        page.clock.fast_forward(16000)
        run.equal(ITEM, 'reduced motion keeps manual navigation without autoplay', login.active_id(page), DEFAULT_IDS[1])


def test_interaction(run, browser, server, photos):
    with login.overlay_page(run, browser, server, photos) as (page, trace):
        page.locator('.ah06-stories').wait_for()
        login.pause_clock(page)
        edge(page, 'next').evaluate('e=>e.click()')
        initial = login.active_id(page)
        page.clock.run_for(2500)
        _, bars = login.progress(page)
        amount = next(b['value'] for b in bars if b['id'] == initial)
        run.check(ITEM, 'five-second story bars reach halfway at 2.5 seconds', .45 <= amount <= .55, bars)
        page.clock.run_for(2400)
        run.equal(ITEM, 'story stays until the default deadline', login.active_id(page), initial)
        page.clock.run_for(150)
        run.check(ITEM, 'story advances after the default deadline', login.active_id(page) != initial)
        hero = page.locator('.ah06-stories').bounding_box()
        x, y = hero['x'] + hero['width'] * .7, hero['y'] + hero['height'] * .35
        page.mouse.move(x, y)
        page.mouse.down()
        held = login.active_id(page)
        page.clock.run_for(6500)
        run.equal(ITEM, 'holding the artwork pauses autoplay', login.active_id(page), held)
        page.mouse.move(hero['x'] + hero['width'] * .3, y, steps=12)
        page.mouse.up()
        page.clock.run_for(32)
        run.check(ITEM, 'real horizontal swipe navigates a story', login.active_id(page) != held)
        run.equal(ITEM, 'swipe never activates an offer or authentication', [x['kind'] for x in trace['auth']], ['getSession'])
        page.clock.resume()
        login.connect(page, login.feed_for(server, interval=7))
        login.pause_clock(page)
        edge(page, 'next').evaluate('e=>e.click()')
        held = login.active_id(page)
        page.clock.run_for(6500)
        run.equal(ITEM, 'existing seven-second administration setting remains effective', login.active_id(page), held)
        page.clock.run_for(600)
        run.check(ITEM, 'configured story advances at seven seconds', login.active_id(page) != held)


def test_managed_copy(run, browser, server, photos, lang, width):
    with login.overlay_page(run, browser, server, photos, lang=lang, width=width, reduced=True) as (page, trace):
        feed = login.feed_for(server)
        for row in feed['banners']:
            row['presentation'].update({'headline': {lang: 'H' * 80}, 'subtitle': {lang: 'S' * 160}, 'label': {lang: 'C' * 40}})
        login.connect(page, feed)
        lengths = active(page).locator('.ah06-headline,.ah06-subtitle,.ah06-cta').evaluate_all('es=>es.map(e=>e.textContent.length)')
        run.equal(ITEM, 'admin copy limits are preserved', lengths, [80, 160, 40])
        metrics = scene_geometry(page)
        run.check(ITEM, 'maximum admin copy keeps the CTA visible above the white sheet', metrics['cta']['hit'] and
                  metrics['cta']['bottom'] < metrics['sheet']['top'], metrics)
        prior.no_overflow(run, page, ITEM)
        run.capture(page, f'{lang}-{width}-customer-managed-maximum-copy.webp')
        login.connect(page, {'version': 1, 'banners': [], 'settings': {}}, mode='empty')
        run.equal(ITEM, 'connected empty feed remains neutral', [page.locator('.ah06-slide').count(), page.locator('.ah06-cta').count()], [0, 0])
        login.original_form(ItemAssertions(run), page)


def run_ai01(run, browser, server, photos, case='all', check_source=True):
    """Run focused cases; a combined gate can provide its own source guard."""
    if check_source and case in ('all', 'source'):
        run.run('AI-01-source-scope', lambda: test_source_scope(run))
    if case == 'smoke':
        run.run('AI-01-ru-customer', lambda: test_default(run, browser, server, photos, 'customer', 'ru', 375))
        return
    for lang, width in (('ru', 375), ('en', 390)):
        if case in ('all', 'managed'):
            run.run(f'AI-01-{lang}-managed', lambda l=lang,w=width: test_managed_copy(run,browser,server,photos,l,w))
        for role in login.ROLES:
            if case in ('all', 'defaults'):
                run.run(f'AI-01-{lang}-{role}-default', lambda r=role,l=lang,w=width: test_default(run,browser,server,photos,r,l,w))
            if case in ('all', 'auth'):
                run.run(f'AI-01-{lang}-{role}-auth', lambda r=role,l=lang,w=width: login.test_auth_contract(ItemAssertions(run),browser,server,photos,r,l,w))
    if case in ('all', 'interaction'):
        run.run('AI-01-tap-swipe-clock', lambda: test_interaction(run,browser,server,photos))
    if case in ('all', 'cta'):
        for access in ('public', 'after_auth'):
            run.run('AI-01-cta-' + access, lambda a=access: login.test_cta(ItemAssertions(run),browser,server,photos,a))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--case', choices=['all','source','smoke','defaults','managed','interaction','auth','cta'], default='all')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for key in ('SUPABASE_URL','SUPABASE_ACCESS_TOKEN','DATABASE_URL','SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(key), 'Production context forbidden: ' + key
    prior.EXPECTED_IDS = {ITEM}
    prior.PRODUCT_PATHS += [path for path in artwork_paths() if path not in prior.PRODUCT_PATHS]
    run = prior.Acceptance(args.output)
    run.provenance['harness_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    run.provenance['harness_dependencies_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in ('tools/brief31c_webkit.py','tools/brief31_webkit.py','tools/brief25b_webkit.py','tools/brief24_webkit.py','tools/qa_all.py')}
    run.provenance['playwright_version'] = importlib.metadata.version('playwright')
    server = prior.prior.qa.serve(ROOT)
    photos = prior.cuisine_photos(prior.prior.fixture_logos(prior.prior.qa.source_photos()))
    photos.update({'ah06-ru': photos['brief30-steak'], 'ah06-en': photos['brief30-plov']})
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            run.provenance['webkit_version'] = browser.version
            run_ai01(run, browser, server, photos, args.case)
            browser.close()
    finally:
        server.shutdown()
    result = run.save()
    result.update({'brief': 'BRIEF-32', 'item': ITEM, 'case_selection': args.case})
    (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if not result['pass']:
        raise SystemExit('BRIEF32_AI01_FAIL: see results.json')
    print(f'BRIEF32_AI01_PASS {len(run.assertions)} assertions; {len(run.screenshots)} viewport screenshots', flush=True)


if __name__ == '__main__':
    main()
