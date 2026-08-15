"""QA: 매물 등록 필수 필드 정책 (저장소 · 라이브 데모 · 마지막 활동일) E2E.

로컬 DB에 QA 계정/매물을 만든다. 끝나고 만든 행은 지운다.
"""
from __future__ import annotations

import os
import random

os.environ.setdefault("EMAIL_DEV_MODE", "1")

from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402
from wakeagain import db as database  # noqa: E402

c = TestClient(server.app)
EMAIL = f"qa_reqfield_{random.randint(100000, 999999)}@example.com"

r = c.post(
    "/api/v1/auth/register",
    json={
        "email": EMAIL,
        "password": "Test!2345",
        "display_name": "QA ReqField",
        "birth_date": "1990-01-01",
        "confirm_age_14": True,
        "country": "KR",
    },
)
assert r.status_code == 200, ("register", r.status_code, r.text[:300])
TOKEN = r.json()["token"]
H = {"Authorization": f"Bearer {TOKEN}"}
uid = int(r.json()["user"]["id"])

# 매물 등록은 이메일 인증(Lv1) 이상을 요구한다 — QA 계정을 직접 인증 처리
from wakeagain import db as _db_boot  # noqa: E402

with _db_boot.db() as _conn:
    _conn.execute(
        """
        UPDATE users SET
          email_verified = 1, phone_verified = 1, phone = '01000000000',
          real_name = 'QA 테스터',
          seller_type = 'individual', seller_trade_name = 'QA 테스터',
          seller_contact_email = ?, seller_contact_phone = '01000000000'
        WHERE id = ?
        """,
        (EMAIL, uid),
    )

# 스크린샷 1장은 항상 필수 → 업로드해서 확보
import io  # noqa: E402

png = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)
up = c.post(
    "/api/v1/uploads/demo",
    headers=H,
    files={"file": ("shot.png", io.BytesIO(png), "image/png")},
)
assert up.status_code == 200, ("upload", up.status_code, up.text[:300])
SHOT = up.json().get("url") or up.json().get("path")


def base(**over):
    body = {
        "title": "QA 필수필드",
        "one_liner": "저장소·데모·활동일 필수화 검증용 매물",
        "status": "beta",
        "product_type": "webapp",
        "story": "필수 필드 정책 검증을 위한 QA 매물입니다.",
        "demo": "",
        "demo_images": [SHOT],
        "features": ["예약을 받으면 알림이 갑니다", "손님 목록을 볼 수 있습니다"],
        "audience": "1인 카페 사장님",
        "works_now": "예약 등록과 목록 조회가 됩니다",
        "limits": "결제 미연동",
        "assets": ["code"],
        "acquisition": "made",
        "keywords": ["예약"],
        "price_start": 300000,
        "contact": EMAIL,
        "license_note": "MIT",
        "attest_works": True,
        "attest_license": True,
        "attest_rights": True,
        "attest_features": True,
        "attest_transfer": True,
        "attest_shots": True,
        # 정책 신규 3종
        "repo_url": "https://github.com/hysoo/wakeagain-qa",
        "is_private_repo": False,
        "live_url": "https://qa.example.com",
        "is_offline": False,
        "last_activity_at": "2026-03",
    }
    body.update(over)
    return body


def post(**over):
    return c.post("/api/v1/projects", headers=H, json=base(**over))


results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, extra: str = "") -> None:
    results.append((name, cond, extra))


created_ids: list[int] = []

# 1) 정상 등록
r = post()
ok = r.status_code == 200
check("정상 등록", ok, "" if ok else f"{r.status_code} {r.text[:200]}")
if ok:
    pid = r.json()["project"]["id"]
    created_ids.append(pid)
    p = r.json()["project"]
    check("repo_url 저장·응답", p.get("repo_url") == "https://github.com/hysoo/wakeagain-qa", str(p.get("repo_url")))
    check("live_url 저장·응답", p.get("live_url") == "https://qa.example.com", str(p.get("live_url")))
    check("last_activity_at 저장·응답", p.get("last_activity_at") == "2026-03", str(p.get("last_activity_at")))

# 2) 저장소 없으면 거부
r = post(repo_url="")
check("저장소 누락 → 400", r.status_code == 400 and r.json()["detail"]["code"] == "repo_url_invalid", f"{r.status_code}")

# 3) 비허용 호스트 거부
r = post(repo_url="https://example.com/a/b")
check("비허용 호스트 → 400", r.status_code == 400, f"{r.status_code}")

# 4) 비공개 레포 허용 (접근성 확인 안 함)
r = post(repo_url="https://github.com/hysoo/super-secret", is_private_repo=True)
ok = r.status_code == 200
check("비공개 레포 등록 허용", ok, "" if ok else r.text[:200])
if ok:
    created_ids.append(r.json()["project"]["id"])
    check("is_private_repo=True 반영", r.json()["project"].get("is_private_repo") is True)

# 5) 라이브 URL 없으면 거부
r = post(live_url="")
check("데모 URL 누락 → 400", r.status_code == 400 and r.json()["detail"]["code"] == "live_url_invalid", f"{r.status_code}")

# 6) 서비스 종료 매물은 데모 URL 없이도 등록 가능 (대안 경로)
r = post(live_url="", is_offline=True)
ok = r.status_code == 200
check("서비스 종료 매물 등록 허용", ok, "" if ok else r.text[:200])
if ok:
    created_ids.append(r.json()["project"]["id"])
    check("is_offline=True 반영", r.json()["project"].get("is_offline") is True)

# 7) 마지막 활동일 검증
r = post(last_activity_at="")
check("활동일 누락 → 400", r.status_code == 400, f"{r.status_code}")
r = post(last_activity_at="2027-01")
check("미래 활동일 → 400", r.status_code == 400, f"{r.status_code}")
r = post(last_activity_at="2026/03")
check("잘못된 형식 → 400", r.status_code == 400, f"{r.status_code}")

# 7.5) 정책 이전 매물 보완 경로: PUT /projects/{id}/verification
#      라이브 매물은 relist가 막히므로 이 경로가 없으면 기존 판매자는 정책을 지킬 수 없다.
r = post()
if r.status_code == 200:
    pid = r.json()["project"]["id"]
    created_ids.append(pid)
    # 정책 이전 상태로 되돌려 놓고(빈 값) 보완이 되는지 본다
    with database.db() as conn:
        conn.execute(
            "UPDATE projects SET repo_url=NULL, live_url=NULL, last_activity_at=NULL,"
            " is_private_repo=0, is_offline=0, bid_count=0 WHERE id=?",
            (pid,),
        )
    v = c.put(
        f"/api/v1/projects/{pid}/verification",
        headers=H,
        json={
            "repo_url": "github.com/corelabsstudio/RoadLog",
            "is_private_repo": False,
            "live_url": "https://roadlog.co.kr",
            "last_activity_at": "2026-08",
        },
    )
    ok = v.status_code == 200
    check("보완 엔드포인트 200", ok, "" if ok else f"{v.status_code} {v.text[:200]}")
    if ok:
        p = v.json()["project"]
        check("보완 후 repo_url 반영", p.get("repo_url") == "https://github.com/corelabsstudio/RoadLog", str(p.get("repo_url")))
        check("보완 후 활동일 반영", p.get("last_activity_at") == "2026-08", str(p.get("last_activity_at")))

    # 입찰이 있으면 기존 링크 교체 금지
    with database.db() as conn:
        conn.execute("UPDATE projects SET bid_count=3 WHERE id=?", (pid,))
    v2 = c.put(
        f"/api/v1/projects/{pid}/verification",
        headers=H,
        json={"repo_url": "https://github.com/corelabsstudio/OtherRepo"},
    )
    check(
        "입찰 후 링크 교체 → 400",
        v2.status_code == 400 and v2.json()["detail"]["code"] == "locked_after_bid",
        f"{v2.status_code}",
    )
    # 입찰이 있어도 빈 항목 채우기는 허용
    with database.db() as conn:
        conn.execute("UPDATE projects SET last_activity_at=NULL WHERE id=?", (pid,))
    v3 = c.put(
        f"/api/v1/projects/{pid}/verification",
        headers=H,
        json={"last_activity_at": "2026-07"},
    )
    check("입찰 후 빈 항목 채우기 허용", v3.status_code == 200, f"{v3.status_code} {v3.text[:150]}")

    # 남의 매물은 거부
    v4 = c.put(f"/api/v1/projects/{pid}/verification", json={"last_activity_at": "2026-07"})
    check("비로그인 → 401/403", v4.status_code in (401, 403), f"{v4.status_code}")
else:
    check("보완 엔드포인트 200", False, "선행 등록 실패")

# 8) 기존 매물(정책 이전)은 그대로 조회되어야 한다 — 빈 값으로 노출
with database.db() as conn:
    old = conn.execute(
        "SELECT id FROM projects WHERE repo_url IS NULL AND listing_status='approved' LIMIT 1"
    ).fetchone()
if old:
    r = c.get(f"/api/v1/projects/{int(old['id'])}")
    ok = r.status_code == 200
    p = r.json().get("project") if ok else {}
    check(
        "정책 이전 매물 조회 정상 + 빈 값",
        ok and p.get("repo_url") == "" and p.get("last_activity_at") == "",
        f"{r.status_code}",
    )
else:
    check("정책 이전 매물 조회 정상 + 빈 값", True, "(대상 없음 — skip)")

# 정리
with database.db() as conn:
    for pid in created_ids:
        conn.execute("DELETE FROM projects WHERE id = ?", (pid,))
    conn.execute("DELETE FROM users WHERE id = ?", (uid,))

print()
fails = 0
for name, ok, extra in results:
    print(("  PASS  " if ok else "  FAIL  ") + name + ((" | " + extra) if extra and not ok else ""))
    if not ok:
        fails += 1
print(f"\n{len(results) - fails}/{len(results)} passed")
raise SystemExit(1 if fails else 0)
