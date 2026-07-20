# WakeAgain

잠든 디지털 프로젝트를 다시 깨우는 곳 — 홈페이지 + 사전 등록 폼.

| 항목 | 표기 |
|------|------|
| 브랜드 (사이트) | **WakeAgain** 영문만 (한글 음차 표기 안 함) |
| 목표 도메인 | **wakeagain.com** (아직 미결제·미등록 — 돈 생기면 등록) |
| **플랫폼 (필수)** | **웹 + Google Play + App Store**, 채널 간 **계정·데이터 호환** → [`PLATFORM.md`](./PLATFORM.md) |
| 임시 배포 | Railway + 기존 도메인 연결 가능 (선택) |
| 운영 | **코어랩스(CoreLabs)** |
| 문의 | **corelabs.studio@gmail.com** |
| 약관 · 개인정보 | `/legal/terms.html` · `/legal/privacy.html` |
| 카피라이트 | © 2026 CoreLabs. All rights reserved. |
| **관리자 검수** | `/admin/` · 헤더 `X-Admin-Key` · 환경변수 `ADMIN_SECRET` (**운영 필수 변경**. 로컬 개발 기본값만 문서 참고) |
| **관리자 전용 앱** | `/admin/install.html` · 공개 앱과 분리된 PWA (`WA Admin`) · **관리자 키 확인 후에만** 설치 UI 개방 · 사이트 메뉴 미노출 |

## 글로벌 준비

- KO/EN UI · 표시 통화 전환: [`docs/GLOBAL.md`](./docs/GLOBAL.md)
- 랜딩·앱 헤더 **KO | EN** 스위치
- 금액 표시 USD/EUR 가능 (DB·정산은 KRW)

## 실배포 전 10점 게이트

사업자·PG·SNS키·실유저·실배포를 **제외**한 만점 기준:

```powershell
cd C:\Users\hysoo\projects\WakeAgain
python _predeploy_gate.py
```

- 점수표: [`docs/PRE_DEPLOY_10.md`](./docs/PRE_DEPLOY_10.md)
- 통과: `PRE-DEPLOY SCORE: 10.0/10`
- 로컬 시크릿: 최초 실행 시 `.env` 자동 생성

## 로컬 실행

```powershell
cd C:\Users\hysoo\projects\WakeAgain
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8080
```

| URL | 용도 |
|-----|------|
| http://127.0.0.1:8080/ | 랜딩 |
| http://127.0.0.1:8080/app/ | **앱 셸** (가입·로그인·프로젝트) — 웹·스토어 동일 UI |
| http://127.0.0.1:8080/api/docs | API 문서 |
| http://127.0.0.1:8080/api/v1/config | 클라이언트 공통 설정 |

Play / App Store: `mobile/README.md` (Capacitor, 같은 API)

## Railway 배포

1. Account Token을 `C:\Users\hysoo\projects\RoadLog\.launch\railway.token` 에 한 줄 저장  
   (채팅에 붙여넣지 말 것 · https://railway.com/account/tokens )
2. 기존 RoadLog 서비스 root를 이 프로젝트로 바꾸거나 새 배포

도메인: 나중에 `wakeagain.com` 연결. 당장은 로컬 또는 Railway 기본 URL로 가능.

**나중 할 일:** `docs/나중_할일_BACKLOG.md`  
- 도메인·HTTPS 후 → SNS 로그인 연결  
- PG 연동 후 → 결제 링크·1시간 입금·2순위 자동 등

## 데이터

폼 접수는 `DATA_DIR/leads.jsonl` (기본 `./data/leads.jsonl`)
