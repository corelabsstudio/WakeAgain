"""Global / multi-region readiness — config surface for clients.

Settlement ledger stays KRW until multi-PG; display currencies are for UX only.
"""
from __future__ import annotations

import os

# Supported UI locales (BCP-47)
LOCALES = (
    {"code": "ko", "label": "한국어", "label_en": "Korean", "dir": "ltr", "default": True},
    {"code": "en", "label": "English", "label_en": "English", "dir": "ltr", "default": False},
)

# Accounting currency (server / DB amounts are this unit until multi-currency ledger)
BASE_CURRENCY = (os.environ.get("WA_BASE_CURRENCY") or "KRW").upper()

# Display currencies (client formatMoney). Rates are approximate display-only.
DISPLAY_CURRENCIES = (
    {
        "code": "KRW",
        "symbol": "₩",
        "decimals": 0,
        "locale": "ko-KR",
        "label": "Korean Won",
    },
    {
        "code": "USD",
        "symbol": "$",
        "decimals": 0,
        "locale": "en-US",
        "label": "US Dollar",
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
        "code": "KR",
        "label": "Korea",
        "label_ko": "한국",
        "default_locale": "ko",
        "default_currency": "KRW",
        "timezone": "Asia/Seoul",
        "age_gate_years": 14,
        "legal_note": "Primary market; Korean e-commerce intermediary rules apply when operating in KR.",
    },
    {
        "code": "GLOBAL",
        "label": "Global",
        "label_ko": "글로벌",
        "default_locale": "en",
        "default_currency": "USD",
        "timezone": "UTC",
        "age_gate_years": 16,
        "legal_note": "International browsing ready; payment rails & local compliance per market TBD.",
    },
)


def public_global_config() -> dict:
    default_locale = (os.environ.get("WA_DEFAULT_LOCALE") or "ko").lower()
    if default_locale not in {x["code"] for x in LOCALES}:
        default_locale = "ko"
    return {
        "enabled": True,
        "default_locale": default_locale,
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
