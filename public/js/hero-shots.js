/* 히어로 배경 = 실제 라이브 매물 스크린샷 타일.
 *
 * 예전엔 종이 서류 상자 스톡/AI 사진이었다. 우리가 파는 건 디지털 프로젝트라
 * 소재부터 어긋났고, 상자 손글씨 라벨이 AI 생성 티를 냈다. 지금은 실제로 팔고 있는
 * 물건의 화면을 그대로 배경에 깐다 — "여기서 뭘 파는지"가 곧 배경이 된다.
 *
 * 실패하면 아무것도 안 붙이고 조용히 끝낸다. 그래도 scrim/glow가 남아서 히어로는
 * 어두운 단색 배경으로 정상 렌더된다(깨지지 않음).
 */
(function () {
  var box = document.getElementById("heroShots");
  if (!box || !window.fetch) return;

  var TILES = 9; // 3열 × 3행

  fetch("/api/v1/projects?status=live", { headers: { Accept: "application/json" } })
    .then(function (r) {
      return r.ok ? r.json() : null;
    })
    .then(function (d) {
      if (!d || !d.projects || !d.projects.length) return;

      var urls = [];
      d.projects.forEach(function (p) {
        (p.demo_images || []).forEach(function (u) {
          if (u && urls.indexOf(u) === -1) urls.push(u);
        });
      });
      if (!urls.length) return;

      var frag = document.createDocumentFragment();
      for (var i = 0; i < TILES; i++) {
        var img = document.createElement("img");
        // 매물 수가 적을 땐 반복해서 격자를 채운다 (빈칸보다 낫다)
        img.src = urls[i % urls.length];
        img.alt = "";
        img.decoding = "async";
        // 상단 3장만 즉시, 나머지는 지연 — 히어로가 above-the-fold라 첫 행은 바로 필요
        img.loading = i < 3 ? "eager" : "lazy";
        // 깨진 이미지는 빈 상자로 남기지 말고 격자에서 뺀다.
        // 전부 실패하면 격자가 비어 어두운 단색 히어로로 자연히 돌아간다.
        img.onerror = function () {
          if (this.parentNode) this.parentNode.removeChild(this);
        };
        frag.appendChild(img);
      }
      box.appendChild(frag);
    })
    .catch(function () {
      /* 배경 장식이라 실패는 무시한다 */
    });
})();
