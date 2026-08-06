/**
 * 입장: 깔끔한 SaaS 랜딩 (stage 0)
 * → 일기 찾기 전: 절대 음산 없음
 * → 분위기(mood)를 아주 천천히 단계 상승
 *
 * mood 0 clean
 * mood 1  일기 3달 전 — 살짝만 어두움 (stage 1)
 * mood 2  일기 1달 전 — 조금 더 딤 (아직 풀 공포 배경 X, stage 1)
 * mood 3  일기 오늘 진입 — 서서히 corrupt (stage 2) + 쿵쿵
 * mood 4  오늘 페이지 머문 뒤 — dread (stage 3) + 쿵쿵 강하게
 *
 * stages: 0 clean → 1 uneasy → 2 corrupt → 3 dread
 */
(function () {
  "use strict";

  var body = document.body;
  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var stage = 0;
  var mood = 0;
  var morphQueue = [];
  var morphIndex = 0;
  var morphLoopStarted = false;
  var dreadTimer = null;
  var corruptTimer = null;

  // 2페이즈: 시간 경과에 따라 화면이 점점 괴기스러워짐 (0~5)
  var p2Decay = 0;
  var p2Elapsed = 0;
  var p2LastTick = 0;
  var p2TickTimer = null;

  var themeMeta = document.querySelector('meta[name="theme-color"]');

  function diaryDiscovered() {
    return !!window.__hauntDiaryDiscovered;
  }

  function emitMood() {
    body.setAttribute("data-mood", String(mood));
    document.dispatchEvent(
      new CustomEvent("haunt-mood", { detail: { mood: mood, stage: stage } })
    );
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[corruption] mood", mood, "stage", stage);
    }
  }

  function setStage(n) {
    n = Math.max(0, Math.min(3, n | 0));
    if (n > 0 && !diaryDiscovered()) {
      if (window.console && /[?&]debug=1/.test(location.search || "")) {
        console.log("[corruption] blocked stage", n, "(diary not found)");
      }
      return;
    }
    if (n <= stage) return;
    stage = n;
    body.classList.remove("stage-clean", "stage-uneasy", "stage-corrupt", "stage-dread");
    var name = ["stage-clean", "stage-uneasy", "stage-corrupt", "stage-dread"][n] || "stage-dread";
    body.classList.add(name);
    body.setAttribute("data-stage", String(n));
    if (themeMeta) {
      themeMeta.setAttribute(
        "content",
        n === 0 ? "#FAF4F0" : n === 1 ? "#e4d8d0" : n === 2 ? "#1a1230" : "#0a0614"
      );
    }
    document.dispatchEvent(
      new CustomEvent("haunt-stage", { detail: { stage: n, mood: mood } })
    );
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[corruption] stage", n, name);
    }

    if (n >= 1) ensureMorphLoop();
    if (n >= 2) {
      var t1 = document.getElementById("terminalLine");
      if (t1) t1.hidden = false;
      // 부패 구간: Pro 버튼 활성화 (트리거·의식용)
      var pro = document.getElementById("planPro");
      if (pro) {
        pro.disabled = false;
        pro.classList.remove("is-disabled");
        pro.title = "";
      }
      // 핵심: 다크만 씌운 라이트 카피 금지 — stage2 진입 즉시 본문 전면 부패
      remorphAll("horror", true);
      burstCorrupt(reduced ? 12 : 8, reduced ? 40 : 120);
      startP2DecayClock();
    }
    if (n >= 3) {
      revealHorrorChrome();
      remorphAll("horror", true);
      burstCorrupt(reduced ? 24 : 16, reduced ? 30 : 90);
      // dread 진입 시 최소 decay 2 보장 (이미 더 높으면 유지)
      if (p2Decay < 2) setP2Decay(2);
    }
  }

  /**
   * 2페이즈 경과 시간 → data-p2-decay 0~5
   * 일기 연 동안은 시간 정지 (읽기 방해 X)
   *  ~12s:1  28s:2  50s:3  80s:4  120s:5
   */
  function startP2DecayClock() {
    if (!p2LastTick) p2LastTick = Date.now();
    body.setAttribute("data-p2-decay", String(p2Decay));
    body.classList.add("p2-d" + p2Decay);
    body.classList.add("phase-2-active");
    if (p2TickTimer) return;
    p2TickTimer = setInterval(tickP2Decay, reduced ? 900 : 1400);
  }

  function tickP2Decay() {
    if (stage < 2) return;
    if (body.classList.contains("is-haunting") || body.classList.contains("is-ending")) {
      return;
    }
    var now = Date.now();
    // 일기 열림 / 탭 숨김: 경과 일시정지
    if (
      body.classList.contains("diary-open") ||
      document.hidden
    ) {
      p2LastTick = now;
      return;
    }
    if (!p2LastTick) p2LastTick = now;
    p2Elapsed += now - p2LastTick;
    p2LastTick = now;

    var next = 0;
    if (p2Elapsed >= (reduced ? 45000 : 120000)) next = 5;
    else if (p2Elapsed >= (reduced ? 32000 : 80000)) next = 4;
    else if (p2Elapsed >= (reduced ? 22000 : 50000)) next = 3;
    else if (p2Elapsed >= (reduced ? 12000 : 28000)) next = 2;
    else if (p2Elapsed >= (reduced ? 5000 : 12000)) next = 1;

    if (next > p2Decay) setP2Decay(next);
  }

  function setP2Decay(n) {
    n = Math.max(0, Math.min(5, n | 0));
    if (n < p2Decay) return;
    var prev = p2Decay;
    p2Decay = n;
    body.setAttribute("data-p2-decay", String(n));
    for (var i = 0; i <= 5; i++) body.classList.remove("p2-d" + i);
    body.classList.add("p2-d" + n);

    // 단계 진입 연출 (사운드 + 짧은 텍스트 부패)
    try {
      var a = window.__hauntAudio;
      if (a && a.unlock) a.unlock();
      if (n === 1 && a) {
        if (a.pulse) a.pulse("soft");
        if (a.whisper) setTimeout(function () { a.whisper(); }, 200);
      } else if (n === 2 && a) {
        if (a.staticBurst) a.staticBurst(140);
        if (a.pulse) a.pulse("mid");
      } else if (n === 3 && a) {
        if (a.rumble) a.rumble(1.2);
        if (a.breath) a.breath();
        if (a.setLevel) a.setLevel(Math.max(2, n > 2 ? 3 : 2));
      } else if (n === 4 && a) {
        if (a.sting) a.sting("soft");
        if (a.hddScratch) a.hddScratch();
        if (a.setLevel) a.setLevel(3);
      } else if (n === 5 && a) {
        if (a.dreadHit) a.dreadHit();
        else if (a.sting) a.sting("blood");
        if (a.setLevel) a.setLevel(3);
      }
    } catch (e) {}

    if (n >= 2 && n > prev) burstCorrupt(reduced ? 4 : 3, reduced ? 60 : 160);
    if (n >= 4) revealHorrorChrome();

    document.dispatchEvent(
      new CustomEvent("haunt-p2-decay", {
        detail: { level: n, prev: prev, elapsed: p2Elapsed },
      })
    );
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[p2-decay]", n, "elapsed", Math.round(p2Elapsed / 1000) + "s");
    }
  }

  /** mood만 올리고, stage는 매핑 규칙에 따라 천천히 */
  function setMood(m) {
    m = Math.max(0, Math.min(4, m | 0));
    if (m > 0 && !diaryDiscovered()) return;
    if (m <= mood) {
      emitMood();
      return;
    }
    mood = m;
    body.classList.toggle("mood-soft", mood === 1);
    body.classList.toggle("mood-dim", mood === 2);
    body.classList.toggle("mood-heavy", mood >= 3);
    body.classList.toggle("mood-peak", mood >= 4);
    emitMood();

    // stage 매핑 (mood → stage, 지연 있음)
    if (mood === 1) {
      setStage(1);
    } else if (mood === 2) {
      // 1달 전: stage 1 유지, CSS mood-dim 만 살짝 더 어둡게
      setStage(1);
      if (window.__hauntAudio) window.__hauntAudio.pulse("soft");
    } else if (mood === 3) {
      // 오늘 진입: 바로 풀 다크 말고 짧게 텀 후 corrupt
      if (window.__hauntAudio) {
        window.__hauntAudio.pulse("mid");
        window.__hauntAudio.setLevel(1);
      }
      if (corruptTimer) clearTimeout(corruptTimer);
      corruptTimer = setTimeout(function () {
        setStage(2);
        if (window.__hauntAudio) window.__hauntAudio.setLevel(2);
      }, reduced ? 400 : 2200);
      // dread 는 더 늦게
      if (dreadTimer) clearTimeout(dreadTimer);
      dreadTimer = setTimeout(function () {
        if (mood >= 3) {
          setMood(4);
        }
      }, reduced ? 3000 : 14000);
    } else if (mood >= 4) {
      setStage(2);
      setTimeout(function () {
        setStage(3);
        if (window.__hauntAudio) window.__hauntAudio.setLevel(3);
      }, reduced ? 300 : 1800);
    }
  }

  function keyForStage(n) {
    if (n <= 0) return "clean";
    if (n === 1) return "mid";
    return "horror";
  }

  function collectMorphs() {
    morphQueue = [];
    document.querySelectorAll("[data-clean]").forEach(function (el) {
      morphQueue.push(el);
    });
    // 히어로·내비 우선 (뒤에 두면 수 분 뒤에도 clean 카피 남음 → 허접)
    var priorityIds = [
      "titleL1",
      "titleL2",
      "eyebrow",
      "topRec",
      "navCta",
      "whisper",
      "corruptPath",
    ];
    var head = [];
    var rest = [];
    morphQueue.forEach(function (el) {
      if (priorityIds.indexOf(el.id) !== -1) head.push(el);
      else if (el.classList && (el.classList.contains("morph") || el.closest(".stasis-lede")))
        head.push(el);
      else rest.push(el);
    });
    // priority 중복 제거
    var seen = {};
    morphQueue = head.concat(rest).filter(function (el) {
      if (seen[el.id || el] && el.id) return false;
      if (el.id) seen[el.id] = true;
      return true;
    });
  }

  function applyMorphToEl(el, key, instant) {
    if (!el) return;
    el.classList.add("morphing");
    function apply() {
      if (el.classList.contains("morph") || el.classList.contains("morph-li")) {
        var html = el.getAttribute("data-" + key);
        if (html == null) html = el.getAttribute("data-mid") || el.getAttribute("data-clean") || "";
        el.innerHTML = html;
        if (el.classList.contains("morph-li") && !html) el.hidden = true;
        else el.hidden = false;
      } else if (el.id === "warnText") {
        var w = el.getAttribute("data-" + key) || "";
        el.innerHTML = w;
        var banner = document.getElementById("warnBanner");
        if (banner) banner.hidden = !w;
      } else if (el.id === "whisper") {
        var wh = el.getAttribute("data-" + key) || "";
        el.innerHTML = wh;
        el.style.display = wh ? "" : "none";
      } else if (
        el.id === "footText" ||
        el.id === "corruptPath" ||
        el.id === "eyebrow" ||
        el.id === "topRec" ||
        el.id === "navCta"
      ) {
        var t = el.getAttribute("data-" + key);
        if (t == null) t = el.getAttribute("data-clean") || el.textContent;
        t = String(t).replace(/<[^>]+>/g, "");
        // 로고 SVG 마크 유지 — .logo-text 만 교체
        if (el.id === "topRec") {
          var logoText = el.querySelector(".logo-text");
          if (logoText) logoText.textContent = t;
          else el.textContent = t;
        } else {
          el.textContent = t;
        }
      } else if (el.id === "titleL1" || el.id === "titleL2") {
        el.textContent = (
          el.getAttribute("data-" + key) ||
          el.getAttribute("data-clean") ||
          ""
        ).replace(/<[^>]+>/g, "");
      } else if (
        el.id === "h2log" ||
        el.id === "h2notes" ||
        el.id === "h2warn" ||
        el.id === "h2res"
      ) {
        el.textContent = (
          el.getAttribute("data-" + key) ||
          el.getAttribute("data-clean") ||
          ""
        ).replace(/<[^>]+>/g, "");
      } else {
        var h = el.getAttribute("data-" + key);
        if (h != null) el.innerHTML = h;
      }
      el.classList.remove("morphing");
      el.classList.add("morphed");
      el.setAttribute("data-morph-key", key);
    }
    if (instant || reduced) apply();
    else setTimeout(apply, 180 + Math.random() * 160);
  }

  function morphKeyNow() {
    if (mood >= 3 || stage >= 2) return "horror";
    if (stage === 1 || mood >= 1) return "mid";
    return "clean";
  }

  function corruptOne() {
    if (stage < 1) return false;
    if (morphIndex >= morphQueue.length) return false;
    var el = morphQueue[morphIndex++];
    if (!el) return corruptOne();
    applyMorphToEl(el, morphKeyNow(), false);
    return true;
  }

  /** mid로 굳은 카피를 horror로 재적용 + 미처리 전부 */
  function remorphAll(key, instant) {
    key = key || morphKeyNow();
    if (!morphQueue.length) collectMorphs();
    morphQueue.forEach(function (el) {
      applyMorphToEl(el, key, !!instant);
    });
    morphIndex = morphQueue.length;
  }

  function burstCorrupt(count, gapMs) {
    var n = count || 6;
    var gap = gapMs != null ? gapMs : 100;
    var i = 0;
    function step() {
      if (i >= n) return;
      if (!corruptOne()) {
        // 큐 소진 시 전체 remorph 한 번
        if (stage >= 2) remorphAll("horror", true);
        return;
      }
      i++;
      setTimeout(step, gap);
    }
    step();
  }

  function revealHorrorChrome() {
    var live = document.getElementById("logLiveRow");
    if (live) {
      live.hidden = false;
      var html = live.getAttribute("data-horror") || live.getAttribute("data-mid") || "";
      live.innerHTML = html;
    }
    // void-face 까만 얼굴 열 금지 (유치함) — 감시 연출은 anom-watcher 실루엣만
    var face = document.getElementById("faceRow");
    if (face) face.hidden = true;
    var sp = document.getElementById("deepSpacer");
    if (sp) sp.hidden = false;
    var t1 = document.getElementById("terminalLine");
    var t2 = document.getElementById("terminalLine2");
    if (t1) t1.hidden = false;
    if (t2) t2.hidden = false;
    var rec = document.getElementById("topRec");
    if (rec) {
      rec.textContent = "● REC · DO NOT LOOK AWAY";
      rec.classList.add("blink");
    }
  }

  function diaryBoost() {
    var b = window.__hauntDiaryBoost;
    return typeof b === "number" && b > 0 ? b : 1;
  }

  /**
   * 일기 페이지 → mood (stage 2 풀다크는 오늘 페이지만)
   * page 0 → mood 1
   * page 1 → mood 2  (살짝 더 어두움, 아직 stage 1)
   * page 2 → mood 3 → (시간 후) mood 4
   */
  function moodFromDiary(detail) {
    if (!detail || !detail.discovered) return 0;
    var p = typeof detail.page === "number" ? detail.page : 0;
    var u = typeof detail.unlocked === "number" ? detail.unlocked : p;
    var high = Math.max(p, u);
    if (high >= 2) return 3;
    if (high >= 1) return 2;
    return 1;
  }

  function onDiary(ev) {
    var d = (ev && ev.detail) || {};
    var targetMood = moodFromDiary(d);
    if (targetMood > mood) setMood(targetMood);

    // 텍스트 부패는 mood 2부터 아주 천천히, mood 3+ 에서 본격
    if (mood >= 2 && morphIndex < morphQueue.length && Math.random() > 0.4) {
      corruptOne();
    }
  }

  function ensureMorphLoop() {
    if (morphLoopStarted) return;
    if (stage < 1) return;
    morphLoopStarted = true;
    setTimeout(function () {
      if (stage >= 1 && mood >= 1) corruptOne();
    }, reduced ? 600 : 2000);
    morphTick();
  }

  function morphTick() {
    if (document.body.classList.contains("is-haunting")) {
      setTimeout(morphTick, 2500);
      return;
    }
    if (stage < 1 || mood < 1) {
      setTimeout(morphTick, 2000);
      return;
    }
    if (morphIndex < morphQueue.length) {
      // mood 낮을수록 드물게
      var chance = mood <= 1 ? 0.35 : mood === 2 ? 0.55 : 0.85;
      if (Math.random() < chance) corruptOne();
      if (mood >= 4 && morphIndex < morphQueue.length && Math.random() > 0.75) {
        corruptOne();
      }
    }
    var base = reduced ? 2200 : mood <= 1 ? 6500 : mood === 2 ? 5200 : mood === 3 ? 4000 : 3200;
    var next = base / Math.min(Math.max(diaryBoost(), 1), 2.2);
    setTimeout(morphTick, next);
  }

  var lastBurstStage = 0;
  setInterval(function () {
    if (stage >= 3 && lastBurstStage < 3) {
      lastBurstStage = 3;
      revealHorrorChrome();
      var burst = setInterval(function () {
        if (!corruptOne()) {
          clearInterval(burst);
          return;
        }
      }, reduced ? 500 : 1400);
    }
    lastBurstStage = Math.max(lastBurstStage, stage);
  }, 400);

  var whisper = document.getElementById("whisper");
  if (whisper && !whisper.getAttribute("data-clean")) {
    whisper.style.display = "none";
  }

  collectMorphs();
  setStage(0);
  mood = 0;
  emitMood();

  document.addEventListener("haunt-diary", onDiary);

  if (diaryDiscovered()) {
    onDiary({
      detail: {
        discovered: true,
        page: window.__hauntDiaryPage || 0,
        unlocked: window.__hauntDiaryPage || 0,
      },
    });
  }

  window.__hauntStage = function () {
    return stage;
  };
  window.__hauntMood = function () {
    return mood;
  };
  window.__hauntSetStage = setStage;
  window.__hauntSetMood = setMood;
  window.__hauntP2Decay = function () {
    return p2Decay;
  };
  window.__hauntSetP2Decay = setP2Decay;
  window.__hauntP2Elapsed = function () {
    return p2Elapsed;
  };
})();
