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
    page.evaluate("""()=>Promise.all([...document.querySelectorAll('.ad30-banner img,.ad30-cuisine img')].map(i=>{
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


def cuisine_labels(page):
    return page.locator('.ad30-cuisine-label').all_text_contents()


def test_declared_types(run,browser,server,photos,lang,width):
    with run.page(browser,server,photos,lang,width,extra=DEFAULT_EXTRA) as page:
        enter(page)
        run.equal('AI06','only the existing restaurant type is shown',cuisine_labels(page),['Local & European'])
        run.equal('AI06','type uses its restaurant cover, not a menu image or default art',
                  page.locator('.ad30-cuisine img').get_attribute('src'),'/qa-image/romant')
        dimensions=page.locator('.ad30-cuisine-label').evaluate("""e=>({
          height:e.getBoundingClientRect().height,line:parseFloat(getComputedStyle(e).lineHeight),
          width:e.clientWidth,contentWidth:e.scrollWidth,contentHeight:e.scrollHeight
        })""")
        run.check('AI06','the complete Local & European type is readable in the existing chip',
                  dimensions['height']>=dimensions['line']*2 and dimensions['contentWidth']<=dimensions['width']
                  and dimensions['contentHeight']<=dimensions['height']+1,dimensions)
        run.capture(page,f'{lang}-{width}-restaurant-cuisine-types.webp')
        page.get_by_role('button',name='Local & European',exact=True).click()
        run.equal('AI06','type selection filters by the declared restaurant membership',
                  page.locator('.ad30-card-name').all_text_contents(),['Romant Restaurant'])
        run.equal('AI06','type selection has a visible pressed chip',page.locator('.ad30-cuisine[aria-pressed="true"]').count(),1)
        run.capture(page,f'{lang}-{width}-restaurant-cuisine-filter.webp')
        page.get_by_role('button',name='Local & European',exact=True).click()
        run.equal('AI06','type deselection restores unclassified restaurants too',
                  page.locator('.ad30-card-name').all_text_contents(),['KFC','Romant Restaurant'])
        prior.no_overflow(run,page,'AI06')


def test_type_without_data(run,browser,server,photos,kind):
    extra=DEFAULT_EXTRA+('stores.forEach(s=>s.description="");' if kind=='no-types'
                         else 'stores[1].cover_url="";')
    with run.page(browser,server,photos,extra=extra) as page:
        enter(page)
        run.equal('AI06',kind+' hides the entire cuisine row despite menu sections and photos',
                  page.locator('.ad30-cuisines,.ad30-cuisine').count(),0)
        run.check('AI06',kind+' leaves no placeholder between the heading and filters',
                  page.locator('.ad30-list>h2').evaluate("e=>e.nextElementSibling?.classList.contains('ad30-filters')"))
        run.equal('AI06',kind+' keeps both real restaurant cards',page.locator('.ad30-card-name').all_text_contents(),
                  ['KFC','Romant Restaurant'])
        run.capture(page,f'ru-375-cuisines-{kind}.webp')


def test_cuisine_grouping(run,browser,server,photos):
    extra=DEFAULT_EXTRA+r"""
      stores[0].description=' Fast food ';
      stores[1].description='Local & European';
      items.forEach(i=>{i.section=i.store_id==='s1'?'Напитки':'Pizza';});
    """
    with run.page(browser,server,photos,extra=extra) as page:
        enter(page)
        run.equal('AI06','restaurant types remain independent of arbitrary menu sections',
                  cuisine_labels(page),['Fast food','Local & European'])
        page.get_by_role('button',name='Fast food',exact=True).click()
        run.equal('AI06','Fast food contains only the restaurant explicitly declaring that type',
                  page.locator('.ad30-card-name').all_text_contents(),['KFC'])
        page.evaluate("()=>{const stores=TLB.stores();stores[0].description=' Local  & European ';stores[0].cover_url='';stores[1].description='local & european';syncStores();render()}")
        run.equal('AI06','same restaurant type groups across case and whitespace',cuisine_labels(page),['Local & European'])
        run.equal('AI06','group can use a cover from another member',
                  page.locator('.ad30-cuisine img').get_attribute('src'),'/qa-image/romant')
        page.get_by_role('button',name='Local & European',exact=True).click()
        run.equal('AI06','grouped type contains both declared restaurants',
                  page.locator('.ad30-card-name').all_text_contents(),['KFC','Romant Restaurant'])
        page.evaluate("()=>{const stores=TLB.stores();stores[0].category='grocery';stores[0].description='Fast food';syncStores();render()}")
        run.equal('AI06','a non-restaurant cannot introduce a restaurant type',cuisine_labels(page),['local & european'])


def test_excluded_types(run,browser,server,photos):
    with run.page(browser,server,photos,extra=DEFAULT_EXTRA) as page:
        enter(page)
        for label in [' Drinks ','Напитки','Beverages','Соусы','Sauces','Добавки','Extras']:
            page.evaluate("label=>{const stores=TLB.stores();stores[0].description=label;stores[1].description='';syncStores();render()}",label)
            run.equal('AI06',label.strip()+' cannot appear as a restaurant cuisine type',cuisine_labels(page),[])
            run.equal('AI06',label.strip()+' leaves no empty cuisine rail',page.locator('.ad30-cuisines').count(),0)


def test_failed_cuisine_image(run,browser,server,photos):
    with run.page(browser,server,photos,extra=DEFAULT_EXTRA) as page:
        enter(page)
        run.equal('AI06','declared type with working image is initially usable',cuisine_labels(page),['Local & European'])
        page.get_by_role('button',name='Local & European',exact=True).click()
        run.equal('AI06','selected type has one matching restaurant before its image fails',page.locator('.ad30-card').count(),1)
        page.route('**/qa-image/ai06-broken',lambda route:route.fulfill(status=200,content_type='image/jpeg',body=b'not an image'))
        page.evaluate("()=>{TLB.stores()[1].cover_url='/qa-image/ai06-broken';syncStores();render();document.querySelectorAll('.ad30-cuisine img').forEach(i=>i.loading='eager')}")
        page.wait_for_function("()=>!document.querySelector('.ad30-cuisine img[src=\"/qa-image/ai06-broken\"]')")
        run.equal('AI06','decoder failure removes the whole type and empty rail',page.locator('.ad30-cuisines,.ad30-cuisine').count(),0)
        run.equal('AI06','failed selected type cannot leave an invisible restriction',
                  page.locator('.ad30-card-name').all_text_contents(),['KFC','Romant Restaurant'])
        page.evaluate('render()')
        run.equal('AI06','known broken image stays hidden on later render',page.locator('.ad30-cuisine').count(),0)
        page.evaluate("()=>{TLB.stores()[1].cover_url='/qa-image/romant?updated=1';syncStores();render()}")
        page.locator('.ad30-cuisine img').evaluate("i=>{i.loading='eager';return i.decode()}")
        run.equal('AI06','a corrected real image makes the declared type available again',cuisine_labels(page),['Local & European'])
        run.equal('AI06','image recovery does not silently reapply an old selection',page.locator('.ad30-cuisine[aria-pressed="true"]').count(),0)


def run_ai03(run,browser,servers,photos):
    """Run AI03 with the master's Acceptance and baseline/candidate servers."""
    if not hasattr(run,'pixel_comparisons'):run.pixel_comparisons=[]
    for lang,width in [('ru',375),('en',390)]:
        run.run(f'{lang}-{width}-original-defaults',lambda l=lang,w=width:test_defaults(run,browser,servers,photos,l,w))
        run.run(f'{lang}-{width}-managed-continuation',lambda l=lang,w=width:test_managed(run,browser,servers['candidate'],photos,l,w))
    run.run('three-independent-default-destinations',lambda:test_default_destinations(run,browser,servers['candidate'],photos))


def run_ai06(run,browser,server,photos):
    """Run AI06 with the master's Acceptance and unmodified candidate server."""
    for lang,width in [('ru',375),('en',390)]:
        run.run(f'{lang}-{width}-declared-cuisine-types',lambda l=lang,w=width:test_declared_types(run,browser,server,photos,l,w))
    for kind in ('no-types','no-type-images'):
        run.run(kind,lambda k=kind:test_type_without_data(run,browser,server,photos,k))
    for name,check in [('type-grouping',test_cuisine_grouping),('excluded-types',test_excluded_types),('failed-type-image',test_failed_cuisine_image)]:
        run.run(name,lambda c=check:c(run,browser,server,photos))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--case',choices=['ai03','ai06','all'],default='all')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for key in ('SUPABASE_URL','SUPABASE_ACCESS_TOKEN','DATABASE_URL','SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(key),'Cloud context forbidden: '+key
    prior.EXPECTED_IDS={'AI03','AI06'} if args.case=='all' else {args.case.upper()}
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
                if args.case in ('ai03','all'):
                    run_ai03(run,browser,servers,photos)
                if args.case in ('ai06','all'):
                    run_ai06(run,browser,servers['candidate'],photos)
                browser.close()
        finally:
            for server in servers.values():server.shutdown()
    result=run.save();result.update({'brief':'BRIEF-32','scope':args.case.upper()+' / original HTML / synthetic SDK / offline WebKit',
        'case_selection':args.case,'pixel_comparisons':run.pixel_comparisons})
    (args.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if not result['pass']:raise SystemExit('BRIEF32_RESTAURANTS_FAIL: see results.json')
    print(f'BRIEF32_RESTAURANTS_PASS {len(run.assertions)} assertions; {len(run.screenshots)} screenshots',flush=True)


if __name__=='__main__':
    main()
