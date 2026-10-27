"""Headless Chromium mobile/text/keyboard emulation; not a physical Android test."""
import json
import hashlib
import os
import time
import urllib.request
from urllib.parse import urljoin
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

URL=os.environ.get('PULSE_CHECK_URL','http://127.0.0.1:4173/pulse-investment-research./').rstrip('/')+'/'
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
    assets=pw.request.new_context()
    checked_assets=[]
    manifest=json.loads(Path('src/data/newResearchSourceManifest.json').read_text())
    for item in manifest['research']:
        pdf_url=urljoin(URL,'research/'+item['filename'])
        response=assets.get(pdf_url,timeout=30000)
        assert response.status==200,f'Research PDF link failed: {pdf_url} ({response.status})'
        body=response.body()
        assert body.startswith(b'%PDF') and len(body)==item['bytes'],f'Research PDF bytes changed: {pdf_url}'
        assert hashlib.sha256(body).hexdigest()==item['sha256'],f'Research PDF hash changed: {pdf_url}'
        page_name='Gilat_Telecom' if item['ticker']=='Gilat Telecom' else item['ticker']
        pages_url=urljoin(URL,'research-pages/'+page_name+'.pages.json')
        response=assets.get(pages_url,timeout=30000)
        assert response.status==200,f'Research page JSON link failed: {pages_url} ({response.status})'
        pages=response.json()['pages']
        assert len(pages)==item['pages'] and all(p['text'].strip() for p in pages),f'Research page content missing: {pages_url}'
        checked_assets.append({'pdf':pdf_url,'sha256':item['sha256'],'pages':pages_url})
    latest_asset=assets.get(urljoin(URL,'data/latest-research-updates.json'),timeout=30000)
    history_asset=assets.get(urljoin(URL,'data/research-update-history.json'),timeout=30000)
    coverage_asset=assets.get(urljoin(URL,'data/issuer-coverage.json'),timeout=30000)
    assert latest_asset.status==200 and history_asset.status==200 and coverage_asset.status==200,'Research JSON assets unavailable'
    published=latest_asset.json()
    history_data=history_asset.json()
    coverage=coverage_asset.json()
    registry=json.loads(Path('public/data/official-registry.json').read_text(encoding='utf-8'))
    registered_ids={c['id'] for c in registry['companies']}
    assert len(coverage['coverage'])==len(published['reports'])==12,'Not every issuer covered'
    assert {r['companyId'] for r in coverage['coverage']}==registered_ids,'Coverage identity mismatch'
    assert {r['companyId'] for r in published['reports']}==registered_ids,'Report identity mismatch'
    assert len([r for r in coverage['coverage'] if r['report']])>=6,'Unexpected loss of retained reports'
    assert all(r['metricCoverage'] in ('no-document','report-only','provisional-structured')
               for r in coverage['coverage'])

    assert published['version']==1 and history_data['version']==1,'Research JSON version mismatch'
    current_by_ticker={r['ticker']:r for r in published['reports']}
    for ticker,ids in [('DLO',{'revenue','grossProfit','operatingCash','capex'}),
                       ('IREN',{'revenue','operatingCash','capex'})]:
        report=current_by_ticker[ticker]
        assert ids.issubset({m['id'] for m in report['metrics']}),f'Missing published {ticker} metrics'
        assert report['reviewRequired'] is True and report['aiAnalysisEnabled'] is False
        assert any(item['companyId']==report['companyId'] and item['contentId']==report['contentId']
                   for item in history_data['entries']),f'Published {ticker} history does not match latest source'
    assert current_by_ticker['DLO']['status']=='needs-reconciliation'
    assert current_by_ticker['IREN']['status']=='historical-baseline-pending-review'
    for ticker, expected, unit in [('אנלייט','165.99','USD million'),('גילת טלקום','71.446','ILS million')]:
        r=current_by_ticker[ticker]
        selfmetric=next((m for m in r['metrics'] if m['id']=='revenue'),None)
        assert selfmetric and str(selfmetric['value'])==expected and selfmetric['unit']==unit,ticker
        assert r['reviewRequired'] is True and r['aiAnalysisEnabled'] is False
        assert any(item['companyId']==r['companyId'] and item['contentId']==r['contentId'] for item in history_data['entries'])
    # Every generated AI packet is a read-only source *input*, never a
    # deployed AI response, approved valuation or private portfolio snapshot.
    ai_packet_count=0
    for issuer in registry['companies']:
        key=issuer['ticker'] or issuer['id']
        packet_resp=assets.get(urljoin(URL,'data/ai-research-packets/'+key+'.json'),timeout=30000)
        assert packet_resp.status==200,f'Missing AI context for {key}'
        packet=packet_resp.json()
        assert packet['companyId']==issuer['id'],f'Cross-issuer packet for {key}'
        assert packet['trustPolicy']['aiAnalysisExecuted'] is False
        assert packet['trustPolicy']['mayModifyTargetsOrProbabilities'] is False
        assert packet['trustPolicy']['includesPersonalPortfolio'] is False
        current=next(r for r in published['reports'] if r['companyId']==issuer['id'])
        bridge=packet['latestIssuerResearch']
        assert len(bridge['sourceBoundMetrics'])==len(current['metrics']),f'AI context facts dropped for {key}'
        assert bridge['modelEligible'] is False
        if key=='FTAI':
            if current['metrics']:
                assert bridge['status']=='pending-review' and bridge['report']['digest']
                assert all(m['reviewStatus']=='pending-review' and m['modelEligible'] is False
                           for m in bridge['sourceBoundMetrics'])
            else:
                assert bridge['status']=='insufficient-evidence' and not bridge['sourceBoundMetrics']
        ai_packet_count+=1
    assert ai_packet_count==12

    ftai=current_by_ticker['FTAI']
    if ftai['metrics']:
        assert ftai['status']=='pending-review' and ftai['reviewRequired'] is True
        assert ftai['reportEvidence'] and ftai['sourceVersion']==ftai['reportEvidence']['sha256']
        assert all(m['reviewStatus']=='pending-review' for m in ftai['metrics'])
    else:
        assert ftai['status']=='insufficient-evidence', 'No FTAI metrics must be labeled as insufficient evidence'
    assert current_by_ticker['SMCI']['status']=='pending-review'
    smci={m['id']:m for m in current_by_ticker['SMCI']['metrics']}
    assert smci['revenue']['value']==39063.072
    assert smci['revenue']['previousValue']==21972.042
    assert smci['revenue']['reviewStatus']=='pending-review'
    assert any(item['companyId']=='us-smci-nasdaq-common' and item['contentId']==current_by_ticker['SMCI']['contentId']
               for item in history_data['entries']),'No SEC XBRL history for SMCI'

    Path('work/mobile-published-research.json').write_text(
        json.dumps({'url':URL,'companyStatuses':{k:r['status'] for k,r in current_by_ticker.items()},
                    'historyEntries':len(history_data['entries']),
                    'aiReadOnlyIssuerPackets':ai_packet_count,
                    'companies':len(published['reports']), 'retainedDocCompanies':len([r for r in coverage['coverage'] if r['report']]),
                    'verifiedAgainstActualPublishedJson':True},ensure_ascii=False,indent=2))
    assets.dispose()
    Path('work/mobile-research-assets.json').write_text(json.dumps({'url':URL,'checked':checked_assets},ensure_ascii=False))
    for width in (320,390,430):
        context=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
        page=context.new_page()
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(URL);page.get_by_role('heading',name='התדריך היומי.',exact=True).wait_for()
        page.get_by_text('התראות לאנדרואיד • הגדרה חד־פעמית',exact=True).wait_for()
        assert page.locator('html').get_attribute('dir')=='rtl'
        assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'Horizontal overflow at {width}'
        page.get_by_role('heading',name='תמונת המאקרו',exact=True).wait_for()
        page.get_by_role('button',name='השבוע הבא',exact=True).click()
        page.get_by_role('button',name='השבוע הנוכחי',exact=True).click()
        page.evaluate("document.activeElement?.blur();document.documentElement.style.fontSize='32px'")
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'Macro and calendar 200% overflow at {width}'
        page.get_by_role('heading',name='תמונת המאקרו',exact=True).scroll_into_view_if_needed()
        page.screenshot(path=f'work/mobile-{width}-macro.png',full_page=False)
        page.evaluate("document.documentElement.style.fontSize='16px'")
        nav=page.get_by_role('navigation',name='ניווט נייד')
        nav.get_by_role('button',name='חדשות',exact=True).click()
        page.get_by_role('textbox',name='חיפוש חדשות').fill('Nebius')
        assert page.get_by_role('article').count()>0
        card=page.get_by_role('article').first
        card.get_by_role('button',name='סימון כנקרא',exact=True).click()
        assert card.get_by_role('button',name='נקרא — ביטול סימון',exact=True).get_attribute('aria-pressed')=='true'
        page.screenshot(path=f'work/mobile-{width}.png',full_page=False)
        page.get_by_text('סינון נוסף',exact=True).click()
        page.evaluate("document.activeElement?.blur();document.documentElement.style.fontSize='32px'")
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'200% text overflow at {width}'
        page.get_by_role('button',name='רענון מידע',exact=True).scroll_into_view_if_needed()
        page.screenshot(path=f'work/mobile-{width}-text200.png',full_page=False)
        # Emulate keyboard's visual viewport independently from layout viewport.
        page.evaluate("document.documentElement.style.fontSize='16px'")
        nav.get_by_role('button',name='מחקר',exact=True).click()
        page.get_by_role('tab',name='מקורות וכלים',exact=True).click()
        official=page.get_by_role('region',name='מקורות רשמיים וחבילת מחקר')
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
        selections=[(f'initial-{i}',label) for i,label in enumerate(labels)]+[('research-us-smci-nasdaq-common','SMCI')]
        supplied={'NBIS':('NBIS',12,'$182.33'),'SNDK':('SNDK',13,'$1,759.50'),'DLO':('DLO',10,'$23.31'),'בריינסוויי':('BWAY',16,'$13.40'),'SMCI':('SMCI',14,'$50.92')}
        for index,(option,label) in enumerate(selections):
            company_select.select_option(option)
            page.get_by_role('tab',name='סקירה',exact=True).click()
            exchange.get_by_role('heading',name=f'מחקר בסיס ל־{label}',exact=True).wait_for()
            latest=exchange.get_by_role('region',name='עדכון המחקר האחרון',exact=True)
            latest.get_by_role('heading',name='עדכון המחקר האחרון שנקלט',exact=True).wait_for()
            if label=='DLO':
                expect(latest).to_contain_text('נדרש בירור גרסת מקור')
                expect(latest).to_contain_text('399.7 USD million')
                expect(latest).to_contain_text('21.14')
                expect(latest).to_contain_text('מודל משני בארכיון')
                expect(latest).to_contain_text('היסטוריית גרסאות מחקר ('+str(sum(x['ticker']==label for x in history_data['entries']))+')')
                expect(latest).to_contain_text('לא ניתוח AI')
                latest.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-latest-research-dlo.png',full_page=False)
            if label=='IREN':
                expect(latest).to_contain_text('נתוני בסיס היסטוריים')
                expect(latest).to_contain_text('707 USD million')
                expect(latest).to_contain_text('4,333.1 USD million')
                expect(latest).to_contain_text('4,500 USD million')
                expect(latest).to_contain_text('אין הפתעת תחזית מוכחת')
                expect(latest).to_contain_text('היסטוריית גרסאות מחקר ('+str(sum(x['ticker']==label for x in history_data['entries']))+')')
                latest.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-latest-research-iren.png',full_page=False)
            if label=='NBIS':
                expect(latest).to_contain_text('582.3 USD million')
                expect(latest).to_contain_text('105.1 USD million')
                expect(latest).to_contain_text('ממתין לבדיקה')
                expect(latest).to_contain_text('מסמך מקור שמור')
                latest.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-issuer-nbis.png',full_page=False)
            if label in ('SNDK','בריינסוויי'):
                expect(latest).to_contain_text('מסמך מקור שמור')
                if label=='SNDK':
                    expect(latest).to_contain_text('8,965 USD million')
                    expect(latest).to_contain_text('1,901 USD million')
                    expect(latest).to_contain_text('2026-07-03')
                latest.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-issuer-{("sndk" if label=="SNDK" else "brainsway")}.png',full_page=False)
            if label=='אנלייט':
                expect(latest).to_contain_text('165.99 USD million')
                expect(latest).to_contain_text('209.691 USD million')
                expect(latest).to_contain_text('מסמך מקור שמור')
                latest.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-issuer-enlight.png',full_page=False)
            if label=='גילת טלקום':
                expect(latest).to_contain_text('71.446 ILS million')
                expect(latest).to_contain_text('66.508 ILS million')
                expect(latest).to_contain_text('מסמך מקור שמור')
                latest.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-issuer-gilat-telecom.png',full_page=False)
            if label=='FTAI':
                if ftai['metrics']:
                    expect(latest).to_contain_text('ממתין לבדיקה')
                else:
                    expect(latest).to_contain_text('אין עדכון פיננסי מבוסס מקור')
            if label=='SMCI':
                expect(latest).to_contain_text('39,063.072 USD million')
                expect(latest).to_contain_text('21,972.042 USD million')
                expect(latest).to_contain_text('ממתין לבדיקת אנליסט')
                latest.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-issuer-smci.png',full_page=False)
            if label=='IREN':
                actuals=exchange.get_by_role('region',name='נתוני בסיס IREN FY2026 מהדוח הרשמי',exact=True)
                expect(actuals).to_contain_text('$707.0M')
                expect(actuals).to_contain_text('$2,100.4M')
                expect(actuals).to_contain_text('$4,333.1M')
                expect(actuals).to_contain_text('2,998.0 + 1,335.1 = 4,333.1')
                expect(actuals).to_contain_text('ממתין לבדיקת אנליסט')
                expect(actuals).to_contain_text('אינם הפתעה ואינם בדיקת איכות התחזית')
                expect(actuals.get_by_text('אין השוואה מספרית תקפה',exact=True)).to_have_count(3)
                expect(actuals.get_by_role('link',name='מקור רשמי · PDF עמוד 12 ↗',exact=True)).to_have_attribute('href','https://iren.gcs-web.com/static-files/1cb9f4da-d4c7-4510-8bda-e475022b59f5#page=12')
                page.evaluate("document.activeElement?.blur();document.documentElement.style.fontSize='32px'")
                page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'IREN actual financial results 200% overflow at {width}'
                page.evaluate("document.documentElement.style.fontSize='16px'")
                actuals.locator('article').first.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-iren-fy26.png',full_page=False)
            if label in ('NBIS','DLO'):
                actuals=exchange.get_by_role('region',name=f'נתוני בסיס {label} Q2 2026 מהדוח הרשמי',exact=True)
                expected=('$582.3M','$-175.9M','$2,246.1M','$5,657.4M') if label=='NBIS' else ('$399.7M','$127.2M','$64.2M','$9.91M')
                for value in expected:expect(actuals).to_contain_text(value)
                expect(actuals).to_contain_text('ממתין לבדיקת אנליסט')
                expect(actuals.get_by_text('אין השוואה מספרית תקפה',exact=True)).to_have_count(4)
                expect(actuals.get_by_role('link',name='מקור רשמי',exact=False)).to_have_count(4)
                page.evaluate("document.activeElement?.blur();document.documentElement.style.fontSize='32px'")
                page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'{label} Q2 results 200% overflow at {width}'
                page.evaluate("document.documentElement.style.fontSize='16px'")
                actuals.locator('article').first.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-{label.lower()}-q2-2026.png',full_page=False)
            if label=='SMCI':
                actuals=exchange.get_by_role('region',name='נתוני בסיס SMCI FY2026 מהדוח הרשמי',exact=True)
                for value in ['$39,063.072M','$2,770.486M','$-6,809.886M']:
                    expect(actuals).to_contain_text(value)
                expect(actuals).to_contain_text('01.07.2025–30.06.2026')
                expect(actuals).to_contain_text('ממתין לבדיקת אנליסט')
                expect(actuals.get_by_text('אין השוואה מספרית תקפה',exact=True)).to_have_count(3)
                expect(actuals.get_by_role('link',name='פרטי הגשת SEC ↗',exact=True)).to_have_count(3)
                expect(actuals.get_by_role('link',name='מקור רשמי · 10-K עמוד 63 · CONSOLIDATED STATEMENTS OF CASH FLOWS ↗',exact=True)).to_have_attribute('href','https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/smci-20260630.htm#:~:text=CONSOLIDATED%20STATEMENTS%20OF%20CASH%20FLOWS')
                page.evaluate("document.activeElement?.blur();document.documentElement.style.fontSize='32px'")
                page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'SMCI actual financial results 200% overflow at {width}'
                page.evaluate("document.documentElement.style.fontSize='16px'")
                actuals.locator('article').first.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-smci-fy26.png',full_page=False)
            page.get_by_label('הדוח הבא',exact=True).wait_for()
            if label=='NBIS':expect(exchange.locator('.research-target-summary strong')).to_have_text('≈$182.33')
            if label=='SNDK':expect(exchange.locator('.research-target-summary strong')).to_have_text('≈$1,759.50')
            full_reading=exchange.get_by_text('קריאת המחקר המלא',exact=True)
            if full_reading.evaluate('(el)=>!el.parentElement.open'):full_reading.click()
            if label in supplied:
                ticker,chapter_count,supplied_target=supplied[label]
                monitor=exchange.get_by_role('region',name=f'מעקב התזה של {ticker}',exact=True)
                expect(monitor.locator('details')).to_have_count(6)
                assert monitor.locator('details[open]').count()==0
                for summary in monitor.locator('summary').all():summary.click()
                expect(monitor.get_by_text('מה לבדוק בדוח הבא:',exact=True)).to_have_count(6)
                page.evaluate("document.activeElement?.blur();document.documentElement.style.fontSize='32px'")
                page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'Thesis monitor {label} 200% overflow at {width}'
                page.evaluate("document.documentElement.style.fontSize='16px'")
                monitor.locator('summary').first.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-thesis-{label}.png',full_page=False)
                monitor.get_by_role('button',name='לנתוני המקור',exact=False).first.click()
                assert '-pdf-section-' in page.evaluate("document.activeElement.id")
                for summary in monitor.locator('summary').all():summary.click()
                context_panel=exchange.get_by_role('region',name=f'אופק והנחות השווי של {ticker}',exact=True)
                expect(context_panel).to_contain_text('אינו שער חי')
                if label=='SNDK':expect(context_panel).to_contain_text('אין מועד יעד קשיח')
                chapters=exchange.get_by_role('navigation',name=f'פרקי הניתוח של {ticker}')
                expect(chapters.get_by_role('button')).to_have_count(chapter_count)
                chapters.get_by_role('button').nth(9).click()
                intake=exchange.get_by_role('group',name='קליטת תוכן דוחות רשמיים')
                if intake.count():
                    intake.locator(':scope > summary').click()
                    expect(intake).to_contain_text('המחקר ומחיר השווי אינם משתנים אוטומטית')
                    document=intake.locator('.intake-document').first
                    if document.count():
                        document.locator(':scope > summary').click()
                        table_details=document.get_by_text('שורות מטבלאות המקור · לבדיקת תקופה ויחידות',exact=True)
                        if table_details.count():table_details.click()
                    page.evaluate("document.activeElement?.blur();document.documentElement.style.fontSize='32px'")
                    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                    assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'Intake {label} 200% overflow at {width}'
                    page.evaluate("document.documentElement.style.fontSize='16px'")
                    intake.locator(':scope > summary').click()
            page.evaluate("document.activeElement?.blur();document.documentElement.style.fontSize='32px'")
            page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
            assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'Overview {label} overflow at {width}'
            page.evaluate("document.documentElement.style.fontSize='16px'")
            page.get_by_role('tab',name='מודל שווי',exact=True).click()
            if label in supplied:
                expect(exchange.get_by_test_id('supplied-weighted-target')).to_have_text(supplied[label][2])
                if label=='SMCI':
                    assert exchange.locator('.prior-research-models').count()==0
                    continue
                archive=exchange.get_by_text('ארכיון מודלים קודמים · אינו הניתוח הפעיל',exact=True)
                if archive.evaluate('(el)=>!el.parentElement.open'):archive.click()
            model=exchange.locator('.company-valuation')
            model.locator('summary').filter(has_text='תרחישים, חישוב ורגישויות').click()
            model.get_by_test_id('weighted-model-target').wait_for()
            for scenario in ['דוב','בסיס','שור']:
                model.get_by_text(f'הנחות {scenario} וחישוב',exact=True).click()
            model.get_by_label('משקל דוב במודל (%)',exact=True).fill('30')
            model.get_by_role('alert').wait_for()
            model.get_by_role('button',name='שחזור הנחות המודל המחושב',exact=True).click()
            expect(model.get_by_role('alert')).to_have_count(0)
            model.get_by_text('רגישות לשינוי בהנחות',exact=True).click()
            model.get_by_text('עובדות מהמקורות ומגבלות המודל',exact=True).click()
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
            if label in ['NBIS','גילת טלקום']:
                model.locator('h4').first.scroll_into_view_if_needed()
                page.screenshot(path=f'work/mobile-{width}-model-{index}.png',full_page=False)
        company_select.select_option('initial-0')
        page.get_by_role('tab',name='מודל שווי',exact=True).click()
        archive=exchange.get_by_text('ארכיון מודלים קודמים · אינו הניתוח הפעיל',exact=True)
        if archive.evaluate('(el)=>!el.parentElement.open'):archive.click()
        exchange.get_by_text('NBIS · המודל שלנו ל־12 חודשים',exact=True).click()
        exchange.get_by_text('בדיקת היתכנות היעדים המקוריים',exact=True).click()
        for label,value in [('מזומן חופשי במועד היעד','3000'),('חוב בכיר נוסף במועד היעד','5000'),('מניות נוספות עד היעד','20'),('שווי החזקות נוסף','1000'),('חלק מתוספת הפירעון המלאה (%)','50'),('הכנסה שנתית לצורך בדיקת המכפיל','11000'),('שיעור EBITDA מתואם (%)','40')]:
            exchange.get_by_label(label,exact=True).fill(value)
        expect(exchange.get_by_text('מכפיל EBITDA נדרש:',exact=False)).to_have_count(3)
        exchange.get_by_label('הסתברות דוב (%)').fill('30')
        exchange.get_by_role('alert').wait_for()
        exchange.get_by_role('button',name='שחזור המודל המקורי',exact=True).first.click()
        assert exchange.get_by_role('alert').count()==0
        page.evaluate("document.activeElement?.blur(); document.documentElement.style.fontSize='32px'")
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        assert page.evaluate('document.documentElement.scrollWidth')<=width+1,f'NBIS valuation 200% overflow at {width}'
        page.screenshot(path=f'work/mobile-{width}-valuation.png',full_page=False)
        page.evaluate("document.documentElement.style.fontSize='16px'")
        exchange.get_by_text('NBIS · המודל שלנו ל־12 חודשים',exact=True).click()
        page.get_by_role('tab',name='מקורות וכלים',exact=True).click()
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
        page.wait_for_function("Array.from(document.querySelectorAll('.research-exchange textarea')).some(el => el.value.includes('PULSE SOURCE TEST 2026'))")
        exchange.locator('summary').filter(has_text='2. החזרת ניתוח').click()
        fields={k:'' for k in ('thesis','revenue','profitability','cashFlow','valuation','advantages','catalysts','risks','bear','base','bull')}
        fields['thesis']='MOBILE TEST IMPORT ONLY'
        payload={'version':1,'companyId':'candidate-nebius','asOf':'2026-10-18','fields':fields,'sourceUrls':['https://nebius.com/financials'],'missing':['SIMULATED mobile test']}
        exchange.get_by_role('textbox',name='ניתוח להחזרה',exact=True).fill('SIMULATED ChatGPT answer\n```json\n'+json.dumps(payload)+'\n```\nEnd of test answer')
        exchange.get_by_role('button',name='בדיקה ותצוגה מקדימה',exact=True).click()
        exchange.get_by_role('button',name='החלת השדות שבחרתי בטיוטה',exact=True).click()
        page.get_by_role('tab',name='המחקר שלי',exact=True).click()
        page.get_by_role('button',name='שמירת מחקר',exact=True).click()
        assert page.evaluate("JSON.parse(localStorage.getItem('pulse.personal.v1')).research.NBIS.thesis")=='MOBILE TEST IMPORT ONLY'
        prior=page.evaluate("JSON.parse(localStorage.getItem('pulse.personal.v1')).research.NBIS.versions[0].fields.thesis")
        page.reload();nav.get_by_role('button',name='מחקר',exact=True).click()
        page.get_by_role('tab',name='מקורות וכלים',exact=True).click()
        exchange=page.get_by_role('region',name='ניתוח מסמכים וייבוא מחקר')
        exchange.locator('summary').filter(has_text='גרסאות מחקר קודמות').click()
        exchange.get_by_text('הצגת הגרסה',exact=True).first.click()
        exchange.get_by_role('button',name='טעינת גרסה זו לטיוטה',exact=True).first.click()
        page.get_by_role('tab',name='המחקר שלי',exact=True).click()
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
        if width==390:
            # Browser-level offline smoke: ensure the *deployed PWA shell* and
            # last validated research snapshot remain readable with no network.
            page.wait_for_function("navigator.serviceWorker && !!navigator.serviceWorker.controller",timeout=20000)
            context.set_offline(True)
            page.reload(wait_until='domcontentloaded')
            page.get_by_role('heading',name='התדריך היומי.',exact=True).wait_for(timeout=10000)
            page.get_by_role('navigation',name='ניווט נייד').get_by_role('button',name='מחקר',exact=True).click()
            page.get_by_label('חברה למחקר',exact=True).select_option('initial-2')
            offline_latest=page.get_by_role('region',name='עדכון המחקר האחרון',exact=True)
            expect(offline_latest).to_contain_text('מצב לא מקוון')
            expect(offline_latest).to_contain_text('399.7 USD million')
            page.screenshot(path='work/mobile-390-offline-research.png',full_page=False)
            context.set_offline(False)
        assert not errors,errors
        results.append({'width':width,'rtl':True,'textScale':'200%','keyboard':'simulated visual viewport','overflow':False,'pageErrors':errors})
        context.close()
    browser.close()
Path('work/mobile-check.json').write_text(json.dumps({'environment':'headless Chromium; Android keyboard and text scaling simulated; no physical receipt test','results':results},indent=2))
print(json.dumps(results))

