#!/usr/bin/env python3
"""BRIEF-31b: original four-app HTML, synthetic SDK, offline WebKit only."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright

import brief31_webkit as prior
import brief31b_cuisines as cuisines

ROOT = Path.cwd()
OWNER_LOGO_SOURCE_COMMIT = '991e86727a307564e08c36be5360b89300e2bbdd'
LOGO_SHA256 = {'en': 'd70ab0a9901e4754f375d7967d43604c84cf9f57f36aea2b9beb15e0e694eaa3',
               'ru': 'b4e016d9c81f28b87f7c77d5458d4ba7b84e840480d650433478fa39dbff2af7'}
BRAND_SOURCE = 'assets/shared/brand-brief31b.js'
prior.PRODUCT_PATHS += ['driver.html', 'merchant.html', BRAND_SOURCE,
                        'assets/brand/logo-talabot-en.webp', 'assets/brand/logo-talabot-ru.webp']


def expected_logo(lang):
    return 'assets/brand/logo-talabot-' + ('en' if lang == 'en' else 'ru') + '.webp'


def check_logo(run, page, selector, lang, name):
    page.wait_for_function("([s,v])=>[...document.querySelectorAll(s)].length>0&&"
                           "[...document.querySelectorAll(s)].every(i=>i.getAttribute('src')===v)",
                           arg=[selector, expected_logo(lang)])
    images = page.locator(selector).evaluate_all("nodes=>Promise.all(nodes.map(async i=>{"
        "await i.decode();return {src:i.getAttribute('src'),alt:i.alt,width:i.naturalWidth,height:i.naturalHeight}}))")
    run.check('AH-03', name, bool(images) and all(i['src'] == expected_logo(lang) and
              i['alt'] == 'Talabot' and i['width'] == 900 and i['height'] == (302 if lang == 'en' else 298) for i in images), images)


def test_assets(run):
    for lang, expected in LOGO_SHA256.items():
        path = ROOT / expected_logo(lang)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        run.equal('AH-03', lang + ' logo is byte-identical to owner source', digest, expected)
        im = Image.open(path)
        run.equal('AH-03', lang + ' source alpha channel is retained', im.convert('RGBA').getchannel('A').getextrema(), (0, 255))


def test_expiry(run, browser, server, photos, lang, width):
    with run.page(browser, server, photos, lang, width, extra=prior.BANNER_EXTRA, role='admin') as page:
        page.evaluate("()=>{tab='b';openBE('b31-multiple')}")
        native = page.locator('#banner-end-time')
        native.fill('2026-11-21T17:24:31')
        label = page.locator('[data-banner-end-display="banner-end-time"]')
        expected = '21 Nov 2026 17:24' if lang == 'en' else '21.11.2026 17:24'
        run.equal('AH-02', 'exact localized expiry without seconds', label.inner_text(), expected)
        run.equal('AH-02', 'editing retains canonical value and original seconds', page.evaluate('BD.to'), '2026-11-21T17:24:31')
        run.equal('AH-02', 'Dushanbe storage unchanged', page.evaluate('bannerEndIso(BD.to)'), '2026-11-21T17:24:31+05:00')
        run.equal('AH-02', 'existing UTC timestamp round trip', page.evaluate("bannerEndShow('2026-11-21T12:24:31Z')"), '2026-11-21T17:24:31')
        run.equal('AH-02', 'native control remains accessible', native.get_attribute('type'), 'datetime-local')
        native.focus()
        origin_lang = lang
        switched_lang = 'ru' if lang == 'en' else 'en'
        page.evaluate('(l)=>TLB.setLang(l)', switched_lang)
        run.equal('AH-02', 'focused expiry follows language immediately without redraw', label.inner_text(),
                  '21 Nov 2026 17:24' if switched_lang == 'en' else '21.11.2026 17:24')
        run.equal('AH-02', 'language update retains field focus and precise draft',
                  page.evaluate('[document.activeElement.id,BD.to]'), ['banner-end-time','2026-11-21T17:24:31'])
        page.evaluate('(l)=>TLB.setLang(l)', origin_lang)
        if lang == 'ru':
            native.locator('..').evaluate('e=>window.scrollTo(0,scrollY+e.getBoundingClientRect().top-180)')
            prior.settle(page)
            run.capture(page, 'ru-375-admin-expiry.webp')
        native.fill('')
        run.equal('AH-02', 'cleared expiry displays no fabricated date', label.inner_text(), '—')
        run.equal('AH-02', 'cleared expiry serializes null', page.evaluate('bannerEndIso(BD.to)'), None)
        page.evaluate("()=>{BE=null;BD=null;showAddB=true;render()}")
        page.locator('#bto').fill('2026-11-21T17:24')
        run.equal('AH-02', 'new-banner field uses same locale display',
                  page.locator('[data-banner-end-display="bto"]').inner_text(), expected)
        next_lang = 'ru' if lang == 'en' else 'en'
        page.locator('#bto').focus()
        page.evaluate('(lang)=>TLB.setLang(lang)', next_lang)
        run.equal('AH-02', 'unsaved new-banner expiry survives language redraw', page.locator('#bto').input_value(), '2026-11-21T17:24')
        run.equal('AH-02', 'preserved field label follows language redraw',
                  page.locator('[data-banner-end-display="bto"]').inner_text(),
                  '21 Nov 2026 17:24' if next_lang == 'en' else '21.11.2026 17:24')
        prior.no_overflow(run, page, 'AH-02')


@contextmanager
def overlay_page(run, browser, server, role, lang, width, mode):
    trace = {'case': run.case, 'role': role, 'language': lang, 'mode': mode,
             'blocked': [], 'page_errors': [], 'http_errors': []}
    context = browser.new_context(viewport={'width': width, 'height': 844 if width >= 390 else 812},
                                  is_mobile=True, has_touch=True, device_scale_factor=1, service_workers='block')
    context.set_default_timeout(7000)
    context.add_init_script('localStorage.setItem("tlb_lang",' + json.dumps(lang) + ');')
    source = prior.sdk(role=role)
    session = "getSession:function(){return Promise.resolve({data:{session:{user:user,access_token:'x'}},error:null})}"
    assert source.count(session) == 1
    replacement = ('getSession:function(){return Promise.resolve({data:{session:null},error:null})}' if mode == 'login' else
                   'getSession:function(){return new Promise(function(){})}')
    source = source.replace(session, replacement)

    def route(request):
        url = urlsplit(request.request.url)
        if url.hostname == 'cdn.jsdelivr.net' and 'supabase-js' in url.path:
            request.fulfill(content_type='application/javascript', body=source)
        elif url.hostname == '127.0.0.1' and url.port == server.server_port and request.request.method == 'GET':
            request.continue_()
        else:
            trace['blocked'].append(request.request.url)
            request.abort('blockedbyclient')

    context.route('**/*', route)
    page = context.new_page()
    page.on('pageerror', lambda e: trace['page_errors'].append(str(e)))
    page.on('response', lambda r: trace['http_errors'].append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
    page.clock.install(time=prior.NOW)
    page.goto(f'http://127.0.0.1:{server.server_port}/{role}.html', wait_until='domcontentloaded')
    page.locator('#tlb-ov' if mode == 'login' else '#tlb-boot').wait_for()
    try:
        yield page
        run.check('NETWORK', 'overlay blocks unexpected outside requests', not trace['blocked'], trace['blocked'])
        run.check('NETWORK', 'overlay has no runtime errors', not trace['page_errors'], trace['page_errors'])
        run.check('NETWORK', 'overlay assets load successfully', not trace['http_errors'], trace['http_errors'])
    finally:
        run.contexts.append(trace)
        context.close()


def test_overlay(run, browser, server, role, lang, width, mode):
    with overlay_page(run, browser, server, role, lang, width, mode) as page:
        selector = ('#tlb-ov img[data-talabot-logo]:visible' if mode == 'login' else '#tlb-boot img[data-talabot-logo]')
        # querySelector cannot use Playwright's :visible pseudo; the driver hides its legacy core wrapper.
        dom_selector = selector.replace(':visible', '')
        check_logo(run, page, dom_selector, lang, role + ' ' + mode + ' localized logo')
        run.equal('AH-03', role + ' ' + mode + ' has one visible logo', page.locator(selector).count(), 1)
        if role == 'customer' and mode == 'login' and lang in ('ru', 'en'):
            run.capture(page, f'{lang}-{width}-customer-login.webp')
        origin = page.evaluate('performance.timeOrigin')
        for locale in ('en', 'tg', 'ru'):
            page.evaluate('(l)=>TLB.setLang(l)', locale)
            check_logo(run, page, dom_selector, locale, role + ' ' + mode + ' switches to ' + locale)
        run.equal('AH-03', 'language changes do not reload the app', page.evaluate('performance.timeOrigin'), origin)
        prior.no_overflow(run, page, 'AH-03')


def test_app(run, browser, server, photos, role, lang, width):
    with run.page(browser, server, photos, lang, width, role=role) as page:
        selector = {'customer': '.d6h .d6-hr > img.d6-logo', 'driver': '.a-brand img',
                    'merchant': '.st-merchant .nav img[data-talabot-logo]', 'admin': '.sbrand img[data-talabot-logo]'}[role]
        if role in ('merchant', 'admin'):
            page.set_viewport_size({'width': 1440, 'height': 900})
        check_logo(run, page, selector, lang, role + ' application brand')
        run.check('AH-03', role + ' brand is visible', page.locator(selector).first.is_visible())
        if role == 'customer':
            # AH-04 explicitly supersedes the former 20px Home logo box.
            run.equal('AH-03', 'customer header logo follows approved AH-04 height', page.locator(selector).evaluate('e=>e.getBoundingClientRect().height'), 36)
            store_images = page.locator('.home-brand-image').evaluate_all('xs=>xs.map(i=>i.getAttribute("src"))')
            run.check('AH-03', 'restaurant logos stay restaurant assets', bool(store_images) and all('assets/brand/logo-talabot-' not in x for x in store_images), store_images)
            if lang in ('ru', 'en'):
                run.capture(page, f'{lang}-{width}-customer-home.webp')
        if role == 'driver':
            height = page.evaluate('s=>document.querySelector(s).getBoundingClientRect().height', selector)
            run.check('AH-03', 'driver header retains original image height', abs(height - 104 * 504 / 2404) < .1, height)
        for locale in ('en', 'tg', 'ru'):
            page.evaluate('(l)=>TLB.setLang(l)', locale)
            check_logo(run, page, selector, locale, role + ' header switches to ' + locale)
        prior.no_overflow(run, page, 'AH-03')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--items', nargs='+', default=['AH-01', 'AH-02', 'AH-03'])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for key in ('SUPABASE_URL', 'SUPABASE_ACCESS_TOKEN', 'DATABASE_URL', 'SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(key), f'Cloud context forbidden: {key}'
    prior.EXPECTED_IDS = set(args.items)
    run = prior.Acceptance(args.output)
    run.provenance['owner_logo_source_commit'] = OWNER_LOGO_SOURCE_COMMIT
    run.provenance['harness_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    run.provenance['harness_dependencies_sha256'] = {
        path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        for path in ('tools/brief31_webkit.py','tools/brief31b_cuisines.py')}
    run.provenance['playwright_version'] = importlib.metadata.version('playwright')
    server = prior.prior.qa.serve(ROOT)
    photos = prior.cuisine_photos(prior.prior.fixture_logos(prior.prior.qa.source_photos()))
    for name in ('sauces-ru', 'extras-en', 'extras-ru', 'sauces-en', 'dips', 'sides', 'saucy', 'failure'):
        photos['ah01-' + name] = photos['brief30-steak']
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            run.provenance['webkit_version'] = browser.version
            for lang, width in (('ru', 375), ('en', 390), ('tg', 375)):
                if 'AH-02' in args.items:
                    run.run(f'{lang}-expiry', lambda l=lang,w=width: test_expiry(run,browser,server,photos,l,w))
                if 'AH-03' in args.items:
                    for role in ('customer', 'driver', 'merchant', 'admin'):
                        run.run(f'{lang}-{role}-brand', lambda r=role,l=lang,w=width: test_app(run,browser,server,photos,r,l,w))
                        for mode in ('login', 'loading'):
                            run.run(f'{lang}-{role}-{mode}', lambda r=role,l=lang,w=width,m=mode: test_overlay(run,browser,server,r,l,w,m))
                if 'AH-01' in args.items and lang in ('ru', 'en'):
                    for name, check in [('sections', cuisines.test_excluded_sections), ('configured', cuisines.test_configured_names), ('missing-images', cuisines.test_missing_images)]:
                        run.run(f'{lang}-cuisines-{name}', lambda c=check,l=lang,w=width: c(run,browser,server,photos,l,w))
                    for selected in (False, True):
                        run.run(f'{lang}-cuisines-failed-{selected}', lambda s=selected,l=lang,w=width: cuisines.test_failed_image(run,browser,server,photos,l,w,s))
            if 'AH-01' in args.items:
                with run.page(browser,server,photos,extra="items.filter(i=>i.id==='tea'||i.id==='juice').forEach(i=>i.image_url='');") as page:
                    cuisines.enter(page)
                    page.locator('.ad30-cuisines').evaluate('e=>window.scrollTo(0,scrollY+e.getBoundingClientRect().top-150)')
                    run.capture(page,'ru-375-restaurants-cuisines.webp')
            if 'AH-03' in args.items:
                run.run('owner-assets', lambda: test_assets(run))
            browser.close()
    finally:
        server.shutdown()
    result = run.save()
    result['brief'] = 'BRIEF-31b'
    if 'AH-03' in args.items:
        audit = []
        for lang in ('en', 'ru'):
            im = Image.open(ROOT / expected_logo(lang)).convert('RGBA')
            pixels = list(im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata())
            opaque_black = sum(a == 255 and max(r,g,b) <= 8 for r,g,b,a in pixels)
            audit.append({'language':lang, 'pixels':len(pixels), 'opaque_near_black_pixels':opaque_black,
                          'fully_transparent_pixels':im.getchannel('A').histogram()[0],
                          'top_left_alpha':im.getpixel((0,0))[3],
                          'transparent_background':im.getpixel((0,0))[3] == 0 and opaque_black < len(pixels)*.05})
        result['owner_asset_review'] = audit
        result['visual_acceptance'] = all(a['transparent_background'] for a in audit)
        if not result['visual_acceptance']:
            print('BRIEF31B_SOURCE_ASSET_BLOCKER: exact supplied logos retain an opaque black background; see owner_asset_review', flush=True)
    (args.output / 'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if not result['pass']:
        raise SystemExit('BRIEF31B_FAIL: see results.json')
    print(f'BRIEF31B_FUNCTIONAL_PASS {len(run.assertions)} assertions; {len(run.screenshots)} viewport screenshots', flush=True)


if __name__ == '__main__':
    main()
