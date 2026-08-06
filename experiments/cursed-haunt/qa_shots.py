from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:4173/?path=nav", wait_until="networkidle")
    page.screenshot(path="qa-p1.png")
    page.evaluate(
        """() => {
      const el = document.querySelector('[data-find=nav]');
      if (el) el.click();
    }"""
    )
    page.wait_for_timeout(500)
    page.screenshot(path="qa-diary.png")
    page.evaluate(
        """() => {
      const n = document.getElementById('diaryNext');
      if (n) { n.click(); }
    }"""
    )
    page.wait_for_timeout(200)
    page.evaluate(
        """() => {
      const n = document.getElementById('diaryNext');
      if (n) { n.click(); }
    }"""
    )
    page.wait_for_timeout(300)
    page.evaluate(
        """() => {
      if (window.__hauntSetStage) window.__hauntSetStage(3);
      if (window.__hauntSetMood) window.__hauntSetMood(4);
      const c = document.getElementById('diaryClose');
      if (c) c.click();
    }"""
    )
    page.wait_for_timeout(1000)
    page.screenshot(path="qa-p2.png")
    page.evaluate("() => { if (window.__hauntSummon) window.__hauntSummon(); }")
    page.wait_for_timeout(4000)
    page.screenshot(path="qa-climax.png")
    print("ok")
    b.close()
