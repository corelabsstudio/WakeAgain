# WakeAgain — 플랫폼 필수 조건 (사용자 확정)

> **2026-07-18 확정. 잊으면 안 됨.**

## 시장 우선순위 (사용자 확정 2026-08-11 — 2026-07-20 방침 뒤집음)

**#1 해외 우선** — 매물 노출·트래픽·첫 거래 성사를 해외에서 먼저 시도. 다국가 PG 연동 지금 진행.  
(2026-07-20 당시엔 "#1 한국에서 성사, 다국가 PG는 KR 이후 보류"였음 — 8/10 글로벌 UI 전환 이후 방향 전환.)  
정산 ledger는 당분간 KRW 유지, PG만 해외 카드/통화 결제 우선 지원.

<details><summary>이전 방침 (2026-07-20, 폐기됨)</summary>

**#1 한국에서 성사** — 매물·입찰·입금·이전 루프를 KR에서 먼저 검증.  
해외 전용 사이트 분리·다국가 PG는 **보류**.  
(UI EN/표시 통화는 유지 가능하나, 운영·약관·정산 기준은 한국.)

</details>

## 글로벌 (기반만 · 확장 보류)

- UI **EN default / KO opt-in** · 표시 통화 USD default (KO 브라우저→KRW seed) · KRW/EUR 선택 가능 (정산 ledger는 KRW)
- 설정: `GET /api/v1/config` → `global` · [`docs/GLOBAL.md`](./docs/GLOBAL.md)
- 다국가 PG·현지 약관·별도 해외 사이트 = **KR 성사 이후**

## 목표

**하나의 제품**이 아래 모두에서 동작·호환되어야 한다.

| 채널 | 요구 |
|------|------|
| **웹사이트** | 브라우저에서 바로 사용 |
| **Google Play** | 안드로이드 앱 다운로드·설치 |
| **Apple App Store** | iOS 앱 다운로드·설치 |

## 호환 의미

- 웹·앱 **같은 계정·같은 데이터** (`/api/v1` + JWT)
- UI는 달라도 **핵심 기능** 동일
- 웹만 만들고 끝 / PC 전용 단독 금지

---

## 제품 핵심 한 줄 (2026-07-19 확정)

> **누구나 쉽게 올리고, 누구나 쉽게 가격을 쓸 수 있지만 — 거래는 확실하게 성사시킨다.**

| 축 | 의미 | 제품에 나타나는 것 |
|----|------|-------------------|
| **쉬운 등록** | 진입장벽 최소 | 무료 올리기 · 쉬운 상태 문구 · 데모 안내(영상 OK) · 바이브 코딩 가능 |
| **쉬운 입찰** | 누구나 참여 | 지금 가격 공개 · 짧은 버튼 말 · Lv2만으로 가격 쓰기 |
| **확실한 거래** | 신뢰·완료 | 빠른 입금(PG 후 1시간 목표) · 미입금 시 차순위 · 사이트 내 신용 점수 · Lv 신원 · 입금 전 이전 금지 · 수수료 사전 고지 |

카피 톤: **쉽고 친절**하되, 돈·시간·제재 규칙은 **단호하고 명확**.

### 통신판매중개자 고지 (전자상거래법)

- 회사(코어랩스) = **통신판매중개자** · 거래 당사자 아님  
- **사이트 하단 필수 문구:**  
  「본 플랫폼은 통신판매중개자이며, 거래되는 상품의 품질과 내용은 판매자가 책임집니다.」  
  + 「이용자 간 사기·분쟁의 1차 책임은 당사자에게 있습니다. … 성사·대금·자산 이전을 보증하지 않습니다.」  
- 상세: `docs/이용약관.md` **v2.0** (전자상거래법·통신판매중개 표준 조항 체계 반영) · `/legal/terms.html`  
- 사기 포지션: `TRUST.md` §0-c  
- ※ 관할 관청 **통신판매중개 신고(등록)** 는 운영 준비 시 별도 행정 절차 (사이트 고지와 별개)

### 사기 전제 (운영 확정)

- 사기꾼 유입을 **전제**로 설계 · 예방은 하되 **피해 배상을 회사 의무로 두지 않음**  
- 금지: 검수·승인·사이트 내 신용 점수를 “보증”처럼 마케팅하는 카피  
- 금지: 랜딩에서 「중개가 아니다」처럼 중개자 지위를 부정하는 카피

### 나중 할 일 (사용자 확정 2026-07-19)

> **전체 체크리스트:** [`docs/나중_할일_BACKLOG.md`](./docs/나중_할일_BACKLOG.md)

#### A. 도메인 등록·HTTPS 이후 → SNS 로그인 연결

| 항목 | 내용 |
|------|------|
| 지금 | SNS 키 발급·연동 **보류** (로컬 `127.0.0.1` 최종 연결 안 함) |
| 트리거 | 도메인 결제·등록 완료 / DNS·HTTPS 붙은 직후 |
| 할 일 | 카카오(우선) → 구글 → 깃허브 · Redirect · `OAUTH_PUBLIC_BASE` |
| 문서 | `docs/OAUTH_SETUP.md` · `docs/OAUTH_발급가이드.md` |
| 유지 | SNS = 가입만 · **만 14세 · Lv2 · Lv3 그대로** |
| 에이전트 | **「SNS 로그인 연결하자」** 상기 |

#### A-2. 사업자 등록 이후 → 약관·고지 보완

| 항목 | 내용 |
|------|------|
| 트리거 | 사업자등록 완료 |
| 할 일 | 상호·대표·사업자번호·주소·연락처를 약관·개인정보·푸터에 반영 · 통신판매중개 신고 번호 게시 · (권장) 변호사 재검토 |
| 문서 | `docs/나중_할일_BACKLOG.md` §A-2 · `docs/이용약관.md` v2.0 |
| 에이전트 | 「사업자 냈다」 시 **법적 고지·약관 보완** 상기 |

#### B. PG 신청·연동 이후 → 결제·마감 자동화 완성

| 항목 | 내용 |
|------|------|
| **운영 방침 (2026-07-21 확정)** | **PG 붙이기 전에는 사이트 운영(실거래) 안 함.** 입금 확인·정산의 정답은 **PG 웹훅**뿐. |
| **금지** | PG 없을 때를 위한 **차선책·수동 운영 기능 추가 금지** (운영 입금 확인 UX, 임시 계좌 안내 플로우, “지금은 수동” 제품 기능 등). |
| 이미 있는 골격 | 자동 낙찰 · 스케줄러 · deal 상태(`awaiting_payment`→`paid`→`inspection`→`completed`) · 1h/48h 기한 필드 |
| **PG사 선정 (2026-08-11 조사·확정)** | **PortOne (구 아임포트)** — 파트너 정산 자동화(수수료 분배·세금계산서·지급 통합) + 해외카드 결제 aggregation. Stripe는 한국 사업자 정산 불가로 탈락. |
| **진행 상태 (2026-08-11 갱신)** | **카드 결제(국내 채널) 코드 완료·실제 결제창까지 로컬 검증 완료, 배포됨** (`wakeagain/payments.py`, `07fca5f`). **PayPal(해외) 채널도 등록·코드 완료**했으나 **PG 계약 심사 대기 중**(영업일 3일, 신청일 2026-08-11) — 승인 전까지 페이팔 실결제 미검증. |
| **수수료 구조 (2026-08-11 확정)** | 국내 판매자 10% / **해외(PayPal 채널) 판매자 19%**(`FEE_RATE_CROSSBORDER`, db.py — 임시값, 실제 계약 수수료 확정 시 재조정). 구매자는 국내·해외 무관 **항상 0원**("$0 buyer fees" 유지, `docs/GLOBAL.md`). |
| 트리거 | ~~사업자 + PG/에스크로 신청·연동 가능 시점~~ → 완료. 다음 트리거는 **PayPal PG 계약 승인 연락** |
| 할 일 (남은 것) | PayPal 실결제 1회 검증 · STC(`bypass.paypal_v2`) 필드 보강 · 웹훅 시크릿 발급·설정 |
| 문서 | `TRUST.md` §0-d · `wakeagain/db.py` deal_* · `wakeagain/payments.py`(신규) · `CLAUDE.md`의 2026-08-11 배포 이력 상세 |
| 에이전트 | PG 이야기 시 **결제 링크·웹훅→paid** 만. **pre-PG 우회 기능 새로 만들지 말 것.** PayPal 상태는 CLAUDE.md 트리거 말 "PortOne 연동 / 페이팔 이어서" 참고. |

---

## 쉬운 말 · 낮은 진입장벽 (2026-07-19 확정)

> **경매 사이트라고 어려우면 안 된다.**  
> **초등학생도 쓸 수 있을 정도로** 쉬운 말·짧은 문장·직관 UI.  
> 단, **쉬움 ≠ 느슨한 거래**. 규칙(입금·신용·2순위)은 분명히.

| 원칙 | 내용 |
|------|------|
| 말 | 전문 용어 최소화. 필요하면 **괄호 설명** 또는 쉬운 말로 대체 |
| 예 | 입찰 → 「얼마에 살지 쓰기」 / 현재가 → 「지금 가격」 / 낙찰 → 「가장 높은 가격으로 사기」 |
| 화면 | 한 화면 한 행동. 버튼은 동사로 |
| 금지 | 영어 약어·업계 은어 남발 (UI에서는 Lv·쉬운 말) |
| 균형 | **이해 속도** + **거래 완료에 대한 신뢰** 동시 |

---

## 거래 속도 · 회전율 (2026-07-19 확정)

> **우리는 메이저급 장기 경매장이 아니다.**  
> 목적: **빠른 거래**, **매물 회전율**, 방치·장난 입찰 최소화.

| 원칙 | 내용 |
|------|------|
| 정체성 | 소형·전문 장터 — 느린 명품 옥션 UX 모방 금지 |
| 낙찰 후 결제 | **안내에 따른 신속 입금**. **PG 후 목표: 1시간** 자동 타이머. 유예 장시간 정책 없음 |
| 왜 짧은 기한 | 결제 의사·자금 여부가 빨리 드러남 → 미입금 시 차순위·회전 |
| 미결제 | 낙찰 무효 · 신용 반영 → (PG 후) 차순위 자동화 목표. **수동 입금 차선책 없음** |
| 고지 | 입찰 UI·약관에 **현재 구현 단계**와 **PG 후 목표**를 분리 고지 (미구현 자동화 약속 금지) |
| 경매 기간 | 기본 **짧게** (예: 3~7일). 30일 방치는 비권장 |
| 입찰 문턱 | L2(실명·휴대폰). 성사·정산 L3. 마찰은 “돈 움직일 때”에 |
| 판매자 가이드 | **입금 확인 전** 코드·도메인·계정 이전 금지 |
| 우선순위 | 거래 성사 건수·속도 > 단일 매물 최고가 극대화 |

### 경매 라운드 · 희소성 (2026-07-30 확정 · 구현)

> **오픈마켓·아이템 장터식 끌올/도배 상위 ≠ 웨이크어게인.**  
> 경매는 **이번 라운드만 무대에 선다.**

| 규칙 | 제품 동작 |
|------|-----------|
| **이번 라운드만 전시** | 공개 목록·검색·`/auctions/live` = `listing_status=approved` **AND** `auction_status=live` 만 |
| **유찰 → 내림** | 마감·입찰 없음 → `auction_status=ended` + `listing_status=archived` · 공개 보드에서 제거 |
| **재등록 → 재검수** | `POST /projects/{id}/relist` → `pending` · 운영 승인 후에만 다시 live |
| **재등록 → 후순위** | 승인 시 `round_started_at=now` · 정렬은 부스트 다음 **`round_started_at ASC`** (줄 맨 뒤) |
| **정렬 철학** | **신뢰 가산점 높은 순** → 동점이면 이번 라운드 입장 순 · 재등록으로만 상단 탈환 불가 |
| **admin 재개** | 기본 = 재검수 큐 · `force_live` 만 즉시 새 라운드(역시 후순위·부스트 초기화) |

#### 상위 노출 가산점 (예비 구매자 기준)

> **판매자 계정 신용이 아니라**, 매물을 보고 사는 사람에게 도움이 되는 정보·케어 약속.

| 축 | 내용 |
|----|------|
| **설명·포트폴리오** | 한 줄 소개, 스토리, 하는 일, 되는 것/한계, 대상, 스크린샷(포트폴리오), 데모 검수, 키워드 등 |
| **헬프티켓** | 무료 포함 **1~3장** · 개수 **비례** (1회당 +8점) · 추가 판매 on 소폭 가산 |

정렬: 유료 부스트 → **exposure_score DESC** → `round_started_at ASC`  
구현: `listing_trust_score_sql` · `compute_listing_exposure_score`

구현: `wakeagain/db.py` (`public_live_where_sql`, `start_auction_round`, `archive_unsold_round`) · `wakeagain/api.py`

### 헬프티켓 (2026-07-30 · 크몽식)

| 항목 | 내용 |
|------|------|
| 성격 | 판매자(제작자) **안내·설명** 창구 · **개발 완료·추가 개발 의무 아님** (플랫폼·제작자 공통) |
| 분쟁 | 사용 여부·답변 내용·횟수 등 의견 차이는 **구매자·판매자 협의** · **사이트 중재·개입 없음** (사기·약관 위반·결제는 기존 신고) |
| 판매자 설정 | 무료 포함 **1~3장** · 추가 1회 단가(0=판매 안 함, 5천~10만) · SLA 24/48/72h |
| 활성화 | 이전 완료 → `inspection` 시 포함분 지급 · 14일 윈도우 |
| 사용 | 구매자 질문 스레드 1 = held → 판매자 답변 시 1회 차감 |
| 추가 구매 | 판매자 단가 · 수수료 15% · 답변 후 판매자 정산 · PG 전 `Q_CREDIT_PURCHASE_MOCK=1` 또는 pending |
| API | `GET/POST .../q-credits/*` · 공개 문구 `q_credit_policy_public()` |

상세 게이트·카피: `TRUST.md` · 약관 초안: `docs/이용약관.md` · 분쟁 안내: `/guide/dispute.html`

---

## 구현 현황 (가능하게 만든 구조)

```
웹 브라우저  ──┐
Play (Capacitor)─┼──►  같은 API  /api/v1/*  ──► SQLite (DATA_DIR)
App Store ──────┘         JWT Bearer
```

| 구성 | 경로 | 역할 |
|------|------|------|
| 공통 API | `wakeagain/api.py` | 가입·로그인·프로젝트·관심 |
| DB | `data/wakeagain.db` | 모든 채널 공유 저장소 |
| 공통 JS 클라이언트 | `public/js/api.js` | 토큰·요청 헬퍼 |
| 웹 앱 셸 | `public/app/` | 로그인·목록·등록 (모바일 UI) |
| 랜딩 | `public/index.html` 등 | 마케팅·사전등록 폼 |
| 스토어 셸 | `mobile/` (Capacitor) | Play / App Store 패키징 |
| 설정 | `GET /api/v1/config` | 클라이언트가 부팅 시 읽음 |

### API (모든 채널 공통)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/health` | 헬스 |
| GET | `/api/v1/config` | 클라이언트 부팅 설정 |
| POST | `/api/v1/auth/register` | 가입 → JWT (**만 14세 이상** · `birth_date` + `confirm_age_14` 필수) |
| GET | `/api/v1/auth/oauth/{google\|github\|kakao}/start` | SNS 로그인 시작 (환경변수 설정된 제공자만) |
| GET | `/api/v1/auth/oauth/.../callback` | OAuth 콜백 → JWT → `/app/?wa_token=` |
| PUT | `/api/v1/me/birth-date` | SNS 후 만 14세 생년월일 |
| POST | `/api/v1/projects/{id}/report` | 구매자 신고 (Lv2) · 3건→경매중단 · 5건→계정정지 |

SNS 설정: `docs/OAUTH_SETUP.md` · **SNS ≠ 계좌만으로 끝** (Lv2·Lv3 유지)
| POST | `/api/v1/auth/login` | 로그인 → JWT |
| GET | `/api/v1/me` | 내 정보 |
| GET | `/api/v1/projects` | 목록 (`?mine=true`) |
| POST | `/api/v1/projects` | 프로젝트 등록 (로그인 필요) |
| POST | `/api/v1/interest` | 구매 관심 |
| POST | `/api/leads` | 랜딩 익명 폼 (DB 저장) |

문서: 서버 실행 후 `/api/docs`

### 웹

```powershell
cd C:\Users\hysoo\projects\WakeAgain
python -m uvicorn server:app --host 0.0.0.0 --port 8080
```

- 사이트: http://127.0.0.1:8080/  
- 앱 셸: http://127.0.0.1:8080/app/

### Play / App Store (Capacitor)

| | |
|--|--|
| 패키지 ID | `com.corelabs.wakeagain` |
| 경로 | `mobile/` |
| 문서 | [`mobile/README.md`](./mobile/README.md) |

```powershell
cd mobile
npm install
npm run add:android   # 최초 1회 (Play)
# npm run add:ios     # macOS only (App Store)

# 개발 (에뮬레이터 → PC API)
$env:WAKEAGAIN_API_BASE = "http://10.0.2.2:8080"
npm run android

# 스토어 빌드 전
$env:WAKEAGAIN_API_BASE = "https://your-api.example"
npm run build:store:prep
# → Android Studio: Generate Signed Bundle (.aab)
```

실기기·스토어에서는 **API를 HTTPS로 배포**한 뒤 `WAKEAGAIN_API_BASE` 를 그 주소로 고정.

### 환경변수

| 변수 | 용도 |
|------|------|
| `DATA_DIR` | DB·데이터 경로 (기본 `./data`) · **프로덕션 볼륨 `/data` 필수** |
| `APP_SECRET` / `JWT_SECRET` | JWT 서명 (운영 필수) · **재배포 시 회전 금지** (전원 로그아웃) |
| `ALLOWED_ORIGINS` | CORS (기본 `*`) |
| `JWT_DAYS` | 토큰 유효일 (기본 30) |
| `DB_BACKUP_ENABLED` | SQLite 스냅샷 자동 백업 (기본 `1`) |
| `DB_BACKUP_INTERVAL_SEC` | 백업 주기 초 (기본 `3600`) |
| `OFFSITE_S3_*` | 오프사이트 백업 (R2/S3) · [`docs/OFFSITE_BACKUP_SETUP.md`](./docs/OFFSITE_BACKUP_SETUP.md) |
| `ALLOW_DESTRUCTIVE_ADMIN` | 회원 전체 삭제·DB 복구 허용 (기본 **꺼짐** · 사고 방지) |

### 회원 데이터 보호 (2026-07-22 확정 · 최우선)

> **회원 데이터 유실 = 서비스 파산급.** 배포·기능보다 먼저 지킨다.

| 장치 | 내용 |
|------|------|
| 영속 볼륨 | Railway Volume → `DATA_DIR=/data` · 컨테이너 재시작해도 DB 유지 |
| 자동 백업 | `wakeagain/backup.py` · 기동 시 + 주기적 스냅샷 → `/data/backups/` |
| **오프사이트** | `wakeagain/offsite_backup.py` · S3/R2 업로드 (볼륨 장애 대비) |
| 급감 감지 | `peak_users` / `last_users` 메타 · 0으로 떨어지면 health·로그 CRITICAL |
| purge 잠금 | `POST /admin/users/purge-all` 기본 403 · `ALLOW_DESTRUCTIVE_ADMIN=1` + confirm 필요 · 삭제 전 백업 |
| 복구 | 원격 pull → `POST /admin/data/restore` · 동일 잠금 |
| 운영 UI | `/admin/` → **데이터·백업** 탭 |

상세: [`docs/DATA_PROTECTION.md`](./docs/DATA_PROTECTION.md) · R2 설정: [`docs/OFFSITE_BACKUP_SETUP.md`](./docs/OFFSITE_BACKUP_SETUP.md)

---

## 트리거

「WakeAgain 이어서」 / 「웨이크어게인 불러와」 → 이 파일 + `BRAND.md` 필수.
