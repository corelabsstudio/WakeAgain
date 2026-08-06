/**
 * cursed-haunt — 규격 자동 전환 (PC / 폰)
 *
 * 화면 너비·포인터 종류를 보고 desktop | mobile 프로필을 고르고,
 * 리사이즈·방향 전환 시 레이아웃 클래스 + 발동 수치를 다시 적용한다.
 *
 * 발동 의식(순서)은 동일, 수치·히트존 크기만 프로필별로 다름.
 * ?summon=1 / ?debug=1
 */
(function () {
  "use strict";

  var hit = document.getElementById("hauntHit");
  var haunt = document.getElementById("haunt");
  var clock = document.getElementById("clock");
  var fakeMsg = document.getElementById("fakeMsg");
  var terminalLine = document.getElementById("terminalLine");
  var seedHint = document.getElementById("seedHint");
  var hauntTitle = document.getElementById("hauntTitle");
  var hauntSub = document.getElementById("hauntSub");
  var hauntList = document.getElementById("hauntList");
  var reducedNote = document.getElementById("reducedNote");

  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced && reducedNote) reducedNote.hidden = false;

  var debug = false;
  try {
    debug = /[?&]debug=1/.test(location.search);
  } catch (e) {}

  // ----- 디바이스 프로필 (자동) -----
  var profile = "desktop"; // desktop | mobile
  var SPEC = {};

  function detectProfile() {
    var w = window.innerWidth || document.documentElement.clientWidth || 1024;
    var narrow = w <= 720;
    var coarse = false;
    var fine = true;
    try {
      coarse = window.matchMedia("(pointer: coarse)").matches;
      fine = window.matchMedia("(pointer: fine)").matches;
    } catch (e) {}
    var touchPoints = navigator.maxTouchPoints || 0;
    // 폰/좁은 화면 우선. 넓은 화면+마우스는 desktop.
    // 아이패드 세로 등: 너비 기준 + coarse
    if (narrow || (coarse && w <= 900 && !fine)) return "mobile";
    if (touchPoints > 0 && w <= 768) return "mobile";
    return "desktop";
  }

  function buildSpec(p) {
    if (p === "mobile") {
      return {
        name: "mobile",
        minDwellMs: 18000,
        deepNeed: 0.85,
        midLo: 0.12,
        midHi: 0.42,
        midHoldMs: 3000,
        ritualSettleMs: 2000,
        midDecay: 80,
        hitSize: 44,
        hitPad: 12,
        hitMaxYRatio: 0.82,
        edgeWeight: 0.75,
        moveDelayMin: 1100,
        moveDelaySpan: 500,
        pulseLiveMin: 1100,
        pulseLiveSpan: 350,
        pulseGapMin: 6000,
        pulseGapSpan: 5000,
        dblWindowMs: 480,
        microGlitchChance: 0.04,
      };
    }
    return {
      name: "desktop",
      minDwellMs: 22000,
      deepNeed: 0.9,
      midLo: 0.12,
      midHi: 0.38,
      midHoldMs: 3500,
      ritualSettleMs: 2500,
      midDecay: 120,
      hitSize: 16,
      hitPad: 8,
      hitMaxYRatio: 1,
      edgeWeight: 0.85,
      moveDelayMin: 900,
      moveDelaySpan: 400,
      pulseLiveMin: 750,
      pulseLiveSpan: 200,
      pulseGapMin: 6000,
      pulseGapSpan: 5000,
      dblWindowMs: 380,
      microGlitchChance: 0.06,
    };
  }

  function applyProfile(force) {
    var next = detectProfile();
    if (!force && next === profile && SPEC.name) return;
    profile = next;
    SPEC = buildSpec(profile);

    var root = document.documentElement;
    root.classList.toggle("is-mobile", profile === "mobile");
    root.classList.toggle("is-desktop", profile === "desktop");
    root.setAttribute("data-device", profile);

    if (hit) {
      hit.style.width = SPEC.hitSize + "px";
      hit.style.height = SPEC.hitSize + "px";
    }
    if (seedHint) {
      var sig = seedHint.getAttribute("data-sig");
      if (!sig) {
        sig = Math.random().toString(16).slice(2, 8);
        seedHint.setAttribute("data-sig", sig);
      }
      seedHint.textContent = "sig:" + sig + (profile === "mobile" ? "·m" : "·d");
    }
    if (pulseOn) placeHit();
    if (debug) console.log("[haunt] profile →", profile, SPEC);
  }

  // ----- clock -----
  function tickClock() {
    if (!clock) return;
    clock.textContent = new Date().toTimeString().slice(0, 8);
  }
  tickClock();
  setInterval(tickClock, 1000);

  var traps = [
    "파일을 찾을 수 없습니다. (error 0xDEAD) — 그런데 누가 계속 읽고 있지?",
    "빌드 큐가 비어 있지 않습니다. 아무도 없습니다. 그런데 컴파일 중입니다.",
    "종료 신호 전송됨… 프로세스가 웃으며 거절했습니다.",
    "permission denied: you abandoned this. it did not abandon you.",
    "sequence rejected. something else accepted.",
    "…도움 요청이 거부되었습니다.",
    "이 버튼은 당신을 위한 것이 아닙니다.",
  ];

  var pageReadyAt = Date.now();
  // Pro(1) 비활성 → Free(2) → Team(3) 만 사용 (hit_pulse 세션용)
  var RITUAL_ORDER = ["2", "3"];
  var ritualIdx = 0;
  var ritualDone = false;
  var ritualDoneAt = 0;
  var hasDeep = false;
  var midHoldMs = 0;
  var midLastTs = 0;
  var hauntActive = false;
  var climaxStartedAt = 0;
  var endingArmed = false;
  var autoEndingTimer = null;

  var pulseOn = false;
  var pulseTimer = null;
  var moveTimer = null;
  var lastHitTap = 0;
  var armedForHit = false;

  applyProfile(true);

  function scrollRatio() {
    var el = document.documentElement;
    var max = el.scrollHeight - el.clientHeight;
    if (max <= 0) return 1;
    return el.scrollTop / max;
  }

  function dwellOk() {
    return Date.now() - pageReadyAt >= SPEC.minDwellMs;
  }
  function midOk() {
    return midHoldMs >= SPEC.midHoldMs;
  }
  function ritualSettled() {
    return ritualDone && Date.now() - ritualDoneAt >= SPEC.ritualSettleMs;
  }
  function softReady() {
    // hit_pulse 트리거 세션에서만 고전 의식 사용 (climax-triggers.js 가 플래그)
    if (!window.__hauntHitPulseMode) return false;
    // 2페이즈 게이트: 일기 발견 + stage≥2
    if (!window.__hauntDiaryDiscovered) return false;
    var st = typeof window.__hauntStage === "function" ? window.__hauntStage() : 0;
    if (st < 2) return false;
    return dwellOk() && hasDeep && midOk() && ritualSettled();
  }

  function logDebug() {
    if (!debug) return;
    console.log("[haunt]", {
      profile: profile,
      dwell: dwellOk(),
      deep: hasDeep,
      midHoldMs: Math.floor(midHoldMs),
      ritualIdx: ritualIdx,
      ritualDone: ritualDone,
      settled: ritualSettled(),
      soft: softReady(),
      pulse: pulseOn,
      scroll: scrollRatio().toFixed(2),
      w: window.innerWidth,
    });
  }

  document.querySelectorAll(".plan-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (!document.body.classList.contains("stage-clean")) return;
      document.querySelectorAll(".plan-btn").forEach(function (b) {
        b.classList.remove("is-on");
      });
      btn.classList.add("is-on");
    });
  });

  document.querySelectorAll("[data-fake]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-fake");
      if (fakeMsg) {
        fakeMsg.hidden = false;
        // clean stage: quieter trap messages
        if (document.body.classList.contains("stage-clean")) {
          fakeMsg.textContent = "Saved.";
          setTimeout(function () {
            if (fakeMsg) fakeMsg.hidden = true;
          }, 1200);
        } else {
          fakeMsg.textContent = traps[Math.floor(Math.random() * traps.length)];
        }
      }
      if (ritualDone) {
        ritualDone = false;
        ritualIdx = 0;
        ritualDoneAt = 0;
        midHoldMs = Math.min(midHoldMs, SPEC.midHoldMs * 0.3);
        disarmPulse();
        logDebug();
        return;
      }
      var need = RITUAL_ORDER[ritualIdx];
      if (id === need) {
        ritualIdx += 1;
        if (ritualIdx >= RITUAL_ORDER.length) {
          ritualDone = true;
          ritualDoneAt = Date.now();
          ritualIdx = 0;
        }
      } else {
        ritualIdx = 0;
        if (id === RITUAL_ORDER[0]) ritualIdx = 1;
      }
      logDebug();
    });
  });

  function onScroll() {
    var r = scrollRatio();
    if (r >= SPEC.deepNeed) hasDeep = true;
    var now = Date.now();
    if (hasDeep && r >= SPEC.midLo && r <= SPEC.midHi) {
      if (!midLastTs) midLastTs = now;
      midHoldMs += now - midLastTs;
      midLastTs = now;
    } else {
      midLastTs = 0;
      midHoldMs = Math.max(0, midHoldMs - SPEC.midDecay);
    }
    evaluateArm();
  }
  window.addEventListener("scroll", onScroll, { passive: true });

  // 리사이즈·방향 전환 → 규격 자동 재적용
  var resizeTimer = null;
  function onViewportChange() {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      applyProfile(false);
      onScroll();
    }, 100);
  }
  window.addEventListener("resize", onViewportChange);
  window.addEventListener("orientationchange", function () {
    setTimeout(function () {
      applyProfile(true);
      onScroll();
    }, 200);
  });
  try {
    var mql = window.matchMedia("(max-width: 720px)");
    if (mql.addEventListener) mql.addEventListener("change", onViewportChange);
    else if (mql.addListener) mql.addListener(onViewportChange);
  } catch (e) {}

  setInterval(function () {
    if (midLastTs) onScroll();
    evaluateArm();
    logDebug();
  }, 400);

  var terms = [
    "> waiting for signal_",
    "> listening :3847_",
    "> child_process still attached_",
    "> memory leak is a form of memory_",
    "> sequence incomplete_",
    "> do not trust the buttons_",
  ];
  var ti = 0;
  setInterval(function () {
    if (!terminalLine || hauntActive) return;
    ti = (ti + 1) % terms.length;
    terminalLine.textContent = terms[ti];
  }, 2800);

  function placeHit() {
    if (!hit || hauntActive) return;
    var pad = SPEC.hitPad;
    var w = SPEC.hitSize;
    var h = SPEC.hitSize;
    hit.style.width = w + "px";
    hit.style.height = h + "px";
    var maxX = Math.max(pad, window.innerWidth - w - pad);
    var maxY = Math.max(pad, window.innerHeight - h - pad);
    if (SPEC.hitMaxYRatio < 1) {
      maxY = Math.max(pad, Math.floor(window.innerHeight * SPEC.hitMaxYRatio) - h);
    }
    var edge = Math.random() < SPEC.edgeWeight;
    var x, y;
    if (edge) {
      var side = Math.floor(Math.random() * 4);
      if (side === 0) {
        x = pad + Math.random() * 28;
        y = pad + Math.random() * maxY;
      } else if (side === 1) {
        x = maxX - Math.random() * 28;
        y = pad + Math.random() * maxY;
      } else if (side === 2) {
        x = pad + Math.random() * maxX;
        y = pad + Math.random() * 28;
      } else {
        x = pad + Math.random() * maxX;
        y = maxY - Math.random() * 28;
      }
    } else {
      x = pad + Math.random() * (maxX - pad);
      y = pad + Math.random() * (maxY - pad);
    }
    hit.style.left = Math.round(x) + "px";
    hit.style.top = Math.round(y) + "px";
  }

  function scheduleMove() {
    if (moveTimer) clearTimeout(moveTimer);
    if (!pulseOn || hauntActive) return;
    var delay = SPEC.moveDelayMin + Math.random() * SPEC.moveDelaySpan;
    moveTimer = setTimeout(function () {
      if (pulseOn && !hauntActive) {
        placeHit();
        scheduleMove();
      }
    }, delay);
  }

  function startPulseBurst() {
    if (hauntActive || !armedForHit) return;
    pulseOn = true;
    if (hit) {
      hit.classList.add("is-hot");
      hit.classList.remove("is-off");
    }
    placeHit();
    scheduleMove();
    var live = SPEC.pulseLiveMin + Math.random() * SPEC.pulseLiveSpan;
    setTimeout(function () {
      endPulseBurst();
    }, live);
  }

  function endPulseBurst() {
    pulseOn = false;
    if (hit) {
      hit.classList.remove("is-hot");
      hit.classList.add("is-off");
    }
    if (moveTimer) {
      clearTimeout(moveTimer);
      moveTimer = null;
    }
    scheduleNextPulse();
  }

  function scheduleNextPulse() {
    if (pulseTimer) clearTimeout(pulseTimer);
    if (hauntActive || !armedForHit) return;
    var gap = SPEC.pulseGapMin + Math.random() * SPEC.pulseGapSpan;
    pulseTimer = setTimeout(function () {
      if (armedForHit && !hauntActive) startPulseBurst();
      else scheduleNextPulse();
    }, gap);
  }

  function disarmPulse() {
    armedForHit = false;
    pulseOn = false;
    if (pulseTimer) {
      clearTimeout(pulseTimer);
      pulseTimer = null;
    }
    if (moveTimer) {
      clearTimeout(moveTimer);
      moveTimer = null;
    }
    if (hit) {
      hit.classList.remove("is-hot");
      hit.classList.add("is-off");
    }
  }

  function evaluateArm() {
    if (hauntActive) return;
    var ok = softReady();
    if (ok && !armedForHit) {
      armedForHit = true;
      if (pulseTimer) clearTimeout(pulseTimer);
      pulseTimer = setTimeout(function () {
        if (armedForHit && !hauntActive) startPulseBurst();
      }, 2000 + Math.random() * 3000);
    } else if (!ok && armedForHit) {
      disarmPulse();
    }
  }

  setInterval(function () {
    if (hauntActive || reduced || !armedForHit) return;
    if (document.body.classList.contains("diary-open")) return;
    if (document.body.classList.contains("is-ending")) return;
    if (Math.random() > SPEC.microGlitchChance) return;
    // 인라인 body filter 금지 (fixed UI 붕괴) — 클래스만
    document.body.classList.add("anom-hue-spike");
    document.body.style.setProperty(
      "--anom-hue",
      30 + Math.random() * 50 + "deg"
    );
    setTimeout(function () {
      if (!hauntActive) {
        document.body.classList.remove("anom-hue-spike");
        document.body.style.removeProperty("--anom-hue");
      }
    }, 70 + Math.random() * 100);
  }, 5000);

  var names = [
    "side_project_v3",
    "todo_app_really_final",
    "saas_idea_2024",
    "untitled_mobile",
    "mvp_before_launch",
    "discord_bot_wip",
    "portfolio_remake",
    "ai_wrapper_demo",
  ];

  function summon() {
    if (hauntActive) return;
    if (document.body.classList.contains("is-ending")) return;
    hauntActive = true;
    endingArmed = false;
    climaxStartedAt = Date.now();
    disarmPulse();
    document.body.classList.add("is-haunting");
    document.body.style.filter = "";
    document.body.style.touchAction = "none";

    // 클라이맥스 진입 공포 타격
    try {
      var au = window.__hauntAudio;
      if (au) {
        if (au.unlock) au.unlock();
        if (au.dreadHit) au.dreadHit();
        else if (au.rumble) au.rumble(1.8);
        if (au.setLevel) au.setLevel(3);
      }
    } catch (e) {}

    if (haunt) {
      haunt.hidden = false;
      haunt.setAttribute("aria-hidden", "false");
    }
    try {
      sessionStorage.setItem("haunt_ok", String(Date.now()));
    } catch (e) {}

    // 1→5 순차 시퀀스 (끝나면 자동 엔딩)
    if (autoEndingTimer) {
      clearTimeout(autoEndingTimer);
      autoEndingTimer = null;
    }
    if (window.__hauntClimaxSequence && typeof window.__hauntClimaxSequence.start === "function") {
      window.__hauntClimaxSequence.start();
    } else {
      // 폴백: 시퀀스 스크립트 없을 때 기존 타이머 엔딩
      autoEndingTimer = setTimeout(function () {
        if (hauntActive && !endingArmed) goToEnding();
      }, reduced ? 4500 : 12000);
    }
  }

  /** 클라이맥스 종료 → 정적 → 엔딩 */
  function goToEnding() {
    if (endingArmed) return;
    endingArmed = true;
    hauntActive = false;
    if (autoEndingTimer) {
      clearTimeout(autoEndingTimer);
      autoEndingTimer = null;
    }
    if (window.__hauntClimaxSequence && window.__hauntClimaxSequence.stop) {
      try {
        window.__hauntClimaxSequence.stop();
      } catch (e) {}
    }
    if (haunt) {
      haunt.hidden = true;
      haunt.setAttribute("aria-hidden", "true");
      haunt.setAttribute("data-climax-phase", "0");
    }
    document.body.classList.remove("is-haunting");
    document.body.removeAttribute("data-climax-phase");
    disarmPulse();
    ritualDone = false;
    ritualIdx = 0;
    ritualDoneAt = 0;

    if (typeof window.__hauntStartEnding === "function") {
      window.__hauntStartEnding();
    }
  }

  function banish() {
    if (document.body.classList.contains("is-ending")) return;
    if (!hauntActive) return;

    // 1~5 시퀀스 끝나기 전에는 스킵 불가 (여운·연출 보호)
    var seq = window.__hauntClimaxSequence;
    if (seq && seq.isRunning && seq.isRunning() && !(seq.isComplete && seq.isComplete())) {
      var p = seq.phase ? seq.phase() : 0;
      if (p < 5) {
        if (fakeMsg) {
          fakeMsg.hidden = false;
          fakeMsg.textContent = "…아직 " + p + "/5";
          setTimeout(function () {
            if (fakeMsg) fakeMsg.hidden = true;
          }, 1000);
        }
        return;
      }
    }

    var seen = Date.now() - climaxStartedAt;
    var minSee = reduced ? 2000 : 4000;
    if (seen < minSee) {
      if (fakeMsg) {
        fakeMsg.hidden = false;
        fakeMsg.textContent = "…아직 끝나지 않았다";
        setTimeout(function () {
          if (fakeMsg) fakeMsg.hidden = true;
        }, 1200);
      }
      return;
    }
    goToEnding();
  }

  // climax-sequence.js 가 끝날 때 호출
  window.__hauntGoToEnding = goToEnding;

  function tryHitActivate(e) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!pulseOn || !armedForHit || hauntActive) return;

    var now = Date.now();
    var sec = new Date().getSeconds();
    var evenSec = sec % 2 === 0;

    if (now - lastHitTap > SPEC.dblWindowMs) {
      lastHitTap = now;
      return;
    }
    lastHitTap = 0;

    if (!evenSec) {
      endPulseBurst();
      midHoldMs = Math.floor(SPEC.midHoldMs * 0.4);
      if (fakeMsg) {
        fakeMsg.hidden = false;
        fakeMsg.textContent = "timing rejected.";
      }
      return;
    }
    // climax-triggers 의 hit_pulse 가 리스닝
    document.dispatchEvent(new CustomEvent("haunt-hit-success"));
    summon();
  }

  if (hit) {
    hit.classList.add("is-off");
    hit.addEventListener("click", tryHitActivate);
    hit.addEventListener(
      "touchend",
      function (e) {
        tryHitActivate(e);
      },
      { passive: false }
    );
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" || e.key === "Esc") banish();
  });
  if (haunt) {
    haunt.addEventListener("click", function () {
      banish();
    });
    haunt.addEventListener(
      "touchend",
      function (e) {
        e.preventDefault();
        banish();
      },
      { passive: false }
    );
  }

  // 외부(클라이맥스 트리거·제작자 패스)용
  window.__hauntSummon = summon;
  window.__hauntBanish = banish;

  // ?summon=1 은 climax-triggers.js 에서도 처리 (중복 소환 가드 있음)
  try {
    if (/[?&]summon=1/.test(location.search) && !window.__hauntClimax) {
      setTimeout(summon, 450);
    }
  } catch (e) {}
})();
