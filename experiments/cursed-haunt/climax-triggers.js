/**
 * 2페이즈 → 3페이즈 게이트 트리거
 * - 약 20종 풀, 세션마다 1개만 활성
 * - phase2Ready: 일기 발견 + stage ≥ 2
 * - 발동 시 클라이맥스가 아니라 **3페이즈 진입** (클라이맥스는 phase3-triggers.js)
 * - 제작자: ?summon=1 · ?debug=1 · ?creator=1 · Shift+Alt+3
 */
(function () {
  "use strict";

  function stage() {
    if (typeof window.__hauntStage === "function") return window.__hauntStage();
    return parseInt(document.body.getAttribute("data-stage") || "0", 10) || 0;
  }

  function phase2Ready() {
    if (!window.__hauntDiaryDiscovered) return false;
    return stage() >= 2;
  }

  function busy() {
    return (
      document.body.classList.contains("is-haunting") ||
      document.body.classList.contains("is-ending") ||
      /* 일기 읽는 중 클라이맥스 끼어들기 방지 */
      document.body.classList.contains("diary-open")
    );
  }

  function enterPhase3() {
    if (window.__hauntPhase3Active) return true;
    window.__hauntPhase3Active = true;
    try {
      sessionStorage.setItem("haunt_phase3", "1");
    } catch (e) {}
    document.body.classList.add("phase-3-active");
    document.body.setAttribute("data-game-phase", "3");
    // stage/mood 최대 끌어올림 — 3페이즈 비주얼
    try {
      if (typeof window.__hauntSetStage === "function") window.__hauntSetStage(3);
      if (typeof window.__hauntSetMood === "function") window.__hauntSetMood(4);
      if (typeof window.__hauntSetP2Decay === "function") window.__hauntSetP2Decay(4);
      else {
        document.body.setAttribute("data-p2-decay", "4");
        document.body.classList.add("p2-d4");
      }
    } catch (e2) {}
    try {
      document.dispatchEvent(
        new CustomEvent("haunt-phase3", {
          detail: { at: Date.now(), from: "p2-trigger", trigger: active && active.id },
        })
      );
    } catch (e3) {}
    // 짧은 진입 연출
    document.body.classList.add("phase3-enter");
    setTimeout(function () {
      document.body.classList.remove("phase3-enter");
    }, 1600);
    try {
      var au = window.__hauntAudio;
      if (au) {
        if (au.rumble) au.rumble(1.4);
        if (au.sting) setTimeout(function () { au.sting("blood"); }, 200);
      }
    } catch (e4) {}
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[phase] entered phase 3 via", active && active.id);
    }
    return true;
  }

  function summon() {
    if (typeof window.__hauntSummon === "function") {
      window.__hauntSummon();
      return true;
    }
    return false;
  }

  function trySummon() {
    // 하위 호환: 프리패스는 클라이맥스 직행 허용
    if (busy()) return;
    if (!window.__hauntCreatorPass) return;
    window.__hauntDiaryDiscovered = true;
    try {
      if (typeof window.__hauntSetStage === "function") window.__hauntSetStage(3);
      if (typeof window.__hauntSetMood === "function") window.__hauntSetMood(4);
    } catch (e) {}
    summon();
  }

  function tryEnterPhase3Strict() {
    if (busy()) return;
    if (!phase2Ready()) return;
    if (window.__hauntPhase3Active) return;
    enterPhase3();
  }

  /**
   * 2페이즈 게이트 트리거 20 — 클린 SaaS 레이아웃 기준
   * (WIP 띠/caret/TODO 등 클린 전용 요소 사용 금지)
   * 대상: 로고·플랜카드·제목·카드·푸터·가짜주소창·경로·시계·배지 등
   */
  function p2Only(fn) {
    return function () {
      if (!phase2Ready() || busy() || window.__hauntPhase3Active) return;
      return fn.apply(this, arguments);
    };
  }

  function armHold(el, ms, done, holdClass) {
    if (!el) return false;
    var t = null;
    var cls = holdClass || "climax-holding";
    function clear() {
      if (t) clearTimeout(t);
      t = null;
      el.classList.remove(cls);
    }
    el.addEventListener("pointerdown", function (e) {
      if (!phase2Ready() || busy() || window.__hauntPhase3Active) return;
      if (e.button != null && e.button !== 0) return;
      el.classList.add(cls);
      t = setTimeout(function () {
        clear();
        done();
      }, ms);
    });
    el.addEventListener("pointerup", clear);
    el.addEventListener("pointerleave", clear);
    el.addEventListener("pointercancel", clear);
    return true;
  }

  function armClicks(el, need, windowMs, done) {
    if (!el) return false;
    var n = 0;
    var reset = null;
    el.addEventListener("click", function (e) {
      if (!phase2Ready() || busy() || window.__hauntPhase3Active) return;
      n++;
      clearTimeout(reset);
      reset = setTimeout(function () {
        n = 0;
      }, windowMs || 2200);
      if (n >= need) {
        n = 0;
        done();
      }
    });
    return true;
  }

  var TRIGGERS = [
    {
      id: "hold_free",
      hint: "Free 카드 길게",
      arm: function (done) {
        var btn =
          document.getElementById("planFree") ||
          document.querySelector(".plan-card.is-on") ||
          document.querySelector("[data-fake='2']");
        armHold(btn, 2500, done);
      },
    },
    {
      id: "triple_logo",
      hint: "로고 3연타",
      arm: function (done) {
        armClicks(document.getElementById("topRec"), 3, 800, done);
      },
    },
    {
      id: "type_kill",
      hint: "키보드 kill / wake",
      arm: function (done) {
        var buf = "";
        document.addEventListener("keydown", function (e) {
          if (!phase2Ready() || busy() || window.__hauntPhase3Active) return;
          if (e.metaKey || e.ctrlKey || e.altKey) return;
          if (e.key.length !== 1 || !/[a-zA-Z]/.test(e.key)) return;
          buf = (buf + e.key.toLowerCase()).slice(-8);
          if (buf.indexOf("kill") !== -1 || buf.indexOf("wake") !== -1) {
            buf = "";
            done();
          }
        });
      },
    },
    {
      id: "deep_hold",
      hint: "맨 아래 스크롤 유지",
      arm: function (done) {
        var hold = 0;
        var last = 0;
        setInterval(function () {
          if (!phase2Ready() || busy() || window.__hauntPhase3Active) {
            hold = 0;
            last = 0;
            return;
          }
          var el = document.documentElement;
          var max = el.scrollHeight - el.clientHeight;
          var r = max <= 0 ? 1 : el.scrollTop / max;
          var now = Date.now();
          if (r >= 0.92) {
            if (!last) last = now;
            hold += now - last;
            last = now;
            if (hold >= 4000) {
              hold = 0;
              done();
            }
          } else {
            last = 0;
            hold = 0;
          }
        }, 200);
      },
    },
    {
      id: "team_spam",
      hint: "Team 카드 연타",
      arm: function (done) {
        var btn =
          document.getElementById("planTeam") ||
          document.querySelector("[data-fake='3']") ||
          document.querySelector(".plan-card.danger-btn");
        armClicks(btn, 5, 2500, done);
      },
    },
    {
      id: "fakeurl_double",
      hint: "가짜 주소창 더블클릭",
      arm: function (done) {
        var bar = document.getElementById("fakeUrlBar");
        if (!bar) return;
        document.documentElement.classList.add("climax-fakeurl-live");
        bar.style.pointerEvents = "auto";
        bar.classList.add("p2-trig-hot");
        var last = 0;
        bar.addEventListener("click", function (e) {
          if (!phase2Ready() || busy() || window.__hauntPhase3Active) return;
          e.preventDefault();
          var now = Date.now();
          if (now - last < 400) {
            last = 0;
            done();
          } else last = now;
        });
      },
    },
    {
      id: "copy_curse",
      hint: "아무 텍스트나 복사",
      arm: function (done) {
        document.addEventListener("copy", function () {
          if (!phase2Ready() || busy() || window.__hauntPhase3Active) return;
          done();
        });
      },
    },
    {
      id: "wait_triple",
      hint: "하단 기다림 문장 3번",
      arm: function (done) {
        // 예전 console.log 자리 — 2페이즈에선 “그것들은 기다린다” 줄
        var el =
          document.getElementById("resWait") ||
          document.querySelector("[data-find='console']") ||
          document.querySelector(".stasis-later .morph");
        if (el) el.classList.add("p2-trig-hot");
        armClicks(el, 3, 2000, done);
      },
    },
    {
      id: "beta_quad",
      hint: "푸터 beta 4번",
      arm: function (done) {
        var el =
          document.querySelector(".foot-beta") ||
          document.querySelector("[data-find='wip']");
        if (el) el.classList.add("p2-trig-hot");
        armClicks(el, 4, 2500, done);
      },
    },
    {
      id: "version_triple",
      hint: "푸터 버전 3번",
      arm: function (done) {
        var el =
          document.querySelector(".foot-micro:not(.foot-beta)") ||
          document.querySelector("[data-find='branch']");
        if (el) el.classList.add("p2-trig-hot");
        armClicks(el, 3, 2500, done);
      },
    },
    {
      id: "title_mash",
      hint: "제목 5연타",
      arm: function (done) {
        armClicks(document.getElementById("mainTitle"), 5, 1800, done);
      },
    },
    {
      id: "scroll_bounce",
      hint: "맨 아래 → 맨 위 빠르게",
      arm: function (done) {
        var sawDeep = false;
        var deepAt = 0;
        window.addEventListener(
          "scroll",
          function () {
            if (!phase2Ready() || busy() || window.__hauntPhase3Active) return;
            var el = document.documentElement;
            var max = el.scrollHeight - el.clientHeight;
            var r = max <= 0 ? 1 : el.scrollTop / max;
            if (r >= 0.9) {
              sawDeep = true;
              deepAt = Date.now();
            }
            if (sawDeep && r <= 0.12 && Date.now() - deepAt < 3500) {
              sawDeep = false;
              done();
            }
          },
          { passive: true }
        );
      },
    },
    {
      id: "plan_sequence",
      hint: "Free → Team → Free 순서",
      arm: function (done) {
        var seq = [];
        var need = ["2", "3", "2"];
        document.querySelectorAll("[data-fake]").forEach(function (btn) {
          btn.addEventListener("click", function () {
            if (!phase2Ready() || busy() || window.__hauntPhase3Active) return;
            var id = btn.getAttribute("data-fake");
            seq.push(id);
            if (seq.length > 3) seq.shift();
            if (
              seq.length === 3 &&
              seq[0] === need[0] &&
              seq[1] === need[1] &&
              seq[2] === need[2]
            ) {
              seq = [];
              done();
            }
          });
        });
      },
    },
    {
      id: "idle_haunt",
      hint: "가만히 있기 (무입력)",
      arm: function (done) {
        var last = Date.now();
        function bump() {
          last = Date.now();
        }
        ["mousemove", "keydown", "scroll", "touchstart", "click"].forEach(function (ev) {
          window.addEventListener(ev, bump, { passive: true });
        });
        setInterval(function () {
          if (!phase2Ready() || busy() || window.__hauntPhase3Active) {
            last = Date.now();
            return;
          }
          if (Date.now() - last >= 35000) {
            last = Date.now() + 999999;
            done();
          }
        }, 1000);
      },
    },
    {
      id: "type_process",
      hint: "키보드 process",
      arm: function (done) {
        var buf = "";
        document.addEventListener("keydown", function (e) {
          if (!phase2Ready() || busy() || window.__hauntPhase3Active) return;
          if (e.key.length !== 1 || !/[a-zA-Z]/.test(e.key)) return;
          buf = (buf + e.key.toLowerCase()).slice(-12);
          if (buf.indexOf("process") !== -1) {
            buf = "";
            done();
          }
        });
      },
    },
    {
      id: "path_hold",
      hint: "상단 경로 문자열 길게",
      arm: function (done) {
        // 2페이즈에만 보이는 corruptPath (stage-clean에선 숨김)
        var el =
          document.getElementById("corruptPath") ||
          document.querySelector(".stasis-path-hide");
        if (el) {
          el.classList.add("p2-trig-hot");
          el.style.pointerEvents = "auto";
        }
        armHold(el, 2200, done);
      },
    },
    {
      id: "badge_hold",
      hint: "상태 뱃지 길게",
      arm: function (done) {
        var el =
          document.getElementById("eyebrow") ||
          document.querySelector(".stasis-badge") ||
          document.querySelector("[data-find='badge']");
        if (el) el.classList.add("p2-trig-hot");
        armHold(el, 2000, done);
      },
    },
    {
      id: "feat_hold",
      hint: "Features 제목 길게",
      arm: function (done) {
        var el =
          document.getElementById("h2log") ||
          document.querySelector(".stasis-card-light h2") ||
          document.querySelector("[data-find='features']");
        if (el) el.classList.add("p2-trig-hot");
        armHold(el, 2000, done);
      },
    },
    {
      id: "quote_hold",
      hint: "하단 서명 줄 길게",
      arm: function (done) {
        var el =
          document.querySelector(".stasis-quote-by") ||
          document.querySelector("[data-find='readme']");
        if (el) el.classList.add("p2-trig-hot");
        armHold(el, 2200, done);
      },
    },
    {
      id: "hit_pulse",
      hint: "깜빡이는 점 더블클릭 (초 짝수)",
      arm: function (done) {
        window.__hauntHitPulseMode = true;
        document.addEventListener("haunt-hit-success", function onHit() {
          document.removeEventListener("haunt-hit-success", onHit);
          done();
        });
      },
    },
  ];

  var USED_KEY = "haunt_climax_used";
  var CURRENT_KEY = "haunt_climax_trigger"; // 이번 로드 전용 (새로고침 시 재사용 안 함)

  function readUsed() {
    try {
      var raw = localStorage.getItem(USED_KEY);
      if (!raw) return [];
      var arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      return [];
    }
  }

  function writeUsed(arr) {
    try {
      localStorage.setItem(USED_KEY, JSON.stringify(arr));
    } catch (e) {}
  }

  function markUsed(id) {
    var used = readUsed();
    if (used.indexOf(id) === -1) {
      used.push(id);
      writeUsed(used);
    }
    return used;
  }

  function unusedPool() {
    var used = readUsed();
    var pool = TRIGGERS.filter(function (t) {
      return used.indexOf(t.id) === -1;
    });
    // 20개 다 쓰면 리셋 후 다시 전체
    if (!pool.length) {
      writeUsed([]);
      return TRIGGERS.slice();
    }
    return pool;
  }

  /**
   * 1) 새로고침마다 새로 뽑음 (session sticky 제거)
   * 2) 이미 뽑힌 트리거는 localStorage 로 제외, 전부 소진 시 리셋
   */
  function pickTrigger() {
    try {
      // 이전 세션 고정값 제거 — 새로고침 = 새 뽑기
      try {
        sessionStorage.removeItem(CURRENT_KEY);
      } catch (e0) {}

      var forced = /[?&]p3=([a-z0-9_]+)/.exec(location.search || "");
      if (forced) {
        for (var i = 0; i < TRIGGERS.length; i++) {
          if (TRIGGERS[i].id === forced[1]) {
            markUsed(forced[1]);
            try {
              sessionStorage.setItem(CURRENT_KEY, forced[1]);
            } catch (e1) {}
            return TRIGGERS[i];
          }
        }
      }

      var pool = unusedPool();
      var pick = pool[(Math.random() * pool.length) | 0];
      markUsed(pick.id);
      try {
        sessionStorage.setItem(CURRENT_KEY, pick.id);
      } catch (e2) {}
      return pick;
    } catch (e) {
      return TRIGGERS[(Math.random() * TRIGGERS.length) | 0];
    }
  }

  var active = pickTrigger();
  var fired = false;
  window.__hauntClimaxTrigger = active.id;
  document.body.setAttribute("data-p3-trigger", active.id);
  document.body.setAttribute(
    "data-p3-remaining",
    String(
      Math.max(
        0,
        TRIGGERS.length -
          readUsed().filter(function (id) {
            return TRIGGERS.some(function (t) {
              return t.id === id;
            });
          }).length
      )
    )
  );

  /** 유저용 미션 힌트 (세션당 1회 토스트) — 너무 노골적이지 않게 */
  var MISSION = {
    hold_free: "요금 카드 ‘Free’. 잠깐 누르고 있어.",
    triple_logo: "왼쪽 위 Stasis 로고. 세 번.",
    type_kill: "키보드. 끝내는 말, 또는 다시 깨우는 말.",
    deep_hold: "페이지 맨 아래. 거기서 조금 더 머물러.",
    team_spam: "‘Team’ 요금 카드. 여러 번.",
    fakeurl_double: "화면 맨 위, 가짜 주소창. 두 번.",
    copy_curse: "아무 글이나 복사해 봐. (Ctrl+C)",
    wait_triple: "페이지 아래쪽, ‘기다린다’ 문장. 세 번.",
    beta_quad: "푸터 끝 beta. 네 번.",
    version_triple: "푸터 버전 숫자(v0.x). 세 번.",
    title_mash: "큰 제목. 빠르게 여러 번.",
    scroll_bounce: "맨 아래까지 갔다가, 빨리 맨 위로.",
    plan_sequence: "Free → Team → 다시 Free.",
    idle_haunt: "아무 것도 하지 마. 가만히.",
    type_process: "키보드로 process.",
    path_hold: "상단 내비 근처 경로 문자열. 길게.",
    badge_hold: "히어로 위 상태 뱃지. 길게.",
    feat_hold: "Features 카드 제목. 길게.",
    quote_hold: "어두운 배너 아래 서명 줄. 길게.",
    hit_pulse: "화면 어딘가 희미한 점. 짝수 초에 더블클릭.",
  };
  active.mission = MISSION[active.id] || active.hint || "이상 속에서 다음 층으로 가는 조건을 찾아라.";

  function onDone() {
    if (fired || busy()) return;
    if (!phase2Ready()) return;
    // 이미 3페이즈면 무시 (클라이맥스는 phase3-triggers)
    if (window.__hauntPhase3Active) return;
    fired = true;
    hideP2Hint(true);
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[p2→p3] gate trigger fired:", active.id);
    }
    tryEnterPhase3Strict();
  }

  // 트리거 장착 (항상 리스너 등록, 발동은 phase2Ready 검사)
  try {
    active.arm(onDone);
  } catch (e) {
    if (window.console) console.warn("[climax] arm failed", active.id, e);
  }

  // ----- 2페이즈 미션 힌트: 방문(세션)당 1회 -----
  var p2Toast = document.getElementById("p2HintToast");
  var p2Text = document.getElementById("p2HintText");
  var p2Close = document.getElementById("p2HintClose");
  var p2Chip = document.getElementById("p2MissionChip");
  var p2HintShown = false;

  function sessionHintKey() {
    return "haunt_p2_hint_" + active.id;
  }

  function alreadyHintedThisSession() {
    try {
      return sessionStorage.getItem(sessionHintKey()) === "1";
    } catch (e) {
      return p2HintShown;
    }
  }

  function markHinted() {
    p2HintShown = true;
    try {
      sessionStorage.setItem(sessionHintKey(), "1");
    } catch (e) {}
  }

  function showP2Hint() {
    if (fired || busy()) return;
    if (!phase2Ready()) return;
    // 일기 연 중에는 미루기 — 닫힌 뒤 다시 시도
    if (document.body.classList.contains("diary-open")) {
      setTimeout(function () {
        if (!fired && phase2Ready() && !busy()) showP2Hint();
      }, 1200);
      return;
    }
    if (alreadyHintedThisSession()) {
      // 이미 봤으면 칩만
      if (p2Chip) p2Chip.hidden = false;
      return;
    }
    markHinted();
    if (p2Text) {
      p2Text.textContent =
        "2페이즈. 다음 층(3페이즈)으로 가는 조건이 하나 있다. — " + active.mission;
    }
    if (p2Toast) {
      p2Toast.hidden = false;
      p2Toast.classList.add("is-in");
      p2Toast.classList.remove("is-out");
    }
    document.body.classList.add("p2-hint-visible");
    // 자동으로 안 사라지게 조금 길게, 닫으면 칩 남김
    setTimeout(function () {
      if (p2Toast && !p2Toast.hidden) {
        p2Toast.classList.remove("is-in");
        p2Toast.classList.add("is-out");
        setTimeout(function () {
          if (p2Toast) p2Toast.hidden = true;
          document.body.classList.remove("p2-hint-visible");
          if (p2Chip && !fired) p2Chip.hidden = false;
        }, 400);
      }
    }, 12000);
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[climax] P2 mission hint:", active.id, active.mission);
    }
  }

  function hideP2Hint(all) {
    if (p2Toast) {
      p2Toast.hidden = true;
      p2Toast.classList.remove("is-in");
    }
    document.body.classList.remove("p2-hint-visible");
    if (all && p2Chip) p2Chip.hidden = true;
  }

  function reShowHintFromChip() {
    if (fired || busy() || window.__hauntPhase3Active) return;
    if (p2Text) {
      p2Text.textContent = "3페이즈 진입 조건 — " + active.mission;
    }
    if (p2Toast) {
      p2Toast.hidden = false;
      p2Toast.classList.add("is-in");
      p2Toast.classList.remove("is-out");
    }
    document.body.classList.add("p2-hint-visible");
  }

  if (p2Close) {
    p2Close.addEventListener("click", function () {
      hideP2Hint(false);
      if (p2Chip && !fired) p2Chip.hidden = false;
    });
  }
  if (p2Chip) {
    p2Chip.addEventListener("click", function () {
      reShowHintFromChip();
    });
  }

  // phase2 진입 감지 → 힌트 1회
  function watchPhase2() {
    if (phase2Ready()) {
      // 일기 닫고 메인 볼 때 보이도록 약간 딜레이
      setTimeout(function () {
        if (phase2Ready() && !busy() && !fired) showP2Hint();
      }, 1800);
      return true;
    }
    return false;
  }
  document.addEventListener("haunt-stage", function (ev) {
    var s = ev && ev.detail && ev.detail.stage;
    if (s >= 2) watchPhase2();
  });
  document.addEventListener("haunt-mood", function (ev) {
    var m = ev && ev.detail && ev.detail.mood;
    if (m >= 3) watchPhase2();
  });
  document.addEventListener("haunt-diary", function () {
    setTimeout(watchPhase2, 500);
  });
  // 이미 조건을 만족한 채 로드된 경우
  setInterval(function () {
    if (!p2HintShown && !alreadyHintedThisSession() && phase2Ready() && !busy() && !fired) {
      watchPhase2();
    }
  }, 3000);

  // 제작자 프리패스
  function isCreator() {
    try {
      if (/[?&](debug|creator|summon)=1/.test(location.search || "")) return true;
      if (localStorage.getItem("haunt_creator") === "1") return true;
    } catch (e) {}
    return false;
  }

  window.__hauntCreatorPass = isCreator();

  if (window.__hauntCreatorPass) {
    try {
      if (/[?&]creator=1/.test(location.search || "")) {
        localStorage.setItem("haunt_creator", "1");
      }
    } catch (e) {}

    var badge = document.createElement("div");
    badge.className = "creator-pass creator-p3";
    badge.innerHTML =
      "<strong>P2→P3</strong> gate: <code>" +
      active.id +
      "</code><br/>" +
      "<button type='button' class='p3-enter'>▶ 3페이즈</button> " +
      "<button type='button' class='p3-go'>▶ 클라이맥스</button>";
    badge.title = "제작자 프리패스";
    document.body.appendChild(badge);
    var enterBtn = badge.querySelector(".p3-enter");
    var go = badge.querySelector(".p3-go");
    if (enterBtn) {
      enterBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        window.__hauntCreatorPass = true;
        window.__hauntDiaryDiscovered = true;
        if (typeof window.__hauntSetStage === "function") window.__hauntSetStage(3);
        if (typeof window.__hauntSetMood === "function") window.__hauntSetMood(4);
        fired = true;
        hideP2Hint(true);
        enterPhase3();
      });
    }
    if (go) {
      go.addEventListener("click", function (e) {
        e.stopPropagation();
        window.__hauntCreatorPass = true;
        if (typeof window.__hauntSetStage === "function") window.__hauntSetStage(3);
        if (typeof window.__hauntSetMood === "function") window.__hauntSetMood(4);
        window.__hauntDiaryDiscovered = true;
        if (!window.__hauntPhase3Active) enterPhase3();
        summon();
      });
    }
  }

  // Shift+Alt+3 = freepass climax (skip)
  document.addEventListener("keydown", function (e) {
    if (e.shiftKey && e.altKey && (e.key === "3" || e.code === "Digit3")) {
      e.preventDefault();
      window.__hauntCreatorPass = true;
      window.__hauntDiaryDiscovered = true;
      if (typeof window.__hauntSetStage === "function") window.__hauntSetStage(3);
      if (!window.__hauntPhase3Active) enterPhase3();
      summon();
    }
  });

  if (/[?&]summon=1/.test(location.search || "")) {
    setTimeout(function () {
      window.__hauntCreatorPass = true;
      window.__hauntDiaryDiscovered = true;
      if (typeof window.__hauntSetStage === "function") window.__hauntSetStage(3);
      if (!window.__hauntPhase3Active) enterPhase3();
      summon();
    }, 500);
  }

  // 새로고침 시 이미 3페이즈였으면 복구
  try {
    if (sessionStorage.getItem("haunt_phase3") === "1" && window.__hauntDiaryDiscovered) {
      window.__hauntPhase3Active = true;
      document.body.classList.add("phase-3-active");
      document.body.setAttribute("data-game-phase", "3");
      fired = true;
      hideP2Hint(true);
    }
  } catch (eRestore) {}

  if (window.console && /[?&]debug=1/.test(location.search || "")) {
    var usedNow = readUsed();
    console.log(
      "[climax] this load trigger:",
      active.id,
      "—",
      active.hint,
      "| used",
      usedNow.length + "/" + TRIGGERS.length,
      usedNow,
      "| remaining after this pick",
      unusedPool()
        .filter(function (t) {
          return t.id !== active.id;
        })
        .map(function (t) {
          return t.id;
        })
    );
  }

  window.__hauntClimax = {
    id: active.id,
    hint: active.hint,
    mission: active.mission,
    role: "p2-to-p3-gate",
    all: TRIGGERS.map(function (t) {
      return { id: t.id, hint: t.hint, mission: MISSION[t.id] || t.hint };
    }),
    used: function () {
      return readUsed().slice();
    },
    remaining: function () {
      return unusedPool().map(function (t) {
        return t.id;
      });
    },
    resetUsed: function () {
      writeUsed([]);
      try {
        sessionStorage.removeItem(CURRENT_KEY);
      } catch (e) {}
    },
    showHint: showP2Hint,
    enterPhase3: enterPhase3,
    summon: function () {
      window.__hauntCreatorPass = true;
      window.__hauntDiaryDiscovered = true;
      if (typeof window.__hauntSetStage === "function") window.__hauntSetStage(3);
      if (!window.__hauntPhase3Active) enterPhase3();
      summon();
    },
    phase2Ready: phase2Ready,
  };

  window.__hauntEnterPhase3 = enterPhase3;
})();
