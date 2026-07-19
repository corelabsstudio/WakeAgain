# SNS 키 발급 가이드 (로컬 WakeAgain)

키는 **본인 계정으로 콘솔에서 직접** 만듭니다.  
에이전트/채팅에 **시크릿을 붙여넣지 마세요.** `.env`에만 저장하세요.

**추천 순서 (한국 유저 위주):** ① 카카오 → ② 구글 → ③ 깃허브  
**1개만** 먼저 켜도 버튼이 뜹니다.

---

## 공통: 로컬 Redirect URI (복붙)

| 제공자 | Redirect URI (로컬) |
|--------|---------------------|
| Google | `http://127.0.0.1:8080/api/v1/auth/oauth/google/callback` |
| GitHub | `http://127.0.0.1:8080/api/v1/auth/oauth/github/callback` |
| Kakao  | `http://127.0.0.1:8080/api/v1/auth/oauth/kakao/callback` |

> `localhost` 와 `127.0.0.1` 은 다릅니다. **우리 서버 기본은 127.0.0.1** 이라 URI도 127.0.0.1 로 맞추세요.

배포 시 `https://도메인` 으로 바꾸고, 콘솔 Redirect에도 **배포 URI를 추가**합니다.

---

## ① 카카오 (한국 · 가장 많이 씀)

1. 열기: https://developers.kakao.com/console/app  
2. **내 애플리케이션** → **애플리케이션 추가하기**  
   - 앱 이름: `WakeAgain`  
   - 사업자명: `코어랩스` (또는 개인)  
3. 만든 앱 클릭 → **앱 키**  
   - **REST API 키** 복사 → 이게 `KAKAO_CLIENT_ID`  
4. **플랫폼** → **Web** 등록  
   - 사이트 도메인: `http://127.0.0.1:8080`  
5. **카카오 로그인** → **활성화 ON**  
6. **Redirect URI** 등록:  
   `http://127.0.0.1:8080/api/v1/auth/oauth/kakao/callback`  
7. **동의 항목**  
   - 닉네임: 필수 또는 선택  
   - **카카오계정(이메일)**: 필수 권장 (없으면 가짜 이메일로 들어감)  
8. (선택) **보안** → Client Secret 사용 시  
   - 발급된 값 → `KAKAO_CLIENT_SECRET`  
   - 안 쓰면 비워 둬도 동작 (코드에서 secret 선택)

`.env` 예:

```env
OAUTH_PUBLIC_BASE=http://127.0.0.1:8080
KAKAO_CLIENT_ID=여기에_REST_API_키
# KAKAO_CLIENT_SECRET=쓰면_여기
```

---

## ② 구글

1. 열기: https://console.cloud.google.com/apis/credentials  
2. 상단 **프로젝트 선택** → **새 프로젝트**  
   - 이름: `WakeAgain`  
3. **OAuth 동의 화면**  
   - User Type: **External** (개인)  
   - 앱 이름: WakeAgain  
   - 지원 이메일: 본인  
   - 개발자 연락처: 본인  
   - 범위: `email`, `profile`, `openid` (기본으로 충분)  
   - 테스트 사용자: **본인 구글 계정 추가** (앱이 테스트 모드일 때 필수)  
4. **사용자 인증 정보** → **+ 만들기** → **OAuth 클라이언트 ID**  
   - 유형: **웹 애플리케이션**  
   - 이름: `WakeAgain Web`  
   - **승인된 자바스크립트 원본:** `http://127.0.0.1:8080`  
   - **승인된 리디렉션 URI:**  
     `http://127.0.0.1:8080/api/v1/auth/oauth/google/callback`  
5. 생성 후  
   - 클라이언트 ID → `GOOGLE_CLIENT_ID`  
   - 클라이언트 보안 비밀 → `GOOGLE_CLIENT_SECRET`

```env
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
```

---

## ③ 깃허브

1. 열기: https://github.com/settings/developers  
2. **OAuth Apps** → **New OAuth App**  
   - Application name: `WakeAgain`  
   - Homepage URL: `http://127.0.0.1:8080`  
   - Authorization callback URL:  
     `http://127.0.0.1:8080/api/v1/auth/oauth/github/callback`  
3. **Register application**  
4. **Client ID** 복사 → `GITHUB_CLIENT_ID`  
5. **Generate a new client secret** → `GITHUB_CLIENT_SECRET`  
   (한 번만 보이니 바로 `.env`에 저장)

```env
GITHUB_CLIENT_ID=Iv1.xxxxx
GITHUB_CLIENT_SECRET=xxxxx
```

---

## 키 넣은 뒤 서버 실행 (PowerShell)

프로젝트 폴더에서:

```powershell
cd C:\Users\hysoo\projects\WakeAgain

# .env.example 을 복사해 값을 채운 뒤:
# copy .env.example .env

# .env 로드 (간단 버전)
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
  $k,$v = $_.Split('=',2)
  [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim(), 'Process')
}

python -m pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8080
```

확인:

1. http://127.0.0.1:8080/api/v1/config → `"oauth": { "providers": [ ... ] }`  
2. http://127.0.0.1:8080/app/ → SNS 버튼 표시  
3. 버튼 클릭 → 동의 → 돌아오면 로그인 + (필요 시) 생년월일

---

## 자주 막히는 것

| 증상 | 원인 |
|------|------|
| 버튼이 안 보임 | 해당 `*_CLIENT_ID` 가 비어 있음 / 서버 재시작 안 함 |
| redirect_uri_mismatch | 콘솔 URI ≠ 코드 URI (127.0.0.1 vs localhost) |
| Google access_denied / 앱 미확인 | 동의 화면 테스트 사용자에 본인 이메일 추가 |
| Kakao 이메일 없음 | 동의 항목에서 이메일 미설정·사용자가 거부 |
| 콜백 404 | 서버가 8080이 아니거나 `OAUTH_PUBLIC_BASE` 불일치 |

---

## 보안

- `.env` 는 git에 올리지 말 것 (`.gitignore` 확인)  
- 채팅/스크린샷에 **Client Secret** 올리지 말 것  
- 유출 의심 시 콘솔에서 시크릿 **재발급**
