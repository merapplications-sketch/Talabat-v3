"""Capture the RU 375 live Home using the approved BRIEF-22b fixture and viewport."""
import hashlib
import io
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageDraw, ImageChops
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path.cwd() / "tools"))
import brief22_webkit as approved

ORIGIN = "https://talabot-gate1-preview-20261116.pages.dev"
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
reference = Image.open("qa-shots/unified-fix/brief22b/ru-375.webp").convert("RGB")
with sync_playwright() as pw:
    browser = pw.webkit.launch()
    ctx = browser.new_context(viewport={"width":375,"height":812}, device_scale_factor=1,
                              is_mobile=True, has_touch=True, service_workers="block")
    ctx.add_init_script("localStorage.setItem('tlb_lang','ru');window.testBroken=false")
    def route(r):
        url = urlsplit(r.request.url)
        if url.hostname == "cdn.jsdelivr.net" and "supabase-js" in url.path:
            r.fulfill(content_type="application/javascript", body=approved.qa.SDK.replace("window.__ROLE", '"customer"'))
        elif r.request.method == "GET" and r.request.url.startswith(ORIGIN + "/"):
            r.continue_()
        else:
            r.abort()
    ctx.route("**/*", route)
    page = ctx.new_page()
    page.clock.set_fixed_time(datetime(2026,11,18,9,tzinfo=timezone.utc))
    nav = page.goto(ORIGIN + "/customer", wait_until="domcontentloaded", timeout=90000)
    assert nav.status == 200 and nav.body() == Path("customer.html").read_bytes(), "live source mismatch"
    page.wait_for_function("typeof TLB!=='undefined' && TLB.orders().length>0")
    row = approved.verify(page, 375)
    assert len(row["titleStyles"]) == 7 and all(row["titleStyles"])
    print("Live source matches",hashlib.sha256(nav.body()).hexdigest(), flush=True)
    print("Order",row["order"],"titles 7 x 900/18px/22px; categories",len(row["category"]),
          "width",row["width"],"DineOut bounds",row["dineBounds"], flush=True)
    page.evaluate("window.scrollTo(0,0)")
    def shot(**kwargs):
        return Image.open(io.BytesIO(page.screenshot(animations="disabled", **kwargs))).convert("RGB")
    viewport = shot()
    page.evaluate("""()=>document.querySelectorAll('#app *').forEach(e=>{
      if(getComputedStyle(e).position==='fixed')e.setAttribute('data-qa-fixed','')})""")
    body = shot(full_page=True, style="[data-qa-fixed]{visibility:hidden!important}")
    assert body.width == 375
    approved_body = reference.crop((0,26,375,26+body.height))
    diff = ImageChops.difference(approved_body, body).convert("L").histogram()
    print("Full-page pixels differing by >16 luminance levels:",
          round(sum(diff[17:])*100/(body.width*body.height),3), "% (lossy reference)", flush=True)
    # Match the reference layout, including the natural first viewport under the full page.
    top = 26
    bottom = reference.height - viewport.height
    assert top + body.height <= bottom
    canvas = Image.new("RGB", (375,reference.height), "#edeae5")
    draw = ImageDraw.Draw(canvas)
    draw.text((6,6),"Live WebKit RU 375 | page content",fill="black")
    canvas.paste(body,(0,top))
    draw.text((6,bottom-20),"Live viewport including fixed controls",fill="black")
    canvas.paste(viewport,(0,bottom))
    canvas.save(out / "ru-375.webp", quality=79, method=6)
    browser.close()
