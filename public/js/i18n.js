/**
 * WakeAgain i18n — KO / EN localization.
 * data-i18n="key" · data-i18n-html · data-money-krw · WakeAgainI18n.t / setLang / formatMoney
 */
(function (global) {
  var STORAGE_LANG = "wa_lang";
  var STORAGE_CUR = "wa_currency";

  var STR = {
    ko: {
      "nav.market": "마켓플레이스",
      "nav.showcase": "자랑하기",
      "nav.guide": "이용안내",
      "nav.metrics": "숫자로 보기",
      "nav.login": "로그인",
      "nav.app": "앱 설치",
      "nav.list": "내 프로젝트 올리기",
      "nav.site": "사이트",
      "nav.logout": "로그아웃",
      "nav.profile": "내 정보",
      "nav.notif": "알림",
      "nav.fees": "수수료",
      "nav.interest": "관심 등록하기",
      "nav.more_market": "마켓플레이스 보기",
      "skip": "본문으로 건너뛰기",
      "doc.title": "WakeAgain — 프로젝트에 두 번째 기회를 주세요.",
      "hero.badge": "잠든 프로젝트를 다시 깨우는 곳",
      "hero.title1": "멈춰버린 프로젝트에",
      "hero.title2": "숨을 불어넣다.",
      "hero.sub": "완성되지 못한 코드, 방치된 도메인, 잠자고 있는 API. 당신의 “실패한 시도”는 누군가에게 “완벽한 시작”이 됩니다.",
      "hero.cta_main": "내 프로젝트는 얼마일까?",
      "hero.cta_sub": "(30초 무료 진단)",
      "hero.stat_projects": "올라온 프로젝트",
      "hero.stat_interest": "관심 있어요",
      "hero.stat_free": "올리는 비용",
      "hero.stat_free_val": "무료",
      "hero.stats_note": "실제 숫자만 보여 줍니다",
      "live.price": "현재 입찰가",
      "live.time": "남은 시간",
      "live.progress": "시작가 대비 · 5명이 가격 씀",
      "live.toast": "방금 입찰 · 보기",
      "problem.title": "세상 밖으로 나오지 못한 프로젝트들",
      "problem.p1": "매일 수많은 프로젝트가 만들어집니다.",
      "problem.p2": "많은 제품들이 세상 밖으로 나오지 않습니다.",
      "problem.p3": "그들이 쓸모없어서가 아닙니다.",
      "problem.p4": "이는 인생이 변하거나, 시간이 없거나, 마케팅이 일어나지 않았기 때문입니다.",
      "problem.bridge": "그래도 문제는 남습니다. 구체적으로는 이런 상황입니다.",
      "problem.c1_t": "시간은 썼는데 수익·유저는 0",
      "problem.c1_p": "사이드 프로젝트 하나에 주말 기준 8~12주를 쓰는 경우가 많습니다. 그런데 출시 후에도 첫 유저 10명을 못 넘기면, 서버·도메인 비용만 매달 나갑니다. “아깝다”와 “더 못 하겠다”가 동시에 남습니다.",
      "problem.c2_t": "팔고 싶은데 장이 없다",
      "problem.c2_p": "커뮤니티·중고 거래에 올리면 문의는 오지만, 가격 기준·데모 검증·이전 절차가 없어 며칠 채팅 끝에 무산되기 쉽습니다. 규모 있는 매각 플랫폼은 큰 딜 위주라 사이드 프로젝트는 문턱이 높습니다.",
      "problem.c3_t": "사고 싶은데, 비교할 수 있는 매물이 없다",
      "problem.c3_p": "0부터 다시 만들면 MVP만 수 주가 기본입니다. 이미 손댄 코드를 사고 싶어도, 아이디어만 있는 매물과 실행 화면이 있는 매물이 뒤섞여 비교가 어렵습니다.",
      "svc.title": "쉽게 올리고, 쉽게 사고, 거래는 확실하게.",
      "svc.lead": "누구나 프로젝트를 올리고 가격을 쓸 수 있어요. 대신 낙찰되면 안내에 따라 빠르게 입금, 안 내면 다음 사람에게 넘어갈 수 있어요. (결제 자동화·1시간 타이머는 PG 연동 후)",
      "svc.1_t": "1. 내 프로젝트 올리기",
      "svc.1_p": "어떻게 만들었는지, 화면(데모), 시작 가격을 적습니다. 올리는 건 무료. 운영자가 보통 1~2일 안에 형식 검수 후 게시 허용하면 모두가 볼 수 있게 올라갑니다. (품질 보증 아님)",
      "svc.2_t": "2. 사고 싶으면 가격 쓰기",
      "svc.2_p": "지금 가격과 남은 시간을 보고, “이 금액에 살게요”라고 씁니다. 낙찰되면 안내에 따라 빠르게 입금. 안 보내면 다음 사람에게 넘어갈 수 있어요.",
      "svc.3_t": "3. 확인 후 넘겨주기",
      "svc.3_p": "화면이 돌아가는 것만 우선합니다. 중요한 코드·계정은 돈 확인 후 넘깁니다. 연락 → 약속 → 넘기기 순서예요.",
      "svc.m_fee": "올리는 비용",
      "svc.m_free": "무료",
      "svc.m_seller_fee": "팔리면 판매자 수수료",
      "svc.m_review": "검토 시간",
      "svc.m_review_v": "1~2일",
      "svc.m_see": "보는 것",
      "svc.m_see_v": "지금 가격 + 시간",
      "svc.m_pay": "이긴 뒤 입금",
      "svc.m_pay_v": "안내 따라 신속",
      "svc.m_skip": "안 내면",
      "svc.m_skip_v": "다음 사람 가능",
      "svc.m_demo": "화면 보여주기",
      "svc.m_demo_v": "중요",
      "svc.m_steps": "넘기는 순서",
      "svc.m_steps_v": "4단계",
      "svc.m_acct": "계정",
      "svc.m_acct_v": "웹·폰 하나",
      "metrics.title": "숫자로 보기",
      "metrics.lead": "수수료·검토·입찰 단위를 한눈에 정리했습니다.",
      "metrics.inc": "가격 올릴 최소 단위",
      "metrics.inc_v": "+1만 원",
      "metrics.interest": "관심 있어요",
      "metrics.interest_v": "1회",
      "showcase.title": "프로젝트 자랑",
      "showcase.cta": "무료진단 후 자랑하기",
      "showcase.board": "보드 보기",
      "showcase.empty": "아직 자랑이 없어요.",
      "reviews.title": "이용 후기",
      "reviews.loading": "후기를 불러오는 중…",
      "reviews.write": "이용 후기 남기기",
      "why.title": "왜 WakeAgain인가요?",
      "why.lead": "통신판매중개 장터입니다. 기술 자산에 두 번째 기회를 주되, 거래 책임은 판매자·구매자에게 있습니다.",
      "why.1_t": "신원 확인 · 단계별 신뢰",
      "why.1_p": "큰돈이 오갈 수 있는 곳이라, 올리거나 가격 쓰기 전에 이메일·이름·휴대폰을 확인하고, 팔기 전에 계좌 정보를 받아요. 연락처는 목록에 안 나가요. 이 절차는 예방이지, 모든 사기를 막거나 배상한다는 보증은 아닙니다.",
      "why.2_t": "상태별 시작가 가이드",
      "why.2_p": "「돌아가는 초안」「써 볼 수 있는 제품」처럼 쉬운 상태에 맞춰 시작가를 안내합니다. 운영 검수 후 공개됩니다.",
      "why.2_a": "상태 쉽게 고르는 법 ›",
      "why.3_t": "관심 있는 구매자 연결",
      "why.3_p": "관심 등록·입찰로 의사 있는 이용자를 모읍니다. 초기에는 커뮤니티를 함께 키워 가는 단계입니다.",
      "why.4_t": "이전 체크리스트 안내",
      "why.4_p": "입금 확인 후 코드·도메인·계정 넘기기 순서를 가이드로 안내합니다. (플랫폼이 이전을 대행·보증하지 않습니다.)",
      "list.title": "최근 올라온 매물",
      "list.loading": "불러오는 중…",
      "list.public": "입찰 중 현재가는 사이트에 들어온 모든 사람에게 실시간으로 공개됩니다.",
      "list.all": "전체",
      "list.empty_cat": "해당 카테고리 매물이 없습니다.",
      "list.more": "프로젝트 더 보기",
      "list.none": "아직 공개 매물이 없습니다.",
      "cta.title": "프로젝트에 두 번째 기회를 주세요.",
      "cta.strong": "우리는 그 프로젝트들에게 다시 한 번 기회를 줍니다.",
      "cta.fine": "올리기·관심·가격 쓰기까지는 쉽게. 올리는 건 무료입니다. 대신 팔리면 규칙을 지킵니다 — 빠른 입금, 안 내면 다음 사람, 판매자 수수료 10%. (1시간 자동 타이머는 PG 후)",
      "cta.note": "쉽게 시작 · 거래는 확실하게 · 팔리면 판매자 수수료 10% · 사는 사람은 합의 가격만",
      "footer.brand": "우리는 기술 자산의 가치가 잊혀지는 것을 반대합니다. 모든 코드는 누군가의 소중한 자산이며, 새로운 가능성의 씨앗입니다.",
      "footer.op": "운영 · 코어랩스(CoreLabs)",
      "footer.contact": "문의: corelabs.studio@gmail.com",
      "footer.tagline": "WakeAgain · 쉽게 올리고 쉽게 사고, 거래는 확실하게 · 상호 코어랩스",
      "footer.broker": "본 플랫폼은 통신판매중개자이며, 거래되는 상품의 품질과 내용은 판매자가 책임집니다.",
      "footer.broker_sub": "이용자 간 사기·분쟁의 1차 책임은 당사자에게 있습니다. WakeAgain(코어랩스)은 거래 당사자가 아니며, 성사·대금·자산 이전을 보증하지 않습니다.",
      "footer.terms": "이용약관",
      "footer.privacy": "개인정보처리방침",
      "footer.why": "왜 WakeAgain인가요",
      "diag.cta": "무료진단",
      "diag.page_title": "내 프로젝트는 얼마일까?",
      "app.auth_title": "쉽게 시작. 거래는 확실하게.",
      "app.auth_lede": "웹·폰 같은 계정. 누구나 올리고 가격을 쓸 수 있지만, 낙찰되면 안내에 따른 빠른 입금·신원 확인으로 거래를 끝냅니다.",
      "app.login": "로그인",
      "app.register": "가입",
      "app.email": "이메일",
      "app.password": "비밀번호",
      "404.title": "페이지를 찾을 수 없어요",
      "404.home": "홈",
      "404.market": "마켓",
      "common.free": "무료",
      "common.loading": "불러오는 중…",
    },
    en: {
      "nav.market": "Marketplace",
      "nav.showcase": "Showcase",
      "nav.guide": "Guide",
      "nav.metrics": "By the numbers",
      "nav.login": "Log in",
      "nav.app": "Get the app",
      "nav.list": "List a project",
      "nav.site": "Website",
      "nav.logout": "Log out",
      "nav.profile": "Profile",
      "nav.notif": "Alerts",
      "nav.fees": "Fees",
      "nav.interest": "Register interest",
      "nav.more_market": "Browse marketplace",
      "skip": "Skip to content",
      "doc.title": "WakeAgain — Give projects a second chance.",
      "hero.badge": "A second chance for shelved projects",
      "hero.title1": "Breathe life into",
      "hero.title2": "paused projects.",
      "hero.sub": "Unfinished code, idle domains, sleeping APIs. Your “failed attempt” can be someone else’s perfect start.",
      "hero.cta_main": "What’s my project worth?",
      "hero.cta_sub": "(30-second free estimate)",
      "hero.stat_projects": "Listed projects",
      "hero.stat_interest": "Interests",
      "hero.stat_free": "Listing fee",
      "hero.stat_free_val": "Free",
      "hero.stats_note": "Live counts only — no fake metrics",
      "live.price": "Current bid",
      "live.time": "Time left",
      "live.progress": "vs start price · 5 bidders",
      "live.toast": "New bid · view",
      "problem.title": "Projects that never left the lab",
      "problem.p1": "Countless projects are built every day.",
      "problem.p2": "Many never ship to the world.",
      "problem.p3": "Not because they were worthless.",
      "problem.p4": "Life changed, time ran out, or marketing never happened.",
      "problem.bridge": "Still, the friction remains. Concretely:",
      "problem.c1_t": "Time spent, revenue & users still zero",
      "problem.c1_p": "A side project often eats 8–12 weekends. If you never clear the first 10 users, server and domain bills keep coming. You feel both “what a waste” and “I can’t keep going.”",
      "problem.c2_t": "Want to sell — but no real market",
      "problem.c2_p": "Community posts get chats, but without pricing norms, demo checks, or transfer steps, deals die after days of messages. Big acquisition marketplaces aim at huge deals — side projects don’t fit.",
      "problem.c3_t": "Want to buy — but listings aren’t comparable",
      "problem.c3_p": "Building an MVP from scratch takes weeks. You want working code, but idea-only PDFs and runnable demos are mixed together. Without live price and countdown, you can’t decide whether to buy now.",
      "svc.title": "Easy to list. Easy to bid. Serious when it sells.",
      "svc.lead": "Anyone can list a project and place a price. After award, deposit promptly per instructions — miss it and the next bidder may get the chance. (1-hour auto timer after PG integration.)",
      "svc.1_t": "1. List your project",
      "svc.1_p": "Share how it was built, a demo, and a starting price. Listing is free. After a light format review (usually 1–2 days) it goes public. Review is not a quality guarantee.",
      "svc.2_t": "2. Bid if you want it",
      "svc.2_p": "See the live price and time left, then say what you’ll pay. Winners deposit quickly per instructions. No deposit, and the next person may take over.",
      "svc.3_t": "3. Verify, then transfer",
      "svc.3_p": "Running demos come first. Critical code and accounts move after payment is confirmed — contact → agree → transfer.",
      "svc.m_fee": "Listing fee",
      "svc.m_free": "Free",
      "svc.m_seller_fee": "Seller fee when sold",
      "svc.m_review": "Review time",
      "svc.m_review_v": "1–2 days",
      "svc.m_see": "What you see",
      "svc.m_see_v": "Live price + timer",
      "svc.m_pay": "After you win",
      "svc.m_pay_v": "Deposit promptly",
      "svc.m_skip": "If you don’t",
      "svc.m_skip_v": "Next bidder may win",
      "svc.m_demo": "Show a demo",
      "svc.m_demo_v": "Essential",
      "svc.m_steps": "Transfer flow",
      "svc.m_steps_v": "4 steps",
      "svc.m_acct": "Account",
      "svc.m_acct_v": "Web + phone, one login",
      "metrics.title": "By the numbers",
      "metrics.lead": "Fees, review time, and bid units at a glance.",
      "metrics.inc": "Minimum bid step",
      "metrics.inc_v": "+₩10,000",
      "metrics.interest": "Interest",
      "metrics.interest_v": "Once",
      "showcase.title": "Project showcase",
      "showcase.cta": "Diagnose, then showcase",
      "showcase.board": "Open board",
      "showcase.empty": "No showcases yet.",
      "reviews.title": "Reviews",
      "reviews.loading": "Loading reviews…",
      "reviews.write": "Leave a review",
      "why.title": "Why WakeAgain?",
      "why.lead": "We are a marketplace intermediary. Tech assets get a second chance — deal liability stays with buyer and seller.",
      "why.1_t": "Identity · staged trust",
      "why.1_p": "Because real money can move, we verify email, name, and phone before listing or bidding, and collect settlement details before closing. Contact info stays off the public list. This is prevention — not a guarantee against fraud or damages.",
      "why.2_t": "Start-price by status",
      "why.2_p": "Simple states like “working prototype” or “usable beta” guide starting prices. Listings go public after ops review.",
      "why.2_a": "How to pick a status ›",
      "why.3_t": "Connect interested buyers",
      "why.3_p": "Interest and bids gather people who mean it. Early on, we grow the community together.",
      "why.4_t": "Transfer checklist",
      "why.4_p": "After payment is confirmed, we guide code, domain, and account handoff order. The platform does not perform or guarantee transfers.",
      "list.title": "Latest listings",
      "list.loading": "Loading…",
      "list.public": "Live bid prices are visible to everyone on the site in real time.",
      "list.all": "All",
      "list.empty_cat": "No listings in this category.",
      "list.more": "Show more projects",
      "list.none": "No public listings yet.",
      "cta.title": "Give projects a second chance.",
      "cta.strong": "We give those projects one more shot.",
      "cta.fine": "Listing, interest, and bidding stay easy — listing is free. After a sale, rules apply: prompt deposit, next bidder if missed, 10% seller fee. (1-hour auto timer after PG.)",
      "cta.note": "Easy to start · serious deals · 10% seller fee · buyers pay the agreed price only",
      "footer.brand": "We refuse to let technical assets be forgotten. Every codebase is someone’s hard-won asset — and a seed of new possibility.",
      "footer.op": "Operated by CoreLabs",
      "footer.contact": "Contact: corelabs.studio@gmail.com",
      "footer.tagline": "WakeAgain · easy to list & buy, serious when it sells · CoreLabs",
      "footer.broker": "This platform is an intermediary. Product quality and content are the seller’s responsibility.",
      "footer.broker_sub": "Primary liability for fraud or disputes sits with the parties. WakeAgain (CoreLabs) is not a party to the deal and does not guarantee completion, payment, or asset transfer.",
      "footer.terms": "Terms",
      "footer.privacy": "Privacy",
      "footer.why": "Why WakeAgain",
      "diag.cta": "Free diagnose",
      "diag.page_title": "What’s my project worth?",
      "app.auth_title": "Easy to start. Serious when it sells.",
      "app.auth_lede": "One account on web and mobile. Anyone can list and bid — after award, deposit and identity rules close the deal.",
      "app.login": "Log in",
      "app.register": "Sign up",
      "app.email": "Email",
      "app.password": "Password",
      "404.title": "Page not found",
      "404.home": "Home",
      "404.market": "Market",
      "common.free": "Free",
      "common.loading": "Loading…",
    },
  };

  var fx = { KRW: 1, USD: 1350, EUR: 1450 };
  var curMeta = {
    KRW: { symbol: "₩", decimals: 0, locale: "ko-KR" },
    USD: { symbol: "$", decimals: 0, locale: "en-US" },
    EUR: { symbol: "€", decimals: 0, locale: "en-US" },
  };

  function detectLang() {
    var saved = localStorage.getItem(STORAGE_LANG);
    if (saved === "ko" || saved === "en") return saved;
    try {
      var q = new URLSearchParams(location.search || "");
      var L = (q.get("lang") || "").toLowerCase();
      if (L === "en" || L === "ko") return L;
    } catch (e) {}
    var nav = (navigator.language || "ko").toLowerCase();
    if (nav.indexOf("ko") === 0) return "ko";
    return "en";
  }

  function detectCurrency(lang) {
    var saved = localStorage.getItem(STORAGE_CUR);
    if (saved && curMeta[saved]) return saved;
    return lang === "en" ? "USD" : "KRW";
  }

  var state = { lang: detectLang(), currency: "KRW" };
  state.currency = detectCurrency(state.lang);

  function t(key) {
    var pack = STR[state.lang] || STR.ko;
    if (pack[key] != null) return pack[key];
    if (STR.en[key] != null) return STR.en[key];
    if (STR.ko[key] != null) return STR.ko[key];
    return key;
  }

  function formatMoney(amountKrw) {
    var n = Number(amountKrw);
    if (!isFinite(n)) return "—";
    var code = state.currency || "KRW";
    var rate = fx[code] || 1;
    var meta = curMeta[code] || curMeta.KRW;
    var shown = code === "KRW" ? n : Math.round(n / rate);
    try {
      return (
        meta.symbol +
        shown.toLocaleString(meta.locale, {
          maximumFractionDigits: meta.decimals,
          minimumFractionDigits: meta.decimals,
        })
      );
    } catch (e) {
      return meta.symbol + String(shown);
    }
  }

  function apply(root) {
    var scope = root || document;
    scope.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (!key) return;
      var val = t(key);
      if (el.hasAttribute("data-i18n-html")) el.innerHTML = val;
      else el.textContent = val;
    });
    scope.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder")));
    });
    scope.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria")));
    });
    scope.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      el.setAttribute("title", t(el.getAttribute("data-i18n-title")));
    });
    document.documentElement.lang = state.lang === "en" ? "en" : "ko";
    document.documentElement.setAttribute("data-wa-lang", state.lang);
    document.documentElement.setAttribute("data-wa-currency", state.currency);
    if (STR[state.lang] && STR[state.lang]["doc.title"]) {
      document.title = STR[state.lang]["doc.title"];
    }
    scope.querySelectorAll("[data-lang-switch]").forEach(function (el) {
      if (el.tagName === "SELECT") el.value = state.lang;
      else if (el.getAttribute("data-lang-switch") === state.lang) {
        el.setAttribute("aria-current", "true");
        el.classList.add("is-on");
      } else {
        el.removeAttribute("aria-current");
        el.classList.remove("is-on");
      }
    });
    scope.querySelectorAll("[data-currency-switch]").forEach(function (el) {
      if (el.tagName === "SELECT") el.value = state.currency;
    });
    scope.querySelectorAll("[data-money-krw]").forEach(function (el) {
      el.textContent = formatMoney(el.getAttribute("data-money-krw"));
    });
  }

  function setLang(lang, opts) {
    if (lang !== "ko" && lang !== "en") return;
    opts = opts || {};
    state.lang = lang;
    localStorage.setItem(STORAGE_LANG, lang);
    if (!localStorage.getItem(STORAGE_CUR) || opts.resetCurrency) {
      state.currency = detectCurrency(lang);
      if (opts.resetCurrency) localStorage.setItem(STORAGE_CUR, state.currency);
    }
    apply(document);
    try {
      var url = new URL(location.href);
      url.searchParams.set("lang", lang);
      history.replaceState(null, "", url.pathname + url.search + url.hash);
    } catch (e) {}
    try {
      document.dispatchEvent(new CustomEvent("wa:langchange", { detail: { lang: lang } }));
    } catch (e) {}
  }

  function setCurrency(code) {
    if (!curMeta[code]) return;
    state.currency = code;
    localStorage.setItem(STORAGE_CUR, code);
    apply(document);
    try {
      document.dispatchEvent(new CustomEvent("wa:currencychange", { detail: { currency: code } }));
    } catch (e) {}
  }

  function ingestConfig(cfg) {
    if (!cfg || !cfg.global) return;
    var g = cfg.global;
    if (g.fx_display_only) {
      Object.keys(g.fx_display_only).forEach(function (k) {
        fx[k] = Number(g.fx_display_only[k]) || fx[k];
      });
    }
  }

  function bindUi(root) {
    var scope = root || document;
    scope.querySelectorAll("[data-lang-switch]").forEach(function (el) {
      if (el.__waLangBound) return;
      el.__waLangBound = true;
      if (el.tagName === "SELECT") {
        el.addEventListener("change", function () {
          setLang(el.value, { resetCurrency: true });
        });
      } else {
        el.addEventListener("click", function (e) {
          e.preventDefault();
          setLang(el.getAttribute("data-lang-switch"), { resetCurrency: true });
        });
      }
    });
    scope.querySelectorAll("[data-currency-switch]").forEach(function (el) {
      if (el.__waCurBound) return;
      el.__waCurBound = true;
      if (el.tagName === "SELECT") {
        el.addEventListener("change", function () {
          setCurrency(el.value);
        });
      }
    });
  }

  function boot() {
    bindUi(document);
    apply(document);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  global.WakeAgainI18n = {
    t: t,
    apply: apply,
    setLang: setLang,
    setCurrency: setCurrency,
    formatMoney: formatMoney,
    ingestConfig: ingestConfig,
    bindUi: bindUi,
    getLang: function () {
      return state.lang;
    },
    getCurrency: function () {
      return state.currency;
    },
    STR: STR,
  };
})(typeof window !== "undefined" ? window : globalThis);
