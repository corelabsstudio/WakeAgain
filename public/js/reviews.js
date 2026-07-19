/**
 * Landing testimonials — approved reviews from API, fallback to scenario cards.
 */
(function () {
  const grid = document.querySelector("#stories .testi-grid");
  const lead = document.querySelector("#stories .center-lead");
  if (!grid || !window.WakeAgainAPI) return;

  const FALLBACK = [
    {
      author_name: "김도윤",
      role_label: "백엔드 개발자 · 사이드 프로젝트 2년차",
      body:
        "주말마다 붙잡던 예약 관리 SaaS를 11주 만들고, 유저는 7명에서 멈췄습니다. WakeAgain에는 데모와 “왜 멈췄는지”만 적었는데, 시작가 45만 원으로 올리고 관심이 붙었습니다.",
      sold_price: null,
      side: "seller",
      _scenario: true,
    },
    {
      author_name: "이수현",
      role_label: "인디 메이커 · 전 스타트업 프로덕트",
      body:
        "처음부터 만들면 최소 6주는 잡는 계획이었습니다. 데모가 있는 프로토타입을 보고 현재가와 남은 시간을 확인한 뒤 판단할 수 있었습니다.",
      sold_price: null,
      side: "buyer",
      _scenario: true,
    },
  ];

  function won(n) {
    if (n == null || n === "") return "";
    return "₩" + Number(n).toLocaleString("ko-KR");
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function cardHtml(r) {
    const side = r.side === "buyer" ? "구매" : "판매";
    const price = won(r.sold_price);
    const accent = price
      ? "<p class='quote-accent'>성사가 <strong>" + price + "</strong> · " + side + "</p>"
      : r._scenario
        ? "<p class='quote-accent'>시나리오 예시</p>"
        : "<p class='quote-accent'>" + side + " 후기</p>";
    return (
      "<article class='glass-card testi-card'>" +
      "<div class='quote-mark' aria-hidden='true'>99</div>" +
      "<p>" +
      escapeHtml(r.body) +
      "</p>" +
      accent +
      "<footer class='testi-foot'><strong>" +
      escapeHtml(r.author_name) +
      "</strong><span>" +
      escapeHtml(r.role_label || (r.side === "buyer" ? "구매자" : "판매자")) +
      "</span></footer></article>"
    );
  }

  async function load() {
    try {
      const data = await window.WakeAgainAPI.listReviews(12);
      const list = (data && data.reviews) || [];
      if (list.length) {
        grid.innerHTML = list.map(cardHtml).join("");
        if (lead) {
          lead.innerHTML =
            '실제 이용 후기입니다. <a class="text-link" href="/review.html">후기 남기기</a>';
        }
      } else {
        grid.innerHTML = FALLBACK.map(cardHtml).join("");
        if (lead) {
          lead.innerHTML =
            '아직 공개 후기가 적어 시나리오 예시를 보여 줍니다. <a class="text-link" href="/review.html">첫 후기 남기기</a>';
        }
      }
    } catch (e) {
      grid.innerHTML = FALLBACK.map(cardHtml).join("");
      if (lead) {
        lead.innerHTML =
          '출시 전 시나리오 예시입니다. <a class="text-link" href="/review.html">후기 남기기</a>';
      }
    }
    // re-trigger reveal if already scrolled
    grid.classList.add("stagger-kids");
    Array.prototype.forEach.call(grid.children, function (child, i) {
      child.style.setProperty("--si", String(i));
      child.classList.add("stagger-child", "is-in");
    });
  }

  load();
})();
