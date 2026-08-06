/**
 * 유출된 개발자 일기
 * - mood 게이트 (3달→1달→오늘 천천히)
 * - 오늘 페이지: CRT/DOS 자동 타이핑 + 또독 키 소리
 *   · 사람 일기처럼 쓰이다가
 *   · 시스템이 가로채 스스로 이어 씀
 */
(function () {
  "use strict";

  var panel = document.getElementById("diaryPanel");
  var bodyEl = document.getElementById("diaryBody");
  var closeBtn = document.getElementById("diaryClose");
  var backdrop = document.getElementById("diaryBackdrop");
  var nextBtn = document.getElementById("diaryNext");
  var tabs = document.querySelectorAll(".diary-tab");
  var pages = document.querySelectorAll(".diary-page");
  var liveType = document.getElementById("diaryLiveType");
  var cursorLine = document.getElementById("diaryCursorLine");
  var termStatus = document.getElementById("diaryTermStatus");
  var sheet = panel ? panel.querySelector(".diary-sheet") : null;

  var page = 0;
  var unlocked = 0;
  var discovered = false;
  var reading = false;
  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var typeToken = 0; // cancel in-flight typing
  var todayDone = false;

  window.__hauntDiaryBoost = 1;
  window.__hauntDiaryDiscovered = false;
  window.__hauntDiaryPage = 0;

  /** 오늘 타이핑 시퀀스 — diary-stories.js 세션 변형 */
  function getTodaySeq() {
    if (window.__hauntDiaryStories && window.__hauntDiaryStories.todaySeq) {
      return window.__hauntDiaryStories.todaySeq;
    }
    return [
      { kind: "status", text: "> open dev_journal.txt — append mode_", delay: 400 },
      {
        kind: "p",
        className: "diary-human diary-last",
        text: "누군가 이 페이지에 접속했다면… 제발 내 코드를 꺼주",
        cps: 16,
      },
      { kind: "pause", ms: 700 },
      {
        kind: "status",
        text: "> INPUT HIJACK — writer_process attached_",
        delay: 200,
        beep: true,
      },
      {
        kind: "p",
        className: "diary-break diary-system",
        text: "바직— ████ process_not_dead ████",
        cps: 26,
        system: true,
        hardKeys: true,
      },
    ];
  }

  function audio() {
    return window.__hauntAudio || null;
  }

  function clickForChar(ch, hard) {
    var a = audio();
    if (!a || !a.typeClick) return;
    if (ch === "\n") a.typeClick("enter");
    else if (ch === " " || ch === "\t") a.typeClick("space");
    else if (hard) a.typeClick("hard");
    else if (/[a-zA-Z0-9가-힣]/.test(ch)) a.typeClick(Math.random() > 0.85 ? "hard" : "mid");
    else a.typeClick("soft");
  }

  function setBoost() {
    var b = 1;
    if (discovered) b = 1.2;
    if (unlocked >= 1) b = 1.45;
    if (unlocked >= 2) b = 1.85;
    if (page >= 2 && unlocked >= 2) b = 2.4;
    if (reading) b *= 1.15;
    if (page === 2 && !todayDone) b *= 1.1;
    window.__hauntDiaryBoost = b;
    window.__hauntDiaryPage = page;
    window.__hauntDiaryDiscovered = discovered;
    document.body.classList.toggle("diary-open", reading);
    document.body.classList.toggle("diary-found", discovered);
    document.body.classList.toggle("diary-typing", page === 2 && reading && !todayDone);
    document.dispatchEvent(
      new CustomEvent("haunt-diary", {
        detail: {
          discovered: discovered,
          page: page,
          unlocked: unlocked,
          boost: b,
          typing: page === 2 && !todayDone,
        },
      })
    );
  }

  function stopTyping() {
    typeToken++;
    if (cursorLine) cursorLine.hidden = true;
    document.body.classList.remove("diary-typing");
  }

  function wait(ms, token) {
    return new Promise(function (resolve) {
      setTimeout(function () {
        resolve(token === typeToken);
      }, ms);
    });
  }

  function typeString(el, text, opts, token) {
    opts = opts || {};
    var cps = opts.cps || 20;
    var hard = !!opts.hardKeys;
    var i = 0;
    return new Promise(function (resolve) {
      function step() {
        if (token !== typeToken) {
          resolve(false);
          return;
        }
        if (i >= text.length) {
          resolve(true);
          return;
        }
        var ch = text.charAt(i);
        el.textContent += ch;
        i++;
        clickForChar(ch, hard);
        // 스크롤 따라가기
        if (bodyEl) bodyEl.scrollTop = bodyEl.scrollHeight;
        var base = 1000 / cps;
        var jitter = (Math.random() - 0.4) * base * 0.5;
        var extra = 0;
        if (ch === "." || ch === "…" || ch === "。") extra = 120 + Math.random() * 180;
        if (ch === "," || ch === "，") extra = 40;
        if (ch === " " && Math.random() > 0.9) extra = 60;
        if (reduced) {
          el.textContent = text;
          resolve(true);
          return;
        }
        setTimeout(step, Math.max(18, base + jitter + extra));
      }
      step();
    });
  }

  async function runTodayTyping(token) {
    if (!liveType) return;
    liveType.innerHTML = "";
    todayDone = false;
    if (cursorLine) cursorLine.hidden = false;
    if (sheet) sheet.classList.add("is-terminal");
    if (nextBtn) {
      nextBtn.disabled = true;
      nextBtn.textContent = "입력 중…";
    }

    var a = audio();
    if (a) {
      try {
        a.unlock();
        if (a.termBeep) a.termBeep(660);
      } catch (e) {}
    }

    var TODAY_SEQ = getTodaySeq();
    // 스토리 메타를 상태줄에 한 번 더
    if (window.__hauntDiaryStories && window.__hauntDiaryStories.current) {
      var st = window.__hauntDiaryStories.current;
      if (window.console && /[?&]debug=1/.test(location.search || "")) {
        console.log("[diary] typing story #" + st.id, st.title);
      }
    }

    for (var s = 0; s < TODAY_SEQ.length; s++) {
      if (token !== typeToken) return;
      var step = TODAY_SEQ[s];
      var ok = true;

      if (step.kind === "pause") {
        ok = await wait(step.ms || 500, token);
        if (!ok) return;
        continue;
      }

      if (step.kind === "status") {
        if (termStatus) {
          termStatus.textContent = step.text;
          termStatus.classList.add("is-flash");
          setTimeout(function () {
            if (termStatus) termStatus.classList.remove("is-flash");
          }, 200);
        }
        if (step.beep && a && a.termBeep) a.termBeep(s % 2 ? 990 : 770);
        else clickForChar(">", true);
        ok = await wait(step.delay || 350, token);
        if (!ok) return;
        continue;
      }

      if (step.kind === "p") {
        var p = document.createElement("p");
        p.className = step.className || "";
        if (step.system) p.classList.add("is-system");
        liveType.appendChild(p);
        var caret = document.createElement("span");
        caret.className = "diary-inline-caret";
        caret.textContent = "█";
        p.appendChild(caret);
        // type into a text node before caret
        var textNode = document.createTextNode("");
        p.insertBefore(textNode, caret);

        // custom type into text node
        var text = step.text;
        var cps = step.cps || 18;
        var hard = !!step.hardKeys;
        var i = 0;
        await new Promise(function (resolve) {
          function tick() {
            if (token !== typeToken) {
              resolve(false);
              return;
            }
            if (reduced) {
              textNode.textContent = text;
              if (caret.parentNode) caret.parentNode.removeChild(caret);
              resolve(true);
              return;
            }
            if (i >= text.length) {
              if (caret.parentNode) caret.parentNode.removeChild(caret);
              resolve(true);
              return;
            }
            var ch = text.charAt(i);
            textNode.textContent += ch;
            i++;
            clickForChar(ch, hard || step.system);
            if (bodyEl) bodyEl.scrollTop = bodyEl.scrollHeight;
            var base = 1000 / cps;
            var jitter = (Math.random() - 0.35) * base * 0.55;
            var extra = 0;
            if (ch === "." || ch === "…") extra = 140 + Math.random() * 160;
            if (ch === ",") extra = 50;
            // 시스템 구간은 더 기계적·균일
            if (step.system) {
              base *= 0.85;
              jitter *= 0.4;
            }
            setTimeout(tick, Math.max(16, base + jitter + extra));
          }
          tick();
        });
        if (token !== typeToken) return;
        ok = await wait(step.system ? 280 : 420, token);
        if (!ok) return;
      }
    }

    if (token !== typeToken) return;
    todayDone = true;
    if (cursorLine) cursorLine.hidden = true;
    document.body.classList.remove("diary-typing");
    if (nextBtn) {
      nextBtn.disabled = false;
      nextBtn.textContent = "닫기";
      nextBtn.dataset.mode = "close";
    }
    if (a && a.termBeep) a.termBeep(440);
    setBoost();
  }

  function showPage(i) {
    page = Math.max(0, Math.min(2, i));
    stopTyping();

    pages.forEach(function (p) {
      var idx = parseInt(p.getAttribute("data-page"), 10);
      var on = idx === page;
      p.hidden = !on;
      p.classList.toggle("is-on", on);
    });
    tabs.forEach(function (t) {
      var idx = parseInt(t.getAttribute("data-diary-page"), 10);
      t.classList.toggle("is-on", idx === page);
      t.disabled = idx > unlocked;
    });

    if (sheet) {
      sheet.classList.toggle("is-terminal", page === 2);
    }

    if (nextBtn) {
      nextBtn.disabled = false;
      if (page >= 2) {
        if (todayDone) {
          nextBtn.textContent = "닫기";
          nextBtn.dataset.mode = "close";
        } else {
          nextBtn.textContent = "입력 중…";
          nextBtn.dataset.mode = "close";
          nextBtn.disabled = true;
        }
      } else if (page >= unlocked) {
        nextBtn.textContent = "다음 페이지 →";
        nextBtn.dataset.mode = "unlock";
      } else {
        nextBtn.textContent = "다음 페이지 →";
        nextBtn.dataset.mode = "next";
      }
    }

    if (page === 2) {
      document.body.classList.add("diary-finale");
      var tok = typeToken;
      // 재방문 시 이미 끝난 경우 즉시 전체 표시
      if (todayDone && liveType && liveType.childNodes.length) {
        if (nextBtn) {
          nextBtn.disabled = false;
          nextBtn.textContent = "닫기";
        }
      } else {
        // 약간의 딜레이 후 타이핑 시작 (단말 켜지는 느낌)
        setTimeout(function () {
          if (tok !== typeToken) return;
          runTodayTyping(typeToken);
        }, reduced ? 0 : 450);
      }
    } else if (sheet) {
      sheet.classList.remove("is-terminal");
    }

    setBoost();
  }

  /** body 에 걸린 filter/transform 이상현상 — fixed 일기 패널 붕괴 원인 */
  function clearBodyLayoutHazards() {
    var b = document.body;
    // anom-* / page-tick 전부 제거 (목록 누락 방지)
    var drop = [];
    for (var i = 0; i < b.classList.length; i++) {
      var c = b.classList[i];
      if (c === "page-tick" || c.indexOf("anom-") === 0) drop.push(c);
    }
    for (var j = 0; j < drop.length; j++) b.classList.remove(drop[j]);
    // CSS 애니메이션이 filter 를 잡고 있으면 !important 규칙보다 우선함 → 강제 취소
    try {
      if (typeof b.getAnimations === "function") {
        b.getAnimations().forEach(function (a) {
          try {
            a.cancel();
          } catch (e1) {}
        });
      }
      if (document.documentElement && document.documentElement.getAnimations) {
        document.documentElement.getAnimations().forEach(function (a) {
          try {
            a.cancel();
          } catch (e2) {}
        });
      }
    } catch (e3) {}
    // 애니메이션 중간 filter 보간값까지 즉시 차단
    try {
      b.style.setProperty("filter", "none", "important");
      b.style.setProperty("transform", "none", "important");
      b.style.setProperty("animation", "none", "important");
      b.style.removeProperty("--anom-hue");
    } catch (e) {
      b.style.filter = "none";
      b.style.transform = "none";
    }
  }

  function releaseBodyLayoutLock() {
    var b = document.body;
    try {
      b.style.removeProperty("filter");
      b.style.removeProperty("transform");
      b.style.removeProperty("animation");
    } catch (e) {
      b.style.filter = "";
      b.style.transform = "";
      b.style.animation = "";
    }
  }

  function openDiary() {
    if (!panel) return;
    discovered = true;
    // 시간 힌트 중단 (아래 scheduleFindHints 가 심어 둔 타이머)
    if (typeof clearFindHints === "function") {
      try {
        clearFindHints();
      } catch (e) {}
    }
    reading = true;
    // 열기 직전: body layout 위험 클래스 제거 (filter/transform → fixed 깨짐)
    clearBodyLayoutHazards();
    panel.hidden = false;
    panel.setAttribute("aria-hidden", "false");
    document.body.classList.add("diary-open");
    if (panel.style) {
      panel.style.display = "";
      panel.style.position = "fixed";
      panel.style.inset = "0";
      panel.style.zIndex = "200";
      panel.style.filter = "none";
      panel.style.transform = "none";
    }
    if (sheet) {
      sheet.style.opacity = "1";
      sheet.style.filter = "none";
      sheet.style.transform = "";
    }
    if (audio()) {
      try {
        audio().unlock();
        if (audio().breath && page === 0) audio().breath();
        else if (audio().pulse) audio().pulse(page >= 2 ? "heavy" : page === 1 ? "mid" : "soft");
      } catch (e) {}
    }
    showPage(page);
    setBoost();
  }

  function closeDiary() {
    if (!panel) return;
    // 타이핑 중 닫으면 중단 (다시 열면 이어쓰기/재시작)
    if (page === 2 && !todayDone) {
      // 부분 입력이라도 유지 — 다시 열면 처음부터 재연출
      stopTyping();
      if (liveType) liveType.innerHTML = "";
    } else {
      stopTyping();
    }
    reading = false;
    panel.hidden = true;
    panel.setAttribute("aria-hidden", "true");
    document.body.classList.remove("diary-open", "diary-typing");
    releaseBodyLayoutLock();
    if (sheet) sheet.classList.remove("is-terminal");
    setBoost();
  }

  function unlockNext() {
    // 페이지 전환 시 mood-dim 등 body 스타일 바뀌어도 fixed 유지
    clearBodyLayoutHazards();
    document.body.classList.add("diary-open");
    // 오디오 실패해도 페이지 넘김은 반드시 진행
    try {
      if (audio()) {
        audio().unlock();
        if (page === 0) audio().pulse("soft");
        else if (page === 1) audio().pulse("mid");
      }
    } catch (e) {}
    if (unlocked < 2) {
      unlocked += 1;
      showPage(unlocked);
    } else {
      showPage(Math.min(page + 1, 2));
    }
    // 시트 다시 보이게 보장 (CSS filter 글리치 대비)
    if (sheet) {
      sheet.style.transform = "";
      sheet.style.opacity = "1";
      sheet.style.filter = "none";
    }
    if (panel) {
      panel.hidden = false;
      panel.style.display = "";
      panel.style.position = "fixed";
      panel.style.inset = "0";
      panel.style.zIndex = "200";
      panel.style.filter = "none";
      panel.style.transform = "none";
    }
  }

  /**
   * 세션마다 발견 경로 1개만 활성 (스크롤 제거 · 21종 · 쉽게 안 찾히게)
   * 주소창 Find the diary = 호기심만
   */
  var FIND_PATHS = [
    "nav", "chip", "footer", "logo", "wip", "branch", "todo", "docs", "stub",
    "badge", "title", "caret", "freehold", "team", "fixme", "features",
    "skeleton", "readme", "console", "fakeurl", "type"
  ];

  var PATH_META = {
    nav: { hint: "nav ?" },
    chip: { hint: "camouflaged file" },
    footer: { hint: "footer dot" },
    logo: { hint: "logo double-click" },
    wip: { hint: "footer beta" },
    branch: { hint: "footer version" },
    todo: { hint: "Pricing pill" },
    docs: { hint: "Docs pill" },
    stub: { hint: "nav micro-dot" },
    badge: { hint: "hero badge" },
    title: { hint: "title triple-click" },
    caret: { hint: "under headline" },
    freehold: { hint: "hold Free 2s" },
    team: { hint: "Team card" },
    fixme: { hint: "fine print under plans" },
    features: { hint: "Features label" },
    skeleton: { hint: "monitor corner" },
    readme: { hint: "last deploy line" },
    console: { hint: "ship later" },
    fakeurl: { hint: "fake address bar" },
    type: { hint: "type diary/journal" }
  };

  function pickFindPath() {
    try {
      var forced = /[?&]path=([a-z]+)/.exec(location.search || "");
      if (forced && FIND_PATHS.indexOf(forced[1]) !== -1) {
        sessionStorage.setItem("haunt_diary_path", forced[1]);
        return forced[1];
      }
      var saved = sessionStorage.getItem("haunt_diary_path");
      if (saved && FIND_PATHS.indexOf(saved) !== -1) return saved;
      var pick = FIND_PATHS[(Math.random() * FIND_PATHS.length) | 0];
      sessionStorage.setItem("haunt_diary_path", pick);
      return pick;
    } catch (e) {
      return FIND_PATHS[(Math.random() * FIND_PATHS.length) | 0];
    }
  }

  var findPath = pickFindPath();
  window.__hauntDiaryFindPath = findPath;
  document.body.setAttribute("data-find-path", findPath);

  function wireHotspots() {
    var nodes = document.querySelectorAll("[data-find]");
    nodes.forEach(function (el) {
      var id = el.getAttribute("data-find");
      var active = id === findPath;
      el.classList.toggle("find-active", active);
      el.classList.toggle("find-dormant", !active);

      if (!active) {
        if (id === "nav" || id === "chip" || id === "footer") {
          el.classList.add("diary-path-off");
          el.setAttribute("aria-hidden", "true");
          if (el.tagName === "BUTTON") el.disabled = true;
        }
        return;
      }

      el.classList.add("find-hard");
      el.classList.remove("diary-path-off");
      if (el.tagName === "BUTTON") el.disabled = false;

      if (id === "logo") {
        var clicks = 0;
        var t = null;
        el.addEventListener("click", function (e) {
          e.preventDefault();
          clicks++;
          clearTimeout(t);
          t = setTimeout(function () { clicks = 0; }, 450);
          if (clicks >= 2) { clicks = 0; openDiary(); }
        });
        return;
      }

      if (id === "title") {
        var n = 0;
        var tt = null;
        el.addEventListener("click", function () {
          n++;
          clearTimeout(tt);
          tt = setTimeout(function () { n = 0; }, 600);
          if (n >= 3) { n = 0; openDiary(); }
        });
        return;
      }

      if (id === "freehold") {
        var holdTimer = null;
        var armed = false;
        function clearHold() {
          if (holdTimer) clearTimeout(holdTimer);
          holdTimer = null;
          armed = false;
          el.classList.remove("find-holding");
        }
        el.addEventListener("pointerdown", function (e) {
          e.preventDefault();
          armed = true;
          el.classList.add("find-holding");
          holdTimer = setTimeout(function () {
            if (armed) openDiary();
            clearHold();
          }, 2000);
        });
        el.addEventListener("pointerup", clearHold);
        el.addEventListener("pointerleave", clearHold);
        el.addEventListener("pointercancel", clearHold);
        return;
      }

      el.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        openDiary();
      });
    });

    if (findPath === "type") {
      var buf = "";
      document.addEventListener("keydown", function (e) {
        if (discovered || reading) return;
        if (e.metaKey || e.ctrlKey || e.altKey) return;
        if (e.key === "Escape") return;
        if (e.key.length === 1 && /[a-zA-Z]/.test(e.key)) {
          buf = (buf + e.key.toLowerCase()).slice(-12);
          if (buf.indexOf("diary") !== -1 || buf.indexOf("journal") !== -1) {
            buf = "";
            openDiary();
          }
        }
      });
    }
  }

  wireHotspots();

  if (closeBtn) closeBtn.addEventListener("click", closeDiary);
  if (backdrop) backdrop.addEventListener("click", closeDiary);

  if (nextBtn) {
    nextBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (nextBtn.disabled) return;
      try {
        if (nextBtn.dataset.mode === "close") {
          closeDiary();
          return;
        }
        if (page < unlocked) showPage(page + 1);
        else unlockNext();
      } catch (err) {
        if (window.console) console.warn("[diary] next failed", err);
        // 폴백: 최소한 페이지 인덱스만 진행
        try {
          if (unlocked < 2) unlocked += 1;
          showPage(Math.min(unlocked, 2));
        } catch (e2) {}
      }
    });
  }

  tabs.forEach(function (t) {
    t.addEventListener("click", function () {
      if (t.disabled) return;
      var idx = parseInt(t.getAttribute("data-diary-page"), 10);
      showPage(idx);
    });
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && reading) {
      if (!document.body.classList.contains("is-haunting")) closeDiary();
    }
  });

  if (window.console && /[?&]debug=1/.test(location.search || "")) {
    console.log(
      "[diary] find path:",
      findPath,
      PATH_META[findPath] && PATH_META[findPath].hint,
      "/",
      FIND_PATHS.length
    );
  }

  document.dispatchEvent(
    new CustomEvent("haunt-find-path", {
      detail: {
        path: findPath,
        meta: PATH_META[findPath],
        paths: FIND_PATHS.slice(),
      },
    })
  );

  /**
   * 시간 힌트 — 1분 / 2분 / 3분 각 1개
   * 그 뒤에도 못 찾으면 "보지 말라" 마무리
   * (일기 열면 즉시 중단)
   */
  var FIND_LADDER = {
    nav: [
      "위쪽 어딘가… 거의 안 보이는 기호가 있다.",
      "메뉴 줄 오른쪽 끝. 배경과 거의 같은 색.",
      "상단 내비 맨 오른쪽 — 희미한 「?」를 눌러 봐.",
    ],
    chip: [
      "히어로 아래, 파일처럼 생긴 잔여물이 있다.",
      "점선 박스 말고… 작은 주석 한 줄. txt 확장자.",
      "「dev_journal.txt」 글자를 클릭해. (아이콘 없을 수 있음)",
    ],
    footer: [
      "페이지 맨 아래를 의심해 봐.",
      "푸터 저작권 줄 옆, 문장보다 작은 무언가.",
      "푸터의 「·」 점 — 그게 링크다.",
    ],
    logo: [
      "브랜드 이름이 그냥 로고가 아닐 수도.",
      "한 번으로는 부족하다. 빠르게.",
      "왼쪽 위 「Stasis」 로고를 더블클릭.",
    ],
    wip: [
      "맨 아래 푸터에 작은 라벨이 있다.",
      "버전 옆… beta 같은 단어.",
      "푸터의 「beta」 글자를 클릭.",
    ],
    branch: [
      "푸터 한구석 버전 문자열.",
      "v0. 으로 시작하는 숫자.",
      "푸터 「v0.9.2」 를 클릭.",
    ],
    todo: [
      "가운데 네비 필 메뉴.",
      "Pricing 항목.",
      "「Pricing」 을 클릭.",
    ],
    docs: [
      "가운데 네비 필 메뉴.",
      "Docs 항목.",
      "「Docs」 를 클릭.",
    ],
    stub: [
      "네비 필 끝 — 거의 안 보이는 점.",
      "Pricing · Docs 옆 여백.",
      "필 메뉴 오른쪽 끝 작은 점을 클릭.",
    ],
    badge: [
      "히어로 위 작은 뱃지.",
      "Uptime · Alerts 쪽.",
      "히어로 상단 뱃지를 클릭.",
    ],
    title: [
      "큰 제목이 수상하다.",
      "한 번, 두 번… 세 번.",
      "메인 타이틀을 빠르게 3번 클릭.",
    ],
    caret: [
      "제목 바로 아래 빈 공간.",
      "거의 투명한 한 줄.",
      "헤드라인 아래 희미한 줄을 클릭.",
    ],
    freehold: [
      "버튼은 눌리는 것만이 전부가 아니다.",
      "Free 요금 카드 — 잠깐 누르고 있어 봐.",
      "「Free」 카드를 2초 동안 길게 누름.",
    ],
    team: [
      "요금 카드 중 Team.",
      "사람 아이콘이 있는 카드.",
      "「Team」 카드를 클릭.",
    ],
    fixme: [
      "요금 카드 아래 작은 문장.",
      "No credit card… 같은 한 줄.",
      "플랜 아래 미세 카피를 클릭.",
    ],
    features: [
      "Features 카드 상단 라벨.",
      "FEATURES 라고 작게 적힌 줄.",
      "Features 카드 위쪽 라벨 클릭.",
    ],
    skeleton: [
      "다크 모니터 미리보기 구석.",
      "대시보드 프레임 오른쪽 아래.",
      "UI section 모니터 우측 하단을 클릭.",
    ],
    readme: [
      "어두운 배너 아래 작은 서명.",
      "last deploy 근처.",
      "「— Stasis · last deploy: today」 클릭.",
    ],
    console: [
      "페이지 아래 거의 안 보이는 코드 한 줄.",
      "ship later.",
      "「console.log('ship later');」 클릭.",
    ],
    fakeurl: [
      "진짜 브라우저 주소창이 아닐 수 있다.",
      "화면 맨 위, 가짜 크롬 바.",
      "상단 가짜 주소창(URL 입력칸)을 클릭.",
    ],
    type: [
      "클릭이 아닐 수도 있다. 입력.",
      "영어 단어. 일기와 관련된.",
      "키보드로 diary 또는 journal 을 쳐 봐.",
    ],
  };

  var toast = document.getElementById("findHintToast");
  var toastTag = document.getElementById("findHintTag");
  var toastText = document.getElementById("findHintText");
  var toastClose = document.getElementById("findHintClose");
  var hintTimers = [];
  var hintHideTimer = null;

  function clearFindHints() {
    for (var i = 0; i < hintTimers.length; i++) clearTimeout(hintTimers[i]);
    hintTimers = [];
    if (hintHideTimer) clearTimeout(hintHideTimer);
    hintHideTimer = null;
    if (toast) toast.hidden = true;
    document.body.classList.remove("find-hint-visible");
  }

  function showFindHint(level, message) {
    if (discovered || !toast || !toastText) return;
    if (toastTag) {
      toastTag.textContent = "HINT " + level + "/3";
      toastTag.classList.remove("is-end");
    }
    toastText.textContent = message;
    toast.hidden = false;
    document.body.classList.add("find-hint-visible");
    toast.classList.remove("is-out");
    toast.classList.add("is-in");
    if (hintHideTimer) clearTimeout(hintHideTimer);
    hintHideTimer = setTimeout(function () {
      if (!toast) return;
      toast.classList.remove("is-in");
      toast.classList.add("is-out");
      setTimeout(function () {
        if (toast && !discovered) toast.hidden = true;
        document.body.classList.remove("find-hint-visible");
      }, 400);
    }, 9000);
  }

  if (toastClose) {
    toastClose.addEventListener("click", function () {
      if (toast) toast.hidden = true;
      document.body.classList.remove("find-hint-visible");
    });
  }

  function scheduleFindHints() {
    clearFindHints();
    if (discovered) return;
    // 디버그 가속: ?hintfast=1 → 5s / 10s / 15s
    var fast = /[?&]hintfast=1/.test(location.search || "");
    var t1 = fast ? 5000 : 60000;
    var t2 = fast ? 10000 : 120000;
    var t3 = fast ? 15000 : 180000;

    var ladder = FIND_LADDER[findPath] || [
      "어딘가에 일기가 있다.",
      "클릭·홀드·더블클릭·타이핑을 의심.",
      "주소창 힌트와 페이지를 다시 훑어 봐.",
    ];

    hintTimers.push(
      setTimeout(function () {
        showFindHint(1, ladder[0] || "");
      }, t1)
    );
    hintTimers.push(
      setTimeout(function () {
        showFindHint(2, ladder[1] || "");
      }, t2)
    );
    hintTimers.push(
      setTimeout(function () {
        showFindHint(3, ladder[2] || "");
      }, t3)
    );
  }

  scheduleFindHints();

  // 제작자 전용: ?diary=1 즉시 오픈 / ?debug=1 경로 배지
  try {
    if (/[?&]diary=1/.test(location.search || "")) {
      setTimeout(function () {
        openDiary();
      }, 300);
    }
    if (/[?&]debug=1/.test(location.search || "") || localStorage.getItem("haunt_creator") === "1") {
      var badge = document.createElement("button");
      badge.type = "button";
      badge.className = "creator-pass";
      badge.innerHTML =
        "<strong>CREATOR</strong> path: <code>" +
        findPath +
        "</code> · 클릭=일기";
      badge.title = "제작자 패스 — 클릭하면 일기 오픈";
      badge.addEventListener("click", function () {
        openDiary();
      });
      document.body.appendChild(badge);
      // 한 번 켜면 로컬에 기억 (일반 공유 URL에는 안 붙음)
      if (/[?&]creator=1/.test(location.search || "")) {
        localStorage.setItem("haunt_creator", "1");
      }
    }
  } catch (e) {}

  setBoost();
})();
