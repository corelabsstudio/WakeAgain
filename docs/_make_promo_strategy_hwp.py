# -*- coding: utf-8 -*-
"""WakeAgain 홍보 전략 → 바탕화면 HWP (한컴 COM)."""
from __future__ import annotations

import os
import sys
import time

try:
    import win32com.client  # type: ignore
except ImportError:
    print("pip install pywin32 필요")
    sys.exit(1)

OUT = os.path.join(os.path.expanduser("~"), "Desktop", "WakeAgain_홍보전략_런칭.md")
# 실제 저장은 HWP — 임시 경로
OUT_HWP = os.path.join(
    os.path.expanduser("~"),
    "Desktop",
    "WakeAgain_홍보전략_런칭.hwp",
)

SECTIONS: list[tuple[str, str]] = [
    (
        "문서 안내",
        """작성일: 2026-07-21
제품: WakeAgain (코어랩스)
목적: 장터 홍보·런칭 전략 메모 (실행 전 정리)

※ 현재 전제 (아직 안 된 것)
- 사업자 등록증 반영·통신판매중개 신고 게시: 미완
- PG/결제 연동·1시간 자동 입금 타이머: 미완 (pre-PG, 운영 안내·수동)
- 커스텀 도메인(wakeagain.com): 보류 가능
- 라이브 URL: Railway 서브도메인으로 공개 가능

→ 그래서 지금은 「대규모 결제 약속」보다
  ① 매물 진열  ② 관심(구매 의사) 수집  ③ 오픈일 이벤트
  중심으로 홍보한다.
""",
    ),
    (
        "1. 전략 한 줄",
        """양면 장터 닭-달걀 문제를 시간으로 나눈다.

1단계  매물 진열 (구경할 카드 만들기) — 판매자 모집
2단계  구매자 예열 (관심 등록·대기) — 손님 모객
3단계  D-day 경매 동시 오픈 — 「사이트 가동 시작」이벤트

판매자 메시지
  「일단 사이트에 매물 등록만 해 주세요. 구매자는 운영이 열심히 찾아볼게요.」

구매자 메시지
  「○월 ○일 경매 오픈. 미리 관심 걸어 두세요. 시작과 동시에 입찰.」

첫 매물
  오픈 전 = 무기한(또는 마감 없음) 진열 · 구경·관심 위주
  오픈일 = 날짜를 정해 경매 시작 · 미리 모은 구매자가 한꺼번에 입찰

이상적인 그림: 오픈 시각에 입찰이 붙으며 현재가·입찰자 수가 살아 움직이는 것.
""",
    ),
    (
        "2. 왜 이 순서가 맞는가",
        """- 손님만 있고 매물 없음 → 이탈
- 매물만 있고 손님 약속 없음 → 판매자 실망
- 진열 먼저 + 오픈일 이벤트 = 양쪽 기대 관리 + 소셜 프루프(실시간 입찰)

등록 무료 · 성사 시에만 판매자 수수료 10% 구조와도 맞음.
사업자·PG 전이라도 「진열 + 관심 + 오픈일」은 진행 가능.
(실제 대금·자동 정산은 PG·사업자 이후 고도화)
""",
    ),
    (
        "3. 홍보 대상 우선순위 (구매자 중심)",
        """※ 판매자를 모으는 채널과 구매자를 모으는 채널을 글·톤을 분리할 것.

1순위  바이브 코딩(Vibe Coding) 커뮤니티  ★★★★★
  - 만든 사람 / 만들고 싶은 사람 / 창업 준비 모두 있음
  - 중요: 여기서 목표의 축은 「판매 모집」이 아니라 「구매자 후보」
  - 시그널 예: 「아이디어는 있는데 개발 시간 없다」「MVP 사는 게 빠르다」

2순위  인디해커(Indie Hacker)  ★★★★★
  - 작은 SaaS를 사고·키우고·다시 파는 문화
  - 플랫폼 사고방식과 가장 유사

3순위  마케팅 전문가  ★★★★☆
  - 「개발은 못 해도 마케팅은 자신」→ 만들어진 앱을 키우는 구매자

4순위  스타트업 대표  ★★★★☆
  - 기능 하나 직접 개발 대신 기존 프로젝트 인수 니즈
  - 딜은 크지만 검증·신뢰 요구가 셈 → 초기엔 소수 DM

5순위  유튜버·콘텐츠 크리에이터  ★★★★☆
  - 「50만 원 AI 앱 한 달 키우기」자체가 콘텐츠
  - 구매 + 홍보 레버리지 / 성사 사례 나온 뒤 파일럿 추천
""",
    ),
    (
        "4. 단계별 실행 (타임라인)",
        """[Phase 0] 메시지 고정 (지금)
- 판매: 매물만 올려 주세요. 손님 모객·오픈일 홍보는 운영이.
- 구매: ○월 ○일 오픈. 지금 관심 등록.
- 과장 금지: 「이미 구매자 줄 섰다」「무조건 팔린다」 사용 안 함.
- 사업자·PG 전임을 내부적으로 인지. 대외 카피에 미구현 자동화(1시간 타이머 등)를 확정처럼 쓰지 않음.

[Phase 1] 매물 확보 (예: 2~3주)
- 목표 공개 카드: 8~15개 (카테고리 2~3종)
- 데모(URL/영상) 있는 매물 우선 · 가능하면 70%+
- 상태: 사이트에 카드로 보이게 (스토리·데모·시작가)
- 경매: 오픈 전 무기한 진열(마감 없음 또는 「오픈일 시작」 안내)
- 입찰: 운영 정책으로 오픈 전 입찰 자제/잠금 안내 가능
- 채널: 바이브·인디 쪽에 「판매자 모집」글 (구매 모객과 분리)

[Phase 2] 구매자 예열 (매물 5개+부터 병행 가능)
- 관심 등록·대기 명단 수집 (목표 예: 관심 의사 30~50)
- 오픈일 + 매물 티저 홍보 (전체 스포일러는 일부만)
- 인디·바이브·마케터 채널 / 가능하면 크리에이터 1명 파일럿 약속

[Phase 3] Launch Day = 경매 시작 = 「가동 시작」
- 전 매물 같은 시각 입찰 오픈 + 경매 기간 통일 (예: 3~7일)
- 미리 모아 둔 구매자에게 동시 링크·알림
- 당일 운영 대기 (문의·신고·입금 안내 — pre-PG는 수동)

[Phase 4] 첫 주 이후
- 성사 1건이라도 사례 홍보
- 미성사: 기간 연장·시작가 조정 가이드
- 사업자·PG 준비되는 대로 결제·정산 자동화 로드맵 연결
""",
    ),
    (
        "5. 판매자 / 구매자 메시지 (복붙 초안)",
        """■ 판매자용 (커뮤니티·지인)

제목 예: 잠든 사이드 프로젝트, 일단 올려만 두세요 (등록 무료)

본문 요지:
- WakeAgain: 잠든 앱·프로토·SaaS를 다시 연결하는 장터
- 지금 단계: 오픈일 전 「진열」모집. 등록 무료, 형식 검수 후 공개
- 구매자 모객·오픈일 홍보는 운영이 진행
- 오픈일(○월 ○일)에 맞춰 경매(가격 쓰기) 시작 예정
- 안 팔려도 플랫폼 수수료 없음. 성사 시에만 판매자 10%
- 데모(화면 녹화 OK) 있으면 우선
- 링크: (Railway 라이브 URL)
- 통신판매중개 · 품질·거래 보증 아님 (판매자·구매자 책임)

■ 구매자용

제목 예: ○월 ○일 오픈 — 돌아가는 MVP·사이드 프로젝트 경매

본문 요지:
- 개발 시간이 없거나, 이미 만든 초안을 이어받고 싶을 때
- 오픈 전 진열 중 · 관심 등록 가능
- 오픈 시각부터 지금 가격 공개 입찰
- 사는 사람 추가 수수료 없음 (합의 가격)
- 데모 있는 매물 우선
- 관심 등록 / 마켓 링크
""",
    ),
    (
        "6. 오픈 전날 체크리스트",
        """[ ] 공개 매물 8개 이상 · 데모 있는 비율 높게
[ ] 관심/대기 구매 의사 표시 확보 (목표 숫자 스스로 기입: ____ 명)
[ ] 오픈 시각·경매 기간 한 줄로 고정
[ ] 판매자 전원에 오픈일·입금 규칙·입금 전 이전 금지 공지
[ ] 당일 공지 채널 (메일/오픈채팅/커뮤니티) 준비
[ ] 과장·미구현 기능(자동 PG 타이머 등) 확정 표현 없는지 확인
[ ] 사업자·약관 고지 상태는 「진행 중/추후」로 내부 인지 (대외 과대 표시 금지)
""",
    ),
    (
        "7. 지금 하면 안 되는 것 / 나중에 할 것",
        """지금(사업자·PG 전) 하면 좋은 것
- 매물 등록 유도 · 진열
- 관심 구매자 리스트
- 오픈일 날짜 잡고 사전 홍보
- 데모·스토리 품질 관리
- 커뮤니티 신뢰 톤 유지

지금 강조·약속하지 말 것
- 「결제 자동화·1시간 타이머 완비」(PG 후)
- 「플랫폼이 거래·이전·사기 배상 보증」
- 사업자번호·통신판매 신고번호가 있는 것처럼 표기 (없으면 비워 두거나 준비 중)

사업자 등록 이후
- 약관·푸터·상호 고지 보완
- 통신판매중개 신고 절차

PG 연동 이후
- 결제 링크 · 입금 기한 자동화 · 2순위 전환 목표
""",
    ),
    (
        "8. 이상적인 오픈 시나리오 (요약)",
        """1) 판매자들에게 매물만 올려 달라고  sufficently 모집
2) 사이트에 카드가 쌓여 「살까 말까」고를 수 있는 장터 형태
3) 구매자 후보(바이브·인디·마케터 등)에게 오픈일 사전 홍보·관심 등록
4) 오픈일 = 가동 시작 = 경매 시작 — 미리 모인 사람들이 동시에 입찰
5) 실시간 현재가·입찰자 수가 살아 보이며 초기 신뢰·사례 확보
6) 이후 사업자·PG로 거래 완결성을 올림

이 문서 목적: 위 전략을 잊지 않도록 바탕화면에 고정.
세부 실행 일정·채널별 최종 문구는 오픈일 확정 후 업데이트.
""",
    ),
]


def insert_text(hwp, text: str) -> None:
    """Insert plain text with newlines as paragraph breaks."""
    # Escape for HWP action; use InsertText in chunks
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
    # 보안 모듈 — 자동 저장 허용 (환경에 따라 무시될 수 있음)
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    except Exception:
        pass

    hwp.XHwpWindows.Item(0).Visible = False
    hwp.HAction.Run("FileNew")

    # Title
    hwp.HAction.GetDefault("InsertText", hwp.HParameterSet.HInsertText.HSet)
    hwp.HParameterSet.HInsertText.Text = "WakeAgain 홍보·런칭 전략"
    hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
    hwp.HAction.Run("BreakPara")
    insert_text(
        hwp,
        "판매자 진열 먼저 → 구매자 예열 → 오픈일 경매 동시 시작\n"
        "(사업자 등록·결제 연동 이전 단계 기준 메모)\n",
    )
    hwp.HAction.Run("BreakPara")

    for title, body in SECTIONS:
        hwp.HAction.GetDefault("InsertText", hwp.HParameterSet.HInsertText.HSet)
        hwp.HParameterSet.HInsertText.Text = f"■ {title}"
        hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
        hwp.HAction.Run("BreakPara")
        insert_text(hwp, body.strip() + "\n")
        hwp.HAction.Run("BreakPara")

    # Save
    out = OUT_HWP
    if os.path.exists(out):
        try:
            os.remove(out)
        except OSError:
            out = os.path.join(
                os.path.expanduser("~"),
                "Desktop",
                f"WakeAgain_홍보전략_런칭_{int(time.time())}.hwp",
            )

    # Hwp save API
    # arg: format "HWP", path
    ok = hwp.SaveAs(out, "HWP")
    if not ok:
        # fallback Format
        hwp.HAction.GetDefault("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
        hwp.HParameterSet.HFileOpenSave.filename = out
        hwp.HParameterSet.HFileOpenSave.Format = "HWP"
        hwp.HAction.Execute("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)

    time.sleep(0.5)
    try:
        hwp.Clear(1)  # hwpClear: 문서 닫기 계열
    except Exception:
        pass
    try:
        hwp.Quit()
    except Exception:
        pass

    if os.path.isfile(out):
        print("OK", out, os.path.getsize(out))
    else:
        print("FAIL missing", out)
        sys.exit(1)


if __name__ == "__main__":
    main()
