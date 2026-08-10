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
) -> dict[str, Any]:
    """Params for the frontend's PortOne.requestPayment() call (V2 Browser SDK)."""
    if not portone_enabled():
        raise PortOnePaymentError("PortOne not configured (store id / channel key / api secret)")
    customer: dict[str, Any] = {"fullName": buyer_name}
    if buyer_email:
        customer["email"] = buyer_email
    if buyer_phone:
        customer["phoneNumber"] = buyer_phone
    return {
        "storeId": _store_id(),
        "channelKey": _channel_key(),
        "paymentId": payment_id,
        "orderName": order_name[:100],
        "totalAmount": int(total_amount),
        "currency": "KRW",
        "payMethod": "CARD",
        "customer": customer,
    }


def build_paypal_payment_request(
    *,
    payment_id: str,
    order_name: str,
    total_amount: int,
    buyer_name: str,
    buyer_email: str | None = None,
) -> dict[str, Any]:
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
    """
    if not paypal_enabled():
        raise PortOnePaymentError("PayPal channel not configured (channel key / store id / api secret)")
    customer: dict[str, Any] = {"fullName": buyer_name}
    if buyer_email:
        customer["email"] = buyer_email
    return {
        "uiType": "PAYPAL_SPB",
        "storeId": _store_id(),
        "channelKey": _paypal_channel_key(),
        "paymentId": payment_id,
        "orderName": order_name[:100],
        "totalAmount": int(total_amount),
        "currency": "CURRENCY_KRW",
        "customer": customer,
        "bypass": _paypal_stc_bypass(order_name),
    }


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


def assert_payment_paid(payment: dict[str, Any], *, expected_amount: int) -> None:
    status = (payment.get("status") or "").upper()
    if status != "PAID":
        raise PortOnePaymentError(f"payment not completed (status={status or 'unknown'})")
    paid_amount = int(((payment.get("amount") or {}).get("total")) or 0)
    if paid_amount != int(expected_amount):
        raise PortOnePaymentError(
            f"paid amount mismatch: expected {expected_amount}, got {paid_amount}"
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
