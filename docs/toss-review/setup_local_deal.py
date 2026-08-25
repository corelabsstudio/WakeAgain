# -*- coding: utf-8 -*-
"""토스 심사 6단계(카드 결제경로) 캡처용 — 로컬 서버에 결제 대기 딜을 하나 만든다.

라이브에서는 낙찰까지 갈 수 없어서(매물 4건이 전부 운영 계정 소유라 자기 매물 입찰 불가)
격리 DB로 띄운 로컬 서버에 판매자·구매자·매물·입찰·성사를 만들고
deal_status = awaiting_payment 상태까지 끌고 간다. 그 화면에서 '카드로 결제하기'가 뜬다.
"""
from __future__ import annotations

import json
import random
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8099"
ADMIN = {"X-Admin-Key": "wakeagain-admin-dev"}
PW = "TossReview12!"


def call(method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept-Language", "ko")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            return f.status, json.loads(f.read())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"_raw": raw[:400]}


def bearer(tok):
    return {"Authorization": "Bearer " + tok}


def make_user(tag, role):
    n = random.randint(100000, 999999)
    email = f"{tag}{n}@example.com"
    s, b = call("POST", "/api/v1/auth/register", {
        "email": email, "password": PW, "display_name": f"{tag}{n}",
        "birth_date": "1990-05-15", "confirm_age_14": True, "country": "KR",
    })
    assert s == 200, (s, b)
    tok = b["token"]
    code = b.get("dev_email_code")
    if code:
        s2, b2 = call("POST", "/api/v1/auth/verify-email", {"code": code}, bearer(tok))
        if s2 == 200 and b2.get("token"):
            tok = b2["token"]
    s3, b3 = call("PUT", "/api/v1/me/profile", {
        "real_name": f"실명{tag}", "phone": f"010{random.randint(10000000, 99999999)}",
        "role": role, "display_name": f"{tag}{n}",
    }, bearer(tok))
    if s3 == 200 and b3.get("token"):
        tok = b3["token"]
    uid = ((b3.get("user") or b.get("user")) or {}).get("id")
    print(f"  [{tag}] {email} id={uid} trust={((b3.get('user') or {}).get('trust') or {}).get('level')}")
    return {"email": email, "token": tok, "id": uid, "h": bearer(tok)}


def main():
    print("1) 판매자")
    seller = make_user("seller", "seller")
    s, b = call("PUT", "/api/v1/me/settlement", {
        "holder": "실명seller", "bank": "토스뱅크",
        "account": "100012345678", "is_business": False,
    }, seller["h"])
    if s == 200 and b.get("token"):
        seller["token"] = b["token"]; seller["h"] = bearer(b["token"])
    print("   settlement:", s, ((b.get("user") or {}).get("trust") or {}).get("level"))
    s, b = call("PUT", "/api/v1/me/seller-identity", {
        "seller_type": "individual", "trade_name": "심사용 판매자",
        "contact_email": seller["email"], "contact_phone": "01099998888",
        "address": "강원특별자치도 춘천시", "mail_order_report_no": "",
    }, seller["h"])
    if s == 200 and b.get("token"):
        seller["token"] = b["token"]; seller["h"] = bearer(b["token"])
    print("   seller-identity:", s)

    print("2) 구매자")
    buyer = make_user("buyer", "buyer")

    print("3) 매물 등록")
    s, b = call("POST", "/api/v1/projects", {
        "title": "심사용 데모 프로젝트",
        "one_liner": "카드 결제경로 확인용 데모 매물",
        "status": "프로토타입", "product_type": "webapp",
        "story": "토스페이먼츠 결제경로 심사 자료 제작을 위한 로컬 데모 매물입니다.",
        "demo": "https://example.com/demo",
        "assets": ["code"],
        "price_start": 300_000, "auction_days": 3, "min_increment": 10_000,
        "license_note": "양도",
        "keywords": ["테스트", "거래", "SaaS", "웹앱", "심사"],
        "features": ["로그인 후 목록을 볼 수 있어요", "항목을 체크하면 저장돼요"],
        "audience": "결제경로 검증", "works_now": "등록부터 결제까지 동작합니다.",
        "limits": "심사 자료용", "acquisition": "made",
        "demo_images": [f"/media/demos/{seller['id']}/shot.png"],
        "repo_url": "https://github.com/corelabsstudio/WakeAgain",
        "is_private_repo": False, "is_offline": True, "last_activity_at": "2026-08",
        "attest_works": True, "attest_features": True, "attest_license": True,
        "attest_rights": True, "attest_shots": True, "attest_transfer": True,
    }, seller["h"])
    assert s == 200, (s, b)
    pid = (b.get("project") or {}).get("id")
    print("   project id =", pid)

    print("4) 관리자 승인")
    s, b = call("POST", f"/api/v1/admin/projects/{pid}/review", {
        "action": "approve", "note": "심사자료 자동 승인",
        "checklist": {"demo_ok": True, "title_ok": True, "price_ok": True, "story_ok": True},
    }, ADMIN)
    print("   approve:", s)

    print("5) 구매자 입찰")
    s, b = call("POST", f"/api/v1/projects/{pid}/bids", {"amount": 300_000}, buyer["h"])
    print("   bid:", s, b.get("detail") or "")

    print("6) 판매자 성사 처리")
    s, b = call("POST", f"/api/v1/projects/{pid}/close-deal",
                {"use_current_bid": True, "note": "심사자료"}, seller["h"])
    proj = b.get("project") or {}
    print("   close-deal:", s, "auction=", proj.get("auction_status"),
          "deal=", proj.get("deal_status"), "sold_price=", proj.get("sold_price"))
    if s != 200 or proj.get("deal_status") != "awaiting_payment":
        print("   !! 결제 대기 상태에 도달하지 못함:", json.dumps(b, ensure_ascii=False)[:500])
        return 1

    out = {"project_id": pid, "buyer_email": buyer["email"], "password": PW,
           "url": f"{BASE}/project.html?id={pid}&lang=ko"}
    print("\n=== 결제 화면 ===")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    with open("docs/toss-review/_local_deal.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
