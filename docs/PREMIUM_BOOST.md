# 프리미엄 매물 상위 노출 (scaffold)

**상태:** DB·목록 정렬·API 필드·헬퍼만 준비. **결제·구매 UI·유저 노출 상품 없음.**  
**플래그:** `PREMIUM_BOOST_ENABLED=0` (기본) — 켜도 상품 API는 아직 없음. 클라이언트가 `purchase_enabled` 보고 버튼 숨김.

## 이미 있는 것

| 항목 | 위치 |
|------|------|
| 컬럼 `boost_until`, `boost_tier`, `boost_product` | `wakeagain/db.py` init |
| 목록 정렬: 활성 부스트 우선 → `id DESC` | `listing_sort_sql()` · `GET /api/v1/projects` (공개 피드) |
| 매물 JSON `boost: { active, until, tier, product, purchase_enabled }` | `project_to_dict` |
| 설정 | `GET /api/v1/config` → `premium_boost` |
| 활성화 헬퍼 | `set_project_boost(conn, id, until_iso=..., tier=1, product="boost_7d")` |
| 해제 헬퍼 | `clear_project_boost(conn, id)` |

부스트 없는 매물만 있으면 정렬 결과는 **예전과 동일** (`id DESC`).

## 나중에 넣을 때 (구현 체크리스트)

1. **상품 정의** — 예: 7일 / 1슬롯 / 가격 (PG 상품 코드)
2. **결제** — PG 웹훅 성공 시  
   `set_project_boost(..., until_iso=now+7d, tier=1, product="boost_7d")`
3. **판매자 UI** — `config.premium_boost.purchase_enabled` 일 때만 「상위 노출」 버튼
4. **카드 UI** — `project.boost.active` 이면 작은 「추천」 뱃지 (품질 보증 문구 금지)
5. **만료** — 스케줄러 또는 lazy: `boost_until < now` 이면 정렬에서 자동 제외 (이미 CASE로 처리). 선택: 주기적으로 `clear_project_boost`
6. **어드민** — 수동 부여/회수 (프로모)
7. **약관** — 광고성 노출 상품 · 품질 보증 아님 고지

## 하지 말 것

- 검수 통과 = 프리미엄 검증 배지와 혼동
- cold start 전 유료 상위 강매
- AI 신뢰도 % 와 결합

## 수동 테스트 (개발)

```python
from datetime import datetime, timedelta, timezone
from wakeagain import db as database

database.init_db()
with database.db() as conn:
    until = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    database.set_project_boost(conn, PROJECT_ID, until_iso=until, tier=1, product="dev")
```

공개 `GET /api/v1/projects` 에서 해당 매물이 앞쪽에 오는지 확인.
