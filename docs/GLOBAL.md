# WakeAgain — Global readiness

**Status:** Global-first launch surface (EN + USD). Settlement remains **KRW** until multi-region PG.

**Default (2026-08-10, global-first launch):**  
- **UI language:** English (`en`) by default. Browser `ko` / `ko-KR` → Korean. Manual KO/EN save wins (`localStorage.wa_lang`).  
- **Display currency:** **USD** by default for non-KO. First visit with `ko` seeds **KRW** until the user picks another currency (`localStorage.wa_currency`).  
- **HTML / OG defaults:** `lang="en"` + English Open Graph on the landing page.  
- **KR chrome:** Business registration block, KR phone numbers, Kakao button — visible only when locale is `ko` (`.wa-kr-only`).  
- **Typography:** Inter (global) · Pretendard/Noto when `data-wa-lang="ko"`.  
- Settlement ledger / PG amounts stay **KRW** until multi-currency payment rails.

**Ops note:** Real KR deals and Korean compliance still matter for settlement; marketing surface is global-first so international visitors do not land on a Korea-only product feel.

## What is ready

| Area | Status |
|------|--------|
| UI language KO / EN | `i18n.js` + `i18n-messages.js` · `data-i18n` · **KO\|EN on all major pages** |
| Landing full copy | Hero → CTA → footer translated |
| App shell | Auth + trust banners + list badges + fees via `t()` in `app.js` |
| Diagnose flow | All 5 questions + options + result CTAs |
| Display currency USD / KRW / EUR | Display-only FX in `/api/v1/config` → `global.fx_display_only` · **default USD** |
| Regions KR + GLOBAL | Config surface for age gate / timezone notes |
| Server timestamps | UTC (existing) |
| API config | `global` block in `GET /api/v1/config` (`default_locale=en`, `default_display_currency=USD`) |
| English legal stub | `/legal/terms.en.html` (summary · KR terms still controlling until counsel) |

### How full translation works
1. First visit: browser language → `ko` if Korean, else `en`. Manual KO/EN → `localStorage.wa_lang` (highest priority)
2. `WakeAgainI18n.apply()` rewrites every `[data-i18n]` node; `document.documentElement.lang` follows
3. Dynamic UI (`app.js`, listings) calls `t("key")` / rebuilds on `wa:langchange`
4. Display money uses `formatMoney` with default **USD** (saved currency wins)
5. Add new strings: extend `_gen_i18n_extra.py` → `python _gen_i18n_extra.py`

## What is not ready (by design)

- Multi-currency **settlement / PG**
- Per-country tax / tax ID collection
- Full EN translation of every page (app deep screens, admin, long legal)
- Geo-IP forced locale (we prefer user choice + browser detect)

## Env overrides

```
WA_DEFAULT_LOCALE=en|ko
WA_DEFAULT_DISPLAY_CURRENCY=USD|KRW|EUR
WA_BASE_CURRENCY=KRW
WA_FX_USD=1350
WA_FX_EUR=1450
```

## Client usage

```html
<script src="/js/i18n.js"></script>
<span data-i18n="nav.market"></span>
<strong data-money-krw="720000"></strong>
<select data-lang-switch><option value="ko">한국어</option><option value="en">English</option></select>
```

```js
WakeAgainI18n.setLang("en");
WakeAgainI18n.formatMoney(1500000); // respects display currency
```

## Next when expanding markets

1. EN copy pass for `/app` deep flows  
2. Local PG + escrow per region  
3. Counsel-reviewed EN terms / privacy  
4. Optional: store user `preferred_locale` on profile  
