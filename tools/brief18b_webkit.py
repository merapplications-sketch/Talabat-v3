#!/usr/bin/env python3
"""BRIEF-18b: original TALABOT HTML with offline read-only Supabase adapter in Linux WebKit.
The before source is pinned to 70dfaf9a. No live data, checkout submission, SQL or deployment.
"""
import json
import os
import pathlib
import sys
from playwright.sync_api import sync_playwright
from full_audit import ROOT, LOCAL, start_server, make_context

MODE = os.environ.get("BRIEF18B_MODE", "after")
assert MODE in ("before", "after")
OUT = ROOT / "qa-shots" / "unified-fix" / "brief18b" / MODE
OUT.mkdir(parents=True, exist_ok=True)
PORTS = (("ru", 375, 667), ("en", 390, 844), ("ru", 320, 700), ("en", 320, 700))
CASES = (("P-01", "merchant"), ("P-02", "customer"),
         ("P-03", "driver"), ("P-04", "customer"))
ROWS = []
ERRORS = []


def shot(page, case, lang, width, kind="main"):
    p = OUT / f"{case}-{lang}-{width}-{kind}-{MODE}.png"
    page.screenshot(path=str(p), animations="disabled", timeout=20000)
    if p.stat().st_size < 2000 or p.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"Bad screenshot {p}")
    return str(p.relative_to(ROOT))


def finance(page):
    return page.evaluate("""() => {
      const c=calc();
      return {total:c.total,sub:c.sub,discount:c.d,happyHour:c.h,
        promo:c.p,pointsValue:c.pv,fee:c.fee,tip:S.tip,
        saved:Math.round((c.d+c.h+c.p+c.pv)*100)/100,due:c.due,wallet:c.w};
    }""")


def prep(page, case):
    if case == "P-01":
        page.evaluate("() => {setTab('m');openSheet('i1')}")
        page.locator(".u18-merchant-option").first.scroll_into_view_if_needed(timeout=5000)
    elif case == "P-02":
        page.evaluate("() => {go('menu',{store:STORES[0].n});openItem('i1')}")
        page.locator("#shT").wait_for(state="visible", timeout=5000)
    elif case == "P-03":
        page.evaluate("""() => {
          const o=mine();
          if(o){o.status='pickedup';o.arrivedCustAt=Date.now();}
          render();
        }""")
        page.locator(".a-tools").wait_for(state="visible", timeout=5000)
    elif case == "P-04":
        page.evaluate("""() => {
          S.sh=null;S.cart={i2:2,['i1~o11']:1};S.cartStore=STORES[0].n;
          S.tip=10;S.usePts=false;S.useWallet=false;S.door=false;S.promo=null;
          go('cart');go('pay');
        }""")
        page.locator(".d69-slide-label").wait_for(state="visible", timeout=5000)
    page.wait_for_timeout(150)


def check(page, case, lang, width):
    if case == "P-01":
        return page.evaluate("""() => {
          const rows=[...document.querySelectorAll('.u18-merchant-option')];
          const row=rows.find(x=>x.querySelector('.u18-option-name')?.value==='Маленький')||rows[0];
          const n=row?.querySelector('.u18-option-name'),p=row?.querySelector('input[type="number"]'),
            sw=row?.querySelector('.sw'),del=row?.querySelector('.rb'),
            box=e=>e?.getBoundingClientRect(),b=box(n),pb=box(p),sb=box(sw),db=box(del),
            css=n&&getComputedStyle(n),line=css?parseFloat(css.lineHeight):0,
            top=css?parseFloat(css.borderTopWidth)+parseFloat(css.paddingTop):0,
            textCenter=b?b.top+top+line/2:0,
            rowCenter=pb?(pb.top+pb.bottom)/2:0,
            diff=Math.abs(textCenter-rowCenter),
            button=[...document.querySelectorAll('.f06-item-editor button')].find(e=>
              e.textContent.trim()==='+ '+TLB.t('optAdd')),
            expected=TLB.lang()==='ru'?'Добавить вариант':'Add variant',
            unclipped=rows.every(r=>{const a=r.querySelector('.u18-option-name');return
              a && a.scrollHeight<=a.clientHeight+3 && a.scrollWidth<=a.clientWidth+1;});
          return {ok:!!n&&!!p&&!!sw&&!!del&&!!button&&
            TLB.t('optAdd')===expected&&diff<=2&&unclipped&&
            b.right<=pb.left+3&&pb.right<=sb.left+3&&sb.right<=db.left+3,
            textCenter,rowCenter,diff,unclipped,button:button?.textContent.trim(),
            text:n?.value,nameHeight:b?.height,priceHeight:pb?.height,
            names:rows.map(r=>r.querySelector('.u18-option-name')?.value)};
        }""")
    if case == "P-02":
        return page.evaluate("""() => {
          const h=document.querySelector('#shT'),c=document.querySelector('.d6s .oshf .btn span:first-child'),
            price=document.querySelector('.d6s .oshf .btn .px6'),
            st=h&&getComputedStyle(h),a=h?.getBoundingClientRect(),b=c?.getBoundingClientRect(),
            p=price?.getBoundingClientRect(),cs=c&&getComputedStyle(c),
            range=document.createRange();if(c)range.selectNodeContents(c);
          const lines=c?[...range.getClientRects()]:[],
            lh=cs?parseFloat(cs.lineHeight):0,actual=Math.max(0,...lines.map(x=>x.height));
          return {ok:!!h&&!!c&&!!price&&
            st.webkitLineClamp==='none'&&st.overflow==='visible'&&
            h.scrollHeight<=h.clientHeight+2&&h.scrollWidth<=h.clientWidth+1&&
            a.height>=parseFloat(st.lineHeight)*2&&
            lines.length===1&&actual<=lh+2&&
            c.scrollWidth<=c.clientWidth+1&&b.right<=p.left+2,
            title:h?.innerText,clamp:st?.webkitLineClamp,titleHeight:a?.height,
            titleScrollHeight:h?.scrollHeight,titleClientHeight:h?.clientHeight,
            cta:c?.innerText,lines:lines.length,lineHeight:lh,textHeight:actual,
            ctaScrollWidth:c?.scrollWidth,ctaClientWidth:c?.clientWidth,
            ctaRight:b?.right,priceLeft:p?.left};
        }""")
    if case == "P-03":
        return page.evaluate("""() => {
          const miss=document.querySelector('.a-tools .a-contact-missing'),
            link=document.querySelector('.a-tools .a-call[href^="tel:"]'),
            old=TLB.toast;let toast=null;
          TLB.toast=m=>{toast=m;};
          try{if(miss)miss.click();}finally{TLB.toast=old;}
          const reason=TLB.t('p18NoClientPhone');
          return {ok:!!miss&&!link&&miss.getAttribute('aria-disabled')==='true'&&
            toast===reason&&miss.getAttribute('title')===reason,
            missing:!!miss,customerTelephoneLink:!!link,toast,reason,
            ariaDisabled:miss?.getAttribute('aria-disabled'),
            foreground:miss&&getComputedStyle(miss).color};
        }""")
    if case == "P-04":
        return page.evaluate("""() => {
          const slider=document.querySelector('.d69-slide-label'),
            now=[...document.querySelectorAll('.p1-schedule .tipr button')]
              .find(b=>b.innerText.includes(TLB.t('whenNow')));
          const line=e=>{
            if(!e)return {ok:false};
            const range=document.createRange();range.selectNodeContents(e);
            const cs=getComputedStyle(e),rects=[...range.getClientRects()],
              height=Math.max(0,...rects.map(r=>r.height)),lh=parseFloat(cs.lineHeight);
            return {ok:rects.length===1&&height<=lh+2&&e.scrollWidth<=e.clientWidth+1,
              text:e.innerText,rectCount:rects.length,height,lineHeight:lh,
              scrollWidth:e.scrollWidth,clientWidth:e.clientWidth};
          };
          const a=line(slider),b=line(now);
          return {ok:a.ok&&b.ok,slider:a,whenNow:b};
        }""")
    raise AssertionError(f"Unsupported case {case}")


def main():
    server = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.webkit.launch(headless=True)
            for lang, width, height in PORTS:
                for case, app in CASES:
                    row = {"id":case,"app":app,"lang":lang,"width":width,"mode":MODE}
                    ctx = page = None
                    js_errors = []
                    try:
                        ctx = make_context(browser, app, lang, width, height)
                        page = ctx.new_page()
                        page.on("pageerror",lambda e:js_errors.append(str(e)[:250]))
                        page.goto(LOCAL + "/" + app + ".html",
                                  wait_until="domcontentloaded",timeout=20000)
                        page.wait_for_timeout(700)
                        prep(page,case)
                        if case == "P-04":
                            row["financial"] = finance(page)
                        if case == "P-03":
                            row["missingScreenshot"] = shot(page,case,lang,width,"missing")
                        if case == "P-04":
                            page.locator(".p1-schedule").scroll_into_view_if_needed(timeout=4000)
                            row["scheduleScreenshot"] = shot(page,case,lang,width,"schedule")
                            page.locator(".d69-slide-label").scroll_into_view_if_needed(timeout=4000)
                        if MODE == "after":
                            row["geometry"] = check(page,case,lang,width)
                            row["status"] = "PASS" if row["geometry"].get("ok") and not js_errors else "FAIL"
                        else:
                            row["status"] = "REFERENCE"
                        if case == "P-03":
                            page.evaluate("""() => {
                              const o=mine();if(o&&o.client)o.client.phone='+992900001111';
                              render();
                            }""")
                            page.wait_for_timeout(80)
                            row["availablePhone"] = page.evaluate("""() => {
                              const a=document.querySelector('.a-tools .a-call[href^="tel:"]');
                              return {ok:!!a&&a.getAttribute('href')==='tel:+992900001111',
                                href:a?.getAttribute('href'),source:'synthetic in-memory authorized order'};
                            }""")
                            row["availableScreenshot"] = shot(page,case,lang,width,"available")
                            if MODE=="after" and not row["availablePhone"]["ok"]:
                                row["status"]="FAIL"
                        row["screenshot"]=shot(page,case,lang,width)
                        row["js_errors"]=js_errors
                        if row["status"]=="FAIL":
                            raise AssertionError(json.dumps(row.get("geometry") or row.get("availablePhone"),
                                                            ensure_ascii=False)[:1400])
                    except Exception as exc:
                        row["status"]="FAIL" if MODE=="after" else "BEFORE_LIMITATION"
                        row["error"]=str(exc)[:1300]
                        if MODE=="after":
                            ERRORS.append({k:row.get(k) for k in ("id","app","lang","width","error")})
                    finally:
                        if page and "screenshot" not in row:
                            try: row["screenshot"]=shot(page,case,lang,width)
                            except Exception: pass
                        ROWS.append(row)
                        if ctx:ctx.close()
            browser.close()
    finally:
        server.shutdown()
    report={"mode":MODE,"browser":"Linux WebKit original TALABOT UI; synthetic read-only adapter; NOT live iPhone",
            "source":"70dfaf9a" if MODE=="before" else "BRIEF-18b isolated review",
            "cases":ROWS,"errors":ERRORS}
    (OUT/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# TALABOT BRIEF-18b "+MODE.upper(),"",
           "Original app rendered in Linux WebKit; offline synthetic fixture, not production or physical iPhone.",""]
    for row in ROWS:
        name=pathlib.Path(row.get("screenshot","")).name
        lines.append(f"- {row['id']} {row['app']} {row['lang']}/{row['width']}: "
                     f"{row['status']} [{name}]({name})")
        for field in ("missingScreenshot","availableScreenshot","scheduleScreenshot"):
            if row.get(field):
                path=pathlib.Path(row[field]).name
                lines.append(f"  - {field}: [{path}]({path})")
    (OUT/"INDEX.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    passed=sum(r["status"]=="PASS" for r in ROWS)
    print("BRIEF18B_WEBKIT",MODE,"CASES",len(ROWS),"PASS",passed,"ERRORS",len(ERRORS),flush=True)
    for e in ERRORS:
        print("BRIEF18B_FAIL",json.dumps(e,ensure_ascii=False),flush=True)
    return bool(MODE=="after" and ERRORS)


if __name__=="__main__":
    sys.exit(main())
