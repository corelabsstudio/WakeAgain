# WakeAgain — Claude Code 안내

이 파일을 읽은 뒤 **현재 디스크·git·라이브**를 재검증하고 작업한다.  
옛 트랜스크립트·Grok 메모리는 자동 동기화되지 않는다. 아래 문서가 정본이다.

**마지막 문서 갱신:** 2026-09-02 (🔄 **경매 폐지 → 고정가(판매가) + 가격 제안(offer) 구조로 전환** — 토스 재심사 대비)

## ⚠️ 동시 작업 규칙 (Claude Code ↔ Cowork) — 작업 시작 전 필독

이 저장소는 **Claude Code와 Cowork가 동시에** 작업한다. 두 에이전트는 서로의 대화·상태를
**볼 수 없다.** 세션 간 실시간 연동은 없고, **디스크가 유일한 공유 채널**이다.
(2026-08-15 실측: 세션 조회 도구에 상대 세션이 잡히지 않음.)

실제로 2026-08-15 「매물 등록 필수 필드 정책」 작업에서 양쪽이 `public/app/app.js`를 동시에
편집했다. 편집 위치가 우연히 안 겹쳐서 사고가 안 났을 뿐이다.

### 1. 편집 전 점유 선언 (필수)

파일을 고치기 **전에** `.claude/ACTIVE_WORK.md`에 항목을 추가하고, 끝나면 지운다.
이게 상대가 볼 수 있는 유일한 신호다.

```
- [Claude Code] wakeagain/api.py, wakeagain/db.py — 필수 필드 검증 — 2026-08-15 15:10 시작
```

작업 시작 시 이 파일을 **먼저 읽고**, 내가 건드릴 파일이 이미 잡혀 있으면
그 파일은 피하거나 사용자에게 조율을 요청한다.

### 2. 기본 분담 (점유 선언이 없을 때의 기본값)

| 영역 | 기본 담당 |
|---|---|
| `wakeagain/*.py` — DB·API·백엔드 | Claude Code |
| `public/**` — HTML·CSS·JS·i18n | Cowork |
| `CLAUDE.md` | 양쪽 가능하나 **다른 섹션**만. 같은 섹션 동시 수정 금지 |

고정 규칙이 아니라 기본값이다. 바꾸려면 ①의 점유 선언으로 덮어쓴다.

### 3. git

- **작업 단위마다 커밋한다.** 여러 세션 작업이 한 덩어리로 쌓이면 되돌리기가 위험해진다
- **`git checkout -- .` · `git reset --hard` 등 광범위 되돌리기 금지.** 상대 작업까지 날아간다
- 커밋 시 `git add .` 대신 **경로를 지정해서 스테이징**한다 (무관한 로그·스크립트 혼입 방지)
- `master` push = **Railway 배포**다. 배포 지시가 없으면 커밋까지만 한다

### 4. 상대가 이미 해놓은 코드를 만났을 때

파일을 열었는데 내가 안 쓴 코드가 이미 있으면 **덮어쓰지 말고** 인터페이스가 맞는지 확인한 뒤
그대로 쓴다. 중복 구현하지 말 것. 사용자에게 "이미 있어서 재사용했다"고 보고한다.

### 2026-08-18 · 위탁 등록(consignor) — 판매자 가입 없이 매물 유지

**배경:** GitHub 아웃리치 누적 12건 중 응답 2건(동의 1·거절 1), **가입 전환 0**. 특히
`onsuYumYumYum` 소유자는 2026-08-03에 "넵 대신 올려주셔도 좋습니다"까지 답했는데도 15일째
가입하지 않았다. 즉 병목은 설득이 아니라 **가입 요구** 자체다.

**발견한 구조적 결함:** 기존 위탁 경로는 「대신 등록 → 상대가 가입 → `transfer-owner`로 인계」였는데,
`project_transfer_blockers`가 `bids_exist` / `already_sold` / `deal_in_progress` / `fee_invoice_exists` /
`help_tickets_exist`를 전부 막는다. **즉 매물이 실제로 잘 되기 시작하는 순간 인계가 영구히 불가능해진다.**
인계를 전제로 한 설계 자체가 틀렸다.

**구현:** `projects`에 위탁자 컬럼 6개 추가(`consignor_name`·`consignor_contact`·`consignor_source_url`·
`consignor_consent_quote`·`consignor_consent_at`·`consignor_payout_note`) + `database.set_project_consignor()` +
관리자 전용 `POST /api/v1/admin/projects/{id}/consignor` + 관리자 화면 입력란. `public/admin/sw.js`
`CACHE`를 `v6-consignor`로 범프.

**설계 요점 3가지:**
1. **`owner_id`는 건드리지 않는다.** 입찰·거래·수수료·헬프티켓이 전부 owner_id에 묶여 있으므로 운영
   계정에 고정해두고, 실제 판매자는 별도 데이터로 들고 간다. 인계가 필요 없어지므로 차단 조건과 무관해진다.
2. **정산 정보는 팔린 뒤에 받는다**(`consignor_payout_note`). 돈이 오가기 전에는 상대에게 아무것도 요구하지 않는다.
3. **위탁자 신원·연락처는 PII라 공개 응답에 절대 싣지 않는다.** 공개 dict에는 불리언 `is_consigned`만
   나가고, 상세는 `include_private=True`에서만. 이 불리언은 필요하다 — 한 계정이 매물을 다 갖고 있는
   이유를 구매자가 알 수 있어야 한다(TRUST.md 신뢰 게이트와 같은 취지).

`transfer-owner`는 **삭제하지 않고 선택 경로로 남겼다** — 위탁자가 스스로 계정을 만들어 직접 운영하겠다고
할 때만 쓴다. 관리자 화면 문구도 그렇게 바꿨다.

**검증:** `_consignor_test.py` 신규 19개 전부 통과(owner_id 불변 · 공개 응답 PII 미노출 · **입찰 후에도
위탁 정보 수정 가능**한 반면 같은 상황에서 `transfer-owner`는 `bids_exist`로 차단됨을 대조 확인 ·
알 수 없는 필드 거부 · 관리자 인증 필수). `_transfer_owner_test.py` 통과, `_auction_suite_test.py` 43/43,
`_smoke_check.py` 전체 통과. ⚠️ 스모크는 **DB 사본으로 돌릴 것** — 개발용 `data/wakeagain.db`에 신고
카운트가 누적돼 있으면 report/auto-pause 2건이 오탐으로 실패한다(2026-08-18에 A/B로 확인, 코드 무관).

**후속 필요:**
- **라이브 매물 #8 백필** — `onsuYumYumYum` 위탁 정보(동의 인용·GitHub 이슈 URL)를 운영 관리자 화면에서
  입력해야 함. 지금은 CLAUDE.md 산문에만 있고 DB에는 없다.
- **아웃리치 문구 수정** — "가입하시면 명의를 넘겨드립니다"를 더 이상 쓰지 말 것. 가입은 이제 불필요하다.
- **공개 페이지 배지** — `is_consigned`를 매물 상세에 노출하는 건 `public/**` 영역이라 미구현(Cowork 담당).

### 2026-08-15 · PortOne 실서비스(Railway) 환경변수 등록 + 페이팔 계약완료 확인 (코드 커밋 없음 — 설정 작업)

**배경:** 사용자가 PortOne 콘솔 스크린샷을 보내며 "이 상태로 토스페이먼츠 신청해도 해외 결제도 가능한가" 질문 → 확인 과정에서 더 큰 문제 발견.

**발견 1 — 페이팔은 진짜 계약 완료:** PortOne 콘솔 확인 결과 페이팔 상태 **"계약 완료"** · 상품 "해외결제 일반결제" · 실연동(live) 채널 `WakeAgain 페이팔` (PG Provider `paypal_v2`, MID `H5FF6VTZU8JPS`, 채널키 `channel-key-c11a9fe2-278d-44f7-96a9-bcbfc4875eb5`). 로컬 `.env`의 `PORTONE_CHANNEL_KEY_PAYPAL` 값과 정확히 일치(해시 비교로 검증, 값 자체는 노출 안 함). `PLATFORM.md`/이 문서에 "PG사 계약 심사 대기 중"으로 남아있던 게 실제로는 승인 완료된 상태였음.

**발견 2 — 그런데 Railway엔 PortOne 환경변수가 하나도 없었음:** `wakeagain.com/api/v1/config`로 `payment_policy.portone.enabled`/`paypal_enabled` 확인했더니 둘 다 `false`. Railway `wakeagain` 서비스 Variables에서 `PORTONE` 검색 결과 **0건**. 로컬 `.env`에는 값이 있었지만 Railway엔 한 번도 옮겨진 적이 없었던 것 — "로컬에서 결제창까지 뜨는 것 확인"(`07fca5f`, 2026-08-11)은 로컬 한정이었고 실서비스는 계속 결제 기능 자체가 꺼져 있었던 상태.

**조치:** 사용자가 Railway Variables → Raw Editor에 아래 5개를 직접 붙여넣고 Update Variables + Deploy까지 완료(API 키·시크릿 값은 안전 규칙상 Claude가 직접 입력 불가 — 값 확인·입력 전부 사용자가 수행):
`PORTONE_STORE_ID` · `PORTONE_CHANNEL_KEY`(카드) · `PORTONE_API_SECRET` · `PORTONE_CHANNEL_KEY_PAYPAL` · `PORTONE_PAYPAL_MERCHANT_ID`

배포 후 `wakeagain.com/api/v1/config` 재확인 → `portone.enabled: true`, `paypal_enabled: true` 둘 다 반영 확인.

**⚠️ 중요 — "enabled: true"의 실제 의미:** `payments.py`의 `portone_enabled()`/`paypal_enabled()`는 **환경변수 3개(store_id·channel_key·api_secret)가 비어있지 않은지만 검사**한다. PG사(토스/페이팔)가 실제로 가맹점 계약을 승인했는지는 전혀 확인하지 않음. 페이팔은 콘솔상 "계약 완료"라 이 플래그가 실제 결제 가능 상태와 일치하지만, **토스페이먼츠는 아직 "신청 접수 및 계약 진행 중"(3단계 중 1단계, PG사 접수 완료)** — 즉 카드결제 쪽은 서버가 "enabled: true"라고 답해도 실제로는 Toss 승인 전이라 진짜 카드 결제는 실패할 수 있음. 사용자가 세션 중 토스페이먼츠 "등록비"를 결제했지만, 이는 계약 진행 단계의 비용이지 승인 완료를 뜻하지 않는다고 확인·전달함.

**교훈 (일반화):** PG 관련 `*_enabled` 플래그를 코드에서 확인할 때는 "환경변수 존재 여부"와 "PG사 실제 승인 여부"를 반드시 구분해서 말할 것 — 둘을 섞으면 아직 승인 안 난 결제수단을 라이브로 오인하기 쉽다.

**후속 필요:**
- ~~**토스페이먼츠**: PortOne 콘솔에서 "계약 완료"로 바뀔 때까지 대기.~~ → **2026-09-02 심사 거부로 종결**(경매·입찰 구조 사유, 최상단 항목 참조). 카드 결제 홍보 금지는 유지.
- **페이팔**: env var는 다 들어갔지만 실결제(`loadPaymentUI` 콜백·STC 필드 등)는 여전히 한 번도 안 해봄 — 실매물로 낙찰→결제 끝까지 테스트 필요.
- **웹훅 시크릿**(`PORTONE_WEBHOOK_SECRET`)은 이번에도 미등록 — 콘솔에서 별도 발급 필요.

### 2026-08-15 · 매물 시작가 인상·인하 (진행 중 라운드 · 무입찰 한정) (`fe84f0b`)

**배경:** 사용자가 "올린 매물 시작가를 올린 후에도 내릴 수 있게 해달라" 요청 → 코드 확인 결과 애초에 판매자가 시작가를 바꾸는 UI/API 자체가 없었음(재등록(relist) 백엔드는 방향 제한 없이 가격을 받지만, 프론트가 가격 입력창을 아예 안 보냄). 되물어본 결과 사용자 의도는 "시작가를 너무 높게 잡아서 안 팔리면 낮춰서 입찰을 유도"하는 용도.

**구현:** `PUT /api/v1/projects/{id}/price` 신규(`wakeagain/api.py`) — **라이브 라운드 + 입찰 0건**일 때만 시작가를 자유롭게 올리거나 내릴 수 있음(상태별 최저가 정책은 그대로 적용, `price_policy.validate_start_price` 재사용). 입찰이 하나라도 들어오면 `bids_exist`로 막고 재등록(relist)을 안내 — 입찰자가 이미 커밋한 뒤 시작가가 바뀌는 공정성 문제를 피하기 위해 의도적으로 제한. `public/app/app.js`의 "내 매물" 카드에 "시작가 조정" 버튼 추가(무입찰 라이브 매물에만 노출), `public/js/api.js`에 `updateProjectPrice()`, `i18n-messages.js`에 한/영 문구 5개. 정적 자산 변경이라 `sw.js` `CACHE`를 `v59-pricelive`로, 관련 `?v=` 쿼리들도 `20260815-pricelive`로 범프.

**검증:** 자동화 테스트로 인상·인하·최저가 미만 거부·입찰 후 잠금·타인 매물 접근 차단 5개 시나리오 확인, `_smoke_check.py` 전체 통과 + `_auction_suite_test.py` 43/43 통과. 브라우저로 버튼이 무입찰 매물에만 뜨는 것도 확인.

### 2026-08-15 · 방문자 카운터 소유자 옵트아웃 (`bc41299`)

**배경:** 사용자가 본인이 사이트 접속할 때 방문자 수에 안 찍히게 할 수 있냐고 질문.

**구현:** `public/js/footer-visitors.js`에 `?notrack=1` 쿼리파라미터로 1년짜리 `wa_notrack` 쿠키 설정 → 이후 이 브라우저는 `/api/v1/visit` POST(카운트 증가)를 건너뛰고 GET으로 현재 숫자만 조회해서 표시(`?notrack=0`으로 원복). 백엔드·스키마 변경 없음, 기존 봇 UA 제외 로직(`_BOT_UA`, api.py)과 같은 결의 "카운트 정직성" 보강.

**사용법:** `https://wakeagain.com/?notrack=1` 한 번 접속하면 그 브라우저는 계속 제외됨. 기기·브라우저별로 각각 한 번씩 해줘야 함(쿠키 기반).

### 2026-08-15 · xAI 번역 모델 갱신 (`b86194a`)

**배경:** 사용자가 "Grok 최신 소식 조사해봐" 요청 → Grok 4.6 출시 확인 후, WakeAgain이 실제 쓰는 모델명이 최신을 자동 추종하는지 확인 요청.

**발견:** `listing_i18n.py`(두 곳)가 `os.environ.get("XAI_MODEL", "grok-4-1-fast-non-reasoning")`로 기본값이 박혀 있었는데, 이 모델명이 xAI 공식 현재 라인업(`grok-4.6`/`4.5`/`4.3`/`4.20-*`)에 없는 구세대 이름이었음. **xAI는 모델을 명시 지정하면 자동으로 최신화되지 않고, `-latest` 별칭도 신뢰 불가**(`grok-4-latest`가 현재 Grok 4.3로 동결돼 있음) — 별도 확인 없이는 계속 구모델에 머무는 구조.

**조치:** 짧은 구조화 JSON 번역(제목/한줄소개/story 등)이라는 용도에 맞춰 `grok-4.20-non-reasoning`으로 교체 — 현재 라인업 중 가장 저렴(입력 $1.25/1M, 출력 $2.50/1M, `grok-4.6` 대비 절반 이하)하면서 컨텍스트도 100만 토큰으로 더 큼. 추론(reasoning) 티어 플래그십은 이 용도엔 불필요하다고 판단해 제외.

**How to apply:** 이후 세션에서 "번역 품질이 왜 이래" 같은 얘기가 나오면 이 모델명부터 확인할 것. `XAI_MODEL` 환경변수가 Railway에 별도로 설정돼 있으면 이 코드 기본값을 덮어쓰므로, Railway Variables 탭도 같이 확인 필요(2026-08-15 세션은 코드 기본값만 변경, Railway 쪽 값 실재 여부는 미확인 — CLI 미로그인이라 대시보드에서 직접 확인 필요).

### 2026-08-14 · 매물 상세 페이지 EN 모드 한글 누출 수정 (`3b1170d`)

**배경:** 사용자가 로드로그 매물(id=11) EN 모드 스크린샷에서 한글 발견 — "SELLER TRUST 코어랩스 · credit 35 신규" 등. 확인 과정에서 `#pEnglishReadyBadge`(RoadLog엔 안 보임)는 버그가 아니라 **판매자가 밝힌 "제품 자체의 영문 UI 지원 여부"** 배지라 정상 동작임을 확인(사용자 오해 정정) — 페이지 번역 완성도와는 무관.

실제 버그 3건, 전부 `public/project.html`:
1. **신용등급 라벨** — `database.credit_grade()`(db.py)가 항상 한글 label만 반환("신규" 등), 프론트가 그대로 출력. `cr.grade`(elite/great/trusted/normal/new/risk, 이미 영문 키)로 EN 라벨 매핑 추가해 해결 — 백엔드 스키마 변경 없이 프론트에서만 처리.
2. **포함 자산(assets)** — 구버전 매물이 슬롯값(`code`) 대신 원문 한글("코드")을 그대로 저장한 레거시 데이터 존재 → `assetMap`에 한글 키도 같이 매핑해 방어.
3. **데모 자유텍스트(`p.demo`)** — `story`/`audience`/`works_now`/`limits_note`와 달리 `_en` 컬럼 자체가 없어 번역 파이프라인 대상이 아님. EN 모드에서 한글 감지 시 원문 대신 "seller notes in Korean" 폴백으로 대체(스키마 확장은 리스크 대비 보류 — 필요시 `listing_i18n.py`의 `_LONG_FIELD_SPECS`에 `demo_en`/`demo_ko` 추가하는 게 정석 후속 작업).

`_smoke_check.py` 전체 통과 + 인라인 스크립트 2개 node --check 통과 확인 후 커밋·푸시(사용자 부재 중, 규칙 7에 따라 자동 배포). sw.js `CACHE`를 `v57-eni18nfix`로 범프.

**후속 필요:** `demo` 필드 정식 이중언어 지원(스키마 컬럼 추가는 확인 후 진행 — 사용자 부재 시 보류한 부분).

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

### 2026-09-02 · 🔄 경매 폐지 → 고정가(판매가) + 가격 제안(offer) 전환 (`f6f5821` 외)

토스가 **입찰 형식(가격 미확정)**을 사유로 가맹을 거부했으므로(바로 아래 항목), 사용자 결정에 따라
판매 방식 자체를 바꿨다. **선택지 1번을 실행한 것이고, 경매는 이제 없다.**

**새 모델:** 판매자가 **판매가**를 정하고, 구매자는 ①판매가로 바로 구매 ②판매가보다 낮은 금액으로
**가격 제안** 중 하나를 택한다. 판매자는 48시간 안에 수락·거절(`OFFER_RESPONSE_HOURS`),
무응답이면 자동 만료. **역제안 없음.** 한 구매자당 대기 제안 1건(새 제안이 이전 것을 `replaced`).
제안 하한 = 상태 등급 최저가, 상한 = 판매가 미만. 제안 금액은 기본 **공개**(`OFFER_AMOUNTS_PUBLIC=0`으로 비공개 전환).

**삭제된 경매 동작 3가지 — 되살리지 말 것:**
1. **마감 자동 낙찰** → 게시 기간(기본 7일) 종료 시 자동 성사 없이 목록에서 내려가고 대기 제안이 만료된다
2. **차순위 자동 낙찰**(`SECOND_BIDDER_AUTO`) → 미입금 시 성사 무효 + 신용 감점 + **매물이 다시 판매 중으로 복귀**
3. **즉시구매가(`price_buy_now`)·호가 단위(`min_increment`)** → 판매가 자체가 구매가라 불필요

**⭐ 딜 플로우는 한 줄도 안 바꿨다.** `finalize_sale` → 수수료 청구서 → 1시간 결제 → 이전 → 검수 →
정산 체인을 그대로 재사용하고, **진입점만** 낙찰에서 「판매가 구매 / 제안 수락」으로 갈아끼웠다.
PortOne·페이팔 결제 코드는 무관.

**구현:**
- `db.py` — `offers` 테이블 신설(status 7종·`expires_at`·`message`) + `projects`에
  `pending_offer_count`·`top_offer_amount`·`top_offer_buyer_id`. **`bids` 테이블은 지우지 않았다**(이력 보존).
  `bid_count`/`bidder_count` 컬럼은 **"누적 제안 수/고유 제안자 수"로 의미만 재해석**해서 재사용한다 —
  컬럼명만 보고 입찰이라고 오해하지 말 것.
- `api.py` — `POST /projects/{id}/offers` · `…/accept` · `…/decline` · `…/withdraw`,
  `POST /projects/{id}/buy`, `GET /listings/live` 신설. 입찰 엔드포인트는 **410**으로 안내.
  `/auctions/live` · `/buy-now` · `resume-auction` · `auctions/release-all`은 **호환 별칭으로 살려뒀다.**
- 공개 dict에 `price`·`sale_status`·`listing_ends_at`·`offer_count`·`pending_offer_count`·`top_offer`·
  `offer_floor` 추가. 옛 키(`price_start`·`auction_status`·`auction_ends_at`·`bid_count`)도 같이 나간다.
- **제안이 있어도 판매가 수정 가능** — 입찰 시절의 `bids_exist` 잠금을 풀었다(제안은 가격이 아니라 매물에 붙는 것).
- 명의이전 차단 사유 `bids_exist` → `offers_pending`.
- 관리자 사용자 통계의 `bids.user_id`(존재하지 않는 컬럼) 오타 버그를 `offers.buyer_id`로 고쳤다.

**⚠️ 작업 중 실제로 낸 사고 — 같은 실수 반복 금지.** 입찰 엔드포인트를 "블록 단위로" 들어내는 패치가
그 사이에 있던 **`POST /projects/{id}/report`와 차단 3종(`/me/blocks`·block·unblock)까지 함께 삭제**했다.
스모크의 `Method Not Allowed`로 뒤늦게 잡았다. **범위를 인덱스로 잘라내는 패치는 자르기 전에 그 구간의
`@router` 목록을 먼저 뽑아 확인할 것.** 이후 `git show HEAD:` 와 라우트 목록을 대조해 누락 0건을 확인하는
절차를 넣었다.

**약관:** 제12조를 「판매가 · 가격 제안 · 성사」로 전면 개정(v2.3), **영문 약관에 없던 대응 조항을 신설**
(Article 12). 이게 토스 재심사의 근거 문서다. `refund.html`·`PLATFORM.md`·`TRUST.md`도 동기화.

**검증:** `_offer_suite_test.py` 신규 59개 + `_sale_deal_suite_test.py` 신규 24개 통과.
`_deal_flow_test` 47/47 · QA 21/21 · 차단 18/18 · 위탁 19/19 · 명의이전 17/17 · 단위 통과 ·
`_smoke_check` 전체 통과 · `_predeploy_gate` 20/20. 입찰 전제라 이식 불가한
`_auction_suite_test.py`·`_auction_advanced_test.py`는 **은퇴**시켰다(분쟁·해피패스·수수료 청구서 시나리오는
`_sale_deal_suite_test.py`로 옮김). `?v=` 63파일 428참조 → `20260902-offers`,
`sw.js` → `v91-offers`, `admin/sw.js` → `v7-offers`.

**후속 필요:**
- **라이브 매물 4건 가격 이관 미착수** — 즉시구매가가 있으면 그 값을, 없으면 시작가를 판매가로 옮기고
  판매자에게 알려야 한다. 지금은 시작가가 그대로 판매가로 읽힌다
- **가이드 9개·블로그 19편의 입찰/bid 문구 미수정**(이번 범위에서 의도적으로 제외).
  특히 `blog/failed-side-project-pricing.html`은 **「고정가보다 경매가 낫다」를 논증하는 글**이라
  find-replace가 아니라 다시 써야 한다
- **토스 재심사 재신청 미착수** — 구조는 바뀌었으니 PortOne 콘솔에서 다시 신청할 수 있다
- 라이브 스크린샷 검증 못 함(이 세션은 브라우저 접근 불가)

### 2026-09-02 · 🛑 토스페이먼츠 심사 거부 — 경매·입찰 구조가 사유 (코드 변경 없음 — 사실 기록)

**사용자 보고(2026-09-02):** 토스페이먼츠가 **경매·입찰 구조의 사이트에는 가맹 승인을 내주지 않는다**고
회신. 8/25에 제출한 결제경로 자료(`docs/toss-review/`)와 무관하게 **구조 자체로 거부**된 것.
아래 「의도적 미완」의 "심사 결과 대기 중 · 공이 토스 쪽에 있다"는 **이 날짜부로 틀린 정보**다.

**거부 사유 = 입찰 형식(가격 미확정).** 사용자가 2026-09-02에 재확인해 확정. "타인 재화 중개"가
사유가 아니므로, **경매를 고정가(+제안) 구조로 바꾸면 재심사 여지가 있다.** 다시 묻지 말 것.

**이게 뜻하는 것:**
- 2026-08-24 경쟁자 실측에서 「5개 차별점 중 유일하게 살아남은 것」이 **실시간 경매·입찰**이었다.
  그 유일한 차별점이 **국내 결제를 막는 바로 그 원인**이다. 경매와 국내 카드 결제는 양립하지 않는다.
- **현재 결제 상태:** 페이팔(해외 구매자)만 열려 있다 — 계약 완료 + KRW→USD 환산 수정(8/25) +
  결제창 렌더 확인. 토스(카드·계좌이체·가상계좌)는 거부. 카카오페이(별도 진행 중 1건)도 같은 사유로
  막힐 가능성이 크다 — 미확인. 즉 **한국 구매자가 국내 수단으로 결제하는 경로가 없다.**
  2026-08-11 「해외 먼저」 결정과는 방향이 일치한다.
- `payments.py`의 `portone_enabled()`는 여전히 `true`를 돌려준다(환경변수 존재만 검사). 카드 채널의
  `channelKey is not correct.`(8/25)는 심사 중이라서가 아니라 **승인이 안 나서**였을 가능성이 높다.

**선택지 (사용자 미결정 · 코드 반영 금지):**
1. 경매를 버리고 고정가 + 제안(offer) 구조로 재심사 — 차별점 상실. 사유가 입찰 형식으로 확정됐으므로 **유효한 경로**
2. 국내 카드 포기, 해외 전용(페이팔) 확정 — 코드 변경 최소, 경매 유지, 한국 구매자 사실상 배제
3. 플랫폼 밖 결제·수동 입금 — **`PLATFORM.md` §B 금지 경로.** 그 규칙은 "PG가 곧 온다"를 전제로
   만든 것이라 전제가 깨졌지만, 다시 여는 건 사용자 결정. 먼저 제안하지 않는다
4. 해외 에스크로(Escrow.com — IndieMaker가 쓰는 것) — 한국 사업자 가입 가능 여부 **미확인**

**하지 말 것:** 토스 승인을 기다리는 문구·작업 일체. 「심사 결과 대기」를 근거로 카드 결제 홍보 보류
상태를 유지하는 건 맞지만, 이제 "승인되면"이 아니라 "구조를 바꾸면"이 조건이다.

### 2026-08-25 · 스크롤월드가 매물 섹션을 덮던 버그

사용자 제보(스크린샷). 실제 크롬에서 재현: `scrollY 8260`, 월드 bottom **481** —
화면 아래 733px 에 매물이 깔려 있는데 fixed 레이어(`inset:0`)가 화면 전체를 덮고 있었다.

**⭐ 매물 카드는 멀쩡했다.** `.lot-card-thumb` 만 `position:absolute` 라 보였고
제목·가격·버튼(`static`)은 `.sw-sky` 에 가려진 것이다. **`.sw-sky` 는 `z-index:0` 이어도
positioned 라, 뒤따르는 static 콘텐츠보다 위에 그려진다.** 이걸 모르면 카드가 깨진 걸로 오진한다.

**걷어내는 처리는 이미 있었다.** `index.html` 의 `past()` 가 `.wa-world` 에 `is-past` 를
토글하고 `world.css` 가 레이어를 숨긴다. **문제는 기준이 `b <= 1`** — 세계가 화면 위로
완전히 사라진 뒤였다. 그전 **한 화면 높이(1vh) 동안** 계속 덮여 있었다.
없던 기능이 아니라 임계값이 틀렸던 것.

| 무엇 | 어떻게 |
|---|---|
| `--wa-world-out` | 월드 bottom / vh 를 1→0 으로. 트랙 끝 1vh(엔진이 "마지막 비행 완주용"으로 남긴 여유분)가 전환 구간 |
| 무대(영상) | `opacity: var(--wa-world-out)` — 전 구간 크로스페이드 |
| 카피·경로점 | `calc((var(--wa-world-out) - 0.7) / 0.3)` — **먼저** 뺀다. 안 그러면 매물 위에 잔상처럼 남는다 |
| 하늘 | 투명화 대신 **`z-index:-1`**. 색이 body 와 같은 `#1a1814` 라 배경은 그대로고, 투명하게 하면 `html` 의 밝은 기본색(`#F5EDE0`)이 비친다 |

⚠️ **처음에 엔진(`scrub-engine.js`)에 같은 토글을 새로 넣었다가 되돌렸다.**
기존 처리를 못 찾고 중복 구현한 것이고, 서로 다른 임계값의 메커니즘 두 개가
애초에 이 버그를 어렵게 만든 원인이다. **고치기 전에 이미 있는지부터 찾을 것.**

**⭐ 브라우저 두 개를 헷갈리지 말 것.** Browser pane(앱 내장)이 화면에 안 떠 있으면
**스크린샷도 스크롤도 안 된다**(`scrollTo` 가 무시됨 — 실측 확인). 이때는
**claude-in-chrome**(사용자의 진짜 크롬)으로 붙으면 전부 정상 동작한다.
이 세션에서 그걸 몰라서 「검증 불가」로 멈출 뻔했다.

검증: 전환 구간 6지점 계측(카피 out 0.7 에서 0 도달 · 하늘 z -1 · 카드 4장 정상) +
스크린샷 3장(깨진 상태 → 카드 복구 → 월드 03챕터 무회귀). smoke 통과.
`?v=` → `20260825-out3` · `sw.js` → `v90-worldout3`

### 2026-08-25 · 대비 결함 수정 — 전 사이트 실패 0 (팔레트 재설계 아님)

브라우저에서 텍스트 노드마다 전경/유효배경 명암비를 계산해 11개 페이지를 실측했다.
**결과가 놀랍도록 좁았다 — 전 페이지의 실패가 사실상 색 하나였다.**

| 대상 | 전 | 후 |
|---|---|---|
| `--muted-2` on `#262018` | 4.44 | **4.75** |
| `.skip-link` 흰글자 on 금색 | 2.38 | **7.46** |

- `--muted-2: #8f8576 → #948a7b` — 채널당 +5. 0.06 모자라서 떨어지던 것이라
  사람 눈에는 같은 색이다. ⚠️ **정의가 4곳에 흩어져 있었다**:
  `styles.css:22` · `yard-theme.css:16` · `yard-theme.css:811` · **`app/app.css:1513`**.
  최상위 CSS 만 grep 해서 마지막 걸 놓쳤고, `/app/` 만 계속 4.44 로 남아 있었다.
  **색 토큰을 고칠 땐 `grep -rn <값> . --include='*'` 로 전 확장자를 훑을 것**
- `.skip-link` 흰 글자 → `#1a1814`. 접근성 기능 자체가 대비 미달이었다
- `project.html:455` `:focus` → `:focus-visible` (마우스 클릭에도 링이 뜨던 것)
- `?v=` **62파일 124참조 + 8파일 8참조** 범프 · `sw.js` → `v86-contrast2`

**안 건드린 것:** `index.html:716` 의 `#8f8576` 는 스크롤월드 씬 accent 로 글자색이
아니라 버튼 배경이다. 그 위 글자가 `#1a1814` 라 4.88:1 로 통과한다.

**검증:** 배포 후 같은 감사를 라이브에 재실행 — 홈·매물·구매·판매·가이드×2·블로그·앱·
404·개인정보·쇼케이스 **11개 페이지 실패 0**. smoke 통과 · pre-deploy 20/20.

⚠️ **스크린샷은 못 찍었다** (브라우저 패널 미표시, 4회 시도) — `.focus()` 도 안 먹었다
(문서에 포커스가 안 잡히는 상태). 계산값으로 검증했고, **skip-link 검은 글자는 사용자가
직접 Tab 눌러 확인**해줬다.

### 2026-08-25 · 사이트 전체 접근성 결함 수정 (디자인은 안 건드림)

Vercel Web Interface Guidelines(103규칙)로 `public/` HTML 66개를 전수 검사했다.
`web-design-guidelines` 스킬을 설치해서 처음 돌린 회차다.

**⚠️ 1차 스캔 161건 → 실제 결함 99건.** 오탐이 62건이었다. 재는 방법이 결과를 바꿨다.

| 항목 | 1차(정규식) | 실측 후 | 왜 |
|---|---|---|---|
| 폼 라벨 없음 | 49 | **3** | `<label>`로 감싼 게 정상 마크업인데 `for=`만 찾았다 |
| 표 오버플로 | 18 | **0** | 375px에서 실측 — 10개 표 전부 안 넘침(최대 331/371px) |
| `outline:none` | 1 | **0** | `box-shadow` 링으로 대체돼 있었다 |
| th scope | 92 | **95** | 정규식이 놓친 게 오히려 3건 더 있었다 |

**고친 것:** `<th scope>` 95건(행 안 `td` 유무로 col/row 자동 배정) ·
`app/index.html` 키워드 입력 `for=` 연결 · `project.html` 공유 textarea `aria-labelledby` ·
`admin/install.html` `aria-label` · `promo/instagram.html` `theme-color`(66개 중 유일 누락) ·
`sw.js` → `v84-a11yscope`

**안 고친 것:** 표 래핑은 CSS 변경 → `?v=` 52파일 범프를 부르는데 실측상 넘치는 표가 0이라 보류.
`project.html:455`가 `:focus-visible` 아닌 `:focus`라 마우스 클릭에도 링이 뜨는 것(미수정).

**⛔ 디자인·색·레이아웃은 한 줄도 안 건드렸다** — 2026-08-16 「디자인 변경 종료」 결정 유지.
다크모드 대비·hover 같은 팔레트 영역은 결함이어도 손대지 않았다. 재개하려면 사용자가 먼저 꺼내야 한다.

**교훈:** 정규식 스캔 결과를 그대로 「결함」이라고 보고하면 안 된다.
`th scope`처럼 마크업만 보면 되는 건 파서로, `표 오버플로`처럼 렌더돼야 아는 건
**브라우저에서 실제로 재고** 판단할 것.

검증: `_smoke_check.py` 통과 · `_predeploy_gate.py` 20/20 · 라이브 10개 페이지 200 ·
재스캔 th 104개 중 누락 0.

### 2026-08-25 · 페이팔 결제가 통화 때문에 아예 안 되던 문제 + 위젯이 2초 만에 지워지던 문제

**배경:** 토스 심사용 결제경로 캡처를 만들다가 「카드로 결제하기」·「PayPal로 결제」를
**실제로 눌러봤더니 둘 다 실패**했다. 캡처만 하고 넘어갔으면 못 봤을 것이다.

| 수단 | PortOne 응답 | 판정 |
|---|---|---|
| 카드(토스 채널) | `RECORD_NOT_FOUND: channelKey is not correct.` | **미해결** — 아래 참조 |
| 페이팔 | `페이팔에서 지원하지 않는 화폐(CURRENCY_KRW)` | 이번에 수정 |

**원인 1 — 페이팔에 KRW를 보내고 있었다.** `payments.py`의 `build_paypal_payment_request`가
`currency: "CURRENCY_KRW"`로 하드코딩돼 있었다. 페이팔은 KRW를 받지 않는다.
`CLAUDE.md`에 「PayPal 실결제 한 번도 안 해봄」이라고 적혀 있던 게 여기서 드러났다.

**원인 2 — 고쳐서 위젯이 떴는데 2초 만에 사라졌다.** `project.html`의 4초 폴러가
`refresh()` → `renderProject()`로 결제 영역을 통째로 다시 그리면서 **페이지에 박히는**
PayPal SPB 위젯을 지웠다. 카드 결제는 팝업이라 이 문제가 없어서 여태 안 보였다.

**구현:**
- `payments.py` — `krw_to_paypal_charge()`가 KRW를 **USD 센트**로 환산(PortOne V2는 금액을
  통화의 최소 단위 정수로 받는다: KRW 1배, USD 100배). 센트 미만은 **올림** — 내림하면
  환산 손실이 판매자 정산분에서 나간다. 두 builder 모두 `(params, charge)` 튜플을 돌려준다
- ⚠️ **환율은 표시용과 분리했다.** `global_config._fx()`의 `WA_FX_USD`는 주석에 "Not for
  settlement"라고 명시돼 있다. 실제로 돈을 청구하는 값이라 **`WA_PAYPAL_FX_USD`**를 따로 뒀다
  (미설정 시 `WA_FX_USD` → 기본 1350 순으로 폴백). **Railway에 아직 등록 안 함**
- `db.py` — `pg_charge_amount` / `pg_charge_currency` / `pg_charge_fx` 컬럼 추가.
  **원장(sold_price·deal_amount)은 KRW 그대로**이고 이건 "실제로 PG에 청구한 값"이다.
  둘을 섞으면 검증이 깨진다
- `api.py` — `_expected_charge()`가 검증 기준을 원장이 아니라 청구 기록에서 읽는다
  (verify·webhook 양쪽). 컬럼이 비어 있는 구버전 행은 KRW로 폴백
- `payments.py` `assert_payment_paid()`에 **통화 검사 추가.** 금액 숫자만 보면
  「300,000원 청구 건에 300,000센트(=$3,000) 결제」가 통과한다 — 실제로 테스트로 잠갔다
- `project.html` — 결제 버튼 누르면 **USD 환산액과 적용 환율을 먼저 보여준다**
  (「해외 결제는 미국 달러로 청구됩니다 — 222.23 USD (적용 환율 1 USD = 1,350원)」).
  `paypalUiMounted` 플래그로 위젯이 떠 있는 동안 폴링 중단

**검증:** `_paypal_currency_test.py` 신규 18개 통과(환산·올림·통화 불일치 거부·하위호환).
`_smoke_check.py` · `_predeploy_gate.py` 10/10 · `_auction_suite_test.py` 43/43 ·
`_deal_flow_test.py` 46/46. **격리 DB로 띄운 로컬 서버에서 실제로 PayPal 결제창이 뜨는 것까지
확인했다** — `initialize-payment/v2`가 400 → 200으로 바뀌고 PayPal 버튼 SDK가 렌더됨.
캡처: `docs/toss-review/shots/06c_페이팔결제창.png`

**⚠️ 카드(토스) 채널은 여전히 안 된다.** `channelKey is not correct.`
토스 계약이 「심사중」이라 채널이 아직 활성이 아닌 것으로 **추정**하나 확인하지 못했다.
PortOne 콘솔에서 카드 채널 키가 실제로 발급·활성 상태인지 봐야 한다.
Railway에도 같은 값이 들어가 있으므로(2026-08-15 기록) **라이브도 같은 상태일 가능성이 높다.**

**후속 필요:**
- `WA_PAYPAL_FX_USD`를 Railway에 등록. 지금은 코드 기본값 1350으로 청구된다 —
  **환율이 고정값이라 시세와 벌어진다.** 실거래가 시작되기 전에 정할 것
  (고정 환율 + 마진, 또는 환율 API 연동)
- 페이팔 **실제 결제 완료**는 아직 안 해봤다. 결제창이 뜨는 것까지만 확인했다
- STC bypass 필드는 여전히 최소값

### 2026-08-24 · 유입경로가 전부 Direct로 나오던 문제 (집계 누락 + 재방문 덮어쓰기)

**배경:** 사용자가 "아직도 방문자 유입경로가 다이렉트로 나온다"고 지적. 전날 `d6f00da`로
유입 경로 기록을 넣었는데도 안 바뀐 상태였다. 원인이 두 개였다.

**원인 1 — 발견 채널 페이지가 애초에 집계에 없었다.** `footer-visitors.js`가 붙은 페이지가
`public/**` 63개 중 **9개**뿐이었다. 블로그 28개 전부, `/guide/*`, `/app/`이 전부 빠져 있었고,
`/api/v1/visit`를 호출하는 곳은 이 파일 하나다 — 즉 **블로그로 들어온 방문은 기록 자체가 없었다.**
GSC 실측(2026-08-21)상 발견형 질의 노출을 가져오는 건 영문 블로그 글인데, 집계에 잡히는 건
홈·매물·판매처럼 이름을 알고 들어오는 페이지뿐이었으니 구조적으로 Direct만 남는다.

**원인 2 — 재방문이 전부 direct로 덮였다.** `captureFirstTouch()`가 첫 방문에 리퍼러가 있어도
localStorage에 `"(direct)"`를 저장하고, 이후 모든 방문이 그 값을 `utm_source`로 보냈다.
서버(`record_visit`)는 특수문자를 턴 뒤(`"direct"`) **utm을 referrer보다 우선**하므로,
오늘 구글에서 들어와도 재방문이면 `direct`로 찍혔다. 서버가 만드는 정상 라벨은 대문자 `Direct`라
관리자 화면에 대소문자 두 행이 갈라져 보이는 게 이 버그의 표식이었다.

**수정:**
- `footer-visitors.js` — 방문 집계에는 **이번 방문 URL에 실제로 붙어 온 표식만** 싣는다
  (`readUtmSource()`). 표식이 없으면 서버가 referrer로 판정한다. 저장된 값은 **가입 귀속(first-touch)
  전용**으로 분리했고, 레거시 `"(direct)"`는 빈 값으로 읽는다(`LEGACY_DIRECT`)
- `api.py` `register()` — `signup_source`가 비면 `signup_referrer`로 채널을 판정한다.
  안 그러면 표식 없는 가입이 전부 빈 값으로 뭉친다
- 블로그 28개 + `/guide/index.html` + `/app/index.html` **30개 페이지에 스크립트 부착**.
  전부 **`data-render="off"`** — 집계만 하고 푸터에 숫자는 안 그린다(영문 페이지에 한글 라벨이
  붙거나 앱 UI가 바뀌는 걸 피함). `ensureEl()`이 이 속성을 보고 렌더를 건너뛴다
- `?v=` → `20260824-visits` (9개 파일), `sw.js` `CACHE` → `v80-visits`

**⚠️ 공개 방문자 수가 올라간다.** 집계 대상 페이지가 9개 → 39개가 되므로 푸터의
「방문자 전체」 숫자가 이전 추세와 불연속이 된다. 과거 수치와 직접 비교하지 말 것.

**집계 규칙(그대로 유지):** 유입 채널은 **한 방문자의 그날 첫 요청에만** 기록된다.
홈에 직접 들어왔다가 나중에 깃허브 링크를 타도 그날은 Direct로 남는다.

**검증:** `_visit_source_test.py` 신규 12개(리퍼러→채널 정규화 · 표식 우선 · 자기 사이트 리퍼러 =
Direct · 봇 제외 · 같은 방문자 중복 미집계 · 가입 귀속 4종) 통과. `_visit_source_front_test.js` 신규
12개 통과 — **`git show HEAD~1`의 옛 코드로 돌리면 B·D가 실패**하는 것까지 확인해서 회귀를 실제로
잡는 테스트임을 검증했다. `_smoke_check.py` 전체 통과 · `_predeploy_gate.py` 10/10 ·
`_auction_suite_test.py` 43/43. 로컬 브라우저로 블로그 글에서 `POST /api/v1/visit`가 나가고
카운터 DOM은 안 생기는 것, 홈은 카운터가 그대로 뜨는 것, `?utm_source=github`가 first-touch로
잡히는 것 확인.

**후속:** 아직 집계에 없는 페이지 — `/guide/` 나머지 8개, `get-app.html`, `diagnose.html`,
`legal/*` 8개, `404.html`, `promo/instagram.html`. 아웃리치 링크(깃허브 이슈·메일)에
`?utm_source=github` 같은 표식을 붙이는 건 **미착수** — 메일·카톡은 referrer가 안 넘어와서
표식 말고는 쪼갤 방법이 없다.

### 2026-08-25 · 🔓 디자인 동결 해제 (아래 2026-08-16 결정을 갱신)

사용자가 동결을 풀었다. 다만 **2026-08-16에 실패한 원인은 그대로 유효하다** —
화면을 못 보는 상태로 진행한 것. 그래서 조건이 붙는다.

- **측정 가능한 결함**(명암비·포커스·오버플로·스크린리더)은 스크린샷 없이도 고쳐도 된다.
  `getComputedStyle` 로 검증되고 판정이 객관적이다
- **취향 기반 변경**(색·폰트·레이아웃 바꾸기)은 **스크린샷이 찍히는지 먼저 확인**하고 시작한다.
  안 찍히면 사용자에게 패널을 띄워달라고 하고 멈춘다
- ⚠️ 2026-08-25 이 회차는 브라우저 패널이 안 떠 있어 **스크린샷 없이** 진행했다.
  계산값으로 검증했고, 눈으로 보이는 유일한 항목(skip-link)은 **사용자가 직접 Tab 눌러
  검은 글자를 확인**해줘서 닫혔다. 패널이 안 뜰 때 쓸 수 있는 방법이다 —
  **내가 못 보면 사용자에게 「무엇을 어떻게 눌러서 무엇이 보이면 정상인지」를 주고 확인받는다.**
  단 이건 항목이 1~2개일 때만 통한다. 취향 판단은 여전히 패널이 필요하다

### 2026-08-16 · ⛔ 디자인 변경 작업 종료 — 현 상태 유지 확정 (2026-08-25 해제됨 ↑)

**사용자 결정: "디자인 바꾸는 건 접고 지금 있는 상태 유지."** 아래 시안 작업은 여기서 끝난다.

- **라이브는 기존 yard 테마 그대로.** 확인: `body class="theme-yard"` · H1 "Give your stalled
  project a second life." · 히어로 사진 유지 · 시안 CSS/JS 참조 **0건**
- 시안 파일(`theme-mono.css` · `theme-taste.css` · `js/chapters.js`)은 **지우지 않고 남겨둔다.**
  `?theme=`으로만 켜지고 평소엔 요청조차 안 나가므로 라이브에 부담이 없다. 나중에 다시 볼 수 있다.
- **재개하지 말 것.** 사용자가 먼저 꺼내지 않는 한 디자인 변경을 제안하지 않는다.

**이 작업이 실패한 이유 (반복 금지):** Claude가 **결과 화면을 못 보는 상태로** 계속 만들었다.
브라우저 패널이 대부분 숨겨져 있어 스크린샷이 한 번밖에 안 잡혔고, 계측값(폰트 크기·패딩·색)만으로
판단했다. 그 결과 ①이미 yard가 `!important`로 덮고 있던 죽은 CSS를 "AI 티의 원인"으로 오진
②대안으로 만든 매물 스크린샷 타일 배경이 기각 ③taste 시안은 "색·폰트만 바뀌었다" ④강도를 올렸더니
"글자 크기만 바꿨다"는 지적. **디자인 작업은 화면을 볼 수 있을 때만 할 것.**

### 2026-08-16 · 디자인 시안 2종 (미리보기 전용 · 기본 테마 불변)

사용자가 "AI로 뽑아낸 티가 난다"며 디자인 변경을 요청. **기능은 그대로 두고 표면만**,
그리고 **실사이트에 적용하지 말고 미리보기로** 만들라는 지시에 따라 테마 시안으로 제작.

**스위처:** `public/js/theme-preview.js` — 공개 페이지 51개에 삽입.
`?theme=<이름>`으로 켜고 `?theme=off`로 끈다. `sessionStorage`라 페이지를 넘겨도 유지되고
탭을 닫으면 자동 해제된다(localStorage 아님 — 시안이 영구히 남는 사고 방지).
켜졌을 때만 해당 CSS·웹폰트를 주입하므로 **평소엔 요청조차 나가지 않는다.**

| 시안 | URL | 성격 |
|---|---|---|
| `theme-mono` | `/?theme=mono` | 모노스페이스·대문자·차가운 슬레이트. yard를 **끄고** 대체 |
| `theme-taste` | `/?theme=taste` | taste-skill 규칙 적용. yard를 **유지한 채 위에 얹음** |

**theme-taste 근거:** [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)의
`skills/redesign-skill/SKILL.md`. 스킬의 Fix Priority(폰트→팔레트→상태→레이아웃→컴포넌트→
빈상태→타이포)를 그대로 따랐다. 적용한 것: 제목 폰트 Outfit(한글은 Pretendard 유지),
강조색 1개로 통일(앰버 — 벽돌색 밑줄 제거), 섹션 패딩을 광학적 비대칭으로 크게(69/79px),
인접 섹션 배경 미세 단차, 3단 그리드 대칭 깨기(1.35fr 1fr 1fr), 카드 반경 2단 체계(14/8px),
hover/active/focus-visible 상태, 그레인 오버레이, `tabular-nums`, `text-wrap: balance`.

**⚠️ 기본 테마(`theme-yard`)는 한 줄도 안 바뀐다.** 검증으로 확인:
시안 OFF 상태에서 Inter·41.4px·weight 700·섹션패딩 34.5/29.6·시안 스타일시트 요청 0건.

**주의:** `theme-mono`는 사용자가 "색·폰트만 바뀌고 UI/UX는 똑같다"고 지적한 상태다.
원본(daoism.systems)의 실제 구조는 **스크롤 없는 챕터 전환**(`body{overflow:hidden}` +
`main{position:fixed}` + `.section` 8개가 `absolute; top:0`로 겹쳐 하나만 `.active`)인데,
그 구조는 크롤러가 첫 챕터만 읽어서 오늘 한 SEO 작업을 무효화한다. 채택 시 홈 한정 +
정적 폴백을 함께 넣을 것.

### 2026-08-16 · 히어로 배경을 실매물 스크린샷으로 교체 + 네비/CTA 정렬 버그

**배경:** 사용자가 "AI로 뽑아낸 티가 난다"고 지적 → 브라우저로 실제 화면을 보고 원인 3개 확인.

**1) 히어로 배경 — 매물 스크린샷 타일을 시도했다가 사진으로 복귀 (❌ 폐기).**
Claude가 기존 사진(`/assets/photo/hero-archive-window.jpg`, 종이 서류 상자)을 AI 생성 티의
주원인으로 지목하고 실매물 스크린샷 3×3 격자 배경(`hero-shots.js`)으로 교체했으나,
**사용자가 결과물을 보고 "너무 구리다"고 판단해 사진으로 되돌렸다.**
`hero-shots.js` 삭제, 관련 CSS·`motion.js` 예외처리 전부 원복. 사진 그대로 유지.

**⚠️ 재시도 금지 사항:** 매물 스크린샷을 히어로 배경 타일로 까는 방식은 이미 시도했고 기각됐다.
다시 제안하지 말 것. 히어로 배경을 바꾸려면 **다른 사진**을 쓴다
(`public/assets/photo/`에 `band-archive-open.jpg`, `still-archive-sill.jpg`도 있음).

**2) Product Hunt 배지 잘림.** 배지가 250px인데 네비가 좁아지면 화면 밖으로 밀렸다
(뷰포트 976px에서 배지 오른쪽 끝 **1049px** — 73px 잘림). 숨김 브레이크포인트를
**720px → 1180px**로 올려 잘린 채 보이는 구간을 없앰.

**3) 히어로 CTA 3번째 버튼 정렬.** `.hero-cta`가 `justify-content: center`라 이벤트 버튼이
켜져 3개가 되면 마지막 하나가 다음 줄 **가운데에 혼자** 떴다 → `flex-start`로 변경
(히어로 카피가 좌측 정렬이므로 버튼도 좌측 기준).

**검증:** CTA 3개가 좌측 정렬로 흐르는 것, PH 배지가 더 이상 오버플로 목록에 없는 것 계측 확인.
사진 복귀 후 재확인 — 사진 로드(1280×720)·마우스 패럴랙스 복원·`heroShots` 잔재 0.
smoke 통과 · predeploy 10/10. `?v=` 52곳 → `20260816-photoback`, `sw.js` → `v73-photoback`.

**심전도(ECG) 애니메이션은 유지한다.** Claude가 한때 제거 후보로 올렸으나 **오판이었다** —
`hero-ecg.js`는 한 주기의 75%가 평평한 직선이고 P·Q·R·S 좌표로 실제 lead-II 파형을 그리며,
`prefers-reduced-motion`을 존중하고, **`listings.js:658`에서 새 입찰이 들어올 때 `spike(1)`이
호출된다** — 즉 장식이 아니라 실시간 상태를 전달하는 모션이다. 사용자가 의도해서 넣은 것이기도 하다.
**다시 제거 대상으로 올리지 말 것.**

**남은 것 (수치 근거 있음):** ①`home-hub`와 `listings`가 연속 3단 카드 그리드
②섹션 패딩이 44/36·44/38로 사실상 같아 리듬 없음 ③카드 라운드 6px·12px 혼재
④카드 배경 대비 거의 없음(`#2c241c` vs `#262018`).

### 2026-08-16 · `styles.css`의 죽은 "AI 티" 스타일 제거 (외형 변화 없음)

**배경:** 사용자가 "사이트가 AI로 뽑아낸 티가 난다"고 지적. `styles.css`를 뒤지니 실제로
전형적인 패턴이 다 있었다 — 히어로 제목 두 줄에 무한 shimmer 그라디언트 + **자홍색 드롭섀도**
(`#e879f9`), 제목 주변 반짝이 점 2개, `.live-card`의 6겹 네온 그림자(자홍 `217,70,239` +
보라 `109,40,217`)가 4.5초 주기로 맥동 + 그라디언트 테두리, `.live-metrics`의 4겹 초록 네온
1.6초 맥동, 로고의 `0 0 40px` 골드 글로우.

**⚠️ 그런데 이것들은 화면에 안 나오고 있었다.** `index.html`이 `<body class="theme-yard">`이고
`yard-theme.css`가 `styles.css` **뒤에** 로드되면서 `!important`로 전부 무력화하고 있었다
(yard-theme에 `/* Glass cards — deep brown field, no violet hover rim */` 주석까지 있다 —
과거에 같은 진단을 하고 덮어놓은 흔적). **즉 이번 커밋은 죽은 코드 정리이고, 외형은 안 바뀐다.**
`theme-yard` 클래스가 빠지는 순간 되살아나는 지뢰였으므로 제거 자체는 유지한다.

**같이 한 것:** 히어로 `line-height` 1.1→1.06 + `text-wrap: balance`(수상작 공통 처리),
`.live-metrics strong`에 `font-variant-numeric: tabular-nums`(숫자 갱신 시 폭 흔들림 방지).
`styles.css`를 고쳤으므로 `?v=`를 **52곳 전부** `20260816-deadai`로 범프, `sw.js` → `v70-deadai`.

**교훈 (일반화):** 이 저장소는 `styles.css` → `ux9.css` → `yard-theme.css` 순으로 로드되고
**yard-theme이 `!important`로 광범위하게 덮는다.** 외형 문제를 고칠 때 `styles.css`만 보고
판단하면 안 된다 — **`getComputedStyle`로 실제 렌더값을 확인**하고, 어느 파일이 이기는지부터 볼 것.

**후속 (실제 외형 작업):** 렌더링되는 건 yard 테마다. 실측한 문제는 ①`home-hub`와 `listings`가
**연속으로 3단 카드 그리드**(가장 전형적인 AI 레이아웃) ②섹션 패딩이 44/36, 44/38로 사실상 같아
리듬이 없음 ③카드 라운드가 6px·12px 혼재 ④카드 배경 대비 거의 없음(`#2c241c` vs `#262018`).
→ `yard-theme.css` 대상 별도 작업.

### 2026-08-16 · `data-i18n-html` 누락으로 내부 링크가 삭제되던 버그 수정

**배경:** 바로 아래 EN 폴백 작업 중 발견. `buy.html`의 `buy.form_note`가 `<a>`를 품고 있는데
`data-i18n-html`이 없어서, `i18n.js`의 `apply()`가 `textContent`로 덮는 순간 **링크가 통째로
사라지고 사전값에 박혀 있던 raw URL(`/guide/contact.html`)이 글자로 노출**되고 있었다.
KO·EN 양쪽 모두. 처음엔 "사전 수정 = `?v=` 범프 동반"이라는 이유로 보류했는데,
**그건 버그를 남길 이유가 안 된다**는 지적을 받고 같은 날 수정.

**전수 점검부터:** 여는 태그의 짝을 깊이 계산으로 찾아 `data-i18n`인데 `data-i18n-html`이 없고
내부에 태그가 있는 요소를 사이트 전체에서 스캔 → **`buy.form_note` 1건뿐**임을 확인(수정 후 0건).

**조치:** `buy.html`에 `data-i18n-html` 부착 + `i18n-messages.js`의 ko/en 값에 앵커 포함
(`<a class="text-link" href="/guide/contact.html">문의 안내 / Contact guide</a>`).
사전을 고쳤으므로 **`i18n-messages.js`의 `?v=`를 21개 참조 파일 전부** `20260816-i18nhtmlfix`로 범프
(문서에 기록된 함정 — 하나라도 빠지면 신규/수정 값이 조용히 무시된다). `sw.js` `CACHE` → `v69-i18nhtmlfix`.

**검증:** 브라우저로 KO·EN 양쪽에서 `<a>`가 살아있고 href가 정상이며 raw URL 노출이 없는 것 확인.
`_smoke_check.py` 통과. `sed` 일괄 치환 후 한글 무결성·diff 규모(23파일 25줄, 의도한 줄만) 확인.

### 2026-08-16 · 정적 폴백 KO→EN (봇에 한글 H1 노출 수정)

**배경:** Awwwards 레퍼런스 후보들과 우리 홈을 Googlebot UA로 나란히 받아 비교하다 발견.
`<html lang="en">`에 meta description도 영문인데, **JS 없이 받는 본문의 H1·H2가 전부 한글**이었다.
`data-i18n` 요소의 정적 폴백 텍스트가 한글로 박혀 있었기 때문 — JS가 돌면 i18n.js가 로케일에 맞게
덮어쓰므로 사람 눈에는 정상이었고, **크롤러에게만 한영이 섞여 보이던 상태**다. 글로벌 EN 우선
전략(`docs/GLOBAL.md`)과 정면으로 어긋났다.

**규모:** `public/**` 15개 파일에 한글 폴백 443개.

**조치:**
- 텍스트만 있는 요소 **406건** + `data-i18n-html`(내부 태그 있는 것) **43건** = **449건**을
  `i18n-messages.js`의 `en` 값으로 치환. 사전을 수정하지 않았으므로 `?v=` 캐시버전 범프 불필요
- 치환 안전장치: 현재 텍스트에 한글이 있고 + 키가 EN 사전에 있고 + EN 값에 한글이 없을 때만.
  HTML 문구가 사전보다 구버전인 35건("마켓" vs "마켓플레이스" 등)은 사전값으로 정정
- `buy.form_note`은 `<a>`를 품고 있는데 `data-i18n-html`이 없어(런타임에 textContent로 덮여
  링크가 사라짐) 정적 폴백만 EN으로 맞춤 — **근본 수정은 미착수**(아래 후속)
- **모바일 드로어 링크 3개**(판매 가이드·구매 가이드·블로그)는 `data-i18n` 자체가 없어 EN 모드에서도
  한글로 남아 있었음 → 기존 키(`guide.tabs.sell`·`guide.tabs.buy`·`nav.blog`)에 바인딩.
  「의도적 미완」의 "모바일 드로어 EN 잔여" 중 이 부분 해소
- `_smoke_check.py`의 `pretty 404`가 **한글 "페이지" 포함 여부로 검사**하고 있어 실패 →
  기본 로케일이 EN이므로 `"Page not found"` 검사로 교체
- `public/sw.js` `CACHE` → `v68-enfallback`

**검증:** 로컬에서 `?lang=ko`는 여전히 한글 H1(`멈춰버린 프로젝트에…`)·드로어 한글,
`?lang=en`은 영문 H1(`Give your stalled project a second life.`)·드로어 전부 영문·본문 한글 0자 확인.
Googlebot UA로 `/`·`/sell.html`·`/buy.html`·`/project.html?id=11` 받아 H1이 전부 영문으로 나오는 것 확인.
태그 균형 검사 통과 · `_smoke_check.py` 전체 통과 · `_predeploy_gate.py` 10/10.

**남은 것:**
- `public/app/index.html` 2건, `legal/*.html` 3건은 **의도적으로 제외** — 앱은 로그인 뒤라 SEO 무관,
  legal은 `.en.html` 짝이 따로 있는 구조
- 봇 본문에 한글이 완전히 0이 되지는 않는다 — 사업자정보(`.wa-kr-only`, 법적 필수)가 DOM에 남는다
- ~~`buy.form_note` 근본 수정~~ — **같은 날 해결**(아래 항목). 캐시 범프가 번거롭다는 이유로 버그를
  남기려 한 판단을 사용자가 지적해서 바로잡았다. **버그는 발견 시점에 고친다.**
- 홈 본문량 자체가 얇다(봇 기준 2,176자). Awwwards 비교군은 7,000~16,000자 —
  `docs/marketing/../design/awwwards_reference.md` 참고

### 2026-08-16 · 관리자 매물 명의 이전 (위탁 등록 인계)

**배경:** 위탁 등록 매물 `#8`을 원 소유자가 가입하면 그 계정으로 넘겨주기로 약속해뒀는데
(위 「위탁 등록 매물」), 확인해보니 **`owner_id`는 생성 시점에만 정해지고 이후 바꾸는 경로가
코드에 아예 없었다** — `db.py`의 `owner_id` 참조가 스키마·인덱스 빼고 전부 읽기뿐이었고,
관리자 라우트에도 판매자를 교체하는 게 없었다. 즉 약속을 지킬 수단이 없는 상태였다.

**구현:** `POST /api/v1/admin/projects/{id}/transfer-owner` (관리자 전용).
대상 계정은 `new_owner_email` 또는 `new_owner_id`로 지정한다.
- `database.project_transfer_blockers()` — 이전을 막는 사유를 코드 리스트로 반환.
  **입찰(`bids_exist`) · 판매완료(`already_sold`) · 딜 진행(`deal_in_progress`) ·
  수수료 청구서(`fee_invoice_exists`) · 헬프티켓(`help_tickets_exist`)** 중 하나라도 있으면 거부.
  "판매자가 누구인가"에 묶인 이력을 매물만 옮겨서 조용히 바꿔버리는 걸 막기 위함 —
  마이그레이션을 시도하지 않고 **거부**하는 쪽을 택했다.
- `database.transfer_project_owner()` — 이전 + 양쪽 계정에 인앱 알림(`notify`).
  매물 메시지(`messages`)는 발신자별 행이라 그대로 둔다.
- 정지 계정으로는 이전 불가. 관리자 화면(`public/admin/index.html`) 매물 상세 패널 하단에
  이메일·메모 입력 + 「명의 이전」 버튼 추가(확인창 1회). `public/admin/sw.js` `CACHE`를
  `wakeagain-admin-v5-xferowner`로 범프.

**검증:** `_transfer_owner_test.py` 신규 17개 시나리오 전부 통과(임시 DATA_DIR로 라이브 DB 격리).
`_smoke_check.py` 통과 · `_auction_suite_test.py` 43/43 통과.
브라우저로 관리자 화면 실제 구동해서 **이전 성공(판매자 표시가 새 계정으로 바뀌는 것)**,
미입력 시 클라이언트 검증, 미가입 이메일 지정 시 서버 메시지 노출까지 확인.

### 2026-08-15 · 매물 등록 필수 필드 (저장소 · 라이브 데모 · 마지막 활동일) (`b8d33ab`)

정책 상세는 아래 「매물 등록 필수 필드 정책」 섹션. 배포 후 실측:

- `/health` ok · `sw.js` `CACHE = wakeagain-shell-v60-reqfields` 반영 확인
- `/api/v1/projects/{id}`에 `repo_url`·`is_private_repo`·`live_url`·`is_offline`·`last_activity_at` 노출 확인
  (운영 DB 마이그레이션 정상 — 배포 직후 1회는 구버전 응답이었고 그 다음부터 반영)
- **운영 라이브 매물 4건 전부 정책 이전**이라 전원 "미등록" 배지 상태:
  `#11 RoadLog` · `#10 리치킷` · `#9 Trace` · `#8 온수냠냠냠`
  → 매물은 내려가지 않음. **판매자 4명에게 저장소·활동일 보완 요청 필요 (미완료)**
- 라이브 보드 카드(`/auctions/live`)는 이 필드를 안 실어보낸다 — 배지는 **매물 상세 페이지에만** 있음.
  카드에도 노출할지는 미정

### 2026-08-11 · select 다크모드 팝업 버그 + SW 캐시버전 규칙 + data-i18n-html 페어링 버그 (`ac0a802`…`2d65b88`)

**배경:** 사용자가 국가 선택 화면 스크린샷을 보내서 "국가 선택 화면 이상하게 나와" — 밝은 배경에 흐린 글씨로 거의 안 보이는 네이티브 `<select>` 드롭다운 버그. 고치는 과정에서 배포해도 반영이 안 되는 걸 보고 서비스워커 캐시 문제를 발견 → 고치고 나니 이번엔 반대로 "한글로 바꿨는데 영어로 보이는 부분이 있어"라는 리포트를 받아 `data-i18n-html` 속성 오용 버그를 발견.

| 커밋 | 내용 |
|------|------|
| `ac0a802` | `styles.css`의 `:root`에 `color-scheme: dark` 선언 — 이걸로 될 줄 알았으나 `getComputedStyle`로 확인해보니 값은 제대로 적용되는데도 팝업이 여전히 안 보임 |
| `98772bc` | **실제 수정**: `select, select option { background: var(--bg-elev); color: var(--text); }` 명시 규칙 추가. `color-scheme: dark`만으론 이 환경에서 네이티브 select 팝업 대비가 안 고쳐짐 — 옵션에 직접 배경·글자색을 줘야 함 |
| `cd569e8` | **`public/sw.js`의 `CACHE` 상수 버전 범프** — 위 CSS 수정을 배포했는데도 라이브에서 계속 예전 화면이 보여서 원인 추적한 결과, 서비스워커가 `sw.js` 파일 자체의 바이트가 안 바뀌면 "업데이트 없음"으로 판단하고 예전 캐시를 계속 서빙하는 걸 발견. 서버 응답(`curl`)·`Cache-Control` 헤더는 전부 정상이었음 — **PWA 서비스워커가 원인일 때는 서버 쪽 확인만으론 못 잡는다**는 걸 실측으로 확인. 이후 "배포 전 최소 확인"에 상시 체크리스트 항목으로 등재(아래 참고) |
| `077e64c` | **`data-i18n-html` 속성 오용 버그(61개 요소)**: `i18n.js`의 `apply()`를 다시 읽어보니 `data-i18n-html`은 `data-i18n="key"`와 **반드시 짝을 이루는 boolean modifier**(`hasAttribute()`로만 읽음)인데, 이번 세션에 새로 만든 가이드 페이지 9개 전부에서 `data-i18n-html="key"`처럼 **값 자체에 키를 넣는 잘못된 패턴**으로 작성했었음 → 셀렉터가 `[data-i18n]`이라 이 요소들은 언어 설정과 무관하게 항상 원본 영어 텍스트만 보임(한글 모드에서도 영어). sed로 `data-i18n-html="X"` → `data-i18n="X" data-i18n-html` 일괄 치환 |
| `11f0415` | 위 일괄치환 후에도 남아있던 2개(`guide.dispute.ht_2`, `role_dont_v`) — 번역값엔 `<strong>` 태그가 있는데 `data-i18n-html` modifier 자체가 아예 안 붙어 있어서 태그가 문자 그대로 노출되던 것 수정 |
| `92cb14b` | **사업자정보 자체가 번역 바인딩이 아예 없던 버그**: `guide/contact.html` 표에서 라벨(회사명/대표자/주소)은 `data-i18n`이 붙어 있었는데 **값 칸**(CoreLabs/Hyeonsu Ho/로마자 주소)은 정적 하드코딩이라 한국어로 바꿔도 로마자 표기 그대로 나왔음 → 원본 한글 값으로 신규 키 추가해서 바인딩 |
| `2d65b88` | `92cb14b`이 `i18n-messages.js` 캐시버전을 `i18n5`로 올렸는데 `contact.html` 자기 자신만 그 버전을 참조하게 고치고 나머지 19개 참조 파일은 워킹트리에 미커밋 상태로 남아있던 걸 뒤늦게 발견 → 전부 커밋 (`project.html`은 세션 시작 전부터 있던 별개 미커밋 작업과 섞여 있어 의도적으로 계속 제외) |

**교훈 (일반화):** ①네이티브 폼 컨트롤 다크모드는 `color-scheme` 선언만으로 안 끝날 수 있다 — 실제 렌더링을 봐야 함. ②PWA가 있는 사이트는 정적 자산을 고칠 때마다 `sw.js`의 `CACHE` 문자열도 반드시 같이 올려야 한다(서버 확인만으론 이 문제를 못 잡음). ③`data-i18n-html`은 `data-i18n`의 modifier이지 독립 키 홀더가 아니다 — 새 페이지 작성 시 반드시 짝으로 쓸 것.

### 2026-08-11 · 구글 로그인 라이브 + 해외 홍보(레딧·X) 1차 실행 (코드 커밋 없음 — 설정·운영 작업)

**구글 OAuth 로그인:** `wakeagain/oauth.py`에 Google/GitHub/Kakao OAuth 구현 자체는 이미 다 있었음(env var 존재 여부로만 켜지는 구조) — 이번 세션은 **새 코드가 아니라 순수 설정 작업**이었음.
- Google Cloud Console에서 OAuth 동의화면(외부·지원이메일) + OAuth 클라이언트 ID(웹 앱, 승인된 자바스크립트 원본 `https://wakeagain.com`, 승인된 리디렉션 URI `https://wakeagain.com/api/v1/auth/oauth/google/callback`) 발급
- Railway `wakeagain` 서비스에 `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`OAUTH_PUBLIC_BASE=https://wakeagain.com` 등록 → Deploy 버튼 눌러 반영
- 라이브에서 실제로 "Continue with Google" 버튼 노출 확인 + 구글 동의화면까지 정상 도달하는 것 브라우저로 직접 검증함(자격정보 입력·동의 클릭 자체는 안전규칙상 사용자가 직접 진행)
- **Client Secret은 Railway에만 존재 — 다시 화면에 안 뜸(구글 콘솔도 마스킹).** 분실 시 재발급 필요
- Google Cloud Console 접근 시 IAM 권한 문제로 두 번 막혔음(기본 브라우저 계정 → `hhs12619@gmail.com`으로 전환 후 해결) — 프로젝트 소유 계정 헷갈리지 말 것

**레딧/X 해외 홍보 1차 실행:** 사용자가 제공한 홍보 전략(r/SideProject·r/indiehackers·r/SaaS + X `#buildinpublic`)을 실행.
- r/SideProject 1차 시도: `wakeagain.com` 링크 포함 게시 → **Reddit 스팸 필터에 의해 자동 삭제됨**("Sorry, this post was removed by Reddit's filters", 낮은 계정 활동+외부링크가 원인으로 추정)
- r/SideProject 2차 시도: 링크 없이 "구글에 WakeAgain 검색하면 바로 나온다"는 문구로 재작성해서 게시 — **최종 생존 여부는 세션 종료 시점까지 미확인**(사용자가 직접 게시 버튼 누름, "아니 내가 게시했어")
- X(Twitter) 포스트: 사용자 제공 템플릿 기반, PayPal 관련 문구는 **의도적으로 제외**(PG 계약 미승인 상태라 "PayPal 연동됨"을 광고하면 안 된다고 판단 — 사용자도 동의) — 사용자가 직접 게시 완료
- r/indiehackers, r/SaaS, Hacker News(Show HN)는 **이번 세션에 미착수** — 전략만 확정, 실제 초안·게시는 다음 세션 과제
- 게시 판단 기준: URL 직접 링크는 스팸필터에 걸리므로, 앞으로도 첫 문단에 링크를 넣지 말고 "검색하면 나온다" 유도 문구 권장(구글에 WakeAgain 검색 시 자사 사이트가 최상단인 것 확인됨)

### 2026-08-11 · 블로그 전체 영문판 신규 (`ce028cb`, `5503944`)

**배경:** `/blog/*` 목록·글 7개도 i18n 자체가 아예 없어서 100% 한글이었음(가이드 페이지와 별개 템플릿). 해외 SEO 유입 자체가 안 되고 있었던 부분 — 사용자가 "영문으로 고치면 해외 검색 유입도 되냐" 질문.

- `blog/index.html` + 글 7개 전부 `terms.html`↔`terms.en.html`과 동일한 양방향 리다이렉트 패턴으로 `index.en.html` + `*.en.html` 8개 신규
- 직역이 아니라 영어권이 실제로 검색할 표현("sell abandoned side project", "sell MVP")으로 키워드 재구성
- 각 `.en.html`은 자기 자신을 가리키는 `canonical` + 독립된 OG/schema.org 메타 보유 (구글이 중복 콘텐츠로 묶지 않도록)
- `sitemap.xml`에 신규 8개 + **기존에도 빠져 있던** `terms.en.html`/`privacy.en.html`/`business.en.html`/`delete-account.en.html`까지 같이 추가 (원래도 사이트맵에 없었음, 이번에 정리)
- `hreflang`은 이번엔 미적용 — 규모 커지면 다음에 붙이는 걸 권장(사용자에게 안내함)

### 2026-08-11 · 가이드·계정삭제 페이지 전체 영문화 (`0c2339f`)

**배경:** 사용자가 스크린샷으로 직접 확인 — `/guide/*` 9개 페이지(판매·구매·이용안내·신용점수·데모·문의·분쟁·자료실 가이드)와 `legal/delete-account.html`이 EN/KO 전환 버튼은 있는데 **본문이 data-i18n 태그 자체가 없어서 언어 설정과 무관하게 100% 한글**로 나오고 있었음 (위 `70eddaa`가 고친 건 API가 내려주는 동적 텍스트였고, 이 정적 페이지 본문은 손대지 않았던 영역).

- `guide/*.html` 9개 파일 본문 전체에 `data-i18n`/`data-i18n-html` 부착 + `i18n-messages.js`에 `guide.*` 네임스페이스로 신규 키 약 270개(ko+en 쌍) 추가
- `credit.html`의 인라인 스크립트(`/api/v1/credit-policy` 호출 후 표 렌더링)도 `guide/status.html`과 동일한 `isEn()` 분기로 이중언어 처리
- `legal/delete-account.html`은 i18n 스크립트 자체가 없었고 terms/privacy/business처럼 `.en.html` 짝도 없었음 → `legal/delete-account.en.html` 신규 생성, 동일한 양방향 리다이렉트 패턴 적용
- **로컬 테스트 중 실제로 걸린 함정:** `i18n-messages.js`에 키를 270개 추가하고도 파일 자체의 캐시버스팅 버전(`?v=20260811-i18n3`)을 안 올렸더니, 브라우저가 예전 캐시를 물고 있어서 신규 키가 전부 "찾지 못함" 상태였음. 본문 텍스트는 `apply()`의 "키 없으면 원래 HTML 유지" 폴백 덕분에 겉보기엔 정상으로 보였지만, `<title data-i18n>`은 그 폴백이 없어서 탭 제목에 `guide.sell.doctitle` 같은 raw 키가 그대로 노출됨 — 이걸 보고 캐시 문제라는 걸 알아챔. **교훈: `i18n-messages.js`에 새 키를 추가할 때마다 파일 자체의 `?v=` 쿼리도 같이 올릴 것** (내용은 같아도 캐시가 안 갱신되면 신규 키가 조용히 무시됨).
- `public/project.html`은 세션 시작 전부터 커밋 안 된 별개 작업(퀵비드 폼 위치 이동 등)이 있어서, 그 파일의 버전범프 한 줄만 워킹트리에 남기고 이번 커밋에서 의도적으로 제외함 — 다음에 그 파일 커밋할 때 같이 딸려갈 것.

### 2026-08-11 · EN 접속 시 한글 노출 제거 (`70eddaa`)

**배경:** 해외 홍보 전, EN으로 접속했을 때 한글이 보이는 곳이 전부 없어야 한다는 사용자 요구로 전수 점검·수정.

- 매물 상태 픽커(써 볼 수 있는 제품 등 blurb·criteria·when·demo_expect)가 `pricing.py`에서 항상 한글로만 내려오던 것 → `_en` 필드 추가, `sell` 폼·`/guide/status.html` 둘 다 EN일 때 사용하도록 수정
- 라이브 입찰 티커의 신용등급·바이어랭크 배지("최고", "파워 바이어" 등)가 언어 무관하게 늘 한글 → `listings.js`에 번역 매핑 추가
- 회원가입·입찰·구매·차단·신고·재등록·메시지 등에서 나오는 백엔드 검증/안내 메시지(영문 버전 자체가 없던 것) 약 90개를 `public/js/api.js`의 `translateBackendText()` 딕셔너리로 커버 — `parseErrorDetail`에 붙어 있어 에러 토스트는 사이트 전역에서 자동 적용됨. 숫자가 끼는 동적 메시지(최소 입찰가 등) 몇 개는 정규식으로 처리
- `price_policy.validate_start_price()`는 `Accept-Language` 헤더 기반으로 서버에서 직접 이중언어 메시지 생성하도록 변경(숫자 포함이라 프론트 딕셔너리로 못 잡던 것)
- **남은 것:** `db.py`/`api.py` 한글 리터럴 자체는 안 지웠음(프론트 딕셔너리로 가로챈 것) — 새 메시지 추가/문구 수정 시 딕셔너리도 같이 고쳐야 함. `database.notify()` 인앱 알림 문구는 여전히 한글 고정. `/admin/*`은 의도적으로 한글 유지. 자세한 내용은 아래 "의도적 미완" 참고.

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
- ~~`FEE_RATE_CROSSBORDER = 0.19`는 페이팔 원가 기반 임시값~~ — **2026-08-13 폐기**: 판매자 수수료 국내·해외 공통 10%로 재확정(`FEE_RATE_CROSSBORDER`도 0.10). 페이팔 자체의 국경간/환전 수수료는 WakeAgain 몫이 아니라 구매자·페이팔 사이 별개 — PH 런칭 페이지·영문 약관과도 이제 일치함
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

## 방문자 카운터 · 유입경로 (푸터 + 관리자)

- 형식: `방문자 오늘 N · 전체 M` (i18n 한/영)
- 규칙: 전체=브라우저 1회(`wa_vid`), 오늘=KST 1일 1회, 봇 UA 제외, `?notrack=1`로 본인 제외
- **유입 채널은 그날 첫 요청에만 기록된다.** 같은 방문자의 그날 이후 이동은 집계 안 함
- 판정 순서: 이번 방문 URL의 `?utm_source=`(또는 `?src=`) → 없으면 `document.referrer`를
  서버가 호스트별 채널로 정규화(`_normalize_referrer`, api.py). 자기 사이트·빈 리퍼러 = `Direct`
- **저장된 first-touch 값은 집계에 쓰지 않는다** — 쓰면 재방문이 전부 그 값으로 덮인다
  (2026-08-23~24 실제 사고, 위 배포 이력 참조). 저장값은 가입 귀속(`signup_source`) 전용
- 스크립트 부착 시 **`data-render="off"`를 붙이면 집계만 하고 푸터에 숫자를 안 그린다.**
  블로그·가이드·앱이 이 모드다. 새 페이지에 붙일 때 기본값으로 쓸 것
- DB: `site_counters`, `site_daily`, `site_visitor_seen`, `site_daily_sources`
- API: `POST/GET /api/v1/visit`, `GET /api/v1/stats`, `GET /api/v1/admin/visit-sources`
- 관리자 화면: `/admin/` → 「유입경로」 탭
- FE: `public/js/footer-visitors.js` · 테스트: `_visit_source_test.py`, `_visit_source_front_test.js`

## 경쟁자 실측 (2026-08-24) — 「우리만 한다」를 쓰기 전에 반드시 읽을 것

이 저장소에 경쟁자 기록이 2026-08-13(AcquireBase·Borderline·Flippa)에서 멈춰 있었다.
2026-08-24에 **고객이 실제로 치는 검색어**로 다시 찾고 **각 사이트를 직접 열어** 확인한 결과,
그때 놓친 경쟁자가 무더기로 나왔다. 아래가 실측값이다.

### 해외 — ⚠️ IndieMaker (indiemaker.com, 구 1Kprojects)가 가장 위험하다

| 항목 | IndieMaker | WakeAgain |
|---|---|---|
| 매물 | **1,957건** (최신 5일 전) | **4건** |
| 판매자 수수료 | **3%**(pre-revenue) / 6.5%(수익 있음) | **10%** (최소 5,000원) |
| 등록비·메시지 과금 | 0 | 0 |
| 구매자 | 3.8% + 매물당 $25 언락 (또는 Premium $24/월) | 0원 |
| 자금 처리 | **Escrow.com 100% 에스크로** | PortOne — 페이팔만 (토스 **거부**, 2026-09-02) |
| pre-revenue | **전용 필터 있음.** "vibe-coded 프로젝트 환영" | 허용 |
| 경매·입찰 | **없음 (고정가)** | 있음 |

2019년 1kProjects 인수(당시 사용자 800명) → 2020-03 IndieMaker로 리브랜딩. 영어 전용·USD.
푸터에 법인 정보 없음(연락처는 hello@indiemaker.com).

그 외 가동 중: **Microns**(microns.io, 매물 15~16 노출, $1,300~$200,000, 고정가) ·
**SideProjectors**(SPA라 매물 수·수수료 크롤 불가, 별도 확인 필요) · Acquire.com · Flippa

### 해외 — 폐업한 곳 (⭐콘텐츠 자산이 된다)

- **Transferslot** — 매물 전부 "Still on sale **6년 전**", 판매완료건 8년 전
- **ThriftMVP** — **DNS 자체가 없음**(도메인 소멸)
- **BuySellMVPs** — 매물 데이터가 없는 껍데기 랜딩
- **BuyMySideProject** — PH 291업보트 받고 폐업

→ 영어권 "Top N marketplaces" 목록 글들이 **죽은 사이트를 그대로 나열**하고 있다
(samdickie.me, iammagnus.com 2021년 글 등). **「2026년 기준 살아있는 곳만」 목록형 영문 글**은
실질 우위가 있는 콘텐츠 각도이고, SEO 표적 `sell abandoned side project`와도 맞는다.

### 한국 — 🛑 「국내 최초」는 사실이 아니다

- **사이트프라이스** (siteprice.co.kr) — 누적 등록 **16,820건 / 판매완료 14,795건** /
  현재 판매중 2,025건. 컨텐츠매물 182건 · **앱·어플매물 37건**. 에스크로 약관 있음, 고정가
- **싸장님들**(owners.kr) — 쇼핑몰양도·사이트매매·**앱 직거래**. 매물에 「월 매출 0원」 항목 존재.
  단 플랫폼이 결제 중개 안 함
- 사이트사구팔구(site4989.com) · 사이트매매(sitebuysell.xyz)
- 기업·스타트업 M&A 층: KMX(딜 1만건+, **스타트업 매도 게시판 별도**) · 마톡 · 컴파니마켓 ·
  M&A거래소(누적 9,660건) · LISTING · **중기부 M&A정보망**(정부 운영)

**⚠️ 단, 사이트프라이스는 우리와 같은 시장이 아니다.** 앱 매물 실측 —
월매출 1만원짜리를 3,500만원(주식앱)·5,000만원(캠핑카앱)·6,000만원(스코어앱)에 부른다.
**「개발비 회수」 호가이고 최저가가 250만원**이라, 주말 바이브코딩 MVP가 올라갈 자리가 아니다.
앱 카테고리는 관리도 안 된다("2020년 10월 서비스 종료 예정" 매물이 아직 목록에 있음).

### 한국 동종 선례 — 있었고, 멈췄다

**Sell Up** (sellup.vercel.app) — 2024-06-13 인프런 팀원 모집글 원문:
"사이드 프로젝트를 판매하고 구매할 수 있는 플랫폼입니다. **미완성 프로젝트를 판매하거나 구매**할 수
있으며… MVP는 완성된 상태이고 배포 후 베타테스트 중입니다."
→ **2026-08-24 직접 열어보니 매물 1건, 사실상 빈 페이지.**

### ⭐ 차별점 최종 판정 — 5개 중 1개 생존

| 차별점 | 판정 |
|---|---|
| 실시간 경매·입찰 | ✅ **유일한 생존.** 국내외 확인한 어디에도 없다 |
| 플랫폼 내장 결제 | ❌ IndieMaker는 Escrow.com, 사이트프라이스도 에스크로 약관 있음 |
| pre-revenue 허용 | ❌ IndieMaker 전용 필터 · 싸장님들 「월매출 0원」 항목 |
| 한국어·한국 사업자 | ❌ 한국어로 사이트·앱 파는 곳이 이미 여럿 |
| 수수료 | ❌ 우리 10% vs IndieMaker 3%(pre-revenue) |

### 🛑 문서·마케팅에서 쓰지 말 것

- 「국내 최초」·「국내에 없다」 — 사실이 아니다
- 「사이트프라이스가 우리 경쟁자다」 — 가격대·매물 성격이 다르다
- 정확한 표현: **「우리 층에는 한국에서 살아있는 경쟁자가 없다. 단 그 층에서 성공한 선례도 없다」**

### 후속 필요

- `docs/_business_plan_preview.html` §06 비교표가 **AcquireBase/Borderline/Flippa 기준이라 낡았다.**
  IndieMaker와 국내 층이 빠져 있고, 「내장 결제·pre-revenue」를 차별점으로 적어둔 부분은 이제 틀렸다
- SideProjectors 매물 수·수수료 미확인(SPA)

### 조사 절차 (다음에 반복할 때 이대로 할 것)

1. **고객 검색어로 검색한다** — "경쟁자"가 아니라 고객이 겪는 문제로
   (`sell abandoned side project`, `사이드 프로젝트 판매`)
2. 결과의 **listicle·커뮤니티 글을 열어 나열된 이름을 전부 뽑는다**
3. **이름마다 사이트를 직접 연다.** 검색 요약으로 끝내지 말 것 —
   ①매물 수 ②**최신 매물 날짜(생존 판정)** ③수수료 ④경매/고정가 ⑤결제 ⑥등록 요건
4. **옛 이름·리브랜딩을 확인한다** (1kProjects → IndieMaker를 이것 때문에 놓쳤다)
5. 죽은 곳은 죽었다고 기록한다

## 사업·콜드스타트 (요약)

- **병목:** 양면 콜드스타트 → **공급(매물) 먼저**. 광고 부족이 1순위 아님.
- **목표 순서:** 라이브 매물 10–30 → 실거래 1–3 → 판매자 채널 고정 → 구매자·바이럴
- **론칭 순서:** 매물 채우기(해외 공급 우선) → 20–50건 후 구매자+결제 ON 동시. 빈 장터에 PG 선행 비추천.
- **거래 레일:** 국경 비의존 단일 프로세스(한↔해·해↔해). 막는 것=이전 불가 매물 유형.
- **PG 전** 수동 입금 확인 UX·임시 계좌 플로우 **신규 금지** (`PLATFORM.md`)
- **공모전 (2026-08-09):** AI 활용 사례 · 분야 **생활 속 AI** · 상세 `workspace/ai-contest-2026-case-submissions.md` / Desktop `공모전_WA_*.png`

### 위탁 등록 매물 (제3자 소유 · 동의 기록) — 2026-08-16 기록

라이브 매물의 **판매자 계정은 4건 전부 `owner_id=30`(코어랩스)**이다. 이 중 3건은 우리 자산이지만
**`#8 온수냠냠냠`은 제3자 소유(레포 `github.com/hanseulhee/onsuYumYumYum`)를 위탁 등록한 건**이다.
매물 목록만 보면 무단 등록으로 오해하기 쉬워서(2026-08-16 실제로 그렇게 의심한 적 있음) 여기 남긴다.

**동의 근거 (공개 기록):** GitHub 이슈 `hanseulhee/onsuYumYumYum#131` — 원 소유자(계정 `hanseulhee`,
GitHub association `owner`)가 스레드에서 **"넵 그럼 대신 올려주셔도 좋습니다~"**로 명시 동의.
이후 우리가 등록 정보 요청 → 매물 등록 → 매물 링크(`/project.html?id=8`) 안내까지 같은 스레드에 남아 있음.
아웃리치 발신 경위는 GitHub 방치 레포 아웃리치 채널(2026-08-03 개시, 총 5건 발신) 참조.

**미이행 약속 (후속 필요):** 스레드에서 **"직접 가입하시면 그 계정으로 매물 명의를 옮겨드리겠다"**고
약속해둔 상태다. 원 소유자가 가입하면 `#8`의 소유권을 그 계정으로 이전해야 한다.
2026-08-16 기준 **원 소유자는 아직 미가입**(전체 가입자 4명 · 이슈 스레드에 8/13 이후 답장 없음).
이전 수단은 아래 「관리자 매물 명의 이전」으로 **2026-08-16에 만들어 뒀다** — 가입 알림이 오면
관리자 화면에서 이메일만 넣으면 된다.

**규칙:** 앞으로도 제3자 소유 매물을 대신 올릴 때는 ①동의 근거(URL·인용문)를 이 섹션에 기록하고
②매물 자체에도 위탁 등록임이 드러나야 한다(현재 `#8`에 그런 표시는 없음 — 검토 필요).

## 아키텍처

- `server.py` — FastAPI 진입점.
- `wakeagain/` — `api.py`, `auth.py`, `db.py`, `listing_i18n.py`, `global_config.py`, `scheduler.py`, `backup.py`, `oauth.py`, `pricing.py`, …
- `public/` — 정적 사이트 + `app/`(SPA) + `admin/` + `js/i18n.js` · `i18n-messages.js` · `listings.js` · `footer-visitors.js`
- `mobile/` — Capacitor 모바일 셸
- `scripts/` · `data/` (SQLite)

## 환경 설정

`.env.example` 기반. 주요: `DATA_DIR`, `APP_SECRET`/`JWT_SECRET`, `ALLOWED_ORIGINS`, `XAI_API_KEY`(매물 양방향 번역 — **2026-08-11부터 Railway에 실제 값 등록됨**, 그 전엔 문서에만 있고 비어있어서 번역 기능이 항상 조용히 실패했음), `WA_DEFAULT_LOCALE`, `WA_DEFAULT_DISPLAY_CURRENCY`, `ADMIN_SECRET`.
- **PortOne 결제** (2026-08-11 코드 추가, **2026-08-15부터 Railway에 실제 등록·라이브 반영 확인됨** — `wakeagain.com/api/v1/config`의 `portone.enabled`/`paypal_enabled` 둘 다 true): `PORTONE_STORE_ID`, `PORTONE_CHANNEL_KEY`(카드 · 토스 — **2026-09-02 심사 거부(경매·입찰 구조). 값은 들어가 있지만 실카드 결제 불가**), `PORTONE_API_SECRET`, `PORTONE_CHANNEL_KEY_PAYPAL`(페이팔 **계약 완료** · 실결제 미검증), `PORTONE_PAYPAL_MERCHANT_ID`, `PORTONE_WEBHOOK_SECRET`(아직 미발급)
- **구글 로그인** (2026-08-11 신규, **Railway에 실제 등록 완료·라이브 동작 확인됨**): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`(Railway에만 존재, 재확인 불가 — 분실 시 Google Cloud Console에서 재발급), `OAUTH_PUBLIC_BASE=https://wakeagain.com`. 코드(`wakeagain/oauth.py`)는 이전부터 있었고 이 세션은 설정만 함
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

- **PayPal 실결제 검증** — **2026-08-15 계약 완료 + Railway env var 반영 확인됨**(위 2026-08-15 항목). 코드(`07fca5f`)도 배포돼 있음. 아직 실제 결제를 한 번도 끝까지 돌려본 적은 없음 — 실매물로 낙찰→결제까지 진행해서 `loadPaymentUI` 콜백·STC 필드 확인 필요
- **🛑 토스페이먼츠(카드·계좌이체·가상계좌) — 2026-09-02 심사 거부 확정.** 사유: **경매·입찰 구조 사이트에는
  승인 불가** — **입찰 형식(가격 미확정)이 사유**로 확정(사용자 재확인, 다시 묻지 말 것). 8/25에 만들어 보낸 결제경로 자료(`docs/toss-review/`)와 신규 제작한 `/legal/refund.html`은
  그대로 남아 있으나 **승인과 무관해졌다.** → **더 이상 "심사 대기"·"승인되면 재확인"이라고 쓰지 말 것.**
  국내 결제를 열려면 구조(경매→고정가)를 바꿔 재심사하거나 국내 카드를 포기해야 한다 — 사용자 미결정.
  카카오페이(별도 진행 중 1건)도 같은 사유로 거부될 가능성 큼, 미확인. 이전 경위(8/15 1단계 → 8/22 PG사
  접수 완료·상점관리자 「심사중」 → 8/25 결제경로 자료 제출)는 git 이력 참조.
- **웹훅 시크릿** 미설정 (`PORTONE_WEBHOOK_SECRET`) — 서버 검증(`/payments/verify`)은 이미 동작하므로 급하지 않음, 콘솔에서 발급만 하면 됨
- **홍보 실행** — r/SideProject 2회 시도(1차 링크 포함→스팸필터 삭제됨, 2차 링크 제거 버전→최종 생존 여부 미확인) + X 게시 완료(PayPal 문구 제외). **r/indiehackers·r/SaaS·HN Show HN은 미착수** — 다음 세션 과제
- **SNS 로그인**: 구글은 라이브·검증 완료(env var는 위 "환경 설정" 참고). GitHub/Kakao는 `oauth.py`에 구현은 있으나 이번 세션엔 미설정·미검증
- 통신판매중개 **행정 신고 번호** (게시 대기) · Play 내부테스트
- 백엔드 하드코딩 한국어 문자열 — **2026-08-11 대부분 해소**(`70eddaa`): 매물 상태 픽커(`pricing.py` _en 필드) + 실제 UI에서 렌더되는 에러/안내 메시지 약 90개(`public/js/api.js`의 `translateBackendText` 딕셔너리, `parseErrorDetail`에서 자동 적용) + 신용등급·바이어랭크 배지(`listings.js`). **db.py/api.py 자체의 한글 리터럴은 그대로 남아있음** — 프론트 번역 딕셔너리로 커버했을 뿐, 문자열이 바뀌면 딕셔너리도 같이 고쳐야 함. `database.notify()`가 만드는 인앱 알림 문구(새 입찰·경매 시작 등)는 여전히 한국어 고정 — 미해결. 관리자(`/admin/*`) 화면은 의도적으로 한국어 유지(운영자 본인만 봄).
- `/app` SPA 46개 키 KO 누락 (쿠폰·선물·정산계좌·프로필 — 지금은 한국 사용자가 봐도 영어)
- ~~`delete-account.html` 영문판 없음~~ — **2026-08-11 해소**: `legal/delete-account.en.html` 신규(terms/privacy/business와 동일한 양방향 리다이렉트 패턴)
- 모바일 드로어 EN 잔여

## 트리거 말

| 말 | 동작 |
|----|------|
| WakeAgain 이어서 / 웨이크어게인 불러와 | PLATFORM + GLOBAL + 이 파일 + 열린 일 요약 (특히 위 "미검증/후속 필요" 목록부터) |
| WakeAgain EN 카피 이어서 | `docs/GROK_TO_CLAUDE_HANDOFF_2026-08-10.md` 부터 |
| 백엔드 한국어 문자열 정리 | `db.py`/`api.py` 하드코딩 약 595개 감사부터 (2026-08-11 발견, 미착수) |
| 앱 SPA 한국어 복구 | `i18n-messages.js` EN-only 46개 키에 KO 대응 추가 |
| PortOne 연동 / 페이팔 이어서 | Railway env var는 둘 다 반영됨(2026-08-15). **카드(토스)는 2026-09-02 심사 거부 — 경매·입찰 구조 사유. 승인을 기다리지 말 것**, 구조 변경 여부는 사용자 결정. 페이팔은 계약 완료 상태 — `wakeagain/payments.py`의 `build_paypal_payment_request` 실결제 테스트부터. pre-PG 우회 금지 (`PLATFORM.md` §B) |
| SNS 로그인 연결 | 구글은 라이브·완료(env var는 위 참고). GitHub/Kakao는 `oauth.py` 구현만 있고 콘솔·env 설정 안 함 — 그것부터 |
| PG | 결제 링크·웹훅→`paid` 만 · pre-PG 우회 금지 |
| 홍보 시작하자 / 매물 채우기 홍보 | r/SideProject 2회 시도 완료(결과 미확인)·X 게시 완료. **r/indiehackers·r/SaaS·HN Show HN부터** 이어서 시작 |

## 배포 전 최소 확인

```text
python _smoke_check.py
# 또는 python _predeploy_gate.py
git status   # docs/marketing/logs/* 등 untracked 제외
```

`master` push 후 Railway 상태·`https://wakeagain.com/health` (플랜 유효 시).  
EN 검수: `/?lang=en` 히어로·카드 Starting bid·`title_en` · `/?lang=ko` 한국어 유지.

⚠️ **`public/*.html`·`public/js/*.js`·`public/styles.css` 등 정적 자산을 바꾼 배포라면 `public/sw.js`의 `CACHE` 상수도 매번 같이 올릴 것** (2026-08-11 발견). 서비스워커(PWA 오프라인 캐시)는 **`sw.js` 파일 자체의 바이트가 안 바뀌면 브라우저가 "업데이트 없음"으로 판단**하고 예전 캐시를 계속 씀 — 서버는 최신인데 이미 한 번 방문한 사용자 브라우저엔 예전 화면이 계속 보이는 원인이 됨(오늘 색상 스킴 수정이 이것 때문에 한동안 반영 안 된 것처럼 보였음). `pwa-install.js`의 자동 업데이트 로직(`reg.update()` + `SKIP_WAITING` + `controllerchange` 리로드)은 이미 잘 짜여 있어서 **`CACHE` 문자열만 바꾸면 나머지는 자동**임 — 그래서 이 한 줄만 잊지 않으면 됨.

## 언어

사용자와 **한국어**로 소통한다.

## 매물 등록 필수 필드 정책 (2026-08-15 확정 · 구현 · 배포 완료 `b8d33ab`)

### 배경
경쟁자 실사(SideProjectors / BuyMySideProject / Failedups / Micro StartUps Acquisitions) 결과
**4곳 전부 코드 검증 기능이 없음.** 그중 최대 경쟁자 SideProjectors의 확인된 약점은
**매물 필수 입력이 대부분 선택 필드**라 트래픽·수익·저장소 링크가 비어 있는 매물이 많다는 것
(외부 평가: "craigslist of buying and selling side projects").

r/SideProject 실사용자가 "코드 품질을 어떻게 검증하느냐"를 물었으나, 실제 코드 리뷰 기능은
매물마다 사람이 봐야 해서 1인 운영에서 지속 불가능하다고 판단.

**방침: "코드를 검증해준다"가 아니라 "검증할 수 있게 강제한다."**

### 구현 사양

등록 폼에 다음 3개를 **필수**로 추가:

1. **저장소 URL** (GitHub/GitLab/Bitbucket)
   - 비공개 레포 허용. `is_private_repo` 불리언 필드를 같이 두고,
     true면 매물 페이지에 "구매 협의 단계에서 저장소 접근 권한 제공" 문구 자동 노출
   - 검증은 URL 형식(host 화이트리스트 + path 패턴)까지만. 실제 접근성은 검사하지 않음
     (비공개 레포에서 항상 실패하므로)

2. **라이브 데모 URL**
   - 대안 경로: `is_offline` 체크박스. true면 데모 URL 대신 **스크린샷 1장 이상 필수**
   - 이미 서비스가 내려간 매물이 다수이므로 이 대안이 없으면 등록이 막힘

3. **마지막 활동일** (`last_commit_at` 또는 `last_operated_at`)
   - 구매자가 방치 기간을 즉시 판단할 수 있게

### 매물 페이지 노출
상단에 신뢰 배지 3개: 저장소 등록 여부 / 데모·스크린샷 여부 / 마지막 활동일.
카피: "WakeAgain의 모든 매물은 저장소 링크가 필수입니다."

### 기존 매물 마이그레이션
- 필수화 이전 등록 매물(onsuYumYumYum 등)을 즉시 비공개 처리하지 말 것
- 판매자에게 보완 요청 후, 보완 전까지 "저장소 미등록" 상태 배지 표시
- 현재 매물 수가 적으므로 수동 대응으로 충분

### i18n
필드 라벨·배지·안내 문구는 기존 KO↔EN 자동 번역 파이프라인에 태울 것.
`listing_i18n.py` 참조. 모델명은 하드코딩되어 있으니 현재 라인업에 실재하는 이름인지 확인.

### ⚠️ 하지 말 것
- 자동 코드 품질 점수/등급 — 오판 시 판매자 분쟁, 근거 방어 불가
- 저장소 크롤링·코드 분석 — 비공개 레포에서 동작 안 함, 비용만 큼
- **필수 항목을 위 3개보다 늘리지 말 것.** 이 시장은 거래량 부족으로 죽음
  (BuyMySideProject는 PH 291업보트를 받고도 폐업). 등록 마찰이 늘면 공급이 마름

### 구현 메모 (2026-08-15)
- 컬럼: `projects.repo_url` / `is_private_repo` / `live_url` / `is_offline` / `last_activity_at`
  (`_ensure_columns`로 추가 — 기존 행은 NULL/0, 강제 비공개 없음)
- **`demo` 컬럼은 건드리지 않았다.** 자유 텍스트(영상 링크·설명 겸용)라 URL 검증을 걸 수 없어
  라이브 데모는 `live_url` 별도 컬럼으로 신설. `demo`는 기존 용도 그대로 선택 입력
- 스크린샷은 이 정책 이전부터 **이미 필수**였다 (`media.MIN_IMAGES_PER_LISTING = 1`).
  그래서 `is_offline` 대안 경로가 자동으로 충족된다
- 검증은 신규 등록(`POST /projects`)에만 강제. 재등록(`relist`)에서는 값을 보내면 반영만 하고
  강제하지 않는다 — 기존 판매자의 재등록을 막지 않기 위함
- 등록 UI는 **PWA 앱 폼 한 곳뿐**(`public/app/index.html` + `app.js`).
  `public/sell.html`은 매물이 아니라 `POST /api/v1/leads`로 가는 레거시 사전등록 폼이라 제외
- UI 라벨·배지 문구는 `public/js/i18n-messages.js`(KO/EN 수기)에 있다.
  `listing_i18n.py`는 판매자 **본문** 자동번역용이라 이 필드들과 무관(URL·불리언·날짜는 번역 대상 아님)
- QA: `_qa_required_fields.py` (15/15 통과)

### 관련
- 마케팅 카피로 재사용: "다른 곳은 저장소 링크가 선택입니다. WakeAgain은 필수입니다."
- 단, **메인 포지셔닝은 이게 아님.** 1순위는 "한글 등록 → 자동 번역 → 해외 매수자"
