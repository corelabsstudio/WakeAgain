# WakeAgain SNS 로그인 설정

SNS 로그인은 **가입·로그인만** 간소화합니다.  
**만 14세 확인 · Lv2 실명/휴대폰 · Lv3 계좌**는 그대로 필요합니다.

> **사용자 확정 (2026-07-19):**  
> 키 발급·실연결은 **`wakeagain.com` 등 도메인 등록 + HTTPS 이후**에 한다.  
> 로컬 `127.0.0.1` 로 최종 붙이지 않음.  
> → 도메인 나오면 에이전트/작업 시 **「SNS 로그인 연결」** 을 상기할 것.

## 환경 변수

```powershell
# 콜백 기준 URL (배포 도메인으로 변경)
$env:OAUTH_PUBLIC_BASE = "http://127.0.0.1:8080"

# Google Cloud Console → OAuth 클라이언트 (웹)
$env:GOOGLE_CLIENT_ID = "....apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET = "...."

# GitHub → Settings → Developer settings → OAuth Apps
$env:GITHUB_CLIENT_ID = "...."
$env:GITHUB_CLIENT_SECRET = "...."

# Kakao Developers → 내 애플리케이션 → REST API 키
$env:KAKAO_CLIENT_ID = "...."          # REST API 키
$env:KAKAO_CLIENT_SECRET = "...."      # (선택) Client Secret 사용 시
```

값이 **없는** 제공자는 앱 UI에 버튼이 안 보입니다.  
설정한 것만 표시됩니다. (1개만 켜도 됨)

## Redirect URI (각 콘솔에 등록)

| 제공자 | Redirect URI |
|--------|----------------|
| Google | `{OAUTH_PUBLIC_BASE}/api/v1/auth/oauth/google/callback` |
| GitHub | `{OAUTH_PUBLIC_BASE}/api/v1/auth/oauth/github/callback` |
| Kakao  | `{OAUTH_PUBLIC_BASE}/api/v1/auth/oauth/kakao/callback` |

로컬 예: `http://127.0.0.1:8080/api/v1/auth/oauth/google/callback`

## API

| 경로 | 설명 |
|------|------|
| `GET /api/v1/config` → `oauth.providers` | 켜진 제공자 목록 |
| `GET /api/v1/auth/oauth/{provider}/start` | 제공자로 리다이렉트 |
| `GET /api/v1/auth/oauth/{provider}/callback` | 코드 교환 → JWT → `/app/?wa_token=...` |
| `PUT /api/v1/me/birth-date` | SNS 후 만 14세 생년월일 |

## 플로우

1. 사용자가 카카오/구글/깃허브 클릭  
2. 동의 → 콜백 → 계정 생성 또는 이메일 계정 연동  
3. 앱이 `wa_token` 저장  
4. **생년월일 없으면** 나이 확인 화면  
5. 이메일 미인증이면 인증 (SNS가 검증 이메일이면 보통 스킵)  
6. 올리기/입찰 전 **Lv2**, 성사 전 **Lv3**

## 보안 메모

- `APP_SECRET` / `JWT_SECRET` 운영에서 반드시 변경  
- OAuth state 는 JWT 서명 (CSRF 방지)  
- 클라이언트 시크릿은 서버 환경변수만 (프론트에 넣지 말 것)
