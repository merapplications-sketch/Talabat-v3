#!/usr/bin/env python3
"""TALABOT BRIEF-18d — source-backed WebKit, pre-preview A-01/A-02.
Original customer HTML, offline synthetic Supabase, LOCAL Leaflet/OSM fixture.
No real order, external network, production SQL or deployment.
"""
import json
import math
import os
import pathlib
import sys
from playwright.sync_api import sync_playwright
from full_audit import ROOT, LOCAL, start_server
from brief18c_webkit import make_offline_context

MODE=os.environ.get("BRIEF18D_MODE","after")
assert MODE in ("after","before")
OUT=ROOT/"qa-shots"/"unified-fix"/"brief18d"/MODE
OUT.mkdir(parents=True,exist_ok=True)
VIEWPORTS=(("ru",375,667),("en",390,844),("ru",320,700),("en",320,700))
SERVER_STATES=("unready","ready")
CASES=[]
ERRORS=[]

def snapshot(page,lang,width,state,suffix="pay"):
    p=OUT/f"{state}-{lang}-{width}-{suffix}-{MODE}.png"
    page.screenshot(path=str(p),animations="disabled",timeout=20000)
    assert p.stat().st_size>2500 and p.read_bytes()[:8]==b"\x89PNG\r\n\x1a\n",p
    return str(p.relative_to(ROOT))

def seed(page,state):
    page.evaluate("""ready => {
      window.__u18ReadyChecks=0;const supported=ready==='ready';
      TLB.deliveryInstructionsReady=async ()=>{
        window.__u18ReadyChecks++;
        return supported;
      };
      const a=curAddr(),m=TLB.me();
      if(!a||!m)throw Error('Missing source address fixture');
      localStorage.setItem('tlb-u18-delivery-'+m.id+'-'+a.id,
        JSON.stringify({keys:['door','call','knock']}));
      S.u18Address=null;S.u18Choices=[];S.u18Remember=false;
      S.sh=null;S.cart={i2:2,['i1~o11']:1};S.cartStore=STORES[0].n;
      S.tip=10;S.usePts=false;S.useWallet=false;S.door=false;S.promo=null;
      go('cart');go('pay');
    }""",state)
    page.locator(".u18-courier").wait_for(state="visible",timeout=5000)
    if MODE=="after":
        page.wait_for_function("""() => U18_SERVER.status==='ready'||U18_SERVER.status==='unready'""",timeout=5000)
    page.wait_for_timeout(110)

def financial(page):
    return page.evaluate("""() => {
      const c=calc();
      return {total:c.total,sub:c.sub,discount:c.d,happyHour:c.h,
        promo:c.p,pointsValue:c.pv,fee:c.fee,tip:S.tip,
        saved:Math.round((c.d+c.h+c.p+c.pv)*100)/100,
        due:c.due,wallet:c.w};
    }""")

def inspect(page,state,lang,width):
    return page.evaluate("""state=>{
      const card=document.querySelector('.d67-checkout .m01-address-card'),
        heading=card?.querySelector('.a01-heading'),
        title=card?.querySelector('.a01-title'),
        change=card?.querySelector('.a01-change'),
        addr=card?.querySelector('.a01-address-line'),
        content=card?.querySelector('.a01-address-content'),
        box=x=>x?.getBoundingClientRect(),
        c=box(content),h=box(heading),a=box(addr),b=box(change),t=box(title),
        css=addr&&getComputedStyle(addr),
        lh=css?parseFloat(css.lineHeight):0,
        rows=a&&lh?Math.ceil((a.height-0.5)/lh):999,
        changeCss=change&&getComputedStyle(change),
        color=changeCss?.color||'',
        label=TLB.t('addrChange'),
        chips=[...document.querySelectorAll('.u18-instruction-chip')],
        keys=chips.map(x=>x.dataset.u18Key),
        available=state==='ready',
        uiValid=available?keys.length===6:
          keys.length===1&&keys[0]==='door',
        extras=(typeof u18Keys==='function')?u18Keys().filter(x=>x!=='door'):[],
        status=typeof U18_SERVER!=='undefined'?U18_SERVER.status:'old',
        checkCalls=window.__u18ReadyChecks;
      const geometry={linkText:change?.innerText,linkFont:parseFloat(changeCss?.fontSize||'0'),
        linkColor:color,linkHeight:b?.height||0,
        headingHeight:h?.height||0,headingText:title?.innerText,
        addressText:addr?.innerText,lines:rows,lineHeight:lh,
        contentWidth:c?.width||0,addrWidth:a?.width||0,cardWidth:box(card)?.width||0,
        addressHeight:a?.height||0,linkSameRow:!!h&&!!b&&
          b.top>=h.top-1&&b.bottom<=h.bottom+1,
        noOverlap:!!a&&!!h&&a.top>=h.bottom-1&&
          !!b&&!!t&&t.right<=b.left+1,
        pageFit:document.documentElement.scrollWidth<=document.documentElement.clientWidth+1};
      const geometryOk=!!card&&!!content&&!!change&&!!addr&&
        geometry.linkText===label&&Math.abs(geometry.linkFont-14)<0.1&&
        color===getComputedStyle(card.querySelector('.a01-icon')).color&&
        geometry.linkSameRow&&geometry.noOverlap&&
        geometry.contentWidth>=geometry.cardWidth-34&&
        geometry.addrWidth>=geometry.contentWidth-1&&
        geometry.pageFit&&(innerWidth!==375||rows<=3);
      const readinessOk=uiValid&&checkCalls===1&&
        (available?status==='ready'&&extras.includes('call')&&extras.includes('knock'):
          status==='unready'&&extras.length===0)&&S.door===true;
      return {ok:geometryOk&&readinessOk,geometry,geometryOk,
        readinessOk,keys,extras,status,checkCalls,remembered:S.u18Choices,
        selectedDoor:S.door};
    }""",state)

def check_edit(page):
    page.locator('.a01-change').click()
    sheet=page.evaluate("""() => S.sheetAddr===true&&S.v==='pay'&&!!document.querySelector('#asheet')""")
    page.evaluate("() => closeSheet()")
    return sheet and page.evaluate("() => S.sheetAddr===false&&S.v==='pay'")

def simulate_order(page,state):
    return page.evaluate("""async state => {
      const checksBefore=window.__u18ReadyChecks;
      window.__calls=0;window.__saves=0;window.__alerts=[];
      const old=window.alert;
      window.alert=m=>window.__alerts.push(String(m));
      TLB.placeOrder=async payload=>{window.__calls++;window.__payload=payload;return {id:987654321};};
      TLB.saveDeliveryInstructions=async(id,keys)=>{
        window.__saves++;window.__savedKeys=keys;return {ok:true};
      };
      ensureQuote=async()=>({fee:10});
      try{await place();}
      catch(e){window.__alerts.push('THROWN: '+e.message);}
      finally{window.alert=old;}
      const ready=state==='ready';
      return {ok:window.__calls===1&&window.__alerts.length===0&&
        window.__u18ReadyChecks===checksBefore&&
        (ready?window.__saves===1&&window.__savedKeys.includes('call'):
          window.__saves===0),
        calls:window.__calls,saveCalls:window.__saves,
        savedKeys:window.__savedKeys||[],readinessChecks:window.__u18ReadyChecks,
        alerts:window.__alerts,hasPayload:!!window.__payload};
    }""",state)

def main():
    server=start_server()
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(headless=True)
            for lang,width,height in VIEWPORTS:
                for state in SERVER_STATES:
                    ctx=page=None
                    row={"id":"BRIEF18d","lang":lang,"width":width,"state":state,"mode":MODE}
                    js_errors=[]
                    network={"tiles":0,"local":0,"failed":0}
                    try:
                        ctx=make_offline_context(browser,lang,width,height,"coordinates",network)
                        page=ctx.new_page()
                        page.on("pageerror",lambda e:js_errors.append(str(e)[:300]))
                        page.clock.install(time="2026-11-17T14:00:00Z")
                        page.goto(LOCAL+"/customer.html",wait_until="domcontentloaded",timeout=20000)
                        page.wait_for_timeout(700)
                        seed(page,state)
                        row["financial"]=financial(page)
                        row["screenshot"]=snapshot(page,lang,width,state)
                        if MODE=="after":
                            result=inspect(page,state,lang,width)
                            row["result"]=result
                            row["editUnchanged"]=check_edit(page)
                            row["fakeOrder"]=simulate_order(page,state)
                            row["status"]="PASS" if (result["ok"] and row["editUnchanged"] and
                                row["fakeOrder"]["ok"] and not js_errors) else "FAIL"
                            if row["status"]=="FAIL":raise AssertionError(json.dumps(
                                {"result":result,"editUnchanged":row["editUnchanged"],
                                 "fakeOrder":row["fakeOrder"],"pageerrors":js_errors},
                                ensure_ascii=False)[:1900])
                        else:
                            row["status"]="REFERENCE"
                        row["pageerrors"]=js_errors
                    except Exception as exc:
                        row["status"]="BEFORE_LIMITATION" if MODE=="before" else "FAIL"
                        row["error"]=str(exc)[:1900]
                        if MODE=="after":ERRORS.append({k:row.get(k) for k in ("state","lang","width","error")})
                    finally:
                        if page and "screenshot" not in row:
                            try:row["screenshot"]=snapshot(page,lang,width,state)
                            except Exception:pass
                        if ctx:ctx.close()
                        CASES.append(row)
            browser.close()
    finally:server.shutdown()
    report={"mode":MODE,"source":"8a416e67" if MODE=="before" else "BRIEF18d candidate",
            "browser":"Linux WebKit original TALABOT customer; synthetic local fixture; NO live order",
            "network":"Leaflet 1.9.4 and generated offline tiles via BRIEF18c fixture",
            "cases":CASES,"errors":ERRORS}
    (OUT/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    rows=["# TALABOT BRIEF-18d "+MODE.upper(),"",
          "Original app and source WebKit; local-only tiles, no production, no SQL or live orders.",""]
    for r in CASES:
        name=pathlib.Path(r.get("screenshot","")).name
        rows.append(f"- {r['state']} {r['lang']}/{r['width']}: {r['status']} [{name}]({name})")
    (OUT/"INDEX.md").write_text("\n".join(rows)+"\n",encoding="utf8")
    good=sum(x["status"]=="PASS" for x in CASES)
    print("BRIEF18D_WEBKIT",MODE,"CASES",len(CASES),"PASS",good,"FAIL",len(ERRORS),flush=True)
    for e in ERRORS:
        print("BRIEF18D_FAIL",json.dumps(e,ensure_ascii=False),flush=True)
    return 1 if MODE=="after" and ERRORS else 0

if __name__=="__main__":
    sys.exit(main())
