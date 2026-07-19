/**
 * Home page — public showcase feed (anyone can browse, FOMO / inspiration).
 * Not marketplace listings.
 */
(function () {
  var grid = document.getElementById("homeShowcaseGrid");
  if (!grid) return;
  var api = window.WakeAgainAPI;

  function esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function card(s) {
    var price =
      s.price_hint != null
        ? "₩" + Number(s.price_hint).toLocaleString("ko-KR")
        : null;
    var tags = "";
    if (s.status_label) tags += "<span>" + esc(s.status_label) + "</span>";
    if (s.product_type_label) tags += "<span>" + esc(s.product_type_label) + "</span>";
    if (price) tags += "<span>힌트 " + price + "</span>";
    return (
      '<article class="home-sc-card">' +
      "<h3>" +
      esc(s.title) +
      "</h3>" +
      '<p class="home-sc-one">' +
      esc(s.one_liner) +
      "</p>" +
      ((s.story || "").trim()
        ? '<p class="home-sc-story">' + esc(s.story) + "</p>"
        : "") +
      '<div class="home-sc-meta">' +
      tags +
      "</div>" +
      '<div class="home-sc-foot">' +
      "<span>" +
      esc(s.author_name || "익명") +
      "</span>" +
      "<span>응원 " +
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
        var en0 = window.WakeAgainI18n && window.WakeAgainI18n.getLang && window.WakeAgainI18n.getLang() === "en";
        grid.innerHTML =
          '<div class="empty-state" style="grid-column:1/-1">' +
          (en0 ? "No showcases yet. " : "아직 자랑이 없어요. ") +
          '<a class="text-link" href="/diagnose.html">' +
          (en0 ? "Free diagnose" : "무료진단") +
          "</a></div>";
        return;
      }
      grid.innerHTML = list.map(card).join("");
    } catch (e) {
      var en1 = window.WakeAgainI18n && window.WakeAgainI18n.getLang && window.WakeAgainI18n.getLang() === "en";
      grid.innerHTML =
        '<div class="empty-state" style="grid-column:1/-1">' +
        (en1 ? "Could not load. " : "불러오지 못했어요. ") +
        '<a class="text-link" href="/showcase.html">' +
        (en1 ? "Board" : "보드") +
        "</a></div>";
    }
  }

  load();
  document.addEventListener("wa:langchange", load);
  document.addEventListener("wa:currencychange", load);
})();
