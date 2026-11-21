#!/usr/bin/env python3
"""AH-01 offline WebKit behavior checks against the original customer app.

Uses the BRIEF-31 synthetic SDK fixture; no production data or network access.
Run from the repository root: python tools/brief31b_cuisines.py /tmp/ah01-results
"""
import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

import brief31_webkit as prior


EXTRA = r"""
  for(const [id,section,store_id,image_url] of [
    ['sauces-ru','Соусы','s1','/qa-image/ah01-sauces-ru'],
    ['extras-en','Extras','s1','/qa-image/ah01-extras-en'],
    ['extras-ru',' Добавки ','s1','/qa-image/ah01-extras-ru'],
    ['sauces-en',' sAuCeS ','s1','/qa-image/ah01-sauces-en'],
    ['dips','Dips','s1','/qa-image/ah01-dips'],
    ['sides','Sides','s1','/qa-image/ah01-sides'],
    ['saucy','Saucy noodles','s1','/qa-image/ah01-saucy'],
    ['missing','Without image','s2',''],
    ['duplicate','Duplicate image','s2','/qa-image/brief30-plov'],
    ['failure','Failing cuisine','s2','/qa-image/ah01-failure']
  ])items.push({...items[0],id:'ah01-'+id,name:'QA '+id,section,store_id,image_url,
    price:5,discount_pct:0,popular:false});
"""


def enter(page):
    page.evaluate("go('cat',{catKey:'rest',cq:'',srt:'',fo:false})")
    page.locator('.ad30-head').wait_for()
    page.locator('.ad30-cuisine img').evaluate_all(
        "nodes=>Promise.all(nodes.map(i=>{i.loading='eager';return i.decode().catch(()=>null)}))")


def labels(page):
    return page.locator('.ad30-cuisine-label').all_text_contents()


def test_excluded_sections(run, browser, server, photos, lang, width):
    with run.page(browser, server, photos, lang, width, extra=EXTRA) as page:
        enter(page)
        actual = labels(page)
        blocked = {'соусы', 'extras', 'добавки', 'sauces'}
        run.check('AH-01', 'RU/EN sauce and add-on sections are omitted',
                  not blocked.intersection(x.strip().lower() for x in actual), actual)
        run.check('AH-01', 'unrelated dish names remain available', 'Saucy noodles' in actual, actual)


def test_configured_names(run, browser, server, photos, lang, width):
    with run.page(browser, server, photos, lang, width, extra=EXTRA) as page:
        page.evaluate("""()=>{TLB.restaurantCuisines=()=>[
          {id:'section:dips',name_ru:' Соусы ',name_en:'Condiments'},
          {id:'section:sides',name_ru:'Гарниры',name_en:' EXTRAS '},
          {id:'section:соусы',name_ru:'Основные блюда',name_en:'Main dishes'},
          {id:'plov',name_ru:'Домашний плов',name_en:'House pilaf'}
        ]}""")
        enter(page)
        actual = labels(page)
        run.check('AH-01', 'excluded name in either configured locale omits the category',
                  not {'Соусы', 'Condiments', 'Гарниры', 'EXTRAS'}.intersection(actual), actual)
        run.check('AH-01', 'configured title cannot reintroduce a sauce section',
                  not {'Основные блюда', 'Main dishes'}.intersection(actual), actual)
        run.check('AH-01', 'valid localized title is preserved',
                  ('Домашний плов' if lang == 'ru' else 'House pilaf') in actual, actual)


def test_missing_images(run, browser, server, photos, lang, width):
    with run.page(browser, server, photos, lang, width, extra=EXTRA) as page:
        enter(page)
        actual = labels(page)
        run.check('AH-01', 'missing or exhausted duplicate imagery never becomes a text chip',
                  'Without image' not in actual and 'Duplicate image' not in actual, actual)
        run.equal('AH-01', 'each rendered cuisine has one image',
                  page.locator('.ad30-cuisine img').count(), page.locator('.ad30-cuisine').count())


def test_failed_image(run, browser, server, photos, lang, width, selected):
    with run.page(browser, server, photos, lang, width, extra=EXTRA) as page:
        enter(page)
        chip = page.get_by_role('button', name='Failing cuisine', exact=True)
        run.equal('AH-01', 'valid cuisine image initially renders', chip.count(), 1)
        if selected:
            chip.click()
            run.equal('AH-01', 'working cuisine filter limits restaurants', page.locator('.ad30-card').count(), 1)
        # A newly configured URL avoids WebKit's decoded-image cache. A 200
        # response with invalid bytes exercises the real decoder error handler.
        page.route('**/qa-image/ah01-broken', lambda route: route.fulfill(
            status=200, content_type='image/jpeg', body=b'not a decodable image'))
        page.evaluate("""()=>{TLB.restaurantCuisines=()=>[
          {id:'section:failing cuisine',image_url:'/qa-image/ah01-broken'}
        ];render()}""")
        page.locator('.ad30-cuisine img').evaluate_all("nodes=>nodes.forEach(i=>i.loading='eager')")
        page.wait_for_function("()=>!document.querySelector('.ad30-cuisine img[src=\"/qa-image/ah01-broken\"]')")
        run.equal('AH-01', 'image failure removes the entire cuisine chip', chip.count(), 0)
        run.equal('AH-01', 'failed active cuisine does not leave a hidden filter',
                  page.locator('.ad30-card').count(), 3)
        run.equal('AH-01', 'no stale selected cuisine remains',
                  page.locator('.ad30-cuisine[aria-pressed="true"]').count(), 0)
        page.evaluate('render()')
        run.equal('AH-01', 'known failed image stays absent on later renders', chip.count(), 0)
        run.check('AH-01', 'other cuisine choices remain usable',
                  'Saucy noodles' in labels(page), labels(page))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ('SUPABASE_URL', 'SUPABASE_ACCESS_TOKEN', 'DATABASE_URL', 'SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(name), f'Cloud context forbidden: {name}'
    run = prior.Acceptance(args.output)
    server = prior.prior.qa.serve(Path.cwd())
    photos = prior.cuisine_photos(prior.prior.fixture_logos(prior.prior.qa.source_photos()))
    for name in ('sauces-ru', 'extras-en', 'extras-ru', 'sauces-en', 'dips', 'sides', 'saucy', 'failure'):
        photos['ah01-' + name] = photos['brief30-steak']
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            for lang, width in (('ru', 375), ('en', 390)):
                for name, check in [('sections', test_excluded_sections), ('configured-names', test_configured_names),
                                    ('missing-images', test_missing_images)]:
                    run.run(f'{lang}-{width}-{name}', lambda c=check, l=lang, w=width: c(run, browser, server, photos, l, w))
                for selected in (False, True):
                    run.run(f'{lang}-{width}-failed-image-selected-{selected}',
                            lambda s=selected, l=lang, w=width: test_failed_image(run, browser, server, photos, l, w, s))
            browser.close()
    finally:
        server.shutdown()
    result = {'scope': 'AH-01 / original HTML / synthetic SDK / offline WebKit',
              'assertions': run.assertions, 'failures': run.failures, 'contexts': run.contexts,
              'provenance': run.provenance, 'pass': not run.failures}
    (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if run.failures:
        raise SystemExit('AH01_FAIL: see results.json')
    print(f'AH01_PASS {len(run.assertions)} assertions', flush=True)


if __name__ == '__main__':
    main()
