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
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

import brief31_webkit as prior

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


@contextmanager
def matching_page(run, browser, server, photos, *, extra='', lang='ru', width=375):
    with run.page(browser, server, photos, lang=lang, width=width,
                  extra=MATCHING_EXTRA + extra) as page:
        page.emulate_media(reduced_motion='reduce')
        yield page


def navigate_host(page, server, photos, hostname, query=''):
    """Serve unmodified checkout files under a test hostname, with no DNS/HTTP out."""
    def route(request):
        parsed = urlsplit(request.request.url)
        if parsed.path.startswith('/qa-image/'):
            key = parsed.path.rsplit('/', 1)[1]
            request.fulfill(status=200, content_type='image/jpeg', body=photos[key])
        else:
            response = request.fetch(url=f'http://127.0.0.1:{server.server_port}' +
                                     parsed.path + ('?' + parsed.query if parsed.query else ''))
            request.fulfill(response=response)
    page.context.route(f'https://{hostname}/**', route)
    page.goto(f'https://{hostname}/customer.html' + query, wait_until='domcontentloaded')
    page.wait_for_function("typeof TLB!=='undefined'&&TLB.stores().length===2&&document.querySelector('.d6-bento')")
    page.evaluate('()=>{TLB.speed=()=>({min:20});render()}')


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

        for host, query, expected in (
            ('talabot-live.test', '', False),
            ('talabot-gate1-preview-20261116.pages.dev.attacker.test', '', False),
            ('talabot-live.test', '?demo=other', False),
            ('talabot-gate1-preview-20261116.pages.dev', '', True),
            ('talabot-live.test', '?demo=dineout', True),
        ):
            count = len(demo_requests)
            navigate_host(page, server, photos, host, query)
            page.wait_for_load_state('networkidle')
            run.equal('AI-02', 'JSON fetch gate: ' + host + query, len(demo_requests) - count, int(expected))
            run.equal('AI-02', 'demo visibility: ' + host + query, page.locator('[data-dineout-demo]').count(), int(expected))
            run.equal('AI-02', 'display data never enters core: ' + host + query, fixture_state(page), initial)
            if expected:
                card = page.locator('[data-dineout-demo]')
                run.equal('AI-02', 'demo has literal Test badge', card.locator('.hb.k').inner_text().strip(), 'Тест')
                run.equal('AI-02', 'demo has no order/cart/store action',
                          card.evaluate("e=>({tag:e.tagName,onclick:e.getAttribute('onclick'),buttons:e.querySelectorAll('button').length})"),
                          {'tag': 'ARTICLE', 'onclick': None, 'buttons': 0})
                card.scroll_into_view_if_needed()
                run.capture(page, 'ai02-ru-375-' + ('preview-host' if not query else 'query-opt-in') + '.webp')
                page.locator('[data-section="dine"] button').click()
                run.equal('AI-02', 'demo remains display-only on expanded list', page.locator('[data-dineout-demo]').count(), 1)
                run.equal('AI-02', 'expanded demo also leaves core untouched', fixture_state(page), initial)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--case', choices=['preview', 'popular'])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for key in ('SUPABASE_URL', 'SUPABASE_ACCESS_TOKEN', 'DATABASE_URL', 'SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(key), 'Cloud context forbidden: ' + key
    prior.EXPECTED_IDS = {'AI-02'} if args.case == 'preview' else {'AI-07'} if args.case == 'popular' else {'AI-02','AI-07'}
    prior.PRODUCT_PATHS += ['assets/preview/dineout-demo.json']
    run = prior.Acceptance(args.output)
    run.provenance.update({'scope_base': SCOPE_BASE,
        'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'matching_state': '2 restaurants; discount_pct=0; no happy hours; no admin banners; synthetic SDK and fixture photographs'})
    photos = prior.cuisine_photos(prior.prior.fixture_logos(prior.prior.qa.source_photos()))
    with baseline_checkout() as source:
        server = prior.prior.qa.serve(ROOT)
        baseline = prior.prior.qa.serve(source)
        try:
            with sync_playwright() as pw:
                browser = pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
                run.provenance['webkit_version'] = browser.version
                if args.case in (None, 'preview'):
                    run.run('ai02-preview-gate-and-core-isolation', lambda: test_preview(run, browser, server, photos))
                if args.case in (None, 'popular'):
                    run.run('ai07-popular-only-sizing', lambda: test_popular(run, browser, server, baseline, photos))
                browser.close()
        finally:
            server.shutdown()
            baseline.shutdown()
    result = run.save()
    result['brief'] = 'BRIEF-32'
    result['scope'] = __doc__.strip()
    (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if not result['pass']:
        raise SystemExit('BRIEF32_FAIL: see results.json')
    print(f'BRIEF32_PASS {len(run.assertions)} assertions; {len(run.screenshots)} screenshots', flush=True)


if __name__ == '__main__':
    main()
