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
    async findEmail(real_name, phone) {
      return request("/api/v1/auth/find-email", {
        method: "POST",
        body: JSON.stringify({ real_name, phone }),
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
    async getProject(id) {
      return request("/api/v1/projects/" + encodeURIComponent(id));
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
