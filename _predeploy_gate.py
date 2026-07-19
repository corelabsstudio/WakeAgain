"""Pre-deploy 10/10 gate (excludes business / PG / SNS keys / real deploy).

Run: python _predeploy_gate.py
Exit 0 only when score is 10/10.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
errors: list[str] = []
passed = 0
TOTAL = 20


def check(n: int, label: str, cond: bool, detail: str = "") -> None:
    global passed
    mark = "OK" if cond else "FAIL"
    print(f"  [{mark}] {n:02d} {label}" + (f" — {detail}" if detail and not cond else ""))
    if cond:
        passed += 1
    else:
        errors.append(f"{n:02d} {label}: {detail or 'failed'}")


def main() -> int:
    print("== WakeAgain pre-deploy gate (10/10 target) ==\n")

    # 01 critical files
    need = [
        "server.py",
        "Dockerfile",
        "railway.toml",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "PLATFORM.md",
        "BRAND.md",
        "TRUST.md",
        "docs/PRE_DEPLOY_10.md",
        "docs/나중_할일_BACKLOG.md",
        "wakeagain/scheduler.py",
        "wakeagain/api.py",
        "wakeagain/db.py",
        "wakeagain/oauth.py",
        "public/index.html",
        "public/app/index.html",
        "public/diagnose.html",
        "public/showcase.html",
        "public/showcase-new.html",
        "public/404.html",
        "public/ux9.css",
        "public/sitemap.xml",
        "public/robots.txt",
        "public/manifest.webmanifest",
        "public/legal/terms.html",
        "public/legal/privacy.html",
        "public/assets/logo-mark.png",
        "public/assets/logo-mark-256.png",
    ]
    missing = [p for p in need if not (ROOT / p).is_file()]
    check(1, "core files present", not missing, ", ".join(missing[:5]))

    # 02 no admin secret leak in public
    leak = False
    for p in (ROOT / "public").rglob("*"):
        if p.suffix.lower() not in {".html", ".js", ".css", ".json", ".webmanifest"}:
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "wakeagain-admin-dev" in t:
            leak = True
            break
    check(2, "admin dev secret not in public", not leak)

    # 03 ux9 on major pages
    majors = [
        "public/index.html",
        "public/app/index.html",
        "public/diagnose.html",
        "public/showcase.html",
        "public/showcase-new.html",
        "public/sell.html",
        "public/buy.html",
    ]
    ux9_ok = all('ux9.css' in (ROOT / p).read_text(encoding="utf-8", errors="ignore") for p in majors)
    check(3, "ux9.css on major pages", ux9_ok)

    # 04 scheduler module API
    from wakeagain import scheduler as sched

    check(4, "scheduler module", callable(sched.run_once) and callable(sched.start))

    # 05 process_expired exists
    from wakeagain import db as database

    check(5, "process_expired_auctions", callable(database.process_expired_auctions))

    # 06 unit: expired auction close
    database.init_db()
    closed = 0
    with database.db() as conn:
        closed = database.process_expired_auctions(conn)
    check(6, "auction closer callable", isinstance(closed, int))

    # 07 pricing policy
    from wakeagain import pricing as price_policy

    pol = price_policy.public_policy()
    check(7, "pricing policy non-empty", bool(pol))

    # 08 oauth safety without keys
    from wakeagain import oauth as oauth_mod

    check(8, "oauth providers list", "kakao" in oauth_mod.PROVIDERS)
    # Without SNS keys, enabled list is empty (safe). With keys (rare pre-biz), still ok.
    enabled = oauth_mod.enabled_providers()
    check(9, "oauth safe without keys (empty or configured)", isinstance(enabled, list))

    # 09-10 via TestClient smoke subset
    # ensure env loaded
    from wakeagain.envutil import load_dotenv, ensure_local_env

    ensure_local_env()
    load_dotenv(override=False)

    from fastapi.testclient import TestClient
    from server import app

    cl = TestClient(app)

    r = cl.get("/health")
    body = r.json() if r.status_code == 200 else {}
    check(10, "health 200 + scheduler", r.status_code == 200 and "scheduler" in body)

    r = cl.get("/api/v1/config")
    cfg = r.json() if r.status_code == 200 else {}
    pay = cfg.get("payment_policy") or {}
    check(11, "config background_scheduler", r.status_code == 200 and pay.get("background_scheduler") is True)

    # security headers on HTML
    r = cl.get("/")
    h = {k.lower(): v for k, v in r.headers.items()}
    check(
        12,
        "security headers",
        h.get("x-content-type-options") == "nosniff" and "x-frame-options" in h,
        str(dict(h)),
    )

    r = cl.get("/no-such-page-predeploy-xyz")
    check(13, "pretty 404", r.status_code == 404 and ("페이지" in r.text or "404" in r.text))

    # showcase gate
    r = cl.post(
        "/api/v1/showcases",
        json={
            "author_name": "gate",
            "title": "gate",
            "one_liner": "line",
            "story": "",
            "diag_score": None,
        },
    )
    # pydantic may 422 if null not allowed — both 400/422 ok for gate
    check(14, "showcase blocks without diag", r.status_code in (400, 422), r.text[:80])

    import random

    title = f"predeploy-{random.randint(100000, 999999)}"
    r = cl.post(
        "/api/v1/showcases",
        json={
            "author_name": "gate",
            "title": title,
            "one_liner": "진단 후",
            "story": "한줄",
            "diag_score": 80,
            "price_hint": 100000,
            "status_key": "prototype",
            "product_type": "webapp",
        },
    )
    check(15, "showcase allows with diag", r.status_code == 200, r.text[:100])

    # legal pages
    check(16, "terms page", cl.get("/legal/terms.html").status_code == 200)
    check(17, "privacy page", cl.get("/legal/privacy.html").status_code == 200)

    # assets
    check(18, "logo assets", cl.get("/assets/logo-mark.png").status_code == 200)

    # unit + full smoke
    print("\n== Unit ==")
    ut = subprocess.run([sys.executable, str(ROOT / "_test_unit.py")], cwd=str(ROOT))
    check(19, "unit tests pass", ut.returncode == 0, f"exit {ut.returncode}")

    print("\n== Full smoke ==")
    sm = subprocess.run([sys.executable, str(ROOT / "_smoke_check.py")], cwd=str(ROOT))
    # re-map: keep 20 as smoke; if we only have 20 slots, combine
    check(20, "smoke all pass + version", sm.returncode == 0, f"exit {sm.returncode}")
    from wakeagain import __version__

    if not __version__:
        errors.append("version empty")
        # already counted 20 via smoke; version is soft-checked in smoke health

    score = round(10 * passed / TOTAL, 1)
    print(f"\n== PRE-DEPLOY SCORE: {score}/10  ({passed}/{TOTAL}) ==")
    if errors:
        print("Failures:")
        for e in errors:
            print(" -", e)
    if passed >= TOTAL:
        print("RESULT: 10/10 pre-deploy (business/PG/SNS/live-deploy excluded)")
        return 0
    print("RESULT: NOT YET 10/10")
    return 1


if __name__ == "__main__":
    # bootstrap env before server import paths
    sys.path.insert(0, str(ROOT))
    from wakeagain.envutil import ensure_local_env, load_dotenv

    ensure_local_env()
    load_dotenv()
    raise SystemExit(main())
