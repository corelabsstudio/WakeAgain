/**
 * 3페이즈 → 클라이맥스 트리거
 * - 별도 20종 풀 (2페이즈 게이트 트리거와 분리)
 * - phase3Ready: __hauntPhase3Active (2페이즈 게이트 통과 후)
 * - 힌트: 3페이즈 진입 후 5분 (300s). ?hintfast=1 이면 8초
 * - 제작자: ?p3fire=1 · Shift+Alt+4
 */
(function () {
  "use strict";

  function stage() {
    if (typeof window.__hauntStage === "function") return window.__hauntStage();
    return parseInt(document.body.getAttribute("data-stage") || "0", 10) || 0;
  }

  function phase3Ready() {
    if (window.__hauntPhase3Active) return true;
    try {
      if (sessionStorage.getItem("haunt_phase3") === "1" && window.__hauntDiaryDiscovered) {
        window.__hauntPhase3Active = true;
        document.body.classList.add("phase-3-active");
        return true;
      }
    } catch (e) {}
    return false;
  }

  function busy() {
    return (
      document.body.classList.contains("is-haunting") ||
      document.body.classList.contains("is-ending") ||
      document.body.classList.contains("diary-open")
    );
  }

  function summon() {
    if (typeof window.__hauntSummon === "function") {
      window.__hauntSummon();
      return true;
    }
    return false;
  }

  // ---------- 20 NEW climax-unlock triggers (2페이즈 게이트와 다른 동작) ----------
  var TRIGGERS = [
    {
      id: "logo_hold",
      hint: "로고 길게",
      arm: function (done) {
        var el = document.getElementById("topRec");
        if (!el) return;
        var t = null;
        function clear() {
          if (t) clearTimeout(t);
          t = null;
          el.classList.remove("p3-holding");
        }
        el.addEventListener("pointerdown", function () {
          if (!phase3Ready() || busy()) return;
          el.classList.add("p3-holding");
          t = setTimeout(function () {
            clear();
            done();
          }, 3000);
        });
        el.addEventListener("pointerup", clear);
        el.addEventListener("pointerleave", clear);
        el.addEventListener("pointercancel", clear);
      },
    },
    {
      id: "type_stasis",
      hint: "키보드 stasis",
      arm: function (done) {
        var buf = "";
        document.addEventListener("keydown", function (e) {
          if (!phase3Ready() || busy()) return;
          if (e.metaKey || e.ctrlKey || e.altKey) return;
          if (e.key.length !== 1 || !/[a-zA-Z]/.test(e.key)) return;
          buf = (buf + e.key.toLowerCase()).slice(-12);
          if (buf.indexOf("stasis") !== -1) {
            buf = "";
            done();
          }
        });
      },
    },
    {
      id: "type_wakeagain",
      hint: "키보드 wakeagain",
      arm: function (done) {
        var buf = "";
        document.addEventListener("keydown", function (e) {
          if (!phase3Ready() || busy()) return;
          if (e.metaKey || e.ctrlKey || e.altKey) return;
          if (e.key.length !== 1 || !/[a-zA-Z]/.test(e.key)) return;
          buf = (buf + e.key.toLowerCase()).slice(-16);
          if (buf.indexOf("wakeagain") !== -1) {
            buf = "";
            done();
          }
        });
      },
    },
    {
      id: "cta_hold",
      hint: "Get started 길게",
      arm: function (done) {
        var btn = document.getElementById("navCta");
        if (!btn) return;
        var t = null;
        function clear() {
          if (t) clearTimeout(t);
          t = null;
          btn.classList.remove("p3-holding");
        }
        btn.addEventListener("pointerdown", function () {
          if (!phase3Ready() || busy()) return;
          btn.classList.add("p3-holding");
          t = setTimeout(function () {
            clear();
            done();
          }, 2500);
        });
        btn.addEventListener("pointerup", clear);
        btn.addEventListener("pointerleave", clear);
      },
    },
    {
      id: "pro_spam",
      hint: "Pro 카드 연타",
      arm: function (done) {
        var btn = document.getElementById("planPro");
        if (!btn) return;
        // 비활성 해제 (3페이즈 트리거용)
        try {
          btn.disabled = false;
          btn.removeAttribute("disabled");
        } catch (e) {}
        var n = 0;
        var reset = null;
        btn.addEventListener("click", function () {
          if (!phase3Ready() || busy()) return;
          n++;
          clearTimeout(reset);
          reset = setTimeout(function () {
            n = 0;
          }, 2800);
          if (n >= 7) {
            n = 0;
            done();
          }
        });
      },
    },
    {
      id: "docs_triple",
      hint: "Docs 3연타",
      arm: function (done) {
        var el = document.querySelector("[data-find='docs']") || document.querySelector(".pill-dead");
        if (!el) return;
        var n = 0;
        var t = null;
        el.addEventListener("click", function () {
          if (!phase3Ready() || busy()) return;
          n++;
          clearTimeout(t);
          t = setTimeout(function () {
            n = 0;
          }, 2000);
          if (n >= 3) {
            n = 0;
            done();
          }
        });
      },
    },
    {
      id: "pricing_hold",
      hint: "Pricing 길게",
      arm: function (done) {
        var el = document.querySelector("[data-find='todo']") || document.querySelector(".pill-todo");
        if (!el) return;
        var t = null;
        function clear() {
          if (t) clearTimeout(t);
          t = null;
        }
        el.addEventListener("pointerdown", function () {
          if (!phase3Ready() || busy()) return;
          t = setTimeout(function () {
            clear();
            done();
          }, 2200);
        });
        el.addEventListener("pointerup", clear);
        el.addEventListener("pointerleave", clear);
      },
    },
    {
      id: "monitor_quad",
      hint: "모니터 프레임 4번",
      arm: function (done) {
        var el =
          document.querySelector(".monitor-frame") ||
          document.querySelector(".stasis-monitor-card") ||
          document.querySelector(".stasis-card-dark");
        if (!el) return;
        var n = 0;
        var t = null;
        el.addEventListener("click", function () {
          if (!phase3Ready() || busy()) return;
          n++;
          clearTimeout(t);
          t = setTimeout(function () {
            n = 0;
          }, 2500);
          if (n >= 4) {
            n = 0;
            done();
          }
        });
      },
    },
    {
      id: "badge_mash",
      hint: "상단 뱃지 5연타",
      arm: function (done) {
        var el = document.getElementById("eyebrow") || document.querySelector(".stasis-badge");
        if (!el) return;
        var n = 0;
        var t = null;
        el.addEventListener("click", function () {
          if (!phase3Ready() || busy()) return;
          n++;
          clearTimeout(t);
          t = setTimeout(function () {
            n = 0;
          }, 2000);
          if (n >= 5) {
            n = 0;
            done();
          }
        });
      },
    },
    {
      id: "title_hold",
      hint: "제목 길게",
      arm: function (done) {
        var el = document.getElementById("mainTitle");
        if (!el) return;
        var t = null;
        function clear() {
          if (t) clearTimeout(t);
          t = null;
        }
        el.addEventListener("pointerdown", function () {
          if (!phase3Ready() || busy()) return;
          t = setTimeout(function () {
            clear();
            done();
          }, 2800);
        });
        el.addEventListener("pointerup", clear);
        el.addEventListener("pointerleave", clear);
      },
    },
    {
      id: "beta_hold",
      hint: "푸터 beta 길게",
      arm: function (done) {
        var el =
          document.querySelector("[data-find='wip']") ||
          document.querySelector(".foot-beta");
        if (!el) return;
        var t = null;
        function clear() {
          if (t) clearTimeout(t);
          t = null;
        }
        el.addEventListener("pointerdown", function () {
          if (!phase3Ready() || busy()) return;
          t = setTimeout(function () {
            clear();
            done();
          }, 2000);
        });
        el.addEventListener("pointerup", clear);
        el.addEventListener("pointerleave", clear);
      },
    },
    {
      id: "version_spam",
      hint: "버전 숫자 5번",
      arm: function (done) {
        var el =
          document.querySelector("[data-find='branch']") ||
          document.querySelector(".foot-micro:not(.foot-beta)");
        if (!el) return;
        var n = 0;
        var t = null;
        el.addEventListener("click", function () {
          if (!phase3Ready() || busy()) return;
          n++;
          clearTimeout(t);
          t = setTimeout(function () {
            n = 0;
          }, 2500);
          if (n >= 5) {
            n = 0;
            done();
          }
        });
      },
    },
    {
      id: "top_hold",
      hint: "맨 위 스크롤 유지",
      arm: function (done) {
        var hold = 0;
        var last = 0;
        setInterval(function () {
          if (!phase3Ready() || busy()) {
            hold = 0;
            last = 0;
            return;
          }
          var el = document.documentElement;
          var max = el.scrollHeight - el.clientHeight;
          var r = max <= 0 ? 0 : el.scrollTop / max;
          var now = Date.now();
          if (r <= 0.06) {
            if (!last) last = now;
            hold += now - last;
            last = now;
            if (hold >= 4500) {
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
      id: "type_escape",
      hint: "키보드 escape",
      arm: function (done) {
        var buf = "";
        document.addEventListener("keydown", function (e) {
          if (!phase3Ready() || busy()) return;
          if (e.key.length !== 1 || !/[a-zA-Z]/.test(e.key)) return;
          buf = (buf + e.key.toLowerCase()).slice(-10);
          if (buf.indexOf("escape") !== -1) {
            buf = "";
            done();
          }
        });
      },
    },
    {
      id: "arrow_sigil",
      hint: "↑↑↓↓ 화살표",
      arm: function (done) {
        var need = ["ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown"];
        var seq = [];
        document.addEventListener("keydown", function (e) {
          if (!phase3Ready() || busy()) return;
          if (need.indexOf(e.key) === -1) {
            seq = [];
            return;
          }
          seq.push(e.key);
          if (seq.length > need.length) seq.shift();
          if (seq.length === need.length) {
            var ok = true;
            for (var i = 0; i < need.length; i++) {
              if (seq[i] !== need[i]) ok = false;
            }
            if (ok) {
              seq = [];
              done();
            }
          }
        });
      },
    },
    {
      id: "space_ritual",
      hint: "스페이스 12번",
      arm: function (done) {
        var n = 0;
        var t = null;
        document.addEventListener("keydown", function (e) {
          if (!phase3Ready() || busy()) return;
          if (e.code !== "Space" && e.key !== " ") return;
          // 스크롤 방해 최소화 — prevent only when close
          n++;
          clearTimeout(t);
          t = setTimeout(function () {
            n = 0;
          }, 4000);
          if (n >= 12) {
            n = 0;
            done();
          }
        });
      },
    },
    {
      id: "features_hold",
      hint: "Features 라벨 길게",
      arm: function (done) {
        var el =
          document.querySelector("[data-find='features']") ||
          document.getElementById("h2log");
        if (!el) return;
        var t = null;
        function clear() {
          if (t) clearTimeout(t);
          t = null;
        }
        el.addEventListener("pointerdown", function () {
          if (!phase3Ready() || busy()) return;
          t = setTimeout(function () {
            clear();
            done();
          }, 2000);
        });
        el.addEventListener("pointerup", clear);
        el.addEventListener("pointerleave", clear);
      },
    },
    {
      id: "quote_double",
      hint: "다크 배너 더블클릭",
      arm: function (done) {
        var el =
          document.getElementById("cardWarn") ||
          document.querySelector(".stasis-quote");
        if (!el) return;
        var last = 0;
        el.addEventListener("click", function () {
          if (!phase3Ready() || busy()) return;
          var now = Date.now();
          if (now - last < 400) {
            last = 0;
            done();
          } else last = now;
        });
      },
    },
    {
      id: "select_all_curse",
      hint: "전체 선택 (Ctrl+A)",
      arm: function (done) {
        document.addEventListener("keydown", function (e) {
          if (!phase3Ready() || busy()) return;
          if ((e.ctrlKey || e.metaKey) && (e.key === "a" || e.key === "A")) {
            // 기본 전체선택은 유지하되 트리거 발동
            done();
          }
        });
      },
    },
    {
      id: "long_idle",
      hint: "오래 가만히 (무입력)",
      arm: function (done) {
        var last = Date.now();
        function bump() {
          last = Date.now();
        }
        ["mousemove", "keydown", "scroll", "touchstart", "click"].forEach(function (ev) {
          window.addEventListener(ev, bump, { passive: true });
        });
        setInterval(function () {
          if (!phase3Ready() || busy()) {
            last = Date.now();
            return;
          }
          // 50초 — 2페이즈 idle(35s)보다 김
          if (Date.now() - last >= 50000) {
            last = Date.now() + 999999;
            done();
          }
        }, 1000);
      },
    },
  ];

  var USED_KEY = "haunt_p3_climax_used";
  var CURRENT_KEY = "haunt_p3_climax_trigger";
  var ENTERED_AT_KEY = "haunt_p3_entered_at";

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
    if (!pool.length) {
      writeUsed([]);
      return TRIGGERS.slice();
    }
    return pool;
  }

  function pickTrigger() {
    try {
      try {
        sessionStorage.removeItem(CURRENT_KEY);
      } catch (e0) {}

      var forced = /[?&]p3t=([a-z0-9_]+)/.exec(location.search || "");
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
  window.__hauntPhase3Trigger = active.id;
  document.body.setAttribute("data-p3-climax-trigger", active.id);

  var MISSION = {
    logo_hold: "왼쪽 위 브랜드. 손가락을 떼지 마.",
    type_stasis: "키보드. 이 서비스 이름.",
    type_wakeagain: "키보드. 기억해야 할 그 이름.",
    cta_hold: "Get started. 잠깐 누르고 있어.",
    pro_spam: "Pro 요금 카드. 여러 번.",
    docs_triple: "내비 Docs. 세 번.",
    pricing_hold: "Pricing. 길게.",
    monitor_quad: "다크 모니터 미리보기. 네 번.",
    badge_mash: "히어로 위 뱃지. 빠르게 다섯.",
    title_hold: "큰 제목. 길게 눌러.",
    beta_hold: "푸터 beta. 길게.",
    version_spam: "푸터 버전 숫자. 다섯 번.",
    top_hold: "맨 위로 올려 두고 머물러.",
    type_escape: "키보드로 escape.",
    arrow_sigil: "화살표. 위 위 아래 아래.",
    space_ritual: "스페이스바. 많이.",
    features_hold: "Features 쪽 라벨. 길게.",
    quote_double: "어두운 인용 배너. 두 번.",
    select_all_curse: "전부 선택해 봐. (Ctrl+A)",
    long_idle: "아무 것도 하지 마. 더 오래.",
  };
  active.mission = MISSION[active.id] || active.hint || "마지막 조건을 찾아라.";

  function onDone() {
    if (fired || busy()) return;
    if (!phase3Ready()) return;
    fired = true;
    hideP3Hint(true);
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[p3→climax] trigger fired:", active.id);
    }
    // 클라이맥스 직전 플래시
    document.body.classList.add("phase3-climax-arm");
    setTimeout(function () {
      document.body.classList.remove("phase3-climax-arm");
      summon();
    }, 280);
  }

  try {
    active.arm(onDone);
  } catch (e) {
    if (window.console) console.warn("[p3] arm failed", active.id, e);
  }

  // ----- 3페이즈 힌트: 진입 후 5분 -----
  var p3Toast = document.getElementById("p3HintToast");
  var p3Text = document.getElementById("p3HintText");
  var p3Close = document.getElementById("p3HintClose");
  var p3Chip = document.getElementById("p3MissionChip");
  var p3HintShown = false;
  var HINT_MS = 5 * 60 * 1000; // 5분
  if (/[?&]hintfast=1/.test(location.search || "")) HINT_MS = 8000;
  if (/[?&]p3hint=1/.test(location.search || "")) HINT_MS = 3000;

  function sessionHintKey() {
    return "haunt_p3_hint_" + active.id;
  }

  function alreadyHinted() {
    try {
      return sessionStorage.getItem(sessionHintKey()) === "1";
    } catch (e) {
      return p3HintShown;
    }
  }

  function markHinted() {
    p3HintShown = true;
    try {
      sessionStorage.setItem(sessionHintKey(), "1");
    } catch (e) {}
  }

  function getEnteredAt() {
    try {
      var v = sessionStorage.getItem(ENTERED_AT_KEY);
      if (v) return parseInt(v, 10) || 0;
    } catch (e) {}
    return 0;
  }

  function setEnteredAt(ts) {
    try {
      sessionStorage.setItem(ENTERED_AT_KEY, String(ts || Date.now()));
    } catch (e) {}
  }

  function showP3Hint() {
    if (fired || busy()) return;
    if (!phase3Ready()) return;
    if (document.body.classList.contains("diary-open")) {
      setTimeout(function () {
        if (!fired && phase3Ready() && !busy()) showP3Hint();
      }, 1200);
      return;
    }
    if (alreadyHinted()) {
      if (p3Chip) p3Chip.hidden = false;
      return;
    }
    markHinted();
    if (p3Text) {
      p3Text.textContent =
        "3페이즈. 클라이맥스 조건이 하나 있다. — " + active.mission;
    }
    if (p3Toast) {
      p3Toast.hidden = false;
      p3Toast.classList.add("is-in");
      p3Toast.classList.remove("is-out");
    }
    document.body.classList.add("p3-hint-visible");
    setTimeout(function () {
      if (p3Toast && !p3Toast.hidden) {
        p3Toast.classList.remove("is-in");
        p3Toast.classList.add("is-out");
        setTimeout(function () {
          if (p3Toast) p3Toast.hidden = true;
          document.body.classList.remove("p3-hint-visible");
          if (p3Chip && !fired) p3Chip.hidden = false;
        }, 400);
      }
    }, 14000);
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[p3] mission hint:", active.id, active.mission);
    }
  }

  function hideP3Hint(all) {
    if (p3Toast) {
      p3Toast.hidden = true;
      p3Toast.classList.remove("is-in");
    }
    document.body.classList.remove("p3-hint-visible");
    if (all && p3Chip) p3Chip.hidden = true;
  }

  function reShowFromChip() {
    if (fired || busy()) return;
    if (p3Text) p3Text.textContent = "클라이맥스 조건 — " + active.mission;
    if (p3Toast) {
      p3Toast.hidden = false;
      p3Toast.classList.add("is-in");
      p3Toast.classList.remove("is-out");
    }
    document.body.classList.add("p3-hint-visible");
  }

  if (p3Close) {
    p3Close.addEventListener("click", function () {
      hideP3Hint(false);
      if (p3Chip && !fired) p3Chip.hidden = false;
    });
  }
  if (p3Chip) {
    p3Chip.addEventListener("click", function () {
      reShowFromChip();
    });
  }

  var hintTimer = null;
  function scheduleHintFromEntry() {
    if (hintTimer) clearTimeout(hintTimer);
    if (!phase3Ready() || fired || alreadyHinted()) {
      if (alreadyHinted() && phase3Ready() && p3Chip && !fired) p3Chip.hidden = false;
      return;
    }
    var entered = getEnteredAt();
    if (!entered) {
      entered = Date.now();
      setEnteredAt(entered);
    }
    var wait = Math.max(0, HINT_MS - (Date.now() - entered));
    if (window.console && /[?&]debug=1/.test(location.search || "")) {
      console.log("[p3] hint in", Math.round(wait / 1000) + "s", "trigger", active.id);
    }
    // 대기 중 미세 칩: 힌트 전엔 숨김. 5분 후 토스트.
    hintTimer = setTimeout(function () {
      if (!fired && phase3Ready() && !busy()) showP3Hint();
    }, wait);
  }

  function onPhase3Enter() {
    if (!getEnteredAt()) setEnteredAt(Date.now());
    document.body.classList.add("phase-3-active");
    document.body.setAttribute("data-game-phase", "3");
    // 2페이즈 칩 숨김
    var p2Chip = document.getElementById("p2MissionChip");
    if (p2Chip) p2Chip.hidden = true;
    var p2Toast = document.getElementById("p2HintToast");
    if (p2Toast) p2Toast.hidden = true;
    scheduleHintFromEntry();
    // 진입 토스트 (힌트 아님 — 층이 바뀌었다는 신호만)
    showLayerToast();
  }

  function showLayerToast() {
    if (busy()) return;
    var el = document.getElementById("p3LayerToast");
    if (!el) {
      el = document.createElement("div");
      el.id = "p3LayerToast";
      el.className = "p3-layer-toast";
      el.setAttribute("aria-hidden", "true");
      el.innerHTML =
        '<span class="p3-layer-tag">PHASE 3</span><p>더 깊은 층이다. 아직 끝나지 않았다.</p>';
      document.body.appendChild(el);
    }
    el.classList.add("is-on");
    setTimeout(function () {
      el.classList.remove("is-on");
    }, 4200);
  }

  document.addEventListener("haunt-phase3", function () {
    onPhase3Enter();
  });

  // 이미 phase3 복구된 로드
  if (phase3Ready()) {
    setTimeout(onPhase3Enter, 400);
  }

  // 늦게 진입하는 경우 폴링
  setInterval(function () {
    if (phase3Ready() && !getEnteredAt()) {
      onPhase3Enter();
    }
  }, 1500);

  // 제작자 표시
  function isCreator() {
    try {
      if (/[?&](debug|creator|summon)=1/.test(location.search || "")) return true;
      if (localStorage.getItem("haunt_creator") === "1") return true;
    } catch (e) {}
    return false;
  }

  if (isCreator()) {
    var badge = document.createElement("div");
    badge.className = "creator-pass creator-p3-climax";
    badge.innerHTML =
      "<strong>P3→CLIMAX</strong> <code>" +
      active.id +
      "</code><br/><button type='button' class='p3-fire'>▶ 이 트리거 발동</button>";
    document.body.appendChild(badge);
    var fireBtn = badge.querySelector(".p3-fire");
    if (fireBtn) {
      fireBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        window.__hauntPhase3Active = true;
        document.body.classList.add("phase-3-active");
        fired = false;
        onDone();
      });
    }
  }

  if (/[?&]p3fire=1/.test(location.search || "")) {
    setTimeout(function () {
      window.__hauntPhase3Active = true;
      document.body.classList.add("phase-3-active");
      onDone();
    }, 700);
  }

  document.addEventListener("keydown", function (e) {
    if (e.shiftKey && e.altKey && (e.key === "4" || e.code === "Digit4")) {
      e.preventDefault();
      window.__hauntPhase3Active = true;
      document.body.classList.add("phase-3-active");
      onDone();
    }
  });

  if (window.console && /[?&]debug=1/.test(location.search || "")) {
    console.log(
      "[p3-climax] trigger:",
      active.id,
      "—",
      active.hint,
      "| hint after",
      HINT_MS / 1000 + "s in phase3",
      "| used",
      readUsed().length + "/" + TRIGGERS.length
    );
  }

  window.__hauntPhase3 = {
    id: active.id,
    hint: active.hint,
    mission: active.mission,
    ready: phase3Ready,
    hintMs: HINT_MS,
    showHint: showP3Hint,
    fire: function () {
      if (!phase3Ready()) {
        window.__hauntPhase3Active = true;
        document.body.classList.add("phase-3-active");
      }
      fired = false;
      onDone();
    },
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
  };
})();
