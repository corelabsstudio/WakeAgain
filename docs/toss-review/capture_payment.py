# -*- coding: utf-8 -*-
"""토스 심사 6단계 — 카드 결제경로 캡처 (로컬 격리 서버).

setup_local_deal.py 가 만든 awaiting_payment 딜에 구매자로 로그인해서 캡처한다.

⚠️ 실제 PG 결제창은 현재 뜨지 않는다 (2026-08-25 실측):
   - 카드(토스 채널): PortOne 응답 "channelKey is not correct."
   - 페이팔:          "페이팔에서 지원하지 않는 화폐(CURRENCY_KRW)"
   그래서 여기서는 '결제 직전 화면'(결제 금액·결제수단 버튼)까지를 캡처한다.
   채널 문제가 풀리면 CLICK_PAY=True 로 두고 다시 돌리면 결제창까지 잡힌다.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
OUT = HERE / "shots"
INFO = json.loads((HERE / "_local_deal.json").read_text(encoding="utf-8"))
BASE = "http://127.0.0.1:8099"
CLICK_PAY = False


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="ko-KR")
        pg = ctx.new_page()

        pg.goto(f"{BASE}/app/#login", wait_until="load", timeout=60000)
        pg.wait_for_timeout(2500)
        pg.fill("#loginEmail", INFO["buyer_email"])
        pg.fill("#loginPass", INFO["password"])
        pg.click("#formLogin button[type=submit]")
        pg.wait_for_timeout(3500)
        print("  로그인 완료:", pg.url)

        pg.goto(INFO["url"], wait_until="load", timeout=60000)
        pg.wait_for_timeout(4500)
        pg.evaluate("document.querySelectorAll('#waCollectionNotice').forEach(n=>n.remove())")

        # 결제 금액과 결제수단 버튼이 한 화면에 들어오도록 결제 패널을 기준으로 잡는다
        pg.locator("#dealActions").first.scroll_into_view_if_needed()
        pg.wait_for_timeout(800)
        pg.evaluate("window.scrollBy(0, -260)")
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(OUT / "06_결제경로.png"))
        print("  [ok] 06_결제경로.png")

        pg.locator("#dealProtectBox").first.screenshot(path=str(OUT / "06b_결제패널.png"))
        print("  [ok] 06b_결제패널.png")

        if CLICK_PAY:
            pg.get_by_role("button", name="카드로 결제하기").first.click()
            pg.wait_for_timeout(8000)
            pg.screenshot(path=str(OUT / "06c_카드결제창.png"))
            print("  [ok] 06c_카드결제창.png")

        b.close()


if __name__ == "__main__":
    main()
