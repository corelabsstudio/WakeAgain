# 오프사이트 백업 설정 (S3 / Cloudflare R2)

회원 DB를 Railway 볼륨 **밖**에도 복사한다.  
볼륨이 날아가도 원격에서 내려받아 복구할 수 있다.

**권장: Cloudflare R2** (무료 티어 · 이그레스 저렴 · S3 호환)

---

## 1. Cloudflare R2 버킷 만들기 (5분)

1. https://dash.cloudflare.com → **R2 Object Storage**
2. **Create bucket**  
   - 이름 예: `wakeagain-backups`  
   - 위치: 아무거나 (Automatic OK)
3. **Manage R2 API Tokens** → **Create API token**  
   - Permission: **Object Read & Write** (해당 버킷만)  
   - TTL: 무제한 또는 충분히 길게  
4. 발급 직후 저장:
   - Access Key ID  
   - Secret Access Key  
   - Endpoint: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`  
     (R2 개요 페이지에 Account ID / S3 API 엔드포인트 표시)

---

## 2. Railway 환경변수

서비스 **wakeagain** → Variables:

| 변수 | 값 예시 |
|------|---------|
| `OFFSITE_BACKUP_ENABLED` | `1` |
| `OFFSITE_S3_ENDPOINT` | `https://xxxxxxxx.r2.cloudflarestorage.com` |
| `OFFSITE_S3_BUCKET` | `wakeagain-backups` |
| `OFFSITE_S3_ACCESS_KEY` | (토큰 Access Key ID) |
| `OFFSITE_S3_SECRET_KEY` | (토큰 Secret) |
| `OFFSITE_S3_REGION` | `auto` |
| `OFFSITE_S3_PREFIX` | `wakeagain/` |
| `OFFSITE_S3_FORCE_PATH_STYLE` | `1` |
| `OFFSITE_KEEP_REMOTE` | `60` |

CLI 예:

```powershell
cd C:\Users\hysoo\projects\WakeAgain
railway variables --set "OFFSITE_BACKUP_ENABLED=1" `
  --set "OFFSITE_S3_ENDPOINT=https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com" `
  --set "OFFSITE_S3_BUCKET=wakeagain-backups" `
  --set "OFFSITE_S3_ACCESS_KEY=..." `
  --set "OFFSITE_S3_SECRET_KEY=..." `
  --set "OFFSITE_S3_REGION=auto" `
  --set "OFFSITE_S3_PREFIX=wakeagain/" `
  --set "OFFSITE_S3_FORCE_PATH_STYLE=1" `
  --set "OFFSITE_KEEP_REMOTE=60" `
  --service wakeagain
```

변수 저장 후 **재배포 또는 재시작** 한 번.

---

## 3. 동작 확인

1. `GET https://wakeagain.com/health`  
   - `data.offsite.configured: true`  
   - `prod_warnings.offsite_backup_missing` 없어야 함
2. `/admin/` → **데이터·백업**  
   - 오프사이트 **ON**  
   - **지금 백업(+오프사이트)** 클릭  
   - 원격 목록에 `wakeagain/…/wakeagain-….db` 보이면 성공
3. Cloudflare R2 콘솔에서 객체 파일 확인

---

## 4. 복구 순서 (볼륨 날아갔을 때)

1. 오프사이트 설정이 살아 있는지 확인 (같은 키로 새 서비스에도 가능)
2. `/admin/` → 원격 백업 **로컬로 받기**
3. 임시 `ALLOW_DESTRUCTIVE_ADMIN=1`
4. 로컬 파일명으로 **복구** (`confirm=RESTORE_FROM_BACKUP`)
5. `ALLOW_DESTRUCTIVE_ADMIN` 다시 끄기

API:

```http
POST /api/v1/admin/data/offsite-pull
{ "object_key": "wakeagain/2026/07/22/wakeagain-....db" }

POST /api/v1/admin/data/restore
{ "backup_name": "wakeagain-....db", "confirm": "RESTORE_FROM_BACKUP" }
```

---

## 5. AWS S3 / Backblaze B2

같은 변수로 동작한다.

| 제공자 | ENDPOINT | REGION | PATH_STYLE |
|--------|----------|--------|------------|
| AWS S3 | (비우지 말고 리전 엔드포인트) `https://s3.ap-northeast-2.amazonaws.com` | `ap-northeast-2` | `0` (가상 호스트) 또는 `1` |
| B2 | `https://s3.<region>.backblazeb2.com` | 해당 리전 | `1` |
| R2 | `https://<acct>.r2.cloudflarestorage.com` | `auto` | `1` |

---

## 6. 보안

- 토큰은 **버킷 전용** Read/Write 최소 권한  
- 버킷 **공개 금지** (private)  
- Secret은 git/채팅에 올리지 말 것  
- 키 유출 시 즉시 R2 토큰 폐기·재발급  

---

구현: `wakeagain/offsite_backup.py` · 로컬 스냅샷 직후 자동 업로드 (`wakeagain/backup.py`)
