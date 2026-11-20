#!/usr/bin/env python3
"""BRIEF-CI1: fast, fully offline WebKit smoke and the CURRENT brief only.

No production services, accounts, data, payments, or modified product HTML.
The approved baseline is provided by the workflow's read-only Git worktree.
"""
import os
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

import brief25b_webkit as fixture
from brief24_webkit import money
from brief25c_webkit import test_brief29


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: ci1_fast_webkit.py APPROVED_BASELINE OUTPUT_DIR")
    baseline = Path(sys.argv[1]).resolve(strict=True)
    out = Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    assert (baseline / "customer.html").is_file(), "Approved baseline is absent"
    # Fail closed on a category/product delta if BRIEF-30 acceptance is missing.
    changed = set(subprocess.check_output(
        ["git", "diff", "--name-only", "af466951", "HEAD"], text=True
    ).splitlines())
    if {"customer.html", "admin.html"} & changed:
        assert (Path("tools") / "brief30_webkit.py").is_file(), (
            "BRIEF-30 product was changed without its focused acceptance script"
        )
    assert not os.environ.get("SUPABASE_URL"), "Cloud database context forbidden"
    assert not os.environ.get("SUPABASE_ACCESS_TOKEN"), "Cloud credentials forbidden"

    approved_server = fixture.qa.serve(baseline)
    current_server = fixture.qa.serve(Path.cwd())
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(executable_path=os.environ.get("TALABOT_WEBKIT") or None)
            photos = fixture.fixture_logos(fixture.qa.source_photos())
            approved_ctx, approved = fixture.page_for(browser, approved_server, photos)
            try:
                expected_money = money(approved)
            finally:
                approved_ctx.close()
            current_ctx, current = fixture.page_for(browser, current_server, photos)
            try:
                assert current.evaluate("S.v==='home'"), "Home failed to open"
                assert current.locator(".home-ad-carousel").count() == 1, "Home campaign missing"
                assert current.locator(".home-l-near .home-l-card").count() >= 3, "Home catalogue missing"
                assert current.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), "Home horizontal overflow"
                actual_money = money(current)
                assert actual_money == expected_money, "Financial parity differs from approved baseline"
                fixture.shot(current, out, "ru-375-home-smoke.webp")
                print("CI1_HOME_RU375_SMOKE_PASS; FINANCIAL_PARITY_PASS", flush=True)
            finally:
                current_ctx.close()

            # Once the BRIEF-30 test is delivered, run ONLY that brief on pushes.
            # Otherwise retain BRIEF-29's last source-backed focused acceptance.
            if (Path("tools") / "brief30_webkit.py").is_file():
                print("CI1_SELECTED_BRIEF_30", flush=True)
            else:
                print("CI1_SELECTED_BRIEF_29", flush=True)
                test_brief29(browser, current_server, photos, out)
            browser.close()
    finally:
        current_server.shutdown()
        approved_server.shutdown()

    if (Path("tools") / "brief30_webkit.py").is_file():
        subprocess.run([sys.executable, "tools/brief30_webkit.py", str(out)], check=True)
    print("CI1_FAST_WEBKIT_PASS; ONE_BRIEF_AND_ONE_HOME_SMOKE", flush=True)


if __name__ == "__main__":
    main()
