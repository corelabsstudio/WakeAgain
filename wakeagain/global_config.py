"""Global / multi-region readiness — config surface for clients.

Settlement ledger stays KRW until multi-PG; display currencies are for UX only.
"""
from __future__ import annotations

import os

# Supported UI locales (BCP-47) — global-first default is English
LOCALES = (
    {"code": "en", "label": "English", "label_en": "English", "dir": "ltr", "default": True},
    {"code": "ko", "label": "한국어", "label_en": "Korean", "dir": "ltr", "default": False},
)

# Accounting currency (server / DB amounts are this unit until multi-currency ledger)
BASE_CURRENCY = (os.environ.get("WA_BASE_CURRENCY") or "KRW").upper()

# Display currencies (client formatMoney). Rates are approximate display-only.
# Global-first: USD is the default display currency; KRW remains opt-in.
DISPLAY_CURRENCIES = (
    {
        "code": "USD",
        "symbol": "$",
        "decimals": 0,
        "locale": "en-US",
        "label": "US Dollar",
    },
    {
        "code": "KRW",
        "symbol": "₩",
        "decimals": 0,
        "locale": "ko-KR",
        "label": "Korean Won",
    },
    {
        "code": "EUR",
        "symbol": "€",
        "decimals": 0,
        "locale": "en-EU",
        "label": "Euro",
    },
)

# Rough display FX (KRW per 1 unit of currency). Not for settlement.
# Override with env WA_FX_USD=1350 etc.
def _fx() -> dict[str, float]:
    return {
        "KRW": 1.0,
        "USD": float(os.environ.get("WA_FX_USD") or "1350"),
        "EUR": float(os.environ.get("WA_FX_EUR") or "1450"),
    }


REGIONS = (
    {
        "code": "GLOBAL",
        "label": "Global",
        "label_ko": "글로벌",
        "default_locale": "en",
        "default_currency": "USD",
        "timezone": "UTC",
        "age_gate_years": 16,
        "legal_note": "Primary acquisition market (global-first launch). Payment rails & local compliance per market TBD.",
    },
    {
        "code": "KR",
        "label": "Korea",
        "label_ko": "한국",
        "default_locale": "ko",
        "default_currency": "KRW",
        "timezone": "Asia/Seoul",
        "age_gate_years": 14,
        "legal_note": "Domestic compliance surface; Korean e-commerce intermediary rules apply when operating in KR.",
    },
)


def public_global_config() -> dict:
    # Global-first launch: English + USD display default (settlement ledger stays KRW)
    default_locale = (os.environ.get("WA_DEFAULT_LOCALE") or "en").lower()
    if default_locale not in {x["code"] for x in LOCALES}:
        default_locale = "en"
    default_display_currency = (os.environ.get("WA_DEFAULT_DISPLAY_CURRENCY") or "USD").upper()
    display_codes = {x["code"] for x in DISPLAY_CURRENCIES}
    if default_display_currency not in display_codes:
        default_display_currency = "USD"
    return {
        "enabled": True,
        "default_locale": default_locale,
        "default_display_currency": default_display_currency,
        "locales": list(LOCALES),
        "base_currency": BASE_CURRENCY,
        "display_currencies": list(DISPLAY_CURRENCIES),
        "fx_display_only": _fx(),
        "fx_note": "Display conversion only. Listing/settlement amounts are stored in base_currency until multi-currency PG.",
        "regions": list(REGIONS),
        "features": {
            "ui_i18n": True,
            "language_switcher": True,
            "currency_display_switch": True,
            "multi_currency_settlement": False,
            "geo_pricing": False,
        },
        "timezone_server": "UTC",
        "contact_email": "corelabs.studio@gmail.com",
    }
