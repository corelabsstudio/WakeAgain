# WakeAgain — Claude Code 안내

이 파일을 읽은 뒤 **현재 디스크·git·라이브**를 재검증하고 작업한다.  
옛 트랜스크립트·Grok 메모리는 자동 동기화되지 않는다. 아래 문서가 정본이다.

**마지막 문서 갱신:** 2026-08-10 (글로벌 EN 론칭 표면 + Railway Trial 만료 반영)

## 필수 문서 (순서)

1. `PLATFORM.md` — 플랫폼 필수·PG 전 금지 규칙
2. `TRUST.md` — 신뢰 게이트·사기 포지션·경매 라운드
3. `docs/GLOBAL.md` — 글로벌 퍼스트(EN+USD) 표면 규칙
4. `PROGRESS.md` — 체크포인트·백로그 요약 (구식일 수 있음 → git log 우선)
5. `docs/나중_할일_BACKLOG.md` — 보류 목록
6. 공통 이관: `../docs/CLAUDE_TO_GROK_HANDOFF.md`
7. **2026-08-10 EN 작업 이관:** `docs/GROK_TO_CLAUDE_HANDOFF_2026-08-10.md`  
   (미러: `../docs/GROK_TO_CLAUDE_HANDOFF_2026-08-10.md`)

## 제품

| 항목 | 값 |
|------|-----|
| 한 줄 | 잠든 디지털 프로젝트 거래 중개 (경매·중개자) |
| 경로 | `C:\Users\hysoo\projects\WakeAgain` |
| 라이브 | https://wakeagain.com (**아래 인프라 주의 읽기**) |
| 원격 | `github.com/corelabsstudio/WakeAgain` · 브랜치 `master` |
| 배포 | push → Railway 서비스 **wakeagain** (`steadfast-dream` / production) |
| 로컬 | `pip install -r requirements.txt` → `uvicorn server:app --host 0.0.0.0 --port 8080` → http://127.0.0.1:8080/ |
| 운영 | 코어랩스 (CoreLabs) · corelabs.studio@gmail.com |
| 사업자 | 705-04-02867 · `/legal/business.html` 게시 완료 |
| 브랜드 | **WakeAgain 영문만** (사이트 한글 음차 금지) |

## ⚠️ 인프라 상태 (2026-08-10 확정)

- **Railway Trial 만료** → 라이브 `wakeagain.com`이 `Application not found` / offline 일 수 있음.
- 원인: 코드 버그가 아니라 **Trial 만료 후 서비스 REMOVED**. Hobby(또는 유료) 결제 후 Redeploy 필요.
- **코드는 `origin/master`에 유지.** 결제 복구 후 `/health`·`?lang=en` 검수.
- Free 플랜(~월 $1 크레딧)으로는 24/7 + `/data` 상시 운영 비현실적. Hobby가 최소 현실 옵션.
- 장기 offline 시 볼륨(`/data` DB·업로드) 삭제 가능 → 결제 전 백업 여부 확인.
- **당분간:** 로컬 개발·커밋·푸시 계속 가능. 라이브 반영은 결제 후.
- 로컬 Railway CLI 토큰 403 가능 → **GitHub push 자동배포**가 정본. 수동 시 GraphQL `serviceInstanceDeployV2` (토큰·플랜 유효할 때).

## 최근 배포 이력 (요약 · 최신 우선)

### 2026-08-10 · 글로벌 EN 론칭 표면 (`63b6bd3` … `9ce7fef`)

| 커밋 계열 | 내용 |
|-----------|------|
| `63b6bd3` | English-first launch surface + create-form i18n |
| `b1c991b`~`b44a245` | 매물 `title_en` / `one_liner_en` · EN 카드 표시 · 약한 휴리스틱 재번역 |
| `508a778` | PH/Indie Hackers 톤 EN UX 카피 전면 |
| `fffac40`~`58d46de` | 콜드스타트 수집 모달 EN/KO i18n (`collect.*`) |
| `27018d1` | `/app/#list` 리스트 크롬 EN |
| `047db35` | auth/profile/settle/fees/coupons 앱 셸 EN |
| `dc9d05b` | `i18n-messages.js` `create_ok` 개행 버그 → EN 팩 전체 로드 실패 복구 |
| `9ce7fef` | Railway outage 재트리거 (Trial 만료로 무반응 확인) |

**글로벌 규칙 (정본 `docs/GLOBAL.md`):**
- 기본 UI **EN**, 표시 통화 **USD** (브라우저 `ko*` → KO + KRW seed)
- 로케일 우선순위: `localStorage.wa_lang` → `?lang=` → 브라우저 언어 → 기본 EN
- KR 전용 UI(사업자 블록·국내 전화·카카오): `.wa-kr-only` (EN에서 숨김)
- 타이포: Inter 기본 · KO일 때만 Pretendard/Noto
- 정산 원장/PG 금액은 **KRW 유지** (다통화 결제 전)
- 매물 필드: `title_en`, `one_liner_en`, `story_en` · `wakeagain/listing_i18n.py` (xAI 번역 또는 휴리스틱)
- 용어 고정(EN): Starting bid · Current bid · Place bid · View listing · Handover · $0 buyer fees · Free price check
- 소비자 UI에서 **PG** 단어 제거 (홈/핵심 i18n)

**로컬 개발 계정 (라이브 DB와 다름):**
- DB: `data/wakeagain.db` (로컬 ≠ 라이브)
- 예: `local@wakeagain.dev` / `LocalDev123!` 또는 로컬 가입 계정
- 관리자 `/admin/` = 이메일 로그인 아님 · `ADMIN_SECRET` 키

**브라우저 네이티브 검증 주의:** `type=email`/`date` 기본 말풍선은 OS/브라우저 언어. EN UI에서는 `novalidate` + 앱 i18n, 생년월일은 EN에서 텍스트 `YYYY-MM-DD` 권장.

### 2026-08 중순 이전 (master에 포함)

- `758025e` — 콜드스타트 **매물 수집 모드** + deal-share 카드
- `e277455` — free resources 페이지 (ebook + Notion → 리스팅 퍼널)
- `83556c5` — 랜딩 히어로 마우스 팔로우 패럴랙스
- `4fb96cb` — seller-trust 카드 스크롤 겹침 수정

### 2026-07-31 · `3da9b26` (경매·헬프티켓)

- 경매 **라운드**: 공개 보드 = `live`만 · 유찰 시 archive · `POST .../relist`
- **노출 점수**: 매물 품질 + 헬프티켓 가산
- **헬프티켓 (q-credits)**: 포함 1~3 · 스레드 · 추가 구매(PG 전 mock)
- **인증**: `passlib` 제거 · `bcrypt` 직접 해시

## 방문자 카운터 (푸터)

- 형식: `방문자 오늘 N · 전체 M` (i18n 한/영)
- 규칙: 전체=브라우저 1회(`wa_vid`), 오늘=KST 1일 1회, 봇 UA 제외
- DB: `site_counters`, `site_daily`, `site_visitor_seen`
- API: `POST/GET /api/v1/visit`, `GET /api/v1/stats`
- FE: `public/js/footer-visitors.js`

## 사업·콜드스타트 (요약)

- **병목:** 양면 콜드스타트 → **공급(매물) 먼저**. 광고 부족이 1순위 아님.
- **목표 순서:** 라이브 매물 10–30 → 실거래 1–3 → 판매자 채널 고정 → 구매자·바이럴
- **론칭 순서:** 매물 채우기(해외 공급 우선) → 20–50건 후 구매자+결제 ON 동시. 빈 장터에 PG 선행 비추천.
- **거래 레일:** 국경 비의존 단일 프로세스(한↔해·해↔해). 막는 것=이전 불가 매물 유형.
- **PG 전** 수동 입금 확인 UX·임시 계좌 플로우 **신규 금지** (`PLATFORM.md`)
- **공모전 (2026-08-09):** AI 활용 사례 · 분야 **생활 속 AI** · 상세 `workspace/ai-contest-2026-case-submissions.md` / Desktop `공모전_WA_*.png`

## 아키텍처

- `server.py` — FastAPI 진입점.
- `wakeagain/` — `api.py`, `auth.py`, `db.py`, `listing_i18n.py`, `global_config.py`, `scheduler.py`, `backup.py`, `oauth.py`, `pricing.py`, …
- `public/` — 정적 사이트 + `app/`(SPA) + `admin/` + `js/i18n.js` · `i18n-messages.js` · `listings.js` · `footer-visitors.js`
- `mobile/` — Capacitor 모바일 셸
- `scripts/` · `data/` (SQLite)

## 환경 설정

`.env.example` 기반. 주요: `DATA_DIR`, `APP_SECRET`/`JWT_SECRET`, `ALLOWED_ORIGINS`, `XAI_API_KEY`(매물 EN 번역), `WA_DEFAULT_LOCALE`, `WA_DEFAULT_DISPLAY_CURRENCY`, `ADMIN_SECRET`.

- ⚠️ 프로덕션 `ADMIN_SECRET` 기본값 금지.
- ⚠️ **회원 데이터 유실 = 사업 실패** — 백업/삭제 변경은 신중.

## 모바일 빌드 (Capacitor)

```bash
cd mobile
npm install
npm run add:android
npm run android
npm run build:store:prep
```

## 테스트

```bash
python _smoke_check.py
python _predeploy_gate.py
python _test_unit.py
python _auction_suite_test.py
python _auction_advanced_test.py
python _block_user_test.py
python _deal_flow_test.py
python _check_live_nav.py
python _verify_handover.py
```

## 작업 방식 (사용자 강제)

1. **애매하면 되묻기** — 추측 구현 금지  
2. 「완료」 전 핵심 한두 줄 되짚기  
3. 사이트 기준 위반 아이디어는 코드 반영 금지 (이유만)  
4. 수익성 → 사업성 → 안정성 순 평가  
5. 「전부」면 부분 실행으로 끝내지 말 것  
6. **말한 것만** — 멋대로 타협·하이브리드 금지  

## 금지

- **PG 전** 수동 입금 확인 UX·임시 계좌 플로우 등 우회 기능 **신규 추가 금지**
- 가짜 GMV·성사 보장·AI 검수 배지 마케팅
- 삭제된 **CoreLabs / CoreLabsPromo** 로컬 툴 복원
- `system32` 등 비프로젝트 cwd에서 제품 작업
- 시크릿·`.env`·토큰 커밋
- 사이트에 WakeAgain **한글 음차** 표기

## 의도적 미완 (사람 행정·다음 코드)

- PG 실결제·웹훅 · 통신판매중개 **행정 신고 번호** · Play 내부테스트
- Railway **Hobby 결제 후 라이브 복구**
- EN 잔여: `sell.html` / `buy.html` / `guide/*` · `keywords_en` · 앱 딥 카피 PH 톤 2차 · 모바일 드로어
- 약관·가이드 문서 PG 표현 잔여 점검

## 트리거 말

| 말 | 동작 |
|----|------|
| WakeAgain 이어서 / 웨이크어게인 불러와 | PLATFORM + GLOBAL + 이 파일 + 열린 일 요약 |
| WakeAgain EN 카피 이어서 | `docs/GROK_TO_CLAUDE_HANDOFF_2026-08-10.md` 부터 |
| sell/buy/guide EN 폴백 | 랜딩 수준 data-i18n + EN 폴백 |
| 매물 keywords_en | 태그 영문 정규화 |
| SNS 로그인 연결 | `docs/OAUTH_*` |
| PG | 결제 링크·웹훅→`paid` 만 · pre-PG 우회 금지 |

## 배포 전 최소 확인

```text
python _smoke_check.py
# 또는 python _predeploy_gate.py
git status   # docs/marketing/logs/* 등 untracked 제외
```

`master` push 후 Railway 상태·`https://wakeagain.com/health` (플랜 유효 시).  
EN 검수: `/?lang=en` 히어로·카드 Starting bid·`title_en` · `/?lang=ko` 한국어 유지.

## 언어

사용자와 **한국어**로 소통한다.
