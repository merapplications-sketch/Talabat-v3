#!/usr/bin/env python3
"""BRIEF-15b BEFORE/AFTER WebKit contracts. Original application DOM, read-only
synthetic Supabase adapter; no RPC mutations, financial edits, deployment, or iOS claim.
BEFORE runs on the pinned original source only for comparable screenshot evidence.
AFTER fails closed on missing interactions, invalid geometry, or JS page errors.
"""
import json, os, pathlib, sys
from playwright.sync_api import sync_playwright
from full_audit import ROOT, LOCAL, start_server, make_context

MODE=os.environ.get("BRIEF15B_MODE","after")
assert MODE in ("before","after")
OUT=ROOT/"qa-shots"/"unified-fix"/"b"/MODE
OUT.mkdir(parents=True,exist_ok=True)
VIEWPORTS=(("ru",375,667),("en",390,844))
CASES=(
    ("C-01","customer"),("C-02","customer"),("C-02","merchant"),("C-02","driver"),
    ("G-01","merchant"),("G-02","merchant"),("G-03","customer"),
    ("G-04","driver"),("G-05","merchant"),("G-06","merchant"),
    ("G-07","admin"),("G-08","customer"),("G-09","customer")
)
rows=[];errors=[]

def shot(pg,case,app,lang,w,stage="main"):
    name=f"{case}-{app}-{lang}-{w}-{stage}-{MODE}.png"
    p=OUT/name
    pg.screenshot(path=str(p),animations="disabled",timeout=16000)
    if p.stat().st_size<=2000 or p.read_bytes()[:8]!=b"\x89PNG\r\n\x1a\n":
        raise AssertionError("Invalid WebKit PNG "+name)
    return str(p.relative_to(ROOT))

def invoke(pg,source):
    result=pg.evaluate(source)
    if not isinstance(result,dict):raise AssertionError("Missing structured DOM proof")
    return result

def geometry(pg,selectors):
    return pg.evaluate("""selectors => {
      const rect=e=>{const r=e.getBoundingClientRect();return {
        x:+r.x.toFixed(2),y:+r.y.toFixed(2),width:+r.width.toFixed(2),
        height:+r.height.toFixed(2),right:+r.right.toFixed(2),bottom:+r.bottom.toFixed(2)}};
      return selectors.flatMap(sel=>[...document.querySelectorAll(sel)].slice(0,6).map(e=>({
        selector:sel,text:(e.textContent||'').trim().slice(0,64),
        rect:rect(e),disabled:!!e.disabled,ariaDisabled:e.getAttribute('aria-disabled')})));
    }""",selectors)

def run_case(pg,case,app,lang,w):
    if case=="C-01":
        pg.evaluate("""() => {
          window.__bClosed=STORES[0].n;
          const real=TLB.isOpen.bind(TLB);
          TLB.isOpen=n=>n===window.__bClosed?false:real(n);
          S.v='cat';S.catKey='*';S.cq='';S.srt='';S.fo=false;render();
        }""")
        pg.wait_for_timeout(85)
        a=invoke(pg,"""() => {
          const e=[...document.querySelectorAll('#app .d6-sr,#app .d6-sc,#app .sr')]
            .find(x=>x.textContent.includes(window.__bClosed));
          if(!e)return {ok:false,reason:'closed store missing from category'};
          const before=S.v;
          e.click();
          const r=e.getBoundingClientRect();
          return {ok:before===S.v && e.getAttribute('onclick')===null &&
            e.getAttribute('aria-disabled')==='true' && r.width>70,
            clickedFrom:before,clickedTo:S.v,blocked:e.getAttribute('aria-disabled'),
            label:e.textContent.slice(0,90),bounds:{width:r.width,height:r.height}};
        }""")
        shot(pg,case,app,lang,w,"closed-category")
        pg.evaluate("""() => {
           S.v='menu';S.store=window.__bClosed;
           document.getElementById('app').innerHTML=vMenu();
        }""")
        pg.wait_for_timeout(55)
        b=invoke(pg,"""() => {
           const e=document.querySelector('#app .d6-add.off');
           const r=e?.getBoundingClientRect();
           return {ok:!!e&&e.disabled&&e.getAttribute('aria-disabled')==='true'&&
             r.width>=0,disabled:!!e?.disabled,width:r?.width||0};
        }""")
        shot(pg,case,app,lang,w,"closed-dish")
        pg.evaluate("""() => {
          S.sh=null;S.cart={i1:1};S.cartStore=window.__bClosed;S.v='cart';render();
        }""")
        pg.wait_for_timeout(55)
        c=invoke(pg,"""() => {
          const e=document.querySelector('#app .d70-dock .btn:last-child');
          const n=document.querySelector('#app .closedb');
          const header=document.querySelector('#app .c01-closed-store .st');
          const r=e?.getBoundingClientRect();
          return {ok:!!e&&e.disabled&&!!n&&!!header&&r.width>100,
             checkoutDisabled:!!e?.disabled,reason:n?.innerText||'',
             storeName:header?.innerText||'',ctaWidth:r?.width||0};
        }""")
        shot(pg,case,app,lang,w,"closed-cart")
        return {"ok":a["ok"] and b["ok"] and c["ok"],"category":a,"dish":b,"cart":c},["#app .d70-dock button","#app .closedb"]
    if case=="C-02":
        pg.evaluate("""() => TLB.toast('BRIEF15B_TOAST_PROBE',true)""")
        pg.wait_for_timeout(110)
        r=invoke(pg,"""() => {
           const e=document.querySelector('.t15-flow-toast'),b=e?.getBoundingClientRect();
           const fixed=[...document.body.children].filter(x=>x.innerText?.trim()==='BRIEF15B_TOAST_PROBE'
                       &&getComputedStyle(x).position==='fixed').length;
           return {ok:!!e&&getComputedStyle(e).position==='static'&&
             b.width>30&&b.width<=320&&fixed===0,
             position:e?getComputedStyle(e).position:null,width:b?.width||0,
             height:b?.height||0,fixed};
        }""")
        shot(pg,case,app,lang,w,"bubble")
        if app in ("merchant","driver"):
            pg.evaluate("""() => {
              document.querySelectorAll('.t15-flow-toast').forEach(x=>x.remove());
              TLB.toast('Ресторан сейчас закрыт',true);
            }""")
            pg.wait_for_timeout(100)
            q=invoke(pg,"""() => ({
              ok:![...document.querySelectorAll('.t15-flow-toast')].some(e=>e.textContent.includes('Ресторан сейчас закрыт')),
              leaked:[...document.querySelectorAll('.t15-flow-toast')].map(e=>e.textContent)
            })""")
            r["suppression"]=q
            r["ok"]=r["ok"] and q["ok"]
        return r,["#app",".t15-flow-toast"]
    if case=="G-01":
        r=invoke(pg,"""() => {
          const e=document.querySelector('#app .top select'),s=e&&getComputedStyle(e),b=e?.getBoundingClientRect();
          return {ok:!!e&&s.color==='rgb(28, 28, 33)'&&s.backgroundColor==='rgb(255, 255, 255)'
            &&b.width>90&&b.height>20,fg:s?.color||'',bg:s?.backgroundColor||'',width:b?.width||0};
        }""")
        return r,["#app .top select"]
    if case=="G-02":
        pg.evaluate("""() => {setTab('m');openSheet('i1')}""")
        pg.wait_for_timeout(90)
        pg.locator(".f06-option-name").first.scroll_into_view_if_needed(timeout=3000)
        r=invoke(pg,"""() => {
          const els=[...document.querySelectorAll('.f06-option-name')];
          return {ok:els.length>0 && els.every(e=>e.tagName==='INPUT'&&
            getComputedStyle(e).whiteSpace==='nowrap'&&e.getBoundingClientRect().height<=51),
            options:els.map(e=>({type:e.tagName,h:e.getBoundingClientRect().height,
              text:e.value.slice(0,40),whiteSpace:getComputedStyle(e).whiteSpace}))};
        }""")
        return r,[".f06-item-editor",".f06-option-name"]
    if case=="G-03":
        pg.evaluate("""() => {go('menu',{store:STORES[0].n});openItem('i1')}""")
        pg.wait_for_timeout(90)
        r=invoke(pg,"""() => {
          const e=document.querySelector('.d6s .oshf .btn .px6'),b=e?.getBoundingClientRect(),
                bt=e?.closest('button'),q=bt?.getBoundingClientRect();
          return {ok:!!e&&getComputedStyle(e).whiteSpace==='nowrap'&&
            e.scrollWidth<=e.clientWidth+2&&b.width>30&&q.width>70&&
            b.left>=q.left-2&&b.right<=q.right+2,
            value:e?.textContent||'',whiteSpace:e?getComputedStyle(e).whiteSpace:'',
            width:b?.width||0,buttonWidth:q?.width||0};
        }""")
        return r,[".d6s .oshf .btn",".d6s .oshf .px6"]
    if case=="G-04":
        r=invoke(pg,"""() => {
          online=false;const active=mine();render();
          const e=document.querySelector('.hd .pill'),b=e?.getBoundingClientRect();
          return {ok:!!active&&!!e&&e.innerText.includes(TLB.t('g04Delivering'))&&
            !e.innerText.includes(TLB.t('shOff'))&&!online&&b.width>60,
            active:!!active,online,pill:e?.innerText||'',width:b?.width||0};
        }""")
        return r,[".hd .pill","#app .card.act"]
    if case=="G-05":
        pg.evaluate("""() => {setTab('o');OF='pending';render()}""")
        pg.wait_for_timeout(85)
        r=invoke(pg,"""() => {
          const card=document.querySelector('#app .oc.new'),
            head=card?.querySelector('.oh'),sp=[...(head?.children||[])],
            reject=card?.querySelector('.ob .b.r'),
            accept=card?.querySelector('.ob .b.g');
          const okSpan=x=>x.scrollWidth<=x.clientWidth+2&&getComputedStyle(x).whiteSpace==='nowrap';
          return {ok:!!card&&!!head&&sp.length===2&&sp.every(okSpan)&&
            !!reject&&!!accept&&[reject,accept].every(x=>
              getComputedStyle(x).whiteSpace==='nowrap'&&x.scrollWidth<=x.clientWidth+2),
            heading:head?.innerText||'',headerWidth:head?.getBoundingClientRect().width||0,
            spans:sp.map(x=>({width:x.clientWidth,scroll:x.scrollWidth,whiteSpace:getComputedStyle(x).whiteSpace})),
            actions:[reject,accept].filter(Boolean).map(x=>({txt:x.innerText,width:x.clientWidth,scroll:x.scrollWidth}))};
        }""")
        return r,["#app .oc.new .oh","#app .oc.new .b.r","#app .oc.new .b.g"]
    if case=="G-06":
        pg.evaluate("""() => {setTab('p');render()}""")
        r=invoke(pg,"""() => {
           if(typeof orderCountLabel!=='function')return {ok:false,error:'plural function absent'};
           const nums=[1,2,5,11,14,21,22,25,101],
             got=nums.map(orderCountLabel),
             ru=TLB.lang()==='ru',
             exp=ru?['заказ','заказа','заказов','заказов','заказов','заказ','заказа','заказов','заказ']:
               ['order','orders','orders','orders','orders','orders','orders','orders','orders'];
           return {ok:got.every((v,i)=>v===exp[i]),numbers:nums,got,expected:exp};
        }""")
        return r,["#app .k"]
    if case=="G-07":
        r=invoke(pg,"""() => {
          const original=TLB.drivers.bind(TLB);
          TLB.drivers=(...args)=>original(...args).map(o=>{
            const copy=Object.assign({},o);delete copy.online;return copy;
          });
          g07SetupLogged=false;
          const out=livePills();render();
          const txt=document.getElementById('app')?.innerText||'';
          return {ok:g07SetupLogged&&!out.includes('schema_patch12.sql')&&
             !txt.includes('schema_patch12.sql')&&!document.querySelector('.setupw'),
             logged:g07SetupLogged,visibleSql:txt.includes('schema_patch12.sql'),
             setupVisible:!!document.querySelector('.setupw')};
        }""")
        return r,["#app .pills","#app"]
    if case=="G-08":
        r=invoke(pg,"""() => {
          S.v='home';S.q='';render();
          const cards=[...document.querySelectorAll('#app .d6-lo')];
          const actual=cards.every(e=>!!e.querySelector('b.nm')?.textContent.trim()&&
             (!!e.querySelector('img')||!!e.querySelector('.d6-name-ph span')?.textContent.trim()));
          const original=TLB.orders.bind(TLB);
          TLB.orders=()=>[];
          render();
          const empty=[...document.querySelectorAll('#app .d6-lo')].length;
          TLB.orders=original;
          return {ok:actual&&empty===0,initialCards:cards.length,named:actual,emptyCount:empty};
        }""")
        return r,["#app .d6-rl","#app .d6-hh"]
    if case=="G-09":
        r=invoke(pg,"""() => {
          TLB.addresses=()=>[];S.useTmp=false;S.v='home';S.q='';render();
          const e=document.querySelector('#app .d6-loc b'),r=e?.getBoundingClientRect();
          const wanted=TLB.t('addrAdd');
          return {ok:!!e&&e.innerText===wanted&&e.scrollWidth<=e.clientWidth+2&&r.width>60,
            label:e?.innerText||'',expected:wanted,width:r?.width||0,scroll:e?.scrollWidth||0};
        }""")
        return r,["#app .d6-loc b","#app .d6-hh"]
    raise RuntimeError("Unregistered case "+case)

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
                        page.on("pageerror",lambda err:page_errors.append(str(err)[:350]))
                        page.goto(LOCAL+"/"+app+".html",wait_until="domcontentloaded",timeout=20000)
                        page.wait_for_timeout(750)
                        if not page.locator("#app").count():raise AssertionError("App not mounted")
                        result,selectors=run_case(page,case,app,lang,w)
                        row["geometry"]=geometry(page,selectors)
                        row["result"]=result
                        row["page_errors"]=page_errors
                        row["status"]="REFERENCE" if MODE=="before" else (
                           "PASS" if result.get("ok") and row["geometry"] and not page_errors else "FAIL")
                        if MODE=="after" and row["status"]!="PASS":
                            raise AssertionError(str({"result":result,"pageErrors":page_errors})[:900])
                    except Exception as exc:
                        row["status"]="BEFORE_LIMITATION" if MODE=="before" else "FAIL"
                        row["error"]=str(exc)[:1100]
                        if MODE=="after":errors.append({"case":case,"app":app,"lang":lang,"width":w,"error":row["error"]})
                    finally:
                        if page:
                            try:row["screenshot"]=shot(page,case,app,lang,w)
                            except Exception as exc:
                                row["screenshot_error"]=str(exc)[:200]
                                if MODE=="after":errors.append({"case":case,"app":app,"lang":lang,"width":w,"error":"PNG "+str(exc)})
                        rows.append(row)
                        if ctx:ctx.close()
            browser.close()
    finally:
        server.shutdown()
    data={"browser":"WebKit Linux, original HTML/JS, synthetic read-only","mode":MODE,
          "viewports":VIEWPORTS,"cases":rows,"errors":errors}
    (OUT/"REPORT.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    index=["# BRIEF-15b "+MODE.upper()+" WebKit", "",
      "Original TALABOT app HTML/JS; synthetic read-only fixture. Not physical Safari or production.",""]
    for row in rows:
        name=pathlib.Path(row.get("screenshot","")).name
        index.append(f"- {row['id']} {row['app']} {row['lang']}/{row['width']}: {row['status']} — [{name}]({name})")
    (OUT/"INDEX.md").write_text("\n".join(index)+"\n",encoding="utf-8")
    print("BRIEF15B",MODE,"cases",len(rows),"fails",len(errors),flush=True)
    for item in errors[:20]:print("BRIEF15B_FAIL",json.dumps(item,ensure_ascii=False),flush=True)
    return 1 if MODE=="after" and (errors or any(r["status"]!="PASS" for r in rows)) else 0

if __name__=="__main__":sys.exit(main())
