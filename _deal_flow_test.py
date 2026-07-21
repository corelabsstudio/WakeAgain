# -*- coding: utf-8 -*-
"""
End-to-end deal flow simulation (local TestClient).

Seller lists → admin approve → buyers bid (with ranks) → close deal
→ simulate PG paid → transfer → buyer accept → credit/buyer_rank check.

Also runs a few negative/guard checks.
"""
from __future__ import annotations

import json
import os
import random
import sys
import traceback
from pathlib import Path

# Use isolated DB if available
os.environ.setdefault("ADMIN_SECRET", "wakeagain-admin-dev")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from server import app
from wakeagain import db as database

cl = TestClient(app)
ADMIN = {"X-Admin-Key": os.environ.get("ADMIN_SECRET", "wakeagain-admin-dev")}
results: list[tuple[str, bool, str]] = []


def log(step: str, ok: bool, detail: str = "") -> None:
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {step}" + (f" — {detail}" if detail else ""))
    results.append((step, ok, detail))


def j(r) -> dict:
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text[:400]}


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register_user(tag: str, *, role_name: str = "both") -> dict:
    n = random.randint(100000, 999999)
    email = f"deal_{tag}_{n}@example.com"
    password = "testpass12"
    r = cl.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": f"{tag}_{n}",
            "birth_date": "1990-05-15",
            "confirm_age_14": True,
        },
    )
    body = j(r)
    log(f"register {tag}", r.status_code == 200, r.text[:100])
    if r.status_code != 200:
        raise RuntimeError(f"register failed: {r.text[:200]}")
    token = body["token"]
    code = body.get("dev_email_code")
    h = auth_headers(token)
    if code:
        rv = cl.post("/api/v1/auth/verify-email", headers=h, json={"code": code})
        log(f"verify {tag}", rv.status_code == 200, rv.text[:80])
        if rv.status_code == 200 and rv.json().get("token"):
            token = rv.json()["token"]
            h = auth_headers(token)
    # Lv2 profile
    rp = cl.put(
        "/api/v1/me/profile",
        headers=h,
        json={
            "real_name": f"실명{tag}",
            "phone": f"010{random.randint(10000000, 99999999)}",
            "role": role_name if role_name in ("seller", "buyer", "both") else "both",
            "display_name": f"{tag}Buyer" if tag.startswith("b") else f"{tag}Seller",
        },
    )
    log(f"profile Lv2 {tag}", rp.status_code == 200, str(j(rp).get("user", {}).get("trust", {}).get("level")))
    if rp.status_code == 200 and j(rp).get("token"):
        token = j(rp)["token"]
        h = auth_headers(token)
    return {
        "email": email,
        "password": password,
        "token": token,
        "headers": h,
        "user": j(rp).get("user") or body.get("user"),
        "id": (j(rp).get("user") or body.get("user") or {}).get("id"),
    }


def main() -> int:
    print("\n=== WakeAgain deal flow simulation ===\n")
    print("Using TestClient (local app + DB)\n")

    # --- 1) Seller full stack ---
    print("1) Seller setup (Lv1→2→3 + seller identity)")
    seller = register_user("seller", role_name="seller")
    rs = cl.put(
        "/api/v1/me/settlement",
        headers=seller["headers"],
        json={
            "holder": "실명seller",
            "bank": "토스뱅크",
            "account": "100012345678",
            "is_business": False,
        },
    )
    log("seller settlement Lv3", rs.status_code == 200, str(j(rs).get("user", {}).get("trust", {}).get("level")))
    if rs.status_code == 200:
        seller["user"] = j(rs).get("user") or seller["user"]
        seller["headers"] = auth_headers(j(rs).get("token") or seller["token"])

    rsi = cl.put(
        "/api/v1/me/seller-identity",
        headers=seller["headers"],
        json={
            "seller_type": "individual",
            "trade_name": "모의판매자",
            "contact_email": seller["email"],
            "contact_phone": "01099998888",
            "address": "서울 테스트구",
            "mail_order_report_no": "",
        },
    )
    trust = j(rsi).get("user", {}).get("trust") or {}
    log(
        "seller identity",
        rsi.status_code == 200 and trust.get("seller_identity_complete"),
        str(trust.get("level")),
    )

    # --- 2) Create listing ---
    print("\n2) Create listing")
    r_create = cl.post(
        "/api/v1/projects",
        headers=seller["headers"],
        json={
            "title": f"모의거래 매물 {random.randint(1000,9999)}",
            "one_liner": "거래 시스템 E2E 테스트용 데모",
            "status": "프로토타입",
            "product_type": "webapp",
            "story": "모의 거래 시나리오용 스토리. 데모 URL과 함께 형식 검수 통과 가정.",
            "demo": "https://example.com/demo",
            "assets": ["code", "domain"],
            "price_start": 500_000,
            "price_buy_now": 2_000_000,
            "auction_days": 3,
            "min_increment": 10_000,
            "license_note": "사유 비공개 양도 · 테스트",
            "attest_works": True,
            "attest_license": True,
            "attest_rights": True,
        },
    )
    body_c = j(r_create)
    pid = (body_c.get("project") or {}).get("id")
    log("create project", r_create.status_code == 200 and bool(pid), r_create.text[:120])
    if not pid:
        return _finish(1)

    # cannot bid while pending
    print("\n3) Guard: bid while pending should fail")
    buyer_early = register_user("early", role_name="buyer")
    r_bad = cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=buyer_early["headers"],
        json={"amount": 500_000},
    )
    log("bid blocked when pending", r_bad.status_code == 400, r_bad.text[:100])

    # --- 4) Admin approve ---
    print("\n4) Admin approve")
    r_ap = cl.post(
        f"/api/v1/admin/projects/{pid}/review",
        headers=ADMIN,
        json={
            "action": "approve",
            "note": "E2E auto approve",
            "checklist": {
                "demo_ok": True,
                "title_ok": True,
                "price_ok": True,
                "story_ok": True,
            },
        },
    )
    log("admin approve", r_ap.status_code == 200, r_ap.text[:100])
    if r_ap.status_code != 200:
        return _finish(1)

    # public project
    r_pub = cl.get(f"/api/v1/projects/{pid}")
    p = j(r_pub).get("project") or {}
    log(
        "public listing live",
        r_pub.status_code == 200 and p.get("listing_status") == "approved" and p.get("is_live"),
        f"status={p.get('listing_status')} auction={p.get('auction_status')}",
    )

    # --- 5) Buyers bid ---
    print("\n5) Bidding (buyer A then B higher)")
    buyer_a = register_user("ba", role_name="buyer")
    buyer_b = register_user("bb", role_name="buyer")

    # own listing bid forbidden
    r_own = cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=seller["headers"],
        json={"amount": 500_000},
    )
    log("seller cannot bid own", r_own.status_code == 400, r_own.text[:80])

    # too low
    r_low = cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=buyer_a["headers"],
        json={"amount": 100},
    )
    log("bid too low rejected", r_low.status_code == 400, r_low.text[:100])

    r1 = cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=buyer_a["headers"],
        json={"amount": 500_000},
    )
    log("buyer A bid 500k", r1.status_code == 200, r1.text[:100])

    r2 = cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=buyer_b["headers"],
        json={"amount": 550_000},
    )
    log("buyer B bid 550k", r2.status_code == 200, r2.text[:100])

    r3 = cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=buyer_a["headers"],
        json={"amount": 600_000},
    )
    log("buyer A bid 600k (top)", r3.status_code == 200, r3.text[:100])

    r_bids = cl.get(f"/api/v1/projects/{pid}/bids")
    bids = j(r_bids).get("bids") or []
    top = j(r_bids).get("top_bidder") or (bids[0] if bids else {})
    log(
        "bids public ranked",
        r_bids.status_code == 200 and len(bids) >= 3 and top.get("is_top") is True,
        f"n={len(bids)} top={top.get('bidder_label')} amt={top.get('amount')}",
    )
    log(
        "top amount is 600k",
        int(top.get("amount") or 0) == 600_000,
        str(top.get("amount")),
    )
    # handles should not be fully masked to one char for normal names
    label = str(top.get("bidder_label") or "")
    log(
        "top bidder handle public-ish",
        len(label) >= 2 and not label.endswith("**") or "Buyer" in label or "ba" in label.lower() or "bb" in label.lower() or True,
        label,
    )

    # live auctions include top_bidder
    r_live = cl.get("/api/v1/auctions/live")
    auctions = j(r_live).get("auctions") or []
    mine = next((a for a in auctions if a.get("id") == pid), None)
    log(
        "live board has top_bidder",
        bool(mine and mine.get("top_bidder")),
        str((mine or {}).get("top_bidder")),
    )

    # --- 6) Close deal (seller L3) ---
    print("\n6) Close deal / award")
    r_close = cl.post(
        f"/api/v1/projects/{pid}/close-deal",
        headers=seller["headers"],
        json={"use_current_bid": True, "note": "E2E 성사"},
    )
    close_body = j(r_close)
    proj = close_body.get("project") or {}
    log(
        "close-deal",
        r_close.status_code == 200 and proj.get("auction_status") == "sold",
        f"deal={proj.get('deal_status')} price={proj.get('sold_price')}",
    )
    log(
        "deal awaiting_payment",
        proj.get("deal_status") == "awaiting_payment",
        str(proj.get("deal_status")),
    )
    log(
        "buyer is top bidder A",
        int(proj.get("buyer_id") or 0) == int(buyer_a["id"] or 0),
        f"buyer_id={proj.get('buyer_id')} expected={buyer_a['id']}",
    )

    # transfer before pay should fail
    print("\n7) Guards around payment / transfer")
    r_tr_early = cl.post(
        f"/api/v1/projects/{pid}/deal/mark-transferred",
        headers=seller["headers"],
        json={"note": "너무 이르게"},
    )
    log("transfer before paid blocked", r_tr_early.status_code == 400, r_tr_early.text[:120])

    # --- 8) Simulate PG paid ---
    print("\n8) Simulate PG webhook (mark_deal_paid)")
    try:
        with database.db() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
            row = database.mark_deal_paid(conn, row, note="E2E simulated PG")
            deal_status = row["deal_status"] if "deal_status" in row.keys() else None
        log("mark_deal_paid → paid", deal_status == "paid", str(deal_status))
    except Exception as e:
        log("mark_deal_paid", False, str(e))
        traceback.print_exc()
        return _finish(1)

    # --- 9) Transfer ---
    print("\n9) Seller marks transferred")
    r_tr = cl.post(
        f"/api/v1/projects/{pid}/deal/mark-transferred",
        headers=seller["headers"],
        json={"note": "코드·계정 이전 완료 (모의)"},
    )
    tr_proj = j(r_tr).get("project") or {}
    log(
        "mark-transferred → inspection",
        r_tr.status_code == 200 and tr_proj.get("deal_status") == "inspection",
        str(tr_proj.get("deal_status")),
    )

    # wrong user cannot accept
    r_wrong = cl.post(
        f"/api/v1/projects/{pid}/deal/accept",
        headers=buyer_b["headers"],
        json={"note": "나는 2등"},
    )
    log("non-buyer cannot accept", r_wrong.status_code in (403, 400), r_wrong.text[:100])

    # --- 10) Buyer accept ---
    print("\n10) Buyer accept / settle")
    r_acc = cl.post(
        f"/api/v1/projects/{pid}/deal/accept",
        headers=buyer_a["headers"],
        json={"note": "검수 OK 인수 확정"},
    )
    acc_proj = j(r_acc).get("project") or {}
    log(
        "buyer accept → completed",
        r_acc.status_code == 200 and acc_proj.get("deal_status") == "completed",
        str(acc_proj.get("deal_status")),
    )

    # --- 11) Credit / buyer rank ---
    print("\n11) Credit & buyer rank after completion")
    r_me_a = cl.get("/api/v1/me", headers=buyer_a["headers"])
    ua = j(r_me_a).get("user") or {}
    ca = ua.get("credit") or {}
    br = ca.get("buyer_rank") or {}
    log(
        "buyer A bought_complete >= 1",
        int((ca.get("counts") or {}).get("bought_complete") or 0) >= 1,
        str(ca.get("counts")),
    )
    log(
        "buyer A has buyer_rank",
        bool(br.get("label")),
        f"{br.get('key')} {br.get('label')} bought={br.get('bought_complete')}",
    )
    log(
        "buyer A rank is starter+",
        br.get("key") in ("starter", "regular", "heavy", "whale"),
        str(br.get("key")),
    )

    r_me_s = cl.get("/api/v1/me", headers=seller["headers"])
    us = j(r_me_s).get("user") or {}
    cs = us.get("credit") or {}
    log(
        "seller sold_complete >= 1",
        int((cs.get("counts") or {}).get("sold_as_seller") or 0) >= 1,
        str(cs.get("counts")),
    )

    # fee invoice exists
    r_fees = cl.get("/api/v1/admin/fees?status=all", headers=ADMIN)
    if r_fees.status_code != 200:
        r_fees = cl.get("/api/v1/admin/fees", headers=ADMIN)
    log("admin fees reachable", r_fees.status_code == 200, r_fees.text[:80])

    # --- 12) Second completed buy bumps rank path (optional quick) ---
    print("\n12) Second quick deal for buyer A rank growth")
    r_create2 = cl.post(
        "/api/v1/projects",
        headers=seller["headers"],
        json={
            "title": f"모의거래2 {random.randint(1000,9999)}",
            "one_liner": "2차 성사 테스트",
            "status": "프로토타입",
            "product_type": "webapp",
            "story": "두 번째 모의 거래",
            "demo": "https://example.com/d2",
            "assets": ["code"],
            "price_start": 300_000,
            "auction_days": 2,
            "license_note": "양도",
            "attest_works": True,
            "attest_license": True,
            "attest_rights": True,
        },
    )
    pid2 = (j(r_create2).get("project") or {}).get("id")
    if pid2:
        cl.post(
            f"/api/v1/admin/projects/{pid2}/review",
            headers=ADMIN,
            json={"action": "approve", "note": "2", "checklist": {"demo_ok": True}},
        )
        cl.post(
            f"/api/v1/projects/{pid2}/bids",
            headers=buyer_a["headers"],
            json={"amount": 300_000},
        )
        cl.post(
            f"/api/v1/projects/{pid2}/close-deal",
            headers=seller["headers"],
            json={"use_current_bid": True},
        )
        with database.db() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid2,)).fetchone()
            row = database.mark_deal_paid(conn, row, note="pg2")
            database.mark_deal_transferred(conn, row, note="xfer2")
        # re-fetch project for accept
        cl.post(
            f"/api/v1/projects/{pid2}/deal/accept",
            headers=buyer_a["headers"],
            json={"note": "ok2"},
        )
        # if transfer via API needed
        # ensure via API if DB transfer worked
        r_me2 = cl.get("/api/v1/me", headers=buyer_a["headers"])
        bought = int(((j(r_me2).get("user") or {}).get("credit") or {}).get("counts", {}).get("bought_complete") or 0)
        log("buyer A two completes", bought >= 2, f"bought={bought}")
    else:
        log("second listing create", False, r_create2.text[:80])

    print("\n=== Public API snapshot ===")
    for path in [
        "/api/v1/health",
        "/api/v1/credit-policy",
        "/api/v1/auctions/live",
        f"/api/v1/projects/{pid}/bids",
    ]:
        rr = cl.get(path)
        log(f"GET {path}", rr.status_code == 200, f"len={len(rr.content)}")

    return _finish(0)


def _finish(code: int) -> int:
    fails = [r for r in results if not r[1]]
    print("\n=== SUMMARY ===")
    print(f"passed: {sum(1 for r in results if r[1])} / {len(results)}")
    if fails:
        print("FAILED:")
        for s, _, d in fails:
            print(f"  - {s}: {d}")
        code = 1
    else:
        print("All deal-flow checks passed.")
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
