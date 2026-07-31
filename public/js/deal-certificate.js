/**
 * WakeAgain deal record confirmation — same card for seller & buyer.
 * Modal + PNG download via canvas (no external deps).
 */
(function (global) {
  var STYLE_ID = "wa-deal-cert-style";
  var ROOT_ID = "waDealCertRoot";

  function isEn() {
    return !!(global.WakeAgainI18n && global.WakeAgainI18n.lang === "en");
  }

  function t(ko, en) {
    return isEn() ? en : ko;
  }

  function won(n) {
    if (n == null || n === "") return "—";
    return "₩" + Number(n).toLocaleString("ko-KR");
  }

  function fmtTime(iso) {
    if (!iso) return "—";
    return String(iso).replace("T", " ").replace(/\+.*$/, "").slice(0, 19);
  }

  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent =
      "#" +
      ROOT_ID +
      "{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;padding:1rem;background:rgba(0,0,0,.72);backdrop-filter:blur(6px)}" +
      "#" +
      ROOT_ID +
      "[hidden]{display:none!important}" +
      "#" +
      ROOT_ID +
      " .wa-cert-panel{max-width:420px;width:100%;max-height:92vh;overflow:auto;border-radius:16px;background:#0f0a1a;border:1px solid rgba(212,160,23,.35);box-shadow:0 20px 50px rgba(0,0,0,.45);padding:1rem 1rem 1.1rem}" +
      "#" +
      ROOT_ID +
      " .wa-cert-card{background:linear-gradient(165deg,#1a1814 0%,#16140f 55%,#12100c 100%);border:1px solid rgba(212,160,23,.4);border-radius:14px;padding:1.15rem 1.2rem 1.25rem;color:#f0e8d8}" +
      "#" +
      ROOT_ID +
      " .wa-cert-brand{font-weight:700;font-size:1.05rem;letter-spacing:-0.02em;margin:0 0 .15rem;background:linear-gradient(90deg,#e8d5a3,#d4a86a);-webkit-background-clip:text;background-clip:text;color:transparent}" +
      "#" +
      ROOT_ID +
      " .wa-cert-title{margin:.35rem 0 .15rem;font-size:1.2rem;font-weight:700;color:#f5f0e6}" +
      "#" +
      ROOT_ID +
      " .wa-cert-lead{margin:0 0 .75rem;font-size:.88rem;color:#a8a0c0;line-height:1.45}" +
      "#" +
      ROOT_ID +
      " .wa-cert-meta{font-size:.78rem;color:#8b83a8;margin:0 0 .65rem;line-height:1.45}" +
      "#" +
      ROOT_ID +
      " .wa-cert-status{display:inline-block;margin:0 0 .75rem;padding:.28rem .65rem;border-radius:999px;font-size:.8rem;font-weight:600;background:rgba(212,160,23,.18);border:1px solid rgba(212,160,23,.4);color:#f0e0b0}" +
      "#" +
      ROOT_ID +
      " .wa-cert-status.is-done{background:rgba(52,211,153,.12);border-color:rgba(52,211,153,.4);color:#a7f3d0}" +
      "#" +
      ROOT_ID +
      " .wa-cert-rows{margin:0;padding:0;list-style:none}" +
      "#" +
      ROOT_ID +
      " .wa-cert-rows li{display:flex;gap:.65rem;padding:.4rem 0;border-top:1px solid rgba(255,255,255,.06);font-size:.9rem;line-height:1.4}" +
      "#" +
      ROOT_ID +
      " .wa-cert-rows .k{flex:0 0 5.5rem;color:#8b83a8;font-size:.8rem}" +
      "#" +
      ROOT_ID +
      " .wa-cert-rows .v{flex:1;color:#f5f0e6;word-break:break-word}" +
      "#" +
      ROOT_ID +
      " .wa-cert-note{margin:.75rem 0 0;font-size:.78rem;color:#9ca3af;line-height:1.45}" +
      "#" +
      ROOT_ID +
      " .wa-cert-fee{margin:.45rem 0 0;font-size:.78rem;color:#e8d5a3}" +
      "#" +
      ROOT_ID +
      " .wa-cert-disc{margin:.65rem 0 0;font-size:.7rem;color:#6b7280;line-height:1.45}" +
      "#" +
      ROOT_ID +
      " .wa-cert-actions{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.95rem}" +
      "#" +
      ROOT_ID +
      " .wa-cert-actions .btn{flex:1;min-width:7rem}" +
      "#" +
      ROOT_ID +
      " .wa-cert-shared{margin:.5rem 0 0;font-size:.75rem;color:#86efac}";
    document.head.appendChild(s);
  }

  function close() {
    var root = document.getElementById(ROOT_ID);
    if (root) root.hidden = true;
  }

  function field(k, v) {
    return (
      "<li><span class=\"k\">" +
      k +
      "</span><span class=\"v\">" +
      v +
      "</span></li>"
    );
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderCardHtml(cert) {
    var en = isEn();
    var title = en ? cert.doc_title_en : cert.doc_title_ko;
    var lead = en ? cert.lead_en : cert.lead_ko;
    var status = en ? cert.status_label_en : cert.status_label_ko;
    var statusNote = en ? cert.status_note_en : cert.status_note_ko;
    var eventLab = en ? cert.event_label_en : cert.event_label_ko;
    var fee = en ? cert.fee_note_en : cert.fee_note_ko;
    var disc = en ? cert.disclaimer_en : cert.disclaimer_ko;
    var shared = en ? cert.note_en : cert.note_ko;
    var done = cert.kind === "complete";

    return (
      '<div class="wa-cert-card" id="waCertCard">' +
      '<p class="wa-cert-brand">WakeAgain</p>' +
      "<h2 class=\"wa-cert-title\">" +
      escapeHtml(title) +
      "</h2>" +
      '<p class="wa-cert-lead">' +
      escapeHtml(lead) +
      "</p>" +
      '<p class="wa-cert-meta">' +
      escapeHtml(en ? "Confirmation No." : "확인번호") +
      " " +
      escapeHtml(cert.doc_id) +
      "<br/>" +
      escapeHtml(en ? "Issued at" : "발급 시각") +
      " " +
      escapeHtml(fmtTime(cert.issued_at)) +
      "</p>" +
      '<span class="wa-cert-status' +
      (done ? " is-done" : "") +
      '">' +
      escapeHtml(status) +
      "</span>" +
      '<p class="wa-cert-note" style="margin-top:0">' +
      escapeHtml(statusNote) +
      "</p>" +
      '<ul class="wa-cert-rows">' +
      field(en ? "Venue" : "거래 장소", escapeHtml(cert.venue)) +
      field(eventLab, escapeHtml(fmtTime(cert.event_at))) +
      field(en ? "Listing No." : "매물 번호", "#" + escapeHtml(cert.project_id)) +
      field(en ? "Listing" : "매물", escapeHtml(cert.project_title)) +
      field(en ? "Amount" : "거래 금액", escapeHtml(won(cert.amount))) +
      field(en ? "Seller" : "판매자", escapeHtml(cert.seller_label)) +
      field(en ? "Buyer" : "구매자", escapeHtml(cert.buyer_label)) +
      "</ul>" +
      '<p class="wa-cert-fee">' +
      escapeHtml(fee) +
      "</p>" +
      '<p class="wa-cert-shared">' +
      escapeHtml(shared) +
      "</p>" +
      '<p class="wa-cert-disc">' +
      escapeHtml(disc) +
      "</p>" +
      "</div>"
    );
  }

  /**
   * Draw certificate to canvas for PNG download (mirrors card content).
   */
  function drawCanvas(cert) {
    var en = isEn();
    var W = 720;
    var H = 980;
    var canvas = document.createElement("canvas");
    canvas.width = W;
    canvas.height = H;
    var ctx = canvas.getContext("2d");

    // background
    var g = ctx.createLinearGradient(0, 0, W, H);
    g.addColorStop(0, "#1a1814");
    g.addColorStop(0.55, "#16140f");
    g.addColorStop(1, "#12100c");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    // border
    ctx.strokeStyle = "rgba(212,160,23,0.55)";
    ctx.lineWidth = 3;
    roundRect(ctx, 18, 18, W - 36, H - 36, 20);
    ctx.stroke();

    var x = 56;
    var y = 64;
    var maxW = W - 112;

    function text(str, size, color, weight) {
      ctx.fillStyle = color || "#f0e8d8";
      ctx.font = (weight || "600") + " " + size + "px system-ui,Segoe UI,sans-serif";
      ctx.fillText(str, x, y);
      y += size + 14;
    }

    function wrap(str, size, color, lineH) {
      ctx.fillStyle = color || "#a8a0c0";
      ctx.font = "400 " + size + "px system-ui,Segoe UI,sans-serif";
      var words = String(str).split(/\s+/);
      var line = "";
      var lh = lineH || size + 8;
      for (var i = 0; i < words.length; i++) {
        var test = line ? line + " " + words[i] : words[i];
        if (ctx.measureText(test).width > maxW && line) {
          ctx.fillText(line, x, y);
          y += lh;
          line = words[i];
        } else line = test;
      }
      if (line) {
        ctx.fillText(line, x, y);
        y += lh;
      }
      y += 6;
    }

    text("WakeAgain", 28, "#e8d5a3", "700");
    y += 4;
    text(en ? cert.doc_title_en : cert.doc_title_ko, 32, "#f5f0e6", "700");
    wrap(en ? cert.lead_en : cert.lead_ko, 16, "#a8a0c0", 24);
    y += 4;
    wrap(
      (en ? "Confirmation No. " : "확인번호 ") + cert.doc_id,
      14,
      "#8b83a8",
      20
    );
    wrap(
      (en ? "Issued at " : "발급 시각 ") + fmtTime(cert.issued_at),
      14,
      "#8b83a8",
      20
    );
    y += 8;

    // status pill
    var st = en ? cert.status_label_en : cert.status_label_ko;
    ctx.font = "600 15px system-ui,Segoe UI,sans-serif";
    var sw = ctx.measureText(st).width + 28;
    ctx.fillStyle =
      cert.kind === "complete" ? "rgba(52,211,153,0.2)" : "rgba(212,160,23,0.22)";
    roundRect(ctx, x, y - 16, sw, 32, 16);
    ctx.fill();
    ctx.fillStyle = cert.kind === "complete" ? "#a7f3d0" : "#f0e0b0";
    ctx.fillText(st, x + 14, y + 4);
    y += 36;
    wrap(en ? cert.status_note_en : cert.status_note_ko, 14, "#9ca3af", 20);
    y += 10;

    var rows = [
      [en ? "Venue" : "거래 장소", cert.venue],
      [en ? cert.event_label_en : cert.event_label_ko, fmtTime(cert.event_at)],
      [en ? "Listing No." : "매물 번호", "#" + cert.project_id],
      [en ? "Listing" : "매물", cert.project_title],
      [en ? "Amount" : "거래 금액", won(cert.amount)],
      [en ? "Seller" : "판매자", cert.seller_label],
      [en ? "Buyer" : "구매자", cert.buyer_label],
    ];
    rows.forEach(function (r) {
      ctx.strokeStyle = "rgba(255,255,255,0.08)";
      ctx.beginPath();
      ctx.moveTo(x, y - 10);
      ctx.lineTo(x + maxW, y - 10);
      ctx.stroke();
      ctx.fillStyle = "#8b83a8";
      ctx.font = "400 14px system-ui,Segoe UI,sans-serif";
      ctx.fillText(r[0], x, y + 6);
      ctx.fillStyle = "#f5f0e6";
      ctx.font = "600 16px system-ui,Segoe UI,sans-serif";
      var val = String(r[1] || "—");
      if (ctx.measureText(val).width > maxW - 140) {
        while (val.length > 4 && ctx.measureText(val + "…").width > maxW - 140) {
          val = val.slice(0, -1);
        }
        val += "…";
      }
      ctx.fillText(val, x + 140, y + 6);
      y += 36;
    });

    y += 12;
    wrap(en ? cert.fee_note_en : cert.fee_note_ko, 13, "#e8d5a3", 18);
    wrap(en ? cert.note_en : cert.note_ko, 13, "#86efac", 18);
    y += 4;
    wrap(en ? cert.disclaimer_en : cert.disclaimer_ko, 12, "#6b7280", 17);

    return canvas;
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function downloadPng(cert) {
    var canvas = drawCanvas(cert);
    var a = document.createElement("a");
    a.download = (cert.file_stem || "WakeAgain-확인서") + ".png";
    a.href = canvas.toDataURL("image/png");
    a.click();
  }

  function shareCardText(cert) {
    var en = isEn();
    if (cert.kind === "complete") {
      return en
        ? "Just closed a deal on WakeAgain — " +
            (cert.project_title || "a project") +
            " sold for " +
            won(cert.amount) +
            "! wakeagain.com"
        : (cert.project_title || "프로젝트") +
            "를 " +
            won(cert.amount) +
            "에 성사시켰어요! WakeAgain에서 잠든 프로젝트에 두 번째 기회를. wakeagain.com";
    }
    return en
      ? "Won an auction on WakeAgain for " +
          (cert.project_title || "a project") +
          "! wakeagain.com"
      : (cert.project_title || "프로젝트") +
          " 경매 낙찰받았어요! WakeAgain wakeagain.com";
  }

  function shareImage(cert) {
    var canvas = drawCanvas(cert);
    canvas.toBlob(function (blob) {
      if (!blob) return;
      var stem = cert.file_stem || "WakeAgain-확인서";
      var file = new File([blob], stem + ".png", { type: "image/png" });
      var text = shareCardText(cert);
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator
          .share({ files: [file], title: "WakeAgain", text: text })
          .catch(function (err) {
            if (err && err.name === "AbortError") return;
          });
        return;
      }
      // Desktop / unsupported fallback: download + open X compose intent
      var a = document.createElement("a");
      var href = URL.createObjectURL(blob);
      a.href = href;
      a.download = stem + ".png";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () {
        URL.revokeObjectURL(href);
      }, 2000);
      window.open(
        "https://twitter.com/intent/tweet?text=" + encodeURIComponent(text),
        "_blank",
        "noopener"
      );
    }, "image/png");
  }

  function show(cert) {
    if (!cert || !cert.doc_id) return;
    ensureStyles();
    var root = document.getElementById(ROOT_ID);
    if (!root) {
      root = document.createElement("div");
      root.id = ROOT_ID;
      root.setAttribute("role", "dialog");
      root.setAttribute("aria-modal", "true");
      document.body.appendChild(root);
    }
    root.hidden = false;
    root.innerHTML =
      '<div class="wa-cert-panel">' +
      renderCardHtml(cert) +
      '<div class="wa-cert-actions">' +
      '<button type="button" class="btn btn-primary" id="waCertSave">' +
      t("이미지로 저장", "Save image") +
      "</button>" +
      '<button type="button" class="btn btn-ghost" id="waCertShare">' +
      t("공유하기", "Share") +
      "</button>" +
      '<button type="button" class="btn btn-ghost" id="waCertClose">' +
      t("닫기", "Close") +
      "</button>" +
      "</div></div>";

    root.querySelector("#waCertClose").addEventListener("click", close);
    root.querySelector("#waCertSave").addEventListener("click", function () {
      downloadPng(cert);
    });
    root.querySelector("#waCertShare").addEventListener("click", function () {
      shareImage(cert);
    });
    root.addEventListener("click", function (e) {
      if (e.target === root) close();
    });
  }

  /**
   * Fetch and show. kind: award | complete | auto
   * autoOpenKey: sessionStorage key to only auto-open once
   */
  async function openFromApi(projectId, kind, opts) {
    opts = opts || {};
    var api = global.WakeAgainAPI;
    if (!api || !api.isLoggedIn || !api.isLoggedIn()) {
      location.href = "/app/#login";
      return null;
    }
    var sk = opts.autoOpenKey;
    if (sk && sessionStorage.getItem(sk) === "1" && opts.skipIfSeen) {
      return null;
    }
    try {
      var cert = await api.getDealCertificate(projectId, kind || "auto");
      show(cert);
      if (sk) sessionStorage.setItem(sk, "1");
      return cert;
    } catch (e) {
      if (opts.silent) return null;
      alert((e && e.message) || t("확인서를 열 수 없습니다.", "Could not open confirmation."));
      return null;
    }
  }

  global.WakeAgainDealCertificate = {
    show: show,
    close: close,
    openFromApi: openFromApi,
    downloadPng: downloadPng,
    shareImage: shareImage,
  };
})(window);
