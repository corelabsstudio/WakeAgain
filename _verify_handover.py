# -*- coding: utf-8 -*-
"""Verify handover checklist + certificate + deal accept gate."""
from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("ADMIN_SECRET", "wakeagain-admin-dev")
os.environ.setdefault("EMAIL_DEV_MODE", "1")
os.environ.setdefault("EMAIL_CODE_FALLBACK", "1")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from server import app
from wakeagain import db as database
from wakeagain.db import (
    seed_handover_checklist,
    handover_checklist_public,
    handover_all_required_checked,
)

cl = TestClient(app)
ADMIN = {"X-Admin-Key": os.environ.get("ADMIN_SECRET", "wakeagain-admin-dev")}
fails = 0


def ok(name: str, cond: bool, detail: str = "") -> None:
    global fails
    mark = "OK" if cond else "FAIL"
    if not cond:
        fails += 1
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


def j(r):
    try:
        return r.json()
    except Exception:
        return {"_raw": (r.text or "")[:400]}


def register(tag: str) -> dict:
    s = f"{tag}{random.randint(10000, 99999)}"
    email = f"{s}@example.com"
    password = "Testpass12!"
    r = cl.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": tag,
            "birth_date": "1995-01-01",
            "confirm_age_14": True,
        },
    )
    data = j(r)
    # may need verify
    token = data.get("access_token") or data.get("token")
    if not token and r.status_code >= 400:
        r = cl.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        data = j(r)
        token = data.get("access_token") or data.get("token")
    # email verify via dev code if present
    user = data.get("user") or {}
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if token:
        # try resend + verify
        rv = cl.post("/api/v1/auth/resend-verify", headers=headers)
        code = j(rv).get("dev_email_code") or data.get("dev_email_code")
        if code:
            cl.post(
                "/api/v1/auth/verify-email",
                headers=headers,
                json={"code": str(code)},
            )
        # L2 profile
        phone = f"010{random.randint(10000000, 99999999)}"
        cl.put(
            "/api/v1/me/profile",
            headers=headers,
            json={
                "real_name": f"{tag}실명",
                "phone": phone,
                "display_name": tag,
                "role": "both",
            },
        )
        # L3 settlement
        cl.put(
            "/api/v1/me/settlement",
            headers=headers,
            json={
                "bank": "카카오뱅크",
                "holder": f"{tag}실명",
                "account": f"3333{random.randint(10000000, 99999999)}",
                "is_business": False,
            },
        )
        # seller public identity (required to list)
        cl.put(
            "/api/v1/me/seller-identity",
            headers=headers,
            json={
                "seller_type": "individual",
                "trade_name": f"판매{tag}",
                "contact_email": email,
                "contact_phone": phone,
                "address": "서울",
                "mail_order_report_no": "",
            },
        )
        me = j(cl.get("/api/v1/me", headers=headers)).get("user") or {}
        return {
            "email": email,
            "headers": headers,
            "id": me.get("id") or user.get("id"),
            "user": me,
        }
    raise RuntimeError(f"register failed {r.status_code} {data}")


def main() -> int:
    print("=== 1) Unit: seed checklist ===")
    seeded = seed_handover_checklist({"assets_json": json.dumps(["code", "domain", "design"])})
    ids = [i["id"] for i in seeded["items"]]
    ok("has asset_code", "asset_code" in ids, str(ids))
    ok("has asset_domain", "asset_domain" in ids)
    ok("has fixed access_guide", "access_guide" in ids)
    ok("has fixed license_ok", "license_ok" in ids)
    pub = handover_checklist_public(seeded)
    ok("not all checked initially", pub["all_required_checked"] is False)
    ok("required count >= 4", pub["required_count"] >= 4, str(pub["required_count"]))

    partial = json.loads(json.dumps(seeded))
    partial["items"][0]["checked"] = True
    ok(
        "partial incomplete",
        handover_all_required_checked(
            {"handover_checklist_json": json.dumps(partial)}
        )
        is False,
    )
    for it in partial["items"]:
        it["checked"] = True
    ok(
        "all checked complete",
        handover_all_required_checked(
            {"handover_checklist_json": json.dumps(partial)}
        )
        is True,
    )

    print("\n=== 2) API routes present ===")
    from wakeagain import api

    paths = [getattr(r, "path", "") for r in api.router.routes]
    ok("handover route", any("handover-checklist" in p for p in paths))
    ok("certificate route", any("certificate" in p for p in paths))

    print("\n=== 3) E2E: sell → pay → transfer → checklist → accept ===")
    database.init_db()
    try:
        seller = register("HS")
        buyer = register("HB")
    except Exception as e:
        ok("register users", False, str(e))
        return 1
    ok("seller registered", bool(seller.get("headers")))
    ok("buyer registered", bool(buyer.get("headers")))

    # create listing with assets
    r = cl.post(
        "/api/v1/projects",
        headers=seller["headers"],
        json={
            "title": "체크리스트검증매물",
            "one_liner": "인수 확인 목록 E2E 검증용 매물입니다",
            "status": "prototype",
            "product_type": "webapp",
            "features": [
                "로그인 후 목록을 볼 수 있어요",
                "항목을 체크하면 저장돼요",
                "인수 버튼은 필수 체크 후 열려요",
            ],
            "audience": "플랫폼 거래 흐름 검증 사용자",
            "works_now": "등록부터 인수까지 테스트 시나리오로 동작합니다.",
            "limits": "실제 결제 없음 · 모의 PG 입금",
            "acquisition": "made",
            "story": "인수 체크리스트 기능 검증을 위해 등록한 매물입니다.",
            "demo": "https://example.com/demo-handover-check",
            "assets": ["code", "domain"],
            "keywords": ["검증", "체크리스트", "인수", "테스트", "SaaS"],
            "price_start": 150000,
            "license_note": "사유 코드 전부 양도",
            "attest_works": True,
            "attest_features": True,
            "attest_license": True,
            "attest_rights": True,
            "attest_transfer": True,
        },
    )
    proj = j(r).get("project") or {}
    pid = proj.get("id")
    ok("create project", r.status_code == 200 and pid, f"{r.status_code} {j(r)}")
    if not pid:
        return 1

    # admin approve
    r_ap = cl.post(
        f"/api/v1/admin/projects/{pid}/review",
        headers=ADMIN,
        json={
            "action": "approve",
            "note": "e2e",
            "checklist": {
                "demo_ok": True,
                "not_idea_only": True,
                "features_ok": True,
                "works_limits_ok": True,
                "status_ok": True,
                "price_ok": True,
                "story_ok": True,
                "rights_ok": True,
                "no_scam": True,
            },
        },
    )
    ok("admin approve", r_ap.status_code == 200, r_ap.text[:120])

    # bid + close
    r_bid = cl.post(
        f"/api/v1/projects/{pid}/bids",
        headers=buyer["headers"],
        json={"amount": 150000},
    )
    ok("bid", r_bid.status_code == 200, r_bid.text[:120])
    r_close = cl.post(
        f"/api/v1/projects/{pid}/close-deal",
        headers=seller["headers"],
        json={"use_current_bid": True},
    )
    ok("close-deal", r_close.status_code == 200, r_close.text[:150])

    # certificate award (both parties)
    r_cert_b = cl.get(
        f"/api/v1/projects/{pid}/certificate?kind=award",
        headers=buyer["headers"],
    )
    r_cert_s = cl.get(
        f"/api/v1/projects/{pid}/certificate?kind=award",
        headers=seller["headers"],
    )
    cb, cs = j(r_cert_b), j(r_cert_s)
    ok("cert buyer 200", r_cert_b.status_code == 200, r_cert_b.text[:100])
    ok("cert seller 200", r_cert_s.status_code == 200)
    ok(
        "same doc_id both parties",
        cb.get("doc_id") and cb.get("doc_id") == cs.get("doc_id"),
        f"{cb.get('doc_id')} vs {cs.get('doc_id')}",
    )
    # stranger cannot
    stranger = register("HX")
    r_cert_x = cl.get(
        f"/api/v1/projects/{pid}/certificate?kind=award",
        headers=stranger["headers"],
    )
    ok("stranger cert forbidden", r_cert_x.status_code == 403, str(r_cert_x.status_code))

    # simulate PG paid
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
        database.mark_deal_paid(conn, row, note="verify-pg")

    r_tr = cl.post(
        f"/api/v1/projects/{pid}/deal/mark-transferred",
        headers=seller["headers"],
        json={"note": "이전 완료 모의"},
    )
    ok("mark-transferred", r_tr.status_code == 200, r_tr.text[:120])

    # get project as buyer — checklist present
    r_get = cl.get(f"/api/v1/projects/{pid}", headers=buyer["headers"])
    p = j(r_get).get("project") or {}
    ho = p.get("handover_checklist") or {}
    items = ho.get("items") or []
    ok("checklist on project", bool(items), str(ho)[:200])
    ok(
        "checklist includes code/domain-ish",
        any("code" in str(i.get("id")) for i in items),
        [i.get("id") for i in items],
    )

    # accept without checks → fail
    r_fail = cl.post(
        f"/api/v1/projects/{pid}/deal/accept",
        headers=buyer["headers"],
        json={"note": "체크 안 함"},
    )
    detail = j(r_fail).get("detail")
    code = detail.get("code") if isinstance(detail, dict) else None
    ok(
        "accept blocked without checklist",
        r_fail.status_code == 400 and code == "handover_checklist_incomplete",
        f"{r_fail.status_code} {detail}",
    )

    # seller cannot check
    r_seller_ck = cl.put(
        f"/api/v1/projects/{pid}/deal/handover-checklist",
        headers=seller["headers"],
        json={"checks": {items[0]["id"]: True} if items else {}},
    )
    ok("seller cannot check", r_seller_ck.status_code == 403, str(r_seller_ck.status_code))

    # buyer checks all
    checks = {i["id"]: True for i in items if i.get("id")}
    r_ck = cl.put(
        f"/api/v1/projects/{pid}/deal/handover-checklist",
        headers=buyer["headers"],
        json={"checks": checks},
    )
    ho2 = j(r_ck).get("handover_checklist") or {}
    ok("buyer checklist save", r_ck.status_code == 200, r_ck.text[:120])
    ok("all required after check", ho2.get("all_required_checked") is True, str(ho2))

    # accept works
    r_acc = cl.post(
        f"/api/v1/projects/{pid}/deal/accept",
        headers=buyer["headers"],
        json={"note": "인수 OK"},
    )
    ap = j(r_acc).get("project") or {}
    ok(
        "accept after checklist",
        r_acc.status_code == 200 and ap.get("deal_status") == "completed",
        f"{r_acc.status_code} {ap.get('deal_status')}",
    )

    # complete certificate
    r_cc = cl.get(
        f"/api/v1/projects/{pid}/certificate?kind=complete",
        headers=buyer["headers"],
    )
    ok(
        "complete certificate",
        r_cc.status_code == 200 and j(r_cc).get("kind") == "complete",
        j(r_cc).get("doc_id"),
    )

    print("\n=== 4) Live site smoke ===")
    import urllib.request

    for url in [
        "https://wakeagain.com/api/v1/health",
        "https://wakeagain.com/js/deal-certificate.js?v=20260725a",
    ]:
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                body = resp.read()
                ok(f"live {url.split('/')[-1][:30]}", resp.status == 200, f"len={len(body)}")
        except Exception as e:
            ok(f"live {url}", False, str(e))

    # live project.html contains handover UI markers (may lag if deploy pending)
    try:
        with urllib.request.urlopen("https://wakeagain.com/project.html", timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            ok("live handoverBox id", "handoverBox" in html)
            ok("live deal-certificate script", "deal-certificate.js" in html)
            ok("live 쪽지로 연락 copy", "쪽지로 연락" in html or "Message counterparty" in html)
    except Exception as e:
        ok("live project.html", False, str(e))

    print("\n=== RESULT ===")
    if fails:
        print(f"FAILED: {fails} check(s)")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
