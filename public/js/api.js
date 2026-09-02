/**
 * WakeAgain shared client — used by website and Capacitor (Play / App Store).
 * Same token, same API, all channels.
 */
(function (global) {
  const STORAGE_TOKEN = "wa_token";
  const STORAGE_USER = "wa_user";
  const STORAGE_API = "wa_api_base";
  const STORAGE_DEV_CODE = "wa_dev_email_code";
  /** Device-local saved email/password for "remember login" (not the session token). */
  const STORAGE_SAVED_LOGIN = "wa_saved_login";

  function isNativeShell() {
    try {
      if (global.WAKEAGAIN_CHANNEL === "native") return true;
      if (
        location.protocol === "capacitor:" ||
        location.protocol === "ionic:" ||
        location.protocol === "file:"
      ) {
        return true;
      }
      if (
        global.Capacitor &&
        global.Capacitor.isNativePlatform &&
        global.Capacitor.isNativePlatform()
      ) {
        return true;
      }
    } catch (e) {
      /* ignore */
    }
    return false;
  }

  /**
   * Site path that works on web and Capacitor (app shell lives under /app/).
   * Pass root-style paths: "/project.html?id=1", "/#listings", "/app/#list"
   */
  function pageUrl(path) {
    var raw = String(path == null ? "/" : path);
    if (!raw) raw = "/";
    if (/^(https?:|mailto:|tel:)/i.test(raw)) return raw;
    if (raw.charAt(0) === "#") {
      // hash-only: stay on current document when possible
      return raw;
    }
    var hash = "";
    var query = "";
    var pathOnly = raw;
    var hi = pathOnly.indexOf("#");
    if (hi >= 0) {
      hash = pathOnly.slice(hi);
      pathOnly = pathOnly.slice(0, hi);
    }
    var qi = pathOnly.indexOf("?");
    if (qi >= 0) {
      query = pathOnly.slice(qi);
      pathOnly = pathOnly.slice(0, qi);
    }
    if (!pathOnly || pathOnly === "") pathOnly = "/";
    if (pathOnly.charAt(0) !== "/") pathOnly = "/" + pathOnly;

    // Normal website or Capacitor https://localhost — root-relative is correct
    if (location.protocol === "http:" || location.protocol === "https:") {
      return pathOnly + query + hash;
    }

    // file:// / capacitor: legacy — resolve relative to current folder depth
    var parts = (location.pathname || "").split("/").filter(function (x) {
      return x && x !== "." ;
    });
    // drop filename
    if (parts.length && /\.(html?|htm)$/i.test(parts[parts.length - 1])) {
      parts.pop();
    }
    var inApp = parts.length > 0 && parts[parts.length - 1].toLowerCase() === "app";
    var target = pathOnly.replace(/^\//, "");
    if (pathOnly === "/") target = "index.html";
    if (inApp) {
      return "../" + target + query + hash;
    }
    return target + query + hash;
  }

  function goPage(path) {
    location.href = pageUrl(path);
  }

  function apiBase() {
    const saved = localStorage.getItem(STORAGE_API);
    if (saved) return saved.replace(/\/$/, "");
    if (global.WAKEAGAIN_API_BASE) return String(global.WAKEAGAIN_API_BASE).replace(/\/$/, "");
    // Capacitor / file: must not use empty base (relative fetch breaks)
    if (isNativeShell()) {
      return "http://10.0.2.2:8080";
    }
    return "";
  }

  function token() {
    return localStorage.getItem(STORAGE_TOKEN) || "";
  }

  function setSession(tok, user) {
    if (tok) localStorage.setItem(STORAGE_TOKEN, tok);
    else localStorage.removeItem(STORAGE_TOKEN);
    if (user) localStorage.setItem(STORAGE_USER, JSON.stringify(user));
    else localStorage.removeItem(STORAGE_USER);
  }

  function getUser() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_USER) || "null");
    } catch {
      return null;
    }
  }

  function setDevCode(code) {
    if (code) localStorage.setItem(STORAGE_DEV_CODE, String(code));
    else localStorage.removeItem(STORAGE_DEV_CODE);
  }

  function getDevCode() {
    return localStorage.getItem(STORAGE_DEV_CODE) || "";
  }

  function isEn() {
    try {
      if (global.WakeAgainI18n && global.WakeAgainI18n.getLang) {
        return global.WakeAgainI18n.getLang() === "en";
      }
    } catch (e) {}
    try {
      var saved = localStorage.getItem("wa_lang");
      if (saved === "en") return true;
      if (saved === "ko") return false;
    } catch (e2) {}
    return true;
  }

  // Backend validation/status text is authored in Korean only. This table
  // translates it for display when the UI is in English, so overseas
  // visitors never see raw Korean copy leak through error/info toasts.
  var BACKEND_MSG_EN = {
    "이메일 인증 후 매물을 등록할 수 있습니다.": "Verify your email before listing a project.",
    "실명·휴대폰 프로필을 완성한 뒤 매물을 등록할 수 있습니다.": "Complete your real name + phone profile before listing a project.",
    "구매자가 판매자를 확인할 수 있도록 판매자 공개 정보를 등록해 주세요. (통신판매중개 고지 의무)": "Add your public seller info so buyers can verify who they're dealing with. (Required disclosure for brokered sales.)",
    "가격 제안에는 이메일 인증만 있으면 됩니다. 먼저 이메일을 확인해 주세요.": "Making an offer only needs email verification. Please verify your email first.",
    "지금은 제안할 수 없습니다. 계정 상태를 확인해 주세요.": "You can't make an offer right now. Please check your account status.",
    "이메일 인증이 필요합니다.": "Email verification is required.",
    "성사 후 결제·인수에는 실명·휴대폰(Lv2) 확인이 필요합니다. 앱 → 내 정보에서 완료해 주세요.": "Paying and taking over after a sale is agreed needs real name + phone verification (Lv2). Complete it under App → My info.",
    "정산·이전 확정 전 정산 계좌(예금주·은행·계좌, Lv3)를 등록해 주세요.": "Add your settlement account (holder name, bank, account, Lv3) before confirming settlement/transfer.",
    "소셜 로그인으로 가입한 계정입니다. 카카오·구글·깃허브로 로그인해 주세요.": "This account signed up via social login. Please sign in with Kakao, Google, or GitHub.",
    "정지된 계정입니다.": "Your account has been suspended.",
    "일치하는 계정을 찾지 못했습니다.": "Couldn't find a matching account.",
    "일치하는 계정을 찾지 못했습니다. 프로필에 등록한 실명·휴대폰을 확인하거나, 아직 실명·휴대폰을 넣지 않았다면 가입 이메일을 직접 입력해 주세요.": "Couldn't find a matching account. Check the real name + phone on your profile, or if you haven't added them yet, enter your sign-up email directly.",
    "가입 이메일 힌트를 찾았습니다. 개인정보 보호를 위해 일부만 표시합니다. 기억나는 전체 주소로 로그인해 주세요.": "Found a hint for your sign-up email. Only part of it is shown for privacy. Please sign in with the full address if you remember it.",
    "등록된 이메일이면 재설정 코드를 발급했습니다.": "If that email is registered, we've issued a reset code.",
    "메일 서버(SMTP)가 아직 연결되지 않았습니다. 계정이 있다면 화면에 코드가 표시됩니다. 코드가 없으면 가입 이메일을 확인하거나 새로 가입해 주세요.": "The mail server isn't connected yet. If you have an account, the code will show on screen. If there's no code, check your sign-up email or create a new account.",
    "메일 서버가 일시적으로 연결되지 않았습니다. 잠시 후 다시 시도해 주세요.": "The mail server is temporarily unavailable. Please try again shortly.",
    "비밀번호가 변경되었습니다. 로그인해 주세요.": "Password changed. Please sign in.",
    "이메일 인증 후 프로필을 저장할 수 있습니다.": "Verify your email before saving your profile.",
    "신원 프로필(실명·휴대폰)을 먼저 완성해 주세요.": "Complete your identity profile (real name + phone) first.",
    "실명·휴대폰 프로필(Lv2)을 먼저 완성해 주세요.": "Complete your real name + phone profile (Lv2) first.",
    "판매가와 제안 금액은 전원 공개입니다.": "The asking price and offers are public to everyone.",
    "키워드 추천을 위해 제목 또는 한 줄 소개를 먼저 적어 주세요.": "Enter a title or one-liner first to get keyword suggestions.",
    "AI 추천입니다. 수정·삭제 후 직접 입력도 가능합니다.": "AI-suggested. You can edit, remove, or type your own.",
    "자동 추천입니다. 수정·삭제 후 직접 입력도 가능합니다.": "Auto-suggested. You can edit, remove, or type your own.",
    "차단된 사용자의 매물입니다.": "This listing belongs to a blocked user.",
    "거래 기록 확인서는 해당 매물의 판매자·구매자만 볼 수 있습니다.": "Only the seller or buyer of this listing can view the deal certificate.",
    "아직 성사 기록이 없습니다.": "There's no sale record yet.",
    "거래 절차 완료 전이므로 「거래 기록 확인서」는 아직 발급할 수 없습니다. 성사 기록 확인서를 이용해 주세요.": "The deal isn't complete yet, so the “deal certificate” isn't available. Please use the sale-agreed certificate instead.",
    "신고는 실명·휴대폰 확인(Lv2) 후 가능합니다.": "Reporting requires real name + phone verification (Lv2).",
    "이 매물은 신고할 수 없는 상태입니다.": "This listing can't be reported in its current state.",
    "본인 매물은 신고할 수 없습니다.": "You can't report your own listing.",
    "차단된 사용자와는 신고할 수 없습니다. (차단을 먼저 해제하세요)": "You can't report a blocked user. (Unblock them first.)",
    "자기 자신은 차단할 수 없습니다.": "You can't block yourself.",
    "정지된 계정은 차단을 사용할 수 없습니다.": "Suspended accounts can't use blocking.",
    "차단 목록에 없는 사용자입니다.": "This user isn't on your block list.",
    "신고 누적으로 판매가 일시 중단된 매물입니다.": "This listing is paused after multiple reports.",
    "지금은 판매 중인 매물이 아닙니다.": "This listing isn't for sale right now.",
    "차단된 사용자의 매물에는 제안할 수 없습니다.": "You can't make offers on a blocked user's listing.",
    "차단된 사용자의 매물은 구매할 수 없습니다.": "You can't buy a blocked user's listing.",
    "제안 금액이 사이트 전체에 즉시 공개됩니다.": "Your offer amount is shown publicly site-wide, instantly.",
    "받는 사람 계정 아이디 또는 이메일을 입력해 주세요.": "Enter the recipient's account ID or email.",
    "인수 확인 목록은 구매자만 체크할 수 있습니다.": "Only the buyer can check the handover checklist.",
    "성사된 매물에서만 사용할 수 있습니다.": "This is only available for completed sales.",
    "입금·이전·검수 단계에서만 체크할 수 있습니다.": "You can only check this during payment/transfer/inspection.",
    "인수 확인 목록을 저장했습니다.": "Handover checklist saved.",
    "이전·검수 단계에서만 인수할 수 있습니다. 판매자 「이전 완료」 후 이용해 주세요.": "You can only take over during transfer/inspection. Please wait until the seller marks “transfer complete.”",
    "인수 확인 목록의 필수 항목을 모두 체크한 뒤 「인수하기」를 눌러 주세요. (직접 이전 후 본인 확인)": "Check all required items on the handover checklist, then click “Take over.” (Confirm you received the transfer directly.)",
    "결제 연동이 아직 설정되지 않았습니다.": "Payment isn't set up yet.",
    "PayPal 채널이 아직 설정되지 않았습니다 (PG 계약 심사 대기 중일 수 있습니다).": "The PayPal channel isn't set up yet (may be pending payment-provider contract review).",
    "차단된 사용자와는 쪽지를 볼 수 없습니다.": "You can't view messages with a blocked user.",
    "차단된 사용자에게 쪽지를 보낼 수 없습니다.": "You can't send messages to a blocked user.",
    "등록 전 「지금 되는 것을 직접 확인」에 체크해 주세요.": "Check “I've verified what currently works” before listing.",
    "등록 전 「하는 일·되는 것·안 되는 것이 사실」에 체크해 주세요.": "Check “What it does / works / doesn't is accurate” before listing.",
    "등록 전 「라이선스·양도 조건을 적었다」에 체크해 주세요.": "Check “I've written the license/transfer terms” before listing.",
    "등록 전 「팔 권한이 있는 자산」에 체크해 주세요.": "Check “I have the right to sell this asset” before listing.",
    "등록 전 「이전 절차를 끝까지 진행할 수 있다」에 체크해 주세요.": "Check “I can see the transfer process through to the end” before listing.",
    "라이선스 또는 양도 조건을 적어 주세요. (예: MIT, 사유 비공개 양도 등)": "Enter the license or transfer terms. (e.g. MIT, private resale, etc.)",
    "「이 제품이 하는 일」을 최소 2가지, 각 8자 이상 쉬운 말로 적어 주세요. 아래 예시 칩을 눌러도 됩니다.": "List at least 2 things “this product does,” 8+ characters each, in plain language. You can also tap the example chips below.",
    "「누구를 위한 제품인가요?」를 짧게라도 적어 주세요. (예: 사장님, 학생)": "Briefly describe “who this is for.” (e.g. small business owners, students)",
    "「지금 되는 것」을 10자 이상 적어 주세요. 예시 칩을 눌러 채울 수 있어요.": "Describe “what currently works” in 10+ characters. You can tap an example chip to fill it in.",
    "「지금 안 되는 것 · 한계」를 짧게라도 적어 주세요. (예: 결제 없음)": "Briefly describe “what doesn't work / limitations.” (e.g. no payments yet)",
    "매물 취득 경로(직접 제작 / 사서·양도받아 재판매 / 기타)를 선택해 주세요.": "Select how you acquired this listing (built it yourself / bought or received it for resale / other).",
    "재판매·기타인 경우 어떻게 취득했는지 10자 이상 적어 주세요.": "If resale/other, describe how you acquired it in 10+ characters.",
    "「왜 팔나요?」를 10자 이상 적어 주세요. (예: 시간 없어서 넘깁니다)": "Describe “why you're selling” in 10+ characters. (e.g. no time to keep working on it)",
    "포함 자산(코드·디자인·도메인 등)을 하나 이상 선택해 주세요. 실제로 넘길 수 있는 것만.": "Select at least one included asset (code, design, domain, etc.) — only things you can actually hand over.",
    "재등록 시에도 동작·기능·권리·양도 확인에 모두 동의해 주세요.": "Please confirm working condition, features, rights, and transfer again when relisting.",
    "성사된 매물은 재등록할 수 없습니다.": "A completed sale can't be relisted.",
    "아직 게시 기간 중입니다. 기간이 끝난 뒤 재등록할 수 있습니다.": "This listing period is still running. You can relist after it ends.",
    "이미 검수 대기 중입니다.": "Already pending review.",
    "지금 상태에서는 재등록할 수 없습니다.": "This listing can't be relisted in its current state.",
    "스크린샷이 있으면 실제 제품 화면 확인에 동의해 주세요.": "If you have screenshots, please confirm they're real product screens.",
    "스크린샷이 실제 실행 화면과 같다는 확인에 체크해 주세요. 실제 제품과 다른 화면은 매물 중단·이용 제한 대상이 될 수 있습니다.": "Please confirm your screenshots match the real running product. Screens that don't match the actual product may lead to the listing being paused or your account restricted.",
    "재등록 접수 · 재검수 후 새 게시 기간에 공개됩니다. 승인 시 공개 목록 후순위(줄 맨 뒤)부터 시작합니다. 오픈마켓식 끌올·도배 상위 노출이 아닙니다.": "Relist received. It goes public for a new listing period after re-review. Once approved, it starts at the back of the public queue — not open-market bump/repost boosting.",
    "게시 허용된 후기만 공개됩니다.": "Only approved reviews are shown publicly.",
    "후기가 접수되었습니다. 운영 검수 후 공개되며, 보통 1~2영업일 안에 반영됩니다.": "Review submitted. It'll go live after staff review, usually within 1–2 business days.",
    "관심 등록은 경량 접수입니다. 제안·성사 전에는 신원·정산 확인이 필요합니다.": "Registering interest is a lightweight signup. Making an offer/closing a deal needs identity + settlement verification first.",
    "사전 접수입니다. 공개 매물·가격 제안은 계정 이메일 인증·실명·휴대폰 확인 후 가능합니다.": "This is a pre-registration. Public listings/offers need account email + real name + phone verification first.",
    // 고정가 + 제안(offer) 전환 (2026-09-02) — 백엔드가 새로 내는 한국어 메시지
    "판매가 이상이면 제안 대신 바로 구매해 주세요.": "That's at or above the asking price — just buy it instead.",
    "이미 대기 중인 제안이 있습니다.": "You already have a pending offer.",
    "본인 매물에는 제안할 수 없습니다.": "You can't make an offer on your own listing.",
    "제안이 접수되었습니다. 판매자가 48시간 안에 수락하거나 거절합니다.": "Offer sent. The seller has 48 hours to accept or decline.",
    "제안을 철회했습니다.": "Offer withdrawn.",
    "제안을 수락했습니다. 결제 → 이전 → 검수 순서로 진행됩니다.": "Offer accepted. Next: payment → transfer → inspection.",
    "제안을 거절했습니다.": "Offer declined.",
    "이미 처리된 제안입니다.": "This offer has already been handled.",
    "제안을 찾을 수 없습니다.": "Offer not found.",
    "판매가로 바로 구매가 성사되었습니다. 결제를 진행해 주세요.": "Bought at the asking price. Please proceed to payment.",
  };

  // A few backend messages embed a runtime number/name via Korean sentence
  // templates, so they can't be matched verbatim — translate by pattern.
  var BACKEND_MSG_EN_PATTERNS = [
    {
      re: /^제안 하한은 ₩([\d,]+) 입니다\.$/,
      en: function (m) {
        return "The minimum offer is ₩" + m[1] + ".";
      },
    },
    {
      re: /^제안 하한은 ₩([\d,]+)\s*입니다\.?/,
      en: function (m) {
        return "The minimum offer is ₩" + m[1] + ".";
      },
    },
    {
      re: /^판매가\(₩([\d,]+)\) 이상이면 제안 대신 바로 구매해 주세요\.?$/,
      en: function (m) {
        return "That's at or above the asking price (₩" + m[1] + ") — just buy it instead.";
      },
    },
    {
      re: /^검색 키워드를 (\d+)~(\d+)개 넣어 주세요\. AI 추천 또는 직접 입력 가능합니다\.$/,
      en: function (m) {
        return "Add " + m[1] + "–" + m[2] + " search keywords. Use the AI suggestions or type your own.";
      },
    },
    {
      re: /^실행 화면 스크린샷을 최소 (\d+)장 이상 올려 주세요\. \(최대 (\d+)장\)$/,
      en: function (m) {
        return "Upload at least " + m[1] + " screenshot(s) of the app running. (Max " + m[2] + ")";
      },
    },
    {
      re: /^(정지된 계정입니다|계정이 정지되었습니다)\.?/,
      en: function () {
        return "Your account has been suspended. Contact corelabs.studio@gmail.com if you believe this is a mistake.";
      },
    },
  ];

  function translateBackendText(text) {
    if (!text || !isEn()) return text;
    var s = String(text);
    if (Object.prototype.hasOwnProperty.call(BACKEND_MSG_EN, s)) return BACKEND_MSG_EN[s];
    for (var i = 0; i < BACKEND_MSG_EN_PATTERNS.length; i++) {
      var m = s.match(BACKEND_MSG_EN_PATTERNS[i].re);
      if (m) return BACKEND_MSG_EN_PATTERNS[i].en(m);
    }
    return s;
  }

  function parseErrorDetail(data, fallback) {
    if (!data) return fallback;
    const d = data.detail;
    if (typeof d === "string") return translateBackendText(d);
    if (d && typeof d === "object") {
      if (d.message) return translateBackendText(d.message);
      if (Array.isArray(d)) {
        return d
          .map(function (x) {
            return x.msg || JSON.stringify(x);
          })
          .join("; ");
      }
      return JSON.stringify(d);
    }
    return translateBackendText(data.message) || fallback;
  }

  async function request(path, options) {
    const opts = options || {};
    const headers = Object.assign({ Accept: "application/json" }, opts.headers || {});
    if (opts.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
    // Locale hint for future localized API messages
    try {
      const lang =
        (global.WakeAgainI18n && global.WakeAgainI18n.getLang && global.WakeAgainI18n.getLang()) ||
        localStorage.getItem("wa_lang") ||
        (navigator.language || "ko").slice(0, 2);
      if (!headers["Accept-Language"]) {
        headers["Accept-Language"] = lang === "en" ? "en,ko;q=0.8" : "ko,en;q=0.8";
      }
    } catch (e) {}
    const t = token();
    if (t) headers.Authorization = "Bearer " + t;
    const url = apiBase() + path;
    const res = await fetch(url, Object.assign({}, opts, { headers }));
    let data = null;
    const text = await res.text();
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { detail: text };
    }
    if (!res.ok) {
      const msg = parseErrorDetail(data, res.statusText || "request failed");
      const err = new Error(msg);
      err.status = res.status;
      err.data = data;
      err.code =
        data && data.detail && typeof data.detail === "object" ? data.detail.code : null;
      throw err;
    }
    return data;
  }

  function rememberAuth(data) {
    if (data.token) setSession(data.token, data.user);
    else if (data.user) localStorage.setItem(STORAGE_USER, JSON.stringify(data.user));
    if (data.dev_email_code) setDevCode(data.dev_email_code);
    return data;
  }

  function applyMailMeta(data) {
    if (data && data.dev_email_code) setDevCode(data.dev_email_code);
    return data;
  }

  function getSavedLogin() {
    try {
      const raw = localStorage.getItem(STORAGE_SAVED_LOGIN);
      if (!raw) return null;
      const o = JSON.parse(raw);
      if (!o || typeof o !== "object") return null;
      return {
        email: String(o.email || "").trim(),
        password: String(o.password || ""),
        remember: o.remember !== false,
      };
    } catch {
      return null;
    }
  }

  function setSavedLogin(email, password) {
    const e = String(email || "").trim();
    if (!e) {
      localStorage.removeItem(STORAGE_SAVED_LOGIN);
      return;
    }
    localStorage.setItem(
      STORAGE_SAVED_LOGIN,
      JSON.stringify({
        email: e,
        password: String(password || ""),
        remember: true,
        saved_at: Date.now(),
      })
    );
  }

  function clearSavedLogin() {
    localStorage.removeItem(STORAGE_SAVED_LOGIN);
  }

  const api = {
    apiBase,
    isNativeShell,
    pageUrl,
    goPage,
    request,
    translateBackendText,
    setApiBase(url) {
      if (url) localStorage.setItem(STORAGE_API, url.replace(/\/$/, ""));
      else localStorage.removeItem(STORAGE_API);
    },
    token,
    getUser,
    getDevCode,
    getSavedLogin,
    setSavedLogin,
    clearSavedLogin,
    clearDevCode() {
      setDevCode(null);
    },
    clearSession() {
      setSession(null, null);
      setDevCode(null);
      // keep saved login credentials for next open
    },
    trust() {
      const u = getUser();
      return (u && u.trust) || null;
    },
    async config() {
      return request("/api/v1/config");
    },
    async register(email, password, display_name, birth_date, confirm_age_14, country) {
      // 첫 방문 때 잡아둔 유입 경로를 함께 보낸다 (footer-visitors.js가 채워둠).
      let src = { source: "", referrer: "", landing: "" };
      try {
        if (window.WakeAgainSource) src = window.WakeAgainSource.get() || src;
      } catch (e) {}
      const data = await request("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          display_name: display_name || "",
          birth_date: birth_date || "",
          confirm_age_14: !!confirm_age_14,
          country: country || "",
          signup_source: src.source || "",
          signup_referrer: src.referrer || "",
          signup_landing: src.landing || "",
        }),
      });
      return rememberAuth(data);
    },
    async setBirthDate(birth_date, confirm_age_14) {
      const data = await request("/api/v1/me/birth-date", {
        method: "PUT",
        body: JSON.stringify({
          birth_date: birth_date || "",
          confirm_age_14: !!confirm_age_14,
        }),
      });
      if (data.user) localStorage.setItem(STORAGE_USER, JSON.stringify(data.user));
      return data;
    },
    oauthStartUrl(provider) {
      return apiBase() + "/api/v1/auth/oauth/" + encodeURIComponent(provider) + "/start";
    },
    async login(email, password) {
      const data = await request("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      return rememberAuth(data);
    },
    async passwordResetRequest(email) {
      return request("/api/v1/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
    },
    async passwordResetConfirm(email, code, new_password) {
      return request("/api/v1/auth/password-reset/confirm", {
        method: "POST",
        body: JSON.stringify({ email, code, new_password }),
      });
    },
    async findEmail(real_name, phone) {
      return request("/api/v1/auth/find-email", {
        method: "POST",
        body: JSON.stringify({ real_name, phone }),
      });
    },
    // ── 고정가 + 제안(offer) — 2026-09-02 계약 (scratchpad OFFER_API.md) ──
    /** Buyer: buy immediately at the asking price → sale agreed (finalize_sale). */
    async buyAtPrice(projectId) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/buy", {
        method: "POST",
        body: JSON.stringify({}),
      });
    },
    /** @deprecated alias of buyAtPrice — kept for older pages */
    async buyNow(projectId) {
      return this.buyAtPrice(projectId);
    },
    /** Public: pending offers (+ `mine` when logged in; owner sees every status). */
    async listOffers(projectId) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/offers");
    },
    /** Buyer: make an offer below the asking price (Lv1 email verified). */
    async makeOffer(projectId, amount, message) {
      var body = { amount: Number(amount) };
      var msg = String(message == null ? "" : message).trim();
      if (msg) body.message = msg.slice(0, 300);
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/offers", {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    /** Seller: accept one pending offer → sale agreed (Lv3 settlement ready). */
    async acceptOffer(projectId, offerId) {
      return request(
        "/api/v1/projects/" +
          encodeURIComponent(projectId) +
          "/offers/" +
          encodeURIComponent(offerId) +
          "/accept",
        { method: "POST", body: "{}" }
      );
    },
    /** Seller: decline one pending offer (optional note to the buyer). */
    async declineOffer(projectId, offerId, note) {
      return request(
        "/api/v1/projects/" +
          encodeURIComponent(projectId) +
          "/offers/" +
          encodeURIComponent(offerId) +
          "/decline",
        { method: "POST", body: JSON.stringify({ note: String(note || "").trim() }) }
      );
    },
    /** Buyer: withdraw my own pending offer. */
    async withdrawOffer(projectId, offerId) {
      return request(
        "/api/v1/projects/" +
          encodeURIComponent(projectId) +
          "/offers/" +
          encodeURIComponent(offerId) +
          "/withdraw",
        { method: "POST", body: "{}" }
      );
    },
    /**
     * Seller/admin manual close. Pass { offer_id } to accept that offer, or
     * { sold_price, buyer_user_id, note } for a manual sale record.
     */
    async closeDeal(projectId, payload) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/close-deal", {
        method: "POST",
        body: JSON.stringify(payload || {}),
      });
    },
    async dealMarkTransferred(projectId, note) {
      return request(
        "/api/v1/projects/" + encodeURIComponent(projectId) + "/deal/mark-transferred",
        { method: "POST", body: JSON.stringify({ note: note || "" }) }
      );
    },
    async dealAccept(projectId, note) {
      return request(
        "/api/v1/projects/" + encodeURIComponent(projectId) + "/deal/accept",
        { method: "POST", body: JSON.stringify({ note: note || "" }) }
      );
    },
    async paymentRequest(projectId, payMethod) {
      var qs = payMethod ? "?method=" + encodeURIComponent(payMethod) : "";
      return request(
        "/api/v1/projects/" + encodeURIComponent(projectId) + "/payment/request" + qs,
        { method: "POST" }
      );
    },
    async paymentVerify(paymentId) {
      return request("/api/v1/payments/verify", {
        method: "POST",
        body: JSON.stringify({ payment_id: paymentId }),
      });
    },
    /** Buyer: { itemId: true/false } receipt checklist */
    async updateHandoverChecklist(projectId, checks) {
      return request(
        "/api/v1/projects/" +
          encodeURIComponent(projectId) +
          "/deal/handover-checklist",
        { method: "PUT", body: JSON.stringify({ checks: checks || {} }) }
      );
    },
    async dealDispute(projectId, note) {
      return request(
        "/api/v1/projects/" + encodeURIComponent(projectId) + "/deal/dispute",
        { method: "POST", body: JSON.stringify({ note: note || "" }) }
      );
    },
    async listNotifications() {
      return request("/api/v1/notifications");
    },
    async markNotificationsRead() {
      return request("/api/v1/notifications/read", { method: "POST", body: "{}" });
    },
    async verifyEmail(code) {
      const data = await request("/api/v1/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ code: String(code || "").trim() }),
      });
      if (data.user) localStorage.setItem(STORAGE_USER, JSON.stringify(data.user));
      setDevCode(null);
      return data;
    },
    async resendVerify() {
      const data = await request("/api/v1/auth/resend-verify", { method: "POST" });
      if (data.dev_email_code) setDevCode(data.dev_email_code);
      if (data.user) localStorage.setItem(STORAGE_USER, JSON.stringify(data.user));
      return data;
    },
    async me() {
      const data = await request("/api/v1/me");
      if (data.user) localStorage.setItem(STORAGE_USER, JSON.stringify(data.user));
      return data;
    },
    async updateProfile(payload) {
      const data = await request("/api/v1/me/profile", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      if (data.user) localStorage.setItem(STORAGE_USER, JSON.stringify(data.user));
      return data;
    },
    async updateSettlement(payload) {
      const data = await request("/api/v1/me/settlement", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      if (data.user) localStorage.setItem(STORAGE_USER, JSON.stringify(data.user));
      return data;
    },
    async updateSellerIdentity(payload) {
      const data = await request("/api/v1/me/seller-identity", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      if (data.user) localStorage.setItem(STORAGE_USER, JSON.stringify(data.user));
      return data;
    },
    async listProjects(mine, limit, offset, searchQ) {
      var q = [];
      if (mine) q.push("mine=true");
      if (limit != null) q.push("limit=" + encodeURIComponent(limit));
      if (offset != null) q.push("offset=" + encodeURIComponent(offset));
      if (searchQ != null && String(searchQ).trim()) {
        q.push("q=" + encodeURIComponent(String(searchQ).trim()));
      }
      return request("/api/v1/projects" + (q.length ? "?" + q.join("&") : ""));
    },
    async suggestKeywords(payload) {
      return request("/api/v1/projects/suggest-keywords", {
        method: "POST",
        body: JSON.stringify(payload || {}),
      });
    },
    async listMessages(projectId) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/messages");
    },
    async postMessage(projectId, body) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/messages", {
        method: "POST",
        body: JSON.stringify({ body: body }),
      });
    },
    async myFees() {
      return request("/api/v1/me/fees");
    },
    async myCoupons() {
      return request("/api/v1/me/coupons");
    },
    async redeemCoupon(code) {
      return request("/api/v1/me/coupons/redeem", {
        method: "POST",
        body: JSON.stringify({ code: String(code || "").trim() }),
      });
    },
    async giftCoupon(couponId, toRecipient) {
      const to = String(toRecipient || "").trim();
      const body = { to: to };
      // Also send typed fields when obvious (backend accepts either)
      if (/^\d+$/.test(to)) {
        body.to_user_id = parseInt(to, 10);
      } else if (to.indexOf("@") >= 0) {
        body.to_email = to;
      }
      return request(
        "/api/v1/me/coupons/" + encodeURIComponent(couponId) + "/gift",
        {
          method: "POST",
          body: JSON.stringify(body),
        }
      );
    },
    async promoEventPublic() {
      return request("/api/v1/promo/event");
    },
    async myPromoEvent() {
      return request("/api/v1/me/promo/event");
    },
    async submitPromoEvent(channel, postUrl) {
      return request("/api/v1/me/promo/event/submit", {
        method: "POST",
        body: JSON.stringify({
          channel: String(channel || "instagram").trim(),
          post_url: String(postUrl || "").trim(),
        }),
      });
    },
    async claimPromoEvent(submissionId) {
      return request(
        "/api/v1/me/promo/event/" +
          encodeURIComponent(submissionId) +
          "/claim",
        { method: "POST", body: "{}" }
      );
    },
    /** @deprecated use myPromoEvent — kept for older pages */
    async myPromoInstagram() {
      return this.myPromoEvent();
    },
    async submitPromoInstagram(postUrl) {
      return this.submitPromoEvent("instagram", postUrl);
    },
    async claimPromoInstagram(submissionId) {
      return this.claimPromoEvent(submissionId);
    },
    async getProject(id) {
      return request("/api/v1/projects/" + encodeURIComponent(id));
    },
    /** kind: award | complete | auto — same doc for seller and buyer */
    async getDealCertificate(projectId, kind) {
      var q = kind ? "?kind=" + encodeURIComponent(kind) : "?kind=auto";
      return request(
        "/api/v1/projects/" + encodeURIComponent(projectId) + "/certificate" + q
      );
    },
    async reportProject(projectId, reason, detail) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/report", {
        method: "POST",
        body: JSON.stringify({ reason: reason, detail: detail || "" }),
      });
    },
    async blockUser(userId) {
      return request("/api/v1/users/" + encodeURIComponent(userId) + "/block", {
        method: "POST",
        body: JSON.stringify({}),
      });
    },
    async unblockUser(userId) {
      return request("/api/v1/users/" + encodeURIComponent(userId) + "/block", {
        method: "DELETE",
      });
    },
    async listBlocks() {
      return request("/api/v1/me/blocks");
    },
    /** Public live board: { listings, ticker (recent offers), poll_seconds }. */
    async liveListings() {
      return request("/api/v1/listings/live");
    },
    /** @deprecated alias of liveListings — kept for older pages */
    async liveAuctions() {
      return this.liveListings();
    },
    async createProject(payload) {
      return request("/api/v1/projects", { method: "POST", body: JSON.stringify(payload) });
    },
    /** Seller: relist for a new listing period — { listing_days (1–30, default 7), price? }. */
    async relistProject(projectId, payload) {
      var body = Object.assign({}, payload || {});
      if (body.listing_days == null && body.auction_days != null) body.listing_days = body.auction_days;
      delete body.auction_days;
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/relist", {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    async deleteProject(projectId) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId), { method: "DELETE" });
    },
    /** Seller: change the asking price while the listing is for sale. */
    async updateProjectPrice(projectId, price) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/price", {
        method: "PUT",
        body: JSON.stringify({ price: Number(price) }),
      });
    },
    // 필수 필드 정책(2026-08-15) 보완: 정책 이전 매물에 저장소·라이브데모·활동일을 채워 넣는다.
    // 보낸 필드만 반영된다.
    async updateProjectVerification(projectId, body) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/verification", {
        method: "PUT",
        body: JSON.stringify(body || {}),
      });
    },
    async getQCredits(projectId) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/q-credits");
    },
    async createQThread(projectId, body) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/q-credits/threads", {
        method: "POST",
        body: JSON.stringify({ body: body }),
      });
    },
    async answerQThread(projectId, threadId, answer) {
      return request(
        "/api/v1/projects/" +
          encodeURIComponent(projectId) +
          "/q-credits/threads/" +
          encodeURIComponent(threadId) +
          "/answer",
        { method: "POST", body: JSON.stringify({ answer: answer }) }
      );
    },
    async cancelQThread(projectId, threadId) {
      return request(
        "/api/v1/projects/" +
          encodeURIComponent(projectId) +
          "/q-credits/threads/" +
          encodeURIComponent(threadId) +
          "/cancel",
        { method: "POST", body: "{}" }
      );
    },
    async purchaseQCredits(projectId, units) {
      return request(
        "/api/v1/projects/" + encodeURIComponent(projectId) + "/q-credits/purchase",
        { method: "POST", body: JSON.stringify({ units: units || 1 }) }
      );
    },
    /**
     * Upload one demo screenshot. Pass a Blob/File (client-resized preferred).
     * Returns { ok, url, bytes, ext, limits }.
     */
    async uploadDemoImage(file) {
      const fd = new FormData();
      fd.append("file", file, file.name || "demo.jpg");
      const headers = { Accept: "application/json" };
      const t = token();
      if (t) headers.Authorization = "Bearer " + t;
      const url = apiBase() + "/api/v1/uploads/demo";
      const res = await fetch(url, { method: "POST", headers: headers, body: fd });
      let data = null;
      const text = await res.text();
      try {
        data = text ? JSON.parse(text) : null;
      } catch (e) {
        data = { detail: text };
      }
      if (!res.ok) {
        const msg = parseErrorDetail(data, res.statusText || "upload failed");
        const err = new Error(msg);
        err.status = res.status;
        err.data = data;
        err.code =
          data && data.detail && typeof data.detail === "object" ? data.detail.code : null;
        throw err;
      }
      return data;
    },
    async createInterest(payload) {
      return request("/api/v1/interest", { method: "POST", body: JSON.stringify(payload) });
    },
    async createLead(payload) {
      return request("/api/leads", { method: "POST", body: JSON.stringify(payload) });
    },
    async stats() {
      return request("/api/v1/stats");
    },
    async recordVisit(visitor_key) {
      let utm = "";
      try {
        const p = new URLSearchParams(window.location.search);
        utm = (p.get("utm_source") || p.get("src") || "").slice(0, 60);
      } catch (e) {}
      return request("/api/v1/visit", {
        method: "POST",
        body: JSON.stringify({
          visitor_key: visitor_key || "",
          referrer: document.referrer || "",
          utm_source: utm,
        }),
      });
    },
    async pricing() {
      return request("/api/v1/pricing");
    },
    async listReviews(limit) {
      return request("/api/v1/reviews" + (limit ? "?limit=" + encodeURIComponent(limit) : ""));
    },
    async createReview(payload) {
      return request("/api/v1/reviews", { method: "POST", body: JSON.stringify(payload) });
    },
    isLoggedIn() {
      return Boolean(token());
    },
  };

  global.WakeAgainAPI = api;
})(typeof window !== "undefined" ? window : globalThis);
