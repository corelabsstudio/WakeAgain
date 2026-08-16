/* 챕터 전환 모드 — 스크롤 대신 화면 고정 + 섹션 교체.
 *
 * daoism.systems 계열의 구조를 우리 홈에 얹어보기 위한 **미리보기 전용** 스크립트다.
 * (원본 실측: body{overflow:hidden} · main{position:fixed} · .section 8개가
 *  absolute·top:0로 겹쳐 있고 하나만 .active)
 *
 * ⚠️ theme-mono 미리보기에서만 로드된다. 기본 사이트는 이 파일을 받지도 않는다.
 *
 * 설계 원칙:
 *  · 마크업을 새로 만들지 않는다. 이미 있는 <section>을 그대로 챕터로 쓴다.
 *  · 기능을 건드리지 않는다. 각 챕터 안의 버튼·폼·링크는 원래대로 동작하고,
 *    내용이 길면 챕터 안에서 세로 스크롤된다.
 *  · 되돌릴 수 있어야 한다. destroy()로 클래스를 걷어내면 원래 문서로 돌아온다.
 */
(function () {
  var main = document.getElementById("main") || document.querySelector("main");
  if (!main) return;

  var chapters = [].slice.call(main.querySelectorAll(":scope > section"));
  if (chapters.length < 2) return;

  var idx = 0;
  var locked = false;

  // 챕터 제목 — 목차에 쓸 짧은 라벨을 각 섹션에서 뽑는다.
  function labelOf(sec, i) {
    var el = sec.querySelector("h1, h2, .eyebrow, .center-title");
    var t = (el && el.textContent ? el.textContent : "").replace(/\s+/g, " ").trim();
    if (!t) t = "SECTION " + (i + 1);
    return t.length > 22 ? t.slice(0, 22) + "…" : t;
  }

  document.body.classList.add("chapters-on");
  // :has() 미지원 브라우저 대비 — html 잠금을 클래스로도 건다
  document.documentElement.classList.add("chapters-on-root");
  document.documentElement.style.overflow = "hidden";
  document.documentElement.style.height = "100dvh";
  chapters.forEach(function (s, i) {
    s.classList.add("chapter");
    s.setAttribute("data-chapter", String(i));
  });

  // 목차 (원본의 상단 메뉴 역할)
  var nav = document.createElement("nav");
  nav.className = "chapter-index";
  nav.setAttribute("aria-label", "Chapters");
  chapters.forEach(function (s, i) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "chapter-index-item";
    b.innerHTML =
      '<span class="chapter-index-num">' +
      String(i + 1).padStart(2, "0") +
      '</span><span class="chapter-index-label">' +
      labelOf(s, i) +
      "</span>";
    b.addEventListener("click", function () {
      go(i);
    });
    nav.appendChild(b);
  });
  document.body.appendChild(nav);

  // 진행 표시
  var counter = document.createElement("div");
  counter.className = "chapter-counter";
  document.body.appendChild(counter);

  // 사이트의 스크롤 등장 시스템(.reveal → .is-in)은 IntersectionObserver로 켜지는데,
  // 챕터가 position:absolute라 관찰이 안 걸려 내용이 opacity:0인 채로 남는다(실측).
  // 챕터가 활성화되는 시점에 그 안의 .reveal을 직접 켜준다.
  function revealInside(sec) {
    if (sec.classList.contains("reveal")) sec.classList.add("is-in");
    sec.querySelectorAll(".reveal").forEach(function (el) {
      el.classList.add("is-in");
    });
  }

  function render() {
    chapters.forEach(function (s, i) {
      var on = i === idx;
      if (on) revealInside(s);
      s.classList.toggle("is-active", on);
      // 바로 다음/이전 챕터는 미리 올려둔다(원본의 .nearby와 같은 역할)
      s.classList.toggle("is-nearby", Math.abs(i - idx) === 1);
      // 표시 상태는 인라인으로 직접 쓴다.
      // 사이트의 .reveal/.is-in 규칙과 캐스케이드가 경합해서 클래스만으론
      // 계산값이 어긋났다(실측: 활성 챕터가 opacity 0으로 남음).
      s.style.opacity = on ? "1" : "0";
      s.style.pointerEvents = on ? "auto" : "none";
      s.style.transform = on ? "none" : "translateY(18px)";
      s.style.zIndex = on ? "2" : "0";
      if (on) s.scrollTop = 0;
    });
    [].slice.call(nav.children).forEach(function (b, i) {
      b.classList.toggle("is-on", i === idx);
    });
    counter.textContent =
      String(idx + 1).padStart(2, "0") + " / " + String(chapters.length).padStart(2, "0");
  }

  function go(n) {
    var next = Math.max(0, Math.min(chapters.length - 1, n));
    if (next === idx) return;
    idx = next;
    render();
  }

  // 휠·키보드·스와이프로 챕터 이동.
  // 챕터 내부가 길어 스크롤 중이면 그 스크롤을 먼저 소진시킨다(기능 보존).
  function innerScrollable(el) {
    while (el && el !== document.body) {
      if (el.scrollHeight > el.clientHeight + 4) {
        var atTop = el.scrollTop <= 0;
        var atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 4;
        return { el: el, atTop: atTop, atBottom: atBottom };
      }
      el = el.parentElement;
    }
    return null;
  }

  window.addEventListener(
    "wheel",
    function (e) {
      if (locked) return;
      var down = e.deltaY > 0;
      var s = innerScrollable(e.target);
      if (s && ((down && !s.atBottom) || (!down && !s.atTop))) return; // 내부 스크롤 우선
      if (Math.abs(e.deltaY) < 12) return;
      e.preventDefault();
      locked = true;
      go(idx + (down ? 1 : -1));
      setTimeout(function () {
        locked = false;
      }, 700);
    },
    { passive: false }
  );

  document.addEventListener("keydown", function (e) {
    var tag = (e.target && e.target.tagName) || "";
    if (/INPUT|TEXTAREA|SELECT/.test(tag)) return; // 폼 입력 방해 금지
    if (e.key === "ArrowDown" || e.key === "PageDown") { e.preventDefault(); go(idx + 1); }
    if (e.key === "ArrowUp" || e.key === "PageUp") { e.preventDefault(); go(idx - 1); }
    if (e.key === "Home") { e.preventDefault(); go(0); }
    if (e.key === "End") { e.preventDefault(); go(chapters.length - 1); }
  });

  var ty = null;
  window.addEventListener("touchstart", function (e) { ty = e.touches[0].clientY; }, { passive: true });
  window.addEventListener("touchend", function (e) {
    if (ty == null) return;
    var dy = ty - e.changedTouches[0].clientY;
    var s = innerScrollable(e.target);
    if (s && ((dy > 0 && !s.atBottom) || (dy < 0 && !s.atTop))) { ty = null; return; }
    if (Math.abs(dy) > 60) go(idx + (dy > 0 ? 1 : -1));
    ty = null;
  }, { passive: true });

  render();

  window.WakeAgainChapters = {
    go: go,
    destroy: function () {
      document.body.classList.remove("chapters-on");
      document.documentElement.classList.remove("chapters-on-root");
      document.documentElement.style.overflow = "";
      document.documentElement.style.height = "";
      chapters.forEach(function (s) {
        s.classList.remove("chapter", "is-active", "is-nearby");
        s.style.opacity = s.style.pointerEvents = s.style.transform = s.style.zIndex = "";
      });
      nav.remove();
      counter.remove();
    },
  };
})();
