# -*- coding: utf-8 -*-
"""페이팔 KRW→USD 환산 회귀 테스트 (2026-08-25).

배경: PortOne이 "페이팔에서 지원하지 않는 화폐(CURRENCY_KRW)"로 결제를 거절했다.
원인은 payments.py가 KRW를 그대로 보낸 것. USD 센트로 환산하도록 고쳤고,
여기서 ①환산이 맞는지 ②검증이 통화까지 보는지 ③원장은 KRW로 남는지를 잠근다.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("PORTONE_STORE_ID", "store-test")
os.environ.setdefault("PORTONE_CHANNEL_KEY", "channel-card-test")
os.environ.setdefault("PORTONE_API_SECRET", "secret-test")
os.environ.setdefault("PORTONE_CHANNEL_KEY_PAYPAL", "channel-paypal-test")
os.environ["WA_PAYPAL_FX_USD"] = "1350"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wakeagain import payments  # noqa: E402

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


def main() -> int:
    print("\n=== PayPal 통화 환산 ===")

    cents, rate = payments.krw_to_paypal_charge(1_350_000)
    check("1,350,000원 -> 100,000센트(=$1,000)", cents == 100_000 and rate == 1350.0, f"{cents} @ {rate}")

    cents, _ = payments.krw_to_paypal_charge(300_000)
    # 300000*100/1350 = 22222.22 -> 올림 22223
    check("300,000원 -> 22,223센트 (센트 미만 올림)", cents == 22_223, str(cents))

    check("표시 포맷", payments.format_minor_amount(22_223, "USD") == "222.23 USD",
          payments.format_minor_amount(22_223, "USD"))
    check("KRW는 최소단위 1배", payments.format_minor_amount(300_000, "KRW") == "300,000 KRW",
          payments.format_minor_amount(300_000, "KRW"))

    try:
        payments.krw_to_paypal_charge(0)
        check("0원은 거부", False, "예외가 안 났음")
    except payments.PortOnePaymentError:
        check("0원은 거부", True)

    print("\n=== 요청 파라미터 ===")
    params, charge = payments.build_paypal_payment_request(
        payment_id="pay-1", order_name="테스트 매물", total_amount=300_000, buyer_name="구매자",
    )
    check("currency = CURRENCY_USD (KRW 아님)", params["currency"] == "CURRENCY_USD", params["currency"])
    check("totalAmount = 센트", params["totalAmount"] == 22_223, str(params["totalAmount"]))
    check("uiType 유지", params["uiType"] == "PAYPAL_SPB", params["uiType"])
    check("charge에 원장 KRW 보존", charge["source_amount_krw"] == 300_000, str(charge["source_amount_krw"]))
    check("charge.currency = USD", charge["currency"] == "USD", charge["currency"])

    params_c, charge_c = payments.build_payment_request(
        payment_id="pay-2", order_name="테스트 매물", total_amount=300_000, buyer_name="구매자",
    )
    check("국내 카드는 KRW 그대로", params_c["currency"] == "KRW" and params_c["totalAmount"] == 300_000,
          f'{params_c["currency"]} {params_c["totalAmount"]}')
    check("카드 charge도 KRW", charge_c["currency"] == "KRW" and charge_c["fx_krw_per_usd"] is None)

    print("\n=== 검증 (assert_payment_paid) ===")
    paid_usd = {"status": "PAID", "amount": {"total": 22_223}, "currency": "CURRENCY_USD"}
    try:
        payments.assert_payment_paid(paid_usd, expected_amount=22_223, expected_currency="USD")
        check("USD 정상 결제 통과", True)
    except payments.PortOnePaymentError as e:
        check("USD 정상 결제 통과", False, str(e))

    # 이게 이번 수정의 핵심 방어: 금액 숫자는 같은데 통화가 다른 결제
    trap = {"status": "PAID", "amount": {"total": 300_000}, "currency": "CURRENCY_USD"}
    try:
        payments.assert_payment_paid(trap, expected_amount=300_000, expected_currency="KRW")
        check("300,000 KRW 청구에 300,000센트 결제 -> 거부", False, "통과해버림")
    except payments.PortOnePaymentError:
        check("300,000 KRW 청구에 300,000센트 결제 -> 거부", True)

    try:
        payments.assert_payment_paid(paid_usd, expected_amount=99_999, expected_currency="USD")
        check("금액 불일치 거부", False, "통과해버림")
    except payments.PortOnePaymentError:
        check("금액 불일치 거부", True)

    # 통화 정보가 없는 응답은 기존처럼 금액만 본다 (하위호환)
    try:
        payments.assert_payment_paid(
            {"status": "PAID", "amount": {"total": 300_000}}, expected_amount=300_000, expected_currency="KRW"
        )
        check("통화 필드 없는 응답은 금액만 검사", True)
    except payments.PortOnePaymentError as e:
        check("통화 필드 없는 응답은 금액만 검사", False, str(e))

    print("\n=== 환율 설정 ===")
    os.environ["WA_PAYPAL_FX_USD"] = "1400"
    check("WA_PAYPAL_FX_USD 반영", payments.paypal_fx_krw_per_usd() == 1400.0)
    os.environ["WA_PAYPAL_FX_USD"] = "이상한값"
    check("잘못된 값이면 기본값", payments.paypal_fx_krw_per_usd() == payments.DEFAULT_PAYPAL_FX_KRW_PER_USD)
    os.environ["WA_PAYPAL_FX_USD"] = "1350"

    bad = [n for n, ok, _ in results if not ok]
    print(f"\n=== {len(results) - len(bad)}/{len(results)} 통과 ===")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
