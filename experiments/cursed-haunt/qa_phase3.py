from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    page.goto(
        "http://127.0.0.1:4173/?creator=1&debug=1&hintfast=1",
        wait_until="networkidle",
        timeout=20000,
    )
    page.wait_for_timeout(800)
    r = page.evaluate(
        """() => {
      window.__hauntDiaryDiscovered = true;
      document.body.classList.add('diary-found');
      if (window.__hauntSetStage) window.__hauntSetStage(2);
      if (window.__hauntSetMood) window.__hauntSetMood(3);
      const p2 = window.__hauntClimax && window.__hauntClimax.id;
      const p3 = window.__hauntPhase3 && window.__hauntPhase3.id;
      const role = window.__hauntClimax && window.__hauntClimax.role;
      if (window.__hauntEnterPhase3) window.__hauntEnterPhase3();
      return {
        p2Gate: p2,
        p3Trig: p3,
        role: role,
        phase3: !!window.__hauntPhase3Active,
        bodyP3: document.body.classList.contains('phase-3-active'),
        hintMs: window.__hauntPhase3 && window.__hauntPhase3.hintMs,
        p3All: window.__hauntPhase3 && window.__hauntPhase3.all.length,
        p2All: window.__hauntClimax && window.__hauntClimax.all.length,
        hasScript: !!document.querySelector('script[src="phase3-triggers.js"]'),
      };
    }"""
    )
    print("state", r)
    page.wait_for_timeout(600)
    toast = page.locator("#p3LayerToast.is-on").count()
    print("layer toast", toast)
    page.wait_for_timeout(9000)
    p3hint = page.evaluate(
        """() => {
      const t = document.getElementById('p3HintToast');
      const c = document.getElementById('p3MissionChip');
      return {
        toastHidden: t ? t.hidden : null,
        text: (document.getElementById('p3HintText') || {}).textContent || '',
        chipVisible: c ? !c.hidden : false,
      };
    }"""
    )
    print("after hint wait", p3hint)
    page.screenshot(path="qa-phase3.png", full_page=False)
    b.close()
print("ok")
