"""Read-only RU/375 preview check using the two approved BRIEF-23 catalogues."""
import io
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path.cwd() / "tools"))
import brief23_webkit as approved

origin = "https://talabot-gate1-preview-20261116.pages.dev"
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
wide = Image.new("RGB", (450,110), "#fdebd8")
pizza = Image.open("assets/3d/pizza.webp").convert("RGBA")
pizza.thumbnail((105,100))
wide.paste(pizza,(177,5),pizza)
fixture_image = io.BytesIO()
wide.save(fixture_image,"JPEG")
expected = Path("customer.html").read_bytes()

with sync_playwright() as pw:
    browser = pw.webkit.launch()
    for label,sdk,has_discounts in [("populated",approved.FULL_SDK,True),("no-discount",approved.EMPTY_SDK,False)]:
        ctx = browser.new_context(viewport={"width":375,"height":812},is_mobile=True,
                                  has_touch=True,device_scale_factor=1,service_workers="block",locale="ru-RU")
        ctx.add_init_script("localStorage.setItem('tlb_lang','ru');window.testBroken=false")
        def route(r):
            u = urlsplit(r.request.url)
            if r.request.method == "GET" and u.hostname == "cdn.jsdelivr.net" and "supabase-js" in u.path:
                return r.fulfill(content_type="application/javascript",body=sdk.replace("window.__ROLE",'"customer"'))
            if r.request.method == "GET" and r.request.url.startswith(origin + "/"):
                if u.path == "/qa-image/wide":
                    return r.fulfill(content_type="image/jpeg",body=fixture_image.getvalue())
                return r.continue_()
            r.abort()
        ctx.route("**/*",route)
        page = ctx.new_page()
        page.clock.set_fixed_time(datetime(2026,11,18,9,tzinfo=timezone.utc))
        nav = page.goto(origin+"/customer",wait_until="domcontentloaded",timeout=90000)
        assert nav.status == 200 and nav.body() == expected, "Live customer source differs from approved release"
        page.locator(".home-again .d6-lo").first.wait_for()
        top = approved.top_geometry(page)
        banner = page.locator(".d6-dn")
        assert banner.is_visible() and page.locator('[data-section="dine"]').is_visible()
        cards = page.locator(".home-dine .d6-dc").count()
        assert bool(cards) == has_discounts, (label,cards)
        width, content = page.evaluate("() => [innerWidth,document.documentElement.scrollWidth]")
        assert width == content == 375
        if has_discounts:
            approved.display(page).save(out/"ru-375.webp",quality=80,method=6)
        print(f"{label} | RU | viewport={width} document={content} | categories={top['categories']} in one row | DineOut=visible | cards={cards}", flush=True)
        ctx.close()
    browser.close()
