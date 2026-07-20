/**
 * Hero metrics — live DB counts only (no fabricated GMV / match %).
 * Only updates the <strong> numbers. Labels stay in HTML with data-i18n
 * so KO/EN switch is never overwritten.
 */
(function () {
  var api = window.WakeAgainAPI;
  var list = document.querySelector(".hero-stats");
  if (!list || !api) return;

  function animateCount(el, target) {
    if (!el) return;
    var n = Number(target);
    if (!isFinite(n)) {
      el.textContent = "—";
      return;
    }
    el.setAttribute("data-count", String(n));
    if (el.dataset.counted === "1") {
      el.textContent = n.toLocaleString();
      return;
    }
    el.dataset.counted = "1";
    var start = performance.now();
    function frame(now) {
      var p = Math.min(1, (now - start) / 900);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(n * eased).toLocaleString();
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  /** Update only count cells — never touch label spans (data-i18n). */
  function applyCounts(projects, interests, animate) {
    var items = list.querySelectorAll(":scope > li");
    if (!items.length) return;

    var s0 = items[0] && items[0].querySelector("strong");
    var s1 = items[1] && items[1].querySelector("strong");
    // items[2] = Free / 무료 — label only, leave to i18n

    if (projects == null) {
      if (s0) s0.textContent = "—";
    } else if (animate) {
      animateCount(s0, projects);
    } else if (s0) {
      s0.setAttribute("data-count", String(projects));
      s0.textContent = Number(projects).toLocaleString();
    }

    if (interests == null) {
      if (s1) s1.textContent = "—";
    } else if (animate) {
      animateCount(s1, interests);
    } else if (s1) {
      s1.setAttribute("data-count", String(interests));
      s1.textContent = Number(interests).toLocaleString();
    }

    // Refresh free + labels from current language (in case apply ran earlier)
    if (window.WakeAgainI18n && typeof window.WakeAgainI18n.apply === "function") {
      window.WakeAgainI18n.apply(list);
    }
  }

  function load(animate) {
    api
      .stats()
      .then(function (s) {
        applyCounts(s.projects || 0, s.interests || 0, animate !== false);
      })
      .catch(function () {
        applyCounts(null, null, false);
      });
  }

  load(true);

  // Lang switch: re-apply i18n on labels only (numbers stay)
  document.addEventListener("wa:langchange", function () {
    if (window.WakeAgainI18n && typeof window.WakeAgainI18n.apply === "function") {
      window.WakeAgainI18n.apply(list);
    }
  });
})();
