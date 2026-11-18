#!/usr/bin/env python3
"""Compare the real customer entry point across the two source revisions and the candidate."""
import argparse
import functools
import http.server
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from datetime import datetime, timezone
from urllib.parse import urlsplit

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

PROJECT = Path.cwd()
sys.path.insert(0, str(PROJECT / "tools"))
from qa_all import FIX


APPROVED = "7c7e66094c10614c01ad7359cda7bc3740e8fcfd"
BEFORE = "d8538a26846491343f4d7d9d3df276ac5095182f"
REFERENCE = "83e94496141375d6e6f1e99ed735cccb70254c32"
EVIDENCE = PROJECT / "qa-shots/unified-fix/brief21"
CASES = [("pending", "ord0", 0), ("preparing", "ord1", 1), ("ready", "ord2", 2),
         ("pickedup", "ord3", 3), ("delivered", "ord4", 4), ("cancelled", "ord5", 1),
         ("rejected", "ord6", 0), ("q14", "hold", 3)]
LABELS = {"ru": ["Оформлен", "Готовится", "Готов", "В пути", "Доставлен"],
          "en": ["Placed", "Preparing", "Ready", "On the way", "Delivered"]}
SEED = """
 orders.forEach(o=>o.delivery_photo=null);
 stores[0].name='KFC';stores[0].logo_url='/qa-image/kfc';stores[0].cover_url='';
 stores[1].name='Romant Restaurant';stores[1].logo_url=window.testBroken?'/qa-image/broken':'';
 stores[1].cover_url='/qa-image/romant';
 oitems.find(i=>i.order_id==='ord4').name='Hot honey';
 for (const [id,store_id] of [['romant','s2'],['repeat','s1']]){
   orders.push({...orders[4],id,store_id});
   oitems.push({...oitems.find(i=>i.order_id==='ord4'),id:'line-'+id,order_id:id,name:store_id==='s2'?'Стейк':'Hot honey'});
 }
 orders.push({...orders[3],id:'hold',status:'pickedup'});
 oitems.push({...oitems[3],id:'line-hold',order_id:'hold'});
 evs.push({order_id:'ord5',kind:'preparing',at:iso(14)},{order_id:'ord5',kind:'cancelled',at:iso(12)},
          {order_id:'ord5',kind:'ready',at:iso(10)});
 T.support_tickets.push({...T.support_tickets[0],id:'q14',order_id:'hold',reason:'payment',subject:'Cash shortage'});
"""
FINISH_SEED = " if(window.__EMPTY)"
assert FIX.count(FINISH_SEED) == 1
SDK = FIX.replace(FINISH_SEED, SEED + FINISH_SEED)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def serve(root):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server

def source_photos():
    path = "docs/management/mockups-20261118/HOME-LIKED-7c7e6609-favourites.png"
    frame = Image.open(io.BytesIO(subprocess.check_output(["git", "show", f"{REFERENCE}:{path}"])))
    photos = {}
    for key, box in [("kfc",(6,1386,480,1696)), ("romant",(527,1386,1001,1696))]:
        buf=io.BytesIO()
        frame.crop(box).convert("RGB").save(buf, "JPEG", quality=95)
        photos[key]=buf.getvalue()
    return photos

def financial(page):
    return page.evaluate("""() => {
      S.cartStore='KFC';S.cart={i2:2,[lk('i1',['o11'],'')]:1};S.tip=10;
      const rows=[];
      for(const wallet of [false,true]){
        S.useWallet=wallet;S.usePts=wallet;
        const v=calc();
        rows.push(Object.fromEntries(['sub','d','h','p','pv','fee','total','due','w','earn','cb']
          .map(k=>[k,v[k]]).concat([['tip',S.tip]])));
      }
      return rows;
    }""")

def shot(page):
    return Image.open(io.BytesIO(page.screenshot(animations="disabled"))).convert("RGB")

def compare(parts, filename):
    header=25
    out=Image.new("RGB",(sum(im.width for _,im in parts),header+max(im.height for _,im in parts)), "white")
    draw=ImageDraw.Draw(out);x=0
    for title,im in parts:
        draw.text((x+7,6),title,fill="black")
        out.paste(im,(x,header));x+=im.width
    out.save(EVIDENCE / filename, "WEBP", lossless=True, method=4)

def page_at(browser, server, photos, lang, width, role="customer", broken=False):
    ctx=browser.new_context(viewport={"width":width,"height":844 if width>=390 else 812},
                            is_mobile=True,has_touch=True,device_scale_factor=1,service_workers="block")
    ctx.add_init_script("localStorage.setItem('tlb_lang',"+json.dumps(lang)+");window.testBroken="+json.dumps(broken))
    def route(req):
        url=urlsplit(req.request.url)
        if url.hostname=="cdn.jsdelivr.net" and "supabase-js" in url.path:
            return req.fulfill(content_type="application/javascript",body=SDK.replace("window.__ROLE",json.dumps(role)))
        if url.hostname=="127.0.0.1" and url.port==server.server_port and req.request.method=="GET":
            if url.path.startswith("/qa-image/"):
                key=url.path.split("/")[-1]
                return req.fulfill(status=200 if key in photos else 404,content_type="image/jpeg",body=photos.get(key,b""))
            return req.continue_()
        req.abort()
    ctx.route("**/*",route)
    page=ctx.new_page()
    page.clock.set_fixed_time(datetime(2026,11,18,9,tzinfo=timezone.utc))
    page.goto(f"http://127.0.0.1:{server.server_port}/{role}.html",wait_until="domcontentloaded")
    page.wait_for_function("typeof TLB!=='undefined' && TLB.orders().length>0 && document.querySelector('#app')?.innerText.trim().length>30")
    return ctx,page

def home(page):
    tiles=page.locator(".d6-lo")
    tiles.first.wait_for()
    tiles.first.scroll_into_view_if_needed()
    page.wait_for_function("""()=>[...document.querySelectorAll('.d6-lo')].every(x=>{
      const img=x.querySelector('img');return img?img.complete&&img.naturalWidth>0:!!x.querySelector('.d6-ph.none')})""")
    return tiles.evaluate_all("""els=>els.map(e=>{const p=e.querySelector('.d6-ph'),i=p.querySelector('img');return {
      store:e.querySelector('.nm').textContent,card:e.offsetWidth,photo:[p.offsetWidth,p.offsetHeight],
      naturalWidth:i?.naturalWidth||0,src:i?.getAttribute('src')||null}})""")

def track(page, order_id):
    page.evaluate("id=>go('track',{tid:id})",order_id)
    page.locator(".p1-summary").wait_for()
    page.wait_for_timeout(90)
    return page.evaluate("""()=>{const list=document.querySelector('.d6-order-progress'),items=[...(list?.children||[])];
     return {heading:document.querySelector('.p1-track-heading').innerText,
      steps:items.map(li=>{const el=li.querySelector('span'),r=document.createRange();r.selectNodeContents(el);
       const box=el.getBoundingClientRect();return {label:el.innerText,cls:li.className,
        current:li.getAttribute('aria-current'),width:el.clientWidth,scroll:el.scrollWidth,
        textFits:[...r.getClientRects()].every(t=>t.left>=box.left-1&&t.right<=box.right+1),
        checked:!!li.querySelector('i svg')}}),
      directlyBelowHeading:!!list&&list.previousElementSibling?.matches('h1')&&!!list.closest('.p1-summary'),
      restaurant:document.querySelector('.p1-restaurant')?.innerText,
      courier:document.querySelector('.p1-courier')?.innerText||null,
      chat:!!document.querySelector('#ch'),support:!!document.querySelector('.p1-contact-help'),
      viewportFits:document.documentElement.scrollWidth===innerWidth};}""")

def verify(approved,before):
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    roots={"7c7e6609":approved,"d8538a26":before,"BRIEF-21":PROJECT}
    servers={k:serve(v) for k,v in roots.items()}
    photos=source_photos()
    data={"fixture":"Offline. Identical order/catalogue rows across sources. Images are cropped from the owner's approved screenshot.",
          "reference":REFERENCE,"approvedSource":APPROVED,"before":BEFORE,"home":[],"tracking":[],"firstScreens":[]}
    try:
      with sync_playwright() as pw:
        browser=pw.webkit.launch(executable_path=os.environ.get("TALABOT_WEBKIT") or None)
        data["webkit"]=browser.version
        for lang,width in [("ru",375),("en",390),("en",430)]:
          for broken in [False,True]:
            row={"lang":lang,"width":width,"brokenLogo":broken,"sources":{}}
            images=[]; money=[]
            for label,server in servers.items():
                ctx,page=page_at(browser,server,photos,lang,width,broken=broken)
                vals=home(page)
                assert len(vals)==3,(label,vals)
                row["sources"][label]=vals
                money.append(financial(page))
                assert all(v["sub"]>0 and v["total"]>v["tip"] for v in money[-1]),money
                images.append((label,shot(page)))
                ctx.close()
            old=row["sources"]["7c7e6609"];new=row["sources"]["BRIEF-21"]
            assert all(v["card"]==152 and v["photo"]==[152,100] and v["naturalWidth"]>0 for v in new),row
            assert all(v["card"]==112 for v in old) and money[0]==money[1]==money[2],row
            if broken: assert any(v["naturalWidth"]==0 for v in old)
            else: assert all(v["naturalWidth"]>0 for v in old)
            row.update(financial=money[0],financialParity=True,withinRequestedTwoPixels=abs(new[0]["card"]-old[0]["card"])<=2,deltaToPinnedSource=new[0]["card"]-old[0]["card"])
            filename=f"home-{lang}-{width}-{'retry' if broken else 'valid'}.webp"
            compare(images,filename);row["comparison"]=filename;data["home"].append(row)
        for lang,width in [("ru",375),("en",390),("ru",320),("en",320)]:
            pairs=[page_at(browser,servers[k],photos,lang,width) for k in ("d8538a26","BRIEF-21")]
            for status,oid,idx in CASES:
                rows=[track(page,oid) for _,page in pairs]
                new=rows[1]
                assert new["directlyBelowHeading"] and new["viewportFits"],(status,lang,width,new)
                for k in ("restaurant","courier","chat","heading","support"): assert rows[0][k]==new[k],(k,rows)
                steps=new["steps"]
                assert [x["label"] for x in steps]==LABELS[lang],(status,steps)
                for i,x in enumerate(steps):
                    assert x["width"]>=x["scroll"] and x["textFits"],(status,width,x)
                    assert (x["current"]=="step")== (i==idx) and x["checked"]==(i<idx), (status,width,steps)
                filename=f"track-{lang}-{width}-{status}.webp"
                compare([(label,shot(page)) for label,(_,page) in zip(("d8538a26","BRIEF-21"),pairs)],filename)
                data["tracking"].append(dict(status=status,lang=lang,width=width,comparison=filename,**new))
            for ctx,_ in pairs:ctx.close()
        for lang,width in [("ru",375),("en",390),("en",430),("ru",320)]:
          for role,screen in [("customer","home"),("customer","restaurant"),("driver","first"),("merchant","first")]:
            images=[]
            for label in ("d8538a26","BRIEF-21"):
                ctx,page=page_at(browser,servers[label],photos,lang,width,role=role)
                if screen=="restaurant":page.evaluate("()=>openN('KFC')")
                if screen=="home":home(page);page.evaluate("window.scrollTo(0,0)")
                page.wait_for_timeout(120)
                images.append((label,shot(page)));ctx.close()
            filename=f"first-{role}-{screen}-{lang}-{width}.webp"
            compare(images,filename);data["firstScreens"].append(filename)
        browser.close()
    finally:
        for s in servers.values():s.shutdown()
    (EVIDENCE/"measurements.json").write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    print("PASS:",len(data["home"]),"home cases with financial parity;",len(data["tracking"]),"tracking;",len(data["firstScreens"]),"first-screen comparisons",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("approved",type=Path);p.add_argument("before",type=Path)
    args=p.parse_args()
    for root,sha in ((args.approved,APPROVED),(args.before,BEFORE)):
        assert subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()==sha
    verify(args.approved,args.before)
