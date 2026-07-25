# -*- coding: utf-8 -*-
"""CoreLabs 제품 포트폴리오 PDF 3종 — WakeAgain / RoadLog / Trace."""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESK = Path(os.path.expanduser("~")) / "Desktop"

LOGO_CANDIDATES = [
    ROOT / "public" / "assets" / "corelabs-logo-lockup.jpg",
    ROOT / "public" / "assets" / "corelabs-logo-lockup.png",
    ROOT / "public" / "assets" / "corelabs-logo-mark.png",
    Path(r"C:\Users\hysoo\Projects\RoadLog\docs\marketing\brand\corelabs_logo_wordmark.png"),
]


def logo_data_uri() -> str:
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
                pad = 18
                im = im.crop(
                    (
                        max(0, min_x - pad),
                        max(0, min_y - pad),
                        min(w, max_x + 1 + pad),
                        min(h, max_y + 1 + pad),
                    )
                )
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            print("logo:", p.name, im.size)
            return f"data:image/png;base64,{b64}"
        except Exception as e:
            print("logo fail", p, e)
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
            return f"data:{mime};base64,{b64}"
    return ""


def font_faces() -> str:
    fonts_dir = Path(__file__).resolve().parent / "fonts"
    win = Path(r"C:\Windows\Fonts")
    pairs = [
        (fonts_dir / "malgun.ttf", "DocKR", "400"),
        (fonts_dir / "malgunbd.ttf", "DocKR", "700"),
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
    print("fonts:", len(rules))
    return "\n".join(rules)


# ── product content ─────────────────────────────────────────

PRODUCTS: list[dict] = [
    {
        "id": "wakeagain",
        "file": "WakeAgain_포트폴리오.pdf",
        "file_alias": "WakeAgain 포트폴리오.pdf",  # user-facing Desktop name
        "name": "WakeAgain",
        "subtitle": "잠든 디지털 프로젝트 거래 장터",
        "tagline": "프로젝트에 두 번째 기회를 주세요.",
        "role": "주사업 · 통신판매중개",
        "version_label": "2026년 7월 25일 · v2.0",
        "bullets": [
            "사이드·MVP·프로토타입을 공개 호가（경매）로 연결하는 시간 거래소",
            "키워드 검색 · 안전거래 루프 · 신원 게이트 · 유저 차단까지 구현",
            "웹 · PWA · Android（Play AAB 제출 패키지 준비）· https://wakeagain.com 라이브",
        ],
        "domain_label": "도메인 · 접속 · 채널",
        "domain_value": (
            "공식 도메인 <strong>https://wakeagain.com</strong>（등록·소유 완료 · 라이브）<br/>"
            "클라우드: Railway · 앱 셸 <strong>/app/</strong> · PWA · "
            "Capacitor Android · <strong>Google Play AAB·스크린샷 패키지 준비（2026-07-25）</strong>"
        ),
        "screenshots": [
            ("메인 랜딩", "wa_home.png"),
            ("앱 · 매물 목록", "wa_app.png"),
            ("Play · 마켓", "wa_play_market.png"),
            ("Play · 매물 상세", "wa_play_detail.png"),
        ],
        "overview": (
            "WakeAgain은 방치된 앱·프로토타입·SaaS·도구 등 디지털 프로젝트를 "
            "공개 호가（경매·가격 쓰기）로 연결하는 <strong>거래 중개 마켓플레이스</strong>입니다. "
            "포지션은 <strong>시간 거래소</strong> — “다시 만들기 싫을 때” 돌아가는 초안을 인수하는 장터입니다. "
            "코어랩스（CoreLabs）가 운영하며, 전자상거래법상 <strong>통신판매중개자</strong>로서 "
            "거래 당사자가 아닙니다. 매물 품질·사기 1차 책임은 이용자에게 있습니다. "
            "서비스는 이미 <strong>https://wakeagain.com</strong> 에서 라이브이며, "
            "웹·PWA·네이티브 앱（Capacitor）이 <strong>동일 JWT API·동일 데이터</strong>를 공유합니다. "
            "실결제·실홍보는 <strong>사업자 등록 및 PG 연동 후</strong>에만 진행합니다."
        ),
        "snapshot": [
            ("제품명", "WakeAgain"),
            ("운영 회사", "코어랩스（CoreLabs）· 대표 호현수"),
            ("포지션", "디지털 프로젝트 장터 · 사이드·MVP 특화 · 시간 거래소"),
            ("형태", "웹 + PWA + Android（Play AAB 준비）· iOS 후속"),
            ("법적 지위", "통신판매중개자（거래 당사자 아님）"),
            ("수익", "등록 무료 · 성사 시 판매자 수수료 10% · 향후 상위 노출（부스트）"),
            ("도메인", "https://wakeagain.com （등록 완료 · 라이브）"),
            ("문의", "corelabs.studio@gmail.com"),
        ],
        "status": [
            ("마켓·검색", "목록·상세·관심 · 키워드 1~5 등록 · 서버사이드 검색 · AI 키워드 추천 · 카테고리"),
            ("경매·거래", "공개 호가 · 입찰 동기화 · 스케줄러 마감 · 딜 상태머신 · 차순위 재낙찰 · 수수료 10%"),
            ("신뢰", "Lv1 입찰 / Lv2 결제·인수 / Lv3 정산 · 만14세 · 유저 차단 · 신고 · 외부직거래 고지"),
            ("멀티채널", "웹 랜딩 · /app 셸 · PWA · Capacitor Android · Play 제출용 AAB·에셋"),
            ("운영·품질", "관리자（매물·회원·매출 등）· Resend 메일 · 백업 · bug_watch · 자동화 테스트"),
            ("의도적 미완", "사업자 번호 게시 · PG 실결제·웹훅 · SNS OAuth · iOS · 부스트 유료 UI"),
        ],
        "problems": [
            "사이드 프로젝트·MVP 대량 생산 후 유저·수익 없이 방치",
            "커뮤니티·중고 거래: 가격 기준·데모 검증·이전 절차 부재",
            "직거래 유도·사기 위험, 중개 책임 경계 불명확",
            "대형 M&A 플랫폼은 사이드 프로젝트 규모에 문턱이 높음",
            "매물 많아지면 카테고리만으로는 발견이 어려움 → 키워드 검색 필수",
        ],
        "values": [
            ("특화", "사이드·MVP 공개 호가 장터"),
            ("투명", "데모·현재가·입찰·배지 공개"),
            ("절차", "안전거래 · 차단·신고·Lv"),
            ("채널", "웹·PWA·Play 동일 API"),
        ],
        "flow": [
            ("1. 등록", "무료 등록 · 키워드 1~5 · 데모·형식 검수 후 공개（보통 1~2영업일, 품질 보증 아님）"),
            ("2. 발견·관심", "키워드 검색·카테고리 · 관심 등록 · 30초 무료 진단（통계 힌트, 감정가 아님）"),
            ("3. 입찰", "공개 현재가·고유 입찰자 수 · 헤비 구매자 배지 · Lv1（이메일）부터 가격 쓰기"),
            ("4. 낙찰·결제", "가격 확정 · PG 결제（목표 1시간）· 미입금 시 차순위 자동 재낙찰"),
            ("5. 이전·인수", "이전 → 검수·인수（기본 48시간 무이의 시 자동 확정）"),
            ("6. 정산", "Lv3 계좌 정산 · 플랫폼 수수료 10% · 입금 확인=PG 웹훅 전용"),
        ],
        "features": [
            "키워드 검색·등록（필수 1~5）· AI 키워드 추천 또는 수동 입력",
            "신원 게이트: Lv1 이메일→입찰 / Lv2 실명·휴대폰→결제·인수 / Lv3 계좌→판매자 정산 · 만 14세 미만 차단",
            "안전거래 루프: 낙찰 → PG（1h）→ 이전 → 검수·인수（48h）→ 정산 · 차순위 자동 낙찰 골격",
            "공개 입찰 보드 · 최고 입찰자 카드 · 헤비 구매자 배지 · 쪽지 외부거래 경고 고정",
            "유저↔유저 차단（Play 콘텐츠 등급 대응）· 신고 임계·경매 중단 · 관리자 검수·회원·매출",
            "스케줄러: 경매 마감 자동 낙찰 · 입금·검수 기한 처리",
            "Resend 인증 메일 · 로그인 기억하기 · KO/EN UI · 표시 통화 기반（정산 원화 우선）",
            "프리미엄 상위 노출（부스트）: DB·목록 정렬 골격 완료 · 결제 상품 UI는 PG 후",
        ],
        "tech": [
            ("스택", "FastAPI（/api/v1 JWT）+ 정적 웹 · SQLite · Railway"),
            ("도메인", "https://wakeagain.com 등록·라이브"),
            ("데이터", "서버 저장 · 관리자 검수 · 로컬·오프사이트 백업 골격"),
            ("결제", "딜 상태머신 완료 · PG 웹훅 연동 후 실운영（수동 입금 확인 경로 없음）"),
            ("플랫폼", "웹 · PWA · Capacitor Android（AAB）· App Store 후속"),
            ("품질", "입찰·딜 E2E 테스트 · bug_watch 상시 감시 · predeploy 게이트"),
        ],
        "business": [
            "등록·관심·입찰 무료",
            "성사 시 판매자 거래대금의 10%（미성사 시 0）",
            "구매자 추가 수수료 없음（초기）",
            "향후: 상위 노출 부스트 등 부가 상품（DB 골격 완료 · PG 후 상품화）",
            "오프플랫폼 입금 경로 없음 · PG 연동 후 실거래 · 사업자 전 실홍보 금지",
        ],
        "users": [
            "판매자: 사이드·MVP 메이커, 바이브 코더, 인디 메이커 — 프로토타입 정리·현금화",
            "구매자: 바이브 코더 → 인디해커 → 마케터 → 대표 → 크리에이터 — 시간 절약·데모 있는 자산",
            "채널: 바이브 코딩·인디해커 커뮤니티 우선 · 매물 진열 후 구매자 모객",
        ],
        "growth_note": (
            "<strong>콜드스타트（초기 매물 확보）실행</strong> — "
            "<strong>Founding Seller</strong>: 순수 가입 증정이 아니라 "
            "<strong>매물 등록·검수 통과</strong> 조건 + Trace 기간 라이선스（90일/6개월）·뱃지·노출 우선. "
            "Phase 0 Pre-Open（1~2주）시드 매물 → Phase 1 Open Auction Day. "
            "데모 URL·키워드·한 줄 설명이 있는 매물만 공개해 ‘빈 장터’ 오픈을 피합니다. "
            "미끼: 가입 불필요 <strong>/diagnose.html</strong> 30초 진단（감정가 아님）."
        ),
        "closing": "잠든 프로젝트에 다시 기회를. — WakeAgain by CoreLabs（대표 호현수） · https://wakeagain.com",
        "disclaimer": (
            "본 포트폴리오는 제품 소개·구현 현황 공유용입니다. WakeAgain은 통신판매중개 플랫폼이며, "
            "매물 품질·가치·사기에 대한 1차 책임은 이용자에게 있습니다. "
            "세부 수수료·일정·기능은 운영 정책에 따라 조정될 수 있습니다. "
            "PG·사업자 전 실결제·실홍보는 하지 않습니다. 라이브: https://wakeagain.com"
        ),
        "abbr": (
            "<strong>약어</strong> — "
            "<strong>MVP</strong>（Minimum Viable Product）: 최소 기능 시제품 / "
            "<strong>SaaS</strong>（Software as a Service）: 구독형 소프트웨어 / "
            "<strong>PG</strong>（Payment Gateway）: 결제대행 / "
            "<strong>PWA</strong>（Progressive Web App）: 설치형 웹앱 / "
            "<strong>AAB</strong>（Android App Bundle）: Google Play 제출 패키지 / "
            "<strong>JWT</strong>: API 인증 토큰 / "
            "<strong>M&amp;A</strong>（Mergers and Acquisitions）: 인수합병 / "
            "<strong>API</strong>（Application Programming Interface）: 프로그램 연동 창구"
        ),
    },
    {
        "id": "roadlog",
        "file": "RoadLog_포트폴리오.pdf",
        "name": "RoadLog",
        "subtitle": "AI 운행·외근 일지 · 제출용 문서 정리",
        "tagline": "오늘 현장 기록, 제출까지 한 번에.",
        "role": "부사업 ① · 캐시카우 · 직접 제공 SaaS",
        "bullets": [
            "운행·외근 메모를 회사 제출용 일지로 AI 정리",
            "Excel · PDF · DOCX 다운로드 · 인쇄 · 저장·이어쓰기",
            "공식 도메인 https://roadlog.co.kr 라이브 · 코어랩스 운영",
        ],
        "domain_label": "도메인 · 접속",
        "domain_value": (
            "공식 도메인 <strong>https://roadlog.co.kr</strong>（등록·소유 · production 라이브）<br/>"
            "Railway 클라우드 · OpenAI 연동 · 데이터 Volume 영속（/data）· 재배포 후 데이터 유지 검증 완료"
        ),
        "screenshots": [
            ("메인 · 작성 UI", "rl_home.png"),
            ("요금 · Free/Pro", "rl_pricing.png"),
        ],
        "overview": (
            "RoadLog（로드로그）는 영업·외근·법인차 현장에서 남긴 메모를 "
            "회사 톤의 운행·외근 일지로 정리하는 <strong>웹 SaaS</strong>입니다. "
            "코어랩스（CoreLabs）가 <strong>직접 제공·직접 과금</strong>하며, "
            "Free 체험 후 Pro·Enterprise로 확장할 수 있습니다. "
            "서비스는 이미 <strong>https://roadlog.co.kr</strong> 에서 라이브 중이며, "
            "코어랩스 초기 <strong>캐시카우（즉시 현금 흐름）</strong> 제품으로 화력을 집중합니다."
        ),
        "snapshot": [
            ("제품명", "RoadLog（로드로그）"),
            ("운영 회사", "코어랩스（CoreLabs）· 대표 호현수"),
            ("포지션", "현장 기록 → 제출용 문서 자동화 · 캐시카우"),
            ("형태", "웹 SaaS · PWA 설치 가능"),
            ("법적 지위", "직접 제공 서비스（직접 과금 시 통신판매 성격）"),
            ("요금（런칭가）", "Free 월 15회 · Pro 월 2,900원 · Enterprise 팀"),
            ("도메인", "https://roadlog.co.kr （라이브 production）"),
            ("문의", "corelabs.studio@gmail.com"),
        ],
        "problems": [
            "종이·엑셀·메신저에 흩어진 운행·방문 기록",
            "퇴근 직전 일지 정리로 하루가 길어짐",
            "회사마다 다른 서식·말투에 맞추기 어려움",
            "위치·시간·주행거리를 나중에 기억해 채우기 힘듦",
        ],
        "values": [
            ("스탬프", "도착·출발 위치·시간 원탭"),
            ("AI 정리", "제출 톤 운행·외근 일지"),
            ("서식", "회사 양식 학습·반영"),
            ("산출", "Excel · PDF · DOCX"),
        ],
        "flow": [
            ("1. 스탬프", "현장 도착·출발 시 퀵 스탬프로 시각·GPS 주소 기록"),
            ("2. 입력", "차량·주행거리·오전/오후 방문지·메모 보완"),
            ("3. AI 작성", "제출용 문장으로 정리 · OpenAI 등 엔진 표시"),
            ("4. 수정", "요약·차량번호 등 제출 전 수정 후 저장"),
            ("5. 제출", "다운로드·인쇄 · 계정에 저장 후 이어쓰기"),
        ],
        "features": [
            "운행일지 · 외근·출장 모드",
            "회사 서식 사진·문서 업로드 및 AI 학습",
            "근무시간 맞춤 스마트 진입 · 다국어（KO/EN）",
            "관리자: 매출·사용 횟수·VIP·후기 관리 · 역할 미리보기",
            "Pro claim（스마트스토어 결제 확인）· ntfy 알림",
            "Volume 영속 · 재배포 후 계정·일지 유지 스모크 통과",
            "법적·운영: 약관·개인정보 · Free 한도 고지 · 데모 결제 업그레이드 차단",
        ],
        "tech": [
            ("스택", "FastAPI + 정적 SPA（web/）· Railway Docker"),
            ("도메인", "https://roadlog.co.kr 등록·라이브"),
            ("데이터", "local JSON + Volume /data · Supabase 선택"),
            ("AI", "OpenAI（gpt-4o-mini）· hybrid 비용 모드 · 키 유효 검증"),
            ("신뢰", "storage_persistent · launch_ready production"),
        ],
        "business": [
            "Free: 월 15회 생성 · Excel/PDF/DOCX · 서식 학습",
            "Pro: 월 2,900원（런칭가）· 무제한·광고 제거 지향",
            "Enterprise: 팀 좌석 · 승인/반려 · 세금계산서",
            "결제: 스마트스토어 claim · PG 정식 연동 확장",
            "수익 구조: 코어랩스 직접 과금（중개 아님）· 초기 캐시카우",
        ],
        "users": [
            "영업·외근 직원, 법인차 운전자",
            "일지 제출이 잦은 개인·프리랜서",
            "팀 단위 일지·승인 관리가 필요한 중소 법인",
        ],
        "growth_note": (
            "<strong>초기 유입·전환 실행</strong> — "
            "지인 DM 3~5명 → 영업·외근 오픈채 1곳 → Free 15회 체험 → "
            "「제출 1회 성공」온보딩 후 Pro claim. "
            "라이브 URL（roadlog.co.kr）로 데모하고, 주간 KPI는 "
            "<strong>신규 가입 · 생성 성공 · 유료 전환</strong>입니다. "
            "유료 광고는 전환 검증 후."
        ),
        "closing": (
            "제출은 단정하게, 입력은 편하게. — RoadLog by CoreLabs（대표 호현수） · "
            "https://roadlog.co.kr"
        ),
        "disclaimer": (
            "본 포트폴리오는 제품 소개용입니다. RoadLog는 일지 작성·문서화를 지원하며, "
            "특정 회사의 법적 서식 적합성을 보증하지 않습니다. "
            "요금·한도·기능은 운영 정책에 따라 변경될 수 있습니다. "
            "라이브: https://roadlog.co.kr"
        ),
        "abbr": (
            "<strong>약어</strong> — "
            "<strong>SaaS</strong>（Software as a Service）: 웹 구독형 소프트웨어 / "
            "<strong>Cash Cow</strong>: 즉시 현금 흐름 제품 / "
            "<strong>AI</strong>（Artificial Intelligence）: 인공지능 / "
            "<strong>API</strong>（Application Programming Interface）: 프로그램 연동 창구 / "
            "<strong>PWA</strong>（Progressive Web App）: 설치형 웹앱 / "
            "<strong>GPS</strong>（Global Positioning System）: 위치 확인 / "
            "<strong>SPA</strong>（Single Page Application）: 단일 페이지 웹앱 / "
            "<strong>PG</strong>（Payment Gateway）: 결제대행"
        ),
    },
    {
        "id": "trace",
        "file": "Trace_포트폴리오.pdf",
        "name": "Trace",
        "subtitle": "인터뷰 기반 AI 경험글 작성 도구",
        "tagline": "말만 하면, 사람들이 읽고 머물 경험글",
        "role": "부사업 ② · Phase 2 · 직접 제공 데스크톱 도구",
        "bullets": [
            "취재형 인터뷰로 행동·사실 재료를 채운다",
            "내 글처럼 정리 — 창작·물타기 금지",
            "설치형 Trace.exe · 코어랩스 직접 제공 · BYOK로 원가 방어",
        ],
        "domain_label": "배포 · 실행 경로",
        "domain_value": (
            "Windows 설치형 <strong>Trace.exe</strong>（설치 경로 예: C:\\Trace\\Trace.exe）· 라이선스 파일 운영<br/>"
            "웹 SaaS가 아닌 <strong>데스크톱 제품</strong> · 판매·데모 채널은 코어랩스 문의·설치 패키지로 연결 "
            "（전용 마케팅 랜딩은 채널 확정 시 추가）"
        ),
        "screenshots": [
            ("데스크톱 UI", "trace_ui.png"),
        ],
        "overview": (
            "Trace는 일반 요약 AI·SEO 나열기가 아닙니다. 관찰 가능한 행동과 사실을 인터뷰로 끌어내, "
            "E-E-A-T형 경험 후기 본문과 발행 패키지까지 만드는 <strong>데스크톱 작성 도구</strong>입니다. "
            "운영: 코어랩스（CoreLabs）· 대표 호현수. "
            "코어랩스 포트폴리오상 <strong>2단계（Phase 2）</strong> 제품으로, "
            "RoadLog 캐시 안정 후 화력을 키우되 제품·설치 패키지는 이미 준비합니다."
        ),
        "snapshot": [
            ("제품명", "Trace"),
            ("운영 회사", "코어랩스（CoreLabs）· 대표 호현수"),
            ("포지션", "취재 에디터 + 블로그 컨설턴트 · Phase 2"),
            ("형태", "Windows 데스크톱 앱（Trace.exe / 설치 패키지）"),
            ("핵심 KPI", "한 판 인터뷰 WOW — 내가 말한 건데 나보다 정리 잘됨"),
            ("가격 지향", "월 약 3만 원대 가성비·인터뷰 퀄 체감"),
            ("AI", "BYOK（사용자 본인 API 키）· 없는 경험 창작 금지"),
            ("문의", "corelabs.studio@gmail.com"),
        ],
        "problems": [
            "말은 풍부한데 글로 옮기면 밋밋하거나 AI 티가 남",
            "일반 요약·키워드 나열은 ‘내가 겪은 일’이 약해 신뢰·체류가 약함",
            "물타기 장문·없는 경험 창작은 장기적으로 브랜드를 해침",
            "본문만 있고 사진·태그·어디에 올릴지 가이드가 없음",
        ],
        "values": [
            ("진정성", "말한 경험만"),
            ("E-E-A-T", "경험 밀도 우선"),
            ("원칙", "물타기·허위 창작 금지"),
            ("패키지", "본문+발행 가이드"),
        ],
        "flow": [
            ("1. 글 주제", "빈 시작·발견 또는 직접 입력"),
            ("2. 경험 인터뷰", "목적 1회 → 순차 행동·사실 →（선택）감정 1회"),
            ("3. 답변", "타이핑 또는 음성"),
            ("4. 기사로 엮기", "구조 플랜 → 경험 후기형 초안"),
            ("5. 결과·패키지", "제목·메타·태그·포스팅 가이드·미리보기"),
            ("6. 발행", "티스토리/네이버 등 수동（자동 로그인·자동 발행 없음）"),
        ],
        "features": [
            "질문 성공 기준: 친구가 답하면 그 답만으로 문단 1개를 쓸 수 있는가",
            "우선 질문: 본 것/한 것 · 선택 · 대기·가격·분 · 막힘 후 행동",
            "내지 않는 질문: 몸 반응·미래형·중간 감정 추측·뻔한 시적 클로즈업",
            "초안 골격: 훅 → 장면 → 막힘 → 생각/행동（말한 것만）→ 결과",
            "산출: Markdown · 티스토리 HTML · 미리보기 · 세션 히스토리·메모리",
            "책임 범위 고지: 읽힐 글·발행 준비까지 — 수익·순위 보장 없음",
        ],
        "tech": [
            ("실행", "C:\\Trace\\Trace.exe（설치형 · 실물 배포 가능）"),
            ("소스", "Python 데스크톱 앱 기반"),
            ("설치", "Inno Setup 등 설치 패키지"),
            ("AI 키", "XAI 등 BYOK · 로컬 .env — 서버 원가 이전"),
            ("데이터", "history · memory · 초안 · user_profile · license"),
        ],
        "business": [
            "형태: 구독 또는 기간 라이선스（체감 월 약 3만 원）",
            "판매 바 = 기능 목록이 아니라 인터뷰 퀄·정리력·가성비 체감",
            "금지: 수익 보장, 감성 일기 AI, 모호한 ‘가장 쉬운 기록’ 포지션",
            "수익 구조: 코어랩스 직접 제공 도구（중개 아님）",
            "원가: BYOK로 AI 호출 비용을 사용자 키로 분산",
        ],
        "users": [
            "경험·후기·리뷰를 꾸준히 쓰는 블로거·리뷰어",
            "말은 많은데 구조화가 어려운 스토리텔러·창업 기록자",
            "‘내 경험’을 지키면서 읽히는 본문이 필요한 크리에이터",
        ],
        "growth_note": (
            "<strong>초기 배포·전환 실행（Phase 2 집중 시）</strong> — "
            "설치 패키지 + <strong>1회 인터뷰 WOW 데모 영상</strong>으로 "
            "블로거·리뷰어 커뮤니티에 체험 라이선스를 뿌리고, "
            "「내가 말한 건데 나보다 정리 잘됨」체감 후 유료 전환. "
            "수익·애드센스·검색 순위 보장 문구는 쓰지 않습니다. "
            "RoadLog 캐시 안정 전에도 제품 완성·버그 수정은 유지합니다."
        ),
        "closing": "인터뷰로 재료를 채우고, 경험글로 남긴다. — Trace by CoreLabs（대표 호현수）",
        "disclaimer": (
            "본 포트폴리오는 제품 소개용입니다. Trace는 읽힐 글·발행 준비를 도우며, "
            "수익·검색 순위·광고 수익을 보장하지 않습니다. "
            "AI는 사용자가 말한 경험을 정리하는 데 쓰이며, 없는 경험을 창작하지 않는 것을 원칙으로 합니다. "
            "운영: 코어랩스（CoreLabs）."
        ),
        "abbr": (
            "<strong>약어</strong> — "
            "<strong>AI</strong>（Artificial Intelligence）: 인공지능 / "
            "<strong>SEO</strong>（Search Engine Optimization）: 검색 최적화 / "
            "<strong>LLM</strong>（Large Language Model）: 대규모 언어 모델 / "
            "<strong>BYOK</strong>（Bring Your Own Key）: 사용자 본인 API 키 / "
            "<strong>E-E-A-T</strong>（Experience, Expertise, Authoritativeness, Trustworthiness）: 경험·전문성·권위·신뢰 / "
            "<strong>KPI</strong>（Key Performance Indicator）: 핵심 성과 지표"
        ),
    },
]


def css(fonts: str) -> str:
    return f"""
{fonts}
  @page {{ size: A4; margin: 12mm 12mm 14mm 12mm; }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0;
    font-family: "DocKR", "Malgun Gothic", "맑은 고딕", sans-serif;
    color: #1e293b;
    font-size: 9.5pt;
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
  }}

  /* Cover: no fixed full-page height (avoids blank page 2) */
  .cover {{
    page-break-after: always;
    break-after: page;
  }}
  .cover-top {{
    background: var(--navy);
    color: #fff;
    padding: 14mm 12mm 11mm;
    text-align: center;
    position: relative;
  }}
  .cover-top::after {{
    content: "";
    position: absolute; left: 0; right: 0; bottom: 0; height: 5px;
    background: linear-gradient(90deg, var(--purple-deep), var(--purple), #c084fc);
  }}
  .cover-kicker {{
    letter-spacing: 0.2em;
    font-size: 8.5pt;
    color: #94a3b8;
    font-weight: 600;
    margin-bottom: 10px;
  }}
  .cover-logo {{
    display: block;
    height: 42px;
    width: auto;
    max-width: 250px;
    margin: 0 auto 10px;
    object-fit: contain;
    background: #fff;
    padding: 8px 16px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
  }}
  .cover-logo-fallback {{
    font-size: 18pt; font-weight: 800; color: #fff; margin-bottom: 10px;
  }}
  .cover-product {{
    font-size: 26pt;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 4px 0 4px;
  }}
  .cover-sub {{
    font-size: 11pt;
    color: #c4b5fd;
    font-weight: 600;
    margin: 0 0 8px;
  }}
  .cover-role {{
    display: inline-block;
    background: rgba(168,85,247,0.2);
    border: 1px solid rgba(196,181,253,0.45);
    color: #e9d5ff;
    font-size: 8pt;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 999px;
  }}
  .cover-body {{
    padding: 7mm 8mm 4mm;
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .cover-tagline {{
    font-size: 13pt;
    font-weight: 800;
    color: var(--navy-2);
    text-align: center;
    margin: 0 0 4mm;
  }}
  .cover-bullets {{
    width: 100%;
    max-width: 460px;
    margin: 0 0 5mm;
    padding: 0;
    list-style: none;
  }}
  .cover-bullets li {{
    position: relative;
    padding: 6px 10px 6px 22px;
    margin: 0 0 4px;
    background: var(--soft-purple);
    border-radius: 8px;
    font-size: 9.2pt;
    color: #334155;
  }}
  .cover-bullets li::before {{
    content: "";
    position: absolute;
    left: 9px; top: 11px;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--purple);
  }}
  .company-banner {{
    width: 100%;
    max-width: 460px;
    background: linear-gradient(90deg, #0b1220, #1e1b4b);
    color: #e2e8f0;
    border-radius: 10px;
    padding: 8px 12px;
    margin-bottom: 4mm;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .company-banner img {{
    height: 22px;
    width: auto;
    background: #fff;
    padding: 4px 8px;
    border-radius: 6px;
  }}
  .company-banner .txt {{
    font-size: 8.5pt;
    line-height: 1.4;
  }}
  .company-banner strong {{ color: #fff; }}
  .meta-box {{
    width: 100%;
    max-width: 420px;
    background: var(--soft);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 7px 14px;
  }}
  .meta-row {{
    display: grid;
    grid-template-columns: 56px 1fr;
    gap: 8px;
    padding: 5px 0;
    font-size: 9.3pt;
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
    margin: 0 0 9px;
    font-size: 8pt;
    color: var(--muted);
  }}
  .doc-header .left {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }}
  .header-mark {{ height: 15px; width: auto; object-fit: contain; }}

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
  }}
  .domain-box {{
    border: 1px solid #c4b5fd;
    background: #faf5ff;
    border-radius: 8px;
    padding: 8px 10px;
    margin: 0 0 8px;
    font-size: 9pt;
  }}
  .domain-box .lab {{
    font-size: 7.5pt;
    font-weight: 800;
    color: var(--purple-deep);
    letter-spacing: 0.04em;
    margin-bottom: 2px;
  }}
  .shot-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 6px 0 8px;
  }}
  .shot-grid.cols-4 {{
    grid-template-columns: 1fr 1fr;
  }}
  .shot {{
    border: 1px solid var(--line);
    border-radius: 10px;
    overflow: hidden;
    background: #0b1220;
  }}
  .shot img {{
    display: block;
    width: 100%;
    height: 110px;
    object-fit: cover;
    object-position: top center;
  }}
  .shot.phone img {{
    height: 150px;
    object-fit: contain;
    object-position: center top;
    background: #0b1220;
  }}
  .shot .cap {{
    background: #fff;
    font-size: 7.5pt;
    font-weight: 700;
    color: #475569;
    padding: 4px 8px;
    border-top: 1px solid var(--line);
  }}
  .growth-note {{
    border: 1px dashed #a855f7;
    background: #faf5ff;
    border-radius: 8px;
    padding: 7px 10px;
    margin: 6px 0 4px;
    font-size: 8.5pt;
    color: #334155;
  }}
  h3 {{
    font-size: 10pt;
    color: var(--purple-deep);
    margin: 7px 0 4px;
    font-weight: 800;
    break-after: avoid;
  }}
  p {{ margin: 0 0 5px; }}
  ul {{ margin: 0 0 5px; padding-left: 17px; }}
  li {{ margin: 1.5px 0; }}
  .fine {{ font-size: 8pt; color: var(--muted); }}
  .abbr {{
    font-size: 7.5pt;
    color: #475569;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 5px 8px;
    margin: 6px 0 8px;
    line-height: 1.42;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 4px 0 7px;
    font-size: 8.5pt;
  }}
  thead {{ display: table-header-group; }}
  tr {{ break-inside: avoid; page-break-inside: avoid; }}
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
  td.k {{ width: 26%; font-weight: 600; color: #334155; }}

  .cards {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
    margin: 5px 0 7px;
    break-inside: avoid;
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
    font-size: 9.5pt;
    margin-bottom: 2px;
  }}
  .card span {{ font-size: 7.4pt; color: var(--muted); }}

  .closing {{
    border: 1.5px solid var(--purple);
    border-left: 6px solid var(--purple);
    border-radius: 8px;
    padding: 9px 11px;
    font-weight: 700;
    background: #faf5ff;
    margin: 6px 0;
    font-size: 9.3pt;
  }}
  .doc-foot {{
    margin-top: 10px;
    padding-top: 6px;
    border-top: 1px solid var(--line);
    font-size: 7.5pt;
    color: var(--muted);
    text-align: center;
  }}
"""


def shot_data_uri(filename: str) -> str:
    path = ROOT / "docs" / "_portfolio_previews" / "shots" / filename
    if not path.is_file():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_html(prod: dict, logo_uri: str, fonts: str) -> str:
    logo_img = (
        f'<img class="cover-logo" src="{logo_uri}" alt="CoreLabs" />'
        if logo_uri
        else '<div class="cover-logo-fallback">CoreLabs</div>'
    )
    logo_mark = (
        f'<img class="header-mark" src="{logo_uri}" alt="" />' if logo_uri else ""
    )
    banner_logo = (
        f'<img src="{logo_uri}" alt="CoreLabs" />' if logo_uri else ""
    )
    bullets = "".join(f"<li>{b}</li>" for b in prod["bullets"])
    snap_rows = "".join(
        f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in prod["snapshot"]
    )
    problems = "".join(f"<li>{p}</li>" for p in prod["problems"])
    cards = "".join(
        f'<div class="card"><strong>{t}</strong><span>{d}</span></div>'
        for t, d in prod["values"]
    )
    flow_rows = "".join(
        f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in prod["flow"]
    )
    features = "".join(f"<li>{f}</li>" for f in prod["features"])
    tech_rows = "".join(
        f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in prod["tech"]
    )
    business = "".join(f"<li>{b}</li>" for b in prod["business"])
    users = "".join(f"<li>{u}</li>" for u in prod["users"])
    version_label = prod.get("version_label") or "2026년 7월"

    status_html = ""
    status = prod.get("status") or []
    if status:
        status_rows = "".join(
            f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in status
        )
        status_html = f"""
<section class="sec">
  <div class="sec-h">05-B 구현 현황 스냅샷（{version_label}）</div>
  <table>
    <thead><tr><th style="width:24%">영역</th><th>구현 · 상태</th></tr></thead>
    <tbody>{status_rows}</tbody>
  </table>
  <p class="fine">※ 의도적 미완은 사업자·PG·스토어 정책 순서에 따른 보류이며, 골격은 코드에 반영되어 있습니다.</p>
</section>
"""

    shot_html = ""
    shots = prod.get("screenshots") or []
    if shots:
        cells = []
        for item in shots:
            if len(item) == 3:
                cap, fn, kind = item
            else:
                cap, fn = item
                kind = "web"
            uri = shot_data_uri(fn)
            if not uri:
                continue
            cls = "shot phone" if kind == "phone" or "play" in fn.lower() else "shot"
            cells.append(
                f'<div class="{cls}"><img src="{uri}" alt="{cap}" />'
                f'<div class="cap">{cap}</div></div>'
            )
        if cells:
            shot_html = (
                '<h3>실제 화면（UI）</h3>'
                f'<div class="shot-grid">{"".join(cells)}</div>'
                f'<p class="fine">캡처: 라이브 웹（wakeagain.com）· Play 제출용 모바일 화면 · 시각 증명용</p>'
            )

    growth_html = ""
    if prod.get("growth_note"):
        growth_html = f'<div class="growth-note">{prod["growth_note"]}</div>'

    live_line = {
        "wakeagain": "라이브: <strong>https://wakeagain.com</strong><br/>",
        "roadlog": "라이브: <strong>https://roadlog.co.kr</strong><br/>",
        "trace": "배포: <strong>Trace.exe 설치형</strong><br/>",
    }.get(prod["id"], "")
    foot_ver = " v2.0" if prod["id"] == "wakeagain" else ""
    header_ver = " · v2.0" if prod["id"] == "wakeagain" else ""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<title>{prod["name"]} 포트폴리오 · CoreLabs</title>
<style>{css(fonts)}</style>
</head>
<body>

<section class="cover">
  <div class="cover-top">
    <div class="cover-kicker">PRODUCT PORTFOLIO</div>
    {logo_img}
    <div class="cover-product">{prod["name"]}</div>
    <p class="cover-sub">{prod["subtitle"]}</p>
    <span class="cover-role">{prod["role"]}</span>
  </div>
  <div class="cover-body">
    <p class="cover-tagline">{prod["tagline"]}</p>
    <ul class="cover-bullets">{bullets}</ul>
    <div class="company-banner">
      {banner_logo}
      <div class="txt">
        <strong>운영 회사 코어랩스（CoreLabs）</strong><br/>
        IT 스튜디오 · 대표 호현수 · corelabs.studio@gmail.com
      </div>
    </div>
    <div class="meta-box">
      <div class="meta-row"><span class="k">운영</span><span class="v">코어랩스（CoreLabs）</span></div>
      <div class="meta-row"><span class="k">대표</span><span class="v">호현수</span></div>
      <div class="meta-row"><span class="k">문의</span><span class="v">corelabs.studio@gmail.com</span></div>
      <div class="meta-row"><span class="k">작성</span><span class="v">{version_label}</span></div>
      <div class="meta-row"><span class="k">용도</span><span class="v">제품 소개 · 사업 준비 · 스토어·파트너</span></div>
    </div>
  </div>
</section>

<div class="doc-header">
  <div class="left">{logo_mark}<span>{prod["name"]} Portfolio | CoreLabs{header_ver}</span></div>
  <div>대표 호현수</div>
</div>

<section class="sec">
  <div class="sec-h">01 제품 한눈에 보기</div>
  <div class="callout">{prod["overview"]}</div>
  <div class="domain-box">
    <div class="lab">{prod["domain_label"]}</div>
    <div>{prod["domain_value"]}</div>
  </div>
  {shot_html}
  <table>
    <thead><tr><th style="width:26%">항목</th><th>내용</th></tr></thead>
    <tbody>{snap_rows}</tbody>
  </table>
  <div class="abbr">{prod["abbr"]}</div>
</section>

<section class="sec">
  <div class="sec-h">02 해결하는 문제</div>
  <ul>{problems}</ul>
</section>

<section class="sec">
  <div class="sec-h">03 핵심 가치</div>
  <div class="cards">{cards}</div>
</section>

<section class="sec">
  <div class="sec-h">04 사용자 흐름</div>
  <table>
    <thead><tr><th style="width:22%">단계</th><th>설명</th></tr></thead>
    <tbody>{flow_rows}</tbody>
  </table>
</section>

<section class="sec">
  <div class="sec-h">05 주요 기능 · 원칙</div>
  <ul>{features}</ul>
</section>
{status_html}
<section class="sec">
  <div class="sec-h">06 기술 · 배포</div>
  <table>
    <thead><tr><th style="width:22%">항목</th><th>내용</th></tr></thead>
    <tbody>{tech_rows}</tbody>
  </table>
</section>

<section class="sec">
  <div class="sec-h">07 비즈니스 · 요금</div>
  <ul>{business}</ul>
</section>

<section class="sec">
  <div class="sec-h">08 대상 사용자 · 초기 실행</div>
  <ul>{users}</ul>
  {growth_html}
</section>

<section class="sec">
  <div class="sec-h">09 한 줄 클로징</div>
  <div class="closing">{prod["closing"]}</div>
  <p class="fine" style="margin-top:8px">{prod["disclaimer"]}</p>
  <div class="callout" style="margin-top:10px">
    운영: <strong>코어랩스（CoreLabs）</strong> · 대표 호현수<br/>
    문의: <strong>corelabs.studio@gmail.com</strong><br/>
    {live_line}
    © 2026 CoreLabs · {prod["name"]} · Product Portfolio{foot_ver}
  </div>
</section>

<p class="doc-foot">corelabs.studio@gmail.com · {prod["name"]} Product Portfolio{foot_ver} · CoreLabs</p>
</body>
</html>
"""


def render_pdf(html: str, out: Path, preview: Path) -> None:
    from playwright.sync_api import sync_playwright

    out.parent.mkdir(parents=True, exist_ok=True)
    preview.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(preview.resolve().as_uri(), wait_until="networkidle")
        page.evaluate("() => document.fonts.ready")
        page.wait_for_timeout(400)
        page.pdf(
            path=str(out),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()
    print("OK", out.name, out.stat().st_size)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--only",
        default="",
        help="comma-separated product ids (e.g. wakeagain)",
    )
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()}

    logo = logo_data_uri()
    fonts = font_faces()
    preview_dir = ROOT / "docs" / "_portfolio_previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    targets = [p for p in PRODUCTS if not only or p["id"] in only]
    for prod in targets:
        html = build_html(prod, logo, fonts)
        out = DESK / prod["file"]
        preview = preview_dir / f"{prod['id']}.html"
        try:
            render_pdf(html, out, preview)
            alias = prod.get("file_alias")
            if alias:
                alias_path = DESK / alias
                alias_path.write_bytes(out.read_bytes())
                print("alias:", alias_path.name)
        except Exception as e:
            print("FAIL", prod["id"], e)
            preview.write_text(html, encoding="utf-8")
            return 1

    # blank page audit
    try:
        from pypdf import PdfReader

        for prod in targets:
            path = DESK / prod["file"]
            r = PdfReader(str(path))
            blank = 0
            for i, page in enumerate(r.pages):
                t = (page.extract_text() or "").strip()
                n = len(t.replace(" ", "").replace("\n", ""))
                if n < 40:
                    blank += 1
                    print(f"  WARN blankish {prod['file']} p{i+1}")
            # domain wording check
            full = "\n".join((p.extract_text() or "") for p in r.pages)
            bad_goal = ("목표 도메인" in full) or ("wakeagain.com（목표）" in full) or (
                "wakeagain.com (목표)" in full
            )
            print(
                f"audit {prod['file']}: pages={len(r.pages)} blankish={blank} "
                f"has_live_domain={'wakeagain.com' in full} bad_goal_wording={bad_goal}"
            )
    except Exception as e:
        print("audit skip", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
