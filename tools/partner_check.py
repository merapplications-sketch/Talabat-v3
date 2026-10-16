"""Public partner page (partner.html) on its read-only preview: form states by real taps, one send per tap, no success the server
did not confirm, values kept after a failure, the "not a robot" check required again after every send, the calculator
(3 cases checked against an independent formula, empty vs zero, limits), layout 360/390/430 RU/EN. Chromium only.
  python3 tools/build_preview.py <dir>/partner partner && python3 tools/partner_check.py <dir>/partner"""
import sys
from playwright.sync_api import sync_playwright
D=sys.argv[1];fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def money(n): return '{:,.2f}'.format(round(n+1e-9,2)).replace(',',' ').replace('.',',')
with sync_playwright() as p:
    b=p.chromium.launch()
    def page(q='',vw=(390,844),lang='ru'):
        pg=b.new_page(viewport={'width':vw[0],'height':vw[1]},is_mobile=True,has_touch=True);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
        pg.add_init_script("try{localStorage.setItem('tlb_lang','%s')}catch(e){}"%lang)
        pg.goto('file://'+D+'/partner.html'+q);pg.wait_for_timeout(400);return pg,errs
    # ---------- settings missing: the form is off, nothing can be sent ----------
    pg,errs=page('?off=1')
    ok(pg.locator('#f-off').count()==1 and pg.locator('#f-send').count()==0 and pg.locator('#ts-box').is_hidden(),'settings missing → «Приём заявок временно недоступен», no send button, no check box')
    ok(not errs,'no JS errors %s'%errs[:1]);pg.close()
    # ---------- form ----------
    pg,errs=page();E=pg.evaluate;sent=lambda:E("()=>__pvPartner.sent.length")
    pg.fill('#f-name','Чайхана Роҳат');pg.fill('#f-phone','90 123 45 67');pg.select_option('#f-cat','sweets')
    pg.click('#f-send');pg.wait_for_timeout(200)
    ok(sent()==0 and 'Пройдите проверку' in pg.inner_text('#f-err'),'send without the check → asks for the check, nothing sent')
    pg.fill('#f-phone','12345');pg.check('#pv-ts-cb');pg.click('#f-send');pg.wait_for_timeout(200)
    ok(sent()==0 and pg.locator('#f-phone-err').count()==1,'wrong phone → message under the field, nothing sent')
    pg.fill('#f-phone','+992 90 123 45 67');ts=E("()=>{const e=document.getElementById('pv-ts');e.__mk=1;return 1}")
    for reply,txt,retry in [('busy','слишком много заявок',False),('verify_failed','Проверка не пройдена',False),('unavailable','Данные сохранены',True),('network','Данные сохранены',True)]:
        E("r=>__pvPartner.reply=r",reply);n0=sent()
        if not pg.is_checked('#pv-ts-cb'): pg.check('#pv-ts-cb')
        pg.locator('#f-send').dispatch_event('click');pg.locator('#f-send').dispatch_event('click');pg.wait_for_timeout(100)
        busy=pg.locator('#f-send').is_disabled() and 'Отправляем' in pg.inner_text('#f-send')
        pg.wait_for_timeout(1000)
        ok(sent()-n0==1 and busy,'%s: two quick taps → ONE send, button disabled while sending'%reply)
        ok(txt.lower() in pg.inner_text('#f-err').lower() and pg.locator('#f-ok').count()==0,'%s: error shown, no success'%reply)
        ok(pg.input_value('#f-name')=='Чайхана Роҳат' and pg.input_value('#f-phone')=='+992 90 123 45 67' and pg.input_value('#f-cat')=='sweets','%s: typed values kept'%reply)
        ok(not pg.is_checked('#pv-ts-cb') and E("()=>document.getElementById('pv-ts').__mk===1"),'%s: the check must be done again (single-use token), check box not rebuilt'%reply)
        ok(('Повторить' in pg.inner_text('#f-send'))==retry,'%s: button says «%s»'%(reply,'Повторить' if retry else 'Отправить заявку'))
    E("()=>__pvPartner.reply='bad_phone'");pg.check('#pv-ts-cb');pg.click('#f-send');pg.wait_for_timeout(1000)
    ok(pg.locator('#f-phone-err').count()==1 and pg.locator('#f-ok').count()==0,'server refuses the phone → message under the field, no success')
    E("()=>__pvPartner.reply='ok'");pg.check('#pv-ts-cb');pg.click('#f-send');pg.wait_for_timeout(1000)
    ok(pg.locator('#f-ok').count()==1 and 'Если она новая' in pg.inner_text('#f-ok'),'server ok → the general answer (same for new / already known number)')
    ok(E("()=>__pvPartner.sent.every(x=>x.hasToken)"),'every send carried a check token')
    pg.click('#f-again');pg.wait_for_timeout(200)
    ok(pg.input_value('#f-name')=='' and pg.locator('#f-send').count()==1,'«Отправить другую заявку» → empty form')
    ok(not errs,'no JS errors %s'%errs[:1])
    # ---------- calculator ----------
    def fill(vals):
        for k in ['avg','cnt','com','disc','pts','fdN','fdFee','cogs','pack','other']: pg.fill('#c-'+k,str(vals.get(k,'')))
        pg.wait_for_timeout(100)
    def expect(v):
        S=v['avg']*v['cnt'];D=S*v['disc']/100 if 'disc' in v else 0;B=S-D;C=B*v['com']/100;P=B*v['pts']/100 if 'pts' in v else 0;F=v['fdN']*v['fdFee'] if 'fdN' in v else 0
        N=B-C-P-F;Pr=None
        if 'cogs' in v: Pr=N-S*v['cogs']/100-(v.get('pack',0)*v['cnt'])-v.get('other',0)
        return N,Pr
    for label,v in [('A no discount, no optional costs',{'avg':80,'cnt':600,'com':15}),
                    ('B discount + points + food cost',{'avg':80,'cnt':600,'com':15,'disc':5,'pts':2,'cogs':35}),
                    ('C free delivery + packaging + other costs',{'avg':62.5,'cnt':480,'com':12.5,'fdN':100,'fdFee':12,'cogs':30,'pack':1.5,'other':5000})]:
        fill(v);N,Pr=expect(v);txt=pg.inner_text('#calc-res')
        ok(pg.inner_text('#calc-n').replace(' ',' ').replace(' ',' ').startswith(money(N)),'%s: revenue after deductions %s (got %s)'%(label,money(N),pg.inner_text('#calc-n')))
        if Pr is None: ok(pg.locator('#calc-p').count()==0 and 'не учтено' in txt,'%s: no profit shown without food cost; empty optional rows «не учтено»'%label)
        else: ok(pg.inner_text('#calc-p').replace(' ',' ').replace(' ',' ').startswith(money(Pr)),'%s: profit after entered costs %s (got %s)'%(label,money(Pr),pg.inner_text('#calc-p')))
        ok('до налогов' in txt and 'Не учтены: налоги' in pg.inner_text('#calc-out'),'%s: «до налогов» + what is not included'%label)
    fill({'avg':80,'cnt':600,'com':15,'disc':0});txt0=pg.inner_text('#calc-res')
    fill({'avg':80,'cnt':600,'com':15});txt1=pg.inner_text('#calc-res')
    ok('−0,00' in txt0 and 'Ваши скидки\tне учтено' in txt1.replace('\n','\t'),'empty ≠ zero: 0 % discount shows −0,00, empty shows «не учтено»')
    fill({'avg':80,'cnt':600});ok(pg.locator('#calc-res').count()==0 and 'Заполните' in pg.inner_text('#calc-out'),'commission empty (no preset rate) → no result, asks to fill it')
    ok(pg.input_value('#c-com')=='','commission field starts empty')
    fill({'avg':80,'cnt':600,'com':150});ok(pg.locator('#calc-res').count()==0 and 'диапазон' in pg.inner_text('#e-com'),'commission 150 % → out-of-range message, no result')
    fill({'avg':80,'cnt':10.5,'com':15});ok('целое' in pg.inner_text('#e-cnt'),'orders per month must be a whole number')
    fill({'avg':80,'cnt':100,'com':15,'fdN':150,'fdFee':10});ok('Не больше' in pg.inner_text('#e-fdN') and pg.locator('#calc-res').count()==0,'free-delivery orders above the orders per month → refused')
    fill({'avg':80,'cnt':100,'com':15,'fdN':50});ok('оба поля' in pg.inner_text('#e-fdFee'),'free-delivery count without its cost → asks for both')
    fill({'avg':0,'cnt':100,'com':15});ok('диапазон' in pg.inner_text('#e-avg'),'average order 0 → out of range')
    el=E("()=>{const e=document.getElementById('c-avg');e.__mk=2;return 1}");pg.focus('#c-avg');pg.keyboard.type('5');pg.wait_for_timeout(100)
    ok(E("()=>document.getElementById('c-avg').__mk===2&&document.activeElement.id==='c-avg'"),'typing in the calculator does not rebuild the field (focus kept)')
    ok(not errs,'no JS errors %s'%errs[:1]);pg.close()
    # ---------- layout ----------
    for vw in [(360,780),(390,844),(430,932),(844,390)]:
        for lang in ['ru','en']:
            pg,errs=page(vw=vw,lang=lang);E=pg.evaluate
            pg.fill('#c-avg','80');pg.fill('#c-cnt','600');pg.fill('#c-com','15');pg.fill('#c-cogs','35')
            sw=E("()=>[document.documentElement.scrollWidth,innerWidth]")
            out=E("()=>[...document.querySelectorAll('input,select,button,#calc-res')].filter(e=>e.offsetParent&&!e.closest('.hp,#pv-strip')&&(e.getBoundingClientRect().right>innerWidth+1||e.getBoundingClientRect().left<-1)).length")
            ok(sw[0]<=sw[1] and out==0,'[%dx%d %s] no sideways scroll, nothing outside the screen %s'%(vw[0],vw[1],lang,sw))
            ok(E("()=>document.documentElement.lang")==lang and (('Подключите' in pg.inner_text('h1')) if lang=='ru' else ('Connect' in pg.inner_text('h1'))),'[%dx%d %s] language'%(vw[0],vw[1],lang))
            ok(not errs,'[%dx%d %s] no JS errors'%(vw[0],vw[1],lang));pg.close()
    b.close()
print('PARTNER PAGE FAILS',len(fails));sys.exit(1 if fails else 0)
