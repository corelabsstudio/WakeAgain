# Grok → Claude Code 작업 이관 (WakeAgain)

**작성:** 2026-08-10  
**목적:** 이 세션에서 한 글로벌 론칭·EN UX 카피 작업을 Claude Code에서 끊김 없이 이어가기 위한 정본.

> 코드/배포 전 **현재 git·라이브**를 다시 확인할 것. 이 문서는 요약이며 도구를 재실행하라는 뜻이 아님.

---

## 1. 프로젝트

| 항목 | 값 |
|------|-----|
| 경로 | `C:\Users\hysoo\projects\WakeAgain` |
| 라이브 | https://wakeagain.com |
| 원격 | `origin` → `https://github.com/corelabsstudio/WakeAgain.git` |
| 기본 브랜치 | `master` |
| 배포 | `master` push → Railway auto-deploy (`steadfast-dream / production`) |
| 헬스 | `https://wakeagain.com/health` |

### 배포 확인 루틴

```text
git status
git log --oneline -5
# push 후
# GET /health → ok:true
# GET /?lang=en → EN 카피
# GET /api/v1/projects?limit=5 → title_en 필드
```

로컬 Railway CLI 토큰은 403이 날 수 있음 → **GitHub push 자동배포**가 정본.

---

## 2. 이 세션에서 완료한 일 (요약)

### A. 글로벌 퍼스트 (해외 론칭 표면)

- 기본 로케일 **EN**, 표시 통화 **USD** (KO 브라우저 → KRW seed)
- KR 전용 UI: 사업자 블록·국내 전화·카카오 버튼 → `.wa-kr-only` (EN에서 숨김)
- 타이포: 기본 Inter · KO일 때만 Pretendard/Noto
- 관련: `wakeagain/global_config.py`, `public/js/i18n.js`, `public/styles.css`, 다수 HTML

### B. 앱 딥플로우 EN

- `public/app/index.html` 올리기 폼 전량 EN 폴백 + `data-i18n` / `app.create_*` 키
- `public/app/app.js` 검증/배너/쿠폰 등 `t()` EN 폴백
- `public/js/i18n-messages.js` 대량 EN/KO 키

### C. 매물명/소개 EN (해외 UI)

- DB 컬럼: `projects.title_en`, `one_liner_en`, `story_en`
- 모듈: `wakeagain/listing_i18n.py` (xAI 번역 + 휴리스틱, 약영문 재시도)
- 목록/상세 API에서 `ensure_rows_en` 후 응답
- FE: `listings.js` `listingTitle()` / `oneLiner()`, `project.html`, `app.js`
- 라이브 매물 큐레이션:
  - Trace → `Trace — AI interview experience writer`
  - 리치킷 → `ReachKit — promo copy & channel recommender`
  - 맵: `LISTING_DEMO_I18N` in `wakeagain/db.py` (KO 제목 exact key)

### D4. App shell full EN pass (login/profile/settle/fees/coupons)

- public/app/index.html: auth foot, age, verify, seller id, profile, settle, notif, fees, coupons EN defaults + data-i18n
- public/app/app.js: create_ok alert, oauth errors EN; price labels Starting bid
- keys in i18n-messages.js

### D5. Login foot Korean under EN (screenshot 2026-08-10 100725) — **fixed in code**

- **Root cause:** `app.create_ok` had raw multiline string → `i18n-messages.js` **SyntaxError** → entire `WA_I18N_EXTRA` never loaded → EN overrides missing; cached/old Korean foot could stick.
- **Fix commit:** `dc9d05b` — escape `\n` in create_ok, naturalize `app.auth_foot` EN, add KO `app.auth_foot`, `app.delete`→Remove, SW `v42-en-auth-foot-fix`
- **Verify when live is up:** `/app/#login` EN → footer must be English (“You can browse public listings… buyer interest form…”)

### ⚠ LIVE OUTAGE (as of 2026-08-10 ~01:20 UTC)

- `https://wakeagain.com/*` → Railway JSON **404 Application not found** (`x-railway-fallback: true`)
- GitHub Deployments last registered: **`58d46de`** (inactive). Later pushes (`27018d1`, `047db35`, `dc9d05b`) **no Railway deployment record**.
- Local `.launch/railway.token` is a **placeholder comment**, not a real Account Token → `deploy_railway.py` / CLI cannot redeploy.
- **Action for operator:** Railway dashboard `steadfast-dream / production` — restart service, re-enable GitHub auto-deploy, fix custom domain, replace Account Token.

### D3. App list EN chrome (/app/#list)

- Toolbar, buy-how panel, feed tabs, empty/more: data-i18n (app.buyhow_*, app.feed_*, app.refresh, ...)
- app.js: Hangul keyword filter in EN, credit label map (신규->New), reload cards on lang/currency change

### D2. Cold-start 진입 모달 i18n

- public/index.html showCollectionModeNotice() — EN/KO 로케일 분기 + collect.* 키
- 세션 dismiss: sessionStorage.wa_collection_notice_dismissed

### D. EN UX Writer 패스 (PH / Indie Hackers 톤) — 이번 배포

- `public/js/i18n.js` EN 팩 전면 폴리시
- `public/js/i18n-messages.js` EN 보강 (start-price→starting bid, PG 제거, safety 등)
- 용어 고정: **Starting bid / Current bid / Place bid / View listing / Handover / Browse listings / Free price check / $0 buyer fees / Live listings**
- 메타: `public/index.html` title/OG
- 캐시: `?v=20260810-ux-en`, SW `wakeagain-shell-v38-ux-en`

---

## 3. 의도적 미완 / 다음 작업 (Claude Code 후보)

우선순위 권장:

1. **KO 페이지 잔존 EN 미번역 서피스**
   - `sell.html`, `buy.html`, `guide/*` 가 EN UI에서도 KO HTML 폴백이 섞일 수 있음
   - 목표: EN 폴백 + data-i18n (랜딩과 동일 수준)

2. **앱 딥 폼 카피 EN 폴리시 2차**
   - `app.create_*` 키가 기능적으로는 EN이지만, PH 톤으로 한번 더 다듬기
   - “KRW ledger” 문구를 구매자용 vs 판매자 정산용으로 분리 표기

3. **매물 EN 품질**
   - Railway에 `XAI_API_KEY` 있으면 신규 한글 매물 자동 번역 품질↑
   - 없으면 휴리스틱/큐레이션 맵 의존 → 새 한글 매물 등록 시 `LISTING_DEMO_I18N` 또는 관리자 EN 편집 UI

4. **키워드 EN**
   - 현재 EN UI에서 순수 한글 태그 숨김
   - 다음: `keywords_en` 저장 또는 태그 영문 정규화

5. **결제 카피**
   - 소비자 UI에서 “PG” 제거 완료(홈/핵심 i18n)
   - 약관·가이드 문서에 잔여 PG 표현 점검

6. **모바일 드로어**
   - 랜딩 모바일 메뉴에 KO 하드코딩 잔여 가능 → EN 폴백/`data-i18n` 통일

---

## 4. 중요 파일 맵

| 영역 | 파일 |
|------|------|
| EN 홈 카피 | `public/js/i18n.js` (`en` pack) |
| 부가 EN 문자열 | `public/js/i18n-messages.js` |
| 마켓 카드 | `public/js/listings.js` |
| 상세 | `public/project.html` |
| 앱 셸/올리기 | `public/app/index.html`, `public/app/app.js` |
| 글로벌 설정 | `wakeagain/global_config.py` |
| 매물 EN | `wakeagain/listing_i18n.py`, `wakeagain/db.py` (`project_to_dict`, `LISTING_DEMO_I18N`) |
| API | `wakeagain/api.py` (`list_projects`, `get_project`, `create_project`) |
| 글로벌 문서 | `docs/GLOBAL.md` |
| 스타일/KR-only | `public/styles.css` (`.wa-kr-only`) |

---

## 5. 사용자 작업 규칙 (강제)

- 말한 것만 한다 / 애매하면 되묻는다  
- 완료 전 핵심 1–2줄 되짚기  
- 사이트 반영 전 필터 → 위반 시 코드 반영 금지  
- 배포는 사용자 확인 후 (이번 요청은 “다 되면 배포”로 승인됨)

---

## 6. 검증 체크리스트 (재개 시)

- [ ] `/?lang=en` 히어로: “Sell the project you stopped building.”
- [ ] 내비: Listings / How it works / Safety
- [ ] 카드: Starting bid / Current bid / Place bid / View listing
- [ ] 한글 매물 카드 제목이 EN UI에서 한글 원문만 보이지 않음 (`title_en`)
- [ ] `/?lang=ko` 는 한국어 유지
- [ ] `/health` ok
- [ ] 불필요 untracked (`docs/marketing/logs/*`) 커밋하지 말 것

---

## 7. 최근 관련 커밋 계열 (참고)

작업 트리에서 `git log --oneline -15` 로 확인. 키워드:

- `feat(global): English-first launch surface`
- `feat(listings): show English titles for EN`
- `fix(listings): show EN title/one-liner on market cards`
- `feat(copy): PH/IH English UX pass` (이번)

---

**트리거 말 (Claude Code):**  
「WakeAgain EN 카피 이어서」 / 「sell/buy/guide EN 폴백」 / 「매물 keywords_en」
