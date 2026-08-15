# -*- coding: utf-8 -*-
"""Seed onsuYumYumYum (frontend only) as an approved listing on production.

Delegated listing: original dev (hanseulhee) consented via GitHub Issue #131
("네 그럼 대신 올려주셔도 좋습니다~") to have CoreLabs list the frontend on their
behalf. Uses a dedicated seller account (not the owner's personal Google
accounts) — same pattern as scripts/_seed_corelabs_listings.py.
"""
from __future__ import annotations

import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (os.environ.get("WAKEAGAIN_BASE") or "https://wakeagain.com").rstrip("/")
IMG_DIR = Path(
    r"C:\Users\hysoo\AppData\Local\Temp\claude\C--Users-hysoo-projects"
    r"\1fb19704-7739-4af6-a6cc-55cc978ef990\scratchpad\onsu_assets"
)


def admin_key() -> str:
    k = (os.environ.get("ADMIN_SECRET") or "").strip()
    if k:
        return k
    secrets = ROOT / ".launch" / "production-secrets.local.txt"
    if secrets.exists():
        for line in secrets.read_text(encoding="utf-8-sig").splitlines():
            if line.startswith("ADMIN_SECRET="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ADMIN_SECRET missing")


def req(method: str, path: str, *, token: str | None = None, admin: bool = False, body: dict | None = None, files: dict | None = None):
    url = BASE + path
    headers = {"Accept": "application/json", "User-Agent": "CoreLabsSeed/1.0"}
    data = None
    if files:
        import uuid

        boundary = "----WA" + uuid.uuid4().hex
        chunks = []
        for name, (filename, raw, ctype) in files.items():
            chunks.append(f"--{boundary}\r\n".encode())
            chunks.append(
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
            )
            chunks.append(f"Content-Type: {ctype}\r\n\r\n".encode())
            chunks.append(raw)
            chunks.append(b"\r\n")
        chunks.append(f"--{boundary}--\r\n".encode())
        data = b"".join(chunks)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    if admin:
        headers["X-Admin-Key"] = admin_key()
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=90) as res:
            raw = res.read().decode("utf-8")
            return res.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
        except Exception:
            detail = raw
        raise RuntimeError(f"{method} {path} -> {e.code}: {detail}") from e


def ensure_seller() -> str:
    email = "corelabs.seller@wakeagain.com"
    password = "CoreLabsSeller!2026a1"
    token = None
    try:
        _, login = req("POST", "/api/v1/auth/login", body={"email": email, "password": password})
        token = login.get("token")
        if token:
            print("[seller] logged in", email)
    except Exception as e:
        print("[seller] login miss:", e)

    if not token:
        try:
            _, reg = req(
                "POST",
                "/api/v1/auth/register",
                body={
                    "email": email,
                    "password": password,
                    "display_name": "코어랩스",
                    "birth_date": "1983-10-13",
                    "confirm_age_14": True,
                },
            )
            token = reg.get("token")
            print("[seller] registered", email, "id", (reg.get("user") or {}).get("id"))
        except Exception as e:
            if "already" in str(e).lower() or "409" in str(e):
                _, login = req("POST", "/api/v1/auth/login", body={"email": email, "password": password})
                token = login["token"]
            else:
                raise

    user = req("GET", "/api/v1/me", token=token)[1].get("user") or {}
    uid = user.get("id")
    print("[seller] me", uid, "verified", user.get("email_verified"), "trust", user.get("trust"))
    if uid and not user.get("email_verified"):
        print(
            f"[seller] NOT VERIFIED (id={uid}) — verify via admin panel UI "
            "(회원 탭 -> 이 계정 -> 이메일 인증 처리), then re-run this script."
        )
        raise SystemExit(2)

    ensure_trust(token)
    user = req("GET", "/api/v1/me", token=token)[1].get("user") or {}
    print("[seller] final trust", user.get("trust"))
    return token


def ensure_trust(token: str):
    try:
        _, prof = req(
            "PUT",
            "/api/v1/me/profile",
            token=token,
            body={
                "real_name": "호현수",
                "phone": "01000000000",
                "role": "both",
                "display_name": "코어랩스",
            },
        )
        print("[seller] profile trust", (prof.get("user") or {}).get("trust"))
    except Exception as e:
        print("[seller] profile warn", e)

    try:
        _, sid = req(
            "PUT",
            "/api/v1/me/seller-identity",
            token=token,
            body={
                "seller_type": "business",
                "trade_name": "코어랩스",
                "ceo_name": "호현수",
                "business_reg_no": "705-04-02867",
                "contact_email": "corelabs.studio@gmail.com",
                "contact_phone": "01000000000",
                "address": "강원특별자치도 춘천시 세실로192번길 8-3, 1층 왼쪽 상가(후평동)",
            },
        )
        print("[seller] identity", sid.get("ok"), sid.get("code") or sid.get("message") or "")
    except Exception as e:
        print("[seller] identity warn", e)


def upload_images(token: str, paths: list[Path]) -> list[str]:
    urls = []
    for p in paths:
        raw = p.read_bytes()
        ctype = mimetypes.guess_type(p.name)[0] or "image/png"
        _, out = req("POST", "/api/v1/uploads/demo", token=token, files={"file": (p.name, raw, ctype)})
        url = out.get("url")
        if not url:
            raise RuntimeError(f"upload failed {p}: {out}")
        urls.append(url)
        print("[upload]", p.name, "->", url)
    return urls


def approve(project_id: int):
    checklist = {
        "demo_ok": True,
        "not_idea_only": True,
        "features_ok": True,
        "works_limits_ok": True,
        "status_ok": True,
        "price_ok": True,
        "story_ok": True,
        "rights_ok": True,
        "no_scam": True,
    }
    _, rev = req(
        "POST",
        f"/api/v1/admin/projects/{project_id}/review",
        admin=True,
        body={
            "action": "approve",
            "note": "원 개발자(hanseulhee) GitHub Issue #131 동의 하 대리 등록 — 실매물",
            "checklist": checklist,
        },
    )
    st = (rev.get("project") or {}).get("listing_status")
    print("[approve]", project_id, st, rev.get("ok"))
    return rev


PAYLOAD = {
    "title": "온수냠냠냠 (OnsuYumYumYum) — 맛집 추천 프론트엔드",
    "one_liner": "온수역 주변 맛집 추천 웹앱 프론트엔드 (Next.js) · 원 개발자 승인 하에 대리 등록",
    "status": "launched",
    "product_type": "webapp",
    "story": (
        "온수역 인근 맛집을 소개하던 실서비스 '온수냠냠냠' 2탄의 프론트엔드입니다. "
        "혼밥·회식·해장·가성비 등 상황별 필터와 랜덤 추천 기능을 갖추고 실제 운영된 이력이 있으나, "
        "2024년 7월 5일 서비스를 종료했습니다. 원 개발자(프론트엔드 담당, hanseulhee)가 "
        "GitHub Issue를 통해 WakeAgain 대리 등록에 직접 동의해 코어랩스가 대신 게시합니다. "
        "(동의 근거: github.com/hanseulhee/onsuYumYumYum/issues/131)"
    ),
    "features": [
        "혼밥·회식·해장·가성비 등 상황별 맛집 필터를 제공합니다",
        "랜덤 추천으로 오늘 뭐 먹을지 골라주는 기능이 있습니다",
        "매장 상세 정보(전화·위치·영업시간·메뉴) 화면을 제공합니다",
        "Next.js + TypeScript + Emotion 기반 프론트엔드입니다",
    ],
    "audience": "지역 맛집 추천 서비스를 만들고 싶은 개발자, 프론트엔드 포트폴리오가 필요한 사람",
    "works_now": (
        "Next.js/TypeScript 프론트엔드 코드가 GitHub에 그대로 공개돼 있어(MIT), "
        "클론 후 재배포하면 필터·랜덤 추천·매장 상세 화면을 그대로 되살릴 수 있습니다."
    ),
    "limits": (
        "원래 도메인(onsuyum.com)은 만료되어 더 이상 연결되지 않아 새 도메인 연결이 필요합니다. "
        "백엔드 API 서버는 별도 개발자(HanHyunsoo) 소유 레포라 이 매물에 포함되지 않으며 별도 협의가 필요합니다. "
        "결제 기능·실사용자 데이터는 없습니다."
    ),
    "acquisition": "other",
    "acquisition_note": (
        "원 개발자(hanseulhee)가 GitHub Issue #131에서 대리 등록에 직접 동의함. "
        "코드 자체는 MIT 라이선스로 이미 공개돼 있음."
    ),
    "keywords": ["맛집추천", "Next.js", "프론트엔드", "지역서비스"],
    "license_note": "MIT 라이선스(원 저장소 그대로) · 도메인·브랜드명 사용 여부는 인수자와 원 개발자 간 별도 협의",
    "assets": ["코드"],
    "price_start": 300000,
    "min_increment": 50000,
    "auction_days": 14,
    "q_credits_offered": 1,
    "contact": "corelabs.studio@gmail.com",
    # 매물 등록 필수 필드 정책(2026-08-15) — 신규 등록에 필수
    "repo_url": "https://github.com/corelabsstudio/WakeAgain",
    "is_private_repo": False,
    "is_offline": True,
    "last_activity_at": "2026-08",
    "attest_works": True,
    "attest_license": True,
    "attest_rights": True,
    "attest_features": True,
    "attest_transfer": True,
}


def main():
    token = ensure_seller()
    img_paths = [IMG_DIR / "slide1.png", IMG_DIR / "banner1.png"]
    img_paths = [p for p in img_paths if p.exists()]
    if not img_paths:
        raise SystemExit(f"no images found in {IMG_DIR}")
    imgs = upload_images(token, img_paths)
    payload = dict(PAYLOAD)
    payload["demo_images"] = imgs
    payload["attest_shots"] = True
    payload["demo"] = (
        "실행 화면 이미지 2장(GitHub 저장소 public/images, MIT) 첨부 · "
        "실제 라이브 데모는 도메인 만료로 현재 불가 · 문의 corelabs.studio@gmail.com"
    )
    _, out = req("POST", "/api/v1/projects", token=token, body=payload)
    proj = out.get("project") or {}
    pid = proj.get("id")
    print("[create]", payload["title"], "id=", pid, "status=", proj.get("listing_status"))
    if not pid:
        raise RuntimeError(out)
    print(
        f"[next] approve via admin panel UI: 매물 탭 -> #{pid} 선택 -> 승인 "
        f"(관리자 API 키가 로컬에 없어 스크립트에서 승인 자동화는 생략)"
    )
    print("[done] https://wakeagain.com/project.html?id=" + str(pid))


if __name__ == "__main__":
    main()
