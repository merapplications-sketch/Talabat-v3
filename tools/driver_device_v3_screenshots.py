#!/usr/bin/env python3
"""Actual Chromium mobile rendering of the source N04 modal with SYNTHETIC local data.
No production login, payment, remote requests or claim of physical iOS keyboard rendering.
The 390×560 capture simulates the keyboard-reduced visual viewport only."""
import pathlib
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"evidence"/"driver-device-v3"
OUT.mkdir(parents=True,exist_ok=True)
original=(ROOT/"driver.html").read_text(encoding="utf-8")
css=original.split("<style>",1)[1].split("</style>",1)[0]
compact=(ROOT/"assets/driver-a/driver-a.css").read_text(encoding="utf-8")
html='''<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta charset="utf-8"><style>'''+css+compact+'''</style></head>
<body style="background:#eef1f4;margin:0;min-height:100vh"><div style="padding:14px;background:#fff;color:#131313">TALABOT · SYNTHETIC QA ONLY · NO REAL CASH/ORDER</div><div id="app"></div></body></html>'''
setup=r"""() => {
 let dict={recvQ:'Confirm cash received',photoT:'Delivery photo',photoS:'Photo proof',photoRe:'Retake photo',
  photoB:'Take photo',cancelB:'Cancel',confirmB:'Confirm',cashGet:'Collect',cashOrder:'Order',cash:'Cash'};
 window.TLB={addDict(ru,en){Object.assign(dict,en);},order(id){return {id,leaveAtDoor:false};},
  isCash(){return true;},toast(){},unlockAudio(){},audioReady(){return false;}};
 window.t=k=>dict[k]||k;
 window.esc=s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
 window.DV=null;window.DLV={};window.CXL=null;window.online=false;
 window.due=()=>278;window.cashBox=()=>'<div class="cashb" style="margin:8px 0"><div class="big"><span>Cash to collect</span><span>278.00 TJS</span></div></div>';
 window.ico=()=>'';window.$=id=>document.getElementById(id);
 window.render=()=>{document.getElementById('app').innerHTML=window.modal();};
 window.modal=()=>'';window.deliverClick=()=>{};window.unlockSound=()=>{};
 window.startShift=()=>{};window.finish=()=>Promise.resolve(true);
 window.confirmDeliver=()=>{};window.takePhoto=()=>{};
}"""
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 context=browser.new_context(viewport={"width":390,"height":844},device_scale_factor=3,
                             is_mobile=True,has_touch=True)
 page=context.new_page()
 page.route("https://**/*",lambda route:route.abort())
 page.set_content(html,wait_until="load")
 page.evaluate(setup)
 page.add_script_tag(path=str(ROOT/"assets"/"driver-tech"/"device-notes-v3.js"))
 page.evaluate("() => {deliverClick(9122);n04ShowDifferent();}")
 amount=page.locator("#cashAmt")
 assert amount.count()==1 and amount.get_attribute("inputmode")=="decimal"
 amount.fill("200")
 assert page.locator("#n04-reason").is_visible()
 page.locator("#cashNote").fill("Customer paid less")
 assert page.locator("#cashAmt").input_value()=="200"
 page.screenshot(path=str(OUT/"n04-390-amount-different.png"))
 print("N04_REAL_CHROMIUM_DOM_PASS 390x844: actual source cash field edited; note visible only for difference")
 page.set_viewport_size({"width":390,"height":560})
 page.evaluate("() => window.__deviceNotesV3.position()")
 bounds=page.locator("#n04-modal").bounding_box()
 assert bounds is not None and bounds["y"]>=0 and bounds["height"]<=560
 page.screenshot(path=str(OUT/"n04-390-keyboard-viewport-simulated.png"))
 print("N04_KEYBOARD_VIEWPORT_SIMULATED_PASS 390x560: modal within reduced viewport; no physical iOS keyboard")
 page.set_viewport_size({"width":320,"height":568})
 page.evaluate("() => window.__deviceNotesV3.position()")
 bounds=page.locator("#n04-modal").bounding_box()
 assert bounds is not None and bounds["x"]>=-1 and bounds["x"]+bounds["width"]<=321
 page.screenshot(path=str(OUT/"n04-320-narrow.png"))
 print("N04_REAL_CHROMIUM_DOM_PASS 320x568: no modal horizontal clipping")
 browser.close()
