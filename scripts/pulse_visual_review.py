"""Visual QA of all five PULSE routes in real headless Chromium.

Screenshots demonstrate the PR preview only. They are not a deployed release
or a physical Android/PWA notification test.
"""
from pathlib import Path
import json
import os
from playwright.sync_api import sync_playwright

URL=os.environ.get("PULSE_CHECK_URL","http://127.0.0.1:4173/pulse-investment-research./").rstrip("/")+"/"
OUT=Path("work/premium-review")
OUT.mkdir(parents=True,exist_ok=True)

def capture(page,*,desktop=False):
    nav=page.get_by_role("navigation",name="ניווט נייד") if not desktop else page.locator(".desktop-nav")
    assert nav.count()==1
    labels={
        "home":"בית","portfolio":"תיק השקעות","research":"מחקר",
        "news":"חדשות","watchlist":"מעקב"
    }
    result=[]
    for key,label in labels.items():
        nav.get_by_role("button",name=label,exact=True).click()
        page.wait_for_timeout(120)
        assert page.locator("html").get_attribute("dir")=="rtl"
        mode="desktop" if desktop else "mobile-390"
        filename=OUT/f"{mode}-{key}.png"
        page.screenshot(path=str(filename),full_page=True,animations="disabled")
        result.append({"view":key,"file":str(filename),"desktop":desktop})
    page.get_by_role("button",name="הגדרות PULSE",exact=True).click()
    dialog=page.get_by_role("dialog",name="הגדרות PULSE · מחקר ותצוגה")
    dialog.get_by_role("button",name="בהיר",exact=True).click()
    assert page.locator("html").get_attribute("data-pulse-theme")=="light"
    filename=OUT/("desktop-settings-light.png" if desktop else "mobile-390-settings-light.png")
    page.screenshot(path=str(filename),full_page=True,animations="disabled")
    result.append({"view":"settings-light","file":str(filename),"desktop":desktop})
    return result

with sync_playwright() as p:
    browser=p.chromium.launch()
    gallery=[]
    for width,height,desktop in ((390,844,False),(1366,900,True)):
        context=browser.new_context(viewport={"width":width,"height":height},device_scale_factor=1)
        page=context.new_page()
        page.goto(URL,wait_until="domcontentloaded")
        page.locator("main").wait_for(timeout=12000)
        gallery.extend(capture(page,desktop=desktop))
        context.close()
    browser.close()
(OUT/"manifest.json").write_text(json.dumps({"kind":"unmerged-pr-preview",
  "verifiedWith":"Playwright Chromium; does not assert actual Android behavior",
  "screenshots":gallery},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"screenshots":len(gallery),"status":"visual-review-artifacts-created"}))
