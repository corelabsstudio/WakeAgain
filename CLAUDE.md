# WakeAgain — Claude Code 안내

이 파일을 읽은 뒤 **현재 디스크·git·라이브**를 재검증하고 작업한다.  
옛 트랜스크립트·Grok 메모리는 자동 동기화되지 않는다. 아래 문서가 정본이다.

**마지막 문서 갱신:** 2026-08-11 (EN/KO 양방향 잔여 누락 정리 + select 팝업 다크모드 버그 + SW 캐시 버전 규칙 + 구글 로그인 라이브 + 해외 홍보(레딧·X) 1차 실행)

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

- **PayPal 실결제 검증** — 코드는 다 짜서 배포됨(`07fca5f`), **PG사 계약 심사 대기 중**(2026-08-11 신청, 영업일 3일). 승인 오면 실제 결제 한 번 끝까지 돌려서 `loadPaymentUI` 콜백·STC 필드 확인해야 함
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
| PortOne 연동 / 페이팔 이어서 | 카드 결제는 완료·검증됨(`07fca5f`). 페이팔은 PG 계약 심사 상태부터 확인(`hhs1261@naver.com` 메일함) → 승인됐으면 `wakeagain/payments.py`의 `build_paypal_payment_request` 실결제 테스트부터. pre-PG 우회 금지 (`PLATFORM.md` §B) |
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
