# -*- coding: utf-8 -*-
"""
Multi-angle auction & deal suite for WakeAgain.

Scenarios:
  A) Multi-bidder ranking + seller close-deal (낙찰)
  B) Auto award on auction end (마감 자동 낙찰)
  C) No-bid auction ends cleanly
  D) Buy-now button 낙찰
  E) Bid reaches buy-now price → auto finalize
  F) Payment default (미입금 무효 + credit)
  G) Dispute during inspection
  H) Full happy path pay→transfer→accept
  I) Guards: own bid, low bid, pending bid, bid after sold, unverified bid
"""
from __future__ import annotations

import os
import random
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
    email = f"auc_{tag}_{n}@example.com"
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


def create_listing(
    seller: dict,
    *,
    title: str | None = None,
    price_start: int = 400_000,
    price_buy_now: int | None = None,
    auction_days: int = 3,
) -> int:
    payload = {
        "title": title or f"경매테스트 {random.randint(1000, 9999)}",
        "one_liner": "입찰·낙찰 시나리오 테스트",
        "status": "프로토타입",
        "product_type": "webapp",
        "story": "자동 테스트용 매물 스토리입니다.",
        "demo": "https://example.com/demo",
        "assets": ["code"],
        "price_start": price_start,
        "auction_days": auction_days,
        "min_increment": 10_000,
        "license_note": "양도 테스트",
        "attest_works": True,
        "attest_license": True,
        "attest_rights": True,
    }
    if price_buy_now is not None:
        payload["price_buy_now"] = price_buy_now
    r = cl.post("/api/v1/projects", headers=seller["headers"], json=payload)
    if r.status_code != 200:
        raise RuntimeError(f"create: {r.text[:200]}")
    return int(j(r)["project"]["id"])


def approve(pid: int) -> None:
    r = cl.post(
        f"/api/v1/admin/projects/{pid}/review",
        headers=ADMIN,
        json={"action": "approve", "note": "suite", "checklist": {"demo_ok": True}},
    )
    if r.status_code != 200:
        raise RuntimeError(f"approve: {r.text[:200]}")


def bid(user: dict, pid: int, amount: int):
    return cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=user["headers"],
        json={"amount": amount},
    )


def get_project(pid: int) -> dict:
    r = cl.get(f"/api/v1/projects/{pid}")
    return (j(r).get("project") or {}) if r.status_code == 200 else {}


def get_bids(pid: int) -> dict:
    r = cl.get(f"/api/v1/projects/{pid}/bids")
    return j(r) if r.status_code == 200 else {}


def expire_auction(pid: int) -> None:
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
    with database.db() as conn:
        conn.execute(
            "UPDATE projects SET auction_ends_at = ? WHERE id = ?",
            (past, pid),
        )
        database.process_expired_auctions(conn)


def expire_payment(pid: int) -> None:
    past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(timespec="seconds")
    with database.db() as conn:
        conn.execute(
            "UPDATE projects SET payment_deadline_at = ? WHERE id = ? AND deal_status = 'awaiting_payment'",
            (past, pid),
        )
        database.process_deal_deadlines(conn)


def pg_pay(pid: int) -> None:
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
        database.mark_deal_paid(conn, row, note="suite PG")


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def scenario_A_multi_bid_close() -> None:
    section("A) Multi-bidder + seller close-deal (낙찰)")
    s = seller_ready("A")
    pid = create_listing(s, price_start=500_000)
    approve(pid)
    b1, b2, b3 = register("A1"), register("A2"), register("A3")

    r = bid(b1, pid, 500_000)
    log("A bid1 500k", r.status_code == 200, r.text[:80])
    r = bid(b2, pid, 520_000)
    log("A bid2 520k", r.status_code == 200, r.text[:80])
    r = bid(b3, pid, 510_000)
    log("A bid3 510k (below top still ok if >= next_min)", r.status_code in (200, 400), r.text[:100])
    # after 520k, next min is 530k
    r = bid(b3, pid, 530_000)
    log("A bid3 530k", r.status_code == 200, r.text[:80])
    r = bid(b1, pid, 600_000)
    log("A bid1 tops 600k", r.status_code == 200, r.text[:80])

    data = get_bids(pid)
    bids = data.get("bids") or []
    top = data.get("top_bidder") or {}
    log("A ranked bids", len(bids) >= 3, f"n={len(bids)}")
    log("A top is 600k", int(top.get("amount") or 0) == 600_000, str(top))
    log("A top handle public", bool(top.get("bidder_label")), str(top.get("bidder_label")))
    # amounts descending
    amts = [int(b.get("amount") or 0) for b in bids]
    log("A amounts sorted desc", amts == sorted(amts, reverse=True), str(amts[:5]))

    r = cl.post(
        f"/api/v1/projects/{pid}/close-deal",
        headers=s["headers"],
        json={"use_current_bid": True, "note": "A 낙찰"},
    )
    p = j(r).get("project") or {}
    log("A close-deal sold", r.status_code == 200 and p.get("auction_status") == "sold", str(p.get("deal_status")))
    log("A winner is b1", int(p.get("buyer_id") or 0) == int(b1["id"] or 0), f"buyer={p.get('buyer_id')} b1={b1['id']}")
    log("A sold_price 600k", int(p.get("sold_price") or 0) == 600_000, str(p.get("sold_price")))

    # bid after sold
    r = bid(b2, pid, 700_000)
    log("A bid after sold blocked", r.status_code == 400, r.text[:80])


def scenario_B_auto_award() -> None:
    section("B) Auto award on auction end")
    s = seller_ready("B")
    pid = create_listing(s, price_start=300_000, auction_days=1)
    approve(pid)
    b1, b2 = register("B1"), register("B2")
    bid(b1, pid, 300_000)
    bid(b2, pid, 350_000)
    bid(b1, pid, 400_000)
    expire_auction(pid)
    p = get_project(pid)
    log("B auto sold", p.get("auction_status") == "sold", f"status={p.get('auction_status')}")
    log("B deal awaiting_payment", p.get("deal_status") == "awaiting_payment", str(p.get("deal_status")))
    log("B winner highest bidder", int(p.get("buyer_id") or 0) == int(b1["id"] or 0), f"buyer={p.get('buyer_id')}")
    log("B sold_price 400k", int(p.get("sold_price") or 0) == 400_000, str(p.get("sold_price")))


def scenario_C_no_bid_end() -> None:
    section("C) No-bid auction ends")
    s = seller_ready("C")
    pid = create_listing(s, price_start=300_000)
    approve(pid)
    expire_auction(pid)
    p = get_project(pid)
    log("C ended without sale", p.get("auction_status") == "ended", str(p.get("auction_status")))
    log("C no buyer", not p.get("buyer_id"), str(p.get("buyer_id")))


def scenario_D_buy_now() -> None:
    section("D) Buy-now 낙찰")
    s = seller_ready("D")
    pid = create_listing(s, price_start=200_000, price_buy_now=800_000)
    approve(pid)
    b = register("D1")
    r = cl.post(f"/api/v1/projects/{pid}/buy-now", headers=b["headers"])
    p = j(r).get("project") or {}
    log("D buy-now ok", r.status_code == 200, r.text[:100])
    log("D sold at buy_now", int(p.get("sold_price") or 0) == 800_000, str(p.get("sold_price")))
    log("D buyer set", int(p.get("buyer_id") or 0) == int(b["id"] or 0), str(p.get("buyer_id")))
    log("D awaiting_payment", p.get("deal_status") == "awaiting_payment", str(p.get("deal_status")))
    # cannot buy again
    r2 = cl.post(f"/api/v1/projects/{pid}/buy-now", headers=register("D2")["headers"])
    log("D second buy-now blocked", r2.status_code == 400, r2.text[:80])


def scenario_E_bid_hits_buy_now() -> None:
    section("E) Bid >= buy-now auto finalize")
    s = seller_ready("E")
    pid = create_listing(s, price_start=200_000, price_buy_now=500_000)
    approve(pid)
    b = register("E1")
    r = bid(b, pid, 500_000)
    p = j(r).get("project") or get_project(pid)
    log("E bid triggers sale", r.status_code == 200 and p.get("auction_status") == "sold", str(p.get("auction_status")))
    log("E sold_price 500k", int(p.get("sold_price") or 0) == 500_000, str(p.get("sold_price")))


def scenario_F_payment_default() -> None:
    section("F) Payment default (미입금 무효)")
    s = seller_ready("F")
    pid = create_listing(s, price_start=250_000)
    approve(pid)
    b = register("F1")
    bid(b, pid, 250_000)
    cl.post(
        f"/api/v1/projects/{pid}/close-deal",
        headers=s["headers"],
        json={"use_current_bid": True},
    )
    p0 = get_project(pid)
    log("F awarded", p0.get("deal_status") == "awaiting_payment", str(p0.get("deal_status")))

    me0 = j(cl.get("/api/v1/me", headers=b["headers"])).get("user") or {}
    defaults0 = int(((me0.get("credit") or {}).get("counts") or {}).get("defaults") or 0)

    expire_payment(pid)
    p = get_project(pid)
    log("F payment_default", p.get("deal_status") == "payment_default", str(p.get("deal_status")))
    log("F auction ended", p.get("auction_status") == "ended", str(p.get("auction_status")))

    me1 = j(cl.get("/api/v1/me", headers=b["headers"])).get("user") or {}
    defaults1 = int(((me1.get("credit") or {}).get("counts") or {}).get("defaults") or 0)
    log("F credit defaults +1", defaults1 >= defaults0 + 1, f"{defaults0}→{defaults1}")


def scenario_G_dispute() -> None:
    section("G) Dispute during inspection")
    s = seller_ready("G")
    pid = create_listing(s, price_start=200_000)
    approve(pid)
    b = register("G1")
    bid(b, pid, 200_000)
    cl.post(f"/api/v1/projects/{pid}/close-deal", headers=s["headers"], json={"use_current_bid": True})
    pg_pay(pid)
    cl.post(
        f"/api/v1/projects/{pid}/deal/mark-transferred",
        headers=s["headers"],
        json={"note": "이전함"},
    )
    r = cl.post(
        f"/api/v1/projects/{pid}/deal/dispute",
        headers=b["headers"],
        json={"note": "동작 확인 중 문제 발견 모의 이의"},
    )
    p = j(r).get("project") or get_project(pid)
    log("G dispute ok", r.status_code == 200, r.text[:100])
    log("G deal disputed", p.get("deal_status") == "disputed", str(p.get("deal_status")))
    # accept should fail while disputed
    r2 = cl.post(
        f"/api/v1/projects/{pid}/deal/accept",
        headers=b["headers"],
        json={"note": "그래도 인수"},
    )
    log("G accept blocked while disputed", r2.status_code == 400, r2.text[:100])


def scenario_H_full_happy() -> None:
    section("H) Full happy path pay→transfer→accept")
    s = seller_ready("H")
    pid = create_listing(s, price_start=450_000)
    approve(pid)
    b1, b2 = register("H1"), register("H2")
    bid(b1, pid, 450_000)
    bid(b2, pid, 480_000)
    bid(b1, pid, 520_000)
    r = cl.post(f"/api/v1/projects/{pid}/close-deal", headers=s["headers"], json={"use_current_bid": True})
    log("H close", r.status_code == 200, str((j(r).get("project") or {}).get("sold_price")))
    # transfer before pay fails
    r_early = cl.post(
        f"/api/v1/projects/{pid}/deal/mark-transferred",
        headers=s["headers"],
        json={"note": "early"},
    )
    log("H transfer before pay blocked", r_early.status_code == 400, r_early.text[:80])
    pg_pay(pid)
    r_tr = cl.post(
        f"/api/v1/projects/{pid}/deal/mark-transferred",
        headers=s["headers"],
        json={"note": "xfer"},
    )
    log("H transferred", r_tr.status_code == 200 and (j(r_tr).get("project") or {}).get("deal_status") == "inspection", str((j(r_tr).get("project") or {}).get("deal_status")))
    r_acc = cl.post(
        f"/api/v1/projects/{pid}/deal/accept",
        headers=b1["headers"],
        json={"note": "인수 OK"},
    )
    p = j(r_acc).get("project") or {}
    log("H completed", r_acc.status_code == 200 and p.get("deal_status") == "completed", str(p.get("deal_status")))
    me = j(cl.get("/api/v1/me", headers=b1["headers"])).get("user") or {}
    br = (me.get("credit") or {}).get("buyer_rank") or {}
    bought = int(((me.get("credit") or {}).get("counts") or {}).get("bought_complete") or 0)
    log("H buyer rank after complete", bought >= 1 and bool(br.get("label")), f"bought={bought} rank={br.get('label')}")


def scenario_I_guards() -> None:
    section("I) Guards (trust / ownership / state)")
    s = seller_ready("I")
    pid = create_listing(s, price_start=300_000)
    # unverified cannot bid
    raw = register("I0", verify=False, profile=False)
    r = bid(raw, pid, 300_000)
    # still pending listing anyway — approve first for unverified test
    approve(pid)
    r = bid(raw, pid, 300_000)
    log("I unverified bid blocked", r.status_code == 403, r.text[:120])

    b = register("I1")
    r = bid(s, pid, 300_000)
    log("I owner bid blocked", r.status_code == 400, r.text[:80])
    r = bid(b, pid, 10)
    log("I low bid blocked", r.status_code == 400, r.text[:80])
    bid(b, pid, 300_000)
    cl.post(f"/api/v1/projects/{pid}/close-deal", headers=s["headers"], json={"use_current_bid": True})
    r = bid(b, pid, 400_000)
    log("I bid after sold blocked", r.status_code == 400, r.text[:80])

    # Lv1 only (verified, no profile) can still bid
    v = register("I2", verify=True, profile=False)
    s2 = seller_ready("I2s")
    pid2 = create_listing(s2, price_start=200_000)
    approve(pid2)
    r = bid(v, pid2, 200_000)
    log("I Lv1-only can bid", r.status_code == 200, r.text[:100])


def main() -> int:
    print("\n########## WakeAgain auction & deal suite ##########\n")
    scenarios = [
        scenario_A_multi_bid_close,
        scenario_B_auto_award,
        scenario_C_no_bid_end,
        scenario_D_buy_now,
        scenario_E_bid_hits_buy_now,
        scenario_F_payment_default,
        scenario_G_dispute,
        scenario_H_full_happy,
        scenario_I_guards,
    ]
    for fn in scenarios:
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
    print("All multi-angle auction/deal checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
