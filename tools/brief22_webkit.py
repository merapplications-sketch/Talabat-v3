"""Render the original Home and the candidate against one offline, synthetic catalogue."""
import argparse
import io
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

import brief21_webkit as qa
from qa_all import FIX

PIN = "7c7e66094c10614c01ad7359cda7bc3740e8fcfd"
REFERENCE = "9e29840e2a58911e5b345c6d690f3d95388c1623"
ROOT = Path.cwd()
FIXTURE = json.loads((ROOT / "qa-fixtures/home-brief22.json").read_text())
SEED = """
stores.splice(0,stores.length,...catalog.stores);
items.splice(0,items.length,...catalog.menu_items);
T.happy_hours.forEach(h=>h.store_id='s1');
orders.forEach(o=>o.delivery_photo=null);
for(const id of ['s2','s3','s4']){
  orders.push({...orders[4],id:'past-'+id,store_id:id});
  oitems.push({...oitems[4],id:'line-'+id,order_id:'past-'+id});
}
"""
qa.SDK = FIX.replace(qa.FINISH_SEED, "const catalog="+json.dumps(FIXTURE)+";"+SEED+qa.FINISH_SEED)
SECTIONS = ["again", "offers", "popular", "picks", "near", "rewards", "dine"]
KEYS = ["d6FavAgain", "hBestT", "d6PopR", "hRecT", "d6Near", "d6CpT", "hDineT"]


def financial(page):
    return page.evaluate("""()=>{ S.cartStore=TLB.stores().find(s=>s.id==='s1').name;
      S.cart={i2:2,[lk('i1',['o11'],'')]:1};S.tip=10;
      return [false,true].map(wallet=>{S.useWallet=wallet;S.usePts=wallet;
        const v=calc();return Object.fromEntries(
          ['sub','d','h','p','pv','fee','total','due','w','earn','cb'].map(k=>[k,v[k]]))})}""")


def compare(page, reference, out, lang, width):
    # Keep the first screen exactly as the user sees it. In the adjacent stitched
    # view, repeatable fixed controls would otherwise cover every element capture.
    page.evaluate("window.scrollTo(0,0)")
    viewport=Image.open(io.BytesIO(page.screenshot(animations='disabled'))).convert('RGB')
    blocks=[page.locator('.d6-hh'),page.locator('.d6-bento'),page.locator('.d6-cats')]
    for name in SECTIONS:
        heading=page.locator(f'[data-section="{name}"]')
        blocks.extend([heading,heading.locator('xpath=following-sibling::*[1]')])
        if name=='picks':
            blocks.append(page.locator('.home-picks .d6-rl'))
        if name=='dine':
            blocks.append(page.locator('.home-dine'))
    shots=[]
    for block in blocks:
        node=block.first
        if not block.count() or not node.is_visible():
            continue
        node.evaluate("""node=>{document.querySelectorAll('[data-qa-overlay]').forEach(e=>e.removeAttribute('data-qa-overlay'));
          document.querySelectorAll('#app *').forEach(e=>{
            if(!e.contains(node)&&!node.contains(e)&&['fixed','sticky'].includes(getComputedStyle(e).position))
              e.setAttribute('data-qa-overlay','');
          })}""")
        shot=node.screenshot(animations='disabled', style='[data-qa-overlay]{visibility:hidden!important}')
        x=round(node.bounding_box()['x'])
        shots.append((x,Image.open(io.BytesIO(shot)).convert('RGB')))
    page.evaluate("document.querySelectorAll('[data-qa-overlay]').forEach(e=>e.removeAttribute('data-qa-overlay'))")
    actual=Image.new('RGB',(width,sum(i.height for _,i in shots)),'white')
    y=0
    for x,img in shots:
        actual.paste(img,(x,y));y+=img.height
    ref=reference.resize((375,round(reference.height*375/reference.width)),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(width+ref.width+8,max(ref.height,actual.height)+viewport.height+58),'#edeae5')
    draw=ImageDraw.Draw(canvas)
    draw.text((6,7),f'Home sections | WebKit {lang.upper()} {width} | QA catalogue',fill='black')
    draw.text((width+14,7),'Owner reference',fill='black')
    canvas.paste(actual,(0,26));canvas.paste(ref,(width+8,26))
    y=max(ref.height,actual.height)+34
    draw.text((6,y),'Original first viewport with navigation',fill='black')
    canvas.paste(viewport,(0,y+20))
    canvas.save(out/f'{lang}-{width}.webp',quality=79,method=6)


def check_pick_summary(page, lang):
    cards=page.locator('.home-picks .d6-pt:visible').evaluate_all("""cards=>cards.map(c=>[
      parseFloat(c.querySelector('.px').firstChild.textContent),
      Number(c.querySelector('.d6-bdg')?.textContent.match(/[0-9.]+/)?.[0]||0)])""")
    minimum=min(price for price,_ in cards)
    maximum=max(discount for _,discount in cards)
    prefix='от' if lang=='ru' else 'from'
    phrase='скидки до' if lang=='ru' else 'discounts up to'
    expected=f'{prefix} {minimum:g} TJS'
    if maximum:
        expected+=f' · {phrase} {maximum:g}%'
    assert page.locator('.home-picks-summary').inner_text()==expected,expected
    return expected


def verify(page, width):
    page.locator('.home-picks .d6-pt').first.wait_for()
    for image in page.locator('.d6h img').all():
        image.evaluate("i=>{i.loading='eager'}")
    page.wait_for_function("()=>[...document.querySelectorAll('.d6h img')].every(i=>i.complete&&i.naturalWidth>0)")
    query="""()=>{const list=q=>[...document.querySelectorAll(q)];
      const dims=s=>list(s).map(e=>[e.offsetWidth,e.offsetHeight]);
      const heads=list('[data-section]');const cats=list('.d6-ct');
      return {order:heads.map(h=>h.dataset.section),width:document.documentElement.scrollWidth,
        category:cats.map(e=>{const r=e.getBoundingClientRect(),t=e.querySelector('b');
          return [r.left,r.right,t.scrollWidth,t.clientWidth,e.querySelector('span').offsetWidth,e.querySelector('img').offsetWidth]}),
        titleStyles:heads.map(e=>[...e.querySelectorAll('h2,h2 b,h2 span')].map(node=>{
          const s=getComputedStyle(node);return [s.fontWeight,s.fontSize,s.lineHeight]})),
        headings:heads.map(e=>{const h=e.querySelector('h2'),r=h.getBoundingClientRect(),b=e.querySelector('button');
          return [h.scrollWidth,h.clientWidth,r.right,b?.getBoundingClientRect().left??innerWidth]}),
        favourites:dims('.home-again .d6-ph'),picks:dims('.home-picks .d6-ph'),dine:dims('.home-dine .d6-ph'),
        dineBounds:['.d6-dn','.home-dine .d6-dc'].map(selector=>{
          const r=document.querySelector(selector).getBoundingClientRect();return [r.left,r.right]}),
        discountAccent:getComputedStyle(document.querySelector('[data-section="dine"] h2 b')).color,
        accentReference:getComputedStyle(document.querySelector('[data-section="dine"] i')).color,
        pictures:list('.d6h img').length,missingDish:list('.home-picks .nm').some(e=>e.textContent==='Суп дня'),
        closed:!!document.querySelector('.d6-sc.closed[aria-disabled=true]')&&!!document.querySelector('.home-again .closed:disabled'),
        headers:list('.home-heading img').map(i=>i.getAttribute('src')),
        prices:list('.home-picks .d6-pt').map(e=>e.querySelector('.px').outerHTML),
        banner:document.querySelector('.d6-dn').outerHTML};}"""
    row=page.evaluate(query)
    assert row['order']==SECTIONS and row['width']==width,row
    assert len(row['category'])==6 and all(left>=0 and right<=width and scroll<=client+1 for left,right,scroll,client,_,_ in row['category']),row
    assert all(scroll<=client+1 and right<=edge+1 for scroll,client,right,edge in row['headings']),row
    assert all(style==['900','18px','22px'] for title in row['titleStyles'] for style in title),row['titleStyles']
    if width>=375:
        assert all(abs(icon-44)<=1 and abs(circle-56)<=1 for *_,circle,icon in row['category'])
    for key,dim in [('favourites',[84,84]),('picks',[150,150]),('dine',[250,130])]:
        assert row[key] and all(x==dim for x in row[key]),(key,row[key])
    banner,first=row['dineBounds']
    assert abs(banner[0]-16)<=1 and abs(width-banner[1]-16)<=1 and abs(first[0]-16)<=1,row['dineBounds']
    assert row['discountAccent']==row['accentReference']
    assert row['pictures']>15 and row['closed'] and not row['missingDish'],row
    return row


def main():
    args=argparse.ArgumentParser()
    args.add_argument('baseline',type=Path)
    args.add_argument('out',type=Path)
    opt=args.parse_args()
    opt.out.mkdir(exist_ok=True,parents=True)
    ref=Image.open(io.BytesIO(subprocess.check_output(['git','show',REFERENCE+':docs/management/mockups-20261118/HOME-APPROVED-FINAL.png'])))
    accepted=subprocess.check_output(['git','show','95bb10a471763904cd2555e9fc45b571e61dce0f:customer.html']).decode()
    current=(ROOT/'customer.html').read_text()
    for start,end in [('function hHead()', '/* the last delivered order'), ('function vCat()', None)]:
        section=lambda src:src.split(start,1)[1].split(end,1)[0] if end else src.split(start,1)[1]
        assert section(current)==section(accepted),('protected customer view',start)
    servers=[qa.serve(p.resolve()) for p in (opt.baseline,ROOT)]
    results=[]
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(executable_path=os.environ.get('TALABOT_WEBKIT') or None)
            for lang,width in [('ru',375),('en',390),('ru',430),('ru',320)]:
                contexts=[]
                for server in servers:
                    ctx,page=qa.page_at(browser,server,{},lang,width)
                    page.locator('.d6-pt').first.wait_for()
                    contexts.append((ctx,page))
                old,new=[p for _,p in contexts]
                row=verify(new,width)
                old.locator('.d6h img').evaluate_all("images=>images.forEach(i=>i.loading='eager')")
                old_order=old.evaluate("""keys=>[...document.querySelectorAll('.d6-sh h2')].map(h=>keys.find(k=>h.textContent.includes(t(k)))).filter(Boolean)""",KEYS)
                assert old_order==KEYS,old_order
                assert row.pop('banner')==old.locator('.d6-dn').evaluate('e=>e.outerHTML')
                baseline_prices=old.locator('.d6-pt').evaluate_all("""cards=>Object.fromEntries(cards.map(e=>[e.querySelector('.nm').textContent,e.querySelector('.px').outerHTML]))""")
                for dish,price in zip(new.locator('.home-picks .nm').all_text_contents(),row['prices']):
                    assert baseline_prices[dish]==price,(dish,price)
                assert any('<s>' in p for p in row['prices']) and any('<s>' not in p for p in row['prices'])
                row['summary']=check_pick_summary(new,lang)
                compare(new,ref,opt.out,lang,width)
                row['financial']=financial(new)
                assert row['financial']==financial(old) and all(m['sub']>0 for m in row['financial'])
                new.evaluate("""()=>{const c=document.querySelector('.d6-lo:not(:disabled)');window.reorder=id=>window.qaReorder=id;c.click()}""")
                assert new.evaluate("TLB.order(window.qaReorder)?.storeId") in ('s1','s3','s4')
                new.evaluate("""()=>{window.quickAdd=(s,id)=>window.qaAdded=[s,id];document.querySelector('.home-picks .d6-pa').click()}""")
                assert new.evaluate("!!window.qaAdded?.[1]")
                new.route('**/missing-logo.webp',lambda route:route.fulfill(status=404,body=''))
                new.evaluate("""()=>{const box=document.createElement('div');box.id='qa-retry';
                  box.innerHTML=favouritePhoto({logo_url:'/missing-logo.webp',cover_url:'assets/3d/bread.webp'},0);document.body.append(box);return true}""")
                new.wait_for_function("()=>{const i=document.querySelector('#qa-retry img');return i?.naturalWidth>0&&i.src.endsWith('bread.webp')}")
                # Remove discounted cards through their normal image-error path.
                new.locator('.home-picks .d6-pt:has(.d6-bdg) .d6-ph > img:first-child').evaluate_all(
                    "images=>images.forEach(i=>i.dispatchEvent(new Event('error')))")
                row['summaryWithoutDiscount']=check_pick_summary(new,lang)
                empty=new.evaluate("""()=>{TLB.orders=()=>[];TLB.bestDishes=()=>[];TLB.allMenus=()=>({});TLB.loyalty=()=>null;TLB.wallet=()=>({balance:0});TLB.promos=()=>[];STORES=[];ALLS=[];
                  return [lastH(),bestH(),recH(),nearH(),walH(),dineH()]}""")
                assert all(not html for html in empty),empty
                results.append(dict(lang=lang,viewport=width,**row))
                for ctx,_ in contexts:ctx.close()
                print('PASS',lang,width,flush=True)
            browser.close()
        (opt.out/'measurements.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    finally:
        for server in servers:server.shutdown()

if __name__=='__main__':
    main()
