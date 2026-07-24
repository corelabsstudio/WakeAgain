/**
 * Hero BACKGROUND only — one green ECG line that scrolls (same shape as the
 * old card monitor path). No VITAL/BPM chrome, no multi-layer ambient waves.
 * window.WakeAgainHeroEcg.spike() brightens briefly on new bids.
 */
(function (global) {
  var canvas = document.getElementById("heroEcgCanvas");
  var hero = document.querySelector(".hero");
  if (!canvas || !canvas.getContext || !hero) return;

  var ctx = canvas.getContext("2d");
  var dpr = Math.min(global.devicePixelRatio || 1, 2);
  var w = 0;
  var h = 0;
  var raf = 0;
  var t0 = performance.now();
  var spike = 0;
  var reduced =
    global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // One beat unit in local coords (mirrors the card SVG silhouette)
  // Baseline y=0; QRS peaks go negative/positive; repeated across width.
  var BEAT = [
    [0, 0],
    [42, 0],
    [48, 0],
    [54, -0.35],
    [62, 0.45],
    [70, -1.55],
    [78, 1.15],
    [86, -0.25],
    [94, 0],
    [140, 0],
  ];
  var BEAT_W = 140;

  function resize() {
    var rect = hero.getBoundingClientRect();
    w = Math.max(320, Math.floor(rect.width));
    h = Math.max(280, Math.floor(rect.height));
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function yAt(localX, amp) {
    // localX within one beat [0, BEAT_W)
    var x = ((localX % BEAT_W) + BEAT_W) % BEAT_W;
    for (var i = 0; i < BEAT.length - 1; i++) {
      var a = BEAT[i];
      var b = BEAT[i + 1];
      if (x >= a[0] && x <= b[0]) {
        var t = b[0] === a[0] ? 0 : (x - a[0]) / (b[0] - a[0]);
        return (a[1] + (b[1] - a[1]) * t) * amp;
      }
    }
    return 0;
  }

  function drawLine(scrollPx, midY, amp, alpha, thick, blur) {
    ctx.beginPath();
    ctx.lineWidth = thick;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.strokeStyle = "rgba(74, 222, 128, " + alpha + ")";
    ctx.shadowColor = "rgba(52, 211, 153, " + Math.min(0.85, alpha + 0.15) + ")";
    ctx.shadowBlur = blur;
    var step = Math.max(2, Math.floor(w / 280));
    for (var x = 0; x <= w; x += step) {
      var y = midY + yAt(x + scrollPx, amp);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  function paint(scrollPx, hot) {
    ctx.clearRect(0, 0, w, h);
    // Single classic ECG line through mid-hero (alive, green)
    var mid = h * 0.52;
    var amp = h * (0.085 + hot * 0.035);
    var alpha = 0.55 + hot * 0.3;
    var thick = 1.85 + hot * 0.7;
    var blur = 12 + hot * 14;

    // Soft trailing echo (same line, slightly behind — still one ECG, not multi-layer noise)
    drawLine(scrollPx + 10, mid, amp * 0.92, alpha * 0.28, thick * 0.85, blur * 0.5);
    drawLine(scrollPx, mid, amp, alpha, thick, blur);

    // Bright tip (scan head)
    var tipX = w * 0.78;
    var tipY = mid + yAt(tipX + scrollPx, amp);
    ctx.beginPath();
    ctx.fillStyle = "rgba(167, 243, 208, " + (0.55 + hot * 0.35) + ")";
    ctx.shadowColor = "rgba(52, 211, 153, 0.95)";
    ctx.shadowBlur = 16 + hot * 12;
    ctx.arc(tipX, tipY, 2.4 + hot * 1.4, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  function frame(now) {
    var t = now - t0;
    if (spike > 0) spike = Math.max(0, spike - 0.016);
    hero.classList.toggle("is-ecg-hot", spike > 0.12);

    // Scroll speed: one beat ~ every ~1s look
    var scroll = (t * 0.085) % BEAT_W;
    // extend scroll so many beats fill the screen smoothly
    scroll = (t * 0.12) % (BEAT_W * 2);
    paint(scroll, spike);

    raf = requestAnimationFrame(frame);
  }

  function start() {
    resize();
    global.addEventListener("resize", resize);
    if (typeof ResizeObserver !== "undefined") {
      try {
        new ResizeObserver(resize).observe(hero);
      } catch (e) {}
    }
    if (reduced) {
      paint(0, 0);
      return;
    }
    raf = requestAnimationFrame(frame);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      requestAnimationFrame(start);
    });
  } else {
    requestAnimationFrame(start);
  }

  global.WakeAgainHeroEcg = {
    spike: function (level) {
      spike = Math.max(spike, level == null ? 1 : Math.min(1, level));
      hero.classList.add("is-ecg-hot");
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
