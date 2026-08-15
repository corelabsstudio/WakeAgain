# -*- coding: utf-8 -*-
"""Seed Trace + ReachKit (리치킷) as approved marketplace listings on production.

Requires ADMIN_SECRET (from .env or env). Creates seller if needed, uploads demos,
creates listings, admin-approves.
"""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (os.environ.get("WAKEAGAIN_BASE") or "https://wakeagain.com").rstrip("/")
SEED_DIR = ROOT / "data" / "listing_seed"


def admin_key() -> str:
    k = (os.environ.get("ADMIN_SECRET") or "").strip()
    if k:
        return k
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_SECRET="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ADMIN_SECRET missing")


def req(method: str, path: str, *, token: str | None = None, admin: bool = False, body: dict | None = None, files: dict | None = None):
    url = BASE + path
    headers = {"Accept": "application/json", "User-Agent": "CoreLabsSeed/1.0"}
    data = None
    if files:
        # multipart manual
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
    email = os.environ.get("SEED_SELLER_EMAIL") or "corelabs.seller@wakeagain.com"
    password = os.environ.get("SEED_SELLER_PASSWORD") or "CoreLabsSeller!2026a1"
    token = None
    # try login first
    try:
        _, login = req("POST", "/api/v1/auth/login", body={"email": email, "password": password})
        token = login.get("token")
        if token:
            print("[seller] logged in", email)
    except Exception as e:
        print("[seller] login miss:", e)

    if not token:
        # register
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
                _, login = req(
                    "POST", "/api/v1/auth/login", body={"email": email, "password": password}
                )
                token = login["token"]
            else:
                raise

    # admin verify email (always if not verified)
    user = req("GET", "/api/v1/me", token=token)[1].get("user") or {}
    uid = user.get("id")
    print("[seller] me", uid, "verified", user.get("email_verified"), "trust", user.get("trust"))
    if uid and not user.get("email_verified"):
        _, v = req("POST", f"/api/v1/admin/users/{uid}/verify-email", admin=True)
        print("[seller] admin verify-email", v)
        _, login = req("POST", "/api/v1/auth/login", body={"email": email, "password": password})
        token = login["token"]
        user = req("GET", "/api/v1/me", token=token)[1].get("user") or {}
        print("[seller] after verify", user.get("email_verified"), user.get("trust"))

    ensure_trust(token, email)
    user = req("GET", "/api/v1/me", token=token)[1].get("user") or {}
    print("[seller] final trust", user.get("trust"))
    return token


def ensure_trust(token: str, email: str):
    # profile Lv2
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

    # seller identity
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
        # try individual fallback
        try:
            _, sid = req(
                "PUT",
                "/api/v1/me/seller-identity",
                token=token,
                body={
                    "seller_type": "individual",
                    "trade_name": "코어랩스",
                    "contact_email": email,
                    "contact_phone": "01000000000",
                    "address": "강원특별자치도 춘천시 세실로192번길 8-3",
                },
            )
            print("[seller] identity individual", sid.get("ok"))
        except Exception as e2:
            print("[seller] identity fail", e2)


def upload_images(token: str, paths: list[Path]) -> list[str]:
    urls = []
    for p in paths:
        raw = p.read_bytes()
        ctype = mimetypes.guess_type(p.name)[0] or "image/png"
        _, out = req(
            "POST",
            "/api/v1/uploads/demo",
            token=token,
            files={"file": (p.name, raw, ctype)},
        )
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
            "note": "CoreLabs 자사 제품 매물 — PG 신청용 실매물 게시",
            "checklist": checklist,
        },
    )
    st = (rev.get("project") or {}).get("listing_status")
    print("[approve]", project_id, st, rev.get("ok"))
    return rev


def create_listing(token: str, payload: dict, image_paths: list[Path]) -> int:
    imgs = upload_images(token, image_paths)
    payload = dict(payload)
    payload["demo_images"] = imgs
    payload["attest_shots"] = True
    if not payload.get("demo"):
        payload["demo"] = f"실행 화면 스크린샷 {len(imgs)}장 첨부 · 데모/설치는 문의 corelabs.studio@gmail.com"
    _, out = req("POST", "/api/v1/projects", token=token, body=payload)
    proj = out.get("project") or {}
    pid = proj.get("id")
    print("[create]", payload["title"], "id=", pid, "status=", proj.get("listing_status"))
    if not pid:
        raise RuntimeError(out)
    approve(int(pid))
    return int(pid)


LISTINGS = [
    {
        "title": "Trace — AI 인터뷰 경험글 작성 도구",
        "one_liner": "말만 하면 E-E-A-T형 경험 후기 본문이 나오는 Windows 데스크톱 작성 도구",
        "status": "beta",
        "product_type": "desktop",
        "story": (
            "취재형 인터뷰로 행동·사실 재료를 끌어내, 내가 말한 내용을 나보다 잘 정리된 "
            "경험 후기 글·발행 패키지로 만드는 데스크톱 도구입니다. "
            "일반 요약 AI·키워드 나열기가 아니라 없는 경험 창작은 금지하고, "
            "BYOK(본인 API 키)로 AI 원가를 방어하는 구조입니다. "
            "Windows 설치형 Trace.exe로 동작하며 코어랩스가 직접 제작·운영합니다. "
            "본업·다른 제품(RoadLog 등)에 화력을 집중하려 양도·협업 가능성을 열어 둡니다."
        ),
        "features": [
            "취재형 인터뷰 질문으로 행동·사실 재료를 끌어냅니다",
            "말한 내용을 E-E-A-T형 경험 후기 본문으로 정리합니다",
            "없는 경험 창작 금지 · 사실 기반 작성 규칙을 지킵니다",
            "Windows 설치형 Trace.exe로 바로 실행할 수 있습니다",
            "BYOK로 사용자 본인 API 키를 써서 원가를 나눕니다",
        ],
        "audience": "블로그·후기·경험글을 써야 하는 사장님·프리랜서·콘텐츠 운영자",
        "works_now": (
            "Windows 데스크톱 앱(Trace.exe) 설치·실행, 인터뷰 플로우, "
            "경험글 초안 생성, 결과 편집 UI까지 동작합니다. 설치 경로 예: C:\\Trace\\Trace.exe"
        ),
        "limits": (
            "웹 SaaS 멀티유저·결제 구독 빌링·팀 협업은 아직 약합니다. "
            "AI는 사용자 API 키(BYOK) 필요. macOS/모바일 앱 없음."
        ),
        "acquisition": "made",
        "assets": ["source", "readme", "docs"],
        "price_start": 890000,
        "price_buy_now": 2900000,
        "min_increment": 50000,
        "auction_days": 14,
        "license_note": "코어랩스 직접 제작 · 양도 시 설치 패키지·소스·브랜드 협의 이전 · LLM API 키는 구매자 부담",
        "keywords": ["Trace", "AI", "인터뷰", "경험글", "블로그", "데스크톱", "BYOK"],
        "contact": "corelabs.studio@gmail.com",
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
        "images": ["trace_1.png", "trace_2.png"],
    },
    {
        "title": "리치킷(ReachKit) — 홍보 문구·채널 추천 도구",
        "one_liner": "사이트 분석 → 홍보 문구·채널 추천까지, 도배 아닌 가드레일 홍보 데스크톱 툴",
        "status": "beta",
        "product_type": "desktop",
        "story": (
            "제품 URL을 넣으면 사이트를 분석하고, 홍보에 쓸 문구와 채널·게시판 추천을 "
            "도와주는 Windows 데스크톱 도구입니다. "
            "100개 카페 원클릭 도배·캡차 우회가 아니라, 가드레일과 검증 대시보드로 "
            "안전하게 쓰고 도달하는 쪽에 맞춰 두었습니다. "
            "특정 서비스에 종속되지 않고 사용자가 넣은 URL 기준입니다. "
            "로드로그 등 자사 제품 홍보 루틴으로 쓰다 범용 제품으로 정리했고, "
            "유료 베타·양도 가능성을 열어 둡니다."
        ),
        "features": [
            "제품 URL 기준으로 사이트 구조·메시지를 분석합니다",
            "홍보 문구 초안을 채널 톤에 맞게 생성합니다",
            "블로그·커뮤니티·SNS 등 채널·게시판을 추천합니다",
            "가드레일로 위험 문구·도배성 패턴을 걸러 줍니다",
            "검증 대시보드로 시도·성공 기록을 남길 수 있습니다",
        ],
        "audience": "자사 제품·서비스를 홍보해야 하는 1인 개발자·소규모 SaaS 운영자",
        "works_now": (
            "Windows에서 ReachKit.bat / 리치킷 바로가기로 실행, "
            "URL 분석·문구 생성·채널 추천·가드레일 UI가 동작합니다."
        ),
        "limits": (
            "카페·플랫폼 자동 가입·캡차 우회·무인 대량 등록은 하지 않습니다. "
            "게시 성공을 보장하지 않으며, 커뮤니티 규정 준수는 사용자 책임입니다. "
            "macOS/웹 SaaS 버전 없음."
        ),
        "acquisition": "made",
        "assets": ["source", "readme", "docs"],
        "price_start": 590000,
        "price_buy_now": 1800000,
        "min_increment": 30000,
        "auction_days": 14,
        "license_note": "코어랩스 직접 제작 · 소스·브랜드·설치 패키지 양도 협의 · 외부 API 키는 구매자 부담",
        "keywords": ["리치킷", "ReachKit", "홍보", "마케팅", "카피", "채널추천", "데스크톱"],
        "contact": "corelabs.studio@gmail.com",
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
        "images": ["reachkit_1.png", "reachkit_icon.png", "reachkit_2.png"],
    },
]


def main():
    print("BASE", BASE)
    token = ensure_seller()
    # list existing to avoid exact dup titles if re-run
    _, listing = req("GET", "/api/v1/projects?limit=50")
    existing_titles = {p.get("title") for p in listing.get("projects") or []}
    print("existing public", len(existing_titles), existing_titles)

    ids = []
    for item in LISTINGS:
        if item["title"] in existing_titles:
            print("skip existing title", item["title"])
            continue
        imgs = [SEED_DIR / n for n in item["images"] if (SEED_DIR / n).exists()]
        if len(imgs) < 2:
            raise SystemExit(f"need >=2 images for {item['title']}: {imgs}")
        payload = {k: v for k, v in item.items() if k != "images"}
        pid = create_listing(token, payload, imgs)
        ids.append(pid)
        time.sleep(0.5)

    _, listing2 = req("GET", "/api/v1/projects?limit=50")
    print("PUBLIC COUNT", listing2.get("total"), [p.get("title") for p in listing2.get("projects") or []])
    print("DONE ids", ids)


if __name__ == "__main__":
    main()
