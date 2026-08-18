"""위탁 등록(consignor) 필드 시나리오 테스트 — `POST /admin/projects/{id}/consignor`.

핵심: 위탁자가 **가입하지 않아도** 매물이 정상적으로 굴러가야 한다. owner_id는 운영
계정에 그대로 두고 실제 판매자는 데이터로만 기록한다. 명의 이전(transfer-owner)은
입찰이 붙으면 막히므로 이 경로는 그것에 의존하지 않는다.
"""

import os
import tempfile

os.environ.setdefault("ADMIN_SECRET", "test-admin-secret")
_TMP = tempfile.mkdtemp(prefix="wa_consignor_test_")
os.environ["DATA_DIR"] = _TMP

from fastapi.testclient import TestClient  # noqa: E402

from server import app  # noqa: E402
from wakeagain import db as database  # noqa: E402

database.init_db()

client = TestClient(app)
ADMIN = {"X-Admin-Key": os.environ["ADMIN_SECRET"]}
OK, FAIL = [], []


def check(name, cond, extra=""):
    (OK if cond else FAIL).append(name)
    print(("  ok  " if cond else " FAIL ") + name + (f"  — {extra}" if extra and not cond else ""))


def signup(email):
    r = client.post("/api/v1/auth/register", json={
        "email": email, "password": "TestPass123!", "display_name": email.split("@")[0][:12],
        "birth_date": "1991-08-20", "confirm_age_14": True})
    assert r.status_code < 400, r.text
    with database.db() as conn:
        return int(conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"])


def make_project(owner_id, title):
    now = database._now()
    with database.db() as conn:
        cur = conn.execute(
            """INSERT INTO projects
                 (owner_id, title, one_liner, status, story, demo, assets_json,
                  price_start, price_current, listing_status, auction_status,
                  created_at, updated_at)
               VALUES (?, ?, ?, 'prototype', ?, ?, '["code"]', 300000, 300000,
                       'approved', 'live', ?, ?)""",
            (owner_id, title, "one liner", "story", "demo", now, now))
        return int(cur.lastrowid)


def set_consignor(pid, **body):
    return client.post(f"/api/v1/admin/projects/{pid}/consignor", json=body, headers=ADMIN)


operator = signup("operator@example.com")
pid = make_project(operator, "abandoned side project")

# 1) 기본 상태 — 위탁 아님
with database.db() as conn:
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
d = database.project_to_dict(row)
check("기본값은 위탁 아님", d["is_consigned"] is False)

# 2) 위탁자 기록
r = set_consignor(pid,
                  consignor_name="seulhyi",
                  consignor_contact="3021062@example.com",
                  consignor_source_url="https://github.com/o/r/issues/131",
                  consignor_consent_quote="넵 그럼 대신 올려주셔도 좋습니다~")
check("위탁자 기록 200", r.status_code == 200, r.text)
body = r.json() if r.status_code == 200 else {}
check("is_consigned=True", body.get("is_consigned") is True, str(body))
check("동의 인용 저장", body.get("consignor", {}).get("consent_quote", "").startswith("넵"), str(body))
check("동의 시각 자동 기록", bool(body.get("consignor", {}).get("consent_at")), str(body))

# 3) owner_id는 안 바뀐다 (핵심)
with database.db() as conn:
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
check("owner_id 불변", int(row["owner_id"]) == operator, f'{row["owner_id"]} != {operator}')

# 4) 공개 응답엔 PII가 안 나간다 (핵심)
pub = database.project_to_dict(row)
check("공개: is_consigned 노출", pub["is_consigned"] is True)
check("공개: consignor 키 없음", "consignor" not in pub, str(pub.keys()))
check("공개: 연락처 문자열 미포함", "3021062@example.com" not in str(pub))
priv = database.project_to_dict(row, include_private=True)
check("비공개: 연락처 포함", priv["consignor"]["contact"] == "3021062@example.com", str(priv["consignor"]))

# 5) 부분 수정 — 안 보낸 필드는 유지
r = set_consignor(pid, consignor_payout_note="정산: 낙찰 후 이메일로 계좌 수령")
check("부분 수정 200", r.status_code == 200, r.text)
c = r.json().get("consignor", {})
check("미전송 필드 유지", c.get("name") == "seulhyi", str(c))
check("신규 필드 반영", "낙찰 후" in c.get("payout_note", ""), str(c))

# 6) "" 로 삭제
r = set_consignor(pid, consignor_payout_note="")
check('""로 삭제', r.json().get("consignor", {}).get("payout_note") == "", r.text)

# 7) 입찰이 붙어도 위탁 정보는 계속 수정 가능 (transfer-owner와 다른 점)
bidder = signup("bidder@example.com")
with database.db() as conn:
    conn.execute(
        "INSERT INTO bids (project_id, bidder_id, amount, created_at) VALUES (?,?,?,?)",
        (pid, bidder, 400000, database._now()))
    conn.execute("UPDATE projects SET bid_count = 1 WHERE id = ?", (pid,))
r = set_consignor(pid, consignor_payout_note="입찰 후에도 기록 가능해야 함")
check("입찰 후에도 위탁 정보 수정 가능", r.status_code == 200, r.text)
with database.db() as conn:
    blockers = database.project_transfer_blockers(conn, pid)
check("대조: 같은 상황에서 명의이전은 차단됨", "bids_exist" in blockers, str(blockers))

# 8) 잘못된 필드 거부
r = client.post(f"/api/v1/admin/projects/{pid}/consignor", json={"nope": "x"}, headers=ADMIN)
check("알 수 없는 필드 거부", r.status_code == 400, f"{r.status_code} {r.text}")

# 9) 없는 매물
r = set_consignor(999999, consignor_name="x")
check("없는 매물 404", r.status_code == 404, f"{r.status_code} {r.text}")

# 10) 인증 없으면 거부
r = client.post(f"/api/v1/admin/projects/{pid}/consignor", json={"consignor_name": "x"})
check("관리자 인증 필수", r.status_code in (401, 403), f"{r.status_code} {r.text}")

print(f"\n=== {len(OK)} passed, {len(FAIL)} failed ===")
if FAIL:
    print("실패:", FAIL)
raise SystemExit(1 if FAIL else 0)
