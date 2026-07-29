/**
 * Hero metrics — live DB counts only (no fabricated GMV / match %).
 * Only updates the <strong> numbers. Labels stay in HTML with data-i18n
 * so KO/EN switch is never overwritten.
 *
 * 「다시 세상으로 나간」: server tallies always; public count only after
 * reveal threshold. Until then show「추후 공개」(i18n).
 */
(function () {
  var api = window.WakeAgainAPI;
  var list = document.querySelector(".hero-stats");
  if (!list || !api) return;

  var lastWentLive = null; // { revealed, count } | null

  function t(key, fallback) {
    if (window.WakeAgainI18n && typeof window.WakeAgainI18n.t === "function") {
      var v = window.WakeAgainI18n.t(key);
      if (v && v !== key) return v;
    }
    return fallback;
  }

  function animateCount(el, target) {
    if (!el) return;
    var n = Number(target);
    if (!isFinite(n)) {
      el.textContent = "—";
      return;
    }
    el.classList.remove("is-later");
    el.removeAttribute("data-i18n");
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

  function applyWentLive(went, animate) {
    var el =
      document.getElementById("heroWentLiveVal") ||
      (list.querySelectorAll(":scope > li")[2] &&
        list.querySelectorAll(":scope > li")[2].querySelector("strong"));
    if (!el) return;

    lastWentLive = went || null;
    var revealed = went && went.revealed && went.count != null;
    if (revealed) {
      if (animate) animateCount(el, went.count);
      else {
        el.classList.remove("is-later");
        el.removeAttribute("data-i18n");
        el.dataset.counted = "1";
        el.setAttribute("data-count", String(went.count));
        el.textContent = Number(went.count).toLocaleString();
      }
      return;
    }

    // Locked:「추후 공개」
    el.classList.add("is-later");
    el.dataset.counted = "0";
    el.removeAttribute("data-count");
    el.setAttribute("data-i18n", "hero.stat_went_live_later");
    el.textContent = t("hero.stat_went_live_later", "추후 공개");
  }

  /** Update only count cells — never touch label spans (data-i18n). */
  function applyCounts(projects, interests, went, animate) {
    var block = document.getElementById("heroStatsBlock");
    if (block) {
      var p = Number(projects) || 0;
      var i = Number(interests) || 0;
      var w = went && went.revealed && went.count != null ? Number(went.count) : 0;
      block.hidden = !(p > 0 || i > 0 || w > 0);
    }
    var items = list.querySelectorAll(":scope > li");
    if (!items.length) return;

    var s0 = items[0] && items[0].querySelector("strong");
    var s1 = items[1] && items[1].querySelector("strong");

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

    applyWentLive(went, animate);

    if (window.WakeAgainI18n && typeof window.WakeAgainI18n.apply === "function") {
      window.WakeAgainI18n.apply(list);
      // Re-apply went-live after i18n so revealed numbers are not overwritten
      if (lastWentLive && lastWentLive.revealed && lastWentLive.count != null) {
        applyWentLive(lastWentLive, false);
      }
    }
  }

  function load(animate) {
    api
      .stats()
      .then(function (s) {
        applyCounts(
          s.projects || 0,
          s.interests || 0,
          s.went_live || { revealed: false },
          animate !== false
        );
      })
      .catch(function () {
        applyCounts(null, null, { revealed: false }, false);
      });
  }

  load(true);

  document.addEventListener("wa:langchange", function () {
    if (window.WakeAgainI18n && typeof window.WakeAgainI18n.apply === "function") {
      window.WakeAgainI18n.apply(list);
    }
    if (lastWentLive && lastWentLive.revealed && lastWentLive.count != null) {
      applyWentLive(lastWentLive, false);
    } else if (lastWentLive) {
      applyWentLive(lastWentLive, false);
    }
  });
})();
