"""PortOne V2 payment integration (test/live).

Flow (per PLATFORM.md §B — PG required for ops, no pre-PG fallback):
  1. Buyer requests payment for an awaiting_payment deal -> request_payment_for_deal()
     stores a fresh pg_payment_id on the project row and returns the params the
     frontend passes to PortOne Browser SDK's PortOne.requestPayment().
  2. After the SDK redirect/callback resolves, the frontend calls
     POST /api/v1/payments/verify with the paymentId. The server re-verifies
     directly against PortOne's server API (never trusts the client-reported
     status) and, if paid, calls db.mark_deal_paid().
  3. PortOne also fires a webhook (Standard Webhooks format) at
     POST /api/v1/payments/webhook as a backup path — same verify+mark_deal_paid
     logic, idempotent (mark_deal_paid no-ops if already paid).
"""

from __future__ import annotations

import base64
import hmac
import json
import os
import secrets
import time
from hashlib import sha256
from typing import Any

import httpx

PORTONE_API_BASE = os.environ.get("PORTONE_API_BASE", "https://api.portone.io").rstrip("/")
WEBHOOK_TOLERANCE_SEC = 300  # reject webhook timestamps older/newer than 5 minutes

# PayPal은 KRW를 받지 않는다 — 2026-08-25 실측으로 확인:
#   "결제 초기화에 실패하였습니다. 페이팔에서 지원하지 않는 화폐(CURRENCY_KRW)입니다."
# 그래서 해외 채널은 USD로 청구한다. 원장·수수료는 KRW 그대로다(docs/GLOBAL.md).
PAYPAL_CURRENCY = "USD"

# PortOne V2는 금액을 **해당 통화의 최소 단위(minor unit)** 정수로 받는다.
# KRW는 1배, USD는 100배(센트). 출처: PortOne requestPayment 요청 형식 문서.
CURRENCY_MINOR_UNIT = {"KRW": 1, "USD": 100, "JPY": 1}

# ⚠️ global_config._fx()의 WA_FX_USD는 "표시용, 정산용 아님"으로 명시돼 있다.
# 실제로 돈을 청구하는 값이라 별도 환경변수로 분리한다. 미설정 시에만 표시용으로 폴백한다.
DEFAULT_PAYPAL_FX_KRW_PER_USD = 1350.0


class PortOnePaymentError(Exception):
    """Raised when PortOne verification fails or a payment doesn't match the deal."""


def _store_id() -> str:
    return (os.environ.get("PORTONE_STORE_ID") or "").strip()


def _channel_key() -> str:
    return (os.environ.get("PORTONE_CHANNEL_KEY") or "").strip()


def _api_secret() -> str:
    return (os.environ.get("PORTONE_API_SECRET") or "").strip()


def _webhook_secret() -> str:
    return (os.environ.get("PORTONE_WEBHOOK_SECRET") or "").strip()


def _paypal_channel_key() -> str:
    return (os.environ.get("PORTONE_CHANNEL_KEY_PAYPAL") or "").strip()


def portone_enabled() -> bool:
    return bool(_store_id() and _channel_key() and _api_secret())


def paypal_enabled() -> bool:
    return bool(_store_id() and _paypal_channel_key() and _api_secret())


def portone_public_config() -> dict[str, Any]:
    """Safe to expose to the frontend — store id / channel key are not secrets."""
    return {
        "enabled": portone_enabled(),
        "store_id": _store_id(),
        "channel_key": _channel_key(),
        "paypal_enabled": paypal_enabled(),
        "paypal_channel_key": _paypal_channel_key(),
    }


def is_paypal_payment(payment: dict[str, Any]) -> bool:
    """True if a verified PortOne payment went through the PayPal channel."""
    key = _paypal_channel_key()
    if not key:
        return False
    used_key = ((payment.get("channel") or {}).get("key")) or ""
    return used_key == key


def new_payment_id(project_id: int) -> str:
    return f"wa-{int(project_id)}-{secrets.token_hex(6)}"


def build_payment_request(
    *,
    payment_id: str,
    order_name: str,
    total_amount: int,
    buyer_name: str,
    buyer_email: str | None = None,
    buyer_phone: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Params for the frontend's PortOne.requestPayment() call (V2 Browser SDK).

    반환값은 PayPal 쪽과 같은 `(params, charge)` 모양이다. 국내 카드는 환산이 없으므로
    charge 는 KRW 원금 그대로다.
    """
    if not portone_enabled():
        raise PortOnePaymentError("PortOne not configured (store id / channel key / api secret)")
    customer: dict[str, Any] = {"fullName": buyer_name}
    if buyer_email:
        customer["email"] = buyer_email
    if buyer_phone:
        customer["phoneNumber"] = buyer_phone
    params = {
        "storeId": _store_id(),
        "channelKey": _channel_key(),
        "paymentId": payment_id,
        "orderName": order_name[:100],
        "totalAmount": int(total_amount),
        "currency": "KRW",
        "payMethod": "CARD",
        "customer": customer,
    }
    charge = {
        "amount": int(total_amount),
        "currency": "KRW",
        "display": format_minor_amount(int(total_amount), "KRW"),
        "source_amount_krw": int(total_amount),
        "fx_krw_per_usd": None,
    }
    return params, charge


def build_paypal_payment_request(
    *,
    payment_id: str,
    order_name: str,
    total_amount: int,
    buyer_name: str,
    buyer_email: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Params for the frontend's PortOne.loadPaymentUI() call (uiType PAYPAL_SPB).

    Unlike the card flow (requestPayment popup), PayPal SPB renders an embedded
    button into a container div on the page — see public/project.html's
    paypalPayBox handling.

    STC (Seller Transaction Confirmation) risk-signal fields: PayPal requires
    these via a bypass.paypal_v2 object for "고위험 산업" merchants (used-goods /
    digital-goods marketplaces — WakeAgain is both), per PortOne's onboarding
    email (2026-08-11). The exact field spec lives in PortOne's STC PDF guide,
    which is image-only (not machine-readable) as of this writing — confirm the
    precise field names with the PG contract contact once they reach out, then
    fill in _paypal_stc_bypass() below. Shipping without full STC fields is not
    blocking (PortOne recommends but the API only *requires* one bypass field),
    but seller-protection coverage on disputed charges may be narrower until then.

    `total_amount` 는 **KRW 낙찰가**로 받는다. PayPal은 KRW를 거절하므로
    (2026-08-25 실측: "지원하지 않는 화폐(CURRENCY_KRW)") 여기서 USD 센트로 환산한다.

    반환값은 `(params, charge)` 두 개다:
      params — 프런트가 loadPaymentUI()에 그대로 넘기는 값
      charge — 실제 청구액·통화·환율. **호출자가 DB에 저장해야 한다** —
               결제 검증(assert_payment_paid)이 KRW가 아니라 이 값과 대조해야 하기 때문이다.
    """
    if not paypal_enabled():
        raise PortOnePaymentError("PayPal channel not configured (channel key / store id / api secret)")
    customer: dict[str, Any] = {"fullName": buyer_name}
    if buyer_email:
        customer["email"] = buyer_email
    cents, rate = krw_to_paypal_charge(total_amount)
    params = {
        "uiType": "PAYPAL_SPB",
        "storeId": _store_id(),
        "channelKey": _paypal_channel_key(),
        "paymentId": payment_id,
        "orderName": order_name[:100],
        "totalAmount": cents,
        "currency": f"CURRENCY_{PAYPAL_CURRENCY}",
        "customer": customer,
        "bypass": _paypal_stc_bypass(order_name),
    }
    charge = {
        "amount": cents,
        "currency": PAYPAL_CURRENCY,
        "display": format_minor_amount(cents, PAYPAL_CURRENCY),
        "source_amount_krw": int(total_amount),
        "fx_krw_per_usd": rate,
    }
    return params, charge


def paypal_fx_krw_per_usd() -> float:
    """PayPal 청구에 쓸 환율 (1 USD 당 원). 돈이 오가는 값이라 표시용과 분리한다."""
    raw = os.environ.get("WA_PAYPAL_FX_USD") or os.environ.get("WA_FX_USD") or ""
    try:
        rate = float(raw)
    except ValueError:
        rate = 0.0
    if rate <= 0:
        rate = DEFAULT_PAYPAL_FX_KRW_PER_USD
    return rate


def krw_to_paypal_charge(krw_amount: int) -> tuple[int, float]:
    """KRW 낙찰가를 PayPal에 청구할 (USD 센트, 적용 환율)로 바꾼다.

    센트 미만은 **올림**한다. 내림하면 환산 손실이 판매자 정산분에서 나가고,
    올림해도 구매자 부담 증가는 1센트 미만이다.
    """
    krw = int(krw_amount)
    if krw <= 0:
        raise PortOnePaymentError(f"invalid charge amount: {krw_amount}")
    rate = paypal_fx_krw_per_usd()
    minor = CURRENCY_MINOR_UNIT["USD"]
    cents = -(-(krw * minor) // int(round(rate)))  # ceil division
    if cents <= 0:
        raise PortOnePaymentError("converted PayPal amount rounded to zero")
    return int(cents), rate


def format_minor_amount(amount: int, currency: str) -> str:
    """로그·UI용 사람이 읽는 금액 (USD 600 -> '6.00 USD')."""
    unit = CURRENCY_MINOR_UNIT.get(currency.upper(), 1)
    if unit == 1:
        return f"{int(amount):,} {currency.upper()}"
    return f"{int(amount) / unit:,.2f} {currency.upper()}"


def _paypal_stc_bypass(order_name: str) -> dict[str, Any]:
    """Best-effort STC risk-signal payload — see build_paypal_payment_request docstring."""
    return {
        "paypal_v2": {
            "item_category": "DIGITAL_GOODS",
            "item_description": order_name[:127],
        }
    }


def fetch_payment(payment_id: str, *, timeout: float = 15.0) -> dict[str, Any]:
    """Server-to-server lookup of a payment's real status. Never trust client input."""
    secret = _api_secret()
    if not secret:
        raise PortOnePaymentError("PORTONE_API_SECRET not set")
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(
                f"{PORTONE_API_BASE}/payments/{payment_id}",
                headers={"Authorization": f"PortOne {secret}"},
            )
    except httpx.HTTPError as e:
        raise PortOnePaymentError(f"PortOne API unreachable: {e}") from e
    if r.status_code == 404:
        raise PortOnePaymentError("payment not found")
    if r.status_code >= 400:
        raise PortOnePaymentError(f"PortOne API error {r.status_code}: {r.text[:300]}")
    return r.json()


def assert_payment_paid(
    payment: dict[str, Any],
    *,
    expected_amount: int,
    expected_currency: str | None = None,
) -> None:
    """결제가 실제로 완료됐고 금액·통화가 우리가 청구한 것과 같은지 확인한다.

    통화까지 보는 이유: PayPal은 USD 센트로 청구하므로 KRW 낙찰가와 숫자만 비교하면
    엉뚱한 통화의 같은 숫자를 통과시킬 수 있다. 예) 300,000 KRW 청구 건에
    300,000 센트(=3,000 USD) 결제가 들어와도 금액만 보면 일치한다.
    """
    status = (payment.get("status") or "").upper()
    if status != "PAID":
        raise PortOnePaymentError(f"payment not completed (status={status or 'unknown'})")
    paid_amount = int(((payment.get("amount") or {}).get("total")) or 0)
    if paid_amount != int(expected_amount):
        raise PortOnePaymentError(
            f"paid amount mismatch: expected {expected_amount}, got {paid_amount}"
        )
    if expected_currency:
        # PortOne은 "KRW" 또는 "CURRENCY_KRW" 형태로 돌려줄 수 있다 — 접두사를 떼고 본다
        paid_currency = str(payment.get("currency") or "").upper().replace("CURRENCY_", "")
        want = expected_currency.upper().replace("CURRENCY_", "")
        if paid_currency and paid_currency != want:
            raise PortOnePaymentError(
                f"paid currency mismatch: expected {want}, got {paid_currency}"
            )


def verify_webhook(*, raw_body: bytes, headers: dict[str, str]) -> dict[str, Any]:
    """Standard Webhooks signature check. Returns the parsed JSON payload on success."""
    secret_raw = _webhook_secret()
    if not secret_raw:
        raise PortOnePaymentError("PORTONE_WEBHOOK_SECRET not set")
    webhook_id = headers.get("webhook-id") or ""
    webhook_ts = headers.get("webhook-timestamp") or ""
    webhook_sig = headers.get("webhook-signature") or ""
    if not (webhook_id and webhook_ts and webhook_sig):
        raise PortOnePaymentError("missing webhook signature headers")
    try:
        ts = int(webhook_ts)
    except ValueError as e:
        raise PortOnePaymentError("bad webhook timestamp") from e
    if abs(time.time() - ts) > WEBHOOK_TOLERANCE_SEC:
        raise PortOnePaymentError("webhook timestamp outside tolerance")

    secret = secret_raw[len("whsec_") :] if secret_raw.startswith("whsec_") else secret_raw
    secret_bytes = base64.b64decode(secret)
    signed_content = f"{webhook_id}.{webhook_ts}.{raw_body.decode('utf-8')}".encode("utf-8")
    expected = base64.b64encode(hmac.new(secret_bytes, signed_content, sha256).digest()).decode()

    provided_sigs = [p.split(",", 1)[1] for p in webhook_sig.split() if "," in p]
    if not any(hmac.compare_digest(expected, sig) for sig in provided_sigs):
        raise PortOnePaymentError("webhook signature mismatch")

    return json.loads(raw_body.decode("utf-8"))
