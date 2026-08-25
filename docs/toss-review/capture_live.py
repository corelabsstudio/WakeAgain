"""토스페이먼츠 결제경로 심사 자료 — 라이브 화면 캡처 (2~5단계).

가이드(토스페이먼츠_홈페이지 결제경로 제작 가이드.pdf) 3페이지의 6단계 중
①표지는 make_cover.py, ⑥카드결제창은 capture_payment.py가 담당한다.
여기서는 라이브(wakeagain.com)에서 찍을 수 있는 것만 찍는다.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "shots"
BASE = "https://wakeagain.com"
VIEW = {"width": 1440, "height": 900}


def dismiss_overlays(page):
    """콜드스타트 안내 모달(#waCollectionNotice)이 전면을 덮어 캡처를 망친다."""
    try:
        btn = page.locator("#waCollectionNoticeClose")
        if btn.count() and btn.first.is_visible():
            btn.first.click()
            page.wait_for_timeout(600)
            return
    except Exception:
        pass
    try:
        page.evaluate(
            "document.querySelectorAll('#waCollectionNotice').forEach(function(n){n.remove()})"
        )
        page.wait_for_timeout(300)
    except Exception:
        pass


def hide_floating(page):
    """position:fixed/sticky 요소가 푸터 위에 겹쳐 사업자정보를 가린다.

    푸터 자체와 그 자손은 남기고, 화면에 떠 있는 것만 숨긴다.
    """
    page.evaluate(
        """
        (() => {
          const footer = document.querySelector('footer.site-footer');
          document.querySelectorAll('body *').forEach(el => {
            if (footer && (el === footer || footer.contains(el) || el.contains(footer))) return;
            const pos = getComputedStyle(el).position;
            if (pos === 'fixed' || pos === 'sticky') el.style.setProperty('display','none','important');
          });
        })()
        """
    )
    page.wait_for_timeout(400)


def shot(page, url, name, *, selector=None, full=False, wait=None, scroll=None):
    page.goto(url, wait_until="load", timeout=60000)
    # i18n·서비스워커가 로드 직후 한 번 더 내비게이션을 일으킨다 — 가라앉을 때까지 기다린다
    page.wait_for_timeout(2500)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    dismiss_overlays(page)
    if scroll:
        for _ in range(3):
            try:
                page.evaluate(scroll)
                break
            except Exception:
                page.wait_for_timeout(1500)
        page.wait_for_timeout(900)
    if wait:
        try:
            page.wait_for_selector(wait, timeout=15000)
        except Exception:
            print(f"   ! wait miss: {wait}")
    page.wait_for_timeout(900)
    target = page.locator(selector).first if selector else page
    target.screenshot(path=str(OUT / name)) if selector else page.screenshot(
        path=str(OUT / name), full_page=full
    )
    print(f"  [ok] {name}  <- {url}")


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport=VIEW, locale="ko-KR")

        print("2단계 · 하단정보 (상호/사업자번호/대표자/주소/통신판매업/전화)")
        pg.goto(f"{BASE}/?lang=ko", wait_until="load", timeout=60000)
        pg.wait_for_timeout(2500)
        dismiss_overlays(pg)
        hide_floating(pg)
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(800)
        pg.locator("footer.site-footer").first.screenshot(
            path=str(OUT / "02_하단정보.png")
        )
        print("  [ok] 02_하단정보.png  <- 라이브 홈 푸터")

        print("3단계 · 환불규정")
        shot(pg, f"{BASE}/legal/refund.html", "03_환불규정.png", full=True)

        print("4단계 · 로그인 / 회원가입")
        shot(pg, f"{BASE}/app/#login", "04a_로그인.png", wait="#viewAuth")
        shot(pg, f"{BASE}/app/#register", "04b_회원가입.png", wait="#viewAuth")

        print("5단계 · 상품선택 / 구매과정")
        shot(pg, f"{BASE}/?lang=ko", "05a_매물목록.png",
             wait="#listingGrid",
             scroll="document.querySelector('#listingGrid').scrollIntoView({block:'center'})")
        shot(pg, f"{BASE}/project.html?id=8&lang=ko", "05b_매물상세.png",
             wait="#bidForm", full=True)
        shot(pg, f"{BASE}/project.html?id=8&lang=ko", "05c_입찰폼.png",
             wait="#bidForm",
             scroll="document.querySelector('#bidForm').scrollIntoView({block:'center'})")

        b.close()
    print("\n저장 위치:", OUT)


if __name__ == "__main__":
    main()
