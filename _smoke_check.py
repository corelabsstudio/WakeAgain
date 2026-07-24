"""Smoke check: API + static + button ID wiring."""
from __future__ import annotations

import re
import random
import subprocess
import shutil
from pathlib import Path

from fastapi.testclient import TestClient
from server import app

ROOT = Path(__file__).resolve().parent
cl = TestClient(app)
errors: list[str] = []
warns: list[str] = []


def ok(label: str, cond: bool, detail: str = "") -> None:
    status = "OK" if cond else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail else ""))
    if not cond:
        errors.append(f"{label}: {detail}")


print("== Pages ==")
for p in [
    "/",
    "/app/",
    "/project.html",
    "/sell.html",
    "/buy.html",
    "/review.html",
    "/legal/terms.html",
    "/legal/privacy.html",
    "/guide/status.html",
    "/guide/credit.html",
    "/guide/dispute.html",
    "/diagnose.html",
    "/showcase.html",
    "/showcase-new.html",
    "/ux9.css",
    "/sitemap.xml",
    "/robots.txt",
    "/admin/",
    "/assets/logo-mark.png",
    "/favicon.ico",
]:
    r = cl.get(p)
    ok(p, r.status_code == 200, str(r.status_code))

print("== 404 ==")
r404 = cl.get("/this-page-does-not-exist-wakeagain")
ok("pretty 404", r404.status_code == 404 and "페이지" in r404.text, str(r404.status_code))

print("== Public API ==")
for p in [
    "/health",
    "/api/v1/health",
    "/api/v1/config",
    "/api/v1/stats",
    "/api/v1/projects",
    "/api/v1/auctions/live",
    "/api/v1/credit-policy",
    "/api/v1/pricing",
    "/api/v1/reviews",
    "/api/v1/showcases",
]:
    r = cl.get(p)
    ok(p, r.status_code == 200, str(r.status_code))
    if p in ("/health", "/api/v1/health") and r.status_code == 200:
        body = r.json()
        ok(f"{p} has scheduler", "scheduler" in body or p == "/api/v1/health")
    if p == "/api/v1/config" and r.status_code == 200:
        cfg = r.json()
        ok("config.credit_policy", "credit_policy" in cfg)
        ok(
            "config.report_policy",
            "report_policy" in (cfg.get("trust_policy") or {}),
        )
        ok(
            "config.block_policy",
            "block_policy" in (cfg.get("trust_policy") or {}),
        )
        ok("config.oauth", "oauth" in cfg)
        pay = cfg.get("payment_policy") or {}
        ok("config.background_scheduler", pay.get("background_scheduler") is True)

print("== Showcase gate ==")
r_sc = cl.post(
    "/api/v1/showcases",
    json={
        "author_name": "x",
        "title": "x",
        "one_liner": "한줄",
        "story": "",
        "status_key": "prototype",
        "product_type": "webapp",
    },
)
ok("showcase requires diag_score", r_sc.status_code == 400, r_sc.text[:80])
sc_title = f"스모크 자랑 {random.randint(100000, 999999)}"
r_sc2 = cl.post(
    "/api/v1/showcases",
    json={
        "author_name": "스모크",
        "title": sc_title,
        "one_liner": "진단 후 자랑",
        "story": "선택 한줄",
        "status_key": "prototype",
        "product_type": "webapp",
        "diag_score": 72,
        "price_hint": 150000,
    },
)
ok("showcase with diag ok", r_sc2.status_code == 200, r_sc2.text[:80])

print("== Auth / profile / create / bid ==")
email = f"smoke{random.randint(10000, 99999)}@example.com"
r = cl.post(
    "/api/v1/auth/register",
    json={
        "email": email,
        "password": "testpass12",
        "display_name": "Smoke",
        "birth_date": "1995-06-15",
        "confirm_age_14": True,
    },
)
ok("register", r.status_code == 200, r.text[:120])
# under-14 must be rejected
r_u14 = cl.post(
    "/api/v1/auth/register",
    json={
        "email": f"u14{random.randint(10000, 99999)}@example.com",
        "password": "testpass12",
        "display_name": "Kid",
        "birth_date": "2020-01-01",
        "confirm_age_14": True,
    },
)
ok("register_block_under14", r_u14.status_code == 403, r_u14.text[:120])
token = r.json().get("token") if r.status_code == 200 else None
code = r.json().get("dev_email_code") if r.status_code == 200 else None
h = {"Authorization": f"Bearer {token}"} if token else {}
if token and code:
    r = cl.post("/api/v1/auth/verify-email", headers=h, json={"code": code})
    ok("verify", r.status_code == 200)
    r = cl.put(
        "/api/v1/me/profile",
        headers=h,
        json={
            "real_name": "스모크",
            "phone": "01011112222",
            "role": "both",
            "display_name": "Smoke",
        },
    )
    ok("profile L2", r.status_code == 200, str(r.json().get("user", {}).get("trust", {}).get("level")))
    r = cl.put(
        "/api/v1/me/settlement",
        headers=h,
        json={
            "holder": "스모크",
            "bank": "카카오",
            "account": "110123456789",
            "is_business": False,
        },
    )
    ok("settlement L3", r.status_code == 200, str(r.json().get("user", {}).get("credit", {}).get("score")))
    # create blocked without seller identity
    r_nosid = cl.post(
        "/api/v1/projects",
        headers=h,
        json={
            "title": "스모크 매물",
            "one_liner": "테스트 한줄",
            "status": "프로토타입",
            "story": "스모크 테스트용 스토리입니다.",
            "demo": "https://example.com",
            "assets": ["code"],
            "keywords": ["스모크", "테스트", "SaaS"],
            "price_start": 2000000,
            "auction_days": 5,
            "license_note": "MIT",
            "attest_works": True,
            "attest_license": True,
            "attest_rights": True,
        },
    )
    ok(
        "create blocked without seller identity",
        r_nosid.status_code == 403,
        r_nosid.text[:120],
    )
    r = cl.put(
        "/api/v1/me/seller-identity",
        headers=h,
        json={
            "seller_type": "individual",
            "trade_name": "스모크판매자",
            "contact_email": email,
            "contact_phone": "01011112222",
            "address": "서울 테스트구",
            "mail_order_report_no": "",
        },
    )
    ok(
        "seller identity",
        r.status_code == 200
        and r.json().get("user", {}).get("trust", {}).get("seller_identity_complete"),
        r.text[:100],
    )
    # public API must NOT leak full phone
    preview = (r.json() or {}).get("public_preview") or {}
    ok(
        "public phone masked",
        "****" in str(preview.get("contact_phone") or "")
        and "2222" not in str(preview.get("contact_phone") or "").replace("*", ""),
        str(preview.get("contact_phone")),
    )
    ok(
        "public email masked",
        "***" in str(preview.get("contact_email") or ""),
        str(preview.get("contact_email")),
    )
    # missing attest must fail
    r_bad = cl.post(
        "/api/v1/projects",
        headers=h,
        json={
            "title": "스모크 매물",
            "one_liner": "테스트 한줄",
            "status": "프로토타입",
            "story": "스모크 테스트용 스토리입니다.",
            "demo": "https://example.com",
            "assets": ["code"],
            "price_start": 2000000,
            "auction_days": 5,
        },
    )
    ok("create blocked without attest", r_bad.status_code == 400, r_bad.text[:100])
    r = cl.post(
        "/api/v1/projects",
        headers=h,
        json={
            "title": "스모크 매물",
            "one_liner": "테스트 한줄",
            "status": "프로토타입",
            "story": "스모크 테스트용 스토리입니다.",
            "demo": "https://example.com",
            "assets": ["code"],
            "keywords": ["스모크", "테스트", "SaaS", "웹앱", "데모"],
            "price_start": 2000000,
            "auction_days": 5,
            "license_note": "MIT",
            "attest_works": True,
            "attest_license": True,
            "attest_rights": True,
        },
    )
    ok("create project", r.status_code == 200, r.text[:100])
    pid = None
    if r.status_code == 200:
        pid = r.json().get("project", {}).get("id")
    r = cl.post("/api/v1/auth/login", json={"email": email, "password": "testpass12"})
    ok("login", r.status_code == 200 and bool(r.json().get("token")))
    r = cl.get("/api/v1/me", headers=h)
    ok("me has credit", r.status_code == 200 and "credit" in r.json().get("user", {}))

    # --- buyer reports → auto pause at 3 ---
    if pid:
        admin_h = {"X-Admin-Key": "wakeagain-admin-dev"}
        r = cl.post(
            f"/api/v1/admin/projects/{pid}/review",
            headers=admin_h,
            json={
                "action": "approve",
                "note": "smoke approve",
                "checklist": {"demo_ok": True},
            },
        )
        ok("admin approve for report test", r.status_code == 200, r.text[:80])
        for i in range(3):
            be = f"buyer{i}{random.randint(1000,9999)}@example.com"
            rr = cl.post(
                "/api/v1/auth/register",
                json={
                    "email": be,
                    "password": "testpass12",
                    "display_name": f"Buyer{i}",
                    "birth_date": "1992-03-01",
                    "confirm_age_14": True,
                },
            )
            bt = rr.json().get("token")
            bc = rr.json().get("dev_email_code")
            bh = {"Authorization": f"Bearer {bt}"}
            if bc:
                cl.post("/api/v1/auth/verify-email", headers=bh, json={"code": bc})
            cl.put(
                "/api/v1/me/profile",
                headers=bh,
                json={
                    "real_name": f"구매{i}",
                    "phone": f"0102222{i:04d}",
                    "role": "buyer",
                    "display_name": f"Buyer{i}",
                },
            )
            reasons = ["low_quality", "plagiarism", "not_working"]
            rrep = cl.post(
                f"/api/v1/projects/{pid}/report",
                headers=bh,
                json={"reason": reasons[i], "detail": f"smoke report {i}"},
            )
            ok(f"report {i+1}", rrep.status_code == 200, rrep.text[:100])
            if i == 2 and rrep.status_code == 200:
                actions = rrep.json().get("actions") or {}
                ok(
                    "auto pause at 3 reports",
                    bool(actions.get("auction_paused"))
                    or (rrep.json().get("project") or {}).get("is_paused"),
                    str(actions),
                )
        # self-report blocked
        rself = cl.post(
            f"/api/v1/projects/{pid}/report",
            headers=h,
            json={"reason": "fraud", "detail": "self"},
        )
        ok("owner cannot report self", rself.status_code in (400, 403), rself.text[:80])

print("== OAuth ==")
r = cl.get("/api/v1/auth/oauth/google/start", follow_redirects=False)
ok(
    "oauth start without keys → 503",
    r.status_code == 503,
    str(r.status_code),
)
r = cl.put(
    "/api/v1/me/birth-date",
    headers=h if "h" in dir() else {},
    json={"birth_date": "1990-01-01", "confirm_age_14": True},
)
# h may be from auth block
ok("birth-date endpoint exists", r.status_code in (200, 401, 403), str(r.status_code))

print("== App button IDs ==")
app_html = (ROOT / "public/app/index.html").read_text(encoding="utf-8")
app_js = (ROOT / "public/app/app.js").read_text(encoding="utf-8")
html_ids = set(re.findall(r'id="([^"]+)"', app_html))
required = set(re.findall(r'\$\("([^"]+)"\)\.addEventListener', app_js))
missing = sorted(required - html_ids)
ok("app.js listeners have HTML ids", not missing, str(missing))

print("== Critical page elements ==")
index = (ROOT / "public/index.html").read_text(encoding="utf-8")
for eid in ["listingGrid", "listingsMore", "navAuthLink"]:
    ok(f"index#{eid}", f'id="{eid}"' in index)
for href in ["/app/#list", "/sell.html", "/buy.html", "/guide/credit.html", "/app/#new"]:
    ok(f"index link {href}", href in index)
proj = (ROOT / "public/project.html").read_text(encoding="utf-8")
for eid in ["bidForm", "bidBtn", "buyNowBtn", "closeDealBtn", "msgForm", "sellerLine"]:
    ok(f"project#{eid}", f'id="{eid}"' in proj)

print("== JS syntax (node --check) ==")
if shutil.which("node"):
    for rel in [
        "public/app/app.js",
        "public/js/api.js",
        "public/js/listings.js",
        "public/js/hero-stats.js",
        "public/js/reviews.js",
        "public/js/motion.js",
    ]:
        r = subprocess.run(["node", "--check", str(ROOT / rel)], capture_output=True, text=True)
        ok(rel, r.returncode == 0, (r.stderr or "")[:120])
else:
    warns.append("node not installed; skipped syntax check")

print()
print("== SUMMARY ==")
if warns:
    print("Warnings:")
    for w in warns:
        print(" -", w)
if errors:
    print(f"FAILED ({len(errors)}):")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)
print("All checks passed.")
