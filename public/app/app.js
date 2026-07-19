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
    return "₩" + Number(n).toLocaleString("ko-KR");
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
  };
  let listOffset = 0;
  const PAGE = 24;
  const tabbar = $("tabbar");
  let feed = "all";
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
    const showTab =
      name === "list" ||
      name === "create" ||
      name === "profile" ||
      name === "sellerId" ||
      name === "settle" ||
      name === "notif" ||
      name === "fees";
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
      b.classList.toggle("is-on", on);
    });
    const hashMap = {
      auth: "#login",
      verify: "#verify",
      profile: "#profile",
      sellerId: "#seller",
      settle: "#settlement",
      list: "#list",
      create: "#new",
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
    history.replaceState(null, "", tab === "register" ? "#register" : "#login");
  }

  function trustOf(user) {
    return (user && user.trust) || api.trust() || {};
  }

  function trustBadgeCopy(level) {
    // Positive “done” language — avoid “확인” sounding like pending/risk
    // Display as Lv0…Lv3 (not L0…L3)
    const map = {
      0: t("app.lv0", "Lv0 · 가입"),
      1: t("app.lv1", "Lv1 · 이메일 완료"),
      2: t("app.lv2", "Lv2 · 인증 완료"),
      3: t("app.lv3", "Lv3 · 거래 준비 완료"),
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
    if (loggedIn && u) {
      const name = u.display_name || u.real_name || (u.email && u.email.split("@")[0]) || "회원";
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
      const t = trustOf(u);
      const c = u.credit || {};
      const level = t.level != null ? Number(t.level) : 0;
      if (badge) {
        badge.hidden = false;
        badge.className = "trust-badge trust-badge--l" + Math.min(3, Math.max(0, level));
        // Keep credit separate in wording so L2 doesn't look like a score warning
        let text = trustBadgeCopy(level);
        if (c.score != null) {
          text += " · 신용 " + c.score;
          if (c.label) text += " " + c.label;
        }
        badge.textContent = text;
        badge.title =
          "신뢰 레벨(자격) Lv" +
          level +
          (t.label ? " · " + t.label : "") +
          (c.score != null ? " / 사이트 내 신용 점수 " + c.score + (c.label ? " " + c.label : "") : "") +
          " · 자세한 산식은 사이트 내 신용 점수 안내";
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
            location.href = n.link;
          });
        }
        list.appendChild(el);
      });
    } catch (e) {
      empty.hidden = false;
      empty.textContent = e.message || t("app.notif_fail", "알림을 불러오지 못했습니다.");
    }
  }

  function showDevCode() {
    const box = $("devCodeBox");
    const text = $("devCodeText");
    const code = api.getDevCode();
    if (code && box && text) {
      box.hidden = false;
      text.textContent = code;
      $("verifyCode").value = code;
    } else if (box) {
      box.hidden = true;
    }
  }

  function fillProfileForm(u) {
    if (!u) return;
    $("profReal").value = u.real_name || "";
    $("profPhone").value = u.phone || "";
    $("profRole").value = u.role || "both";
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
      if ($("creditScoreNum")) $("creditScoreNum").textContent = (c.score != null ? c.score : "—") + "점";
      if ($("creditGradeLabel")) $("creditGradeLabel").textContent = c.label ? "· " + c.label : "";
      const cnt = c.counts || {};
      if ($("creditCounts")) {
        $("creditCounts").textContent =
          "성사(판매) " +
          (cnt.sold_as_seller || 0) +
          " · 성사(구매) " +
          (cnt.bought_complete || 0) +
          " · 미입금 " +
          (cnt.defaults || 0);
      }
      const b = c.breakdown;
      if ($("creditBreak") && b) {
        $("creditBreak").textContent =
          "가감 합: 기본 " +
          (b.base || 30) +
          " · Lv2 +" +
          (b.l2_identity || 0) +
          " · Lv3 +" +
          (b.l3_settlement || 0) +
          " · 성사 +" +
          ((b.sold_as_seller || 0) + (b.bought_complete || 0)) +
          " · 정시 +" +
          (b.on_time_payment || 0) +
          " · 미입금 " +
          (b.defaults || 0);
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
          t("app.need_login_list", "로그인하면 매물 등록·내 매물이 가능합니다. 등록 전 이메일 인증과 실명·휴대폰 확인이 필요합니다.");
      }
      if (banner) banner.hidden = true;
      return;
    }
    if (gate) gate.hidden = true;
    const t = trustOf(u);
    if (!banner) return;
    if (t.can_list && t.deal_ready) {
      banner.hidden = false;
      banner.className = "trust-banner is-ok";
      banner.innerHTML = t("app.banner_l3", "신뢰 Lv3 · 거래 준비 완료. 성사 단계에서 정산 계좌를 사용합니다.");
    } else if (t.can_list) {
      banner.hidden = false;
      banner.className = "trust-banner";
      banner.innerHTML =
        "신원·판매자 공개 정보 완료. 성사 전 <button type='button' class='text-link' id='bannerSettle'>정산 계좌(Lv3)</button>를 등록해 주세요.";
      setTimeout(() => {
        $("bannerSettle")?.addEventListener("click", () => setView("settle"));
      }, 0);
    } else if (!t.email_verified) {
      banner.hidden = false;
      banner.className = "trust-banner is-warn";
      banner.innerHTML =
        "이메일 미인증 · 매물 등록 불가. <button type='button' class='text-link' id='bannerVerify'>지금 인증</button>";
      setTimeout(() => {
        $("bannerVerify")?.addEventListener("click", () => {
          showDevCode();
          setView("verify");
        });
      }, 0);
    } else if (!t.profile_complete) {
      banner.hidden = false;
      banner.className = "trust-banner is-warn";
      banner.innerHTML =
        "실명·휴대폰 미입력 · 매물 등록 불가. <button type='button' class='text-link' id='bannerProf'>프로필 완성</button>";
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
        "판매자 공개 정보 미등록 · 매물 등록 불가. <button type='button' class='text-link' id='bannerSeller'>판매자 정보 등록</button>";
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
      $("sidNameLabel").textContent = biz ? "상호 *" : "공개 성명 *";
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
          t("app.need_gates", "매물 등록에는 로그인 · 이메일 인증 · 실명·휴대폰 · 판매자 공개 정보가 필요합니다.");
      }
      return false;
    }
    const u = api.getUser();
    const t = trustOf(u);
    if (!t.email_verified) {
      pendingAfterAuth = "create";
      showDevCode();
      setView("verify");
      return false;
    }
    if (!t.profile_complete) {
      pendingAfterAuth = "create";
      fillProfileForm(u);
      setView("profile");
      return false;
    }
    if (!t.seller_identity_complete) {
      pendingAfterAuth = "create";
      fillSellerIdForm(u);
      setView("sellerId");
      return false;
    }
    if (!t.can_list) {
      pendingAfterAuth = "create";
      fillProfileForm(u);
      setView("profile");
      return false;
    }
    return true;
  }

  async function afterAuthSuccess() {
    const u = api.getUser();
    const t = trustOf(u);
    const next = pendingAfterAuth;
    pendingAfterAuth = null;
    const note = $("authNeedNote");
    if (note) note.hidden = true;

    // SNS login: birth date (만 14세) still required once
    if (u && (u.needs_age_gate || !u.birth_date)) {
      setView("age");
      return;
    }

    if (!t.email_verified) {
      showDevCode();
      setView("verify");
      return;
    }
    if (next === "create" && !t.profile_complete) {
      fillProfileForm(u);
      setView("profile");
      return;
    }
    if (next === "create" && !t.seller_identity_complete) {
      fillSellerIdForm(u);
      setView("sellerId");
      return;
    }
    if (next === "create" && t.can_list) {
      setView("create");
      return;
    }
    if (next === "profile") {
      fillProfileForm(u);
      setView("profile");
      return;
    }
    if (next === "seller") {
      fillSellerIdForm(u);
      setView("sellerId");
      return;
    }
    await loadProjects();
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
      el.querySelector("h3").textContent = p.title || "—";
      el.querySelector(".p-one").textContent = p.one_liner || "";
      const cur = p.price_current != null ? p.price_current : p.price_start;
      const bids = p.bid_count || 0;
      const typeBit = p.product_type_label || "";
      const ls = p.listing_status || "";
      const aStatus = p.auction_status || "live";

      const badge = el.querySelector(".p-card-badge");
      let badgeText = "LIVE";
      let badgeCls = "";
      if (ls === "pending") {
        badgeText = t("app.badge_pending", "검토중");
        badgeCls = "is-wait";
      } else if (ls === "hold") {
        badgeText = t("app.badge_hold", "보류");
        badgeCls = "is-wait";
      } else if (ls === "rejected") {
        badgeText = t("app.badge_rejected", "반려");
        badgeCls = "is-bad";
      } else if (aStatus === "sold") {
        badgeText = t("app.badge_sold", "성사");
        badgeCls = "is-sold";
      } else if (aStatus === "ended") {
        badgeText = t("app.badge_ended", "종료");
        badgeCls = "is-wait";
      } else if (bids > 0) {
        badgeText = t("app.badge_live", "입찰 중");
      } else if (ls === "approved") {
        badgeText = t("app.badge_open", "공개");
      }
      badge.textContent = badgeText;
      if (badgeCls) badge.classList.add(badgeCls);

      const priceLabel = el.querySelector(".p-card-price span");
      const priceVal = el.querySelector(".p-card-price strong");
      if (aStatus === "sold") {
        priceLabel.textContent = t("app.price_sold", "팔린 가격");
        priceVal.textContent =
          cur != null || p.sold_price != null
            ? "₩" + Number(p.sold_price != null ? p.sold_price : cur).toLocaleString("ko-KR")
            : "—";
      } else {
        priceLabel.textContent = bids > 0 ? t("app.price_now", "지금 가격") : t("app.price_start", "시작 가격");
        priceVal.textContent =
          cur != null ? "₩" + Number(cur).toLocaleString("ko-KR") : "—";
      }

      el.querySelector(".p-meta").textContent = [
        typeBit,
        p.status_label || p.status || "",
        bids > 0 ? t("app.bids_n", "가격 {n}번 씀", { n: bids }) : t("app.bids_none", "아직 가격 없음"),
      ]
        .filter(Boolean)
        .join(" · ");

      let liveText = t("app.live_wait", "첫 입찰 대기");
      if (ls === "pending") liveText = t("app.live_pending", "검토 중 · 아직 비공개");
      else if (ls === "hold") liveText = t("app.live_hold", "잠깐 보류");
      else if (ls === "rejected") liveText = t("app.live_reject", "다시 고쳐 주세요");
      else if (aStatus === "sold") liveText = t("app.live_sold", "팔렸어요");
      else if (aStatus === "ended") liveText = t("app.live_ended", "끝났어요");
      else if (ls === "approved") liveText = bids > 0 ? t("app.badge_live", "입찰 중") : t("app.live_wait", "첫 입찰 대기");
      el.querySelector(".p-live").textContent = liveText;

      el.addEventListener("click", () => {
        location.href = "/project.html?id=" + encodeURIComponent(p.id);
      });
      list.appendChild(el);
    });
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
      const data = await api.listProjects(feed === "mine", PAGE, listOffset);
      const projects = data.projects || [];
      if (listOffset === 0) {
        empty.hidden = projects.length > 0;
        empty.textContent =
          feed === "mine"
            ? t("app.empty_mine", "아직 올린 프로젝트가 없습니다.")
            : t("app.empty_all", "아직 공개 매물이 없습니다. 첫 프로젝트를 올려 보세요.");
      }
      appendProjectCards(projects);
      listOffset += projects.length;
      if (more) more.hidden = !data.has_more;
    } catch (e) {
      empty.hidden = false;
      empty.textContent = e.message || t("app.load_fail", "불러오기에 실패했습니다.");
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
          t("app.fees_empty", "아직 수수료 청구 내역이 없습니다. 매물이 성사되면 여기에 표시됩니다.");
      }
      inv.forEach((f) => {
        const el = document.createElement("article");
        el.className = "p-card";
        el.style.minHeight = "auto";
        el.innerHTML =
          "<div class='p-card-top'><h3></h3><span class='p-card-badge'></span></div>" +
          "<div class='p-card-foot'><p class='p-card-price'><span>수수료 10%</span><strong></strong></p>" +
          "<p class='p-meta'></p><p class='p-live'></p></div>";
        el.querySelector("h3").textContent = f.project_title || "매물 #" + f.project_id;
        el.querySelector(".p-card-badge").textContent =
          f.status === "paid" ? t("app.fee_paid", "확인됨") : t("app.fee_wait", "대기");
        if (f.status === "paid") el.querySelector(".p-card-badge").classList.add("is-sold");
        else el.querySelector(".p-card-badge").classList.add("is-wait");
        el.querySelector(".p-card-price strong").textContent =
          "₩" + Number(f.fee_amount).toLocaleString("ko-KR");
        el.querySelector(".p-meta").textContent =
          "거래 ₩" + Number(f.deal_amount).toLocaleString("ko-KR");
        el.querySelector(".p-live").textContent =
          f.status === "paid"
            ? t("app.fee_paid_note", "입금 확인됨 (운영자)")
            : t("app.fee_wait_note", "입금 대기 · 운영자 확인") + " · corelabs.studio@gmail.com";
        list.appendChild(el);
      });
    } catch (e) {
      empty.hidden = false;
      empty.textContent = e.message || "불러오기 실패";
    }
  }

  // --- events ---
  document.querySelectorAll(".auth-tabs .tab").forEach((btn) => {
    btn.addEventListener("click", () => switchAuthTab(btn.getAttribute("data-tab") || "login"));
  });

  // 가입: 생년월일 max = 오늘, 힌트용 min 나이 경계는 서버가 최종 판단
  if ($("regBirth")) {
    const t = new Date();
    const yyyy = t.getFullYear();
    const mm = String(t.getMonth() + 1).padStart(2, "0");
    const dd = String(t.getDate()).padStart(2, "0");
    $("regBirth").setAttribute("max", yyyy + "-" + mm + "-" + dd);
  }

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
      btn.setAttribute("aria-label", show ? t("app.pw_hide", "비밀번호 숨기기") : t("app.pw_show", "비밀번호 보기"));
      btn.title = show ? t("app.pw_hide", "비밀번호 숨기기") : t("app.pw_show", "비밀번호 보기");
    });
  });

  $("formLogin").addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("loginErr"));
    const btn = e.target.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      await api.login($("loginEmail").value.trim(), $("loginPass").value);
      await afterAuthSuccess();
    } catch (err) {
      showErr($("loginErr"), err.message || t("app.login_fail", "로그인에 실패했습니다."));
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  $("btnShowReset")?.addEventListener("click", () => {
    $("formLogin").hidden = true;
    $("formRegister").hidden = true;
    $("formReset").hidden = false;
    $("resetEmail").value = $("loginEmail").value || "";
  });
  $("btnResetBack")?.addEventListener("click", () => {
    $("formReset").hidden = true;
    $("formLogin").hidden = false;
  });
  $("btnResetReq")?.addEventListener("click", async () => {
    showErr($("resetErr"));
    try {
      const data = await api.passwordResetRequest($("resetEmail").value.trim());
      if (data.dev_email_code) {
        $("resetDevBox").hidden = false;
        $("resetDevCode").textContent = data.dev_email_code;
        $("resetCode").value = data.dev_email_code;
      }
      showErr($("resetErr"), t("app.reset_sent", "코드를 발급했습니다.") + (data.dev_email_code ? " (개발 모드)" : ""));
    } catch (err) {
      showErr($("resetErr"), err.message || "실패");
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
      showErr($("resetErr"), t("app.reset_ok", "변경 완료. 로그인해 주세요."));
      $("formReset").hidden = true;
      $("formLogin").hidden = false;
    } catch (err) {
      showErr($("resetErr"), err.message || "실패");
    }
  });
  $("btnNotif")?.addEventListener("click", () => loadNotifications());
  $("btnBackNotif")?.addEventListener("click", () => loadProjects(true));
  $("btnFees")?.addEventListener("click", () => loadFees());
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

  $("formRegister").addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("regErr"));
    const terms = $("regTerms");
    if (terms && !terms.checked) {
      showErr($("regErr"), t("app.reg_terms_err", "이용약관 및 개인정보처리방침에 동의해 주세요."));
      return;
    }
    const pass = $("regPass") ? $("regPass").value : "";
    const pass2 = $("regPass2") ? $("regPass2").value : "";
    const birth = $("regBirth") ? $("regBirth").value.trim() : "";
    const ageOk = $("regAge14") ? $("regAge14").checked : false;
    if (!birth) {
      showErr($("regErr"), t("app.reg_birth_err", "생년월일을 입력해 주세요."));
      if ($("regBirth")) $("regBirth").focus();
      return;
    }
    // Client-side 만 나이 (서버가 최종 판단)
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
        showErr($("regErr"), t("app.reg_under14", "만 14세 미만은 WakeAgain에 가입할 수 없습니다."));
        return;
      }
    } catch (_) {
      showErr($("regErr"), t("app.reg_birth_bad", "생년월일을 다시 확인해 주세요."));
      return;
    }
    if (!ageOk) {
      showErr($("regErr"), t("app.reg_age_check", "만 14세 이상임을 확인해 주세요."));
      return;
    }
    if (pass.length < 8) {
      showErr($("regErr"), t("app.reg_pass_len", "비밀번호는 8자 이상이어야 합니다."));
      return;
    }
    if (pass !== pass2) {
      showErr($("regErr"), t("app.reg_pass_match", "비밀번호가 서로 다릅니다. 다시 입력해 주세요."));
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
        true
      );
      pendingAfterAuth = pendingAfterAuth || "create";
      await afterAuthSuccess();
    } catch (err) {
      showErr($("regErr"), err.message || t("app.reg_fail", "가입에 실패했습니다."));
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  $("formVerify").addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("verifyErr"));
    try {
      await api.verifyEmail($("verifyCode").value.trim());
      const u = api.getUser();
      const t = trustOf(u);
      if (!t.profile_complete) {
        fillProfileForm(u);
        setView("profile");
      } else if (!t.seller_identity_complete) {
        fillSellerIdForm(u);
        setView("sellerId");
      } else {
        await afterAuthSuccess();
      }
    } catch (err) {
      showErr($("verifyErr"), err.message || t("app.verify_fail", "인증 실패"));
    }
  });

  $("btnResendCode").addEventListener("click", async () => {
    showErr($("verifyErr"));
    try {
      await api.resendVerify();
      showDevCode();
      showErr($("verifyErr"), t("app.verify_resent", "새 코드를 발급했습니다.") + (api.getDevCode() ? " (개발 모드 코드 표시)" : ""));
    } catch (err) {
      showErr($("verifyErr"), err.message || "재발송 실패");
    }
  });

  $("formProfile").addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("profErr"));
    try {
      await api.updateProfile({
        real_name: $("profReal").value.trim(),
        phone: $("profPhone").value.trim(),
        role: $("profRole").value,
        display_name: $("profDisplay").value.trim(),
      });
      const u = api.getUser();
      const t = trustOf(u);
      if (pendingAfterAuth === "create") {
        if (!t.seller_identity_complete) {
          fillSellerIdForm(u);
          setView("sellerId");
        } else {
          pendingAfterAuth = null;
          setView("create");
        }
      } else if (!t.seller_identity_complete && (u.role === "seller" || u.role === "both")) {
        fillSellerIdForm(u);
        setView("sellerId");
      } else {
        await loadProjects();
      }
    } catch (err) {
      if (err.code === "email_unverified") {
        showDevCode();
        setView("verify");
      }
      showErr($("profErr"), err.message || t("app.save_fail", "저장 실패"));
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
      showErr($("sidErr"), err.message || t("app.save_fail", "저장 실패"));
    }
  });

  $("formSettle").addEventListener("submit", async (e) => {
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
      showErr($("setErr"), err.message || t("app.save_fail", "저장 실패"));
    }
  });

  $("btnLogout").addEventListener("click", () => {
    api.clearSession();
    feed = "all";
    document.querySelectorAll(".seg-btn").forEach((x) => {
      x.classList.toggle("is-on", x.getAttribute("data-feed") === "all");
    });
    setView("auth");
    switchAuthTab("login");
    syncChrome();
  });

  $("btnGoLogin").addEventListener("click", () => {
    pendingAfterAuth = "list";
    setView("auth");
    switchAuthTab("login");
  });

  async function openProfile() {
    if (!(await ensureSession())) {
      setView("auth");
      return;
    }
    const u = api.getUser();
    const t = trustOf(u);
    if (!t.email_verified) {
      showDevCode();
      setView("verify");
      return;
    }
    fillProfileForm(u);
    setView("profile");
  }
  $("btnProfile").addEventListener("click", () => openProfile());
  $("userChip")?.addEventListener("click", () => openProfile());

  $("btnBackFromProfile").addEventListener("click", () => loadProjects());
  $("btnGoSettle")?.addEventListener("click", () => {
    fillProfileForm(api.getUser());
    setView("settle");
  });
  $("btnBackFromSettle").addEventListener("click", () => {
    fillProfileForm(api.getUser());
    setView("profile");
  });

  $("btnRefresh").addEventListener("click", () => loadProjects());
  $("btnNew").addEventListener("click", async () => {
    if (await requireListReady()) setView("create");
  });
  $("btnBackList").addEventListener("click", () => loadProjects());

  document.querySelectorAll(".seg-btn").forEach((b) => {
    b.addEventListener("click", () => {
      document.querySelectorAll(".seg-btn").forEach((x) => x.classList.remove("is-on"));
      b.classList.add("is-on");
      feed = b.getAttribute("data-feed") || "all";
      loadProjects(true);
    });
  });

  document.querySelectorAll(".tabbar-item[data-go]").forEach((b) => {
    b.addEventListener("click", async () => {
      const go = b.getAttribute("data-go");
      if (go === "new") {
        if (await requireListReady()) setView("create");
      } else if (go === "profile") {
        $("btnProfile").click();
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
      (yes ? "<div class='sc-label'>이럴 때 선택</div><ul>" + yes + "</ul>" : "") +
      (no ? "<div class='sc-label'>아닐 때</div><ul>" + no + "</ul>" : "") +
      (band.demo_expect
        ? "<div class='sc-label'>데모</div><p class='sc-when' style='margin:0'>" +
          band.demo_expect +
          "</p>"
        : "");
  }

  function applyPriceGuide(forceSuggest) {
    const st = $("pStatus") && $("pStatus").value;
    const band = bandForStatus(st);
    const guide = $("pPriceGuide");
    const hint = $("pPriceHint");
    const price = $("pPrice");
    const criteria = $("pStatusCriteria");
    if (!band) {
      if (guide) guide.textContent = "상태에 따라 시작 입찰가 구간이 달라집니다.";
      if (criteria) criteria.hidden = true;
      return;
    }
    renderCriteria(criteria, band);
    if (guide) {
      guide.innerHTML =
        "<strong>" +
        (band.label || band.status) +
        "</strong> — " +
        band.blurb +
        "<br/>권장 <strong>₩" +
        Number(band.suggest).toLocaleString("ko-KR") +
        "</strong> · 최저 ₩" +
        Number(band.min).toLocaleString("ko-KR") +
        " · 호가 단위 ₩" +
        Number(band.min_increment).toLocaleString("ko-KR");
    }
    if (hint) {
      hint.textContent =
        (band.examples || "") +
        " · 권장 상단 약 ₩" +
        Number(band.max_soft).toLocaleString("ko-KR") +
        " (초과 시 경고만)";
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

  function applyDemoHelp() {
    const key = $("pProductType") ? $("pProductType").value : "";
    const help = window.WakeAgainDemoHelp;
    if (!help) return;
    // Show under product type and reinforce near demo field
    help.applyTo($("pDemoHelp"), null, key || null);
    help.applyTo($("pDemoHelpBelow"), $("pDemo"), key || null);
  }
  $("pProductType")?.addEventListener("change", applyDemoHelp);

  $("formProject").addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr($("projErr"));
    if (!(await requireListReady())) return;
    const works = $("pAttestWorks");
    const licAck = $("pAttestLicense");
    const rights = $("pAttestRights");
    const licenseNote = $("pLicense") ? $("pLicense").value.trim() : "";
    if (works && !works.checked) {
      showErr($("projErr"), "「최소한 돌아가는지 직접 확인」에 체크해 주세요.");
      works.focus();
      return;
    }
    if (!licenseNote || licenseNote.length < 2) {
      showErr($("projErr"), "라이선스 또는 양도 조건을 적어 주세요. (예: MIT)");
      if ($("pLicense")) $("pLicense").focus();
      return;
    }
    if (licAck && !licAck.checked) {
      showErr($("projErr"), "「라이선스·양도 조건을 기재했다」에 체크해 주세요.");
      licAck.focus();
      return;
    }
    if (rights && !rights.checked) {
      showErr($("projErr"), "「팔 권한이 있는 자산」에 체크해 주세요.");
      rights.focus();
      return;
    }
    const feeAck = $("pFeeAck");
    if (feeAck && !feeAck.checked) {
      showErr($("projErr"), "등록 전 판매자 수수료 10% 고지에 동의해 주세요.");
      feeAck.focus();
      return;
    }
    const st = $("pStatus").value;
    const band = bandForStatus(st);
    const start = $("pPrice").value ? Number($("pPrice").value) : null;
    if (band && (start == null || start < band.min)) {
      showErr(
        $("projErr"),
        (band.label || st) +
          " 최저 시작가는 ₩" +
          Number(band.min).toLocaleString("ko-KR") +
          " 입니다."
      );
      return;
    }
    const ptype = $("pProductType") ? $("pProductType").value : "";
    if (!ptype) {
      showErr($("projErr"), "제품 형태(웹사이트·앱·데스크톱 등)를 선택해 주세요.");
      if ($("pProductType")) $("pProductType").focus();
      return;
    }
    const PRICE_MAX = 100000000;
    if (start != null && start > PRICE_MAX) {
      showErr($("projErr"), "시작가는 최대 ₩100,000,000 까지입니다.");
      $("pPrice").focus();
      return;
    }
    const buyNowRaw = $("pBuyNow") && $("pBuyNow").value ? Number($("pBuyNow").value) : null;
    if (buyNowRaw != null) {
      if (buyNowRaw > PRICE_MAX) {
        showErr($("projErr"), "즉시구매가는 최대 ₩100,000,000 까지입니다. 쓰지 않으려면 비워 두세요.");
        if ($("pBuyNow")) $("pBuyNow").focus();
        return;
      }
      if (start != null && buyNowRaw < start) {
        showErr(
          $("projErr"),
          "즉시구매가는 시작가(₩" + Number(start).toLocaleString("ko-KR") + ") 이상이어야 합니다. 쓰지 않으려면 비워 두세요."
        );
        if ($("pBuyNow")) $("pBuyNow").focus();
        return;
      }
    }
    const payload = {
      title: $("pTitle").value.trim(),
      one_liner: $("pOne").value.trim(),
      status: st,
      product_type: ptype,
      story: $("pStory").value.trim(),
      demo: $("pDemo").value.trim(),
      assets: ["code"],
      price_start: start,
      min_increment: band ? band.min_increment : 10000,
      contact: (api.getUser() && api.getUser().email) || "",
      license_note: licenseNote,
      attest_works: true,
      attest_license: true,
      attest_rights: true,
    };
    if (buyNowRaw != null && buyNowRaw > 0) {
      payload.price_buy_now = buyNowRaw;
    }
    const btn = e.target.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      await api.createProject(payload);
      $("formProject").reset();
      applyPriceGuide(true);
      applyDemoHelp();
      feed = "mine";
      document.querySelectorAll(".seg-btn").forEach((x) => {
        x.classList.toggle("is-on", x.getAttribute("data-feed") === "mine");
      });
      alert(
        "올리기 요청이 접수되었어요.\n\n" +
          "운영자가 확인한 뒤에 모두가 볼 수 있게 올라갑니다.\n" +
          "보통 1~2일 안에 결과가 나와요.\n" +
          "「내가 올린 것」에서 상태를 확인할 수 있어요."
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
      showErr($("projErr"), err.message || "등록에 실패했습니다.");
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
    return "list";
  }

  async function applyRoute() {
    const route = routeFromHash();
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
        const t = trustOf(api.getUser());
        if (!t.email_verified) {
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
        const t = trustOf(api.getUser());
        if (!t.email_verified) {
          showDevCode();
          setView("verify");
        } else if (!t.profile_complete) {
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
      const t = new Date();
      const yyyy = t.getFullYear();
      const mm = String(t.getMonth() + 1).padStart(2, "0");
      const dd = String(t.getDate()).padStart(2, "0");
      $("ageBirth").setAttribute("max", yyyy + "-" + mm + "-" + dd);
    }
    $("formAge").addEventListener("submit", async (e) => {
      e.preventDefault();
      showErr($("ageErr"));
      const birth = $("ageBirth") ? $("ageBirth").value.trim() : "";
      const ok14 = $("ageConfirm14") && $("ageConfirm14").checked;
      if (!birth) {
        showErr($("ageErr"), t("app.reg_birth_err", "생년월일을 입력해 주세요."));
        return;
      }
      if (!ok14) {
        showErr($("ageErr"), t("app.reg_age_check", "만 14세 이상임을 확인해 주세요."));
        return;
      }
      try {
        await api.setBirthDate(birth, true);
        await afterAuthSuccess();
      } catch (err) {
        showErr($("ageErr"), err.message || t("app.save_fail", "저장 실패"));
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
            ? "소셜 로그인이 취소되었습니다."
            : oauthErr === "not_configured"
              ? "해당 SNS 로그인이 아직 설정되지 않았습니다."
              : oauthErr === "suspended"
                ? "정지된 계정입니다."
                : "소셜 로그인에 실패했습니다. 다시 시도해 주세요.";
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
          showErr($("loginErr"), (e && e.message) || "소셜 로그인 세션 실패");
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
    await ensureSession();
    const u0 = api.getUser();
    if (api.isLoggedIn() && u0 && (u0.needs_age_gate || !u0.birth_date)) {
      setView("age");
      return;
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
  });
  document.addEventListener("wa:currencychange", function () {
    try {
      if (window.WakeAgainI18n) window.WakeAgainI18n.apply(document);
    } catch (e) {}
  });
})();
