# WakeAgain — Global readiness

**Status:** UI/locale foundation ready (KO + EN). Settlement remains **KRW** until multi-region PG.

## What is ready

| Area | Status |
|------|--------|
| UI language KO / EN | `i18n.js` + `i18n-messages.js` · `data-i18n` · **KO\|EN on all major pages** |
| Landing full copy | Hero → CTA → footer translated |
| App shell | Auth + trust banners + list badges + fees via `t()` in `app.js` |
| Diagnose flow | All 5 questions + options + result CTAs |
| Display currency KRW / USD / EUR | Display-only FX in `/api/v1/config` → `global.fx_display_only` |
| Regions KR + GLOBAL | Config surface for age gate / timezone notes |
| Server timestamps | UTC (existing) |
| API config | `global` block in `GET /api/v1/config` |
| English legal stub | `/legal/terms.en.html` (summary · KR terms still controlling until counsel) |

### How full translation works
1. User taps **EN** (any page with lang switch) → `localStorage.wa_lang=en`
2. `WakeAgainI18n.apply()` rewrites every `[data-i18n]` node
3. Dynamic UI (`app.js`, listings) calls `t("key")` / rebuilds on `wa:langchange`
4. Add new strings: extend `_gen_i18n_extra.py` → `python _gen_i18n_extra.py`

## What is not ready (by design)

- Multi-currency **settlement / PG**
- Per-country tax / tax ID collection
- Full EN translation of every page (app deep screens, admin, long legal)
- Geo-IP forced locale (we prefer user choice + browser detect)

## Env overrides

```
WA_DEFAULT_LOCALE=ko|en
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
