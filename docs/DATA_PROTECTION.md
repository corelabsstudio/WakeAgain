# WakeAgain — 회원 데이터 보호

**확정 2026-07-22**  
원칙: **회원·거래 데이터 유실 = 서비스 파산급 사고.**  
기능 배포보다 데이터 생존이 우선이다.

---

## 1. 저장 위치

| 환경 | 경로 | 비고 |
|------|------|------|
| 로컬 | `./data/wakeagain.db` | gitignore |
| 프로덕션 (Railway) | `/data/wakeagain.db` | **Volume 마운트 필수** · env `DATA_DIR=/data` |
| 백업 (1차) | `{DATA_DIR}/backups/wakeagain-*.db` | 같은 볼륨 안 (재배포에도 남음) |
| 백업 (2차) | S3 호환 오프사이트 (R2/S3/B2) | **볼륨 장애·프로젝트 삭제 대비** · `docs/OFFSITE_BACKUP_SETUP.md` |
| 메타 | `{DATA_DIR}/db_health.json` | peak/last 회원 수 · 마지막 백업 · 오프사이트 시각 |

볼륨이 없거나 `DATA_DIR`이 컨테이너 ephemeral 경로면 **배포마다 회원 전원 소멸**한다.  
오프사이트까지 켜야 “개망” 시나리오를 한 단계 더 막는다.

---

## 2. 자동 장치 (코드)

| 장치 | 동작 |
|------|------|
| 기동 백업 | `init_db` 후 `backup.startup_hooks()` — 스냅샷 + WAL + 급감 경고 |
| 주기 백업 | 옥션 스케줄러 틱에서 `maybe_periodic_backup()` (기본 1시간) |
| 오프사이트 | 로컬 스냅샷 직후 S3 PUT (R2 등) · 원격 로테이션 `OFFSITE_KEEP_REMOTE` |
| 로테이션 | 로컬 최근 ~48개 + 일별 14일 · 원격 기본 60개 |
| integrity | `PRAGMA integrity_check` |
| health | `GET /health` → `data.users`, `data.offsite`, `prod_warnings.offsite_backup_missing` |
| purge 잠금 | `ALLOW_DESTRUCTIVE_ADMIN` 없으면 전체 삭제 403 · 허용 시에도 **pre-purge 백업 후** 삭제 |
| 복구 | 원격 pull → 로컬 restore · 동일 잠금 |

구현: `wakeagain/backup.py` · `wakeagain/offsite_backup.py` · `server.py` · `scheduler.py` · `api.py`

---

## 3. 운영 체크리스트 (배포 전·후)

1. Railway 서비스에 **Volume** 이 `/data` 에 붙어 있는가  
2. 변수 `DATA_DIR=/data`  
3. `ALLOW_DESTRUCTIVE_ADMIN` **없거나 0** (평시)  
4. `APP_SECRET` / `JWT_SECRET` **재배포 시 회전 금지** (전원 로그아웃 + 정산 복호 영향)  
5. 배포 후 `GET /health` → `data.users` 가 예상과 같은가  
6. `/admin/` → **데이터·백업** 탭에서 백업 파일 목록 확인  

---

## 4. 사고 대응 (로그인 전원 실패 / 회원 0)

1. 패닉 금지. **새 가입으로 “덮어쓰지” 말 것** (peak 메타·백업이 진실)  
2. `/admin/` → 데이터·백업 · 또는 `GET /api/v1/admin/data/status`  
3. `backups/` 에 파일이 있으면:
   - 임시로 `ALLOW_DESTRUCTIVE_ADMIN=1`
   - `POST /api/v1/admin/data/restore`  
     body: `{ "backup_name": "wakeagain-....db", "confirm": "RESTORE_FROM_BACKUP" }`
   - 변수 다시 끄기 (`0` 또는 삭제)
4. 로컬에 없고 **오프사이트**에 있으면: **로컬로 받기** → restore  
5. 둘 다 없으면 Railway 지원·이전 볼륨 (최후)  
6. 원인 기록: 볼륨 미연결, 잘못된 `DATA_DIR`, purge, 시크릿 회전 혼동 등 

---

## 5. 금지

- 프로덕션에서 `purge-all` 을 “테스트용”으로 실행  
- 볼륨 없이 프로덕션 오픈  
- `DATA_DIR` 을 이미지 내부 경로로 두기  
- 배포 스크립트가 `APP_SECRET` 을 매번 새로 만들기 (`deploy_railway.py` 기본은 회전 안 함)  
- 회원 0 인 상태를 “정상 초기화”로 방치 (peak 가 있었다면 사고)  

---

## 6. 추가 권장 (다음 단계)

| 항목 | 이유 |
|------|------|
| ~~오프사이트 백업~~ | **완료** — R2/S3 연동 (`OFFSITE_S3_*`) · 설정 가이드 `OFFSITE_BACKUP_SETUP.md` |
| 일 1회 운영자 알림 (회원 수 델타) | 조용한 유실 조기 발견 |
| Postgres 이전 (규모 커지면) | 단일 SQLite 파일 한계·운영 도구 |

**최소 방어선:** 볼륨 + 로컬 스냅샷 + purge 잠금 + **오프사이트(R2)**.  
R2 키가 없으면 health에 `offsite_backup_missing` 경고가 뜬다.
)
