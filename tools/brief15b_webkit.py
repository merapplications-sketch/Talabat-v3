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
    ("C-01","customer"),("C-01a","customer"),("C-01b","customer"),("C-01c","customer"),("C-01d","customer"),
    ("C-02","customer"),("C-02","merchant"),("C-02","driver"),
    ("G-01","merchant"),("G-02","merchant"),("G-03","customer"),
    ("G-04","driver"),("G-05","merchant"),("G-06","merchant"),("G-06","admin"),
    ("G-06b","admin"),("G-07","admin"),("G-08","customer"),("G-09","customer"),
    ("G-10","merchant"),("G-11","merchant"),("G-12","customer")
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

def close_store_for_visual(pg):
    # Isolated synthetic fixture: alter availability only inside this new page.
    pg.evaluate("""() => {
      window.__bClosed=STORES[0].n;
      const open=TLB.isOpen.bind(TLB);
      TLB.isOpen=n=>n===window.__bClosed?false:open(n);
    }""")

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
    if case=="C-01a":
        close_store_for_visual(pg)
        pg.evaluate("""() => {S.v='home';S.q='';S.hf=null;render()}""")
        pg.locator("#app .d6-sc.closed").first.scroll_into_view_if_needed(timeout=3000)
        r=invoke(pg,"""() => {
          const e=[...document.querySelectorAll('#app .d6-sc.closed')].find(x=>x.textContent.includes(window.__bClosed)),
                badge=e?.querySelector('.hb.k'),rect=badge?.getBoundingClientRect(),
                photo=e?.querySelector('.d6-ph')?.getBoundingClientRect(),before=S.v;
          if(e)e.click();
          return {ok:!!e&&!!badge&&badge.innerText.includes(TLB.t('closedStoreBadge'))&&
            e.getAttribute('onclick')===null&&getComputedStyle(e).filter.includes('grayscale')&&
            S.v===before&&rect.width>20&&photo&&rect.right<=photo.right+1,
            home:before,view:S.v,closed:badge?.innerText||'',badgeRect:rect&&{x:rect.x,y:rect.y,width:rect.width},
            photoRight:photo?.right||0};
        }""")
        shot(pg,case,app,lang,w,"home")
        pg.evaluate("""() => {S.v='home';S.q=window.__bClosed.slice(0,12);render()}""")
        pg.locator("#app .d6-sr.closed").first.scroll_into_view_if_needed(timeout=3000)
        search=invoke(pg,"""() => {
          const e=document.querySelector('#app .d6-sr.closed'),t=e?.querySelector('.g12-closed-badge'),v=S.v;
          if(e)e.click();
          return {ok:!!e&&!!t&&t.innerText.includes(TLB.t('closedStoreBadge'))&&
             !e.getAttribute('onclick')&&v===S.v,screen:S.v,visibleBadge:t?.innerText||''};
        }""")
        shot(pg,case,app,lang,w,"search")
        r["search"]=search
        return {"ok":r["ok"] and search["ok"],"home":r,"search":search},["#app .d6-sr.closed .g12-closed-badge","#app .d6-sr.closed"]
    if case=="C-01b":
        close_store_for_visual(pg)
        pg.evaluate("""() => {S.v='cat';S.catKey='rest';S.cq='';S.srt='';S.fo=false;render()}""")
        pg.locator("#app .d6-sr.closed").first.scroll_into_view_if_needed(timeout=3000)
        pg.evaluate("""() => {
          const badge=document.querySelector('#app .d6-sr.closed .g12-closed-badge'),
                nav=document.querySelector('#app .nav');
          if(!badge||!nav)return;
          const b=badge.getBoundingClientRect(),n=nav.getBoundingClientRect();
          if(b.bottom>n.top-14)window.scrollBy(0,b.bottom-n.top+36);
        }""")
        pg.wait_for_timeout(95)
        r=invoke(pg,"""() => {
          const e=document.querySelector('#app .d6-sr.closed'),card=document.querySelector('#app .c-current'),
                nav=document.querySelector('#app .nav'),navTop=nav?.getBoundingClientRect()?.top||innerHeight,
                badge=e?.querySelector('.g12-closed-badge'),row=e?.getBoundingClientRect(),
                a=card?.getBoundingClientRect(),b=badge?.getBoundingClientRect();
          const overlap=x=>a&&x&&Math.min(a.right,x.right)-Math.max(a.left,x.left)>2&&
            Math.min(a.bottom,x.bottom)-Math.max(a.top,x.top)>2;
          return {ok:!!e&&!!card&&!!badge&&getComputedStyle(card).position!=='fixed'&&
             !overlap(row)&&!overlap(b)&&!!b&&b.width>25&&b.height>10&&
             b.bottom<=navTop-8&&b.top>0,
             mode:getComputedStyle(card).position,navTop,overlapRow:!!overlap(row),
             overlapBadge:!!overlap(b),badge:badge?.innerText||'',
             badgeRect:b&&{x:b.x,y:b.y,right:b.right,bottom:b.bottom}};
        }""")
        shot(pg,case,app,lang,w,"category")
        return r,["#app .c-current","#app .d6-sr.closed","#app .d6-sr.closed .g12-closed-badge"]
    if case=="C-01c":
        close_store_for_visual(pg)
        pg.evaluate("""() => {S.v='cat';S.catKey='rest';S.cq='';render()}""")
        before=invoke(pg,"""() => {
          const e=document.querySelector('#app .d6-sr.closed'),v=S.v;
          if(e)e.click();
          return {ok:!!e&&S.v===v&&e.getAttribute('onclick')===null,
            before:v,after:S.v};
        }""")
        pg.evaluate("""() => {S.v='menu';S.store=window.__bClosed;S.sh=null;render()}""")
        pg.wait_for_timeout(90)
        after=invoke(pg,"""() => {
          const view=document.querySelector('#app .c01-closed-menu'),
            adds=[...document.querySelectorAll('#app .d6-add')],
            r=view?.getBoundingClientRect();
          openItem('i1');
          return {ok:!!view&&!!r&&r.width>250&&adds.length>0&&
             adds.every(x=>x.disabled)&&!S.sh&&!view.querySelector('.d6-mi[onclick],.d6-pv[onclick]'),
             grey:!!view,buttons:adds.map(x=>({disabled:x.disabled,aria:x.getAttribute('aria-disabled')})),
             sheetOpen:!!S.sh};
        }""")
        shot(pg,case,app,lang,w,"direct-link-grey")
        return {"ok":before["ok"] and after["ok"],"tap":before,"direct":after},["#app .c01-closed-menu","#app .d6-add"]
    if case=="C-01d":
        close_store_for_visual(pg)
        pg.evaluate("""() => {
          S.cart={i1:1};S.cartStore=window.__bClosed;S.v='cart';S.sh=null;S.gCheckout=false;render();
        }""")
        r=invoke(pg,"""() => {
          const group=document.querySelector('#app .grpe'),
            more=document.querySelector('#app .d70-dock .btn.s'),
            pay=document.querySelector('#app .d70-dock .btn:last-child'),
            notice=document.querySelector('#app #c01-cart-closed'),
            v=S.v;
          group?.click();more?.click();
          return {ok:!!group&&group.disabled&&!!more&&more.disabled&&!!pay&&pay.disabled&&
            !!notice&&notice.innerText.includes(TLB.t('closedBanner'))&&S.v===v,
            groupDisabled:!!group?.disabled,moreDisabled:!!more?.disabled,
            payDisabled:!!pay?.disabled,reason:notice?.innerText||'',after:S.v};
        }""")
        shot(pg,case,app,lang,w,"closed-cart-actions")
        return r,["#app .grpe","#app .d70-dock button","#app #c01-cart-closed"]
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
          const e=document.querySelector('#app .top .g10-store-wrap select'),
                label=document.querySelector('#app .top .g10-store-label'),
                visual=label&&getComputedStyle(label),sel=e&&getComputedStyle(e),
                box=label?.getBoundingClientRect();
          return {ok:!!e&&!!label&&e.value===STORE&&label.innerText===STORE&&
            visual.color==='rgb(28, 28, 33)'&&
            visual.pointerEvents==='none'&&
            sel.backgroundColor==='rgb(255, 255, 255)'&&
            box.width>90&&box.height>18,
            displayLabel:label?.innerText||'',selected:e?.value||'',
            labelInk:visual?.color||'',background:sel?.backgroundColor||'',
            width:box?.width||0,height:box?.height||0};
        }""")
        return r,["#app .top .g10-store-label","#app .top .g10-store-wrap select"]
    if case=="G-02":
        pg.evaluate("""() => {setTab('m');openSheet('i1')}""")
        pg.wait_for_timeout(90)
        pg.locator(".f15c-group-name").first.scroll_into_view_if_needed(timeout=3000)
        top=invoke(pg,"""() => {
          const e=document.querySelector('.f15c-group-name'),r=e?.getBoundingClientRect();
          return {ok:!!e&&e.tagName==='TEXTAREA'&&
            e.scrollHeight<=e.clientHeight+3&&getComputedStyle(e).whiteSpace==='pre-wrap',
            value:e?.value||'',height:r?.height||0,client:e?.clientHeight||0,
            scroll:e?.scrollHeight||0};
        }""")
        shot(pg,case,app,lang,w,"group-title")
        pg.locator(".u18-merchant-option").first.scroll_into_view_if_needed(timeout=3000)
        pg.evaluate("""() => {
          const ed=document.querySelector('.f06-item-editor'),
            row=ed?.querySelector('.u18-merchant-option'),foot=ed?.querySelector('.f06-actions');
          if(!ed||!row||!foot)return;
          const delta=row.getBoundingClientRect().bottom-foot.getBoundingClientRect().top+20;
          if(delta>0)ed.scrollTop+=delta;
        }""")
        pg.wait_for_timeout(110)
        opts=invoke(pg,"""() => {
          const rows=[...document.querySelectorAll('.u18-merchant-option')];
          const metrics=rows.map(row=>{
            const name=row.querySelector('textarea.u18-option-name'),
              price=row.querySelector('.f15c-option-controls input[type=number]'),
              toggle=row.querySelector('.f15c-option-controls .sw'),
              remove=row.querySelector('.f15c-option-controls .rb'),
              box=x=>x?.getBoundingClientRect(),r=box(row),n=box(name),p=box(price),
              t=box(toggle),d=box(remove),foot=box(document.querySelector('.f06-item-editor .f06-actions')),
              ed=box(document.querySelector('.f06-item-editor'));
            const xok=!!r&&!!n&&!!p&&!!t&&!!d&&n.right<=p.left+3&&
              p.right<=t.left+3&&t.right<=d.left+3&&d.right<=r.right+3;
            return {name:name?.value||'',nameHeight:n?.height||0,
              natural:name?.scrollHeight||0,editorHeight:name?.clientHeight||0,
              sameRow:xok&&Math.abs(n.top-p.top)<30&&Math.abs(n.top-t.top)<30,
              nowrapError:!!name&&name.scrollHeight<=name.clientHeight+3,
              fullyVisible:!!foot&&!!ed&&r.top>=ed.top-3&&r.bottom<=foot.top-4,
              positions:r&&{rowRight:r.right,nameRight:n.right,priceLeft:p.left,priceRight:p.right,
                toggleLeft:t.left,toggleRight:t.right,deleteLeft:d.left,deleteRight:d.right}};
          });
          return {ok:metrics.length>0&&metrics.every(x=>x.sameRow&&x.nowrapError)
              &&metrics.some(x=>x.fullyVisible),metrics};
        }""")
        shot(pg,case,app,lang,w,"option-controls")
        return {"ok":top["ok"] and opts["ok"],"group":top,"options":opts},[
          ".f15c-group-name",".u18-merchant-option",".u18-option-name"]
    if case=="G-03":
        pg.evaluate("""() => {go('menu',{store:STORES[0].n});openItem('i1')}""")
        pg.wait_for_timeout(90)
        r=invoke(pg,"""() => {
          const bt=document.querySelector('.d6s .oshf .btn'),caption=bt?.querySelector('span:first-child'),
                price=bt?.querySelector('.px6'),l=caption?.getBoundingClientRect(),
                p=price?.getBoundingClientRect(),b=bt?.getBoundingClientRect();
          const gap=l&&p?p.left-l.right:0;
          return {ok:!!bt&&!!caption&&!!price&&getComputedStyle(price).whiteSpace==='nowrap'&&
             price.scrollWidth<=price.clientWidth+2&&gap>=7&&
             p.right<=b.right-6&&l.left>=b.left+6,
             gap,price:price?.innerText||'',priceWidth:p?.width||0,
             buttonRight:b?.right||0,captionRight:l?.right||0};
        }""")
        return r,[".d6s .oshf .btn",".d6s .oshf .btn span:first-child",".d6s .oshf .px6"]
    if case=="G-04":
        r=invoke(pg,"""() => {
          online=false;const active=mine();render();
          const e=document.querySelector('.hd .a-shift-dot'),b=e?.getBoundingClientRect();
          return {ok:!!active&&!!e&&e.innerText.includes(TLB.t('g04Delivering'))&&
            !e.innerText.includes(TLB.t('shOff'))&&!online&&b.width>60,
            active:!!active,online,pill:e?.innerText||'',width:b?.width||0};
        }""")
        return r,[".hd .a-shift-dot","#app .a-sheet"]
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
    if case=="G-06" and app=="admin":
        r=invoke(pg,"""() => {
          if(typeof g06Orders!=='function')return {ok:false,error:'admin plural helper absent'};
          const nums=[0,1,2,5,11,14,21,22,25,101],
             expected=TLB.lang()==='ru'?['заказов','заказ','заказа','заказов','заказов',
                 'заказов','заказ','заказа','заказов','заказ']:
                 ['orders','order','orders','orders','orders','orders','orders','orders','orders','orders'],
             actual=nums.map(g06Orders);
          return {ok:actual.every((v,i)=>v===expected[i]),nums,expected,actual};
        }""")
        return r,["#app .grid","#app .k"]
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
    if case=="G-06b":
        r=invoke(pg,"""() => {
          const n=TLB.orders().length,card=document.querySelector('#app .grid .k'),
                label=card?.querySelector('span'),expected=g06Orders(n),
                title=expected.charAt(0).toLocaleUpperCase(TLB.lang()==='ru'?'ru-RU':'en-US')+expected.slice(1),
                actual=label?.textContent?.trim()||'';
          return {ok:!!label&&actual===title&&/^[A-ZА-ЯЁ]/.test(actual),
             expected:title,actual,n};
        }""")
        return r,["#app .grid .k","#app .grid .k span"]
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
          const actual=cards.length>0&&cards.every(e=>!!e.querySelector('b.nm')?.textContent.trim()&&
             (!!e.querySelector('img')||!!e.querySelector('.d6-ph.none')));
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
          const e=document.querySelector('#app .d6-loc b'),box=e?.getBoundingClientRect(),
                parent=e?.closest('.d6-loc')?.getBoundingClientRect(),
                wanted=TLB.t('addrAddFirst'),css=e&&getComputedStyle(e);
          return {ok:!!e&&e.innerText===wanted&&css.whiteSpace==='nowrap'&&
             css.textOverflow==='ellipsis'&&e.scrollHeight<=e.clientHeight+3&&
             box.width>40&&box.bottom<=parent.bottom+2,
            label:e?.innerText||'',expected:wanted,whiteSpace:css?.whiteSpace||'',
            overflow:css?.textOverflow||'',width:box?.width||0,height:box?.height||0,
            parentHeight:parent?.height||0};
        }""")
        return r,["#app .d6-loc b","#app .d6-loc","#app .d6-hh"]
    if case=="G-10":
        r=invoke(pg,"""() => {
          const sel=document.querySelector('#app .top .g10-store-wrap select'),
             label=document.querySelector('#app .g10-store-label'),v=label?.getBoundingClientRect();
          return {ok:!!sel&&!!label&&sel.value===STORE&&label.innerText===STORE&&
             getComputedStyle(label).textOverflow==='ellipsis'&&
             label.scrollWidth>label.clientWidth&&v.width>60&&
             getComputedStyle(label).pointerEvents==='none',
             value:sel?.value||'',label:label?.innerText||'',width:v?.width||0,
             scroll:label?.scrollWidth||0,overflow:label&&getComputedStyle(label).textOverflow};
        }""")
        return r,["#app .top .g10-store-label","#app .top select"]
    if case=="G-11":
        pg.evaluate("""() => setTab('p')""")
        r=invoke(pg,"""() => {
          const e=document.querySelector('#app textarea#sdesc'),r=e?.getBoundingClientRect(),
            s=TLB.myStores().find(x=>x.name===STORE);
          return {ok:!!e&&e.tagName==='TEXTAREA'&&e.maxLength===300&&
             e.value===String(s?.description||'')&&r.height>=92&&
             getComputedStyle(e).whiteSpace==='pre-wrap',
             content:e?.value?.slice(0,90)||'',height:r?.height||0,tag:e?.tagName||''};
        }""")
        return r,["#app textarea#sdesc","#app .fld2"]
    if case=="G-12":
        close_store_for_visual(pg)
        evidence={}
        views=(
            ("search","() => {S.v='home';S.q=window.__bClosed.slice(0,12);S.hf=null;render()}"),
            ("category","() => {S.v='cat';S.catKey='rest';S.cq='';S.srt='disc';S.fo=false;render()}"),
            ("reorder","() => {S.v='cat';S.catKey='rest';S.cq='';S.srt='';S.fo=false;render()}")
        )
        for scene,script in views:
            pg.evaluate(script)
            pg.wait_for_timeout(85)
            pg.locator("#app .d6-sr.closed").first.scroll_into_view_if_needed(timeout=3000)
            pg.evaluate("""() => {
              const row=document.querySelector('#app .d6-sr.closed');
              if(!row)return;const top=row.getBoundingClientRect().top;
              if(top>155)window.scrollBy(0,top-145);
            }""")
            pg.wait_for_timeout(115)
            data=invoke(pg,"""() => {
              const row=document.querySelector('#app .d6-sr.closed'),
                badge=row?.querySelector('.g12-closed-badge,.or'),
                photo=row?.querySelector('.d6-ph.th'),
                offer=row?.querySelector('.g12-delivery-text'),
                b=badge?.getBoundingClientRect(),p=photo?.getBoundingClientRect(),
                textRects=[],hits=[];
              if(row){
                const walker=document.createTreeWalker(row,NodeFilter.SHOW_TEXT);
                let node;
                while((node=walker.nextNode())){
                  if(!node.textContent?.trim()||badge?.contains(node.parentElement))continue;
                  const parent=node.parentElement;
                  if(!parent)continue;
                  const style=getComputedStyle(parent);
                  if(style.display==='none'||style.visibility==='hidden')continue;
                  const range=document.createRange();range.selectNodeContents(node);
                  for(const r of range.getClientRects()){
                    if(r.width<1||r.height<1)continue;
                    textRects.push({text:node.textContent.trim().slice(0,46),
                      left:r.left,right:r.right,top:r.top,bottom:r.bottom});
                    if(b&&Math.min(r.right,b.right)-Math.max(r.left,b.left)>1&&
                       Math.min(r.bottom,b.bottom)-Math.max(r.top,b.top)>1)
                        hits.push(node.textContent.trim().slice(0,80));
                  }
                }
              }
              const contained=!!badge&&!!photo&&photo.contains(badge)&&!!b&&!!p&&
                  b.left>=p.left-1&&b.top>=p.top-1&&b.right<=p.right+1&&b.bottom<=p.bottom+1;
              const style=offer&&getComputedStyle(offer),ellipsis=!!offer&&
                  style.textOverflow==='ellipsis'&&style.whiteSpace==='nowrap'&&offer.clientWidth>20;
              const correct=badge?.textContent?.trim()===TLB.t('closedStoreBadge');
              return {ok:contained&&correct&&hits.length===0&&textRects.length>=3&&ellipsis,
                scene:S.v,badgeText:badge?.textContent?.trim()||'',
                badgeParent:badge?.parentElement?.className||'',contained,
                textNodesMeasured:textRects.length,overlappingTextNodes:hits,
                badgeRect:b&&{left:b.left,right:b.right,top:b.top,bottom:b.bottom},
                photoRect:p&&{left:p.left,right:p.right,top:p.top,bottom:p.bottom},
                offer:offer?.innerText||'',offerScroll:offer?.scrollWidth||0,
                offerWidth:offer?.clientWidth||0,ellipsis};
            }""")
            if scene=="reorder":
                data["reorderSectionPresent"]=pg.evaluate("""() => {
                  const s=TLB.t('hLastGo');return !!s&&
                     (document.querySelector('#app')?.innerText||'').includes(s)
                }""")
                data["ok"]=data["ok"] and data["reorderSectionPresent"]
            evidence[scene]=data
            shot(pg,case,app,lang,w,scene)
        return {"ok":all(v["ok"] for v in evidence.values()),"scenes":evidence},[
          "#app .d6-sr.closed .g12-closed-badge",
          "#app .d6-sr.closed .g12-delivery-text","#app .d6-sr.closed .d6-ph"]
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
    index=["# BRIEF-15c "+MODE.upper()+" WebKit", "",
      "Original TALABOT app HTML/JS; synthetic read-only fixture. Not physical Safari or production.",""]
    for row in rows:
        name=pathlib.Path(row.get("screenshot","")).name
        index.append(f"- {row['id']} {row['app']} {row['lang']}/{row['width']}: {row['status']} — [{name}]({name})")
    (OUT/"INDEX.md").write_text("\n".join(index)+"\n",encoding="utf-8")
    print("BRIEF15B",MODE,"cases",len(rows),"fails",len(errors),flush=True)
    for item in errors[:20]:print("BRIEF15B_FAIL",json.dumps(item,ensure_ascii=False),flush=True)
    return 1 if MODE=="after" and (errors or any(r["status"]!="PASS" for r in rows)) else 0

if __name__=="__main__":sys.exit(main())
