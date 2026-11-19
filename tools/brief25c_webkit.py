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


def test_dineout(browser,server,photos,out):
    # A missing cover must reveal the actual supplied store brand, not a white blank.
    extra="""stores[0].discount_pct=7;
      stores.push({...stores[0],id:'s5',name:'Cafe fixture 5',discount_pct:10},
                  {...stores[1],id:'s6',name:'Cafe fixture 6',discount_pct:12,cover_url:''});"""
    ctx,page=prior.page_for(browser,server,photos,extra)
    try:
        cards=page.locator('.home-dine .d6-dc')
        assert cards.count()>=4
        assert cards.first.locator('.dine-cover-photo').count()==1
        assert cards.first.locator('.dish-store-logo img').count()==1
        missing=cards.filter(has_text='Cafe fixture 6')
        assert missing.count()==1
        assert missing.locator('.dine-cover-photo').count()==0
        assert missing.locator('.dine-fallback-mark').count()==1
        assert missing.locator('.dish-store-logo img').count()==1
        assert missing.locator('.dine-brand-cover').evaluate("e=>getComputedStyle(e).backgroundColor")!='rgb(255, 255, 255)'
        for card in cards.all():
            corner=card.locator('.dish-store-logo').bounding_box()
            cover=card.locator('.dine-brand-cover').bounding_box()
            assert corner and cover and corner['x']+corner['width']<=cover['x']+cover['width']+1
            assert abs((corner['x']+corner['width'])-(cover['x']+cover['width']))<14
        cards.first.locator('.dine-cover-photo').evaluate("e=>e.loading='eager'")
        missing.locator('.dine-fallback-mark').evaluate("e=>e.loading='eager'")
        page.wait_for_function("()=>[...document.querySelectorAll('.home-dine .d6-dc .dine-fallback-mark')].some(e=>e.complete&&e.naturalWidth>0)")
        page.locator('.home-dine').scroll_into_view_if_needed()
        prior.shot(page,out,'ru-375-dineout-branded-fallback-fixture.webp')
    finally:
        ctx.close()
    # Also verify a broken nonempty cover URL falls back after an actual load failure.
    ctx,page=prior.page_for(browser,server,photos,extra.replace("cover_url:''","cover_url:'/qa-image/broken'"))
    try:
        missing=page.locator('.home-dine .d6-dc').filter(has_text='Cafe fixture 6')
        missing.locator('.dine-cover-photo').evaluate("e=>e.loading='eager'")
        page.wait_for_function("()=>![...document.querySelectorAll('.home-dine .d6-dc')].some(e=>e.textContent.includes('Cafe fixture 6')&&e.querySelector('.dine-cover-photo'))")
        assert missing.locator('.dine-fallback-mark').count()==1
        assert missing.locator('.dish-store-logo img').count()==1
    finally:
        ctx.close()


def test_reel_badges(browser,server,photos,out):
    ctx,page=prior.page_for(browser,server,photos)
    try:
        page.locator('.reel-card').nth(1).click()
        viewer=page.locator('.reel-viewer[open]')
        page.wait_for_function("()=>{const e=document.querySelector('.reel-feed');return !!e&&e.scrollTop>=e.clientHeight*.75}")
        hot=viewer.locator('.reel-pane').nth(1)
        assert hot.locator('.reel-title-row strong').inner_text()=='Hot honey'
        deal=hot.locator('.reel-badges .reel-deal')
        assert deal.inner_text()=='−5%',deal.inner_text()
        dealbox=deal.bounding_box()
        back=viewer.locator('.reel-back').bounding_box()
        assert dealbox and back and dealbox['x']<40 and dealbox['y']>back['y']+back['height']-1,(dealbox,back)
        assert hot.locator('.reel-social>*').count()==0, 'No synthetic stats without fixture API'
        prior.shot(page,out,'ru-375-reel-dish-discount-fixture.webp')
        # The offer reel has both red pills in the same top-left horizontal band.
        viewer.locator('.reel-pages button').last.click()
        offer=viewer.locator('.reel-pane').last
        page.wait_for_function("()=>{const e=document.querySelector('.reel-feed');return e.scrollTop>=e.clientHeight*(e.children.length-1)-3}")
        assert offer.locator('.reel-badges .reel-deal').inner_text()=='−20%'
        assert offer.locator('.reel-badges .reel-offer').inner_text()=='Акция'
        prior.shot(page,out,'ru-375-reel-offer-badges-fixture.webp')
        viewer.locator('.reel-back').click()
    finally:
        ctx.close()


def test_comment_sheet(browser,server,photos,out):
    ctx,page=prior.page_for(browser,server,photos)
    try:
        prior.linked_reel_fixture(page)
        # Synthetic QA-only author/time metadata, never inserted into customer defaults.
        page.evaluate("""()=>{TalabotReelStats.read=async id=>({
          likes:37,liked:false,views:215,comments:[
            {author:'Анна QA',text:'Тестовый комментарий · fixture',created_at:'2026-11-19T09:35:00Z'},
            {author:'Демо Никита',text:'Demo only · fixture',created_at:'2026-11-19T09:42:00Z'}]})}""")
        page.locator('.reel-card').nth(1).click()
        viewer=page.locator('.reel-viewer[open]')
        page.wait_for_function("()=>{const e=document.querySelector('.reel-feed');return !!e&&e.scrollTop>=e.clientHeight*.75}")
        pane=viewer.locator('.reel-pane').nth(1)
        pane.locator('.reel-comment').wait_for()
        pane.locator('.reel-comment').click()
        sheet=page.locator('.reel-comments[open]')
        sheet.wait_for()
        rows=sheet.locator('.reel-chat-list .reel-chat-item')
        assert rows.count()==2
        assert rows.nth(0).locator('.reel-chat-avatar').inner_text()=='А'
        assert rows.nth(0).locator('.reel-chat-byline strong').inner_text()=='Анна QA'
        assert rows.nth(0).locator('.reel-chat-byline time').count()==1
        assert rows.nth(0).locator('.reel-chat-text').inner_text()=='Тестовый комментарий · fixture'
        assert sheet.locator('.reel-chat-grip').count()==1
        assert sheet.evaluate("e=>e.querySelector('.reel-chat-heading h2')===document.activeElement")
        assert sheet.locator('.reel-chat-close').evaluate("e=>document.activeElement!==e")
        assert sheet.locator('.reel-chat-close svg').count()==1
        assert sheet.locator('.reel-comment-form .reel-chat-send svg').count()==1
        assert sheet.locator('.reel-chat-list').evaluate("e=>getComputedStyle(e).listStyleType")=='none'
        assert sheet.locator('.reel-chat-close').evaluate("e=>getComputedStyle(e).borderTopStyle")=='none'
        assert sheet.locator('.reel-comment-form input').evaluate("e=>parseFloat(getComputedStyle(e).borderTopLeftRadius)")>=14
        assert sheet.evaluate("e=>parseFloat(getComputedStyle(e).borderTopLeftRadius)")>=20
        prior.shot(page,out,'ru-375-reel-comments-designed-final-fixture.webp')
        sheet.locator('.reel-chat-close').click()
        assert page.locator('.reel-comments[open]').count()==0
        viewer.locator('.reel-back').click()
    finally:
        ctx.close()


def test_reel_linked_badges(browser,server,photos,out):
    """Y-06: one genuine original-app WebKit screenshot of badges AND optional linked stats."""
    ctx,page=prior.page_for(browser,server,photos)
    try:
        # The adapter below is injected only in this disposable QA page, NEVER product HTML.
        prior.linked_reel_fixture(page)
        page.locator('.reel-card').nth(1).click()
        viewer=page.locator('.reel-viewer[open]')
        page.wait_for_function("()=>{const f=document.querySelector('.reel-feed');return f&&f.scrollTop>=f.clientHeight*.75}")
        pane=viewer.locator('.reel-pane').nth(1)
        deal=pane.locator('.reel-badges .reel-deal')
        assert deal.inner_text()=='−5%'
        like=pane.locator('.reel-avatar .reel-like')
        comment=pane.locator('.reel-social .reel-comment')
        views=pane.locator('.reel-social > span[aria-label]')
        like.wait_for()
        assert comment.count()==1 and views.count()==1
        assert '37' in like.inner_text() and '2' in comment.inner_text() and views.inner_text()=='215'
        assert pane.locator('.reel-title-row strong').inner_text()=='Hot honey'
        for loc in (deal,like,comment,views):
            assert loc.is_visible()
            bounds=loc.bounding_box()
            assert bounds and 0<=bounds['x']<375 and 0<=bounds['y']<812,bounds
        prior.shot(page,out,'ru-375-reel-badges-and-social-linked-fixture.webp')
        viewer.locator('.reel-back').click()
    finally:
        ctx.close()

def main():
    import sys
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    server=prior.qa.serve(ROOT)
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            photos=prior.fixture_logos(prior.qa.source_photos())
            test_dineout(browser,server,photos,out)
            test_reel_badges(browser,server,photos,out)
            test_reel_linked_badges(browser,server,photos,out)
            test_comment_sheet(browser,server,photos,out)
            ctx,page=prior.page_for(browser,server,photos)
            try:
                result={'Y-01':test_flash(page,out),'Y-02':'PASS','Y-03':'PASS','Y-04':'PASS'}
            finally:
                ctx.close();browser.close()
    finally:
        server.shutdown()
    (out/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print('BRIEF-25c Y-01..Y-04 PASS')

if __name__=='__main__':
    main()
