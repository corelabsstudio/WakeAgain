"""Replace junk listings with a few realistic demo projects (early launch)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "wakeagain.db"

# Password: demo-seller-2026 (bcrypt if available — we keep existing hash or placeholder)
# We only need a user row as owner_id FK.

SAMPLES = [
    {
        "title": "ShopPulse",
        "one_liner": "소상공인 주문·배송 알림 SaaS — 카카오톡 연동 초안",
        "status": "launched",
        "product_type": "webapp",
        "story": (
            "주말에 만들었던 동네 가게용 주문 알림 서비스입니다. "
            "실제로 3개 가게에서 2주 써 보고 멈추었습니다. "
            "마케팅·영업할 시간이 없어 넘기려 합니다. 카카오 알림톡 연동 코드와 간단한 대시보드가 있습니다."
        ),
        "demo": "데모 영상: 주문 접수 → 사장님 알림 흐름 (3분)\n스테이징: 요청 시 계정 안내",
        "price_start": 890000,
        "price_current": 1120000,
        "price_buy_now": 2500000,
        "bid_count": 4,
        "license_note": "직접 작성 코드 위주 · 오픈소스 라이브러리 MIT/Apache 명시 예정",
        "keywords": ["SaaS", "카카오", "주문", "알림", "소상공인"],
        "days_left": 4,
    },
    {
        "title": "ReceiptFold",
        "one_liner": "영수증 사진 → 가계부 자동 분류 모바일 베타",
        "status": "beta",
        "product_type": "mobile",
        "story": (
            "Flutter로 만든 개인 가계부 앱입니다. OCR은 외부 API를 붙였고, "
            "카테고리 추천은 규칙 기반입니다. 스토어 제출 직전 단계에서 이직으로 중단했습니다."
        ),
        "demo": "Android APK 설치 링크 (요청 시) · 화면 녹화 2분",
        "price_start": 450000,
        "price_current": 450000,
        "price_buy_now": 980000,
        "bid_count": 0,
        "license_note": "본인 작성 · OCR API 키는 이전 시 구매자 계정으로 교체 필요",
        "keywords": ["가계부", "영수증", "OCR", "모바일앱", "Flutter"],
        "days_left": 6,
    },
    {
        "title": "MeetNotes Lite",
        "one_liner": "회의 녹음 업로드 → 요약·액션 아이템 초안 웹앱",
        "status": "prototype",
        "product_type": "webapp",
        "story": (
            "바이브 코딩으로 올린 Next.js 프로토입니다. Whisper API + 프롬프트로 요약을 뽑습니다. "
            "UI는 한 페이지만 있고, 결제·팀 기능은 없습니다. 아이디어 PDF가 아니라 돌아가는 화면이 있습니다."
        ),
        "demo": "https://example-demo.invalid/meetnotes (스테이징) · 샘플 녹음 3개 포함",
        "price_start": 320000,
        "price_current": 380000,
        "price_buy_now": 700000,
        "bid_count": 2,
        "license_note": "자체 코드 + OpenAI API 사용 (키 별도)",
        "keywords": ["회의", "요약", "AI", "웹앱", "Whisper"],
        "days_left": 3,
    },
    {
        "title": "csv-kit",
        "one_liner": "CSV 병합·중복 제거·컬럼 매핑 CLI 도구 모음",
        "status": "other",
        "product_type": "desktop",
        "story": (
            "데이터 정리할 때 쓰던 Python CLI입니다. pip 설치 가능한 패키지 구조이고 README가 있습니다. "
            "GUI는 없고 터미널 전용입니다. 사이드 프로젝트로 공개했다가 유지보수 여력이 없어 양도합니다."
        ),
        "demo": "Git 저장소 클론 후 `pip install -e .` · README 샘플 커맨드 5개",
        "price_start": 180000,
        "price_current": 210000,
        "price_buy_now": 400000,
        "bid_count": 1,
        "license_note": "MIT 예정 · 양도 후 패키지명 변경 가능",
        "keywords": ["CSV", "데이터", "CLI", "Python", "도구"],
        "days_left": 5,
    },
    {
        "title": "TraceDraft",
        "one_liner": "AI 인터뷰 답변으로 블로그 초안을 뽑는 웹 도구",
        "status": "beta",
        "product_type": "webapp",
        "story": (
            "질문 5~7개에 답하면 블로그 포스트 초안이 나옵니다. "
            "프롬프트와 결과 편집 UI까지 있고, 실제 글 2편을 이걸로 올렸습니다. "
            "본업 바빠서 더 못 키웁니다."
        ),
        "demo": "웹 데모 링크 (요청 시 게스트 계정) · 결과 예시 스크린 3장",
        "price_start": 550000,
        "price_current": 720000,
        "price_buy_now": 1500000,
        "bid_count": 5,
        "license_note": "직접 작성 프론트/백 · LLM API 키는 구매자 부담",
        "keywords": ["AI", "블로그", "콘텐츠", "웹앱", "초안"],
        "days_left": 2,
    },
]


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"DB not found: {DB}")

    now = datetime.now(timezone.utc).astimezone()
    now_s = now.isoformat(timespec="seconds")

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # ensure keywords column (additive; matches wakeagain.db migrations)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()}
    if "keywords_json" not in cols:
        conn.execute("ALTER TABLE projects ADD COLUMN keywords_json TEXT DEFAULT '[]'")
        print("added keywords_json column")

    # Wipe listing-related rows (keep users)
    for table in (
        "bids",
        "reports",
        "fee_invoices",
        "messages",
        "notifications",
        "projects",
    ):
        try:
            conn.execute(f"DELETE FROM {table}")
            print(f"cleared {table}")
        except sqlite3.OperationalError as e:
            print(f"skip {table}: {e}")

    # Prefer an existing user as owner; create demo seller if empty
    row = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    if row:
        owner_id = int(row["id"])
    else:
        conn.execute(
            """
            INSERT INTO users (email, password_hash, display_name, created_at,
              email_verified, real_name, phone, role)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                "demo.seller@wakeagain.local",
                "not-a-real-hash",
                "데모판매자",
                now_s,
                "김데모",
                "01012345678",
                "seller",
            ),
        )
        owner_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        print("created demo owner", owner_id)

    # Best-effort seller identity so listings pass public rules if checked
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "seller_type" in cols:
        conn.execute(
            """
            UPDATE users SET
              seller_type = COALESCE(NULLIF(seller_type,''), 'individual'),
              seller_trade_name = COALESCE(NULLIF(seller_trade_name,''), '데모판매자'),
              seller_contact_email = COALESCE(NULLIF(seller_contact_email,''), email),
              seller_contact_phone = COALESCE(NULLIF(seller_contact_phone,''), '01012345678'),
              seller_identity_at = COALESCE(seller_identity_at, ?)
            WHERE id = ?
            """,
            (now_s, owner_id),
        )

    attest = json.dumps(
        {
            "works": True,
            "license": True,
            "rights": True,
            "note": "demo seed listing",
        },
        ensure_ascii=False,
    )

    for s in SAMPLES:
        ends = (now + timedelta(days=int(s["days_left"]))).isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT INTO projects (
              owner_id, title, one_liner, status, product_type, story, demo, assets_json,
              keywords_json,
              price_start, price_buy_now, price_current, bid_count, bidder_count, min_increment,
              auction_ends_at, auction_status, listing_status,
              contact, license_note, seller_attest_json,
              created_at, updated_at, demo_verified
            ) VALUES (
              ?,?,?,?,?,?,?,?,
              ?,
              ?,?,?,?,?,?,
              ?, 'live', 'approved',
              ?,?,?,
              ?,?, 1
            )
            """,
            (
                owner_id,
                s["title"],
                s["one_liner"],
                s["status"],
                s["product_type"],
                s["story"],
                s["demo"],
                "[]",
                json.dumps(s.get("keywords") or [], ensure_ascii=False),
                s["price_start"],
                s["price_buy_now"],
                s["price_current"],
                s["bid_count"],
                s["bid_count"],  # demo: treat as unique bidders
                10000,
                ends,
                "corelabs.studio@gmail.com",
                s["license_note"],
                attest,
                now_s,
                now_s,
            ),
        )
        print("seeded", s["title"])

    conn.commit()
    n = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE listing_status='approved'"
    ).fetchone()[0]
    print(f"done — approved projects: {n}")
    conn.close()


if __name__ == "__main__":
    main()
