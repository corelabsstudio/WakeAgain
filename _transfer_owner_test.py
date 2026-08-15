"""관리자 매물 명의 이전 (`POST /admin/projects/{id}/transfer-owner`) 시나리오 테스트.

위탁 등록 매물(원 소유자 동의를 받고 코어랩스 계정으로 대신 올린 것)을 상대가 가입한 뒤
그 계정으로 넘기는 경로. 이력이 붙은 매물은 거부되는지까지 확인한다.
"""

import os
import tempfile

os.environ.setdefault("ADMIN_SECRET", "test-admin-secret")
_TMP = tempfile.mkdtemp(prefix="wa_transfer_test_")
os.environ["DATA_DIR"] = _TMP

from fastapi.testclient import TestClient  # noqa: E402

from server import app  # noqa: E402
from wakeagain import db as database  # noqa: E402

database.init_db()  # 임시 DATA_DIR이라 스키마를 직접 만든다 (라이브 DB와 격리)

client = TestClient(app)
ADMIN = {"X-Admin-Key": os.environ["ADMIN_SECRET"]}
OK = []
FAIL = []


def check(name: str, cond: bool, extra: str = "") -> None:
    (OK if cond else FAIL).append(name)
    print(("  ok  " if cond else " FAIL ") + name + (f"  — {extra}" if extra and not cond else ""))


def signup(email: str) -> int:
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123!",
            "display_name": email.split("@")[0][:12],
            "birth_date": "1991-08-20",
            "confirm_age_14": True,
        },
    )
    assert r.status_code < 400, r.text
    with database.db() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    return int(row["id"])


def make_project(owner_id: int, title: str) -> int:
    """API 등록 폼은 필수 필드가 많아, 이전 로직만 보기 위해 DB에 직접 최소 행을 만든다."""
    now = database._now()
    with database.db() as conn:
        cur = conn.execute(
            """
            INSERT INTO projects
              (owner_id, title, one_liner, status, story, demo, assets_json,
               price_start, price_current, listing_status, auction_status,
               created_at, updated_at)
            VALUES (?, ?, ?, 'prototype', ?, ?, '["code"]', 300000, 300000,
                    'approved', 'live', ?, ?)
            """,
            (owner_id, title, "one liner", "story", "demo", now, now),
        )
        return int(cur.lastrowid)


def transfer(pid: int, **body):
    return client.post(f"/api/v1/admin/projects/{pid}/transfer-owner", json=body, headers=ADMIN)


print("\n=== 관리자 매물 명의 이전 ===")

seller = signup("consign-seller@example.com")   # 코어랩스 역할 (대신 등록한 쪽)
owner = signup("real-owner@example.com")        # 원 소유자 (나중에 가입)
bidder = signup("bidder@example.com")

# 1. 인증 없이는 막힌다
pid = make_project(seller, "위탁매물 A")
r = client.post(f"/api/v1/admin/projects/{pid}/transfer-owner", json={"new_owner_id": owner})
check("관리자 키 없으면 거부", r.status_code in (401, 403), f"{r.status_code}")

# 2. 이메일로 이전 성공
r = transfer(pid, new_owner_email="real-owner@example.com", note="GitHub 이슈 동의 건")
check("이메일로 명의 이전 성공", r.status_code == 200, r.text[:200])
if r.status_code == 200:
    check("응답의 new_owner_id가 원 소유자", r.json()["new_owner_id"] == owner)
with database.db() as conn:
    row = conn.execute("SELECT owner_id FROM projects WHERE id = ?", (pid,)).fetchone()
check("DB owner_id 실제로 바뀜", int(row["owner_id"]) == owner, str(dict(row)))

# 3. 양쪽에 알림이 갔다
with database.db() as conn:
    n_new = conn.execute(
        "SELECT COUNT(*) c FROM notifications WHERE user_id = ?", (owner,)
    ).fetchone()["c"]
    n_old = conn.execute(
        "SELECT COUNT(*) c FROM notifications WHERE user_id = ?", (seller,)
    ).fetchone()["c"]
check("새 소유자에게 알림", int(n_new) >= 1)
check("이전 소유자에게 알림", int(n_old) >= 1)

# 4. 같은 계정으로 다시 이전 → 거부
r = transfer(pid, new_owner_id=owner)
check("같은 소유자로 재이전 거부", r.status_code == 400 and r.json()["detail"]["code"] == "same_owner", r.text[:200])

# 5. 대상 계정 없음 → 404 (상대가 아직 가입 안 한 경우)
pid2 = make_project(seller, "위탁매물 B")
r = transfer(pid2, new_owner_email="not-signed-up-yet@example.com")
check("미가입 계정 지정 시 404", r.status_code == 404 and r.json()["detail"]["code"] == "target_not_found", r.text[:200])

# 6. 대상 미지정 → 400
r = transfer(pid2)
check("대상 미지정 시 400", r.status_code == 400 and r.json()["detail"]["code"] == "target_required", r.text[:200])

# 7. 입찰이 있으면 거부
pid3 = make_project(seller, "위탁매물 C (입찰 있음)")
with database.db() as conn:
    conn.execute(
        "INSERT INTO bids (project_id, bidder_id, amount, created_at) VALUES (?,?,?,?)",
        (pid3, bidder, 310000, database._now()),
    )
    conn.execute("UPDATE projects SET bid_count = 1, bidder_count = 1 WHERE id = ?", (pid3,))
r = transfer(pid3, new_owner_id=owner)
check("입찰 있으면 거부", r.status_code == 400 and r.json()["detail"]["code"] == "bids_exist", r.text[:200])
with database.db() as conn:
    row = conn.execute("SELECT owner_id FROM projects WHERE id = ?", (pid3,)).fetchone()
check("거부된 매물은 소유자 그대로", int(row["owner_id"]) == seller)

# 8. 딜 진행 중이면 거부
pid4 = make_project(seller, "위탁매물 D (딜 진행)")
with database.db() as conn:
    conn.execute("UPDATE projects SET deal_status = 'awaiting_payment' WHERE id = ?", (pid4,))
r = transfer(pid4, new_owner_id=owner)
check("딜 진행 중이면 거부", r.status_code == 400 and r.json()["detail"]["code"] == "deal_in_progress", r.text[:200])

# 9. 이미 판매됐으면 거부
pid5 = make_project(seller, "위탁매물 E (판매완료)")
with database.db() as conn:
    conn.execute(
        "UPDATE projects SET auction_status = 'sold', sold_at = ?, buyer_id = ? WHERE id = ?",
        (database._now(), bidder, pid5),
    )
r = transfer(pid5, new_owner_id=owner)
check("판매된 매물 거부", r.status_code == 400 and r.json()["detail"]["code"] == "already_sold", r.text[:200])

# 10. 헬프티켓 이력 있으면 거부
pid6 = make_project(seller, "위탁매물 F (헬프티켓)")
with database.db() as conn:
    conn.execute(
        """INSERT INTO q_threads (project_id, buyer_id, seller_id, body, created_at)
           VALUES (?,?,?,?,?)""",
        (pid6, bidder, seller, "질문", database._now()),
    )
r = transfer(pid6, new_owner_id=owner)
check("헬프티켓 이력 있으면 거부", r.status_code == 400 and r.json()["detail"]["code"] == "help_tickets_exist", r.text[:200])

# 11. 수수료 청구서 있으면 거부
pid7 = make_project(seller, "위탁매물 G (수수료 청구서)")
with database.db() as conn:
    conn.execute(
        """INSERT INTO fee_invoices (project_id, seller_id, deal_amount, fee_amount, created_at)
           VALUES (?,?,?,?,?)""",
        (pid7, seller, 300000, 30000, database._now()),
    )
r = transfer(pid7, new_owner_id=owner)
check("수수료 청구서 있으면 거부", r.status_code == 400 and r.json()["detail"]["code"] == "fee_invoice_exists", r.text[:200])

# 12. 정지 계정으로는 못 넘긴다
pid8 = make_project(seller, "위탁매물 H")
with database.db() as conn:
    conn.execute(
        "UPDATE users SET is_suspended = 1, suspended_at = ? WHERE id = ?",
        (database._now(), owner),
    )
r = transfer(pid8, new_owner_id=owner)
check("정지 계정으로 이전 거부", r.status_code == 400 and r.json()["detail"]["code"] == "target_suspended", r.text[:200])

# 13. 없는 매물 → 404
r = transfer(999999, new_owner_id=owner)
check("없는 매물 404", r.status_code == 404)

print(f"\n결과: {len(OK)} 통과 / {len(FAIL)} 실패")
if FAIL:
    for f in FAIL:
        print("  실패:", f)
    raise SystemExit(1)
print("전부 통과")
