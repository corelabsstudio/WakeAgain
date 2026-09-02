# -*- coding: utf-8 -*-
"""
성사 이후(딜) 시나리오 스위트 — 고정가 + 제안 구조 (2026-09-02 경매 폐지 후).

제안·구매 자체의 시나리오는 `_offer_suite_test.py`가 담당한다. 이 파일은 성사된 뒤의
결제·이전·검수·분쟁·신용 반영을 본다.

시나리오:
  F) 미입금 → 성사 무효 + 신용 감점 + 매물 판매 재개
  G) 검수 중 이의(분쟁)
  H) 해피패스 결제→이전→인수
  I) 가드: 본인 매물·하한 미만·미인증·성사 후 제안 차단, Lv1만으로 제안 가능
  L) 수수료 청구서 발행
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

database.init_db()
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
    listing_days: int = 3,
) -> int:
    payload = {
        "title": title or f"판매테스트 {random.randint(1000, 9999)}",
        "one_liner": "판매가·제안 시나리오 테스트",
        "status": "프로토타입",
        "product_type": "webapp",
        "story": "자동 테스트용 매물 스토리입니다.",
        "demo": "https://example.com/demo",
        "assets": ["code"],
        "price": price_start,
        "listing_days": listing_days,
        "license_note": "양도 테스트",
        "keywords": ["테스트", "판매", "SaaS", "웹앱", "제안"],
        "features": ["로그인 후 목록을 볼 수 있어요", "항목을 체크하면 저장돼요"],
        "audience": "판매 시나리오 검증 사용자",
        "works_now": "등록부터 성사까지 시나리오로 동작합니다.",
        "limits": "실제 결제 없음 · 테스트 전용",
        "acquisition": "made",
        "demo_images": [f"/media/demos/{seller['id']}/test.png"],
        "attest_shots": True,
        # 매물 등록 필수 필드 정책(2026-08-15) — 신규 등록에 필수
        "repo_url": "https://github.com/corelabsstudio/WakeAgain",
        "is_private_repo": False,
        "is_offline": True,
        "last_activity_at": "2026-08",
        "attest_works": True,
        "attest_features": True,
        "attest_license": True,
        "attest_rights": True,
        "attest_transfer": True,
    }
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


def offer(user: dict, pid: int, amount: int):
    return cl.post(
        f"/api/v1/projects/{pid}/offers",
        headers=user["headers"],
        json={"amount": amount},
    )


def buy(user: dict, pid: int):
    return cl.post(f"/api/v1/projects/{pid}/buy", headers=user["headers"])


def accept_top_offer(seller: dict, pid: int):
    """판매자가 최고 대기 제안을 수락 → 성사."""
    offers = j(cl.get(f"/api/v1/projects/{pid}/offers", headers=seller["headers"])).get("offers") or []
    pending = [o for o in offers if o.get("status") == "pending"]
    if not pending:
        raise RuntimeError("no pending offer to accept")
    oid = pending[0]["id"]
    return cl.post(f"/api/v1/projects/{pid}/offers/{oid}/accept", headers=seller["headers"], json={})


def get_project(pid: int, headers: dict | None = None) -> dict:
    r = cl.get(f"/api/v1/projects/{pid}", headers=headers or {})
    return (j(r).get("project") or {}) if r.status_code == 200 else {}


def get_offers(pid: int, headers: dict | None = None) -> dict:
    r = cl.get(f"/api/v1/projects/{pid}/offers", headers=headers or {})
    return j(r) if r.status_code == 200 else {}


def expire_listing(pid: int) -> None:
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
    with database.db() as conn:
        conn.execute(
            "UPDATE projects SET auction_ends_at = ? WHERE id = ?",
            (past, pid),
        )
        database.process_expired_listings(conn)


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


def scenario_F_payment_default() -> None:
    section("F) Payment default (미입금 무효)")
    s = seller_ready("F")
    pid = create_listing(s, price_start=250_000)
    approve(pid)
    b = register("F1")
    buy(b, pid)
    p0 = get_project(pid)
    log("F awarded", p0.get("deal_status") == "awaiting_payment", str(p0.get("deal_status")))

    me0 = j(cl.get("/api/v1/me", headers=b["headers"])).get("user") or {}
    defaults0 = int(((me0.get("credit") or {}).get("counts") or {}).get("defaults") or 0)

    expire_payment(pid)
    p = get_project(pid, headers=s["headers"])
    log("F payment_default", p.get("deal_status") == "payment_default", str(p.get("deal_status")))
    log("F 판매 재개", p.get("sale_status") == "live", str(p.get("sale_status")))

    me1 = j(cl.get("/api/v1/me", headers=b["headers"])).get("user") or {}
    defaults1 = int(((me1.get("credit") or {}).get("counts") or {}).get("defaults") or 0)
    log("F credit defaults +1", defaults1 >= defaults0 + 1, f"{defaults0}→{defaults1}")


def scenario_G_dispute() -> None:
    section("G) Dispute during inspection")
    s = seller_ready("G")
    pid = create_listing(s, price_start=200_000)
    approve(pid)
    b = register("G1")
    buy(b, pid)
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
    offer(b2, pid, 300_000)
    offer(b1, pid, 380_000)
    r = accept_top_offer(s, pid)
    log("H 제안 수락", r.status_code == 200, str((j(r).get("project") or {}).get("sold_price")))
    log("H 성사가 = 최고 제안", int((j(r).get("project") or {}).get("sold_price") or 0) == 380_000)
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
    r_p = cl.get(f"/api/v1/projects/{pid}", headers=b1["headers"])
    ho = (j(r_p).get("project") or {}).get("handover_checklist") or {}
    checks = {it["id"]: True for it in (ho.get("items") or []) if it.get("id")}
    if checks:
        cl.put(
            f"/api/v1/projects/{pid}/deal/handover-checklist",
            headers=b1["headers"],
            json={"checks": checks},
        )
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
    # 미인증 계정은 제안 불가
    raw = register("I0", verify=False, profile=False)
    approve(pid)
    r = offer(raw, pid, 200_000)
    log("I 미인증 제안 차단", r.status_code == 403, r.text[:120])

    b = register("I1")
    r = offer(s, pid, 200_000)
    log("I 본인 매물 제안 차단", r.status_code == 400, r.text[:80])
    r = offer(b, pid, 10)
    log("I 하한 미만 차단", r.status_code == 400, r.text[:80])
    offer(b, pid, 200_000)
    accept_top_offer(s, pid)
    r = offer(b, pid, 250_000)
    log("I 성사 후 제안 차단", r.status_code == 400, r.text[:80])
    r = buy(b, pid)
    log("I 성사 후 구매 차단", r.status_code == 400, r.text[:80])

    # Lv1(이메일만)으로도 제안 가능
    v = register("I2", verify=True, profile=False)
    s2 = seller_ready("I2s")
    pid2 = create_listing(s2, price_start=200_000)
    approve(pid2)
    r = offer(v, pid2, 150_000)
    log("I Lv1만으로 제안 가능", r.status_code == 200, r.text[:100])


def scenario_L_fee_invoice() -> None:
    section("L) 수수료 청구서")
    s = seller_ready("L")
    pid = create_listing(s, price_start=500_000)
    approve(pid)
    b = register("L1")
    buy(b, pid)
    with database.db() as conn:
        inv = conn.execute(
            "SELECT * FROM fee_invoices WHERE project_id = ? ORDER BY id DESC LIMIT 1", (pid,)
        ).fetchone()
    log("L 청구서 발행", inv is not None)
    if inv:
        log("L 거래액 = 판매가", int(inv["deal_amount"]) == 500_000, str(inv["deal_amount"]))
        log("L 수수료 10%", int(inv["fee_amount"]) == 50_000, str(inv["fee_amount"]))
        log("L 상태 pending", (inv["status"] or "") == "pending", str(inv["status"]))
    mine = j(cl.get("/api/v1/me/fees", headers=s["headers"]))
    log("L 판매자 수수료 목록", isinstance(mine.get("invoices"), list) and len(mine["invoices"]) >= 1,
        str(len(mine.get("invoices") or [])))


def main() -> int:
    print("=== WakeAgain 성사 이후(딜) 스위트 — 고정가 + 제안 ===")
    for fn in (
        scenario_F_payment_default,
        scenario_G_dispute,
        scenario_H_full_happy,
        scenario_I_guards,
        scenario_L_fee_invoice,
    ):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            log(f"{fn.__name__} 예외", False, f"{type(e).__name__}: {e}")
            traceback.print_exc()
    ok = sum(1 for _, o, _ in results if o)
    total = len(results)
    print(f"\n=== {ok}/{total} passed ===")
    if ok != total:
        for step, o, detail in results:
            if not o:
                print(f"  FAIL: {step} — {detail}")
        return 1
    print("모든 딜 시나리오 통과")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
