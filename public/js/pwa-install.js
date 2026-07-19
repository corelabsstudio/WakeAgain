/**
 * Register service worker + install CTA (beforeinstallprompt).
 */
(function () {
  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/sw.js").catch(function () {
      /* ignore */
    });
  });

  var deferred = null;
  var btnSelectors = ["[data-pwa-install]", "#btnInstallApp", ".js-pwa-install"];

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferred = e;
    document.documentElement.classList.add("pwa-installable");
    btnSelectors.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        el.hidden = false;
        el.removeAttribute("disabled");
      });
    });
  });

  window.addEventListener("appinstalled", function () {
    deferred = null;
    document.documentElement.classList.remove("pwa-installable");
    document.documentElement.classList.add("pwa-installed");
  });

  function isStandalone() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    );
  }

  if (isStandalone()) {
    document.documentElement.classList.add("pwa-installed");
  }

  document.addEventListener("click", function (ev) {
    var t = ev.target.closest("[data-pwa-install], #btnInstallApp, .js-pwa-install");
    if (!t) return;
    ev.preventDefault();
    if (deferred) {
      deferred.prompt();
      deferred.userChoice.finally(function () {
        deferred = null;
      });
      return;
    }
    // Fallback: open install guide
    location.href = "/get-app.html";
  });
})();
