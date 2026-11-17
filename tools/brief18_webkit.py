#!/usr/bin/env python3
"""TALABOT BRIEF-18 — original source WebKit, synthetic read-only QA adapter.
Reference snapshots are pinned to f7d961ec; not a native iPhone or production test.
Never place an order, write to a real API, or run a migration.
"""
import os,sys,json,pathlib,traceback
from playwright.sync_api import sync_playwright
from full_audit import ROOT,LOCAL,start_server,make_context

MODE=os.environ.get("BRIEF18_MODE","after")
assert MODE in ("before","after")
OUT=ROOT/"qa-shots"/"unified-fix"/"brief18"/MODE
OUT.mkdir(parents=True,exist_ok=True)
VIEWPORTS=(("ru",375,667),("en",390,844),("ru",320,700),("en",320,700))
CASES=(("U-01","customer"),("U-02","customer"),("U-03","customer"),
       ("U-04","customer"),("U-05","merchant"),("U-06","customer"),
       ("U-02-driver","driver"))
rows=[];errors=[]

def shot(pg,key,lang,w,part="main"):
    dst=OUT/f"{key}-{lang}-{w}-{part}-{MODE}.png"
    pg.screenshot(path=str(dst),animations="disabled",timeout=16000)
    if dst.stat().st_size<2000 or dst.read_bytes()[:8]!=b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"Invalid evidence PNG {dst.name}")
    return str(dst.relative_to(ROOT))

def rects(pg,selectors):
    return pg.evaluate("""sels=>sels.flatMap(s=>[...document.querySelectorAll(s)].slice(0,10).map(e=>{
       const r=e.getBoundingClientRect();return {selector:s,txt:(e.innerText||e.value||'').slice(0,55),
         left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,
         scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight};
    }))""",selectors)

def assert_result(pg,script):
    out=pg.evaluate(script)
    if not isinstance(out,dict):raise AssertionError("No inspectable DOM verification")
    return out

def seed_cart(pg):
    # Exactly the original F-05 seeded valid options fixture. Tip is explicitly 10.
    pg.evaluate("""() => {
      S.sh=null;S.cart={i2:2,['i1~o11']:1};S.cartStore=STORES[0].n;
      S.tip=10;S.usePts=false;S.useWallet=false;S.door=false;S.promo=null;
      go('cart');go('pay');
    }""")
    pg.wait_for_timeout(120)

def financial(pg):
    return pg.evaluate("""() => {
      const c=calc();
      const saved=Math.round((c.d+c.h+c.p+c.pv)*100)/100;
      return {total:c.total,sub:c.sub,discount:c.d,happyHour:c.h,
         promo:c.p,pointsValue:c.pv,fee:c.fee,tip:S.tip,
         saved,due:c.due,wallet:c.w};
    }""")

def prepare(pg,case,lang,w,h):
    if case=="U-01":
        pg.evaluate("""() => {go('menu',{store:STORES[0].n});openItem('i1')}""")
        pg.wait_for_timeout(100)
    elif case in ("U-02","U-03","U-04","U-06"):
        seed_cart(pg)
        if case=="U-02" and MODE=="after":
            pg.evaluate("""() => {
              S.door=true;S.u18Choices=['call','no_ring'];render();
            }""")
        if case=="U-06":
            pg.evaluate("""() => {
              const wallet=TLB.wallet.bind(TLB),loyalty=TLB.loyalty.bind(TLB);
              TLB.wallet=()=>Object.assign({},wallet()||{},{balance:100});
              TLB.loyalty=()=>Object.assign({},loyalty()||{},{
                points_per_tjs:10,balance:5000,min_redeem:10,
                voucher_points:10,min_order:0});
              S.usePts=true;S.useWallet=true;render();
            }""")
        pg.wait_for_timeout(120)
    elif case=="U-05":
        pg.evaluate("""() => {setTab('m');openSheet('i1')}""")
        pg.wait_for_timeout(120)
    elif case=="U-02-driver":
        pg.evaluate("""() => {
          const o=mine();if(o){o.status='pickedup';o.arrivedCustAt=Date.now()}
          if(window.TLB)TLB.getDeliveryInstructions=async ()=>({
            keys:['door','call','no_ring','knock']});
          render();
        }""")
        pg.wait_for_timeout(270)

def inspect(pg,case,lang,w):
    if case=="U-01":
        pg.locator(".d6s .og").first.scroll_into_view_if_needed(timeout=2400)
        r=assert_result(pg,"""() => {
          const g=document.querySelector('.d6s .u18-options'),
             rows=[...document.querySelectorAll('.d6s .u18-options-list .d6-ch')],
             hint=g?.querySelector('.u18-opt-hint'),
             radio=rows.find(x=>x.getAttribute('role')==='radio'),
             check=rows.find(x=>x.getAttribute('role')==='checkbox'),
             box=x=>x?.getBoundingClientRect();
          const flat=rows.every(row=>{const r=box(row),n=box(row.querySelector('.nm')),
            mark=box(row.querySelector('.mk')),price=box(row.querySelector('.pr'));
            return !!r&&!!n&&!!mark&&n.left>=r.left-2&&mark.right<=r.right+3&&
              (!price||n.right<=price.left+3)&&(!price||price.right<=mark.left+3)&&
              getComputedStyle(row).borderTopWidth==='0px'&&
              getComputedStyle(row).borderBottomWidth==='1px'&&
              getComputedStyle(row).borderRadius==='0px';
          });
          const band=document.querySelectorAll('.d6s .u18-options')[1];
          return {ok:!!g&&rows.length>=3&&!!hint&&hint.innerText.includes(TLB.t('u18ChooseOne'))&&
             !!radio&&!!check&&flat&&!!band&&getComputedStyle(band,'::before').height==='8px',
            count:rows.length,radio:!!radio,checkbox:!!check,flat,hint:hint?.innerText||''};
        }""")
        return r,[".d6s .u18-options",".d6s .u18-opt-hint",".d6s .d6-ch"]
    if case=="U-02":
        pg.locator(".u18-courier").scroll_into_view_if_needed(timeout=2400)
        r=assert_result(pg,"""() => {
          const e=document.querySelector('.u18-courier'),rail=e?.querySelector('.u18-instruction-rail'),
            choices=[...(rail?.querySelectorAll('.u18-instruction-chip')||[])],
            door=choices.find(x=>x.dataset.u18Key==='door'),
            other=choices.find(x=>x.dataset.u18Key==='call'),
            remember=e?.querySelector('.u18-remember input'),boxes=choices.map(x=>x.getBoundingClientRect()),
            horizontal=boxes.every((x,i)=>!i||x.left>=boxes[i-1].right-1),
            outer=rail?.getBoundingClientRect(),doorSelected=door?.getAttribute('aria-checked')==='true';
          return {ok:!!e&&choices.length===6&&!!remember&&!!rail&&horizontal&&doorSelected&&
             other?.getAttribute('aria-checked')==='true'&&
             getComputedStyle(rail).overflowX==='auto'&&outer.width>0&&
             choices.every(x=>x.innerText.trim().length>2)&&S.door===true,
             names:choices.map(x=>x.innerText),horizontal,doorSelected,remember:!!remember,
             scroll:rail?.scrollWidth||0,client:rail?.clientWidth||0};
        }""")
        # Screenshot the entire visible instruction panel rather than a bottom-edge partial heading.
        pg.evaluate("""() => {
          const card=document.querySelector('.u18-courier');
          if(card)window.scrollBy(0,card.getBoundingClientRect().top-105);
        }""")
        pg.wait_for_timeout(130)
        shot(pg,case,lang,w,"instructions")
        return r,[".u18-courier",".u18-instruction-rail",".u18-instruction-chip"]
    if case=="U-03":
        pg.locator(".u18-tip-card").scroll_into_view_if_needed(timeout=2400)
        r=assert_result(pg,"""() => {
          const card=document.querySelector('.u18-tip-card'),img=card?.querySelector('img'),
            tip=[...(card?.querySelectorAll('.tip')||[])],rect=img?.getBoundingClientRect();
          return {ok:!!card&&!!img&&img.getAttribute('src')==='assets/3d/motor-scooter-yellow.png'&&
            tip.length===4&&S.tip===10&&tip[2].classList.contains('on')&&
            rect.width>=45&&card.innerText.includes(TLB.t('u18TipDesc')),
            tip:tip.map(x=>x.innerText),selected:S.tip,image:img?.getAttribute('src')||'',
            imageWidth:rect?.width||0};
        }""")
        return r,[".u18-tip-card",".u18-tip-card img",".u18-tip-card .tip"]
    if case=="U-04":
        pg.locator(".d68-pay-dock .u18-saving").wait_for(state="visible",timeout=2800)
        pay=assert_result(pg,"""() => {
          const band=document.querySelector('.d68-pay-dock .u18-saving'),
            slider=document.querySelector('#hbtn'),dock=document.querySelector('.d68-pay-dock'),
            b=band?.getBoundingClientRect(),s=slider?.getBoundingClientRect();
          const saved=Math.round((calc().d+calc().h+calc().p+calc().pv)*100)/100;
          const overlap=b&&s&&Math.min(b.right,s.right)-Math.max(b.left,s.left)>1&&
            Math.min(b.bottom,s.bottom)-Math.max(b.top,s.top)>1;
          return {ok:!!band&&!!slider&&saved>0&&band.innerText.includes(saved.toFixed(2))&&
             band.querySelector('img')?.getAttribute('src')==='assets/3d/party-popper.webp'&&
             !document.querySelector('.d67-checkout .sv')&&!overlap&&b.bottom<=s.top,
            saved,overlap:!!overlap,bandBottom:b?.bottom||0,sliderTop:s?.top||0,
            dockPosition:dock&&getComputedStyle(dock).position};
        }""")
        shot(pg,case,lang,w,"pay")
        pg.evaluate("""() => go('cart')""")
        pg.wait_for_timeout(90)
        cart=assert_result(pg,"""() => {
          const band=document.querySelector('.d70-dock .u18-saving'),
            buttons=[...document.querySelectorAll('.d70-dock button')],b=band?.getBoundingClientRect(),
            first=buttons[0]?.getBoundingClientRect(),
            saved=Math.round((calc().d+calc().h+calc().p+calc().pv)*100)/100;
          return {ok:!!band&&saved>0&&band.innerText.includes(saved.toFixed(2))&&
              !!first&&b.bottom<=first.top&&buttons.length>=2,
              saved,bandBottom:b?.bottom||0,buttons:buttons.length,firstTop:first?.top||0};
        }""")
        shot(pg,case,lang,w,"cart")
        return {"ok":pay["ok"] and cart["ok"],"pay":pay,"cart":cart},[
          ".d70-dock .u18-saving",".d70-dock button"]
    if case=="U-05":
        pg.locator(".u18-merchant-option").first.scroll_into_view_if_needed(timeout=2800)
        r=assert_result(pg,"""() => {
          const rows=[...document.querySelectorAll('.u18-merchant-option')];
          const results=rows.map(row=>{
            const name=row.querySelector('textarea.u18-option-name'),
              price=row.querySelector('input[type=number]'),sw=row.querySelector('.sw'),
              del=row.querySelector('.rb'),box=x=>x?.getBoundingClientRect(),
              r=box(row),n=box(name),p=box(price),s=box(sw),d=box(del);
            return {name:name?.value||'',wrapped:!!name&&
               getComputedStyle(name).whiteSpace==='pre-wrap'&&
               name.scrollHeight<=name.clientHeight+3,
               order:!!n&&!!p&&!!s&&!!d&&n.right<=p.left+4&&
                 p.right<=s.left+4&&s.right<=d.left+4&&d.right<=r.right+4,
               sameRow:!!n&&!!p&&Math.abs((n.top+n.bottom)/2-(p.top+p.bottom)/2)<25};
          });
          const title=document.querySelector('.f15c-group-name'),
                th=title?.getBoundingClientRect()?.height||0;
          const correctTitle=!!title&&title.scrollHeight<=title.clientHeight+3&&
               th>=44&&th<=120&&getComputedStyle(title).whiteSpace==='pre-wrap';
          return {ok:correctTitle&&results.length>=2&&results.every(x=>x.wrapped&&x.order&&x.sameRow),
             rows:results,titleHeight:th,titleScroll: title?.scrollHeight||0,
             titleClient:title?.clientHeight||0,correctTitle};
        }""")
        return r,[".u18-merchant-option",".u18-option-name",".f15c-option-controls input",".f15c-group-name"]
    if case=="U-06":
        r=assert_result(pg,"""() => {
          const pts=document.querySelector('.d79-points-toggle.on'),
            wal=document.querySelector('.d76-wallet-toggle.on'),
            rgb=e=>e&&getComputedStyle(e).backgroundColor,
            ok=getComputedStyle(document.documentElement).getPropertyValue('--ok').trim(),
            sample=document.createElement('span');
          sample.style.background=ok;document.body.appendChild(sample);
          const color=rgb(sample);sample.remove();
          return {ok:!!pts&&!!wal&&rgb(pts)===color&&rgb(wal)===color,
            ptsColor:rgb(pts),walletColor:rgb(wal),expected:color,
            otherSwitches:[...document.querySelectorAll('.wsw.on:not(.d79-points-toggle):not(.d76-wallet-toggle)')].map(rgb)};
        }""")
        return r,[".d79-points-toggle",".d76-wallet-toggle"]
    if case=="U-02-driver":
        pg.locator(".a-sheet").wait_for(state="visible",timeout=2800)
        r=assert_result(pg,"""() => {
          const p=document.querySelector('.a-u18-instructions'),
             tags=[...(p?.querySelectorAll('.a-u18-tags>span')||[])],
             box=p?.getBoundingClientRect(),sheet=document.querySelector('#a-sheet-body')?.getBoundingClientRect();
          return {ok:!!p&&tags.length>=3&&p.innerText.includes(TLB.t('u18DriverTitle'))&&
             !!box&&!!sheet&&box.left>=sheet.left-3&&box.right<=sheet.right+3&&
             tags.some(x=>x.innerText.includes(TLB.t('u18DriverDoor'))),
             title:p?.querySelector('h3')?.innerText||'',tags:tags.map(x=>x.innerText),
             width:box?.width||0};
        }""")
        return r,[".a-u18-instructions",".a-u18-tags span","#a-sheet"]
    raise RuntimeError("Unhandled BRIEF18 case "+case)

def main():
    server=start_server()
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(headless=True)
            for lang,w,h in VIEWPORTS:
                for case,app in CASES:
                    ctx=page=None
                    row={"id":case,"app":app,"lang":lang,"width":w,"mode":MODE}
                    page_errors=[]
                    try:
                        ctx=make_context(browser,app,lang,w,h)
                        page=ctx.new_page()
                        # Deterministic synthetic pricing hour; prevent midnight rollover in before/after parity.
                        page.clock.install(time="2026-11-17T14:00:00Z")
                        page.on("pageerror",lambda err:page_errors.append(str(err)[:350]))
                        page.goto(LOCAL+"/"+app+".html",wait_until="domcontentloaded",timeout=20000)
                        page.wait_for_timeout(750)
                        if not page.locator("#app").count():raise AssertionError("App not mounted")
                        prepare(page,case,lang,w,h)
                        if app=="customer" and case!="U-01":
                            row["financial"]=financial(page)
                        if MODE=="before":
                            if case=="U-02":
                                page.locator(".d69-preferences").evaluate("e=>e.open=true")
                                page.locator(".d69-preferences").scroll_into_view_if_needed(timeout=2000)
                            elif case=="U-03":
                                page.locator(".d67-checkout .tipr").last.scroll_into_view_if_needed(timeout=2000)
                            elif case=="U-04":
                                for part,screen in (("pay","pay"),("cart","cart")):
                                    if screen=="cart":page.evaluate("() => go('cart')")
                                    else:page.locator(".d67-checkout .sv").scroll_into_view_if_needed(timeout=1800)
                                    shot(page,case,lang,w,part)
                                page.evaluate("() => go('pay')")
                            elif case=="U-05":
                                page.locator(".f15c-option-row").first.scroll_into_view_if_needed(timeout=2500)
                            row["status"]="REFERENCE"
                        else:
                            result,selectors=inspect(page,case,lang,w)
                            row["result"]=result;row["geometry"]=rects(page,selectors)
                            row["status"]="PASS" if result.get("ok") and row["geometry"] and not page_errors else "FAIL"
                            if row["status"]!="PASS":
                                raise AssertionError(json.dumps({"result":result,"pageErrors":page_errors},ensure_ascii=False)[:1400])
                        row["page_errors"]=page_errors
                    except Exception as exc:
                        row["status"]="BEFORE_LIMITATION" if MODE=="before" else "FAIL"
                        row["error"]=str(exc)[:1600]
                        if MODE=="after":
                            errors.append({k:row.get(k) for k in ("id","app","lang","width","error")})
                    finally:
                        if page:
                            try:row["screenshot"]=shot(page,case,lang,w)
                            except Exception as exc:
                                row["screenshot_error"]=str(exc)[:300]
                                if MODE=="after":errors.append({"id":case,"app":app,"lang":lang,"width":w,
                                                                "error":"PNG "+str(exc)[:200]})
                        rows.append(row)
                        if ctx:ctx.close()
            browser.close()
    finally:server.shutdown()
    data={"mode":MODE,"browser":"Linux WebKit; original TALABOT UI, synthetic-only read adapter",
          "viewport_cases":VIEWPORTS,"cases":rows,"errors":errors}
    (OUT/"REPORT.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    index=["# TALABOT BRIEF-18 "+MODE.upper(),"","Original HTML/JS, read-only synthetic fixture.",
           "NOT a physical iPhone, deployed production, or SQL migration test.",""]
    for r in rows:
        filename=pathlib.Path(r.get("screenshot","")).name
        index.append(f"- {r['id']} {r['app']} {r['lang']}/{r['width']}: {r['status']} [{filename}]({filename})")
    (OUT/"INDEX.md").write_text("\n".join(index)+"\n",encoding="utf-8")
    print("BRIEF18_WEBKIT",MODE,"TOTAL",len(rows),"PASS",sum(r["status"]=="PASS" for r in rows),
          "FAIL",len(errors),flush=True)
    for err in errors[:24]:print("BRIEF18_FAIL",json.dumps(err,ensure_ascii=False),flush=True)
    return 1 if MODE=="after" and errors else 0

if __name__=="__main__":sys.exit(main())
