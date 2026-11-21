#!/usr/bin/env python3
"""BRIEF-32 AI03/AI06: original restaurant HTML, synthetic SDK, offline WebKit.

The default fixture has two restaurants, no DineOut offers, and no admin banners.
The approved 8cd90a8a checkout supplies the original default-banner comparison.
No product HTML is patched or replaced by the harness.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

import brief31_webkit as prior
from brief31d_webkit import BASELINE, baseline_checkout

ROOT = Path.cwd()
DEFAULT_EXTRA = r"""
  stores.splice(2);
  stores.forEach(s=>{s.discount_pct=0;s.free_delivery_min=0;s.free_first_delivery=false;});
  stores[0].description='';
  stores[1].description='Local & European';
  T.happy_hours=[];T.banners=[];
"""
MANAGED_EXTRA = DEFAULT_EXTRA + r"""
  T.banners=[
    {id:'restaurants-first',title:'Restaurant offer',placement:'top',is_active:true,sort:1,
      image_url:'/qa-image/kfc',link_type:'store',link_value:'s2',presentation:{
        placements:['restaurants'],action:'restaurant',label:{ru:'Открыть ресторан',en:'Open restaurant'},
        images:{ru:'/qa-image/kfc',en:'/qa-image/romant'}}},
    {id:'restaurants-free',title:'Delivery offer',placement:'top',is_active:true,sort:2,
      image_url:'/qa-image/romant',presentation:{placements:['restaurants'],action:'list',filter:'free'}},
    {id:'orders-only',title:'Orders only',placement:'top',is_active:true,sort:0,
      image_url:'/qa-image/kfc',presentation:{placements:['orders'],action:'restaurant'}}
  ];
"""


def enter(page):
    page.evaluate("openCat('rest')")
    page.locator('.ad30-head').wait_for()
    page.evaluate("""()=>Promise.all([...document.querySelectorAll('.ad30-banner img')].map(i=>{
      i.loading='eager';return i.decode().catch(()=>null);
    }))""")
    prior.settle(page)


def route_state(page):
    return page.evaluate("({view:S.v,category:S.catKey,sort:S.srt,open:S.fo})")


def banner_shape(page):
    return page.locator('.ad30-banner-row').evaluate("""rail=>{
      const r=rail.getBoundingClientRect();
      const style=e=>{const s=getComputedStyle(e);return Object.fromEntries(
        ['display','position','flexBasis','aspectRatio','borderRadius','padding','backgroundColor',
         'color','fontSize','lineHeight','fontWeight','objectFit','overflow'].map(k=>[k,s[k]]));};
      const bounds=e=>{const b=e.getBoundingClientRect();return [b.x-r.x,b.y-r.y,b.width,b.height];};
      return {rail:style(rail),cards:[...rail.children].map(e=>({
        tag:e.tagName,cls:e.className,label:e.getAttribute('aria-label'),tap:e.getAttribute('onclick'),
        rect:bounds(e),style:style(e),children:[...e.children].map(c=>({
          tag:c.tagName,cls:c.className,text:c.textContent,src:c.getAttribute('src'),rect:bounds(c),style:style(c)
        }))
      }))};
    }""")


def save_pair(run, before, after, name):
    images=[Image.open(io.BytesIO(raw)).convert('RGB') for raw in (before,after)]
    canvas=Image.new('RGB',(sum(i.width for i in images),28+max(i.height for i in images)),'white')
    draw=ImageDraw.Draw(canvas);x=0
    for title,image in zip(('8cd90a8a approved baseline','BRIEF-32 candidate'),images):
        draw.text((x+6,7),title,fill='black');canvas.paste(image,(x,28));x+=image.width
    path=run.output/name;canvas.save(path,'WEBP',lossless=True,method=4)
    run.screenshots.append({'file':name,'width':canvas.width,'height':canvas.height,
                            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    if images[0].size==images[1].size:
        diff=ImageChops.difference(*images)
        maximum=ImageChops.lighter(ImageChops.lighter(*diff.split()[:2]),diff.split()[2])
        count=images[0].width*images[0].height-maximum.histogram()[0]
        run.pixel_comparisons.append({'file':name,'different_pixels':count,'difference_bbox':diff.getbbox()})


def test_defaults(run,browser,servers,photos,lang,width):
    observed={};shots={}
    for revision,server in servers.items():
        with run.page(browser,server,photos,lang,width,extra=DEFAULT_EXTRA) as page:
            run.equal('AI03','fixture has exactly the two restaurants',
                      page.evaluate("STORES.map(s=>s.n)"),['KFC','Romant Restaurant'])
            run.equal('AI03','fixture has no DineOut-eligible restaurant',page.evaluate('STORES.filter(s=>s.disc>0).length'),0)
            if revision=='candidate':
                run.equal('AI03','current Home hides the empty DineOut section',page.locator('.dine-head,.home-dine').count(),0)
            run.equal('AI03','fixture has no admin banners',page.evaluate('TLB.banners().length'),0)
            enter(page)
            run.equal('AI03',revision+' shows the three original default banners',
                      page.locator('.ad30-banner').count(),3)
            labels=['Скидки','Бесплатная доставка','Для вас'] if lang=='ru' else ['Discounts','Free delivery','For you']
            run.equal('AI03',revision+' default labels keep their original order',
                      page.locator('.ad30-banner b').all_text_contents(),labels)
            observed[revision]=banner_shape(page)
            shots[revision]=page.locator('.ad30-banner-row').screenshot(animations='disabled')
            prior.no_overflow(run,page,'AI03')
            if revision=='candidate':
                run.capture(page,f'{lang}-{width}-restaurants-defaults.webp')
                page.locator('.ad30-banner-row').evaluate('e=>e.scrollLeft=e.scrollWidth')
                run.check('AI03','third default is reachable by horizontal scrolling',
                          page.locator('.ad30-tone-you').evaluate('e=>{const r=e.getBoundingClientRect();return r.right<=innerWidth&&r.left>=0}'))
                run.capture(page,f'{lang}-{width}-restaurants-third-default.webp')
    run.equal('AI03','all default banner markup, relative geometry, and visual styles match 8cd90a8a',
              observed['candidate'],observed['baseline'])
    save_pair(run,shots['baseline'],shots['candidate'],f'{lang}-{width}-default-banners-baseline-candidate.webp')


def test_default_destinations(run,browser,server,photos):
    with run.page(browser,server,photos,extra=DEFAULT_EXTRA) as page:
        for tone,sort in [('disc','disc'),('free','free'),('you','')]:
            enter(page)
            run.equal('AI03',tone+' default destination is available',page.locator('.ad30-tone-'+tone).count(),1)
            page.locator('.ad30-tone-'+tone).click()
            run.equal('AI03',tone+' opens its original individual destination',route_state(page),
                      {'view':'cat','category':'rest','sort':sort,'open':bool(sort)})
            run.equal('AI03',tone+' produces the real matching restaurant list',
                      page.locator('.ad30-card .ad30-card-name').all_text_contents(),
                      [] if sort else ['KFC','Romant Restaurant'])
            if sort:
                run.equal('AI03',tone+' has the existing honest empty-filter state',page.locator('.ad30-empty').count(),1)
        page.evaluate("()=>{const rows=TLB.stores();rows[0].fee_type='free';rows[1].discount_pct=20;syncStores()}")
        for tone,expected in [('disc',['Romant Restaurant']),('free',['KFC']),('you',['KFC','Romant Restaurant'])]:
            enter(page);page.locator('.ad30-tone-'+tone).click()
            run.equal('AI03',tone+' uses genuine offer eligibility when offers exist',
                      page.locator('.ad30-card-name').all_text_contents(),expected)


def test_managed(run,browser,server,photos,lang,width):
    with run.page(browser,server,photos,lang,width,extra=MANAGED_EXTRA) as page:
        enter(page)
        run.equal('AI03','configured restaurant placement replaces the default trio',
                  page.locator('.ad30-banner').evaluate_all('es=>es.map(e=>e.dataset.bannerId)'),
                  ['restaurants-first','restaurants-free'])
        run.equal('AI03','managed rail preserves placement and rotation metadata',
                  page.locator('.ad30-banner-row').get_attribute('data-banner-rail'),'restaurants')
        run.equal('AI03','managed art follows the selected language',
                  page.locator('[data-banner-id="restaurants-first"]>img').get_attribute('src'),
                  '/qa-image/kfc' if lang=='ru' else '/qa-image/romant')
        run.equal('AI03','managed optional CTA remains optional',
                  page.locator('[data-banner-id="restaurants-free"] .banner31-cta').count(),0)
        run.capture(page,f'{lang}-{width}-restaurants-managed.webp')
        page.locator('[data-banner-id="restaurants-first"]').click()
        run.equal('AI03','managed restaurant target is unchanged',page.evaluate('({view:S.v,store:S.store})'),
                  {'view':'menu','store':'Romant Restaurant'})
        enter(page);page.locator('[data-banner-id="restaurants-free"]').click()
        run.equal('AI03','managed list target is unchanged',route_state(page),
                  {'view':'cat','category':'rest','sort':'free','open':True})
        prior.no_overflow(run,page,'AI03')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--case',choices=['ai03'],default='ai03')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for key in ('SUPABASE_URL','SUPABASE_ACCESS_TOKEN','DATABASE_URL','SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(key),'Cloud context forbidden: '+key
    prior.EXPECTED_IDS={'AI03'}
    run=prior.Acceptance(args.output);run.pixel_comparisons=[]
    run.provenance.update({'baseline':BASELINE,'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                           'playwright_version':importlib.metadata.version('playwright')})
    photos=prior.cuisine_photos(prior.prior.fixture_logos(prior.prior.qa.source_photos()))
    with baseline_checkout(args.baseline) as baseline:
        servers={'baseline':prior.prior.qa.serve(baseline),'candidate':prior.prior.qa.serve(ROOT)}
        try:
            with sync_playwright() as pw:
                browser=pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
                run.provenance['webkit_version']=browser.version
                for lang,width in [('ru',375),('en',390)]:
                    run.run(f'{lang}-{width}-original-defaults',lambda l=lang,w=width:test_defaults(run,browser,servers,photos,l,w))
                    run.run(f'{lang}-{width}-managed-continuation',lambda l=lang,w=width:test_managed(run,browser,servers['candidate'],photos,l,w))
                run.run('three-independent-default-destinations',lambda:test_default_destinations(run,browser,servers['candidate'],photos))
                browser.close()
        finally:
            for server in servers.values():server.shutdown()
    result=run.save();result.update({'brief':'BRIEF-32','scope':'AI03 / original HTML / synthetic SDK / offline WebKit',
        'case_selection':args.case,'pixel_comparisons':run.pixel_comparisons})
    (args.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if not result['pass']:raise SystemExit('BRIEF32_RESTAURANTS_FAIL: see results.json')
    print(f'BRIEF32_RESTAURANTS_PASS {len(run.assertions)} assertions; {len(run.screenshots)} screenshots',flush=True)


if __name__=='__main__':
    main()
