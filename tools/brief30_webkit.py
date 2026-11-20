#!/usr/bin/env python3
"""TALABOT BRIEF-30 AD01..AD07 acceptance on ORIGINAL customer/admin HTML.

Offline-only synthetic fixture: KFC, Romant, Gulistan Flowers, closed test restaurant,
and the real discount / last-order dimensions from home-brief25b.json.
Never touches prod, remote accounts, payment processing or database.
"""
import io
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
  for(const item of items){
    item.section=({combo:'Бургеры',hot:'Бургеры',steak:'Стейки',plov:'Плов'})[item.id]||item.section||'';
  }
  T.banners.push({
    id:'ad30-campaign',title:'Скидки до 20%',link_value:'s2',
    link_type:'store',placement:'top',is_active:true,sort:10,
    image_url:'/qa-image/romant',
    presentation:{audience:'restaurants',action:'campaign',campaign:'discount',floating:true,
      floating_text:{ru:'Что нового — скидки до 20%',en:'What’s new — up to 20% off'}}
  });
"""

def capture(page, output, name):
    raw = page.screenshot(full_page=True, animations="disabled")
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    assert image.width > 0 and image.height >= 600, (name, image.size)
    image.save(output / name, quality=85, method=6)


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
    assert cards.last.get_by_text("Закрыт" if ru else "Closed").count() == 1
    assert page.locator(".ad30-float").count() == 1, "Explicit floating field supplied"
    capture(page, output, f"{lang}-{width}-brief30-complete-restaurants-fixture.webp")

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
    page.locator(".ad30-float").click()
    dialog.wait_for()
    dialog.locator(".hh-sheet-close").click()
    assert page.evaluate("S.v==='cat'")
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
            photos = prior.fixture_logos(prior.qa.source_photos())
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
