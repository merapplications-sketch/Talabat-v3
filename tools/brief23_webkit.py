"""Customer WebKit checks in the offline TALABOT catalogue."""
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

import brief22_webkit as previous
from brief22_webkit import qa

BASE='343fe0807819f46c97895b14290eae81a19e472c'
PROPOSAL='1d13286e0c00b471a93e52471cfbb1fc38f5fd10'
PREVIEW='https://talabot-gate1-preview-20261116.pages.dev'


def top_geometry(page):
    cats=page.locator('.d6-ct').evaluate_all("""els=>els.map(e=>{const r=e.getBoundingClientRect();return [r.left,r.right,r.top]})""")
    assert len(cats)==6 and len({r[2] for r in cats})==1 and all(0<=x<y<=page.viewport_size['width'] for x,y,_ in cats)
    boxes=page.locator('.home-again .d6-ph').evaluate_all("els=>els.map(e=>[e.offsetWidth,e.offsetHeight])")
    assert boxes and all(r==[84,84] for r in boxes)
    return {'categories':len(cats),'logos':boxes}


def published_top(browser):
    # Fetch only the deployed public customer UI. Its data source in this test is
    # the approved QA catalogue, including order history for the repeat-order rail.
    ctx=browser.new_context(viewport={'width':430,'height':932},service_workers='block',is_mobile=True)
    ctx.add_init_script("localStorage.setItem('tlb_lang','ru')")
    def route(r):
        from urllib.parse import urlsplit
        u=urlsplit(r.request.url)
        if u.hostname=='cdn.jsdelivr.net' and 'supabase-js' in u.path:
            return r.fulfill(content_type='application/javascript',body=qa.SDK.replace('window.__ROLE','"customer"'))
        if u.hostname==PREVIEW.split('//')[1] and r.request.method=='GET':
            return r.continue_()
        r.abort()
    ctx.route('**/*',route)
    page=ctx.new_page()
    response=page.goto(PREVIEW+'/customer',wait_until='domcontentloaded')
    assert response.ok
    expected=subprocess.check_output(['git','show',BASE+':customer.html'])
    assert response.body()==expected
    page.locator('.home-again .d6-lo').first.wait_for()
    info=top_geometry(page);ctx.close()
    return info
