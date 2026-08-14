/* Floating private feedback widget — non-member guestbook, delivered to the operator only (never public). */
(function (global) {
  function t(key, fallback) {
    try {
      if (global.WakeAgainI18n) return global.WakeAgainI18n.t(key);
    } catch (e) {}
    return fallback;
  }

  function applyI18n(root) {
    try {
      if (global.WakeAgainI18n) global.WakeAgainI18n.apply(root);
    } catch (e) {}
  }

  function build() {
    var wrap = document.createElement("div");
    wrap.className = "fb-widget";
    wrap.innerHTML =
      '<button type="button" class="fb-widget-btn" id="fbOpenBtn" aria-haspopup="dialog" aria-expanded="false">' +
      '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M3 4.5A1.5 1.5 0 0 1 4.5 3h11A1.5 1.5 0 0 1 17 4.5v8A1.5 1.5 0 0 1 15.5 14H9l-3.8 3v-3H4.5A1.5 1.5 0 0 1 3 12.5v-8Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>' +
      '<span data-i18n="feedback.button">' + t("feedback.button", "피드백") + "</span>" +
      "</button>" +
      '<div class="fb-panel" id="fbPanel" role="dialog" aria-modal="false" aria-labelledby="fbTitle" hidden>' +
      '<div class="fb-panel-head">' +
      '<h3 id="fbTitle" data-i18n="feedback.title">' + t("feedback.title", "사이트 피드백") + "</h3>" +
      '<button type="button" class="fb-panel-close" id="fbCloseBtn" data-i18n-aria="feedback.close" aria-label="' + t("feedback.close", "닫기") + '">&times;</button>' +
      "</div>" +
      '<p class="fb-panel-desc" data-i18n="feedback.desc">' + t("feedback.desc", "회원이 아니어도 남길 수 있어요. 공개되지 않고 운영자에게만 전달됩니다.") + "</p>" +
      '<form id="fbForm" novalidate>' +
      '<textarea id="fbMessage" data-i18n-placeholder="feedback.placeholder" placeholder="' + t("feedback.placeholder", "둘러보면서 느낀 점, 불편한 점, 아이디어 무엇이든 좋아요.") + '"></textarea>' +
      '<input type="email" id="fbContact" autocomplete="email" data-i18n-placeholder="feedback.contact_placeholder" placeholder="' + t("feedback.contact_placeholder", "답장 받을 이메일 (선택)") + '" />' +
      '<input type="text" id="fbHp" name="company" class="fb-panel-hp" tabindex="-1" autocomplete="off" aria-hidden="true" />' +
      '<div class="fb-panel-actions">' +
      '<button type="submit" class="btn btn-primary btn-sm" id="fbSubmitBtn"><span data-i18n="feedback.submit">' + t("feedback.submit", "보내기") + "</span></button>" +
      "</div>" +
      '<p class="fb-panel-msg" id="fbMsg" hidden></p>' +
      "</form>" +
      "</div>";
    document.body.appendChild(wrap);
    return wrap;
  }

  function init() {
    if (document.querySelector(".fb-widget")) return;
    var wrap = build();
    var openBtn = wrap.querySelector("#fbOpenBtn");
    var panel = wrap.querySelector("#fbPanel");
    var closeBtn = wrap.querySelector("#fbCloseBtn");
    var form = wrap.querySelector("#fbForm");
    var msgEl = wrap.querySelector("#fbMsg");
    var submitBtn = wrap.querySelector("#fbSubmitBtn");

    applyI18n(wrap);
    document.addEventListener("wa:langchange", function () {
      applyI18n(wrap);
    });

    function open() {
      panel.hidden = false;
      openBtn.setAttribute("aria-expanded", "true");
      var ta = wrap.querySelector("#fbMessage");
      if (ta) ta.focus();
      document.addEventListener("click", onOutsideClick, true);
      document.addEventListener("keydown", onKeydown, true);
    }
    function close() {
      panel.hidden = true;
      openBtn.setAttribute("aria-expanded", "false");
      document.removeEventListener("click", onOutsideClick, true);
      document.removeEventListener("keydown", onKeydown, true);
    }
    function onOutsideClick(e) {
      if (!wrap.contains(e.target)) close();
    }
    function onKeydown(e) {
      if (e.key === "Escape") close();
    }

    openBtn.addEventListener("click", function () {
      if (panel.hidden) open();
      else close();
    });
    closeBtn.addEventListener("click", close);

    function showMsg(key, fallback, ok) {
      msgEl.hidden = false;
      msgEl.className = "fb-panel-msg " + (ok ? "is-ok" : "is-err");
      msgEl.textContent = t(key, fallback);
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var message = wrap.querySelector("#fbMessage").value.trim();
      var contact = wrap.querySelector("#fbContact").value.trim();
      var hp = wrap.querySelector("#fbHp").value.trim();
      if (!message) {
        showMsg("feedback.error_empty", "내용을 입력해주세요.", false);
        return;
      }
      submitBtn.disabled = true;
      msgEl.hidden = true;
      var lang = (global.WakeAgainI18n && global.WakeAgainI18n.getLang && global.WakeAgainI18n.getLang()) || "ko";
      var payload = {
        message: message,
        contact: contact,
        page: location.pathname,
        lang: lang,
        hp: hp,
      };
      var req = global.WakeAgainAPI && global.WakeAgainAPI.request
        ? global.WakeAgainAPI.request("/api/v1/feedback", { method: "POST", body: JSON.stringify(payload) })
        : fetch("/api/v1/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }).then(function (r) {
            if (!r.ok) throw new Error("failed");
            return r.json();
          });
      req
        .then(function () {
          showMsg("feedback.success", "감사합니다! 피드백이 전달됐어요.", true);
          form.reset();
          setTimeout(close, 1600);
        })
        .catch(function () {
          showMsg("feedback.error", "전송에 실패했어요. 잠시 후 다시 시도해주세요.", false);
        })
        .finally(function () {
          submitBtn.disabled = false;
        });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(typeof window !== "undefined" ? window : globalThis);
