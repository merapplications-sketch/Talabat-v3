"""Stage 22 synthetic-only, isolated Playwright security and UX acceptance.
Never navigate or send data outside the exact Cloudflare Pages fixture origin.
No live logins, customer data, order submission, payment, production writes or deployment.
"""
import asyncio
import hashlib
import json
import os
import ssl
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, HTTPSHandler, Request
from playwright.async_api import async_playwright

HOST = "talabot-safari-demo-20261115.pages.dev"
URL = "https://" + HOST
OUTDIR = Path("stage22-qa-artifacts")
OUTDIR.mkdir(exist_ok=True)
SHA = {
    "/": "2c74b7af8b8d1cdad0d3ce446ad2591703088e17948f2ba6636a83d7795466b2",
    "/demo-guard.js": "8d19a5a9d251b30202a9f6cb9d4703df67b2e862885ab5fbac4b86ec2c7892d4",
    "/demo-fixture.js": "2ac636de0fb1719d182242d803fc394cee5c7aa6969ecd2fae8ce829cb4826a8",
}
report = {
    "case": "TALABOT_STAGE22_ISOLATED_SYNTHETIC_ONLY",
    "status": "STARTED",
    "http_assets": [],
    "network": {"blocked": [], "requests": [], "responses": [], "failed": [],
                "websockets": [], "pageerrors": [], "console": []},
    "geometry": [],
    "checkout": {"status": "NOT_EXECUTED"},
    "visual": {},
    "har": {"status": "NOT_CAPTURED"},
}

def allowed(u):
    p = urlsplit(u)
    return p.scheme == "https" and p.hostname == HOST and p.port in (None, 443) and not p.username and not p.password

def label(u):
    p = urlsplit(u)
    return (p.hostname or "<unknown>") + (p.path or "/")

def check(predicate, message):
    if not predicate:
        raise RuntimeError(message)

def log():
    artifact = OUTDIR / "case-result.json"
    artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("STAGE22_RESULT_BEGIN")
    # Bounded printable summary; fully structured JSON is retained as local artifact.
    for k in ("status", "http_assets", "geometry", "en_reload", "checkout", "visual", "har"):
        print(json.dumps({k: report.get(k)}, ensure_ascii=False, default=str)[:30000])
    n = report["network"]
    print(json.dumps({"requests": len(n["requests"]), "responses": len(n["responses"]),
                      "failed": len(n["failed"]), "failed_sample": n["failed"][:14],
                      "blocked": n["blocked"], "websockets": n["websockets"],
                      "pageerrors": n["pageerrors"], "console_sample": n["console"][:12]},
                     ensure_ascii=False)[:12000])
    print("STAGE22_RESULT_END", flush=True)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise RuntimeError("FAIL_CLOSED_UNEXPECTED_HTTP_REDIRECT")

def preflight():
    check(os.getenv("GITHUB_ACTIONS") == "true", "UNAUTHORIZED_ENVIRONMENT")
    check(os.getenv("GITHUB_REPOSITORY") == "merapplications-sketch/Talabat-v3", "UNAUTHORIZED_REPOSITORY")
    check(os.getenv("GITHUB_REF") == "refs/heads/review/stage22-one-shot-qa-20261115", "UNAUTHORIZED_BRANCH")
    opener = build_opener(NoRedirect(), HTTPSHandler(context=ssl.create_default_context()))
    for path in ("/", "/demo-guard.js", "/demo-fixture.js", "/assets/3d/hamburger.webp"):
        check(allowed(URL + path), "OUTSIDE_ORIGIN_IN_PREFLIGHT")
        with opener.open(Request(URL + path, headers={"User-Agent": "TALABOT-Stage22-Preflight"}),
                         timeout=20) as response:
            blob = response.read(3_000_000)
            evidence = {"path": path, "http_status": response.status, "type": response.headers.get("Content-Type", ""),
                        "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
            if path == "/":
                evidence["csp"] = response.headers.get("Content-Security-Policy", "")
                evidence["nosniff"] = response.headers.get("X-Content-Type-Options", "")
        report["http_assets"].append(evidence)
        check(evidence["http_status"] == 200, "LIVE_ASSET_STATUS_" + path)
        if path in SHA:
            check(evidence["sha256"] == SHA[path], "HOSTED_SOURCE_CHANGED_" + path)
        if path == "/":
            check("connect-src 'none'" in evidence["csp"] and "form-action 'none'" in evidence["csp"], "CSP_BLOCKING_MISSING")
            check(evidence["nosniff"].lower() == "nosniff", "NO_SNIFF_MISSING")
        if path.endswith(".js"):
            check("javascript" in evidence["type"].lower(), "INVALID_JS_MIME")
        if path.endswith(".webp"):
            check("image/webp" in evidence["type"].lower(), "INVALID_WEBP_MIME")

def sanitize_har(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("log", {}).get("entries", [])
    for entry in entries:
        for side in ("request", "response"):
            obj = entry.get(side, {})
            obj["headers"] = [h for h in obj.get("headers", [])
                              if h.get("name", "").lower() not in ("authorization", "cookie", "set-cookie", "proxy-authorization")]
            obj.pop("cookies", None)
            obj.pop("postData", None)
            obj.pop("queryString", None)
            if side == "response":
                obj.get("content", {}).pop("text", None)
                obj.get("content", {}).pop("encoding", None)
    destination = OUTDIR / "stage22-network-sanitized.har"
    destination.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    report["har"] = {"entry_count": len(entries), "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                     "redacted": True, "file": destination.name}
    path.unlink()
    check(len(entries) > 0, "HAR_EMPTY_AFTER_LIVE_NAVIGATION")

async def main():
    preflight()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = None
        try:
            ctx = await browser.new_context(
                viewport={"width": 390, "height": 844},
                service_workers="block",
                accept_downloads=False,
                record_har_path="stage22-qa-artifacts/local-raw.har",
            )
            async def intercept(route):
                if allowed(route.request.url):
                    await route.continue_()
                else:
                    report["network"]["blocked"].append({"type": "HTTP", "path": label(route.request.url)})
                    await route.abort("blockedbyclient")
            await ctx.route("**/*", intercept)
            check(hasattr(ctx, "route_web_socket"), "NO_WS_INTERCEPTOR_AVAILABLE")
            async def intercept_ws(route):
                report["network"]["websockets"].append(label(route.url))
                await route.close()
            await ctx.route_web_socket("**/*", intercept_ws)
            async def attach(page):
                page.on("request", lambda r: report["network"]["requests"].append(label(r.url)))
                page.on("response", lambda r: report["network"]["responses"].append({"path": label(r.url), "status": r.status,
                                                                                   "type": r.headers.get("content-type", "")}))
                page.on("requestfailed", lambda r: report["network"]["failed"].append({"path": label(r.url), "error": str(r.failure)}))
                page.on("pageerror", lambda e: report["network"]["pageerrors"].append(str(e)[:300]))
                page.on("console", lambda m: report["network"]["console"].append({"kind": m.type, "text": m.text[:200]})
                        if m.type == "error" else None)
            dry = await ctx.new_page()
            await attach(dry)
            try:
                await dry.goto("https://qa-stage22-denied.invalid/never-sent", timeout=5000)
            except Exception:
                pass
            check(len(report["network"]["blocked"]) == 1 and
                  report["network"]["blocked"][0]["path"].startswith("qa-stage22-denied.invalid/"),
                  "SYNTHETIC_OUTSIDE_ORIGIN_DENIAL_NOT_PROVEN")
            await dry.close()

            page = await ctx.new_page()
            await attach(page)
            resp = await page.goto(URL + "/?lang=en", wait_until="load", timeout=30000)
            check(resp is not None and resp.status == 200, "INITIAL_HOSTED_PAGE_NOT_LOADED")
            await page.wait_for_timeout(450)
            check(not report["network"]["websockets"], "WEBSOCKET_ATTEMPT_FOUND")
            check(len(report["network"]["blocked"]) == 1, "UNEXPECTED_OFF_ORIGIN_AFTER_LOAD")
            # Non-invasive independent control: the load-time guard must be really active, not merely included as source.
            guard = await page.evaluate("""() => ({
                blocked: typeof window.__demoBlockedActions === 'number',
                api: !!window.TLB && String(window.TLB.placeOrder).includes('__demoBlockedActions'),
                global: String(window.place).includes('__demoBlockedActions'),
                phone: !!(typeof ME!=='undefined' && ME.phone),
                addresses: typeof curAddr === 'function' && !!curAddr()
            })""")
            report["guard"] = guard
            check(all(guard.values()), "GUARD_OR_FAKE_PRECONDITION_NOT_READY")

            # Reuse already checked eight viewport cases by referencing the previous accepted run; avoid redoing whole matrix.
            # One current-commit 390px DOM sample is still needed for artifact/visual comparability.
            geometry = await page.evaluate("""() => ({
                lang:document.documentElement.lang,
                document_scroll:document.documentElement.scrollWidth,
                viewport:document.documentElement.clientWidth,
                demo_banner:!!document.querySelector('#tlb-demo-banner'),
                title:document.title
            })""")
            report["geometry"].append({"width": 390, "locale": "en", **geometry})
            check(geometry["lang"] == "en" and geometry["document_scroll"] <= geometry["viewport"] + 1,
                  "EN_390_GEOMETRY")
            await page.screenshot(path=str(OUTDIR / "en-home-390.png"), full_page=True, animations="disabled")
            await page.reload(wait_until="load")
            report["en_reload"] = await page.evaluate("document.documentElement.lang==='en'")
            check(report["en_reload"], "EN_LOCALE_NOT_PERSISTED_ON_RELOAD")

            # Exact synthetic cart only. Never relax app checks or invent prod accounts.
            fixture = await page.evaluate("""() => {
                if(typeof S==='undefined'||typeof lk!=='function'||typeof render!=='function') return {ok:false};
                const store=STORES.find(x=>menuOf(x.n).some(it=>it.id==='i1'));
                if(!store)return {ok:false};
                const selected=TLB.optionsOf('i1').filter(g=>g.required).map(g=>g.options[0].id);
                S.store=store.n;S.cartStore=store.n;
                S.cart={[lk('i1',selected,'')]:2};
                S.pay='cash';S.useWallet=false;S.usePts=false;S.v='pay';S.hcf=null;render();
                const thumb=document.querySelector('#hbtn .d69-slide-thumb');
                return {
                   ok:!!thumb, thumb_disabled:thumb?thumb.disabled:null,
                   valid:badKeys().length===0,
                   busy:!!S.busy, visible:!document.hidden,
                   phone_present:!!ME.phone, address_present:!!curAddr(),
                   store_open:!closedNow(S.cartStore), too_far:tooFar(),
                   total:calc().total, quote_ready:!!S.quote, current_view:S.v
                };
            }""")
            report["fixture"] = fixture
            check(fixture.get("ok") and fixture.get("valid") and not fixture.get("thumb_disabled") and
                  not fixture.get("busy") and fixture.get("visible") and fixture.get("phone_present") and
                  fixture.get("address_present") and fixture.get("store_open") and not fixture.get("too_far"),
                  "SYNTHETIC_CHECKOUT_PRECONDITION_FAILED")
            await page.screenshot(path=str(OUTDIR / "checkout-before.png"), full_page=True, animations="disabled")

            # Instrument real browser pointer events; this does not call app methods or alter state.
            await page.evaluate("""() => {
                window.__stage22PointerEvents=[];
                const thumb=document.querySelector('#hbtn .d69-slide-thumb');
                for(const ev of ['pointerdown','pointermove','pointerup','lostpointercapture']){
                    thumb.addEventListener(ev, e=>window.__stage22PointerEvents.push({type:ev,x:Math.round(e.clientX)}));
                }
            }""")
            before = await page.evaluate("window.__demoBlockedActions")
            thumb = await page.locator("#hbtn .d69-slide-thumb").bounding_box()
            bar = await page.locator("#hbtn").bounding_box()
            check(bool(thumb) and bool(bar), "NO_VISIBLE_SLIDER_RECT")
            start_x = thumb["x"] + thumb["width"]/2
            y = thumb["y"] + thumb["height"]/2
            await page.mouse.move(start_x, y)
            await page.mouse.down()
            down = await page.evaluate("""() => ({
                acquired:typeof HOLD !== 'undefined' && !!HOLD,
                hidden:document.hidden,
                enabled:!document.querySelector('#hbtn .d69-slide-thumb').disabled,
                events:window.__stage22PointerEvents.slice(-3),
                max:typeof HOLD!=='undefined' && HOLD ? HOLD.max : null
            })""")
            report["checkout"]["pointer_down"] = down
            check(down["acquired"] and not down["hidden"] and down["enabled"], "POINTER_DOWN_NOT_ACQUIRED")
            # Use the actual HTML slider HOLD.max, not guessed CSS width; must cross 96% threshold.
            end_x = start_x + down["max"] + 14
            await page.mouse.move(end_x, y, steps=22)
            moved = await page.evaluate("""() => ({
                active:typeof HOLD!=='undefined' && !!HOLD,
                progress:typeof HOLD!=='undefined' && HOLD ? HOLD.p : null,
                events:window.__stage22PointerEvents.slice(-5)
            })""")
            report["checkout"]["pointer_moved"] = moved
            check(moved["active"] and moved["progress"] >= 0.96, "POINTER_GESTURE_NOT_COMPLETE")
            await page.mouse.up()
            await page.wait_for_timeout(550)
            result = await page.evaluate("""() => ({
                blocked_actions:window.__demoBlockedActions,
                view:S.v, busy:!!S.busy,
                completion_counter:window.__stage22PointerEvents.length,
                event_types:window.__stage22PointerEvents.slice(-8).map(x=>x.type),
                success_visible:!!document.querySelector('[data-order-success],.order-success')
            })""")
            report["checkout"].update(result)
            report["checkout"]["blocked_actions_delta"] = result["blocked_actions"]-before
            report["checkout"]["status"] = "PASS" if result["blocked_actions"] > before and result["view"] == "pay" and not result["success_visible"] else "FAIL"
            await page.screenshot(path=str(OUTDIR/"checkout-after.png"), full_page=True, animations="disabled")
            check(report["checkout"]["status"] == "PASS", "DEMO_SLIDER_NO_BLOCKING_PROOF")

            # Visual / copy / fee checks on the genuine DOM, no design changes.
            report["visual"] = await page.evaluate("""() => {
                const root=document.querySelector('.d67-checkout');
                const text=root?root.innerText:'';
                const hasMethod=text.includes('Cash')||text.includes('Наличн');
                const imgs=[...document.images].map(i=>({
                    src:i.getAttribute('src')||'',width:i.naturalWidth,height:i.naturalHeight,
                    visible:!!(i.getBoundingClientRect().width&&i.getBoundingClientRect().height)
                }));
                return {
                    visible_delivery_amount:text.includes('12') || text.includes('Delivery'),
                    money_39:text.includes('39'),
                    fee_text_excerpt:text.slice(-950),
                    cash_option:hasMethod,
                    broken_image_paths:imgs.filter(i=>i.visible&&!i.width).slice(0,18),
                    doc_overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,
                    footer:!!document.querySelector('.d68-pay-dock'),
                };
            }""")
            check(len(report["network"]["blocked"]) == 1 and not report["network"]["websockets"],
                  "EXTERNAL_TRANSPORT_DURING_SLIDER")
            # Persist synthetic screenshot only; raw banner colours and business rules are unchanged.
        finally:
            if ctx is not None:
                await ctx.close()  # HAR finalized even if one assertion fails.
            await browser.close()
            path = OUTDIR/"local-raw.har"
            if path.exists():
                sanitize_har(path)
    check(not report["network"]["pageerrors"], "BROWSER_PAGE_ERRORS")
    # Inspect all observed request events for any external destination other than the deliberate test.
    external = [r for r in report["network"]["requests"]
                if not r.startswith(HOST+"/") and not r.startswith("qa-stage22-denied.invalid/")]
    check(not external, "UNEXPECTED_EXTERNAL_REQUEST_EVENTS")
    check(len(report["network"]["blocked"]) == 1, "EXTERNAL_ATTEMPT_OBSERVED")
    check(report["har"]["entry_count"] > 0, "EMPTY_REAL_HAR")
    report["status"] = "PASS_GUARDED_SYNTHETIC_SCOPE"

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        report["status"] = "FAIL_CLOSED_NO_GO: " + str(e)[:240]
        log()
        raise
    else:
        log()
