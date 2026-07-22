"""WakeAgain production durability E2E.

Flow:
  1) Register seller + buyer
  2) Lv2 profile + seller identity (seller), email verify both (admin)
  3) Create listing → admin approve → bid → notification
  4) Snapshot expected IDs/counts
  5) (external) restart / redeploy
  6) Re-login + assert listing / bid / notification still present

Usage:
  python scripts/durability_e2e.py seed
  python scripts/durability_e2e.py verify --state data/durability_state.json
  python scripts/durability_e2e.py full   # seed only; restart/redeploy is orchestrated outside
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (os.environ.get("WAKEAGAIN_BASE") or "https://wakeagain.com").rstrip("/")
STATE_PATH = Path(os.environ.get("DURABILITY_STATE") or ROOT / "data" / "durability_state.json")


def _admin_key() -> str:
    k = (os.environ.get("ADMIN_SECRET") or "").strip()
    if k:
        return k
    # try railway CLI
    import subprocess

    try:
        out = subprocess.check_output(
            ["railway", "variables", "--json"],
            cwd=str(ROOT),
            text=True,
            timeout=60,
        )
        data = json.loads(out)
        return (data.get("ADMIN_SECRET") or "").strip()
    except Exception as e:
        raise SystemExit(f"ADMIN_SECRET missing: {e}") from e


def req(method: str, path: str, *, token: str | None = None, admin: bool = False, body: dict | None = None):
    url = BASE + path
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    if admin:
        headers["X-Admin-Key"] = _admin_key()
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as res:
            raw = res.read().decode("utf-8")
            return res.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
        except Exception:
            detail = {"detail": raw}
        raise RuntimeError(f"{method} {path} -> {e.code}: {detail}") from e


def stamp() -> str:
    return str(int(time.time()) % 10_000_000)


def seed() -> dict:
    s = stamp()
    seller_email = f"durability.seller.{s}@example.com"
    buyer_email = f"durability.buyer.{s}@example.com"
    password = f"DurabTest!{s}a1"
    birth = "1995-05-15"

    print(f"[seed] base={BASE}")
    print(f"[seed] seller={seller_email}")
    print(f"[seed] buyer={buyer_email}")

    # register seller
    _, reg_s = req(
        "POST",
        "/api/v1/auth/register",
        body={
            "email": seller_email,
            "password": password,
            "display_name": f"DurSeller{s}",
            "birth_date": birth,
            "confirm_age_14": True,
        },
    )
    seller_tok = reg_s["token"]
    seller_id = reg_s["user"]["id"]
    print(f"[seed] seller id={seller_id}")

    # register buyer
    _, reg_b = req(
        "POST",
        "/api/v1/auth/register",
        body={
            "email": buyer_email,
            "password": password,
            "display_name": f"DurBuyer{s}",
            "birth_date": birth,
            "confirm_age_14": True,
        },
    )
    buyer_tok = reg_b["token"]
    buyer_id = reg_b["user"]["id"]
    print(f"[seed] buyer id={buyer_id}")

    # admin verify both emails
    for uid in (seller_id, buyer_id):
        code, out = req("POST", f"/api/v1/admin/users/{uid}/verify-email", admin=True, body={})
        print(f"[seed] verify-email user={uid} -> {code} ok={out.get('ok')}")

    # refresh tokens via login after verify
    _, login_s = req("POST", "/api/v1/auth/login", body={"email": seller_email, "password": password})
    seller_tok = login_s["token"]
    _, login_b = req("POST", "/api/v1/auth/login", body={"email": buyer_email, "password": password})
    buyer_tok = login_b["token"]

    # seller Lv2 profile
    _, prof = req(
        "PUT",
        "/api/v1/me/profile",
        token=seller_tok,
        body={
            "real_name": "내구성판매",
            "phone": "01012345678",
            "role": "both",
            "display_name": f"DurSeller{s}",
        },
    )
    print(f"[seed] seller profile trust.level={prof['user']['trust'].get('level')}")

    # seller identity (list gate)
    _, sid = req(
        "PUT",
        "/api/v1/me/seller-identity",
        token=seller_tok,
        body={
            "seller_type": "individual",
            "trade_name": f"DurSeller{s}",
            "contact_email": seller_email,
            "contact_phone": "01012345678",
            "address": "서울시 테스트구 내구성로 1",
        },
    )
    print(f"[seed] seller identity ok={sid.get('ok')}")

    # buyer Lv2 (for bid only Lv1 needed, but complete anyway)
    req(
        "PUT",
        "/api/v1/me/profile",
        token=buyer_tok,
        body={
            "real_name": "내구성구매",
            "phone": "01087654321",
            "role": "buyer",
            "display_name": f"DurBuyer{s}",
        },
    )

    # create listing
    title = f"내구성테스트매물-{s}"
    _, proj = req(
        "POST",
        "/api/v1/projects",
        token=seller_tok,
        body={
            "title": title,
            "one_liner": "재시작·재배포 후에도 남아야 하는 테스트 매물",
            "status": "prototype",
            "product_type": "webapp",
            "story": "회원 데이터 영속성 검증용으로 등록한 매물입니다. 재배포 후에도 입찰·알림과 함께 유지되어야 합니다.",
            "demo": "https://example.com/demo-durability",
            "assets": ["readme"],
            "price_start": 150000,
            "price_buy_now": 500000,
            "min_increment": 10000,
            "auction_days": 7,
            "license_note": "MIT 양도 테스트",
            "attest_works": True,
            "attest_license": True,
            "attest_rights": True,
        },
    )
    project = proj["project"]
    project_id = project["id"]
    print(f"[seed] project id={project_id} status={project.get('listing_status')}")

    # admin approve
    checklist = {
        "demo_ok": True,
        "not_idea_only": True,
        "status_ok": True,
        "price_ok": True,
        "story_ok": True,
        "no_scam": True,
    }
    _, rev = req(
        "POST",
        f"/api/v1/admin/projects/{project_id}/review",
        admin=True,
        body={"action": "approve", "note": "durability e2e", "checklist": checklist},
    )
    print(f"[seed] approve ok={rev.get('ok')} listing={rev.get('project', {}).get('listing_status')}")

    # buyer bid
    bid_amount = 160000
    _, bid = req(
        "POST",
        f"/api/v1/projects/{project_id}/bids",
        token=buyer_tok,
        body={"amount": bid_amount},
    )
    bid_id = bid["bid"]["id"]
    print(f"[seed] bid id={bid_id} amount={bid_amount}")

    # seller notifications (new bid)
    _, notif = req("GET", "/api/v1/notifications", token=seller_tok)
    notifs = notif.get("notifications") or []
    print(f"[seed] seller notifications count={len(notifs)} unread={notif.get('unread')}")
    if not notifs:
        raise RuntimeError("expected at least one notification for seller after bid")

    state = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "base": BASE,
        "seller_email": seller_email,
        "buyer_email": buyer_email,
        "password": password,
        "seller_id": seller_id,
        "buyer_id": buyer_id,
        "project_id": project_id,
        "project_title": title,
        "bid_id": bid_id,
        "bid_amount": bid_amount,
        "notification_ids": [n["id"] for n in notifs],
        "notification_titles": [n.get("title") for n in notifs],
        "unread_before": notif.get("unread"),
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[seed] wrote {STATE_PATH}")
    return state


def verify(state_path: Path | None = None, label: str = "verify") -> dict:
    path = state_path or STATE_PATH
    state = json.loads(path.read_text(encoding="utf-8"))
    print(f"[{label}] base={state['base']} project_id={state['project_id']}")

    # health users
    _, health = req("GET", "/health")
    users = (health.get("data") or {}).get("users")
    print(f"[{label}] health.users={users} offsite={ (health.get('data') or {}).get('offsite') }")

    # re-login seller
    _, login_s = req(
        "POST",
        "/api/v1/auth/login",
        body={"email": state["seller_email"], "password": state["password"]},
    )
    seller_tok = login_s["token"]
    assert login_s["user"]["id"] == state["seller_id"], "seller id mismatch after login"
    print(f"[{label}] seller login OK id={login_s['user']['id']}")

    # re-login buyer
    _, login_b = req(
        "POST",
        "/api/v1/auth/login",
        body={"email": state["buyer_email"], "password": state["password"]},
    )
    buyer_tok = login_b["token"]
    assert login_b["user"]["id"] == state["buyer_id"], "buyer id mismatch after login"
    print(f"[{label}] buyer login OK id={login_b['user']['id']}")

    # listing mine
    _, mine = req("GET", "/api/v1/projects?mine=true", token=seller_tok)
    projects = mine.get("projects") or []
    found = next((p for p in projects if p["id"] == state["project_id"]), None)
    if not found:
        raise RuntimeError(f"project {state['project_id']} missing from mine list ({len(projects)} items)")
    assert found.get("title") == state["project_title"]
    print(f"[{label}] project OK title={found.get('title')} listing={found.get('listing_status')}")

    # bids
    _, bids = req("GET", f"/api/v1/projects/{state['project_id']}/bids")
    bid_list = bids.get("bids") or []
    bid_found = next((b for b in bid_list if b.get("id") == state["bid_id"]), None)
    if not bid_found:
        # some public bid payloads may omit id — match amount
        bid_found = next((b for b in bid_list if int(b.get("amount") or 0) == int(state["bid_amount"])), None)
    if not bid_found:
        raise RuntimeError(f"bid missing: {bid_list}")
    print(f"[{label}] bid OK amount={bid_found.get('amount')} id={bid_found.get('id')}")

    # notifications
    _, notif = req("GET", "/api/v1/notifications", token=seller_tok)
    notifs = notif.get("notifications") or []
    ids = {n["id"] for n in notifs}
    expected = set(state["notification_ids"])
    missing = expected - ids
    if missing:
        # allow extra notifs; require at least one expected or title match
        titles = {n.get("title") for n in notifs}
        if not any(t in titles for t in (state.get("notification_titles") or [])):
            raise RuntimeError(f"notifications missing expected ids={missing} have={list(ids)[:10]}")
    print(f"[{label}] notifications OK count={len(notifs)} unread={notif.get('unread')}")

    # me still has profile fields
    _, me = req("GET", "/api/v1/me", token=seller_tok)
    assert me["user"].get("email") == state["seller_email"]
    print(f"[{label}] me OK email={me['user'].get('email')} level={me['user'].get('trust',{}).get('level')}")

    result = {
        "ok": True,
        "label": label,
        "users": users,
        "project_id": state["project_id"],
        "bid_id": state["bid_id"],
        "notifications": len(notifs),
        "seller_login": True,
        "buyer_login": True,
    }
    print(f"[{label}] PASS {json.dumps(result, ensure_ascii=False)}")
    return result


def main() -> int:
    global STATE_PATH
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["seed", "verify", "full"])
    ap.add_argument("--state", default=str(STATE_PATH))
    ap.add_argument("--label", default="verify")
    args = ap.parse_args()
    STATE_PATH = Path(args.state)

    if args.cmd == "seed":
        seed()
        return 0
    if args.cmd == "verify":
        verify(STATE_PATH, label=args.label)
        return 0
    if args.cmd == "full":
        seed()
        verify(STATE_PATH, label="after-seed")
        return 0
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
