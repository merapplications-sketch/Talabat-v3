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
        heading=page.locator('.dine-head')
        image=heading.get_by_role('img',name='DineOut — Скидка до 50% на счёт')
        action=heading.get_by_role('button',name='Все')
        assert image.get_attribute('src')=='assets/customer-c/dineout-header.webp'
        page.wait_for_function("()=>document.querySelector('.dine-head img').naturalWidth===750")
        assert image.evaluate("i=>i.naturalHeight===250")
        assert action.is_visible()
        assert action.get_attribute('aria-label')=='Все'
        assert action.inner_text().strip()==''
        assert action.locator('svg').count()==1
        assert page.locator('.home-heading:not(.dine-head) button').filter(has_text='Все').first.is_visible()
        assert heading.evaluate("""e=>{
          const section=e.getBoundingClientRect();
          const art=e.querySelector('img').getBoundingClientRect();
          const link=e.querySelector('button').getBoundingClientRect();
          const cover=e.nextElementSibling.querySelector('.dine-brand-cover').getBoundingClientRect();
          return Math.abs(art.width-(section.width-52))<1
            && Math.abs(art.height-art.width/3)<1
            && Math.abs(art.left-section.left)<1 && Math.abs(link.right-section.right)<1
            && Math.abs(link.left-art.right-12)<1
            && link.width===40 && link.height===40
            && Math.abs((link.top+link.bottom-art.top-art.bottom)/2)<1
            && Math.abs(art.top-section.top-16)<1
            && Math.abs(cover.top-section.bottom-12)<1;
        }""")
        assert page.locator('.d6-dn').count()==0
        widths=cards.evaluate_all("nodes=>nodes.slice(0,3).map(n=>n.getBoundingClientRect().width)")
        assert all(208<=w<=260 for w in widths),widths
        rail=page.locator('.home-dine')
        assert rail.evaluate("e=>e.scrollWidth>e.clientWidth")
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
            assert abs(corner['x']-cover['x']-8)<1
            assert abs((corner['y']+corner['height'])-(cover['y']+cover['height']))<14
            badge=card.locator('.dine-brand-cover .hb').bounding_box()
            assert badge and abs(badge['y']-cover['y']-9)<1
            assert badge['y']+badge['height']<corner['y'],(badge,corner)
        first=cards.first
        assert first.locator('.dine-meta .rt').count()==1
        assert first.locator('.dine-bill-distance').count()==1
        assert 'на двоих' not in first.locator('.dine-bill-distance').inner_text()
        a,b=cards.nth(0).bounding_box(),cards.nth(1).bounding_box()
        assert a and b and a['x']<b['x']<375<b['x']+b['width'],(a,b)
        cards.first.locator('.dine-cover-photo').evaluate("e=>e.loading='eager'")
        missing.locator('.dine-fallback-mark').evaluate("e=>e.loading='eager'")
        page.wait_for_function("()=>[...document.querySelectorAll('.home-dine .d6-dc .dine-fallback-mark')].some(e=>e.complete&&e.naturalWidth>0)")
        page.locator('.dine-head').scroll_into_view_if_needed()
        prior.shot(page,out,'ru-375-dineout-y11-fixture.webp')
        heading.get_by_role('button',name='Все').click()
        assert page.locator('.dine-head').count()==0
        assert page.locator('.home-dine .d6-dc').count()>=4
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


    # Optional future frontend binding: show an amount only if fixture explicitly provides it.
    ctx,page=prior.page_for(browser,server,photos,extra+";stores[1].dineout_price_for_two_tjs=270;")
    try:
        card=page.locator('.home-dine .d6-dc').filter(has_text='Romant Restaurant')
        assert '≈ 270 TJS на двоих' in card.locator('.dine-bill-distance').inner_text()
        card.click()
        assert page.evaluate("S.v==='menu' && S.store==='Romant Restaurant'")
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

def test_brief26(browser, server, photos, out):
    from datetime import datetime, timezone
    from io import BytesIO
    from PIL import Image

    seed = """
      orders.push({...orders[0],id:'romant-previous',store_id:'s2'});
      stores.forEach(s=>{delete s.home_reels;s.created_at=iso(90*24*60)});
      stores[0].fee_type='free';
      T.happy_hours=[
        {id:'hh-r',store_id:'s2',days:[3],start_time:'13:00:00',end_time:'14:12:20',discount_pct:20,active:true},
        {id:'hh-k',store_id:'s1',days:[3],start_time:'13:00:00',end_time:'14:12:20',discount_pct:5,active:true},
        {id:'hh-c',store_id:'s4',days:[3],start_time:'13:00:00',end_time:'14:12:20',discount_pct:30,active:true}
      ];
      for(const [id,placement,title,link_value,image_url] of [
        ['hh-art','top','Счастливые часы','s2','/qa-image/romant'],
        ['ad-r','top','Top Romant','s2','/qa-image/romant'],
        ['ad-k','top','Top KFC','s1','/qa-image/kfc'],
        ['ad-next','top','Top KFC next','s1','/qa-image/kfc'],
        ['miss-r','dont_miss','Romant offer','s2','/qa-image/romant'],
        ['miss-k','dont_miss','KFC offer','s1','/qa-image/kfc']
      ])T.banners.push({id,placement,title,link_value,image_url,link_type:'store',is_active:true});
    """
    ctx,page=prior.page_for(browser,server,photos,seed)
    try:
        page.emulate_media(reduced_motion='reduce')
        tile=page.locator('.d6-bt.k-hap')
        assert tile.locator('img').get_attribute('src')=='/qa-image/romant'
        assert tile.locator('.hcd').inner_text()=='12:20'
        assert tile.locator('.cd').evaluate("e=>getComputedStyle(e).backgroundColor")=='rgb(255, 255, 255)'
        assert page.locator('.home-flash').evaluate("e=>e.getBoundingClientRect().top-e.previousElementSibling.getBoundingClientRect().bottom")>=16
        assert page.locator('.home-dine-section').evaluate("""e=>e.contains(e.querySelector('.dine-head button'))
          && !!e.querySelector('.home-dine .d6-dc') && getComputedStyle(e).backgroundColor==='rgb(247, 243, 238)'
          && getComputedStyle(e.querySelector('.dine-head img')).mixBlendMode==='multiply'""")
        assert page.locator('.hdt').evaluate('''e=>{
          const dots=e.getBoundingClientRect(), rail=e.previousElementSibling.getBoundingClientRect();
          return Math.abs(rail.bottom-dots.bottom-12)<1 && dots.top>=rail.top &&
            dots.left>=rail.left && dots.right<=rail.right;
        }''')
        assert page.locator('.home-ad-dots').evaluate("e=>getComputedStyle(e).position")=='absolute'
        assert page.evaluate("()=>['KFC','Romant Restaurant'].every(n=>triedRestaurants().has(n))")
        assert page.locator('.home-discover .reel-tile[data-reel-key^="restaurant:"]').count()==0
        assert {'−20%', '−5%'} <= set(page.locator('.home-discover .reel-deal').all_inner_texts())
        page.evaluate("""()=>{document.querySelectorAll('.d6h img').forEach(i=>i.loading='eager');scrollTo(0,0)}""")
        page.wait_for_function("()=>[...document.querySelectorAll('.d6h img')].every(i=>i.complete&&i.naturalWidth>0)")
        full=page.screenshot(full_page=True,animations='disabled',style='body{position:relative}#app .nav{position:absolute}')
        Image.open(BytesIO(full)).convert('RGB').save(out/'ru-375-home-brief26-fixture.webp',quality=90,method=6)

        page.locator('#hsc button').filter(has=page.get_by_alt_text('Top KFC next')).click()
        assert page.evaluate("S.v==='menu'&&S.store==='KFC'")
        page.evaluate("go('home')")
        page.locator('.d6-bt').filter(has=page.get_by_alt_text('Top Romant',exact=True)).click()
        assert page.evaluate("S.v==='menu'&&S.store==='Romant Restaurant'")
        page.evaluate("go('home')")
        for title,store in [('Скидка 5% в KFC','KFC'),('Скидка 20% в Romant Restaurant','Romant Restaurant')]:
            page.locator('.home-ad-card').filter(has=page.get_by_text(title,exact=True)).click()
            assert page.evaluate("name=>S.v==='menu'&&S.store===name",store)
            page.evaluate("go('home')")

        tile.click()
        sheet=page.get_by_role('dialog',name='Счастливые часы')
        assert sheet.is_visible() and sheet.locator('.hcd').inner_text()=='12:20'
        stores=sheet.locator('.hh-sheet-store')
        assert stores.count()==3 and stores.last.is_disabled()
        assert stores.last.locator('.hh-sheet-copy > b').first.inner_text()=='Закрытый ресторан QA'
        assert '−20% до 14:12' in stores.first.inner_text()
        assert '−5% до 14:12' in stores.nth(1).inner_text()
        page.evaluate("document.activeElement.blur()")
        prior.shot(page,out,'ru-375-happy-hours-brief26-fixture.webp')
        sheet.locator('.hh-sheet-close').click()
        sheet.wait_for(state='detached')
        tile.click()
        sheet.locator('.hh-sheet-store').first.click()
        assert page.evaluate("S.v==='menu'&&S.store==='Romant Restaurant'")
        page.evaluate("go('home')")
        tile.click()
        page.clock.set_fixed_time(datetime(2026,11,18,9,0,1,tzinfo=timezone.utc))
        page.wait_for_function("""()=>[...document.querySelectorAll('.hcd')].length===2
          && [...document.querySelectorAll('.hcd')].every(e=>e.textContent==='12:19')""")
        page.clock.set_fixed_time(datetime(2026,11,18,9,12,20,tzinfo=timezone.utc))
        sheet.wait_for(state='detached')
        tile.wait_for(state='detached')
        assert page.get_by_alt_text("Счастливые часы",exact=True).count()==0
    finally:
        ctx.close()

    ctx,page=prior.page_for(browser,server,photos,seed.replace("'/qa-image/romant'],\n        ['ad-r'","null],\n        ['ad-r'",1))
    try:
        assert page.locator('.d6-bt.k-hap:not(.img) .hcd').inner_text()=='12:20'
    finally:
        ctx.close()


    preview_seed=seed+"T.banners=T.banners.filter(b=>!b.id.startsWith('ad-'));"
    ctx,page=prior.page_for(browser,server,photos,preview_seed)
    try:
        page.emulate_media(reduced_motion='reduce')
        assert page.locator('.d6-bento > .k-free .tt').inner_text()=='Доставка бесплатно'
        assert page.locator('.d6-bento > .k-free img').get_attribute('src')=='assets/3d/motor-scooter.webp'
        happy=page.locator('.d6-bento > .k-hap.img')
        assert happy.locator('.tt').inner_text()=='Счастливые часы'
        assert happy.locator('.hcd').inner_text()=='12:20'
        assert page.locator('.d6-bm .hcd').count()==0
        assert happy.evaluate("""e=>{
          const img=e.querySelector('img').getBoundingClientRect(), cd=e.querySelector('.cd').getBoundingClientRect();
          const title=e.querySelector('.tt').getBoundingClientRect();
          return cd.left>=img.left && cd.top>=img.top && cd.bottom<=img.bottom && cd.right<=img.right
            && title.bottom<=cd.top;
        }""")
        assert page.locator('.home-ad-card b').first.inner_text()=='Скидка 20% в Romant Restaurant'
        kfc=page.locator('.home-dine .d6-dc').filter(has_text='KFC')
        assert kfc.locator('.dine-bill-distance').inner_text()=='< 100 м'
        assert not page.get_by_text('0 км',exact=True).count()
        page.evaluate("()=>{document.querySelectorAll('.d6h img').forEach(i=>i.loading='eager');scrollTo(0,0)}")
        page.wait_for_function("()=>[...document.querySelectorAll('.d6h img')].every(i=>i.complete&&i.naturalWidth>0)")
        full=page.screenshot(full_page=True,animations='disabled',style='body{position:relative}#app .nav{position:absolute}')
        Image.open(BytesIO(full)).convert('RGB').save(out/'ru-375-home-brief26b-fixture.webp',quality=90,method=6)
        # Unrounded 50–100 m must still be shown as below 100, and no longitude means no distance.
        assert page.evaluate("""()=>{
          const a=curAddr(), st=STORES.find(s=>s.n==='KFC');
          return distanceLabel({...st,la:a.lat+0.0007,lo:a.lng})==='< 100 м'
            && distanceLabel({...st,la:a.lat+0.001,lo:a.lng})==='0.1 км'
            && distanceLabel({...st,lo:null})==='';
        }""")
        page.evaluate("()=>{STORES.find(s=>s.n==='KFC').lo=null;render()}")
        assert kfc.locator('.dine-bill-distance').count()==0
    finally:
        ctx.close()

    ctx,page=prior.page_for(browser,server,photos,preview_seed,lang='en',width=390)
    try:
        page.emulate_media(reduced_motion='reduce')
        assert page.locator('.home-ad-card b').first.inner_text()=='20% off at Romant Restaurant'
        assert page.locator('.home-dine .d6-dc').filter(has_text='KFC').locator('.dine-bill-distance').inner_text()=='< 100 m'
        page.locator('[data-section="advert"]').evaluate("e=>scrollTo(0,scrollY+e.getBoundingClientRect().top-78)")
        prior.shot(page,out,'en-390-dont-miss-brief26b-fixture.webp')
    finally:
        ctx.close()


def test_brief27(browser,server,photos,out):
    from io import BytesIO
    from PIL import Image

    small_photos=dict(photos)
    for name in ('kfc','romant'):
        image=Image.open(BytesIO(photos[name])).convert('RGB').resize((300,200))
        output=BytesIO()
        image.save(output,format='JPEG',quality=89)
        small_photos[name]=output.getvalue()
    seed="""
      const keepPhoto=(id,title,url)=>({id,title,image_url:url,placement:'top',is_active:true});
      T.banners.push(keepPhoto('feature','Предложение','/qa-image/romant'),
        keepPhoto('free-art','Доставка бесплатно','/qa-image/kfc'),
        keepPhoto('pizza-art','Время пиццы','/qa-image/romant'));
    """
    check_image="""i=>{
      const css=getComputedStyle(i),image=i.getBoundingClientRect(),tile=i.parentNode.getBoundingClientRect();
      return i.naturalWidth===300 && i.naturalHeight===200 && css.objectFit==='cover' && css.objectPosition==='0% 50%'
        && ['left','top','right','bottom'].every(edge=>Math.abs(image[edge]-tile[edge])<1);
    }"""
    ctx,page=prior.page_for(browser,server,small_photos,seed)
    try:
        page.emulate_media(reduced_motion='reduce')
        for image in page.locator('.d6-bento > .d6-bt.img > img').all():
            image.evaluate('i=>i.decode()')
            assert image.evaluate(check_image)
        assert page.locator('.d6-bento > .d6-bt.img > img').count()==2
        prior.shot(page,out,'ru-375-side-banners-brief27-fixture.webp')
    finally:
        ctx.close()

    happy_seed="""
      stores[0].fee_type='free';
      T.happy_hours.push({id:'hh-photo',store_id:'s2',days:[3],start_time:'13:00:00',end_time:'14:12:20',discount_pct:20,active:true});
      T.banners.push({id:'small-hh',title:'Счастливые часы',image_url:'/qa-image/romant',placement:'top',is_active:true});
    """
    ctx,page=prior.page_for(browser,server,small_photos,happy_seed)
    try:
        page.emulate_media(reduced_motion='reduce')
        happy=page.locator('.d6-bento > .d6-bt.k-hap')
        happy.locator('img').evaluate('i=>i.decode()')
        assert happy.locator('img').evaluate(check_image)
        assert happy.locator('.hcd').is_visible() and happy.locator('.hcd').inner_text()=='12:20'
        prior.shot(page,out,'ru-375-happy-banner-brief27-fixture.webp')
        block=page.locator('.home-dine-section')
        geometry=block.evaluate("""e=>{const r=e.getBoundingClientRect(), before=e.previousElementSibling;
          return {gap:r.top-before.getBoundingClientRect().bottom, radius:getComputedStyle(e).borderTopLeftRadius,
            followsReels:before.classList.contains('home-discover')};
        }""")
        assert geometry['gap']>=24 and geometry['radius']=='20px' and geometry['followsReels'],geometry
        heading=page.locator('[data-section="discover"]')
        heading.evaluate("e=>scrollTo(0, scrollY+e.getBoundingClientRect().top-66)")
        page.evaluate("""()=>document.querySelectorAll('.home-discover img,.home-dine-section img').forEach(i=>i.loading='eager')""")
        page.wait_for_function("""()=>[...document.querySelectorAll('.home-discover img,.home-dine-section img')].every(i=>i.complete&&i.naturalWidth>0)""")
        prior.shot(page,out,'ru-375-dineout-separation-brief27-fixture.webp')
    finally:
        ctx.close()

    prior.qa.SDK=prior.FIX
    ctx,page=prior.qa.page_at(browser,server,small_photos,'ru',375,role='admin')
    try:
        page.evaluate("""()=>{TLB.uploadImage=async()=>'/qa-image/kfc';tab='b';showAddB=true;render()}""")
        assert page.get_by_text('1200×1260',exact=False).is_visible()
        page.locator('input[onchange="pickB(event)"]').set_input_files({
            'name':'small.jpg','mimeType':'image/jpeg','buffer':small_photos['kfc']})
        page.wait_for_function("()=>document.getElementById('banner-create-size')?.textContent.includes('300×200')")
        page.wait_for_function("()=>document.getElementById('bp')?.getAttribute('src')==='/qa-image/kfc'")
        page.evaluate("openBE(TLB.banners(true)[0].id)")
        assert page.get_by_text('900×600',exact=False).is_visible()
        page.locator('input[onchange="bannerImg(event)"]').set_input_files({
            'name':'small.jpg','mimeType':'image/jpeg','buffer':small_photos['romant']})
        page.wait_for_function("()=>BD.imageSize?.width===300 && document.getElementById('banner-edit-size').textContent.includes('300×200')")
        assert page.evaluate("""()=>bannerSizeWarning({width:1200,height:1260})===''
          && bannerSizeWarning({width:900,height:600}).includes('большого баннера')""")
    finally:
        ctx.close()


def test_brief29(browser,server,photos,out):
    # The BRIEF-30 restaurant-category replacement retains BRIEF-29 navigation
    # contracts but intentionally changes .d6-sr to the approved .ad30-card.
    def restaurant_names(page):
        if page.locator('.ad30-card').count():
            return page.locator('.ad30-card-name').all_inner_texts()
        return page.locator('.d6-sr .nt').all_inner_texts()
    seed="""
      stores[0].fee_type='free';
      stores[1].logo_url='/qa-image/pro-khinkali';
      const put=(id,title,target,presentation={},ends_at=null)=>T.banners.push({
        id,title,link_value:target,link_type:'store',placement:'top',is_active:true,presentation,ends_at,
        image_url:target==='s1'?'/qa-image/kfc':'/qa-image/romant'
      });
      put('cta-dish','KFC · Hot honey','s1',{action:'order',item_id:'hot'});
      put('side-free','Доставка бесплатно','s1');
      put('side-discount','Скидки до 20%','s2');
      put('cta-restaurant','Romant Restaurant','s2',{action:'restaurant'});
      put('cta-campaign','Скидки сегодня','s2',{action:'campaign',campaign:'discount',label:{ru:'Смотреть акцию'}},'2026-11-18T09:12:20Z');
      put('cta-filter','Бесплатная доставка','s1',{action:'list',filter:'free',label:{ru:'Смотреть доставку'}});
      put('orders-private','Только мои заказы','s1',{audience:'orders'});
    """
    ctx,page=prior.page_for(browser,server,photos,seed)
    try:
        page.emulate_media(reduced_motion='reduce')
        rail=page.locator('#hsc')
        def activate(index,text):
            rail.evaluate("(e,index)=>e.scrollTo(index*e.clientWidth,0)",index)
            button=rail.locator('button').nth(index)
            assert button.locator('.cta').inner_text()==text
            page.wait_for_function("""i=>{const e=document.querySelector('#hsc');return Math.abs(e.scrollLeft-i*e.clientWidth)<=1}""",arg=index)
            return button

        button=activate(0,'Заказать сейчас')
        prior.shot(page,out,'ru-375-brief29-slide-order.webp')
        button.click()
        assert page.evaluate("S.v==='menu'&&S.store==='KFC'&&S.sh?.id==='hot'")
        page.evaluate("S.sh=null;go('home')")
        button=activate(1,'Открыть ресторан')
        prior.shot(page,out,'ru-375-brief29-slide-restaurant.webp')
        button.click()
        assert page.evaluate("S.v==='menu'&&S.store==='Romant Restaurant'&&!S.sh")
        page.evaluate("go('home')")
        button=activate(2,'Смотреть акцию')
        assert button.locator('.hcd').inner_text()=='12:20'
        prior.shot(page,out,'ru-375-brief29-slide-campaign.webp')
        button.click()
        sheet=page.locator('.hh-sheet[open]')
        assert sheet.locator('.hcd').inner_text()=='12:20'
        assert sheet.locator('.hh-sheet-store').count()==1
        assert 'Romant Restaurant' in sheet.locator('.hh-sheet-store').inner_text()
        prior.shot(page,out,'ru-375-brief29-campaign-sheet.webp')
        sheet.locator('.hh-sheet-close').click()
        sheet.wait_for(state='detached')

        page.locator('.d6-bento > button').filter(has=page.get_by_alt_text('Доставка бесплатно',exact=True)).click()
        assert page.evaluate("S.v==='cat'&&S.catKey==='rest'&&S.srt==='free'")
        assert restaurant_names(page)==['KFC','Romant Restaurant'],restaurant_names(page)
        prior.shot(page,out,'ru-375-brief29-free-delivery.webp')
        page.evaluate("go('home')")
        page.locator('.d6-bento > button').filter(has=page.get_by_alt_text('Скидки до 20%',exact=True)).click()
        assert page.evaluate("S.v==='cat'&&S.catKey==='rest'&&S.srt==='disc'")
        assert restaurant_names(page)==['Romant Restaurant'],restaurant_names(page)
        prior.shot(page,out,'ru-375-brief29-discounts.webp')
        page.evaluate("go('home')")
        activate(3,'Смотреть доставку').click()
        assert page.evaluate("S.v==='cat'&&S.srt==='free'")
        page.evaluate("go('cat',{catKey:'rest',cq:'',srt:'',fo:false})")
        row=page.locator('.ad30-card' if page.locator('.ad30-card').count() else '.d6-sr').filter(has_text='Romant Restaurant')
        assert row.locator('img').first.get_attribute('src')=='/qa-image/pro-khinkali'
        prior.shot(page,out,'ru-375-brief29-category-logos.webp')

        page.evaluate("go('home')")
        section=page.locator('.home-ad-carousel')
        section.scroll_into_view_if_needed()
        assert section.evaluate("""e=>{
          const b=e.getBoundingClientRect(), d=e.querySelector('.home-ad-dots').getBoundingClientRect();
          return Math.abs(b.bottom-d.bottom-12)<1 && d.top>b.top && d.right<=b.right;
        }""")
        prior.shot(page,out,'ru-375-brief29-dont-miss-dots.webp')
        page.evaluate("go('orders')")
        ads=page.locator('.d76-order-banners button')
        assert ads.count()>0 and 'Только мои заказы' not in ads.evaluate_all("es=>es.map(e=>e.ariaLabel)")
        page.evaluate("""()=>{const get=TLB.settings;TLB.settings=()=>({...get(),orders_banner_mode:1});render()}""")
        assert ads.count()==1 and ads.first.get_attribute('aria-label')=='Только мои заказы'

        page.evaluate("openCampaign('free')")
        assert page.locator('.hh-sheet[open] .hh-sheet-store').count()==2
        assert page.locator('.hh-sheet[open] .hcd').count()==0
    finally:
        ctx.close()

    prior.qa.SDK=prior.FIX
    ctx,page=prior.qa.page_at(browser,server,photos,'ru',375,role='admin')
    try:
        page.evaluate("()=>{tab='b';showAddB=true;render()}")
        options=page.locator('#banner-orders-mode')
        assert options.input_value()=='0'
        options.select_option('1')
        assert options.input_value()=='1'
        assert page.locator('#action option').all_text_contents()==[
            'По ссылке баннера','Заказать сейчас','Открыть ресторан','Смотреть список','Открыть кампанию']
        page.locator('#action').select_option('campaign')
        prior.shot(page,out,'ru-375-brief29-admin-options.webp')
        assert page.evaluate("Object.keys(bannerPresentation()).length===0")
        page.evaluate("()=>{const get=TLB.banners;TLB.banners=all=>get(all).map(b=>({...b,presentation:null}))}")
        assert page.evaluate("bannerPresentation().presentation.action==='campaign'")
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
            test_brief26(browser,server,photos,out)
            test_brief27(browser,server,photos,out)
            test_brief29(browser,server,photos,out)
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
    print('BRIEF-25c Y-01..Y-04 and BRIEF-26 Z-01..Z-10 BRIEF-27 AA-01..AA-02 and BRIEF-29 AC-01..AC-07 PASS')

if __name__=='__main__':
    main()
