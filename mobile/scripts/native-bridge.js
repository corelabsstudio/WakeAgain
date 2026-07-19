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

  async function run() {
    var Cap = window.Capacitor;
    if (!Cap || typeof Cap.isNativePlatform !== "function" || !Cap.isNativePlatform()) {
      return;
    }
    document.documentElement.classList.add("is-native-app");
    document.body && document.body.classList.add("is-native-app");

    try {
      var StatusBar = Cap.Plugins && Cap.Plugins.StatusBar;
      if (StatusBar) {
        if (StatusBar.setStyle) {
          await StatusBar.setStyle({ style: "DARK" });
        }
        if (StatusBar.setBackgroundColor) {
          await StatusBar.setBackgroundColor({ color: "#050508" });
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
    // Capacitor injects bridge slightly after load
    setTimeout(run, 50);
    setTimeout(run, 400);
  });
})();
