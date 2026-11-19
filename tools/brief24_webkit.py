"""Verify Home with the three businesses and displayed prices reported by the owner."""
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from brief22_webkit import qa
from brief23_webkit import display
from qa_all import FIX


CATALOG = json.loads(Path('qa-fixtures/home-brief24.json').read_text())
BASE = 'c5a8ff8a2d3a74301a3f35130a8f84316528449c'
SEED = """
stores.splice(0,stores.length,...catalog.stores);
items.splice(0,items.length,...catalog.menu_items);
stores.forEach(s=>s.created_at=iso(90*24*60));
const past=orders.find(o=>o.status==='delivered');
orders.splice(0,orders.length,{...past,store_id:'s1'});
oitems.splice(0,oitems.length,{...oitems[0],order_id:past.id,item_id:'hot',name:'Hot honey'});
T.happy_hours=[];T.item_options=[];T.item_option_groups=[];T.banners=[];
"""


def page_for(browser, server, photos, extra=''):
    qa.SDK = FIX.replace(qa.FINISH_SEED, 'const catalog='+json.dumps(CATALOG)+';'+SEED+extra+';\n'+qa.FINISH_SEED)
    return qa.page_at(browser, server, photos, 'ru', 375)


def layout(rail):
    return rail.evaluate("""e=>{const boxes=[...e.children].map(c=>{const r=c.getBoundingClientRect();return [r.x,r.y,r.width,r.height]});
      e.scrollLeft=e.scrollWidth; const scroll=e.scrollLeft; e.scrollLeft=0;
      return {boxes,scroll,rows:getComputedStyle(e).gridTemplateRows.split(' ').length}}""")


def money(page):
    return page.evaluate("""()=>{let rows=[];for(const [store,cart] of [['KFC',{combo:1,hot:1}],
       ['Romant Restaurant',{plov:1}],['Romant Restaurant',{steak:2}]]) {
      S.cartStore=store;S.cart=cart;S.tip=0;
      for(const wallet of [false,true]){S.usePts=wallet;S.useWallet=wallet;const v=calc();
        rows.push(Object.fromEntries(['sub','d','h','p','fee0','fee','fw','total','due','w','pv','earn','cb'].map(k=>[k,v[k]])))}
    }return rows}""")


def assert_image(img, source, fit):
    assert img.count()==1, img
    img.evaluate("i=>i.loading='eager'")
    img.evaluate("i=>i.decode()")
    info=img.evaluate("""i=>({src:i.getAttribute('src'),fit:getComputedStyle(i).objectFit,
        background:getComputedStyle(i).backgroundColor})""")
    assert (info['src'],info['fit'])==(source,fit),info
    if fit=='contain':
        assert info['background']=='rgb(250, 250, 250)',info


def card_photo(page, selector, restaurant):
    return page.locator(selector).filter(has_text=restaurant).locator('.d6-ph > img').first


def current_home(page, out):
    for section in ['meals','advert','discover','flash']:
        assert page.locator(f'[data-section="{section}"]').is_visible(), section
    meals=page.locator('.home-meals')
    assert meals.locator('.home-picks-summary').inner_text()=='от 60 TJS'
    assert meals.locator('.nm').all_inner_texts()==['Hot honey','Плов']
    assert meals.locator('.d6-pt:visible').count()==2
    assert page.locator('.home-ad-card b').inner_text()=='Скидка 20% в Romant Restaurant'
    disc=page.locator('.home-discover')
    assert disc.locator('.home-picks-summary').inner_text()=='Вы ещё не пробовали'
    assert disc.locator('.discover-row b').all_inner_texts()==['Romant Restaurant']
    assert 'Новый' not in disc.inner_text() and disc.locator('em').count()==0
    flash=page.locator('.flash-grid')
    prices=flash.locator('.flash-description').evaluate_all("""es=>Object.fromEntries(es.map(e=>[
      e.querySelector('b').textContent,[parseFloat(e.querySelector('.px').firstChild.textContent),+e.querySelector('s').textContent]]))""")
    assert prices=={'Combo':[161.5,170],'Hot honey':[85.5,90]},prices
    store_prices=page.evaluate("()=>Object.fromEntries(homeProducts().map(c=>[c.it.name,c.price]))")
    assert store_prices=={'Combo':161.5,'Hot honey':85.5,'Стейк':180,'Плов':60}
    data={key:layout(page.locator(sel)) for key,sel in {
        'flash':'.flash-grid','popular':'[data-section=popular] + .d6-rl','near':'.home-l-near'}.items()}
    a,b=data['flash']['boxes']
    assert a[1]<b[1] and a[0]==b[0] and a[2]==b[2]==250
    a,b=data['popular']['boxes']
    assert data['popular']['rows']==1 and a[1]==b[1] and a[0]<b[0]
    assert a[2]==b[2] and 130<a[2]<140
    a,b,c=data['near']['boxes']
    assert data['near']['rows']==2 and a[1]==c[1]<b[1] and a[0]==b[0]<c[0] and data['near']['scroll']>0
    assert page.locator('[data-section=near] b').evaluate("e=>getComputedStyle(e).textDecorationLine")=='none'
    gap=page.evaluate("""()=>{const bounds=s=>document.querySelector(s).getBoundingClientRect();
      return bounds('[data-section=near] h2').top-Math.max(...Array.from(document.querySelectorAll('.flash-item'),e=>e.getBoundingClientRect().bottom))}""")
    assert 0<gap<=32,gap
    assert page.evaluate("document.documentElement.scrollWidth")==375
    for selector in ('.d6-sc',):
        assert_image(card_photo(page,selector,'KFC'),'/qa-image/kfc','contain')
        assert_image(card_photo(page,selector,'Romant'),'/qa-image/romant','cover')
    for selector in ('.discover-row','.home-dine .d6-dc'):
        assert_image(card_photo(page,selector,'Romant'),'/qa-image/romant','cover')
    assert_image(page.locator('.home-ad-card .ad-art'),'/qa-image/romant','cover')
    logo=page.locator('.home-l-near .home-l-card').filter(has_text='KFC').locator('.dish-store-logo img')
    assert logo.evaluate("e=>getComputedStyle(e).objectFit")=='contain'
    assert page.locator('.home-l-offers .hb.r').count()==2
    assert page.locator('.home-ad-dots .on').count()==1
    display(page).save(out/'ru-375.webp',quality=86,method=6)
    page.locator('.home-ad-card').click()
    assert page.evaluate("S.v==='menu' && S.store==='Romant Restaurant'")
    page.evaluate("go('home')")
    page.evaluate("()=>{S.q='KFC';render()}")
    assert_image(card_photo(page,'.d6-res .d6-sr','KFC'),'/qa-image/kfc','contain')
    page.evaluate("openN('KFC')")
    assert_image(page.locator('.d6-cover > img'),'assets/3d/hamburger.webp','cover')
    page.evaluate("()=>{S.q='';go('home')}")
    return {'geometry':data,'gap':gap,'prices':store_prices}


def catalogue_sizes(browser, server, photos, out):
    # This second fixture contains only restaurants. The owner's fixture keeps the flower shop.
    reports={}
    for count in range(1,7):
        seed="""stores.splice(2);
          for(let i=2;i<count;i++)stores.push({...stores[i%2],id:'fixture-'+i,name:'Кафе QA '+(i+1)});
          stores.splice(count);""".replace('count',str(count))
        ctx,page=page_for(browser,server,photos,seed)
        try:
            report={}
            for section,selector,width in [('popular','[data-section=popular] + .d6-rl',150),('near','.d6-nr',292)]:
                grid=layout(page.locator(selector))
                boxes=grid['boxes']
                assert len(boxes)==count and all(abs(b[2]-width)<1 for b in boxes),(section,count,grid)
                rows=1 if count<(4 if section=='popular' else 2) else 2
                assert grid['rows']==rows and len({b[1] for b in boxes})==rows,(section,count,grid)
                for i,box in enumerate(boxes):
                    assert box[1]==boxes[i%rows][1]
                    if i>=rows:assert box[0]>boxes[i-rows][0]
                if count>=4:
                    assert boxes[0][0]==boxes[1][0] and boxes[0][1]<boxes[1][1]
                    if count==6 or section=='near':assert grid['scroll']>0
                report[section]=grid
            reports[count]=report
            if count==6:
                display(page).save(out/'ru-375-six-restaurants.webp',quality=86,method=6)
        finally:
            ctx.close()
    return reports


def variants(browser, server, photos):
    def check(extra, test):
        ctx,page=page_for(browser,server,photos,extra)
        try:test(page)
        finally:ctx.close()

    def curated(p):
        # Stored flags stay dormant until the shared public menu model exposes them.
        assert set(p.locator('.home-meals .nm').all_inner_texts())=={'Плов','Hot honey'}
        assert set(p.locator('.flash-description b').all_inner_texts())=={'Combo','Hot honey'}
        # Explicit customer-component contract for a future mapped catalogue.
        marked=p.evaluate("""()=>{const products=homeProducts().map(c=>({...c,it:{...c.it,
          meal_for_one:c.it.id==='steak',flash_sale:c.it.id==='hot'}}));
          function names(html,selector){const node=document.createElement('template');
            node.innerHTML=html;return [...node.content.querySelectorAll(selector)].map(e=>e.textContent)}
          return [names(mealsH(products),'.nm'),names(flashH(products),'.flash-description b')]}""")
        assert marked==[['Стейк'],['Hot honey']]
        assert p.locator('.home-ad-card b').inner_text()=='Объявление KFC'
        assert p.locator('.home-discover .discover-row b').all_inner_texts()==['Romant Restaurant']
        assert 'Новый' in p.locator('.home-discover').inner_text()
        assert '12%' in p.locator('.discover-row em').inner_text()
    check("""items.find(i=>i.id==='steak').meal_for_one=true;items.find(i=>i.id==='hot').flash_sale=true;
        stores[1].created_at=iso(24*60);stores[1].first_order_discount_pct=12;
        T.banners.push({id:'campaign',placement:'dont_miss',title:'Объявление KFC',link_type:'store',link_value:'s1',is_active:true});""",curated)

    def branded(p):
        for selector in ('.d6-sc','.discover-row','.home-dine .d6-dc'):
            assert_image(card_photo(p,selector,'Romant'),'/qa-image/kfc','contain')
        assert_image(p.locator('.home-ad-card .ad-art'),'/qa-image/kfc','contain')
    check("stores[1].logo_url='/qa-image/kfc'",branded)

    def unavailable_logo(p):
        img=card_photo(p,'.d6-sc','KFC')
        img.evaluate("i=>i.loading='eager'")
        p.wait_for_function("document.querySelector('.d6-sc img[src$=\"hamburger.webp\"]')?.naturalWidth>0")
        assert_image(img,'assets/3d/hamburger.webp','cover')
    check("stores[0].logo_url='/qa-image/broken'",unavailable_logo)

    def large(p):
        prices=p.locator('.home-meals .d6-pt').evaluate_all("a=>a.map(e=>+e.dataset.price)")
        assert prices==list(range(1,11)),prices
        assert layout(p.locator('.flash-grid'))['rows']==2
        assert layout(p.locator('[data-section=popular] + .d6-rl'))['scroll']>0
        p.locator('[data-section=meals] button').click()
        assert p.locator('.home-meals .d6-pt').count()==10
    check("""for(let i=15;i>=1;i--)items.push({...items[1],id:'p'+i,name:'Meal '+i,price:i,discount_pct:0});
        for(let i=0;i<5;i++)stores.push({...stores[0],id:'other'+i,name:'Test '+i});
        items.push({...items[0],id:'fourth'},{...items[0],id:'fifth'});
        T.app_settings.push({key:'home_meal_price_cap',value:12});""",large)

    def mixed_photos(p):
        meals=p.locator('.home-meals')
        assert meals.locator('.nm').all_inner_texts()==['Фото 70','Hot honey','Без фото 20','Плов']
        assert meals.locator('.home-picks-summary').inner_text()=='от 20 TJS'
        meals.locator('[data-section=meals] button').click()
        assert p.locator('.home-meals .nm').all_inner_texts()==['Фото 70','Hot honey','Без фото 20','Плов']
    check("""items.push({...items[1],id:'photo70',name:'Фото 70',price:70,discount_pct:0},
        {...items[1],id:'plain20',name:'Без фото 20',price:20,discount_pct:0,image_url:''});""",mixed_photos)

    def three_deals(p):
        boxes=layout(p.locator('.flash-grid'))
        assert boxes['rows']==2 and len(boxes['boxes'])==3 and boxes['scroll']>0
    check("items.push({...items[0],id:'third',name:'Third offer'})",three_deals)

    def empty(p):
        assert all(p.locator('[data-section='+s+']').count()==0 for s in ['meals','flash','advert','discover'])
    check("stores.forEach(s=>s.is_open=false)",empty)

    def no_paid_delivery(p):
        assert p.locator('.home-meals .home-picks-summary').inner_text()=='от 60 TJS + бесплатная доставка'
        assert p.locator('.flash-item').count()==1 and layout(p.locator('.flash-grid'))['rows']==1
    check("""stores[0].is_open=false;stores[1].free_delivery_min=50;
        items.find(i=>i.id==='steak').available=false;""",no_paid_delivery)

    def long_history(p):
        p.wait_for_function("discoveryHistory?.names instanceof Set")
        assert p.locator('.home-discover').count()==0
    check("""for(let i=1;i<60;i++)orders.push({...orders[0],id:'recent'+i});
        orders.push({...orders[0],id:'older',store_id:'s2',_hist:true});""",long_history)



def closed_home_cards(browser, server, photos, out):
    views=[('ru',375),('en',390)]
    results={}
    for lang,width in views:
        # The G-08 fixture has a delivered order from a store without a logo.
        qa.SDK=FIX
        ctx,page=qa.page_at(browser,server,photos,lang,width)
        try:
            repeat=page.locator('.home-again .d6-lo').first
            repeat.wait_for()
            probe=repeat.evaluate("""e=>({name:e.querySelector('.nm').textContent.trim(),
                initial:e.querySelector('.dish-store-logo')?.textContent.trim(),
                image:!!e.querySelector('img'),emptySlot:!!e.querySelector('.d6-ph.none')})""")
            print('G08_FIXTURE_DOM',lang,width,json.dumps(probe,ensure_ascii=False),flush=True)
        finally:
            ctx.close()

        # Exercise both the logo-backed and empty photo slots with the new Home rails.
        seed="stores[0].is_open=false;stores[0].created_at=iso(24*60);"
        if lang=='ru':
            seed+="stores[0].logo_url=stores[0].cover_url='';"
        qa.SDK=FIX.replace(qa.FINISH_SEED,'const catalog='+json.dumps(CATALOG)+';'+SEED+seed+';\n'+qa.FINISH_SEED)
        ctx,page=qa.page_at(browser,server,photos,lang,width)
        try:
            label='Закрыт' if lang=='ru' else 'Closed'
            def verify(selector):
                card=page.locator(selector).filter(has_text='KFC')
                card.scroll_into_view_if_needed()
                badge=card.locator('.hb.k')
                assert badge.inner_text()==label,(selector,lang)
                bounds=badge.bounding_box()
                assert bounds and bounds['width']>20 and bounds['height']>0,(selector,bounds)
                assert card.evaluate("""e=>{
                  const blocked=e.disabled||e.getAttribute('aria-disabled')==='true';
                  const active=e.querySelector('button:not(:disabled),a[href],[onclick]');
                  e.click();
                  return blocked&&!e.onclick&&!active&&S.v==='home'&&
                    getComputedStyle(e).filter.includes('grayscale');
                }"""),selector
                return round(bounds['width'],1)

            widths={sel:verify(sel) for sel in ('.d6-sc','.home-l-near .home-l-card','.discover-row','.d6-lo')}
            page.locator('.d6-sc.closed').filter(has_text='KFC').screenshot(path=str(out/f'closed-{lang}-{width}.png'))
            page.evaluate("()=>{S.q='KFC';render()}")
            widths['.d6-sr']=verify('.d6-sr')
            results[lang]=widths
            print('V01_CLOSED_CARDS',lang,width,widths,flush=True)
        finally:
            ctx.close()
    return results


def main():
    baseline,out=map(Path,sys.argv[1:3]);out.mkdir(parents=True,exist_ok=True)
    assert Path('talabat-core.js').read_bytes()==(baseline/'talabat-core.js').read_bytes(), 'Frozen shared core changed'
    servers=[qa.serve(root.resolve()) for root in (baseline,Path.cwd())]
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            photos=qa.source_photos()
            old,ref=page_for(browser,servers[0],photos)
            new,page=page_for(browser,servers[1],photos)
            result=current_home(page,out)
            result['money']=money(page)
            assert result['money']==money(ref)
            assert result['money'][2]['fee']>0 and result['money'][4]['fw']>0 and result['money'][4]['fee']==0
            old.close();new.close()
            result['catalogueSizes']=catalogue_sizes(browser,servers[1],photos,out)
            variants(browser,servers[1],photos)
            result['closedHomeCards']=closed_home_cards(browser,servers[1],photos,out)
            ctx,closed=page_for(browser,servers[1],photos,"stores[0].is_open=false;")
            display(closed).save(out/'ru-375-full-closed-and-discount.webp',quality=86,method=6)
            ctx.close()
            browser.close()
        (out/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
        print('PASS R-01..R-09, logo/cover fallback, three-store RU/375, admin precedence, history, zero-data rules and six financial comparisons')
    finally:
        for s in servers:s.shutdown()


if __name__=='__main__':
    main()
