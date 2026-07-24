/**
 * Hero background green ECG — full-section ambient “alive” pulse.
 * Not on the live card. window.WakeAgainHeroEcg.spike() for bid energy.
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

  // Green vital layers (monitor green, not purple)
  var layers = [
    { amp: 0.07, speed: 0.00052, freq: 0.011, phase: 0.0, color: [52, 211, 153], alpha: 0.5, thick: 1.8, mid: 0.32 },
    { amp: 0.05, speed: 0.00068, freq: 0.015, phase: 1.9, color: [74, 222, 128], alpha: 0.38, thick: 1.4, mid: 0.48 },
    { amp: 0.038, speed: 0.0004, freq: 0.009, phase: 3.4, color: [16, 185, 129], alpha: 0.3, thick: 1.15, mid: 0.62 },
    { amp: 0.028, speed: 0.00085, freq: 0.02, phase: 4.6, color: [110, 231, 183], alpha: 0.22, thick: 1.0, mid: 0.78 },
  ];

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

  function ecgY(x, time, layer, mid, ampPx) {
    var base =
      Math.sin(x * layer.freq * 0.32 + time * layer.speed * 38 + layer.phase) * ampPx * 0.32;
    var qrs = 0;
    // Heart-rate cycle: ~1 beat per ~90–110 px scroll units
    var cycle =
      (x * 0.016 + time * (0.78 + spike * 0.35) + layer.phase * 2.2) % 100;
    if (cycle > 40 && cycle < 58) {
      var u = (cycle - 40) / 18;
      if (u < 0.18) qrs = ampPx * 0.2 * (u / 0.18);
      else if (u < 0.34) qrs = -ampPx * (1.2 + spike * 1.1) * ((u - 0.18) / 0.16);
      else if (u < 0.5) qrs = ampPx * 0.9 * ((u - 0.34) / 0.16);
      else qrs = -ampPx * 0.28 * (1 - (u - 0.5) / 0.5);
    }
    // Soft P / T
    var pwave = 0;
    if (cycle > 22 && cycle < 34) {
      pwave = -Math.sin(((cycle - 22) / 12) * Math.PI) * ampPx * 0.16;
    }
    if (cycle > 62 && cycle < 80) {
      pwave += -Math.sin(((cycle - 62) / 18) * Math.PI) * ampPx * 0.22;
    }
    var noise = Math.sin(x * 0.085 + time * 0.0018 + layer.phase) * ampPx * 0.07;
    return mid + base + qrs + pwave + noise;
  }

  function drawStatic() {
    resize();
    ctx.clearRect(0, 0, w, h);
    ctx.globalCompositeOperation = "lighter";
    for (var i = 0; i < layers.length; i++) {
      var L = layers[i];
      var mid = h * L.mid;
      var ampPx = h * L.amp;
      ctx.beginPath();
      ctx.lineWidth = L.thick;
      ctx.strokeStyle =
        "rgba(" + L.color[0] + "," + L.color[1] + "," + L.color[2] + "," + L.alpha * 0.7 + ")";
      ctx.shadowColor =
        "rgba(" + L.color[0] + "," + L.color[1] + "," + L.color[2] + ",0.25)";
      ctx.shadowBlur = 10;
      var step = Math.max(3, Math.floor(w / 200));
      for (var x = 0; x <= w; x += step) {
        var y = ecgY(x, 0, L, mid, ampPx);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    ctx.shadowBlur = 0;
    ctx.globalCompositeOperation = "source-over";
  }

  function frame(now) {
    var time = now - t0;
    if (spike > 0) spike = Math.max(0, spike - 0.014);
    hero.classList.toggle("is-ecg-hot", spike > 0.12);

    ctx.clearRect(0, 0, w, h);
    ctx.globalCompositeOperation = "lighter";

    for (var i = 0; i < layers.length; i++) {
      var L = layers[i];
      var mid = h * L.mid;
      var ampPx = h * L.amp * (1 + spike * 1.5);
      var a = L.alpha * (0.72 + spike * 0.55);
      ctx.beginPath();
      ctx.lineWidth = L.thick + spike * 1.1;
      ctx.lineJoin = "round";
      ctx.strokeStyle =
        "rgba(" + L.color[0] + "," + L.color[1] + "," + L.color[2] + "," + a + ")";
      ctx.shadowColor =
        "rgba(" + L.color[0] + "," + L.color[1] + "," + L.color[2] + "," + (0.22 + spike * 0.4) + ")";
      ctx.shadowBlur = 14 + spike * 22;
      var step = Math.max(3, Math.floor(w / 240));
      for (var x = 0; x <= w; x += step) {
        var y = ecgY(x, time, L, mid, ampPx);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    ctx.shadowBlur = 0;
    ctx.globalCompositeOperation = "source-over";
    raf = requestAnimationFrame(frame);
  }

  function onResize() {
    resize();
  }

  function start() {
    resize();
    global.addEventListener("resize", onResize);
    if (typeof ResizeObserver !== "undefined") {
      try {
        new ResizeObserver(onResize).observe(hero);
      } catch (e) {}
    }
    if (reduced) {
      drawStatic();
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
