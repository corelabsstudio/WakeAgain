/**
 * WakeAgain shared client — used by website and Capacitor (Play / App Store).
 * Same token, same API, all channels.
 */
(function (global) {
  const STORAGE_TOKEN = "wa_token";
  const STORAGE_USER = "wa_user";
  const STORAGE_API = "wa_api_base";
  const STORAGE_DEV_CODE = "wa_dev_email_code";

  function apiBase() {
    const saved = localStorage.getItem(STORAGE_API);
    if (saved) return saved.replace(/\/$/, "");
    if (global.WAKEAGAIN_API_BASE) return String(global.WAKEAGAIN_API_BASE).replace(/\/$/, "");
    // Capacitor / file: must not use empty base (relative fetch breaks)
    if (
      location.protocol === "capacitor:" ||
      location.protocol === "ionic:" ||
      location.protocol === "file:" ||
      (global.Capacitor && global.Capacitor.isNativePlatform && global.Capacitor.isNativePlatform())
    ) {
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

  function parseErrorDetail(data, fallback) {
    if (!data) return fallback;
    const d = data.detail;
    if (typeof d === "string") return d;
    if (d && typeof d === "object") {
      if (d.message) return d.message;
      if (Array.isArray(d)) {
        return d
          .map(function (x) {
            return x.msg || JSON.stringify(x);
          })
          .join("; ");
      }
      return JSON.stringify(d);
    }
    return data.message || fallback;
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

  const api = {
    apiBase,
    request,
    setApiBase(url) {
      if (url) localStorage.setItem(STORAGE_API, url.replace(/\/$/, ""));
      else localStorage.removeItem(STORAGE_API);
    },
    token,
    getUser,
    getDevCode,
    clearDevCode() {
      setDevCode(null);
    },
    clearSession() {
      setSession(null, null);
      setDevCode(null);
    },
    trust() {
      const u = getUser();
      return (u && u.trust) || null;
    },
    async config() {
      return request("/api/v1/config");
    },
    async register(email, password, display_name, birth_date, confirm_age_14) {
      const data = await request("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          display_name: display_name || "",
          birth_date: birth_date || "",
          confirm_age_14: !!confirm_age_14,
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
    async placeBid(projectId, amount) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/bids", {
        method: "POST",
        body: JSON.stringify({ amount: Number(amount) }),
      });
    },
    async buyNow(projectId) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/buy-now", {
        method: "POST",
        body: JSON.stringify({}),
      });
    },
    async closeDeal(projectId, payload) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/close-deal", {
        method: "POST",
        body: JSON.stringify(payload || { use_current_bid: true }),
      });
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
    async listProjects(mine, limit, offset) {
      var q = [];
      if (mine) q.push("mine=true");
      if (limit != null) q.push("limit=" + encodeURIComponent(limit));
      if (offset != null) q.push("offset=" + encodeURIComponent(offset));
      return request("/api/v1/projects" + (q.length ? "?" + q.join("&") : ""));
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
    async getProject(id) {
      return request("/api/v1/projects/" + encodeURIComponent(id));
    },
    async reportProject(projectId, reason, detail) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/report", {
        method: "POST",
        body: JSON.stringify({ reason: reason, detail: detail || "" }),
      });
    },
    async liveAuctions() {
      return request("/api/v1/auctions/live");
    },
    async listBids(projectId) {
      return request("/api/v1/projects/" + encodeURIComponent(projectId) + "/bids");
    },
    async createProject(payload) {
      return request("/api/v1/projects", { method: "POST", body: JSON.stringify(payload) });
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
