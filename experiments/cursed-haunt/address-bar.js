/**
 * 주소창 눈속임
 * - 가짜 브라우저 크롬에 표시되는 URL 오염
 * - 같은 origin 경로 pushState / replaceState
 * - document.title 단계 동기화
 * - climax: WakeAgain 경로 암시 (실제 이탈은 선택)
 *
 * 리스너: haunt-stage, haunt-diary, body.is-haunting
 */
(function () {
  "use strict";

  var chrome = document.getElementById("fakeChrome");
  var urlText = document.getElementById("fakeUrlText");
  var urlLock = document.getElementById("fakeUrlLock");
  var tabTitle = document.getElementById("fakeTabTitle");
  var urlBar = document.getElementById("fakeUrlBar");

  if (!chrome || !urlText) return;

  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var debug = false;
  try {
    debug = /[?&]debug=1/.test(location.search || "");
  } catch (e) {}

  // 실제 브라우저 주소창에 넣을 수 있는 것: 같은 origin path 뿐
  var PATHS = {
    0: "/",
    1: "/draft",
    2: "/abandoned/mvp_final_FINAL2",
    3: "/process_not_dead",
    climax: "/wake-again",
  };

  // 가짜 크롬에 보이는 “풀 URL” (도메인은 눈속임)
  var FAKE_URLS = {
    0: "http://localhost:4173/",
    1: "http://localhost:4173/draft?wip=1",
    2: "https://stasis.app/abandoned/mvp_final_FINAL2",
    // 도메인 광고 대신 워드마크 각인
    3: "about:WakeAgain — process_not_dead",
    climax: "WakeAgain — you left this running",
  };

  var TITLES = {
    0: "Stasis — WIP (local)",
    1: "Stasis — WIP…",
    2: "Stasis? — abandoned",
    3: "WakeAgain · still running",
    climax: "WakeAgain — 당신이 버린 것",
  };

  // stage 2+ 깜빡임용 오염 문자열 (WakeAgain 글자 노출 비중↑)
  var POLLUTE = [
    "https://stasis.app/████/draft",
    "file:///C:/Users/…/abandoned/mvp.exe",
    "https://0.0.0.0:3847/still_listening",
    "WakeAgain",
    "WakeAgain — still listening",
    "about:blank#WakeAgain",
    "chrome://WakeAgain/please-stop",
    "https://stasis.app/draft?who=WakeAgain",
  ];

  // stage 0: 일기 찾기 전 주소창 힌트 (영어) — 세션 경로에 맞춰 일부 교체
  var FIND_HINTS_DEFAULT = [
    "http://localhost:4173/find-the-diary",
    "http://localhost:4173/?q=find+the+diary",
    "http://localhost:4173/#find-the-diary",
    "http://localhost:4173/dev_journal.txt — find the diary",
    "file:///~/projects/stasis/find-the-diary",
    "http://localhost:4173/wip#FIND_THE_DIARY",
  ];
  var FIND_HINTS = FIND_HINTS_DEFAULT.slice();
  var FIND_TITLES = [
    "Find the diary",
    "find the diary — Stasis WIP",
    "dev_journal.txt — find the diary",
  ];

  // 경로별 힌트 — 위치는 모호하게 (쉽게 안 찾히게)
  var PATH_HINTS = {
    nav: ["http://localhost:4173/find-the-diary#somewhere-above", "http://localhost:4173/?q=look+closer"],
    chip: ["http://localhost:4173/?q=leftover+file", "file:///~/projects/stasis/*.txt"],
    footer: ["http://localhost:4173/find-the-diary#below", "http://localhost:4173/?q=dot"],
    logo: ["http://localhost:4173/#brand", "http://localhost:4173/?q=double"],
    wip: ["http://localhost:4173/?q=not+shipped", "http://localhost:4173/#wip"],
    branch: ["http://localhost:4173/?q=feat/landing-v0", "http://localhost:4173/#git"],
    todo: ["http://localhost:4173/?q=TODO", "http://localhost:4173/#pricing"],
    docs: ["http://localhost:4173/?q=struck", "http://localhost:4173/#docs"],
    stub: ["http://localhost:4173/?q=ellipsis", "http://localhost:4173/#more"],
    badge: ["http://localhost:4173/?q=draft", "http://localhost:4173/#status"],
    title: ["http://localhost:4173/?q=headline", "http://localhost:4173/#triple"],
    caret: ["http://localhost:4173/?q=comment", "http://localhost:4173/#caret"],
    freehold: ["http://localhost:4173/?q=hold", "http://localhost:4173/#free"],
    team: ["http://localhost:4173/?q=delete-later", "http://localhost:4173/#team"],
    fixme: ["http://localhost:4173/?q=FIXME", "http://localhost:4173/#wire"],
    features: ["http://localhost:4173/?q=Features.tsx", "http://localhost:4173/#file"],
    skeleton: ["http://localhost:4173/?q=404", "http://localhost:4173/#screenshot"],
    readme: ["http://localhost:4173/?q=last+edit", "http://localhost:4173/#readme"],
    console: ["http://localhost:4173/?q=ship+later", "http://localhost:4173/#console"],
    fakeurl: ["http://localhost:4173/find-the-diary", "http://localhost:4173/#address-bar"],
    type: ["http://localhost:4173/?q=type+the+word", "http://localhost:4173/#keyboard"],
  };

  function applyFindPathHints(path) {
    var list = PATH_HINTS[path];
    if (!list || !list.length) {
      FIND_HINTS = FIND_HINTS_DEFAULT.slice();
      return;
    }
    // 경로 전용 + 공통 find-the-diary 섞기
    FIND_HINTS = list.concat([
      "http://localhost:4173/find-the-diary",
      "http://localhost:4173/wip#FIND_THE_DIARY",
    ]);
  }

  // diary.js 가 먼저/나중에 와도 동작
  if (window.__hauntDiaryFindPath) {
    applyFindPathHints(window.__hauntDiaryFindPath);
  }
  document.addEventListener("haunt-find-path", function (ev) {
    var p = ev && ev.detail && ev.detail.path;
    if (p) applyFindPathHints(p);
  });

  var currentStage = 0;
  var isClimax = false;
  var diaryFound = false;
  var lastPushed = null;
  var glitchTimer = null;
  var polluteTimer = null;
  var hintTimer = null;
  var hintIndex = 0;
  // replaceState 가 path 만 쓰면 ?path= ?p3= ?debug= ?summon= 이 증발함
  // → 이후 로드되는 climax-triggers / ending 등이 쿼리를 못 읽음
  var preservedSearch = location.search || "";
  var preservedHash = location.hash || "";

  function log() {
    if (debug && window.console) {
      console.log.apply(console, ["[address-bar]"].concat([].slice.call(arguments)));
    }
  }

  function setFakeDisplay(url, title, stageKey) {
    urlText.textContent = url;
    if (tabTitle) tabTitle.textContent = title;
    document.title = title;
    chrome.setAttribute("data-chrome-stage", String(stageKey === "climax" ? 4 : stageKey));
    if (urlLock) {
      // 이모지 대신 CSS 자물쇠 (허접 톤 제거)
      urlLock.textContent = "";
      if (stageKey === 0 || stageKey === 1) {
        urlLock.classList.remove("is-broken");
      } else {
        urlLock.classList.add("is-broken");
      }
    }
  }

  function syncPath(path) {
    if (!path || path === lastPushed) return;
    try {
      // 현재 파일 경로 유지(로컬 서버 index.html) + 가짜 경로 세그먼트
      // 로컬: / 또는 /index.html → pushState로 path만 바꿈 (새로고침 시 404 주의 → replace 위주)
      var base = location.pathname;
      // experiments serve root is cursed-haunt/, so relative paths work if we stay under /
      // Use history state without leaving index.html resolution: encode as query-like path
      // Safer for python -m http.server: use hash-free path under root; 404 on hard refresh is ok for ARG.
      var next = path;
      // If serving as /index.html, keep directory
      if (base.indexOf("index.html") !== -1) {
        next = base.replace(/index\.html$/, "") + path.replace(/^\//, "");
        if (next.slice(-1) === "/" && path === "/") next = base;
      }
      // 쿼리/해시 유지 — 제작·디버그·트리거 강제 파라미터가 사라지지 않게
      next = next + preservedSearch + preservedHash;
      history.replaceState({ hauntPath: path, stage: currentStage }, "", next);
      lastPushed = path;
      log("path", next);
    } catch (err) {
      log("path fail", err && err.message);
    }
  }

  function applyStage(n, force) {
    if (isClimax && !force) return;
    n = Math.max(0, Math.min(3, n | 0));
    if (!force && n < currentStage) return;
    currentStage = n;

    var key = n;
    setFakeDisplay(FAKE_URLS[key], TITLES[key], key);
    syncPath(PATHS[key]);

    chrome.classList.toggle("is-uneasy", n === 1);
    chrome.classList.toggle("is-corrupt", n === 2);
    chrome.classList.toggle("is-dread", n >= 3);
    chrome.classList.remove("is-climax");
    chrome.classList.toggle("is-hinting", n === 0 && !diaryFound);

    if (urlBar) {
      urlBar.classList.toggle("glitching", (n >= 2 || (n === 0 && !diaryFound)) && !reduced);
    }

    stopPollute();
    stopFindHint();
    if (n === 0 && !diaryFound) startFindHint();
    else if (n >= 2 && !reduced) startPollute(n);
    log("stage", n);
  }

  /** 일기 찾기 전: 주소창에 Find the diary 영어 힌트 순환 */
  function startFindHint() {
    stopFindHint();
    if (diaryFound || currentStage > 0 || isClimax) return;
    chrome.classList.add("is-hinting");
    var baseUrl = FAKE_URLS[0];
    var baseTitle = TITLES[0];
    var showHint = true;

    function tick() {
      if (diaryFound || currentStage > 0 || isClimax) {
        stopFindHint();
        return;
      }
      if (showHint) {
        var u = FIND_HINTS[hintIndex % FIND_HINTS.length];
        var t = FIND_TITLES[hintIndex % FIND_TITLES.length];
        hintIndex++;
        urlText.textContent = u;
        urlText.classList.add("url-flash", "url-hint");
        if (tabTitle) tabTitle.textContent = t;
        document.title = t;
        // 힌트 보이는 동안 짧게 유지 후 원래 URL로
        setTimeout(function () {
          if (diaryFound || currentStage > 0 || isClimax) return;
          urlText.classList.remove("url-flash");
          // 힌트 URL을 조금 더 오래 보여 주기 (읽히게)
        }, reduced ? 0 : 200);
      } else {
        urlText.textContent = baseUrl;
        urlText.classList.remove("url-flash", "url-hint");
        if (tabTitle) tabTitle.textContent = baseTitle;
        document.title = baseTitle;
      }
      showHint = !showHint;
    }

    // 첫 힌트는 곧 노출
    setTimeout(function () {
      if (!diaryFound && currentStage === 0) tick();
    }, reduced ? 800 : 2500);

    hintTimer = setInterval(tick, reduced ? 5000 : 4200);
  }

  function stopFindHint() {
    if (hintTimer) {
      clearInterval(hintTimer);
      hintTimer = null;
    }
    chrome.classList.remove("is-hinting");
    if (urlText) urlText.classList.remove("url-hint");
  }

  function onDiaryFound() {
    if (diaryFound) return;
    diaryFound = true;
    stopFindHint();
    // 찾은 직후: 주소가 일기 파일로 고정되는 연출
    if (currentStage <= 1 && !isClimax) {
      urlText.textContent = "http://localhost:4173/dev_journal.txt";
      urlText.classList.remove("url-hint");
      urlText.classList.add("url-flash");
      if (tabTitle) tabTitle.textContent = "dev_journal.txt";
      document.title = "dev_journal.txt — opened";
      setTimeout(function () {
        urlText.classList.remove("url-flash");
        if (currentStage === 0) {
          setFakeDisplay(FAKE_URLS[0], TITLES[0], 0);
        } else if (currentStage === 1) {
          setFakeDisplay(FAKE_URLS[1], TITLES[1], 1);
        }
      }, 1600);
    }
    log("diary found — stop find-hints");
  }

  function startPollute(n) {
    stopPollute();
    var base = FAKE_URLS[n] || FAKE_URLS[2];
    polluteTimer = setInterval(function () {
      if (isClimax || document.body.classList.contains("is-haunting")) return;
      if (Math.random() > 0.55) {
        var junk = POLLUTE[(Math.random() * POLLUTE.length) | 0];
        urlText.textContent = junk;
        urlText.classList.add("url-flash");
        setTimeout(function () {
          urlText.classList.remove("url-flash");
          if (!isClimax) urlText.textContent = base;
        }, reduced ? 0 : 120 + Math.random() * 200);
      }
      // title micro flicker
      if (n >= 3 && Math.random() > 0.7) {
        document.title = Math.random() > 0.5 ? TITLES[3] : "⚠️ still running";
        setTimeout(function () {
          if (!isClimax) document.title = TITLES[3];
        }, 180);
      }
    }, n >= 3 ? 2200 : 3800);
  }

  function stopPollute() {
    if (polluteTimer) {
      clearInterval(polluteTimer);
      polluteTimer = null;
    }
  }

  function enterClimax() {
    if (isClimax) return;
    isClimax = true;
    stopPollute();
    stopFindHint();
    setFakeDisplay(FAKE_URLS.climax, TITLES.climax, "climax");
    syncPath(PATHS.climax);
    chrome.classList.add("is-climax", "is-dread");
    chrome.classList.remove("is-uneasy", "is-corrupt");
    if (urlBar) urlBar.classList.add("glitching");
    // brief glitch cascade then settle
    if (!reduced) {
      var i = 0;
      glitchTimer = setInterval(function () {
        urlText.textContent = POLLUTE[i % POLLUTE.length];
        i++;
        if (i > 6) {
          clearInterval(glitchTimer);
          glitchTimer = null;
          urlText.textContent = FAKE_URLS.climax;
        }
      }, 90);
    }
    log("climax");
  }

  function exitClimax() {
    // 보스 연출 종료 후 최종 스테이지 유지
    isClimax = false;
    applyStage(Math.max(currentStage, 3), true);
  }

  // ---- events ----
  document.addEventListener("haunt-stage", function (ev) {
    var s = ev && ev.detail && typeof ev.detail.stage === "number" ? ev.detail.stage : 0;
    applyStage(s);
  });

  document.addEventListener("haunt-diary", function (ev) {
    var d = (ev && ev.detail) || {};
    if (d.discovered) onDiaryFound();
    // 일기 마지막 페이지 → URL도 한 단계 더 더럽히기
    if (d.page >= 2 && currentStage < 3) {
      if (currentStage <= 1) {
        urlText.textContent = "https://stasis.app/draft#dev_journal.txt";
        if (tabTitle) tabTitle.textContent = "dev_journal.txt — leaked";
      }
    }
    if (d.page >= 2 && !isClimax) {
      setTimeout(function () {
        if (!isClimax && currentStage >= 2) {
          urlText.textContent = "https://stasis.app/abandoned/…journal_leaked";
        }
      }, 400);
    }
  });

  // body class watcher for haunt boss
  var mo = new MutationObserver(function () {
    if (document.body.classList.contains("is-haunting")) {
      enterClimax();
    } else if (isClimax) {
      exitClimax();
    }
  });
  mo.observe(document.body, { attributes: true, attributeFilter: ["class"] });

  // 초기
  applyStage(0, true);

  // 외부 훅
  window.__hauntAddressBar = {
    setStage: applyStage,
    climax: enterClimax,
    getStage: function () {
      return currentStage;
    },
  };

  // popstate: 뒤로가기 시 가짜 표시만 맞추기 (실제 스테이지는 유지)
  window.addEventListener("popstate", function (ev) {
    var st = ev.state && typeof ev.state.stage === "number" ? ev.state.stage : currentStage;
    if (!isClimax) {
      setFakeDisplay(
        FAKE_URLS[st] || FAKE_URLS[0],
        TITLES[st] || TITLES[0],
        st
      );
    }
  });
})();
