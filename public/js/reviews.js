/**
 * Landing testimonials — approved reviews from API, fallback to scenario cards.
 * KO/EN via WakeAgainI18n.
 */
(function () {
  const grid = document.querySelector("#stories .testi-grid");
  const lead = document.querySelector("#stories .center-lead");
  if (!grid || !window.WakeAgainAPI) return;

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

  const FALLBACK = [
    {
      author_name: "김도윤",
      author_name_en: "Doyoon K.",
      role_label: "백엔드 개발자 · 사이드 프로젝트 2년차",
      role_label_en: "Backend dev · 2 years of side projects",
      body:
        "주말마다 붙잡던 예약 관리 SaaS를 11주 만들고, 유저는 7명에서 멈췄습니다. WakeAgain에는 데모와 “왜 멈췄는지”만 적었는데, 시작가 45만 원으로 올리고 관심이 붙었습니다.",
      body_en:
        "I spent 11 weeks on a booking SaaS that stalled at 7 users. On WakeAgain I only posted a demo and why I stopped — listed at ₩450k and interest started coming in.",
      sold_price: null,
      side: "seller",
      _scenario: true,
    },
    {
      author_name: "이수현",
      author_name_en: "Suhyun L.",
      role_label: "인디 메이커 · 전 스타트업 프로덕트",
      role_label_en: "Indie maker · ex-startup product",
      body:
        "처음부터 만들면 최소 6주는 잡는 계획이었습니다. 데모가 있는 프로토타입을 보고 현재가와 남은 시간을 확인한 뒤 판단할 수 있었습니다.",
      body_en:
        "Building from zero would have taken at least six weeks. Seeing a runnable prototype with live price and countdown let me decide whether to bid.",
      sold_price: null,
      side: "buyer",
      _scenario: true,
    },
  ];

  function won(n) {
    if (n == null || n === "") return "";
    if (window.WakeAgainI18n && window.WakeAgainI18n.formatMoney) {
      return window.WakeAgainI18n.formatMoney(n);
    }
    return "₩" + Number(n).toLocaleString(isEn() ? "en-US" : "ko-KR");
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function cardHtml(r) {
    const side = r.side === "buyer"
      ? tt("reviews.side_buy", "구매", "Buyer")
      : tt("reviews.side_sell", "판매", "Seller");
    const price = won(r.sold_price);
    const accent = price
      ? "<p class='quote-accent'>" +
        tt("reviews.sold_at", "성사가", "Sold at") +
        " <strong>" +
        price +
        "</strong> · " +
        side +
        "</p>"
      : r._scenario
        ? "<p class='quote-accent'>" + tt("reviews.scenario", "시나리오 예시", "Scenario example") + "</p>"
        : "<p class='quote-accent'>" + side + " " + tt("reviews.review_word", "후기", "review") + "</p>";
    const author = isEn() && r.author_name_en ? r.author_name_en : r.author_name;
    const role =
      (isEn() && r.role_label_en ? r.role_label_en : r.role_label) ||
      (r.side === "buyer"
        ? tt("reviews.buyer", "구매자", "Buyer")
        : tt("reviews.seller", "판매자", "Seller"));
    const body = isEn() && r.body_en ? r.body_en : r.body;
    return (
      "<article class='glass-card testi-card'>" +
      "<div class='quote-mark' aria-hidden='true'>99</div>" +
      "<p>" +
      escapeHtml(body) +
      "</p>" +
      accent +
      "<footer class='testi-foot'><strong>" +
      escapeHtml(author) +
      "</strong><span>" +
      escapeHtml(role) +
      "</span></footer></article>"
    );
  }

  function setLead(html) {
    if (!lead) return;
    lead.removeAttribute("data-i18n");
    lead.innerHTML = html;
  }

  async function load() {
    try {
      const data = await window.WakeAgainAPI.listReviews(12);
      const list = (data && data.reviews) || [];
      if (list.length) {
        grid.innerHTML = list.map(cardHtml).join("");
        setLead(
          tt("reviews.lead_real", "실제 이용 후기입니다.", "Real reviews from the community.") +
            ' <a class="text-link" href="/review.html">' +
            tt("reviews.write", "후기 남기기", "Leave a review") +
            "</a>"
        );
      } else {
        grid.innerHTML = FALLBACK.map(cardHtml).join("");
        setLead(
          tt(
            "reviews.lead_few",
            "아직 공개 후기가 적어 시나리오 예시를 보여 줍니다.",
            "Few public reviews yet — showing scenario examples."
          ) +
            ' <a class="text-link" href="/review.html">' +
            tt("reviews.write_first", "첫 후기 남기기", "Write the first review") +
            "</a>"
        );
      }
    } catch (e) {
      grid.innerHTML = FALLBACK.map(cardHtml).join("");
      setLead(
        tt("reviews.lead_pre", "출시 전 시나리오 예시입니다.", "Pre-launch scenario examples.") +
          ' <a class="text-link" href="/review.html">' +
          tt("reviews.write", "후기 남기기", "Leave a review") +
          "</a>"
      );
    }
    grid.classList.add("stagger-kids");
    Array.prototype.forEach.call(grid.children, function (child, i) {
      child.style.setProperty("--si", String(i));
      child.classList.add("stagger-child", "is-in");
    });
  }

  load();
  document.addEventListener("wa:langchange", load);
  document.addEventListener("wa:currencychange", load);
})();
