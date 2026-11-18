"""Check the deployed Home B with the manager's RU 375px reference and synthetic session."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright

import brief20_visual as approved
from qa_all import FIX

ORIGIN = "https://talabot-gate1-preview-20261116.pages.dev"
OUT = Path("qa-shots/ops-live-homeb-d8538a26")
OUT.mkdir(parents=True, exist_ok=True)
reference_path = Path("qa-shots/unified-fix/brief20/compare/customer-home-ru-375-side-by-side.png")
source = Path(".ops-source")
live_assets = {}
blocked_hosts = set()
with sync_playwright() as pw:
    browser = pw.webkit.launch()
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2,
                              is_mobile=True, has_touch=True, locale="ru-RU", service_workers="block")
    ctx.add_init_script("localStorage.setItem('tlb_lang','ru')")
    def route(r):
        u = urlsplit(r.request.url)
        if r.request.method == "GET" and (u.scheme + "://" + u.netloc) == ORIGIN:
            r.continue_()
        elif u.hostname == "cdn.jsdelivr.net" and "supabase-js" in u.path:
            r.fulfill(status=200, content_type="application/javascript",
                      body=FIX.replace("window.__ROLE", '"customer"'))
        else:
            blocked_hosts.add(u.hostname)
            r.abort("blockedbyclient")
    ctx.route("**/*", route)
    page = ctx.new_page()
    responses = []
    page.on("response", lambda r: responses.append(r) if r.url.startswith(ORIGIN + "/") else None)
    js_errors = []
    page.on("pageerror", lambda e: js_errors.append(str(e)))
    nav = page.goto(ORIGIN + "/customer", wait_until="load", timeout=90000)
    assert nav.status == 200
    approved.prepare(page, "customer", "home")
    metrics = approved.audit(page, "customer", "home", "ru", 375)
    page.screenshot(path=str(OUT / "live-home-ru-375.png"), full_page=True, animations="disabled")
    for resp in responses:
        path = urlsplit(resp.url).path.lstrip("/")
        rel = "customer.html" if path == "customer" else path
        f = source / rel
        if not f.is_file():
            continue
        data = resp.body()
        live_hash = hashlib.sha256(data).hexdigest()
        assert resp.status == 200 and live_hash == hashlib.sha256(f.read_bytes()).hexdigest(), rel
        live_assets[rel] = live_hash
    browser.close()
assert {"customer.html", "talabat-core.js", "assets/customer-c/customer-c.js"} <= live_assets.keys()
with Image.open(reference_path) as original:
    w, h = original.size
    reference = original.crop((w // 2, 0, w, h)).convert("RGB")
live = Image.open(OUT / "live-home-ru-375.png").convert("RGB")
comparison = Image.new("RGB", (reference.width + live.width, max(reference.height, live.height)), "white")
comparison.paste(reference)
comparison.paste(live, (reference.width, 0))
comparison.save(OUT / "reference-and-live.png", optimize=True)
comparison.resize((750, comparison.height // 2)).save(OUT / "overview.png", optimize=True)
diff, geometry = approved.pixel_delta(reference, live)
checks = {"url": ORIGIN + "/customer", "browser": "Linux WebKit", "fixture": "PM BRIEF-20 synthetic RU",
          "source": "d8538a26846491343f4d7d9d3df276ac5095182f", "deployment": "ec0a2582-39c1-442a-959c-548327c8c247",
          "metrics": metrics, "pixel_difference_pct": diff, "geometry": geometry, "verified_asset_count": len(live_assets),
          "live_sha256": live_assets, "errors": approved.errors + js_errors, "blocked_external_hosts": sorted(filter(None,blocked_hosts))}
(OUT / "check.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2))
print("Width:", metrics["width"], "scroll width:", metrics["scrollWidth"], "DineOut:", metrics["dineout"],
      "delta:", diff, "size:", geometry, "matching files:", len(live_assets), "errors:", checks["errors"], flush=True)
assert not checks["errors"] and diff <= 1.5 and reference.size == live.size
