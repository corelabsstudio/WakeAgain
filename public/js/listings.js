/**
 * Landing marketplace — public live auction prices for every visitor.
 * Polls /api/v1/auctions/live so rising bids are visible site-wide.
 */
(function () {
  const api = window.WakeAgainAPI;
  const grid = document.getElementById("listingGrid");
  const empty = document.getElementById("filterEmpty");
  if (!grid) return;

  /* Offline fallback — same tone as seeded demo listings */
  const PREVIEW = [
    {
      id: "preview-1",
      title: "ShopPulse",
      one_liner: "소상공인 주문·배송 알림 SaaS — 카카오톡 연동 초안",
      status: "출시됨·방치",
      listing_status: "preview",
      auction_status: "live",
      product_type: "webapp",
      product_type_label: "웹 앱 / SaaS",
      price_start: 890000,
      price_current: 1120000,
      bid_count: 4,
      cats: "saas",
      icon: "violet",
    },
    {
      id: "preview-2",
      title: "ReceiptFold",
      one_liner: "영수증 사진 → 가계부 자동 분류 모바일 베타",
      status: "베타",
      listing_status: "preview",
      auction_status: "live",
      product_type: "mobile",
      product_type_label: "모바일 앱",
      price_start: 450000,
      price_current: 450000,
      bid_count: 0,
      cats: "mobile",
      icon: "green",
    },
    {
      id: "preview-3",
      title: "MeetNotes Lite",
      one_liner: "회의 녹음 업로드 → 요약·액션 아이템 초안 웹앱",
      status: "프로토타입",
      listing_status: "preview",
      auction_status: "live",
      product_type: "webapp",
      product_type_label: "웹 앱 / SaaS",
      price_start: 320000,
      price_current: 380000,
      bid_count: 2,
      cats: "saas ai",
      icon: "purple",
    },
    {
      id: "preview-4",
      title: "csv-kit",
      one_liner: "CSV 병합·중복 제거·컬럼 매핑 CLI 도구 모음",
      status: "기타",
      listing_status: "preview",
      auction_status: "live",
      product_type: "desktop",
      product_type_label: "데스크톱 프로그램",
      price_start: 180000,
      price_current: 210000,
      bid_count: 1,
      cats: "saas",
      icon: "violet",
    },
    {
      id: "preview-5",
      title: "TraceDraft",
      one_liner: "AI 인터뷰 답변으로 블로그 초안을 뽑는 웹 도구",
      status: "베타",
      listing_status: "preview",
      auction_status: "live",
      product_type: "webapp",
      product_type_label: "웹 앱 / SaaS",
      price_start: 550000,
      price_current: 720000,
      bid_count: 5,
      cats: "saas ai",
      icon: "blue",
    },
  ];

  const ICONS = {
    purple:
      '<svg width="28" height="28" viewBox="0 0 24 24" fill="none"><rect x="3" y="7" width="18" height="12" rx="2" stroke="currentColor" stroke-width="1.6"/><circle cx="9" cy="13" r="1.5" fill="currentColor"/><path d="M14 10l5 3-5 3v-6z" fill="currentColor"/></svg>',
    violet:
      '<svg width="28" height="28" viewBox="0 0 24 24" fill="none"><path d="M8 8l-4 4 4 4M16 8l4 4-4 4M13 6l-2 12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    blue:
      '<svg width="28" height="28" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="1.6"/><circle cx="9" cy="11" r="1.2" fill="currentColor"/><circle cx="15" cy="11" r="1.2" fill="currentColor"/><path d="M9 15c1 1.2 5 1.2 6 0" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    green:
      '<svg width="28" height="28" viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="6" rx="7" ry="3" stroke="currentColor" stroke-width="1.6"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" stroke="currentColor" stroke-width="1.6"/></svg>',
  };

  function inferCats(p) {
    const blob = [p.title, p.one_liner, p.status, p.story, p.demo, (p.assets || []).join(" ")]
      .join(" ")
      .toLowerCase();
    const cats = [];
    if (/mobile|ios|android|앱|app|flutter|react native/.test(blob)) cats.push("mobile");
    if (/ai|ml|model|llm|gpt|diffusion|neural|머신|인공지능/.test(blob)) cats.push("ai");
    if (/saas|web|next|react|vue|api|대시보드|쇼핑몰|생산성/.test(blob) || !cats.length) {
      cats.push("saas");
    }
    return cats.join(" ");
  }

  function iconTone(p) {
    const cats = inferCats(p);
    if (cats.includes("ai") && cats.includes("saas")) return "purple";
    if (cats.includes("ai")) return "blue";
    if (cats.includes("mobile")) return "green";
    return "violet";
  }

  function badge(p) {
    if (p.listing_status === "preview") return { cls: "new", text: "예시" };
    const a = (p.auction_status || "live").toLowerCase();
    if (a === "sold") return { cls: "ending", text: "팔림" };
    if (a === "ended") return { cls: "draft", text: "끝남" };
    if ((p.bid_count || 0) > 0) return { cls: "live", text: "입찰 중" };
    if (p.listing_status === "pending") return { cls: "draft", text: "검토 중" };
    return { cls: "live", text: "첫 입찰 대기" };
  }

  function formatPrice(p) {
    if (p.listing_status === "preview") {
      const cur = p.price_current != null ? p.price_current : p.price_start;
      return {
        label: (p.bid_count || 0) > 0 ? "지금 가격" : "시작 가격",
        value: "₩" + Number(cur).toLocaleString("ko-KR"),
      };
    }
    const cur = p.price_current != null ? p.price_current : p.price_start;
    if (cur != null) {
      return {
        label: (p.bid_count || 0) > 0 ? "지금 가격 · 공개" : "시작 가격 · 공개",
        value: "₩" + Number(cur).toLocaleString("ko-KR"),
      };
    }
    return { label: "가격", value: "문의" };
  }

  function detailHref(p) {
    if (p.listing_status === "preview" || String(p.id).indexOf("preview") === 0) {
      return "/buy.html";
    }
    return "/project.html?id=" + encodeURIComponent(p.id);
  }

  function cardHtml(p) {
    const tone = p.icon || iconTone(p);
    const b = badge(p);
    const price = formatPrice(p);
    const href = detailHref(p);
    const cats = p.cats || inferCats(p);
    const bids = p.bid_count || 0;
    const title = escapeHtml(p.title || "Untitled");
    const line = escapeHtml(p.one_liner || "");
    const bidNote =
      bids > 0
        ? `<span class="listing-bid-note">${bids}명이 가격 씀 · 모두 공개</span>`
        : `<span class="listing-bid-note">첫 입찰 대기</span>`;
    const ptype = escapeHtml(p.product_type_label || "");
    const typeBit = ptype
      ? `<span class="listing-type-tag">${ptype}</span>`
      : "";
    return (
      `<article class="listing-card" data-cats="${escapeAttr(cats)}" data-product-type="${escapeAttr(p.product_type || "")}" data-id="${escapeAttr(String(p.id))}">` +
      `<div class="listing-icon ${tone}">${ICONS[tone] || ICONS.violet}</div>` +
      `<div class="listing-body">` +
      `<div class="listing-title-row"><h3>${title}</h3><span class="badge ${b.cls}">${b.text}</span></div>` +
      `<p>${line}</p>${typeBit}${bidNote}` +
      `<div class="listing-foot"><div><span class="label">${price.label}</span><strong data-price>${price.value}</strong></div>` +
      `<a class="btn btn-primary btn-sm" href="${href}">${bids > 0 ? "가격 쓰고 보기" : "프로젝트 자세히 보기"}</a></div>` +
      `</div></article>`
    );
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/'/g, "&#39;");
  }

  let filter = "all";
  let source = "preview";
  let cache = [];

  function applyFilter() {
    const cards = Array.prototype.slice.call(grid.querySelectorAll(".listing-card"));
    let shown = 0;
    cards.forEach(function (card) {
      const cats = (card.getAttribute("data-cats") || "").split(/\s+/);
      const ok = filter === "all" || cats.indexOf(filter) !== -1;
      card.hidden = !ok;
      if (ok) shown++;
    });
    if (empty) {
      empty.hidden = shown > 0;
      if (shown === 0) {
        empty.textContent =
          source === "api"
            ? "해당 카테고리 매물이 없습니다."
            : "해당 카테고리 예시가 없습니다.";
      }
    }
  }

  function render(list, fromApi) {
    source = fromApi ? "api" : "preview";
    cache = list.slice();
    grid.innerHTML = list.map(cardHtml).join("");
    const note = document.getElementById("listingSourceNote");
    if (note) {
      note.hidden = false;
      note.textContent = fromApi
        ? "공개 경매 · 현재가는 사이트 방문객 전원에게 실시간 공개 · 4초마다 갱신"
        : "아직 등록 매물이 없어 예시입니다. 입찰이 붙으면 현재가가 전원에게 공개됩니다.";
    }
    if (fromApi) {
      filter = "all";
      document.querySelectorAll(".listings .tab").forEach(function (btn) {
        const on = btn.getAttribute("data-filter") === "all";
        btn.classList.toggle("is-on", on);
        btn.setAttribute("aria-selected", on ? "true" : "false");
      });
    }
    applyFilter();
    updateHeroLive(pickHero(list), fromApi);
    updateTicker([]);
  }

  function heroPrice(p) {
    const n = p.price_current != null ? p.price_current : p.price_start;
    return Number(n) || 0;
  }

  /**
   * Hero card = live auction with the highest public bid (current price).
   * High number = social proof / curiosity on the landing page.
   * Tie-break: more bids, then nearer end (if known).
   */
  function pickHero(list) {
    if (!list || !list.length) return null;
    const live = list.filter(function (p) {
      return (p.auction_status || "live") === "live";
    });
    const pool = live.length ? live : list.slice();
    pool.sort(function (a, b) {
      const pd = heroPrice(b) - heroPrice(a);
      if (pd !== 0) return pd;
      const bd = (b.bid_count || 0) - (a.bid_count || 0);
      if (bd !== 0) return bd;
      const ea = a.auction_ends_at ? Date.parse(a.auction_ends_at) : Infinity;
      const eb = b.auction_ends_at ? Date.parse(b.auction_ends_at) : Infinity;
      return (isNaN(ea) ? Infinity : ea) - (isNaN(eb) ? Infinity : eb);
    });
    return pool[0];
  }

  /** Hero remaining-time: one stable countdown (not ISO date). */
  let heroCountdownId = null;
  let heroEndsKey = null;

  function fmtRemainMs(ms) {
    if (ms <= 0) return "마감";
    var sec = Math.floor(ms / 1000);
    var d = Math.floor(sec / 86400);
    sec %= 86400;
    var h = Math.floor(sec / 3600);
    sec %= 3600;
    var m = Math.floor(sec / 60);
    var s = sec % 60;
    var clock =
      String(h).padStart(2, "0") +
      ":" +
      String(m).padStart(2, "0") +
      ":" +
      String(s).padStart(2, "0");
    // Multi-day: "2일 14:22:01" — glanceable days + live clock
    if (d > 0) return d + "일 " + clock;
    return clock;
  }

  function paintHeroTimer(timer) {
    if (!timer) return;
    var ends = timer.getAttribute("data-ends-at");
    if (!ends) return;
    var end = Date.parse(ends);
    if (isNaN(end)) {
      timer.textContent = "—";
      timer.classList.remove("timer-urgent", "timer-ended");
      return;
    }
    var left = end - Date.now();
    var next = fmtRemainMs(left);
    if (timer.textContent !== next) timer.textContent = next;
    timer.classList.toggle("timer-urgent", left > 0 && left < 3600000);
    timer.classList.toggle("timer-ended", left <= 0);
    // Absolute end only on hover — never fight the countdown on screen
    timer.title =
      left > 0
        ? "마감 " + String(ends).replace("T", " ").slice(0, 16)
        : "경매 종료";
  }

  function startHeroCountdown(timer, endsAt) {
    if (!timer) return;
    // Hand off from static demo timer (data-seconds)
    timer.removeAttribute("data-seconds");
    if (!endsAt) {
      timer.removeAttribute("data-ends-at");
      heroEndsKey = null;
      if (heroCountdownId) {
        clearInterval(heroCountdownId);
        heroCountdownId = null;
      }
      return;
    }
    var key = String(endsAt);
    timer.setAttribute("data-ends-at", key);
    paintHeroTimer(timer);
    if (heroEndsKey === key && heroCountdownId) return;
    heroEndsKey = key;
    if (heroCountdownId) clearInterval(heroCountdownId);
    heroCountdownId = setInterval(function () {
      paintHeroTimer(timer);
    }, 1000);
  }

  function updateHeroLive(first, fromApi) {
    const card = document.querySelector(".live-card");
    if (!card || !first) return;
    const name = card.querySelector(".live-card-head strong");
    const sub = card.querySelector(".live-card-head p");
    const bid = card.querySelector(".live-metrics strong.mono");
    const timer = card.querySelector(".timer");
    if (name) name.textContent = first.title || "—";
    if (sub) {
      sub.textContent = fromApi
        ? (first.bid_count || 0) + "회 입찰 · " + (first.auction_status || "live")
        : first.one_liner || "";
    }
    const price = first.price_current != null ? first.price_current : first.price_start;
    if (bid && price != null) {
      const next = "₩" + Number(price).toLocaleString("ko-KR");
      if (bid.textContent !== next) {
        bid.textContent = next;
        bid.classList.add("price-flash");
        setTimeout(function () {
          bid.classList.remove("price-flash");
        }, 500);
      }
    }
    const badgeEl = card.querySelector(".live-badge");
    if (badgeEl) {
      const label =
        fromApi && (first.bid_count || 0) > 0
          ? "AUCTION LIVE"
          : fromApi
            ? "LISTED · PUBLIC"
            : "PREVIEW";
      const textEl = badgeEl.querySelector(".live-badge-text");
      if (textEl) {
        textEl.textContent = label;
      } else {
        badgeEl.innerHTML =
          '<span class="live-dot" aria-hidden="true"></span><span class="live-badge-text">' +
          label +
          "</span>";
      }
    }
    // link whole card area via toast line
    const toast = card.querySelector(".live-toast");
    if (toast && fromApi && first.id) {
      toast.innerHTML =
        '<span class="pulse-dot"></span> 현재가 전원 공개 · <a href="/project.html?id=' +
        encodeURIComponent(first.id) +
        '" style="color:inherit;text-decoration:underline">상세·입찰</a>';
    }
    // Real auction: stable HH:MM:SS (or N일 HH:MM:SS). Never show raw date in the value.
    if (timer && first.auction_ends_at) {
      startHeroCountdown(timer, first.auction_ends_at);
    } else if (timer && fromApi) {
      startHeroCountdown(timer, null);
      timer.textContent = "—";
      timer.removeAttribute("title");
      timer.classList.remove("timer-urgent", "timer-ended");
    }
  }

  function updateTicker(ticker) {
    const toast = document.querySelector(".live-toast");
    if (!toast || !ticker || !ticker.length) return;
    const t = ticker[0];
    if (!t) return;
    // keep link if present — optional secondary line only when no project link set
  }

  function patchPrices(auctions) {
    if (!auctions || !auctions.length) return;
    const byId = {};
    auctions.forEach(function (a) {
      byId[String(a.id)] = a;
    });
    grid.querySelectorAll(".listing-card[data-id]").forEach(function (card) {
      const id = card.getAttribute("data-id");
      const a = byId[id];
      if (!a) return;
      const strong = card.querySelector("[data-price]");
      const price = a.price_current != null ? a.price_current : a.price_start;
      if (strong && price != null) {
        const next = "₩" + Number(price).toLocaleString("ko-KR");
        if (strong.textContent !== next) {
          strong.textContent = next;
          strong.classList.add("price-flash");
          setTimeout(function () {
            strong.classList.remove("price-flash");
          }, 500);
        }
      }
      const note = card.querySelector(".listing-bid-note");
      if (note) {
        note.textContent =
          (a.bid_count || 0) > 0
            ? (a.bid_count || 0) + "명이 가격 씀 · 모두 공개"
            : "첫 입찰 대기";
      }
      const badgeEl = card.querySelector(".badge");
      if (badgeEl) {
        if ((a.bid_count || 0) > 0) {
          badgeEl.textContent = "입찰 중";
          badgeEl.className = "badge live";
        } else if (badgeEl.textContent === "입찰 중" || badgeEl.textContent === "판매 중") {
          badgeEl.textContent = "첫 입찰 대기";
          badgeEl.className = "badge live";
        }
      }
    });
    // merge into cache for hero
    cache = cache.map(function (p) {
      const a = byId[String(p.id)];
      return a ? Object.assign({}, p, a) : p;
    });
    updateHeroLive(pickHero(cache), source === "api");
  }

  document.querySelectorAll(".listings .tab").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".listings .tab").forEach(function (b) {
        b.classList.remove("is-on");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("is-on");
      btn.setAttribute("aria-selected", "true");
      filter = btn.getAttribute("data-filter") || "all";
      applyFilter();
    });
  });

  let pageOffset = 0;
  const PAGE = 24;
  let hasMore = false;

  async function load(reset) {
    if (!api) {
      render(PREVIEW, false);
      return;
    }
    if (reset !== false) {
      pageOffset = 0;
    }
    try {
      const data = await api.listProjects(false, PAGE, pageOffset);
      const projects = (data && data.projects) || [];
      hasMore = !!(data && data.has_more);
      if (pageOffset === 0) {
        if (projects.length) render(projects, true);
        else render(PREVIEW, false);
      } else if (projects.length && source === "api") {
        cache = cache.concat(projects);
        grid.innerHTML = cache.map(cardHtml).join("");
        applyFilter();
      }
      pageOffset += projects.length;
      var moreBtn = document.getElementById("listingsMore");
      if (moreBtn) moreBtn.hidden = !(source === "api" && hasMore);
    } catch (e) {
      console.warn("listings", e);
      if (pageOffset === 0) render(PREVIEW, false);
    }
  }

  async function pollLive() {
    if (!api || source !== "api") return;
    try {
      const live = await api.liveAuctions();
      if (live && live.auctions) patchPrices(live.auctions);
      if (live && live.ticker && live.ticker.length) {
        const t = live.ticker[0];
        const toast = document.querySelector(".live-toast");
        if (toast && t) {
          toast.innerHTML =
            '<span class="pulse-dot"></span> 방금 입찰 · ₩' +
            Number(t.amount).toLocaleString("ko-KR") +
            " · " +
            (t.bidder_label || "") +
            ' · <a href="/project.html?id=' +
            encodeURIComponent(t.project_id) +
            '" style="color:inherit;text-decoration:underline">보기</a>';
        }
      }
    } catch (e) {
      /* quiet */
    }
  }

  load(true).then(function () {
    setInterval(pollLive, 4000);
    pollLive();
  });
  var moreEl = document.getElementById("listingsMore");
  if (moreEl) {
    moreEl.addEventListener("click", function () {
      load(false);
    });
  }
})();
