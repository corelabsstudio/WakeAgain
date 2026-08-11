/* WakeAgain multi-channel app shell — auth + trust gates (L0–L3) */
(function () {
  const api = window.WakeAgainAPI;
  if (!api) {
    console.error("WakeAgainAPI missing");
    return;
  }

  function t(key, fallback, vars) {
    try {
      if (window.WakeAgainI18n && window.WakeAgainI18n.t) {
        var v = window.WakeAgainI18n.t(key, vars);
        if (v && v !== key) return v;
      }
    } catch (e) {}
    if (fallback == null) return key;
    if (vars && typeof fallback === "string") {
      Object.keys(vars).forEach(function (k) {
        fallback = fallback.split("{" + k + "}").join(String(vars[k]));
      });
    }
    return fallback;
  }

  const $ = (id) => document.getElementById(id);
  function money(n) {
    if (window.WakeAgainI18n && window.WakeAgainI18n.formatMoney) return window.WakeAgainI18n.formatMoney(n);
    // Global-first fallback when i18n not loaded yet (display FX only)
    return "$" + Math.round(Number(n) / 1350).toLocaleString("en-US");
  }

  /** Navigate to any site page (landing, project detail, legal…) from app shell. */
  function goPage(path) {
    if (api.goPage) api.goPage(path);
    else location.href = path;
  }
  function pageUrl(path) {
    return api.pageUrl ? api.pageUrl(path) : path;
  }

  function goHomeSite() {
    // Full site homepage (landing) — same as website main
    goPage("/");
  }

  function goMarketList() {
    loadProjects(true);
  }

  const views = {
    auth: $("viewAuth"),
    age: $("viewAge"),
    verify: $("viewVerify"),
    profile: $("viewProfile"),
    sellerId: $("viewSellerId"),
    settle: $("viewSettle"),
    list: $("viewApp"),
    create: $("viewCreate"),
    notif: $("viewNotif"),
    fees: $("viewFees"),
    coupons: $("viewCoupons"),
  };
  let listOffset = 0;
  const PAGE = 24;
  const tabbar = $("tabbar");
  let feed = "all";
  let marketSearchQ = "";
  let listingKeywords = [];
  const KW_MAX = 5;
  let pendingAfterAuth = null;
  let lastView = "list";

  function showErr(el, msg) {
    if (!el) return;
    if (!msg) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = msg;
  }

  function setView(name) {
    Object.keys(views).forEach((k) => {
      if (views[k]) views[k].hidden = k !== name;
    });
    // Keep bottom tabs on auth/verify too so user can always open 홈·마켓
    const showTab =
      name === "list" ||
      name === "create" ||
      name === "profile" ||
      name === "sellerId" ||
      name === "settle" ||
      name === "notif" ||
      name === "fees" ||
      name === "coupons" ||
      name === "auth" ||
      name === "verify" ||
      name === "age";
    tabbar.hidden = !showTab;
    document.querySelectorAll(".tabbar-item[data-go]").forEach((b) => {
      const go = b.getAttribute("data-go");
      const on =
        (name === "create" && go === "new") ||
        (name === "list" && go === "list") ||
        ((name === "profile" ||
          name === "sellerId" ||
          name === "settle" ||
          name === "verify") &&
          go === "profile");
      // "home" is a site navigation action — never sticky-selected as SPA view
      b.classList.toggle("is-on", go === "home" ? false : on);
    });
    if (name === "auth" && window.WakeAgainCountries && $("regCountry") && !$("regCountry").options.length) {
      window.WakeAgainCountries.populateSelect($("regCountry"));
    }
    if (name === "profile" && window.WakeAgainCountries && $("profCountry")) {
      const u = api.getUser();
      window.WakeAgainCountries.populateSelect($("profCountry"), (u && u.country) || "");
    }
    const hashMap = {
      auth: "#login",
      verify: "#verify",
      profile: "#profile",
      sellerId: "#seller",
      settle: "#settlement",
      list: "#list",
      create: "#new",
      fees: "#fees",
      coupons: "#coupons",
    };
    if (hashMap[name]) history.replaceState(null, "", hashMap[name]);
    lastView = name === "auth" || name === "verify" ? lastView : name;
    syncChrome();
  }

  function switchAuthTab(tab) {
    document.querySelectorAll(".auth-tabs .tab").forEach((b) => {
      b.classList.toggle("is-on", b.getAttribute("data-tab") === tab);
    });
    $("formLogin").hidden = tab !== "login";
    $("formRegister").hidden = tab !== "register";
    if ($("formReset")) $("formReset").hidden = true;
    if ($("formFindId")) $("formFindId").hidden = true;
    history.replaceState(null, "", tab === "register" ? "#register" : "#login");
    if (tab === "login") fillSavedLoginForm();
  }

  function hideAuthExtraForms() {
    if ($("formReset")) $("formReset").hidden = true;
    if ($("formFindId")) $("formFindId").hidden = true;
    if ($("findIdResult")) $("findIdResult").hidden = true;
    showErr($("findIdErr"));
    showErr($("resetErr"));
  }

  function isAppLaunch() {
    try {
      const q = new URLSearchParams(location.search || "");
      const standalone =
        (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) ||
        window.navigator.standalone === true;
      const native =
        window.Capacitor &&
        window.Capacitor.isNativePlatform &&
        window.Capacitor.isNativePlatform();
      return standalone || native || q.get("source") === "pwa";
    } catch (e) {
      return false;
    }
  }

  /** Prefill email/password from "로그인 정보 저장" on this device. */
  function fillSavedLoginForm() {
    if (!$("loginEmail")) return;
    let saved = null;
    try {
      saved = api.getSavedLogin && api.getSavedLogin();
    } catch (e) {
      saved = null;
    }
    if (!saved || !saved.email) {
      if ($("loginRemember")) $("loginRemember").checked = false;
      return;
    }
    $("loginEmail").value = saved.email;
    if ($("loginPass") && saved.password) $("loginPass").value = saved.password;
    if ($("loginRemember")) $("loginRemember").checked = true;
  }

  function trustOf(user) {
    return (user && user.trust) || api.trust() || {};
  }

  function trustBadgeCopy(level) {
    // Positive “done” language — avoid “확인” sounding like pending/risk
    // Display as Lv0…Lv3 (not L0…L3)
    const map = {
      0: t("app.lv0", "Lv0 · Joined"),
      1: t("app.lv1", "Lv1 · Email verified"),
      2: t("app.lv2", "Lv2 · Identity done"),
      3: t("app.lv3", "Lv3 · Ready to trade"),
    };
    return map[level] != null ? map[level] : "Lv" + level;
  }

  function initialOf(name) {
    const s = String(name || "").trim();
    if (!s) return "?";
    // first grapheme-ish
    return s.slice(0, 1).toUpperCase();
  }

  function syncChrome() {
    // Prefer token: stale wa_user in localStorage must not show logout
    const loggedIn = typeof api.isLoggedIn === "function" ? api.isLoggedIn() : !!api.token();
    const u = loggedIn ? api.getUser() : null;
    const chip = $("userChip");
    const label = $("userLabel");
    const avatar = $("userAvatar");
    const meta = $("userChipMeta");
    const logout = $("btnLogout");
    const login = $("btnGoLogin");
    const prof = $("btnProfile");
    const badge = $("trustBadge");
    const notif = $("btnNotif");
    const fees = $("btnFees");
    const coupons = $("btnCoupons");
    if (loggedIn && u) {
      const name = u.display_name || u.real_name || (u.email && u.email.split("@")[0]) || t("app.member", "Member");
      if (label) label.textContent = name;
      if (avatar) avatar.textContent = initialOf(name);
      if (meta) {
        const em = u.email || "";
        meta.textContent = em.length > 22 ? em.slice(0, 18) + "…" : em;
        meta.hidden = !em;
      }
      if (chip) chip.hidden = false;
      if (logout) logout.hidden = false;
      if (login) login.hidden = true;
      if (prof) prof.hidden = false;
      if (notif) notif.hidden = false;
      if (fees) fees.hidden = false;
      if (coupons) coupons.hidden = false;
      const trust = trustOf(u);
      const c = u.credit || {};
      const level = trust.level != null ? Number(trust.level) : 0;
      if (badge) {
        badge.hidden = false;
        badge.className = "trust-badge trust-badge--l" + Math.min(3, Math.max(0, level));
        // Keep credit separate in wording so L2 doesn't look like a score warning
        let text = trustBadgeCopy(level);
        if (c.score != null) {
          text += t("app.credit_suffix", " · credit {n}", { n: c.score });
          if (c.label) {
            text += " " + creditLabelUi(c.label);
          }
        }
        badge.textContent = text;
        badge.title =
          t("app.trust_tip", "Trust level (eligibility) Lv{n}", { n: level }) +
          " · " +
          trustBadgeCopy(level) +
          (c.score != null
            ? t("app.credit_tip", " / on-site credit score {n}{label} · see credit guide", {
                n: c.score,
                label: c.label ? " " + creditLabelUi(c.label) : "",
              })
            : "");
      }
      refreshNotifBadge();
    } else {
      if (chip) chip.hidden = true;
      if (label) label.textContent = "";
      if (avatar) avatar.textContent = "?";
      if (meta) meta.textContent = "";
      if (logout) logout.hidden = true;
      if (login) login.hidden = false;
      if (prof) prof.hidden = true;
      if (notif) notif.hidden = true;
      if (fees) fees.hidden = true;
      if (coupons) coupons.hidden = true;
      if (badge) {
        badge.hidden = true;
        badge.className = "trust-badge";
      }
    }
  }

  async function refreshNotifBadge() {
    const dot = $("notifBadge");
    if (!dot || !api.isLoggedIn()) return;
    try {
      const data = await api.listNotifications();
      const n = data.unread || 0;
      if (n > 0) {
        dot.hidden = false;
        dot.textContent = n > 9 ? "9+" : String(n);
      } else {
        dot.hidden = true;
      }
    } catch {
      /* ignore */
    }
  }

  async function loadNotifications() {
    setView("notif");
    const list = $("notifList");
    const empty = $("notifEmpty");
    list.innerHTML = "";
    try {
      const data = await api.listNotifications();
      const items = data.notifications || [];
      empty.hidden = items.length > 0;
      items.forEach((n) => {
        const el = document.createElement("article");
        el.className = "n-card" + (n.is_read ? "" : " unread");
        el.innerHTML = "<strong></strong><p></p><div class='n-time'></div>";
        el.querySelector("strong").textContent = n.title;
        el.querySelector("p").textContent = n.body;
        el.querySelector(".n-time").textContent = (n.created_at || "").replace("T", " ").slice(0, 19);
        if (n.link) {
          el.style.cursor = "pointer";
          el.addEventListener("click", () => {
            var link = n.link;
            if (link && link.charAt(0) === "/") goPage(link);
            else if (link && /^https?:\/\//i.test(link)) {
              try {
                var u = new URL(link);
                goPage(u.pathname + u.search + u.hash);
              } catch (e) {
                location.href = link;
              }
            } else location.href = link;
          });
        }
        list.appendChild(el);
      });
    } catch (e) {
      empty.hidden = false;
      empty.textContent = e.message || t("app.notif_fail", "Couldn’t load notifications.");
    }
  }

  function showDevCode(extraMsg) {
    const box = $("devCodeBox");
    const text = $("devCodeText");
    const code = api.getDevCode();
    const note = $("devCodeNote");
    if (code && box && text) {
      box.hidden = false;
      text.textContent = code;
      if ($("verifyCode")) $("verifyCode").value = code;
      if (note) {
        note.textContent =
          extraMsg ||
          t("app.dev_code_hint", "In dev / without mail, the code appears here. It may not hit your inbox.");
      }
    } else if (box) {
      box.hidden = true;
    }
  }

  function fillProfileForm(u) {
    if (!u) return;
    $("profReal").value = u.real_name || "";
    $("profPhone").value = u.phone || "";
    // role is always "both" (sell+buy) — purpose selector removed
    $("profDisplay").value = u.display_name || "";
    if (u.settlement) {
      $("setHolder").value = u.settlement.holder || u.real_name || "";
      $("setBank").value = u.settlement.bank || "";
      // account not returned full — leave blank unless empty mask
      if (!u.settlement.has_account) $("setAccount").value = "";
      $("setBiz").checked = !!u.settlement.is_business;
    }
    const card = $("creditCard");
    if (card && u.credit) {
      card.hidden = false;
      const c = u.credit;
      if ($("creditScoreNum"))
        $("creditScoreNum").textContent = t("app.credit_points", "{n} pts", {
          n: c.score != null ? c.score : "—",
        });
      if ($("creditGradeLabel"))
        $("creditGradeLabel").textContent = c.label ? "· " + creditLabelUi(c.label) : "";
      const br = c.buyer_rank || null;
      const rankLine = $("buyerRankLine");
      if (rankLine && $("buyerRankBadge")) {
        if (br && br.label) {
          rankLine.hidden = false;
          $("buyerRankBadge").textContent = creditLabelUi(br.label);
          $("buyerRankBadge").setAttribute("data-rank", br.key || "");
          $("buyerRankBadge").classList.toggle("is-caution", !!br.caution);
          if ($("buyerRankMeta")) {
            const next =
              br.next_min != null
                ? t("app.buyer_next", " · {n} more closes to “{label}”", {
                    label: creditLabelUi(br.next_label || ""),
                    n: Math.max(0, br.next_min - (br.bought_complete || 0)),
                  })
                : t("app.buyer_top", " · top buyer badge");
            $("buyerRankMeta").textContent =
              t("app.buyer_closes", "Buyer closes: {n}", { n: br.bought_complete || 0 }) +
              (br.key === "scout" ? t("app.buyer_first", " · badge from first close") : next);
          }
        } else {
          rankLine.hidden = true;
        }
      }
      const cnt = c.counts || {};
      if ($("creditCounts")) {
        $("creditCounts").textContent = t("app.stats_line", "Sold {s} · Bought {b} · Missed pay {m}", {
          s: cnt.sold_as_seller || 0,
          b: cnt.bought_complete || 0,
          m: cnt.defaults || 0,
        });
      }
      const b = c.breakdown;
      if ($("creditBreak") && b) {
        $("creditBreak").textContent = t(
          "app.credit_breakdown",
          "Adjustments: base {base} · closes +{close} · on-time +{ontime} · missed {miss}",
          {
            base: b.base || 30,
            close: (b.sold_as_seller || 0) + (b.bought_complete || 0),
            ontime: b.on_time_payment || 0,
            miss: b.defaults || 0,
          }
        ) +
          " · Lv2 +" +
          (b.l2_identity || 0) +
          " · Lv3 +" +
          (b.l3_settlement || 0);
      }
    } else if (card) {
      card.hidden = true;
    }
  }

  function updateTrustBanner() {
    const banner = $("trustBanner");
    const gate = $("authGateNote");
    const u = api.getUser();
    if (!u) {
      if (gate) {
        gate.hidden = false;
        gate.textContent =
          t("app.need_login_list", "Sign in to list or manage projects. Email verification and name/phone are required before listing.");
      }
      if (banner) banner.hidden = true;
      return;
    }
    if (gate) gate.hidden = true;
    const trust = trustOf(u);
    if (!banner) return;
    if (trust.can_list && trust.deal_ready) {
      banner.hidden = false;
      banner.className = "trust-banner is-ok";
      banner.innerHTML = t("app.banner_l3", "Trust Lv3 · ready to trade. Settlement account is used when a deal closes.");
    } else if (trust.can_list) {
      banner.hidden = false;
      banner.className = "trust-banner";
      banner.innerHTML =
        t("app.banner_need_settle", "Identity & seller info done. Before closing, register a <button type='button' class='text-link' id='bannerSettle'>settlement account (Lv3)</button>.");
      setTimeout(() => {
        $("bannerSettle")?.addEventListener("click", () => setView("settle"));
      }, 0);
    } else if (!trust.email_verified) {
      banner.hidden = false;
      banner.className = "trust-banner is-warn";
      banner.innerHTML =
        t("app.banner_need_verify", "Email not verified · listing blocked. <button type='button' class='text-link' id='bannerVerify'>Verify now</button>");
      setTimeout(() => {
        $("bannerVerify")?.addEventListener("click", () => {
          showDevCode();
          setView("verify");
        });
      }, 0);
    } else if (!trust.profile_complete) {
      banner.hidden = false;
      banner.className = "trust-banner is-warn";
      banner.innerHTML =
        t("app.banner_need_prof", "Name/phone missing · listing blocked. <button type='button' class='text-link' id='bannerProf'>Complete profile</button>");
      setTimeout(() => {
        $("bannerProf")?.addEventListener("click", () => {
          fillProfileForm(api.getUser());
          setView("profile");
        });
      }, 0);
    } else {
      banner.hidden = false;
      banner.className = "trust-banner is-warn";
      banner.innerHTML =
        t("app.banner_need_seller", "Public seller info missing · listing blocked. <button type='button' class='text-link' id='bannerSeller'>Add seller info</button>");
      setTimeout(() => {
        $("bannerSeller")?.addEventListener("click", () => {
          fillSellerIdForm(api.getUser());
          setView("sellerId");
        });
      }, 0);
    }
  }

  async function ensureSession() {
    if (!api.token()) {
      syncChrome();
      return false;
    }
    try {
      await api.me();
      syncChrome();
      return true;
    } catch {
      api.clearSession();
      syncChrome();
      return false;
    }
  }

  function fillSellerIdForm(u) {
    if (!u) return;
    const sid = u.seller_identity || {};
    if ($("sidType")) $("sidType").value = sid.type || "individual";
    if ($("sidName"))
      $("sidName").value = sid.trade_name || u.real_name || u.display_name || "";
    if ($("sidCeo")) $("sidCeo").value = sid.ceo_name || "";
    if ($("sidBizNo")) $("sidBizNo").value = sid.business_reg_no || "";
    if ($("sidMailOrder")) $("sidMailOrder").value = sid.mail_order_report_no || "";
    if ($("sidEmail"))
      $("sidEmail").value = sid.contact_email || u.email || "";
    if ($("sidPhone")) $("sidPhone").value = sid.contact_phone || u.phone || "";
    if ($("sidAddr")) $("sidAddr").value = sid.address || "";
    toggleSellerBizFields();
  }

  function toggleSellerBizFields() {
    const biz = $("sidType") && $("sidType").value === "business";
    if ($("sidBizFields")) $("sidBizFields").hidden = !biz;
    if ($("sidNameLabel"))
      $("sidNameLabel").textContent = biz ? t("app.sid_name_biz", "Business name *") : t("app.sid_name_ind", "Public name *");
    if ($("sidCeo")) $("sidCeo").required = !!biz;
    if ($("sidBizNo")) $("sidBizNo").required = !!biz;
    if ($("sidAddr")) $("sidAddr").required = !!biz;
  }

  /**
   * Ensure user can list (L2 + seller public identity).
   */
  async function requireListReady() {
    if (!(await ensureSession())) {
      pendingAfterAuth = "create";
      setView("auth");
      switchAuthTab("login");
      const note = $("authNeedNote");
      if (note) {
        note.hidden = false;
        note.textContent =
          t("app.need_gates", "Listing requires sign-in, email verification, name/phone, and public seller info.");
      }
      return false;
    }
    const u = api.getUser();
    const trust = trustOf(u);
    if (!trust.email_verified) {
      pendingAfterAuth = "create";
      showDevCode();
      setView("verify");
      return false;
    }
    if (!trust.profile_complete) {
      pendingAfterAuth = "create";
      fillProfileForm(u);
      setView("profile");
      return false;
    }
    if (!trust.seller_identity_complete) {
      pendingAfterAuth = "create";
      fillSellerIdForm(u);
      setView("sellerId");
      return false;
    }
    if (!trust.can_list) {
      pendingAfterAuth = "create";
      fillProfileForm(u);
      setView("profile");
      return false;
    }
    return true;
  }

  async function afterAuthSuccess() {
    const u = api.getUser();
    const trust = trustOf(u);
    const next = pendingAfterAuth;
    pendingAfterAuth = null;
    const note = $("authNeedNote");
    if (note) note.hidden = true;

    // SNS login: birth date (만 14세) still required once
    if (u && (u.needs_age_gate || !u.birth_date)) {
      setView("age");
      return;
    }

    // Explicit destinations that need a full session path
    if (next === "profile") {
      if (!trust.email_verified) {
        showDevCode();
        setView("verify");
        return;
      }
      fillProfileForm(u);
      setView("profile");
      return;
    }
    if (next === "seller") {
      if (!trust.email_verified) {
        showDevCode();
        setView("verify");
        return;
      }
      fillSellerIdForm(u);
      setView("sellerId");
      return;
    }
    if (next === "create") {
      // Listing still requires verify + profile + seller identity
      if (!trust.email_verified) {
        showDevCode();
        pendingAfterAuth = "create";
        setView("verify");
        return;
      }
      if (!trust.profile_complete) {
        fillProfileForm(u);
        setView("profile");
        return;
      }
      if (!trust.seller_identity_complete) {
        fillSellerIdForm(u);
        setView("sellerId");
        return;
      }
      if (trust.can_list) {
        setView("create");
        return;
      }
    }

    // Default after login: open marketplace like the website (browse freely).
    // Email verify is a soft gate — banner still prompts, but user is not trapped.
    await loadProjects();
    if (!trust.email_verified) {
      updateTrustBanner();
      showDevCode();
    }
  }

  function appendProjectCards(projects) {
    const list = $("projectList");
    projects.forEach((p) => {
      const el = document.createElement("article");
      el.className = "p-card";
      el.innerHTML =
        "<div class='p-card-top'><h3></h3><span class='p-card-badge'></span></div>" +
        "<p class='p-one'></p>" +
        "<div class='p-card-foot'>" +
        "<p class='p-card-price'><span></span><strong></strong></p>" +
        "<p class='p-meta'></p>" +
        "<p class='p-live'></p>" +
        "</div>";
      const cur = p.price_current != null ? p.price_current : p.price_start;
      const bids =
        p.bidder_count != null ? Number(p.bidder_count) || 0 : Number(p.bid_count) || 0;
      const enLang =
        window.WakeAgainI18n &&
        window.WakeAgainI18n.getLang &&
        window.WakeAgainI18n.getLang() === "en";
      const typeBit =
        (enLang && p.product_type_label_en) || p.product_type_label || "";
      const statusBit =
        (enLang && p.status_label_en) || p.status_label || p.status || "";
      const enUi =
        enLang ||
        (document.documentElement.getAttribute("data-wa-lang") || document.documentElement.lang || "")
          .toLowerCase()
          .indexOf("en") === 0;
      let oneLine = p.one_liner || "";
      let titleShow = p.title || "—";
      if (enUi) {
        if (p.title_en) titleShow = p.title_en;
        else {
          var tm = String(p.title || "").match(/[A-Za-z][A-Za-z0-9+.#\-]*/g);
          if (tm && tm.length) titleShow = tm.join(" ");
        }
        if (p.one_liner_en) oneLine = p.one_liner_en;
      }
      const ls = p.listing_status || "";
      const aStatus = p.auction_status || "live";
      el.querySelector("h3").textContent = titleShow;
      el.querySelector(".p-one").textContent = oneLine;
      let kws = Array.isArray(p.keywords) ? p.keywords.filter(Boolean) : [];
      var enK =
        (window.WakeAgainI18n && window.WakeAgainI18n.getLang && window.WakeAgainI18n.getLang() === "en") ||
        String(document.documentElement.getAttribute("data-wa-lang") || "").indexOf("en") === 0;
      if (enK) {
        var latinOnly = kws.filter(function (k) {
          return !/[\uac00-\ud7a3]/.test(String(k));
        });
        if (latinOnly.length) kws = latinOnly;
      }
      kws = kws.slice(0, 5);
      if (kws.length) {
        const kwRow = document.createElement("p");
        kwRow.className = "p-kw";
        kws.forEach(function (k) {
          const tag = document.createElement("span");
          tag.className = "p-kw-tag";
          tag.textContent = "#" + k;
          kwRow.appendChild(tag);
        });
        el.querySelector(".p-one").after(kwRow);
      }

      const badge = el.querySelector(".p-card-badge");
      let badgeText = "LIVE";
      let badgeCls = "";
      if (ls === "pending") {
        badgeText = t("app.badge_pending", "In review");
        badgeCls = "is-wait";
      } else if (ls === "hold") {
        badgeText = t("app.badge_hold", "On hold");
        badgeCls = "is-wait";
      } else if (ls === "rejected") {
        badgeText = t("app.badge_rejected", "Rejected");
        badgeCls = "is-bad";
      } else if (ls === "archived" || aStatus === "ended") {
        badgeText = t("app.badge_archived", "Round ended");
        badgeCls = "is-wait";
      } else if (aStatus === "sold") {
        badgeText = t("app.badge_sold", "Sold");
        badgeCls = "is-sold";
      } else if (bids > 0) {
        badgeText = t("app.badge_live", "Bidding");
      } else if (ls === "approved" && aStatus === "live") {
        badgeText = t("app.badge_open", "This round");
      }
      badge.textContent = badgeText;
      if (badgeCls) badge.classList.add(badgeCls);

      const priceLabel = el.querySelector(".p-card-price span");
      const priceVal = el.querySelector(".p-card-price strong");
      if (aStatus === "sold") {
        priceLabel.textContent = t("app.price_sold", "Sold for");
        priceVal.textContent =
          cur != null || p.sold_price != null
            ? money(p.sold_price != null ? p.sold_price : cur)
            : "—";
      } else {
        priceLabel.textContent = bids > 0 ? t("app.price_now", "Current bid") : t("app.price_start", "Starting bid");
        priceVal.textContent =
          cur != null ? money(cur) : "—";
      }

      const qOff = p.q_credits_offered != null ? Number(p.q_credits_offered) : null;
      const qPrice = p.q_credit_unit_price != null ? Number(p.q_credit_unit_price) : 0;
      let qBit = "";
      if (qOff != null) {
        qBit =
          t("app.q_included", "Help tickets ×{n}", { n: qOff }) +
          (qPrice > 0
            ? t("app.q_addon", " · +{p}/session", { p: money(qPrice) })
            : "");
      }
      const exp =
        p.exposure_score != null
          ? t("app.exposure", "Boost {n}", { n: p.exposure_score })
          : "";
      el.querySelector(".p-meta").textContent = [
        typeBit,
        statusBit,
        qBit,
        exp,
        bids > 0
          ? t("app.bids_n", "{n} bidders", { n: bids })
          : t("app.bids_none", "No bids yet"),
      ]
        .filter(Boolean)
        .join(" · ");

      let liveText = t("app.live_wait", "Waiting for first bid");
      if (ls === "pending") liveText = t("app.live_pending", "In review · not public yet");
      else if (ls === "hold") liveText = t("app.live_hold", "On hold");
      else if (ls === "rejected") liveText = t("app.live_reject", "Please revise");
      else if (ls === "archived" || aStatus === "ended")
        liveText = t("app.live_archived", "Round ended · delisted · re-list needs re-review (lower priority)"
        );
      else if (aStatus === "sold") liveText = t("app.live_sold", "Sold");
      else if (ls === "approved" && aStatus === "live")
        liveText = bids > 0 ? t("app.badge_live", "Bidding") : t("app.live_wait", "Waiting for first bid");
      el.querySelector(".p-live").textContent = liveText;

      // Mine feed: re-list after round ends (re-review, back of queue)
      if (feed === "mine" && p.can_relist) {
        const actions = document.createElement("div");
        actions.className = "p-card-actions";
        actions.style.marginTop = "8px";
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-sm btn-primary";
        btn.textContent = t("app.btn_relist", "Re-list (re-review)");
        btn.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          relistListing(p);
        });
        actions.appendChild(btn);
        el.appendChild(actions);
      }

      el.addEventListener("click", () => {
        goPage("/project.html?id=" + encodeURIComponent(p.id));
      });
      list.appendChild(el);
    });
  }

  async function relistListing(p) {
    if (!p || !p.id) return;
    const ok = window.confirm(
      t("app.relist_confirm", "Re-list “{title}”?\n\n· Ops re-review required\n· After approval it starts at the end of this round’s public list\n· Not a paid pin or bump",
        { title: p.title || "" }
      )
    );
    if (!ok) return;
    try {
      const daysRaw = window.prompt(
        t("app.relist_days_prompt", "Auction days (1–30, default 7)"),
        "7"
      );
      let days = parseInt(daysRaw == null || daysRaw === "" ? "7" : daysRaw, 10);
      if (!Number.isFinite(days)) days = 7;
      days = Math.max(1, Math.min(30, days));
      const res = await api.relistProject(p.id, {
        auction_days: days,
        attest_works: true,
        attest_features: true,
        attest_license: true,
        attest_rights: true,
        attest_transfer: true,
        attest_shots: true,
      });
      window.alert(
        (res && res.note && api.translateBackendText(res.note)) ||
          t("app.relist_ok", "Re-list submitted. It goes public after re-review.")
      );
      feed = "mine";
      loadProjects(true);
    } catch (err) {
      const msg =
        (err && err.detail && (err.detail.message || err.detail)) ||
        (err && err.message) ||
        String(err);
      window.alert(t("app.relist_fail", "Re-list failed") + "\n" + msg);
    }
  }

  async function loadProjects(reset) {
    if (reset !== false) listOffset = 0;
    setView("list");
    syncChrome();
    updateTrustBanner();
    const list = $("projectList");
    const empty = $("emptyList");
    const more = $("btnLoadMore");
    if (listOffset === 0) list.innerHTML = "";
    empty.hidden = true;

    if (feed === "mine") {
      if (!(await ensureSession())) {
        pendingAfterAuth = "list";
        setView("auth");
        switchAuthTab("login");
        return;
      }
    }

    try {
      const data = await api.listProjects(feed === "mine", PAGE, listOffset, marketSearchQ);
      const projects = data.projects || [];
      if (listOffset === 0) {
        empty.hidden = projects.length > 0;
        if (marketSearchQ && !projects.length) {
          empty.textContent = t("app.search_empty", "No search results.");
        } else {
          empty.textContent =
            feed === "mine"
              ? t("app.empty_mine", "You haven’t listed a project yet.")
              : t("app.empty_all", "No public listings yet. Be the first to list.");
        }
      }
      appendProjectCards(projects);
      listOffset += projects.length;
      if (more) more.hidden = !data.has_more;
    } catch (e) {
      empty.hidden = false;
      empty.textContent = e.message || t("app.load_fail", "Failed to load.");
      if (more) more.hidden = true;
    }
  }

  async function loadFees() {
    if (!(await ensureSession())) {
      setView("auth");
      return;
    }
    setView("fees");
    const list = $("feeList");
    const empty = $("feeEmpty");
    list.innerHTML = "";
    list.classList.add("project-list--stack");
    try {
      const data = await api.myFees();
      const inv = data.invoices || [];
      empty.hidden = inv.length > 0;
      if (!inv.length) {
        empty.textContent =
          t("app.fees_empty", "No fee invoices yet. Closed deals show up here.");
      }
      inv.forEach((f) => {
        const el = document.createElement("article");
        el.className = "p-card";
        el.style.minHeight = "auto";
        const pct =
          f.fee_rate_pct != null
            ? Number(f.fee_rate_pct)
            : f.fee_rate != null
              ? Math.round(Number(f.fee_rate) * 100)
              : 10;
        el.innerHTML =
          "<div class='p-card-top'><h3></h3><span class='p-card-badge'></span></div>" +
          "<div class='p-card-foot'><p class='p-card-price'><span></span><strong></strong></p>" +
          "<p class='p-meta'></p><p class='p-live'></p></div>";
        el.querySelector("h3").textContent = f.project_title || t("app.listing_num", "Listing #{id}", { id: f.project_id });
        el.querySelector(".p-card-badge").textContent =
          f.status === "paid" ? t("app.fee_paid", "Confirmed") : t("app.fee_wait", "Pending");
        if (f.status === "paid") el.querySelector(".p-card-badge").classList.add("is-sold");
        else el.querySelector(".p-card-badge").classList.add("is-wait");
        el.querySelector(".p-card-price span").textContent = t("app.fee_pct", "Fee {p}%", { p: pct });
        el.querySelector(".p-card-price strong").textContent =
          money(f.fee_amount);
        el.querySelector(".p-meta").textContent =
          t("app.deal_amount", "Deal {p}", { p: money(f.deal_amount) });
        el.querySelector(".p-live").textContent =
          f.status === "paid"
            ? t("app.fee_paid_note", "Payment confirmed (ops)")
            : t("app.fee_wait_note", "Awaiting payment · ops review") + " · corelabs.studio@gmail.com";
        list.appendChild(el);
      });
    } catch (e) {
      empty.hidden = false;
      empty.textContent = e.message || t("app.load_fail_short", "Load failed");
    }
  }

  async function loadCoupons() {
    if (!(await ensureSession())) {
      setView("auth");
      return;
    }
    setView("coupons");
    location.hash = "coupons";
    const list = $("couponList");
    const empty = $("couponEmpty");
    if (list) list.innerHTML = "";
    // Viral event claims (approved channel post → claim button)
    try {
      const promo = api.myPromoEvent
        ? await api.myPromoEvent()
        : await api.myPromoInstagram();
      const subs = promo.submissions || [];
      const claimable = subs.filter((s) => s.status === "approved");
      const host = list;
      claimable.forEach((s) => {
        const el = document.createElement("article");
        el.className = "p-card";
        el.style.minHeight = "auto";
        el.style.borderColor = "rgba(52,211,153,0.4)";
        const ch = s.channel_label_en || s.channel_label_ko || s.channel || t("app.event", "Event");
        el.innerHTML =
          "<div class='p-card-top'><h3></h3><span class='p-card-badge is-live'>" +
          t("app.coupon_ready", "Ready to claim") +
          "</span></div>" +
          "<div class='p-card-foot'><p class='p-meta'></p>" +
          "<div class='form-actions' style='margin-top:0.5rem'>" +
          "<button type='button' class='btn btn-primary btn-sm btn-claim'>" +
          t("app.coupon_claim", "Claim coupon") +
          "</button></div></div>";
        el.querySelector("h3").textContent = t("app.event_approved", "Event approved · {ch}", { ch: ch });
        el.querySelector(".p-meta").textContent =
          t("app.coupon_claim_hint", "Approved · tap to register an 8% fee coupon (once per account)");
        el.querySelector(".btn-claim").addEventListener("click", async () => {
          try {
            if (api.claimPromoEvent) await api.claimPromoEvent(s.id);
            else await api.claimPromoInstagram(s.id);
            alert(t("app.coupon_claimed", "Coupon registered. 8% fee applies when a deal closes."));
            loadCoupons();
          } catch (ex) {
            alert(ex.message || t("app.coupon_claim_fail", "Claim failed"));
          }
        });
        if (host) host.appendChild(el);
      });
      const pending = subs.filter((s) => s.status === "pending");
      pending.forEach((s) => {
        const el = document.createElement("article");
        el.className = "p-card";
        el.style.minHeight = "auto";
        const ch = s.channel_label_en || s.channel_label_ko || s.channel || t("app.event", "Event");
        el.innerHTML =
          "<div class='p-card-top'><h3></h3><span class='p-card-badge is-wait'>" +
          t("app.badge_pending", "In review") +
          "</span></div>" +
          "<div class='p-card-foot'><p class='p-meta'></p></div>";
        el.querySelector("h3").textContent = t("app.event_pending", "Event pending · {ch}", { ch: ch });
        el.querySelector(".p-meta").textContent = s.post_url || "";
        if (host) host.appendChild(el);
      });
      // Soft CTA when event open and no submission yet
      if (promo.event_open && !subs.some((s) => ["pending", "approved", "claimed"].includes(s.status))) {
        const el = document.createElement("article");
        el.className = "p-card";
        el.style.minHeight = "auto";
        el.style.borderColor = "rgba(212,160,23,0.35)";
        el.innerHTML =
          "<div class='p-card-top'><h3>" +
          t("app.event_promo_title", "Spread the word · 8% coupon") +
          "</h3><span class='p-card-badge is-live'>" +
          t("app.event", "Event") +
          "</span></div>" +
          "<div class='p-card-foot'><p class='p-meta'></p>" +
          "<div class='form-actions' style='margin-top:0.5rem'>" +
          "<a class='btn btn-ghost btn-sm' href='/promo/event.html'>" +
          t("app.event_join", "Join event") +
          "</a></div></div>";
        el.querySelector(".p-meta").textContent =
          t("app.event_promo_hint", "X, Instagram, blog, or community · once per account · same reward");
        if (host) host.appendChild(el);
      }
    } catch {
      /* ignore */
    }
    try {
      const data = await api.myCoupons();
      const items = data.coupons || [];
      if (empty) {
        const hasCards = list && list.children.length > 0;
        empty.hidden = items.length > 0 || hasCards;
      }
      items.forEach((c) => {
        const el = document.createElement("article");
        el.className = "p-card";
        el.style.minHeight = "auto";
        const st =
          c.status === "available"
            ? t("app.coupon_available", "Available")
            : t("app.coupon_used", "Used");
        const origin =
          c.origin === "gift" ? t("app.coupon_gifted_in", "Gift received") : c.origin === "redeem" ? t("app.coupon_code_reg", "Code added") : c.origin || "";
        el.innerHTML =
          "<div class='p-card-top'><h3></h3><span class='p-card-badge'></span></div>" +
          "<div class='p-card-foot'><p class='p-meta'></p>" +
          (c.status === "available"
            ? "<div class='form-actions' style='margin-top:0.5rem'><button type='button' class='btn btn-ghost btn-sm btn-gift'>" +
              t("app.coupon_gift", "Gift") +
              "</button></div>"
            : "") +
          "</div>";
        el.querySelector("h3").textContent =
          c.label_en || c.label_ko || t("app.fee_coupon", "Fee coupon");
        const badge = el.querySelector(".p-card-badge");
        badge.textContent = st;
        if (c.status === "available") badge.classList.add("is-live");
        else badge.classList.add("is-sold");
        el.querySelector(".p-meta").textContent =
          origin +
          (c.used_project_id ? t("app.listing_ref", " · listing #{id}", { id: c.used_project_id }) : "") +
          t("app.no_expiry", " · no expiry");
        const giftBtn = el.querySelector(".btn-gift");
        if (giftBtn) {
          giftBtn.addEventListener("click", async () => {
            const to = prompt(
              t(
                "app.gift_prompt_to",
                "Enter recipient account ID or email.\n(e.g. 12 or friend@email.com)"
              )
            );
            if (!to || !to.trim()) return;
            if (
              !confirm(
                t("app.gift_confirm", "Gift this coupon? It moves to their account immediately and can’t be undone. (We don’t broker coupon sales.)")
              )
            )
              return;
            try {
              await api.giftCoupon(c.id, to.trim());
              alert(t("app.gift_ok", "Gifted. It’s on their account now."));
              loadCoupons();
            } catch (ex) {
              alert(ex.message || t("app.gift_fail", "Gift failed"));
            }
          });
        }
        if (list) list.appendChild(el);
      });
    } catch (e) {
      if (empty) {
        empty.hidden = false;
        empty.textContent = e.message || t("app.load_fail_short", "Load failed");
      }
    }
  }

  // --- events ---
  document.querySelectorAll(".auth-tabs .tab").forEach((btn) => {
    btn.addEventListener("click", () => switchAuthTab(btn.getAttribute("data-tab") || "login"));
  });

  function isEnUi() {
    try {
      return (
        window.WakeAgainI18n &&
        window.WakeAgainI18n.getLang &&
        window.WakeAgainI18n.getLang() === "en"
      );
    } catch (e) {
      return true;
    }
  }

  /** Server credit / buyer-rank labels are KO — map for EN UI (no hangul under EN). */
  var CREDIT_LABEL_EN = {
    최고: "Elite",
    우수: "Good",
    신뢰: "Trusted",
    보통: "Average",
    신규: "New",
    주의: "Caution",
    위험: "Risk",
    일반: "Standard",
    최우수: "Excellent",
    // buyer rank
    "파워 바이어": "Power buyer",
    "헤비 구매자": "Heavy buyer",
    "단골 구매자": "Regular buyer",
    "첫 구매 완료": "First purchase",
    "구매 준비 중": "Getting ready",
  };

  function creditLabelUi(label) {
    if (label == null || label === "") return "";
    var cl = String(label);
    if (!isEnUi()) return cl;
    return CREDIT_LABEL_EN[cl] || cl;
  }

  /** Override browser chrome validation (KO Chrome balloons) with app language. */
  function wireEmailField(el) {
    if (!el || el.dataset.waEmailWired === "1") return;
    el.dataset.waEmailWired = "1";
    const refresh = function () {
      el.setCustomValidity("");
      if (!el.value.trim()) {
        el.setCustomValidity(t("app.err_email_required", "Please enter your email."));
        return;
      }
      if (el.validity.typeMismatch || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value.trim())) {
        const v = el.value.trim();
        if (v.indexOf("@") < 0) {
          el.setCustomValidity(
            t("app.err_email_at", "Please include an '@' in the email address. '{v}' is missing an '@'.", {
              v: v,
            })
          );
        } else {
          el.setCustomValidity(t("app.err_email_invalid", "Please enter a valid email address."));
        }
      }
    };
    el.addEventListener("invalid", refresh);
    el.addEventListener("input", function () {
      el.setCustomValidity("");
    });
    el.addEventListener("blur", function () {
      if (el.value.trim()) refresh();
    });
  }

  /**
   * EN UI: use text date fields so Korean Chrome does not show "연도-월-일".
   * KO UI: keep native type=date.
   */
  function syncBirthDateInputs() {
    const en = isEnUi();
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, "0");
    const dd = String(now.getDate()).padStart(2, "0");
    const maxDay = yyyy + "-" + mm + "-" + dd;
    ["regBirth", "ageBirth"].forEach(function (id) {
      const el = $(id);
      if (!el) return;
      const val = el.value;
      if (en) {
        if (el.type !== "text") el.type = "text";
        el.placeholder = t("app.birth_ph", "YYYY-MM-DD");
        el.setAttribute("inputmode", "numeric");
        el.setAttribute("pattern", "\\d{4}-\\d{2}-\\d{2}");
        el.setAttribute("maxlength", "10");
        el.setAttribute("autocomplete", "bday");
        el.removeAttribute("max");
        el.dataset.waDateText = "1";
        el.setCustomValidity("");
        const onInvalid = function () {
          el.setCustomValidity("");
          if (!el.value.trim()) {
            el.setCustomValidity(t("app.reg_birth_err", "Enter your date of birth."));
          } else if (!/^\d{4}-\d{2}-\d{2}$/.test(el.value.trim())) {
            el.setCustomValidity(t("app.err_birth_format", "Enter your date of birth as YYYY-MM-DD."));
          }
        };
        if (el.dataset.waDateWired !== "1") {
          el.dataset.waDateWired = "1";
          el.addEventListener("invalid", onInvalid);
          el.addEventListener("input", function () {
            el.setCustomValidity("");
          });
        }
      } else {
        if (el.type !== "date") el.type = "date";
        el.removeAttribute("placeholder");
        el.removeAttribute("pattern");
        el.removeAttribute("maxlength");
        el.removeAttribute("inputmode");
        el.setAttribute("max", maxDay);
        el.setCustomValidity("");
        el.dataset.waDateText = "0";
      }
      if (val) el.value = val;
      else if (en) el.placeholder = t("app.birth_ph", "YYYY-MM-DD");
    });
  }

  // Birth fields + email validity (browser chrome often stays KO on Korean Windows)
  ["loginEmail", "regEmail", "resetEmail"].forEach(function (id) {
    wireEmailField($(id));
  });
  syncBirthDateInputs();

  /** Password show/hide (eye) on login / register / reset */
  document.querySelectorAll(".pw-toggle[data-pw-target]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-pw-target");
      const input = id ? $(id) : null;
      if (!input) return;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.classList.toggle("is-on", show);
      btn.setAttribute("aria-pressed", show ? "true" : "false");
      btn.setAttribute("aria-label", show ? t("app.pw_hide", "Hide password") : t("app.pw_show", "Show password"));
      btn.title = show ? t("app.pw_hide", "Hide password") : t("app.pw_show", "Show password");
    });
  });

  $("formLogin")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("loginErr"));
    const emailEl = $("loginEmail");
    if (emailEl) {
      emailEl.setCustomValidity("");
      const emailVal = emailEl.value.trim();
      if (!emailVal) {
        showErr($("loginErr"), t("app.err_email_required", "Please enter your email."));
        emailEl.focus();
        return;
      }
      if (emailVal.indexOf("@") < 0) {
        showErr(
          $("loginErr"),
          t("app.err_email_at", "Please include an '@' in the email address. '{v}' is missing an '@'.", {
            v: emailVal,
          })
        );
        emailEl.focus();
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
        showErr($("loginErr"), t("app.err_email_invalid", "Please enter a valid email address."));
        emailEl.focus();
        return;
      }
    }
    const btn = e.target.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    const email = $("loginEmail").value.trim();
    const pass = $("loginPass").value;
    const remember = !!($("loginRemember") && $("loginRemember").checked);
    try {
      await api.login(email, pass);
      try {
        if (remember) api.setSavedLogin(email, pass);
        else api.clearSavedLogin();
      } catch (e2) {}
      await afterAuthSuccess();
    } catch (err) {
      var msg = (err && err.message) || t("app.login_fail", "Sign-in failed.");
      if (/failed to fetch|networkerror|load failed|network request failed/i.test(String(msg))) {
        msg = t(
          "app.login_server_down",
          "Can’t reach the server. Start WakeAgain Local (desktop shortcut) and try again."
        );
      }
      showErr($("loginErr"), msg);
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  $("btnShowReset")?.addEventListener("click", () => {
    $("formLogin").hidden = true;
    $("formRegister").hidden = true;
    if ($("formFindId")) $("formFindId").hidden = true;
    $("formReset").hidden = false;
    $("resetEmail").value = $("loginEmail").value || "";
  });
  $("btnShowFindId")?.addEventListener("click", () => {
    $("formLogin").hidden = true;
    $("formRegister").hidden = true;
    if ($("formReset")) $("formReset").hidden = true;
    $("formFindId").hidden = false;
    if ($("findIdResult")) $("findIdResult").hidden = true;
    showErr($("findIdErr"));
  });
  $("btnFindIdBack")?.addEventListener("click", () => {
    hideAuthExtraForms();
    $("formFindId").hidden = true;
    $("formLogin").hidden = false;
  });
  $("formFindId")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("findIdErr"));
    if ($("findIdResult")) $("findIdResult").hidden = true;
    const btn = e.target.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      const data = await api.findEmail(
        $("findIdName").value.trim(),
        $("findIdPhone").value.trim()
      );
      if (data.found) {
        // API returns masked only (privacy). Prefer email_masked / emails_masked.
        const list =
          Array.isArray(data.emails_masked) && data.emails_masked.length
            ? data.emails_masked
            : Array.isArray(data.emails) && data.emails.length
              ? data.emails
              : data.email_masked
                ? [data.email_masked]
                : data.email
                  ? [data.email]
                  : [];
        if (!list.length) {
          showErr(
            $("findIdErr"),
            data.message || t("app.find_id_not_found", "No matching account found.")
          );
        } else {
          $("findIdEmail").textContent = list.join("\n");
          $("findIdResult").hidden = false;
          // Do not store full email for auto-fill (API no longer returns it).
          if ($("findIdResult")) $("findIdResult").dataset.email = "";
          showErr(
            $("findIdErr"),
            data.message ||
              t("app.find_id_ok", "Found an email hint for this account. Only part of it is shown."
              )
          );
        }
      } else {
        showErr(
          $("findIdErr"),
          data.message || t("app.find_id_not_found", "No matching account found.")
        );
      }
    } catch (err) {
      showErr($("findIdErr"), err.message || t("app.find_id_not_found", "No matching account found."));
    } finally {
      if (btn) btn.disabled = false;
    }
  });
  $("btnFindIdUse")?.addEventListener("click", () => {
    // Full address is not returned (masked only). Go to login and let user type it.
    hideAuthExtraForms();
    $("formFindId").hidden = true;
    $("formLogin").hidden = false;
    if ($("loginEmail")) {
      $("loginEmail").value = "";
      $("loginEmail").focus();
      $("loginEmail").placeholder =
        t("app.find_id_login_hint", "Use the hint to enter your full email");
    }
  });
  $("btnResetBack")?.addEventListener("click", () => {
    $("formReset").hidden = true;
    if ($("formFindId")) $("formFindId").hidden = true;
    $("formLogin").hidden = false;
  });
  $("btnResetReq")?.addEventListener("click", async () => {
    showErr($("resetErr"));
    if ($("resetDevBox")) $("resetDevBox").hidden = true;
    if ($("resetDevNote")) {
      $("resetDevNote").hidden = true;
      $("resetDevNote").textContent = "";
    }
    const btn = $("btnResetReq");
    if (btn) btn.disabled = true;
    try {
      const data = await api.passwordResetRequest($("resetEmail").value.trim());
      if (data.dev_email_code) {
        $("resetDevBox").hidden = false;
        $("resetDevCode").textContent = data.dev_email_code;
        $("resetCode").value = data.dev_email_code;
        if ($("resetDevLabel")) {
          $("resetDevLabel").textContent = data.email_sent
            ? t("app.reset_code_also", "On-screen code (also emailed)")
            : t("app.reset_code_screen", "Reset code (enter here)");
        }
        if ($("resetDevNote") && (data.warning || data.dev_note)) {
          $("resetDevNote").hidden = false;
          $("resetDevNote").textContent = data.warning || data.dev_note || "";
        }
      }
      let msg = "";
      if (data.email_sent) {
        msg = t("app.reset_sent_mail", "Email sent. Check inbox and spam.");
      } else if (data.dev_email_code) {
        msg =
          data.warning ||
          t("app.reset_sent_screen", "Code shown on screen instead of email. Enter it below.");
      } else if (data.warning) {
        msg = data.warning;
      } else {
        msg = t("app.reset_sent", "If that email is registered, a reset code was issued. Check spam or confirm the address."
        );
      }
      showErr($("resetErr"), msg);
    } catch (err) {
      showErr($("resetErr"), err.message || t("app.fail", "Failed"));
    } finally {
      if (btn) btn.disabled = false;
    }
  });
  $("formReset")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("resetErr"));
    try {
      await api.passwordResetConfirm(
        $("resetEmail").value.trim(),
        $("resetCode").value.trim(),
        $("resetPass").value
      );
      showErr($("resetErr"), t("app.reset_ok", "Password updated. Please sign in."));
      $("formReset").hidden = true;
      $("formLogin").hidden = false;
    } catch (err) {
      showErr($("resetErr"), err.message || t("app.fail", "Failed"));
    }
  });
  $("btnNotif")?.addEventListener("click", () => loadNotifications());
  $("btnBackNotif")?.addEventListener("click", () => loadProjects(true));
  $("btnFees")?.addEventListener("click", () => loadFees());
  $("btnCoupons")?.addEventListener("click", () => loadCoupons());
  $("btnCouponsFromFees")?.addEventListener("click", () => loadCoupons());
  $("btnBackCoupons")?.addEventListener("click", () => {
    location.hash = "list";
    setView("list");
  });
  $("formCouponRedeem")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = $("couponRedeemErr");
    const ok = $("couponRedeemOk");
    showErr(err);
    if (ok) {
      ok.hidden = true;
      ok.textContent = "";
    }
    const code = $("couponCode") ? $("couponCode").value.trim() : "";
    if (!code) {
      showErr(err, t("app.code_required", "Enter the code."));
      return;
    }
    try {
      const res = await api.redeemCoupon(code);
      if (ok) {
        ok.hidden = false;
        ok.textContent =
          t("app.coupon_reg_ok", "Registered: {code}", {
            code: (res.coupon && (res.coupon.label_en || res.coupon.label_ko)) || t("app.coupon", "Coupon"),
          });
      }
      if ($("couponCode")) $("couponCode").value = "";
      loadCoupons();
    } catch (ex) {
      showErr(err, ex.message || t("app.save_fail", "Save failed"));
    }
  });
  $("btnBackFees")?.addEventListener("click", () => loadProjects(true));
  $("btnLoadMore")?.addEventListener("click", () => loadProjects(false));
  $("btnMarkRead")?.addEventListener("click", async () => {
    try {
      await api.markNotificationsRead();
      await loadNotifications();
      refreshNotifBadge();
    } catch {
      /* ignore */
    }
  });

  $("formRegister")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("regErr"));
    const terms = $("regTerms");
    if (terms && !terms.checked) {
      showErr($("regErr"), t("app.reg_terms_err", "Please accept the Terms and Privacy Policy."));
      return;
    }
    const pass = $("regPass") ? $("regPass").value : "";
    const pass2 = $("regPass2") ? $("regPass2").value : "";
    const emailReg = $("regEmail") ? $("regEmail").value.trim() : "";
    if (!emailReg) {
      showErr($("regErr"), t("app.err_email_required", "Please enter your email."));
      if ($("regEmail")) $("regEmail").focus();
      return;
    }
    if (emailReg.indexOf("@") < 0) {
      showErr(
        $("regErr"),
        t("app.err_email_at", "Please include an '@' in the email address. '{v}' is missing an '@'.", {
          v: emailReg,
        })
      );
      if ($("regEmail")) $("regEmail").focus();
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailReg)) {
      showErr($("regErr"), t("app.err_email_invalid", "Please enter a valid email address."));
      if ($("regEmail")) $("regEmail").focus();
      return;
    }
    const birth = $("regBirth") ? $("regBirth").value.trim() : "";
    const ageOk = $("regAge14") ? $("regAge14").checked : false;
    if (!birth) {
      showErr($("regErr"), t("app.reg_birth_err", "Enter your date of birth."));
      if ($("regBirth")) $("regBirth").focus();
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(birth)) {
      showErr($("regErr"), t("app.err_birth_format", "Enter your date of birth as YYYY-MM-DD."));
      if ($("regBirth")) $("regBirth").focus();
      return;
    }
    // Client-side age check (server is authoritative)
    try {
      const parts = birth.split("-").map(Number);
      const by = parts[0];
      const bm = parts[1];
      const bd = parts[2];
      const today = new Date();
      let age = today.getFullYear() - by;
      const m = today.getMonth() + 1 - bm;
      if (m < 0 || (m === 0 && today.getDate() < bd)) age -= 1;
      if (age < 14) {
        showErr($("regErr"), t("app.reg_under14", "You must be 14+ to join WakeAgain."));
        return;
      }
    } catch (_) {
      showErr($("regErr"), t("app.reg_birth_bad", "Please check your date of birth."));
      return;
    }
    if (!ageOk) {
      showErr($("regErr"), t("app.reg_age_check", "Please confirm you are 14 or older."));
      return;
    }
    if (pass.length < 8) {
      showErr($("regErr"), t("app.reg_pass_len", "Password must be at least 8 characters."));
      return;
    }
    if (pass !== pass2) {
      showErr($("regErr"), t("app.reg_pass_match", "Passwords don’t match. Try again."));
      if ($("regPass2")) $("regPass2").focus();
      return;
    }
    const btn = e.target.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      await api.register(
        $("regEmail").value.trim(),
        pass,
        $("regName").value.trim(),
        birth,
        true,
        $("regCountry") ? $("regCountry").value : ""
      );
      pendingAfterAuth = pendingAfterAuth || "create";
      await afterAuthSuccess();
    } catch (err) {
      showErr($("regErr"), err.message || t("app.reg_fail", "Sign-up failed."));
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  $("formVerify")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("verifyErr"));
    try {
      await api.verifyEmail($("verifyCode").value.trim());
      const u = api.getUser();
      const trust = trustOf(u);
      if (!trust.profile_complete) {
        fillProfileForm(u);
        setView("profile");
      } else if (!trust.seller_identity_complete) {
        fillSellerIdForm(u);
        setView("sellerId");
      } else {
        await afterAuthSuccess();
      }
    } catch (err) {
      showErr($("verifyErr"), err.message || t("app.verify_fail", "Verification failed"));
    }
  });

  $("btnResendCode")?.addEventListener("click", async () => {
    showErr($("verifyErr"));
    try {
      const data = await api.resendVerify();
      showDevCode(data && data.warning);
      let msg =
        (data && data.message) ||
        t("app.verify_resent", "A new code was issued.");
      if (data && data.email_sent) msg += t("app.reg_ok_mail", " · email sent (check spam)");
      else if (api.getDevCode()) msg += t("app.reg_ok_screen", " · code shown on screen");
      else if (data && data.warning) msg += " · " + data.warning;
      // use non-error tone: clear then set as status on verifyErr with soft style
      showErr($("verifyErr"), msg);
    } catch (err) {
      showErr($("verifyErr"), err.message || t("app.resend_fail", "Resend failed"));
    }
  });

  $("formProfile")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("profErr"));
    try {
      await api.updateProfile({
        real_name: $("profReal").value.trim(),
        phone: $("profPhone").value.trim(),
        // Always both — no purpose picker (was confusing empty UI after t("app.role_both", "Seller+buyer"))
        role: "both",
        display_name: $("profDisplay").value.trim(),
        country: $("profCountry") ? $("profCountry").value : "",
      });
      const u = api.getUser();
      const trust = trustOf(u);
      // Only force seller-identity when user is mid-listing flow.
      // Do not bounce to seller form just because role is both/seller.
      if (pendingAfterAuth === "create") {
        if (!trust.seller_identity_complete) {
          fillSellerIdForm(u);
          setView("sellerId");
        } else {
          pendingAfterAuth = null;
          setView("create");
        }
      } else {
        await loadProjects();
      }
    } catch (err) {
      if (err.code === "email_unverified") {
        showDevCode();
        setView("verify");
      }
      showErr($("profErr"), err.message || t("app.save_fail", "Save failed"));
    }
  });

  $("sidType")?.addEventListener("change", toggleSellerBizFields);
  $("btnGoSellerId")?.addEventListener("click", () => {
    fillSellerIdForm(api.getUser());
    setView("sellerId");
  });
  $("btnBackFromSellerId")?.addEventListener("click", () => {
    fillProfileForm(api.getUser());
    setView("profile");
  });
  $("formSellerId")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("sidErr"));
    const type = $("sidType") ? $("sidType").value : "individual";
    const payload = {
      seller_type: type,
      trade_name: $("sidName") ? $("sidName").value.trim() : "",
      ceo_name: $("sidCeo") ? $("sidCeo").value.trim() : "",
      business_reg_no: $("sidBizNo") ? $("sidBizNo").value.trim() : "",
      mail_order_report_no: $("sidMailOrder") ? $("sidMailOrder").value.trim() : "",
      contact_email: $("sidEmail") ? $("sidEmail").value.trim() : "",
      contact_phone: $("sidPhone") ? $("sidPhone").value.trim() : "",
      address: $("sidAddr") ? $("sidAddr").value.trim() : "",
    };
    try {
      await api.updateSellerIdentity(payload);
      if (pendingAfterAuth === "create") {
        pendingAfterAuth = null;
        if (await requireListReady()) setView("create");
      } else {
        setView("list");
        await loadProjects();
      }
    } catch (err) {
      showErr($("sidErr"), err.message || t("app.save_fail", "Save failed"));
    }
  });

  $("formSettle")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("setErr"));
    try {
      await api.updateSettlement({
        holder: $("setHolder").value.trim(),
        bank: $("setBank").value.trim(),
        account: $("setAccount").value.trim(),
        is_business: $("setBiz").checked,
      });
      await loadProjects();
    } catch (err) {
      showErr($("setErr"), err.message || t("app.save_fail", "Save failed"));
    }
  });

  function doLogout() {
    api.clearSession();
    feed = "all";
    document.querySelectorAll(".seg-btn").forEach((x) => {
      x.classList.toggle("is-on", x.getAttribute("data-feed") === "all");
    });
    setView("auth");
    switchAuthTab("login");
    fillSavedLoginForm();
    syncChrome();
  }

  $("btnLogout")?.addEventListener("click", doLogout);
  $("btnLogoutFromProfile")?.addEventListener("click", doLogout);
  $("btnFeesFromProfile")?.addEventListener("click", () => loadFees());

  $("btnGoLogin")?.addEventListener("click", () => {
    pendingAfterAuth = "list";
    setView("auth");
    switchAuthTab("login");
    fillSavedLoginForm();
  });

  async function loadBlockList() {
    const list = $("blockList");
    const empty = $("blockListEmpty");
    const errEl = $("blockListErr");
    if (!list) return;
    if (errEl) {
      errEl.hidden = true;
      errEl.textContent = "";
    }
    list.innerHTML = "";
    if (empty) empty.hidden = true;
    try {
      const data = await api.listBlocks();
      const blocks = data.blocks || [];
      if (!blocks.length) {
        if (empty) empty.hidden = false;
        return;
      }
      blocks.forEach((b) => {
        const row = document.createElement("div");
        row.className = "project-card";
        row.style.cssText = "display:flex;align-items:center;justify-content:space-between;gap:0.75rem;padding:0.75rem 0.9rem";
        const name = (b.display_name || t("app.user", "User")).replace(/</g, "&lt;");
        const meta = (b.email_masked || "").replace(/</g, "&lt;");
        row.innerHTML =
          "<div><strong>" +
          name +
          "</strong>" +
          (meta ? '<p class="muted fine" style="margin:0.15rem 0 0">' + meta + "</p>" : "") +
          "</div>" +
          '<button type="button" class="btn btn-ghost btn-sm" data-unblock="' +
          String(b.blocked_user_id) +
          '">' +
          (window.WakeAgainI18n && window.WakeAgainI18n.t
            ? window.WakeAgainI18n.t("app.blocks_unblock")
            : t("app.unblock", "Unblock")) +
          "</button>";
        list.appendChild(row);
      });
      list.querySelectorAll("[data-unblock]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const uid = btn.getAttribute("data-unblock");
          if (!uid) return;
          btn.disabled = true;
          try {
            await api.unblockUser(uid);
            await loadBlockList();
          } catch (ex) {
            if (errEl) {
              errEl.hidden = false;
              errEl.textContent = ex.message || t("app.unblock_fail", "Unblock failed");
            }
            btn.disabled = false;
          }
        });
      });
    } catch (ex) {
      if (errEl) {
        errEl.hidden = false;
        errEl.textContent = ex.message || t("app.block_load_fail", "Couldn’t load block list.");
      }
      if (empty) empty.hidden = false;
    }
  }

  async function loadGiftCouponSelect() {
    const sel = $("giftCouponSelect");
    if (!sel) return;
    sel.innerHTML = "";
    const emptyOpt = document.createElement("option");
    emptyOpt.value = "";
    emptyOpt.textContent = t("app.coupon_loading", "Loading available coupons…");
    sel.appendChild(emptyOpt);
    try {
      const data = await api.myCoupons();
      const items = (data.coupons || []).filter((c) => c.status === "available");
      sel.innerHTML = "";
      if (!items.length) {
        const o = document.createElement("option");
        o.value = "";
        o.textContent = t("app.coupon_none_gift", "No coupons to gift");
        sel.appendChild(o);
        sel.disabled = true;
        return;
      }
      sel.disabled = false;
      const ph = document.createElement("option");
      ph.value = "";
      ph.textContent = t("app.coupon_pick", "Choose a coupon…");
      sel.appendChild(ph);
      items.forEach((c) => {
        const o = document.createElement("option");
        o.value = String(c.id);
        const origin =
          c.origin === "gift" ? t("app.coupon_gifted_in", "Gift received") : c.origin === "redeem" ? t("app.coupon_code_reg", "Code added") : c.origin || "";
        o.textContent =
          (c.label_en || c.label_ko || t("app.fee_coupon", "Fee coupon")) +
          (origin ? " · " + origin : "") +
          " (#" +
          c.id +
          ")";
        sel.appendChild(o);
      });
    } catch (e) {
      sel.innerHTML = "";
      const o = document.createElement("option");
      o.value = "";
      o.textContent = e.message || t("app.coupon_list_fail", "Couldn’t load coupons");
      sel.appendChild(o);
      sel.disabled = true;
    }
  }

  async function openProfile() {
    if (!(await ensureSession())) {
      setView("auth");
      return;
    }
    const u = api.getUser();
    // Profile is viewable without email verify — same as website soft gates
    fillProfileForm(u);
    const idLine = $("myAccountIdLine");
    const idEl = $("myAccountId");
    if (u && u.id != null && idEl) {
      idEl.textContent = String(u.id);
      if (idLine) idLine.hidden = false;
    }
    setView("profile");
    loadBlockList();
    loadGiftCouponSelect();
  }
  $("btnProfile")?.addEventListener("click", () => openProfile());
  $("userChip")?.addEventListener("click", () => openProfile());

  $("formCouponGift")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = $("giftCouponErr");
    const ok = $("giftCouponOk");
    if (err) {
      err.hidden = true;
      err.textContent = "";
    }
    if (ok) {
      ok.hidden = true;
      ok.textContent = "";
    }
    const couponId = ($("giftCouponSelect") && $("giftCouponSelect").value) || "";
    const to = ($("giftToRecipient") && $("giftToRecipient").value.trim()) || "";
    if (!couponId) {
      if (err) {
        err.hidden = false;
        err.textContent = t("app.coupon_pick_need", "Select a coupon to send.");
      }
      return;
    }
    if (!to) {
      if (err) {
        err.hidden = false;
        err.textContent = t("app.gift_to_need", "Enter recipient account ID or email.");
      }
      return;
    }
    if (
      !confirm(
        t("app.gift_confirm", "Gift this coupon? It moves to their account immediately and can’t be undone. (We don’t broker coupon sales.)")
      )
    ) {
      return;
    }
    const btn = $("btnGiftCoupon");
    if (btn) btn.disabled = true;
    try {
      const res = await api.giftCoupon(couponId, to);
      if (ok) {
        ok.hidden = false;
        ok.textContent =
          (res && res.message_ko && api.translateBackendText(res.message_ko)) ||
          t("app.gift_done", "Gifted. Auto-registered on their account.");
      }
      if ($("giftToRecipient")) $("giftToRecipient").value = "";
      await loadGiftCouponSelect();
    } catch (ex) {
      if (err) {
        err.hidden = false;
        err.textContent = ex.message || t("app.gift_fail", "Gift failed");
      }
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  $("btnGoCouponsFromProfile")?.addEventListener("click", () => {
    loadCoupons();
  });

  $("btnBackFromProfile")?.addEventListener("click", () => loadProjects());
  $("btnGoSettle")?.addEventListener("click", () => {
    fillProfileForm(api.getUser());
    setView("settle");
  });
  $("btnBackFromSettle")?.addEventListener("click", () => {
    fillProfileForm(api.getUser());
    setView("profile");
  });

  $("btnRefresh")?.addEventListener("click", () => loadProjects());
  $("btnNew")?.addEventListener("click", async () => {
    if (await requireListReady()) setView("create");
  });
  $("btnBackList")?.addEventListener("click", () => loadProjects());

  // Brand / 홈 → site landing or marketplace (never dead-end)
  document.querySelectorAll("[data-nav-home]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      goHomeSite();
    });
  });
  document.querySelectorAll("[data-nav-market]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      goMarketList();
    });
  });
  // Logo: stay in app marketplace (list) so login shell always has a home
  var brand = document.querySelector("header.app-top a.brand");
  if (brand) {
    brand.addEventListener("click", function (e) {
      e.preventDefault();
      if (api.isLoggedIn && api.isLoggedIn()) {
        goMarketList();
      } else {
        setView("auth");
        switchAuthTab("login");
      }
    });
  }
  $("btnVerifySkip")?.addEventListener("click", function () {
    pendingAfterAuth = null;
    loadProjects(true);
  });
  $("btnVerifyHome")?.addEventListener("click", function (e) {
    e.preventDefault();
    goHomeSite();
  });
  $("btnAuthBrowse")?.addEventListener("click", function (e) {
    e.preventDefault();
    loadProjects(true);
  });
  $("btnAuthHome")?.addEventListener("click", function (e) {
    e.preventDefault();
    goHomeSite();
  });

  document.querySelectorAll(".seg-btn").forEach((b) => {
    b.addEventListener("click", () => {
      // skip keyword mode buttons inside create form
      if (b.closest && b.closest("#kwBlock")) return;
      if (b.getAttribute("data-kw-mode")) return;
      if (!b.getAttribute("data-feed")) return;
      document.querySelectorAll(".seg-btn[data-feed]").forEach((x) => x.classList.remove("is-on"));
      b.classList.add("is-on");
      feed = b.getAttribute("data-feed") || "all";
      loadProjects(true);
    });
  });

  document.querySelectorAll(".tabbar-item[data-go]").forEach((b) => {
    b.addEventListener("click", async () => {
      const go = b.getAttribute("data-go");
      if (go === "home") {
        goHomeSite();
        return;
      }
      if (go === "new") {
        if (await requireListReady()) setView("create");
      } else if (go === "profile") {
        openProfile();
      } else {
        await loadProjects();
      }
    });
  });

  // Start price bands by product status
  let pricingBands = null;
  function bandForStatus(status) {
    if (!pricingBands || !pricingBands.statuses) return null;
    return (
      pricingBands.statuses.find((s) => s.status === status || s.key === status || s.label === status) ||
      null
    );
  }
  function renderCriteria(el, band) {
    if (!el || !band) return;
    el.hidden = false;
    const yes = (band.criteria_yes || [])
      .slice(0, 4)
      .map((t) => "<li>" + t + "</li>")
      .join("");
    const no = (band.criteria_no || [])
      .slice(0, 3)
      .map((t) => "<li>" + t + "</li>")
      .join("");
    el.innerHTML =
      "<p class='sc-when'>" +
      (band.when || band.blurb || "") +
      "</p>" +
      (yes
        ? "<div class='sc-label'>" +
          t("app.status_pick_when", "Choose when") +
          "</div><ul>" +
          yes +
          "</ul>"
        : "") +
      (no
        ? "<div class='sc-label'>" +
          t("app.status_not_when", "Not when") +
          "</div><ul>" +
          no +
          "</ul>"
        : "") +
      (band.demo_expect
        ? "<div class='sc-label'>" +
          t("app.status_demo", "Demo") +
          "</div><p class='sc-when' style='margin:0'>" +
          band.demo_expect +
          "</p>"
        : "");
  }

  function isEnUi() {
    return !!(
      window.WakeAgainI18n &&
      window.WakeAgainI18n.getLang &&
      window.WakeAgainI18n.getLang() === "en"
    );
  }

  function bandLabel(band) {
    if (!band) return "";
    return (isEnUi() && band.label_en) || band.label || band.status || "";
  }

  function bandBlurb(band) {
    if (!band) return "";
    return (isEnUi() && band.blurb_en) || band.blurb || "";
  }

  /** Prefer radio chips; fall back to select (legacy). */
  function fieldValue(nameOrId) {
    const checked = document.querySelector(
      'input[type="radio"][name="' + nameOrId + '"]:checked'
    );
    if (checked) return String(checked.value || "").trim();
    const el = $(nameOrId);
    return el ? String(el.value || "").trim() : "";
  }

  function setFieldValue(nameOrId, value) {
    const radios = document.querySelectorAll(
      'input[type="radio"][name="' + nameOrId + '"]'
    );
    if (radios.length) {
      let matched = false;
      radios.forEach(function (r) {
        const on = r.value === value;
        r.checked = on;
        if (on) matched = true;
      });
      if (!matched && value) {
        /* leave none checked if unknown */
      }
    }
    const el = $(nameOrId);
    if (el) el.value = value || "";
  }

  function syncSelectFromRadios(nameOrId) {
    const el = $(nameOrId);
    if (!el) return;
    const v = fieldValue(nameOrId);
    if (v) el.value = v;
  }

  function wireChoiceChips(nameOrId, onChange) {
    const radios = document.querySelectorAll(
      'input[type="radio"][name="' + nameOrId + '"]'
    );
    if (!radios.length) return;
    radios.forEach(function (r) {
      r.addEventListener("change", function () {
        syncSelectFromRadios(nameOrId);
        if (typeof onChange === "function") onChange();
      });
    });
    syncSelectFromRadios(nameOrId);
  }

  function applyPriceGuide(forceSuggest) {
    const st = fieldValue("pStatus");
    const band = bandForStatus(st);
    const guide = $("pPriceGuide");
    const hint = $("pPriceHint");
    const price = $("pPrice");
    const criteria = $("pStatusCriteria");
    const en = isEnUi();
    if (!band) {
      if (guide)
        guide.textContent = en
          t("app.status_price_note", "Start-price band depends on status.");
      if (criteria) criteria.hidden = true;
      return;
    }
    renderCriteria(criteria, band);
    if (guide) {
      const moneyFn =
        window.WakeAgainI18n && window.WakeAgainI18n.formatMoney
          ? (n) => window.WakeAgainI18n.formatMoney(n)
          : (n) => "$" + Math.round(Number(n) / 1350).toLocaleString("en-US");
      guide.innerHTML =
        "<strong>" +
        bandLabel(band) +
        "</strong> — " +
        bandBlurb(band) +
        "<br/>" +
        t("app.price_rec", "Suggested ") +
        "<strong>" +
        moneyFn(band.suggest) +
        "</strong> · " +
        t("app.price_min", "Min ") +
        moneyFn(band.min) +
        " · " +
        t("app.price_step", "Bid step ") +
        moneyFn(band.min_increment);
    }
    if (hint) {
      const moneyFn =
        window.WakeAgainI18n && window.WakeAgainI18n.formatMoney
          ? (n) => window.WakeAgainI18n.formatMoney(n)
          : (n) => "$" + Math.round(Number(n) / 1350).toLocaleString("en-US");
      hint.textContent =
        (band.examples || "") +
        t("app.price_cap_warn", " · soft cap ~{p} (warn only if higher)", {
          p: moneyFn(band.max_soft),
        });
    }
    if (price) {
      price.min = band.min;
      price.step = band.min_increment;
      if (forceSuggest || !price.value) {
        price.value = band.suggest;
      }
    }
  }
  $("pStatus")?.addEventListener("change", () => applyPriceGuide(true));
  wireChoiceChips("pStatus", function () {
    applyPriceGuide(true);
  });

  function applyDemoHelp() {
    const key = fieldValue("pProductType");
    const help = window.WakeAgainDemoHelp;
    if (!help) return;
    // Show under product type and reinforce near demo field
    help.applyTo($("pDemoHelp"), null, key || null);
    help.applyTo($("pDemoHelpBelow"), $("pDemo"), key || null);
  }
  $("pProductType")?.addEventListener("change", applyDemoHelp);
  wireChoiceChips("pProductType", applyDemoHelp);

  // Demo: one-tap fill (optional text; screenshots preferred)
  document.getElementById("demoFillRow")?.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-demo-fill]");
    if (!btn) return;
    const kind = btn.getAttribute("data-demo-fill");
    const ta = $("pDemo");
    if (!ta) return;
    const help = window.WakeAgainDemoHelp;
    let text = "";
    if (kind === "type" && help) {
      text = help.fillText(fieldValue("pProductType") || "other");
    } else if (help && help.fills && help.fills[kind]) {
      text = help.fills[kind].text;
    }
    if (!text) return;
    if (
      ta.value.trim() &&
      !confirm(t("app.fill_example_confirm", "Replace your draft with example copy?"))
    ) {
      return;
    }
    ta.value = text;
    ta.focus();
    try {
      ta.setSelectionRange(ta.value.length, ta.value.length);
    } catch (_) {}
  });

  /** Uploaded demo screenshot public URLs (max 5). */
  let demoImageUrls = [];
  const DEMO_MIN = 1; // 최소 등록 1장 · 더 올리면 가산
  const DEMO_MAX = 5;
  const DEMO_MAX_EDGE = 1280;
  const DEMO_JPEG_Q = 0.82;

  function setDemoShotErr(msg) {
    const el = $("demoShotErr");
    if (!el) return;
    if (!msg) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = msg;
  }

  function renderDemoShots() {
    const grid = $("demoShotGrid");
    const hint = $("demoShotHint");
    if (hint) {
      hint.textContent = t("app.shots_count", "{n} shots · min {min}", {
        n: demoImageUrls.length + " / " + DEMO_MAX,
        min: DEMO_MIN,
      });
    }
    if (!grid) return;
    if (!demoImageUrls.length) {
      grid.innerHTML = "";
      return;
    }
    const base = (api.apiBase && api.apiBase()) || "";
    grid.innerHTML = demoImageUrls
      .map(function (url, i) {
        const src = url.indexOf("http") === 0 ? url : base + url;
        return (
          '<div class="demo-shot-item" data-i="' +
          i +
          '"><img src="' +
          src.replace(/"/g, "") +
          '" alt="Screenshot ' +
          (i + 1) +
          '" loading="lazy" /><button type="button" class="rm" data-rm="' +
          i +
          '" aria-label="' +
          t("app.delete", "Remove") +
          '">×</button></div>'
        );
      })
      .join("");
    grid.querySelectorAll("[data-rm]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const idx = Number(btn.getAttribute("data-rm"));
        demoImageUrls = demoImageUrls.filter(function (_, j) {
          return j !== idx;
        });
        renderDemoShots();
      });
    });
  }

  /** Resize image in browser → JPEG blob under ~1.2MB typical. */
  function resizeImageFile(file) {
    return new Promise(function (resolve, reject) {
      if (!file || !file.type || file.type.indexOf("image/") !== 0) {
        reject(new Error(t("app.img_type", "Images only.")));
        return;
      }
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = function () {
        try {
          let w = img.naturalWidth || img.width;
          let h = img.naturalHeight || img.height;
          if (!w || !h) {
            URL.revokeObjectURL(url);
            reject(new Error(t("app.img_read_fail", "Couldn’t read image.")));
            return;
          }
          const scale = Math.min(1, DEMO_MAX_EDGE / Math.max(w, h));
          w = Math.max(1, Math.round(w * scale));
          h = Math.max(1, Math.round(h * scale));
          const canvas = document.createElement("canvas");
          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(img, 0, 0, w, h);
          URL.revokeObjectURL(url);
          canvas.toBlob(
            function (blob) {
              if (!blob) {
                reject(new Error(t("app.img_convert_fail", "Image convert failed")));
                return;
              }
              resolve(blob);
            },
            "image/jpeg",
            DEMO_JPEG_Q
          );
        } catch (e) {
          URL.revokeObjectURL(url);
          reject(e);
        }
      };
      img.onerror = function () {
        URL.revokeObjectURL(url);
        reject(new Error(t("app.img_open_fail", "Couldn’t open image.")));
      };
      img.src = url;
    });
  }

  async function addDemoFiles(fileList) {
    setDemoShotErr("");
    const files = Array.from(fileList || []).filter(Boolean);
    if (!files.length) return;
    const room = DEMO_MAX - demoImageUrls.length;
    if (room <= 0) {
      setDemoShotErr(t("app.shots_max", "Up to {n} screenshots.", { n: DEMO_MAX }));
      return;
    }
    const slice = files.slice(0, room);
    for (let i = 0; i < slice.length; i++) {
      try {
        const blob = await resizeImageFile(slice[i]);
        const named = new File(
          [blob],
          "demo-" + Date.now() + "-" + i + ".jpg",
          { type: "image/jpeg" }
        );
        const res = await api.uploadDemoImage(named);
        if (res && res.url) {
          demoImageUrls.push(res.url);
          renderDemoShots();
        }
      } catch (err) {
        setDemoShotErr(err.message || t("app.upload_fail", "Upload failed"));
      }
    }
    if (files.length > room) {
      setDemoShotErr(
        t("app.shots_partial", "Max {max} · only first {n} uploaded.", {
          max: DEMO_MAX,
          n: room,
        })
      );
    }
  }

  $("btnDemoPick")?.addEventListener("click", function () {
    if (!api.getUser()) {
      setDemoShotErr(t("app.shots_need_login", "Sign in to upload screenshots."));
      setView("login");
      return;
    }
    $("pDemoImages")?.click();
  });
  $("pDemoImages")?.addEventListener("change", function (e) {
    const input = e.target;
    addDemoFiles(input.files).finally(function () {
      input.value = "";
    });
  });
  renderDemoShots();

  function normalizeKeyword(raw) {
    return String(raw || "")
      .replace(/[#，,|/]+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 24);
  }

  function renderKeywordChips() {
    const host = $("kwChips");
    const countEl = $("kwCount");
    if (host) {
      host.innerHTML = "";
      listingKeywords.forEach(function (k, idx) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "kw-chip";
        chip.setAttribute("aria-label", "remove " + k);
        chip.innerHTML = "<span></span><span class='kw-x' aria-hidden='true'>×</span>";
        chip.querySelector("span").textContent = k;
        chip.addEventListener("click", function () {
          listingKeywords.splice(idx, 1);
          renderKeywordChips();
        });
        host.appendChild(chip);
      });
    }
    if (countEl) countEl.textContent = listingKeywords.length + " / " + KW_MAX;
  }

  function addKeyword(raw) {
    const k = normalizeKeyword(raw);
    if (!k) return false;
    const key = k.toLowerCase();
    if (listingKeywords.some(function (x) {
      return x.toLowerCase() === key;
    })) {
      return false;
    }
    if (listingKeywords.length >= KW_MAX) {
      showErr($("projErr"), t("app.kw_full", "Up to 5 keywords."));
      return false;
    }
    listingKeywords.push(k);
    renderKeywordChips();
    showErr($("projErr"));
    return true;
  }

  function setKeywords(list) {
    listingKeywords = [];
    (list || []).forEach(function (k) {
      addKeyword(k);
    });
    renderKeywordChips();
  }

  function setKwMode(mode) {
    const ai = $("kwModeAi");
    const man = $("kwModeManual");
    const row = $("kwAiRow");
    if (ai) ai.classList.toggle("is-on", mode === "ai");
    if (man) man.classList.toggle("is-on", mode === "manual");
    if (row) row.hidden = mode !== "ai";
  }

  $("kwModeAi")?.addEventListener("click", function () {
    setKwMode("ai");
  });
  $("kwModeManual")?.addEventListener("click", function () {
    setKwMode("manual");
  });
  $("btnKwAdd")?.addEventListener("click", function () {
    const inp = $("pKeywordInput");
    if (!inp) return;
    if (addKeyword(inp.value)) inp.value = "";
    inp.focus();
  });
  $("pKeywordInput")?.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      const inp = $("pKeywordInput");
      if (inp && addKeyword(inp.value)) inp.value = "";
    }
  });
  $("btnKwSuggest")?.addEventListener("click", async function () {
    const title = $("pTitle") ? $("pTitle").value.trim() : "";
    const one = $("pOne") ? $("pOne").value.trim() : "";
    if (!title && !one) {
      showErr($("projErr"), t("app.kw_need_title", "Add a title or one-liner first."));
      if ($("pTitle")) $("pTitle").focus();
      return;
    }
    const btn = $("btnKwSuggest");
    if (btn) btn.disabled = true;
    showErr($("projErr"));
    try {
      const lang =
        window.WakeAgainI18n && window.WakeAgainI18n.getLang
          ? window.WakeAgainI18n.getLang()
          : "ko";
      const data = await api.suggestKeywords({
        title: title,
        one_liner: one,
        story: $("pStory") ? $("pStory").value.trim() : "",
        product_type: fieldValue("pProductType"),
        lang: lang,
      });
      setKeywords(data.keywords || []);
      const note = $("kwSourceNote");
      if (note) {
        note.hidden = false;
        note.textContent =
          data.source === "ai"
            ? t("app.kw_source_ai", "AI suggestions · edit anytime")
            : t("app.kw_source_auto", "Auto suggestions · edit anytime");
      }
    } catch (err) {
      showErr($("projErr"), err.message || t("app.load_fail", "Failed to load."));
    } finally {
      if (btn) btn.disabled = false;
    }
  });
  setKwMode("ai");
  renderKeywordChips();

  $("formMarketSearch")?.addEventListener("submit", function (e) {
    e.preventDefault();
    const inp = $("marketSearchQ");
    marketSearchQ = inp ? (inp.value || "").trim() : "";
    const clearBtn = $("btnMarketSearchClear");
    if (clearBtn) clearBtn.hidden = !marketSearchQ;
    loadProjects(true);
  });
  $("btnMarketSearchClear")?.addEventListener("click", function () {
    marketSearchQ = "";
    if ($("marketSearchQ")) $("marketSearchQ").value = "";
    const clearBtn = $("btnMarketSearchClear");
    if (clearBtn) clearBtn.hidden = true;
    loadProjects(true);
  });

  function parseFeatureLines(raw) {
    return String(raw || "")
      .split(/\r?\n/)
      .map((line) => line.replace(/^[\s·•\-\*]+/, "").trim())
      .filter((line) => line.length >= 8)
      .slice(0, 12);
  }

  function selectedAssets() {
    return Array.from(document.querySelectorAll('input[name="pAsset"]:checked')).map(
      (el) => el.value
    );
  }

  function selectedAcquisition() {
    const el = document.querySelector('input[name="pAcquisition"]:checked');
    return el ? el.value : "";
  }

  function syncAcqNote() {
    const wrap = $("pAcqNoteWrap");
    const note = $("pAcqNote");
    const acq = selectedAcquisition();
    if (!wrap) return;
    const need = acq === "resale" || acq === "other";
    wrap.hidden = !need;
    if (note) {
      note.required = need;
      if (!need) note.value = "";
    }
  }

  document.querySelectorAll('input[name="pAcquisition"]').forEach((r) => {
    r.addEventListener("change", syncAcqNote);
  });
  syncAcqNote();

  $("formProject")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("projErr"));
    if (!(await requireListReady())) return;
    const works = $("pAttestWorks");
    const featAck = $("pAttestFeatures");
    const licAck = $("pAttestLicense");
    const rights = $("pAttestRights");
    const transfer = $("pAttestTransfer");
    const licenseNote = $("pLicense") ? $("pLicense").value.trim() : "";
    const one = $("pOne") ? $("pOne").value.trim() : "";
    if (one.length < 10) {
      showErr($("projErr"), t("app.err_oneliner", "Add a short one-liner (min 10 chars · what it does)."));
      if ($("pOne")) $("pOne").focus();
      return;
    }
    const features = parseFeatureLines($("pFeatures") ? $("pFeatures").value : "");
    if (features.length < 2) {
      showErr($("projErr"), t("app.err_features", "List at least 2 “what it does” lines (8+ chars each). More lines boost ranking."));
      if ($("pFeatures")) $("pFeatures").focus();
      return;
    }
    const audience = $("pAudience") ? $("pAudience").value.trim() : "";
    if (audience.length < 4) {
      showErr($("projErr"), t("app.err_audience", "Who is this for? (e.g. founders)"));
      if ($("pAudience")) $("pAudience").focus();
      return;
    }
    const worksNow = $("pWorksNow") ? $("pWorksNow").value.trim() : "";
    if (worksNow.length < 10) {
      showErr($("projErr"), t("app.err_works", "Describe what works now (10+ chars)."));
      if ($("pWorksNow")) $("pWorksNow").focus();
      return;
    }
    const limits = $("pLimits") ? $("pLimits").value.trim() : "";
    if (limits.length < 5) {
      showErr($("projErr"), t("app.err_limits", "Describe limits (e.g. no payments yet)."));
      if ($("pLimits")) $("pLimits").focus();
      return;
    }
    const story = $("pStory") ? $("pStory").value.trim() : "";
    if (story.length < 10) {
      showErr($("projErr"), t("app.err_story", "Why are you selling? (10+ chars)"));
      if ($("pStory")) $("pStory").focus();
      return;
    }
    const demo = $("pDemo") ? $("pDemo").value.trim() : "";
    if (demoImageUrls.length < DEMO_MIN) {
      showErr(
        $("projErr"),
        t(
          "app.err_shots_min",
          "Upload at least {n} live screenshots (different screens preferred).",
          { n: DEMO_MIN }
        )
      );
      const box = document.querySelector(".demo-shot-box");
      if (box) box.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    const shotAck = $("pAttestShots");
    if (demoImageUrls.length && shotAck && !shotAck.checked) {
      showErr($("projErr"), t("app.err_shots_attest", "Confirm screenshots match the real product. Fake/mocked UI can lead to suspension."));
      if (shotAck) {
        shotAck.focus();
        shotAck.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      return;
    }
    const acquisition = selectedAcquisition();
    if (!acquisition) {
      showErr($("projErr"), t("app.err_acquisition", "Choose how you got the asset (built / resale / other)."));
      return;
    }
    const acqNote = $("pAcqNote") ? $("pAcqNote").value.trim() : "";
    if ((acquisition === "resale" || acquisition === "other") && acqNote.length < 10) {
      showErr($("projErr"), t("app.err_acquisition_note", "For resale/other, explain how you obtained it (10+ chars)."));
      if ($("pAcqNote")) $("pAcqNote").focus();
      return;
    }
    const assets = selectedAssets();
    if (!assets.length) {
      showErr($("projErr"), t("app.err_assets", "Select at least one included asset (code, design, domain…)."));
      return;
    }
    if (works && !works.checked) {
      showErr($("projErr"), t("app.err_attest_works", "Confirm you verified what works today."));
      works.focus();
      return;
    }
    if (featAck && !featAck.checked) {
      showErr($("projErr"), t("app.err_attest_features", "Confirm features / works / limits are accurate."));
      featAck.focus();
      return;
    }
    if (!licenseNote || licenseNote.length < 2) {
      showErr($("projErr"), t("app.err_license", "Add license or transfer terms (e.g. MIT)."));
      if ($("pLicense")) $("pLicense").focus();
      return;
    }
    if (licAck && !licAck.checked) {
      showErr($("projErr"), t("app.err_attest_license", "Confirm you stated license/transfer terms."));
      licAck.focus();
      return;
    }
    if (rights && !rights.checked) {
      showErr($("projErr"), t("app.err_attest_rights", "Confirm you have rights to sell."));
      rights.focus();
      return;
    }
    if (transfer && !transfer.checked) {
      showErr($("projErr"), t("app.err_attest_transfer", "Confirm you can complete the handoff."));
      transfer.focus();
      return;
    }
    const feeAck = $("pFeeAck");
    if (feeAck && !feeAck.checked) {
      showErr($("projErr"), t("app.err_fee_ack", "Accept the 10% seller fee notice before listing."));
      feeAck.focus();
      return;
    }
    const st = fieldValue("pStatus");
    const band = bandForStatus(st);
    const start = $("pPrice").value ? Number($("pPrice").value) : null;
    if (band && (start == null || start < band.min)) {
      showErr(
        $("projErr"),
        t("app.err_start_min", "{label}: minimum start is {p}.", {
          label: band.label || st,
          p: money(band.min),
        })
      );
      return;
    }
    const ptype = fieldValue("pProductType");
    if (!ptype) {
      showErr($("projErr"), t("app.err_product_type", "Pick a product type (website, app, desktop…)."));
      const chips = document.getElementById("pProductTypeChips");
      if (chips) chips.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    if (!st) {
      showErr($("projErr"), t("app.err_status", "Pick build status (“how far is it?”)."));
      const chips = document.getElementById("pStatusChips");
      if (chips) chips.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    const PRICE_MAX = 100000000;
    if (start != null && start > PRICE_MAX) {
      showErr(
        $("projErr"),
        t("app.err_start_max", "Start price max is {p}.", { p: money(PRICE_MAX) })
      );
      $("pPrice").focus();
      return;
    }
    const buyNowRaw = $("pBuyNow") && $("pBuyNow").value ? Number($("pBuyNow").value) : null;
    if (buyNowRaw != null) {
      if (buyNowRaw > PRICE_MAX) {
        showErr(
          $("projErr"),
          t("app.err_buy_max", "Buy-now max is {p}. Leave blank to skip.", { p: money(PRICE_MAX) })
        );
        if ($("pBuyNow")) $("pBuyNow").focus();
        return;
      }
      if (start != null && buyNowRaw < start) {
        showErr(
          $("projErr"),
          t("app.err_buy_vs_start", "Buy-now must be ≥ start ({p}). Leave blank to skip.", { p: money(start) })
        );
        if ($("pBuyNow")) $("pBuyNow").focus();
        return;
      }
    }
    if (!listingKeywords.length) {
      showErr($("projErr"), t("app.kw_need", "Add 1–5 search keywords."));
      if ($("pKeywordInput")) $("pKeywordInput").focus();
      return;
    }
    const payload = {
      title: $("pTitle").value.trim(),
      one_liner: one,
      status: st,
      product_type: ptype,
      features,
      audience,
      works_now: worksNow,
      limits,
      acquisition,
      acquisition_note: acqNote,
      story,
      demo: demo || (demoImageUrls.length ? t("app.demo_shots", "Screenshots ×{n}", { n: demoImageUrls.length }) : ""),
      demo_images: demoImageUrls.slice(0, DEMO_MAX),
      assets,
      keywords: listingKeywords.slice(0, KW_MAX),
      price_start: start,
      min_increment: band ? band.min_increment : 10000,
      contact: (api.getUser() && api.getUser().email) || "",
      license_note: licenseNote,
      attest_works: true,
      attest_features: true,
      attest_license: true,
      attest_rights: true,
      attest_transfer: true,
      attest_shots: !!(demoImageUrls.length && $("pAttestShots") && $("pAttestShots").checked),
      q_credits_offered: $("pQCredits")
        ? Math.max(1, Math.min(3, parseInt($("pQCredits").value || "1", 10) || 1))
        : 1,
      q_credit_unit_price: $("pQUnitPrice")
        ? Math.max(0, Math.min(100000, parseInt($("pQUnitPrice").value || "0", 10) || 0))
        : 0,
      q_credit_sla_hours: $("pQSla")
        ? parseInt($("pQSla").value || "48", 10) || 48
        : 48,
    };
    if (buyNowRaw != null && buyNowRaw > 0) {
      payload.price_buy_now = buyNowRaw;
    }
    // Extra help tickets: 0 = not sold, else min 5,000 KRW ledger units (server clamps)
    if (payload.q_credit_unit_price > 0 && payload.q_credit_unit_price < 5000) {
      showErr(
        $("projErr"),
        t("app.err_q_price", "Extra help-ticket price must be 0 (not sold) or at least {p}.",
          { p: money(5000) }
        )
      );
      if ($("pQUnitPrice")) $("pQUnitPrice").focus();
      return;
    }
    const btn = e.target.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      await api.createProject(payload);
      $("formProject").reset();
      demoImageUrls = [];
      renderDemoShots();
      setDemoShotErr("");
      listingKeywords = [];
      renderKeywordChips();
      syncAcqNote();
      const kwNote = $("kwSourceNote");
      if (kwNote) {
        kwNote.hidden = true;
        kwNote.textContent = "";
      }
      setKwMode("ai");
      applyPriceGuide(true);
      applyDemoHelp();
      feed = "mine";
      document.querySelectorAll(".seg-btn").forEach((x) => {
        x.classList.toggle("is-on", x.getAttribute("data-feed") === "mine");
      });
      alert(
        t(
          "app.create_ok",
          "Listing submitted.\n\nIt goes public after ops review (usually 1–2 days).\nCheck status under My listings."
        )
      );
      await loadProjects();
    } catch (err) {
      if (err.code === "email_unverified") {
        showDevCode();
        setView("verify");
      } else if (err.code === "profile_incomplete") {
        fillProfileForm(api.getUser());
        setView("profile");
      }
      showErr($("projErr"), err.message || t("app.create_fail", "Listing failed."));
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  async function loadSocialButtons() {
    const box = $("socialLoginBox");
    if (!box) return;
    let providers = [];
    try {
      const cfg = await api.config();
      providers = (cfg.oauth && cfg.oauth.providers) || [];
    } catch (_) {
      providers = [];
    }
    const map = {};
    providers.forEach((p) => {
      map[p.id] = p;
    });
    let any = false;
    document.querySelectorAll("#socialLoginBtns [data-provider]").forEach((a) => {
      const id = a.getAttribute("data-provider");
      if (map[id]) {
        a.hidden = false;
        a.href = api.oauthStartUrl(id);
        any = true;
      } else {
        a.hidden = true;
      }
    });
    if ($("socialLoginOff")) $("socialLoginOff").hidden = any;
    if ($("socialLoginHint")) $("socialLoginHint").hidden = !any;
  }

  function routeFromHash() {
    const h = (location.hash || "").replace(/^#/, "").toLowerCase();
    if (h === "register") return "register";
    if (h === "login" || h === "auth") return "login";
    if (h === "age") return "age";
    if (h === "verify") return "verify";
    if (h === "profile") return "profile";
    if (h === "seller" || h === "seller-identity") return "seller";
    if (h === "settlement" || h === "settle") return "settle";
    if (h === "new" || h === "create") return "create";
    if (h === "mine") return "mine";
    if (h === "fees") return "fees";
    if (h === "coupons" || h === "coupon") return "coupons";
    return "list";
  }

  async function applyRoute() {
    const route = routeFromHash();
    if (route === "fees") {
      await loadFees();
      return;
    }
    if (route === "coupons") {
      await loadCoupons();
      return;
    }
    if (route === "login") {
      setView("auth");
      switchAuthTab("login");
      return;
    }
    if (route === "register") {
      setView("auth");
      switchAuthTab("register");
      return;
    }
    if (route === "verify") {
      if (await ensureSession()) {
        showDevCode();
        setView("verify");
      } else setView("auth");
      return;
    }
    if (route === "profile") {
      if (await ensureSession()) {
        const trust = trustOf(api.getUser());
        if (!trust.email_verified) {
          showDevCode();
          setView("verify");
        } else {
          fillProfileForm(api.getUser());
          setView("profile");
        }
      } else setView("auth");
      return;
    }
    if (route === "seller") {
      if (await ensureSession()) {
        const trust = trustOf(api.getUser());
        if (!trust.email_verified) {
          showDevCode();
          setView("verify");
        } else if (!trust.profile_complete) {
          fillProfileForm(api.getUser());
          setView("profile");
        } else {
          fillSellerIdForm(api.getUser());
          setView("sellerId");
        }
      } else setView("auth");
      return;
    }
    if (route === "settle") {
      if (await ensureSession()) {
        fillProfileForm(api.getUser());
        setView("settle");
      } else setView("auth");
      return;
    }
    if (route === "create") {
      if (await requireListReady()) setView("create");
      return;
    }
    if (route === "mine") {
      feed = "mine";
      document.querySelectorAll(".seg-btn").forEach((x) => {
        x.classList.toggle("is-on", x.getAttribute("data-feed") === "mine");
      });
    }
    await loadProjects();
  }

  window.addEventListener("hashchange", () => {
    applyRoute();
  });

  if ($("formAge")) {
    if ($("ageBirth")) {
      const now = new Date();
      const yyyy = now.getFullYear();
      const mm = String(now.getMonth() + 1).padStart(2, "0");
      const dd = String(now.getDate()).padStart(2, "0");
      $("ageBirth").setAttribute("max", yyyy + "-" + mm + "-" + dd);
    }
    $("formAge")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      showErr($("ageErr"));
      const birth = $("ageBirth") ? $("ageBirth").value.trim() : "";
      const ok14 = $("ageConfirm14") && $("ageConfirm14").checked;
      if (!birth) {
        showErr($("ageErr"), t("app.reg_birth_err", "Enter your date of birth."));
        return;
      }
      if (!ok14) {
        showErr($("ageErr"), t("app.reg_age_check", "Please confirm you are 14 or older."));
        return;
      }
      try {
        await api.setBirthDate(birth, true);
        await afterAuthSuccess();
      } catch (err) {
        showErr($("ageErr"), err.message || t("app.save_fail", "Save failed"));
      }
    });
  }

  (async function boot() {
    // OAuth callback: /app/?wa_token=...&oauth=google#list
    try {
      const q = new URLSearchParams(location.search || "");
      const tok = q.get("wa_token");
      const oauthErr = q.get("oauth_error");
      if (oauthErr) {
        setView("auth");
        switchAuthTab("login");
        const msg =
          oauthErr === "denied"
            ? t("app.oauth_cancel", "Social sign-in was cancelled.")
            : oauthErr === "not_configured"
              ? t("app.oauth_off", "That social login isn’t configured yet.")
              : oauthErr === "suspended"
                ? t("app.oauth_suspended", "This account is suspended.")
                : t("app.oauth_fail", "Social sign-in failed. Please try again.");
        showErr($("loginErr"), msg);
        history.replaceState(null, "", location.pathname + (location.hash || "#login"));
      } else if (tok) {
        localStorage.setItem("wa_token", tok);
        history.replaceState(null, "", location.pathname + (location.hash || "#list"));
        try {
          await api.me();
        } catch (e) {
          localStorage.removeItem("wa_token");
          localStorage.removeItem("wa_user");
          setView("auth");
          showErr($("loginErr"), (e && e.message) || t("app.oauth_fail", "Social sign-in session failed"));
          await loadSocialButtons();
          return;
        }
        await afterAuthSuccess();
        await loadSocialButtons();
        return;
      }
    } catch (e) {
      console.warn("oauth boot", e);
    }
    try {
      await api.config();
    } catch (e) {
      console.warn("config", e);
    }
    await loadSocialButtons();
    try {
      pricingBands = await api.pricing();
      applyPriceGuide(true);
    } catch (e) {
      console.warn("pricing", e);
    }
    const sessionOk = await ensureSession();
    const u0 = api.getUser();
    if (sessionOk && u0 && (u0.needs_age_gate || !u0.birth_date)) {
      setView("age");
      return;
    }

    // App / PWA launch: land on login when signed out; if session exists, open marketplace
    if (isAppLaunch()) {
      if (!sessionOk) {
        history.replaceState(null, "", location.pathname + location.search + "#login");
        setView("auth");
        switchAuthTab("login");
        fillSavedLoginForm();
        return;
      }
      // signed in: avoid stuck on #login from start_url
      const h0 = (location.hash || "").replace(/^#/, "").toLowerCase();
      if (!h0 || h0 === "login" || h0 === "auth") {
        history.replaceState(null, "", location.pathname + location.search + "#list");
      }
    } else {
      fillSavedLoginForm();
    }

    await applyRoute();
  })();

  document.addEventListener("wa:langchange", function () {
    try {
      if (window.WakeAgainI18n) window.WakeAgainI18n.apply(document);
    } catch (e) {}
    try {
      syncChrome();
    } catch (e) {}
    try {
      syncBirthDateInputs();
    } catch (e) {}
    try {
      applyPriceGuide(false);
    } catch (e) {}
    try {
      // Always re-render market cards (EN title/one-liner/keywords + labels)
      loadProjects(true);
    } catch (e) {}
  });
  document.addEventListener("wa:currencychange", function () {
    try {
      if (window.WakeAgainI18n) window.WakeAgainI18n.apply(document);
    } catch (e) {}
    try {
      loadProjects(true);
    } catch (e) {}
  });
})();
