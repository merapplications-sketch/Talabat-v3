#!/usr/bin/env python3
"""TALABOT BRIEF-30 AD01..AD07 acceptance on ORIGINAL customer/admin HTML.

Offline-only synthetic fixture: KFC, Romant, Gulistan Flowers, closed test restaurant,
and the real discount / last-order dimensions from home-brief25b.json.
Never touches prod, remote accounts, payment processing or database.
"""
import base64
import hashlib
import io
import json
import os
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

import brief25b_webkit as prior

ROOT = Path.cwd()
EXTRA = """
  stores.find(s=>s.id==='s1').search_rank=2;
  stores.find(s=>s.id==='s2').search_rank=1;
  stores.find(s=>s.id==='s2').discount_pct=30;
  for(const item of items){
    item.section=({combo:'Бургеры',hot:'Бургеры',steak:'Стейки',plov:'Плов'})[item.id]||item.section||'';
    if(item.id==='steak'||item.id==='plov')item.image_url='/qa-image/brief30-'+item.id;
  }
  T.banners.push({
    id:'ad30-campaign',title:'Скидки до 30%',link_value:'s2',
    link_type:'store',placement:'top',is_active:true,sort:10,
    image_url:'/qa-image/romant',
    presentation:{audience:'restaurants',action:'campaign',campaign:'discount',floating:true,
      floating_text:{ru:'Что нового — скидки до 30%',en:'What’s new — up to 30% off'}}
  });
"""

def cuisine_photos(photos):
    """Licensed sample dishes, used only by the disposable offline catalog."""
    fixture = json.loads((ROOT / 'qa-fixtures/home-brief30.json').read_text())
    for photo in fixture['photos']:
        content = base64.b64decode(photo['content_base64'], validate=True)
        assert hashlib.sha256(content).hexdigest() == photo['sha256']
        photos['brief30-' + photo['id']] = content
    return photos


def check_cuisine_images(page):
    # A missing semantic 3D asset must resolve to this cuisine's real menu image,
    # never to a shared basket or another cuisine's picture.
    images = page.locator('.ad30-cuisine-circle img')
    images.evaluate_all("nodes=>nodes.forEach(i=>i.loading='eager')")
    page.wait_for_function("""()=>[...document.querySelectorAll('.ad30-cuisine-circle img')]
      .every(i=>i.complete&&i.naturalWidth>0)""")
    sources = images.evaluate_all("nodes=>nodes.map(i=>i.getAttribute('src'))")
    assert set(sources) == {'assets/3d/hamburger.webp', '/qa-image/brief30-steak', '/qa-image/brief30-plov'}, sources
    assert len(sources) == len(set(sources)), 'Cuisine pictures must be distinct'
    for source in ('/qa-image/brief30-steak', '/qa-image/brief30-plov'):
        metrics = page.locator('.ad30-cuisine-circle img[src="' + source + '"]').evaluate("""i=>({
          fit:getComputedStyle(i).objectFit,
          radius:getComputedStyle(i.parentElement).borderRadius,
          overflow:getComputedStyle(i.parentElement).overflow,
          image:[i.clientWidth,i.clientHeight],circle:[i.parentElement.clientWidth,i.parentElement.clientHeight]
        })""")
        assert metrics['fit'] == 'cover' and metrics['radius'] == '50%' and metrics['overflow'] == 'hidden', metrics
        assert metrics['image'] == metrics['circle'], metrics

def capture(page, output, name):
    # A real viewport preserves the relationship between fixed controls and rows.
    raw = page.screenshot(full_page=False, animations="disabled")
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    assert image.size == (page.viewport_size['width'], page.viewport_size['height']), (name, image.size)
    image.save(output / name, quality=85, method=6)


def settle_layout(page):
    page.evaluate("()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done)))")


def floating_metrics(page):
    settle_layout(page)
    return page.locator('.ad30-float').evaluate("""b=>{
      const r=b.getBoundingClientRect(),s=b.querySelector('span'),n=document.querySelector('.nav').getBoundingClientRect();
      const bar=document.querySelector('.bar')?.getBoundingClientRect();
      const range=document.createRange();range.selectNodeContents(s);
      const text=s.getBoundingClientRect();
      return {text:s.textContent,label:b.getAttribute('aria-label'),width:r.width,max:innerWidth*.92,
        gap:(bar?Math.min(n.top,bar.top):n.top)-r.bottom,
        textFits:s.scrollWidth<=s.clientWidth+1&&[...range.getClientRects()].every(x=>x.left>=text.left-1&&x.right<=text.right+1),
        oneLine:[...range.getClientRects()].length===1,
        visible:getComputedStyle(b).visibility==='visible'&&getComputedStyle(b).opacity!=='0',
        overlaps:[...document.querySelectorAll('.ad30-card-copy')].filter(e=>{const c=e.getBoundingClientRect();
          return r.left<c.right&&r.right>c.left&&r.top<c.bottom&&r.bottom>c.top}).length,
        overflow:document.documentElement.scrollWidth>innerWidth+1};
    }""")


def check_floating_layout(page, lang):
    metrics = floating_metrics(page)
    expected = 'Что нового — скидки до 30%' if lang == 'ru' else 'What’s new — up to 30% off'
    assert metrics['text'] == metrics['label'] == expected, metrics
    assert metrics['textFits'] and metrics['oneLine'], metrics
    assert metrics['width'] <= metrics['max'] + 1 and not metrics['overflow'], metrics
    assert abs(metrics['gap'] - 12) <= 1, metrics
    assert not metrics['visible'] or metrics['overlaps'] == 0, metrics
    return metrics


def reveal_floating_campaign(page):
    settle_layout(page)
    page.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)')
    # Wait for the downward-scroll hide before reversing direction; WebKit may
    # coalesce back-to-back programmatic scroll events after a dialog closes.
    page.wait_for_function("""()=>scrollY>60&&getComputedStyle(document.querySelector('.ad30-float')).opacity==='0'""")
    assert not page.locator('.ad30-float').is_visible(), 'Campaign must hide on downward scroll'
    page.evaluate('window.scrollBy(0,-24)')
    settle_layout(page)
    page.locator('.ad30-float').wait_for(state='visible')


def check_floating_cart_and_long_copy(page, lang):
    # The cart keeps its accepted place in the stack; the campaign sits above it.
    saved = page.evaluate('({cart:S.cart,store:S.cartStore})')
    page.evaluate("()=>{S.cartStore='KFC';S.cart={combo:1};render()}")
    assert page.locator('#app .bar').count() == 1
    reveal_floating_campaign(page)
    assert check_floating_layout(page, lang)['visible']
    page.evaluate('saved=>{S.cart=saved.cart;S.cartStore=saved.store;render()}', saved)

    # Overlong authored copy is not silently ellipsized or allowed to overflow.
    # The regular campaign banner stays available until its floating copy is edited.
    original = page.evaluate("TLB.banners().find(b=>b.id==='ad30-campaign').presentation.floating_text[TLB.lang()]")
    long_copy = original * 16
    page.evaluate("text=>{TLB.banners().find(b=>b.id==='ad30-campaign').presentation.floating_text[TLB.lang()]=text;render()}", long_copy)
    settle_layout(page)
    assert page.locator('.ad30-float span').text_content() == long_copy
    assert not page.locator('.ad30-float').is_visible()
    assert page.locator('.ad30-banner').count() == 4
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    page.evaluate("text=>{TLB.banners().find(b=>b.id==='ad30-campaign').presentation.floating_text[TLB.lang()]=text;render()}", original)


def check_empty_filter_reset(page, lang, width, output):
    ru = lang == 'ru'
    page.locator('.ad30-cuisine').filter(has_text='Плов' if ru else 'Pilaf').click()
    page.locator('.ad30-filter').filter(has_text='Рейтинг 4.0+' if ru else 'Rating 4.0+').click()
    assert page.locator('.ad30-card').count() == 0
    empty = page.locator('.ad30-empty')
    assert empty.count() == 1, 'An empty filter must explain the state and provide a way out'
    assert empty.get_by_text('Нет ресторанов по этому фильтру' if ru else 'No restaurants match this filter', exact=True).count() == 1
    assert empty.locator('svg').count() == 1
    reset = empty.get_by_role('button', name='Сбросить фильтры' if ru else 'Reset filters', exact=True)
    assert reset.count() == 1
    settle_layout(page)
    assert reset.is_visible()
    clear = reset.evaluate("""b=>{const r=b.getBoundingClientRect(),nav=document.querySelector('.nav').getBoundingClientRect();
      return {bottom:r.bottom,edge:nav.top-12,hit:document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest('button')===b}}""")
    assert clear['bottom']<=clear['edge']+1 and clear['hit'], ('Reset is obscured by bottom navigation',clear)
    capture(page, output, f'{lang}-{width}-brief30b-empty-filter-viewport-fixture.webp')
    reset.click()
    assert page.locator('.ad30-card').count() == 3
    assert page.locator('.ad30-empty').count() == 0
    assert page.locator('.ad30-cuisine[aria-pressed="true"],.ad30-filter[aria-pressed="true"]').count() == 0
    assert page.locator('.ad30-current-sort').inner_text() == ('Рекомендуемые' if ru else 'Recommended')

    # Reset also removes query and legacy banner/open-only restrictions, not
    # just the currently selected cuisine/chip that produced the first empty state.
    page.evaluate("()=>{S.cq='no-matching-restaurant-qa';S.srt='free';S.fo=true;render()}")
    assert page.locator('.ad30-card').count() == 0
    page.get_by_role('button', name='Сбросить фильтры' if ru else 'Reset filters', exact=True).click()
    assert page.evaluate("S.cq===''&&S.srt===''&&S.fo===false&&S.v==='cat'&&S.catKey==='rest'")
    assert page.locator('input#cq').input_value() == ''
    assert page.locator('.ad30-card').count() == 3
    assert page.locator('.ad30-filter[aria-pressed="true"]').count() == 0


def enter_restaurants(page):
    page.evaluate("go('cat',{catKey:'rest',cq:'',srt:'',fo:false})")
    page.locator(".ad30-head").wait_for()


def check_restaurants(page, lang, width, output):
    enter_restaurants(page)
    ru = lang == 'ru'
    header = page.locator(".ad30-head")
    assert header.get_by_role("heading", name="Рестораны" if ru else "Restaurants").count() == 1
    assert header.locator(".ad30-address").count() == 1
    assert header.locator(".ad30-icon").count() == 3
    assert page.locator("input#cq").get_attribute("placeholder") == ("Поиск: плов…" if ru else "Search: pilaf…")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "Viewport overflow"

    rail = page.locator(".ad30-banner-row")
    assert rail.locator(".ad30-banner").count() == 4, "3 defaults and manager campaign"
    assert rail.evaluate("e=>e.scrollWidth>e.clientWidth")
    metrics = rail.evaluate("""e=>{
      const a=e.querySelector('.ad30-banner'),w=e.clientWidth;
      return {width:a.getBoundingClientRect().width,client:w,corner:getComputedStyle(a).borderTopLeftRadius}
    }""")
    assert 2.1 < metrics['client']/metrics['width'] < 2.7, metrics
    assert metrics['corner'] == '20px', metrics
    assert page.locator(".ad30-again-item").count() >= 1
    assert page.locator(".ad30-again-logo img").count() >= 1
    cards = page.locator(".ad30-card")
    assert cards.count() == 3, cards.all_inner_texts()
    assert 'Romant' in cards.first.inner_text(), "search_rank=1 must lead"
    assert cards.first.locator(".home-ad-label").inner_text() == ("Реклама" if ru else "Ad")
    assert 'KFC' in cards.nth(1).inner_text()
    assert cards.last.get_attribute("class").endswith("closed"), "Closed must be last"
    assert cards.first.locator(".ad30-card-logo").evaluate(
        "e=>Math.abs(e.getBoundingClientRect().width-96)<1&&Math.abs(e.getBoundingClientRect().height-96)<1")
    assert cards.first.locator(".ad30-card-logo .hrt").count() == 1
    assert cards.first.locator(".ad30-card-logo img").get_attribute("src") == '/qa-image/pro-khinkali'
    assert cards.first.locator(".ad30-card-offer").count() == 1
    assert cards.last.locator(".ad30-card-closed").count() == 1, cards.last.inner_text()
    assert cards.last.locator(".ad30-card-closed").inner_text().strip() == ("Закрыт" if ru else "Closed"), cards.last.inner_text()
    assert page.locator(".ad30-float").count() == 1, "Explicit floating field supplied"
    check_cuisine_images(page)
    check_floating_layout(page, lang)
    capture(page, output, f"{lang}-{width}-brief30b-restaurants-viewport-fixture.webp")
    cuisine_crop = Image.open(io.BytesIO(page.locator('.ad30-cuisines').screenshot(animations='disabled'))).convert('RGB')
    cuisine_crop.save(output / f'{lang}-{width}-brief30b-cuisines-closeup-fixture.webp', quality=90, method=6)
    reveal_floating_campaign(page)
    visible_metrics = check_floating_layout(page, lang)
    assert visible_metrics['visible'] and visible_metrics['overlaps'] == 0, visible_metrics
    capture(page, output, f"{lang}-{width}-brief30b-campaign-viewport-fixture.webp")
    page.evaluate('window.scrollTo(0,0)')
    settle_layout(page)
    check_floating_layout(page, lang)

    # Sorting sheet is a real interactive modal, not a decorative screenshot.
    page.locator(".ad30-sort").click()
    sheet = page.locator(".ad30-sort-sheet")
    sheet.wait_for()
    assert sheet.locator(".ad30-sort-choice").count() == 4
    capture(page, output, f"{lang}-{width}-brief30-sort-sheet-fixture.webp")
    sheet.locator(".ad30-sort-choice").nth(1).click()
    assert page.locator(".ad30-sort-sheet").count() == 0
    assert page.locator(".ad30-current-sort").inner_text() == ("По рейтингу" if ru else "By rating")

    # Cuisine controls are sourced from menu item sections, and clicking again clears.
    cuisine = page.locator(".ad30-cuisine").filter(has_text="Плов")
    if not ru:
        cuisine = page.locator(".ad30-cuisine").filter(has_text="Pilaf")
    cuisine.click()
    assert cuisine.get_attribute("aria-pressed") == "true"
    assert page.locator(".ad30-card").count() == 1
    assert "Romant" in page.locator(".ad30-card").inner_text()
    capture(page, output, f"{lang}-{width}-brief30-cuisine-filter-fixture.webp")
    cuisine.click()
    assert cuisine.get_attribute("aria-pressed") == "false"
    assert cards.count() == 3
    check_empty_filter_reset(page, lang, width, output)

    # Multiple active chips combine via logical AND, no fake match for low rating.
    disc = page.locator(".ad30-filter").filter(has_text="Скидки" if ru else "Discounts")
    rate = page.locator(".ad30-filter").filter(has_text="Рейтинг 4.0+" if ru else "Rating 4.0+")
    disc.click()
    assert cards.count() == 1 and "Romant" in cards.first.inner_text()
    rate.click()
    assert disc.get_attribute("aria-pressed") == "true"
    assert rate.get_attribute("aria-pressed") == "true"
    assert cards.count() == 0
    rate.click()
    disc.click()
    assert cards.count() == 3

    # Three default banners link to genuine list filters; campaign opens existing Z-07 sheet.
    rail.locator(".ad30-banner").first.click()
    assert page.evaluate("S.v==='cat' && S.srt==='disc'")
    assert cards.count() == 1
    page.evaluate("go('cat',{catKey:'rest',cq:'',srt:'',fo:false})")
    rail.locator(".ad30-banner").nth(3).click()
    dialog = page.locator("#happy-hour-sheet[open]")
    dialog.wait_for()
    assert "Romant" in dialog.inner_text()
    dialog.locator(".hh-sheet-close").click()
    assert page.locator("#happy-hour-sheet").count() == 0

    # Floating campaign is the same manager-directed Z-07 action, never automatic.
    reveal_floating_campaign(page)
    page.locator(".ad30-float").click()
    dialog.wait_for()
    dialog.locator(".hh-sheet-close").click()
    assert page.evaluate("S.v==='cat'")
    check_floating_cart_and_long_copy(page, lang)
    page.evaluate("go('home')")
    assert page.locator(".ad30-banner-row").count() == 0
    assert page.evaluate("heroSlides().every(x=>x.b?.id!=='ad30-campaign')"), "Manager restaurant banner leaked into Home"
    page.evaluate("go('cat',{catKey:'grocery',cq:'',srt:'',fo:false})")
    assert page.locator(".ad30-head").count() == 0, "Other categories changed"
    print(f"BRIEF30_AD01_AD07_CUSTOMER_PASS {lang}/{width}", flush=True)


def check_admin(browser, server, photos):
    # Source-backed REAL admin HTML with the same local-only adapter.
    prior.qa.SDK = prior.FIX
    context, page = prior.qa.page_at(browser, server, photos, 'ru', 375, role='admin')
    try:
        page.evaluate("()=>{tab='b';showAddB=true;render()}")
        options = page.locator("#audience option").all_text_contents()
        assert "Рестораны" in options, options
        page.locator("#audience").select_option("restaurants")
        assert page.locator("#audience").input_value() == "restaurants"
        assert page.evaluate("bannerPresentation().presentation.audience==='restaurants'") if page.evaluate("bannerSchema()") else True
        print("BRIEF30_ADMIN_AUDIENCE_PASS", flush=True)
    finally:
        context.close()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: brief30_webkit.py OUTPUT_DIR")
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    server = prior.qa.serve(ROOT)
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(executable_path=os.environ.get("TALABOT_WEBKIT") or None)
            photos = cuisine_photos(prior.fixture_logos(prior.qa.source_photos()))
            for lang, width in (("ru",375),("en",390)):
                context, page = prior.page_for(browser, server, photos, EXTRA, lang=lang, width=width)
                try:
                    check_restaurants(page, lang, width, out)
                finally:
                    context.close()
            check_admin(browser, server, photos)
            browser.close()
    finally:
        server.shutdown()
    print("BRIEF30_AD01..AD07_WEBKIT_ALL_PASS; NO PRODUCTION OR PAYMENTS", flush=True)


if __name__ == "__main__":
    main()
