/**
 * 메인 페이지 공포 앰비언스 (발동 조건과 무관)
 * — 텍스트 글리치, 경로 부패, 떠다니는 단어, 간헐적 화면 틱
 */
(function () {
  "use strict";

  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) return;

  function stageOk(min) {
    var s = window.__hauntStage ? window.__hauntStage() : 0;
    // data-stage fallback
    if (typeof s !== "number") {
      s = parseInt(document.body.getAttribute("data-stage") || "0", 10) || 0;
    }
    return s >= min;
  }

  var path = document.getElementById("corruptPath");
  var whisper = document.getElementById("whisper");
  var terminalLine2 = document.getElementById("terminalLine2");
  var floatWords = document.getElementById("floatWords");
  var faceHint = document.getElementById("faceHint");

  var pathHorror = "C:\\Users\\…\\abandoned\\mvp_final_FINAL2\\";
  var glitchChars = "█▓▒░ ent_ERROR 01xeil 귀신 process_null ■◆";

  function corruptString(s, amount) {
    var arr = s.split("");
    var n = Math.max(1, Math.floor(arr.length * amount));
    for (var i = 0; i < n; i++) {
      var j = Math.floor(Math.random() * arr.length);
      arr[j] = glitchChars.charAt(Math.floor(Math.random() * glitchChars.length));
    }
    return arr.join("");
  }

  // 경로 문자열 가끔 깨짐 — stage 2+
  if (path) {
    setInterval(function () {
      if (document.body.classList.contains("is-haunting")) return;
      if (!stageOk(2)) return;
      if (Math.random() > 0.35) return;
      var base = path.getAttribute("data-horror") || pathHorror;
      path.textContent = corruptString(base, 0.15 + Math.random() * 0.25);
      setTimeout(function () {
        if (path && stageOk(2)) path.textContent = base;
      }, 80 + Math.random() * 200);
    }, 2200);
  }

  // 로그 한 줄 — stage 3 + 요소 생긴 뒤
  var liveLines = [
    "it knows you opened this tab",
    "someone is reading with you",
    "your cursor is too loud",
    "do not scroll to the bottom",
    "I was also a side project",
    "kill me properly next time",
    "404 is not death",
    "WakeAgain is listening",
    "signed: WakeAgain",
  ];
  setInterval(function () {
    if (document.body.classList.contains("is-haunting")) return;
    if (!stageOk(3)) return;
    var logLive = document.getElementById("logLive");
    if (!logLive) return;
    logLive.textContent = liveLines[Math.floor(Math.random() * liveLines.length)];
  }, 3400);

  if (whisper) {
    setInterval(function () {
      if (document.body.classList.contains("is-haunting")) return;
      if (!stageOk(2)) return;
      whisper.classList.toggle("whisper-on", Math.random() > 0.4);
    }, 1600);
  }

  var t2 = [
    "> soft lock detected_",
    "> user_id = unknown_",
    "> heartbeat from /dev/null_",
    "> please don't leave again_",
    "> …",
  ];
  var t2i = 0;
  if (terminalLine2) {
    setInterval(function () {
      if (document.body.classList.contains("is-haunting")) return;
      if (!stageOk(3) || terminalLine2.hidden) return;
      t2i = (t2i + 1) % t2.length;
      terminalLine2.textContent = t2[t2i];
    }, 4100);
  }

  // WakeAgain 은 의도적으로 섞어 무의식 각인 (도메인 URL 대신 워드마크)
  var words = [
    "버려진",
    "미완성",
    "FINAL2",
    "원혼",
    "kill -9",
    "나중에",
    "???",
    "살아있음",
    "WakeAgain",
    "WakeAgain",
    "wake again",
  ];
  function spawnWord() {
    if (!floatWords || document.body.classList.contains("is-haunting")) return;
    if (!stageOk(3)) return;
    if (Math.random() > 0.55) return;
    var el = document.createElement("span");
    el.className = "float-word";
    var w = words[Math.floor(Math.random() * words.length)];
    el.textContent = w;
    if (/wakeagain/i.test(w)) el.classList.add("float-word-brand");
    el.style.left = 5 + Math.random() * 85 + "%";
    el.style.top = 10 + Math.random() * 70 + "%";
    floatWords.appendChild(el);
    setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 2200);
  }
  setInterval(spawnWord, 2800);

  if (faceHint) {
    setInterval(function () {
      if (document.body.classList.contains("is-haunting")) return;
      if (!stageOk(3)) return;
      if (Math.random() > 0.12) return;
      faceHint.classList.add("face-on");
      setTimeout(function () {
        faceHint.classList.remove("face-on");
      }, 90 + Math.random() * 120);
    }, 5000);
  }

  function audio() {
    return window.__hauntAudio || null;
  }

  setInterval(function () {
    if (document.body.classList.contains("is-haunting")) return;
    if (document.body.classList.contains("is-ending")) return;
    if (document.body.classList.contains("diary-open")) return;
    if (!stageOk(2)) return;
    if (Math.random() > 0.12) return;
    document.body.classList.add("page-tick");
    var a = audio();
    if (a && a.staticBurst) a.staticBurst(70);
    setTimeout(function () {
      document.body.classList.remove("page-tick");
    }, 60 + Math.random() * 80);
  }, 4500);

  setInterval(function () {
    if (document.body.classList.contains("is-haunting")) return;
    if (!stageOk(2)) return;
    document.querySelectorAll(".glitch-text").forEach(function (el) {
      if (Math.random() > 0.5) el.classList.add("glitch-burst");
      else el.classList.remove("glitch-burst");
    });
  }, 900);

  function p2Decay() {
    if (typeof window.__hauntP2Decay === "function") return window.__hauntP2Decay();
    return parseInt(document.body.getAttribute("data-p2-decay") || "0", 10) || 0;
  }

  // stage2+ : decay 높을수록 속삭임·숨 더 자주
  setInterval(function () {
    if (document.body.classList.contains("is-haunting")) return;
    if (document.body.classList.contains("is-ending")) return;
    if (document.body.classList.contains("diary-open")) return;
    if (!stageOk(2)) return;
    var d = p2Decay();
    if (d < 2 && !stageOk(3)) return;
    var chance = d >= 5 ? 0.45 : d >= 3 ? 0.32 : 0.2;
    if (Math.random() > chance) return;
    var a = audio();
    if (!a) return;
    if (Math.random() > 0.5 && a.whisper) a.whisper();
    else if (a.breath) a.breath();
  }, 9000);

  // decay 3+: 블랙아웃 플래시 (높을수록 자주)
  setInterval(function () {
    if (document.body.classList.contains("is-haunting")) return;
    if (document.body.classList.contains("is-ending")) return;
    if (document.body.classList.contains("diary-open")) return;
    if (!stageOk(2)) return;
    var d = p2Decay();
    if (d < 3) return;
    if (Math.random() > (d >= 5 ? 0.22 : 0.1)) return;
    document.body.classList.add("horror-blackout");
    var a = audio();
    if (a && a.sting) a.sting("soft");
    setTimeout(function () {
      document.body.classList.remove("horror-blackout");
    }, 70 + Math.random() * 90);
  }, 12000);

  // decay 2+: 가장자리 맥박
  setInterval(function () {
    if (!stageOk(2) || document.body.classList.contains("is-haunting")) return;
    if (document.body.classList.contains("diary-open")) return;
    var d = p2Decay();
    if (d < 2) return;
    document.body.classList.add("horror-pulse-edge");
    setTimeout(function () {
      document.body.classList.remove("horror-pulse-edge");
    }, 500 + d * 40);
  }, 7000);

  // decay 올라갈 때 float word 더 자주
  setInterval(function () {
    if (!stageOk(2) || document.body.classList.contains("is-haunting")) return;
    if (document.body.classList.contains("diary-open")) return;
    var d = p2Decay();
    if (d < 2) return;
    if (Math.random() > 0.35 + d * 0.08) return;
    spawnWord();
  }, 2200);
})();
