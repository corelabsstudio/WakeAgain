# WakeAgain Mobile — Google Play · Apple App Store

웹 앱 셸(`public/app`) + 공통 API(`/api/v1`)를 **Capacitor**로 감쌉니다.  
**같은 계정·같은 데이터**를 웹과 공유합니다.

| 스토어 | 패키지 ID | 비고 |
|--------|-----------|------|
| Google Play | `com.corelabs.wakeagain` | Windows에서 Android Studio 빌드 가능 |
| Apple App Store | `com.corelabs.wakeagain` | **macOS + Xcode 필수** |

---

## 1. 사전 요구

- Node.js 18+
- **Android:** [Android Studio](https://developer.android.com/studio) (SDK · 에뮬레이터)
- **iOS:** macOS · Xcode 15+ · Apple Developer 계정
- 백엔드: 로컬 또는 **HTTPS** 배포된 WakeAgain API

```powershell
cd C:\Users\hysoo\projects\WakeAgain\mobile
npm install
```

---

## 2. 최초 1회 — 네이티브 프로젝트 생성

```powershell
cd C:\Users\hysoo\projects\WakeAgain\mobile
npm run add:android
# macOS only:
# npm run add:ios
```

생성물: `mobile/android/`, `mobile/ios/` (git에 포함해도 됨)

---

## 3. 개발 (에뮬레이터 ↔ PC API)

**터미널 1 — API**

```powershell
cd C:\Users\hysoo\projects\WakeAgain
python -m uvicorn server:app --host 0.0.0.0 --port 8080
```

**터미널 2 — 앱**

```powershell
cd C:\Users\hysoo\projects\WakeAgain\mobile
# Android 에뮬레이터 → 호스트 PC
$env:WAKEAGAIN_API_BASE = "http://10.0.2.2:8080"
npm run android
```

실기기(같은 Wi‑Fi):

```powershell
$env:WAKEAGAIN_API_BASE = "http://192.168.x.x:8080"
npm run android
```

Android Studio에서 **Run** ▶

---

## 4. 스토어 제출 빌드

### 공통

1. API를 **HTTPS** 도메인에 배포 (예: Railway + 커스텀 도메인)
2. CORS / `ALLOWED_ORIGINS`에 앱 스킴 허용 (필요 시 `*`)
3. `JWT_SECRET` · `ADMIN_SECRET` · `EMAIL_DEV_MODE=0` 운영 설정

```powershell
cd mobile
$env:WAKEAGAIN_API_BASE = "https://your-api.example"
npm run build:store:prep
```

### Google Play

1. Android Studio에서 `android/` 열기  
2. **Build → Generate Signed Bundle / APK → Android App Bundle (.aab)**  
3. Play Console → 앱 만들기 → AAB 업로드  
4. 스토어 등록정보: 스크린샷, 개인정보처리방침 URL (`/legal/privacy.html`), 콘텐츠 등급  

### Apple App Store (Mac)

```bash
export WAKEAGAIN_API_BASE=https://your-api.example
npm run cap:sync
npm run ios
```

1. Xcode → Signing & Capabilities (Team)  
2. **Product → Archive → Distribute App**  
3. App Store Connect 메타데이터 · 심사용 계정  

---

## 5. 구조

| 경로 | 역할 |
|------|------|
| `../public` | 웹·앱 공통 UI (원본) |
| `www/` | Capacitor 패키징 복사본 (`npm run sync:www`) |
| `scripts/sync-www.js` | public → www + API 베이스 주입 |
| `scripts/native-bridge.js` | StatusBar · Splash · 뒤로가기 |
| `scripts/patch-android.js` | cleartext(개발) 네트워크 설정 |
| `capacitor.config.json` | appId · 스플래시 · 상태바 |
| `../server.py` + `../wakeagain/` | 공통 백엔드 |

---

## 6. 앱에서 쓰는 화면

- 진입: **앱 셸** `app/index.html` (가입·목록·올리기·정산 계좌)
- 매물 상세·진단·자랑: 동일 `public` 페이지 (상대 경로로 패키징)
- API: `window.WAKEAGAIN_API_BASE` + `js/api.js` JWT

---

## 6-b. 스토어 전 — 사이트에서 앱처럼 배포 (PWA)

Play 본인확인·스토어 심사가 늦어져도 사용자는 웹에서 설치할 수 있습니다.

| URL | 역할 |
|-----|------|
| `/get-app.html` | 설치 안내 (Android/iOS/PC) |
| `/app/` | 앱 셸 (standalone 가능) |
| `/manifest.webmanifest` · `/sw.js` | PWA |

**운영:** 사이트를 **HTTPS**로 배포한 뒤 홈의 「앱 설치」로 유입.

---

## 7. 체크리스트 (제출 전)

- [ ] `WAKEAGAIN_API_BASE` 가 `https://...` (로컬/10.0.2.2 아님)
- [ ] 스플래시·아이콘 (Android Studio / Xcode에서 교체 가능, 소스는 `public/assets/logo-mark.png`)
- [ ] 개인정보처리방침·이용약관 URL 접속 가능
- [ ] 테스트 계정 (심사) 준비
- [ ] 만 14세 미만 가입 차단 동작 확인
- [ ] 푸시 알림은 현재 미구현 (스토어 설명에 과장 금지)

---

## 8. 자주 쓰는 명령

```powershell
npm run sync:www          # 웹만 다시 복사
npm run cap:sync          # www + 네이티브 동기화
npm run android           # 동기화 후 Android Studio
npm run doctor            # Capacitor 환경 점검
```

문의: corelabs.studio@gmail.com · CoreLabs
