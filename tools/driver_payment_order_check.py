"""Display-only patch of 31 Oct (owner request): in the driver «Детали» dialog the cash breakdown (aCashDetail) comes
before the invoice. LOCAL only (R1 harness, isolated services). python3 tools/driver_payment_order_check.py
Checks: order of the two blocks for a mixed wallet + cash order, amounts unchanged, swipe / grip untouched."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import driver_journey_r1_check as S
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m): print(('PASS ' if c else 'FAIL ') + m, flush=True); (None if c else fails.append(m))
with sync_playwright() as pw:
    b = pw.chromium.launch(); c, p, errs = S.boot(b, 390, 716, 'pickup')
    p.evaluate("async()=>{const x=__UI_TABLES.orders.find(x=>x.id==='ord1');Object.assign(x,{payment:'cash',total:315,wallet_used:153.52,status:'preparing'});await TLB.reload()}"); S.settle(p)
    due = p.evaluate("due(TLB.order('ord1'))")
    p.locator('.a-quick-details,.k-act-details').click(); S.settle(p)
    r = p.evaluate("""()=>{const b=document.querySelector('.a-dialog-body'),c=b&&b.querySelector('.a-cash-detail'),i=b&&b.querySelector('.inv');
      return {cash:!!c,inv:!!i,before:!!(c&&i&&(c.compareDocumentPosition(i)&Node.DOCUMENT_POSITION_FOLLOWING)),text:c?c.innerText:''}}""")
    ok(r['cash'] and r['inv'] and r['before'], 'details: cash breakdown shown before the invoice (%s)' % {k: r[k] for k in ('cash', 'inv', 'before')})
    ok(due == 161.48 and ('153' in r['text']), 'amounts unchanged: due %s, wallet part in the breakdown' % due)
    p.screenshot(path=str(S.ROOT/'docs/driver-handoff/mobile-polish-20261031/after-driver-details-390.png'))
    p.get_by_role('button', name='Закрыть', exact=True).click(); S.settle(p)
    ok(p.evaluate("!document.getElementById('a-grip') && !document.getElementById('swp') && !!document.getElementById('k-main')"), 'compact card (31 Oct): no grip / swipe, one stage button')
    ok(not errs, 'no page errors %s' % errs[:2]); b.close()
print('\nDRIVER PAYMENT ORDER CHECK %s' % ('FAILS %d' % len(fails) if fails else 'OK')); sys.exit(1 if fails else 0)
