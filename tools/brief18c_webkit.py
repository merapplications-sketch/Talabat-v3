#!/usr/bin/env python3
"""TALABOT BRIEF-18c M-01: original-app checkout WebKit, read-only offline QA.
All Leaflet resources and OSM tiles are fulfilled from pinned/local bytes in CI.
No remote browser network, real customer data, checkout writes or SQL.
"""
import json
import math
import os
import pathlib
import struct
import sys
import zlib
from playwright.sync_api import sync_playwright
from full_audit import ROOT, LOCAL, start_server, make_context

MODE = os.environ.get("BRIEF18C_MODE", "after")
assert MODE in ("before", "after")
OUT = ROOT / "qa-shots" / "unified-fix" / "brief18c" / MODE
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORTS = (("ru", 375, 667), ("en", 390, 844),
             ("ru", 320, 700), ("en", 320, 700))
STATES = ("coordinates", "no_coordinates", "tile_failure")
LEAFLET_JS = pathlib.Path(os.environ.get("BRIEF18C_LEAFLET_JS", "/nonexistent"))
LEAFLET_CSS = pathlib.Path(os.environ.get("BRIEF18C_LEAFLET_CSS", "/nonexistent"))
CASES = []
ERRORS = []


def fixed_png_tile():
    """Generate one deterministic pale road/park PNG tile; no external tile provider."""
    n = 256
    rows = []
    for y in range(n):
        row = bytearray(b"\0")
        for x in range(n):
            color = (237, 240, 235)
            if 18 <= x <= 62 and 16 <= y <= 68:
                color = (211, 228, 206)
            if 189 <= x <= 241 and 174 <= y <= 239:
                color = (212, 223, 206)
            if abs((x - 125) - 0.16 * (y - 128)) < 8 or abs(y - 94 + 0.11 * (x - 128)) < 7:
                color = (255, 255, 255)
            if 93 < x < 144 and 113 < y < 171:
                color = (226, 229, 220)
            row.extend(color)
        rows.append(bytes(row))
    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data +
                struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(b"".join(rows), level=9)) +
            chunk(b"IEND", b""))


TILE = fixed_png_tile()


def make_offline_context(browser, lang, width, height, state, network):
    ctx = make_context(browser, "customer", lang, width, height)
    if LEAFLET_JS.is_file() and LEAFLET_CSS.is_file():
        js = LEAFLET_JS.read_bytes()
        css = LEAFLET_CSS.read_bytes()
        ctx.route("https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js",
                  lambda route: route.fulfill(status=200, content_type="application/javascript", body=js))
        ctx.route("https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css",
                  lambda route: route.fulfill(status=200, content_type="text/css", body=css))
    def tile(route):
        network["tiles"] += 1
        if state == "tile_failure":
            network["failed"] += 1
            route.abort("failed")
        else:
            network["local"] += 1
            route.fulfill(status=200, content_type="image/png", body=TILE)
    ctx.route("https://tile.openstreetmap.org/**", tile)
    return ctx


def seed(page, state):
    if state == "no_coordinates":
        page.evaluate("""() => {
          const old=TLB.addresses.bind(TLB);
          TLB.addresses=()=>old().map(a=>({...a,lat:null,lng:null}));
        }""")
    page.evaluate("""() => {
      S.sh=null;S.cart={i2:2,['i1~o11']:1};S.cartStore=STORES[0].n;
      S.tip=10;S.usePts=false;S.useWallet=false;S.door=false;S.promo=null;
      go('cart');go('pay');
    }""")
    page.locator(".d67-checkout .card").first.wait_for(state="visible", timeout=6000)
    page.wait_for_timeout(150)


def financial(page):
    return page.evaluate("""() => {
      const c=calc();
      return {total:c.total,sub:c.sub,discount:c.d,happyHour:c.h,promo:c.p,
        pointsValue:c.pv,fee:c.fee,tip:S.tip,
        saved:Math.round((c.d+c.h+c.p+c.pv)*100)/100,due:c.due,wallet:c.w};
    }""")


def screenshot(page, state, lang, width, part="main"):
    dst = OUT / f"M-01-{state}-{lang}-{width}-{part}-{MODE}.png"
    page.screenshot(path=str(dst), animations="disabled", timeout=18000)
    assert dst.is_file() and dst.stat().st_size > 2500
    assert dst.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    return str(dst.relative_to(ROOT))


def inspect(page, state):
    if state != "no_coordinates":
        page.wait_for_function("""() =>
          !!document.getElementById('m01-pay-preview')&&
          typeof M01!=='undefined'&&!!M01.map&&!!M01.map.getCenter()
        """, timeout=11000)
    result = page.evaluate("""state => {
      const shell=document.getElementById('m01-pay-preview'),
        card=document.querySelector('.d67-checkout .card'),
        pin=shell?.querySelector('.m01-pin'),
        attr=shell?.querySelector('.m01-osm'),
        box=e=>e?.getBoundingClientRect(),s=box(shell),c=box(card),p=box(pin),
        current=typeof M01!=='undefined'?M01.map:null,
        leaflets=document.querySelectorAll('.d67-checkout .leaflet-container').length,
        center=current?.getCenter(),coord=shell?[+shell.dataset.lat,+shell.dataset.lng]:null,
        pixelGap=current&&coord?current.project(center,current.getZoom()).distanceTo(
          current.project(coord,current.getZoom())):null,
        dx=p&&s?Math.abs((p.left+p.right)/2-(s.left+s.right)/2):null,
        dy=p&&s?Math.abs((p.top+p.bottom)/2-(s.top+s.bottom)/2):null,
        stationary=!!current&&!current.dragging.enabled()&&!current.scrollWheelZoom.enabled()&&
          !current.doubleClickZoom.enabled()&&!current.touchZoom.enabled()&&
          !current.boxZoom.enabled()&&!current.keyboard.enabled(),
        change=[...card.querySelectorAll('button')].find(b=>
          b.textContent.includes(TLB.t('addrChange'))||b.textContent.includes(TLB.t('addrAdd')));
      const common={pageFit:document.documentElement.scrollWidth<=document.documentElement.clientWidth+1,
        labels:!!change&&!!card&&card.innerText.includes(TLB.t('addrL')),
        cardHeight:c?.height,hasMap:!!shell,mapCount:leaflets,attr:attr?.innerText||'',
        width:s?.width,height:s?.height,pinDx:dx,pinDy:dy,
        addressText:card?.querySelector('.rg')?.innerText||'', coords:coord,
        center:center?[center.lat,center.lng]:null,pixelGap,stationary,
        bg:shell?getComputedStyle(shell).backgroundColor:null};
      if(state==='no_coordinates')return {...common,ok:!shell&&leaflets===0&&
        !card.classList.contains('m01-address-card')&&!!change&&common.pageFit&&common.labels};
      return {...common,ok:!!shell&&!!current&&leaflets===1&&stationary&&
        common.pageFit&&common.labels&&!!attr&&attr.innerText==='© OpenStreetMap'&&
        s.width>200&&Math.abs(s.height-130)<=2&&
        dx<=4&&dy<=4&&pixelGap<=1&&
        Math.abs(s.left-c.left)<=2&&Math.abs(s.right-c.right)<=2};
    }""", state)
    if state != "no_coordinates":
        page.evaluate("""() => {
          const shell=document.getElementById('m01-pay-preview');
          const box=shell.getBoundingClientRect();
          const x=(box.left+box.right)/2,y=(box.top+box.bottom)/2;
          const tile=shell.querySelector('.m01-tiles');
          for(const [type,dx,dy] of [
            ['pointerdown',0,0],['pointermove',45,28],['pointermove',76,38],
            ['pointerup',76,38]
          ])tile.dispatchEvent(new PointerEvent(type,{
            bubbles:true,cancelable:true,pointerId:1,isPrimary:true,
            clientX:x+dx,clientY:y+dy,buttons:type==='pointerup'?0:1
          }));
        }""")
        stable = page.evaluate("""initial => {
          const c=M01.map.getCenter();
          return Math.abs(c.lat-initial[0])<1e-10&&
                 Math.abs(c.lng-initial[1])<1e-10;
        }""", result["center"])
        result["dragUnchanged"] = stable
        result["ok"] = result["ok"] and stable
    return result


def inspect_edit_and_dispose(page):
    page.locator("#m01-pay-preview").click(timeout=5000)
    page.wait_for_function("() => S.sheetAddr===true", timeout=3000)
    clicked = page.evaluate("""() => S.v==='pay'&&S.sheetAddr===true&&
      !!document.querySelector('#asheet')""")
    page.evaluate("() => closeSheet()")
    page.wait_for_function("() => !S.sheetAddr&&!!document.getElementById('m01-pay-preview')",
                           timeout=3000)
    page.evaluate("() => go('cart')")
    gone = page.evaluate("""() => S.v==='cart'&&!document.getElementById('m01-pay-preview')&&
      !M01.map&&!M01.observer&&!M01.scrollCheck&&
      !document.querySelector('.d67-checkout .leaflet-container')""")
    return {"editUnchanged":clicked,"mapDisposed":gone,"ok":clicked and gone}


def main():
    server = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(headless=True)
            for lang, width, height in VIEWPORTS:
                for state in STATES:
                    row = {"id":"M-01","lang":lang,"width":width,"state":state,
                           "mode":MODE}
                    ctx=page=None
                    pageerrors=[]
                    network={"tiles":0,"local":0,"failed":0}
                    try:
                        ctx=make_offline_context(browser,lang,width,height,state,network)
                        page=ctx.new_page()
                        page.on("pageerror",lambda e:pageerrors.append(str(e)[:350]))
                        page.goto(LOCAL+"/customer.html",wait_until="domcontentloaded",timeout=20000)
                        page.wait_for_timeout(750)
                        seed(page,state)
                        row["financial"]=financial(page)
                        if MODE=="after":
                            row["result"]=inspect(page,state)
                            row["network"]=dict(network)
                            if state=="coordinates":
                                row["result"]["localTiles"]=network["local"]>0
                                row["result"]["ok"] = row["result"]["ok"] and network["local"]>0
                            if state=="no_coordinates":
                                row["result"]["noTileRequests"]=network["tiles"]==0
                                row["result"]["ok"] = row["result"]["ok"] and network["tiles"]==0
                            if state=="tile_failure":
                                row["result"]["failedTiles"]=network["failed"]>0
                                row["result"]["ok"] = row["result"]["ok"] and network["failed"]>0
                        else:
                            row["status"]="REFERENCE"
                        row["screenshot"]=screenshot(page,state,lang,width)
                        if MODE=="after":
                            if state!="no_coordinates":
                                row["lifecycle"]=inspect_edit_and_dispose(page)
                                row["result"]["ok"] = row["result"]["ok"] and row["lifecycle"]["ok"]
                            row["status"]="PASS" if row["result"]["ok"] and not pageerrors else "FAIL"
                            if row["status"]=="FAIL":
                                raise AssertionError(json.dumps({"result":row["result"],
                                   "errors":pageerrors,"network":network},ensure_ascii=False)[:1800])
                        row["pageerrors"]=pageerrors
                    except Exception as exc:
                        row["status"]="BEFORE_LIMITATION" if MODE=="before" else "FAIL"
                        row["error"]=str(exc)[:1800]
                        if MODE=="after":
                            ERRORS.append({k:row.get(k) for k in ("id","state","lang","width","error")})
                    finally:
                        if page and "screenshot" not in row:
                            try:row["screenshot"]=screenshot(page,state,lang,width)
                            except Exception:pass
                        CASES.append(row)
                        if ctx:ctx.close()
            browser.close()
    finally:server.shutdown()
    report={"mode":MODE,"browser":"Linux WebKit; original TALABOT customer app; offline read-only fixture",
      "tiles":"locally generated fixed PNG; browser remote requests intercepted",
      "source":"ef69571a" if MODE=="before" else "BRIEF-18c isolated branch",
      "cases":CASES,"errors":ERRORS}
    (OUT/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    lines=[f"# TALABOT BRIEF-18c M-01 {MODE.upper()}","",
      "Original customer HTML in Linux WebKit. Leaflet 1.9.4 and OSM tile responses are LOCAL.",
      "No live app, native Safari, payment placement, API writes or production.",""]
    for r in CASES:
        name=pathlib.Path(r.get("screenshot","")).name
        lines.append(f"- {r['state']} {r['lang']}/{r['width']}: {r['status']} [{name}]({name})")
    (OUT/"INDEX.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    passed=sum(r["status"]=="PASS" for r in CASES)
    print("BRIEF18C_WEBKIT",MODE,"CASES",len(CASES),"PASS",passed,"ERRORS",len(ERRORS),flush=True)
    for e in ERRORS:
        print("BRIEF18C_FAIL",json.dumps(e,ensure_ascii=False),flush=True)
    return 1 if MODE=="after" and ERRORS else 0


if __name__=="__main__":
    sys.exit(main())
