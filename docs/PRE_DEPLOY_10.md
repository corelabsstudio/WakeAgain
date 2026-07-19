# WakeAgain — 실배포 전 10점 점수표

**정의:** 사업자 · PG · SNS 키 · 실유저 · **실배포(도메인/HTTPS)** 를 제외한  
**코드·제품으로 통제 가능한 범위**에서 만점.

| # | 항목 | 검증 |
|---|------|------|
| 1 | 랜딩·앱·진단·자랑·약관 페이지 200 | smoke / gate |
| 2 | 공통 API health · config · stats · projects | smoke |
| 3 | 가입 · 만14세 차단 · 이메일 인증(dev) · L2 · L3 | smoke |
| 4 | 매물 등록 게이트 (신원·attest) · 신고 자동 일시정지 | smoke |
| 5 | 자랑 = **진단 점수 필수** (diag_score) | smoke |
| 6 | 경매 마감 **자동 낙찰** 로직 | unit |
| 7 | 경매 **상시 스케줄러** 모듈 | health + unit |
| 8 | 보안 헤더 (nosniff · frame · referrer) | gate |
| 9 | 관리 키 **프론트 미노출** | gate |
| 10 | 404 · sitemap · robots · ux9 | smoke |
| 11 | 디자인 UX9 전 페이지 링크 | gate |
| 12 | 약관·개인정보·중개 고지 존재 (사업자 칸 제외) | smoke |
| 13 | `.env.example` · `.gitignore` · secrets 로컬 생성 | gate |
| 14 | Dockerfile · railway.toml | gate |
| 15 | PLATFORM · BRAND · TRUST · BACKLOG 문서 | gate |
| 16 | smoke 전체 PASS (0 FAIL) | smoke |
| 17 | 시작가/상태 정책 API | smoke |
| 18 | OAuth 코드 존재 + 미설정 시 503 (키 없이 안전) | smoke |
| 19 | PWA manifest · 로고 자산 | gate |
| 20 | 버전·health ready | health |

**만점 판정:** `python _predeploy_gate.py` → `PRE-DEPLOY SCORE: 10/10`

### 만점 이후에도 남는 것 (점수 밖)
- 사업자등록 · 통판중개 신고 번호
- SNS 콘솔 키 (사업자·도메인 이후)
- PG · 1시간 입금 · 2순위 자동
- 실도메인 · HTTPS · Railway 공개
- 실유저·실거래
