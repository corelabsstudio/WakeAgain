# WakeAgain — Claude Code 안내

이 파일을 읽은 뒤 **현재 디스크·git·라이브**를 재검증하고 작업한다.  
옛 트랜스크립트·Grok 메모리는 자동 동기화되지 않는다. 아래 문서가 정본이다.

## 필수 문서 (순서)

1. `PLATFORM.md` — 플랫폼 필수·PG 전 금지 규칙
2. `TRUST.md` — 신뢰 게이트·사기 포지션·경매 라운드
3. `PROGRESS.md` — 체크포인트·백로그 요약
4. `docs/나중_할일_BACKLOG.md` — 보류 목록
5. 공통 이관: `../docs/CLAUDE_TO_GROK_HANDOFF.md`  
   (바탕화면 복사본: `Desktop/CLAUDE_TO_GROK_HANDOFF.md`)

## 제품

| 항목 | 값 |
|------|-----|
| 한 줄 | 잠든 디지털 프로젝트 거래 중개 (경매·중개자) |
| 경로 | `C:\Users\hysoo\Projects\WakeAgain` |
| 라이브 | https://wakeagain.com |
| 원격 | `github.com/corelabsstudio/WakeAgain` · 브랜치 `master` |
| 배포 | push → Railway 서비스 **wakeagain** 자동 |
| 로컬 | `uvicorn server:app --host 0.0.0.0 --port 8080` → http://127.0.0.1:8080/ |
| 운영 | 코어랩스 (CoreLabs) · corelabs.studio@gmail.com |
| 사업자 | 705-04-02867 · `/legal/business.html` 게시 완료 |

## 최근 배포 (2026-07-31 · `3da9b26`)

- 경매 **라운드**: 공개 보드 = `live`만 · 유찰 시 archive · `POST .../relist` 재검수·후순위
- **노출 점수**: 매물 품질 + 헬프티켓 가산 → `round_started_at`
- **헬프티켓 (q-credits)**: 포함 1~3 · 스레드 · 추가 구매(PG 전 mock) · 중재 없음 고지
- **인증**: `passlib` 제거 · `bcrypt` 직접 해시 (`wakeagain/auth.py`)
- 검증 당시: smoke·auction·deal·block·q-credit e2e·predeploy 10/10

## 작업 방식 (사용자 강제)

1. **말한 것만** — 멋대로 범위 확장·하이브리드 기본값 금지  
2. **애매하면 되묻기** — 추측 구현 금지  
3. 「완료」 전 핵심 한두 줄 되짚기  
4. 사이트 기준 위반 아이디어는 코드 반영 금지 (이유만)  
5. 수익성 → 사업성 → 안정성 순 평가  
6. 「전부」면 부분 실행으로 끝내지 말 것  

## 금지

- **PG 전** 수동 입금 확인 UX·임시 계좌 플로우 등 우회 기능 **신규 추가 금지** (`PLATFORM.md` §B)
- 가짜 GMV·성사 보장·AI 검수 배지 마케팅
- 삭제된 **CoreLabs / CoreLabsPromo** 로컬 툴 복원
- `system32` 등 비프로젝트 cwd에서 제품 작업
- 시크릿·`.env`·토큰 커밋

## 의도적 미완 (사람 행정)

- PG 실결제·웹훅  
- 통신판매중개 **행정 신고 번호** 게시  
- Play 내부테스트  

## 트리거 말

- 「WakeAgain 이어서」 / 「웨이크어게인 불러와」 → 위 문서 읽고 열린 일만 요약 후 진행  
- 「SNS 로그인 연결」 → OAuth 문서 (`docs/OAUTH_*`) · 도메인 이미 있음  
- 「PG」 → 결제 링크·웹훅→`paid` 만 · pre-PG 우회 금지  

## 배포 전 최소 확인

```text
python _smoke_check.py
# 또는 python _predeploy_gate.py
git status   # 불필요 untracked 제외 후 push
```

`master` push 후 Railway 상태·`https://wakeagain.com/health` 확인.
