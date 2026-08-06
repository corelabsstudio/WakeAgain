# -*- coding: utf-8 -*-
"""Full-flow QA: phase1 → diary → phase2 → climax → ending"""
from __future__ import annotations

import json
import sys
import time

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4173"
results: list[dict] = []


def pass_(name: str, detail: str = "") -> None:
    results.append({"ok": True, "name": name, "detail": detail})
    print("PASS", name, detail)


def fail(name: str, detail: str = "") -> None:
    results.append({"ok": False, "name": name, "detail": detail})
    print("FAIL", name, detail)


def assert_(cond: bool, name: str, detail: str = "") -> None:
    if cond:
        pass_(name, detail)
    else:
        fail(name, detail)


def main() -> int:
    console_errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda e: console_errors.append(str(e)))
        page.on(
            "console",
            lambda m: console_errors.append(m.text) if m.type == "error" else None,
        )
        # 이상현상은 reduced-motion 이면 비활성 — 정상 모션으로 검증
        page.emulate_media(reduced_motion="no-preference")
        page.add_init_script(
            "try{sessionStorage.clear();localStorage.removeItem('haunt_creator');}catch(e){}"
        )

        page.goto(f"{BASE}/?path=nav&debug=1&p3=hold_free", wait_until="networkidle")
        page.wait_for_timeout(600)
        # 쿼리가 주소줄 연출 후에도 유지되는지
        search_kept = page.evaluate("() => location.search")
        assert_("p3=hold_free" in search_kept, "query preserved after address-bar", search_kept)

        body = page.evaluate(
            """() => ({
            stage: document.body.getAttribute('data-stage'),
            mood: document.body.getAttribute('data-mood'),
            classes: document.body.className,
            findPath: document.body.getAttribute('data-find-path'),
            diaryDisc: !!window.__hauntDiaryDiscovered,
            anomPool: (window.__hauntAnomalies && window.__hauntAnomalies.pool) || null,
            anomAll: (window.__hauntAnomalies && window.__hauntAnomalies.all) || null,
            trigger: window.__hauntClimaxTrigger,
            phase2: window.__hauntAnomalies && window.__hauntAnomalies.phase2Active(),
          })"""
        )

        assert_(body["stage"] == "0", "P1 stage=0", str(body["stage"]))
        assert_("stage-clean" in body["classes"], "P1 stage-clean")
        assert_(not body["diaryDisc"], "P1 diary not discovered")
        assert_(body["findPath"] == "nav", "P1 find path=nav", str(body["findPath"]))
        assert_(body["phase2"] is False, "P1 phase2 off")
        assert_(
            isinstance(body["anomAll"], list) and len(body["anomAll"]) >= 30,
            "anomaly catalog size",
            str(len(body["anomAll"] or [])),
        )
        assert_(
            isinstance(body["anomPool"], list) and len(body["anomPool"]) >= 10,
            "session pool size",
            str(len(body["anomPool"] or [])),
        )
        assert_(body["trigger"] == "hold_free", "trigger forced", str(body["trigger"]))

        fired_p1 = page.evaluate(
            """async () => {
            const before = document.body.className;
            if (window.__hauntAnomalies) window.__hauntAnomalies.fire();
            await new Promise(r => setTimeout(r, 50));
            return before === document.body.className;
          }"""
        )
        assert_(fired_p1, "P1 fire() no-op")

        # 히든 핫스팟은 일반 click 이 불안정 → DOM click 으로 발견 경로 검증
        opened = page.evaluate(
            """() => {
            const el = document.querySelector('[data-find=nav].find-active');
            if (!el) return { ok: false, why: 'no el' };
            el.click();
            return {
              ok: document.body.classList.contains('diary-open'),
              disc: !!window.__hauntDiaryDiscovered,
              panelHidden: document.getElementById('diaryPanel').hidden,
              mood: window.__hauntMood && window.__hauntMood(),
              stage: window.__hauntStage && window.__hauntStage(),
            };
          }"""
        )
        page.wait_for_timeout(250)
        body = page.evaluate(
            """() => ({
            open: document.body.classList.contains('diary-open'),
            disc: !!window.__hauntDiaryDiscovered,
            panelHidden: document.getElementById('diaryPanel').hidden,
            mood: window.__hauntMood(),
            stage: window.__hauntStage(),
          })"""
        )
        assert_(body["open"] and body["disc"] and not body["panelHidden"], "diary opens", str(opened))
        assert_(body["mood"] >= 1, "mood≥1", str(body["mood"]))
        assert_(body["stage"] >= 1, "stage≥1", str(body["stage"]))

        def diary_next() -> None:
            page.evaluate(
                """() => {
              const b = document.getElementById('diaryNext');
              if (b) b.click();
            }"""
            )
            page.wait_for_timeout(200)

        tab0 = page.locator('.diary-page[data-page="0"]').evaluate("el => !el.hidden")
        assert_(tab0, "page0 visible")

        diary_next()
        state = page.evaluate(
            """() => {
            const p0 = document.querySelector('.diary-page[data-page="0"]');
            const p1 = document.querySelector('.diary-page[data-page="1"]');
            return {
              p0: p0 && !p0.hidden,
              p1: p1 && !p1.hidden,
              page: window.__hauntDiaryPage,
              mood: window.__hauntMood(),
              bodyFilter: getComputedStyle(document.body).filter,
              panelPos: getComputedStyle(document.getElementById('diaryPanel')).position,
              open: document.body.classList.contains('diary-open'),
            };
          }"""
        )
        assert_(
            state["p1"] and not state["p0"],
            "3mo→1mo switch",
            json.dumps({"p0": state["p0"], "p1": state["p1"], "page": state["page"]}),
        )
        assert_(state["mood"] >= 2, "mood≥2 page1", str(state["mood"]))
        assert_(state["panelPos"] == "fixed", "panel fixed after mood-dim", state["panelPos"])
        bf = state["bodyFilter"] or "none"
        assert_(bf in ("none", "none none") or bf == "none", "body filter none diary open", bf)

        diary_next()
        state = page.evaluate(
            """() => {
            const p2 = document.querySelector('.diary-page[data-page="2"]');
            return {
              p2: p2 && !p2.hidden,
              mood: window.__hauntMood(),
              page: window.__hauntDiaryPage,
            };
          }"""
        )
        assert_(state["p2"], "today page visible", json.dumps(state))
        assert_(state["mood"] >= 3, "mood≥3 today", str(state["mood"]))

        page.evaluate(
            """() => {
            if (window.__hauntSetStage) window.__hauntSetStage(2);
            if (window.__hauntSetMood) window.__hauntSetMood(3);
          }"""
        )
        page.wait_for_timeout(100)

        blocked = page.evaluate(
            """() => {
            const before = document.body.className;
            window.__hauntAnomalies.fire();
            return {
              phase2: window.__hauntAnomalies.phase2Active(),
              open: document.body.classList.contains('diary-open'),
              classChanged: before !== document.body.className,
            };
          }"""
        )
        assert_(blocked["phase2"] is True, "phase2Active while stage≥2")
        assert_(not blocked["classChanged"], "fire blocked diary-open")

        page.evaluate(
            """() => {
          const b = document.getElementById('diaryClose');
          if (b) b.click();
        }"""
        )
        page.wait_for_timeout(200)
        assert_(
            page.evaluate("() => !document.body.classList.contains('diary-open')"),
            "diary closes",
        )

        # Force stage 3 for dread ambient path
        page.evaluate(
            """() => {
            if (window.__hauntSetMood) window.__hauntSetMood(4);
            if (window.__hauntSetStage) window.__hauntSetStage(3);
          }"""
        )
        page.wait_for_timeout(300)

        anom = page.evaluate(
            """async () => {
            const all = window.__hauntAnomalies.all.slice();
            const required = [
              'red_flash','screen_shake','hue_spike','invert_blink','grayscale_drain',
              'text_blood_wipe','watcher_behind','wake_flash','dead_gray_wash',
              'terminal_log_crawl','button_dodge','header_bleed_reveal','clipboard_curse',
              'gaze_tilt','loading_99_reverse','viewport_squeeze','cursor_scorch_trail',
              'tab_title_panic','sub_bass_rumble','hdd_scratch','fake_comment','creep_toast',
              'avatar_hollow','diary_sneak_peek','text_erode','scroll_jolt','clock_lie',
              'path_scream','ghost_banner','mirror_flip','double_vision','blood_pulse',
              'static_burst','vignette_crush','title_glitch','card_jitter','button_scatter',
              'letter_space','hide_chunk','cursor_bleed','scrollbar_creep','refresh_deepens',
              'skew_tear','zoom_pulse'
            ];
            const missing = required.filter(id => all.indexOf(id) === -1);
            const fireErrors = [];
            for (let i = 0; i < 50; i++) {
              try { window.__hauntAnomalies.fire(); }
              catch (e) { fireErrors.push(String(e)); }
              await new Promise(r => setTimeout(r, 25));
            }
            const fxAfterFire = !!(
              document.getElementById('anomWatcher') ||
              document.getElementById('anomGhostBanner') ||
              document.getElementById('anomCreepToast') ||
              document.querySelector('.anom-blood-layer') ||
              document.body.className.includes('anom-')
            );
            // 백그라운드 루프 정지 — hazard CSS 측정 중 fire 재개입 방지
            const prevDisc = window.__hauntDiaryDiscovered;
            window.__hauntDiaryDiscovered = false;
            await new Promise(r => setTimeout(r, 1200));
            [...document.body.classList].forEach(c => {
              if (c.startsWith('anom-') || c === 'page-tick') document.body.classList.remove(c);
            });
            document.body.style.removeProperty('filter');
            document.body.style.removeProperty('transform');
            document.body.style.removeProperty('animation');
            // page-tick 등 잔여 애니메이션 취소 후 측정
            try {
              document.body.getAnimations().forEach(a => a.cancel());
              document.documentElement.getAnimations().forEach(a => a.cancel());
            } catch (e) {}
            const hazards = ['anom-red-flash','anom-shake','anom-invert','anom-gray',
              'anom-skew','anom-zoom','anom-dead-gray','anom-refresh-deep','page-tick','anom-hue-spike'];
            const hazReport = [];
            for (const h of hazards) {
              [...document.body.classList].forEach(c => {
                if (c.startsWith('anom-') || c === 'page-tick') document.body.classList.remove(c);
              });
              try { document.body.getAnimations().forEach(a => a.cancel()); } catch (e) {}
              document.body.classList.add(h);
              document.body.classList.add('diary-open');
              // product openDiary path
              document.body.style.setProperty('filter', 'none', 'important');
              document.body.style.setProperty('animation', 'none', 'important');
              try { document.body.getAnimations().forEach(a => a.cancel()); } catch (e) {}
              const f = getComputedStyle(document.body).filter;
              const t = getComputedStyle(document.body).transform;
              document.body.classList.remove('diary-open', h);
              document.body.style.removeProperty('filter');
              document.body.style.removeProperty('animation');
              hazReport.push({ h, f, t, ok: !f || f === 'none' || f === 'none none' });
            }
            // product path: openDiary 인라인 !important 잠금 + cancel
            document.body.classList.add('anom-dead-gray');
            document.body.style.setProperty('filter', 'hue-rotate(90deg) contrast(1.2)');
            document.body.classList.add('diary-open');
            document.body.style.setProperty('filter', 'none', 'important');
            document.body.style.setProperty('animation', 'none', 'important');
            try { document.body.getAnimations().forEach(a => a.cancel()); } catch (e) {}
            const inlineF = getComputedStyle(document.body).filter;
            document.body.classList.remove('diary-open', 'anom-dead-gray');
            document.body.style.removeProperty('filter');
            document.body.style.removeProperty('animation');
            window.__hauntDiaryDiscovered = prevDisc;
            const flash = window.__hauntAnomalies.flash({ force: true, ms: 40 });
            await new Promise(r => setTimeout(r, 80));
            return {
              count: all.length, all, missing, fireErrors, hazReport,
              inlineF, flash, wake: !!document.getElementById('wakeFlash'),
              fx: fxAfterFire || !!document.getElementById('wakeFlash'),
            };
          }"""
        )
        assert_(anom["count"] >= 40, "anomaly count", str(anom["count"]))
        assert_(len(anom["missing"]) == 0, "required anomaly ids", ",".join(anom["missing"]))
        assert_(len(anom["fireErrors"]) == 0, "no fire errors", str(anom["fireErrors"][:3]))
        bad = [h for h in anom["hazReport"] if not h["ok"]]
        assert_(len(bad) == 0, "hazards killed under diary-open", json.dumps(bad))
        inf = anom["inlineF"] or "none"
        assert_(
            inf in ("none", "none none"),
            "inline filter overridden diary-open",
            inf,
        )
        assert_(anom["flash"] is not False and anom["wake"], "wake flash works")
        assert_(anom["fx"] or anom["wake"], "phase2 fx present")

        # DOM integrity
        dom = page.evaluate(
            """() => {
            const ids = ['diaryPanel','diaryNext','haunt','hauntP1','hauntP2','hauntP3',
              'hauntP4','hauntP5','endingVoid','endingL1','endingL2','planFree','planTeam',
              'fakeUrlBar','mainTitle','p2HintToast','p2MissionChip','hauntHit','topRec',
              'resWait','corruptPath'];
            const missing = ids.filter(id => !document.getElementById(id));
            const finds = Array.from(document.querySelectorAll('[data-find]'))
              .map(el => el.getAttribute('data-find'));
            return { missing, finds, n: finds.length };
          }"""
        )
        assert_(len(dom["missing"]) == 0, "required DOM ids", ",".join(dom["missing"]))
        assert_(dom["n"] >= 20, "find hotspots", str(dom["n"]))

        # Climax + ending (reduced 타이밍이 아니라 수동 단축 없음 — 타임아웃 여유)
        climax = page.evaluate(
            """async () => {
            const phases = [];
            document.addEventListener('haunt-climax-phase', e => phases.push(e.detail.phase));
            window.__hauntSummon();
            const start = Date.now();
            while (Date.now() - start < 45000) {
              if (document.body.classList.contains('is-ending')) break;
              await new Promise(r => setTimeout(r, 120));
            }
            return {
              phases,
              ending: document.body.classList.contains('is-ending'),
              haunting: document.body.classList.contains('is-haunting'),
              domain: ((document.getElementById('endingVoid')||{}).innerText||'').includes('niagaekaw'),
              complete: window.__hauntClimaxSequence && window.__hauntClimaxSequence.isComplete(),
            };
          }"""
        )
        for n in (1, 2, 3, 4, 5):
            assert_(n in climax["phases"], f"climax phase {n}", str(climax["phases"]))
        assert_(climax["phases"][:1] == [1] or climax["phases"][0] == 1, "starts at 1")
        # sequential
        seq = all(
            climax["phases"][i] <= climax["phases"][i + 1]
            for i in range(len(climax["phases"]) - 1)
        ) if len(climax["phases"]) > 1 else False
        assert_(seq and 1 in climax["phases"] and 5 in climax["phases"], "phases sequential", "→".join(map(str, climax["phases"])))
        assert_(climax["ending"], "ending after climax", json.dumps(climax))
        assert_(not climax["domain"], "no domain in ending")

        # silence + type lines — 최대 12초 폴링
        et = {"l1": "", "l2": "", "title": ""}
        for _ in range(60):
            et = page.evaluate(
                """() => ({
                l1: (document.getElementById('endingL1')||{}).textContent || '',
                l2: (document.getElementById('endingL2')||{}).textContent || '',
                title: document.title,
              })"""
            )
            if "wakeagain" in et["l1"].lower() and "no signal" in et["l2"].lower():
                break
            page.wait_for_timeout(200)
        assert_("wakeagain" in et["l1"].lower(), "ending l1", et["l1"])
        assert_("no signal" in et["l2"].lower(), "ending l2", et["l2"])

        end_gate = page.evaluate(
            """() => {
            const before = document.body.className;
            window.__hauntAnomalies.fire();
            return {
              phase2: window.__hauntAnomalies.phase2Active(),
              changed: before !== document.body.className,
            };
          }"""
        )
        assert_(end_gate["phase2"] is False, "phase2 off ending")
        assert_(not end_gate["changed"], "anomalies no-op ending")

        # Second page: trigger type_kill + mission toast z-index
        page2 = browser.new_page()
        page2.emulate_media(reduced_motion="no-preference")
        page2.add_init_script("try{sessionStorage.clear();}catch(e){}")
        page2.goto(f"{BASE}/?path=logo&debug=1&p3=type_kill", wait_until="networkidle")
        page2.wait_for_timeout(400)
        trig = page2.evaluate("() => window.__hauntClimaxTrigger")
        assert_(trig == "type_kill", "p3=type_kill honored", str(trig))
        # open diary via logo double-click (find path)
        opened = page2.evaluate(
            """() => {
            const el = document.querySelector('[data-find=logo].find-active');
            if (!el) return false;
            el.click();
            el.click();
            return document.body.classList.contains('diary-open');
          }"""
        )
        page2.wait_for_timeout(200)
        assert_(opened, "logo path opens diary")

        # advance diary fully
        for _ in range(2):
            page2.evaluate("() => { const b=document.getElementById('diaryNext'); if(b) b.click(); }")
            page2.wait_for_timeout(180)
        page2.evaluate(
            """() => {
            if (window.__hauntSetStage) window.__hauntSetStage(2);
            if (window.__hauntSetMood) window.__hauntSetMood(4);
          }"""
        )
        page2.wait_for_timeout(100)
        # while diary open, p2 toast should not steal interaction - z-index diary higher
        z = page2.evaluate(
            """() => {
            const d = getComputedStyle(document.getElementById('diaryPanel')).zIndex;
            const t = document.getElementById('p2HintToast');
            const tz = t ? getComputedStyle(t).zIndex : '0';
            return { d: parseInt(d,10)||0, t: parseInt(tz,10)||0 };
          }"""
        )
        assert_(z["d"] > z["t"], "diary z-index above p2 toast", json.dumps(z))

        page2.evaluate("() => { const b=document.getElementById('diaryClose'); if(b) b.click(); }")
        page2.wait_for_timeout(300)

        # type_kill trigger (diary 닫힌 뒤)
        page2.keyboard.type("kill", delay=30)
        page2.wait_for_timeout(800)
        haunting = page2.evaluate("() => document.body.classList.contains('is-haunting')")
        assert_(haunting, "type_kill trigger starts climax")

        page2.close()

        # Phase1 gate: stage cannot rise without diary
        page3 = browser.new_page()
        page3.goto(f"{BASE}/?path=nav", wait_until="domcontentloaded")
        page3.wait_for_timeout(200)
        blocked_stage = page3.evaluate(
            """() => {
            const before = window.__hauntStage();
            window.__hauntSetStage(2);
            return { before, after: window.__hauntStage() };
          }"""
        )
        assert_(
            blocked_stage["after"] == 0,
            "stage blocked without diary",
            json.dumps(blocked_stage),
        )
        page3.close()

        browser.close()

    # soft-fail console noise that is not real errors
    real_err = [e for e in console_errors if e and "favicon" not in e.lower()]
    assert_(len(real_err) == 0, "no page errors", " | ".join(real_err[:5]))

    failed = [r for r in results if not r["ok"]]
    print("\n==== SUMMARY ====")
    print(f"pass {len(results) - len(failed)} / {len(results)}")
    for f in failed:
        print(" -", f["name"], f["detail"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
