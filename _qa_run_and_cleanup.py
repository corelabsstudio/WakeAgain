# -*- coding: utf-8 -*-
"""WakeAgain QA: local auction suite (isolated DB) + live smoke/bid probe + cleanup.

Run:
  python _qa_run_and_cleanup.py
"""
from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT: dict = {
    "started": datetime.now(timezone.utc).isoformat(),
    "local": {},
    "live": {},
    "cleanup": {},
    "bugs": [],
    "ok": [],
}


def note_ok(msg: str) -> None:
    print(f"  [OK] {msg}")
    REPORT["ok"].append(msg)


def note_bug(msg: str) -> None:
    print(f"  [BUG] {msg}")
    REPORT["bugs"].append(msg)


def load_prod_secrets() -> dict[str, str]:
    p = ROOT / ".launch" / "production-secrets.local.txt"
    out: dict[str, str] = {}
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def run_local_suites() -> None:
    print("\n== LOCAL suites (isolated DATA_DIR) ==")
    data_dir = Path(tempfile.mkdtemp(prefix="wa_qa_"))
    env = os.environ.copy()
    env["DATA_DIR"] = str(data_dir)
    env["ADMIN_SECRET"] = "wakeagain-admin-dev"
    env["EMAIL_DEV_MODE"] = "1"
    env["APP_SECRET"] = "qa-local-app-secret-not-prod"
    env["JWT_SECRET"] = "qa-local-jwt-secret-not-prod"
    env["AUCTION_SCHEDULER"] = "0"
    # avoid loading production .env secrets into tests
    env.pop("DATABASE_URL", None)

    suites = [
        ("unit", "_test_unit.py"),
        ("smoke", "_smoke_check.py"),
        ("auction_suite", "_auction_suite_test.py"),
        ("auction_advanced", "_auction_advanced_test.py"),
        ("deal_flow", "_deal_flow_test.py"),
        ("block_user", "_block_user_test.py"),
    ]
    results = {}
    py = sys.executable
    for name, script in suites:
        path = ROOT / script
        if not path.is_file():
            results[name] = {"skip": True, "reason": "missing"}
            continue
        print(f"\n-- {name} --")
        t0 = time.time()
        try:
            p = subprocess.run(
                [py, str(path)],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
                encoding="utf-8",
                errors="replace",
            )
            dur = round(time.time() - t0, 1)
            out = (p.stdout or "") + "\n" + (p.stderr or "")
            # keep last 40 lines in report
            tail = "\n".join(out.splitlines()[-40:])
            ok = p.returncode == 0
            results[name] = {
                "exit": p.returncode,
                "sec": dur,
                "ok": ok,
                "tail": tail,
            }
            print(f"exit={p.returncode} sec={dur}")
            # surface FAIL lines
            fails = [ln for ln in out.splitlines() if "[FAIL]" in ln or "FAIL" == ln.strip()[-4:]]
            for ln in fails[:20]:
                print(" ", ln)
                if "[FAIL]" in ln:
                    note_bug(f"local/{name}: {ln.strip()}")
            if ok:
                note_ok(f"local/{name} passed ({dur}s)")
            else:
                note_bug(f"local/{name} exit {p.returncode}")
                # print a bit more context
                print(tail[-1500:])
        except subprocess.TimeoutExpired:
            results[name] = {"ok": False, "exit": -1, "sec": 300, "error": "timeout"}
            note_bug(f"local/{name} timeout")
        except Exception as e:
            results[name] = {"ok": False, "error": str(e)}
            note_bug(f"local/{name} exception: {e}")

    # cleanup temp data dir
    try:
        shutil.rmtree(data_dir, ignore_errors=True)
        note_ok(f"local DATA_DIR removed ({data_dir.name})")
    except Exception as e:
        note_bug(f"local DATA_DIR cleanup failed: {e}")

    REPORT["local"] = results


def http_json(method: str, url: str, *, headers: dict | None = None, body: dict | None = None, timeout: int = 30):
    data = None
    hdrs = {"Accept": "application/json", "User-Agent": "WakeAgain-QA/1.0"}
    if headers:
        hdrs.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read().decode("utf-8", errors="replace")
            try:
                return res.status, json.loads(raw)
            except Exception:
                return res.status, {"_raw": raw[:500]}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"_raw": raw[:500]}
    except Exception as e:
        return 0, {"_error": str(e)}


def run_live_probe(base: str, admin_key: str) -> None:
    print("\n== LIVE API probe ==")
    live: dict = {"base": base, "endpoints": {}, "auction": {}}

    endpoints = [
        ("GET", "/health"),
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/config"),
        ("GET", "/api/v1/stats"),
        ("GET", "/api/v1/projects?limit=10"),
        ("GET", "/api/v1/auctions/live"),
        ("GET", "/api/v1/reviews?limit=5"),
        ("GET", "/api/v1/showcases?limit=5"),
        ("GET", "/api/v1/pricing"),
        ("GET", "/api/v1/credit-policy"),
        ("GET", "/"),
        ("GET", "/app/"),
        ("GET", "/sell.html"),
        ("GET", "/buy.html"),
        ("GET", "/project.html"),
        ("GET", "/diagnose.html"),
        ("GET", "/yard-theme.css?v=20260729-logo"),
        ("GET", "/assets/logo-mark-yard.png"),
        ("GET", "/js/i18n-messages.js?v=20260725e"),
        ("GET", "/js/reviews.js?v=20260729-quote"),
    ]
    for method, path in endpoints:
        st, body = http_json(method, base + path)
        ok = 200 <= st < 400
        live["endpoints"][path] = st
        if ok:
            note_ok(f"live {method} {path} -> {st}")
        else:
            note_bug(f"live {method} {path} -> {st} {str(body)[:120]}")

    # admin session
    st, body = http_json("GET", base + "/api/v1/admin/session", headers={"X-Admin-Key": admin_key})
    live["admin_session"] = st
    if st == 200:
        note_ok("live admin session ok")
    else:
        note_bug(f"live admin session -> {st}")

    # snapshot before
    st, stats0 = http_json("GET", base + "/api/v1/stats")
    live["stats_before"] = stats0 if st == 200 else {"status": st}

    # attempt register + bid path
    stamp = datetime.now(timezone.utc).strftime("%m%d%H%M%S")
    n = random.randint(1000, 9999)
    seller_email = f"qa_seller_{stamp}_{n}@example.com"
    buyer_email = f"qa_buyer_{stamp}_{n}@example.com"
    password = "QaTestPass12!"
    created_user_ids: list[int] = []
    created_project_ids: list[int] = []

    def register(email: str, name: str):
        return http_json(
            "POST",
            base + "/api/v1/auth/register",
            body={
                "email": email,
                "password": password,
                "display_name": name,
                "birth_date": "1992-05-15",
                "confirm_age_14": True,
            },
        )

    st_s, body_s = register(seller_email, f"QA판매{n}")
    st_b, body_b = register(buyer_email, f"QA구매{n}")
    live["register_seller"] = st_s
    live["register_buyer"] = st_b

    if st_s != 200:
        note_bug(f"live seller register -> {st_s} {str(body_s)[:160]}")
    else:
        note_ok("live seller registered")
        uid = (body_s.get("user") or {}).get("id")
        if uid:
            created_user_ids.append(int(uid))

    if st_b != 200:
        note_bug(f"live buyer register -> {st_b} {str(body_b)[:160]}")
    else:
        note_ok("live buyer registered")
        uid = (body_b.get("user") or {}).get("id")
        if uid:
            created_user_ids.append(int(uid))

    token_s = body_s.get("token") if st_s == 200 else None
    token_b = body_b.get("token") if st_b == 200 else None

    # try email verify with dev code if present
    for label, tok, body in (("seller", token_s, body_s), ("buyer", token_b, body_b)):
        if not tok:
            continue
        code = body.get("dev_email_code")
        if code:
            stv, bv = http_json(
                "POST",
                base + "/api/v1/auth/verify-email",
                headers={"Authorization": f"Bearer {tok}"},
                body={"code": code},
            )
            if stv == 200 and bv.get("token"):
                if label == "seller":
                    token_s = bv["token"]
                else:
                    token_b = bv["token"]
                note_ok(f"live {label} email verified (dev code)")
            else:
                note_bug(f"live {label} verify-email -> {stv}")
        else:
            # admin force-verify
            uid = (body.get("user") or {}).get("id")
            if uid and admin_key:
                stv, bv = http_json(
                    "POST",
                    base + f"/api/v1/admin/users/{uid}/verify-email",
                    headers={"X-Admin-Key": admin_key},
                )
                if stv == 200:
                    note_ok(f"live {label} admin verify-email")
                else:
                    note_bug(f"live {label} admin verify-email -> {stv} {str(bv)[:120]}")

    # profile for both
    for label, tok in (("seller", token_s), ("buyer", token_b)):
        if not tok:
            continue
        st, b = http_json(
            "PUT",
            base + "/api/v1/me/profile",
            headers={"Authorization": f"Bearer {tok}"},
            body={
                "real_name": f"QA실명{label}",
                "phone": f"010{random.randint(10000000, 99999999)}",
                "role": "both",
                "display_name": f"QA{label}{n}",
            },
        )
        if st == 200:
            note_ok(f"live {label} profile")
            if b.get("token"):
                if label == "seller":
                    token_s = b["token"]
                else:
                    token_b = b["token"]
        else:
            note_bug(f"live {label} profile -> {st} {str(b)[:140]}")

    # seller settlement + identity
    if token_s:
        st, b = http_json(
            "PUT",
            base + "/api/v1/me/settlement",
            headers={"Authorization": f"Bearer {token_s}"},
            body={
                "holder": "QA실명seller",
                "bank": "카카오뱅크",
                "account": f"3333{random.randint(10000000, 99999999)}",
                "is_business": False,
            },
        )
        live["settlement"] = st
        if st == 200:
            note_ok("live seller settlement")
        else:
            note_bug(f"live seller settlement -> {st} {str(b)[:140]}")

        st, b = http_json(
            "PUT",
            base + "/api/v1/me/seller-identity",
            headers={"Authorization": f"Bearer {token_s}"},
            body={
                "seller_type": "individual",
                "trade_name": "QA테스트판매",
                "contact_email": seller_email,
                "contact_phone": "01011112222",
                "address": "서울",
                "mail_order_report_no": "",
            },
        )
        live["seller_identity"] = st
        if st == 200:
            note_ok("live seller identity")
        else:
            note_bug(f"live seller identity -> {st} {str(b)[:140]}")

        # create listing
        st, b = http_json(
            "POST",
            base + "/api/v1/projects",
            headers={"Authorization": f"Bearer {token_s}"},
            body={
                "title": f"[QA삭제예정] 입찰테스트 {stamp}",
                "one_liner": "자동 QA — 완료 후 삭제",
                "status": "프로토타입",
                "product_type": "webapp",
                "story": "QA 자동화 테스트 매물. 완료 후 삭제합니다.",
                "demo": "https://example.com/qa-demo",
                "assets": ["code"],
                "price_start": 300_000,
                "auction_days": 2,
                "min_increment": 10_000,
                "license_note": "QA",
                "keywords": ["QA", "테스트", "삭제예정", "웹앱", "입찰"],
                "attest_works": True,
                "attest_license": True,
                "attest_rights": True,
            },
        )
        live["create_project"] = st
        if st == 200:
            pid = int((b.get("project") or {}).get("id") or 0)
            created_project_ids.append(pid)
            note_ok(f"live listing created id={pid}")
            # approve
            st_a, ba = http_json(
                "POST",
                base + f"/api/v1/admin/projects/{pid}/review",
                headers={"X-Admin-Key": admin_key},
                body={"action": "approve", "note": "qa", "checklist": {"demo_ok": True}},
            )
            live["approve"] = st_a
            if st_a == 200:
                note_ok(f"live listing approved id={pid}")
            else:
                note_bug(f"live approve -> {st_a} {str(ba)[:140]}")

            # bid
            if token_b and st_a == 200:
                st_bid, bb = http_json(
                    "POST",
                    base + f"/api/v1/projects/{pid}/bids",
                    headers={"Authorization": f"Bearer {token_b}"},
                    body={"amount": 310_000},
                )
                live["bid"] = st_bid
                if st_bid == 200:
                    note_ok("live bid 310000 ok")
                else:
                    note_bug(f"live bid -> {st_bid} {str(bb)[:180]}")

                # second bid lower (should fail)
                st_low, bl = http_json(
                    "POST",
                    base + f"/api/v1/projects/{pid}/bids",
                    headers={"Authorization": f"Bearer {token_b}"},
                    body={"amount": 300_000},
                )
                live["bid_low"] = st_low
                if st_low >= 400:
                    note_ok(f"live low bid correctly rejected ({st_low})")
                else:
                    note_bug(f"live low bid should fail, got {st_low}")

                # interest
                st_i, bi = http_json(
                    "POST",
                    base + f"/api/v1/projects/{pid}/interest",
                    headers={"Authorization": f"Bearer {token_b}"},
                )
                live["interest"] = st_i
                if st_i in (200, 201):
                    note_ok("live interest ok")
                else:
                    # some APIs return 400 if already interested etc.
                    note_bug(f"live interest -> {st_i} {str(bi)[:120]}")

                # fetch project + bids public
                st_p, bp = http_json("GET", base + f"/api/v1/projects/{pid}")
                st_bids, bbids = http_json("GET", base + f"/api/v1/projects/{pid}/bids")
                live["project_get"] = st_p
                live["bids_get"] = st_bids
                if st_p == 200:
                    note_ok("live project detail ok")
                else:
                    note_bug(f"live project detail -> {st_p}")
                if st_bids == 200:
                    note_ok(f"live bids list ok count={len(bbids.get('bids') or bbids.get('items') or [])}")
                else:
                    note_bug(f"live bids list -> {st_bids}")
        else:
            note_bug(f"live create project -> {st} {str(b)[:180]}")

    # cleanup live test users (and their projects)
    print("\n== LIVE cleanup ==")
    cleanup = {"user_ids": created_user_ids, "project_ids": created_project_ids}
    if created_user_ids and admin_key:
        st_c, bc = http_json(
            "POST",
            base + "/api/v1/admin/users/delete",
            headers={"X-Admin-Key": admin_key},
            body={"confirm": "DELETE_SELECTED_USERS", "user_ids": created_user_ids},
        )
        cleanup["delete_status"] = st_c
        cleanup["delete_body"] = {
            k: bc.get(k)
            for k in ("ok", "message", "users_before", "users_after", "deleted", "detail", "_raw", "_error")
            if bc.get(k) is not None
        }
        if st_c == 200 and bc.get("ok"):
            note_ok(f"live deleted QA users {created_user_ids}")
        else:
            note_bug(f"live user delete -> {st_c} {str(bc)[:200]}")
            # try reject/hide projects at least
            for pid in created_project_ids:
                st_r, br = http_json(
                    "POST",
                    base + f"/api/v1/admin/projects/{pid}/review",
                    headers={"X-Admin-Key": admin_key},
                    body={"action": "reject", "note": "QA cleanup"},
                )
                if st_r == 200:
                    note_ok(f"live rejected leftover project {pid}")
                else:
                    note_bug(f"live reject project {pid} -> {st_r} {str(br)[:120]}")
    else:
        note_bug("live cleanup skipped (no user ids or admin key)")

    st, stats1 = http_json("GET", base + "/api/v1/stats")
    live["stats_after"] = stats1 if st == 200 else {"status": st}
    # public projects should still be 0 (or unchanged approved)
    if st == 200:
        approved = stats1.get("projects_approved")
        if approved == 0 or approved == (stats0 or {}).get("projects_approved"):
            note_ok(f"live projects_approved after cleanup = {approved}")
        else:
            note_bug(f"live projects_approved changed unexpectedly: before={(stats0 or {}).get('projects_approved')} after={approved}")

    REPORT["live"] = live
    REPORT["cleanup"] = cleanup


def run_playwright_buttons(base: str) -> None:
    print("\n== LIVE browser button/nav smoke ==")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        note_bug("playwright not installed — skip UI smoke")
        return

    findings = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page_errors: list[str] = []
        failed_req: list[str] = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on(
            "requestfailed",
            lambda r: failed_req.append(f"{r.url} {r.failure}")
            if r.resource_type in ("document", "script", "xhr", "fetch")
            else None,
        )

        page.goto(base + "/?landing=1", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(800)
        if page_errors:
            for e in page_errors:
                note_bug(f"home pageerror: {e}")
        else:
            note_ok("home no pageerror")

        # key CTAs visible
        for sel, label in [
            ("a.btn-primary", "primary CTA"),
            ("text=내 프로젝트 올리기", "nav list CTA"),
            ("text=마켓", "nav market"),
        ]:
            try:
                loc = page.locator(sel).first
                if loc.count() == 0:
                    note_bug(f"UI missing: {label} ({sel})")
                else:
                    note_ok(f"UI present: {label}")
            except Exception as e:
                note_bug(f"UI check {label}: {e}")

        # click diagnose CTA if present
        try:
            link = page.locator('a[href="/diagnose.html"]').first
            if link.count():
                link.click(timeout=5000)
                page.wait_for_load_state("networkidle", timeout=30000)
                note_ok(f"clicked diagnose -> {page.url}")
            else:
                note_bug("diagnose link not found on home")
        except Exception as e:
            note_bug(f"diagnose click failed: {e}")

        # app shell
        page_errors.clear()
        page.goto(base + "/app/#login", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1000)
        if page_errors:
            for e in page_errors[:5]:
                note_bug(f"app pageerror: {e}")
        else:
            note_ok("app/#login no pageerror")

        # sell page
        page_errors.clear()
        page.goto(base + "/sell.html", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(600)
        if page_errors:
            for e in page_errors[:5]:
                note_bug(f"sell pageerror: {e}")
        else:
            note_ok("sell.html no pageerror")

        # buy page
        page_errors.clear()
        page.goto(base + "/buy.html", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(600)
        if page_errors:
            for e in page_errors[:5]:
                note_bug(f"buy pageerror: {e}")
        else:
            note_ok("buy.html no pageerror")

        if failed_req:
            for fr in failed_req[:8]:
                note_bug(f"requestfailed: {fr[:180]}")
        else:
            note_ok("no critical requestfailed")

        browser.close()
    REPORT["live"]["ui"] = {"findings": findings, "pageerrors_checked": True}


def main() -> int:
    print("WakeAgain QA run", datetime.now().isoformat(timespec="seconds"))
    secrets = load_prod_secrets()
    admin = secrets.get("ADMIN_SECRET") or os.environ.get("ADMIN_SECRET") or ""
    base = (secrets.get("URL") or "https://wakeagain.com").rstrip("/")
    # prefer custom domain
    if "railway.app" in base:
        base = "https://wakeagain.com"

    run_local_suites()
    if admin:
        run_live_probe(base, admin)
    else:
        note_bug("no ADMIN_SECRET — skip live write/cleanup")
        # still read-only live
        st, body = http_json("GET", base + "/health")
        if st == 200:
            note_ok("live health ok (read-only)")
        else:
            note_bug(f"live health -> {st}")

    run_playwright_buttons(base)

    REPORT["ended"] = datetime.now(timezone.utc).isoformat()
    REPORT["summary"] = {
        "ok_count": len(REPORT["ok"]),
        "bug_count": len(REPORT["bugs"]),
        "bugs": REPORT["bugs"],
    }
    out = ROOT / "docs" / "marketing" / "logs" / f"qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(REPORT, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n== SUMMARY ==")
    print(f"OK: {len(REPORT['ok'])}  BUGS: {len(REPORT['bugs'])}")
    for b in REPORT["bugs"]:
        print(" -", b)
    print("report:", out)
    return 0 if not REPORT["bugs"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
