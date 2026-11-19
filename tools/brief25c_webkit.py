"""BRIEF-25c: independent synthetic WebKit checks for owner-only visual changes."""
from pathlib import Path
import os
import json
from playwright.sync_api import sync_playwright

import brief25b_webkit as prior

ROOT=Path.cwd()

def test_flash(page,out):
    grid=page.locator('.home-flash .flash-grid')
    assert grid.locator('.flash-item').count()==2
    measurements=grid.evaluate("""e=>{
      const rail=e.getBoundingClientRect();
      const a=[...e.children].map(x=>{
        const r=x.getBoundingClientRect();
        const photo=x.querySelector('.d6-ph').getBoundingClientRect();
        const price=x.querySelector('.px'),style=getComputedStyle(price),box=price.getBoundingClientRect();
        const name=getComputedStyle(x.querySelector('.flash-description>b'));
        return {x:r.x,right:r.right,width:r.width,y:r.y,photoWidth:photo.width,
          priceWhiteSpace:style.whiteSpace,priceHeight:box.height,priceLineHeight:parseFloat(style.lineHeight),
          titleClamp:name.webkitLineClamp};
      });
      return {right:rail.right,flow:getComputedStyle(e).gridAutoFlow,a};
    }""")
    first,second=measurements['a']
    assert measurements['flow']=='row',measurements
    assert 215<=first['width']<=230 and first['right']<measurements['right'],measurements
    assert second['x']<measurements['right']<second['right'],measurements
    assert abs(first['y']-second['y'])<1,measurements
    for x in (first,second):
        assert abs(x['photoWidth']-88)<1,x
        assert x['priceWhiteSpace']=='nowrap' and x['titleClamp']=='2',x
        assert x['priceHeight']<=x['priceLineHeight']*1.1,x
    grid.scroll_into_view_if_needed()
    prior.shot(page,out,'ru-375-flash-one-and-half-fixture.webp')
    return measurements

def main():
    import sys
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    server=prior.qa.serve(ROOT)
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            photos=prior.fixture_logos(prior.qa.source_photos())
            ctx,page=prior.page_for(browser,server,photos)
            try:
                result={'Y-01':test_flash(page,out)}
            finally:
                ctx.close();browser.close()
    finally:
        server.shutdown()
    (out/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print('BRIEF-25c Y-01 PASS')

if __name__=='__main__':
    main()
