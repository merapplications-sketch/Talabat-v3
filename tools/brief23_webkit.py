"""Customer WebKit checks in the offline TALABOT catalogue."""
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright

import brief22_webkit as previous
from brief22_webkit import qa

BASE='c5a8ff8a2d3a74301a3f35130a8f84316528449c'
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
    # Observe the normal signed-out entry point before testing the published UI
    # with synthetic order history. No production session or credentials are used.
    def public_assets(r):
        u=urlsplit(r.request.url)
        if r.request.method=='GET' and (u.hostname==urlsplit(PREVIEW).hostname or
            (u.hostname=='cdn.jsdelivr.net' and 'supabase-js' in u.path)):
            return r.continue_()
        r.abort()
    ctx.route('**/*',public_assets)
    page=ctx.new_page()
    page.goto(PREVIEW+'/customer',wait_until='domcontentloaded')
    page.locator('#tlb-pw').wait_for(timeout=18000)
    ctx.unroute('**/*',public_assets)
    def route(r):
        u=urlsplit(r.request.url)
        if u.hostname=='cdn.jsdelivr.net' and 'supabase-js' in u.path:
            return r.fulfill(content_type='application/javascript',body=qa.SDK.replace('window.__ROLE','"customer"'))
        if u.hostname==PREVIEW.split('//')[1] and r.request.method=='GET':
            return r.continue_()
        r.abort()
    ctx.route('**/*',route)
    response=page.goto(PREVIEW+'/customer',wait_until='domcontentloaded')
    assert response.ok
    expected=subprocess.check_output(['git','show',BASE+':customer.html'])
    assert response.body()==expected
    page.locator('.home-again .d6-lo').first.wait_for()
    info=top_geometry(page);ctx.close()
    return dict(info,realCatalogue='sign-in required')

FULL_SDK=qa.SDK.replace(qa.FINISH_SEED, """
stores[2].logo_url='';stores[2].cover_url='/qa-image/wide';
stores[3].logo_url=stores[3].cover_url='/qa-image/wide';
stores[3].free_delivery_min=350;
stores[0].fee_type='free';stores[0].created_at=iso(2*24*60);
stores[0].first_order_discount_pct=15;
items.find(i=>i.id==='i1').price=18;items.find(i=>i.id==='i2').price=19;
items.find(i=>i.id==='i7').price=23;
stores[3].created_at=iso(12*24*60);
T.app_settings.push({key:'home_meal_price_cap',value:16});
banners.push({id:'home-sponsor',placement:'dont_miss',is_active:true,link_type:'store',link_value:'s1',title:'Обед в «Мяте»',image_url:'assets/3d/sushi.webp'});
"""+qa.FINISH_SEED)
EMPTY_SDK=FULL_SDK.replace(qa.FINISH_SEED,"""
stores[2].cover_url='';
T.app_settings=T.app_settings.filter(x=>x.key!=='home_meal_price_cap');
T.banners=T.banners.filter(x=>x.placement!=='dont_miss');
stores.forEach(s=>{s.discount_pct=0;s.created_at=iso(42*24*60)});
items.forEach(i=>i.discount_pct=0);T.happy_hours=[];
"""+qa.FINISH_SEED)
ORDER=['again','offers','meals','popular','advert','picks','flash','near','rewards','dine','discover']
OPTIONAL={'advert','flash','discover'}


def display(page):
    page.evaluate("""()=>{document.querySelectorAll('.d6h img').forEach(i=>i.loading='eager');window.scrollTo(0,0)}""")
    page.wait_for_function("""()=>[...document.querySelectorAll('.d6h img')].every(i=>i.complete&&i.naturalWidth>0)""")
    page.evaluate("""()=>document.querySelectorAll('#app *').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.classList.add('qa-fixed')})""")
    try:
        return Image.open(io.BytesIO(page.screenshot(full_page=True,style='.qa-fixed{visibility:hidden!important}',animations='disabled'))).convert('RGB')
    finally:
        page.evaluate("document.querySelectorAll('.qa-fixed').forEach(e=>e.classList.remove('qa-fixed'))")


def repeat_logos(page):
    tiles=page.locator('.home-again .d6-lo')
    for name,initial in [('Лимон','Л'),('Сад','С')]:
        logo=tiles.filter(has_text=name).locator('.dish-store-logo')
        assert logo.inner_text()==initial and logo.locator('img').count()==0
        assert logo.evaluate("""e=>getComputedStyle(e).backgroundColor==='rgb(255, 255, 255)'&&
          parseFloat(getComputedStyle(e).fontSize)>=32&&e.getBoundingClientRect().width>=80""")
    brand=tiles.filter(has_text='Мята').locator('.dish-store-logo img')
    brand.evaluate("i=>i.loading='eager'")
    page.wait_for_function("""()=>document.querySelector('.home-again img[src$="leafy-green.webp"]')?.naturalWidth>0""")


def geometry(page,width,full):
    top_geometry(page)
    repeat_logos(page)
    order=page.locator('.home-heading').evaluate_all("a=>a.map(e=>e.dataset.section)")
    assert order==[x for x in ORDER if full or x not in OPTIONAL],order
    assert page.locator('.d6-dn').count()==1 and bool(page.locator('.home-dine .d6-dc').count())==full
    row=page.evaluate("""()=>{const q=s=>document.querySelector(s),all=s=>[...document.querySelectorAll(s)];
      const R=e=>e.getBoundingClientRect();
      const badge=all('.d6-sc .pk').find(e=>/350 TJS/.test(e.textContent));
      const noLogo=all('.home-picks:not(.home-meals) .d6-pt').find(e=>e.querySelector('.st').textContent==='Лимон');
      return {width:document.documentElement.scrollWidth,badge:[badge.innerText,getComputedStyle(badge).whiteSpace,badge.clientWidth,badge.scrollWidth],
        near:all('.d6-nr .d6-nc').map(e=>[R(e).left,R(e).right,R(e).top,R(e).bottom]),
        meta:all('.d6-sc').every(e=>R(e.querySelector('.nm')).left===R(e.querySelector('.mt')).left),
        initials:noLogo.querySelector('.dish-store-logo').textContent.trim()==='Л'&&!noLogo.querySelector('.dish-store-logo img'),
        gap:all('.home-picks .d6-pt').every(e=>Math.abs(R(e.querySelector('.st')).top-R(e.querySelector('.nm')).bottom-4)<1),
        bolt:!!q('.d6-ot.f b svg'),yellow:q('.d6-ot.g img')?.getAttribute('src'),extra:!!q('.d6-ot .s'),
        links:all('.home-heading button').map(e=>e.parentNode.dataset.section),
        nearAll:!!q('[data-section=near] button'),price:all('.home-picks:not(.home-meals) .d6-pt').map(e=>[e.querySelector('.nm').textContent,e.querySelector('.px').outerHTML])}}""")
    assert row['width']==width and row['meta'] and row['initials'] and row['gap'],row
    a,b,c,d=row['near']
    assert a[0]==b[0]<c[0]==d[0] and a[2]==c[2]<b[2]==d[2]
    assert row['nearAll'] and 'picks' in row['links']
    assert row['badge'][1]=='nowrap' and row['badge'][2]>=row['badge'][3]
    if page.evaluate("TLB.lang()")== 'ru':assert row['badge'][0]=='Бесплатно от 350 TJS'
    assert row['yellow']=='assets/3d/motor-scooter-yellow.png' and not row['extra']
    if full:
        styles=page.locator('.flash-description .px').evaluate_all("""prices=>prices.map(p=>{
          const current=getComputedStyle(p),old=getComputedStyle(p.querySelector('s'));
          return [current.color,current.fontWeight,current.textDecorationLine,current.textDecorationColor,
                  old.color,old.textDecorationLine,old.display]})""")
        gray=page.locator('.flash-description').first.evaluate("""e=>{const probe=document.createElement('span');
          probe.style.color='var(--mut)';e.append(probe);const color=getComputedStyle(probe).color;probe.remove();return color}""")
        assert styles and all(v==['rgb(28, 28, 33)','800','underline','rgb(217, 249, 157)',gray,'line-through','inline-block'] for v in styles),styles
        assert row['bolt']
        assert page.evaluate("document.querySelector('.home-meals .home-picks-summary').textContent.includes(t('lunchFree'))")
        assert page.locator('.home-meals .d6-pt .d6-pa').count()>0
        assert page.locator('.flash-item').count()==1
        assert page.locator('.home-ad-card .ad-art').count()==1
        assert page.locator('.discover-row em').count()==0
        assert page.locator('.flash-grid').evaluate("e=>getComputedStyle(e).gridTemplateRows.split(' ').length")==1
        for section in ('meals','discover'):
            assert section in row['links']
    return row


def cart_checks(page,lang,width):
    page.evaluate("()=>{window.confirm=()=>{throw new Error('unexpected window.confirm')}}")
    source='Мята'
    def reset():
        page.evaluate("""()=>{S.sh=null;S.cart={i2:2};S.cartStore='Мята';S.store='Мята';go('home')}""")
    def trigger(kind):
        if kind=='home':
            page.locator('.home-picks:not(.home-meals) .d6-pt').filter(has_text='Лимон').first.locator('.d6-pa').evaluate('b=>b.click()')
        elif kind=='meal':
            page.evaluate("()=>{S.cartStore='Лимон';S.cart={i6:1};render()}")
            page.locator('.home-meals .d6-pt').filter(has_text='Суши с овощами').locator('.d6-pa').evaluate('b=>b.click()')
        elif kind=='menu':
            page.evaluate("()=>{openN('Лимон');addFrom('i6')}")
        elif kind=='sheet':
            page.evaluate("()=>{openN('Лимон');openItem('i6');shAdd()}")
        elif kind=='reorder':
            page.evaluate("()=>{S.cartStore='Лимон';S.cart={i6:1};reorder('ord4');roGo()}")
        elif kind=='group':
            page.evaluate("()=>{S.cartStore='Лимон';S.cart={i6:1};S.grp={store_id:'s1'};grpAddMore()}")
    routes=('home','meal','menu','sheet','reorder','group') if width in (375,390) else ('home',)
    for kind in routes:
        for accept in (False,True):
            reset();trigger(kind)
            modal=page.locator('dialog.cart-choice[open]')
            modal.wait_for(timeout=4000)
            prior='Лимон' if kind in ('meal','reorder','group') else source
            assert prior in modal.locator('p').inner_text()
            saved=page.evaluate("JSON.stringify([S.cartStore,S.cart])")
            modal.locator('[value='+('start' if accept else 'cancel')+']').click()
            page.wait_for_function("!document.querySelector('.cart-choice')")
            if accept:
                assert page.evaluate("S.cartStore")!=prior
                if kind!='group':assert page.evaluate("cartCount()>0")
            else:
                assert page.evaluate("JSON.stringify([S.cartStore,S.cart])")==saved
    reset()
    page.evaluate("quickAdd('Мята','i2')")
    assert not page.locator('dialog.cart-choice').count() and page.evaluate('S.cart.i2')==3
    if lang=='ru':
        assert page.evaluate('[freePlaces(1),freePlaces(2),freePlaces(5),freePlaces(21)]')==['в 1 месте рядом','в 2 местах рядом','в 5 местах рядом','в 21 месте рядом']
    return 2*len(routes)+1


def cart_spacing(page):
    page.evaluate("()=>{S.cart={i2:1};S.cartStore='Мята';go('home');scrollTo(0,document.documentElement.scrollHeight)}")
    page.wait_for_timeout(100)
    return page.evaluate("""()=>{const last=document.querySelector('.discover-row:last-child')||document.querySelector('.d6-dn');
      return Math.round(document.querySelector('.bar').getBoundingClientRect().top-last.getBoundingClientRect().bottom)}""")


def main():
    baseline,out=map(Path,sys.argv[1:3]);out.mkdir(parents=True,exist_ok=True)
    wide=Image.new('RGB',(450,110),'#fdebd8')
    asset=Image.open('assets/3d/pizza.webp').convert('RGBA');asset.thumbnail((105,100));wide.paste(asset,(177,5),asset)
    stream=io.BytesIO();wide.save(stream,'JPEG');photos={'wide':stream.getvalue()}
    servers=[qa.serve(root.resolve()) for root in (baseline,Path.cwd())];report=[]
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            if os.environ.get('CHECK_PUBLISHED_TOP')=='1':
                report.append({'published430WithQaCatalogue':published_top(browser)})
            for lang,width in [('ru',375),('en',390),('ru',430),('ru',320)]:
                for full in (True,False):
                    qa.SDK=FULL_SDK if full else EMPTY_SDK
                    pairs=[qa.page_at(browser,s,photos,lang,width) for s in servers]
                    old,new=[p for _,p in pairs]
                    errors=[];new.on('pageerror',lambda e:errors.append(str(e)))
                    new.locator('.home-picks:not(.home-meals) .d6-pt').first.wait_for()
                    row=geometry(new,width,full)
                    old_prices=dict(old.locator('.home-picks .d6-pt').evaluate_all("a=>a.map(e=>[e.querySelector('.nm').textContent,e.querySelector('.px').outerHTML])"))
                    assert all(old_prices[n]==price for n,price in row['price'])
                    if lang=='ru' and width==375 and full:
                        display(new).save(out/'ru-375.webp',quality=83,method=6)
                    new.locator('[data-section=near] button').evaluate('b=>b.click()')
                    assert new.locator('.d6-nc').count()==4
                    new.evaluate("go('home')")
                    row['money']=previous.financial(new);assert row['money']==previous.financial(old)
                    pairs[0][0].close()
                    if full:
                        row['cartCases']=cart_checks(new,lang,width)
                        new.locator('.flash-item').first.evaluate('b=>b.click()')
                        assert new.evaluate("S.v==='menu'&&!!S.sh")
                        new.evaluate("()=>{shClose();go('home')}")
                    row['cartClearance']=cart_spacing(new)
                    assert row['cartClearance']>=15,row['cartClearance']
                    assert not errors,errors
                    report.append(dict(lang=lang,width=width,full=full,**{k:v for k,v in row.items() if k!='width'}))
                    pairs[1][0].close()
                    print('PASS',lang,width,'populated' if full else 'empty',flush=True)
            browser.close()
        (out/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    finally:
        for s in servers:s.shutdown()


if __name__=='__main__':
    main()
