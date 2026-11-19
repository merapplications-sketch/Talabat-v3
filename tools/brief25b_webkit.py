"""TALABOT BRIEF-25b: offline WebKit QA only; never use real endpoints or data."""
import io
import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

from qa_all import FIX
from brief24_webkit import qa, SEED

ROOT=Path.cwd()
CATALOG=json.loads((ROOT/'qa-fixtures/home-brief25b.json').read_text(encoding='utf8'))

def fixture_logos(photos):
    # PRO.хинкали fixture branding is deliberately synthesized; not a production asset.
    logo=Image.new('RGB',(220,220),(247,241,232))
    brush=ImageDraw.Draw(logo)
    brush.rounded_rectangle((8,8,212,212),radius=30,fill=(159,54,31))
    path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if Path(path).exists():
        big=ImageFont.truetype(path,58)
        small=ImageFont.truetype(path,23)
        brush.text((37,59),'PRO.',font=big,fill='white')
        brush.text((46,132),'хинкали',font=small,fill='white')
    else:
        brush.text((71,82),'PRO.',fill='white')
    buf=io.BytesIO();logo.save(buf,format='JPEG',quality=95)
    photos['pro-khinkali']=buf.getvalue()
    return photos

def test_owner_fixture(page):
    assert len(CATALOG['stores'])==4
    assert page.locator('.home-l-near .home-l-card').count()==4
    assert page.locator('.home-l-near .home-l-card.closed').count()==1
    romant=page.locator('.home-l-near .home-l-card').filter(has_text='Romant')
    assert romant.locator('img[src="/qa-image/pro-khinkali"]').count()==1
    assert '3.4' in romant.inner_text() and '(11)' in romant.inner_text()
    kfc=page.locator('.home-l-near .home-l-card').filter(has_text='KFC')
    assert kfc.count()==1 and not kfc.is_disabled() and kfc.locator('img[src="/qa-image/kfc"]').count()==1

def page_for(browser,server,photos,extra=''):
    seed='const catalog='+json.dumps(CATALOG,ensure_ascii=False)+';\n'+SEED+extra+'\n'
    qa.SDK=FIX.replace(qa.FINISH_SEED,seed+qa.FINISH_SEED)
    return qa.page_at(browser,server,photos,'ru',375)

def shot(page,out,name):
    assert name.endswith('.webp')
    image=Image.open(io.BytesIO(page.screenshot(animations='disabled'))).convert('RGB')
    image.save(out/name,quality=85,method=6)

def linked_reel_fixture(page):
    # Isolated JavaScript QA injection only. No app product defaults, no API, no storage.
    page.evaluate("""() => {
      window.__brief25bStats={views:[],taps:[]};
      window.TalabotReelStats={
        views:async id=>{__brief25bStats.views.push(id)},
        taps:async id=>{__brief25bStats.taps.push(id)},
        read:async id=>({likes:37,liked:false,views:215,comments:[
          {text:'Тестовый комментарий · fixture'},{text:'Demo only · fixture'}]}),
        toggleLike:async()=>true,
        comment:async()=>true
      };
    }""")

def test_recommended(page,out):
    # Best dishes and sponsorship exist only in the QA catalogue, not product defaults.
    page.evaluate("data=>{TLB.bestDishes=()=>data;render()}",CATALOG['best_dishes'])
    recommended=page.locator('section.home-picks:not(.home-meals)')
    assert recommended.count()==1 and recommended.locator('.d6-pt').count()>=2
    assert recommended.locator('.home-ad-label').first.inner_text()=='Реклама'
    headings=page.locator('.home-heading').evaluate_all("nodes=>nodes.map(n=>n.dataset.section)")
    assert headings.index('advert')<headings.index('picks'),headings
    page.locator('[data-section="advert"]').evaluate("e=>window.scrollTo(0,window.scrollY+e.getBoundingClientRect().top-10)")
    shot(page,out,'ru-375-recommended-after-ad-fixture.webp')

def test_l_card_metadata(page):
    # Supply known synthetic measured prep time only inside the disposable browser fixture.
    page.evaluate("()=>{TLB.speed=()=>({min:20});render()}")
    for section in ('.home-l-offers','.home-l-near'):
        romant=page.locator(section+' .home-l-card').filter(has_text='Romant')
        assert '3.4' in romant.locator('.home-l-rating').inner_text()
        assert '(11)' in romant.locator('.home-l-rating').inner_text()
        metadata=romant.locator('.home-l-meta').inner_text()
        assert ' · ' in metadata and 'TJS' in metadata,metadata

def test_reels(page,out):
    cards=page.locator('.reel-card')
    assert cards.count()>=2,'Needs a second sample reel'
    cards.nth(1).click()
    viewer=page.locator('.reel-viewer[open]')
    viewer.wait_for()
    assert viewer.locator('.reel-social>*').count()==0,'Unbound social UI must stay hidden'
    viewer.locator('.reel-back').click()
    page.wait_for_function("!document.querySelector('.reel-viewer')")
    linked_reel_fixture(page)
    cards=page.locator('.reel-card')
    cards.nth(1).click()
    viewer=page.locator('.reel-viewer[open]')
    pane=viewer.locator('.reel-pane').nth(1)
    pane.locator('.reel-like').wait_for()
    assert pane.locator('.reel-comment').count()==1
    assert '37' in pane.inner_text() and '215' in pane.inner_text()
    assert viewer.locator('.reel-pages button').count()>=2
    shot(page,out,'ru-375-reels-second-linked-fixture.webp')
    pane.locator('.reel-comment').click()
    page.locator('.reel-comments[open]').wait_for()
    assert 'Тестовый комментарий' in page.locator('.reel-comments').inner_text()
    shot(page,out,'ru-375-reels-second-comments-fixture.webp')
    page.locator('.reel-comments form[method="dialog"] button').click()
    viewer.locator('.reel-back').click()

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    server=qa.serve(ROOT)
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            photos=fixture_logos(qa.source_photos())
            ctx,page=page_for(browser,server,photos)
            try:
                test_owner_fixture(page)
                test_l_card_metadata(page)
                test_recommended(page,out)
                test_reels(page,out)
            finally:
                ctx.close()
                browser.close()
    finally:
        server.shutdown()

if __name__=='__main__':
    main()
