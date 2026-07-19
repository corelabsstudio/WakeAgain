"""Offline unit tests (no network). Exit 0 on pass."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from wakeagain import db as database
from wakeagain import pricing as price_policy
from wakeagain.envutil import ensure_local_env, load_dotenv

ensure_local_env()
load_dotenv()
database.init_db()

errors: list[str] = []


def ok(label: str, cond: bool, detail: str = "") -> None:
    print(f"  [{'OK' if cond else 'FAIL'}] {label}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        errors.append(f"{label}: {detail}")


print("== pricing ==")
ok("STATUS_PRICING", bool(price_policy.STATUS_PRICING))
ok("public_policy", bool(price_policy.public_policy()))

print("== auction expire ==")
with database.db() as conn:
    email = f"unit{random.randint(1000000, 9999999)}@example.com"
    conn.execute(
        """
        INSERT INTO users (email, password_hash, display_name, created_at)
        VALUES (?, 'x', 'Unit', ?)
        """,
        (email, database._now()),
    )
    uid = int(conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"])
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    title = f"expired-{random.randint(1000, 9999)}"
    conn.execute(
        """
        INSERT INTO projects (
          owner_id, title, one_liner, status, story, demo, assets_json,
          price_start, listing_status, auction_status, auction_ends_at, created_at, updated_at
        ) VALUES (?, ?, 'unit one', 'prototype', 'unit story ok', '', '[]',
          100000, 'approved', 'live', ?, ?, ?)
        """,
        (uid, title, past, database._now(), database._now()),
    )
    n = database.process_expired_auctions(conn)
    ok("closed at least one expired", n >= 1, str(n))
    row = conn.execute(
        "SELECT auction_status FROM projects WHERE title = ?",
        (title,),
    ).fetchone()
    ok(
        "status ended or sold",
        row is not None and (row["auction_status"] or "") in ("ended", "sold"),
        str(row["auction_status"] if row else None),
    )

print("== scheduler once ==")
from wakeagain import scheduler as sched

n2 = sched.run_once()
ok("run_once returns int", isinstance(n2, int))
st = sched.status()
ok("status has last_run_at", bool(st.get("last_run_at")))

print("== SUMMARY ==")
if errors:
    print("FAILED", len(errors))
    for e in errors:
        print(" -", e)
    raise SystemExit(1)
print("All unit checks passed.")
