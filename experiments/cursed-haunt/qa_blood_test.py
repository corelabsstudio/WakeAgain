from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:4173/?creator=1", wait_until="networkidle")
    page.evaluate(
        """() => {
      window.__hauntDiaryDiscovered = true;
      document.body.classList.add('diary-found', 'phase-2-active');
      if (window.__hauntSetStage) window.__hauntSetStage(2);
      window.__hauntAnomalies.bloodText(true);
    }"""
    )
    page.wait_for_timeout(1500)
    r = page.evaluate(
        """() => {
      const drips = [...document.querySelectorAll('.anom-blood-drip.from-letter')];
      const title = document.getElementById('mainTitle');
      return {
        layers: document.querySelectorAll('.anom-blood-layer').length,
        drips: drips.length,
        beads: document.querySelectorAll('.anom-blood-bead').length,
        bleeding: !!(title && title.classList.contains('anom-bleeding')),
        sample: drips.slice(0, 4).map((d) => ({ left: d.style.left, top: d.style.top })),
      };
    }"""
    )
    print("first", r)
    page.screenshot(path="qa-blood-letters.png", full_page=False)
    page.evaluate("() => window.__hauntAnomalies.bloodText(false)")
    page.wait_for_timeout(200)
    print(
        "second cooldown",
        page.evaluate("() => document.querySelectorAll('.anom-blood-layer').length"),
    )
    b.close()
print("ok")
