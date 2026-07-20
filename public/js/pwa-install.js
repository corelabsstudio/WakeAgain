/**
 * Service worker + install CTA.
 * - Chrome/Edge: beforeinstallprompt
 * - iOS Safari: Share → Add to Home Screen (no install API)
 * - Kakao/in-app browsers: block install — open external browser
 */
(function () {
  var deferred = null;
  var btnSelectors = ["[data-pwa-install]", "#btnInstallApp", ".js-pwa-install"];

  function t(key, fallback) {
    try {
      if (window.WakeAgainI18n && typeof window.WakeAgainI18n.t === "function") {
        var v = window.WakeAgainI18n.t(key);
        if (v && v !== key) return v;
      }
    } catch (e) { /* ignore */ }
    return fallback;
  }

  function isStandalone() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    );
  }

  function ua() {
    return (navigator.userAgent || "") + " " + (navigator.vendor || "");
  }

  function isIos() {
    var u = ua();
    return /iPhone|iPad|iPod/i.test(u) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  }

  function isAndroid() {
    return /Android/i.test(ua());
  }

  /** KakaoTalk, Instagram, Facebook, Naver, Line, etc. — no reliable PWA install */
  function isInAppBrowser() {
    var u = ua();
    return /KAKAOTALK|FBAN|FBAV|Instagram|Line\/|NAVER\(|Naver|DaumApps|Twitter|X\/|Snapchat|EverytimeApp|Band\//i.test(u);
  }

  function isSafari() {
    var u = ua();
    return /Safari/i.test(u) && !/Chrome|CriOS|FxiOS|EdgiOS|OPiOS|Android/i.test(u);
  }

  function setStatus(msg, kind) {
    var el = document.getElementById("pwaInstallStatus");
    if (!el) return;
    el.hidden = !msg;
    el.textContent = msg || "";
    el.setAttribute("data-kind", kind || "info");
  }

  function scrollToGuide() {
    var steps = document.getElementById("getAppSteps") || document.querySelector(".get-steps");
    if (steps && steps.scrollIntoView) {
      steps.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function openExternalHint() {
    // Best-effort: Android intent to open Chrome; iOS cannot force Safari from JS.
    var url = location.href.split("#")[0];
    if (isAndroid()) {
      // Chrome intent
      var intent =
        "intent://" +
        location.host +
        location.pathname +
        location.search +
        "#Intent;scheme=https;package=com.android.chrome;end";
      location.href = intent;
      setTimeout(function () {
        setStatus(
          t(
            "getapp.inapp_hint",
            "카카오톡 등 앱 안 브라우저에서는 설치가 안 됩니다. 우측 메뉴(⋮) → 「다른 브라우저로 열기」 또는 Chrome에서 다시 열어 주세요."
          ),
          "warn"
        );
        scrollToGuide();
      }, 800);
      return;
    }
    setStatus(
      t(
        "getapp.inapp_hint",
        "카카오톡 등 앱 안 브라우저에서는 설치가 안 됩니다. 우측 메뉴(⋮) → 「다른 브라우저로 열기」 또는 Safari/Chrome에서 다시 열어 주세요."
      ),
      "warn"
    );
    scrollToGuide();
    try {
      // Help user copy link
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).catch(function () {});
      }
    } catch (e) { /* ignore */ }
  }

  function updateButtons() {
    var installable = !!deferred && !isStandalone();
    document.documentElement.classList.toggle("pwa-installable", installable);
    btnSelectors.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        el.hidden = false;
        el.removeAttribute("disabled");
        if (isStandalone()) {
          el.setAttribute("aria-disabled", "true");
        } else {
          el.removeAttribute("aria-disabled");
        }
      });
    });
  }

  function showInAppBanner() {
    if (!isInAppBrowser() || isStandalone()) return;
    if (document.getElementById("pwaInAppBanner")) return;
    var ban = document.createElement("div");
    ban.id = "pwaInAppBanner";
    ban.className = "pwa-inapp-banner";
    ban.setAttribute("role", "alert");
    ban.innerHTML =
      "<strong>" +
      t("getapp.inapp_title", "앱 안에서 보고 있어요") +
      "</strong>" +
      "<p>" +
      t(
        "getapp.inapp_banner",
        "카카오톡·인스타 등 앱 안 브라우저에서는 홈 화면 설치가 막혀 있습니다. 메뉴에서 외부 브라우저(Chrome/Safari)로 연 뒤 「홈 화면에 설치」를 눌러 주세요."
      ) +
      "</p>" +
      '<button type="button" class="btn btn-primary btn-sm" id="pwaOpenExternal">' +
      t("getapp.open_external", "외부 브라우저 안내") +
      "</button>";
    var main = document.querySelector("main") || document.body;
    main.insertBefore(ban, main.firstChild);
    document.getElementById("pwaOpenExternal").addEventListener("click", openExternalHint);
  }

  // SW register
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () {
        /* ignore */
      });
    });
  }

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferred = e;
    updateButtons();
    setStatus(
      t("getapp.ready", "설치 준비가 됐습니다. 「홈 화면에 설치」를 눌러 주세요."),
      "ok"
    );
  });

  window.addEventListener("appinstalled", function () {
    deferred = null;
    document.documentElement.classList.remove("pwa-installable");
    document.documentElement.classList.add("pwa-installed");
    setStatus(t("getapp.installed", "설치됐습니다. 홈 화면 아이콘으로 열어 주세요."), "ok");
  });

  if (isStandalone()) {
    document.documentElement.classList.add("pwa-installed");
  }

  document.addEventListener("DOMContentLoaded", function () {
    showInAppBanner();
    updateButtons();
    if (isStandalone()) {
      setStatus(t("getapp.already", "이미 앱(홈 화면)으로 실행 중입니다."), "ok");
    } else if (isInAppBrowser()) {
      setStatus(
        t(
          "getapp.inapp_hint",
          "카카오톡 등 앱 안에서는 설치가 안 됩니다. 외부 브라우저로 열어 주세요."
        ),
        "warn"
      );
    }
  });

  document.addEventListener("click", function (ev) {
    var tEl = ev.target.closest("[data-pwa-install], #btnInstallApp, .js-pwa-install");
    if (!tEl) return;
    ev.preventDefault();

    if (isStandalone()) {
      setStatus(t("getapp.already", "이미 앱(홈 화면)으로 실행 중입니다."), "ok");
      return;
    }

    // In-app browser (Kakao etc.)
    if (isInAppBrowser()) {
      openExternalHint();
      return;
    }

    // Native install prompt (Android Chrome / desktop)
    if (deferred) {
      deferred.prompt();
      deferred.userChoice
        .then(function (choice) {
          if (choice && choice.outcome === "accepted") {
            setStatus(t("getapp.installed", "설치됐습니다. 홈 화면 아이콘으로 열어 주세요."), "ok");
          } else {
            setStatus(
              t("getapp.dismissed", "설치가 취소됐습니다. 브라우저 메뉴에서 다시 시도할 수 있어요."),
              "info"
            );
          }
        })
        .finally(function () {
          deferred = null;
          updateButtons();
        });
      return;
    }

    // iOS Safari: no prompt API
    if (isIos()) {
      setStatus(
        t(
          "getapp.ios_howto",
          "iPhone: Safari 하단 공유 버튼 → 「홈 화면에 추가」 → 추가를 눌러 주세요. (Chrome 앱 안에서는 안 될 수 있어요)"
        ),
        "info"
      );
      scrollToGuide();
      // If not on guide page, go there
      if (!/get-app\.html/i.test(location.pathname)) {
        location.href = "/get-app.html#install";
      }
      return;
    }

    // Android without prompt yet (criteria / first visit)
    if (isAndroid()) {
      setStatus(
        t(
          "getapp.android_howto",
          "Android: Chrome 메뉴(⋮) → 「앱 설치」또는 「홈 화면에 추가」를 눌러 주세요. 버튼이 바로 안 뜨면 잠시 후 다시 시도하세요."
        ),
        "info"
      );
      scrollToGuide();
      if (!/get-app\.html/i.test(location.pathname)) {
        location.href = "/get-app.html#install";
      }
      return;
    }

    // Desktop fallback
    setStatus(
      t(
        "getapp.desktop_howto",
        "Chrome/Edge 주소창 오른쪽 설치 아이콘, 또는 메뉴 → 「앱 설치」를 사용하세요."
      ),
      "info"
    );
    scrollToGuide();
    if (!/get-app\.html/i.test(location.pathname)) {
      location.href = "/get-app.html#install";
    }
  });
})();
