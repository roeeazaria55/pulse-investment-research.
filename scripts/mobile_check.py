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
        exchange=page.get_by_role('region',name='ניתוח מסמכים וייבוא מחקר')
        # Every initial company has its own published baseline; opening it is read-only.
        company_select=page.get_by_label('חברה למחקר',exact=True)
        labels=['NBIS','META','DLO','FTAI','LMND','SNDK','IREN','נקסט ויזן','אנלייט','בריינסוויי','גילת טלקום']
        for index,label in enumerate(labels):
            company_select.select_option(f'initial-{index}')
            exchange.get_by_role('heading',name=f'מחקר בסיס ל־{label}',exact=True).wait_for()
            exchange.get_by_text('קריאת המחקר המלא',exact=True).click()
            assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'Baseline {label} overflow at {width}'
            # Blur the native select/summary before resizing text. Let Chromium
            # finish RTL focus scrolling before measuring the stable layout.
            page.evaluate("document.activeElement?.blur(); document.documentElement.style.fontSize='32px'")
            page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
            page.evaluate("window.scrollTo({left:0,top:window.scrollY,behavior:'instant'})")
            if page.evaluate('document.documentElement.scrollWidth')>width+1:
                page.screenshot(path=f'work/mobile-{width}-baseline-overflow.png',full_page=False)
                overflow=page.evaluate("""() => [...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.left < -1||r.right>document.documentElement.clientWidth+1)}).map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.slice(0,100),rect:[e.getBoundingClientRect().left,e.getBoundingClientRect().right]})).slice(-20)""")
                metrics=page.evaluate("() => ({inner:innerWidth,client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,x:scrollX,visual:visualViewport.width,navWidth:getComputedStyle(document.querySelector('.bottom-nav')).width})")
                raise AssertionError(f'Baseline {label} 200% overflow at {width}: {metrics} {overflow}')
            page.evaluate("document.documentElement.style.fontSize='16px'")
        company_select.select_option('initial-0')
        exchange.get_by_role('heading',name='מחקר בסיס ל־NBIS',exact=True).wait_for()
        exchange.get_by_text('NBIS · מחשבון תרחישים מספרי לסוף 2027',exact=True).click()
        exchange.get_by_text('עריכת ההנחות · דוב',exact=True).click()
        exchange.get_by_label('מחיר גיוס הון עתידי למניה ($)').first.fill('0')
        exchange.get_by_role('alert').wait_for()
        exchange.get_by_role('button',name='איפוס הנחות',exact=True).first.click()
        assert exchange.get_by_role('alert').count()==0
        page.evaluate("document.activeElement?.blur(); document.documentElement.style.fontSize='32px'")
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'NBIS valuation 200% overflow at {width}'
        page.screenshot(path=f'work/mobile-{width}-valuation.png',full_page=False)
        page.evaluate("document.documentElement.style.fontSize='16px'")
        exchange.get_by_text('NBIS · מחשבון תרחישים מספרי לסוף 2027',exact=True).click()
        exchange.locator('summary').filter(has_text='1. קריאת PDF').click()
        # Small in-memory PDF fixture tests the actual bundled PDF.js worker.
        content=b'BT /F1 12 Tf 40 150 Td (PULSE SOURCE TEST 2026) Tj ET'
        objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream']
        pdf=b'%PDF-1.4\n';offsets=[0]
        for idx,obj in enumerate(objects,1):
            offsets.append(len(pdf));pdf+=str(idx).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
        xref=len(pdf);pdf+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
        pdf+=b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF'
        exchange.get_by_label('קובץ מסמך',exact=True).set_input_files({'name':'source-test.pdf','mimeType':'application/pdf','buffer':pdf})
        exchange.get_by_role('button',name='חילוץ טקסט מהקובץ',exact=True).click()
        page.wait_for_function("document.querySelector('.research-exchange textarea').value.includes('PULSE SOURCE TEST 2026')")
        exchange.locator('summary').filter(has_text='2. החזרת ניתוח').click()
        fields={k:'' for k in ('thesis','revenue','profitability','cashFlow','valuation','advantages','catalysts','risks','bear','base','bull')}
        fields['thesis']='MOBILE TEST IMPORT ONLY'
        payload={'version':1,'companyId':'candidate-nebius','asOf':'2026-10-18','fields':fields,'sourceUrls':['https://nebius.com/financials'],'missing':['SIMULATED mobile test']}
        exchange.get_by_role('textbox',name='ניתוח להחזרה',exact=True).fill('SIMULATED ChatGPT answer\n```json\n'+json.dumps(payload)+'\n```\nEnd of test answer')
        exchange.get_by_role('button',name='בדיקה ותצוגה מקדימה',exact=True).click()
        exchange.get_by_role('button',name='החלת השדות שבחרתי בטיוטה',exact=True).click()
        page.get_by_role('button',name='שמירת מחקר',exact=True).click()
        assert page.evaluate("JSON.parse(localStorage.getItem('pulse.personal.v1')).research.NBIS.thesis")=='MOBILE TEST IMPORT ONLY'
        prior=page.evaluate("JSON.parse(localStorage.getItem('pulse.personal.v1')).research.NBIS.versions[0].fields.thesis")
        page.reload();nav.get_by_role('button',name='מחקר',exact=True).click()
        exchange=page.get_by_role('region',name='ניתוח מסמכים וייבוא מחקר')
        exchange.locator('summary').filter(has_text='גרסאות מחקר קודמות').click()
        exchange.get_by_text('הצגת הגרסה',exact=True).first.click()
        exchange.get_by_role('button',name='טעינת גרסה זו לטיוטה',exact=True).first.click()
        page.get_by_role('button',name='שמירת מחקר',exact=True).click()
        assert page.evaluate("JSON.parse(localStorage.getItem('pulse.personal.v1')).research.NBIS.thesis")==prior
        assert page.evaluate("JSON.parse(localStorage.getItem('pulse.personal.v1')).research.NBIS.versions[0].fields.thesis")=='MOBILE TEST IMPORT ONLY'
        assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'Research exchange overflow at {width}'
        page.screenshot(path=f'work/mobile-{width}-research.png',full_page=False)
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
