/**
 * Hero BACKGROUND — single green ECG line scrolling L→R.
 * Amplitude grows left→right (small flatline → strong QRS) = “coming alive”.
 * window.WakeAgainHeroEcg.spike() brightens on new bids.
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

  // Classic QRS beat unit (local y scale)
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

  function beatY(localX) {
    var x = ((localX % BEAT_W) + BEAT_W) % BEAT_W;
    for (var i = 0; i < BEAT.length - 1; i++) {
      var a = BEAT[i];
      var b = BEAT[i + 1];
      if (x >= a[0] && x <= b[0]) {
        var t = b[0] === a[0] ? 0 : (x - a[0]) / (b[0] - a[0]);
        return a[1] + (b[1] - a[1]) * t;
      }
    }
    return 0;
  }

  /**
   * Life envelope: left ≈ flat / tiny, right = full QRS.
   * ease-in so most of the “waking” happens toward the right.
   */
  function lifeAt(x) {
    var u = w > 0 ? Math.max(0, Math.min(1, x / w)) : 0;
    // slight floor so left isn’t dead zero (still faintly alive)
    var floor = 0.06;
    // power curve: small for longer, then grows strongly
    var grow = Math.pow(u, 1.65);
    return floor + (1 - floor) * grow;
  }

  function sampleY(x, scrollPx, baseAmp) {
    var life = lifeAt(x);
    // early left: almost flatline with tiny murmur; right: full ECG shape
    var shape = beatY(x + scrollPx);
    // when life is low, damp shape more; also shrink baseline wobble
    return shape * baseAmp * life;
  }

  function drawLine(scrollPx, midY, baseAmp, alphaScale, thick, blur, hot) {
    ctx.beginPath();
    ctx.lineJoin = "round";
    ctx.lineCap = "round";

    var step = Math.max(2, Math.floor(w / 300));
    // Build path first
    for (var x = 0; x <= w; x += step) {
      var y = midY + sampleY(x, scrollPx, baseAmp);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }

    // Stroke with gradient alpha left→right (waking glow)
    var grad = ctx.createLinearGradient(0, 0, w, 0);
    var a0 = (0.18 + hot * 0.08) * alphaScale;
    var a1 = (0.72 + hot * 0.25) * alphaScale;
    grad.addColorStop(0, "rgba(52, 211, 153, " + a0 + ")");
    grad.addColorStop(0.35, "rgba(52, 211, 153, " + (a0 * 0.9 + a1 * 0.25) + ")");
    grad.addColorStop(0.7, "rgba(74, 222, 128, " + (a0 * 0.35 + a1 * 0.7) + ")");
    grad.addColorStop(1, "rgba(167, 243, 208, " + a1 + ")");

    ctx.lineWidth = thick;
    ctx.strokeStyle = grad;
    ctx.shadowColor = "rgba(52, 211, 153, " + (0.25 + hot * 0.35) + ")";
    ctx.shadowBlur = blur;
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  function paint(scrollPx, hot) {
    ctx.clearRect(0, 0, w, h);
    var mid = h * 0.52;
    // base amp at full life (right edge)
    var baseAmp = h * (0.1 + hot * 0.04);
    var thick = 1.9 + hot * 0.75;
    var blur = 11 + hot * 16;

    // Soft echo
    drawLine(scrollPx + 12, mid, baseAmp * 0.9, 0.32, thick * 0.8, blur * 0.45, hot);
    // Main line
    drawLine(scrollPx, mid, baseAmp, 1, thick, blur, hot);

    // Bright tip on the right — where the heart is “most alive”
    var tipX = w * 0.86;
    var tipY = mid + sampleY(tipX, scrollPx, baseAmp);
    var tipR = 2.2 + hot * 1.6 + lifeAt(tipX) * 1.2;
    ctx.beginPath();
    ctx.fillStyle = "rgba(167, 243, 208, " + (0.45 + lifeAt(tipX) * 0.4 + hot * 0.25) + ")";
    ctx.shadowColor = "rgba(52, 211, 153, 0.95)";
    ctx.shadowBlur = 14 + hot * 14 + lifeAt(tipX) * 8;
    ctx.arc(tipX, tipY, tipR, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  function frame(now) {
    var t = now - t0;
    if (spike > 0) spike = Math.max(0, spike - 0.016);
    hero.classList.toggle("is-ecg-hot", spike > 0.12);

    var scroll = (t * 0.12) % (BEAT_W * 2);
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
