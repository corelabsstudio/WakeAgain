/**
 * Landing marketplace — public live auction prices for every visitor.
 * Polls /api/v1/auctions/live so rising bids are visible site-wide.
 */
(function () {
  const api = window.WakeAgainAPI;
  const grid = document.getElementById("listingGrid");
  const empty = document.getElementById("filterEmpty");
  if (!grid) return;

  /* No fake/sample listings — empty market shows empty state only. */

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
    try {
      if (window.WakeAgainI18n && window.WakeAgainI18n.getLang) {
        var L = window.WakeAgainI18n.getLang();
        if (L === "en" || L === "ko") return L === "en";
      }
    } catch (e0) {}
    try {
      var htmlLang = String(document.documentElement.getAttribute("data-wa-lang") || document.documentElement.lang || "").toLowerCase();
      if (htmlLang.indexOf("en") === 0) return true;
      if (htmlLang.indexOf("ko") === 0) return false;
    } catch (e1) {}
    try {
      var q = new URLSearchParams(location.search || "").get("lang");
      if (q === "en") return true;
      if (q === "ko") return false;
    } catch (e2) {}
    try {
      var saved = localStorage.getItem("wa_lang");
      if (saved === "en") return true;
      if (saved === "ko") return false;
    } catch (e3) {}
    // Global-first default when nothing says Korean
    return true;
  }

  function hasHangul(s) {
    return /[\uac00-\ud7a3]/.test(String(s || ""));
  }

  var CREDIT_LABEL_EN = {
    \ucd5c\uace0: "Elite",
    \uc6b0\uc218: "Good",
    \uc2e0\ub8b0: "Trusted",
    \ubcf4\ud1b5: "Average",
    \uc2e0\uaddc: "New",
    \uc8fc\uc758: "Caution",
    \uc704\ud5d8: "Risk",
    \uc77c\ubc18: "Standard",
    \ucd5c\uc6b0\uc218: "Excellent",
    // buyer rank
    "\ud30c\uc6cc \ubc14\uc774\uc5b4": "Power buyer",
    "\ud5e4\ube44 \uad6c\ub9e4\uc790": "Heavy buyer",
    "\ub2e8\uace8 \uad6c\ub9e4\uc790": "Regular buyer",
    "\uccab \uad6c\ub9e4 \uc644\ub8cc": "First purchase",
    "\uad6c\ub9e4 \uc900\ube44 \uc911": "Getting ready",
  };

  function creditLabelUi(label) {
    if (label == null || label === "") return "";
    var cl = String(label);
    if (!isEn()) return cl;
    return CREDIT_LABEL_EN[cl] || cl;
  }

  function latinBits(s) {
    var m = String(s || "").match(/[A-Za-z][A-Za-z0-9+.#\-]*/g);
    if (!m || !m.length) return "";
    // de-dupe keep order
    var out = [];
    var seen = {};
    m.forEach(function (w) {
      var k = w.toLowerCase();
      if (seen[k]) return;
      seen[k] = 1;
      out.push(w);
    });
    return out.join(" ").trim();
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
    // Global-first fallback when i18n not loaded yet
    return "$" + Math.round(Number(n) / 1350).toLocaleString("en-US");
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

  function listingTitle(p) {
    var raw = (p && p.title) || "";
    if (!isEn()) return raw;
    var en = (p && p.title_en) || "";
    if (en && String(en).trim()) return String(en).trim();
    // Client fallback: keep brand tokens (Trace, ReachKit) if KO title lacks title_en yet
    var bits = latinBits(raw);
    if (bits) return bits;
    return raw;
  }

  function oneLiner(p) {
    var raw = (p && p.one_liner) || "";
    if (!isEn()) return raw;
    var en = (p && p.one_liner_en) || "";
    if (en && String(en).trim() && !/paused project marketplace listing|demo-ready side project/i.test(en)) {
      return String(en).trim();
    }
    if (en && String(en).trim() && !hasHangul(en)) return String(en).trim();
    // Prefer non-Hangul fragments from KO one-liner when EN copy still weak
    var bits = latinBits(raw);
    if (bits && bits.length >= 4) return bits;
    if (en && String(en).trim()) return String(en).trim();
    return raw;
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
    if (bidderCount(p) > 0) return { cls: "live", text: tt("list.badge_live", isEn() ? "Live" : "입찰 중") };
    if (p.listing_status === "pending") return { cls: "draft", text: tt("list.badge_review", isEn() ? "Under review" : "검토 중") };
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
            ? tt("list.price_now_pub", en ? "Current bid · public" : "지금 가격 · 공개")
            : tt("list.price_start_pub", en ? "Starting bid · public" : "시작 가격 · 공개"),
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
        const rank = top.buyer_rank && top.buyer_rank.label ? " · " + creditLabelUi(top.buyer_rank.label) : "";
        return isEn()
          ? "Lead " + creditLabelUi(top.label) + rank + " · " + base
          : "최고 " + top.label + rank + " · " + base;
      }
      return base;
    }
    return tt("list.badge_wait", isEn() ? "Awaiting first bid" : "첫 입찰 대기");
  }

  function keywordsOf(p) {
    var localized = isEn()
      ? (p && Array.isArray(p.keywords_en) && p.keywords_en.length ? p.keywords_en : p && p.keywords)
      : (p && Array.isArray(p.keywords_ko) && p.keywords_ko.length ? p.keywords_ko : p && p.keywords);
    if (!localized || !localized.length) return [];
    var list = localized.map(function (k) {
      return String(k).trim();
    }).filter(Boolean);
    if (isEn()) {
      // Translated tags win; if none were available, fall back to dropping pure Hangul tags
      var enOnly = list.filter(function (k) {
        return !hasHangul(k);
      });
      if (enOnly.length) list = enOnly;
    }
    return list.slice(0, 5);
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
    const title = escapeHtml(listingTitle(p) || "Untitled");
    const line = escapeHtml(oneLiner(p));
    const st = escapeHtml(statusLabel(p));
    const top = p.top_bidder || null;
    const bidNote = `<span class="listing-bid-note">${escapeHtml(bidNoteText(bids, top))}</span>`;
    const ptype = escapeHtml(typeLabel(p));
    const flag =
      window.WakeAgainCountries && p.seller_country
        ? window.WakeAgainCountries.flagEmoji(p.seller_country)
        : "";
    const flagBit = flag
      ? `<span class="listing-type-tag" title="${escapeAttr(window.WakeAgainCountries.countryName(p.seller_country))}">${flag}</span>`
      : "";
    const enReadyBit = p.english_ready
      ? `<span class="listing-type-tag listing-type-tag-en" title="${escapeAttr(tt("list.english_ready_title", isEn() ? "Seller says the product UI works in English" : "판매자가 밝힌: 제품 UI 영어 지원"))}">🌐 ${escapeHtml(tt("list.english_ready", isEn() ? "EN UI" : "영어 UI"))}</span>`
      : "";
    const typeBit =
      flagBit +
      enReadyBit +
      (ptype ? `<span class="listing-type-tag">${ptype}</span>` : "") +
      (st ? `<span class="listing-type-tag">${st}</span>` : "");
    const cta =
      bids > 0
        ? tt("list.cta_bid", isEn() ? "Place bid" : "가격 쓰고 보기")
        : tt("list.cta_view", isEn() ? "View listing" : "프로젝트 자세히 보기");
    const searchBlob = escapeAttr(
      [p.title, p.title_en, p.one_liner, p.one_liner_en, (p.keywords || []).join(" "), p.story]
        .join(" ")
        .toLowerCase()
    );
    const thumbSrc = Array.isArray(p.demo_images) && p.demo_images.length ? p.demo_images[0] : null;
    const mediaInner = thumbSrc
      ? `<img class="lot-card-thumb" src="${escapeAttr(thumbSrc)}" alt="${title}" decoding="async" />`
      : `<div class="listing-icon ${tone}">${ICONS[tone] || ICONS.violet}</div>`;
    return (
      `<article class="listing-card lot-card" data-cats="${escapeAttr(cats)}" data-product-type="${escapeAttr(p.product_type || "")}" data-id="${escapeAttr(String(p.id))}" data-search="${searchBlob}">` +
      `<div class="lot-card-media${thumbSrc ? " has-thumb" : ""}">` +
      mediaInner +
      `<span class="badge ${b.cls}">${b.text}</span>` +
      `</div>` +
      `<div class="listing-body">` +
      `<h3 class="lot-card-title">${title}</h3>` +
      `<p class="lot-card-line">${line}</p>` +
      `<div class="lot-card-meta">${typeBit}${keywordsHtml(p)}${bidNote}</div>` +
      `<div class="listing-foot">` +
      `<div class="lot-card-price"><span class="label">${price.label}</span>` +
      `<strong data-price data-money-krw="${escapeAttr(String(p.price_current != null ? p.price_current : p.price_start || 0))}">${price.value}</strong></div>` +
      `<a class="btn btn-primary btn-sm lot-card-cta" href="${href}">${cta}</a>` +
      `</div></div></article>`
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

  function sourceNoteText(fromApi, isEmpty) {
    if (isEmpty) {
      return tt(
        "list.source_empty",
        isEn()
          ? "No live listings yet. Be the first to list a project."
          : "아직 공개 매물이 없습니다. 첫 매물을 올려 보세요."
      );
    }
    return fromApi
      ? tt(
          "list.source_api",
          isEn()
            ? "Live auction · current price public to every visitor · refreshes every 4s"
            : "공개 경매 · 현재가는 사이트 방문객 전원에게 실시간 공개 · 4초마다 갱신"
        )
      : tt(
          "list.source_loading",
          isEn() ? "Loading listings…" : "매물을 불러오는 중…"
        );
  }

  function showEmptyMarket(message) {
    source = "api";
    cache = [];
    grid.innerHTML = "";
    if (empty) {
      empty.hidden = false;
      empty.textContent =
        message ||
        tt(
          "list.empty_market",
          isEn()
            ? "No listings yet. List a project for free."
            : "등록된 매물이 없습니다. 무료로 프로젝트를 올려 보세요."
        );
    }
    const note = document.getElementById("listingSourceNote");
    if (note) {
      note.hidden = false;
      note.removeAttribute("data-i18n");
      note.textContent = sourceNoteText(true, true);
    }
    updateHeroLive(null, true);
    var moreBtn = document.getElementById("listingsMore");
    if (moreBtn) moreBtn.hidden = true;
  }

  function render(list, fromApi) {
    source = fromApi ? "api" : "preview";
    cache = list.slice();
    if (!list.length) {
      showEmptyMarket();
      return;
    }
    if (empty) empty.hidden = true;
    grid.innerHTML = list.map(cardHtml).join("");
    const note = document.getElementById("listingSourceNote");
    if (note) {
      note.hidden = false;
      note.removeAttribute("data-i18n");
      note.textContent = sourceNoteText(fromApi, false);
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
    if (!card) return;
    const name = card.querySelector(".live-card-head strong");
    const sub = card.querySelector(".live-card-head p");
    const bid = card.querySelector(".live-metrics strong.mono");
    const timer = card.querySelector(".timer");
    const icon = card.querySelector(".live-icon");
    if (!first) {
      if (name) name.textContent = tt("live.empty_title", isEn() ? "No live auction" : "진행 중 매물 없음");
      if (sub) {
        sub.textContent = tt(
          "live.empty_sub",
          isEn() ? "List a project to appear here" : "매물이 등록되면 여기에 표시됩니다"
        );
      }
      if (bid) {
        bid.textContent = "—";
        bid.removeAttribute("data-money-krw");
      }
      if (icon) icon.textContent = "—";
      const badgeEl = card.querySelector(".live-badge");
      if (badgeEl) {
        const textEl = badgeEl.querySelector(".live-badge-text");
        const label = tt("live.empty_badge", isEn() ? "WAITING" : "대기 중");
        if (textEl) textEl.textContent = label;
      }
      if (timer) {
        startHeroCountdown(timer, null);
        timer.textContent = "—";
        timer.removeAttribute("data-seconds");
        timer.removeAttribute("title");
        timer.classList.remove("timer-urgent", "timer-ended");
      }
      var progP = card.querySelector(".live-progress p");
      if (progP) {
        progP.textContent = tt(
          "live.empty_progress",
          isEn() ? "Open market · free to list" : "마켓 오픈 · 등록 무료"
        );
        progP.removeAttribute("data-i18n");
      }
      var progBar = card.querySelector(".live-progress-bar span");
      if (progBar) progBar.style.setProperty("--w", "0%");
      const toast = card.querySelector(".live-toast");
      if (toast) {
        toast.innerHTML =
          '<span class="pulse-dot"></span> ' +
          '<a href="/sell.html" style="color:inherit;text-decoration:underline">' +
          (isEn() ? "List a project" : "매물 등록하기") +
          "</a>";
      }
      return;
    }
    var liveTitle = listingTitle(first) || first.title || "—";
    if (name) name.textContent = liveTitle;
    if (icon) icon.textContent = (liveTitle || "?").trim().charAt(0).toUpperCase() || "—";
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

    // Progress line: show real start price + bidder count (not vague "vs start")
    var progP = card.querySelector(".live-progress p");
    var progBar = card.querySelector(".live-progress-bar span");
    var start = first.price_start != null ? Number(first.price_start) : null;
    var cur =
      first.price_current != null ? Number(first.price_current) : start;
    var bidders = bidderCount(first);
    if (progP) {
      var en = isEn();
      var startTxt = start != null && !isNaN(start) ? money(start) : "—";
      if (en) {
        progP.textContent =
          "Start " + startTxt + " · " + bidders + " bidder" + (bidders === 1 ? "" : "s");
      } else {
        progP.textContent =
          "시작가 " + startTxt + " · 입찰자 " + bidders + "명";
      }
      // i18n must not overwrite dynamic numbers
      progP.removeAttribute("data-i18n");
    }
    if (progBar && start != null && start > 0 && cur != null && !isNaN(cur)) {
      // Fill vs start: 0% at start, ~100% when 2× start (cap 100%)
      var ratio = Math.max(0, (cur - start) / start);
      var pct = Math.min(100, Math.round(ratio * 100));
      // Always show a little bar when listed
      if (pct < 4 && cur >= start) pct = 4;
      progBar.style.setProperty("--w", pct + "%");
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
          badgeEl.textContent = tt("list.badge_live", isEn() ? "Live" : "입찰 중");
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
      showEmptyMarket(
        tt("list.empty_offline", isEn() ? "Could not load listings." : "매물을 불러오지 못했습니다.")
      );
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
          showEmptyMarket(
            tt(
              "list.empty_search",
              isEn() ? "No matches. Try another keyword." : "검색 결과가 없습니다. 다른 키워드를 시도해 보세요."
            )
          );
        } else {
          showEmptyMarket();
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
      if (pageOffset === 0) {
        showEmptyMarket(
          tt("list.empty_offline", isEn() ? "Could not load listings." : "매물을 불러오지 못했습니다.")
        );
      }
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
    // Re-paint after async load so EN titles win even if i18n lang settled mid-fetch
    rerenderForLocale();
    setInterval(pollLive, 4000);
    pollLive();
  });
  // Late lang switches (URL ?lang= / pill) always re-paint cards
  setTimeout(function () {
    rerenderForLocale();
  }, 0);
  setTimeout(function () {
    rerenderForLocale();
  }, 400);
  var moreEl = document.getElementById("listingsMore");
  if (moreEl) {
    moreEl.addEventListener("click", function () {
      load(false);
    });
  }
})();
