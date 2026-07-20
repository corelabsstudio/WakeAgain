/**
 * sell / buy pre-registration forms — uses WakeAgainAPI when available.
 */
async function submitForm(form) {
  const fd = new FormData(form);
  const assets = fd.getAll("asset");
  const payload = Object.fromEntries(fd.entries());
  payload.assets = assets;
  delete payload.asset;
  delete payload.rights_ok;
  delete payload.terms_ok;
  delete payload.fee_ack;

  // numeric fields
  if (payload.price_start === "") delete payload.price_start;
  else if (payload.price_start != null) payload.price_start = Number(payload.price_start);
  if (payload.price_buy_now === "") delete payload.price_buy_now;
  else if (payload.price_buy_now != null) payload.price_buy_now = Number(payload.price_buy_now);

  const api = window.WakeAgainAPI;
  if (api) {
    // buy: prefer /interest for unified buyer list; sell: legacy leads
    if (payload.type === "buy") {
      return api.createInterest({
        email: payload.contact,
        name: payload.name || "",
        category: payload.category,
        budget: payload.budget || "",
        note: payload.note || "",
      });
    }
    return api.createLead(payload);
  }

  const res = await fetch("/api/leads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let msg = "submit failed";
    try {
      const j = await res.json();
      if (j && j.detail) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      const t = await res.text();
      if (t) msg = t;
    }
    throw new Error(msg);
  }
  return res.json();
}

function wire(id) {
  const form = document.getElementById(id);
  if (!form) return;
  const ok = document.getElementById("ok");
  const errBox = document.getElementById("formError");

  // prefill email if logged in
  const api = window.WakeAgainAPI;
  if (api && api.isLoggedIn()) {
    const u = api.getUser();
    const contact = form.querySelector("#contact");
    if (u && contact && !contact.value) contact.value = u.email || "";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (errBox) {
      errBox.hidden = true;
      errBox.textContent = "";
    }
    if (!form.reportValidity()) return;

    const btn = form.querySelector('button[type="submit"]');
    const prev = btn ? btn.textContent : "";
    const t =
      window.WakeAgainI18n && window.WakeAgainI18n.t
        ? window.WakeAgainI18n.t.bind(window.WakeAgainI18n)
        : (k) => k;
    if (btn) {
      btn.disabled = true;
      btn.textContent = t("common.sending");
    }
    try {
      await submitForm(form);
      form.hidden = true;
      if (ok) {
        ok.hidden = false;
        ok.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } catch (err) {
      const msg =
        t("common.submit_fail") +
        (err && err.message ? "\n" + err.message : "");
      if (errBox) {
        errBox.hidden = false;
        errBox.textContent = msg;
      } else {
        alert(msg);
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = prev;
      }
    }
  });
}

wire("sellForm");
wire("buyForm");

/* Start-price + classification guide by status (sell form) */
(async function sellPricingGuide() {
  const statusEl = document.getElementById("status");
  const priceEl = document.getElementById("price_start");
  const guide = document.getElementById("sellPriceGuide");
  const hint = document.getElementById("sellPriceHint");
  const criteria = document.getElementById("sellStatusCriteria");
  if (!statusEl || !priceEl) return;
  let bands = null;
  try {
    if (window.WakeAgainAPI) bands = await window.WakeAgainAPI.pricing();
  } catch (e) {
    return;
  }
  function t(key, vars) {
    if (window.WakeAgainI18n && window.WakeAgainI18n.t) {
      return window.WakeAgainI18n.t(key, vars);
    }
    return key;
  }
  function money(n) {
    if (window.WakeAgainI18n && window.WakeAgainI18n.formatMoney) {
      return window.WakeAgainI18n.formatMoney(n);
    }
    return "₩" + Number(n).toLocaleString("ko-KR");
  }
  function renderCriteria(band) {
    if (!criteria || !band) return;
    criteria.hidden = false;
    const yes = (band.criteria_yes || [])
      .slice(0, 4)
      .map((line) => "<li>" + line + "</li>")
      .join("");
    const no = (band.criteria_no || [])
      .slice(0, 3)
      .map((line) => "<li>" + line + "</li>")
      .join("");
    criteria.innerHTML =
      "<p class='sc-when'>" +
      (band.when || band.blurb || "") +
      "</p>" +
      (yes
        ? "<div class='sc-label'>" + t("sell.criteria_yes") + "</div><ul>" + yes + "</ul>"
        : "") +
      (no
        ? "<div class='sc-label'>" + t("sell.criteria_no") + "</div><ul>" + no + "</ul>"
        : "") +
      (band.demo_expect
        ? "<div class='sc-label'>" +
          t("sell.criteria_demo") +
          "</div><p class='sc-when' style='margin:0'>" +
          band.demo_expect +
          "</p>"
        : "");
  }
  function apply(force) {
    if (!bands) return;
    const st = statusEl.value;
    const band = (bands.statuses || []).find(
      (s) => s.status === st || s.key === st || s.label === st
    );
    if (!band) {
      if (guide) guide.textContent = t("sell.price_pick_status");
      if (criteria) criteria.hidden = true;
      return;
    }
    renderCriteria(band);
    if (guide) {
      guide.innerHTML =
        "<strong>" +
        (band.label || band.status) +
        "</strong> — " +
        band.blurb +
        " · " +
        t("sell.price_suggest") +
        " <strong>" +
        money(band.suggest) +
        "</strong> (" +
        t("sell.price_min") +
        " " +
        money(band.min) +
        ")";
    }
    if (hint) {
      hint.textContent = (band.examples || "") + " · " + t("sell.price_server_check");
    }
    priceEl.min = band.min;
    priceEl.step = band.min_increment;
    if (force || !priceEl.value) priceEl.value = band.suggest;
    priceEl.placeholder = t("sell.price_ph_suggest", { n: band.suggest });
  }
  statusEl.addEventListener("change", () => apply(true));
  document.addEventListener("wa:langchange", () => {
    if (statusEl.value) apply(false);
  });
  if (statusEl.value) apply(true);
})();
