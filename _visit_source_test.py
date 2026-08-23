"""유입 경로(방문 집계 + 가입 귀속) 서버 시나리오 테스트.

`POST /api/v1/visit`가 referrer를 채널로 정규화하는지, URL 표식(utm)이 있을 때만
그게 우선하는지, 그리고 가입 시 표식이 없으면 첫 방문 referrer로 채널을 판정하는지
확인한다. 프런트 쪽 회귀는 `_visit_source_front_test.js`가 본다.

    python _visit_source_test.py
"""

import os
import tempfile

os.environ.setdefault("ADMIN_SECRET", "test-admin-secret")
_TMP = tempfile.mkdtemp(prefix="wa_visit_source_test_")
os.environ["DATA_DIR"] = _TMP

from fastapi.testclient import TestClient  # noqa: E402

from server import app  # noqa: E402
from wakeagain import db as database  # noqa: E402

database.init_db()

client = TestClient(app)
ADMIN = {"X-Admin-Key": os.environ["ADMIN_SECRET"]}
# 내부 유입(자기 사이트 리퍼러) 판정은 Host 헤더를 쓴다. TestClient 기본값은
# "testserver"라 실제 도메인으로 맞춰야 그 분기가 실제와 같게 동작한다.
HOST = {"host": "wakeagain.com"}
OK, FAIL = [], []
_seq = [0]


def check(name, cond, extra=""):
    (OK if cond else FAIL).append(name)
    print(("  ok  " if cond else " FAIL ") + name + (f"  — {extra}" if extra and not cond else ""))


def visit(referrer="", utm="", key=None):
    _seq[0] += 1
    key = key or f"visitor{_seq[0]:08d}"
    r = client.post(
        "/api/v1/visit",
        json={"visitor_key": key, "referrer": referrer, "utm_source": utm, "landing": "/"},
        headers=HOST,
    )
    assert r.status_code < 400, r.text
    return key


def sources():
    r = client.get("/api/v1/admin/visit-sources", headers=ADMIN)
    assert r.status_code < 400, r.text
    return {s["source"]: s["visits"] for s in r.json()["sources"]}


def register(email, source="", referrer=""):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123!",
            "display_name": email.split("@")[0][:12],
            "birth_date": "1991-08-20",
            "confirm_age_14": True,
            "signup_source": source,
            "signup_referrer": referrer,
            "signup_landing": "/",
        },
        headers=HOST,
    )
    assert r.status_code < 400, r.text
    with database.db() as conn:
        row = conn.execute(
            "SELECT signup_source, signup_referrer FROM users WHERE email = ?", (email,)
        ).fetchone()
    return dict(row)


# ── 방문 집계 ────────────────────────────────────────────────────────────
visit(referrer="https://www.google.com/")
check("구글 리퍼러 → Google", sources().get("Google") == 1, sources())

visit(referrer="")
check("리퍼러 없음 → Direct", sources().get("Direct") == 1, sources())

visit(referrer="https://news.ycombinator.com/item?id=1")
check("HN 리퍼러 → HackerNews", sources().get("HackerNews") == 1, sources())

visit(referrer="https://wakeagain.com/blog/")
check("자기 사이트 리퍼러 → Direct", sources().get("Direct") == 2, sources())

visit(referrer="https://www.google.com/", utm="github")
check("표식이 있으면 리퍼러보다 우선", sources().get("github") == 1, sources())

visit(referrer="https://example.invalid/x")
check("모르는 호스트는 호스트명 그대로", sources().get("example.invalid") == 1, sources())

# 같은 방문자가 그날 또 눌러도 채널은 한 번만 센다
before = sources()
k = visit(referrer="https://www.reddit.com/")
visit(referrer="https://www.google.com/", key=k)
after = sources()
check("같은 방문자 재요청은 중복 집계 안 함", after.get("Reddit") == 1 and after.get("Google") == before.get("Google"), after)

# 봇 UA는 집계에서 빠진다 (기존 동작 유지 확인)
before = sources()
client.post(
    "/api/v1/visit",
    json={"visitor_key": "botvisitor0001", "referrer": "https://www.google.com/"},
    headers={"User-Agent": "Googlebot/2.1", **HOST},
)
check("봇 UA는 집계 제외", sources() == before, sources())

# ── 가입 귀속 ────────────────────────────────────────────────────────────
row = register("ref-google@example.com", source="", referrer="https://www.google.com/")
check("가입: 표식 없으면 첫 방문 리퍼러로 판정", row["signup_source"] == "Google", row)

row = register("utm-github@example.com", source="github", referrer="https://www.google.com/")
check("가입: 표식이 있으면 그대로 유지", row["signup_source"] == "github", row)

row = register("no-touch@example.com", source="", referrer="")
check("가입: 아무것도 없으면 Direct", row["signup_source"] == "Direct", row)

row = register("own-ref@example.com", source="", referrer="https://wakeagain.com/sell.html")
check("가입: 자기 사이트 리퍼러는 Direct", row["signup_source"] == "Direct", row)

print(f"\n통과 {len(OK)} / 실패 {len(FAIL)}")
if FAIL:
    print("실패: " + ", ".join(FAIL))
    raise SystemExit(1)
