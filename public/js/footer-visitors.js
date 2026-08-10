/**
 * Footer visitor counter — 오늘 / 전체 방문자 수 (맨 하단).
 * Records one visit per page load (unique visitor per wa_vid cookie).
 */
(function () {
  var STORAGE_KEY = "wa_vid";
  var COOKIE = "wa_vid";

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

  function record() {
    ensureEl();
    var key = getVisitorKey();
    var url = apiBase() + "/api/v1/visit";
    var body = JSON.stringify({ visitor_key: key });

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

  document.addEventListener("wa:langchange", function () {
    var root = document.getElementById("footerVisitors");
    if (root && window.WakeAgainI18n && typeof window.WakeAgainI18n.apply === "function") {
      window.WakeAgainI18n.apply(root);
    }
  });
})();
