/**
 * WakeAgain i18n — global UI foundation (ko / en).
 * Usage: data-i18n="key" on elements; WakeAgainI18n.t("key"); formatMoney(n).
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
      "skip": "본문으로 건너뛰기",
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
      "showcase.title": "프로젝트 자랑",
      "showcase.cta": "무료진단 후 자랑하기",
      "showcase.empty": "아직 자랑이 없어요.",
      "diag.cta": "무료진단",
      "lang.label": "언어",
      "cur.label": "표시 통화",
      "global.banner": "Global-ready · UI: KO/EN · Prices stored in KRW (display convert)",
      "app.auth_title": "쉽게 시작. 거래는 확실하게.",
      "app.auth_lede": "웹·폰 같은 계정. 누구나 올리고 가격을 쓸 수 있지만, 낙찰되면 안내에 따른 빠른 입금·신원 확인으로 거래를 끝냅니다.",
      "app.login": "로그인",
      "app.register": "가입",
      "app.email": "이메일",
      "app.password": "비밀번호",
      "footer.terms": "이용약관",
      "footer.privacy": "개인정보처리방침",
      "404.title": "페이지를 찾을 수 없어요",
      "404.home": "홈",
      "404.market": "마켓",
    },
    en: {
      "nav.market": "Marketplace",
      "nav.showcase": "Showcase",
      "nav.guide": "Guide",
      "nav.metrics": "Numbers",
      "nav.login": "Log in",
      "nav.app": "Get app",
      "nav.list": "List a project",
      "nav.site": "Site",
      "nav.logout": "Log out",
      "nav.profile": "Profile",
      "nav.notif": "Alerts",
      "nav.fees": "Fees",
      "skip": "Skip to content",
      "hero.badge": "A second chance for shelved projects",
      "hero.title1": "Breathe life into",
      "hero.title2": "paused projects.",
      "hero.sub": "Unfinished code, idle domains, sleeping APIs. Your “failed attempt” can be someone else’s perfect start.",
      "hero.cta_main": "What’s my project worth?",
      "hero.cta_sub": "(30-sec free estimate)",
      "hero.stat_projects": "Listed projects",
      "hero.stat_interest": "Interests",
      "hero.stat_free": "Listing fee",
      "hero.stat_free_val": "Free",
      "hero.stats_note": "Live counts only — no fake metrics",
      "live.price": "Current bid",
      "live.time": "Time left",
      "live.progress": "vs start · 5 bidders",
      "live.toast": "New bid · view",
      "showcase.title": "Project showcase",
      "showcase.cta": "Diagnose, then showcase",
      "showcase.empty": "No showcases yet.",
      "diag.cta": "Free diagnose",
      "lang.label": "Language",
      "cur.label": "Display currency",
      "global.banner": "Global-ready · UI: KO/EN · Amounts stored in KRW (display convert)",
      "app.auth_title": "Easy to start. Serious when it sells.",
      "app.auth_lede": "One account on web & mobile. Anyone can list and bid — after award, deposit and identity rules close the deal.",
      "app.login": "Log in",
      "app.register": "Sign up",
      "app.email": "Email",
      "app.password": "Password",
      "footer.terms": "Terms",
      "footer.privacy": "Privacy",
      "404.title": "Page not found",
      "404.home": "Home",
      "404.market": "Market",
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
    var nav = (navigator.language || "ko").toLowerCase();
    if (nav.indexOf("ko") === 0) return "ko";
    return "en";
  }

  function detectCurrency(lang) {
    var saved = localStorage.getItem(STORAGE_CUR);
    if (saved && curMeta[saved]) return saved;
    return lang === "en" ? "USD" : "KRW";
  }

  var state = {
    lang: detectLang(),
    currency: "KRW",
  };
  state.currency = detectCurrency(state.lang);

  function t(key) {
    var pack = STR[state.lang] || STR.ko;
    if (pack[key] != null) return pack[key];
    if (STR.en[key] != null) return STR.en[key];
    return key;
  }

  /** amount is stored KRW integer */
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
    document.documentElement.lang = state.lang === "en" ? "en" : "ko";
    document.documentElement.setAttribute("data-wa-lang", state.lang);
    document.documentElement.setAttribute("data-wa-currency", state.currency);
    // sync switchers
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
    // reformat money nodes
    scope.querySelectorAll("[data-money-krw]").forEach(function (el) {
      var raw = el.getAttribute("data-money-krw");
      el.textContent = formatMoney(raw);
    });
  }

  function setLang(lang) {
    if (lang !== "ko" && lang !== "en") return;
    state.lang = lang;
    localStorage.setItem(STORAGE_LANG, lang);
    if (!localStorage.getItem(STORAGE_CUR)) {
      state.currency = detectCurrency(lang);
    }
    apply(document);
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
      el.addEventListener("click", function (e) {
        if (el.tagName === "SELECT") return;
        e.preventDefault();
        setLang(el.getAttribute("data-lang-switch"));
      });
      if (el.tagName === "SELECT") {
        el.addEventListener("change", function () {
          setLang(el.value);
        });
      }
    });
    scope.querySelectorAll("[data-currency-switch]").forEach(function (el) {
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
    getLang: function () {
      return state.lang;
    },
    getCurrency: function () {
      return state.currency;
    },
    STR: STR,
  };
})(typeof window !== "undefined" ? window : globalThis);
