/**
 * Landing marketplace — public live auction prices for every visitor.
 * Polls /api/v1/auctions/live so rising bids are visible site-wide.
 */
(function () {
  const api = window.WakeAgainAPI;
  const grid = document.getElementById("listingGrid");
  const empty = document.getElementById("filterEmpty");
  if (!grid) return;

  /* Offline fallback — bilingual sample copy */
  const PREVIEW = [
    {
      id: "preview-1",
      title: "ShopPulse",
      one_liner: "소상공인 주문·배송 알림 SaaS — 카카오톡 연동 초안",
      one_liner_en: "Order & shipping alerts for small shops — KakaoTalk draft",
      status: "출시됨·방치",
      status_en: "Launched · idle",
      listing_status: "preview",
      auction_status: "live",
      product_type: "webapp",
      keywords: ["SaaS", "카카오", "주문", "알림", "소상공인"],
      price_start: 890000,
      price_current: 1120000,
      bid_count: 4,
      bidder_count: 4,
      cats: "saas",
      icon: "violet",
    },
    {
      id: "preview-2",
      title: "ReceiptFold",
      one_liner: "영수증 사진 → 가계부 자동 분류 모바일 베타",
      one_liner_en: "Receipt photo → auto expense categories · mobile beta",
      status: "베타",
      status_en: "Beta",
      listing_status: "preview",
      auction_status: "live",
      product_type: "mobile",
      keywords: ["가계부", "영수증", "OCR", "모바일앱", "Flutter"],
      price_start: 450000,
      price_current: 450000,
      bid_count: 0,
      bidder_count: 0,
      cats: "mobile",
      icon: "green",
    },
    {
      id: "preview-3",
      title: "MeetNotes Lite",
      one_liner: "회의 녹음 업로드 → 요약·액션 아이템 초안 웹앱",
      one_liner_en: "Upload meeting audio → summary & action items draft",
      status: "프로토타입",
      status_en: "Prototype",
      listing_status: "preview",
      auction_status: "live",
      product_type: "webapp",
      keywords: ["회의", "요약", "AI", "웹앱", "Whisper"],
      price_start: 320000,
      price_current: 380000,
      bid_count: 2,
      bidder_count: 2,
      cats: "saas ai",
      icon: "purple",
    },
    {
      id: "preview-4",
      title: "csv-kit",
      one_liner: "CSV 병합·중복 제거·컬럼 매핑 CLI 도구 모음",
      one_liner_en: "CSV merge, dedupe & column-mapping CLI toolkit",
      status: "기타",
      status_en: "Other",
      listing_status: "preview",
      auction_status: "live",
      product_type: "desktop",
      keywords: ["CSV", "데이터", "CLI", "Python", "도구"],
      price_start: 180000,
      price_current: 210000,
      bid_count: 1,
      bidder_count: 1,
      cats: "saas",
      icon: "violet",
    },
    {
      id: "preview-5",
      title: "TraceDraft",
      one_liner: "AI 인터뷰 답변으로 블로그 초안을 뽑는 웹 도구",
      one_liner_en: "AI interview answers → blog draft web tool",
      status: "베타",
      status_en: "Beta",
      listing_status: "preview",
      auction_status: "live",
      product_type: "webapp",
      keywords: ["AI", "블로그", "콘텐츠", "웹앱", "초안"],
      price_start: 550000,
      price_current: 720000,
      bid_count: 5,
      bidder_count: 5,
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

  function isEn() {
    return !!(window.WakeAgainI18n && window.WakeAgainI18n.getLang && window.WakeAgainI18n.getLang() === "en");
  }

  function tt(key, fallback) {
    try {
      if (window.WakeAgainI18n && window.WakeAgainI18n.t) {
        var v = window.WakeAgainI18n.t(key);
        if (v && v !== key) return v;
      }
    } catch (e) {}
    return fallback;
  }

  function money(n) {
    if (window.WakeAgainI18n && window.WakeAgainI18n.formatMoney) {
      return window.WakeAgainI18n.formatMoney(n);
    }
    return "₩" + Number(n).toLocaleString(isEn() ? "en-US" : "ko-KR");
  }

  var TYPE_LABEL = {
    website: { ko: "웹사이트", en: "Website" },
    webapp: { ko: "웹 앱 / SaaS", en: "Web app / SaaS" },
    mobile: { ko: "모바일 앱", en: "Mobile app" },
    desktop: { ko: "데스크톱 프로그램", en: "Desktop" },
    api: { ko: "API / SDK / 백엔드", en: "API / SDK / backend" },
    game: { ko: "게임", en: "Game" },
    other: { ko: "기타", en: "Other" },
  };

  var STATUS_LABEL = {
    prototype: { ko: "돌아가는 초안", en: "Working prototype" },
    beta: { ko: "써 볼 수 있는 제품", en: "Usable product" },
    launched: { ko: "공개했다가 멈춤", en: "Launched, then paused" },
    other: { ko: "그 외 (도구·코드·자료)", en: "Other (tools · code · assets)" },
  };

  function typeLabel(p) {
    if (isEn() && p.product_type_label_en) return p.product_type_label_en;
    var code = (p.product_type || "").toLowerCase();
    if (TYPE_LABEL[code]) return isEn() ? TYPE_LABEL[code].en : TYPE_LABEL[code].ko;
    return p.product_type_label || "";
  }

  function statusLabel(p) {
    if (isEn() && p.status_label_en) return p.status_label_en;
    var key = String(p.status || p.status_key || "").toLowerCase();
    if (STATUS_LABEL[key]) return isEn() ? STATUS_LABEL[key].en : STATUS_LABEL[key].ko;
    return p.status_label || p.status || "";
  }

  function oneLiner(p) {
    if (isEn() && p.one_liner_en) return p.one_liner_en;
    return p.one_liner || "";
  }

  function storyText(p) {
    if (isEn() && p.story_en) return p.story_en;
    return p.story || "";
  }

  function badge(p) {
    if (p.listing_status === "preview") return { cls: "new", text: tt("list.badge_sample", isEn() ? "Sample" : "예시") };
    const a = (p.auction_status || "live").toLowerCase();
    if (a === "sold") return { cls: "ending", text: tt("list.badge_sold", isEn() ? "Sold" : "팔림") };
    if (a === "ended") return { cls: "draft", text: tt("list.badge_ended", isEn() ? "Ended" : "끝남") };
    if (bidderCount(p) > 0) return { cls: "live", text: tt("list.badge_live", isEn() ? "Bidding" : "입찰 중") };
    if (p.listing_status === "pending") return { cls: "draft", text: tt("list.badge_review", isEn() ? "In review" : "검토 중") };
    return { cls: "live", text: tt("list.badge_wait", isEn() ? "Awaiting first bid" : "첫 입찰 대기") };
  }

  /** Unique people who bid (not total bid events). */
  function bidderCount(p) {
    if (p == null) return 0;
    if (p.bidder_count != null) return Number(p.bidder_count) || 0;
    return Number(p.bid_count) || 0;
  }

  function formatPrice(p) {
    var en = isEn();
    if (p.listing_status === "preview") {
      const cur = p.price_current != null ? p.price_current : p.price_start;
      return {
        label: bidderCount(p) > 0 ? tt("list.price_now", en ? "Current" : "지금 가격") : tt("list.price_start", en ? "Start" : "시작 가격"),
        value: money(cur),
      };
    }
    const cur = p.price_current != null ? p.price_current : p.price_start;
    if (cur != null) {
      return {
        label:
          bidderCount(p) > 0
            ? tt("list.price_now_pub", en ? "Current · public" : "지금 가격 · 공개")
            : tt("list.price_start_pub", en ? "Start · public" : "시작 가격 · 공개"),
        value: money(cur),
      };
    }
    return { label: tt("list.price", en ? "Price" : "가격"), value: tt("list.inquire", en ? "Inquire" : "문의") };
  }

  function detailHref(p) {
    var path;
    if (p.listing_status === "preview" || String(p.id).indexOf("preview") === 0) {
      path = "/buy.html";
    } else {
      path = "/project.html?id=" + encodeURIComponent(p.id);
    }
    if (window.WakeAgainAPI && window.WakeAgainAPI.pageUrl) {
      return window.WakeAgainAPI.pageUrl(path);
    }
    return path;
  }

  function bidNoteText(bidders, top) {
    if (bidders > 0) {
      const base = isEn()
        ? bidders + " bidders · public"
        : bidders + "명 입찰 · 모두 공개";
      if (top && top.label) {
        const rank = top.buyer_rank && top.buyer_rank.label ? " · " + top.buyer_rank.label : "";
        return isEn()
          ? "Lead " + top.label + rank + " · " + base
          : "최고 " + top.label + rank + " · " + base;
      }
      return base;
    }
    return tt("list.badge_wait", isEn() ? "Awaiting first bid" : "첫 입찰 대기");
  }

  function keywordsOf(p) {
    const raw = p && p.keywords;
    if (!raw || !raw.length) return [];
    return raw.map(function (k) {
      return String(k).trim();
    }).filter(Boolean).slice(0, 5);
  }

  function keywordsHtml(p) {
    const kws = keywordsOf(p);
    if (!kws.length) return "";
    return (
      '<div class="listing-kw">' +
      kws
        .map(function (k) {
          return '<span class="listing-kw-tag">#' + escapeHtml(k) + "</span>";
        })
        .join("") +
      "</div>"
    );
  }

  function cardHtml(p) {
    const tone = p.icon || iconTone(p);
    const b = badge(p);
    const price = formatPrice(p);
    const href = detailHref(p);
    const cats = p.cats || inferCats(p);
    const bids = bidderCount(p);
    const title = escapeHtml(p.title || "Untitled");
    const line = escapeHtml(oneLiner(p));
    const st = escapeHtml(statusLabel(p));
    const top = p.top_bidder || null;
    const bidNote = `<span class="listing-bid-note">${escapeHtml(bidNoteText(bids, top))}</span>`;
    const ptype = escapeHtml(typeLabel(p));
    const typeBit =
      (ptype ? `<span class="listing-type-tag">${ptype}</span>` : "") +
      (st ? `<span class="listing-type-tag">${st}</span>` : "");
    const cta =
      bids > 0
        ? tt("list.cta_bid", isEn() ? "Bid & view" : "가격 쓰고 보기")
        : tt("list.cta_view", isEn() ? "View project" : "프로젝트 자세히 보기");
    const searchBlob = escapeAttr(
      [p.title, p.one_liner, p.one_liner_en, (p.keywords || []).join(" "), p.story]
        .join(" ")
        .toLowerCase()
    );
    return (
      `<article class="listing-card" data-cats="${escapeAttr(cats)}" data-product-type="${escapeAttr(p.product_type || "")}" data-id="${escapeAttr(String(p.id))}" data-search="${searchBlob}">` +
      `<div class="listing-icon ${tone}">${ICONS[tone] || ICONS.violet}</div>` +
      `<div class="listing-body">` +
      `<div class="listing-title-row"><h3>${title}</h3><span class="badge ${b.cls}">${b.text}</span></div>` +
      `<p>${line}</p>${keywordsHtml(p)}${typeBit}${bidNote}` +
      `<div class="listing-foot"><div><span class="label">${price.label}</span><strong data-price data-money-krw="${escapeAttr(String(p.price_current != null ? p.price_current : p.price_start || 0))}">${price.value}</strong></div>` +
      `<a class="btn btn-primary btn-sm" href="${href}">${cta}</a></div>` +
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
  let searchQ = "";

  function applyFilter() {
    const cards = Array.prototype.slice.call(grid.querySelectorAll(".listing-card"));
    const q = (searchQ || "").trim().toLowerCase();
    let shown = 0;
    cards.forEach(function (card) {
      const cats = (card.getAttribute("data-cats") || "").split(/\s+/);
      const catOk = filter === "all" || cats.indexOf(filter) !== -1;
      const blob = (card.getAttribute("data-search") || card.textContent || "").toLowerCase();
      const qOk = !q || blob.indexOf(q) !== -1;
      const ok = catOk && qOk;
      card.hidden = !ok;
      if (ok) shown++;
    });
    if (empty) {
      empty.hidden = shown > 0;
      if (shown === 0) {
        if (q) {
          empty.textContent = tt(
            "list.empty_search",
            isEn() ? "No matches. Try another keyword." : "검색 결과가 없습니다. 다른 키워드를 시도해 보세요."
          );
        } else {
          empty.textContent =
            source === "api"
              ? tt("list.empty_cat", isEn() ? "No listings in this category." : "해당 카테고리 매물이 없습니다.")
              : tt("list.empty_sample", isEn() ? "No samples in this category." : "해당 카테고리 예시가 없습니다.");
        }
      }
    }
  }

  function syncSearchClear() {
    const clearBtn = document.getElementById("listingSearchClear");
    if (clearBtn) clearBtn.hidden = !(searchQ && searchQ.trim());
  }

  function sourceNoteText(fromApi) {
    return fromApi
      ? tt(
          "list.source_api",
          isEn()
            ? "Live auction · current price public to every visitor · refreshes every 4s"
            : "공개 경매 · 현재가는 사이트 방문객 전원에게 실시간 공개 · 4초마다 갱신"
        )
      : tt(
          "list.source_preview",
          isEn()
            ? "No live listings yet — samples shown. Live prices go public once bidding starts."
            : "아직 등록 매물이 없어 예시입니다. 입찰이 붙으면 현재가가 전원에게 공개됩니다."
        );
  }

  function render(list, fromApi) {
    source = fromApi ? "api" : "preview";
    cache = list.slice();
    grid.innerHTML = list.map(cardHtml).join("");
    const note = document.getElementById("listingSourceNote");
    if (note) {
      note.hidden = false;
      note.removeAttribute("data-i18n");
      note.textContent = sourceNoteText(fromApi);
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
      const bd = bidderCount(b) - bidderCount(a);
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
    if (ms <= 0) return tt("list.ended_short", isEn() ? "Ended" : "마감");
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
    // Multi-day: "2d 14:22:01" / "2일 14:22:01"
    if (d > 0) return d + (isEn() ? "d " : "일 ") + clock;
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
        ? (isEn() ? "Ends " : "마감 ") + String(ends).replace("T", " ").slice(0, 16)
        : tt("list.auction_ended", isEn() ? "Auction ended" : "경매 종료");
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
      if (fromApi) {
        var bc = bidderCount(first);
        sub.textContent = isEn()
          ? bc + " bidders · " + (first.auction_status || "live")
          : bc + "명 입찰 · " + (first.auction_status || "live");
      } else {
        sub.textContent = oneLiner(first);
      }
    }
    const price = first.price_current != null ? first.price_current : first.price_start;
    if (bid && price != null) {
      const next = money(price);
      if (bid.textContent !== next) {
        bid.textContent = next;
        bid.classList.add("price-flash");
        setTimeout(function () {
          bid.classList.remove("price-flash");
        }, 500);
        // Green ECG spike — bid = heartbeat of a living project
        if (window.WakeAgainHeroEcg && window.WakeAgainHeroEcg.spike) {
          window.WakeAgainHeroEcg.spike(1);
        }
      }
    }
    const badgeEl = card.querySelector(".live-badge");
    if (badgeEl) {
      const label =
        fromApi && bidderCount(first) > 0
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
        '<span class="pulse-dot"></span> ' +
        (isEn() ? "Live price public · " : "현재가 전원 공개 · ") +
        '<a href="/project.html?id=' +
        encodeURIComponent(first.id) +
        '" style="color:inherit;text-decoration:underline">' +
        (isEn() ? "Details & bid" : "상세·입찰") +
        "</a>";
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
        const next = money(price);
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
        note.textContent = bidNoteText(bidderCount(a));
      }
      const badgeEl = card.querySelector(".badge");
      if (badgeEl) {
        if (bidderCount(a) > 0) {
          badgeEl.textContent = tt("list.badge_live", isEn() ? "Bidding" : "입찰 중");
          badgeEl.className = "badge live";
        } else if (
          badgeEl.textContent === "입찰 중" ||
          badgeEl.textContent === "Bidding" ||
          badgeEl.textContent === "판매 중"
        ) {
          badgeEl.textContent = tt("list.badge_wait", isEn() ? "Awaiting first bid" : "첫 입찰 대기");
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
      applyFilter();
      return;
    }
    if (reset !== false) {
      pageOffset = 0;
    }
    try {
      const data = await api.listProjects(false, PAGE, pageOffset, searchQ);
      const projects = (data && data.projects) || [];
      hasMore = !!(data && data.has_more);
      if (pageOffset === 0) {
        if (projects.length) {
          render(projects, true);
        } else if (searchQ && searchQ.trim()) {
          // Active search with zero hits — don't fall back to sample cards
          source = "api";
          cache = [];
          grid.innerHTML = "";
          if (empty) {
            empty.hidden = false;
            empty.textContent = tt(
              "list.empty_search",
              isEn() ? "No matches. Try another keyword." : "검색 결과가 없습니다. 다른 키워드를 시도해 보세요."
            );
          }
          updateHeroLive(null, true);
        } else {
          render(PREVIEW, false);
        }
      } else if (projects.length && source === "api") {
        cache = cache.concat(projects);
        grid.innerHTML = cache.map(cardHtml).join("");
        applyFilter();
      }
      pageOffset += projects.length;
      var moreBtn = document.getElementById("listingsMore");
      if (moreBtn) moreBtn.hidden = !(source === "api" && hasMore);
      syncSearchClear();
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
            '<span class="pulse-dot"></span> ' +
            (isEn() ? "New bid · " : "방금 입찰 · ") +
            money(t.amount) +
            " · " +
            (t.bidder_label || "") +
            ' · <a href="' +
            (window.WakeAgainAPI && window.WakeAgainAPI.pageUrl
              ? window.WakeAgainAPI.pageUrl("/project.html?id=" + encodeURIComponent(t.project_id))
              : "/project.html?id=" + encodeURIComponent(t.project_id)) +
            '" style="color:inherit;text-decoration:underline">' +
            (isEn() ? "view" : "보기") +
            "</a>";
        }
      }
    } catch (e) {
      /* quiet */
    }
  }

  function rerenderForLocale() {
    if (cache && cache.length) {
      grid.innerHTML = cache.map(cardHtml).join("");
      applyFilter();
      var note = document.getElementById("listingSourceNote");
      if (note) {
        note.removeAttribute("data-i18n");
        note.textContent = sourceNoteText(source === "api");
      }
      updateHeroLive(pickHero(cache), source === "api");
    }
  }
  document.addEventListener("wa:langchange", rerenderForLocale);
  document.addEventListener("wa:currencychange", rerenderForLocale);

  var searchForm = document.getElementById("listingSearchForm");
  var searchInput = document.getElementById("listingSearchQ");
  var searchClear = document.getElementById("listingSearchClear");
  if (searchForm && searchInput) {
    searchForm.addEventListener("submit", function (e) {
      e.preventDefault();
      searchQ = (searchInput.value || "").trim();
      syncSearchClear();
      load(true);
    });
  }
  if (searchClear && searchInput) {
    searchClear.addEventListener("click", function () {
      searchQ = "";
      searchInput.value = "";
      syncSearchClear();
      load(true);
    });
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
