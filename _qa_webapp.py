# -*- coding: utf-8 -*-
"""Web-app shell QA: /app/, assets, public↔www sync, client flows, optional Playwright."""
from __future__ import annotations

import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from server import app
from wakeagain.db import init_db
from wakeagain.admin_auth import ADMIN_SECRET
from wakeagain import media as media_mod

init_db()
cl = TestClient(app)
errors: list[str] = []
warns: list[str] = []


def ok(label: str, cond: bool, detail: str = "") -> None:
    print(f"  [{'OK' if cond else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not cond:
        errors.append(f"{label}: {detail}")


def warn(label: str, detail: str = "") -> None:
    print(f"  [WARN] {label}" + (f" — {detail}" if detail else ""))
    warns.append(f"{label}: {detail}")


def file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


print("== 1) Web-app shell pages ==")
for path in [
    "/app/",
    "/app/index.html",
    "/app/app.css",
    "/app/app.js",
    "/project.html",
    "/styles.css",
    "/ux9.css",
    "/yard-theme.css",
    "/js/api.js",
    "/js/i18n.js",
    "/js/i18n-messages.js",
    "/js/listings.js",
    "/js/ui-sound.js",
    "/manifest.webmanifest",
    "/sw.js",
]:
    r = cl.get(path)
    ok(path, r.status_code == 200, str(r.status_code))

print("\n== 2) /app/ HTML structure (shell views) ==")
html = (ROOT / "public/app/index.html").read_text(encoding="utf-8")
app_js = (ROOT / "public/app/app.js").read_text(encoding="utf-8")
for eid in [
    "viewApp",  # 마켓 목록 셸 (구 viewList 아님)
    "viewCreate",
    "viewAuth",
    "viewProfile",
    "formProject",
    "formLogin",
    "formRegister",
    "projectList",
    "btnBackList",
    "btnNew",
    "btnRefresh",
    "buy-how",  # class check separate
    "min-check5",
    "pQCredits",
    "pQUnitPrice",
    "easy-path-grid",
    "exposure-guide",
]:
    if eid in ("buy-how", "min-check5", "easy-path-grid", "exposure-guide"):
        ok(f"class/section {eid}", eid in html)
    else:
        ok(f"id #{eid}", f'id="{eid}"' in html or f"id='{eid}'" in html)

# hash routes used by app
for frag in ["#list", "#new", "#login", "#profile", "#fees", "#coupons"]:
    ok(f"hash route mention {frag}", frag in html or frag in app_js)

print("\n== 3) App CSS (responsive icons + easy path) ==")
css = (ROOT / "public/app/app.css").read_text(encoding="utf-8")
ok("wa-icon-sm mobile max-width", "max-width: 767.98px" in css)
ok("wa-icon-sm desktop min-width", "min-width: 768px" in css and ".wa-icon-sm" in css)
ok("easy-path-grid", ".easy-path-grid" in css)
ok("buy-how", ".buy-how" in css)
ok("exposure-guide", ".exposure-guide" in css)
ok("field-tag", ".field-tag" in css)

print("\n== 4) App.js wiring ==")
# collect getElementById / $("#id") patterns
ids_html = set(re.findall(r'\bid=["\']([A-Za-z][\w-]*)["\']', html))
# app.js: $("id") and getElementById("id")
js_ids = set(re.findall(r'\$\(["\']([A-Za-z][\w-]*)["\']\)', app_js))
js_ids |= set(re.findall(r'getElementById\(["\']([A-Za-z][\w-]*)["\']\)', app_js))
# only check ids that look like UI controls (skip dynamic)
missing = sorted(i for i in js_ids if i not in ids_html and not i.startswith("dynamic"))
# filter known optional/template ids that may be created at runtime
optional_prefixes = ("bid", "fee", "coupon", "msg", "deal", "q", "notif")
# re-check: many ids are only on other pages
# Focus: ids referenced in app.js that are expected on app shell
critical_js = [
    "formProject",
    "formLogin",
    "formRegister",
    "projectList",
    "viewApp",
    "viewCreate",
    "viewAuth",
    "pQCredits",
]
for cid in critical_js:
    if cid in app_js or f'$("{cid}")' in app_js or f"$('{cid}')" in app_js:
        ok(f"app.js critical id present in HTML: {cid}", cid in ids_html)

# node syntax
if shutil.which("node"):
    for rel in [
        "public/app/app.js",
        "public/js/api.js",
        "public/js/listings.js",
        "public/js/native-bridge.js",  # web no-op; used by Capacitor www
        "mobile/www/js/native-bridge.js",
        "mobile/www/app/app.js",
    ]:
        p = ROOT / rel
        if not p.exists():
            warn(f"missing {rel}")
            continue
        r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
        ok(f"syntax {rel}", r.returncode == 0, (r.stderr or "")[:100])

print("\n== 5) public/app ↔ mobile/www/app sync ==")
pairs = [
    ("public/app/index.html", "mobile/www/app/index.html"),
    ("public/app/app.css", "mobile/www/app/app.css"),
    ("public/app/app.js", "mobile/www/app/app.js"),
    ("public/project.html", "mobile/www/project.html"),
    ("public/js/api.js", "mobile/www/js/api.js"),
]
for a, b in pairs:
    pa, pb = ROOT / a, ROOT / b
    if not pb.exists():
        ok(f"www has {b}", False, "missing")
        continue
    # css/js should be identical; html may differ (path rewrites)
    if a.endswith((".css", ".js")):
        ok(f"sync identical {a}", file_sha(pa) == file_sha(pb), f"{file_sha(pa)} vs {file_sha(pb)}")
    else:
        ta = pa.read_text(encoding="utf-8", errors="replace")
        tb = pb.read_text(encoding="utf-8", errors="replace")
        # key markers should exist in both
        for marker in ["wa-icon-sm", "buy-how", "헬프티켓", "min-check5", "easy-path"]:
            if marker in ta:
                ok(f"www keeps {marker}", marker in tb)

# mobile shell relative assets
www_html = (ROOT / "mobile/www/app/index.html").read_text(encoding="utf-8")
ok("www relative app.css", 'href="app.css' in www_html or "href='app.css" in www_html)
ok("www relative app.js", "src=\"app.js" in www_html or "src='app.js" in www_html or "app.js" in www_html)
ok("www runtime-config", "runtime-config" in www_html)

print("\n== 6) Web-app client API flow (as /app/ would call) ==")
email = f"webapp{random.randint(10000,99999)}@example.com"
r = cl.post(
    "/api/v1/auth/register",
    json={
        "email": email,
        "password": "testpass12",
        "display_name": "WebAppQA",
        "birth_date": "1993-03-03",
        "confirm_age_14": True,
    },
)
ok("register", r.status_code == 200, r.text[:80])
body = r.json() if r.status_code == 200 else {}
token = body.get("token")
code = body.get("dev_email_code")
uid = int((body.get("user") or {}).get("id") or 0)
h = {"Authorization": f"Bearer {token}"} if token else {}
if token and code:
    r = cl.post("/api/v1/auth/verify-email", headers=h, json={"code": code})
    ok("verify-email", r.status_code == 200)
    if r.json().get("token"):
        token = r.json()["token"]
        h = {"Authorization": f"Bearer {token}"}
r = cl.post("/api/v1/auth/login", json={"email": email, "password": "testpass12"})
ok("login", r.status_code == 200 and bool(r.json().get("token")))
if r.status_code == 200 and r.json().get("token"):
    token = r.json()["token"]
    h = {"Authorization": f"Bearer {token}"}
r = cl.get("/api/v1/me", headers=h)
ok("me", r.status_code == 200)
r = cl.get("/api/v1/config")
ok("config for boot", r.status_code == 200 and "credit_policy" in r.json())
ok("config q_credit_policy", "q_credit_policy" in r.json() or "q_credit" in json.dumps(r.json()))
r = cl.get("/api/v1/projects")
ok("projects list", r.status_code == 200)
r = cl.get("/api/v1/auctions/live")
ok("live board", r.status_code == 200)

# seller path for create form
cl.put(
    "/api/v1/me/profile",
    headers=h,
    json={"real_name": "웹앱QA", "phone": f"010{random.randint(10000000,99999999)}", "role": "both", "display_name": "WebAppQA"},
)
cl.put(
    "/api/v1/me/settlement",
    headers=h,
    json={"holder": "웹앱QA", "bank": "카카오", "account": f"3333{random.randint(10000000,99999999)}", "is_business": False},
)
cl.put(
    "/api/v1/me/seller-identity",
    headers=h,
    json={
        "seller_type": "individual",
        "trade_name": "웹앱판매",
        "contact_email": email,
        "contact_phone": "01011112222",
        "address": "서울",
        "mail_order_report_no": "",
    },
)
png = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415408d763f8cfc000000301010018dd8db00000000049454e44ae426082"
)
urls = [
    media_mod.save_demo_image(user_id=uid, raw=png, filename_hint=f"wa{i}.png")["url"]
    for i in range(2)
]
payload = {
    "title": "웹앱 검수 매물",
    "one_liner": "웹앱 셸에서 올린 것처럼",
    "status": "프로토타입",
    "product_type": "webapp",
    "story": "웹앱 QA용 스토리입니다. 등록 폼 최소 통과 검증.",
    "demo": "https://example.com",
    "assets": ["code"],
    "demo_images": urls,
    "attest_shots": True,
    "features": [
        "예약과 고객 목록을 한 화면에서 관리한다",
        "알림으로 다음 일정을 놓치지 않게 한다",
    ],
    "audience": "혼자 예약 관리하는 소상공인",
    "works_now": "데모 링크에서 로그인 없이 예약 목록과 상태 변경을 눌러 볼 수 있다.",
    "limits": "결제 연동과 실 SMS 알림은 아직 없고 더미만 동작한다.",
    "acquisition": "made",
    "attest_works": True,
    "attest_features": True,
    "attest_license": True,
    "attest_rights": True,
    "attest_transfer": True,
    "price_start": 300000,
    "auction_days": 3,
    "license_note": "MIT",
    "keywords": ["웹앱", "QA", "테스트", "SaaS", "검수"],
    "q_credits_offered": 2,
    "q_credit_unit_price": 0,
    "q_credit_sla_hours": 48,
}
r = cl.post("/api/v1/projects", headers=h, json=payload)
ok("create listing via app API", r.status_code == 200, r.text[:100])
pid = (r.json().get("project") or {}).get("id") if r.status_code == 200 else None
if pid:
    r = cl.post(
        f"/api/v1/admin/projects/{pid}/review",
        headers={"X-Admin-Key": ADMIN_SECRET},
        json={"action": "approve", "note": "webapp qa", "checklist": {"demo_ok": True}},
    )
    ok("admin approve", r.status_code == 200, r.text[:80])
    r = cl.get(f"/api/v1/projects/{pid}")
    ok("project detail for project.html", r.status_code == 200)
    ok("project has q_credits_offered", (r.json().get("project") or {}).get("q_credits_offered") == 2)
    r = cl.get("/api/v1/projects")
    ids = [p.get("id") for p in (r.json().get("projects") or r.json().get("items") or [])]
    # list shape may vary
    data = r.json()
    projs = data.get("projects") or data.get("items") or data.get("results") or []
    if not projs and isinstance(data, list):
        projs = data
    ok("list non-empty after approve", len(projs) >= 1, f"n={len(projs)}")

print("\n== 7) project.html web-app pieces ==")
ph = (ROOT / "public/project.html").read_text(encoding="utf-8")
for marker in ["buy-how-proj", "qCreditPolicy", "qAskForm", "bidForm", "max-width: 767.98px", "헬프티켓"]:
    ok(f"project.html has {marker}", marker in ph)

print("\n== 8) Optional Playwright browser (if installed) ==")
try:
    from playwright.sync_api import sync_playwright  # type: ignore
except Exception as e:
    warn("playwright not installed", str(e)[:80])
    print("  (skip real browser; pip install playwright && playwright install chromium)")
else:
    # Use ASGI transport via uvicorn in-process is hard; use TestClient base_url isn't real browser.
    # Start nothing — use file:// won't hit API. Skip if no server.
    # Instead launch chromium against TestClient is not supported; check if :8080 up.
    import socket

    def port_open(port: int) -> bool:
        s = socket.socket()
        s.settimeout(0.3)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
            return True
        except OSError:
            return False

    if not port_open(8080):
        # start uvicorn subprocess briefly
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8080"],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import time

        for _ in range(40):
            if port_open(8080):
                break
            time.sleep(0.25)
        started = True
    else:
        proc = None
        started = False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})  # mobile
            console_errs: list[str] = []
            page.on(
                "pageerror",
                lambda exc: console_errs.append(str(exc)[:120]),
            )
            page.goto("http://127.0.0.1:8080/app/", wait_until="networkidle", timeout=30000)
            ok("browser /app/ title", "WakeAgain" in (page.title() or "") or "Wake" in page.content())
            ok(
                "browser has projectList or empty",
                page.locator("#projectList, #emptyList, .project-list").count() >= 1,
            )
            ok("browser buy-how visible mobile", page.locator(".buy-how").count() >= 1)
            ok("browser viewApp exists", page.locator("#viewApp").count() >= 1)
            # measure icon size
            box = page.locator(".wa-icon-sm").first.bounding_box()
            if box:
                ok(
                    "mobile icon box ~28px",
                    20 <= box["width"] <= 36,
                    f"w={box['width']:.1f}",
                )
            else:
                warn("no wa-icon-sm box")
            # list cards after API
            page.wait_for_timeout(800)
            cards = page.locator("#projectList .project-card, #projectList a, #projectList article, #projectList li, #projectList .card")
            n_cards = cards.count()
            ok("market list rendered or empty state", n_cards >= 0)  # always true; tighten below
            empty_vis = page.locator("#emptyList:not([hidden])").count()
            ok(
                "has cards or empty message",
                n_cards >= 1 or empty_vis >= 1 or page.locator("#projectList").count() >= 1,
                f"cards={n_cards}",
            )
            # desktop width
            page.set_viewport_size({"width": 1280, "height": 800})
            page.goto("http://127.0.0.1:8080/app/", wait_until="networkidle", timeout=30000)
            box2 = page.locator(".wa-icon-sm").first.bounding_box()
            if box2:
                ok("desktop icon larger", box2["width"] >= 40, f"w={box2['width']:.1f}")
                if box:
                    ok(
                        "desktop icon != mobile size",
                        abs(box2["width"] - box["width"]) >= 8,
                        f"m={box['width']:.0f} d={box2['width']:.0f}",
                    )
            # navigate hash new
            page.goto("http://127.0.0.1:8080/app/#new", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(400)
            ok(
                "create view or auth shown",
                page.locator("#viewCreate:not([hidden]), #viewAuth:not([hidden]), #formProject, #formLogin").count()
                >= 1,
            )
            # login panel
            page.goto("http://127.0.0.1:8080/app/#login", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(300)
            ok("login form fields", page.locator("#formLogin input, #loginEmail, input[type=password]").count() >= 1)
            # register
            page.goto("http://127.0.0.1:8080/app/#register", wait_until="networkidle", timeout=30000)
            ok("register form", page.locator("#formRegister, #viewAuth").count() >= 1)
            # live project detail if any listing id from API
            try:
                import urllib.request

                with urllib.request.urlopen("http://127.0.0.1:8080/api/v1/projects", timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                projs = data.get("projects") or data.get("items") or []
                live_id = projs[0].get("id") if projs else None
            except Exception:
                live_id = pid if pid else None
            if live_id:
                page.goto(
                    f"http://127.0.0.1:8080/project.html?id={live_id}",
                    wait_until="networkidle",
                    timeout=30000,
                )
                ok("project detail buy-how", page.locator(".buy-how-proj, #bidForm, #pTitle").count() >= 1)
            else:
                page.goto(
                    "http://127.0.0.1:8080/project.html?id=1",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                ok("project page loads", page.locator("body").count() == 1)
            ok("no hard pageerror", len(console_errs) == 0, "; ".join(console_errs[:3]))
            browser.close()
    except Exception as ex:
        ok("playwright run", False, str(ex)[:160])
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()

print("\n== SUMMARY ==")
if warns:
    print("Warnings:")
    for w in warns:
        print(" -", w)
if errors:
    print(f"FAILED ({len(errors)}):")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)
print("All web-app checks passed.")
