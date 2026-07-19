/**
 * WakeAgain motion pack — cinematic entrance + site motion.
 * Soft dark / trust. Respects prefers-reduced-motion.
 */
(function () {
  var reduce =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var body = document.body;
  var params = new URLSearchParams(window.location.search || "");
  var forceIntro = params.get("intro") === "1";
  var forceSkip = params.get("skip") === "1" || params.get("skipIntro") === "1";
  var enteredKey = "wa_intro_entered";

  function siteMotion() {
    body.classList.remove("motion-pending");
    if (reduce) {
      body.classList.add("motion-off");
      document.querySelectorAll(".reveal, .hero-anim, .hero-device-anim").forEach(function (el) {
        el.classList.add("is-in");
      });
      document.querySelectorAll("[data-count]").forEach(function (el) {
        var n = el.getAttribute("data-count");
        var pre = el.getAttribute("data-prefix") || "";
        var suf = el.getAttribute("data-suffix") || "";
        el.textContent = pre + n + suf;
      });
      document.querySelectorAll(".bar-fill").forEach(function (el) {
        el.style.width = el.style.getPropertyValue("--w") || "62%";
      });
      document.querySelectorAll(".chart-grow span").forEach(function (el) {
        el.style.height = el.style.getPropertyValue("--h") || "50%";
      });
      return;
    }

    body.classList.add("motion-on");
    requestAnimationFrame(function () {
      body.classList.add("hero-ready");
    });

    var bar = document.querySelector(".scroll-progress span");
    function onScrollProgress() {
      if (!bar) return;
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      var p = max > 0 ? h.scrollTop / max : 0;
      bar.style.transform = "scaleX(" + Math.min(1, Math.max(0, p)) + ")";
    }
    window.addEventListener("scroll", onScrollProgress, { passive: true });
    onScrollProgress();

    var layers = document.querySelectorAll("[data-parallax]");
    function onParallax() {
      var y = window.scrollY || 0;
      layers.forEach(function (el) {
        var f = parseFloat(el.getAttribute("data-parallax") || "0.1");
        var rect = el.getBoundingClientRect();
        if (rect.bottom < -80 || rect.top > window.innerHeight + 80) return;
        var offset = (rect.top + rect.height * 0.3 - window.innerHeight * 0.4) * f;
        el.style.transform = "translate3d(0," + offset.toFixed(1) + "px,0)";
      });
    }
    window.addEventListener("scroll", onParallax, { passive: true });
    onParallax();

    function countUp(el) {
      if (el.dataset.counted) return;
      el.dataset.counted = "1";
      var target = parseFloat(el.getAttribute("data-count") || "0");
      var pre = el.getAttribute("data-prefix") || "";
      var suf = el.getAttribute("data-suffix") || "";
      var start = performance.now();
      var dur = 900;
      function frame(now) {
        var t = Math.min(1, (now - start) / dur);
        var eased = 1 - Math.pow(1 - t, 3);
        var val = Math.round(target * eased);
        el.textContent = pre + val + suf;
        if (t < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    }

    function activate(el) {
      if (el.classList.contains("is-in")) return;
      el.classList.add("is-in");
      el.querySelectorAll("[data-count]").forEach(countUp);
      if (el.classList.contains("stagger-kids")) {
        Array.prototype.forEach.call(el.children, function (child, i) {
          child.style.setProperty("--si", String(i));
          child.classList.add("stagger-child");
          requestAnimationFrame(function () {
            child.classList.add("is-in");
          });
        });
      }
    }

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) {
              activate(e.target);
              io.unobserve(e.target);
            }
          });
        },
        { rootMargin: "0px 0px -10% 0px", threshold: 0.12 }
      );
      document.querySelectorAll(".reveal").forEach(function (el) {
        io.observe(el);
      });
    } else {
      document.querySelectorAll(".reveal").forEach(activate);
    }

    setTimeout(function () {
      document.querySelectorAll(".chart-grow span").forEach(function (el, i) {
        el.style.transitionDelay = 80 * i + "ms";
        el.style.height = el.style.getPropertyValue("--h") || "50%";
      });
      document.querySelectorAll(".bar-fill").forEach(function (el) {
        el.style.width = el.style.getPropertyValue("--w") || "62%";
      });
    }, 450);
  }

  function hideIntro(instant) {
    var intro = document.getElementById("siteIntro");
    body.classList.remove("intro-locked");
    try {
      sessionStorage.setItem(enteredKey, "1");
    } catch (e) {}

    function done() {
      if (intro) {
        intro.setAttribute("aria-hidden", "true");
        intro.classList.add("is-gone");
      }
      body.classList.add("intro-done");
      siteMotion();
      var main = document.getElementById("main");
      if (main && !instant) {
        try {
          main.setAttribute("tabindex", "-1");
          main.focus({ preventScroll: true });
        } catch (e2) {}
      }
    }

    if (!intro || instant || reduce) {
      if (intro) intro.classList.add("is-gone");
      done();
      return;
    }

    intro.classList.add("is-leaving");
    body.classList.add("intro-leaving");
    var btn = document.getElementById("introEnter");
    if (btn) btn.disabled = true;
    setTimeout(done, 900);
  }

  function showIntro() {
    var intro = document.getElementById("siteIntro");
    if (!intro) {
      siteMotion();
      return;
    }
    intro.classList.add("is-visible");
    body.classList.add("intro-locked");
    requestAnimationFrame(function () {
      intro.classList.add("is-active");
    });

    var enter = document.getElementById("introEnter");
    var skip = document.getElementById("introSkip");
    if (enter) {
      enter.addEventListener("click", function () {
        hideIntro(false);
      });
      setTimeout(function () {
        try {
          enter.focus();
        } catch (e) {}
      }, 400);
    }
    if (skip) {
      skip.addEventListener("click", function () {
        hideIntro(true);
      });
    }
    document.addEventListener("keydown", function onKey(e) {
      if (e.key === "Enter" && body.classList.contains("intro-locked")) {
        if (document.activeElement === skip) return;
        hideIntro(false);
      }
      if (e.key === "Escape" && body.classList.contains("intro-locked")) {
        hideIntro(true);
      }
    });
  }

  function boot() {
    var already = false;
    try {
      already = sessionStorage.getItem(enteredKey) === "1";
    } catch (e) {}

    if (forceSkip || (already && !forceIntro)) {
      var intro = document.getElementById("siteIntro");
      if (intro) {
        intro.classList.add("is-gone");
        intro.setAttribute("aria-hidden", "true");
      }
      body.classList.remove("intro-locked");
      body.classList.add("intro-done");
      siteMotion();
      return;
    }

    showIntro();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
