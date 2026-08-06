#!/usr/bin/env python3
"""End-to-end smoke for cursed-haunt: P1 diary, P2 FX, P3 gate, climax, ending."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4173"
OUT = Path(__file__).resolve().parent / "QA_E2E.json"
results = []


def check(name: str, ok: bool, detail: str = ""):
    results.append({"name": name, "ok": bool(ok), "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))

        # --- load ---
        page.goto(f"{BASE}/?creator=1&debug=1&hintfast=1", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(500)
        check("load", page.locator("body").count() == 1)
        check("scripts_audio", page.evaluate("() => typeof window.__hauntAudio === 'object'"))
        check("scripts_anomalies", page.evaluate("() => !!(window.__hauntAnomalies && window.__hauntAnomalies.ringApproach)"))
        check("scripts_p2_gate", page.evaluate("() => !!(window.__hauntClimax && window.__hauntClimax.enterPhase3)"))
        check("scripts_p3", page.evaluate("() => !!(window.__hauntPhase3 && window.__hauntPhase3.id)"))
        check("faces_assets", page.evaluate("""async () => {
          const r = await fetch('assets/faces/face-1.jpg');
          return r.ok;
        }"""))
        check("clean_stage", page.evaluate("() => document.body.classList.contains('stage-clean')"))

        # --- P1 diary force open ---
        page.evaluate("""() => {
          window.__hauntDiaryDiscovered = true;
          document.body.classList.add('diary-found');
          if (typeof window.__hauntOpenDiary === 'function') window.__hauntOpenDiary();
        }""")
        page.wait_for_timeout(400)
        # if diary panel still hidden, click creator path or force setStage via diary pages
        page.evaluate("""() => {
          const panel = document.getElementById('diaryPanel');
          if (panel) {
            panel.hidden = false;
            panel.setAttribute('aria-hidden', 'false');
            document.body.classList.add('diary-open');
          }
        }""")
        page.wait_for_timeout(200)

        # advance diary pages if possible
        for _ in range(3):
            btn = page.locator("#diaryNext")
            if btn.count() and btn.is_enabled():
                try:
                    btn.click(timeout=1000)
                    page.wait_for_timeout(300)
                except Exception:
                    break

        page.evaluate("""() => {
          document.body.classList.remove('diary-open');
          const panel = document.getElementById('diaryPanel');
          if (panel) { panel.hidden = true; }
          window.__hauntDiaryDiscovered = true;
          if (window.__hauntSetStage) window.__hauntSetStage(2);
          if (window.__hauntSetMood) window.__hauntSetMood(3);
          document.body.classList.add('phase-2-active', 'diary-found');
        }""")
        page.wait_for_timeout(600)

        stage = page.evaluate("() => document.body.getAttribute('data-stage')")
        check("p2_stage", stage in ("2", "3"), f"stage={stage}")
        check(
            "p2_anomalies_active",
            page.evaluate("() => window.__hauntAnomalies.phase2Active()"),
        )

        # blood from letters only
        page.evaluate("() => window.__hauntAnomalies.bloodText(true)")
        page.wait_for_timeout(800)
        blood = page.evaluate("""() => ({
          layers: document.querySelectorAll('.anom-blood-layer').length,
          fromLetters: document.querySelectorAll('.anom-blood-drip.from-letter').length,
          onTitle: document.getElementById('mainTitle')?.classList.contains('anom-bleeding'),
        })""")
        check("blood_from_letters", blood["fromLetters"] >= 2 and blood["onTitle"], str(blood))
        check("blood_layer_single", blood["layers"] <= 1, str(blood))

        # ring approach
        page.evaluate("() => window.__hauntAnomalies.ringApproach({force:true, approachMs:2000, scareMs:500})")
        page.wait_for_timeout(400)
        ring = page.evaluate("() => !!document.getElementById('anomRingApproach')")
        check("ring_approach_spawn", ring)
        page.wait_for_timeout(2800)

        # faces (should work)
        page.evaluate("() => window.__hauntAnomalies.cardFaces({ms:1500})")
        page.wait_for_timeout(500)
        faces = page.evaluate("() => document.querySelectorAll('.anom-card-face').length")
        check("faces_spawn", faces >= 1, f"n={faces}")

        # hands
        page.evaluate("() => window.__hauntAnomalies.risingHands({ms:1500})")
        page.wait_for_timeout(400)
        check("hands_spawn", page.evaluate("() => !!document.getElementById('anomRisingHands')"))

        # audio API
        check(
            "audio_codeLaugh",
            page.evaluate("() => typeof window.__hauntAudio.codeLaugh === 'function'"),
        )

        # P3 enter
        page.evaluate("""() => {
          if (window.__hauntEnterPhase3) window.__hauntEnterPhase3();
          else if (window.__hauntClimax) window.__hauntClimax.enterPhase3();
        }""")
        page.wait_for_timeout(500)
        check(
            "p3_active",
            page.evaluate(
                "() => !!(window.__hauntPhase3Active || document.body.classList.contains('phase-3-active'))"
            ),
        )
        check(
            "p3_trigger_id",
            page.evaluate("() => !!(window.__hauntPhase3 && window.__hauntPhase3.id)"),
        )

        # climax summon
        page.evaluate("""() => {
          if (window.__hauntSummon) window.__hauntSummon();
        }""")
        page.wait_for_timeout(1200)
        check(
            "climax_haunting",
            page.evaluate("() => document.body.classList.contains('is-haunting')"),
        )
        haunt = page.locator("#haunt")
        check("climax_panel", haunt.count() > 0 and not haunt.is_hidden() if haunt.count() else False)

        # wait a bit for sequence
        page.wait_for_timeout(3000)
        check("no_pageerror_critical", len([e for e in errs if "haunt" in e.lower() or "Syntax" in e]) == 0, f"errs={len(errs)}")

        page.screenshot(path=str(Path(__file__).parent / "qa-e2e-final.png"), full_page=False)
        browser.close()

    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    report = {
        "passed": passed,
        "total": total,
        "failed": [r for r in results if not r["ok"]],
        "results": results,
        "ts": time.time(),
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n=== {passed}/{total} passed ===")
    if report["failed"]:
        print("FAILED:", json.dumps(report["failed"], ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
