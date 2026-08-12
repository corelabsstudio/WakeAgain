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

    if (!el) {
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
    }

    // Static pages already ship a hardcoded #footerVisitors (see index.html etc.) —
    // this block runs for both that case and the freshly-created one above, so the
    // sources drilldown gets wired up everywhere exactly once.
    if (!document.getElementById("footerVisitorsSources")) {
      var sourcesEl = document.createElement("span");
      sourcesEl.id = "footerVisitorsSources";
      sourcesEl.className = "footer-visitors-sources fine";
      sourcesEl.style.display = "none";
      el.appendChild(sourcesEl);
    }

    var todayEl = document.getElementById("footerVisitorsToday");
    if (todayEl && !todayEl.dataset.waSourcesBound) {
      todayEl.dataset.waSourcesBound = "1";
      todayEl.title = "관리자: 클릭하면 오늘 유입 경로";
      todayEl.style.cursor = "pointer";
      todayEl.style.textDecoration = "underline dotted";
      todayEl.addEventListener("click", toggleSources);
    }
    return el;
  }

  // --- admin-only "today visitors" referrer drilldown ---
  var ADMIN_KEY_STORAGE = "wa_admin_key";

  function getAdminKey(forcePrompt) {
    var k = "";
    try {
      k = localStorage.getItem(ADMIN_KEY_STORAGE) || "";
    } catch (e) {}
    if ((!k || forcePrompt) && typeof window.prompt === "function") {
      var entered = window.prompt("관리자 키(X-Admin-Key)");
      if (entered) {
        k = entered.trim();
        try {
          localStorage.setItem(ADMIN_KEY_STORAGE, k);
        } catch (e2) {}
      }
    }
    return k;
  }

  function renderSources(box, data) {
    var sources = (data && data.sources) || [];
    if (!sources.length) {
      box.textContent = "오늘 유입 기록 없음";
      return;
    }
    var total = sources.reduce(function (sum, s) {
      return sum + (s.visits || 0);
    }, 0);
    box.innerHTML = sources
      .map(function (s) {
        var pct = total ? Math.round((s.visits / total) * 100) : 0;
        return (
          '<span class="footer-visitors-source-row">' +
          s.source +
          " " +
          s.visits +
          " (" +
          pct +
          "%)</span>"
        );
      })
      .join(" · ");
  }

  function toggleSources() {
    var box = document.getElementById("footerVisitorsSources");
    if (!box) return;

    if (box.style.display !== "none") {
      box.style.display = "none";
      return;
    }

    var key = getAdminKey(false);
    if (!key) return;

    box.style.display = "";
    box.textContent = "불러오는 중…";

    fetch(apiBase() + "/api/v1/admin/visit-sources", {
      headers: { "X-Admin-Key": key },
      credentials: "same-origin",
    })
      .then(function (r) {
        if (r.status === 401) {
          try {
            localStorage.removeItem(ADMIN_KEY_STORAGE);
          } catch (e) {}
          throw new Error("unauthorized");
        }
        return r.json();
      })
      .then(function (data) {
        renderSources(box, data);
      })
      .catch(function () {
        box.textContent = "관리자 키가 틀렸거나 불러오기 실패";
      });
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
    var body = JSON.stringify({ visitor_key: key, referrer: document.referrer || "" });

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
