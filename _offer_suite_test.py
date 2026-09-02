# -*- coding: utf-8 -*-
"""
고정가 + 가격 제안(offer) 구조 시나리오 스위트 (2026-09-02 경매 폐지 후).

경매·입찰이 사라지고 구매 경로가 둘로 바뀌었다:
  판매가로 바로 구매 / 판매가보다 낮은 금액을 제안 → 판매자 수락

시나리오:
  A) 제안 → 판매자 수락 → 성사(awaiting_payment)
  B) 판매가로 바로 구매 → 즉시 성사
  C) 제안 거절 → 구매자가 다시 제안 가능
  D) 구매자 제안 철회
  E) 한 구매자당 pending 1개 (새 제안이 이전 것을 replaced 처리)
  F) 하한 미만 거부 / 판매가 이상은 use_buy 안내
  G) 판매자 응답 기한 경과 → 자동 만료
  H) 게시 기간 종료 → 자동 낙찰 없이 목록에서 내려감 + 대기 제안 만료
  I) 수락 후 미입금 → 성사 무효 + 매물 판매 재개(차순위 자동 낙찰 없음)
  J) 성사되면 다른 대기 제안은 closed
  K) 가드: 본인 매물 제안 불가 · 이메일 미인증 불가 · 입찰 엔드포인트 410 · 제안 있어도 판매가 수정 가능
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

PRICE = 400_000  # 판매가 (beta 등급 하한 150,000 이상)
FLOOR = 150_000  # beta 등급 제안 하한


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
    email = f"off_{tag}_{n}@example.com"
    r = cl.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "testpass12",
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
    return {"email": email, "token": token, "headers": h, "id": uid, "tag": tag}


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


def create_listing(seller: dict, *, price: int = PRICE, listing_days: int = 3) -> int:
    payload = {
        "title": f"제안테스트 {random.randint(1000, 9999)}",
        "one_liner": "판매가·제안 시나리오 테스트",
        "status": "써 볼 수 있는 제품",
        "product_type": "webapp",
        "story": "자동 테스트용 매물 스토리입니다.",
        "demo": "https://example.com/demo",
        "assets": ["code"],
        "price": price,
        "listing_days": listing_days,
        "license_note": "양도 테스트",
        "keywords": ["테스트", "제안", "SaaS", "웹앱", "판매"],
        "features": ["로그인 후 목록을 볼 수 있어요", "항목을 체크하면 저장돼요"],
        "audience": "제안 시나리오 검증 사용자",
        "works_now": "등록부터 성사까지 시나리오로 동작합니다.",
        "limits": "실제 결제 없음 · 테스트 전용",
        "acquisition": "made",
        "demo_images": [f"/media/demos/{seller['id']}/test.png"],
        "attest_shots": True,
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
        raise RuntimeError(f"create: {r.text[:300]}")
    return int(j(r)["project"]["id"])


def approve(pid: int) -> None:
    r = cl.post(
        f"/api/v1/admin/projects/{pid}/review",
        headers=ADMIN,
        json={"action": "approve", "note": "suite", "checklist": {"demo_ok": True}},
    )
    if r.status_code != 200:
        raise RuntimeError(f"approve: {r.text[:200]}")


def live_listing(seller: dict, **kw) -> int:
    pid = create_listing(seller, **kw)
    approve(pid)
    return pid


def offer(user: dict, pid: int, amount: int, message: str = ""):
    return cl.post(
        f"/api/v1/projects/{pid}/offers",
        headers=user["headers"],
        json={"amount": amount, "message": message},
    )


def get_offers(pid: int, headers: dict | None = None) -> dict:
    r = cl.get(f"/api/v1/projects/{pid}/offers", headers=headers or {})
    return j(r) if r.status_code == 200 else {}


def get_project(pid: int, headers: dict | None = None) -> dict:
    r = cl.get(f"/api/v1/projects/{pid}", headers=headers or {})
    return (j(r).get("project") or {}) if r.status_code == 200 else {}


def expire_listing(pid: int) -> None:
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
    with database.db() as conn:
        conn.execute("UPDATE projects SET auction_ends_at = ? WHERE id = ?", (past, pid))
        database.process_expired_listings(conn)


def expire_offer_window(pid: int) -> int:
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
    with database.db() as conn:
        conn.execute(
            "UPDATE offers SET expires_at = ? WHERE project_id = ? AND status = 'pending'",
            (past, pid),
        )
        return database.expire_stale_offers(conn)


def expire_payment(pid: int) -> None:
    past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(timespec="seconds")
    with database.db() as conn:
        conn.execute(
            "UPDATE projects SET payment_deadline_at = ? WHERE id = ? AND deal_status = 'awaiting_payment'",
            (past, pid),
        )
        database.process_deal_deadlines(conn)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# --- A. 제안 → 수락 → 성사 -------------------------------------------------
def scenario_a() -> None:
    section("A. 제안 → 판매자 수락 → 성사")
    s = seller_ready("A")
    b = register("Ab")
    pid = live_listing(s)

    p = get_project(pid)
    log("판매가 노출", p.get("price") == PRICE, f"price={p.get('price')} status={p.get('sale_status')}")
    log("입찰 잔재 없음", p.get("next_min_bid") is None and p.get("price_buy_now") is None,
        f"next_min_bid={p.get('next_min_bid')} buy_now={p.get('price_buy_now')}")

    r = offer(b, pid, 300_000, "이 금액이면 바로 결제하겠습니다.")
    log("제안 접수", r.status_code == 200, f"{r.status_code} {j(r).get('offer', {}).get('amount')}")
    oid = j(r)["offer"]["id"]

    pub = get_offers(pid)
    log("공개 제안 목록", pub.get("pending_count") == 1 and pub["offers"][0]["amount"] == 300_000,
        f"pending={pub.get('pending_count')}")
    log("제안 금액 공개", pub.get("amounts_public") is True)

    p = get_project(pid)
    log("매물 제안 카운터", p.get("pending_offer_count") == 1 and p.get("offer_count") == 1,
        f"pending={p.get('pending_offer_count')} total={p.get('offer_count')}")
    log("top_offer 노출", (p.get("top_offer") or {}).get("amount") == 300_000)

    ra = cl.post(f"/api/v1/projects/{pid}/offers/{oid}/accept", headers=s["headers"], json={})
    log("판매자 수락", ra.status_code == 200, f"{ra.status_code} {(j(ra).get('project') or {}).get('sold_price')}")
    p = j(ra).get("project") or {}
    log("성사 상태", p.get("sale_status") == "sold" and p.get("deal_status") == "awaiting_payment",
        f"{p.get('sale_status')}/{p.get('deal_status')}")
    log("성사가 = 제안가", p.get("sold_price") == 300_000, str(p.get("sold_price")))
    log("결제 기한 세팅", bool(p.get("payment_deadline_at")))
    log("수수료 청구서", (j(ra).get("fee") or {}).get("fee", 0) > 0,
        str((j(ra).get("fee") or {}).get("fee")))


# --- B. 판매가로 바로 구매 --------------------------------------------------
def scenario_b() -> None:
    section("B. 판매가로 바로 구매")
    s = seller_ready("B")
    b = register("Bb")
    pid = live_listing(s)

    r = cl.post(f"/api/v1/projects/{pid}/buy", headers=b["headers"])
    log("바로 구매", r.status_code == 200, f"{r.status_code}")
    p = j(r).get("project") or {}
    log("즉시 성사", p.get("sale_status") == "sold" and p.get("sold_price") == PRICE,
        f"{p.get('sale_status')} {p.get('sold_price')}")
    log("결제 대기", p.get("deal_status") == "awaiting_payment", str(p.get("deal_status")))

    r2 = cl.post(f"/api/v1/projects/{pid}/buy", headers=register("Bc")["headers"])
    log("두 번째 구매 차단", r2.status_code == 400, f"{r2.status_code}")

    r3 = cl.post(f"/api/v1/projects/{pid}/buy-now", headers=b["headers"])
    log("buy-now 별칭 살아있음", r3.status_code in (400, 200), f"{r3.status_code}")


# --- C. 거절 → 재제안 --------------------------------------------------------
def scenario_c() -> None:
    section("C. 제안 거절 → 다시 제안")
    s = seller_ready("C")
    b = register("Cb")
    pid = live_listing(s)

    oid = j(offer(b, pid, 200_000))["offer"]["id"]
    rd = cl.post(
        f"/api/v1/projects/{pid}/offers/{oid}/decline",
        headers=s["headers"],
        json={"note": "조금만 더 올려주세요"},
    )
    log("거절", rd.status_code == 200 and j(rd)["offer"]["status"] == "declined",
        f"{rd.status_code} {j(rd).get('offer', {}).get('status')}")

    p = get_project(pid)
    log("거절 후 판매 계속", p.get("sale_status") == "live" and p.get("pending_offer_count") == 0,
        f"{p.get('sale_status')} pending={p.get('pending_offer_count')}")

    r2 = offer(b, pid, 320_000)
    log("같은 구매자 재제안 가능", r2.status_code == 200, f"{r2.status_code}")
    log("누적 제안 2건", get_project(pid).get("offer_count") == 2,
        str(get_project(pid).get("offer_count")))


# --- D. 철회 ----------------------------------------------------------------
def scenario_d() -> None:
    section("D. 구매자 제안 철회")
    s = seller_ready("D")
    b = register("Db")
    other = register("Dc")
    pid = live_listing(s)
    oid = j(offer(b, pid, 250_000))["offer"]["id"]

    rx = cl.post(f"/api/v1/projects/{pid}/offers/{oid}/withdraw", headers=other["headers"])
    log("남의 제안 철회 불가", rx.status_code == 403, f"{rx.status_code}")

    rw = cl.post(f"/api/v1/projects/{pid}/offers/{oid}/withdraw", headers=b["headers"])
    log("본인 철회", rw.status_code == 200 and j(rw)["offer"]["status"] == "withdrawn", f"{rw.status_code}")
    log("철회 후 대기 0", get_project(pid).get("pending_offer_count") == 0)

    ra = cl.post(f"/api/v1/projects/{pid}/offers/{oid}/accept", headers=s["headers"], json={})
    log("철회된 제안 수락 불가", ra.status_code == 400, f"{ra.status_code}")


# --- E. 한 구매자당 pending 1개 ---------------------------------------------
def scenario_e() -> None:
    section("E. 한 구매자당 대기 제안 1개")
    s = seller_ready("E")
    b = register("Eb")
    pid = live_listing(s)

    offer(b, pid, 200_000)
    offer(b, pid, 260_000)
    p = get_project(pid)
    log("대기 1건 유지", p.get("pending_offer_count") == 1, str(p.get("pending_offer_count")))
    log("누적은 2건", p.get("offer_count") == 2, str(p.get("offer_count")))
    pub = get_offers(pid)
    log("최신 금액이 대기 제안", pub["offers"][0]["amount"] == 260_000, str(pub["offers"][0]["amount"]))
    seller_view = get_offers(pid, s["headers"])
    statuses = sorted(o["status"] for o in seller_view["offers"])
    log("이전 제안 replaced", statuses == ["pending", "replaced"], str(statuses))
    log("본인 제안 mine 노출", (get_offers(pid, b["headers"]).get("mine") or {}).get("amount") == 260_000)


# --- F. 금액 가드 ------------------------------------------------------------
def scenario_f() -> None:
    section("F. 제안 금액 하한·상한")
    s = seller_ready("F")
    b = register("Fb")
    pid = live_listing(s)

    r_low = offer(b, pid, FLOOR - 10_000)
    code_low = ((j(r_low).get("detail") or {}) or {}).get("code")
    log("하한 미만 거부", r_low.status_code == 400 and code_low == "offer_too_low", f"{r_low.status_code} {code_low}")

    r_eq = offer(b, pid, PRICE)
    code_eq = ((j(r_eq).get("detail") or {}) or {}).get("code")
    log("판매가 이상은 구매 안내", r_eq.status_code == 400 and code_eq == "use_buy", f"{r_eq.status_code} {code_eq}")

    r_ok = offer(b, pid, PRICE - 1)
    log("판매가 바로 아래는 허용", r_ok.status_code == 200, f"{r_ok.status_code}")
    log("하한값 공개", get_project(pid).get("offer_floor") == FLOOR, str(get_project(pid).get("offer_floor")))


# --- G. 응답 기한 만료 -------------------------------------------------------
def scenario_g() -> None:
    section("G. 판매자 무응답 → 제안 자동 만료")
    s = seller_ready("G")
    b = register("Gb")
    pid = live_listing(s)
    oid = j(offer(b, pid, 280_000))["offer"]["id"]

    n = expire_offer_window(pid)
    log("만료 처리 실행", n == 1, f"expired={n}")
    seller_view = get_offers(pid, s["headers"])
    st = [o["status"] for o in seller_view["offers"]]
    log("상태 expired", st == ["expired"], str(st))
    p = get_project(pid)
    log("매물은 그대로 판매 중", p.get("sale_status") == "live" and p.get("pending_offer_count") == 0,
        f"{p.get('sale_status')} pending={p.get('pending_offer_count')}")
    log("만료 후 재제안 가능", offer(b, pid, 300_000).status_code == 200)
    _ = oid


# --- H. 게시 기간 종료 -------------------------------------------------------
def scenario_h() -> None:
    section("H. 게시 기간 종료 — 자동 낙찰 없음")
    s = seller_ready("H")
    b = register("Hb")
    pid = live_listing(s)
    offer(b, pid, 350_000)

    expire_listing(pid)
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
        offers = conn.execute(
            "SELECT status FROM offers WHERE project_id = ?", (pid,)
        ).fetchall()
    log("자동 성사 안 됨", (row["auction_status"] or "") == "ended" and not row["sold_at"],
        f"{row['auction_status']} sold_at={row['sold_at']}")
    log("목록에서 내려감", (row["listing_status"] or "") == "archived", str(row["listing_status"]))
    log("대기 제안 만료", [o["status"] for o in offers] == ["expired"],
        str([o["status"] for o in offers]))
    log("공개 상세 404", cl.get(f"/api/v1/projects/{pid}").status_code == 404)


# --- I. 미입금 → 판매 재개 ---------------------------------------------------
def scenario_i() -> None:
    section("I. 수락 후 미입금 → 성사 무효 · 판매 재개")
    s = seller_ready("I")
    b1 = register("Ib")
    b2 = register("Ic")
    pid = live_listing(s)
    oid = j(offer(b1, pid, 300_000))["offer"]["id"]
    offer(b2, pid, 260_000)
    cl.post(f"/api/v1/projects/{pid}/offers/{oid}/accept", headers=s["headers"], json={})

    expire_payment(pid)
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
        u = conn.execute("SELECT * FROM users WHERE id = ?", (b1["id"],)).fetchone()
    log("성사 무효", (row["deal_status"] or "") == "payment_default", str(row["deal_status"]))
    log("차순위 자동 낙찰 없음", not row["sold_at"] and row["buyer_id"] is None,
        f"sold_at={row['sold_at']} buyer={row['buyer_id']}")
    log("판매 재개", (row["auction_status"] or "") == "live", str(row["auction_status"]))
    log("판매가 복구", int(row["price_current"] or 0) == PRICE, str(row["price_current"]))
    log("미입금 신용 감점", int(u["credit_defaults"] or 0) >= 1, f"defaults={u['credit_defaults']}")


# --- J. 성사 시 다른 제안 종료 -----------------------------------------------
def scenario_j() -> None:
    section("J. 성사되면 다른 대기 제안은 종료")
    s = seller_ready("J")
    b1 = register("Jb")
    b2 = register("Jc")
    b3 = register("Jd")
    pid = live_listing(s)
    oid = j(offer(b1, pid, 300_000))["offer"]["id"]
    offer(b2, pid, 250_000)
    offer(b3, pid, 280_000)
    log("대기 3건", get_project(pid).get("pending_offer_count") == 3,
        str(get_project(pid).get("pending_offer_count")))

    cl.post(f"/api/v1/projects/{pid}/offers/{oid}/accept", headers=s["headers"], json={})
    seller_view = get_offers(pid, s["headers"])
    st = sorted(o["status"] for o in seller_view["offers"])
    log("수락 1 · 종료 2", st == ["accepted", "closed", "closed"], str(st))
    log("대기 0으로 초기화", get_project(pid, s["headers"]).get("pending_offer_count") == 0)


# --- K. 가드 ----------------------------------------------------------------
def scenario_k() -> None:
    section("K. 가드")
    s = seller_ready("K")
    b = register("Kb")
    unverified = register("Ku", verify=False, profile=False)
    pid = live_listing(s)

    r_own = offer(s, pid, 200_000)
    log("본인 매물 제안 불가", r_own.status_code == 400, f"{r_own.status_code}")

    r_unv = offer(unverified, pid, 200_000)
    log("이메일 미인증 제안 불가", r_unv.status_code == 403, f"{r_unv.status_code}")

    log("POST /bids 410", cl.post(f"/api/v1/projects/{pid}/bids", json={"amount": 1}).status_code == 410)
    log("GET /bids 410", cl.get(f"/api/v1/projects/{pid}/bids").status_code == 410)

    offer(b, pid, 250_000)
    rp = cl.put(f"/api/v1/projects/{pid}/price", headers=s["headers"], json={"price": 500_000})
    log("제안 있어도 판매가 수정 가능", rp.status_code == 200, f"{rp.status_code}")
    log("수정된 판매가 반영", get_project(pid).get("price") == 500_000, str(get_project(pid).get("price")))

    rdel = cl.delete(f"/api/v1/projects/{pid}", headers=s["headers"])
    code = ((j(rdel).get("detail") or {}) or {}).get("code")
    log("대기 제안 있으면 삭제 불가", rdel.status_code == 400 and code == "offers_pending",
        f"{rdel.status_code} {code}")

    board = j(cl.get("/api/v1/listings/live"))
    ids = [x["id"] for x in board.get("listings", [])]
    log("라이브 보드 노출", pid in ids, f"listings={len(ids)}")
    log("보드 별칭 키 유지", "auctions" in board and len(board["auctions"]) == len(board["listings"]))


def main() -> int:
    print("=== WakeAgain 고정가 + 제안 스위트 ===")
    for fn in (
        scenario_a, scenario_b, scenario_c, scenario_d, scenario_e,
        scenario_f, scenario_g, scenario_h, scenario_i, scenario_j, scenario_k,
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
    print("모든 고정가·제안 시나리오 통과")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
