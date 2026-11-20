#!/usr/bin/env python3
"""TALABOT BRIEF-30 source-backed synthetic WebKit; AD-01 only at this commit."""
import io
import os
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

import brief25b_webkit as prior


def capture(page, dest):
    raw = page.screenshot(full_page=True, animations="disabled")
    Image.open(io.BytesIO(raw)).convert("RGB").save(dest, quality=86, method=6)


def check_header(page, lang, width, out):
    page.evaluate("go('cat',{catKey:'rest',cq:'',srt:'',fo:false})")
    h = page.locator(".ad30-head")
    h.wait_for()
    assert h.get_by_role("heading", name="Рестораны" if lang == "ru" else "Restaurants").count() == 1
    assert h.locator(".ad30-address").count() == 1
    assert h.locator(".ad30-icon").count() == 3
    assert h.locator(".ad30-icon svg").count() == 3
    ph = page.locator("input#cq").get_attribute("placeholder")
    assert ph == ("Поиск: плов…" if lang == "ru" else "Search: pilaf…"), ph
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), "Horizontal overflow"
    capture(page, out / f"{lang}-{width}-brief30-ad01-header-fixture.webp")
    page.evaluate("go('cat',{catKey:'grocery',cq:'',srt:'',fo:false})")
    assert page.locator(".ad30-head").count() == 0, "Other categories must remain unchanged"
    print(f"BRIEF30_AD01_HEADER_PASS {lang}/{width}", flush=True)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: brief30_webkit.py output_folder")
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    server = prior.qa.serve(Path.cwd())
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(executable_path=os.environ.get("TALABOT_WEBKIT") or None)
            photos = prior.fixture_logos(prior.qa.source_photos())
            for lang, width in (("ru", 375), ("en", 390)):
                context, page = prior.page_for(browser, server, photos, lang=lang, width=width)
                try:
                    check_header(page, lang, width, out)
                finally:
                    context.close()
            browser.close()
    finally:
        server.shutdown()
    print("BRIEF30_AD01_PASS; AD02..AD07_NOT_YET_IMPLEMENTED", flush=True)


if __name__ == "__main__":
    main()
