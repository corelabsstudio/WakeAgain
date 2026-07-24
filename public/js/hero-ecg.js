/**
 * Hero BACKGROUND — real monitor-style ECG.
 * Flat baseline most of the time; one sharp QRS “blip” per cycle.
 * Life envelope: left quieter → right fuller. spike() on new bids.
 */
(function (global) {
  var canvas = document.getElementById("heroEcgCanvas");
  var hero = document.querySelector(".hero");
  if (!canvas || !canvas.getContext || !hero) return;

  var ctx = canvas.getContext("2d", { alpha: true });
  var dpr = 1;
  var w = 0;
  var h = 0;
  /** Pixels per one RR cycle (flat…spike…flat). Wider = fewer spikes on screen. */
  var beatW = 700;
  var raf = 0;
  var t0 = performance.now();
  var spike = 0;
  var reduced =
    global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /**
   * Clinical lead-II-ish shape in unit cycle u∈[0,1].
   * ~75% pure flat line so you literally see “선 → 툭 → 선”.
   * y: negative = up on canvas.
   */
  var BEAT = [
    [0.0, 0],
    [0.55, 0], // long isoelectric run
    // tiny P
    [0.58, -0.1],
    [0.6, 0],
    [0.63, 0],
    // QRS — the only big event
    [0.645, 0.12], // Q
    [0.66, -1.0], // R (up)
    [0.675, 0.35], // S
    [0.69, 0],
    [0.74, 0],
    // soft T
    [0.78, -0.2],
    [0.82, 0],
    [1.0, 0], // rest of cycle flat
  ];

  // How many full cycles scroll past per second (keep slow & readable)
  var CYCLES_PER_SEC = 0.55;

  function resize() {
    var rect = hero.getBoundingClientRect();
    w = Math.max(320, Math.floor(rect.width));
    h = Math.max(280, Math.floor(rect.height));
    dpr = Math.min(global.devicePixelRatio || 1, w > 1400 ? 1.25 : 2);
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // Aim for ~1.5–2.2 spikes visible across the hero
    beatW = Math.round(Math.max(520, Math.min(1400, w * 0.55)));
  }

  function beatY(localX) {
    var u = (((localX % beatW) + beatW) % beatW) / beatW;
    for (var i = 0; i < BEAT.length - 1; i++) {
      var a = BEAT[i];
      var b = BEAT[i + 1];
      if (u >= a[0] && u <= b[0]) {
        var t = b[0] === a[0] ? 0 : (u - a[0]) / (b[0] - a[0]);
        // Keep QRS linear (sharp); smooth P/T
        var sharp = a[0] >= 0.63 && b[0] <= 0.7;
        if (!sharp) t = t * t * (3 - 2 * t);
        return a[1] + (b[1] - a[1]) * t;
      }
    }
    return 0;
  }

  /** Left = almost pure flatline; right = full QRS. */
  function lifeAt(x) {
    var u = w > 0 ? Math.max(0, Math.min(1, x / w)) : 0;
    var floor = 0.05;
    return floor + (1 - floor) * Math.pow(u, 2.1);
  }

  function sampleY(x, scrollPx, baseAmp) {
    return beatY(x + scrollPx) * baseAmp * lifeAt(x);
  }

  function clearFull() {
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.restore();
  }

  function paint(scrollPx, hot) {
    clearFull();
    var mid = h * 0.52;
    // Sized for R-peak only — baseline stays a thin straight line
    var baseAmp = h * (0.085 + hot * 0.03);
    var thick = 1.7 + hot * 0.4;

    ctx.beginPath();
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    for (var x = 0; x <= w; x += 1) {
      var y = mid + sampleY(x, scrollPx, baseAmp);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }

    var a0 = 0.28 + hot * 0.1;
    var a1 = 0.82 + hot * 0.15;
    var grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, "rgba(52, 211, 153, " + a0 + ")");
    grad.addColorStop(0.5, "rgba(52, 211, 153, " + (a0 * 0.5 + a1 * 0.5) + ")");
    grad.addColorStop(1, "rgba(167, 243, 208, " + a1 + ")");
    ctx.lineWidth = thick;
    ctx.strokeStyle = grad;
    ctx.shadowBlur = 0;
    ctx.stroke();

    // Monitor sweep tip
    var tipX = w - 2;
    var tipY = mid + sampleY(tipX, scrollPx, baseAmp);
    ctx.beginPath();
    ctx.fillStyle = "rgba(190, 255, 220, " + (0.65 + hot * 0.25) + ")";
    ctx.arc(tipX, tipY, 2 + hot, 0, Math.PI * 2);
    ctx.fill();
  }

  function frame(now) {
    var t = now - t0;
    if (spike > 0) spike = Math.max(0, spike - 0.016);
    hero.classList.toggle("is-ecg-hot", spike > 0.12);

    var scroll = ((t / 1000) * CYCLES_PER_SEC * beatW) % beatW;
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
