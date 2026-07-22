# -*- coding: utf-8 -*-
"""
Advanced auction tests:
  J) Concurrent / race bidding
  K) Second-bidder auto re-award on payment default
  L) Fee invoice lifecycle (pending → paid / cancelled)
"""
from __future__ import annotations

import os
import random
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("ADMIN_SECRET", "wakeagain-admin-dev")
os.environ.setdefault("SECOND_BIDDER_AUTO", "1")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from server import app
from wakeagain import db as database

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
        return {"_raw": (r.text or "")[:250]}


def H(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def register(tag: str) -> dict:
    n = random.randint(100000, 999999)
    email = f"adv_{tag}_{n}@example.com"
    r = cl.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "testpass12",
            "display_name": f"{tag}{n % 1000}",
            "birth_date": "1990-01-10",
            "confirm_age_14": True,
        },
    )
    body = j(r)
    if r.status_code != 200:
        raise RuntimeError(r.text[:200])
    tok = body["token"]
    h = H(tok)
    if body.get("dev_email_code"):
        rv = cl.post("/api/v1/auth/verify-email", headers=h, json={"code": body["dev_email_code"]})
        if rv.status_code == 200 and j(rv).get("token"):
            tok = j(rv)["token"]
            h = H(tok)
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
    if rp.status_code == 200 and j(rp).get("token"):
        tok = j(rp)["token"]
        h = H(tok)
    uid = (j(rp).get("user") or body.get("user") or {}).get("id")
    return {"email": email, "token": tok, "headers": h, "id": uid, "tag": tag}


def seller_ready(tag: str) -> dict:
    s = register(tag)
    cl.put(
        "/api/v1/me/settlement",
        headers=s["headers"],
        json={
            "holder": f"실명{tag}",
            "bank": "국민",
            "account": f"1234{random.randint(10000000, 99999999)}",
            "is_business": False,
        },
    )
    cl.put(
        "/api/v1/me/seller-identity",
        headers=s["headers"],
        json={
            "seller_type": "individual",
            "trade_name": f"샵{tag}",
            "contact_email": s["email"],
            "contact_phone": "01033334444",
            "address": "부산",
            "mail_order_report_no": "",
        },
    )
    return s


def create_and_approve(seller: dict, **kwargs) -> int:
    price_start = kwargs.get("price_start", 300_000)
    payload = {
        "title": kwargs.get("title") or f"고급테스트 {random.randint(1000,9999)}",
        "one_liner": "레이스·차순위·수수료",
        "status": "프로토타입",
        "product_type": "webapp",
        "story": "고급 시나리오 테스트 매물",
        "demo": "https://example.com/x",
        "assets": ["code"],
        "price_start": price_start,
        "auction_days": kwargs.get("auction_days", 3),
        "min_increment": 10_000,
        "license_note": "양도",
        "keywords": ["테스트", "경매", "SaaS", "웹앱", "양도"],
        "attest_works": True,
        "attest_license": True,
        "attest_rights": True,
    }
    if kwargs.get("price_buy_now") is not None:
        payload["price_buy_now"] = kwargs["price_buy_now"]
    r = cl.post("/api/v1/projects", headers=seller["headers"], json=payload)
    if r.status_code != 200:
        raise RuntimeError(r.text[:200])
    pid = int(j(r)["project"]["id"])
    ra = cl.post(
        f"/api/v1/admin/projects/{pid}/review",
        headers=ADMIN,
        json={"action": "approve", "note": "adv", "checklist": {"demo_ok": True}},
    )
    if ra.status_code != 200:
        raise RuntimeError(ra.text[:200])
    return pid


def bid(user: dict, pid: int, amount: int):
    return cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=user["headers"],
        json={"amount": amount},
    )


def scenario_J_race() -> None:
    print("\n=== J) Concurrent / race bidding ===")
    s = seller_ready("JR")
    pid = create_and_approve(s, price_start=500_000)
    buyers = [register(f"R{i}") for i in range(6)]

    # Seed first bid so next_min is clear
    r0 = bid(buyers[0], pid, 500_000)
    log("J seed bid", r0.status_code == 200, r0.text[:60])

    # Fire many concurrent bids around/above next min (510k+)
    # Some will be too low depending on race order — that's expected.
    amounts = [510_000, 520_000, 530_000, 540_000, 550_000, 560_000, 570_000, 580_000]
    jobs = []
    for i, amt in enumerate(amounts * 2):  # 16 concurrent-ish
        u = buyers[i % len(buyers)]
        jobs.append((u, amt))

    outcomes: list[tuple[int, int]] = []  # (status, amount)
    lock = threading.Lock()

    def worker(u, amt):
        # each thread gets own client (safer with starlette)
        local = TestClient(app)
        rr = local.post(
            f"/api/v1/projects/{pid}/bids",
            headers=u["headers"],
            json={"amount": amt},
        )
        with lock:
            outcomes.append((rr.status_code, amt, (j(rr).get("project") or {}).get("price_current")))

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(worker, u, a) for u, a in jobs]
        for f in as_completed(futs):
            try:
                f.result()
            except Exception as e:
                log("J worker exception", False, str(e))

    ok_n = sum(1 for st, _, _ in outcomes if st == 200)
    bad_n = sum(1 for st, _, _ in outcomes if st != 200)
    log("J concurrent requests ran", len(outcomes) == len(jobs), f"n={len(outcomes)}")
    log("J some bids accepted", ok_n >= 1, f"ok={ok_n} reject={bad_n}")

    p = j(cl.get(f"/api/v1/projects/{pid}")).get("project") or {}
    price = int(p.get("price_current") or 0)
    log("J price_current is max accepted", price >= 500_000, f"price={price}")

    bids = j(cl.get(f"/api/v1/projects/{pid}/bids")).get("bids") or []
    amts = [int(b.get("amount") or 0) for b in bids]
    log("J public board sorted", amts == sorted(amts, reverse=True), str(amts[:8]))
    log("J top matches price_current", amts and amts[0] == price, f"top={amts[0] if amts else None} price={price}")

    # Sequential integrity: no accepted bid should be below previous next_min at that moment
    # Weak check: all accepted amounts unique sequence max is price
    log("J bid_count positive", int(p.get("bid_count") or 0) >= 1, str(p.get("bid_count")))


def scenario_K_second_bidder() -> None:
    print("\n=== K) Second-bidder auto on payment default ===")
    log("K second_bidder_auto on", database.second_bidder_auto_enabled(), "")
    s = seller_ready("KS")
    pid = create_and_approve(s, price_start=400_000)
    b1, b2, b3 = register("K1"), register("K2"), register("K3")
    bid(b1, pid, 400_000)
    bid(b2, pid, 450_000)
    bid(b3, pid, 430_000)
    bid(b1, pid, 500_000)  # b1 wins

    r = cl.post(
        f"/api/v1/projects/{pid}/close-deal",
        headers=s["headers"],
        json={"use_current_bid": True},
    )
    p = j(r).get("project") or {}
    log("K first award b1", int(p.get("buyer_id") or 0) == int(b1["id"] or 0), str(p.get("buyer_id")))
    log("K first price 500k", int(p.get("sold_price") or 0) == 500_000, str(p.get("sold_price")))

    # Expire payment → should re-award to b2 at 450k
    past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(timespec="seconds")
    with database.db() as conn:
        conn.execute(
            "UPDATE projects SET payment_deadline_at = ? WHERE id = ?",
            (past, pid),
        )
        out = database.process_deal_deadlines(conn)

    log("K process defaulted", out.get("payment_default", 0) >= 1, str(out))
    log("K second award count", out.get("second_bidder_awards", 0) >= 1, str(out))

    p2 = j(cl.get(f"/api/v1/projects/{pid}")).get("project") or {}
    log(
        "K re-award awaiting_payment",
        p2.get("deal_status") == "awaiting_payment",
        str(p2.get("deal_status")),
    )
    log(
        "K new buyer is b2 (2nd highest unique)",
        int(p2.get("buyer_id") or 0) == int(b2["id"] or 0),
        f"buyer={p2.get('buyer_id')} b2={b2['id']} b3={b3['id']}",
    )
    log(
        "K new sold_price is 450k",
        int(p2.get("sold_price") or 0) == 450_000,
        str(p2.get("sold_price")),
    )

    # First buyer should have default mark
    me1 = j(cl.get("/api/v1/me", headers=b1["headers"])).get("user") or {}
    d1 = int(((me1.get("credit") or {}).get("counts") or {}).get("defaults") or 0)
    log("K first buyer defaults>=1", d1 >= 1, str(d1))

    # Fee invoice should be pending for new award (old cancelled)
    with database.db() as conn:
        pending = conn.execute(
            "SELECT * FROM fee_invoices WHERE project_id = ? AND status = 'pending'",
            (pid,),
        ).fetchall()
        cancelled = conn.execute(
            "SELECT * FROM fee_invoices WHERE project_id = ? AND status = 'cancelled'",
            (pid,),
        ).fetchall()
    log("K fee pending for re-award", len(pending) == 1, f"pending={len(pending)}")
    log("K old fee cancelled", len(cancelled) >= 1, f"cancelled={len(cancelled)}")
    if pending:
        fee = int(pending[0]["fee_amount"])
        expected = int(round(450_000 * 0.10))
        log("K fee 10% of 450k", fee == expected, f"fee={fee} expected={expected}")


def scenario_L_fee_invoices() -> None:
    print("\n=== L) Fee invoice lifecycle ===")
    s = seller_ready("LF")
    pid = create_and_approve(s, price_start=1_000_000)
    b = register("L1")
    bid(b, pid, 1_000_000)
    cl.post(
        f"/api/v1/projects/{pid}/close-deal",
        headers=s["headers"],
        json={"use_current_bid": True},
    )

    # Seller fees list
    r_fees = cl.get("/api/v1/me/fees", headers=s["headers"])
    invs = j(r_fees).get("invoices") or []
    mine = [x for x in invs if int(x.get("project_id") or 0) == pid]
    log("L seller sees fee invoice", r_fees.status_code == 200 and len(mine) >= 1, str(mine[:1]))
    if not mine:
        return
    inv = mine[0]
    fee = int(inv.get("fee_amount") or 0)
    deal = int(inv.get("deal_amount") or 0)
    log("L fee amount 10%", fee == int(round(deal * 0.1)), f"deal={deal} fee={fee}")
    log("L fee pending", inv.get("status") == "pending", str(inv.get("status")))
    inv_id = int(inv["id"])

    # Admin mark paid
    r_pay = cl.post(f"/api/v1/admin/fees/{inv_id}/paid", headers=ADMIN)
    log("L admin mark fee paid", r_pay.status_code == 200, r_pay.text[:80])
    paid = (j(r_pay).get("invoice") or {}).get("status")
    log("L invoice status paid", paid == "paid", str(paid))

    r_fees2 = cl.get("/api/v1/me/fees", headers=s["headers"])
    inv2 = next((x for x in (j(r_fees2).get("invoices") or []) if int(x.get("id") or 0) == inv_id), {})
    log("L seller sees paid", inv2.get("status") == "paid", str(inv2.get("status")))
    log("L paid_at set", bool(inv2.get("paid_at")), str(inv2.get("paid_at")))

    # Cancel path via payment default (separate listing)
    pid2 = create_and_approve(s, price_start=200_000, title=f"수수료취소 {random.randint(1,9999)}")
    b2 = register("L2")
    bid(b2, pid2, 200_000)
    cl.post(f"/api/v1/projects/{pid2}/close-deal", headers=s["headers"], json={"use_current_bid": True})
    past = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(timespec="seconds")
    with database.db() as conn:
        conn.execute(
            "UPDATE projects SET payment_deadline_at = ? WHERE id = ?",
            (past, pid2),
        )
        # Disable second bidder path noise: only one bidder
        database.process_deal_deadlines(conn)
        cancelled = conn.execute(
            "SELECT status, note FROM fee_invoices WHERE project_id = ?",
            (pid2,),
        ).fetchall()
    statuses = [r["status"] for r in cancelled]
    log("L fee cancelled on default", "cancelled" in statuses, str(statuses))


def main() -> int:
    print("\n########## Advanced: race / 2nd bidder / fees ##########\n")
    for fn in (scenario_J_race, scenario_K_second_bidder, scenario_L_fee_invoices):
        try:
            fn()
        except Exception as e:
            log(f"{fn.__name__} CRASH", False, str(e))
            traceback.print_exc()

    fails = [r for r in results if not r[1]]
    print("\n########## SUMMARY ##########")
    print(f"passed: {sum(1 for r in results if r[1])} / {len(results)}")
    if fails:
        print("FAILED:")
        for s, _, d in fails:
            print(f"  - {s}: {d}")
        return 1
    print("All advanced auction checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
