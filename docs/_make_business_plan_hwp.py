# -*- coding: utf-8 -*-
"""CoreLabs 사업계획서 → 바탕화면 HWP."""
from __future__ import annotations

import os
import sys
import time

try:
    import win32com.client  # type: ignore
except ImportError:
    print("pip install pywin32 필요")
    sys.exit(1)

OUT = os.path.join(
    os.path.expanduser("~"),
    "Desktop",
    "CoreLabs_사업계획서_WakeAgain_RoadLog.hwp",
)

# 회사 로고 (확정 2026-07-21: 육각 C + 네트워크 락업)
LOGO_PATHS = [
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "public",
        "assets",
        "corelabs-logo-lockup.png",
    ),
    os.path.join(os.path.expanduser("~"), "Desktop", "CoreLabs_logo_final.png"),
    os.path.join(os.path.expanduser("~"), "Desktop", "CoreLabs_logo_final.jpg"),
]


def resolve_logo() -> str | None:
    for p in LOGO_PATHS:
        if os.path.isfile(p):
            return p
    return None


def insert_logo(hwp, path: str) -> bool:
    """표지용 CoreLabs 락업 삽입. 실패해도 본문은 계속."""
    try:
        # InsertPicture(path, embedded, sizeoption, reverse, watermark, effect, width, height)
        # sizeoption 1 = 문단 너비에 맞춤 / 0 = 원본
        hwp.InsertPicture(path, True, 1, False, False, 0, 0, 0)
        hwp.HAction.Run("BreakPara")
        return True
    except Exception as e1:
        try:
            act = hwp.CreateAction("InsertPicture")
            pset = act.CreateSet()
            act.GetDefault(pset)
            pset.SetItem("FileName", path)
            pset.SetItem("Embedded", 1)
            pset.SetItem("sizeoption", 1)
            act.Execute(pset)
            hwp.HAction.Run("BreakPara")
            return True
        except Exception as e2:
            print("logo insert failed:", e1, e2)
            return False

SECTIONS: list[tuple[str, str]] = [
    (
        "1. 사업 개요",
        """상호(예정): 코어랩스(CoreLabs)
대표 문의: corelabs.studio@gmail.com
작성일: 2026년 7월
문서 목적: 사업자등록·통신판매(중개) 관련 준비 및 내부 사업·대외 제출용 사업계획 요약

■ 한 줄 정의
코어랩스는 소프트웨어·웹 기반 디지털 제품을 기획·개발·운영하는 IT 스튜디오이다.
대표 서비스는 (1) 잠든 사이드 프로젝트 거래 장터 WakeAgain, (2) 운행·업무 기록 서비스 RoadLog 이다.

■ 사업 형태
- 개인사업자 또는 법인 전환 전 단계의 온라인 IT 서비스 사업
- 사업장 주소: 신청 서류상 주소(기존 사업장과 동일 주소 가능 여부는 관할 세무서 기준)
- 브랜드: 상호 CoreLabs / 서비스명 WakeAgain, RoadLog (서비스명은 브랜드)

■ 법적 지위 요약
- WakeAgain: 전자상거래법상 통신판매중개자(장터). 거래 당사자 아님. 매물 품질·사기 1차 책임은 이용자.
- RoadLog: 코어랩스가 직접 제공하는 소프트웨어·SaaS성 서비스(직접 공급 시 통신판매업 신고 검토).
- 서비스마다 사업자를 나누지 않고, CoreLabs 1개 상호로 운영하는 것을 원칙으로 한다.
""",
    ),
    (
        "2. 사업 배경 및 필요성",
        """■ 시장 문제
1) 사이드 프로젝트·MVP가 대량 생산되나, 출시 후 유저·수익 없이 방치되는 자산이 많다.
2) 중고·커뮤니티 거래는 가격 기준·데모 검증·이전 절차·직거래 사기 위험이 크다.
3) 운행·현장 업무 기록은 엑셀·종이·분산 도구에 의존해 정리·증빙·협업 비용이 크다.

■ 기회
- “만드는 사람”과 “시간·마케팅은 있으나 0부터 만들기 싫은 사람”을 연결하는 전문 장터 수요
- 한국 우선 검증 후 웹·앱 동일 계정으로 확장 가능한 구조
- 기존 개발 역량으로 자체 제품(RoadLog)과 플랫폼(WakeAgain)을 병행 운영 가능
""",
    ),
    (
        "3. 사업 아이템",
        """【제품 A】 WakeAgain
- 개념: 잠든 앱·프로토타입·SaaS·도구 등 디지털 프로젝트를 공개 호가(경매·가격 쓰기)로 연결하는 마켓플레이스
- 슬로건: 프로젝트에 두 번째 기회를 주세요.
- 제품 핵심: 쉽게 올리고 쉽게 가격을 쓰되, 거래는 단계형 안전 절차로 관리
- 주요 기능:
  · 매물 등록(무료) · 형식 검수 후 공개(보통 1~2일, 품질 보증 아님)
  · 공개 현재가·입찰자 수·실시간 폴링
  · 관심 등록 · 30초 무료 진단(통계 힌트, 감정가 아님)
  · 신원 단계(Lv1 입찰 / Lv2 낙찰 후 결제·인수 / Lv3 판매자 정산)
  · 안전거래 루프: 낙찰 → PG 결제(1시간) → 이전 → 검수·인수(또는 48시간 무이의 자동 확정) → 정산
  · 쪽지 시 “플랫폼 외부 거래 시 보호 불가” 고정 고지
  · 웹 + PWA · 향후 Google Play / App Store 동일 API
- 수익: 등록 무료. 성사 시 판매자 수수료 10%. 구매자 추가 수수료 없음.
- 배포: Railway 등 클라우드 (라이브 URL 운영 중). 목표 도메인 wakeagain.com

【제품 B】 RoadLog
- 개념: 운행·업무 일지 및 관련 기록을 디지털화하는 웹/업무 지원 서비스
- 역할: 코어랩스 직접 제공 서비스(구독·이용료 등 직접 과금 시 통신판매 성격)
- 목표: 현장 기록 부담 감소, 정리·출력·보관의 표준화
- 운영: 웹 기반, 클라우드 배포. WakeAgain과 별 브랜드·동일 스튜디오 운영

【공통】
- 기술 스택: 웹 앱(프론트+API), SQLite/파일 기반 데이터, 클라우드 배포
- 다국어·다통화 표시 기반(정산 기준은 원화 우선)
""",
    ),
    (
        "4. 목표 고객",
        """■ WakeAgain
[판매자]
- 사이드 프로젝트·MVP를 만들었으나 운영·마케팅 여력이 없는 개발자·바이브 코더
- 폴더에만 남은 프로토타입을 정리·현금화하고 싶은 인디 메이커

[구매자]
- 시간 없는 직장인·창업 준비자 (0부터 만들기보다 인수 선호)
- 마케팅·영업은 가능하나 개발이 부담인 사람
- 인디해커·스타트업 대표(기능·MVP 빠른 확보)
- (중장기) 콘텐츠 크리에이터

■ RoadLog
- 운행 일지·현장 기록이 필요한 개인·소상공·소규모 조직
- 종이·엑셀 기록을 디지털로 전환하려는 이용자
""",
    ),
    (
        "5. 비즈니스 모델",
        """■ WakeAgain
| 항목 | 내용 |
| 등록 | 무료 |
| 관심·입찰 | 무료 |
| 성사 수수료 | 판매자 거래대금의 10% |
| 구매자 | 합의(낙찰)가만 |
| 부가 수익(향후) | 노출 상품, 프리미엄 검수 등(도입 시 고지) |

■ RoadLog
- 서비스 이용료·구독 등 직접 과금(요금제 확정 시 약관·고지 반영)
- B2C 중심, 필요 시 B2B 확장

■ 결제
- 실거래·정산은 PG(결제대행) 연동 후 운영
- PG 전 수동·오프플랫폼 입금 차선책은 운영 경로로 두지 않음
- WakeAgain: PG 결제 확인 후 이전·인수·정산 자동화 목표
""",
    ),
    (
        "6. 경쟁 우위 및 차별점",
        """1) 사이드 프로젝트·MVP에 특화된 공개 호가 장터(대형 M&A 플랫폼과 다른 문턱)
2) 데모·공개 가격·입찰자 수 등 투명성
3) 게임 안전거래형 단계 절차 + 외부 직거래 보호 불가 고지
4) 입찰 허들 최소화(이메일 인증) / 낙찰 후 신원·정산 강화
5) 웹·앱 동일 계정 구조로 모바일 확장 용이
6) 자체 제품(RoadLog)과 플랫폼(WakeAgain) 병행으로 스튜디오 수익 다각화
""",
    ),
    (
        "7. 마케팅·성장 전략",
        """■ 양면 시장
- 판매자: “매물만 올려 주세요. 등록 무료. 손님 모객·오픈은 운영이.”
- 구매자: “다시 만들기 전에, 돌아가는 초안을.” + 안전결제 안내

■ 채널 우선순위
1) 바이브 코딩 커뮤니티 (구매 의사 시그널 중심)
2) 인디해커·사이드프로젝트 커뮤니티
3) 마케터·비개발 창업자
4) 스타트업·크리에이터(후순위 파일럿)

■ 런칭
- 매물 진열 → 관심 등록 수집 → 오픈일 경매 동시 시작 이벤트
- 콜드스타트: 데모 있는 매물 품질 게이트, 관심 KPI 우선

■ 브랜딩
- 사이트 표기: WakeAgain / RoadLog 영문
- 상호·세금·약관: CoreLabs
""",
    ),
    (
        "8. 운영 및 조직",
        """■ 초기
- 1인(또는 소수) 스튜디오: 개발·운영·검수·고객응대
- 매물 형식 검수: 보통 1~2영업일 (품질·가치 감정 아님, 사람 확인)

■ 시스템 운영
- 클라우드 호스팅(Railway 등)
- 관리자 검수(/admin), 신고·경매 중단 기준
- 스케줄러: 경매 마감 자동 낙찰, 입금·검수 기한 처리

■ 개인정보·신뢰
- 만 14세 미만 가입 불가
- 단계별 신원(이메일 → 실명·휴대폰 → 정산 계좌)
- 개인정보처리방침·이용약관 게시
""",
    ),
    (
        "9. 추진 일정 (요약)",
        """1단계 — 사업 기반
- CoreLabs 사업자등록
- (해당 시) 통신판매업 신고 / 중개 고지 정비
- 약관·푸터 상호·사업자번호 반영

2단계 — 결제·실거래
- PG 신청·연동
- WakeAgain 결제 링크·웹훅·정산 자동화
- RoadLog 유료 결제(해당 시)

3단계 — 성장
- 매물·관심 확보, 커뮤니티 홍보
- 앱스토어 정식 등록(목표)
- 도메인(wakeagain.com 등) 연결

4단계 — 고도화
- 2순위 자동, 분쟁 프로세스 강화
- 해외 표시·확장 검토(정산·약관은 한국 우선)
""",
    ),
    (
        "10. 손익·재무 가정 (초기 스케치)",
        """※ 실제 수치는 런칭 후 데이터로 갱신. 아래는 계획용 가정.

■ WakeAgain
- 성사 1건 거래대금 가정 예: 50만~150만 원대 사이드 프로젝트
- 수수료 10% → 건당 5만~15만 원 매출(부가세 별도 논의)
- 고정비: 호스팅, 도메인, PG 수수료, 마케팅, 검수 시간

■ RoadLog
- 월 구독 또는 건당 요금(요금표 확정 후 반영)
- 서버 비용은 이용자 규모에 연동

■ 손익 분기
- 초기: 제품 완성·신뢰 구축 우선
- 중기: 월 성사 건수 × 평균 수수료 + RoadLog 구독으로 호스팅·운영비 상회 목표
""",
    ),
    (
        "11. 리스크 및 대응",
        """| 리스크 | 대응 |
| 직거래·사기 유도 | 채팅 상단 “외부 거래 시 보호 불가” 고정, 신고·계정 제재 |
| 허위 매물 | 형식 검수, 데모 우선, 신고 누적 시 경매 중단 |
| 미입금·장난 입찰 | 1시간 결제 기한, 신용 점수, 낙찰 무효 |
| 중개자 책임 오해 | 약관·랜딩 면책 + 4단계 관리 시각화 |
| 양면 시장 콜드스타트 | 매물 진열 우선, 구매자 관심 KPI, 커뮤니티 타깃 분리 |
| 규제·신고 | 사업자·통신판매(중개) 고지 정비, 필요 시 전문가 자문 |
""",
    ),
    (
        "12. 결론 및 요청 사항",
        """코어랩스는 WakeAgain(디지털 프로젝트 장터)과 RoadLog(운행·기록 서비스)를 축으로
온라인 IT 서비스 사업을 전개한다.

사업자등록 완료 후:
1) 사이트·약관에 상호·사업자정보 반영
2) PG 연동으로 실거래 안전결제 가동
3) 매물·이용자 확보 및 지속 개선

본 문서는 사업 방향과 운영 원칙을 정리한 계획서이며,
세부 수치·요금·일정은 시장 반응과 행정 절차에 따라 조정한다.

문의: corelabs.studio@gmail.com
© 2026 CoreLabs
""",
    ),
]


def insert_text(hwp, text: str) -> None:
    for i, line in enumerate(text.split("\n")):
        if i > 0:
            hwp.HAction.Run("BreakPara")
        if line == "":
            continue
        hwp.HAction.GetDefault("InsertText", hwp.HParameterSet.HInsertText.HSet)
        hwp.HParameterSet.HInsertText.Text = line
        hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)


def main() -> None:
    hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    except Exception:
        pass

    try:
        hwp.XHwpWindows.Item(0).Visible = False
    except Exception:
        pass

    hwp.HAction.Run("FileNew")

    # Cover — company logo then title
    logo = resolve_logo()
    if logo:
        print("logo:", logo)
        insert_logo(hwp, logo)
    else:
        print("logo: not found (text-only cover)")

    hwp.HAction.GetDefault("InsertText", hwp.HParameterSet.HInsertText.HSet)
    hwp.HParameterSet.HInsertText.Text = "사업계획서"
    hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
    hwp.HAction.Run("BreakPara")
    insert_text(
        hwp,
        "코어랩스(CoreLabs)\n"
        "서비스: WakeAgain · RoadLog\n"
        "작성: 2026년 7월\n"
        "용도: 사업자등록·사업 준비 자료\n",
    )
    hwp.HAction.Run("BreakPara")

    for title, body in SECTIONS:
        hwp.HAction.GetDefault("InsertText", hwp.HParameterSet.HInsertText.HSet)
        hwp.HParameterSet.HInsertText.Text = f"■ {title}"
        hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
        hwp.HAction.Run("BreakPara")
        insert_text(hwp, body.strip() + "\n")
        hwp.HAction.Run("BreakPara")

    out = OUT
    if os.path.exists(out):
        try:
            os.remove(out)
        except OSError:
            out = os.path.join(
                os.path.expanduser("~"),
                "Desktop",
                f"CoreLabs_사업계획서_{int(time.time())}.hwp",
            )

    ok = False
    try:
        ok = bool(hwp.SaveAs(out, "HWP"))
    except Exception:
        ok = False
    if not ok:
        try:
            hwp.HAction.GetDefault("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
            hwp.HParameterSet.HFileOpenSave.filename = out
            hwp.HParameterSet.HFileOpenSave.Format = "HWP"
            hwp.HAction.Execute("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
        except Exception as e:
            print("SaveAs failed:", e)

    time.sleep(0.8)
    try:
        hwp.Clear(1)
    except Exception:
        pass
    try:
        hwp.Quit()
    except Exception:
        pass

    if os.path.isfile(out) and os.path.getsize(out) > 1000:
        print("OK", out, os.path.getsize(out))
    else:
        # fallback: also write markdown next to it
        md = out.replace(".hwp", ".md")
        with open(md, "w", encoding="utf-8") as f:
            f.write("# 사업계획서 — CoreLabs (WakeAgain · RoadLog)\n\n")
            for title, body in SECTIONS:
                f.write(f"## {title}\n\n{body.strip()}\n\n")
        print("HWP missing or small; wrote MD", md)
        if not os.path.isfile(out):
            sys.exit(1)


if __name__ == "__main__":
    main()
