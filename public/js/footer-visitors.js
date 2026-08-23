/**
 * Footer visitor counter — 오늘 / 전체 방문자 수 (맨 하단).
 * Records one visit per page load (unique visitor per wa_vid cookie).
 */
(function () {
  var STORAGE_KEY = "wa_vid";
  var COOKIE = "wa_vid";
  var NOTRACK_COOKIE = "wa_notrack";

  function setCookie(name, value, maxAgeSeconds) {
    try {
      document.cookie =
        name + "=" + encodeURIComponent(value) + "; path=/; max-age=" + maxAgeSeconds + "; SameSite=Lax";
    } catch (e) {}
  }

  function getCookie(name) {
    try {
      var m = document.cookie.match(new RegExp("(?:^|;\\s*)" + name + "=([^;]+)"));
      return m ? decodeURIComponent(m[1]) : "";
    } catch (e) {
      return "";
    }
  }

  // Owner opt-out: visiting once with ?notrack=1 sets a 1yr cookie so this
  // browser's own visits stop counting toward the public footer numbers.
  // ?notrack=0 turns counting back on.
  function isOwnerNoTrack() {
    try {
      var params = new URLSearchParams(window.location.search);
      if (params.has("notrack")) {
        var on = params.get("notrack") === "1";
        setCookie(NOTRACK_COOKIE, on ? "1" : "0", 31536000);
        return on;
      }
    } catch (e) {}
    return getCookie(NOTRACK_COOKIE) === "1";
  }

  function t(key, fallback) {
    if (window.WakeAgainI18n && typeof window.WakeAgainI18n.t === "function") {
      var v = window.WakeAgainI18n.t(key);
      if (v && v !== key) return v;
    }
    return fallback;
  }

  function uuidish() {
    try {
      if (crypto && crypto.randomUUID) return crypto.randomUUID().replace(/-/g, "");
    } catch (e) {}
    var s = "";
    for (var i = 0; i < 32; i++) s += Math.floor(Math.random() * 16).toString(16);
    return s;
  }

  // ── 유입 경로 (first-touch) ────────────────────────────────────────────
  // 카톡·인앱 브라우저는 referrer를 안 넘긴다. 그래서 링크에 ?utm_source=를 박고
  // 그 값을 쓴다. 단, 여기 저장하는 것은 가입 귀속용 first-touch 전용이다 —
  // 방문 집계에는 이번 방문 URL의 표식만 쓰고, 없으면 서버가 referrer로 판정한다.
  var SRC_KEY = "wa_src";
  var SRC_REF_KEY = "wa_src_ref";
  var SRC_LAND_KEY = "wa_src_land";
  // 2026-08-23 버그 잔재. referrer가 있어도 이 문자열을 저장해서,
  // 재방문이 전부 direct로 덮였다. 값으로 치지 않고 빈 것으로 읽는다.
  var LEGACY_DIRECT = "(direct)";

  function readUtmSource() {
    try {
      var p = new URLSearchParams(window.location.search);
      return (p.get("utm_source") || p.get("src") || "").slice(0, 60);
    } catch (e) {
      return "";
    }
  }

  function readStoredSource() {
    try {
      var v = localStorage.getItem(SRC_KEY) || "";
      return v === LEGACY_DIRECT ? "" : v;
    } catch (e) {
      return "";
    }
  }

  // 첫 방문의 표식·리퍼러·랜딩을 적어둔다 — 가입 때 "처음 우리를 알게 된 곳"으로 쓴다.
  // 방문 집계(record)와는 쓰임이 다르다. 그쪽은 이번 방문의 URL 표식만 본다.
  function captureFirstTouch() {
    var utm = readUtmSource();
    var stored = readStoredSource();
    try {
      if (utm && !stored) localStorage.setItem(SRC_KEY, utm);
      if (localStorage.getItem(SRC_REF_KEY) === null) {
        localStorage.setItem(SRC_REF_KEY, (document.referrer || "").slice(0, 300));
        localStorage.setItem(SRC_LAND_KEY, (window.location.href || "").slice(0, 300));
      }
    } catch (e) {}
    return { source: utm || stored, first: !stored };
  }

  function getVisitorKey() {
    var k = "";
    try {
      k = localStorage.getItem(STORAGE_KEY) || "";
    } catch (e) {}
    if (!k || k.length < 8) {
      // cookie fallback
      try {
        var m = document.cookie.match(/(?:^|;\s*)wa_vid=([^;]+)/);
        if (m) k = decodeURIComponent(m[1]);
      } catch (e2) {}
    }
    if (!k || k.length < 8) k = uuidish();
    try {
      localStorage.setItem(STORAGE_KEY, k);
    } catch (e3) {}
    try {
      document.cookie =
        COOKIE +
        "=" +
        encodeURIComponent(k) +
        "; path=/; max-age=31536000; SameSite=Lax";
    } catch (e4) {}
    return k;
  }

  // data-render="off" 페이지는 집계만 하고 푸터에 숫자를 그리지 않는다.
  // (블로그·가이드·앱 — 영문 페이지에 한글 라벨이 붙거나 앱 UI가 바뀌는 걸 피한다)
  var RENDER_OFF = (function () {
    try {
      var s = document.currentScript || document.querySelector('script[src*="footer-visitors.js"]');
      return !!(s && s.getAttribute("data-render") === "off");
    } catch (e) {
      return false;
    }
  })();

  function ensureEl() {
    if (RENDER_OFF) return null;
    var el = document.getElementById("footerVisitors");
    if (el) return el;

    var host =
      document.querySelector(".footer-bottom") ||
      document.querySelector("footer.site-footer") ||
      document.querySelector("footer.app-legal-foot") ||
      document.querySelector("footer");
    if (!host) return null;

    el = document.createElement("p");
    el.id = "footerVisitors";
    el.className = "footer-visitors muted fine";
    el.setAttribute("aria-live", "polite");
    el.innerHTML =
      '<span class="footer-visitors-label" data-i18n="footer.visitors_label">방문자</span> ' +
      '<span class="footer-visitors-nums">' +
      '<span data-i18n="footer.visitors_today">오늘</span> ' +
      '<strong id="footerVisitorsToday">—</strong>' +
      '<span class="footer-visitors-sep" aria-hidden="true"> · </span>' +
      '<span data-i18n="footer.visitors_total">전체</span> ' +
      '<strong id="footerVisitorsTotal">—</strong>' +
      "</span>";
    host.appendChild(el);
    return el;
  }

  function apply(stats) {
    ensureEl();
    var today = document.getElementById("footerVisitorsToday");
    var total = document.getElementById("footerVisitorsTotal");
    if (today) {
      today.textContent = Number(stats.today_visitors || 0).toLocaleString();
    }
    if (total) {
      total.textContent = Number(stats.visitors || 0).toLocaleString();
    }
    var root = document.getElementById("footerVisitors");
    if (root && window.WakeAgainI18n && typeof window.WakeAgainI18n.apply === "function") {
      window.WakeAgainI18n.apply(root);
    }
  }

  function apiBase() {
    if (window.WakeAgainAPI && typeof window.WakeAgainAPI.apiBase === "function") {
      return window.WakeAgainAPI.apiBase();
    }
    return "";
  }

  function fetchStatsOnly() {
    if (window.WakeAgainAPI && typeof window.WakeAgainAPI.stats === "function") {
      return window.WakeAgainAPI.stats()
        .then(function (s) {
          apply({ visitors: s.visitors, today_visitors: s.today_visitors });
        })
        .catch(function () {});
    }
    return fetch(apiBase() + "/api/v1/visit", { method: "GET", credentials: "same-origin" })
      .then(function (r) {
        return r.json();
      })
      .then(apply)
      .catch(function () {});
  }

  function record() {
    ensureEl();
    if (isOwnerNoTrack()) return fetchStatsOnly();
    var key = getVisitorKey();
    captureFirstTouch(); // 가입 귀속용 first-touch 갱신 (집계와는 별개)
    var url = apiBase() + "/api/v1/visit";
    var body = JSON.stringify({
      visitor_key: key,
      referrer: document.referrer || "",
      // 이번 방문 URL에 실제로 붙어 온 표식만 보낸다. 저장값을 보내면
      // 재방문이 전부 그 값으로 덮여서 진짜 유입처(리퍼러)가 사라진다.
      utm_source: readUtmSource(),
      landing: (window.location.pathname || "").slice(0, 300),
    });

    // Prefer shared client when present
    if (window.WakeAgainAPI && typeof window.WakeAgainAPI.request === "function") {
      return window.WakeAgainAPI.request("/api/v1/visit", {
        method: "POST",
        body: body,
      })
        .then(apply)
        .catch(function () {
          // still try GET stats
          return window.WakeAgainAPI.stats()
            .then(function (s) {
              apply({
                visitors: s.visitors,
                today_visitors: s.today_visitors,
              });
            })
            .catch(function () {});
        });
    }

    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: body,
      credentials: "same-origin",
      keepalive: true,
    })
      .then(function (r) {
        return r.json();
      })
      .then(apply)
      .catch(function () {});
  }

  function boot() {
    ensureEl();
    record();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  // 가입 폼(api.js)에서 읽어 쓴다.
  window.WakeAgainSource = {
    get: function () {
      var g = function (k) {
        try {
          return localStorage.getItem(k) || "";
        } catch (e) {
          return "";
        }
      };
      return {
        source: g(SRC_KEY),
        referrer: g(SRC_REF_KEY),
        landing: g(SRC_LAND_KEY),
      };
    },
  };

  document.addEventListener("wa:langchange", function () {
    var root = document.getElementById("footerVisitors");
    if (root && window.WakeAgainI18n && typeof window.WakeAgainI18n.apply === "function") {
      window.WakeAgainI18n.apply(root);
    }
  });
})();
