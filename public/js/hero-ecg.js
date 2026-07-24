/**
 * Live-card vital monitor — BPM + heartbeat pulse (no free-floating background waves).
 * window.WakeAgainHeroEcg.spike() brightens the monitor on new bids.
 */
(function (global) {
  var bpmEl = document.getElementById("heroEcgBpm");
  var card = document.querySelector(".live-card");
  if (!bpmEl && !card) return;

  var reduced =
    global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var baseBpm = 72;
  var spike = 0;
  var t0 = performance.now();
  var raf = 0;

  function tick(now) {
    var t = (now - t0) / 1000;
    if (spike > 0) spike = Math.max(0, spike - 0.02);
    if (card) card.classList.toggle("is-ecg-hot", spike > 0.12);

    // Gentle living BPM around 68–76; bid spike pushes higher
    var bpm = Math.round(baseBpm + Math.sin(t * 0.7) * 3.5 + spike * 26);
    if (bpmEl) bpmEl.textContent = bpm + " BPM";

    if (!reduced) raf = requestAnimationFrame(tick);
  }

  function start() {
    if (reduced) {
      if (bpmEl) bpmEl.textContent = "72 BPM";
      return;
    }
    raf = requestAnimationFrame(tick);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }

  global.WakeAgainHeroEcg = {
    spike: function (level) {
      spike = Math.max(spike, level == null ? 1 : Math.min(1, level));
      if (card) card.classList.add("is-ecg-hot");
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
