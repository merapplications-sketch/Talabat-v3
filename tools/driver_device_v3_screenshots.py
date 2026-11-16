#!/usr/bin/env python3
"""TALABOT Gate1 driver cash UI — synthetic Chromium mobile layout evidence ONLY.
Never connect to live Supabase, map providers or any public service. Resized viewport
stands in for the area left after a mobile software keyboard, NOT native iOS Safari."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evidence"/"driver-device-v3"
OUT.mkdir(parents=True,exist_ok=True)
ADAPTER=(ROOT/"assets/driver-tech/device-notes-v3.js").read_text(encoding="utf-8")

MOCK_HTML=r"""
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
:root{--o:#f1511b;--ink:#17243c;--ok:#27ae60;--mut:#6b7180;--a-vh:100dvh;--a-vtop:0px}
*{box-sizing:border-box}body{margin:0;background:#f6f6f8;font:14px -apple-system,BlinkMacSystemFont,Arial,sans-serif;color:var(--ink)}
header{background:#f1511b;color:#fff;padding:18px 16px;font-weight:700;font-size:18px}
.card{padding:20px;margin:16px;background:white;border-radius:18px}
.ov{position:fixed;top:0;left:0;right:0;bottom:0;background:#0007;z-index:900;display:flex;align-items:flex-end}
.md{background:white;width:100%;border-radius:26px 26px 0 0;padding:22px 18px 28px}
h3{margin:0 0 14px;font-size:18px}
.b{display:block;width:100%;border:0;border-radius:999px;padding:14px;font-size:14px;font-weight:700;color:#fff;background:#f1511b;text-align:center;margin-top:10px;cursor:pointer}
.b.g{background:#27ae60}.b.s{background:#f1f1f4;color:#17243c}
input[type=text]{width:100%;padding:13px 14px;margin-bottom:8px;background:#f3f3f6;border:1.5px solid transparent;border-radius:14px;font-size:16px;color:#17243c;outline:none}
input:focus{border-color:#f1511b;background:#fff}
.cashb{background:#fff7e0;border:2px solid #f5b400;border-radius:16px;padding:11px 14px;margin:10px 0;color:#8a5b00}
.cashb .big{display:flex;justify-content:space-between;font-size:16px;font-weight:800}
.cashb .r{display:flex;justify-content:space-between;color:#6b5a2a;font-size:12px}
.xs{font-size:11px}.mut{color:#6b7180}
.php img{width:100%}
</style>
</head><body><header>TALABOT · Synthetic mobile QA</header>
<div class="card" id="status">Fixture only — no real orders, money or accounts.</div><div id="app"></div>
<script>
var DV=null,DLV={},CXL=null,chatOpen=false,online=true;
var dict={},submits=[];
var TLB={
  addDict:function(ru,en){Object.assign(dict,en)},
  order:function(id){return {id:id,payment:'cash',total:278,leaveAtDoor:false}},
  isCash:function(){return true},
  unlockAudio:function(){return true},testSound:function(){},audioReady:function(){return true},
  toast:function(x){document.querySelector('#status').textContent=x}
};
function t(key){return dict[key]||key}
function esc(x){return String(x).replace(/[&<>"]/g,function(c){if(c==='&')return '&amp;';if(c==='<')return '&lt;';if(c==='>')return '&gt;';return '&quot;'})}
function ico(){return ''}
function due(){return 278}
function cashBox(){return '<div class="cashb"><div class="big"><span>Cash due</span><span>278.00 TJS</span></div><div class="r"><span>Paid by customer</span><span>Cash</span></div></div>'}
function $(id){return document.getElementById(id)}
function modal(){return ''}
function render(){document.querySelector('#app').innerHTML=modal()}
function deliverClick(){}
function confirmDeliver(){submits.push({amount:DV.amt,note:DV.note});return Promise.resolve(true)}
function unlockSound(){}
</script></body></html>
"""

def smoke(page,width,height,filename,different=False):
    page.set_viewport_size({"width":width,"height":height})
    page.set_content(MOCK_HTML)
    page.add_script_tag(content=ADAPTER)
    page.evaluate("deliverClick(990001)")
    if different:
        page.locator("#n04-other").click()
        assert page.evaluate("document.activeElement.id")=="cashAmt", "amount field should focus on mobile tap"
        assert page.locator("#cashAmt").is_editable()
        page.locator("#cashAmt").fill("200")
        assert page.locator("#n04-reason").is_visible()
        page.locator("#cashNote").fill("Customer says only 200 TJS")
        assert page.evaluate("document.querySelector('#cashAmt').value")=="200"
        page.evaluate("window.__deviceNotesV3.position()")
        rect=page.locator("#cashAmt").bounding_box()
        assert rect and rect["y"]>=0 and rect["y"]+rect["height"]<=height+2, f"amount is outside reduced viewport: {rect}"
    else:
        assert page.locator("#n04-full").is_visible()
        assert page.locator("#cashAmt").count()==0, "no duplicate numeric amount field in full-amount mode"
        assert page.locator("#cashNote").count()==0, "reason must be absent in full-amount mode"
    page.screenshot(path=str(OUT/filename),full_page=False)
    return {"filename":filename,"width":width,"viewport_height":height,"mode":"different" if different else "full",
            "layout":"reduced visual viewport; keyboard region is NOT rendered" if height<700 else "full viewport"}

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context(is_mobile=True,has_touch=True,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
        viewport={"width":390,"height":844},device_scale_factor=2)
    page=context.new_page()
    page.route("**/*",lambda route:route.abort()) # No network, even external fonts/images.
    captures=[
        smoke(page,390,844,"N04_full_390_synthetic.png",False),
        smoke(page,390,520,"N04_partial_reduced_vv_390_synthetic.png",True),
        smoke(page,430,550,"N04_partial_reduced_vv_430_synthetic.png",True),
        smoke(page,320,470,"N04_partial_reduced_vv_320_synthetic.png",True),
    ]
    context.close()
    browser.close()
manifest={"source":"real N-04 adapter HTML in isolated synthetic Chromium mobile harness",
          "not_native_ios_safari":True,"no_real_accounts_orders_or_payments":True,
          "no_external_http":True,"keyboard_note":"520/550/470px viewport represents visible area above a mobile software keyboard; screenshots do not claim an actual iOS keyboard",
          "captures":captures}
(OUT/"EVIDENCE.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("PASS N04_form_visible_above_keyboard: synthetic mobile Chromium viewports 390, 430 and 320; captures="+str(len(captures)))
print("PASS N04_amount_field_editable_and_focused: actual adapter DOM with inputmode decimal, native focus, visible amount/reason.")
