"""Headless Chromium mobile/text/keyboard emulation; not a physical Android test."""
import json
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

URL='http://127.0.0.1:4173/pulse-investment-research./'
for attempt in range(30):
    try:
        with urllib.request.urlopen(URL,timeout=2) as r:
            if r.status==200:break
    except Exception:time.sleep(1)
else:raise RuntimeError('Preview did not become ready')
Path('work').mkdir(exist_ok=True)
results=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    for width in (320,390,430):
        context=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
        page=context.new_page()
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(URL);page.get_by_role('heading',name='התדריך היומי.',exact=True).wait_for()
        page.get_by_text('התראות לאנדרואיד • הגדרה חד־פעמית',exact=True).wait_for()
        assert page.locator('html').get_attribute('dir')=='rtl'
        assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'Horizontal overflow at {width}'
        nav=page.get_by_role('navigation',name='ניווט נייד')
        nav.get_by_role('button',name='חדשות',exact=True).click()
        page.get_by_role('textbox',name='חיפוש חדשות').fill('Nebius')
        assert page.get_by_role('article').count()>0
        card=page.get_by_role('article').first
        card.get_by_role('button',name='סימון כנקרא',exact=True).click()
        assert card.get_by_role('button',name='נקרא — ביטול סימון',exact=True).get_attribute('aria-pressed')=='true'
        page.screenshot(path=f'work/mobile-{width}.png',full_page=False)
        page.evaluate("document.documentElement.style.fontSize='32px'")
        assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'200% text overflow at {width}'
        page.get_by_role('button',name='רענון מידע',exact=True).scroll_into_view_if_needed()
        page.screenshot(path=f'work/mobile-{width}-text200.png',full_page=False)
        # Emulate keyboard's visual viewport independently from layout viewport.
        page.evaluate("document.documentElement.style.fontSize='16px'")
        nav.get_by_role('button',name='מחקר',exact=True).click()
        official=page.get_by_role('region',name='מקורות רשמיים וחבילת מחקר')
        official.get_by_role('button',name='NBIS',exact=True).click()
        official.get_by_role('button',name='הכנת חבילת מקורות ל־NBIS',exact=True).click()
        pack=page.get_by_role('dialog',name='בקשת ניתוח ל־ChatGPT')
        assert 'מטא־נתונים וקישורים בלבד' in pack.get_by_role('textbox',name='טקסט להעתקה').input_value()
        pack.get_by_role('button',name='סגירה',exact=True).click()
        assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'Official panel overflow at {width}'
        page.screenshot(path=f'work/mobile-{width}-official.png',full_page=False)
        nav.get_by_role('button',name='תיק השקעות',exact=True).click()
        page.get_by_role('button',name='הוספת אחזקה',exact=True).click()
        dialog=page.get_by_role('dialog')
        dialog.locator('input').first.focus()
        page.evaluate("""() => { const vv=new EventTarget(); vv.height=360; Object.defineProperty(window,'visualViewport',{value:vv,configurable:true}); document.dispatchEvent(new FocusEvent('focusin',{bubbles:true})); }""")
        assert page.locator('html').evaluate("e=>e.classList.contains('keyboard-open')")
        assert dialog.bounding_box()['height']<=340
        dialog.get_by_role('button',name='סגירה',exact=True).click()
        assert not errors,errors
        results.append({'width':width,'rtl':True,'textScale':'200%','keyboard':'simulated visual viewport','overflow':False,'pageErrors':errors})
        context.close()
    browser.close()
Path('work/mobile-check.json').write_text(json.dumps({'environment':'headless Chromium; Android keyboard and text scaling simulated; no physical receipt test','results':results},indent=2))
print(json.dumps(results))
