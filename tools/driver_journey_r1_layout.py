"""Final layout-only check after the long-text height fix; no journey/services re-run."""
import driver_journey_r1_check as S
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
 for eng in ['chromium','webkit']:
  b=getattr(pw,eng).launch()
  for w,outer in [(360,780),(390,844),(430,932)]:
   c,p,e=S.boot(b,w,outer-128,'pickup');S.essentials(p,f'{eng} {w} final work layout');p.screenshot(path=str(S.OUT/f'final-work-{eng}-{w}.png'))
   p.locator('#a-mode-toggle').click();S.settle(p);S.essentials(p,f'{eng} {w} final map layout');p.screenshot(path=str(S.OUT/f'final-map-{eng}-{w}.png'))
   p.set_viewport_size({'width':w,'height':outer-68});S.settle(p);S.essentials(p,f'{eng} {w} compact-browser layout');c.close()
  b.close()
