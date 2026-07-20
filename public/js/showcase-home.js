/**
 * Home page — public showcase feed (anyone can browse, FOMO / inspiration).
 * Not marketplace listings. KO/EN aware.
 */
(function () {
  var grid = document.getElementById("homeShowcaseGrid");
  if (!grid) return;
  var api = window.WakeAgainAPI;

  function isEn() {
    return !!(window.WakeAgainI18n && window.WakeAgainI18n.getLang && window.WakeAgainI18n.getLang() === "en");
  }

  function tt(key, ko, en) {
    try {
      if (window.WakeAgainI18n && window.WakeAgainI18n.t) {
        var v = window.WakeAgainI18n.t(key);
        if (v && v !== key) return v;
      }
    } catch (e) {}
    return isEn() ? en : ko;
  }

  function money(n) {
    if (window.WakeAgainI18n && window.WakeAgainI18n.formatMoney) {
      return window.WakeAgainI18n.formatMoney(n);
    }
    return "₩" + Number(n).toLocaleString(isEn() ? "en-US" : "ko-KR");
  }

  function esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function card(s) {
    var price = s.price_hint != null ? money(s.price_hint) : null;
    var st = (isEn() && s.status_label_en) || s.status_label || "";
    var pt = (isEn() && s.product_type_label_en) || s.product_type_label || "";
    var one = (isEn() && s.one_liner_en) || s.one_liner || "";
    var story = (isEn() && s.story_en) || s.story || "";
    var tags = "";
    if (st) tags += "<span>" + esc(st) + "</span>";
    if (pt) tags += "<span>" + esc(pt) + "</span>";
    if (price) {
      tags +=
        "<span>" +
        tt("showcase.hint", "힌트", "Hint") +
        " " +
        price +
        "</span>";
    }
    return (
      '<article class="home-sc-card">' +
      "<h3>" +
      esc(s.title) +
      "</h3>" +
      '<p class="home-sc-one">' +
      esc(one) +
      "</p>" +
      (String(story).trim()
        ? '<p class="home-sc-story">' + esc(story) + "</p>"
        : "") +
      '<div class="home-sc-meta">' +
      tags +
      "</div>" +
      '<div class="home-sc-foot">' +
      "<span>" +
      esc(s.author_name || tt("showcase.anon", "익명", "Anonymous")) +
      "</span>" +
      "<span>" +
      tt("showcase.cheer", "응원", "Cheers") +
      " " +
      (s.cheer_count || 0) +
      "</span>" +
      "</div></article>"
    );
  }

  async function load() {
    try {
      var data;
      if (api && api.request) {
        data = await api.request("/api/v1/showcases?limit=6");
      } else {
        var res = await fetch("/api/v1/showcases?limit=6");
        data = await res.json();
      }
      var list = (data && data.showcases) || [];
      if (!list.length) {
        grid.innerHTML =
          '<div class="empty-state" style="grid-column:1/-1">' +
          tt("showcase.empty", "아직 자랑이 없어요. ", "No showcases yet. ") +
          '<a class="text-link" href="/diagnose.html">' +
          tt("diag.cta", "무료진단", "Free diagnose") +
          "</a></div>";
        return;
      }
      grid.innerHTML = list.map(card).join("");
    } catch (e) {
      grid.innerHTML =
        '<div class="empty-state" style="grid-column:1/-1">' +
        tt("showcase.load_fail", "불러오지 못했어요. ", "Could not load. ") +
        '<a class="text-link" href="/showcase.html">' +
        tt("showcase.board", "보드", "Board") +
        "</a></div>";
    }
  }

  load();
  document.addEventListener("wa:langchange", load);
  document.addEventListener("wa:currencychange", load);
})();
