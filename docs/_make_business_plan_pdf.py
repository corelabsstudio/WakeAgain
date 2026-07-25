# -*- coding: utf-8 -*-
"""CoreLabs 사업계획서 PDF — 주사업 WakeAgain · 부사업 RoadLog · Trace."""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESK = Path(os.path.expanduser("~")) / "Desktop"
OUT_PDF = DESK / "CoreLabs_사업계획서_WakeAgain_RoadLog_Trace.pdf"
# User-facing alias (same design as prior “CoreLabs 사업계획서.pdf”)
OUT_ALIAS_SIMPLE = DESK / "CoreLabs 사업계획서.pdf"
OUT_ALIAS_SHORT = DESK / "CoreLabs_사업계획서_WakeAgain_RoadLog.pdf"
OUT_HTML = ROOT / "docs" / "_business_plan_preview.html"

LOGO_CANDIDATES = [
    ROOT / "public" / "assets" / "corelabs-logo-lockup.jpg",
    ROOT / "public" / "assets" / "corelabs-logo-lockup.png",
    ROOT / "public" / "assets" / "corelabs-logo-mark.png",
    Path(r"C:\Users\hysoo\Projects\RoadLog\docs\marketing\brand\corelabs_logo_wordmark.png"),
]


def logo_data_uri() -> str:
    """Prefer lockup; crop large empty margins so cover logo looks bigger."""
    from PIL import Image
    import io

    for p in LOGO_CANDIDATES:
        if not p.is_file():
            continue
        try:
            im = Image.open(p).convert("RGBA")
            w, h = im.size
            px = im.load()
            min_x, min_y, max_x, max_y = w, h, 0, 0
            found = False
            for y in range(0, h, 2):
                for x in range(0, w, 2):
                    r, g, b, a = px[x, y]
                    if a < 40:
                        continue
                    if r > 230 and g > 230 and b > 230:
                        continue
                    if (r + g + b) > 680:
                        continue
                    found = True
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
            if found and (max_x - min_x) > 40 and (max_y - min_y) > 20:
                pad = 20
                box = (
                    max(0, min_x - pad),
                    max(0, min_y - pad),
                    min(w, max_x + 1 + pad),
                    min(h, max_y + 1 + pad),
                )
                im = im.crop(box)
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            print("logo:", p, "cropped", im.size)
            return f"data:image/png;base64,{b64}"
        except Exception as e:
            print("logo crop fail", p, e)
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
            return f"data:{mime};base64,{b64}"
    print("logo: missing — text-only cover mark")
    return ""


def font_faces() -> str:
    fonts_dir = Path(__file__).resolve().parent / "fonts"
    win = Path(r"C:\Windows\Fonts")
    pairs = [
        (fonts_dir / "malgun.ttf", "DocKR", "400"),
        (fonts_dir / "malgunbd.ttf", "DocKR", "700"),
        (fonts_dir / "HancomGothic-Regular.ttf", "DocKR", "400"),
        (fonts_dir / "HancomGothic-Bold.ttf", "DocKR", "700"),
        (win / "malgun.ttf", "DocKR", "400"),
        (win / "malgunbd.ttf", "DocKR", "700"),
    ]
    rules: list[str] = []
    seen: set[tuple[str, str]] = set()
    for path, family, weight in pairs:
        if not path.is_file():
            continue
        key = (family, weight)
        if key in seen:
            continue
        seen.add(key)
        uri = path.resolve().as_uri()
        rules.append(
            f"""@font-face {{
  font-family: "{family}";
  src: url("{uri}") format("truetype");
  font-weight: {weight};
  font-style: normal;
  font-display: block;
}}"""
        )
    print("fonts:", len(rules), [str(p.name) for p, _, _ in pairs if p.is_file()])
    return "\n".join(rules)


def build_html(logo_uri: str) -> str:
    logo_img = (
        f'<img class="cover-logo" src="{logo_uri}" alt="CoreLabs" />'
        if logo_uri
        else '<div class="cover-logo-fallback">CoreLabs</div>'
    )
    logo_mark = (
        f'<img class="header-mark" src="{logo_uri}" alt="" />' if logo_uri else ""
    )
    fonts = font_faces()

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<title>CoreLabs 사업계획서 — WakeAgain · RoadLog · Trace</title>
<style>
{fonts}
  @page {{
    size: A4;
    margin: 13mm 13mm 15mm 13mm;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0;
    font-family: "DocKR", "Malgun Gothic", "맑은 고딕", sans-serif;
    color: #1e293b;
    font-size: 9.6pt;
    line-height: 1.48;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  :root {{
    --navy: #0b1220;
    --navy-2: #111827;
    --purple: #a855f7;
    --purple-deep: #7c3aed;
    --muted: #64748b;
    --line: #e2e8f0;
    --soft: #f8fafc;
    --soft-purple: #f5f3ff;
    --accent: #0ea5e9;
  }}

  .cover {{
    /* Keep cover on its own page WITHOUT forcing full-page height.
       Fixed height + page-break-after creates a blank middle page. */
    page-break-after: always;
    break-after: page;
    display: block;
  }}
  .cover-top {{
    background: var(--navy);
    color: #fff;
    padding: 12mm 12mm 10mm;
    text-align: center;
    position: relative;
  }}
  .cover-top::after {{
    content: "";
    position: absolute;
    left: 0; right: 0; bottom: 0;
    height: 5px;
    background: linear-gradient(90deg, var(--purple-deep), var(--purple), #c084fc);
  }}
  .cover-kicker {{
    letter-spacing: 0.22em;
    font-size: 8.5pt;
    color: #94a3b8;
    font-weight: 600;
    margin-bottom: 10px;
  }}
  .cover-logo {{
    display: block;
    height: 44px;
    width: auto;
    max-width: 260px;
    margin: 0 auto 10px;
    object-fit: contain;
    background: #fff;
    padding: 8px 16px;
    border-radius: 12px;
    box-shadow: 0 8px 28px rgba(0,0,0,0.25);
  }}
  .cover-logo-fallback {{
    font-size: 20pt;
    font-weight: 800;
    color: #fff;
    margin-bottom: 12px;
  }}
  .cover-title {{
    font-size: 23pt;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 0 0 5px;
  }}
  .cover-sub {{
    font-size: 10.5pt;
    color: #c4b5fd;
    font-weight: 600;
    margin: 0 0 6px;
  }}
  .cover-pills {{
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
  }}
  .pill {{
    background: rgba(168,85,247,0.18);
    border: 1px solid rgba(196,181,253,0.45);
    color: #e9d5ff;
    font-size: 8pt;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 999px;
  }}
  .cover-body {{
    padding: 5mm 7mm 4mm;
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .cover-tagline {{
    font-size: 12pt;
    font-weight: 800;
    color: var(--navy-2);
    margin: 0 0 2mm;
    text-align: center;
  }}
  .cover-points {{
    text-align: center;
    color: var(--muted);
    font-size: 9.2pt;
    line-height: 1.55;
    margin: 0 0 4mm;
  }}
  .portfolio-strip {{
    width: 100%;
    display: grid;
    grid-template-columns: 1.15fr 1fr 1fr;
    gap: 7px;
    margin-bottom: 4mm;
  }}
  .p-card {{
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 8px 9px;
    background: #fff;
  }}
  .p-card.main {{
    border-color: #c4b5fd;
    background: linear-gradient(180deg, #faf5ff 0%, #fff 70%);
  }}
  .p-card .role {{
    font-size: 7.5pt;
    font-weight: 800;
    color: var(--purple-deep);
    letter-spacing: 0.04em;
    margin-bottom: 3px;
  }}
  .p-card .name {{
    font-size: 11pt;
    font-weight: 800;
    color: var(--navy-2);
    margin-bottom: 2px;
  }}
  .p-card .desc {{
    font-size: 8pt;
    color: var(--muted);
    line-height: 1.4;
  }}
  .p-card .dom {{
    margin-top: 5px;
    font-size: 7.5pt;
    font-weight: 700;
    color: #4c1d95;
    word-break: break-all;
  }}
  .meta-box {{
    width: 100%;
    max-width: 420px;
    margin-top: 2mm;
    background: var(--soft);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 7px 14px;
  }}
  .meta-row {{
    display: grid;
    grid-template-columns: 64px 1fr;
    gap: 8px;
    padding: 5px 0;
    font-size: 9.5pt;
  }}
  .meta-row + .meta-row {{ border-top: 1px solid #eef2f7; }}
  .meta-row .k {{ color: var(--muted); font-weight: 600; }}
  .meta-row .v {{ color: var(--navy-2); font-weight: 600; }}

  .doc-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--line);
    padding-bottom: 6px;
    margin: 0 0 10px;
    font-size: 8pt;
    color: var(--muted);
  }}
  .doc-header .left {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }}
  .header-mark {{
    height: 15px;
    width: auto;
    object-fit: contain;
  }}
  /* IMPORTANT: do NOT use page-break-inside:avoid on large .sec blocks —
     that forces whole sections to the next page and leaves blank middle pages. */
  .sec {{
    margin: 0 0 9px;
    break-inside: auto;
    page-break-inside: auto;
  }}
  .sec-h {{
    background: var(--purple);
    color: #fff;
    font-weight: 800;
    font-size: 10pt;
    padding: 6px 10px;
    border-radius: 6px;
    margin: 0 0 6px;
    break-after: avoid;
    page-break-after: avoid;
  }}
  .callout {{
    border: 1.5px solid var(--purple);
    border-left: 5px solid var(--purple);
    border-radius: 8px;
    padding: 7px 10px;
    margin: 0 0 7px;
    background: #faf5ff;
    font-size: 9pt;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  h3 {{
    font-size: 10pt;
    color: var(--purple-deep);
    margin: 7px 0 3px;
    font-weight: 800;
    break-after: avoid;
    page-break-after: avoid;
  }}
  p {{ margin: 0 0 4px; }}
  ul, ol {{ margin: 0 0 4px; padding-left: 17px; }}
  li {{ margin: 1px 0; }}
  .fine {{ font-size: 8pt; color: var(--muted); }}
  .abbr {{
    font-size: 7.6pt;
    color: #475569;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 5px 8px;
    margin: 5px 0 7px;
    line-height: 1.42;
  }}
  .abbr strong {{ color: #334155; }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 4px 0 7px;
    font-size: 8.5pt;
    break-inside: auto;
    page-break-inside: auto;
  }}
  thead {{ display: table-header-group; }}
  tr {{
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  th {{
    background: var(--navy-2);
    color: #fff;
    font-weight: 700;
    text-align: left;
    padding: 5px 8px;
  }}
  td {{
    padding: 4px 8px;
    border-bottom: 1px solid var(--line);
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
  td.k {{ width: 24%; font-weight: 600; color: #334155; }}

  .cards {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
    margin: 5px 0 7px;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .card {{
    background: var(--soft-purple);
    border-radius: 10px;
    padding: 8px 5px;
    text-align: center;
  }}
  .card strong {{
    display: block;
    color: var(--purple-deep);
    font-size: 10pt;
    margin-bottom: 2px;
  }}
  .card span {{
    font-size: 7.5pt;
    color: var(--muted);
  }}

  .two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .three-col {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6px;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .box {{
    background: var(--soft);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 8px 9px;
  }}
  .box h3 {{ margin-top: 0; }}
  /* product blocks inside sec 03 may span pages */
  .product-block {{
    margin: 0 0 8px;
    break-inside: auto;
    page-break-inside: auto;
  }}
  .tag-main {{
    display: inline-block;
    background: #7c3aed;
    color: #fff;
    font-size: 7.5pt;
    font-weight: 800;
    padding: 2px 7px;
    border-radius: 999px;
    margin-right: 4px;
    vertical-align: middle;
  }}
  .tag-side {{
    display: inline-block;
    background: #0f172a;
    color: #e2e8f0;
    font-size: 7.5pt;
    font-weight: 800;
    padding: 2px 7px;
    border-radius: 999px;
    margin-right: 4px;
    vertical-align: middle;
  }}

  .closing {{
    border: 1.5px solid var(--purple);
    border-left: 6px solid var(--purple);
    border-radius: 8px;
    padding: 10px 12px;
    font-weight: 700;
    background: #faf5ff;
    margin: 7px 0;
    font-size: 9.2pt;
  }}

  .doc-foot {{
    margin-top: 12px;
    padding-top: 7px;
    border-top: 1px solid var(--line);
    font-size: 7.5pt;
    color: var(--muted);
    text-align: center;
  }}
</style>
</head>
<body>

<!-- ============ COVER ============ -->
<section class="cover">
  <div class="cover-top">
    <div class="cover-kicker">BUSINESS PLAN</div>
    {logo_img}
    <h1 class="cover-title">사업계획서</h1>
    <p class="cover-sub">CoreLabs · WakeAgain · RoadLog · Trace</p>
    <div class="cover-pills">
      <span class="pill">주사업 WakeAgain</span>
      <span class="pill">부사업 ① RoadLog</span>
      <span class="pill">부사업 ② Trace</span>
    </div>
  </div>
  <div class="cover-body">
    <p class="cover-tagline">소프트웨어를 만들고, 잠든 프로젝트에 다시 기회를 줍니다.</p>
    <div class="cover-points">
      IT 스튜디오 <strong>코어랩스(CoreLabs)</strong> · 대표 호현수<br/>
      전략: <strong>캐시카우(RoadLog)로 현금 흐름 → WakeAgain 양면 시장 확장 → Trace 스케일</strong><br/>
      이미 라이브: roadlog.co.kr · WakeAgain Railway · Trace 설치형<br/>
      채널: 웹 · PWA · Android(Capacitor) · <strong>Google Play AAB 제출 패키지 준비</strong>
    </div>
    <div class="portfolio-strip">
      <div class="p-card main">
        <div class="role">MAIN · 주사업(전략)</div>
        <div class="name">WakeAgain</div>
        <div class="desc">잠든 사이드 프로젝트 장터<br/>통신판매중개 · 수수료 10%</div>
        <div class="dom">https://wakeagain.com<br/>웹·PWA·Play AAB 준비</div>
      </div>
      <div class="p-card">
        <div class="role">CASH · 초기 집중</div>
        <div class="name">RoadLog</div>
        <div class="desc">AI 운행·외근 일지 SaaS<br/>즉시 과금 가능</div>
        <div class="dom">https://roadlog.co.kr</div>
      </div>
      <div class="p-card">
        <div class="role">SIDE ② · 2단계</div>
        <div class="name">Trace</div>
        <div class="desc">인터뷰 경험글 도구<br/>BYOK로 원가 방어</div>
        <div class="dom">설치형 Trace.exe</div>
      </div>
    </div>
    <div class="meta-box">
      <div class="meta-row"><span class="k">운영</span><span class="v">코어랩스 (CoreLabs)</span></div>
      <div class="meta-row"><span class="k">대표</span><span class="v">호현수</span></div>
      <div class="meta-row"><span class="k">문의</span><span class="v">corelabs.studio@gmail.com</span></div>
      <div class="meta-row"><span class="k">작성</span><span class="v">2026년 7월 25일 · v6.0 최신화</span></div>
      <div class="meta-row"><span class="k">용도</span><span class="v">사업자등록 · 투자·파트너 · 내부 정렬 · 스토어 제출</span></div>
    </div>
  </div>
</section>

<!-- ============ BODY ============ -->
<div class="doc-header">
  <div class="left">{logo_mark}<span>CoreLabs Business Plan · WakeAgain · RoadLog · Trace</span></div>
  <div>대표 호현수</div>
</div>

<section class="sec">
  <div class="sec-h">01 사업 개요</div>
  <div class="callout">
    <strong>한 줄 정의</strong> — 코어랩스는 소프트웨어·웹 기반 디지털 제품을 기획·개발·운영하는
    <strong>IT 스튜디오</strong>입니다.
    <strong>전략 주사업</strong>은 잠든 사이드 프로젝트 장터 <strong>WakeAgain</strong>,
    <strong>초기 캐시카우(Cash Cow, 즉시 현금 창출 제품)</strong>는 이미 라이브인
    <strong>RoadLog</strong>,
    <strong>2단계 부사업</strong>은 인터뷰 경험글 도구 <strong>Trace</strong>입니다.
    세 제품을 “동시에 전면 마케팅”하지 않고, <strong>화력 집중 순서</strong>를 명시합니다.
  </div>
  <table>
    <thead><tr><th style="width:26%">항목</th><th>내용</th></tr></thead>
    <tbody>
      <tr><td class="k">상호</td><td>코어랩스 (CoreLabs)</td></tr>
      <tr><td class="k">대표</td><td>호현수</td></tr>
      <tr><td class="k">문의</td><td>corelabs.studio@gmail.com</td></tr>
      <tr><td class="k">사업 형태</td><td>온라인 IT 서비스 (개인사업자 → 법인 전환 검토 전 단계)</td></tr>
      <tr><td class="k">브랜드 구조</td><td>상호 CoreLabs 1개 · 제품 브랜드: WakeAgain / RoadLog / Trace</td></tr>
      <tr><td class="k">운영 원칙</td><td>단일 상호 · 제품별 약관·고지 · 리소스 집중 순서 준수</td></tr>
      <tr><td class="k">포트폴리오</td><td>
        <span class="tag-main">전략 주</span>WakeAgain &nbsp;
        <span class="tag-side">캐시</span>RoadLog &nbsp;
        <span class="tag-side">2단계</span>Trace
      </td></tr>
      <tr><td class="k">실행 현황</td><td>
        RoadLog production 라이브 · WakeAgain Railway 라이브(키워드 검색·입찰·관리자·PWA) ·
        <strong>Google Play 제출용 AAB·스크린샷 패키지 준비(2026-07-25)</strong> ·
        Trace 설치형 제품화 · <strong>사업자·PG 전 → 실홍보·실결제 금지</strong>
      </td></tr>
    </tbody>
  </table>
  <h3>도메인 · 접속 경로</h3>
  <table>
    <thead><tr><th style="width:22%">제품</th><th>구분</th><th>주소 / 경로</th></tr></thead>
    <tbody>
      <tr>
        <td class="k">WakeAgain</td>
        <td>주사업 · 장터</td>
        <td>공식 도메인 <strong>https://wakeagain.com</strong> (등록·소유 완료 · 라이브)<br/>
        클라우드: Railway · 채널: 웹 + PWA + Capacitor Android(Play AAB) · iOS 후속</td>
      </tr>
      <tr>
        <td class="k">RoadLog</td>
        <td>캐시카우 · SaaS</td>
        <td><strong>https://roadlog.co.kr</strong> (라이브 production · Volume 영속 · OpenAI 연동 확인)</td>
      </tr>
      <tr>
        <td class="k">Trace</td>
        <td>2단계 · 데스크톱</td>
        <td>설치형 앱 <strong>Trace.exe</strong> · 판매 채널 확정 시 전용 랜딩 도메인 연결</td>
      </tr>
    </tbody>
  </table>
  <h3>법적 지위 요약</h3>
  <table>
    <thead><tr><th style="width:22%">제품</th><th>지위 · 소비자 보호 방향</th></tr></thead>
    <tbody>
      <tr><td class="k">WakeAgain</td><td>전자상거래법상 <strong>통신판매중개자</strong>. 거래 당사자 아님. 다만 약관 면책만으로 끝내지 않고
      <strong>분쟁 접수·초기 거래 개입 기준·신원 단계</strong>를 운영 정책으로 명문화(상세 §11).</td></tr>
      <tr><td class="k">RoadLog</td><td>코어랩스 <strong>직접 제공</strong> SaaS. 직접 과금 시 통신판매업 신고 검토 · 약관·환불 고지.</td></tr>
      <tr><td class="k">Trace</td><td>코어랩스 <strong>직접 제공</strong> 도구. 중개 아님 · 구독·라이선스 약관.</td></tr>
    </tbody>
  </table>
  <div class="abbr">
    <strong>약어 안내</strong> —
    <strong>SaaS</strong>(Software as a Service): 웹 구독형 소프트웨어 /
    <strong>Cash Cow</strong>: 즉시 현금 흐름을 만드는 제품 /
    <strong>PG</strong>(Payment Gateway): 결제대행 /
    <strong>MVP</strong>(Minimum Viable Product): 최소 기능 시제품 /
    <strong>PWA</strong>(Progressive Web App): 설치형 웹앱 /
    <strong>BYOK</strong>(Bring Your Own Key): 사용자 본인 AI 키 /
    <strong>KPI</strong>(Key Performance Indicator): 핵심 성과 지표 /
    <strong>GTM</strong>(Go-To-Market): 시장 진입·판매 전략 /
    <strong>AAB</strong>(Android App Bundle): Google Play 제출 패키지 /
    <strong>JWT</strong>: API 인증 토큰
  </div>
</section>

<section class="sec">
  <div class="sec-h">01-B 리소스 집중 원칙 (Focus · 1인·소수 팀 대응)</div>
  <div class="callout">
    <strong>원칙</strong> — 제품이 세 개여도 <strong>동시에 전면 마케팅하지 않습니다.</strong>
    플랫폼(WakeAgain)의 콜드스타트(Cold Start, 초기 공급·수요 모두 부족) 리스크를
    <strong>이미 라이브인 RoadLog 매출·신뢰</strong>로 완충하고,
    Trace는 제품 완성·설치 패키지 준비 후 2단계로 스케일합니다.
  </div>
  <table>
    <thead><tr><th style="width:18%">단계</th><th style="width:22%">화력 집중</th><th>목표 · 리소스 배분(가이드)</th></tr></thead>
    <tbody>
      <tr>
        <td class="k">Phase 0<br/>지금~90일</td>
        <td><strong>RoadLog 캐시카우</strong></td>
        <td>운영·마케팅 약 50% · 사업자·PG·청구 경로 정비 ·
        지인·현장 직군 Free→Pro 전환 · 월 유료 전환 N명 KPI</td>
      </tr>
      <tr>
        <td class="k">Phase 1<br/>병행</td>
        <td><strong>WakeAgain 공급</strong></td>
        <td>개발·검수 약 35% · Founding Seller·시드 매물 확보 ·
        공개 전 데모 게이트 · 오픈일 경매 이벤트 · 구매자 모집은 매물 진열 후</td>
      </tr>
      <tr>
        <td class="k">Phase 2<br/>현금 안정 후</td>
        <td><strong>Trace 스케일</strong></td>
        <td>약 15% → 확대 · 설치 패키지·데모 영상 · 구독 전환 ·
        BYOK로 AI 원가 방어</td>
      </tr>
    </tbody>
  </table>
  <ul>
    <li><strong>중단 기준</strong>: 주간 운영 시간이 한 제품에 과도하게 쏠려 캐시카우 장애(결제·로그인·생성 실패)가 생기면 즉시 RoadLog 안정화 우선</li>
    <li><strong>시너지</strong>: CoreLabs 단일 브랜드 신뢰 · 기술 스택 공유 · 고객 문의 채널 통합(corelabs.studio@gmail.com)</li>
    <li><strong>하지 않는 것</strong>: 세 제품 동시 유료 광고 집행 · 기능 폭주 개발 · 수익 보장형 마케팅 문구</li>
  </ul>
</section>

<section class="sec">
  <div class="sec-h">02 사업 배경 및 필요성</div>
  <div class="two-col">
    <div class="box">
      <h3>시장 문제</h3>
      <ul>
        <li>사이드 프로젝트·MVP 대량 생산 후 유저·수익 없이 방치</li>
        <li>커뮤니티·중고 거래: 가격 기준·데모 검증·이전 절차·직거래 사기</li>
        <li>운행·현장 기록: 종이·엑셀·분산 도구로 정리·제출 비용 큼</li>
        <li>경험·후기 글: 말은 풍부하나 구조화·신뢰 문장이 약함(일반 요약 AI의티)</li>
      </ul>
    </div>
    <div class="box">
      <h3>기회</h3>
      <ul>
        <li>만드는 사람 ↔ 시간·마케팅은 있으나 0부터 만들기 싫은 사람 연결 (WakeAgain)</li>
        <li>현장 직군 일지 디지털화·AI 제출용 정리 (RoadLog)</li>
        <li>인터뷰로 재료를 채운 ‘내 경험글’ 작성 도구 (Trace)</li>
        <li>한국 우선 검증 후 웹·앱·데스크톱 채널 확장</li>
      </ul>
    </div>
  </div>
</section>

<section class="sec">
  <div class="sec-h">03 사업 아이템</div>

  <div class="product-block">
    <h3><span class="tag-main">주사업</span> 제품 A · WakeAgain</h3>
    <table>
      <thead><tr><th style="width:24%">항목</th><th>내용</th></tr></thead>
      <tbody>
        <tr><td class="k">개념</td><td>잠든 앱·프로토타입·SaaS·도구 등 디지털 프로젝트를 공개 호가(경매·가격 쓰기)로 연결하는
        <strong>거래 중개 마켓플레이스</strong> (“시간 거래소” — 다시 만들기 싫을 때)</td></tr>
        <tr><td class="k">슬로건</td><td>프로젝트에 두 번째 기회를 주세요.</td></tr>
        <tr><td class="k">제품 핵심</td><td>쉽게 올리고 쉽게 가격을 쓰되, 거래는 단계형 안전 절차로 관리 · 웹·앱 동일 계정·API</td></tr>
        <tr><td class="k">수익</td><td>등록 무료 · 성사 시 판매자 수수료 10% · 구매자 추가 수수료 없음(초기) ·
        향후 상위 노출(부스트) 등 부가 상품(PG 후)</td></tr>
        <tr><td class="k">도메인</td><td><strong>https://wakeagain.com</strong> (등록 완료 · 라이브) · Railway ·
        Capacitor 네이티브 셸</td></tr>
        <tr><td class="k">법적 역할</td><td>통신판매중개자 (거래 당사자 아님 · 약관·고지·초기 개입 기준 명문화)</td></tr>
        <tr><td class="k">채널</td><td>웹사이트 + PWA + <strong>Google Play(AAB 패키지 준비)</strong> + Apple App Store(후속) —
        동일 JWT API·동일 데이터</td></tr>
      </tbody>
    </table>
    <p><strong>주요 기능 · 안전 장치 (2026-07 구현 반영)</strong></p>
    <ul>
      <li>매물 등록(무료) · 키워드 1~5개 필수 · <strong>AI 키워드 추천</strong>(또는 수동) ·
      <strong>형식·데모 검수 후 공개</strong>(보통 1~2영업일, 가치 감정·품질 보증 아님)</li>
      <li><strong>서버사이드 키워드 검색</strong>(제목·한 줄·스토리·키워드·유형) + 카테고리 탭 ·
      공개 현재가·고유 입찰자 수 · 관심 등록 · 30초 무료 진단(통계 힌트, 감정가 아님)</li>
      <li>신원 게이트: <strong>Lv1 이메일 → 입찰</strong> · <strong>Lv2 실명·휴대폰 → 결제·인수</strong> ·
      <strong>Lv3 계좌 → 판매자 정산</strong> · 만 14세 미만 가입 차단</li>
      <li>안전거래 루프: 낙찰 → <strong>PG 결제(목표 1시간)</strong> → 이전 → 검수·인수(기본 48h 무이의 시 자동 확정) → 정산 ·
      <strong>1순위 미입금 시 차순위 자동 낙찰</strong>(골격 완료 · 실결제=PG 웹훅 전용)</li>
      <li>공개 입찰 보드 · 헤비 구매자 배지 · 최고 입찰자 카드 · 쪽지 외부거래 경고 고정</li>
      <li><strong>유저↔유저 차단</strong>(Play 콘텐츠 등급 대응) · 신고·누적 제재 · 관리자(매물·회원·후기·수수료·매출·신고)</li>
      <li>채널: 웹 + PWA(앱 셸·하단 탭) + Android Capacitor · <strong>Play 스토어 제출용 AAB·아이콘·스크린샷 준비</strong></li>
      <li>운영 인프라: Resend 메일 인증 · SQLite 백업·오프사이트 백업 골격 · bug_watch 자동 감시 ·
      프리미엄 상위노출 DB/정렬 골격(결제 UI는 PG 후)</li>
      <li><strong>초기 거래 개입</strong>: 런칭 후 성사 건수 초기 구간은 운영자 수동 확인·분쟁 SLA 적용(§11)</li>
    </ul>
  </div>

  <div class="product-block">
    <h3>WakeAgain · 기능 현황 스냅샷 (v6.0 · 2026-07-25)</h3>
    <table>
      <thead><tr><th style="width:28%">영역</th><th>구현 · 상태</th></tr></thead>
      <tbody>
        <tr><td class="k">마켓·검색</td><td>목록·상세·관심 · 키워드 검색/등록 · AI 키워드 추천 · 카테고리 · 라이브 경매 폴링</td></tr>
        <tr><td class="k">경매·거래</td><td>공개 호가 · 입찰 레이스 동기화 · 스케줄러 마감 · 딜 상태머신 · 차순위 재낙찰 · 수수료 인보이스(10%)</td></tr>
        <tr><td class="k">신뢰·컴플라이언스</td><td>Lv1~3 게이트 · 만14세 · 유저 차단 · 신고 임계 · 약관·개인정보 · 외부직거래 고지</td></tr>
        <tr><td class="k">멀티채널</td><td>웹 랜딩 + /app 셸 + PWA · Capacitor Android · Play AAB·피처그래픽·폰/태블릿 스크린샷</td></tr>
        <tr><td class="k">관리·품질</td><td>관리자 검수·회원·매출 · Resend 인증메일 · 자동 테스트 스위트 · bug_watch · 데이터 보호 백업</td></tr>
        <tr><td class="k">미완(의도적)</td><td><strong>사업자 등록·번호 게시</strong> · <strong>PG 실결제·웹훅</strong> · SNS OAuth · iOS 제출 · 부스트 유료 상품 UI</td></tr>
      </tbody>
    </table>
    <p class="fine">※ PG 연동 전 실거래·실홍보 없음. 입금 확인은 PG 웹훅만 허용(관리자 수동 입금 확인 경로 없음).</p>
  </div>

  <div class="product-block">
    <h3><span class="tag-side">부사업 ①</span> 제품 B · RoadLog</h3>
    <table>
      <thead><tr><th style="width:24%">항목</th><th>내용</th></tr></thead>
      <tbody>
        <tr><td class="k">개념</td><td>운행·외근 메모를 회사 제출용 일지로 AI 정리하는 웹 SaaS</td></tr>
        <tr><td class="k">슬로건</td><td>오늘 현장 기록, 제출까지 한 번에.</td></tr>
        <tr><td class="k">핵심 산출</td><td>Excel · PDF · DOCX 다운로드 · 인쇄 · 계정 저장·이어쓰기</td></tr>
        <tr><td class="k">요금 (런칭가)</td><td>Free 월 15회 · Pro 월 2,900원 · Enterprise 팀 좌석(세금계산서)</td></tr>
        <tr><td class="k">도메인</td><td><strong>https://roadlog.co.kr</strong> (라이브 · production · OpenAI 연동 · Volume 영속)</td></tr>
        <tr><td class="k">역할</td><td>코어랩스 직접 제공 · 직접 과금(스마트스토어 claim 등)</td></tr>
      </tbody>
    </table>
    <p><strong>주요 기능</strong></p>
    <ul>
      <li>퀵 스탬프(위치·시간) · 운행/외근 일지 AI 작성 · 회사 서식 학습</li>
      <li>제출 전 요약·차량번호 수정 · 관리자 대시보드 · 역할 미리보기</li>
      <li>클라우드 배포(Railway) · 데이터 영속 Volume(/data)</li>
    </ul>
  </div>

  <div class="product-block">
    <h3><span class="tag-side">부사업 ②</span> 제품 C · Trace</h3>
    <table>
      <thead><tr><th style="width:24%">항목</th><th>내용</th></tr></thead>
      <tbody>
        <tr><td class="k">개념</td><td>취재형 인터뷰로 행동·사실을 끌어내, 경험 후기형 본문·발행 패키지를 만드는 데스크톱 작성 도구</td></tr>
        <tr><td class="k">슬로건</td><td>말만 하면, 사람들이 읽고 머물 경험글</td></tr>
        <tr><td class="k">형태</td><td>Windows 데스크톱 앱 (Trace.exe / 설치 패키지)</td></tr>
        <tr><td class="k">가격 지향</td><td>월 약 3만 원대 구독·라이선스 체감 (가성비·인터뷰 품질)</td></tr>
        <tr><td class="k">AI</td><td>BYOK(사용자 본인 API 키) 가능 · 없는 경험 창작 금지</td></tr>
        <tr><td class="k">배포</td><td>설치형 로컬 실행 · 판매 바=인터뷰 퀄·정리력 체감 (수익 보장 광고 금지)</td></tr>
      </tbody>
    </table>
    <p><strong>주요 기능</strong></p>
    <ul>
      <li>경험 인터뷰(목적 → 순차 행동·사실 → 선택 감정) · 기사 구조 플랜 · 1인칭 초안</li>
      <li>제목·메타·태그·포스팅 가이드 · Markdown/HTML 패키지 · 티스토리·네이버 등 수동 발행</li>
      <li>물타기·허위 경험 창작 금지 · E-E-A-T(경험·전문성·권위·신뢰) 밀도 지향</li>
    </ul>
  </div>
  <p class="fine">공통: 코어랩스 단일 운영 · 웹/클라우드 또는 데스크톱 · 한국 원화 정산 우선 · 상호·세금·약관은 CoreLabs.</p>
</section>

<section class="sec">
  <div class="sec-h">04 목표 고객</div>
  <table>
    <thead><tr><th style="width:18%">구분</th><th>페르소나</th><th>니즈</th></tr></thead>
    <tbody>
      <tr><td class="k">WA 판매자</td><td>사이드·MVP 메이커, 바이브 코더, 인디 메이커</td><td>폴더에 남은 프로토타입 정리·현금화, 운영 여력 부족</td></tr>
      <tr><td class="k">WA 구매자</td><td>바이브 코더 → 인디해커 → 마케터 → 대표 → 크리에이터</td><td>0부터 만들기보다 인수, 시간 절약, 데모 있는 자산</td></tr>
      <tr><td class="k">RoadLog</td><td>영업·외근·법인차 운행 기록이 필요한 개인·팀</td><td>종이·엑셀 → 제출용 디지털 일지, 증빙·보관</td></tr>
      <tr><td class="k">Trace</td><td>블로거·리뷰어·스토리텔러·창업 기록자</td><td>말은 많은데 구조화가 어려움 · ‘내 경험’ 지키는 본문</td></tr>
    </tbody>
  </table>
</section>

<section class="sec">
  <div class="sec-h">05 비즈니스 모델</div>
  <div class="three-col">
    <div class="box">
      <h3>WakeAgain (주)</h3>
      <ul>
        <li>등록·관심·입찰: 무료</li>
        <li>성사 시 판매자 10%</li>
        <li>구매자 추가 수수료 없음(초기)</li>
        <li>향후: 상위 노출 부스트(DB·정렬 골격 완료 · PG 후 상품화)</li>
      </ul>
    </div>
    <div class="box">
      <h3>RoadLog (부1)</h3>
      <ul>
        <li>Free 월 15회 체험</li>
        <li>Pro 월 2,900원(런칭가)</li>
        <li>Enterprise 팀·세금계산서</li>
        <li>스마트스토어 claim 경로</li>
      </ul>
    </div>
    <div class="box">
      <h3>Trace (부2)</h3>
      <ul>
        <li>구독 또는 기간 라이선스</li>
        <li>목표 체감 월 ~3만 원</li>
        <li>BYOK로 AI 원가 분산 가능</li>
        <li>직접 판매(중개 아님)</li>
      </ul>
    </div>
  </div>
  <ul>
    <li>실거래·정산은 <strong>PG(결제대행)</strong> 연동 후 운영 · PG 전 오프플랫폼 입금은 운영 경로로 두지 않음</li>
    <li>WakeAgain: PG 확인 후 이전·인수·정산 자동화 목표</li>
    <li>RoadLog·Trace: 코어랩스 직접 과금 · 약관·고지 반영</li>
  </ul>
</section>

<section class="sec">
  <div class="sec-h">06 경쟁 우위 및 차별점</div>
  <div class="cards">
    <div class="card"><strong>특화</strong><span>사이드·MVP<br/>공개 호가 장터</span></div>
    <div class="card"><strong>투명</strong><span>데모·가격<br/>입찰·배지 공개</span></div>
    <div class="card"><strong>절차</strong><span>단계형 안전거래<br/>차단·신고·Lv</span></div>
    <div class="card"><strong>채널</strong><span>웹·PWA·Play<br/>동일 API</span></div>
  </div>
  <ul>
    <li>대형 M&amp;A(인수합병) 플랫폼과 다른 문턱 — 사이드 프로젝트 규모에 맞춤</li>
    <li>입찰 허들 최소화(이메일 Lv1) / 낙찰 후 신원·정산 강화 · 키워드 검색으로 매물 발견성 확보</li>
    <li>이미 동작하는 라이브 스택(Railway·도메인·검수·입찰·앱 패키지) — 아이디어 단계와 차별</li>
    <li>RoadLog: 현장 일지 특화 + 회사 서식 학습 + 실제 라이브 도메인 운영</li>
    <li>Trace: 일반 요약 LLM이 아닌 ‘취재 인터뷰 → 경험글’ 전용 워크플로</li>
  </ul>
</section>

<section class="sec">
  <div class="sec-h">07 마케팅·성장 전략 (GTM · 그로스 훅)</div>
  <div class="two-col">
    <div class="box">
      <h3>메시지</h3>
      <ul>
        <li><strong>WA 판매자</strong>: 매물만 올려 주세요. 등록 무료. 손님 모객·오픈은 운영이.</li>
        <li><strong>WA 구매자</strong>: 다시 만들기 전에, 돌아가는 초안을. + 안전결제.</li>
        <li><strong>RoadLog</strong>: 제출은 단정하게, 입력은 편하게. · roadlog.co.kr</li>
        <li><strong>Trace</strong>: 말만 하면, 읽고 머물 경험글. (수익 보장 금지)</li>
      </ul>
    </div>
    <div class="box">
      <h3>채널 · 순서 (Focus 반영)</h3>
      <ul>
        <li><strong>1순위</strong> RoadLog: 영업·외근·법인차 직군 · 지인 DM · 오픈채 1곳</li>
        <li><strong>2순위</strong> WA 판매자: 바이브 코딩·인디해커·사이드프로젝트 커뮤니티</li>
        <li><strong>3순위</strong> WA 구매자: 매물 진열 후 마케터·비개발 창업자</li>
        <li><strong>4순위</strong> Trace: 블로거·리뷰어 (Phase 2)</li>
      </ul>
    </div>
  </div>
  <h3>WakeAgain · 판매자(Seller) 그로스 훅 — 양면 시장 공급 우선</h3>
  <table>
    <thead><tr><th style="width:28%">훅</th><th>실행 내용 · 측정</th></tr></thead>
    <tbody>
      <tr>
        <td class="k">Founding Seller<br/>프로그램</td>
        <td><strong>매물 등록(데모 URL 등) 검수 통과</strong> 조건 · 초대 판매자 목표 50~100명 ·
        보상: <strong>Trace 기간 라이선스(90일/6개월)</strong> + 프로필 뱃지·노출 우선 ·
        (선택) 첫 성사 수수료 0~5% 한시 우대 · KPI: 검수 통과 매물 수 ·
        순수 가입만으로 전원 증정 금지</td>
      </tr>
      <tr>
        <td class="k">시드 매물 게이트</td>
        <td>공개 오픈 조건: <strong>데모 URL·스크린샷·한 줄 설명·키워드 필수</strong> 매물
        최소 M건(예: 15~30) 진열 후 구매자 캠페인 시작 · “빈 장터” 오픈 금지 ·
        Phase 0 Pre-Open 1~2주 → Phase 1 Open Auction Day</td>
      </tr>
      <tr>
        <td class="k">폴더 청산 캠페인</td>
        <td>카피: “안 쓰는 사이드 프로젝트, 등록 3분이면 끝” ·
        커뮤니티 주 2회 게시 + 1:1 DM 주 10건 · KPI: 주간 신규 등록</td>
      </tr>
      <tr>
        <td class="k">오픈일 경매 이벤트</td>
        <td>관심(워치) 수집 → 오픈일 동시 경매 시작 ·
        판매자에게 “관심 수 미리 공개”로 동기 부여 · KPI: 관심 대비 입찰 전환</td>
      </tr>
      <tr>
        <td class="k">추천·초대</td>
        <td>판매자 초대 코드 · 피추천 등록 시 양측 노출 부스트(유료 아님) ·
        KPI: 초대 경유 등록 비율</td>
      </tr>
      <tr>
        <td class="k">운영 대행 마찰 제거</td>
        <td>등록 템플릿·가격 가이드(시세 힌트, 감정 아님) ·
        검수 피드백 24~48h · “거절 사유 표준화”로 재등록률 상승</td>
      </tr>
    </tbody>
  </table>
  <ul>
    <li><strong>RoadLog</strong>: 라이브 URL 기준 데모 → Free 15회 → Pro claim · 주간 “일지 1회 생성” 온보딩 체크</li>
    <li><strong>Trace</strong>: 설치 후 1회 인터뷰 WOW 데모 영상 · 체험 라이선스 → 유료 (수익·순위 보장 문구 금지)</li>
    <li>브랜딩: 제품 영문 표기 · 상호·세금·약관은 CoreLabs · 유료 광고는 캐시카우 검증 후</li>
  </ul>
</section>

<section class="sec">
  <div class="sec-h">08 운영 및 조직</div>
  <ul>
    <li>초기: 1인(또는 소수) 스튜디오 — 개발·운영·검수·고객응대 · <strong>주간 리소스 보드</strong>로 제품별 시간 기록</li>
    <li>WakeAgain 매물 형식·데모 검수: 보통 1~2영업일 (가치 감정 아님 · 거절 사유 템플릿)</li>
    <li>클라우드 호스팅(Railway) · 관리자 탭(매물·회원·후기·수수료·매출·신고) · 신고·차단·경매 중단 ·
    스케줄러(마감·입금·검수 기한)</li>
    <li>품질: 거래/입찰 자동화 테스트 · <strong>bug_watch</strong> 상시 감시(알림 ntfy/Telegram/Discord) ·
    SQLite 로컬 백업 + S3 호환 오프사이트 백업 골격</li>
    <li>메일: Resend(HTTPS) · 도메인 인증 완료 · 발송 실패 시 앱 내 코드 폴백</li>
    <li>RoadLog: production 모니터링 · Volume 영속 · 장애 시 최우선 복구</li>
    <li>Trace: 설치 패키지·업데이트 · BYOK 로컬 키 관리 원칙</li>
    <li>만 14세 미만 가입 불가 · 단계별 신원 · 약관·개인정보처리방침 ·
    <strong>사업자 번호는 등록 후 푸터·약관 게시</strong></li>
  </ul>
</section>

<section class="sec">
  <div class="sec-h">09 추진 일정 (실행 로드맵)</div>
  <table>
    <thead><tr><th style="width:16%">단계</th><th>내용 · 완료 정의</th></tr></thead>
    <tbody>
      <tr><td class="k">0. 지금<br/>기반</td>
        <td><strong>CoreLabs 사업자등록</strong> · 통신판매/중개 고지 · 약관·푸터 상호·사업자번호 ·
        RoadLog·WA 사이트 반영 · 분쟁 접수 채널·SLA 초안 게시 ·
        <strong>Google Play 콘솔 제출(AAB·스토어 리스팅)</strong></td></tr>
      <tr><td class="k">1. 결제</td>
        <td>PG 신청·연동 · RoadLog 유료 경로 안정화 · WA 결제 링크·웹훅·정산 자동화 ·
        차순위·1h 타이머 실동작 · 오프플랫폼 입금 경로 없음 확인</td></tr>
      <tr><td class="k">2. 캐시<br/>집중</td>
        <td>RoadLog Free→Pro 전환 캠페인 · 주간 생성·유료 KPI ·
        장애 0건 유지 · (여유 시) Enterprise 1팀 파일럿</td></tr>
      <tr><td class="k">3. WA<br/>공급</td>
        <td>Founding Seller(매물 조건+Trace 라이선스) · 시드 매물 M건 · 데모·키워드 게이트 ·
        관심 KPI · 오픈일 경매 · <strong>초기 성사 건 운영자 개입</strong></td></tr>
      <tr><td class="k">4. 확장</td>
        <td>wakeagain.com 고도화 · 부스트 유료 상품 · Apple App Store · Trace 스케일 ·
        SNS OAuth · 분쟁 프로세스 고도화 · 해외는 한국 정산·약관 우선 후 검토</td></tr>
    </tbody>
  </table>
  <p class="fine">현재(2026-07-25): RoadLog production · WakeAgain Railway 라이브(검색·입찰·차단·관리자·PWA) ·
  Play 제출 패키지 준비 · Trace 설치형 · <strong>남은 게이트: 사업자 → PG → 실오픈 홍보</strong>.</p>
</section>

<section class="sec">
  <div class="sec-h">10 손익·재무 가정 (초기 스케치)</div>
  <p class="fine">※ 실제 수치는 런칭 후 데이터로 갱신. 계획용 가정이며, 손익 분기는 <strong>RoadLog 구독 먼저</strong> 맞추는 것을 우선합니다.</p>
  <ul>
    <li><strong>RoadLog (1순위 매출)</strong>: Free 유입 → Pro 월 2,900원 · Enterprise 팀 · 서버비 연동 ·
    목표: 월 고정비(호스팅·도메인·도구)를 Pro 소수로 커버 가능한 구간 조기 확인</li>
    <li><strong>WakeAgain</strong>: 성사 1건 거래대금 예 50만~150만 원 · 수수료 10% → 건당 약 5만~15만 원
    (부가세 별도) · 초기 우대 수수료 구간은 의도적 손실 허용(신뢰·리뷰 확보)</li>
    <li><strong>Trace</strong>: 월 ~3만 원 구독·라이선스 · BYOK로 AI 원가 이전 · Phase 2 본격화</li>
    <li>고정비: 호스팅, 도메인, PG 수수료, 검수 시간, 최소 마케팅</li>
    <li>투자·파트너 관점: “이미 라이브 과금 경로 + 플랫폼 옵션성” — 아이디어만 있는 팀과 차별</li>
  </ul>
</section>

<section class="sec">
  <div class="sec-h">11 리스크 · 법적·운영 대응 (강화)</div>
  <table>
    <thead><tr><th style="width:26%">리스크</th><th>대응</th></tr></thead>
    <tbody>
      <tr><td class="k">리소스 분산</td><td>Phase 0~2 화력 배분 표(§01-B) · 주간 시간 보드 ·
      캐시카우 장애 시 전 제품 개발 중단 후 복구</td></tr>
      <tr><td class="k">직거래·사기 유도</td><td>채팅 상단 고정 고지 · 외부 거래 유도 키워드 모니터링 ·
      신고 시 계정 정지·경매 중단 · <strong>유저 차단</strong></td></tr>
      <tr><td class="k">허위·먹튀 매물</td><td>데모 필수 게이트 · 형식 검수 · 누적 신고 시 영구 제한 ·
      초기 성사 건 정산 전 운영 확인</td></tr>
      <tr><td class="k">미입금·장난 입찰</td><td>1시간 결제 기한 · 미결제 낙찰 무효 · 차순위 자동 재낙찰 · 신용·재입찰 제한</td></tr>
      <tr><td class="k">앱스토어 정책</td><td>만 14세 · 차단·신고 · 개인정보 방침 · Play 콘텐츠 등급 정합 ·
      실서비스 전 사업자·결제 정책 정비</td></tr>
      <tr><td class="k">데이터 유실</td><td>Volume 영속 · 로컬 백업 · 오프사이트(S3 호환) 백업 골격 · 파괴적 작업 잠금</td></tr>
      <tr><td class="k">중개 책임·분쟁</td><td>약관 면책 + <strong>분쟁 접수 창구·처리 기한(SLA)</strong> 명시 ·
      전자상거래 소비자 보호 의무 범위 안내 · 필요 시 전문 자문 ·
      <strong>초기 N건 운영자 개입 기준</strong>(아래)</td></tr>
      <tr><td class="k">콜드스타트</td><td>판매자 훅 6종(§07) · 시드 매물 전 구매자 광고 금지 ·
      RoadLog 현금으로 운영 지속성 확보</td></tr>
      <tr><td class="k">AI 비용·품질</td><td>RoadLog hybrid·한도 · Trace BYOK · 허위 경험 창작 금지</td></tr>
      <tr><td class="k">규제·신고</td><td>사업자·통신판매(중개) 고지 · 환불·청약 관련 고지 정비</td></tr>
    </tbody>
  </table>
  <h3>WakeAgain · 초기 거래 운영자 개입 기준 (신뢰 구축용)</h3>
  <ul>
    <li><strong>적용 구간</strong>: 공개 오픈 후 성사 거래 초기 구간(예: 첫 20~50건) 또는 월간 분쟁 비율 임계치 초과 시</li>
    <li><strong>개입 트리거</strong>: 미이전 · 데모 불일치 신고 · 외부 입금 유도 · 48시간 인수 전 분쟁 접수</li>
    <li><strong>조치</strong>: 거래 일시 중지 · 양측 자료 요청(24h) · 규정에 따른 낙찰 무효·재진행·계정 제재 · 기록 보관</li>
    <li><strong>원칙</strong>: 품질·가치 보증은 하지 않음. 다만 <strong>절차 위반·명백한 사기 징후</strong>에는 중개자로서 조치</li>
    <li><strong>목표</strong>: 초기에 “먹튀 가능한 장터” 이미지를 차단 → 이후 자동화 비중 확대</li>
  </ul>
</section>

<section class="sec">
  <div class="sec-h">12 결론 및 실행 약속</div>
  <div class="closing">
    코어랩스는 <strong>이미 라이브인 RoadLog로 현금 흐름과 운영 신뢰를 만들고</strong>,
    <strong>WakeAgain으로 사이드 프로젝트 양면 시장을 키우며</strong>,
    <strong>Trace로 작성 도구 포트폴리오를 확장</strong>합니다.
    세 제품을 나열하는 것이 아니라, <strong>집중 순서·법적 개입 기준·판매자 그로스 훅</strong>까지 명시한 실행 계획입니다.
  </div>
  <p><strong>향후 90일 실행 약속:</strong></p>
  <ol>
    <li><strong>사업자등록</strong> 완료 후 약관·중개 고지·분쟁 SLA·푸터 사업자번호를 사이트에 반영</li>
    <li>PG 연동 및 RoadLog 유료 전환 경로 안정화 (캐시카우 KPI) · WA 결제 웹훅 가동</li>
    <li>Google Play 제출·심사 대응 · (후속) App Store</li>
    <li>WakeAgain Founding Seller + 시드 매물 게이트 달성 후 오픈 이벤트</li>
    <li>초기 성사 거래 운영자 개입 로그 축적 → 자동화 기준 고도화</li>
  </ol>
  <p class="fine" style="margin-top:10px">
    본 문서는 사업 방향·운영 원칙·리스크 대응·<strong>제품 구현 현황</strong>을 정리한 계획서이며,
    세부 수치·요금·일정은 시장 반응과 행정 절차에 따라 조정합니다.
    아이디어가 아니라 <strong>동작하는 제품·도메인·스토어 패키지</strong>를 전제로 합니다.
  </p>
  <div class="callout" style="margin-top:12px">
    운영: <strong>코어랩스(CoreLabs)</strong> · 대표 호현수<br/>
    문의: <strong>corelabs.studio@gmail.com</strong><br/>
    도메인: <strong>https://wakeagain.com</strong> · <strong>https://roadlog.co.kr</strong> · Trace 설치형<br/>
    © 2026 CoreLabs · WakeAgain · RoadLog · Trace · Business Plan <strong>v6.0</strong>
  </div>
</section>

<p class="doc-foot">corelabs.studio@gmail.com · CoreLabs Business Plan · 2026.07.25 · v6.0</p>

</body>
</html>
"""


def render_pdf(html: str, out: Path) -> None:
    from playwright.sync_api import sync_playwright

    out.parent.mkdir(parents=True, exist_ok=True)
    html_path = OUT_HTML
    html_path.write_text(html, encoding="utf-8")
    print("html:", html_path)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.evaluate("() => document.fonts.ready")
        page.wait_for_timeout(500)
        page.pdf(
            path=str(out),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()
    print("OK", out, out.stat().st_size if out.is_file() else 0)


def main() -> int:
    logo = logo_data_uri()
    html = build_html(logo)
    try:
        render_pdf(html, OUT_PDF)
    except Exception as e:
        print("playwright pdf failed:", e)
        OUT_HTML.write_text(html, encoding="utf-8")
        print("wrote HTML only:", OUT_HTML)
        return 1
    # Desktop aliases (user-facing names)
    for alias in (OUT_ALIAS_SHORT, OUT_ALIAS_SIMPLE):
        try:
            alias.write_bytes(OUT_PDF.read_bytes())
            print("alias:", alias)
        except Exception as e:
            print("alias copy skip:", alias, e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
