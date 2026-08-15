# -*- coding: utf-8 -*-
from fastapi.testclient import TestClient
from server import app
from wakeagain.db import init_db, db, mark_deal_paid
from wakeagain import db as database
from wakeagain.admin_auth import ADMIN_SECRET
from wakeagain import media as media_mod
import random

init_db()
cl = TestClient(app)
errs = []

def ok(label, cond, detail=""):
    print(("OK" if cond else "FAIL"), label, (detail or "")[:120])
    if not cond:
        errs.append(label)

def reg(tag):
    e = f"{tag}{random.randint(10000,99999)}@example.com"
    r = cl.post("/api/v1/auth/register", json={
        "email": e, "password": "testpass12", "display_name": tag,
        "birth_date": "1990-05-05", "confirm_age_14": True,
    })
    body = r.json()
    t = body["token"]
    h = {"Authorization": f"Bearer {t}"}
    if body.get("dev_email_code"):
        rv = cl.post("/api/v1/auth/verify-email", headers=h, json={"code": body["dev_email_code"]})
        if rv.json().get("token"):
            t = rv.json()["token"]
            h = {"Authorization": f"Bearer {t}"}
    phone = f"010{random.randint(10000000,99999999)}"
    cl.put("/api/v1/me/profile", headers=h, json={
        "real_name": tag, "phone": phone, "role": "both", "display_name": tag,
    })
    return {"h": h, "id": body["user"]["id"], "email": e}

s = reg("QSeller")
cl.put("/api/v1/me/settlement", headers=s["h"], json={
    "holder": "QSeller", "bank": "카카오", "account": f"3333{random.randint(10000000,99999999)}", "is_business": False,
})
cl.put("/api/v1/me/seller-identity", headers=s["h"], json={
    "seller_type": "individual", "trade_name": "QSeller", "contact_email": s["email"],
    "contact_phone": "01011112222", "address": "서울", "mail_order_report_no": "",
})
png = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de0000000c4944415408d763f8cfc000000301010018dd8db00000000049454e44ae426082")
urls = [media_mod.save_demo_image(user_id=s["id"], raw=png, filename_hint=f"q{i}.png")["url"] for i in range(2)]
payload = {
    "title": "Q크레딧 E2E",
    "one_liner": "헬프티켓 e2e 테스트",
    "status": "프로토타입",
    "product_type": "webapp",
    "story": "헬프티켓 전체 흐름 검수용 스토리입니다. 충분히 길게 작성합니다.",
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
    "price_start": 200000,
    "auction_days": 3,
    "license_note": "MIT",
    "keywords": ["헬프", "티켓", "테스트", "e2e", "qa"],
    "q_credits_offered": 2,
    "q_credit_unit_price": 10000,
    "q_credit_sla_hours": 48,
}
r = cl.post("/api/v1/projects", headers=s["h"], json=payload)
ok("create", r.status_code == 200, r.text)
if r.status_code != 200:
    raise SystemExit(1)
pid = r.json()["project"]["id"]
ok("q offered 2", r.json()["project"].get("q_credits_offered") == 2)
r = cl.post(f"/api/v1/admin/projects/{pid}/review", headers={"X-Admin-Key": ADMIN_SECRET},
            json={"action": "approve", "note": "qa", "checklist": {"demo_ok": True}})
ok("approve", r.status_code == 200, r.text)
b = reg("QBuyer")
r = cl.post(f"/api/v1/projects/{pid}/bids", headers=b["h"], json={"amount": 200000})
ok("bid", r.status_code == 200, r.text)
r = cl.post(f"/api/v1/projects/{pid}/close-deal", headers=s["h"], json={"use_current_bid": True})
ok("close", r.status_code == 200, r.text)
with db() as conn:
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    mark_deal_paid(conn, row, note="qa pay")
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    database.mark_deal_transferred(conn, row)
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    print("deal", row["deal_status"], "q_rem", row["q_credits_remaining"], "window", row["q_window_ends_at"])
r = cl.get(f"/api/v1/projects/{pid}/q-credits", headers=b["h"])
ok("buyer get q-credits", r.status_code == 200, r.text)
data = r.json()
ok("policy has non-intervene note", "중재" in str((data.get("policy") or {}).get("message_ko") or ""))
ok("available >= 1", int(data.get("available") or 0) >= 1, str(data.get("available")))
r = cl.post(f"/api/v1/projects/{pid}/q-credits/threads", headers=b["h"],
            json={"body": "설정 파일 위치가 어디인가요? Windows 기준."})
ok("ask thread", r.status_code == 200, r.text)
body = r.json()
tid = (body.get("thread") or {}).get("id")
if not tid:
    threads = (cl.get(f"/api/v1/projects/{pid}/q-credits", headers=b["h"]).json().get("threads") or [])
    tid = threads[0]["id"] if threads else None
ok("thread id", bool(tid), str(tid))
r = cl.post(f"/api/v1/projects/{pid}/q-credits/threads/{tid}/answer", headers=s["h"],
            json={"answer": "config.yaml 프로젝트 루트에 있습니다. 수정 후 재시작하세요."})
ok("answer", r.status_code == 200, r.text)
data = cl.get(f"/api/v1/projects/{pid}/q-credits", headers=b["h"]).json()
print("after", "remaining", data.get("q_credits_remaining"), "available", data.get("available"))
ok("deducted after answer", int(data.get("q_credits_remaining") or 99) <= 1)
print("ERRS", len(errs))
for e in errs:
    print(" -", e)
raise SystemExit(1 if errs else 0)
