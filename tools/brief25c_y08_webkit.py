"""BRIEF-25c Y-08: offline WebKit vote contract and original customer card/viewer parity."""
import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import brief25b_webkit as prior

ROOT=Path.cwd()
def linked_fixture(page):
    # This adapter and its numbers never ship with the app. It tests consumer UI only.
    page.evaluate("""() => {
      window.__votes={states:{},calls:[]};
      for(const c of homeReels)window.__votes.states[c.id]={
        likes:37,liked:false,disliked:false,
        comments:[{text:'Synthetic QA one'},{text:'Synthetic QA two'}],views:215};
      window.TalabotReelStats={
        read:async id=>({...window.__votes.states[id]}),
        toggleLike:async id=>{const s=window.__votes.states[id];window.__votes.calls.push(['like',id]);
          s.likes+=s.liked?-1:1;s.liked=!s.liked;return {...s}},
        toggleDislike:async id=>{const s=window.__votes.states[id];window.__votes.calls.push(['dislike',id]);
          s.disliked=!s.disliked;return {...s}},
        comment:async()=>true,
        views:async()=>true,taps:async()=>true
      };
      observeReelMedia();
    }""")

def state(page,id):
    return page.evaluate("id=>({...__votes.states[id],calls:__votes.calls.filter(x=>x[1]===id)})",id)

def test_cards(page,out):
    cards=page.locator('.reel-card')
    assert cards.count()>=4
    assert page.locator('.reel-tile').count()==cards.count()
    assert page.locator('.reel-feedback button').count()==0, 'Disconnected adapter must be invisible'
    # Earlier stats provider only supported likes: do not show a half-working vote pill.
    prior.linked_reel_fixture(page)
    page.evaluate("observeReelMedia()")
    assert page.locator('.reel-feedback button').count()==0
    linked_fixture(page)
    tile=page.locator('.reel-tile').first
    tile.scroll_into_view_if_needed()
    page.wait_for_function("""()=>document.querySelector('.reel-tile .reel-feedback:not([hidden]) button[data-reaction="like"]')!=null""")
    like=tile.locator('button[data-reaction=like]')
    dislike=tile.locator('button[data-reaction=dislike]')
    id=tile.get_attribute('data-reel-key')
    assert like.locator('svg').count()==1 and dislike.locator('svg').count()==1
    assert like.locator('span').inner_text()=='37'
    assert dislike.locator('span').count()==0
    assert like.get_attribute('aria-pressed')=='false'
    assert dislike.get_attribute('aria-pressed')=='false'
    assert tile.evaluate("""e=>!e.querySelector('.reel-card button')&&!!e.querySelector('button.reel-card')""")
    assert tile.evaluate("e=>getComputedStyle(e.querySelector('.reel-feedback')).backgroundColor")!='rgba(0, 0, 0, 0)'
    prior.shot(page,out,'ru-375-reels-like-dislike-linked-fixture.webp')

    like.click()
    page.wait_for_function("()=>document.querySelector('.reel-tile .reel-feedback [data-reaction=like] span')?.textContent==='38'")
    assert page.locator('.reel-viewer').count()==0 and state(page,id)['liked'] and not state(page,id)['disliked']
    prior.shot(page,out,'ru-375-reels-like-active-fixture.webp')
    # Same customer toggling removes the existing like; no duplicate increment.
    like=tile.locator('button[data-reaction=like]');like.click()
    page.wait_for_function("()=>document.querySelector('.reel-tile .reel-feedback [data-reaction=like] span')?.textContent==='37'")
    assert not state(page,id)['liked'] and state(page,id)['likes']==37
    # Dislike is counted only in the linked provider, never exposed as a number.
    dislike=tile.locator('button[data-reaction=dislike]');dislike.click()
    page.wait_for_function("()=>document.querySelector('.reel-tile .reel-feedback [data-reaction=dislike]')?.getAttribute('aria-pressed')==='true'")
    assert state(page,id)['disliked'] and not state(page,id)['liked']
    assert tile.locator('button[data-reaction=dislike] span').count()==0
    # Switch dislike -> like: client clears opposite vote first.
    like=tile.locator('button[data-reaction=like]');like.click()
    page.wait_for_function("()=>document.querySelector('.reel-tile .reel-feedback [data-reaction=like] span')?.textContent==='38'")
    s=state(page,id)
    assert s['liked'] and not s['disliked'] and s['likes']==38
    assert s['calls'][-2:]==[['dislike',id],['like',id]],s
    # Switch like -> dislike and then undo it.
    dislike=tile.locator('button[data-reaction=dislike]');dislike.click()
    page.wait_for_function("()=>document.querySelector('.reel-tile .reel-feedback [data-reaction=dislike]')?.getAttribute('aria-pressed')==='true'")
    s=state(page,id)
    assert not s['liked'] and s['disliked'] and s['likes']==37
    assert s['calls'][-2:]==[['like',id],['dislike',id]],s
    tile.locator('button[data-reaction=dislike]').click()
    page.wait_for_function("()=>document.querySelector('.reel-tile .reel-feedback [data-reaction=dislike]')?.getAttribute('aria-pressed')==='false'")
    assert not state(page,id)['disliked'] and not state(page,id)['liked']
    assert page.locator('.reel-viewer').count()==0
    # Synchronize the identical provider-derived count with the full-screen viewer.
    tile.locator('button[data-reaction=like]').click()
    page.wait_for_function("()=>document.querySelector('.reel-tile .reel-feedback [data-reaction=like] span')?.textContent==='38'")
    tile.locator('button.reel-card').click()
    viewer=page.locator('.reel-viewer[open]')
    viewer.wait_for()
    pane=viewer.locator('.reel-pane').first
    pane.locator('.reel-avatar .reel-like').wait_for()
    assert '38' in pane.locator('.reel-avatar .reel-like').inner_text()
    pane.locator('.reel-avatar .reel-like').click()
    page.wait_for_function("()=>document.querySelector('.reel-tile .reel-feedback [data-reaction=like] span')?.textContent==='37'")
    assert not state(page,id)['liked'] and state(page,id)['likes']==37
    viewer.locator('.reel-back').click()
    assert tile.locator('button[data-reaction=like] span').inner_text()=='37'
    return {'card_count':cards.count(),'like_dislike_undo':'PASS','mutual_exclusion':'PASS',
            'no_viewer_from_pill':'PASS','viewer_counter_parity':'PASS'}

def test_combined_y06(page,out):
    # Fullscreen: top-left source discount + linked likes/comments/views together.
    card=page.locator('.reel-card').nth(1);card.scroll_into_view_if_needed()
    page.wait_for_function("()=>document.querySelectorAll('.reel-tile .reel-feedback:not([hidden])').length>=2")
    card.click()
    viewer=page.locator('.reel-viewer[open]')
    page.wait_for_function("()=>{const f=document.querySelector('.reel-feed');return !!f&&f.scrollTop>=f.clientHeight*.75}")
    pane=viewer.locator('.reel-pane').nth(1)
    assert pane.locator('.reel-badges .reel-deal').inner_text()=='−5%'
    like=pane.locator('.reel-avatar .reel-like')
    like.wait_for()
    assert like.is_visible() and '37' in like.inner_text()
    assert pane.locator('.reel-social .reel-comment').is_visible()
    assert pane.locator('.reel-social > span[aria-label]').inner_text()=='215'
    prior.shot(page,out,'ru-375-y06-y08-reel-badges-social-linked-fixture.webp')
    viewer.locator('.reel-back').click()
    return 'PASS'

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    server=prior.qa.serve(ROOT)
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            photos=prior.fixture_logos(prior.qa.source_photos())
            ctx,page=prior.page_for(browser,server,photos)
            try:
                card_report=test_cards(page,out)
                y06=test_combined_y06(page,out)
            finally:
                ctx.close();browser.close()
    finally:
        server.shutdown()
    report={'Y-08':card_report,'Y-06':y06}
    (out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('BRIEF-25c Y-06/Y-08 WebKit PASS')

if __name__=='__main__':
    main()
