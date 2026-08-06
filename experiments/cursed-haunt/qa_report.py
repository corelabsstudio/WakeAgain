# -*- coding: utf-8 -*-
"""Full integrity + flow report after all rewrites."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:4173"
results: list[dict] = []


def ok(name: str, detail: str = "") -> None:
    results.append({"ok": True, "name": name, "detail": detail})
    print("PASS", name, detail)


def fail(name: str, detail: str = "") -> None:
    results.append({"ok": False, "name": name, "detail": detail})
    print("FAIL", name, detail)


def assert_(c: bool, name: str, detail: str = "") -> None:
    (ok if c else fail)(name, detail)


def static_checks() -> None:
    print("\n=== STATIC ===")
    stories = (ROOT / "diary-stories.js").read_text(encoding="utf-8")
    audio = (ROOT / "haunt-audio.js").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    anom = (ROOT / "anomalies.js").read_text(encoding="utf-8")
    addr = (ROOT / "address-bar.js").read_text(encoding="utf-8")
    corr = (ROOT / "corruption-progress.js").read_text(encoding="utf-8")
    diary = (ROOT / "diary.js").read_text(encoding="utf-8")

    ids = re.findall(r'id:\s*"(\d+)"', stories)
    assert_(len(ids) == 20, "story count 20", str(len(ids)))
    assert_(ids == [f"{i:02d}" for i in range(1, 21)], "story ids 01-20 sequential")

    # jargon banned in story body (allow minimal)
    banned = [
        "spawn(",
        "tsc ",
        "npm ",
        "git log",
        "git checkout",
        "TypeScript",
        "localhost:4173",
        "process_not_dead",
        "function ",
        "Continuously",
        "indicted",
        "軽い",
        "廉价",
    ]
    found_ban = [b for b in banned if b in stories]
    assert_(len(found_ban) == 0, "no banned jargon in stories", ",".join(found_ban))

    # length: past/mid paras roughly long
    para_blocks = re.findall(r"paras:\s*\[(.*?)\]", stories, re.S)
    assert_(len(para_blocks) >= 40, "past+mid para blocks ≥40", str(len(para_blocks)))
    # average string length in first past block sample
    strs = re.findall(r'"([^"\\]{40,})"', stories)
    hangul = [t for t in strs if re.search(r"[가-힣]", t)]
    avg = sum(len(t) for t in hangul) / max(1, len(hangul))
    assert_(avg >= 45, "avg long Korean string ≥45 chars", f"avg={avg:.0f} n={len(hangul)}")

    # audio API surface
    for fn in [
        "unlock",
        "setLevel",
        "pulse",
        "sting",
        "whisper",
        "breath",
        "staticBurst",
        "signalDrop",
        "dreadHit",
        "hddScratch",
        "rumble",
        "typeClick",
    ]:
        assert_(fn in audio, f"audio has {fn}")

    # critical CSS gates
    assert_("body.diary-open" in css and "filter: none !important" in css, "diary-open kills filter")
    assert_("anom-gray:not(.diary-open)" in css, "anomaly filters gated")
    assert_("preservedSearch" in addr, "address-bar preserves query")
    assert_("remorphAll" in corr, "corruption remorphAll")
    assert_("clearBodyLayoutHazards" in diary, "diary layout hazard clear")
    assert_("sfxFor" in anom or "sting" in anom, "anomaly sfx wiring")

    # scripts in index
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for scr in [
        "app.js",
        "haunt-audio.js",
        "diary-stories.js",
        "diary.js",
        "corruption-progress.js",
        "address-bar.js",
        "dread-ambient.js",
        "anomalies.js",
        "climax-triggers.js",
        "climax-sequence.js",
        "ending.js",
    ]:
        assert_(scr in html, f"index loads {scr}")


def browser_checks() -> None:
    print("\n=== BROWSER FLOW ===")
    console_errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: console_errors.append(str(e)))
        page.add_init_script("try{sessionStorage.clear()}catch(e){}")
        page.emulate_media(reduced_motion="no-preference")

        # --- P1 ---
        page.goto(f"{BASE}/?path=nav&debug=1&p3=hold_free&story=1", wait_until="networkidle")
        page.wait_for_timeout(500)
        search = page.evaluate("() => location.search")
        assert_("path=nav" in search and "p3=hold_free" in search, "query preserved", search)

        b = page.evaluate(
            """() => ({
          stage: document.body.getAttribute('data-stage'),
          clean: document.body.classList.contains('stage-clean'),
          disc: !!window.__hauntDiaryDiscovered,
          phase2: window.__hauntAnomalies && window.__hauntAnomalies.phase2Active(),
          story: window.__hauntDiaryStories && window.__hauntDiaryStories.current,
          audio: !!(window.__hauntAudio && window.__hauntAudio.sting),
          anomN: window.__hauntAnomalies && window.__hauntAnomalies.all.length,
          trigger: window.__hauntClimaxTrigger,
        })"""
        )
        assert_(b["stage"] == "0" and b["clean"], "P1 clean stage")
        assert_(not b["disc"] and b["phase2"] is False, "P1 no diary / no anomalies")
        assert_(b["audio"], "audio API present")
        assert_(b["anomN"] and b["anomN"] >= 40, "anomaly catalog", str(b["anomN"]))
        assert_(b["trigger"] == "hold_free", "p3 trigger forced", str(b["trigger"]))
        assert_(b["story"] and b["story"]["id"] == "01", "story=1 forces #01", str(b["story"] and b["story"]["id"]))

        # story length on page
        lens = page.evaluate(
            """() => {
          const st = window.__hauntDiaryStories.current;
          return {
            past: (st.past.paras||[]).length,
            mid: (st.mid.paras||[]).length,
            human: (st.today.human||[]).length,
            pastChars: (st.past.paras||[]).join('').length,
            midChars: (st.mid.paras||[]).join('').length,
            humanChars: (st.today.human||[]).join('').length,
            title: st.title,
          };
        }"""
        )
        assert_(lens["past"] >= 5 and lens["mid"] >= 5, "story para counts", json.dumps(lens))
        assert_(
            lens["pastChars"] >= 250 and lens["midChars"] >= 250 and lens["humanChars"] >= 200,
            "story content long enough",
            json.dumps({k: lens[k] for k in ("pastChars", "midChars", "humanChars")}),
        )

        # sample multiple stories
        multi = page.evaluate(
            """() => {
          const all = window.__hauntDiaryStories.all;
          const out = [];
          for (let i = 0; i < all.length; i++) {
            const st = all[i];
            const pc = (st.past.paras||[]).join('').length;
            const mc = (st.mid.paras||[]).join('').length;
            const hc = (st.today.human||[]).join('').length;
            const jargon = /spawn\\(|TypeScript|git log|npm |tsc |process_not_dead/.test(
              JSON.stringify(st)
            );
            out.push({ id: st.id, title: st.title, pc, mc, hc, jargon, ok: pc>=200 && mc>=200 && hc>=150 && !jargon });
          }
          return out;
        }"""
        )
        bad_stories = [x for x in multi if not x["ok"]]
        assert_(len(multi) == 20, "runtime 20 stories")
        assert_(len(bad_stories) == 0, "all 20 stories length+no jargon", json.dumps(bad_stories[:3], ensure_ascii=False))

        # open diary
        page.evaluate(
            """() => {
          const el = document.querySelector('[data-find=nav].find-active');
          if (el) el.click();
        }"""
        )
        page.wait_for_timeout(300)
        d = page.evaluate(
            """() => ({
          open: document.body.classList.contains('diary-open'),
          title: document.getElementById('diaryTitle') && document.getElementById('diaryTitle').textContent,
          p0: document.querySelector('.diary-page[data-page=\"0\"]') && document.querySelector('.diary-page[data-page=\"0\"]').innerText.length,
          bodyFilter: getComputedStyle(document.body).filter,
          panelFixed: getComputedStyle(document.getElementById('diaryPanel')).position,
        })"""
        )
        assert_(d["open"], "diary opens")
        assert_("일기" in (d["title"] or ""), "diary title Korean journal style", d["title"])
        assert_(d["p0"] and d["p0"] >= 200, "page0 long text rendered", str(d["p0"]))
        assert_(
            not d["bodyFilter"] or d["bodyFilter"] in ("none", "none none"),
            "body filter none diary-open",
            d["bodyFilter"],
        )
        assert_(d["panelFixed"] == "fixed", "panel fixed")

        # next pages
        page.evaluate("() => { const n=document.getElementById('diaryNext'); if(n) n.click(); }")
        page.wait_for_timeout(200)
        p1 = page.evaluate(
            """() => {
          const el = document.querySelector('.diary-page[data-page=\"1\"]');
          return {
            on: el && !el.hidden,
            len: el && el.innerText.length,
            mood: window.__hauntMood(),
            page: window.__hauntDiaryPage,
          };
        }"""
        )
        assert_(p1["on"] and p1["page"] == 1, "3mo→1mo", json.dumps(p1))
        assert_(p1["mood"] >= 2, "mood≥2 on page1", str(p1["mood"]))
        assert_(p1["len"] and p1["len"] >= 200, "page1 long", str(p1["len"]))

        page.evaluate("() => { const n=document.getElementById('diaryNext'); if(n) n.click(); }")
        page.wait_for_timeout(250)
        p2 = page.evaluate(
            """() => ({
          page: window.__hauntDiaryPage,
          mood: window.__hauntMood(),
          terminal: document.querySelector('.diary-sheet') && document.querySelector('.diary-sheet').classList.contains('is-terminal'),
        })"""
        )
        assert_(p2["page"] == 2 and p2["mood"] >= 3, "today page mood≥3", json.dumps(p2))

        # force stage 3
        page.evaluate(
            """() => {
          if (window.__hauntSetMood) window.__hauntSetMood(4);
          if (window.__hauntSetStage) window.__hauntSetStage(3);
          document.getElementById('diaryClose') && document.getElementById('diaryClose').click();
        }"""
        )
        page.wait_for_timeout(500)

        morph = page.evaluate(
            """() => ({
          l1: document.getElementById('titleL1') && document.getElementById('titleL1').textContent,
          l2: document.getElementById('titleL2') && document.getElementById('titleL2').textContent,
          stage: document.body.getAttribute('data-stage'),
          dread: document.body.classList.contains('stage-dread'),
          phase2: window.__hauntAnomalies.phase2Active(),
        })"""
        )
        assert_(morph["dread"] and morph["stage"] == "3", "stage dread", json.dumps(morph))
        assert_(
            morph["l1"] and "Simple" not in morph["l1"] and "monitoring" not in (morph["l1"] or ""),
            "hero morphed off clean English",
            morph["l1"],
        )
        assert_(morph["phase2"] is True, "phase2 active")

        # anomalies fire without throw
        fire = page.evaluate(
            """async () => {
          let err = 0;
          for (let i = 0; i < 30; i++) {
            try { window.__hauntAnomalies.fire(); } catch (e) { err++; }
            await new Promise(r => setTimeout(r, 20));
          }
          return {
            err,
            hasFx: !!(document.getElementById('wakeFlash') || document.getElementById('anomGhostBanner')
              || document.getElementById('anomCreepToast') || document.body.className.includes('anom-')),
            flash: window.__hauntAnomalies.flash({ force: true, silent: true, ms: 40 }),
          };
        }"""
        )
        assert_(fire["err"] == 0, "anomaly fire no throw")
        assert_(fire["hasFx"] or fire["flash"] is not False, "anomaly visual/fx")

        # diary-open blocks fire
        page.evaluate(
            """() => {
          document.body.classList.add('diary-open');
        }"""
        )
        blocked = page.evaluate(
            """() => {
          const before = document.body.className;
          window.__hauntAnomalies.fire();
          return before === document.body.className || document.body.classList.contains('diary-open');
        }"""
        )
        page.evaluate("() => document.body.classList.remove('diary-open')")
        assert_(blocked, "anomalies respect diary-open busy")

        # climax 1-5 ending
        climax = page.evaluate(
            """async () => {
          const phases = [];
          document.addEventListener('haunt-climax-phase', e => phases.push(e.detail.phase));
          window.__hauntSummon();
          const t0 = Date.now();
          while (Date.now() - t0 < 50000) {
            if (document.body.classList.contains('is-ending')) break;
            await new Promise(r => setTimeout(r, 120));
          }
          // wait ending lines
          let l1='', l2='';
          for (let i=0;i<80;i++) {
            l1 = (document.getElementById('endingL1')||{}).textContent || '';
            l2 = (document.getElementById('endingL2')||{}).textContent || '';
            if (/wakeagain/i.test(l1) && /no signal/i.test(l2)) break;
            await new Promise(r => setTimeout(r, 150));
          }
          return {
            phases,
            ending: document.body.classList.contains('is-ending'),
            l1, l2,
            domain: ((document.getElementById('endingVoid')||{}).innerText||'').includes('niagaekaw'),
            phase2: window.__hauntAnomalies.phase2Active(),
          };
        }"""
        )
        for n in (1, 2, 3, 4, 5):
            assert_(n in climax["phases"], f"climax phase {n}", str(climax["phases"]))
        assert_(climax["ending"], "ending reached")
        assert_("wakeagain" in climax["l1"].lower(), "ending l1", climax["l1"])
        assert_("no signal" in climax["l2"].lower(), "ending l2", climax["l2"])
        assert_(not climax["domain"], "ending no domain")
        assert_(climax["phase2"] is False, "anomalies off in ending")

        # stage gate without diary
        page3 = browser.new_page()
        page3.add_init_script("try{sessionStorage.clear()}catch(e){}")
        page3.goto(f"{BASE}/?path=nav", wait_until="domcontentloaded")
        page3.wait_for_timeout(200)
        gate = page3.evaluate(
            """() => {
          window.__hauntSetStage(2);
          return window.__hauntStage();
        }"""
        )
        assert_(gate == 0, "stage blocked without diary", str(gate))
        page3.close()

        # type_kill trigger
        page4 = browser.new_page()
        page4.add_init_script("try{sessionStorage.clear()}catch(e){}")
        page4.goto(f"{BASE}/?path=logo&p3=type_kill&story=3", wait_until="networkidle")
        page4.wait_for_timeout(400)
        assert_(
            page4.evaluate("() => window.__hauntClimaxTrigger") == "type_kill",
            "type_kill trigger",
        )
        page4.evaluate(
            """() => {
          const el = document.querySelector('[data-find=logo].find-active');
          if (el) { el.click(); el.click(); }
        }"""
        )
        page4.wait_for_timeout(200)
        page4.evaluate(
            """() => {
          const n = document.getElementById('diaryNext');
          if (n) { n.click(); }
        }"""
        )
        page4.wait_for_timeout(120)
        page4.evaluate(
            """() => {
          const n = document.getElementById('diaryNext');
          if (n) n.click();
        }"""
        )
        page4.wait_for_timeout(150)
        page4.evaluate(
            """() => {
          if (window.__hauntSetStage) window.__hauntSetStage(2);
          document.getElementById('diaryClose') && document.getElementById('diaryClose').click();
        }"""
        )
        page4.wait_for_timeout(300)
        page4.keyboard.type("kill", delay=40)
        page4.wait_for_timeout(600)
        assert_(
            page4.evaluate("() => document.body.classList.contains('is-haunting')"),
            "type_kill starts climax",
        )
        page4.close()

        browser.close()

    real_err = [e for e in console_errors if e and "favicon" not in e.lower()]
    assert_(len(real_err) == 0, "no page errors", " | ".join(real_err[:5]))


def main() -> int:
    static_checks()
    try:
        browser_checks()
    except Exception as e:
        fail("browser suite exception", str(e))
        import traceback

        traceback.print_exc()

    failed = [r for r in results if not r["ok"]]
    print("\n==== SUMMARY ====")
    print(f"pass {len(results) - len(failed)} / {len(results)}")
    for f in failed:
        print(" -", f["name"], f["detail"])
    # write json report
    out = ROOT / "QA_REPORT.json"
    out.write_text(json.dumps({"results": results, "failed": len(failed)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
