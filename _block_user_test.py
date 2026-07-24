# -*- coding: utf-8 -*-
"""User↔user block: hide listings, reject bid/message, list/unblock."""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

os.environ.setdefault("ADMIN_SECRET", "wakeagain-admin-dev")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from server import app

cl = TestClient(app)
ADMIN = {"X-Admin-Key": os.environ.get("ADMIN_SECRET", "wakeagain-admin-dev")}
results: list[tuple[str, bool, str]] = []


def log(step: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'OK' if ok else 'FAIL'}] {step}" + (f" — {detail}" if detail else ""))
    results.append((step, ok, detail))


def j(r):
    try:
        return r.json()
    except Exception:
        return {"_raw": (r.text or "")[:300]}


def H(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register(tag: str, *, verify: bool = True, profile: bool = True) -> dict:
    n = random.randint(100000, 999999)
    email = f"blk_{tag}_{n}@example.com"
    password = "testpass12"
    r = cl.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": f"{tag}{n % 1000}",
            "birth_date": "1991-08-20",
            "confirm_age_14": True,
        },
    )
    body = j(r)
    if r.status_code != 200:
        raise RuntimeError(f"register {tag}: {r.text[:200]}")
    token = body["token"]
    h = H(token)
    if verify and body.get("dev_email_code"):
        rv = cl.post("/api/v1/auth/verify-email", headers=h, json={"code": body["dev_email_code"]})
        if rv.status_code == 200:
            if j(rv).get("token"):
                token = j(rv)["token"]
                h = H(token)
            body = j(rv)
    uid = (body.get("user") or {}).get("id")
    if profile and verify:
        rp = cl.put(
            "/api/v1/me/profile",
            headers=h,
            json={
                "real_name": f"실명{tag}",
                "phone": f"010{random.randint(10000000, 99999999)}",
                "role": "both",
                "display_name": f"{tag}User{n % 100}",
            },
        )
        if rp.status_code == 200:
            if j(rp).get("token"):
                token = j(rp)["token"]
                h = H(token)
            uid = (j(rp).get("user") or {}).get("id") or uid
    return {"email": email, "password": password, "token": token, "headers": h, "id": uid, "tag": tag}


def seller_ready(tag: str = "S") -> dict:
    s = register(tag)
    cl.put(
        "/api/v1/me/settlement",
        headers=s["headers"],
        json={
            "holder": f"실명{tag}",
            "bank": "카카오뱅크",
            "account": f"3333{random.randint(10000000, 99999999)}",
            "is_business": False,
        },
    )
    cl.put(
        "/api/v1/me/seller-identity",
        headers=s["headers"],
        json={
            "seller_type": "individual",
            "trade_name": f"판매{tag}",
            "contact_email": s["email"],
            "contact_phone": "01011112222",
            "address": "서울",
            "mail_order_report_no": "",
        },
    )
    return s


def approve(pid: int) -> None:
    r = cl.post(
        f"/api/v1/admin/projects/{pid}/review",
        headers=ADMIN,
        json={"action": "approve", "note": "block test", "checklist": {"demo_ok": True}},
    )
    if r.status_code != 200:
        raise RuntimeError(f"approve {pid}: {r.text[:200]}")


def create_listing(seller: dict, title: str) -> int:
    r = cl.post(
        "/api/v1/projects",
        headers=seller["headers"],
        json={
            "title": title,
            "one_liner": "차단 테스트 매물 한 줄",
            "status": "프로토타입",
            "product_type": "webapp",
            "story": "차단 기능 검증용 스토리입니다. 데모와 자산 설명을 충분히 적습니다.",
            "demo": "https://example.com/demo",
            "assets": ["code"],
            "price_start": 100_000,
            "price_buy_now": 500_000,
            "auction_days": 3,
            "min_increment": 10_000,
            "license_note": "MIT",
            "keywords": ["테스트", "차단", "SaaS"],
            "attest_works": True,
            "attest_license": True,
            "attest_rights": True,
        },
    )
    body = j(r)
    if r.status_code != 200:
        raise RuntimeError(f"create listing: {r.text[:200]}")
    pid = int((body.get("project") or body).get("id") or body.get("id"))
    approve(pid)
    return pid


def main() -> int:
    print("== User block suite ==")
    try:
        seller = seller_ready("BlkS")
        buyer = register("BlkB")
        other = register("BlkO")
        pid = create_listing(seller, f"차단테스트 {random.randint(1000,9999)}")
        log("setup listing", True, f"pid={pid} seller={seller['id']} buyer={buyer['id']}")
    except Exception as e:
        log("setup", False, str(e)[:200])
        print_summary()
        return 1

    # Public can see before block
    r = cl.get(f"/api/v1/projects/{pid}")
    log("public get before block", r.status_code == 200, str(r.status_code))

    r = cl.get("/api/v1/projects")
    ids = [p["id"] for p in (j(r).get("projects") or [])]
    log("public list contains listing", pid in ids, f"n={len(ids)}")

    # Self-block rejected
    r = cl.post(f"/api/v1/users/{buyer['id']}/block", headers=buyer["headers"])
    log("cannot block self", r.status_code == 400, str(r.status_code))

    # Block seller
    r = cl.post(f"/api/v1/users/{seller['id']}/block", headers=buyer["headers"])
    body = j(r)
    log("block seller", r.status_code == 200 and body.get("blocked") is True, str(body.get("message_ko") or r.text)[:120])

    # Idempotent second block
    r2 = cl.post(f"/api/v1/users/{seller['id']}/block", headers=buyer["headers"])
    log("block again already", r2.status_code == 200 and j(r2).get("already") is True, str(r2.status_code))

    # List blocks
    r = cl.get("/api/v1/me/blocks", headers=buyer["headers"])
    blocks = j(r).get("blocks") or []
    log(
        "list blocks has seller",
        r.status_code == 200 and any(int(b["blocked_user_id"]) == int(seller["id"]) for b in blocks),
        f"count={len(blocks)}",
    )

    # Buyer list hides seller listing
    r = cl.get("/api/v1/projects", headers=buyer["headers"])
    ids = [p["id"] for p in (j(r).get("projects") or [])]
    log("buyer list hides blocked", pid not in ids, f"ids_sample={ids[:5]}")

    # Buyer detail 404
    r = cl.get(f"/api/v1/projects/{pid}", headers=buyer["headers"])
    detail = j(r).get("detail")
    code = detail.get("code") if isinstance(detail, dict) else None
    log("buyer detail blocked 404", r.status_code == 404 and code == "blocked", f"{r.status_code} {code}")

    # Other user still sees
    r = cl.get(f"/api/v1/projects/{pid}", headers=other["headers"])
    log("other still sees listing", r.status_code == 200, str(r.status_code))

    # Bid rejected
    r = cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=buyer["headers"],
        json={"amount": 150000},
    )
    detail = j(r).get("detail")
    code = detail.get("code") if isinstance(detail, dict) else None
    log("bid rejected when blocked", r.status_code == 403 and code == "blocked", f"{r.status_code} {code}")

    # Buy-now rejected
    r = cl.post(f"/api/v1/projects/{pid}/buy-now", headers=buyer["headers"])
    detail = j(r).get("detail")
    code = detail.get("code") if isinstance(detail, dict) else None
    log("buy-now rejected when blocked", r.status_code == 403 and code == "blocked", f"{r.status_code} {code}")

    # Reverse: seller blocked buyer — seller also can't bid on buyer's listing if any.
    # Simpler: buyer blocked seller means seller trying to message on seller's own project is OK.
    # Message between pair: buyer messages seller project after block
    r = cl.post(
        f"/api/v1/projects/{pid}/messages",
        headers=buyer["headers"],
        json={"body": "hello after block"},
    )
    # May be 403 owner/bidders only OR blocked — either is fine if not 200
    log("message not ok when blocked", r.status_code != 200, str(r.status_code))

    # Unblock
    r = cl.delete(f"/api/v1/users/{seller['id']}/block", headers=buyer["headers"])
    log("unblock", r.status_code == 200 and j(r).get("blocked") is False, str(j(r).get("message_ko") or "")[:80])

    r = cl.get(f"/api/v1/projects/{pid}", headers=buyer["headers"])
    log("after unblock detail visible", r.status_code == 200, str(r.status_code))

    r = cl.get("/api/v1/projects", headers=buyer["headers"])
    ids = [p["id"] for p in (j(r).get("projects") or [])]
    log("after unblock list shows", pid in ids, f"n={len(ids)}")

    # Bid works after unblock
    r = cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=buyer["headers"],
        json={"amount": 150000},
    )
    log("bid ok after unblock", r.status_code == 200, str(r.status_code) + " " + (r.text or "")[:80])

    # Config exposes block_policy
    r = cl.get("/api/v1/config")
    bp = (j(r).get("trust_policy") or {}).get("block_policy") or {}
    log("config.block_policy", bool(bp.get("enabled")), str(bp.get("paths") or {})[:80])

    return print_summary()


def print_summary() -> int:
    fails = [x for x in results if not x[1]]
    print()
    print(f"== Result: {len(results) - len(fails)}/{len(results)} OK ==")
    for step, ok, detail in fails:
        print(f"  FAIL {step}: {detail}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
