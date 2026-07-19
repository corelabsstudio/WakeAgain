/**
 * Hero metrics — live DB counts only (no fabricated GMV / match %).
 * Policy: metrics_policy.mode = live_counts in /api/v1/config
 */
(function () {
  const api = window.WakeAgainAPI;
  const list = document.querySelector(".hero-stats");
  if (!list || !api) return;

  function setItems(items) {
    list.innerHTML = items
      .map(function (it) {
        return (
          "<li><strong" +
          (it.count != null ? ' data-count="' + it.count + '" data-suffix="' + (it.suffix || "") + '"' : "") +
          ">" +
          it.display +
          "</strong><span>" +
          it.label +
          "</span></li>"
        );
      })
      .join("");
    // animate counts if motion already wired
    list.querySelectorAll("[data-count]").forEach(function (el) {
      if (el.dataset.counted) return;
      el.dataset.counted = "1";
      var target = parseFloat(el.getAttribute("data-count") || "0");
      var suf = el.getAttribute("data-suffix") || "";
      var start = performance.now();
      function frame(now) {
        var t = Math.min(1, (now - start) / 900);
        var eased = 1 - Math.pow(1 - t, 3);
        var val = Math.round(target * eased);
        el.textContent = val.toLocaleString("ko-KR") + suf;
        if (t < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    });
  }

  api
    .stats()
    .then(function (s) {
      setItems([
        {
          count: s.projects || 0,
          display: String(s.projects || 0),
          label: "올라온 프로젝트",
          suffix: "",
        },
        {
          count: s.interests || 0,
          display: String(s.interests || 0),
          label: "관심 있어요",
          suffix: "",
        },
        {
          display: "무료",
          label: "올리는 비용",
        },
      ]);
    })
    .catch(function () {
      setItems([
        { display: "—", label: "올라온 프로젝트" },
        { display: "—", label: "관심 있어요" },
        { display: "무료", label: "올리는 비용" },
      ]);
    });
})();
