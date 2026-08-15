/* 테마 시안 미리보기 스위치 (전 페이지 공통).
 *
 * ?theme=mono 로 한 번 켜면 세션 동안 페이지를 넘겨도 유지된다.
 * ?theme=off 로 끄고, 세션이 끝나면(탭을 닫으면) 자동으로 원래 테마로 돌아온다.
 * localStorage가 아니라 sessionStorage를 쓰는 이유: 시안이 실수로 영구히
 * 남는 걸 막기 위해서다.
 *
 * yard-theme.css가 !important로 광범위하게 덮기 때문에, 시안이 켜져 있는 동안은
 * 그 스타일시트를 disabled 처리한다.
 */
(function () {
  var KEY = "wa_theme_preview";
  var theme = null;

  try {
    var q = new URLSearchParams(location.search || "").get("theme");
    if (q === "off" || q === "none") {
      sessionStorage.removeItem(KEY);
    } else if (q) {
      sessionStorage.setItem(KEY, q);
    }
    theme = sessionStorage.getItem(KEY);
  } catch (e) {
    return;
  }
  // 등록된 시안들. css = 스타일시트, font = 시안 전용 웹폰트,
  // keepYard = 기존 yard 테마를 끄지 않고 그 위에 얹을지 여부.
  var THEMES = {
    mono: {
      cls: "theme-mono",
      css: "/theme-mono.css?v=20260816-mono2",
      font: "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&display=swap",
      keepYard: false,
    },
    taste: {
      cls: "theme-taste",
      css: "/theme-taste.css?v=20260816-taste2",
      font: "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap",
      // yard를 유지한 채 그 위에 얹는다 — 기존 디자인을 갈아엎는 게 아니라
      // 'redesign' 성격이라, 살아있는 규칙은 그대로 두고 문제만 덮어쓴다.
      keepYard: true,
    },
  };

  var conf = THEMES[theme];
  if (!conf) return;

  document.documentElement.setAttribute("data-wa-theme", theme);

  // 시안 전용 폰트 — 평소 로딩에 부담을 주지 않도록 켜졌을 때만 주입
  if (conf.font) {
    var f = document.createElement("link");
    f.rel = "stylesheet";
    f.href = conf.font;
    document.head.appendChild(f);
  }

  // 시안 스타일시트도 켜졌을 때만 주입 (평소엔 요청조차 안 나간다)
  var c = document.createElement("link");
  c.rel = "stylesheet";
  c.href = conf.css;
  document.head.appendChild(c);

  function applyBody() {
    if (!conf.keepYard) {
      var y = document.querySelector('link[href*="yard-theme.css"]');
      if (y) y.disabled = true;
    }
    if (document.body) {
      if (!conf.keepYard) document.body.classList.remove("theme-yard");
      document.body.classList.add(conf.cls);
    }
  }
  if (document.body) applyBody();
  else document.addEventListener("DOMContentLoaded", applyBody);
})();
