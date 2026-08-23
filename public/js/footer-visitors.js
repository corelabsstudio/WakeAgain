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
  // 그 값을 최우선으로 쓴다. 한 번 잡은 경로는 덮어쓰지 않는다 — 가입 시점의
  // referrer(대개 우리 사이트 자신)가 아니라 "처음 우리를 알게 된 곳"이 알고 싶은 것이라서.
  var SRC_KEY = "wa_src";
  var SRC_REF_KEY = "wa_src_ref";
  var SRC_LAND_KEY = "wa_src_land";

  function readUtmSource() {
    try {
      var p = new URLSearchParams(window.location.search);
      return (p.get("utm_source") || p.get("src") || "").slice(0, 60);
    } catch (e) {
      return "";
    }
  }

  function captureFirstTouch() {
    var utm = readUtmSource();
    var stored = "";
    try {
      stored = localStorage.getItem(SRC_KEY) || "";
    } catch (e) {}
    // 이미 잡아둔 게 있으면 유지. 단 표식이 새로 붙어 오면 그건 더 정확하므로 갱신.
    if (stored && !utm) return { source: stored, first: false };
    var source = utm || "";
    try {
      localStorage.setItem(SRC_KEY, source || "(direct)");
      if (!localStorage.getItem(SRC_REF_KEY)) {
        localStorage.setItem(SRC_REF_KEY, (document.referrer || "").slice(0, 300));
        localStorage.setItem(SRC_LAND_KEY, (window.location.href || "").slice(0, 300));
      }
    } catch (e2) {}
    return { source: source, first: !stored };
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

  function ensureEl() {
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
    var touch = captureFirstTouch();
    var url = apiBase() + "/api/v1/visit";
    var body = JSON.stringify({
      visitor_key: key,
      referrer: document.referrer || "",
      utm_source: touch.source || "",
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
