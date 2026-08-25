# -*- coding: utf-8 -*-
"""캡처들을 토스페이먼츠 제출용 한 파일(PDF)로 묶는다.

가이드 3페이지의 6단계 순서를 그대로 따른다.
슬라이드마다 단계 라벨과 실제 URL을 같이 적어서 심사자가 경로를 확인할 수 있게 한다.
"""
import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
SHOTS = HERE / "shots"

MERCHANT = {
    "상호명": "코어랩스 (CoreLabs)",
    "사업자등록번호": "705-04-02867",
    "통신판매업 신고번호": "제2026-강원춘천-0553호",
    "대표자명": "호현수",
    "사업장주소": "강원특별자치도 춘천시 세실로192번길 8-3, 1층 왼쪽 상가(후평동)",
    "유선전화": "033-818-2021",
    "가맹점 URL": "https://wakeagain.com",
    "Test ID": "corelabs.seller@wakeagain.com",
    "Test PW": "Toss-Review-2026!",
}

SLIDES = [
    dict(label="② 하단정보", url="https://wakeagain.com  (모든 페이지 하단 푸터)",
         img="02a_사업자정보표.png", layout="side", extra="02b_하단한줄.png",
         note="상호명 · 대표자명 · 사업자등록번호 · 통신판매업신고번호 · 사업장주소 · "
              "유선전화번호 6개 항목이 <b>모든 페이지 하단</b>에 노출됩니다. "
              "아래는 같은 푸터의 한 줄 요약입니다."),
    dict(label="③ 환불규정 (1/4)", url="https://wakeagain.com/legal/refund.html",
         img="03a_환불규정_1.png",
         note="취소·환불 정책 — 한눈에 보기 표. 결제 전/결제 후/이전 시작 후/거래 확정 후 단계별 기준."),
    dict(label="③ 환불규정 (2/4)", url="https://wakeagain.com/legal/refund.html",
         img="03b_환불규정_2.png",
         note="서비스 제공 기간(결제 확인 후 3영업일 이내 이전, 이전 후 48시간 내 확정)과 환불 요청 절차."),
    dict(label="③ 환불규정 (3/4)", url="https://wakeagain.com/legal/refund.html",
         img="03c_환불규정_3.png",
         note="설명과 실제 자산이 다를 때의 이의 제기, 청약철회가 제한되는 경우."),
    dict(label="③ 환불규정 (4/4)", url="https://wakeagain.com/legal/refund.html",
         img="03d_환불규정_4.png",
         note="통신판매중개자 지위 고지 및 페이지 하단 사업자 정보."),
    dict(label="④ 로그인", url="https://wakeagain.com/app/#login",
         img="04a_로그인.png",
         note="이메일 로그인 및 SNS 로그인(구글·깃허브·카카오)을 제공합니다."),
    dict(label="④ 회원가입", url="https://wakeagain.com/app/#register",
         img="04b_회원가입.png",
         note="만 14세 이상 확인 후 가입합니다. 비회원 구매는 제공하지 않습니다."),
    dict(label="⑤ 상품 선택", url="https://wakeagain.com  (마켓플레이스 목록)",
         img="05a_매물목록.png",
         note="판매 중인 프로젝트 목록입니다. 카드를 선택하면 상세 페이지로 이동합니다."),
    dict(label="⑤ 상품 상세", url="https://wakeagain.com/project.html?id=8",
         img="05b_매물상세.png", layout="side",
         note="상품 설명 · 포함 자산 · 판매자 정보 · 가격을 확인합니다."),
    dict(label="⑤ 구매(입찰) 과정", url="https://wakeagain.com/project.html?id=8",
         img="05c_입찰폼.png",
         note="금액을 입력하고 「입찰하기」를 누릅니다. 최고가 입찰자가 낙찰되면 결제 단계로 넘어갑니다."),
    dict(label="⑥ 결제 경로 — 낙찰 후 결제 대기", url="project.html (낙찰 후 · 구매자 화면)",
         img="06_결제경로.png",
         note="낙찰 금액과 판매자 수수료, 결제 기한이 표시됩니다. 낙찰 후 <b>1시간 내</b> 결제해야 합니다."),
    dict(label="⑥ 결제 경로 — 결제수단 선택", url="project.html (낙찰 후 · 구매자 화면)",
         img="06b_결제패널.png", layout="side",
         note="「카드로 결제하기」를 누르면 PortOne 결제창이 호출됩니다. "
              "국내 카드는 <b>토스페이먼츠 채널</b>로 연동되어 있습니다."),
]


def b64(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def build_html() -> str:
    rows = "".join(
        f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in MERCHANT.items()
    )
    cover = f"""
    <section class="slide cover">
      <p class="kick">토스페이먼츠 결제경로 심사 자료</p>
      <h1>WakeAgain</h1>
      <p class="sub">① 가맹점 정보</p>
      <table class="m">{rows}</table>
      <p class="foot">작성일 2026-08-25 · 코어랩스</p>
    </section>"""
    body = []
    for sl in SLIDES:
        f = SHOTS / sl["img"]
        if not f.exists():
            print("  ! 없음:", sl["img"])
            continue
        extra = SHOTS / sl["extra"] if sl.get("extra") else None
        extra_html = (
            f'<div class="extra"><img src="{b64(extra)}" alt="footer line"></div>'
            if extra and extra.exists() else ""
        )
        if sl.get("layout") == "side":
            main = f"""
      <div class="side">
        <div class="shot tall"><img src="{b64(f)}" alt="{sl['label']}"></div>
        <div class="aside"><p class="note">{sl['note']}</p>{extra_html}</div>
      </div>"""
        else:
            main = f"""
      <div class="shot"><img src="{b64(f)}" alt="{sl['label']}"></div>
      <p class="note">{sl['note']}</p>{extra_html}"""
        body.append(f"""
    <section class="slide">
      <header><span class="badge">{sl['label']}</span><span class="url">{sl['url']}</span></header>{main}
    </section>""")
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>
@page {{ size: 1280px 800px; margin: 0; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Malgun Gothic','맑은 고딕',sans-serif; color:#111; background:#fff; }}
.slide {{ width:1280px; height:800px; padding:34px 44px; page-break-after:always;
         display:flex; flex-direction:column; }}
header {{ display:flex; align-items:center; gap:14px; border-bottom:2px solid #3182f6;
          padding-bottom:12px; margin-bottom:16px; flex:0 0 auto; }}
.badge {{ background:#3182f6; color:#fff; font-weight:700; font-size:19px;
          padding:7px 16px; border-radius:6px; white-space:nowrap; }}
.url {{ font-size:15px; color:#555; word-break:break-all; }}
.shot {{ flex:1 1 auto; min-height:0; display:flex; align-items:center; justify-content:center;
         border:1px solid #d8dde5; border-radius:8px; background:#f7f8fa; overflow:hidden; }}
.shot img {{ max-width:100%; max-height:100%; object-fit:contain; display:block; }}
.note {{ flex:0 0 auto; margin-top:12px; font-size:15px; color:#333; line-height:1.6; }}
.side {{ flex:1 1 auto; min-height:0; display:flex; gap:22px; align-items:stretch; }}
.side .shot {{ flex:0 0 auto; max-width:52%; }}
.side .shot.tall img {{ max-height:640px; }}
.side .aside {{ flex:1 1 auto; display:flex; flex-direction:column; justify-content:center; gap:16px; }}
.side .aside .note {{ margin-top:0; font-size:16px; }}
.extra {{ border:1px solid #d8dde5; border-radius:6px; background:#f7f8fa; padding:8px; }}
.extra img {{ width:100%; display:block; }}
.cover {{ justify-content:center; }}
.cover .kick {{ font-size:20px; color:#3182f6; font-weight:700; margin-bottom:10px; }}
.cover h1 {{ font-size:62px; letter-spacing:-2px; margin-bottom:6px; }}
.cover .sub {{ font-size:22px; color:#555; margin-bottom:26px; }}
.m {{ border-collapse:collapse; width:100%; max-width:920px; }}
.m th, .m td {{ border:1px solid #d8dde5; padding:11px 16px; font-size:17px; text-align:left; }}
.m th {{ background:#eef4ff; width:250px; font-weight:700; color:#1b4fa0; }}
.cover .foot {{ margin-top:26px; font-size:15px; color:#777; }}
</style></head><body>{cover}{''.join(body)}</body></html>"""


def main():
    html = build_html()
    tmp = HERE / "_deck.html"
    tmp.write_text(html, encoding="utf-8")
    out = HERE / "WakeAgain_토스페이먼츠_결제경로.pdf"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(tmp.as_uri(), wait_until="load")
        pg.wait_for_timeout(1500)
        pg.pdf(path=str(out), width="1280px", height="800px",
               print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()
    tmp.unlink(missing_ok=True)
    print("생성:", out, f"({out.stat().st_size/1024/1024:.1f} MB)")


if __name__ == "__main__":
    main()
