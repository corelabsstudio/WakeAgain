/**
 * Full-flow QA: phase1 → diary → phase2 anomalies → climax 1–5 → ending
 * Run: node qa-full.mjs
 * Server: http://127.0.0.1:4173 (python -m http.server 4173)
 */
import { chromium } from "playwright";

const BASE = process.env.HAUNT_URL || "http://127.0.0.1:4173";
const results = [];
function pass(name, detail) {
  results.push({ ok: true, name, detail: detail || "" });
  console.log("PASS", name, detail || "");
}
function fail(name, detail) {
  results.push({ ok: false, name, detail: detail || "" });
  console.log("FAIL", name, detail || "");
}
function assert(cond, name, detail) {
  if (cond) pass(name, detail);
  else fail(name, detail);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on("pageerror", (e) => consoleErrors.push(String(e)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  // Prefer reduced motion for faster climax timers
  await page.emulateMedia({ reducedMotion: "reduce" });

  // --- Phase 1: clean load ---
  await page.goto(`${BASE}/?path=nav&debug=1&p3=hold_free`, {
    waitUntil: "networkidle",
  });
  await page.waitForTimeout(400);

  let body = await page.evaluate(() => ({
    stage: document.body.getAttribute("data-stage"),
    mood: document.body.getAttribute("data-mood"),
    classes: document.body.className,
    findPath: document.body.getAttribute("data-find-path"),
    diaryDisc: !!window.__hauntDiaryDiscovered,
    anomPool: (window.__hauntAnomalies && window.__hauntAnomalies.pool) || null,
    anomAll: (window.__hauntAnomalies && window.__hauntAnomalies.all) || null,
    trigger: window.__hauntClimaxTrigger,
    phase2: window.__hauntAnomalies && window.__hauntAnomalies.phase2Active(),
  }));

  assert(body.stage === "0", "P1 stage=0 clean", `stage=${body.stage}`);
  assert(body.classes.includes("stage-clean"), "P1 stage-clean class");
  assert(!body.diaryDisc, "P1 diary not discovered");
  assert(body.findPath === "nav", "P1 forced find path=nav", body.findPath);
  assert(body.phase2 === false, "P1 anomalies phase2 off");
  assert(Array.isArray(body.anomAll) && body.anomAll.length >= 30, "anomaly catalog size", String(body.anomAll && body.anomAll.length));
  assert(Array.isArray(body.anomPool) && body.anomPool.length >= 10, "session pool size", String(body.anomPool && body.anomPool.length));
  assert(body.trigger === "hold_free", "climax trigger forced", body.trigger);

  // Anomalies should NOT fire in phase 1
  const firedP1 = await page.evaluate(async () => {
    const before = document.body.className;
    if (window.__hauntAnomalies) window.__hauntAnomalies.fire();
    await new Promise((r) => setTimeout(r, 50));
    return { before, after: document.body.className, same: before === document.body.className };
  });
  assert(firedP1.same, "P1 fire() is no-op (phase2 gate)");

  // --- Find diary (nav path) ---
  const nav = page.locator("#diaryHint.find-active, [data-find=nav].find-active");
  await nav.click({ force: true });
  await page.waitForTimeout(200);

  body = await page.evaluate(() => ({
    open: document.body.classList.contains("diary-open"),
    disc: !!window.__hauntDiaryDiscovered,
    panelHidden: document.getElementById("diaryPanel").hidden,
    page: window.__hauntDiaryPage,
    mood: window.__hauntMood(),
    stage: window.__hauntStage(),
  }));
  assert(body.open && body.disc && !body.panelHidden, "diary opens via find path");
  assert(body.mood >= 1, "mood≥1 after open page0", `mood=${body.mood}`);
  assert(body.stage >= 1, "stage≥1 after diary", `stage=${body.stage}`);

  // --- Diary page walk 0→1→2 ---
  async function diaryNext() {
    await page.locator("#diaryNext").click({ force: true });
    await page.waitForTimeout(150);
  }

  // page 0 content visible
  let tab0 = await page.locator('.diary-page[data-page="0"]').evaluate((el) => !el.hidden);
  assert(tab0, "diary page 0 visible");

  await diaryNext(); // unlock → page 1
  let state = await page.evaluate(() => {
    const p0 = document.querySelector('.diary-page[data-page="0"]');
    const p1 = document.querySelector('.diary-page[data-page="1"]');
    const next = document.getElementById("diaryNext");
    return {
      p0: p0 && !p0.hidden,
      p1: p1 && !p1.hidden,
      page: window.__hauntDiaryPage,
      mood: window.__hauntMood(),
      nextText: next && next.textContent,
      bodyFilter: getComputedStyle(document.body).filter,
      panelPos: getComputedStyle(document.getElementById("diaryPanel")).position,
      panelZ: getComputedStyle(document.getElementById("diaryPanel")).zIndex,
      open: document.body.classList.contains("diary-open"),
    };
  });
  assert(state.p1 && !state.p0, "3mo→1mo page switch", JSON.stringify({ p0: state.p0, p1: state.p1, page: state.page }));
  assert(state.mood >= 2, "mood≥2 on page1", `mood=${state.mood}`);
  assert(state.panelPos === "fixed", "diary panel still fixed after mood-dim", state.panelPos);
  assert(
    !state.bodyFilter || state.bodyFilter === "none",
    "body filter none while diary open",
    state.bodyFilter
  );

  await diaryNext(); // unlock → page 2 today
  state = await page.evaluate(() => {
    const p2 = document.querySelector('.diary-page[data-page="2"]');
    return {
      p2: p2 && !p2.hidden,
      page: window.__hauntDiaryPage,
      mood: window.__hauntMood(),
      typing: document.body.classList.contains("diary-typing") || document.body.classList.contains("diary-finale"),
    };
  });
  assert(state.p2, "today page visible", JSON.stringify(state));
  assert(state.mood >= 3, "mood≥3 on today page", `mood=${state.mood}`);

  // Force stage 2 quickly (corrupt timer may be mid-flight)
  await page.evaluate(() => {
    if (window.__hauntSetStage) window.__hauntSetStage(2);
    if (window.__hauntSetMood) window.__hauntSetMood(3);
  });
  await page.waitForTimeout(100);

  // Anomalies still blocked while diary open
  const blockedOpen = await page.evaluate(() => {
    const before = document.body.className;
    window.__hauntAnomalies.fire();
    return {
      phase2: window.__hauntAnomalies.phase2Active(),
      open: document.body.classList.contains("diary-open"),
      classChanged: before !== document.body.className,
    };
  });
  assert(blockedOpen.phase2 === true, "phase2Active true with stage≥2+diary");
  assert(!blockedOpen.classChanged, "fire() blocked while diary-open");

  // Close diary
  await page.locator("#diaryClose").click({ force: true });
  await page.waitForTimeout(200);
  assert(
    await page.evaluate(() => !document.body.classList.contains("diary-open")),
    "diary closes"
  );

  // --- Fire every anomaly id once ---
  const anomReport = await page.evaluate(async () => {
    const all = window.__hauntAnomalies.all.slice();
    const report = [];
    const hazards = [
      "anom-red-flash",
      "anom-shake",
      "anom-invert",
      "anom-gray",
      "anom-skew",
      "anom-zoom",
      "anom-dead-gray",
      "anom-refresh-deep",
      "page-tick",
    ];

    // Temporarily expose run by id via pool + ALL isn't exported with run
    // Use fire() many times + direct class toggles for layout safety
    for (let i = 0; i < 40; i++) {
      try {
        window.__hauntAnomalies.fire();
      } catch (e) {
        report.push({ id: "fire#" + i, err: String(e) });
      }
      await new Promise((r) => setTimeout(r, 30));
    }

    // Simulate each hazard class with diary closed then open
    for (const h of hazards) {
      document.body.classList.add(h);
      const f1 = getComputedStyle(document.body).filter;
      const t1 = getComputedStyle(document.body).transform;
      document.body.classList.add("diary-open");
      const f2 = getComputedStyle(document.body).filter;
      const t2 = getComputedStyle(document.body).transform;
      document.body.classList.remove("diary-open", h);
      report.push({
        hazard: h,
        filterWith: f1,
        filterDiary: f2,
        transformDiary: t2,
        ok:
          !f2 || f2 === "none" || f2 === "none none",
      });
    }

    // hue_spike style filter residual
    document.body.style.filter = "hue-rotate(90deg)";
    document.body.classList.add("diary-open");
    const inlineVsCss = getComputedStyle(document.body).filter;
    document.body.classList.remove("diary-open");
    document.body.style.filter = "";

    return {
      allCount: all.length,
      all,
      hazards: report.filter((r) => r.hazard),
      fireErrors: report.filter((r) => r.err),
      inlineFilterWhileDiary: inlineVsCss,
    };
  });

  assert(anomReport.allCount >= 35, "anomaly catalog complete", String(anomReport.allCount));
  assert(anomReport.fireErrors.length === 0, "no fire() throw", JSON.stringify(anomReport.fireErrors));
  const badHaz = anomReport.hazards.filter((h) => !h.ok);
  assert(badHaz.length === 0, "body filter killed under diary-open", JSON.stringify(badHaz));
  assert(
    !anomReport.inlineFilterWhileDiary ||
      anomReport.inlineFilterWhileDiary === "none" ||
      anomReport.inlineFilterWhileDiary === "none none",
    "inline hue filter overridden by diary-open",
    anomReport.inlineFilterWhileDiary
  );

  // Fire each anomaly by monkey-patching through internal? Re-run page with debug listing
  // Direct invoke: recreate by re-loading fire and checking elements created
  const eachAnom = await page.evaluate(async () => {
    // Pull ALL runs via re-exec isn't available. Use session pool fire + known side effects.
    const ids = window.__hauntAnomalies.all;
    const missing = [];
    // Ensure expected ids present
    const required = [
      "red_flash",
      "screen_shake",
      "hue_spike",
      "invert_blink",
      "grayscale_drain",
      "text_blood_wipe",
      "watcher_behind",
      "wake_flash",
      "dead_gray_wash",
      "terminal_log_crawl",
      "button_dodge",
      "header_bleed_reveal",
      "clipboard_curse",
      "gaze_tilt",
      "loading_99_reverse",
      "viewport_squeeze",
      "cursor_scorch_trail",
      "tab_title_panic",
      "sub_bass_rumble",
      "hdd_scratch",
      "fake_comment",
      "creep_toast",
      "avatar_hollow",
      "diary_sneak_peek",
      "text_erode",
      "scroll_jolt",
      "clock_lie",
      "path_scream",
      "ghost_banner",
      "mirror_flip",
      "double_vision",
      "blood_pulse",
      "static_burst",
      "vignette_crush",
      "title_glitch",
      "card_jitter",
      "button_scatter",
      "letter_space",
      "hide_chunk",
      "cursor_bleed",
      "scrollbar_creep",
      "refresh_deepens",
    ];
    for (const id of required) {
      if (ids.indexOf(id) === -1) missing.push(id);
    }
    return { ids, missing, count: ids.length };
  });
  assert(eachAnom.missing.length === 0, "all expected anomaly ids registered", eachAnom.missing.join(","));

  // Manual invoke of key visual anomalies by dispatching classes + watcher
  const visualOk = await page.evaluate(async () => {
    const out = {};
    // watcher
    document.body.classList.add("phase-2-active");
    // create watcher via fire until present or timeout
    for (let i = 0; i < 80; i++) {
      window.__hauntAnomalies.fire();
      if (document.getElementById("anomWatcher") || document.querySelector(".anom-blood-layer") || document.getElementById("anomGhostBanner")) break;
      await new Promise((r) => setTimeout(r, 20));
    }
    out.hasWatcherOrFx =
      !!document.getElementById("anomWatcher") ||
      !!document.querySelector(".anom-blood-layer") ||
      !!document.getElementById("anomGhostBanner") ||
      !!document.getElementById("anomCreepToast") ||
      !!document.getElementById("wakeFlash") ||
      document.body.className.includes("anom-");
    // flash API
    out.flash = window.__hauntAnomalies.flash({ force: true, ms: 40 });
    await new Promise((r) => setTimeout(r, 60));
    out.wakeEl = !!document.getElementById("wakeFlash");
    return out;
  });
  assert(visualOk.hasWatcherOrFx || visualOk.wakeEl, "phase2 visual anomaly can produce DOM", JSON.stringify(visualOk));
  assert(visualOk.flash !== false && visualOk.wakeEl, "wake flash API works");

  // --- Climax sequence 1–5 ---
  const climax = await page.evaluate(async () => {
    const phases = [];
    document.addEventListener("haunt-climax-phase", (e) => {
      phases.push(e.detail.phase);
    });
    window.__hauntSummon();
    // reduced motion: shorter phases — wait up to 25s
    const start = Date.now();
    while (Date.now() - start < 25000) {
      const ending = document.body.classList.contains("is-ending");
      const running = window.__hauntClimaxSequence && window.__hauntClimaxSequence.isRunning();
      if (ending) break;
      if (!running && phases.length >= 5) {
        await new Promise((r) => setTimeout(r, 500));
        if (document.body.classList.contains("is-ending")) break;
      }
      await new Promise((r) => setTimeout(r, 100));
    }
    return {
      phases,
      ending: document.body.classList.contains("is-ending"),
      haunting: document.body.classList.contains("is-haunting"),
      title: document.title,
      l1: (document.getElementById("endingL1") || {}).textContent,
      l2: (document.getElementById("endingL2") || {}).textContent,
      domainInEnding: ((document.getElementById("endingVoid") || {}).innerText || "").includes("niagaekaw"),
      complete: window.__hauntClimaxSequence && window.__hauntClimaxSequence.isComplete(),
    };
  });

  assert(climax.phases.includes(1), "climax phase 1", JSON.stringify(climax.phases));
  assert(climax.phases.includes(2), "climax phase 2");
  assert(climax.phases.includes(3), "climax phase 3");
  assert(climax.phases.includes(4), "climax phase 4");
  assert(climax.phases.includes(5), "climax phase 5");
  // phases should be sequential 1..5
  const seqOk =
    climax.phases.filter((p, i, a) => i === 0 || p >= a[i - 1]).length === climax.phases.length &&
    climax.phases[0] === 1;
  assert(seqOk, "climax phases non-decreasing from 1", climax.phases.join("→"));
  assert(climax.ending, "ending after climax", JSON.stringify({ ending: climax.ending, haunting: climax.haunting }));
  assert(!climax.domainInEnding, "ending has no domain spam");

  // Wait for ending text
  await page.waitForTimeout(3500);
  const endingText = await page.evaluate(() => ({
    l1: (document.getElementById("endingL1") || {}).textContent || "",
    l2: (document.getElementById("endingL2") || {}).textContent || "",
    title: document.title,
  }));
  assert(/wakeagain/i.test(endingText.l1), "ending line1 wakeagain", endingText.l1);
  assert(/no signal/i.test(endingText.l2), "ending line2 no signal", endingText.l2);

  // Anomalies off in ending
  const endGate = await page.evaluate(() => {
    const before = document.body.className;
    window.__hauntAnomalies.fire();
    return {
      phase2: window.__hauntAnomalies.phase2Active(),
      changed: before !== document.body.className,
    };
  });
  assert(endGate.phase2 === false, "phase2 off in ending");
  assert(!endGate.changed, "anomalies no-op in ending");

  // --- Script/DOM integrity ---
  const dom = await page.evaluate(() => {
    const ids = [
      "diaryPanel",
      "diaryNext",
      "haunt",
      "hauntP1",
      "hauntP2",
      "hauntP3",
      "hauntP4",
      "hauntP5",
      "endingVoid",
      "endingL1",
      "endingL2",
      "planFree",
      "planTeam",
      "fakeUrlBar",
      "mainTitle",
      "p2HintToast",
      "p2MissionChip",
      "hauntHit",
    ];
    const missing = ids.filter((id) => !document.getElementById(id));
    const findPaths = document.querySelectorAll("[data-find]");
    const finds = Array.from(findPaths).map((el) => el.getAttribute("data-find"));
    return { missing, finds, findCount: finds.length };
  });
  assert(dom.missing.length === 0, "required DOM ids present", dom.missing.join(","));
  assert(dom.findCount >= 20, "find hotspots ≥20", String(dom.findCount));

  // Trigger DOM wiring for all climax triggers (static check via re-parse)
  const triggers = await page.evaluate(() => {
    // from body attribute
    return {
      active: document.body.getAttribute("data-p3-trigger"),
      hasSummon: typeof window.__hauntSummon === "function",
      hasSeq: !!(window.__hauntClimaxSequence && window.__hauntClimaxSequence.start),
      hasEnding: typeof window.__hauntStartEnding === "function",
    };
  });
  assert(triggers.hasSummon && triggers.hasSeq && triggers.hasEnding, "public APIs wired");

  assert(consoleErrors.length === 0, "no page console errors", consoleErrors.slice(0, 5).join(" | "));

  await browser.close();

  const failed = results.filter((r) => !r.ok);
  console.log("\n==== SUMMARY ====");
  console.log("pass", results.length - failed.length, "/", results.length);
  if (failed.length) {
    failed.forEach((f) => console.log(" -", f.name, f.detail));
    process.exit(1);
  }
  process.exit(0);
}

main().catch((e) => {
  console.error(e);
  process.exit(2);
});
