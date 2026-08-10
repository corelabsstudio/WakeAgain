# WakeAgain — Claude Code 안내

이 파일을 읽은 뒤 **현재 디스크·git·라이브**를 재검증하고 작업한다.  
옛 트랜스크립트·Grok 메모리는 자동 동기화되지 않는다. 아래 문서가 정본이다.

**마지막 문서 갱신:** 2026-08-11 (PortOne V2 결제 연동 착수 — 카드 실제 테스트 완료, PayPal PG 계약 심사 대기)

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
| 사업자 | 705-04-02867 · `/legal/business.html` (KO) + `/legal/business.en.html` (EN 요약, 2026-08-11 신규) 게시 완료 |
| 브랜드 | **WakeAgain 영문만** (사이트 한글 음차 금지) |

## ⚠️ 인프라 상태 (2026-08-11 갱신 — Railway Trial 이슈 해결됨)

- **Railway Hobby 결제 완료 (2026-08-10) → 라이브 정상.** 이전 "Trial 만료·Application not found" 이슈는 해소됨.
- 로컬 Railway CLI 는 여전히 **로그인 안 되어 있음** (`railway login`은 이 프로젝트의 비대화형 셸에서 불가 — 사용자가 직접 대화형 터미널에서 실행 필요). 배포는 **GitHub push 자동배포**로만 진행 중, 문제 없음.
- **환경변수 추가 후 주의:** Railway는 변수 추가만으로 자동 재시작되지 않을 수 있음 — Variables 탭에 "Apply N change / Deploy" 대기 패널이 뜨면 **Deploy 버튼을 직접 눌러야** 반영됨 (2026-08-11에 XAI_API_KEY 추가 때 실제로 이 단계를 놓쳐서 한동안 반영 안 됐던 적 있음).

## 최근 배포 이력 (요약 · 최신 우선)

### 2026-08-11 · PortOne V2 결제 연동 착수 + 국가 배지 + 매물 페이지 카피 정리 (`07fca5f`, `ecb6d2a`)

**배경:** PayPal 채널 등록 시 "포트원 전용 링크로 가입/연동한 계정만 가능" 에러를 한 번 겪음 → PortOne 콘솔의 "⚡ 전자결제 신청" (해외결제 → 페이팔 → 결제모듈 **일반결제(SPB)/정기결제(RT) → V2** 선택)으로 재신청해야 정상 등록됨. `hhs1261@naver.com` 네이버 메일함에 전용 온보딩 링크가 옴 — 다음에 또 PG 채널 추가할 때 이 절차부터 밟을 것.

| 커밋 | 내용 |
|------|------|
| `07fca5f` | **PortOne V2 카드 결제** — `wakeagain/payments.py`(신규): `build_payment_request`/`fetch_payment`/`verify_webhook`(Standard Webhooks HMAC). `POST /payment/request`·`/payments/verify`·`/payments/webhook` 3개 엔드포인트. `mark_deal_paid()`에 연결. **로컬에서 실제 PortOne 결제창(Toss 채널)까지 뜨는 것 확인** — 카드 정보 입력만 사용자가 직접 함(안전규칙상 대행 불가). ⚠️ 이때 발견: PortOne 응답에서 seller_country가 `_refresh_auction_ended`의 재조회로 날아가는 버그 있었음 → 리프레시 전에 미리 떼어내는 식으로 고침(같은 패턴 재사용 시 주의) |
| `07fca5f` | **PayPal 채널(SPB)** — `PORTONE_CHANNEL_KEY_PAYPAL`(`.env`, git 미포함). `loadPaymentUI(uiType:"PAYPAL_SPB")` 임베드 버튼 방식(카드 팝업과 다름). STC(위험정보, PayPal이 "중고거래/디지털상품" 고위험군에 필수 요구) bypass 필드는 최소값만 넣음 — 정확한 필드 스펙은 PortOne STC 가이드가 이미지 PDF라 못 읽음, **PG 계약 담당자 연락 오면 확인 필요**. **2026-08-11 기준 PG사 계약 심사 대기 중(영업일 3일)** — 승인 전까진 실결제 안 될 수 있음 |
| `07fca5f` | **수수료 정책 변경**: 국내 10%(구매자 0원, 그대로) / **해외(PayPal 채널로 결제) 판매자 19%**(`FEE_RATE_CROSSBORDER`, db.py — 페이팔 실제 계약 수수료 나오면 재조정 필요한 **임시값**), 구매자는 여전히 0원(`docs/GLOBAL.md`의 "$0 buyer fees" 유지 결정, `mark_deal_paid` 직전 `adjust_fee_invoice_for_crossborder()`로 자동 상향). **최소 수수료 5,000원** 신설(`FEE_MIN_KRW`) — 이용약관 제13조·terms.html·terms.en.html 동기화 완료 |
| `07fca5f` | **국가 배지** — `users.country`(ISO alpha-2) 신규 컬럼, 가입·프로필 폼에 국가 선택 추가, `public/js/countries.js`(국기 이모지 헬퍼) 신규, 매물 카드·상세 페이지에 판매자 국기 표시 |
| `07fca5f` | **OG 메타태그** — `wakeagain/og.py` 신규, `server.py`에 `/project.html` 라우트 가로채서 매물별 영문 OG/Twitter 카드 서버사이드 주입 (크롤러는 JS 안 돌리므로 정적 삽입 필수) |
| `07fca5f` | **Share & Promote** — 매물 상세 페이지 판매자 전용 영역에 X 공유·링크 복사·Reddit 템플릿 (전부 영문 하드코딩, 사이트 언어 설정과 무관) |
| `07fca5f` | 하단 탭바 CSS 버그 수정 — `repeat(3,1fr)`인데 버튼 4개(홈·프로젝트·올리기·내 정보)라 4번째가 줄바꿈되던 것 → `repeat(4,1fr)` |
| `ecb6d2a` | 매물 상세 페이지 **카피 중복 제거** — `.bid-notice`(문단 5개)가 바로 아래 "4단계" 시각 박스랑 같은 내용을 두 번 말하고 있어서 1줄로 축소. "안전·책임 고지" 7개 항목에 아이콘 부착(불릿 점 → SVG 아이콘, 문구는 법적 고지라 거의 유지) |

**미검증/후속 필요:**
- PayPal 실제 결제 **한 번도 안 해봄** — PG 계약 승인 오면 `loadPaymentUI`의 콜백 시그니처(`onPaymentSuccess`/`onPaymentFail`)·컨테이너 자동감지(`.portone-ui-container` 클래스)가 문서 그대로 작동하는지 실제로 확인 필요
- STC `bypass.paypal_v2` 필드 최소값만 채움 — PG 담당자 연락 오면 정확한 필드명 확인해서 보강
- `FEE_RATE_CROSSBORDER = 0.19`는 페이팔 원가(국경간 4.4%+환전 4%≈8.4% 추정치) 기반 임시값 — 실제 계약 수수료율 확정되면 `wakeagain/db.py` 상수 하나만 고치면 됨
- 웹훅 시크릿(`PORTONE_WEBHOOK_SECRET`) 미설정 — 콘솔 "결제알림(Webhook) 관리"에서 발급 필요(엔드포인트 등록 후 나옴, 도메인 붙은 뒤 진행 권장)
- 홍보(Reddit/X/HN) 카피·실행은 이번 세션에 **논의만 하고 착수 안 함** — 결제 연동을 먼저 끝내기로 사용자가 결정

### 2026-08-11 · 해외 우선 전환 + 사이트 전체 i18n 정비 + 매물 양방향 번역 (`92527f3` … `6b3115c`)

**배경:** 사용자가 세션 중 시장 우선순위를 뒤집음 — "한국 먼저"(2026-07-20 확정, `PLATFORM.md`) → **"해외 먼저"**(2026-08-11 재확정). 이 커밋들은 전부 그 결정에 따른 후속작업.

| 커밋 | 내용 |
|------|------|
| `92527f3` | sell.html/buy.html/manifest.webmanifest EN 전환 잔여 마무리, `$` 이스케이프 깨짐 버그 수정 |
| `402436b`~`3860981` | 매물 카드에 실제 스크린샷(`demo_images`) 노출 — 예전엔 항상 이니셜 아이콘만 썼음. `loading="lazy"` 제거(above-the-fold라 즉시 로드해야 함) |
| `be13b5d`~`cf84ed4` | **사이트 전체 data-i18n 키 감사** — 94개 키가 `i18n-messages.js`에 아예 없어서 언어 전환이 안 먹혔음(nav·footer·hero·404·안내카드 등). 전부 채움 + `data-i18n-html` 누락으로 `<strong>` 태그가 문자 그대로 보이던 버그 수정 |
| `8e33d49`, `ca96b25` | **매물 본문 양방향 자동번역** — `title`/`one_liner`만 되던 걸 `story`/`features`/`audience`/`works_now`/`limits`/`keywords`까지 확장, KO→EN뿐 아니라 EN→KO도. DB에 `*_en`/`*_ko` 컬럼 13개 추가, `listing_i18n.fill_listing_i18n()`이 등록 시점에 xAI로 한 번에 번역(비용 통제), `ensure_rows_i18n()`이 조회 시 누락분 지연 백필. **XAI_API_KEY를 이 세션에서 처음으로 Railway에 등록** — 이전까진 이 번역 기능(기존 title_en 포함) 한 번도 실제로 작동한 적 없었음(항상 휴리스틱/시드데이터였음) |
| `b17c1b4`, `f7729e4` | **법적 고지 해외판** — `legal/privacy.en.html`, `legal/business.en.html` 신규(사업자 등록정보는 원문 한글 유지, 라벨만 번역). `i18n.js`에 링크 자동전환 로직 추가(25개 페이지 수동수정 없이 해결) + `terms/privacy/business.html` ↔ `.en.html` **양방향 자동 리다이렉트** (직접 URL 접속도 커버) |
| `6b3115c` | PLATFORM.md 시장우선순위 뒤집기 기록 + **PG사 조사·선정**: Stripe 탈락(한국 사업자 정산 불가) → **PortOne** 선정(파트너 정산 자동화가 경매 수수료 분배 구조와 일치). 사용자가 PortOne 가입 완료·통신판매업 신고 진행 중, 실제 API 키·PG 가맹 심사 상태는 미확인 |

**미검증/후속 필요:**
- 백엔드(Python)가 직접 내려주는 하드코딩 한국어 문자열이 `db.py`/`api.py`에 **약 595개** — 신용등급 라벨("신규") 등 일부는 여전히 항상 한국어로 뜸. 프론트 i18n 정비로는 못 고침, 별도 백엔드 작업 필요
- `/app` SPA(쿠폰·선물·정산계좌·프로필 등) 46개 키가 반대로 **EN만 있고 KO 없음** — 한국 사용자가 봐도 영어로 보임
- `delete-account.html`(Google Play 계정삭제 안내) 영문판 없음
- PortOne 실제 연동(웹훅→`paid`)은 API 키 확보 전까지 착수 안 함 (`PLATFORM.md` §B)

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
- 매물 필드 (2026-08-11 확장): `title`/`one_liner`/`story`/`audience`/`works_now`/`limits_note`/`features`/`keywords` 전부 `_en`+`_ko` 컬럼 보유, 양방향(KO↔EN) 번역 · `wakeagain/listing_i18n.py`의 `fill_listing_i18n()`(생성시) / `ensure_rows_i18n()`(조회시 지연 백필) · xAI 필요(`XAI_API_KEY`, 2026-08-11부터 Railway에 실제 등록됨)
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

`.env.example` 기반. 주요: `DATA_DIR`, `APP_SECRET`/`JWT_SECRET`, `ALLOWED_ORIGINS`, `XAI_API_KEY`(매물 양방향 번역 — **2026-08-11부터 Railway에 실제 값 등록됨**, 그 전엔 문서에만 있고 비어있어서 번역 기능이 항상 조용히 실패했음), `WA_DEFAULT_LOCALE`, `WA_DEFAULT_DISPLAY_CURRENCY`, `ADMIN_SECRET`.
- **PortOne 결제** (2026-08-11 추가, 로컬 `.env`에만 있음 — Railway 등록 여부 확인 필요): `PORTONE_STORE_ID`, `PORTONE_CHANNEL_KEY`(카드), `PORTONE_API_SECRET`, `PORTONE_CHANNEL_KEY_PAYPAL`(PG 계약 심사 대기), `PORTONE_PAYPAL_MERCHANT_ID`, `PORTONE_WEBHOOK_SECRET`(아직 미발급)
- 환경변수 값 확인은 Railway 대시보드 Variables 탭에서만 가능(CLI 미로그인) — **값 실화 여부를 절대 추측하지 말 것**, 문서에 이름이 있다고 실제로 설정돼있다는 뜻 아님(2026-08-11에 실제로 이 착각으로 반나절 헤맴).

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
7. **작업 완료 시 자동 커밋+푸시** (2026-08-11 확정) — 로컬 검증까지 끝나면 매번 묻지 말고 바로 `git commit` + `git push origin master`. Railway가 push로 자동 배포되므로 이게 곧 배포 트리거. 단, 애매하거나 위험한 변경(스키마·삭제·PG 등)은 여전히 확인 후 진행.

## 금지

- **PG 전** 수동 입금 확인 UX·임시 계좌 플로우 등 우회 기능 **신규 추가 금지**
- 가짜 GMV·성사 보장·AI 검수 배지 마케팅
- 삭제된 **CoreLabs / CoreLabsPromo** 로컬 툴 복원
- `system32` 등 비프로젝트 cwd에서 제품 작업
- 시크릿·`.env`·토큰 커밋
- 사이트에 WakeAgain **한글 음차** 표기

## 의도적 미완 (사람 행정·다음 코드)

- **PayPal 실결제 검증** — 코드는 다 짜서 배포됨(`07fca5f`), **PG사 계약 심사 대기 중**(2026-08-11 신청, 영업일 3일). 승인 오면 실제 결제 한 번 끝까지 돌려서 `loadPaymentUI` 콜백·STC 필드 확인해야 함
- **웹훅 시크릿** 미설정 (`PORTONE_WEBHOOK_SECRET`) — 서버 검증(`/payments/verify`)은 이미 동작하므로 급하지 않음, 콘솔에서 발급만 하면 됨
- **홍보 실행** (Reddit r/SideProject·r/indiehackers, X #buildinpublic, HN Show HN) — 전략은 논의 완료, 카피 초안·실제 게시는 미착수
- 통신판매중개 **행정 신고 번호** (게시 대기) · Play 내부테스트
- 백엔드 하드코딩 한국어 문자열 (`db.py`/`api.py` 약 595개 — 신용등급 라벨 등 일부 UI 요소가 언어와 무관하게 항상 한국어)
- `/app` SPA 46개 키 KO 누락 (쿠폰·선물·정산계좌·프로필 — 지금은 한국 사용자가 봐도 영어)
- `delete-account.html` 영문판 없음
- 모바일 드로어 EN 잔여

## 트리거 말

| 말 | 동작 |
|----|------|
| WakeAgain 이어서 / 웨이크어게인 불러와 | PLATFORM + GLOBAL + 이 파일 + 열린 일 요약 (특히 위 "미검증/후속 필요" 목록부터) |
| WakeAgain EN 카피 이어서 | `docs/GROK_TO_CLAUDE_HANDOFF_2026-08-10.md` 부터 |
| 백엔드 한국어 문자열 정리 | `db.py`/`api.py` 하드코딩 약 595개 감사부터 (2026-08-11 발견, 미착수) |
| 앱 SPA 한국어 복구 | `i18n-messages.js` EN-only 46개 키에 KO 대응 추가 |
| PortOne 연동 / 페이팔 이어서 | 카드 결제는 완료·검증됨(`07fca5f`). 페이팔은 PG 계약 심사 상태부터 확인(`hhs1261@naver.com` 메일함) → 승인됐으면 `wakeagain/payments.py`의 `build_paypal_payment_request` 실결제 테스트부터. pre-PG 우회 금지 (`PLATFORM.md` §B) |
| SNS 로그인 연결 | `docs/OAUTH_*` |
| PG | 결제 링크·웹훅→`paid` 만 · pre-PG 우회 금지 |
| 홍보 시작하자 / 매물 채우기 홍보 | Reddit(r/SideProject·r/indiehackers·r/buildinpublic)·X(#buildinpublic)·HN(Show HN) 전략은 확정됨(이번 세션 논의) — 카피 초안부터 시작 |

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
