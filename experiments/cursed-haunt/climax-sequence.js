/**
 * 클라이맥스 1→5 순차 스크린세이버
 *  1 신호 탈취 / 노이즈
 *  2 좀비 프로세스 폭주
 *  3 화면 붕괴 (피·얼굴·지직)
 *  4 WakeAgain 각인 폭풍
 *  5 최종 선언 → 엔딩 핸드오프
 */
(function () {
  "use strict";

  var haunt = document.getElementById("haunt");
  if (!haunt) return;

  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var phases = {
    1: document.getElementById("hauntP1"),
    2: document.getElementById("hauntP2"),
    3: document.getElementById("hauntP3"),
    4: document.getElementById("hauntP4"),
    5: document.getElementById("hauntP5"),
  };
  var listEl = document.getElementById("hauntList");
  var subEl = document.getElementById("hauntSub");
  var rainEl = document.getElementById("hauntRain");
  var facesEl = document.getElementById("hauntFaces");
  var wakeStorm = document.getElementById("hauntWakeStorm");
  var exitEl = document.getElementById("hauntExit");

  var running = false;
  var phase = 0;
  var timers = [];
  var intervals = [];
  var complete = false;

  var PROC_NAMES = [
    "side_project_v3",
    "todo_app_really_final",
    "saas_idea_2024",
    "untitled_mobile",
    "mvp_before_launch",
    "discord_bot_wip",
    "portfolio_remake",
    "ai_wrapper_demo",
    "abandoned_mvp",
    "stasis_draft",
    "final_FINAL2",
    "wake_me_later",
  ];

  function clearAllTimers() {
    timers.forEach(function (t) {
      clearTimeout(t);
    });
    intervals.forEach(function (t) {
      clearInterval(t);
    });
    timers = [];
    intervals = [];
  }

  function later(ms, fn) {
    var id = setTimeout(fn, ms);
    timers.push(id);
    return id;
  }

  function every(ms, fn) {
    var id = setInterval(fn, ms);
    intervals.push(id);
    return id;
  }

  function audio() {
    return window.__hauntAudio || null;
  }

  function setPhase(n) {
    phase = n;
    haunt.setAttribute("data-climax-phase", String(n));
    document.body.setAttribute("data-climax-phase", String(n));
    for (var k = 1; k <= 5; k++) {
      var el = phases[k];
      if (!el) continue;
      var on = k === n;
      el.hidden = !on;
      el.classList.toggle("is-on", on);
    }
    haunt.className = "haunt climax-p" + n;
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[climax-seq] phase", n);
    }
    document.dispatchEvent(
      new CustomEvent("haunt-climax-phase", { detail: { phase: n } })
    );
  }

  function hideAllPhases() {
    for (var k = 1; k <= 5; k++) {
      if (phases[k]) {
        phases[k].hidden = true;
        phases[k].classList.remove("is-on");
      }
    }
  }

  function flashWake(mode) {
    var a = audio();
    if (a && a.sting) a.sting(mode === "neon" ? "neon" : "blood");
    if (window.__hauntAnomalies && typeof window.__hauntAnomalies.flash === "function") {
      // silent: 스팅은 위에서 1회만
      window.__hauntAnomalies.flash({
        force: true,
        mode: mode || "blood",
        ms: 40 + Math.random() * 30,
        silent: true,
      });
      return;
    }
    // fallback
    if (!wakeStorm) return;
    wakeStorm.textContent = "WakeAgain";
    wakeStorm.classList.add("is-on", mode === "neon" ? "neon" : "blood");
    setTimeout(function () {
      wakeStorm.classList.remove("is-on", "neon", "blood");
    }, 50);
  }

  function fillProcessList() {
    if (!listEl) return;
    listEl.innerHTML = "";
    var picks = PROC_NAMES.slice().sort(function () {
      return Math.random() - 0.5;
    });
    picks.forEach(function (p, i) {
      later(i * (reduced ? 80 : 160), function () {
        if (phase !== 2) return;
        var li = document.createElement("li");
        li.textContent =
          "zombie · " +
          p +
          " · pid " +
          (1000 + Math.floor(Math.random() * 8000)) +
          " · still running";
        listEl.appendChild(li);
        listEl.scrollTop = listEl.scrollHeight;
        var a = audio();
        if (a && a.typeClick) a.typeClick(Math.random() > 0.5 ? "soft" : "mid");
      });
    });
    if (subEl) {
      subEl.textContent =
        "WakeAgain · " +
        picks[0] +
        ".exe — count " +
        picks.length;
    }
  }

  function startRain() {
    if (!rainEl) return;
    rainEl.innerHTML = "";
    rainEl.hidden = false;
    var words = [
      "버려진",
      "FINAL2",
      "kill -9",
      "나중에",
      "HELP",
      "process",
      "WakeAgain",
      "error",
      "████",
      "still",
    ];
    every(reduced ? 200 : 90, function () {
      if (phase < 2 || phase > 4) return;
      var s = document.createElement("span");
      s.className = "haunt-rain-word";
      s.textContent = words[Math.floor(Math.random() * words.length)];
      s.style.left = Math.random() * 100 + "%";
      s.style.animationDuration = 1.2 + Math.random() * 1.8 + "s";
      rainEl.appendChild(s);
      setTimeout(function () {
        if (s.parentNode) s.parentNode.removeChild(s);
      }, 3200);
    });
  }

  function stopRain() {
    if (rainEl) {
      rainEl.hidden = true;
      rainEl.innerHTML = "";
    }
  }

  /** 클라이맥스에 유아틱 까만 얼굴 금지 — 감시자 연출은 2페이즈 전용 */
  function startFaces() {
    if (facesEl) {
      facesEl.hidden = true;
      facesEl.innerHTML = "";
    }
  }

  function stopFaces() {
    if (facesEl) {
      facesEl.hidden = true;
      facesEl.innerHTML = "";
    }
  }

  function runPhase1(next) {
    setPhase(1);
    var a = audio();
    if (a) {
      if (a.unlock) a.unlock();
      if (a.staticBurst) a.staticBurst(280);
      if (a.rumble) a.rumble(1.8);
      if (a.hddScratch) a.hddScratch();
      if (a.termBeep) a.termBeep(140);
    }
    document.title = "SIGNAL INTERRUPT";
    // 주소창도 단계 연출
    try {
      var ut = document.getElementById("fakeUrlText");
      if (ut) ut.textContent = "about:signal-interrupt";
    } catch (e) {}
    later(reduced ? 1600 : 3600, next);
  }

  function runPhase2(next) {
    setPhase(2);
    fillProcessList();
    startRain();
    var a = audio();
    if (a && a.setLevel) a.setLevel(2);
    try {
      var ut = document.getElementById("fakeUrlText");
      if (ut) ut.textContent = "about:zombie-list";
    } catch (e) {}
    every(reduced ? 400 : 200, function () {
      if (phase !== 2) return;
      if (a && a.typeClick) a.typeClick("soft");
    });
    later(reduced ? 2200 : 5200, next);
  }

  function runPhase3(next) {
    setPhase(3);
    // 얼굴 스폰 없음 — 화면 붕괴·시선 압박은 비네팅/노이즈/사운드만
    startFaces();
    if (haunt) haunt.classList.add("climax-p3-gaze");
    var a = audio();
    if (a) {
      if (a.rumble) a.rumble(2.2);
      if (a.hddScratch) a.hddScratch();
      if (a.setLevel) a.setLevel(3);
      if (a.whisper) a.whisper();
    }
    document.title = "DO NOT LOOK AWAY";
    try {
      var ut = document.getElementById("fakeUrlText");
      if (ut) ut.textContent = "about:viewport-corrupt";
    } catch (e) {}
    if (haunt) haunt.classList.add("climax-shake-on");
    later(reduced ? 500 : 900, function () {
      if (haunt) haunt.classList.remove("climax-shake-on");
    });
    var n = 0;
    every(reduced ? 320 : 180, function () {
      if (phase !== 3) return;
      n++;
      if (n % 7 === 0) haunt.classList.toggle("climax-invert", true);
      if (n % 7 === 1) haunt.classList.toggle("climax-invert", false);
      if (n % 6 === 0 && a && a.pulse) a.pulse("heavy");
      if (n % 11 === 0 && a && a.hddScratch) a.hddScratch();
    });
    later(reduced ? 2000 : 4600, function () {
      haunt.classList.remove("climax-invert", "climax-shake-on", "climax-p3-gaze");
      next();
    });
  }

  function runPhase4(next) {
    setPhase(4);
    stopFaces();
    var a = audio();
    if (a && a.termBeep) a.termBeep(660);
    document.title = "WakeAgain";
    try {
      var ut = document.getElementById("fakeUrlText");
      if (ut) ut.textContent = "WakeAgain";
      var tab = document.getElementById("fakeTabTitle");
      if (tab) tab.textContent = "WakeAgain";
    } catch (e) {}
    var flashes = reduced ? 4 : 9;
    var i = 0;
    function burst() {
      if (phase !== 4) return;
      if (i >= flashes) {
        next();
        return;
      }
      flashWake(i % 2 === 0 ? "blood" : "neon");
      if (a && a.typeClick) a.typeClick("hard");
      i++;
      later(reduced ? 280 : 180 + Math.random() * 220, burst);
    }
    // 브랜드 텍스트 글리치
    var brand = document.getElementById("hauntBrand");
    if (brand) {
      every(120, function () {
        if (phase !== 4) return;
        brand.style.transform =
          "translate(" +
          (Math.random() * 8 - 4) +
          "px," +
          (Math.random() * 6 - 3) +
          "px) skewX(" +
          (Math.random() * 6 - 3) +
          "deg)";
      });
    }
    later(200, burst);
  }

  function runPhase5(next) {
    setPhase(5);
    stopRain();
    var a = audio();
    if (a) {
      if (a.rumble) a.rumble(2);
      if (a.setLevel) a.setLevel(3);
      if (a.termBeep) a.termBeep(220);
    }
    document.title = "PROCESS_NOT_DEAD";
    try {
      var ut = document.getElementById("fakeUrlText");
      if (ut) ut.textContent = "PROCESS_NOT_DEAD";
    } catch (e) {}
    if (exitEl) exitEl.textContent = "[ 신호 종료 대기… ]";
    later(reduced ? 1000 : 1800, function () {
      if (exitEl) exitEl.textContent = "[ 연결 끊는 중… ]";
    });
    later(reduced ? 1800 : 2800, function () {
      if (exitEl) exitEl.textContent = "[ … ]";
    });
    later(reduced ? 2400 : 4200, function () {
      complete = true;
      next();
    });
  }

  function finishToEnding() {
    running = false;
    phase = 0;
    clearAllTimers();
    stopRain();
    stopFaces();
    hideAllPhases();
    if (typeof window.__hauntGoToEnding === "function") {
      window.__hauntGoToEnding();
    } else if (typeof window.__hauntStartEnding === "function") {
      // fallback
      if (haunt) {
        haunt.hidden = true;
        haunt.setAttribute("aria-hidden", "true");
      }
      document.body.classList.remove("is-haunting");
      window.__hauntStartEnding();
    }
  }

  /**
   * app.js summon 이 오버레이를 연 뒤 호출
   */
  function startSequence() {
    if (running) return;
    running = true;
    complete = false;
    phase = 0;
    clearAllTimers();
    hideAllPhases();
    stopRain();
    stopFaces();

    if (haunt) {
      haunt.hidden = false;
      haunt.setAttribute("aria-hidden", "false");
    }

    var chain = reduced
      ? [runPhase1, runPhase2, runPhase3, runPhase4, runPhase5]
      : [runPhase1, runPhase2, runPhase3, runPhase4, runPhase5];

    var i = 0;
    function step() {
      if (i >= chain.length) {
        finishToEnding();
        return;
      }
      var fn = chain[i++];
      fn(step);
    }
    step();
  }

  function stopSequence() {
    clearAllTimers();
    running = false;
    stopRain();
    stopFaces();
    haunt.classList.remove("climax-invert");
  }

  function isComplete() {
    return complete;
  }

  function currentPhase() {
    return phase;
  }

  function isRunning() {
    return running;
  }

  window.__hauntClimaxSequence = {
    start: startSequence,
    stop: stopSequence,
    isComplete: isComplete,
    phase: currentPhase,
    isRunning: isRunning,
  };
})();
