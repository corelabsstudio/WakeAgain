/**
 * Capacitor native polish — safe no-op on web.
 * Loaded after runtime-config.js in the app shell.
 */
(function () {
  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  function markNative() {
    document.documentElement.classList.add("is-native-app");
    if (document.body) document.body.classList.add("is-native-app");
  }

  async function run() {
    var Cap = window.Capacitor;
    if (!Cap || typeof Cap.isNativePlatform !== "function" || !Cap.isNativePlatform()) {
      return;
    }
    markNative();

    try {
      var StatusBar = Cap.Plugins && Cap.Plugins.StatusBar;
      if (StatusBar) {
        // Overlay + CSS safe-area on .app-top only (avoid body double padding / giant top bar)
        if (StatusBar.setOverlaysWebView) {
          await StatusBar.setOverlaysWebView({ overlay: true });
        }
        if (StatusBar.setStyle) {
          await StatusBar.setStyle({ style: "DARK" });
        }
        if (StatusBar.setBackgroundColor) {
          await StatusBar.setBackgroundColor({ color: "#050508" });
        }
        if (StatusBar.show) {
          await StatusBar.show();
        }
      }
    } catch (e) {
      /* ignore */
    }

    try {
      var SplashScreen = Cap.Plugins && Cap.Plugins.SplashScreen;
      if (SplashScreen && SplashScreen.hide) {
        await SplashScreen.hide();
      }
    } catch (e) {
      /* ignore */
    }

    // Hardware back → hash history or exit list
    try {
      var App = Cap.Plugins && Cap.Plugins.App;
      if (App && App.addListener) {
        App.addListener("backButton", function (ev) {
          if (window.history.length > 1) {
            window.history.back();
          } else if (ev && ev.canGoBack === false && App.exitApp) {
            App.exitApp();
          }
        });
      }
    } catch (e) {
      /* ignore */
    }
  }

  ready(function () {
    // Class ASAP so first paint uses compact native CSS
    try {
      var Cap = window.Capacitor;
      if (Cap && typeof Cap.isNativePlatform === "function" && Cap.isNativePlatform()) {
        markNative();
      }
    } catch (e) {
      /* ignore */
    }
    // Capacitor injects bridge slightly after load
    setTimeout(run, 50);
    setTimeout(run, 400);
  });
})();
