from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:4173/?path=nav", wait_until="networkidle")
    page.evaluate(
        """() => {
      const el = document.querySelector('[data-find=nav]');
      if (el) el.click();
    }"""
    )
    page.wait_for_timeout(250)
    page.evaluate("() => { const n=document.getElementById('diaryNext'); if(n) n.click(); }")
    page.wait_for_timeout(150)
    page.evaluate("() => { const n=document.getElementById('diaryNext'); if(n) n.click(); }")
    page.wait_for_timeout(200)
    page.evaluate(
        """() => {
      if (window.__hauntSetMood) window.__hauntSetMood(4);
      if (window.__hauntSetStage) window.__hauntSetStage(3);
      const c = document.getElementById('diaryClose');
      if (c) c.click();
    }"""
    )
    page.wait_for_timeout(700)
    t = page.evaluate(
        """() => ({
      l1: document.getElementById('titleL1') && document.getElementById('titleL1').textContent,
      l2: document.getElementById('titleL2') && document.getElementById('titleL2').textContent,
      stage: document.body.getAttribute('data-stage'),
      classes: document.body.className,
      eyebrow: document.getElementById('eyebrow') && document.getElementById('eyebrow').textContent,
      lede: document.querySelector('.stasis-lede') && document.querySelector('.stasis-lede').innerText.slice(0,120)
    })"""
    )
    print(json.dumps(t, ensure_ascii=False, indent=2))
    page.screenshot(path="qa-p2b.png")
    page.evaluate("() => { if (window.__hauntSummon) window.__hauntSummon(); }")
    page.wait_for_timeout(4500)
    page.screenshot(path="qa-climax2.png")
    page.wait_for_timeout(8000)
    page.screenshot(path="qa-climax5.png")
    print("shots ok")
    b.close()
