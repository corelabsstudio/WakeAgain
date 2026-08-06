from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.add_init_script("try{sessionStorage.clear()}catch(e){}")
    page.goto(
        "http://127.0.0.1:4173/?path=nav&debug=1&p3=hold_free",
        wait_until="networkidle",
    )
    page.wait_for_timeout(500)
    info = page.evaluate(
        """() => {
      const el = document.querySelector('[data-find=nav]');
      const r = el ? el.getBoundingClientRect() : null;
      return {
        search: location.search,
        path: document.body.getAttribute('data-find-path'),
        winPath: window.__hauntDiaryFindPath,
        classes: el && el.className,
        disabled: el && el.disabled,
        ariaHidden: el && el.getAttribute('aria-hidden'),
        rect: r && { w: r.width, h: r.height, x: r.x, y: r.y },
        display: el && getComputedStyle(el).display,
        opacity: el && getComputedStyle(el).opacity,
        pe: el && getComputedStyle(el).pointerEvents,
        visibility: el && getComputedStyle(el).visibility,
      };
    }"""
    )
    print("INFO", info)
    page.locator("#diaryHint").dispatch_event("click")
    page.wait_for_timeout(200)
    print(
        "after dispatch",
        page.evaluate(
            """() => ({
      open: document.body.classList.contains('diary-open'),
      disc: !!window.__hauntDiaryDiscovered,
      panelHidden: document.getElementById('diaryPanel').hidden
    })"""
        ),
    )
    page.evaluate(
        """() => {
      const el = document.querySelector('[data-find=nav]');
      if (el) el.click();
    }"""
    )
    page.wait_for_timeout(200)
    print(
        "after el.click",
        page.evaluate(
            """() => ({
      open: document.body.classList.contains('diary-open'),
      disc: !!window.__hauntDiaryDiscovered
    })"""
        ),
    )
    b.close()
