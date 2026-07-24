/**
 * Hero live-card green ECG — “project is alive” vital sign.
 * Exposes window.WakeAgainHeroEcg.spike() for bid pulse.
 */
(function (global) {
  var canvas = document.getElementById("heroEcgCanvas");
  if (!canvas || !canvas.getContext) return;

  var ctx = canvas.getContext("2d");
  var dpr = Math.min(global.devicePixelRatio || 1, 2);
  var w = 0;
  var h = 0;
  var raf = 0;
  var t0 = performance.now();
  var phase = 0;
  var spike = 0; // 0..1
  var bpmEl = document.getElementById("heroEcgBpm");
  var card = canvas.closest(".live-card");
  var reduced =
    global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Classic green monitor palette
  var GREEN = [52, 211, 153];
  var GREEN_BRIGHT = [74, 222, 128];
  var GREEN_DIM = [16, 185, 129];

  function resize() {
    var rect = canvas.parentElement
      ? canvas.parentElement.getBoundingClientRect()
      : canvas.getBoundingClientRect();
    w = Math.max(120, Math.floor(rect.width || 320));
    h = Math.max(48, Math.floor(rect.height || 64));
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  /**
   * ECG-ish y for one sample along scrolling strip.
   * xNorm 0..1 across visible width; t advances so waveform scrolls left→right feel.
   */
  function ecgAt(xPx, t, amp) {
    var mid = h * 0.55;
    // Scroll so the QRS complex marches across
    var scroll = t * 0.095 + phase;
    var u = ((xPx * 0.42 + scroll) % 110 + 110) % 110;
    var y = mid;
    // baseline wobble (alive, not flatline)
    y += Math.sin(xPx * 0.04 + t * 0.002) * amp * 0.06;
    y += Math.sin(xPx * 0.11 + t * 0.0035) * amp * 0.03;

    // P wave
    if (u > 18 && u < 30) {
      var p = (u - 18) / 12;
      y -= Math.sin(p * Math.PI) * amp * 0.18;
    }
    // QRS complex
    if (u > 38 && u < 56) {
      var q = (u - 38) / 18;
      if (q < 0.18) y += amp * 0.22 * (q / 0.18);
      else if (q < 0.38) y -= amp * (1.15 + spike * 0.85) * ((q - 0.18) / 0.2);
      else if (q < 0.55) y += amp * 0.95 * (1 + spike * 0.5) * ((q - 0.38) / 0.17);
      else y -= amp * 0.35 * (1 - (q - 0.55) / 0.45);
    }
    // T wave
    if (u > 62 && u < 82) {
      var tw = (u - 62) / 20;
      y -= Math.sin(tw * Math.PI) * amp * 0.28;
    }
    return y;
  }

  function drawStatic() {
    resize();
    ctx.clearRect(0, 0, w, h);
    ctx.lineWidth = 1.6;
    ctx.strokeStyle = "rgba(52, 211, 153, 0.75)";
    ctx.shadowColor = "rgba(52, 211, 153, 0.45)";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    var amp = h * 0.32;
    for (var x = 0; x <= w; x += 2) {
      var y = ecgAt(x, 0, amp);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  function frame(now) {
    var t = now - t0;
    if (spike > 0) spike = Math.max(0, spike - 0.022);
    if (card) card.classList.toggle("is-ecg-hot", spike > 0.15);

    // ~70 BPM baseline, spikes feel like a jump
    var bpm = Math.round(68 + Math.sin(t * 0.0011) * 4 + spike * 28);
    if (bpmEl) bpmEl.textContent = bpm + " BPM";

    ctx.clearRect(0, 0, w, h);

    // soft fill under the line
    var amp = h * (0.34 + spike * 0.12);
    ctx.beginPath();
    for (var x = 0; x <= w; x += 2) {
      var y = ecgAt(x, t, amp);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    var fill = ctx.createLinearGradient(0, 0, 0, h);
    fill.addColorStop(0, "rgba(52, 211, 153, " + (0.12 + spike * 0.12) + ")");
    fill.addColorStop(1, "rgba(52, 211, 153, 0)");
    ctx.fillStyle = fill;
    ctx.fill();

    // main glowing trace
    ctx.globalCompositeOperation = "lighter";
    ctx.beginPath();
    ctx.lineWidth = 1.7 + spike * 1.1;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    var a = 0.82 + spike * 0.18;
    ctx.strokeStyle =
      "rgba(" + GREEN_BRIGHT[0] + "," + GREEN_BRIGHT[1] + "," + GREEN_BRIGHT[2] + "," + a + ")";
    ctx.shadowColor =
      "rgba(" + GREEN[0] + "," + GREEN[1] + "," + GREEN[2] + "," + (0.45 + spike * 0.4) + ")";
    ctx.shadowBlur = 10 + spike * 18;
    for (var x2 = 0; x2 <= w; x2 += 2) {
      var y2 = ecgAt(x2, t, amp);
      if (x2 === 0) ctx.moveTo(x2, y2);
      else ctx.lineTo(x2, y2);
    }
    ctx.stroke();

    // secondary dim echo (depth)
    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.shadowBlur = 4;
    ctx.strokeStyle =
      "rgba(" + GREEN_DIM[0] + "," + GREEN_DIM[1] + "," + GREEN_DIM[2] + ",0.28)";
    for (var x3 = 0; x3 <= w; x3 += 3) {
      var y3 = ecgAt(x3, t * 0.97 + 40, amp * 0.7);
      if (x3 === 0) ctx.moveTo(x3, y3);
      else ctx.lineTo(x3, y3);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.globalCompositeOperation = "source-over";

    // bright leading “beam” tip
    var tipX = ((t * 0.095 + phase) % 110) / 110;
    // tip is where the latest QRS is drawn — approximate right-side energy
    var beamX = w * (0.78 + Math.sin(t * 0.003) * 0.04);
    var beamY = ecgAt(beamX, t, amp);
    ctx.beginPath();
    ctx.fillStyle = "rgba(167, 243, 208, " + (0.55 + spike * 0.4) + ")";
    ctx.shadowColor = "rgba(52, 211, 153, 0.9)";
    ctx.shadowBlur = 14 + spike * 10;
    ctx.arc(beamX, beamY, 2.2 + spike * 1.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    raf = requestAnimationFrame(frame);
  }

  function spikePulse(level) {
    spike = Math.max(spike, level == null ? 1 : Math.min(1, level));
    if (card) card.classList.add("is-ecg-hot");
  }

  function start() {
    resize();
    global.addEventListener("resize", function () {
      resize();
    });
    if (reduced) {
      drawStatic();
      if (bpmEl) bpmEl.textContent = "72 BPM";
      return;
    }
    raf = requestAnimationFrame(frame);
  }

  // Start after layout
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    // next frame so parent has size
    requestAnimationFrame(start);
  }

  global.WakeAgainHeroEcg = {
    spike: spikePulse,
    setAlive: function (on) {
      if (!card) return;
      card.classList.toggle("is-ecg-flat", !on);
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
