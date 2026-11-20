#!/usr/bin/env python3
"""BRIEF-31 focused, offline WebKit acceptance against ORIGINAL application HTML.

The SDK fixture supplies synthetic rows only. Product HTML, CSS, and JavaScript
are served unchanged from the checkout. Foreign network requests are intercepted
before navigation, and any unexpected one fails the run. This is viewport/browser
acceptance, not physical iPhone or production/backend acceptance.

Coverage: AF-01 unified banner configuration/actions; AF-02 per-banner expiry;
AF-03 advertising meals; AF-04 option clipping; AF-05 order carousel; AF-06 empty
DineOut; AG-01 compact popular rail; AG-02 supplied localized art; AG-03 restaurant
advertising; AG-04 sort icon; AG-05 draggable dish options; AG-06 preserved group.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright

import brief25b_webkit as prior
from brief30_webkit import cuisine_photos

ROOT = Path.cwd()
NOW = datetime(2026, 11, 18, 9, tzinfo=timezone.utc)
EXPECTED_IDS = {f'{prefix}-{n:02}' for prefix in ('AF', 'AG') for n in range(1, 7)}
OWNER_IMAGES = {
    'ru': '63bca41639ccefcbde4bf8c9d8049303d5e9fdd9',
    'en': 'c70b04c0ca131f0456eaddcb3299d67593ce70d3',
}
PRODUCT_PATHS = [
    'customer.html','admin.html','talabat-core.js',
    'assets/shared/banner-system-brief31.js',
    'assets/customer-c/banners-brief31.css','assets/customer-c/home-brief31.css',
    'assets/customer-c/dish-group-brief31.css','assets/customer-c/dish-group-brief31.js',
    'assets/customer-c/restaurants-brief30.js','assets/customer-c/restaurants-brief30.css',
    'assets/customer-c/dineout-header-ru.webp','assets/customer-c/dineout-header-en.webp',
]


def source_hashes():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in PRODUCT_PATHS if (ROOT/name).is_file()}


BASE_EXTRA = r"""
  for(const item of items){
    item.section=({combo:'Бургеры',hot:'Бургеры',steak:'Стейки',plov:'Плов'})[item.id]||item.section||'';
    if(item.id==='steak'||item.id==='plov')item.image_url='/qa-image/brief30-'+item.id;
  }
  stores[1].home_sponsored_dishes=[{item_id:'steak',rank:0}];
  for(const [id,name,section] of [
    ['tea','Зелёный чай','Напитки'],['juice','Fresh juice','Beverages'],
    ['sauce','Соус','Соусы'],['extra','Extra cheese','Extras']
  ])items.push({...items[1],id,name,section,price:5,discount_pct:0,popular:false});
  T.banners=[];
  window.__B31T=T;
  window.__B31GRP=GRP;
"""


BANNER_EXTRA = r"""
  stores[0].fee_type='free';
  const allPlaces=['home_main','home_side','dont_miss','home_bottom','orders','restaurants','checkout'];
  const put=(id,placements,action='',other={})=>T.banners.push({
    id,title:id,link_type:'store',link_value:'s1',placement:'top',is_active:true,
    image_url:'/qa-image/kfc',sort:20,presentation:{placements,action,label:{ru:'',en:'',tg:''},...other}
  });
  put('b31-multiple',allPlaces,'restaurant',{label:{ru:'Открыть',en:'Open',tg:'Кушодан'},
    images:{ru:'/qa-image/kfc',en:'/qa-image/romant',tg:'/qa-image/pro-khinkali'}});
  T.banners[0].sort=1;
  put('b31-plain',['home_main'],'restaurant');T.banners.at(-1).sort=2;
  put('b31-dish',['home_main'],'order',{item_id:'hot',label:{ru:'Купить сейчас',en:'Buy now'}});T.banners.at(-1).sort=3;
  put('b31-restaurant',['home_main'],'restaurant',{label:{ru:'Открыть ресторан',en:'Open restaurant'}});
  T.banners.at(-1).sort=4;T.banners.at(-1).link_value='s2';
  put('b31-free',['home_side','restaurants'],'list',{filter:'free',label:{ru:'Смотреть',en:'View'}});
  put('b31-campaign',['home_main','restaurants'],'campaign',{campaign:'discount',label:{ru:'Смотреть акцию',en:'View offer'}});
  T.banners.at(-1).link_value='s2';T.banners.at(-1).ends_at=new Date(now+2*86400000+5*3600000+10*60000+30000).toISOString();
  put('b31-orders-second',['orders'],'restaurant',{label:{ru:'Второй баннер',en:'Second banner'}});T.banners.at(-1).link_value='s2';
  put('b31-expired',['home_main','orders','restaurants'],'restaurant');T.banners.at(-1).ends_at=new Date(now-1000).toISOString();
  put('b31-future',['home_main','orders'],'restaurant');T.banners.at(-1).starts_at=new Date(now+3600000).toISOString();
  put('b31-inactive',['home_main'],'restaurant');T.banners.at(-1).is_active=false;
  put('b31-empty-places',[],'restaurant');
  put('b31-unsafe',['home_bottom'],'link',{url:'javascript:window.__b31Unsafe=true'});
"""


def sdk(extra='', *, role='customer', fixture='catalog'):
    seed = (('const catalog=' + json.dumps(prior.CATALOG, ensure_ascii=False) + ';\n'
            + prior.SEED + BASE_EXTRA) if fixture == 'catalog' else
            prior.qa.SEED + '\nwindow.__B31T=T;window.__B31GRP=GRP;\n') + extra + '\n'
    return prior.FIX.replace(prior.qa.FINISH_SEED, seed + prior.qa.FINISH_SEED).replace('window.__ROLE', json.dumps(role))


class Acceptance:
    def __init__(self, output):
        self.output = output
        self.assertions = []
        self.screenshots = []
        self.failures = []
        self.contexts = []
        self.case = ''
        self.provenance = {
            'started_at':datetime.now(timezone.utc).isoformat(),
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'git_tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],text=True).strip(),
            'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'product_sha256':source_hashes(),
            'fixture_time':NOW.isoformat(),
        }

    def check(self, item, name, passed, details=None):
        entry = {'item': item, 'case': self.case, 'name': name, 'pass': bool(passed)}
        if details is not None:
            entry['details'] = details
        self.assertions.append(entry)
        assert passed, json.dumps(entry, ensure_ascii=False)

    def equal(self, item, name, actual, expected):
        self.check(item, name, actual == expected, {'actual': actual, 'expected': expected})

    def capture(self, page, name):
        settle(page)
        page.evaluate("""()=>Promise.all([...document.images].filter(i=>{
          const r=i.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight;
        }).map(i=>{i.loading='eager';return i.decode().catch(()=>null)}))""")
        raw = page.screenshot(full_page=False, animations='disabled')
        image = Image.open(io.BytesIO(raw)).convert('RGB')
        viewport = page.viewport_size
        assert image.size == (viewport['width'], viewport['height']), (name, image.size)
        path = self.output / name
        image.save(path, quality=88, method=6)
        self.screenshots.append({'file': name, 'width': image.width, 'height': image.height,
                                 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

    @contextmanager
    def page(self, browser, server, photos, lang='ru', width=375, extra='', role='customer', fixture='catalog'):
        trace = {'case': self.case, 'role': role, 'language': lang, 'width': width,
                 'blocked': [], 'page_errors': [], 'failed_local_requests': [], 'http_errors': []}
        context = browser.new_context(viewport={'width': width, 'height': 844 if width >= 390 else 812},
                                      is_mobile=True, has_touch=True, device_scale_factor=1,
                                      service_workers='block')
        context.set_default_timeout(8000)
        context.add_init_script('localStorage.setItem("tlb_lang",' + json.dumps(lang) + ');')
        fixture_source = sdk(extra, role=role, fixture=fixture)

        def route(request):
            url = urlsplit(request.request.url)
            if url.hostname == 'cdn.jsdelivr.net' and 'supabase-js' in url.path:
                request.fulfill(content_type='application/javascript', body=fixture_source)
            elif url.hostname == '127.0.0.1' and url.port == server.server_port and request.request.method == 'GET':
                if url.path.startswith('/qa-image/'):
                    key = url.path.rsplit('/', 1)[1]
                    request.fulfill(status=200 if key in photos else 404, content_type='image/jpeg', body=photos.get(key, b''))
                else:
                    request.continue_()
            else:
                trace['blocked'].append({'method': request.request.method, 'url': request.request.url})
                request.abort('blockedbyclient')

        context.route('**/*', route)
        page = context.new_page()
        page.on('pageerror', lambda error: trace['page_errors'].append(str(error)))
        page.on('requestfailed', lambda request: trace['failed_local_requests'].append(
            {'url': request.url, 'failure': request.failure}) if request.url.startswith(f'http://127.0.0.1:{server.server_port}/') else None)
        page.on('response', lambda response: trace['http_errors'].append(
            {'url': response.url, 'status': response.status}) if response.status >= 400 else None)
        page.clock.install(time=NOW)
        page.goto(f'http://127.0.0.1:{server.server_port}/{role}.html', wait_until='domcontentloaded')
        page.wait_for_function("typeof TLB!=='undefined'&&TLB.orders().length>0&&document.querySelector('#app')?.innerText.trim().length>30")
        if role == 'customer':
            page.evaluate('()=>{TLB.speed=()=>({min:20});render()}')
        try:
            yield page
            page.wait_for_load_state('networkidle')
            self.check('NETWORK', 'no unexpected external requests', not trace['blocked'], trace['blocked'])
            self.check('NETWORK', 'no JavaScript runtime errors', not trace['page_errors'], trace['page_errors'])
            self.check('NETWORK', 'no failed local transport', not trace['failed_local_requests'], trace['failed_local_requests'])
            self.check('NETWORK', 'no HTTP error responses', not trace['http_errors'], trace['http_errors'])
        finally:
            self.contexts.append(trace)
            context.close()

    def run(self, name, callback):
        self.case = name
        try:
            callback()
            print('BRIEF31_CASE_PASS ' + name, flush=True)
        except Exception as error:
            self.failures.append({'case': name, 'error': str(error), 'traceback': traceback.format_exc()})
            print('BRIEF31_CASE_FAIL ' + name + ': ' + str(error)[:700], flush=True)

    def save(self):
        self.provenance['completed_at']=datetime.now(timezone.utc).isoformat()
        self.provenance['source_unchanged_during_run']=source_hashes()==self.provenance['product_sha256']
        if not self.provenance['source_unchanged_during_run']:
            self.failures.append({'case':'source-provenance','error':'Product source changed during acceptance run'})
        covered = {a['item'] for a in self.assertions if a['pass']} & EXPECTED_IDS
        result = {'brief': 'BRIEF-31', 'scope': 'original HTML / synthetic SDK / offline WebKit',
                  'physical_phone_tested': False, 'production_tested': False,
                  'assertions': self.assertions, 'covered_items': sorted(covered),
                  'missing_items': sorted(EXPECTED_IDS - covered), 'failures': self.failures,
                  'contexts': self.contexts, 'screenshots': self.screenshots,
                  'provenance':self.provenance,
                  'pass': not self.failures and covered == EXPECTED_IDS}
        (self.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        return result


def settle(page):
    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')


def no_overflow(run, page, item):
    metrics = page.evaluate('({width:innerWidth,document:document.documentElement.scrollWidth})')
    run.check(item, 'page fits horizontal viewport', metrics['document'] <= metrics['width'] + 1, metrics)


def reveal_section(page, locator):
    # Native scrollIntoView can put the heading below the sticky Home search.
    locator.evaluate('e=>window.scrollTo(0,scrollY+e.getBoundingClientRect().top-80)')
    settle(page)


def test_home(run, browser, server, photos, lang, width):
    with run.page(browser, server, photos, lang, width) as page:
        meals = page.locator('section.home-meals')
        run.equal('AF-03', 'taste heading', ' '.join(meals.locator('[data-section="meals"] h2').inner_text().split()),
                  'на твой вкус' if lang == 'ru' else 'for your taste')
        names = meals.locator('.d6-pt .nm').all_inner_texts()
        run.equal('AF-03', 'administration pins lead by rank', names[:2], ['Стейк', 'Hot honey'])
        run.check('AF-03', 'automatic food remains after pins', 'Плов' in names, names)
        run.check('AF-03', 'drinks sauces and extras excluded', not set(names) & {'Зелёный чай', 'Fresh juice', 'Соус', 'Extra cheese'}, names)
        run.equal('AF-03', 'both pins visibly labelled as advertising', meals.locator('.home-ad-label').all_inner_texts(),
                  ['Реклама', 'Реклама'] if lang == 'ru' else ['Ad', 'Ad'])
        reveal_section(page, meals)
        run.capture(page, f'{lang}-{width}-taste-advertising.webp')

        popular = page.locator('[data-section="popular"]')
        run.check('AG-01', 'popular heading has no slash decoration', '///' not in popular.inner_text(), popular.inner_text())
        reveal_section(page, popular)
        metrics = page.locator('[data-section="popular"] + .d6-rl').evaluate('''rail=>{
          const r=rail.getBoundingClientRect(),cards=[...rail.children].map(e=>e.getBoundingClientRect());
          return {rail:[r.left,r.right],cards:cards.map(c=>[c.left,c.right,c.width]),
            thirdVisible:cards.length>2?Math.max(0,Math.min(r.right,cards[2].right)-Math.max(r.left,cards[2].left))/cards[2].width:0};
        }''')
        run.check('AG-01', 'approximately two and a half cards visible', 0.35 <= metrics['thirdVisible'] <= 0.65, metrics)
        run.capture(page, f'{lang}-{width}-popular-rail.webp')

        heading = page.locator('.dine-head')
        art = heading.locator('img').first
        run.equal('AG-02', 'locale selects supplied image', art.get_attribute('src'), f'assets/customer-c/dineout-header-{lang}.webp')
        run.equal('AG-02', 'localized descriptive alt', art.get_attribute('alt'),
                  'В ресторане — Скидка до 50% на счёт' if lang == 'ru' else 'DineOut — Up to 50% off your bill')
        reveal_section(page, heading)
        run.capture(page, f'{lang}-{width}-dineout.webp')
        no_overflow(run, page, 'AG-01')


def test_empty_dineout(run, browser, server, photos, lang, width):
    with run.page(browser, server, photos, lang, width, extra='stores.forEach(s=>s.discount_pct=0);items.forEach(i=>i.discount_pct=0);') as page:
        run.equal('AF-06', 'empty DineOut title and rail absent', page.locator('.dine-head,.home-dine,.home-dine-section').count(), 0)
        page.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)')
        run.capture(page, f'{lang}-{width}-empty-dineout-hidden.webp')


def test_tg_dineout(run, browser, server, photos):
    with run.page(browser, server, photos, 'tg', 390) as page:
        art = page.locator('.dine-head img').first
        run.equal('AG-02', 'Tajik temporarily uses supplied RU art', art.get_attribute('src'), 'assets/customer-c/dineout-header-ru.webp')
        run.check('AG-02', 'Tajik alternative text is localized', bool(art.get_attribute('alt')) and art.get_attribute('alt') not in
                  ('В ресторане — Скидка до 50% на счёт', 'DineOut — Up to 50% off your bill'), art.get_attribute('alt'))


def test_source_assets(run):
    for lang, expected in OWNER_IMAGES.items():
        data = (ROOT / 'assets/customer-c' / f'dineout-header-{lang}.webp').read_bytes()
        actual = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
        run.equal('AG-02', f'{lang} art byte-identical to owner source', actual, expected)


def banner(page, ident, place='home_main'):
    return page.locator(f'[data-banner-place="{place}"][data-banner-id="{ident}"]')


def show_banner(page, ident, place='home_main'):
    target = banner(page, ident, place)
    target.evaluate('''e=>{const rail=e.closest('[data-banner-rail]');
      rail.scrollTo({left:e.offsetLeft-rail.firstElementChild.offsetLeft,top:0,behavior:'instant'})}''')
    settle(page)
    return target


def test_banners(run, browser, server, photos, lang, width):
    with run.page(browser, server, photos, lang, width, extra=BANNER_EXTRA) as page:
        page.emulate_media(reduced_motion='reduce')
        run.equal('AF-01', 'banner order follows administration sort',
                  page.locator('[data-banner-rail="home_main"] [data-banner-id]').evaluate_all('es=>es.map(e=>e.dataset.bannerId)'),
                  ['b31-multiple','b31-plain','b31-dish','b31-restaurant','b31-campaign'])
        run.equal('AF-01', 'current locale chooses banner image', banner(page,'b31-multiple').locator('img').first.get_attribute('src'),
                  '/qa-image/kfc' if lang=='ru' else '/qa-image/romant')
        run.equal('AF-01', 'blank CTA leaves no overlaid button', banner(page,'b31-plain').locator('.banner31-cta').count(),0)
        for placement in ('home_main','home_side','dont_miss','home_bottom'):
            run.equal('AF-01', 'one campaign can occupy '+placement, banner(page,'b31-multiple',placement).count(),1)
        run.equal('AF-01', 'unselected placement does not fall back', page.locator('[data-banner-id="b31-empty-places"]').count(),0)
        run.capture(page,f'{lang}-{width}-managed-home-banners.webp')

        show_banner(page,'b31-plain').click()
        run.check('AF-01','whole image remains clickable without CTA',page.evaluate("S.v==='menu'&&S.store==='KFC'&&!S.sh"))
        page.evaluate("go('home')")
        dish=show_banner(page,'b31-dish')
        run.equal('AF-01','dish slide owns its CTA',dish.locator('.banner31-cta').inner_text().strip(), 'Купить сейчас' if lang=='ru' else 'Buy now')
        dish.click()
        run.check('AF-01','order action opens assigned dish',page.evaluate("S.v==='menu'&&S.store==='KFC'&&S.sh?.id==='hot'"))
        page.evaluate("()=>{S.sh=null;go('home')}")
        restaurant=show_banner(page,'b31-restaurant')
        run.equal('AF-01','next slide owns different CTA',restaurant.locator('.banner31-cta').inner_text().strip(),
                  'Открыть ресторан' if lang=='ru' else 'Open restaurant')
        restaurant.click()
        run.check('AF-01','next slide owns different destination',page.evaluate("S.v==='menu'&&S.store==='Romant Restaurant'&&!S.sh"))
        page.evaluate("go('home')")

        run.equal('AF-02','untimed free-delivery banner has no countdown',banner(page,'b31-free','home_side').locator('.hcd').count(),0)
        run.equal('AF-02','expired and future and inactive banners hidden',
                  page.locator('[data-banner-id="b31-expired"],[data-banner-id="b31-future"],[data-banner-id="b31-inactive"]').count(),0)
        campaign=show_banner(page,'b31-campaign')
        text=campaign.locator('.hcd').inner_text()
        run.equal('AF-02','countdown over a day uses days and hours',text,'2 д 05:10' if lang=='ru' else '2 d 05:10')
        campaign.click()
        sheet=page.locator('#happy-hour-sheet[open]')
        sheet.wait_for()
        run.check('AF-01','campaign action opens existing Z07 sheet',sheet.locator('.hh-sheet-store').count()>0)
        run.capture(page,f'{lang}-{width}-managed-campaign-sheet.webp')
        sheet.locator('.hh-sheet-close').click()
        banner(page,'b31-free','home_side').click()
        run.check('AF-01','list action applies assigned filter',page.evaluate("S.v==='cat'&&S.catKey==='rest'&&S.srt==='free'"))
        page.evaluate("go('home')")
        banner(page,'b31-unsafe','home_bottom').click()
        run.check('AF-01','unsafe link is never executed',page.evaluate("!window.__b31Unsafe&&S.v==='home'"))
        run.equal('AF-01','links with embedded credentials rejected',page.evaluate("TALABOT_BANNERS.safeLink('https://name:secret@example.com/')"),'')

        # Expiry must remove the actual visible card without a user navigation.
        page.evaluate("()=>{const b=TLB.banners(true).find(x=>x.id==='b31-multiple');b.ends_at=new Date(Date.now()+1300).toISOString();render()}")
        run.equal('AF-02','near-expiry banner starts visible',banner(page,'b31-multiple').count(),1)
        page.clock.fast_forward(2400)
        page.wait_for_function("()=>!document.querySelector('[data-banner-id=\"b31-multiple\"]')")
        run.equal('AF-02','expiry removes every placement of the banner',page.locator('[data-banner-id="b31-multiple"]').count(),0)
        no_overflow(run,page,'AF-01')

    side_only=BANNER_EXTRA+"T.banners=T.banners.filter(b=>b.id==='b31-free');T.banners[0].presentation.placements=['home_side'];"
    with run.page(browser,server,photos,lang,width,extra=side_only) as page:
        run.equal('AF-01','side-only placement stays in its own rail',page.locator('[data-banner-rail="home_side"] [data-banner-id="b31-free"]').count(),1)
        run.equal('AF-01','side-only banner is not promoted into main placement',page.locator('[data-banner-place="home_main"]').count(),0)


def test_admin(run, browser, server, photos, lang, width):
    with run.page(browser,server,photos,lang,width,extra=BANNER_EXTRA,role='admin') as page:
        page.evaluate("()=>{tab='b';openBE('b31-multiple')}")
        fields=page.locator('[name="banner-place"]')
        run.equal('AF-01','admin offers all seven banner locations',fields.evaluate_all('es=>es.map(e=>e.value)'),
                  ['home_main','home_side','dont_miss','home_bottom','orders','restaurants','checkout'])
        run.equal('AF-01','multiple existing locations load selected',page.locator('[name="banner-place"]:checked').count(),7)
        run.equal('AF-01','admin has one image control for each locale',page.locator('.banner31-images input[type=file]').count(),3)
        run.equal('AF-01','free text CTA also offers preset labels',page.locator('#banner-label-options-ru option').evaluate_all('es=>es.map(e=>e.value)'),
                  ['Купить сейчас','Смотреть','Открыть'])
        page.locator('#banner-label-ru').fill('Смотреть выбор')
        page.locator('#banner-label-en').fill('View selection')
        page.locator('#banner-label-tg').fill('')
        page.evaluate("()=>{window.__originalServerLabel=TLB.banners(true).find(x=>x.id==='b31-multiple').presentation.label.ru;TLB.banners(true).find(x=>x.id==='b31-multiple').presentation.label.ru='Concurrent server edit';render()}")
        run.check('AF-01','concurrent presentation change displays existing conflict warning',page.locator('.confn').count()==1)
        run.equal('AF-01','concurrent change preserves typed editor draft',page.locator('#banner-label-ru').input_value(),'Смотреть выбор')
        page.evaluate("()=>{TLB.banners(true).find(x=>x.id==='b31-multiple').presentation.label.ru=__originalServerLabel;render()}")
        for choice in fields.all():
            choice.set_checked(choice.get_attribute('value') in ('orders','restaurants'))
        page.locator('#banner-action').select_option('list')
        page.locator('#banner-filter').select_option('disc')
        page.evaluate("()=>{window.__upload=[];TLB.uploadImage=async(file,options)=>{__upload.push({name:file.name,type:file.type,size:file.size,options});return '/qa-image/pro-khinkali'}}")
        page.locator('input[type=file][aria-label$=" EN"]').set_input_files({'name':'banner-en-qa.jpg','mimeType':'image/jpeg','buffer':photos['romant']})
        page.wait_for_function("()=>BD.presentation.images.en==='/qa-image/pro-khinkali'")
        run.equal('AF-01','upload uses selected locale and preserves edited CTA',page.locator('#banner-label-en').input_value(),'View selection')
        run.equal('AF-01','upload preserves other locales',page.evaluate('BD.presentation.images.ru'),'/qa-image/kfc')
        run.equal('AF-01','upload called once for selected file',page.evaluate('__upload.length'),1)
        run.equal('AF-01','upload rerender preserves multi-selection',page.locator('[name="banner-place"]:checked').evaluate_all('es=>es.map(e=>e.value)'),['orders','restaurants'])
        reveal_section(page,page.locator('.banner31-editor'))
        run.capture(page,f'{lang}-{width}-admin-banner-placements-images.webp')
        page.locator('input[oninput="bd(\'sort\',this.value)"]').fill('7')
        page.locator('#banner-end-time').fill('2026-11-21T17:24:31')
        reveal_section(page,page.locator('#banner-action'))
        run.capture(page,f'{lang}-{width}-admin-banner-actions-expiry.webp')
        page.evaluate("()=>{window.__saved=[];TLB.updateBanner=async(id,payload)=>{__saved.push({id,payload});return {}}}")
        page.locator('button[onclick="bannerSave()"]').click()
        page.wait_for_function('()=>__saved.length===1')
        saved=page.evaluate('__saved[0]')
        run.equal('AF-01','save targets edited banner',saved['id'],'b31-multiple')
        payload=saved['payload']
        run.equal('AF-01','save carries exact selected locations',payload['presentation']['placements'],['orders','restaurants'])
        run.equal('AF-01','save carries own action/filter', [payload['presentation']['action'],payload['presentation']['filter']],['list','disc'])
        run.equal('AF-01','save keeps blank localized CTA blank',payload['presentation']['label']['tg'],'')
        run.equal('AF-01','save carries display order',payload['sort'],7)
        run.equal('AF-02','end time saves exact seconds in Dushanbe timezone',payload['ends_at'],'2026-11-21T17:24:31+05:00')
        run.equal('AF-02','end time round trip does not truncate to a day',page.evaluate("bannerEndShow('2026-11-21T12:24:31Z')"),'2026-11-21T17:24:31')
        run.equal('AF-02','empty expiry serializes as null',page.evaluate("bannerEndIso('')"),None)
        no_overflow(run,page,'AF-01')

        page.locator('#banner-timing summary').click()
        run.equal('AF-05','each placement has an interval control',page.locator('#banner-timing input[type=number]').count(),7)
        run.equal('AF-05','absent timing keys stay disabled',page.locator('#banner-timing input:disabled').count(),7)
        run.equal('AF-05','orders timing default is three seconds',page.locator('#rotation-orders').input_value(),'3')
        page.evaluate("""()=>{const settings=TLB.settings.bind(TLB);TLB.settings=()=>({...settings(),banner_rotation_orders_seconds:3});
          window.__timingWrites=[];TLB.setSetting=async(key,value)=>{__timingWrites.push({key,value});return {}};render();document.getElementById('banner-timing').open=true}""")
        page.locator('#rotation-orders').fill('5')
        page.locator('button[onclick="saveBannerRotation(\'orders\')"]').click()
        page.wait_for_function('()=>__timingWrites.length===1')
        run.equal('AF-05','interval saves only the selected existing setting',page.evaluate('__timingWrites'),
                  [{'key':'banner_rotation_orders_seconds','value':5}])
        run.check('AF-05','other missing interval keys remain disabled',page.locator('#rotation-home_main').is_disabled())
        page.locator('#rotation-orders').fill('0')
        page.once('dialog',lambda dialog:dialog.dismiss())
        page.locator('button[onclick="saveBannerRotation(\'orders\')"]').click()
        run.equal('AF-05','invalid zero interval sends no request',page.evaluate('__timingWrites.length'),1)
        page.locator('#rotation-orders').fill('5')
        reveal_section(page,page.locator('#banner-timing'))
        run.capture(page,f'{lang}-{width}-admin-placement-timing.webp')
        page.locator('#banner-timing summary').click()

        # The taste editor shares the already proposed W09 field and must keep
        # a draft when a save fails. No database or real merchant row is used.
        page.locator('#taste-admin summary').click()
        page.locator('#taste-store').select_option('s1')
        page.locator('#taste-dish').select_option('combo')
        page.locator('#taste-rank').fill('3')
        page.locator('[onclick="tasteAdd()"]').click()
        run.equal('AF-03','taste pin editor retains existing pin and appends selected dish',page.evaluate('tastePins()'),
                  [{'item_id':'hot','rank':1},{'item_id':'combo','rank':3}])
        page.locator('[onclick="tasteAdd()"]').click()
        run.equal('AF-03','adding the same dish twice creates no duplicate',page.evaluate('tastePins().length'),2)
        reveal_section(page,page.locator('#taste-admin'))
        run.capture(page,f'{lang}-{width}-admin-taste-pins.webp')
        page.evaluate("()=>{window.__pinWrites=[];TLB.updateStore=async(id,payload)=>{__pinWrites.push({id,payload});return {error:'generic'}}}")
        page.once('dialog',lambda dialog:dialog.dismiss())
        page.locator('#taste-save').click()
        page.wait_for_function('()=>!tasteBusy&&__pinWrites.length===1')
        run.equal('AF-03','failed pin save preserves draft',page.evaluate('tastePins()'),
                  [{'item_id':'hot','rank':1},{'item_id':'combo','rank':3}])
        page.evaluate("()=>{TLB.updateStore=async(id,payload)=>{__pinWrites.push({id,payload});return {}}}")
        page.locator('#taste-admin summary').click() if not page.locator('#taste-save').is_visible() else None
        page.locator('#taste-save').click()
        page.wait_for_function('()=>!tasteBusy&&__pinWrites.length===2')
        pin_write=page.evaluate('__pinWrites[1]')
        run.equal('AF-03','pin save writes only authorized existing optional field',pin_write,
                  {'id':'s1','payload':{'home_sponsored_dishes':[{'item_id':'hot','rank':1},{'item_id':'combo','rank':3}]}})
        page.locator('#taste-admin summary').click() if not page.locator('#taste-store').is_visible() else None
        page.locator('#taste-store').select_option('s4')
        run.check('AF-03','store without pin column remains read only',page.locator('#taste-save').is_disabled())

        page.evaluate("()=>{showAddB=true;bannerCreatePresentation={};window.__creates=[];TLB.addBanner=async payload=>{__creates.push(payload);return {}};render()}")
        page.locator('#bt').fill('Campaign default QA')
        page.locator('#banner-action').select_option('campaign')
        run.equal('AF-01','campaign select exposes its actual default',page.locator('#banner-campaign').input_value(),'happy')
        page.locator('button[onclick="addBanner()"]').click()
        page.wait_for_function('()=>__creates.length===1')
        run.equal('AF-01','untouched secondary campaign select is serialized',page.evaluate('__creates[0].presentation.campaign'),'happy')

    # Optional backend columns do not exist in the original deployed contract.
    # Pending editor fields must be disabled and omitted, never silently written.
    legacy="T.banners=[{id:'legacy',title:'Legacy QA',link_type:'store',link_value:'s1',placement:'top',is_active:true,image_url:'/qa-image/kfc'}];"
    with run.page(browser,server,photos,lang,width,extra=legacy,role='admin') as page:
        page.evaluate("()=>{tab='b';openBE('legacy')}")
        run.check('AF-01','missing schema makes advanced controls read only',page.locator('[name="banner-place"]').first.is_disabled())
        run.equal('AF-01','missing schema omits optional save fields',page.evaluate('bannerPresentation()'),{})
        run.check('AF-01','missing schema is visible to admin',page.locator('.banner31-note[role=status]').is_visible())
        page.evaluate("()=>{window.__saved=[];TLB.updateBanner=async(id,payload)=>{__saved.push(payload);return {}}}")
        page.locator('button[onclick="bannerSave()"]').click()
        page.wait_for_function('()=>__saved.length===1')
        run.check('AF-01','legacy save contains no proposed presentation column',page.evaluate("!Object.hasOwn(__saved[0],'presentation')"))


def test_orders(run,browser,server,photos,lang,width):
    with run.page(browser,server,photos,lang,width,extra=BANNER_EXTRA) as page:
        page.evaluate("go('orders')")
        rail=page.locator('[data-banner-rail="orders"]')
        geometry=rail.evaluate('''r=>{const b=r.getBoundingClientRect(),s=getComputedStyle(r),left=parseFloat(s.paddingLeft),right=parseFloat(s.paddingRight);return {width:b.width,left:b.left,right:b.right,contentWidth:r.clientWidth-left-right,contentRight:b.right-right,
          cards:[...r.children].map(e=>{const x=e.getBoundingClientRect(),img=e.querySelector('img');return {width:x.width,height:x.height,left:x.left,right:x.right,fit:img?getComputedStyle(img).objectFit:null}})}}''')
        run.equal('AF-05','orders have exactly their own assigned banners',rail.locator('[data-banner-id]').evaluate_all('es=>es.map(e=>e.dataset.bannerId)'),['b31-multiple','b31-orders-second'])
        run.check('AF-05','one large banner fills available screen width',geometry['contentWidth']>=width-34 and all(abs(c['width']-geometry['contentWidth'])<=1 and c['height']>=160 for c in geometry['cards']),geometry)
        run.check('AF-05','printed banner copy is not cropped',all(c['fit']=='contain' for c in geometry['cards']),geometry)
        run.check('AF-05','only one whole slide is in view',geometry['cards'][1]['left']>=geometry['contentRight']-1,geometry)
        run.equal('AF-05','unconfigured orders rotation is three seconds',page.evaluate("bannerRotationMs('orders')"),3000)
        run.capture(page,f'{lang}-{width}-orders-large-banner.webp')
        initial=rail.evaluate('e=>e.scrollLeft')
        page.clock.fast_forward(3500)
        page.wait_for_function('()=>document.querySelector(\'[data-banner-rail="orders"]\').scrollLeft>20')
        page.wait_for_timeout(300)
        rotated=rail.evaluate('e=>e.scrollLeft')
        run.check('AF-05','default clock automatically advances orders banner',rotated>initial+20,{'initial':initial,'rotated':rotated})
        page.evaluate("()=>{const settings=TLB.settings.bind(TLB);TLB.settings=()=>({...settings(),banner_rotation_orders_seconds:5});render()}")
        settle(page)
        prior_offset=rail.evaluate('e=>e.scrollLeft')
        page.clock.fast_forward(3400)
        run.check('AF-05','configured five seconds does not advance after three',abs(rail.evaluate('e=>e.scrollLeft')-prior_offset)<=1)
        page.clock.fast_forward(2200)
        page.wait_for_timeout(350)
        run.check('AF-05','configured five seconds advances when due',abs(rail.evaluate('e=>e.scrollLeft')-prior_offset)>20)
        run.equal('AF-05','orders timing does not change another placement',page.evaluate("bannerRotationMs('home_main')"),3000)
        toggle=page.locator('[data-banner-toggle="orders"]')
        toggle.click()
        run.equal('AF-05','visible pause control reflects paused state',toggle.get_attribute('aria-pressed'),'true')
        held=rail.evaluate('e=>e.scrollLeft')
        page.clock.fast_forward(8000)
        run.check('AF-05','pause keeps the same slide',abs(rail.evaluate('e=>e.scrollLeft')-held)<=1)
        toggle.click()
        page.emulate_media(reduced_motion='reduce')
        held=rail.evaluate('e=>e.scrollLeft')
        page.clock.fast_forward(8000)
        run.check('AF-05','reduced motion disables automatic rotation',abs(rail.evaluate('e=>e.scrollLeft')-held)<=1)
        page.emulate_media(reduced_motion='no-preference')
        rail.evaluate("e=>e.addEventListener('pointerdown',event=>{window.__heldPointer={pointerId:event.pointerId,pointerType:event.pointerType}},{once:true})")
        box=rail.bounding_box()
        # Press the real rail padding so releasing cannot navigate a banner.
        page.mouse.move(box['x']+4,box['y']+box['height']/2)
        page.mouse.down()
        page.wait_for_function('()=>!!window.__heldPointer')
        held=rail.evaluate('e=>e.scrollLeft')
        page.clock.fast_forward(13000)
        page.wait_for_timeout(300)
        run.check('AF-05','long held pointer prevents rotation beyond normal cooldown',abs(rail.evaluate('e=>e.scrollLeft')-held)<=1)
        run.check('AF-05','native swipe scrolling is not disabled',rail.evaluate("e=>getComputedStyle(e).touchAction!=='none'"))
        pointer=page.evaluate('__heldPointer')
        rail.dispatch_event('pointercancel',{**pointer,'bubbles':True})
        page.mouse.up()
        page.clock.fast_forward(3000)
        run.check('AF-05','pointer cancellation starts a fresh release cooldown',abs(rail.evaluate('e=>e.scrollLeft')-held)<=1)
        page.clock.fast_forward(11000)
        page.wait_for_timeout(350)
        run.check('AF-05','rotation resumes after cancelled pointer is released',abs(rail.evaluate('e=>e.scrollLeft')-held)>20)
        run.equal('AF-05','gesture lifecycle never activates a banner',page.evaluate('S.v'),'orders')
        no_overflow(run,page,'AF-05')


def enter_restaurants(page):
    page.evaluate("go('cat',{catKey:'rest',cq:'',srt:'',fo:false})")
    page.locator('.ad30-head').wait_for()


def test_restaurants(run,browser,server,photos,lang,width):
    with run.page(browser,server,photos,lang,width,extra=BANNER_EXTRA) as page:
        enter_restaurants(page)
        row=page.locator('.ad30-banner-row')
        run.equal('AG-03','restaurant rail uses only assigned advertising',row.locator('[data-banner-id]').evaluate_all('es=>es.map(e=>e.dataset.bannerId)'),
                  ['b31-multiple','b31-free','b31-campaign'])
        left=row.locator('[data-banner-id]').first.bounding_box()['x']
        run.check('AG-03','first advertising card has 16px screen inset',abs(left-16)<=1,{'left':left})
        run.equal('AG-03','advertising cards do not expose pressed filter state',row.locator('[aria-pressed]').count(),0)
        run.capture(page,f'{lang}-{width}-restaurant-advertising.webp')
        banner(page,'b31-multiple','restaurants').click()
        run.check('AG-03','restaurant advertising opens assigned destination',page.evaluate("S.v==='menu'&&S.store==='KFC'"))
        enter_restaurants(page)
        sort=page.locator('.ad30-sort')
        shape=sort.evaluate('''e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {
          width:r.width,height:r.height,radius:s.borderRadius,text:e.innerText,label:e.getAttribute('aria-label'),icons:e.querySelectorAll('svg').length}}''')
        run.check('AG-04','sorting is an accessible round icon button',shape['width']>=44 and abs(shape['width']-shape['height'])<=1
                  and (shape['radius']=='50%' or float(shape['radius'].replace('px','').split()[0])>=shape['width']/2)
                  and bool(shape['label']) and shape['icons']==1 and not shape['text'].strip(),shape)
        run.equal('AG-04','default sort has no orange marker',sort.locator('.ad30-sort-dot').count(),0)
        run.equal('AG-04','recommended caption removed from filter row',page.locator('.ad30-current-sort').count(),0)
        sort.click()
        sheet=page.locator('.ad30-sort-sheet')
        sheet.wait_for()
        run.equal('AG-04','four actual sort options remain inside sheet',sheet.locator('.ad30-sort-choice').count(),4)
        run.check('AG-04','default choice remains named inside sheet',('Рекомендуемые' if lang=='ru' else 'Recommended') in sheet.inner_text())
        run.capture(page,f'{lang}-{width}-sort-sheet.webp')
        sheet.locator('.ad30-sort-choice').nth(1).click()
        run.equal('AG-04','nondefault choice adds orange dot',page.locator('.ad30-sort .ad30-sort-dot').count(),1)
        page.locator('.ad30-sort').click()
        page.locator('.ad30-sort-choice').first.click()
        run.equal('AG-04','returning to default removes orange dot',page.locator('.ad30-sort .ad30-sort-dot').count(),0)
        banner(page,'b31-campaign','restaurants').click()
        run.check('AG-03','campaign advertisement opens existing campaign dialog',page.locator('#happy-hour-sheet[open]').is_visible())
        page.locator('.hh-sheet-close').click()
        no_overflow(run,page,'AG-03')


def test_group(run,browser,server,photos,lang,width):
    with run.page(browser,server,photos,lang,width,fixture='original') as page:
        page.evaluate("""()=>{
          window.__groupWrites=[];window.__groupSnapshot=structuredClone(window.__GRP);
          TLB.groupSet=async(id,status)=>{__groupWrites.push({id,status});__groupSnapshot.status=status;return {group:structuredClone(__groupSnapshot)}};
          TLB.groupGet=async()=>({group:structuredClone(__groupSnapshot)});
          S.gid=__groupSnapshot.id;S.grp=structuredClone(__groupSnapshot);grpKeep();go('menu',{store:STORES[0].n});
        }""")
        ident=page.evaluate('S.gid')
        original_store=page.evaluate('S.store')
        page.evaluate("go('group')")
        page.locator('[onclick="grpBack()"]').click()
        run.equal('AG-06','group back restores menu and restaurant',page.evaluate('({view:S.v,store:S.store})'),{'view':'menu','store':original_store})
        run.equal('AG-06','group identity survives back navigation',page.evaluate('S.gid'),ident)
        run.equal('AG-06','back navigation makes no group mutation',page.evaluate('__groupWrites'),[])
        pill=page.locator('.b31-group-resume')
        run.check('AG-06','active group has persistent reentry control',pill.is_visible())
        hit=pill.evaluate('''e=>{const r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
          return {visible:r.top>=0&&r.bottom<=innerHeight,hit:e===hit||e.contains(hit),width:r.width}}''')
        run.check('AG-06','resume control is visible and receives taps',hit['visible'] and hit['hit'] and hit['width']<=width,hit)
        run.capture(page,f'{lang}-{width}-group-preserved-resume.webp')
        pill.click()
        run.check('AG-06','resume reopens the same group',page.evaluate("S.v==='group'&&S.gid==="+json.dumps(ident)))
        toggle=page.locator('#b31-group-toggle')
        run.equal('AG-06','only one close or reopen control exists',page.locator('[onclick="grpStatus(\'closed\')"],[onclick="grpStatus(\'open\')"],#b31-group-toggle').count(),1)
        before=toggle.bounding_box()
        run.check('AG-06','open group offers close collection',('Закрыть сбор' if lang=='ru' else 'Close collection') in toggle.inner_text(),toggle.inner_text())
        toggle.click()
        page.wait_for_function("()=>S.grp.status==='closed'")
        run.check('AG-06','same toggle becomes reopen',('Открыть снова' if lang=='ru' else 'Reopen') in toggle.inner_text(),toggle.inner_text())
        after=toggle.bounding_box()
        run.check('AG-06','close and reopen keep the same control position',abs(before['x']-after['x'])<=1 and abs(before['y']-after['y'])<=1,
                  {'before':before,'after':after})
        run.capture(page,f'{lang}-{width}-group-closed-toggle.webp')
        toggle.click()
        page.wait_for_function("()=>S.grp.status==='open'")
        run.equal('AG-06','toggle commits only close then reopen',page.evaluate('__groupWrites.map(x=>x.status)'),['closed','open'])
        page.locator('[onclick="grpBack()"]').click()
        run.equal('AG-06','repeated back still restores original menu',page.evaluate('S.v'),'menu')
        page.evaluate("go('cat',{catKey:'rest',cq:'KFC',srt:'free',fo:true})")
        page.locator('.b31-group-resume').click()
        page.locator('[onclick="grpBack()"]').click()
        run.equal('AG-06','back restores category query and restrictions',page.evaluate('({v:S.v,cat:S.catKey,q:S.cq,sort:S.srt,open:S.fo})'),
                  {'v':'cat','cat':'rest','q':'KFC','sort':'free','open':True})
        run.equal('AG-06','no navigation cancellation was sent',page.evaluate('__groupWrites.map(x=>x.status)'),['closed','open'])
        no_overflow(run,page,'AG-06')


def test_dish(run, browser, server, photos, lang, width):
    extra = "items[0].image_url='/qa-image/romant';opts[2].price_delta=30;groups[1].max_sel=1;"
    with run.page(browser, server, photos, lang, width, extra=extra, fixture='original') as page:
        page.evaluate("()=>{go('menu',{store:STORES[0].n});openItem('i1')}")
        page.locator('.sheet.d6s').wait_for()
        scroller = page.locator('.d6s .osh')
        metrics = scroller.evaluate('''e=>{
          const r=e.getBoundingClientRect();return {width:e.clientWidth,scroll:e.scrollWidth,left:r.left,right:r.right,
            prices:[...e.querySelectorAll('.d6-ch .pr')].map(x=>{const b=x.getBoundingClientRect();return [x.textContent,b.left,b.right]}),
            badges:[...e.querySelectorAll('.d6-pill')].map(x=>{const b=x.getBoundingClientRect();return [x.textContent,b.left,b.right]})};
        }''')
        run.check('AF-04', 'options have no horizontal scroll or displacement', metrics['scroll'] <= metrics['width'] + 1
                  and metrics['left'] >= -1 and metrics['right'] <= width + 1, metrics)
        for label, left, right in metrics['prices'] + metrics['badges']:
            run.check('AF-04', f'option price or choice badge fits: {label}', left >= 11 and right <= width - 11,
                      {'left': left, 'right': right, 'width': width})
        run.check('AF-04', 'fixture exercises additional 30 TJS option', any('30' in row[0] for row in metrics['prices']), metrics['prices'])
        handle = page.locator('[data-dish-handle]')
        run.equal('AG-05', 'handle is an accessible button', handle.get_attribute('type'), 'button')
        run.equal('AG-05', 'options begin at lower detent', handle.get_attribute('aria-expanded'), 'false')
        before = page.locator('.d6s-p').evaluate('''e=>{const p=document.querySelector('.d6s-top'),s=getComputedStyle(e);
          return {top:e.getBoundingClientRect().top,photo:p.getBoundingClientRect().height,radius:parseFloat(s.borderTopLeftRadius),shadow:s.boxShadow}}''')
        run.check('AG-05', 'options have rounded separation and shadow', before['radius'] >= 20 and before['shadow'] != 'none', before)
        run.capture(page, f'{lang}-{width}-dish-options-collapsed.webp')
        box = handle.bounding_box()
        page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
        page.mouse.down()
        page.mouse.move(box['x'] + box['width'] / 2, max(44, box['y'] - 170), steps=12)
        page.mouse.up()
        page.wait_for_function("()=>document.querySelector('[data-dish-handle]').getAttribute('aria-expanded')==='true'")
        page.wait_for_timeout(250)
        after = page.locator('.d6s-p').evaluate('''e=>({top:e.getBoundingClientRect().top,
          photo:document.querySelector('.d6s-top').getBoundingClientRect().height})''')
        run.check('AG-05', 'drag raises options over photo', after['top'] < before['top'] - 40, {'before': before, 'after': after})
        run.check('AG-05', 'photo shrinks on expansion', after['photo'] < before['photo'] - 20, {'before': before, 'after': after})
        run.capture(page, f'{lang}-{width}-dish-options-expanded.webp')
        handle.click()
        page.wait_for_function("()=>document.querySelector('[data-dish-handle]').getAttribute('aria-expanded')==='false'")
        page.wait_for_timeout(250)
        handle.focus()
        handle.press('Enter')
        page.wait_for_function("()=>document.querySelector('[data-dish-handle]').getAttribute('aria-expanded')==='true'")
        run.equal('AG-05', 'keyboard alternative expands options', handle.get_attribute('aria-expanded'), 'true')
        no_overflow(run, page, 'AF-04')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--case', choices=['home', 'empty', 'tg', 'assets', 'dish', 'banners', 'admin', 'restaurants', 'group', 'orders'])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ('SUPABASE_URL', 'SUPABASE_ACCESS_TOKEN', 'DATABASE_URL', 'SUPABASE_DB_PASSWORD'):
        assert not os.environ.get(name), f'Cloud context forbidden: {name}'
    run = Acceptance(args.output)
    server = prior.qa.serve(ROOT)
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            photos = cuisine_photos(prior.fixture_logos(prior.qa.source_photos()))
            if args.case in (None, 'assets'):
                run.run('owner-source-assets', lambda: test_source_assets(run))
            for lang, width in (('ru', 375), ('en', 390)):
                if args.case in (None, 'home'):
                    run.run(f'{lang}-{width}-home', lambda l=lang,w=width: test_home(run,browser,server,photos,l,w))
                if args.case in (None, 'empty'):
                    run.run(f'{lang}-{width}-empty', lambda l=lang,w=width: test_empty_dineout(run,browser,server,photos,l,w))
                if args.case in (None, 'dish'):
                    run.run(f'{lang}-{width}-dish', lambda l=lang,w=width: test_dish(run,browser,server,photos,l,w))
                if args.case in (None, 'banners'):
                    run.run(f'{lang}-{width}-banners', lambda l=lang,w=width: test_banners(run,browser,server,photos,l,w))
                if args.case in (None, 'admin'):
                    run.run(f'{lang}-{width}-admin', lambda l=lang,w=width: test_admin(run,browser,server,photos,l,w))
                if args.case in (None, 'restaurants'):
                    run.run(f'{lang}-{width}-restaurants', lambda l=lang,w=width: test_restaurants(run,browser,server,photos,l,w))
                if args.case in (None, 'group'):
                    run.run(f'{lang}-{width}-group', lambda l=lang,w=width: test_group(run,browser,server,photos,l,w))
                if args.case in (None, 'orders'):
                    run.run(f'{lang}-{width}-orders', lambda l=lang,w=width: test_orders(run,browser,server,photos,l,w))
            if args.case in (None, 'tg'):
                run.run('tg-390-art', lambda: test_tg_dineout(run,browser,server,photos))
            browser.close()
    finally:
        server.shutdown()
    result = run.save()
    # A focused development invocation reports only its executed cases. The CI
    # invocation has no --case flag and fails closed unless all 12 IDs passed.
    if run.failures or (not args.case and not result['pass']):
        raise SystemExit('BRIEF31_FAIL: see results.json')
    print(f'BRIEF31_PASS {len(run.assertions)} assertions; {len(run.screenshots)} viewport screenshots', flush=True)


if __name__ == '__main__':
    main()
