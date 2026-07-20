# WakeAgain — 진행 체크포인트

**저장 시점:** 2026-07-20  
**상태:** **실배포 전 10/10** (사업자·PG·SNS키·실유저·실배포 제외) — `python _predeploy_gate.py`  
**버전:** `1.0.0-pre` · 점수표 `docs/PRE_DEPLOY_10.md`

### 2026-07-20 품질 패치 (PG·사업자·실유저·실배포 제외)

- [x] 경매 **백그라운드 스케줄러** (`wakeagain/scheduler.py`, 기본 60초, `AUCTION_SCHEDULER`)
- [x] `/health` 스케줄러·prod 경고 노출
- [x] 보안 헤더 (nosniff · frame · referrer · permissions)
- [x] HTML 캐시 무효화 · 정적 자산 캐시
- [x] `public/404.html` 예쁜 404
- [x] `sitemap.xml` · `robots.txt` 정리
- [x] `ux9.css` 디자인 레이어 전 페이지
- [x] 자랑 = 무료진단 후만 등록 (UI + API `diag_score`)
- [x] `.env.example` · `.gitignore` · **로컬 `.env` 자동 시크릿**
- [x] smoke + **unit** + **`_predeploy_gate.py` → 10/10**


### 법적 정합 수정 (2026-07-19 · 사업자 제외)

- [x] 약관 **v2.1** — 입금·2순위 고지를 pre-PG 구현 상태와 일치  
- [x] 유저 대면 카피: 「1시간 자동」 약속 제거 → 안내 신속 입금 + PG 후 목표  
- [x] 수수료 조문 링크 **제13조** (구 제6조 오표기 수정)  
- [x] 면책 조문 링크 **제21조** (구 제14조의2 정리)  
- [x] 랜딩 과장 카피 완화 (바이어 풀 · 이전 전문가)  
- [x] 「승인」→「게시 허용/형식 검수」 사용자·어드민 표기  
- [x] 어드민 기본 키 UI 노출 제거  
- [x] 정산 계좌 **저장 시 암호화** + 개인정보방침 1.1  
- [ ] 사업자·통신판매중개 신고 정보 게시 (사업자 등록 후 A-2)

### 나중 할 일 (보류 백로그)

**전체 목록:** [`docs/나중_할일_BACKLOG.md`](./docs/나중_할일_BACKLOG.md)

#### A. 도메인 등록·HTTPS 이후
- [ ] **SNS 로그인 연결** (카카오 우선 · 코드 있음 · `docs/OAUTH_발급가이드.md`)
- [ ] `OAUTH_PUBLIC_BASE=https://{도메인}` + 콘솔 Redirect 등록
- [ ] 통신판매중개 행정 신고 (사이트 고지와 별개)

#### A-2. 사업자 등록 이후
- [ ] **약관·개인정보·푸터에 사업자 정보 보완** (상호·대표·등록번호·주소·연락처)
- [ ] 통신판매중개 신고 번호 게시
- [ ] (권장) 약관 변호사 재검토

#### B. PG 신청·연동 이후
- [ ] 낙찰 시 **결제 링크 자동 생성·발송**
- [ ] **1시간 입금 타이머** + 미입금 시 **2순위 자동 전환**
- [ ] PG 웹훅 ↔ 성사·수수료 연동
- [x] 마감 경매 **백그라운드 스케줄러** (완료 · PG 전에도 동작)
- [ ] 입금 확인 전 이전 금지 UX를 결제 상태와 연동 (PG 상태 연동 후)

> 지금: 마감 자동 낙찰·**상시 스케줄러**·앱 알림 있음. **결제 링크·2순위 자동은 PG 후.**

---

## 지금까지 한 일

### 브랜드 · 카피
- 브랜드: **WakeAgain**
- 슬로건: **프로젝트에 두 번째 기회를 주세요.**
- 선언 문구 확정 (문구 수정: **시간이 없거나**)
- 카피 문서: `copy.md` (프로젝트 루트 + `Desktop\WakeAgain\copy.md`)
- **미끼 유틸:** `/diagnose.html` — 「내 잠든 프로젝트, 팔릴까?」 30초 진단 + 시작가 힌트 (가입 불필요 · 정적)

### 디자인
- Variant 선택 디자인 6장 기준 랜딩 반영  
  (`Desktop\WakeAgain\1.png` ~ `6.png`)
- 딥 블랙 + 퍼플/바이올렛 UI
- 모바일 메뉴 드로어(큰 매물 등록 카드) 제거
- 큰 모니터에서 더 꽉 차게 반응형 조정 (폭·히어로·타이포)
- **sell/buy** 페이지 랜딩과 동일 퍼플 톤 + pill nav

### 랜딩 섹션 순서
1. Hero — 「멈춰버린 프로젝트에 숨을 불어넣다.」 + **실건수 지표**
2. Problem 선언 + 문제 3카드
3. Services 3카드 + 지표
4. Testimonials (시나리오 예시 — 가상 명시)
5. 왜 WakeAgain인가요? (벤토)
6. 최근 올라온 매물 (**API `/api/v1/projects`**, 없으면 예시 카드)
7. Final CTA (슬로건) + Footer

### 플랫폼 · API (웹 + Play + App Store 호환)
| 구성 | 경로 |
|------|------|
| 공통 API | `wakeagain/api.py` · JWT |
| 공개 통계 | `GET /api/v1/stats` (허수 GMV/성공률 없음) |
| 랜딩 매물 JS | `public/js/listings.js` |
| 히어로 지표 | `public/js/hero-stats.js` |
| 앱 셸 | `public/app/` — 공개 목록 로그인 없이 열람, 등록/내매물은 로그인 |
| sell/buy | 사전등록 폼 + 계정 등록 경로 안내 |

### 히어로 수치 정책 (확정)
- **mode:** `live_counts` — DB 실건수만
- 표시: **등록 매물** · **관심 등록** · **등록 비용 무료**
- 금지: 가짜 활성 바이어 수 / 누적 거래액($4.2M) / 매칭 성공률(89%)
- config: `metrics_policy` in `GET /api/v1/config`

### 인증 · 신뢰 플로우 (TRUST.md)
| 레벨 | 조건 | 가능 |
|------|------|------|
| L0 가입 | 이메일+비번 | 열람, 경량 관심 |
| L1 | 이메일 6자리 코드 | 프로필 입력 |
| L2 | 실명+휴대폰+역할 | **매물 등록** · (향후 입찰) |
| L3 | 정산(예금주·은행·계좌) | **성사·이전 준비** |

| 행동 | 필요 |
|------|------|
| 공개 매물 보기 | 비로그인 OK (연락처 비공개) |
| 매물 등록 `POST /projects` | **L2** (서버 403 게이트) |
| 관심 등록 (buy) | 이메일만 (입찰 권한 아님) |
| 빠른 판매 접수 (sell) | lead OK · 공개 리스팅 아님 |

해시: `/app/#login` `#register` `#verify` `#profile` `#settlement` `#list` `#new`  
문서: `TRUST.md` · 개발 시 `dev_email_code` (`EMAIL_DEV_MODE=1`)

### 코드 위치
| 항목 | 경로 |
|------|------|
| 랜딩 HTML | `public/index.html` |
| 스타일 | `public/styles.css` |
| API/서버 | `server.py` + `wakeagain/` |
| 판매/구매 폼 | `public/sell.html`, `public/buy.html` |
| 로컬 확인 | http://127.0.0.1:8080/ |

---

## 이번에 완료 (2026-07-19 순차)

- [x] 실제 매물 데이터 연동 (데모 카드 → API, 빈 경우 예시 배지)
- [x] 로그인/회원가입 플로우 정리 (공개 열람 · 해시 라우트 · 한국어 UI)
- [x] sell/buy 페이지 퍼플 톤 맞춤
- [x] 히어로 수치 실건수 정책 결정·반영
- [x] 신뢰·개인정보 게이트 L0–L3
- [x] **법적 표기 (RoadLog 정렬):** 이용약관 · 개인정보처리방침 · © CoreLabs · corelabs.studio@gmail.com
- [x] **공개 실시간 경매:** 입찰 현재가 방문객 전원 공개 · `/project.html` · `/api/v1/auctions/live` 폴링
- [x] **관리자 검수 페이지:** `/admin/` 체크리스트 · 승인/보류/반려 · 공개는 approved만
- [x] **관리자 전용 PWA:** `/admin/install.html` · manifest `WA Admin` · SW scope `/admin/` · `GET /api/v1/admin/session` 키 게이트
- [x] PROGRESS 갱신 · 배포 준비 메모

### 공개 경매 (제품 결정)
- 입찰 중 **현재가·호가 횟수·최근 입찰 티커** = 사이트 전원 공개 (로그인 불필요)
- 입찰 실행만 L2 신원 필요
- 입찰자 표기: 닉 마스킹 (`김**`) · 연락처 비공개
- 폴링 4초 · 가격 변동 시 하이라이트

### 법적 · 운영 표기
| 항목 | 값 |
|------|-----|
| 운영 | 코어랩스(CoreLabs) |
| 문의 | corelabs.studio@gmail.com |
| 카피라이트 | © 2026 CoreLabs. All rights reserved. |
| 약관 | `/legal/terms.html` · `docs/이용약관.md` |
| 개인정보 | `/legal/privacy.html` · `docs/개인정보처리방침.md` |

---

## 나중에 이어서 하면 좋은 것 (후보)

- [ ] Railway 배포 (`railway.toml` 있음) · `APP_SECRET` / `JWT_SECRET` 설정
- [ ] 실기기용 `WAKEAGAIN_API_BASE` = HTTPS API URL
- [ ] 매물 `listing_status` 승인 운영(admin) 또는 수동 DB 플래그
- [ ] 히어로 live-card를 첫 매물 입찰 UX로 고도화
- [ ] 도메인 wakeagain.com 등록 후 DNS
- [ ] Variant 미세 조정 (원하면)

### 배포 준비 한 줄
1. `DATA_DIR` 영속 볼륨  
2. `JWT_SECRET` 또는 `APP_SECRET` 강한 값  
3. Railway root = 이 프로젝트 · Dockerfile / railway.toml  
4. 배포 URL을 모바일 `WAKEAGAIN_API_BASE`에 고정  

---

## 이어하기 한 줄

> 「PROGRESS.md 기준으로 이어서」 / 「배포 준비」 / 「승인 플로우」 라고 말하면 됩니다.
