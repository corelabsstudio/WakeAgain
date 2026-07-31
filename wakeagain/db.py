from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from wakeagain import pricing as price_policy

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DATA_DIR", str(ROOT / "data")))
DATA.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA / "wakeagain.db"

PHONE_RE = re.compile(r"^01[016789]\d{7,8}$")
_SETTLEMENT_ENC_PREFIX = "enc:v1:"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _settlement_fernet():
    """Derive Fernet from APP_SECRET / JWT_SECRET for at-rest account encryption."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None
    secret = (
        os.environ.get("APP_SECRET")
        or os.environ.get("JWT_SECRET")
        or "wakeagain-dev-insecure"
    ).encode("utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_settlement_account(plain: str) -> str:
    """Store settlement account encrypted at rest when cryptography is available."""
    raw = (plain or "").strip()
    if not raw:
        return ""
    if raw.startswith(_SETTLEMENT_ENC_PREFIX):
        return raw
    f = _settlement_fernet()
    if f is None:
        return raw
    token = f.encrypt(raw.encode("utf-8")).decode("ascii")
    return _SETTLEMENT_ENC_PREFIX + token


def decrypt_settlement_account(stored: str) -> str:
    """Decrypt settlement account; plaintext legacy values pass through."""
    raw = (stored or "").strip()
    if not raw:
        return ""
    if not raw.startswith(_SETTLEMENT_ENC_PREFIX):
        return raw
    f = _settlement_fernet()
    if f is None:
        return ""
    try:
        token = raw[len(_SETTLEMENT_ENC_PREFIX) :].encode("ascii")
        return f.decrypt(token).decode("utf-8")
    except Exception:
        return ""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r["name"] for r in rows}


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = _column_names(conn, table)
    for name, decl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT NOT NULL UNIQUE COLLATE NOCASE,
              password_hash TEXT NOT NULL,
              display_name TEXT,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              title TEXT NOT NULL,
              one_liner TEXT NOT NULL,
              status TEXT NOT NULL,
              story TEXT NOT NULL,
              demo TEXT NOT NULL,
              assets_json TEXT NOT NULL DEFAULT '[]',
              price_start INTEGER,
              price_buy_now INTEGER,
              contact TEXT,
              listing_status TEXT NOT NULL DEFAULT 'pending',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS interests (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
              email TEXT NOT NULL,
              name TEXT,
              category TEXT NOT NULL,
              budget TEXT,
              note TEXT,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS leads (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              lead_type TEXT NOT NULL,
              contact TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bids (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              bidder_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              amount INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
              author_name TEXT NOT NULL,
              role_label TEXT,
              body TEXT NOT NULL,
              sold_price INTEGER,
              side TEXT NOT NULL DEFAULT 'seller',
              listing_status TEXT NOT NULL DEFAULT 'pending',
              review_note TEXT,
              reviewed_at TEXT,
              created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
            CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(listing_status);
            CREATE INDEX IF NOT EXISTS idx_interests_email ON interests(email);
            CREATE INDEX IF NOT EXISTS idx_bids_project ON bids(project_id);
            CREATE INDEX IF NOT EXISTS idx_bids_created ON bids(created_at);
            CREATE TABLE IF NOT EXISTS notifications (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              title TEXT NOT NULL,
              body TEXT NOT NULL,
              link TEXT,
              is_read INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              body TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fee_invoices (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              seller_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              deal_amount INTEGER NOT NULL,
              fee_amount INTEGER NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending',
              note TEXT,
              created_at TEXT NOT NULL,
              paid_at TEXT
            );

            CREATE TABLE IF NOT EXISTS coupon_campaigns (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              code TEXT NOT NULL UNIQUE COLLATE NOCASE,
              name TEXT NOT NULL,
              fee_rate REAL NOT NULL DEFAULT 0.08,
              max_redemptions INTEGER NOT NULL,
              redeem_count INTEGER NOT NULL DEFAULT 0,
              active INTEGER NOT NULL DEFAULT 1,
              note TEXT,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_coupons (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              campaign_id INTEGER NOT NULL REFERENCES coupon_campaigns(id) ON DELETE CASCADE,
              origin TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'available',
              used_project_id INTEGER,
              used_at TEXT,
              gifted_from_id INTEGER,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(listing_status);
            CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_project ON messages(project_id);
            CREATE INDEX IF NOT EXISTS idx_fee_seller ON fee_invoices(seller_id);
            CREATE INDEX IF NOT EXISTS idx_user_coupons_user ON user_coupons(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_coupons_status ON user_coupons(status);

            CREATE TABLE IF NOT EXISTS showcases (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
              author_name TEXT NOT NULL,
              title TEXT NOT NULL,
              one_liner TEXT NOT NULL,
              story TEXT NOT NULL,
              demo TEXT NOT NULL DEFAULT '',
              status_key TEXT NOT NULL DEFAULT 'prototype',
              product_type TEXT NOT NULL DEFAULT 'other',
              price_hint INTEGER,
              diag_score INTEGER,
              cheer_count INTEGER NOT NULL DEFAULT 0,
              listing_status TEXT NOT NULL DEFAULT 'approved',
              created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_showcases_status ON showcases(listing_status);
            CREATE INDEX IF NOT EXISTS idx_showcases_created ON showcases(created_at);
            """
        )
        # Trust / PII columns (additive migration)
        _ensure_columns(
            conn,
            "users",
            {
                "real_name": "TEXT",
                "phone": "TEXT",
                "role": "TEXT DEFAULT 'both'",
                "email_verified": "INTEGER NOT NULL DEFAULT 0",
                "phone_verified": "INTEGER NOT NULL DEFAULT 0",
                "email_code_hash": "TEXT",
                "email_code_expires": "TEXT",
                "reset_code_hash": "TEXT",
                "reset_code_expires": "TEXT",
                "settlement_bank": "TEXT",
                "settlement_holder": "TEXT",
                "settlement_account": "TEXT",
                "is_business": "INTEGER NOT NULL DEFAULT 0",
                "profile_updated_at": "TEXT",
                # Credit score (auto) — see TRUST.md § credit
                "credit_score": "INTEGER NOT NULL DEFAULT 50",
                "credit_sold": "INTEGER NOT NULL DEFAULT 0",
                "credit_bought": "INTEGER NOT NULL DEFAULT 0",
                "credit_defaults": "INTEGER NOT NULL DEFAULT 0",
                "credit_on_time": "INTEGER NOT NULL DEFAULT 0",
                "credit_updated_at": "TEXT",
                # Age gate (만 14세 이상) — YYYY-MM-DD
                "birth_date": "TEXT",
                # Auto / ops suspension (fraud · report flood)
                "is_suspended": "INTEGER NOT NULL DEFAULT 0",
                "suspended_at": "TEXT",
                "suspend_reason": "TEXT",
                # SNS OAuth (google | github | kakao)
                "oauth_provider": "TEXT",
                "oauth_subject": "TEXT",
                # Public seller identity (전자상거래법 통신판매중개 — 구매자 확인용)
                "seller_type": "TEXT",  # individual | business
                "seller_trade_name": "TEXT",  # 상호 또는 개인 성명(공개)
                "seller_ceo_name": "TEXT",  # 대표자 (사업자)
                "seller_biz_no": "TEXT",  # 사업자등록번호
                "seller_mail_order_no": "TEXT",  # 통신판매업 신고번호
                "seller_contact_email": "TEXT",
                "seller_contact_phone": "TEXT",
                "seller_address": "TEXT",
                "seller_identity_at": "TEXT",
            },
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_oauth "
            "ON users(oauth_provider, oauth_subject) "
            "WHERE oauth_provider IS NOT NULL AND oauth_subject IS NOT NULL"
        )
        # Auction + deal fields
        _ensure_columns(
            conn,
            "projects",
            {
                "price_current": "INTEGER",
                "bid_count": "INTEGER NOT NULL DEFAULT 0",
                # Unique people who placed at least one bid (not total bid events)
                "bidder_count": "INTEGER NOT NULL DEFAULT 0",
                "min_increment": "INTEGER NOT NULL DEFAULT 10000",
                "auction_ends_at": "TEXT",
                "auction_status": "TEXT DEFAULT 'live'",  # live | ended | sold | paused
                "review_note": "TEXT",
                "reviewed_at": "TEXT",
                "review_checklist_json": "TEXT",
                "demo_verified": "INTEGER NOT NULL DEFAULT 0",
                "sold_price": "INTEGER",
                "sold_at": "TEXT",
                "buyer_id": "INTEGER",
                "deal_note": "TEXT",
                # Buyer-protection deal flow (game-trade style escrow steps)
                # awaiting_payment | paid | inspection | completed | disputed | payment_default
                "deal_status": "TEXT",
                "payment_deadline_at": "TEXT",
                "paid_at": "TEXT",
                "transfer_started_at": "TEXT",
                "inspection_deadline_at": "TEXT",
                "buyer_accepted_at": "TEXT",
                "settled_at": "TEXT",
                "deal_dispute_note": "TEXT",
                # website | webapp | mobile | desktop | api | game | other
                "product_type": "TEXT DEFAULT 'other'",
                "report_count": "INTEGER NOT NULL DEFAULT 0",
                "paused_reason": "TEXT",
                # Seller listing attestations (required at create)
                "license_note": "TEXT",
                "seller_attest_json": "TEXT",
                # Marketplace discovery tags (JSON array, max 5) — search + listing cards
                "keywords_json": "TEXT DEFAULT '[]'",
                # Buyer-facing product clarity (plain language; no coding required)
                "features_json": "TEXT DEFAULT '[]'",  # JSON array of feature bullets
                "audience": "TEXT",  # who it's for
                "works_now": "TEXT",  # what works today
                "limits_note": "TEXT",  # what doesn't / limits
                # made | resale | other
                "acquisition": "TEXT",
                "acquisition_note": "TEXT",
                # Buyer handover receipt checklist (JSON) — parties self-transfer; site records checks
                "handover_checklist_json": "TEXT",
                # Premium listing boost (scaffold — payment/UI later; sort already respects active boost)
                # boost_until: ISO end time; null/empty = not boosted
                "boost_until": "TEXT",
                # JSON array of public screenshot URLs: ["/media/demos/{uid}/….jpg", …] max 5
                "demo_images_json": "TEXT DEFAULT '[]'",
                # boost_tier: 0=none, higher = stronger pin among boosted (future products)
                "boost_tier": "INTEGER NOT NULL DEFAULT 0",
                # optional product code e.g. boost_7d (filled when paid product ships)
                "boost_product": "TEXT",
                # Auction round model: public board = this live round only
                # round_started_at: when this listing entered the public board (relist → new time → back of queue)
                "round_started_at": "TEXT",
                "round_number": "INTEGER NOT NULL DEFAULT 0",
                # Intended length; ends_at is set/refreshed on approve (start of round)
                "auction_days_intended": "INTEGER NOT NULL DEFAULT 7",
                # 헬프티켓 (Kmong-style: included count + seller-set add-on price)
                "q_credits_offered": "INTEGER NOT NULL DEFAULT 1",  # free included help tickets 1–3
                "q_credit_unit_price": "INTEGER NOT NULL DEFAULT 0",  # add-on 1회 가격 KRW; 0 = not sold
                "q_credit_sla_hours": "INTEGER NOT NULL DEFAULT 48",
                # Per-deal balances (snapshotted when inspection starts)
                "q_credits_total": "INTEGER NOT NULL DEFAULT 0",
                "q_credits_remaining": "INTEGER NOT NULL DEFAULT 0",
                "q_credits_held": "INTEGER NOT NULL DEFAULT 0",
                "q_credits_purchased": "INTEGER NOT NULL DEFAULT 0",
                "q_window_ends_at": "TEXT",
            },
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS q_threads (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              project_id INTEGER NOT NULL,
              buyer_id INTEGER NOT NULL,
              seller_id INTEGER NOT NULL,
              body TEXT NOT NULL,
              answer_body TEXT,
              status TEXT NOT NULL DEFAULT 'open',
              credit_state TEXT NOT NULL DEFAULT 'held',
              source TEXT NOT NULL DEFAULT 'included',
              sla_deadline_at TEXT,
              created_at TEXT NOT NULL,
              answered_at TEXT,
              FOREIGN KEY (project_id) REFERENCES projects(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_q_threads_project ON q_threads(project_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS q_credit_purchases (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              project_id INTEGER NOT NULL,
              buyer_id INTEGER NOT NULL,
              seller_id INTEGER NOT NULL,
              units INTEGER NOT NULL DEFAULT 1,
              unit_price INTEGER NOT NULL,
              gross_amount INTEGER NOT NULL,
              fee_amount INTEGER NOT NULL DEFAULT 0,
              seller_amount INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT 'pending_payment',
              -- pending_payment | paid | escrowed | settled | refunded
              thread_id INTEGER,
              created_at TEXT NOT NULL,
              paid_at TEXT,
              settled_at TEXT,
              note TEXT,
              FOREIGN KEY (project_id) REFERENCES projects(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_q_purchases_project ON q_credit_purchases(project_id)"
        )
        # Backfill: live approved rows get a stable round_started_at for queue order
        try:
            conn.execute(
                """
                UPDATE projects
                SET round_started_at = COALESCE(
                      NULLIF(round_started_at, ''),
                      NULLIF(reviewed_at, ''),
                      NULLIF(created_at, ''),
                      updated_at
                    ),
                    round_number = CASE
                      WHEN COALESCE(round_number, 0) < 1
                           AND listing_status = 'approved'
                           AND COALESCE(auction_status, 'live') = 'live'
                      THEN 1
                      ELSE COALESCE(round_number, 0)
                    END,
                    auction_days_intended = CASE
                      WHEN COALESCE(auction_days_intended, 0) < 1 THEN 7
                      ELSE auction_days_intended
                    END
                WHERE listing_status = 'approved'
                  AND COALESCE(auction_status, 'live') = 'live'
                """
            )
            # Unsold ended that still look "approved" → archive off public board
            conn.execute(
                """
                UPDATE projects
                SET listing_status = 'archived',
                    updated_at = COALESCE(updated_at, datetime('now'))
                WHERE listing_status = 'approved'
                  AND COALESCE(auction_status, '') = 'ended'
                """
            )
        except Exception:
            pass
        _ensure_columns(
            conn,
            "fee_invoices",
            {
                "fee_rate": "REAL",
                "user_coupon_id": "INTEGER",
            },
        )
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS coupon_campaigns (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              code TEXT NOT NULL UNIQUE COLLATE NOCASE,
              name TEXT NOT NULL,
              fee_rate REAL NOT NULL DEFAULT 0.08,
              max_redemptions INTEGER NOT NULL,
              redeem_count INTEGER NOT NULL DEFAULT 0,
              active INTEGER NOT NULL DEFAULT 1,
              note TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_coupons (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              campaign_id INTEGER NOT NULL REFERENCES coupon_campaigns(id) ON DELETE CASCADE,
              origin TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'available',
              used_project_id INTEGER,
              used_at TEXT,
              gifted_from_id INTEGER,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_user_coupons_user ON user_coupons(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_coupons_status ON user_coupons(status);
            """
        )
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reports (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              reason TEXT NOT NULL,
              detail TEXT,
              status TEXT NOT NULL DEFAULT 'open',
              created_at TEXT NOT NULL,
              resolved_at TEXT,
              resolve_note TEXT,
              UNIQUE(project_id, reporter_id)
            );
            CREATE INDEX IF NOT EXISTS idx_reports_project ON reports(project_id);
            CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
            CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id);

            -- User↔user block (Play content rating: block=yes). Separate from project reports.
            CREATE TABLE IF NOT EXISTS user_blocks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              blocker_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              blocked_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              created_at TEXT NOT NULL,
              UNIQUE(blocker_id, blocked_id)
            );
            CREATE INDEX IF NOT EXISTS idx_user_blocks_blocker ON user_blocks(blocker_id);
            CREATE INDEX IF NOT EXISTS idx_user_blocks_blocked ON user_blocks(blocked_id);
            """
        )
        # Backfill current price from start for existing rows
        conn.execute(
            """
            UPDATE projects
            SET price_current = COALESCE(price_current, price_start, 0),
                bid_count = COALESCE(bid_count, 0),
                bidder_count = COALESCE(bidder_count, 0),
                min_increment = COALESCE(min_increment, 10000),
                auction_status = COALESCE(auction_status, 'live')
            WHERE price_current IS NULL OR bid_count IS NULL
            """
        )
        # Unique bidders from real bid rows; demo seeds (no bid rows) mirror bid_count
        conn.execute(
            """
            UPDATE projects
            SET bidder_count = (
              SELECT COUNT(DISTINCT bidder_id)
              FROM bids
              WHERE bids.project_id = projects.id
            )
            WHERE EXISTS (
              SELECT 1 FROM bids WHERE bids.project_id = projects.id
            )
            """
        )
        conn.execute(
            """
            UPDATE projects
            SET bidder_count = COALESCE(bid_count, 0)
            WHERE NOT EXISTS (
              SELECT 1 FROM bids WHERE bids.project_id = projects.id
            )
            """
        )


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", (raw or "").strip())
    if digits.startswith("82") and len(digits) >= 11:
        digits = "0" + digits[2:]
    return digits


def validate_phone(raw: str) -> str:
    digits = normalize_phone(raw)
    if not PHONE_RE.match(digits):
        raise ValueError("invalid phone — use Korean mobile e.g. 01012345678")
    return digits


def format_phone_display(digits: str) -> str:
    d = normalize_phone(digits)
    if len(d) == 11:
        return f"{d[:3]}-{d[3:7]}-{d[7:]}"
    if len(d) == 10:
        return f"{d[:3]}-{d[3:6]}-{d[6:]}"
    return d


def mask_phone_public(digits: str) -> str:
    """공개 화면: 뒷자리 마스킹 (예: 010-1234-****)."""
    d = normalize_phone(digits)
    if len(d) == 11:
        return f"{d[:3]}-{d[3:7]}-****"
    if len(d) == 10:
        return f"{d[:3]}-{d[3:6]}-****"
    if len(d) >= 4:
        return d[:-4] + "****"
    return "****" if d else ""


def mask_email_public(email: str) -> str:
    """공개 화면: 로컬부 일부 마스킹 (예: ab***@domain.com)."""
    e = (email or "").strip()
    if "@" not in e:
        return e
    local, _, domain = e.partition("@")
    if len(local) <= 2:
        masked = (local[:1] + "***") if local else "***"
    else:
        masked = local[:2] + "***"
    return f"{masked}@{domain}"


# ── Credit score (0–100, auto) ─────────────────────────────────────────────
# Public formula — also exposed via GET /api/v1/config and /guide/credit.html
# Base kept low: identity alone must not look "trusted". Score rises mainly via deals.
CREDIT_BASE = 30
CREDIT_MIN = 0
CREDIT_MAX = 100
CREDIT_RULES = {
    "base": CREDIT_BASE,
    "l2_identity": 5,
    "l3_settlement": 5,
    "sold_as_seller": 12,
    "sold_as_seller_cap": 36,
    "bought_complete": 12,
    "bought_complete_cap": 36,
    "on_time_payment": 8,
    "on_time_payment_cap": 24,
    "default_unpaid": -40,
    "note_ko": (
        "사이트 내 신용 점수는 0~100이며 거래 행동에 따라 자동 반영됩니다. "
        "기본점은 낮고, 성사·정시 입금에 가점, 낙찰 후 미입금에 큰 감점이 있습니다. "
        "신원만 채운 상태로는 ‘신뢰’ 등급에 가지 않습니다. "
        "신뢰 레벨(Lv0~Lv3)과 별개이며 보증이 아닙니다."
    ),
}


def credit_grade(score: int) -> dict:
    s = max(CREDIT_MIN, min(CREDIT_MAX, int(score)))
    if s >= 90:
        key, label = "elite", "최고"
    elif s >= 75:
        key, label = "great", "우수"
    elif s >= 60:
        key, label = "trusted", "신뢰"
    elif s >= 40:
        key, label = "normal", "보통"
    elif s >= 20:
        key, label = "new", "신규"
    else:
        key, label = "risk", "주의"
    return {"score": s, "grade": key, "label": label}


# Buyer rank — public badge from completed purchases (separate from Lv / credit grade).
# Visible to sellers & others as social proof; not a payment guarantee.
BUYER_RANK_TIERS = (
    # min_bought, key, label_ko, short_perk_ko
    (10, "whale", "파워 바이어", "최고 구매 배지 · 입찰·프로필에 강조 표시"),
    (5, "heavy", "헤비 구매자", "헤비 배지 · 판매자에게 눈에 띄는 구매 신호"),
    (3, "regular", "단골 구매자", "단골 배지 · 성사 건수 공개"),
    (1, "starter", "첫 구매 완료", "첫 성사 배지"),
    (0, "scout", "구매 준비 중", "구경·관심 등록 · 첫 성사 후 배지 성장"),
)


def buyer_rank(bought_complete: int = 0, defaults: int = 0) -> dict:
    """Public buyer ladder from completed buys. Defaults dim the badge tone."""
    n = max(0, int(bought_complete or 0))
    d = max(0, int(defaults or 0))
    key, label, perk = "scout", "구매 준비 중", BUYER_RANK_TIERS[-1][3]
    min_need = 0
    for min_b, k, lab, p in BUYER_RANK_TIERS:
        if n >= min_b:
            key, label, perk = k, lab, p
            min_need = min_b
            break
    # next tier progress
    next_min = None
    next_label = None
    for min_b, k, lab, _p in reversed(BUYER_RANK_TIERS):
        if min_b > n:
            next_min = min_b
            next_label = lab
            break
    return {
        "key": key,
        "label": label,
        "bought_complete": n,
        "defaults": d,
        "perk": perk,
        "tier_min": min_need,
        "next_min": next_min,
        "next_label": next_label,
        "caution": d > 0,
        "public": True,
        "note": "성사(구매) 횟수 기반 공개 배지. 보증·보험 아님.",
    }


def buyer_rank_policy() -> dict:
    return {
        "doc": "구매 성사 횟수에 따른 공개 배지 (헤비 구매자 등). 신용 점수·Lv와 별개.",
        "tiers": [
            {
                "min_bought": t[0],
                "key": t[1],
                "label": t[2],
                "perk": t[3],
            }
            for t in reversed(BUYER_RANK_TIERS)
        ],
        "note_ko": (
            "구매가 성사될수록 다른 이용자·판매자에게 보이는 배지가 올라갑니다. "
            "헤비 구매자·파워 바이어는 ‘이 사람은 실제로 사는 사람’ 신호입니다. "
            "미입금 이력이 있으면 주의 표시가 붙을 수 있습니다. 보증이 아닙니다."
        ),
    }


def compute_credit(row: sqlite3.Row | dict, trust: dict | None = None) -> dict:
    """Derive score from counters + trust gates. Stored score is refreshed via recompute."""
    def g(key: str, default=0):
        try:
            if isinstance(row, dict):
                v = row.get(key, default)
            else:
                v = row[key] if key in row.keys() else default
            return 0 if v is None else v
        except (IndexError, KeyError):
            return default

    if trust is None:
        trust = compute_trust(row)

    sold = max(0, int(g("credit_sold") or 0))
    bought = max(0, int(g("credit_bought") or 0))
    defaults = max(0, int(g("credit_defaults") or 0))
    on_time = max(0, int(g("credit_on_time") or 0))

    score = CREDIT_BASE
    if trust.get("profile_complete"):
        score += CREDIT_RULES["l2_identity"]
    if trust.get("deal_ready"):
        score += CREDIT_RULES["l3_settlement"]

    score += min(
        CREDIT_RULES["sold_as_seller_cap"],
        sold * CREDIT_RULES["sold_as_seller"],
    )
    score += min(
        CREDIT_RULES["bought_complete_cap"],
        bought * CREDIT_RULES["bought_complete"],
    )
    score += min(
        CREDIT_RULES["on_time_payment_cap"],
        on_time * CREDIT_RULES["on_time_payment"],
    )
    score += defaults * CREDIT_RULES["default_unpaid"]
    score = max(CREDIT_MIN, min(CREDIT_MAX, score))
    grade = credit_grade(score)

    return {
        **grade,
        "breakdown": {
            "base": CREDIT_BASE,
            "l2_identity": CREDIT_RULES["l2_identity"] if trust.get("profile_complete") else 0,
            "l3_settlement": CREDIT_RULES["l3_settlement"] if trust.get("deal_ready") else 0,
            "sold_as_seller": min(
                CREDIT_RULES["sold_as_seller_cap"],
                sold * CREDIT_RULES["sold_as_seller"],
            ),
            "bought_complete": min(
                CREDIT_RULES["bought_complete_cap"],
                bought * CREDIT_RULES["bought_complete"],
            ),
            "on_time_payment": min(
                CREDIT_RULES["on_time_payment_cap"],
                on_time * CREDIT_RULES["on_time_payment"],
            ),
            "defaults": defaults * CREDIT_RULES["default_unpaid"],
        },
        "counts": {
            "sold_as_seller": sold,
            "bought_complete": bought,
            "on_time_payments": on_time,
            "defaults": defaults,
        },
        "buyer_rank": buyer_rank(bought, defaults),
        "rules": CREDIT_RULES,
    }


def recompute_user_credit(conn: sqlite3.Connection, user_id: int) -> dict:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (int(user_id),)).fetchone()
    if not row:
        return credit_grade(CREDIT_BASE)
    credit = compute_credit(row)
    now = _now()
    conn.execute(
        """
        UPDATE users SET credit_score = ?, credit_updated_at = ?
        WHERE id = ?
        """,
        (int(credit["score"]), now, int(user_id)),
    )
    return credit


def credit_bump(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    sold: int = 0,
    bought: int = 0,
    on_time: int = 0,
    defaults: int = 0,
) -> dict:
    """Increment counters then recompute score."""
    conn.execute(
        """
        UPDATE users SET
          credit_sold = COALESCE(credit_sold, 0) + ?,
          credit_bought = COALESCE(credit_bought, 0) + ?,
          credit_on_time = COALESCE(credit_on_time, 0) + ?,
          credit_defaults = COALESCE(credit_defaults, 0) + ?
        WHERE id = ?
        """,
        (int(sold), int(bought), int(on_time), int(defaults), int(user_id)),
    )
    return recompute_user_credit(conn, user_id)


def public_credit_summary(row: sqlite3.Row | dict | None) -> dict | None:
    if not row:
        return None
    credit = compute_credit(row)
    bought = credit["counts"]["bought_complete"]
    defaults = credit["counts"]["defaults"]
    return {
        "score": credit["score"],
        "grade": credit["grade"],
        "label": credit["label"],
        "counts": {
            "sold_as_seller": credit["counts"]["sold_as_seller"],
            "bought_complete": bought,
            "defaults": defaults,
        },
        "buyer_rank": buyer_rank(bought, defaults),
    }


def compute_trust(row: sqlite3.Row | dict) -> dict:
    def g(key: str, default=None):
        try:
            if isinstance(row, dict):
                return row.get(key, default)
            return row[key] if key in row.keys() else default
        except (IndexError, KeyError):
            return default

    email_verified = bool(int(g("email_verified") or 0))
    real_name = (g("real_name") or "").strip()
    phone = (g("phone") or "").strip()
    phone_ok = bool(phone and PHONE_RE.match(normalize_phone(phone)))
    profile_ok = bool(real_name and phone_ok and email_verified)
    bank = (g("settlement_bank") or "").strip()
    holder = (g("settlement_holder") or "").strip()
    account = (g("settlement_account") or "").strip()
    deal_ready = bool(profile_ok and bank and holder and account)

    if deal_ready:
        level = 3
    elif profile_ok:
        level = 2
    elif email_verified:
        level = 1
    else:
        level = 0

    missing = []
    if not email_verified:
        missing.append("email_verification")
    if not real_name:
        missing.append("real_name")
    if not phone_ok:
        missing.append("phone")
    if level >= 2 and not deal_ready:
        if not holder:
            missing.append("settlement_holder")
        if not bank:
            missing.append("settlement_bank")
        if not account:
            missing.append("settlement_account")

    seller_ok = seller_identity_complete(row)
    if profile_ok and not seller_ok:
        missing.append("seller_identity")

    suspended = bool(int(g("is_suspended") or 0))
    return {
        "level": level,
        "label": {0: "가입", 1: "이메일 인증", 2: "신원 확인", 3: "거래 준비"}.get(level, "가입"),
        "code": f"Lv{level}",
        "email_verified": email_verified,
        "profile_complete": profile_ok,
        "seller_identity_complete": seller_ok,
        "deal_ready": deal_ready,
        "is_suspended": suspended,
        "can_browse": True,
        "can_interest": not suspended,
        # 매물 올리기 = Lv2 + 판매자 공개 신원 (중개자 고지 의무)
        "can_list": profile_ok and seller_ok and not suspended,
        # 입찰 = Lv1(이메일)만 — 실명·휴대폰(Lv2)은 낙찰 후 결제·이전 단계
        "can_bid": email_verified and not suspended,
        # 낙찰 후 결제·인수 등 구매 이행
        "can_fulfill_purchase": profile_ok and not suspended,
        "can_close_deal": deal_ready and not suspended,
        "can_report": profile_ok and not suspended,
        # 유저 차단: 로그인 + 정지 아님 (Lv 무관 — 개인 안전)
        "can_block": not suspended,
        "missing": missing,
    }


# --- user blocks (user ↔ user; not project reports) ---


def is_blocked_either(conn: sqlite3.Connection, user_a: int | None, user_b: int | None) -> bool:
    """True if either user has blocked the other (bidirectional interaction guard)."""
    if not user_a or not user_b:
        return False
    a, b = int(user_a), int(user_b)
    if a == b:
        return False
    row = conn.execute(
        """
        SELECT 1 FROM user_blocks
        WHERE (blocker_id = ? AND blocked_id = ?)
           OR (blocker_id = ? AND blocked_id = ?)
        LIMIT 1
        """,
        (a, b, b, a),
    ).fetchone()
    return bool(row)


def is_blocked_by(conn: sqlite3.Connection, blocker_id: int, blocked_id: int) -> bool:
    """True if blocker_id has blocked blocked_id (one-way)."""
    row = conn.execute(
        """
        SELECT 1 FROM user_blocks
        WHERE blocker_id = ? AND blocked_id = ?
        LIMIT 1
        """,
        (int(blocker_id), int(blocked_id)),
    ).fetchone()
    return bool(row)


def blocked_owner_ids(conn: sqlite3.Connection, viewer_id: int | None) -> set[int]:
    """Owners whose listings should be hidden from viewer (viewer blocked them, or they blocked viewer)."""
    if not viewer_id:
        return set()
    vid = int(viewer_id)
    rows = conn.execute(
        """
        SELECT blocked_id AS uid FROM user_blocks WHERE blocker_id = ?
        UNION
        SELECT blocker_id AS uid FROM user_blocks WHERE blocked_id = ?
        """,
        (vid, vid),
    ).fetchall()
    return {int(r["uid"]) for r in rows if r["uid"] is not None}


def list_user_blocks(conn: sqlite3.Connection, blocker_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT b.id, b.blocked_id, b.created_at,
               u.display_name, u.email
        FROM user_blocks b
        JOIN users u ON u.id = b.blocked_id
        WHERE b.blocker_id = ?
        ORDER BY b.id DESC
        LIMIT 200
        """,
        (int(blocker_id),),
    ).fetchall()
    out = []
    for r in rows:
        email = (r["email"] or "").strip()
        masked = email
        if "@" in email:
            local, _, domain = email.partition("@")
            masked = (local[:1] + "***@" + domain) if local else ("***@" + domain)
        out.append(
            {
                "id": int(r["id"]),
                "blocked_user_id": int(r["blocked_id"]),
                "display_name": (r["display_name"] or "").strip() or "사용자",
                "email_masked": masked,
                "created_at": r["created_at"],
            }
        )
    return out


def create_user_block(conn: sqlite3.Connection, blocker_id: int, blocked_id: int) -> dict:
    """Insert block. Caller must validate ids and not self."""
    now = _now()
    conn.execute(
        """
        INSERT OR IGNORE INTO user_blocks (blocker_id, blocked_id, created_at)
        VALUES (?, ?, ?)
        """,
        (int(blocker_id), int(blocked_id), now),
    )
    row = conn.execute(
        """
        SELECT id, blocker_id, blocked_id, created_at FROM user_blocks
        WHERE blocker_id = ? AND blocked_id = ?
        """,
        (int(blocker_id), int(blocked_id)),
    ).fetchone()
    return {
        "id": int(row["id"]),
        "blocker_id": int(row["blocker_id"]),
        "blocked_id": int(row["blocked_id"]),
        "created_at": row["created_at"],
    }


def delete_user_block(conn: sqlite3.Connection, blocker_id: int, blocked_id: int) -> bool:
    cur = conn.execute(
        "DELETE FROM user_blocks WHERE blocker_id = ? AND blocked_id = ?",
        (int(blocker_id), int(blocked_id)),
    )
    return cur.rowcount > 0


def seller_identity_complete(row: sqlite3.Row | dict | None) -> bool:
    """구매자가 판매자를 특정할 수 있는 최소 공개 정보가 있는지."""
    if not row:
        return False

    def g(key: str, default=None):
        try:
            if isinstance(row, dict):
                return row.get(key, default)
            return row[key] if key in row.keys() else default
        except (IndexError, KeyError):
            return default

    st = (g("seller_type") or "").strip()
    name = (g("seller_trade_name") or "").strip()
    email = (g("seller_contact_email") or "").strip()
    phone = (g("seller_contact_phone") or "").strip()
    if st not in ("individual", "business"):
        return False
    if len(name) < 2 or "@" not in email or len(phone) < 10:
        return False
    if st == "business":
        biz = re.sub(r"\D", "", (g("seller_biz_no") or ""))
        ceo = (g("seller_ceo_name") or "").strip()
        if len(biz) < 10 or len(ceo) < 2:
            return False
    return True


def public_seller_identity(
    row: sqlite3.Row | dict | None,
    *,
    reveal_contact: bool = False,
) -> dict | None:
    """
    매물 상세 등 구매자 확인용 판매자 신원.
    전자상거래법상 통신판매중개 — 판매자 특정 가능 정보 제공.

    개인정보 보호 (필수):
    - 전체 전화·이메일을 불특정 다수에게 노출하지 않음 (유출·불법 소지 위험).
    - 기본 마스킹. reveal_contact=True 는 낙찰 구매자·판매자 본인 등 권한 검사 후에만.
    """
    if not row or not seller_identity_complete(row):
        return None

    def g(key: str, default=None):
        try:
            if isinstance(row, dict):
                return row.get(key, default)
            return row[key] if key in row.keys() else default
        except (IndexError, KeyError):
            return default

    st = (g("seller_type") or "").strip()
    phone_raw = (g("seller_contact_phone") or "").strip()
    email_raw = (g("seller_contact_email") or "").strip()
    mail_order = (g("seller_mail_order_no") or "").strip()
    biz_no = (g("seller_biz_no") or "").strip()
    addr = (g("seller_address") or "").strip()
    if reveal_contact:
        phone_out = format_phone_display(phone_raw) if phone_raw else ""
        email_out = email_raw
        addr_out = addr
        contact_note = "낙찰·성사 당사자에게만 전체 연락처가 공개됩니다."
    else:
        phone_out = mask_phone_public(phone_raw) if phone_raw else ""
        email_out = mask_email_public(email_raw) if email_raw else ""
        # 주소는 시·군 정도만 대략 노출(앞 구간) — 전체 주소는 낙찰 후
        if addr and len(addr) > 12:
            addr_out = addr[:10] + "…"
        else:
            addr_out = addr
        contact_note = (
            "연락처는 일부만 표시됩니다. 낙찰(성사)된 구매자에게만 전체 전화·이메일이 공개됩니다."
        )
    out = {
        "type": st,
        "type_label": "사업자" if st == "business" else "개인판매자",
        "name": (g("seller_trade_name") or "").strip(),
        "ceo_name": (g("seller_ceo_name") or "").strip() if st == "business" else "",
        "business_reg_no": biz_no if st == "business" else "",
        "mail_order_report_no": mail_order,
        "mail_order_status": (
            "registered"
            if mail_order
            else ("not_registered" if st == "individual" else "not_registered")
        ),
        "mail_order_status_label": (
            "통신판매업 신고 완료" if mail_order else "통신판매업 신고번호 미등록(표시)"
        ),
        "contact_email": email_out,
        "contact_phone": phone_out,
        "address": addr_out,
        "contact_revealed": bool(reveal_contact),
        "note_ko": (
            "판매자가 직접 입력한 신고 정보입니다(본인인증 자동검증 전). "
            "통신판매중개 플랫폼에서 구매자가 판매자를 확인할 수 있도록 공개됩니다. "
            "운영자(코어랩스)는 거래 당사자가 아니며, 신원·품질을 보증하지 않습니다. "
            + contact_note
        ),
    }
    return out


def user_to_dict(row: sqlite3.Row, *, public: bool = False) -> dict:
    trust = compute_trust(row)
    credit = compute_credit(row, trust)
    phone_raw = (row["phone"] if "phone" in row.keys() else None) or ""
    base = {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"] or "",
        "created_at": row["created_at"],
        "trust": trust,
        "credit": {
            "score": credit["score"],
            "grade": credit["grade"],
            "label": credit["label"],
            "counts": credit["counts"],
            "buyer_rank": credit.get("buyer_rank"),
        },
    }
    if public:
        # never expose PII on public surfaces
        base["display_name"] = (row["display_name"] or "").strip() or "Member"
        base.pop("email", None)
        return base

    role = ""
    if "role" in row.keys():
        role = row["role"] or "both"
    birth = ""
    if "birth_date" in row.keys():
        birth = (row["birth_date"] or "").strip()
    suspended = bool(int(row["is_suspended"] or 0)) if "is_suspended" in row.keys() else False
    oauth_provider = ""
    if "oauth_provider" in row.keys():
        oauth_provider = (row["oauth_provider"] or "").strip()
    seller_identity = {
        "type": (row["seller_type"] if "seller_type" in row.keys() else None) or "",
        "trade_name": (row["seller_trade_name"] if "seller_trade_name" in row.keys() else None) or "",
        "ceo_name": (row["seller_ceo_name"] if "seller_ceo_name" in row.keys() else None) or "",
        "business_reg_no": (row["seller_biz_no"] if "seller_biz_no" in row.keys() else None) or "",
        "mail_order_report_no": (row["seller_mail_order_no"] if "seller_mail_order_no" in row.keys() else None)
        or "",
        "contact_email": (row["seller_contact_email"] if "seller_contact_email" in row.keys() else None)
        or "",
        "contact_phone": (row["seller_contact_phone"] if "seller_contact_phone" in row.keys() else None)
        or "",
        "address": (row["seller_address"] if "seller_address" in row.keys() else None) or "",
        "updated_at": (row["seller_identity_at"] if "seller_identity_at" in row.keys() else None) or "",
        "complete": seller_identity_complete(row),
    }
    return {
        **base,
        "credit": credit,  # full breakdown for self
        "birth_date": birth,  # self only — age verification record
        "needs_age_gate": not bool(birth),
        "oauth_provider": oauth_provider,
        "auth_method": oauth_provider if oauth_provider else "password",
        "is_suspended": suspended,
        "suspended_at": (row["suspended_at"] if "suspended_at" in row.keys() else None) or "",
        "suspend_reason": (row["suspend_reason"] if "suspend_reason" in row.keys() else None) or "",
        "real_name": (row["real_name"] if "real_name" in row.keys() else None) or "",
        "phone": phone_raw,
        "phone_display": format_phone_display(phone_raw) if phone_raw else "",
        "role": role or "both",
        "phone_verified": bool(int(row["phone_verified"] or 0)) if "phone_verified" in row.keys() else False,
        "seller_identity": seller_identity,
        "settlement": {
            "bank": (row["settlement_bank"] if "settlement_bank" in row.keys() else None) or "",
            "holder": (row["settlement_holder"] if "settlement_holder" in row.keys() else None) or "",
            # mask account in API responses — never expose full number
            "account_masked": _mask_account(
                decrypt_settlement_account(
                    (row["settlement_account"] if "settlement_account" in row.keys() else None) or ""
                )
            ),
            "has_account": bool(
                (row["settlement_account"] if "settlement_account" in row.keys() else None) or ""
            ),
            "is_business": bool(int(row["is_business"] or 0)) if "is_business" in row.keys() else False,
        },
        "profile_updated_at": (row["profile_updated_at"] if "profile_updated_at" in row.keys() else None) or "",
    }


def _mask_account(account: str) -> str:
    # accept encrypted blob or plain digits
    plain = decrypt_settlement_account(account) if (account or "").startswith(_SETTLEMENT_ENC_PREFIX) else (account or "")
    digits = re.sub(r"\D", "", plain)
    if len(digits) < 4:
        return "****" if digits else ""
    return "****" + digits[-4:]


def _row_get(row: sqlite3.Row, key: str, default=None):
    try:
        if key in row.keys():
            val = row[key]
            return default if val is None else val
    except (IndexError, KeyError):
        pass
    return default


# Product form / delivery channel (not the same as status = completion stage)
PRODUCT_TYPES: dict[str, str] = {
    "website": "웹사이트",
    "webapp": "웹 앱 / SaaS",
    "mobile": "모바일 앱",
    "desktop": "데스크톱 프로그램",
    "api": "API / SDK / 백엔드",
    "game": "게임",
    "other": "기타",
}

PRODUCT_TYPES_EN: dict[str, str] = {
    "website": "Website",
    "webapp": "Web app / SaaS",
    "mobile": "Mobile app",
    "desktop": "Desktop",
    "api": "API / SDK / backend",
    "game": "Game",
    "other": "Other",
}

# Demo / seed listings — EN copy for marketplace UI when lang=en (seller-authored KO kept)
LISTING_DEMO_I18N: dict[str, dict[str, str]] = {
    "ShopPulse": {
        "one_liner_en": "Order & shipping alerts for small shops — KakaoTalk draft",
        "story_en": (
            "A weekend-built order-alert service for neighborhood shops. "
            "Three shops used it for two weeks, then it paused. "
            "No time to market — handing off Kakao alimtalk code and a simple dashboard."
        ),
    },
    "ReceiptFold": {
        "one_liner_en": "Receipt photo → auto expense categories · mobile beta",
        "story_en": (
            "Personal expense app in Flutter. OCR via external API; "
            "category rules are rule-based. Stopped just before store submit after a job change."
        ),
    },
    "MeetNotes Lite": {
        "one_liner_en": "Upload meeting audio → summary & action items draft",
        "story_en": (
            "Next.js prototype: Whisper API + prompts for summaries. "
            "One-page UI, no payments or teams — but a running screen, not just a PDF idea."
        ),
    },
    "csv-kit": {
        "one_liner_en": "CSV merge, dedupe & column-mapping CLI toolkit",
        "story_en": (
            "Python CLI for data cleanup. pip-installable with a README. "
            "Terminal only — no GUI. Side project I'm transferring for lack of maintainer time."
        ),
    },
    "TraceDraft": {
        "one_liner_en": "AI interview answers → blog draft web tool",
        "story_en": (
            "Answer 5–7 questions and get a blog post draft. "
            "Prompting and edit UI included; two real posts shipped from it. "
            "Day job got busy — not scaling further."
        ),
    },
}


def normalize_product_type(value: str | None) -> str:
    raw = (value or "").strip().lower()
    aliases = {
        "web": "website",
        "site": "website",
        "웹사이트": "website",
        "웹": "website",
        "saas": "webapp",
        "web-app": "webapp",
        "웹앱": "webapp",
        "app": "mobile",
        "mobile_app": "mobile",
        "ios": "mobile",
        "android": "mobile",
        "어플": "mobile",
        "앱": "mobile",
        "모바일": "mobile",
        "pc": "desktop",
        "windows": "desktop",
        "mac": "desktop",
        "데스크톱": "desktop",
        "데스크탑": "desktop",
        "프로그램": "desktop",
        "backend": "api",
        "sdk": "api",
        "기타": "other",
    }
    key = aliases.get(raw, raw)
    if key in PRODUCT_TYPES:
        return key
    return "other"


def product_type_public(key: str | None) -> dict:
    k = normalize_product_type(key)
    return {
        "key": k,
        "label": PRODUCT_TYPES.get(k, PRODUCT_TYPES["other"]),
        "label_en": PRODUCT_TYPES_EN.get(k, PRODUCT_TYPES_EN["other"]),
    }


def _parse_demo_images(row: sqlite3.Row | dict) -> list[str]:
    raw = _row_get(row, "demo_images_json") if not isinstance(row, dict) else row.get("demo_images_json")
    try:
        data = json.loads(raw or "[]")
    except (json.JSONDecodeError, TypeError):
        data = []
    if not isinstance(data, list):
        return []
    out: list[str] = []
    for u in data:
        s = str(u or "").strip()
        if s.startswith("/media/demos/") and s not in out:
            out.append(s)
        if len(out) >= 5:
            break
    return out


def project_to_dict(row: sqlite3.Row, *, include_private: bool = False) -> dict:
    try:
        assets = json.loads(row["assets_json"] or "[]")
    except json.JSONDecodeError:
        assets = []
    try:
        keywords_raw = json.loads(_row_get(row, "keywords_json") or "[]")
    except (json.JSONDecodeError, TypeError):
        keywords_raw = []
    if not isinstance(keywords_raw, list):
        keywords_raw = []
    keywords = [str(k).strip() for k in keywords_raw if str(k).strip()][:5]
    try:
        features_raw = json.loads(_row_get(row, "features_json") or "[]")
    except (json.JSONDecodeError, TypeError):
        features_raw = []
    if not isinstance(features_raw, list):
        features_raw = []
    features = [str(f).strip() for f in features_raw if str(f).strip()][:12]
    acquisition = (_row_get(row, "acquisition") or "") or ""
    if acquisition not in ("made", "resale", "other"):
        acquisition = ""
    price_start = _row_get(row, "price_start")
    price_current = _row_get(row, "price_current")
    if price_current is None:
        price_current = price_start
    bid_count = int(_row_get(row, "bid_count", 0) or 0)
    # Unique bidders; fall back to bid_count only if column missing on very old rows
    bidder_raw = _row_get(row, "bidder_count")
    if bidder_raw is None:
        bidder_count = bid_count
    else:
        bidder_count = int(bidder_raw or 0)
    min_inc = int(_row_get(row, "min_increment", 10000) or 10000)
    auction_status = (_row_get(row, "auction_status") or "live") or "live"
    ends = _row_get(row, "auction_ends_at") or ""
    # Public: next minimum bid amount
    base = int(price_current or 0)
    if bid_count == 0 and price_start is not None:
        next_min = int(price_start)
    else:
        next_min = base + min_inc

    sold_price = _row_get(row, "sold_price")
    fee = fee_breakdown(sold_price if sold_price is not None else price_current)
    ptype = product_type_public(_row_get(row, "product_type"))
    status_raw = _row_get(row, "status")
    title = row["title"] or ""
    demo_i18n = LISTING_DEMO_I18N.get(title) or {}
    data = {
        "id": row["id"],
        "owner_id": row["owner_id"],
        "title": title,
        "one_liner": row["one_liner"],
        "one_liner_en": demo_i18n.get("one_liner_en") or "",
        "status": row["status"],
        "status_label": price_policy.status_label(status_raw, lang="ko"),
        "status_label_en": price_policy.status_label(status_raw, lang="en"),
        "product_type": ptype["key"],
        "product_type_label": ptype["label"],
        "product_type_label_en": ptype["label_en"],
        "story": row["story"],
        "story_en": demo_i18n.get("story_en") or "",
        "demo": row["demo"],
        "demo_images": _parse_demo_images(row),
        "assets": assets,
        "keywords": keywords,
        "features": features,
        "audience": (_row_get(row, "audience") or "") or "",
        "works_now": (_row_get(row, "works_now") or "") or "",
        "limits": (_row_get(row, "limits_note") or "") or "",
        "acquisition": acquisition,
        "acquisition_note": (_row_get(row, "acquisition_note") or "") or "",
        "price_start": price_start,
        "price_current": price_current,
        "price_buy_now": _row_get(row, "price_buy_now"),
        "bid_count": bid_count,
        "bidder_count": bidder_count,
        "min_increment": min_inc,
        "next_min_bid": next_min,
        "auction_ends_at": ends,
        "auction_status": auction_status,
        "is_live": auction_status == "live" and (row["listing_status"] or "") == "approved",
        "is_paused": auction_status == "paused",
        "listing_status": row["listing_status"],
        "round_started_at": (_row_get(row, "round_started_at") or "") or "",
        "round_number": int(_row_get(row, "round_number") or 0),
        "auction_days_intended": int(_row_get(row, "auction_days_intended") or 7),
        "can_relist": (
            (row["listing_status"] or "") in ("archived", "rejected", "hold")
            or (
                (row["listing_status"] or "") == "approved"
                and auction_status in ("ended", "paused")
            )
        )
        and auction_status != "sold"
        and not (_row_get(row, "sold_at") or ""),
        # 헬프티켓 (공개: 판매자 설정 / 당사자: 잔여)
        "q_credits_offered": int(_row_get(row, "q_credits_offered") or 0),
        "q_credit_unit_price": int(_row_get(row, "q_credit_unit_price") or 0),
        "q_credit_sla_hours": int(_row_get(row, "q_credit_sla_hours") or 48),
        "q_credits_total": int(_row_get(row, "q_credits_total") or 0),
        "q_credits_remaining": int(_row_get(row, "q_credits_remaining") or 0),
        "q_credits_held": int(_row_get(row, "q_credits_held") or 0),
        "q_credits_purchased": int(_row_get(row, "q_credits_purchased") or 0),
        "q_window_ends_at": (_row_get(row, "q_window_ends_at") or "") or "",
        "q_credits_extra_for_sale": int(_row_get(row, "q_credit_unit_price") or 0) > 0,
        "report_count": int(_row_get(row, "report_count", 0) or 0),
        "paused_reason": _row_get(row, "paused_reason") or "",
        "license_note": (_row_get(row, "license_note") or "") or "",
        "demo_verified": bool(int(_row_get(row, "demo_verified", 0) or 0)),
        # Trust exposure (from SQL join or computed later)
        "exposure_score": (
            int(_row_get(row, "exposure_score"))
            if _row_get(row, "exposure_score") is not None
            else None
        ),
        # Premium boost scaffold (no purchase UI yet)
        "boost": project_boost_public(row),
        "sold_price": sold_price,
        "sold_at": _row_get(row, "sold_at") or "",
        "buyer_id": _row_get(row, "buyer_id"),
        "deal_note": _row_get(row, "deal_note") or "",
        "deal_status": _row_get(row, "deal_status") or "",
        "payment_deadline_at": _row_get(row, "payment_deadline_at") or "",
        "paid_at": _row_get(row, "paid_at") or "",
        "transfer_started_at": _row_get(row, "transfer_started_at") or "",
        "inspection_deadline_at": _row_get(row, "inspection_deadline_at") or "",
        "buyer_accepted_at": _row_get(row, "buyer_accepted_at") or "",
        "settled_at": _row_get(row, "settled_at") or "",
        "deal_dispute_note": _row_get(row, "deal_dispute_note") or "",
        "deal_policy": deal_policy_public(),
        "fee": fee,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if include_private:
        data["contact"] = row["contact"] or ""
        data["review_note"] = _row_get(row, "review_note") or ""
        data["reviewed_at"] = _row_get(row, "reviewed_at") or ""
        try:
            data["review_checklist"] = json.loads(_row_get(row, "review_checklist_json") or "{}")
        except json.JSONDecodeError:
            data["review_checklist"] = {}
        try:
            data["seller_attest"] = json.loads(_row_get(row, "seller_attest_json") or "{}")
        except json.JSONDecodeError:
            data["seller_attest"] = {}
    return data


# Seller success fee — flat 10% of deal price (buyer pays only deal price)
FEE_RATE = 0.10
FEE_PAYER = "seller"


def premium_boost_feature_enabled() -> bool:
    """Master switch for selling/showing boost products. Sort still works if rows have boost_until."""
    return os.environ.get("PREMIUM_BOOST_ENABLED", "0").strip() not in {
        "0",
        "false",
        "False",
        "",
    }


def listing_collection_mode() -> bool:
    """Cold-start mode: approved listings go live but their auction clock does not
    start (auction_ends_at left empty) until an admin releases them all at once
    (see release_all_paused_auctions). Default OFF; set WA_LISTING_COLLECTION_MODE=1
    while stockpiling listings before the public launch/buyer push."""
    return os.environ.get("WA_LISTING_COLLECTION_MODE", "0").strip() not in {
        "0",
        "false",
        "False",
        "",
    }


def release_all_paused_auctions(conn: sqlite3.Connection) -> int:
    """Launch-day trigger: give every live listing that's been waiting with no
    auction clock (created during listing_collection_mode) a fresh, synchronized
    countdown starting now. Returns the number of listings released."""
    rows = conn.execute(
        """
        SELECT id, auction_days_intended FROM projects
        WHERE listing_status = 'approved'
          AND COALESCE(auction_status, 'live') = 'live'
          AND (auction_ends_at IS NULL OR auction_ends_at = '')
        """
    ).fetchall()
    now = _now()
    n = 0
    for row in rows:
        days = max(1, min(int(row["auction_days_intended"] or 7), 30))
        try:
            from datetime import datetime, timedelta, timezone

            ends = (datetime.now(timezone.utc) + timedelta(days=days)).astimezone().isoformat(
                timespec="seconds"
            )
        except Exception:
            ends = now
        conn.execute(
            "UPDATE projects SET auction_ends_at = ?, round_started_at = ?, updated_at = ? WHERE id = ?",
            (ends, now, now, int(row["id"])),
        )
        n += 1
    return n


def project_boost_active(row: sqlite3.Row | dict, *, now: str | None = None) -> bool:
    until = (_row_get(row, "boost_until") or "") if not isinstance(row, dict) else (row.get("boost_until") or "")
    until = (until or "").strip()
    if not until:
        return False
    now = now or _now()
    # ISO strings with offset compare correctly if same format; string compare works for zero-padded ISO
    return until > now


def project_boost_public(row: sqlite3.Row | dict) -> dict:
    """Public boost fields for API cards. purchase UI gated by PREMIUM_BOOST_ENABLED."""
    until = (_row_get(row, "boost_until") or "") or ""
    if isinstance(row, dict):
        until = (row.get("boost_until") or "") or ""
        tier = int(row.get("boost_tier") or 0)
        product = (row.get("boost_product") or "") or ""
    else:
        tier = int(_row_get(row, "boost_tier", 0) or 0)
        product = (_row_get(row, "boost_product") or "") or ""
    until = until.strip()
    active = bool(until and project_boost_active(row))
    return {
        "active": active,
        "until": until if until else "",
        "tier": tier if active or tier else 0,
        "product": product,
        # clients: hide "Buy boost" until true
        "purchase_enabled": premium_boost_feature_enabled(),
    }


def public_live_where_sql(alias: str = "") -> str:
    """Only the current live auction round is publicly listed."""
    p = f"{alias}." if alias else ""
    return (
        f"{p}listing_status = 'approved' "
        f"AND COALESCE({p}auction_status, 'live') = 'live'"
    )


# 예비 구매자 기준 가산점: 매물 설명·포트폴리오 완성도 + 헬프티켓 개수 비례
# (판매자 신용·신원 이력은 별도 — 노출 가산점에 넣지 않음)
HELP_TICKET_POINTS_PER = 8  # 포함 헬프티켓 1회당
HELP_TICKET_POINTS_CAP = 24  # 최대 3회 × 8
PORTFOLIO_POINTS_CAP = 60
EXPOSURE_SCORE_CAP = 100


def listing_trust_score_sql(project_alias: str = "p", user_alias: str = "u") -> str:
    """
    SQL exposure score for prospective buyers:
    1) Listing description + portfolio quality
    2) Help-ticket count (proportional)

    user_alias kept for call-site compatibility; not used in score.
    """
    p = project_alias
    _ = user_alias
    # Portfolio / description quality (max ~60)
    portfolio = f"""(
      CASE WHEN LENGTH(COALESCE({p}.one_liner, '')) >= 15 THEN 4 ELSE 0 END
      + CASE WHEN LENGTH(COALESCE({p}.story, '')) >= 80 THEN 8
             WHEN LENGTH(COALESCE({p}.story, '')) >= 40 THEN 5
             WHEN LENGTH(COALESCE({p}.story, '')) >= 20 THEN 2
             ELSE 0 END
      + CASE WHEN LENGTH(COALESCE({p}.features_json, '')) > 80 THEN 10
             WHEN LENGTH(COALESCE({p}.features_json, '')) > 30 THEN 6
             WHEN LENGTH(COALESCE({p}.features_json, '')) > 10 THEN 3
             ELSE 0 END
      + CASE WHEN LENGTH(COALESCE({p}.works_now, '')) >= 40 THEN 8
             WHEN LENGTH(COALESCE({p}.works_now, '')) >= 20 THEN 5
             ELSE 0 END
      + CASE WHEN LENGTH(COALESCE({p}.limits_note, '')) >= 20 THEN 6
             WHEN LENGTH(COALESCE({p}.limits_note, '')) >= 10 THEN 3
             ELSE 0 END
      + CASE WHEN LENGTH(COALESCE({p}.audience, '')) >= 8 THEN 3 ELSE 0 END
      + CASE WHEN LENGTH(COALESCE({p}.demo, '')) >= 8 THEN 3 ELSE 0 END
      + CASE WHEN LENGTH(COALESCE({p}.demo_images_json, '')) > 120 THEN 12
             WHEN LENGTH(COALESCE({p}.demo_images_json, '')) > 40 THEN 8
             WHEN LENGTH(COALESCE({p}.demo_images_json, '')) > 8 THEN 4
             ELSE 0 END
      + CASE WHEN COALESCE({p}.demo_verified, 0) = 1 THEN 6 ELSE 0 END
      + CASE WHEN LENGTH(COALESCE({p}.license_note, '')) >= 5 THEN 2 ELSE 0 END
      + CASE WHEN LENGTH(COALESCE({p}.keywords_json, '')) > 8 THEN 2 ELSE 0 END
    )"""
    # Help tickets: linear with offered count (1–3 free) × points, capped
    help_t = f"""(
      MIN(
        {HELP_TICKET_POINTS_CAP},
        MIN({Q_CREDITS_INCLUDED_MAX}, MAX(0, COALESCE({p}.q_credits_offered, 0)))
          * {HELP_TICKET_POINTS_PER}
      )
      + CASE WHEN COALESCE({p}.q_credit_unit_price, 0) >= 5000 THEN 4 ELSE 0 END
    )"""
    return f"MIN({EXPOSURE_SCORE_CAP}, ({portfolio}) + ({help_t}))"


def listing_sort_sql(project_alias: str = "p", user_alias: str = "u") -> str:
    """
    Marketplace ORDER BY:
    1) Paid boost (optional)
    2) Buyer-facing exposure score DESC (portfolio + help tickets)
    3) round_started_at ASC (same score → round queue; relist back of line)
    4) id ASC

    Placeholder `?` = now ISO for boost window.
    """
    p = project_alias
    score = listing_trust_score_sql(project_alias, user_alias)
    return (
        "ORDER BY "
        f"CASE WHEN IFNULL({p}.boost_until, '') != '' AND {p}.boost_until > ? "
        f"THEN COALESCE({p}.boost_tier, 0) ELSE 0 END DESC, "
        f"{score} DESC, "
        f"COALESCE(NULLIF({p}.round_started_at, ''), {p}.created_at, printf('%020d', {p}.id)) ASC, "
        f"{p}.id ASC"
    )


def compute_listing_exposure_score(
    project_row: sqlite3.Row | dict,
    owner_row: sqlite3.Row | dict | None = None,
) -> dict:
    """Python mirror: portfolio quality + help tickets only (buyer-facing)."""

    def pg(key: str, default=0):
        try:
            if isinstance(project_row, dict):
                v = project_row.get(key, default)
            else:
                v = project_row[key] if key in project_row.keys() else default
            return default if v is None else v
        except (IndexError, KeyError):
            return default

    _ = owner_row  # not used — exposure is listing quality for buyers
    parts: dict[str, int] = {}

    one = str(pg("one_liner") or "")
    parts["one_liner"] = 4 if len(one) >= 15 else 0
    story = str(pg("story") or "")
    if len(story) >= 80:
        parts["story"] = 8
    elif len(story) >= 40:
        parts["story"] = 5
    elif len(story) >= 20:
        parts["story"] = 2
    else:
        parts["story"] = 0
    feats = str(pg("features_json") or "")
    if len(feats) > 80:
        parts["features"] = 10
    elif len(feats) > 30:
        parts["features"] = 6
    elif len(feats) > 10:
        parts["features"] = 3
    else:
        parts["features"] = 0
    works = str(pg("works_now") or "")
    parts["works_now"] = 8 if len(works) >= 40 else (5 if len(works) >= 20 else 0)
    limits = str(pg("limits_note") or "")
    parts["limits"] = 6 if len(limits) >= 20 else (3 if len(limits) >= 10 else 0)
    parts["audience"] = 3 if len(str(pg("audience") or "")) >= 8 else 0
    parts["demo_text"] = 3 if len(str(pg("demo") or "")) >= 8 else 0
    demos = str(pg("demo_images_json") or "")
    if len(demos) > 120:
        parts["portfolio_shots"] = 12
    elif len(demos) > 40:
        parts["portfolio_shots"] = 8
    elif len(demos) > 8:
        parts["portfolio_shots"] = 4
    else:
        parts["portfolio_shots"] = 0
    parts["demo_verified"] = 6 if int(pg("demo_verified") or 0) else 0
    parts["license"] = 2 if len(str(pg("license_note") or "")) >= 5 else 0
    parts["keywords"] = 2 if len(str(pg("keywords_json") or "")) > 8 else 0

    portfolio_sub = sum(
        parts[k]
        for k in parts
        if k
        not in (
            "help_tickets",
            "help_addon_sale",
        )
    )
    # soft cap portfolio contribution
    if portfolio_sub > PORTFOLIO_POINTS_CAP:
        # scale down proportionally for display consistency with SQL MIN cap on total
        pass

    q_off = max(
        0,
        min(Q_CREDITS_INCLUDED_MAX, int(pg("q_credits_offered") or 0)),
    )
    parts["help_tickets"] = min(
        HELP_TICKET_POINTS_CAP, q_off * HELP_TICKET_POINTS_PER
    )
    parts["help_addon_sale"] = (
        4 if int(pg("q_credit_unit_price") or 0) >= 5000 else 0
    )

    total = int(sum(parts.values()))
    total = min(EXPOSURE_SCORE_CAP, total)
    return {
        "score": total,
        "parts": parts,
        "label_ko": (
            "높음" if total >= 50 else ("보통" if total >= 25 else "낮음")
        ),
        "note_ko": (
            "예비 구매자 기준 가산점: 매물 설명·포트폴리오 완성도 + 헬프티켓 개수 비례. "
            "점수 높을수록 공개 목록 상위에 노출됩니다."
        ),
        "rules": {
            "help_ticket_points_per": HELP_TICKET_POINTS_PER,
            "help_ticket_cap": HELP_TICKET_POINTS_CAP,
            "portfolio_cap": PORTFOLIO_POINTS_CAP,
            "score_cap": EXPOSURE_SCORE_CAP,
        },
    }


def start_auction_round(
    conn: sqlite3.Connection,
    project_id: int,
    *,
    auction_days: int | None = None,
    clear_boost: bool = True,
) -> sqlite3.Row:
    """
    Begin a public auction round after ops approve.
    - New round_started_at (queue position = back if relist)
    - Fresh auction_ends_at from now + days
    - Reset bid counters / current price to start for the new round
    """
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise ValueError("project not found")
    days = int(auction_days if auction_days is not None else (_row_get(row, "auction_days_intended") or 7))
    days = max(1, min(days, 30))
    now = _now()
    if listing_collection_mode():
        # Cold-start: go live on the board, but don't start the clock yet —
        # release_all_paused_auctions() starts every held listing at once on launch day.
        ends = ""
    else:
        try:
            from datetime import datetime, timedelta, timezone

            ends = (datetime.now(timezone.utc) + timedelta(days=days)).astimezone().isoformat(
                timespec="seconds"
            )
        except Exception:
            ends = now
    start_price = int(_row_get(row, "price_start") or 0)
    rn = int(_row_get(row, "round_number") or 0) + 1
    boost_sql = ", boost_until = NULL, boost_tier = 0, boost_product = NULL" if clear_boost else ""
    conn.execute(
        f"""
        UPDATE projects SET
          listing_status = 'approved',
          auction_status = 'live',
          auction_days_intended = ?,
          auction_ends_at = ?,
          round_started_at = ?,
          round_number = ?,
          price_current = ?,
          bid_count = 0,
          bidder_count = 0,
          paused_reason = '',
          deal_note = '',
          reviewed_at = ?,
          updated_at = ?
          {boost_sql}
        WHERE id = ?
        """,
        (days, ends, now, rn, start_price, now, now, project_id),
    )
    fresh = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not fresh:
        raise ValueError("project not found after start_auction_round")
    return fresh


def archive_unsold_round(
    conn: sqlite3.Connection,
    project_id: int,
    *,
    note: str = "마감 · 입찰 없음 · 이번 라운드 종료",
) -> None:
    """End a live round with no sale — leave the public board (not permanent display)."""
    now = _now()
    conn.execute(
        """
        UPDATE projects SET
          auction_status = 'ended',
          listing_status = 'archived',
          deal_note = ?,
          updated_at = ?
        WHERE id = ?
        """,
        (note[:500], now, project_id),
    )


def set_project_boost(
    conn: sqlite3.Connection,
    project_id: int,
    *,
    until_iso: str,
    tier: int = 1,
    product: str = "",
) -> sqlite3.Row:
    """
    Activate/update boost on a listing (admin or future payment webhook).
    Does not charge money — call after payment confirmed.
    """
    until = (until_iso or "").strip()
    if not until:
        raise ValueError("boost_until required")
    tier = max(0, min(int(tier), 100))
    product = (product or "").strip()[:40]
    now = _now()
    conn.execute(
        """
        UPDATE projects SET
          boost_until = ?,
          boost_tier = ?,
          boost_product = ?,
          updated_at = ?
        WHERE id = ?
        """,
        (until, tier, product, now, int(project_id)),
    )
    row = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (int(project_id),)
    ).fetchone()
    if not row:
        raise ValueError("project not found")
    return row


def clear_project_boost(conn: sqlite3.Connection, project_id: int) -> sqlite3.Row:
    """Remove boost (expiry job or admin)."""
    now = _now()
    conn.execute(
        """
        UPDATE projects SET
          boost_until = NULL,
          boost_tier = 0,
          boost_product = NULL,
          updated_at = ?
        WHERE id = ?
        """,
        (now, int(project_id)),
    )
    row = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (int(project_id),)
    ).fetchone()
    if not row:
        raise ValueError("project not found")
    return row


# Listing asset keys → buyer receipt checklist labels
HANDOVER_ASSET_LABELS: dict[str, tuple[str, str]] = {
    "code": (
        "소스·코드 (GitHub 이전 또는 ZIP 등 합의 방식)",
        "Source/code (GitHub transfer or agreed ZIP/link)",
    ),
    "design": ("디자인 파일 (피그마 등)", "Design files (Figma, etc.)"),
    "domain": (
        "도메인 소유권 이전 (등록업체 Push/Transfer)",
        "Domain ownership transfer (registrar push/transfer)",
    ),
    "docs": (
        "기획·문서·README/실행 매뉴얼",
        "Docs / README / runbook",
    ),
    "accounts": (
        "계정·스토어·호스팅 권한 또는 재배포 안내",
        "Accounts / store / hosting access or redeploy guide",
    ),
    "other": ("기타 포함 자산 이전", "Other included assets handed over"),
    "readme": ("README·운영 매뉴얼", "README / ops manual"),
}

# Always appended (not from assets)
HANDOVER_FIXED_ITEMS: list[dict[str, Any]] = [
    {
        "id": "access_guide",
        "label_ko": "실행·배포·DB/API 연결 방법 안내를 받았다",
        "label_en": "Received run / deploy / DB-API connection instructions",
        "required": True,
    },
    {
        "id": "secrets_ok",
        "label_ko": "키·시크릿은 재발급 또는 안전한 이전 절차를 안내받았다",
        "label_en": "Keys/secrets reissued or transferred via a safe procedure",
        "required": True,
    },
    {
        "id": "license_ok",
        "label_ko": "라이선스·양도 조건을 이해했다",
        "label_en": "Understood license / transfer terms",
        "required": True,
    },
]


def _parse_assets_list(row: sqlite3.Row | dict) -> list[str]:
    raw = _row_get(row, "assets_json") if not isinstance(row, dict) else row.get("assets_json")
    if isinstance(row, dict) and "assets" in row and isinstance(row["assets"], list):
        return [str(a).strip() for a in row["assets"] if str(a).strip()]
    try:
        data = json.loads(raw or "[]")
    except (json.JSONDecodeError, TypeError):
        data = []
    if not isinstance(data, list):
        return []
    return [str(a).strip() for a in data if str(a).strip()][:20]


def seed_handover_checklist(row: sqlite3.Row | dict) -> dict:
    """Build checklist from listing assets + fixed receipt items."""
    assets = _parse_assets_list(row)
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in assets:
        k = key.lower()
        if k in seen:
            continue
        seen.add(k)
        labels = HANDOVER_ASSET_LABELS.get(k)
        if labels:
            ko, en = labels
        else:
            ko, en = f"포함 자산: {key}", f"Asset: {key}"
        items.append(
            {
                "id": f"asset_{k}"[:40],
                "label_ko": ko,
                "label_en": en,
                "required": True,
                "checked": False,
                "checked_at": None,
            }
        )
    if not items:
        items.append(
            {
                "id": "asset_bundle",
                "label_ko": "매물에 포함된 핵심 자산 이전",
                "label_en": "Core listed assets handed over",
                "required": True,
                "checked": False,
                "checked_at": None,
            }
        )
    for fix in HANDOVER_FIXED_ITEMS:
        if fix["id"] in seen:
            continue
        items.append(
            {
                "id": fix["id"],
                "label_ko": fix["label_ko"],
                "label_en": fix["label_en"],
                "required": bool(fix.get("required", True)),
                "checked": False,
                "checked_at": None,
            }
        )
    now = _now()
    return {
        "items": items,
        "seeded_at": now,
        "updated_at": now,
        "disclaimer_ko": (
            "체크는 구매자 확인이며, WakeAgain이 파일·계정 이전을 검증하거나 보증하지 않습니다. "
            "이전은 판매자·구매자가 쪽지 등으로 직접 진행합니다."
        ),
        "disclaimer_en": (
            "Checks are the buyer's confirmation; WakeAgain does not verify or guarantee "
            "file/account transfer. Parties hand off via messages etc."
        ),
    }


def load_handover_checklist(row: sqlite3.Row | dict) -> dict | None:
    raw = _row_get(row, "handover_checklist_json")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return None
    return data


def handover_checklist_public(data: dict | None) -> dict | None:
    if not data:
        return None
    items = data.get("items") or []
    total = len(items)
    checked_n = sum(1 for it in items if it.get("checked"))
    required = [it for it in items if it.get("required", True)]
    req_n = len(required)
    req_ok = sum(1 for it in required if it.get("checked"))
    return {
        "items": items,
        "total": total,
        "checked_count": checked_n,
        "required_count": req_n,
        "required_checked": req_ok,
        "all_required_checked": req_n > 0 and req_ok >= req_n,
        "seeded_at": data.get("seeded_at") or "",
        "updated_at": data.get("updated_at") or "",
        "disclaimer_ko": data.get("disclaimer_ko") or "",
        "disclaimer_en": data.get("disclaimer_en") or "",
    }


def ensure_handover_checklist(
    conn: sqlite3.Connection, row: sqlite3.Row
) -> tuple[sqlite3.Row, dict]:
    """Seed checklist once after sale; return (row, public checklist)."""
    existing = load_handover_checklist(row)
    if existing and existing.get("items"):
        return row, handover_checklist_public(existing)  # type: ignore[return-value]
    seeded = seed_handover_checklist(row)
    pid = int(row["id"])
    now = _now()
    conn.execute(
        "UPDATE projects SET handover_checklist_json = ?, updated_at = ? WHERE id = ?",
        (json.dumps(seeded, ensure_ascii=False), now, pid),
    )
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    return row, handover_checklist_public(seeded)  # type: ignore[return-value]


def apply_handover_checks(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    checks: dict[str, bool],
) -> tuple[sqlite3.Row, dict]:
    """Buyer updates checked flags. checks: { item_id: true/false }."""
    row, pub = ensure_handover_checklist(conn, row)
    data = load_handover_checklist(row) or seed_handover_checklist(row)
    now = _now()
    items = data.get("items") or []
    for it in items:
        iid = str(it.get("id") or "")
        if iid not in checks:
            continue
        want = bool(checks[iid])
        it["checked"] = want
        it["checked_at"] = now if want else None
    data["items"] = items
    data["updated_at"] = now
    pid = int(row["id"])
    conn.execute(
        "UPDATE projects SET handover_checklist_json = ?, updated_at = ? WHERE id = ?",
        (json.dumps(data, ensure_ascii=False), now, pid),
    )
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    return row, handover_checklist_public(data)  # type: ignore[return-value]


def handover_all_required_checked(row: sqlite3.Row | dict) -> bool:
    data = load_handover_checklist(row)
    if not data:
        return False
    pub = handover_checklist_public(data)
    return bool(pub and pub.get("all_required_checked"))


def fee_breakdown(amount: int | None, *, rate: float | None = None) -> dict:
    """Seller success fee. Default 10%. Coupon may pass rate=0.08 (「수수료 8% 쿠폰」)."""
    r = FEE_RATE if rate is None else float(rate)
    if r <= 0 or r > 0.5:
        r = FEE_RATE
    rate_pct = int(round(r * 100))
    if amount is None:
        return {
            "rate": r,
            "rate_pct": rate_pct,
            "payer": FEE_PAYER,
            "payer_ko": "판매자",
            "amount": None,
            "fee": None,
            "seller_net": None,
            "coupon_applied": rate is not None and abs(r - FEE_RATE) > 1e-9,
            "note": (
                f"성사 시 판매자 수수료 {rate_pct}%. 구매자는 합의가만 부담."
                if rate is not None
                else "성사 시 판매자에게 거래 대금의 10% 수수료. 구매자는 합의가만 부담."
            ),
        }
    amt = int(amount)
    fee = int(round(amt * r))
    return {
        "rate": r,
        "rate_pct": rate_pct,
        "payer": FEE_PAYER,
        "payer_ko": "판매자",
        "amount": amt,
        "fee": fee,
        "seller_net": amt - fee,
        "coupon_applied": rate is not None and abs(r - FEE_RATE) > 1e-9,
        "note": (
            f"판매자 수수료 {rate_pct}% 적용"
            + (" (쿠폰)" if rate is not None and abs(r - FEE_RATE) > 1e-9 else "")
            + ". 구매자는 합의가만 부담."
        ),
    }


# --- Marketing coupons (seller success fee 8% etc.) ---

DEFAULT_COUPON_FEE_RATE = 0.08


def ensure_coupon_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS coupon_campaigns (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          code TEXT NOT NULL UNIQUE COLLATE NOCASE,
          name TEXT NOT NULL,
          fee_rate REAL NOT NULL DEFAULT 0.08,
          max_redemptions INTEGER NOT NULL,
          redeem_count INTEGER NOT NULL DEFAULT 0,
          active INTEGER NOT NULL DEFAULT 1,
          note TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_coupons (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          campaign_id INTEGER NOT NULL REFERENCES coupon_campaigns(id) ON DELETE CASCADE,
          origin TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'available',
          used_project_id INTEGER,
          used_at TEXT,
          gifted_from_id INTEGER,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS promo_submissions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          campaign_id INTEGER NOT NULL REFERENCES coupon_campaigns(id) ON DELETE CASCADE,
          post_url TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          admin_note TEXT,
          reviewed_at TEXT,
          claimed_at TEXT,
          user_coupon_id INTEGER,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_user_coupons_user ON user_coupons(user_id);
        CREATE INDEX IF NOT EXISTS idx_promo_sub_user ON promo_submissions(user_id);
        CREATE INDEX IF NOT EXISTS idx_promo_sub_status ON promo_submissions(status);
        """
    )
    _ensure_columns(
        conn,
        "coupon_campaigns",
        {
            # Viral URL verify flow (no public code on event page)
            "allow_url_claim": "INTEGER NOT NULL DEFAULT 0",
            # Optional event window (ISO). Empty = no bound on that side.
            "starts_at": "TEXT",
            "ends_at": "TEXT",
        },
    )
    _ensure_columns(
        conn,
        "promo_submissions",
        {
            # x | linkedin_blog | community | instagram
            "channel": "TEXT NOT NULL DEFAULT 'instagram'",
        },
    )


# Unified viral event: all channels → same 8% fee coupon; 1 claim / account / campaign
PROMO_CHANNELS: dict[str, dict[str, str]] = {
    "x": {
        "id": "x",
        "label_ko": "X (트위터)",
        "short_ko": "X",
        "hint_ko": "WakeAgain 소개글 URL (게시물에 사이트 링크 포함)",
        "placeholder": "https://x.com/…/status/…",
    },
    "linkedin_blog": {
        "id": "linkedin_blog",
        "label_ko": "링크드인 / 블로그",
        "short_ko": "링크드인·블로그",
        "hint_ko": "링크드인 게시물 또는 블로그 후기·소개글 URL",
        "placeholder": "https://www.linkedin.com/… 또는 블로그 글 주소",
    },
    "community": {
        "id": "community",
        "label_ko": "디스코드 / 개발 커뮤니티",
        "short_ko": "커뮤니티",
        "hint_ko": "디스코드·오픈카톡·개발 커뮤니티 등 공개 가능한 추천글 링크",
        "placeholder": "https://discord.com/… 또는 커뮤니티 글 URL",
    },
    "instagram": {
        "id": "instagram",
        "label_ko": "인스타그램",
        "short_ko": "인스타",
        "hint_ko": "인스타 게시물·릴스 URL",
        "placeholder": "https://www.instagram.com/p/… 또는 /reel/…",
    },
}


def promo_channel_list() -> list[dict]:
    return [
        {
            **ch,
            "reward_ko": "성사 수수료 8% 쿠폰 1장",
        }
        for ch in PROMO_CHANNELS.values()
    ]


def _parse_iso_dt(value: str | None) -> datetime | None:
    s = (value or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def campaign_is_event_open(row: sqlite3.Row) -> bool:
    """True when viral URL-claim campaign is active, in window, and not sold out."""
    if not row:
        return False
    if not int(row["active"] or 0):
        return False
    if not int(_row_get(row, "allow_url_claim", 0) or 0):
        return False
    max_r = int(row["max_redemptions"] or 0)
    used = int(row["redeem_count"] or 0)
    if max_r > 0 and used >= max_r:
        return False
    now = datetime.now(timezone.utc)
    starts = _parse_iso_dt(_row_get(row, "starts_at", "") or "")
    ends = _parse_iso_dt(_row_get(row, "ends_at", "") or "")
    if starts and now < starts:
        return False
    if ends and now >= ends:
        return False
    return True


def campaign_to_dict(row: sqlite3.Row, *, include_code: bool = True) -> dict:
    fee_rate = float(row["fee_rate"] if "fee_rate" in row.keys() else DEFAULT_COUPON_FEE_RATE)
    max_r = int(row["max_redemptions"] or 0)
    used = int(row["redeem_count"] or 0)
    allow_url = bool(int(_row_get(row, "allow_url_claim", 0) or 0))
    starts_at = (_row_get(row, "starts_at", None) or "") or ""
    ends_at = (_row_get(row, "ends_at", None) or "") or ""
    event_open = campaign_is_event_open(row) if allow_url else False
    d = {
        "id": int(row["id"]),
        "name": row["name"] or "",
        "fee_rate": fee_rate,
        "fee_rate_pct": int(round(fee_rate * 100)),
        "label_ko": f"성사 수수료 {int(round(fee_rate * 100))}% 쿠폰",
        "max_redemptions": max_r,
        "redeem_count": used,
        "remaining": max(0, max_r - used),
        "active": bool(int(row["active"] or 0)),
        "note": (row["note"] if "note" in row.keys() else None) or "",
        "created_at": row["created_at"] or "",
        "no_expiry": True,
        "allow_url_claim": allow_url,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "event_open": event_open,
    }
    if include_code:
        d["code"] = row["code"] or ""
    return d


def user_coupon_to_dict(row: sqlite3.Row, campaign: dict | None = None) -> dict:
    st = (row["status"] or "available") or "available"
    origin = (row["origin"] or "") or ""
    fee_pct = (campaign or {}).get("fee_rate_pct") or 8
    return {
        "id": int(row["id"]),
        "user_id": int(row["user_id"]),
        "campaign_id": int(row["campaign_id"]),
        "origin": origin,
        "status": st,
        "used_project_id": row["used_project_id"],
        "used_at": (row["used_at"] if "used_at" in row.keys() else None) or "",
        "gifted_from_id": row["gifted_from_id"] if "gifted_from_id" in row.keys() else None,
        "created_at": row["created_at"] or "",
        "campaign": campaign,
        "label_ko": (campaign or {}).get("label_ko")
        or f"성사 수수료 {fee_pct}% 쿠폰",
        "available": st == "available",
    }


def generate_coupon_code(conn: sqlite3.Connection | None = None) -> str:
    """
    Secure-looking redeem code: WA-XXXXXXXXXXXX (A–Z, 2–9, no ambiguous 0/O/1/I).
    Retries if collision when conn is provided.
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(12):
        raw = "".join(secrets.choice(alphabet) for _ in range(12))
        code = f"WA-{raw[:4]}-{raw[4:8]}-{raw[8:12]}"
        if conn is None:
            return code
        hit = conn.execute(
            "SELECT id FROM coupon_campaigns WHERE code = ? COLLATE NOCASE",
            (code,),
        ).fetchone()
        if not hit:
            return code
    # extremely unlikely
    return f"WA-{secrets.token_hex(8).upper()}"


def create_coupon_campaign(
    conn: sqlite3.Connection,
    *,
    code: str = "",
    name: str = "",
    fee_rate: float = DEFAULT_COUPON_FEE_RATE,
    max_redemptions: int = 100,
    note: str = "",
    allow_url_claim: bool = False,
    starts_at: str = "",
    ends_at: str = "",
) -> dict:
    ensure_coupon_tables(conn)
    code_n = re.sub(r"\s+", "", (code or "").strip().upper())
    if not code_n:
        code_n = generate_coupon_code(conn)
    if len(code_n) < 4:
        raise ValueError("code too short")
    # Marketing coupons: hard cap 100 redemptions per code
    if max_redemptions < 1 or max_redemptions > 100:
        raise ValueError("max_redemptions must be 1–100")
    fee_rate = float(fee_rate)
    if fee_rate <= 0 or fee_rate >= FEE_RATE:
        # must be better than default 10% for seller
        fee_rate = DEFAULT_COUPON_FEE_RATE
    name = (name or "").strip() or f"성사 수수료 {int(round(fee_rate * 100))}% 쿠폰"
    now = _now()
    url_flag = 1 if allow_url_claim else 0
    starts = (starts_at or "").strip()
    ends = (ends_at or "").strip()
    if starts and _parse_iso_dt(starts) is None:
        raise ValueError("invalid starts_at")
    if ends and _parse_iso_dt(ends) is None:
        raise ValueError("invalid ends_at")
    if starts and ends:
        st = _parse_iso_dt(starts)
        en = _parse_iso_dt(ends)
        if st and en and en <= st:
            raise ValueError("ends_at must be after starts_at")
    try:
        cur = conn.execute(
            """
            INSERT INTO coupon_campaigns (
              code, name, fee_rate, max_redemptions, redeem_count, active, note, created_at,
              allow_url_claim, starts_at, ends_at
            ) VALUES (?, ?, ?, ?, 0, 1, ?, ?, ?, ?, ?)
            """,
            (
                code_n,
                name[:80],
                fee_rate,
                int(max_redemptions),
                (note or "")[:200],
                now,
                url_flag,
                starts or None,
                ends or None,
            ),
        )
    except sqlite3.OperationalError:
        cur = conn.execute(
            """
            INSERT INTO coupon_campaigns (
              code, name, fee_rate, max_redemptions, redeem_count, active, note, created_at
            ) VALUES (?, ?, ?, ?, 0, 1, ?, ?)
            """,
            (code_n, name[:80], fee_rate, int(max_redemptions), (note or "")[:200], now),
        )
    except sqlite3.IntegrityError as e:
        raise ValueError("code already exists") from e
    cid = int(cur.lastrowid)
    # backfill flags/dates if older schema path was used
    cols = _column_names(conn, "coupon_campaigns")
    if "allow_url_claim" in cols:
        conn.execute(
            "UPDATE coupon_campaigns SET allow_url_claim = ? WHERE id = ?",
            (url_flag, cid),
        )
    if "starts_at" in cols:
        conn.execute(
            "UPDATE coupon_campaigns SET starts_at = ?, ends_at = ? WHERE id = ?",
            (starts or None, ends or None, cid),
        )
    row = conn.execute(
        "SELECT * FROM coupon_campaigns WHERE id = ?", (cid,)
    ).fetchone()
    return campaign_to_dict(row)


def list_coupon_campaigns(conn: sqlite3.Connection) -> list[dict]:
    ensure_coupon_tables(conn)
    rows = conn.execute(
        "SELECT * FROM coupon_campaigns ORDER BY id DESC LIMIT 100"
    ).fetchall()
    return [campaign_to_dict(r) for r in rows]


def redeem_coupon_code(conn: sqlite3.Connection, user_id: int, code: str) -> dict:
    """
    User registers a campaign code once per account per campaign.
    Gift-received coupons do not block redeem.
    """
    ensure_coupon_tables(conn)
    code_n = re.sub(r"\s+", "", (code or "").strip().upper())
    if not code_n:
        raise ValueError("code required")
    camp = conn.execute(
        "SELECT * FROM coupon_campaigns WHERE code = ? COLLATE NOCASE",
        (code_n,),
    ).fetchone()
    if not camp or not int(camp["active"] or 0):
        raise ValueError("invalid or inactive code")
    cid = int(camp["id"])
    max_r = int(camp["max_redemptions"] or 0)
    used = int(camp["redeem_count"] or 0)
    if used >= max_r:
        raise ValueError("campaign sold out")
    # 1 redeem per account per campaign (origin=redeem only)
    already = conn.execute(
        """
        SELECT id FROM user_coupons
        WHERE user_id = ? AND campaign_id = ? AND origin = 'redeem'
        LIMIT 1
        """,
        (int(user_id), cid),
    ).fetchone()
    if already:
        raise ValueError("already redeemed on this account")
    now = _now()
    conn.execute(
        "UPDATE coupon_campaigns SET redeem_count = redeem_count + 1 WHERE id = ?",
        (cid,),
    )
    cur = conn.execute(
        """
        INSERT INTO user_coupons (
          user_id, campaign_id, origin, status, created_at, updated_at
        ) VALUES (?, ?, 'redeem', 'available', ?, ?)
        """,
        (int(user_id), cid, now, now),
    )
    row = conn.execute(
        "SELECT * FROM user_coupons WHERE id = ?", (int(cur.lastrowid),)
    ).fetchone()
    return user_coupon_to_dict(row, campaign_to_dict(camp))


def list_user_coupons(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    ensure_coupon_tables(conn)
    rows = conn.execute(
        """
        SELECT uc.*, c.code AS c_code, c.name AS c_name, c.fee_rate AS c_fee_rate
        FROM user_coupons uc
        JOIN coupon_campaigns c ON c.id = uc.campaign_id
        WHERE uc.user_id = ?
        ORDER BY uc.id DESC
        LIMIT 50
        """,
        (int(user_id),),
    ).fetchall()
    out = []
    for r in rows:
        camp = {
            "id": int(r["campaign_id"]),
            "code": r["c_code"] or "",
            "name": r["c_name"] or "",
            "fee_rate": float(r["c_fee_rate"] or DEFAULT_COUPON_FEE_RATE),
            "fee_rate_pct": int(round(float(r["c_fee_rate"] or DEFAULT_COUPON_FEE_RATE) * 100)),
            "label_ko": f"성사 수수료 {int(round(float(r['c_fee_rate'] or DEFAULT_COUPON_FEE_RATE) * 100))}% 쿠폰",
            "no_expiry": True,
        }
        out.append(user_coupon_to_dict(r, camp))
    return out


def resolve_gift_recipient(
    conn: sqlite3.Connection,
    *,
    to_email: str | None = None,
    to_user_id: int | None = None,
    to: str | None = None,
) -> int:
    """Resolve gift recipient by numeric account id or email. Returns users.id."""
    # Prefer explicit user id
    if to_user_id is not None:
        try:
            uid = int(to_user_id)
        except (TypeError, ValueError) as e:
            raise ValueError("invalid recipient") from e
        if uid <= 0:
            raise ValueError("invalid recipient")
        row = conn.execute(
            "SELECT id FROM users WHERE id = ?", (uid,)
        ).fetchone()
        if not row:
            raise ValueError("recipient not found")
        return int(row["id"])

    # Unified field: digits → user id, otherwise email
    raw = (to if to is not None else to_email) or ""
    s = str(raw).strip()
    if not s:
        raise ValueError("recipient required")

    if s.isdigit():
        uid = int(s)
        if uid <= 0:
            raise ValueError("invalid recipient")
        row = conn.execute(
            "SELECT id FROM users WHERE id = ?", (uid,)
        ).fetchone()
        if not row:
            raise ValueError("recipient not found")
        return int(row["id"])

    email = s.lower()
    if "@" not in email or len(email) > 200:
        raise ValueError("invalid recipient")
    row = conn.execute(
        "SELECT id FROM users WHERE email = ? COLLATE NOCASE",
        (email,),
    ).fetchone()
    if not row:
        raise ValueError("recipient not found")
    return int(row["id"])


def gift_user_coupon(
    conn: sqlite3.Connection,
    *,
    coupon_id: int,
    from_user_id: int,
    to_email: str | None = None,
    to_user_id: int | None = None,
    to: str | None = None,
) -> dict:
    """Transfer available coupon ownership to another user. Auto-registers on their account."""
    ensure_coupon_tables(conn)
    to_id = resolve_gift_recipient(
        conn, to_email=to_email, to_user_id=to_user_id, to=to
    )
    if to_id == int(from_user_id):
        raise ValueError("cannot gift to yourself")
    row = conn.execute(
        "SELECT * FROM user_coupons WHERE id = ?", (int(coupon_id),)
    ).fetchone()
    if not row or int(row["user_id"]) != int(from_user_id):
        raise ValueError("coupon not found")
    if (row["status"] or "") != "available":
        raise ValueError("coupon not available")
    now = _now()
    conn.execute(
        """
        UPDATE user_coupons SET
          user_id = ?,
          origin = 'gift',
          gifted_from_id = ?,
          updated_at = ?
        WHERE id = ?
        """,
        (to_id, int(from_user_id), now, int(coupon_id)),
    )
    camp = conn.execute(
        "SELECT * FROM coupon_campaigns WHERE id = ?",
        (int(row["campaign_id"]),),
    ).fetchone()
    fresh = conn.execute(
        "SELECT * FROM user_coupons WHERE id = ?", (int(coupon_id),)
    ).fetchone()
    notify(
        conn,
        to_id,
        "쿠폰 선물 받음",
        f"성사 수수료 {int(round(float(camp['fee_rate'] or 0.08) * 100))}% 쿠폰이 계정에 등록되었습니다.",
        "/app/#coupons",
    )
    return user_coupon_to_dict(fresh, campaign_to_dict(camp) if camp else None)


_IG_URL_RE = re.compile(
    r"^https?://(www\.)?(instagram\.com|instagr\.am)/",
    re.I,
)
_X_URL_RE = re.compile(
    r"^https?://(www\.)?(twitter\.com|x\.com)/",
    re.I,
)
_LINKEDIN_URL_RE = re.compile(
    r"^https?://([a-z0-9-]+\.)?linkedin\.com/",
    re.I,
)
_HTTP_URL_RE = re.compile(r"^https?://", re.I)


def normalize_instagram_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        raise ValueError("url required")
    if not u.startswith("http"):
        u = "https://" + u
    if not _IG_URL_RE.match(u):
        raise ValueError("instagram url required")
    if len(u) > 500:
        raise ValueError("url too long")
    return u


def normalize_promo_url(channel: str, url: str) -> str:
    """Validate post URL for the selected viral channel."""
    ch = (channel or "").strip().lower()
    if ch not in PROMO_CHANNELS:
        raise ValueError("invalid channel")
    u = (url or "").strip()
    if not u:
        raise ValueError("url required")
    if not u.startswith("http"):
        u = "https://" + u
    if len(u) > 500:
        raise ValueError("url too long")
    if not _HTTP_URL_RE.match(u):
        raise ValueError("invalid url")
    if ch == "instagram":
        if not _IG_URL_RE.match(u):
            raise ValueError("instagram url required")
    elif ch == "x":
        if not _X_URL_RE.match(u):
            raise ValueError("x url required")
    elif ch == "linkedin_blog":
        # LinkedIn or any public blog/article URL
        if not (_LINKEDIN_URL_RE.match(u) or _HTTP_URL_RE.match(u)):
            raise ValueError("blog url required")
        # reject obvious non-content platforms for this option
        if _IG_URL_RE.match(u) or _X_URL_RE.match(u):
            raise ValueError("use correct channel")
    elif ch == "community":
        if _IG_URL_RE.match(u) or _X_URL_RE.match(u):
            raise ValueError("use correct channel")
        if not _HTTP_URL_RE.match(u):
            raise ValueError("community url required")
    return u


def get_active_url_claim_campaign(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Latest viral event campaign that is open (active + window + remaining)."""
    ensure_coupon_tables(conn)
    rows = conn.execute(
        """
        SELECT * FROM coupon_campaigns
        WHERE active = 1 AND IFNULL(allow_url_claim, 0) = 1
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()
    for row in rows:
        if campaign_is_event_open(row):
            return row
    return None


def get_url_claim_campaign_for_display(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Open campaign, or latest closed viral campaign (for 'ended' message)."""
    open_c = get_active_url_claim_campaign(conn)
    if open_c:
        return open_c
    ensure_coupon_tables(conn)
    return conn.execute(
        """
        SELECT * FROM coupon_campaigns
        WHERE IFNULL(allow_url_claim, 0) = 1
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()


def promo_submission_to_dict(row: sqlite3.Row) -> dict:
    ch = (_row_get(row, "channel", "instagram") or "instagram") or "instagram"
    meta = PROMO_CHANNELS.get(ch) or PROMO_CHANNELS["instagram"]
    return {
        "id": int(row["id"]),
        "user_id": int(row["user_id"]),
        "campaign_id": int(row["campaign_id"]),
        "channel": ch,
        "channel_label_ko": meta.get("label_ko") or ch,
        "post_url": row["post_url"] or "",
        "status": row["status"] or "pending",
        "admin_note": (row["admin_note"] if "admin_note" in row.keys() else None) or "",
        "reviewed_at": (row["reviewed_at"] if "reviewed_at" in row.keys() else None) or "",
        "claimed_at": (row["claimed_at"] if "claimed_at" in row.keys() else None) or "",
        "user_coupon_id": row["user_coupon_id"] if "user_coupon_id" in row.keys() else None,
        "created_at": row["created_at"] or "",
        "can_claim": (row["status"] or "") == "approved",
    }


def submit_promo_event(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    channel: str,
    post_url: str,
) -> dict:
    """
    Submit one viral post for review.
    One pending/approved/claimed submission per account per event campaign (all channels share the limit).
    """
    ensure_coupon_tables(conn)
    camp = get_active_url_claim_campaign(conn)
    if not camp:
        raise ValueError("no active promo campaign")
    if not campaign_is_event_open(camp):
        raise ValueError("no active promo campaign")
    cid = int(camp["id"])
    ch = (channel or "").strip().lower()
    if ch not in PROMO_CHANNELS:
        raise ValueError("invalid channel")
    url = normalize_promo_url(ch, post_url)
    # 계정당 이벤트 전체 1회 (채널 무관)
    existing = conn.execute(
        """
        SELECT * FROM promo_submissions
        WHERE user_id = ? AND campaign_id = ?
          AND status IN ('pending', 'approved', 'claimed')
        ORDER BY id DESC LIMIT 1
        """,
        (int(user_id), cid),
    ).fetchone()
    if existing:
        st = existing["status"] or ""
        if st == "pending":
            raise ValueError("already pending")
        if st == "approved":
            raise ValueError("already approved")
        if st == "claimed":
            raise ValueError("already claimed")
    now = _now()
    try:
        cur = conn.execute(
            """
            INSERT INTO promo_submissions (
              user_id, campaign_id, channel, post_url, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """,
            (int(user_id), cid, ch, url, now, now),
        )
    except sqlite3.OperationalError:
        cur = conn.execute(
            """
            INSERT INTO promo_submissions (
              user_id, campaign_id, post_url, status, created_at, updated_at
            ) VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (int(user_id), cid, url, now, now),
        )
        if "channel" in _column_names(conn, "promo_submissions"):
            conn.execute(
                "UPDATE promo_submissions SET channel = ? WHERE id = ?",
                (ch, int(cur.lastrowid)),
            )
    row = conn.execute(
        "SELECT * FROM promo_submissions WHERE id = ?", (int(cur.lastrowid),)
    ).fetchone()
    return promo_submission_to_dict(row)


def submit_promo_instagram(
    conn: sqlite3.Connection, user_id: int, post_url: str
) -> dict:
    """Backward-compatible: Instagram channel on unified event."""
    return submit_promo_event(
        conn, user_id, channel="instagram", post_url=post_url
    )


def list_user_promo_submissions(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    ensure_coupon_tables(conn)
    rows = conn.execute(
        """
        SELECT * FROM promo_submissions
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 20
        """,
        (int(user_id),),
    ).fetchall()
    return [promo_submission_to_dict(r) for r in rows]


def list_promo_submissions_admin(
    conn: sqlite3.Connection, status: str = "pending"
) -> list[dict]:
    ensure_coupon_tables(conn)
    st = (status or "pending").strip().lower()
    if st == "all":
        rows = conn.execute(
            """
            SELECT s.*, u.email AS user_email, u.display_name AS user_name,
                   c.name AS campaign_name
            FROM promo_submissions s
            JOIN users u ON u.id = s.user_id
            JOIN coupon_campaigns c ON c.id = s.campaign_id
            ORDER BY s.id DESC LIMIT 100
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT s.*, u.email AS user_email, u.display_name AS user_name,
                   c.name AS campaign_name
            FROM promo_submissions s
            JOIN users u ON u.id = s.user_id
            JOIN coupon_campaigns c ON c.id = s.campaign_id
            WHERE s.status = ?
            ORDER BY s.id DESC LIMIT 100
            """,
            (st,),
        ).fetchall()
    out = []
    for r in rows:
        d = promo_submission_to_dict(r)
        d["user_email"] = r["user_email"] or ""
        d["user_name"] = r["user_name"] or ""
        d["campaign_name"] = r["campaign_name"] or ""
        out.append(d)
    return out


def review_promo_submission(
    conn: sqlite3.Connection,
    submission_id: int,
    *,
    action: str,
    admin_note: str = "",
) -> dict:
    ensure_coupon_tables(conn)
    action = (action or "").strip().lower()
    if action not in ("approve", "reject"):
        raise ValueError("action must be approve or reject")
    row = conn.execute(
        "SELECT * FROM promo_submissions WHERE id = ?", (int(submission_id),)
    ).fetchone()
    if not row:
        raise ValueError("not found")
    if (row["status"] or "") != "pending":
        raise ValueError("not pending")
    now = _now()
    if action == "reject":
        conn.execute(
            """
            UPDATE promo_submissions SET
              status = 'rejected', admin_note = ?, reviewed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            ((admin_note or "")[:300], now, now, int(submission_id)),
        )
        notify(
            conn,
            int(row["user_id"]),
            "이벤트 인증 반려",
            (admin_note or "제출이 반려되었습니다. 가이드를 확인 후 다시 시도해 주세요.")[:200],
            "/promo/event.html",
        )
    else:
        camp = conn.execute(
            "SELECT * FROM coupon_campaigns WHERE id = ?",
            (int(row["campaign_id"]),),
        ).fetchone()
        if not camp or not int(camp["active"] or 0):
            raise ValueError("campaign inactive")
        if int(camp["redeem_count"] or 0) >= int(camp["max_redemptions"] or 0):
            raise ValueError("campaign sold out")
        # Allow approve even if event window ended (user already submitted while open)
        conn.execute(
            """
            UPDATE promo_submissions SET
              status = 'approved', admin_note = ?, reviewed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            ((admin_note or "")[:300], now, now, int(submission_id)),
        )
        notify(
            conn,
            int(row["user_id"]),
            "이벤트 인증 승인",
            "승인되었습니다. 앱 → 쿠폰에서 「쿠폰 받기」를 눌러 등록하세요. (성사 수수료 8% 쿠폰)",
            "/app/#coupons",
        )
    fresh = conn.execute(
        "SELECT * FROM promo_submissions WHERE id = ?", (int(submission_id),)
    ).fetchone()
    return promo_submission_to_dict(fresh)


def claim_promo_coupon(conn: sqlite3.Connection, user_id: int, submission_id: int) -> dict:
    """After admin approve, user claims → user_coupon origin=promo."""
    ensure_coupon_tables(conn)
    row = conn.execute(
        "SELECT * FROM promo_submissions WHERE id = ?", (int(submission_id),)
    ).fetchone()
    if not row or int(row["user_id"]) != int(user_id):
        raise ValueError("not found")
    if (row["status"] or "") != "approved":
        raise ValueError("not approved")
    camp = conn.execute(
        "SELECT * FROM coupon_campaigns WHERE id = ?",
        (int(row["campaign_id"]),),
    ).fetchone()
    if not camp or not int(camp["active"] or 0):
        raise ValueError("campaign inactive")
    if int(camp["redeem_count"] or 0) >= int(camp["max_redemptions"] or 0):
        raise ValueError("campaign sold out")
    now = _now()
    conn.execute(
        "UPDATE coupon_campaigns SET redeem_count = redeem_count + 1 WHERE id = ?",
        (int(camp["id"]),),
    )
    cur = conn.execute(
        """
        INSERT INTO user_coupons (
          user_id, campaign_id, origin, status, created_at, updated_at
        ) VALUES (?, ?, 'promo', 'available', ?, ?)
        """,
        (int(user_id), int(camp["id"]), now, now),
    )
    uc_id = int(cur.lastrowid)
    conn.execute(
        """
        UPDATE promo_submissions SET
          status = 'claimed', claimed_at = ?, user_coupon_id = ?, updated_at = ?
        WHERE id = ?
        """,
        (now, uc_id, now, int(submission_id)),
    )
    uc = conn.execute("SELECT * FROM user_coupons WHERE id = ?", (uc_id,)).fetchone()
    notify(
        conn,
        int(user_id),
        "쿠폰 받기 완료",
        campaign_to_dict(camp).get("label_ko") or "수수료 쿠폰이 등록되었습니다.",
        "/app/#coupons",
    )
    return user_coupon_to_dict(uc, campaign_to_dict(camp))


def take_seller_coupon_for_fee(
    conn: sqlite3.Connection, seller_id: int, project_id: int
) -> tuple[float, int | None, dict]:
    """
    Consume one available coupon for seller fee. Returns (rate, user_coupon_id, fee_dict extras).
    No expiry. FIFO by id.
    """
    ensure_coupon_tables(conn)
    row = conn.execute(
        """
        SELECT uc.*, c.fee_rate AS c_fee_rate, c.name AS c_name
        FROM user_coupons uc
        JOIN coupon_campaigns c ON c.id = uc.campaign_id
        WHERE uc.user_id = ? AND uc.status = 'available'
        ORDER BY uc.id ASC
        LIMIT 1
        """,
        (int(seller_id),),
    ).fetchone()
    if not row:
        return FEE_RATE, None, {}
    rate = float(row["c_fee_rate"] or DEFAULT_COUPON_FEE_RATE)
    if rate <= 0 or rate >= FEE_RATE:
        rate = DEFAULT_COUPON_FEE_RATE
    now = _now()
    conn.execute(
        """
        UPDATE user_coupons SET
          status = 'used',
          used_project_id = ?,
          used_at = ?,
          updated_at = ?
        WHERE id = ? AND status = 'available'
        """,
        (int(project_id), now, now, int(row["id"])),
    )
    return (
        rate,
        int(row["id"]),
        {
            "coupon_id": int(row["id"]),
            "coupon_name": row["c_name"] or "",
            "fee_rate": rate,
        },
    )


# --- Buyer reports (quality / plagiarism / not working) ---

REPORT_REASONS: dict[str, str] = {
    "low_quality": "저퀄리티 코드",
    "plagiarism": "표절·도용 코드",
    "not_working": "작동하지 않음",
    "fraud": "사기·기망 의심",
    "other": "기타",
}

# Unique open reports on one listing → pause auction
REPORT_PAUSE_THRESHOLD = int(os.environ.get("REPORT_PAUSE_THRESHOLD", "3"))
# Unique open reports across a seller's listings → suspend account
REPORT_ACCOUNT_SUSPEND_THRESHOLD = int(os.environ.get("REPORT_ACCOUNT_SUSPEND_THRESHOLD", "5"))


def report_to_dict(row: sqlite3.Row) -> dict:
    reason = row["reason"] or ""
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "reporter_id": row["reporter_id"],
        "reason": reason,
        "reason_label": REPORT_REASONS.get(reason, reason),
        "detail": (row["detail"] if "detail" in row.keys() else None) or "",
        "status": row["status"] or "open",
        "created_at": row["created_at"],
        "resolved_at": (row["resolved_at"] if "resolved_at" in row.keys() else None) or "",
        "resolve_note": (row["resolve_note"] if "resolve_note" in row.keys() else None) or "",
    }


def count_open_reports(conn: sqlite3.Connection, project_id: int) -> int:
    return int(
        conn.execute(
            "SELECT COUNT(*) AS c FROM reports WHERE project_id = ? AND status = 'open'",
            (int(project_id),),
        ).fetchone()["c"]
    )


def count_seller_open_reports(conn: sqlite3.Connection, owner_id: int) -> int:
    return int(
        conn.execute(
            """
            SELECT COUNT(*) AS c FROM reports r
            JOIN projects p ON p.id = r.project_id
            WHERE p.owner_id = ? AND r.status = 'open'
            """,
            (int(owner_id),),
        ).fetchone()["c"]
    )


def pause_project_for_reports(conn: sqlite3.Connection, project_id: int, count: int) -> bool:
    """Pause live auction when report threshold hit. Returns True if newly paused."""
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (int(project_id),)).fetchone()
    if not row:
        return False
    status = (row["auction_status"] if "auction_status" in row.keys() else None) or "live"
    if status in ("sold", "ended", "paused"):
        # still refresh report_count
        conn.execute(
            "UPDATE projects SET report_count = ?, updated_at = ? WHERE id = ?",
            (count, _now(), int(project_id)),
        )
        return False
    if count < REPORT_PAUSE_THRESHOLD:
        conn.execute(
            "UPDATE projects SET report_count = ?, updated_at = ? WHERE id = ?",
            (count, _now(), int(project_id)),
        )
        return False
    note = (
        f"[자동] 구매자 신고 {count}건 누적(기준 {REPORT_PAUSE_THRESHOLD})으로 경매 중단. "
        "저퀄리티·표절·미작동 등 신고 검토 필요."
    )
    conn.execute(
        """
        UPDATE projects
        SET auction_status = 'paused',
            report_count = ?,
            paused_reason = ?,
            review_note = CASE
              WHEN review_note IS NULL OR review_note = '' THEN ?
              ELSE review_note || ' | ' || ?
            END,
            updated_at = ?
        WHERE id = ?
        """,
        (count, note, note, note, _now(), int(project_id)),
    )
    owner_id = int(row["owner_id"])
    title = row["title"] or "매물"
    notify(
        conn,
        owner_id,
        "경매 자동 중단 (신고 누적)",
        f"「{title}」에 신고가 {count}건 쌓여 경매가 자동 중단되었습니다. 운영 검토 후 재개될 수 있습니다.",
        f"/project.html?id={project_id}",
    )
    return True


def suspend_user_for_reports(conn: sqlite3.Connection, owner_id: int, total: int) -> bool:
    """Suspend seller account when report flood threshold hit."""
    if total < REPORT_ACCOUNT_SUSPEND_THRESHOLD:
        return False
    row = conn.execute("SELECT * FROM users WHERE id = ?", (int(owner_id),)).fetchone()
    if not row:
        return False
    if int(row["is_suspended"] or 0) if "is_suspended" in row.keys() else 0:
        return False
    reason = (
        f"[자동] 판매 매물에 대한 오픈 신고 {total}건 누적"
        f"(기준 {REPORT_ACCOUNT_SUSPEND_THRESHOLD}). 계정 일시 정지."
    )
    conn.execute(
        """
        UPDATE users
        SET is_suspended = 1, suspended_at = ?, suspend_reason = ?
        WHERE id = ?
        """,
        (_now(), reason, int(owner_id)),
    )
    # Pause all live listings of this seller
    conn.execute(
        """
        UPDATE projects
        SET auction_status = 'paused',
            paused_reason = COALESCE(paused_reason, '') || ' [계정 정지 연동]',
            updated_at = ?
        WHERE owner_id = ? AND COALESCE(auction_status, 'live') = 'live'
          AND listing_status = 'approved'
        """,
        (_now(), int(owner_id)),
    )
    notify(
        conn,
        int(owner_id),
        "계정 자동 정지 (신고 누적)",
        reason + " 문의: corelabs.studio@gmail.com",
        "/app/",
    )
    return True


def apply_report_thresholds(conn: sqlite3.Connection, project_id: int) -> dict:
    """After a new report: update counts, maybe pause listing / suspend seller."""
    count = count_open_reports(conn, project_id)
    paused = pause_project_for_reports(conn, project_id, count)
    proj = conn.execute(
        "SELECT owner_id FROM projects WHERE id = ?", (int(project_id),)
    ).fetchone()
    owner_id = int(proj["owner_id"]) if proj else 0
    seller_total = count_seller_open_reports(conn, owner_id) if owner_id else 0
    suspended = suspend_user_for_reports(conn, owner_id, seller_total) if owner_id else False
    return {
        "project_open_reports": count,
        "seller_open_reports": seller_total,
        "auction_paused": paused,
        "account_suspended": suspended,
        "pause_threshold": REPORT_PAUSE_THRESHOLD,
        "account_suspend_threshold": REPORT_ACCOUNT_SUSPEND_THRESHOLD,
    }


def notify(conn: sqlite3.Connection, user_id: int, title: str, body: str, link: str = "") -> None:
    if not user_id:
        return
    conn.execute(
        """
        INSERT INTO notifications (user_id, title, body, link, is_read, created_at)
        VALUES (?, ?, ?, ?, 0, ?)
        """,
        (int(user_id), title[:120], body[:1000], (link or "")[:300], _now()),
    )
    # Optional email if SMTP configured
    try:
        from wakeagain.mailer import send_mail, smtp_configured

        if smtp_configured():
            u = conn.execute("SELECT email FROM users WHERE id = ?", (int(user_id),)).fetchone()
            if u and u["email"]:
                send_mail(u["email"], f"[WakeAgain] {title[:80]}", body + (f"\n\n{link}" if link else ""))
    except Exception:
        pass


def notification_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "link": row["link"] or "",
        "is_read": bool(int(row["is_read"] or 0)),
        "created_at": row["created_at"],
    }


def message_to_dict(row: sqlite3.Row) -> dict:
    name = ""
    try:
        name = (row["display_name"] or "").strip()
    except (IndexError, KeyError):
        name = ""
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "sender_id": row["sender_id"],
        "sender_label": name or "회원",
        "body": row["body"],
        "created_at": row["created_at"],
    }


def fee_invoice_to_dict(row: sqlite3.Row) -> dict:
    fee_rate = _row_get(row, "fee_rate")
    try:
        fee_rate_f = float(fee_rate) if fee_rate is not None else FEE_RATE
    except (TypeError, ValueError):
        fee_rate_f = FEE_RATE
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "seller_id": row["seller_id"],
        "deal_amount": row["deal_amount"],
        "fee_amount": row["fee_amount"],
        "fee_rate": fee_rate_f,
        "fee_rate_pct": int(round(fee_rate_f * 100)),
        "user_coupon_id": _row_get(row, "user_coupon_id"),
        "status": row["status"],
        "note": row["note"] or "",
        "created_at": row["created_at"],
        "paid_at": row["paid_at"] or "",
    }


def create_fee_invoice(
    conn: sqlite3.Connection,
    *,
    project_id: int,
    seller_id: int,
    deal_amount: int,
    note: str = "",
) -> dict:
    now = _now()
    # one open invoice per project — do not consume coupon if already exists
    existing = conn.execute(
        "SELECT * FROM fee_invoices WHERE project_id = ? AND status = 'pending'",
        (project_id,),
    ).fetchone()
    if existing:
        return fee_invoice_to_dict(existing)

    # Apply one available seller coupon → e.g. 8% fee (「수수료 8% 쿠폰」)
    rate, coupon_id, cmeta = take_seller_coupon_for_fee(
        conn, int(seller_id), int(project_id)
    )
    fee = fee_breakdown(deal_amount, rate=rate if coupon_id else None)
    note_final = (note or "")[:500]
    if coupon_id:
        note_final = (
            (note_final + " · " if note_final else "")
            + f"쿠폰 적용 수수료 {fee['rate_pct']}% (user_coupon #{coupon_id})"
        )[:500]
    try:
        cur = conn.execute(
            """
            INSERT INTO fee_invoices (
              project_id, seller_id, deal_amount, fee_amount, status, note, created_at,
              fee_rate, user_coupon_id
            ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)
            """,
            (
                project_id,
                seller_id,
                deal_amount,
                fee["fee"],
                note_final,
                now,
                fee["rate"],
                coupon_id,
            ),
        )
    except sqlite3.OperationalError:
        cur = conn.execute(
            """
            INSERT INTO fee_invoices (
              project_id, seller_id, deal_amount, fee_amount, status, note, created_at
            ) VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """,
            (project_id, seller_id, deal_amount, fee["fee"], note_final, now),
        )
    row = conn.execute("SELECT * FROM fee_invoices WHERE id = ?", (int(cur.lastrowid),)).fetchone()
    out = fee_invoice_to_dict(row)
    if cmeta:
        out["coupon"] = cmeta
    return out


def deal_payment_hours() -> int:
    try:
        return max(1, min(int(os.environ.get("DEAL_PAYMENT_HOURS") or "1"), 48))
    except ValueError:
        return 1


def deal_inspection_hours() -> int:
    """Auto-accept window after transfer (default 48h, clamp 24–72)."""
    try:
        return max(24, min(int(os.environ.get("DEAL_INSPECTION_HOURS") or "48"), 72))
    except ValueError:
        return 48


def deal_policy_public() -> dict:
    pay_h = deal_payment_hours()
    insp_h = deal_inspection_hours()
    return {
        "payment_hours": pay_h,
        "inspection_hours": insp_h,
        "stages": [
            "awaiting_payment",
            "paid",
            "inspection",
            "completed",
        ],
        "message_ko": (
            f"낙찰 후 PG로 {pay_h}시간 이내 결제 → 입금 확인 후 판매자 이전 → 구매자 검수 후 「인수하기」. "
            f"이전(수령) 후 {insp_h}시간 안에 이의가 없으면 자동 구매 확정·정산. "
            "입금 확인 전 코드·계정 이전 금지. 대금은 인수(또는 자동 확정) 후 판매자에게 정산됩니다."
        ),
        "message_en": (
            f"Pay via PG within {pay_h}h of award → seller transfers after payment confirmed → "
            f"buyer inspects and accepts. No dispute within {insp_h}h → auto-confirm & settle. "
            "No asset handoff before payment. Seller is paid after accept (or auto-accept)."
        ),
        "buyer_accept_label_ko": "인수하기",
        "no_transfer_before_payment_ko": "입금 확인 전 코드·도메인·계정 이전 금지",
    }


def finalize_sale(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    sold_price: int,
    buyer_id: int | None,
    note: str,
) -> sqlite3.Row:
    """Mark project sold, open fee invoice (held), start payment deadline."""
    now = _now()
    now_dt = datetime.now(timezone.utc)
    pay_deadline = (now_dt + timedelta(hours=deal_payment_hours())).isoformat(timespec="seconds")
    pid = int(row["id"])
    owner_id = int(row["owner_id"])
    pay_h = deal_payment_hours()
    insp_h = deal_inspection_hours()
    conn.execute(
        """
        UPDATE projects SET
          auction_status = 'sold', sold_price = ?, sold_at = ?, buyer_id = ?,
          price_current = ?, deal_note = ?, updated_at = ?,
          deal_status = 'awaiting_payment',
          payment_deadline_at = ?,
          paid_at = NULL,
          transfer_started_at = NULL,
          inspection_deadline_at = NULL,
          buyer_accepted_at = NULL,
          settled_at = NULL,
          deal_dispute_note = NULL
        WHERE id = ?
        """,
        (
            sold_price,
            now,
            buyer_id,
            sold_price,
            (note or "성사")[:500],
            now,
            pay_deadline,
            pid,
        ),
    )
    inv = create_fee_invoice(
        conn,
        project_id=pid,
        seller_id=owner_id,
        deal_amount=sold_price,
        note=note or "성사 수수료(정산 보류)",
    )
    fee = inv["fee_amount"]
    # Seed buyer handover checklist from listing assets (parties transfer off-site)
    if not load_handover_checklist(row):
        seeded = seed_handover_checklist(row)
        conn.execute(
            "UPDATE projects SET handover_checklist_json = ? WHERE id = ?",
            (json.dumps(seeded, ensure_ascii=False), pid),
        )
    notify(
        conn,
        owner_id,
        "성사 · 입금 대기",
        f"「{row['title']}」 성사 ₩{sold_price:,}. 구매자 {pay_h}시간 내 입금 후, "
        f"이전→검수(최대 {insp_h}시간)·인수 확정 시 정산됩니다. "
        f"수수료 ₩{fee:,}"
        + (
            f" ({int(round(float(inv.get('fee_rate') or FEE_RATE) * 100))}%)"
            if isinstance(inv, dict)
            else " (10%)"
        )
        + ".",
        f"/project.html?id={pid}",
    )
    if buyer_id:
        notify(
            conn,
            int(buyer_id),
            "낙찰 · 결제 안내",
            f"「{row['title']}」 ₩{sold_price:,} 낙찰. {pay_h}시간 이내 PG 결제해 주세요. "
            f"결제·인수 전 실명·휴대폰(Lv2)이 필요합니다. "
            f"결제 확인 후 이전·검수, 「인수하기」 또는 {insp_h}시간 무이의 시 자동 확정·정산.",
            f"/project.html?id={pid}",
        )
    # Credit for sale/purchase applied at settle_complete (not at award)
    return conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()


def mark_deal_paid(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    note: str = "",
) -> sqlite3.Row:
    """Mark payment confirmed (call only from PG webhook / payment success handler).

    No admin/manual product path — pre-PG fallbacks are not supported.
    Buyer must be Lv2 (real name + phone) before payment is accepted.
    """
    status = (_row_get(row, "deal_status") or "") or ""
    if status not in ("awaiting_payment", ""):
        if status == "paid":
            return row
        raise ValueError("not awaiting payment")
    buyer_id = _row_get(row, "buyer_id")
    if buyer_id:
        bu = conn.execute("SELECT * FROM users WHERE id = ?", (int(buyer_id),)).fetchone()
        if bu:
            tr = compute_trust(bu)
            if not tr.get("can_fulfill_purchase"):
                raise ValueError(
                    "buyer must complete Lv2 (real name + phone) before payment confirmation"
                )
    now = _now()
    pid = int(row["id"])
    conn.execute(
        """
        UPDATE projects SET
          deal_status = 'paid',
          paid_at = ?,
          deal_note = COALESCE(?, deal_note),
          updated_at = ?
        WHERE id = ?
        """,
        (now, (note or "입금 확인")[:500], now, pid),
    )
    owner_id = int(row["owner_id"])
    buyer_id = _row_get(row, "buyer_id")
    notify(
        conn,
        owner_id,
        "입금 확인 · 이전 가능",
        f"「{row['title']}」 입금이 확인되었습니다. 프로젝트를 이전한 뒤 「이전 완료」를 눌러 주세요.",
        f"/project.html?id={pid}",
    )
    if buyer_id:
        notify(
            conn,
            int(buyer_id),
            "입금 확인됨",
            f"「{row['title']}」 입금이 확인되었습니다. 판매자 이전 후 검수하고 「인수하기」를 눌러 주세요.",
            f"/project.html?id={pid}",
        )
    return conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()


def mark_deal_transferred(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    note: str = "",
) -> sqlite3.Row:
    """Seller finished handoff → inspection window starts."""
    status = (_row_get(row, "deal_status") or "") or ""
    if status not in ("paid", "inspection"):
        raise ValueError("payment must be confirmed before transfer")
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat(timespec="seconds")
    insp_deadline = (now_dt + timedelta(hours=deal_inspection_hours())).isoformat(
        timespec="seconds"
    )
    pid = int(row["id"])
    insp_h = deal_inspection_hours()
    conn.execute(
        """
        UPDATE projects SET
          deal_status = 'inspection',
          transfer_started_at = COALESCE(transfer_started_at, ?),
          inspection_deadline_at = ?,
          deal_note = COALESCE(?, deal_note),
          updated_at = ?
        WHERE id = ?
        """,
        (now, insp_deadline, (note or "이전 완료 · 검수 중")[:500], now, pid),
    )
    buyer_id = _row_get(row, "buyer_id")
    if buyer_id:
        notify(
            conn,
            int(buyer_id),
            "이전 완료 · 검수",
            f"「{row['title']}」 이전이 완료되었습니다. 검수 후 「인수하기」를 눌러 주세요. "
            f"{insp_h}시간 내 이의가 없으면 자동 확정·정산됩니다.",
            f"/project.html?id={pid}",
        )
    notify(
        conn,
        int(row["owner_id"]),
        "검수 대기",
        f"「{row['title']}」 구매자 검수 중입니다. 인수 또는 {insp_h}시간 후 자동 확정 시 정산됩니다.",
        f"/project.html?id={pid}",
    )
    # Activate included Q-credits once (inspection handoff)
    try:
        activate_q_credits_for_deal(conn, pid)
    except Exception:
        pass
    return conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()


# --- 헬프티켓 (Kmong-style included + seller-priced add-ons) ---

Q_CREDITS_INCLUDED_MIN = 1
Q_CREDITS_INCLUDED_MAX = 3  # 무료(포함) 헬프티켓 1~3장
Q_CREDIT_PRICE_MIN = 5_000
Q_CREDIT_PRICE_MAX = 100_000
Q_CREDIT_WINDOW_DAYS = 14
Q_CREDIT_PLATFORM_FEE_RATE = 0.15  # on add-on purchases; seller gets rest after answer


def q_credit_policy_public() -> dict:
    return {
        "included_min": Q_CREDITS_INCLUDED_MIN,
        "included_max": Q_CREDITS_INCLUDED_MAX,
        "unit_price_min": Q_CREDIT_PRICE_MIN,
        "unit_price_max": Q_CREDIT_PRICE_MAX,
        "window_days": Q_CREDIT_WINDOW_DAYS,
        "platform_fee_rate": Q_CREDIT_PLATFORM_FEE_RATE,
        "model": "included_plus_seller_priced_addon",
        "message_ko": (
            "헬프티켓은 성사·이전 후, 판매자(제작자)가 제공하는 안내·설명 창구입니다. "
            "플랫폼·제작자의 개발 완료나 추가 개발·무제한 수정을 보장하는 상품이 아닙니다. "
            "질문 범위·답변 내용·횟수 소진 등 이용과 관련한 의견 차이는 "
            "구매자와 판매자가 서로 맞춰 주시면 됩니다. "
            "사이트는 헬프티켓의 사용 여부·내용에 대해 중재하거나 평가하지 않습니다. "
            "(사기·약관 위반·결제 장애 등은 기존 신고·안내 절차를 이용해 주세요.) "
            "포함 횟수는 매물에 기본 제공되고, 추가 1회 가격은 판매자가 정하며, "
            "추가 구매분은 답변 완료 후 판매자에게 정산(플랫폼 수수료 제외)됩니다."
        ),
        "message_en": (
            "Help tickets are seller guidance after transfer—not a guarantee of "
            "development completion or unlimited changes by the platform or seller. "
            "Scope, answers, and usage are between buyer and seller; "
            "the site does not mediate or judge help-ticket content. "
            "(Fraud, terms violations, and payment issues follow the usual report process.) "
            "Included tickets come with the listing; add-on price is set by the seller; "
            "add-ons settle to the seller after an answer (platform fee excluded)."
        ),
        "dispute_note_ko": (
            "헬프티켓 이용에 관한 의견 차이는 당사자 간 협의가 원칙이며, "
            "사이트 운영은 이에 개입하지 않습니다."
        ),
        "deduct_on": "seller_answer",
        "concurrent_open_max": 1,
    }


def normalize_q_credits_offered(n: int | None) -> int:
    """Free included help tickets: 1–3 only."""
    try:
        v = int(n if n is not None else 1)
    except (TypeError, ValueError):
        v = 1
    return max(Q_CREDITS_INCLUDED_MIN, min(v, Q_CREDITS_INCLUDED_MAX))


def normalize_q_credit_unit_price(p: int | None) -> int:
    """0 = add-on not for sale; otherwise clamp to min/max."""
    try:
        v = int(p if p is not None else 0)
    except (TypeError, ValueError):
        v = 0
    if v <= 0:
        return 0
    return max(Q_CREDIT_PRICE_MIN, min(v, Q_CREDIT_PRICE_MAX))


def normalize_q_credit_sla_hours(h: int | None) -> int:
    try:
        v = int(h if h is not None else 48)
    except (TypeError, ValueError):
        v = 48
    if v not in (24, 48, 72):
        v = 48
    return v


def activate_q_credits_for_deal(conn: sqlite3.Connection, project_id: int) -> sqlite3.Row:
    """Snapshot included credits when inspection starts. Idempotent if already activated."""
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise ValueError("project not found")
    # Already activated (window set)
    if _row_get(row, "q_window_ends_at") or "":
        return row
    offered = normalize_q_credits_offered(_row_get(row, "q_credits_offered"))
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat(timespec="seconds")
    window = (now_dt + timedelta(days=Q_CREDIT_WINDOW_DAYS)).isoformat(timespec="seconds")
    conn.execute(
        """
        UPDATE projects SET
          q_credits_total = ?,
          q_credits_remaining = ?,
          q_credits_held = 0,
          q_window_ends_at = ?,
          updated_at = ?
        WHERE id = ?
        """,
        (offered, offered, window, now, project_id),
    )
    buyer_id = _row_get(row, "buyer_id")
    if buyer_id:
        if offered > 0:
            notify(
                conn,
                int(buyer_id),
                "헬프티켓 지급",
                f"「{row['title']}」 헬프티켓 {offered}회가 지급되었습니다. "
                f"{Q_CREDIT_WINDOW_DAYS}일 안에 사용해 주세요. "
                f"(판매자 안내용 · 개발 보증 아님 · 이용 의견 차이는 당사자 협의)",
                f"/project.html?id={project_id}",
            )
        else:
            unit = int(_row_get(row, "q_credit_unit_price") or 0)
            if unit > 0:
                notify(
                    conn,
                    int(buyer_id),
                    "추가 헬프티켓 구매 가능",
                    f"「{row['title']}」 포함 헬프티켓은 0회입니다. "
                    f"필요하면 추가 헬프티켓(1회 ₩{unit:,})을 구매할 수 있습니다.",
                    f"/project.html?id={project_id}",
                )
    return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def q_credits_available(row: sqlite3.Row | dict) -> int:
    rem = int(_row_get(row, "q_credits_remaining") if not isinstance(row, dict) else row.get("q_credits_remaining") or 0)
    held = int(_row_get(row, "q_credits_held") if not isinstance(row, dict) else row.get("q_credits_held") or 0)
    return max(0, rem - held)


def q_window_open(row: sqlite3.Row) -> bool:
    ends = (_row_get(row, "q_window_ends_at") or "") or ""
    if not ends:
        return False
    exp = _parse_iso(ends) if "_parse_iso" in dir() else None
    try:
        from datetime import datetime, timezone

        if exp is None:
            exp = datetime.fromisoformat(str(ends).replace("Z", "+00:00"))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) <= exp.astimezone(timezone.utc)
    except Exception:
        return True


def open_q_thread(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    buyer_id: int,
    body: str,
) -> dict:
    """Buyer spends one credit (held until seller answers)."""
    body = (body or "").strip()
    if len(body) < 10:
        raise ValueError("질문은 10자 이상 적어 주세요.")
    if len(body) > 2000:
        raise ValueError("질문은 2000자 이내로 적어 주세요.")
    pid = int(row["id"])
    seller_id = int(row["owner_id"])
    if int(buyer_id) != int(_row_get(row, "buyer_id") or 0):
        raise ValueError("낙찰 구매자만 헬프티켓을 사용할 수 있습니다.")
    st = (_row_get(row, "deal_status") or "") or ""
    if st not in ("inspection", "completed"):
        raise ValueError("이전·검수 또는 인수 확정 후에 헬프티켓을 사용할 수 있습니다.")
    if st == "disputed":
        raise ValueError("분쟁 중에는 새 질문을 등록할 수 없습니다.")
    if not q_window_open(row):
        raise ValueError("헬프티켓 사용 기간이 끝났습니다.")
    avail = q_credits_available(row)
    if avail < 1:
        raise ValueError("남은 헬프티켓이 없습니다. 추가 헬프티켓을 구매해 주세요.")
    open_n = conn.execute(
        """
        SELECT COUNT(*) AS c FROM q_threads
        WHERE project_id = ? AND status = 'open' AND credit_state = 'held'
        """,
        (pid,),
    ).fetchone()["c"]
    if int(open_n or 0) >= 1:
        raise ValueError("답변 대기 중인 질문이 있습니다. 답변 후 다시 질문해 주세요.")

    sla_h = normalize_q_credit_sla_hours(_row_get(row, "q_credit_sla_hours"))
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat(timespec="seconds")
    sla = (now_dt + timedelta(hours=sla_h)).isoformat(timespec="seconds")
    # Included first: if remaining after this hold is still > purchased pool, it's included
    purchased = int(_row_get(row, "q_credits_purchased") or 0)
    remaining = int(_row_get(row, "q_credits_remaining") or 0)
    held = int(_row_get(row, "q_credits_held") or 0)
    effective_left = remaining - held
    source = "purchased" if purchased > 0 and effective_left <= purchased else "included"

    conn.execute(
        """
        UPDATE projects SET
          q_credits_held = COALESCE(q_credits_held, 0) + 1,
          updated_at = ?
        WHERE id = ?
        """,
        (now, pid),
    )
    cur = conn.execute(
        """
        INSERT INTO q_threads (
          project_id, buyer_id, seller_id, body, status, credit_state, source,
          sla_deadline_at, created_at
        ) VALUES (?, ?, ?, ?, 'open', 'held', ?, ?, ?)
        """,
        (pid, buyer_id, seller_id, body[:2000], source, sla, now),
    )
    tid = int(cur.lastrowid)
    notify(
        conn,
        seller_id,
        "헬프티켓 도착",
        f"「{row['title']}」 구매자 헬프 요청 1건. {sla_h}시간 내 답변해 주세요.",
        f"/project.html?id={pid}",
    )
    trow = conn.execute("SELECT * FROM q_threads WHERE id = ?", (tid,)).fetchone()
    return q_thread_to_dict(trow)


def answer_q_thread(
    conn: sqlite3.Connection,
    thread_id: int,
    *,
    seller_id: int,
    answer: str,
) -> dict:
    answer = (answer or "").strip()
    if len(answer) < 5:
        raise ValueError("답변은 5자 이상 적어 주세요.")
    trow = conn.execute("SELECT * FROM q_threads WHERE id = ?", (thread_id,)).fetchone()
    if not trow:
        raise ValueError("질문을 찾을 수 없습니다.")
    if int(trow["seller_id"]) != int(seller_id):
        raise ValueError("판매자만 답변할 수 있습니다.")
    if (trow["status"] or "") != "open" or (trow["credit_state"] or "") != "held":
        raise ValueError("이미 처리된 질문입니다.")
    pid = int(trow["project_id"])
    now = _now()
    conn.execute(
        """
        UPDATE q_threads SET
          answer_body = ?, status = 'answered', credit_state = 'consumed',
          answered_at = ?
        WHERE id = ?
        """,
        (answer[:4000], now, thread_id),
    )
    prow = conn.execute(
        "SELECT q_credits_held, q_credits_remaining FROM projects WHERE id = ?",
        (pid,),
    ).fetchone()
    held_n = max(0, int(prow["q_credits_held"] or 0) - 1)
    rem_n = max(0, int(prow["q_credits_remaining"] or 0) - 1)
    conn.execute(
        """
        UPDATE projects SET
          q_credits_held = ?,
          q_credits_remaining = ?,
          updated_at = ?
        WHERE id = ?
        """,
        (held_n, rem_n, now, pid),
    )
    # Settle add-on purchase if this thread used a purchased credit (FIFO escrowed)
    if (trow["source"] or "") == "purchased":
        pur = conn.execute(
            """
            SELECT * FROM q_credit_purchases
            WHERE project_id = ? AND buyer_id = ? AND status IN ('paid', 'escrowed')
              AND (thread_id IS NULL OR thread_id = 0)
            ORDER BY id ASC LIMIT 1
            """,
            (pid, int(trow["buyer_id"])),
        ).fetchone()
        if pur:
            conn.execute(
                """
                UPDATE q_credit_purchases SET
                  status = 'settled', thread_id = ?, settled_at = ?, note = '답변 완료 정산'
                WHERE id = ?
                """,
                (thread_id, now, int(pur["id"])),
            )
    notify(
        conn,
        int(trow["buyer_id"]),
        "헬프티켓 답변",
        f"판매자가 헬프티켓에 답변했습니다. 1회가 사용되었습니다.",
        f"/project.html?id={pid}",
    )
    trow = conn.execute("SELECT * FROM q_threads WHERE id = ?", (thread_id,)).fetchone()
    return q_thread_to_dict(trow)


def cancel_q_thread(
    conn: sqlite3.Connection,
    thread_id: int,
    *,
    buyer_id: int,
) -> dict:
    trow = conn.execute("SELECT * FROM q_threads WHERE id = ?", (thread_id,)).fetchone()
    if not trow:
        raise ValueError("질문을 찾을 수 없습니다.")
    if int(trow["buyer_id"]) != int(buyer_id):
        raise ValueError("본인 질문만 취소할 수 있습니다.")
    if (trow["status"] or "") != "open" or (trow["credit_state"] or "") != "held":
        raise ValueError("이미 처리된 질문입니다.")
    pid = int(trow["project_id"])
    now = _now()
    conn.execute(
        """
        UPDATE q_threads SET status = 'cancelled', credit_state = 'released'
        WHERE id = ?
        """,
        (thread_id,),
    )
    prow = conn.execute(
        "SELECT q_credits_held FROM projects WHERE id = ?", (pid,)
    ).fetchone()
    held_n = max(0, int(prow["q_credits_held"] or 0) - 1) if prow else 0
    conn.execute(
        """
        UPDATE projects SET
          q_credits_held = ?,
          updated_at = ?
        WHERE id = ?
        """,
        (held_n, now, pid),
    )
    trow = conn.execute("SELECT * FROM q_threads WHERE id = ?", (thread_id,)).fetchone()
    return q_thread_to_dict(trow)


def list_q_threads(conn: sqlite3.Connection, project_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM q_threads WHERE project_id = ?
        ORDER BY id DESC LIMIT 50
        """,
        (project_id,),
    ).fetchall()
    return [q_thread_to_dict(r) for r in rows]


def q_thread_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": int(row["id"]),
        "project_id": int(row["project_id"]),
        "buyer_id": int(row["buyer_id"]),
        "seller_id": int(row["seller_id"]),
        "body": row["body"] or "",
        "answer_body": row["answer_body"] or "",
        "status": row["status"] or "",
        "credit_state": row["credit_state"] or "",
        "source": row["source"] or "included",
        "sla_deadline_at": row["sla_deadline_at"] or "",
        "created_at": row["created_at"] or "",
        "answered_at": row["answered_at"] or "",
    }


def purchase_q_credit_units(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    buyer_id: int,
    units: int = 1,
    mock_paid: bool = False,
) -> dict:
    """
    Buyer buys add-on Q credits at seller-set unit price.
    Real PG: status pending_payment until webhook.
    mock_paid=True (dev/env): mark paid/escrowed and increment remaining.
    """
    units = max(1, min(int(units or 1), 5))
    if int(buyer_id) != int(_row_get(row, "buyer_id") or 0):
        raise ValueError("낙찰 구매자만 추가 헬프티켓을 살 수 있습니다.")
    st = (_row_get(row, "deal_status") or "") or ""
    if st not in ("inspection", "completed"):
        raise ValueError("이전·검수 이후에만 추가 헬프티켓을 구매할 수 있습니다.")
    if not q_window_open(row) and int(_row_get(row, "q_credits_total") or 0) == 0:
        # allow purchase only if window set; if no window, try activate
        pass
    if _row_get(row, "q_window_ends_at") and not q_window_open(row):
        raise ValueError("헬프티켓 사용 기간이 끝나 추가 구매할 수 없습니다.")
    price = normalize_q_credit_unit_price(_row_get(row, "q_credit_unit_price"))
    if price <= 0:
        raise ValueError("이 매물은 추가 헬프티켓 판매를 하지 않습니다.")
    gross = price * units
    fee = int(round(gross * Q_CREDIT_PLATFORM_FEE_RATE))
    seller_amt = gross - fee
    pid = int(row["id"])
    seller_id = int(row["owner_id"])
    now = _now()
    status = "paid" if mock_paid else "pending_payment"
    cur = conn.execute(
        """
        INSERT INTO q_credit_purchases (
          project_id, buyer_id, seller_id, units, unit_price, gross_amount,
          fee_amount, seller_amount, status, created_at, paid_at, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pid,
            buyer_id,
            seller_id,
            units,
            price,
            gross,
            fee,
            seller_amt,
            status,
            now,
            now if mock_paid else None,
            "mock paid" if mock_paid else "awaiting PG",
        ),
    )
    purchase_id = int(cur.lastrowid)
    if mock_paid:
        conn.execute(
            """
            UPDATE q_credit_purchases SET status = 'escrowed' WHERE id = ?
            """,
            (purchase_id,),
        )
        conn.execute(
            """
            UPDATE projects SET
              q_credits_total = COALESCE(q_credits_total, 0) + ?,
              q_credits_remaining = COALESCE(q_credits_remaining, 0) + ?,
              q_credits_purchased = COALESCE(q_credits_purchased, 0) + ?,
              updated_at = ?
            WHERE id = ?
            """,
            (units, units, units, now, pid),
        )
        notify(
            conn,
            seller_id,
            "추가 헬프티켓 구매",
            f"「{row['title']}」 구매자가 헬프티켓 {units}회를 구매했습니다. "
            f"답변 완료 시 약 ₩{seller_amt:,} 정산 예정입니다.",
            f"/project.html?id={pid}",
        )
    pur = conn.execute(
        "SELECT * FROM q_credit_purchases WHERE id = ?", (purchase_id,)
    ).fetchone()
    return {
        "id": purchase_id,
        "project_id": pid,
        "units": units,
        "unit_price": price,
        "gross_amount": gross,
        "fee_amount": fee,
        "seller_amount": seller_amt,
        "status": pur["status"],
        "paid": mock_paid,
        "message_ko": (
            f"추가 헬프티켓 {units}회가 지급되었습니다. 답변 완료 후 판매자 정산 ₩{seller_amt:,}."
            if mock_paid
            else "PG 결제 연동 후 실제 결제가 가능합니다. (지금은 대기 상태)"
        ),
    }


def settle_complete(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    reason: str = "buyer_accept",
    note: str = "",
) -> sqlite3.Row:
    """Release settlement to seller after accept or auto-confirm."""
    status = (_row_get(row, "deal_status") or "") or ""
    if status == "completed":
        return row
    if status != "inspection":
        raise ValueError("not in inspection — seller must mark transfer first")
    now = _now()
    pid = int(row["id"])
    owner_id = int(row["owner_id"])
    buyer_id = _row_get(row, "buyer_id")
    sold_price = int(_row_get(row, "sold_price") or 0)
    fee = fee_breakdown(sold_price)
    conn.execute(
        """
        UPDATE projects SET
          deal_status = 'completed',
          buyer_accepted_at = COALESCE(buyer_accepted_at, ?),
          settled_at = ?,
          deal_note = ?,
          updated_at = ?
        WHERE id = ?
        """,
        (
            now,
            now,
            (note or f"정산 완료 ({reason})")[:500],
            now,
            pid,
        ),
    )
    # Credit once on successful settlement
    credit_bump(conn, owner_id, sold=1)
    if buyer_id:
        on_time = 1
        pay_deadline = _parse_iso(str(_row_get(row, "payment_deadline_at") or ""))
        paid_at = _parse_iso(str(_row_get(row, "paid_at") or ""))
        if pay_deadline and paid_at and paid_at > pay_deadline:
            on_time = 0
        credit_bump(conn, int(buyer_id), bought=1, on_time=on_time)
    notify(
        conn,
        owner_id,
        "정산 완료",
        f"「{row['title']}」 구매 확정. 판매 대금 정산 진행(합의가 ₩{sold_price:,} · 수수료 ₩{fee['fee']:,}).",
        f"/project.html?id={pid}",
    )
    if buyer_id:
        notify(
            conn,
            int(buyer_id),
            "인수·구매 확정",
            f"「{row['title']}」 구매가 확정되었습니다. 이용해 주셔서 감사합니다.",
            f"/project.html?id={pid}",
        )
    return conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()


def mark_deal_disputed(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    note: str,
    by_user_id: int,
) -> sqlite3.Row:
    status = (_row_get(row, "deal_status") or "") or ""
    if status not in ("paid", "inspection", "awaiting_payment"):
        raise ValueError("cannot dispute in this status")
    now = _now()
    pid = int(row["id"])
    conn.execute(
        """
        UPDATE projects SET
          deal_status = 'disputed',
          deal_dispute_note = ?,
          deal_note = ?,
          updated_at = ?
        WHERE id = ?
        """,
        ((note or "")[:800], f"이의 제기 (user {by_user_id})"[:500], now, pid),
    )
    notify(
        conn,
        int(row["owner_id"]),
        "거래 이의 제기",
        f"「{row['title']}」 거래에 이의가 접수되었습니다. 운영이 검토합니다.",
        f"/project.html?id={pid}",
    )
    buyer_id = _row_get(row, "buyer_id")
    if buyer_id and int(buyer_id) != int(by_user_id):
        notify(
            conn,
            int(buyer_id),
            "거래 이의 제기",
            f"「{row['title']}」 거래 이의가 접수되었습니다.",
            f"/project.html?id={pid}",
        )
    return conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()


def second_bidder_auto_enabled() -> bool:
    """When primary winner misses payment, re-award to next highest unique bidder."""
    raw = (os.environ.get("SECOND_BIDDER_AUTO") or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def next_bid_after_default(
    conn: sqlite3.Connection, project_id: int, excluded_buyer_id: int | None
) -> sqlite3.Row | None:
    """Highest bid from a different bidder than the defaulted winner."""
    if excluded_buyer_id is None:
        return conn.execute(
            """
            SELECT * FROM bids WHERE project_id = ?
            ORDER BY amount DESC, id DESC LIMIT 1
            """,
            (int(project_id),),
        ).fetchone()
    return conn.execute(
        """
        SELECT * FROM bids
        WHERE project_id = ? AND bidder_id != ?
        ORDER BY amount DESC, id DESC
        LIMIT 1
        """,
        (int(project_id), int(excluded_buyer_id)),
    ).fetchone()


def reaward_to_next_bidder(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    excluded_buyer_id: int | None,
) -> sqlite3.Row | None:
    """
    After payment default: offer sale to next-highest unique bidder.
    Returns re-awarded project row, or None if no eligible second bid.
    """
    pid = int(row["id"])
    nxt = next_bid_after_default(conn, pid, excluded_buyer_id)
    if not nxt:
        return None
    amount = int(nxt["amount"])
    bidder_id = int(nxt["bidder_id"])
    if amount <= 0:
        return None
    awarded = finalize_sale(
        conn,
        row,
        sold_price=amount,
        buyer_id=bidder_id,
        note="1순위 미입금 · 차순위 자동 낙찰",
    )
    # Tag note for clarity
    conn.execute(
        """
        UPDATE projects SET deal_note = ?
        WHERE id = ?
        """,
        (
            f"1순위 미입금 → 차순위 자동 낙찰 ₩{amount:,} (bidder#{bidder_id})",
            pid,
        ),
    )
    notify(
        conn,
        int(row["owner_id"]),
        "차순위 자동 낙찰",
        f"「{row['title']}」 1순위 미입금으로 차순위 ₩{amount:,} 에 자동 낙찰되었습니다. 새 구매자 입금 대기.",
        f"/project.html?id={pid}",
    )
    return conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone() or awarded


def void_for_nonpayment(conn: sqlite3.Connection, row: sqlite3.Row) -> sqlite3.Row:
    """Buyer missed payment deadline → void award, credit penalty; optional 2nd bidder re-award."""
    now = _now()
    pid = int(row["id"])
    buyer_id = _row_get(row, "buyer_id")
    owner_id = int(row["owner_id"])
    title = row["title"]
    conn.execute(
        """
        UPDATE projects SET
          deal_status = 'payment_default',
          auction_status = 'ended',
          deal_note = ?,
          updated_at = ?
        WHERE id = ?
        """,
        ("입금 기한 초과 · 낙찰 무효", now, pid),
    )
    # cancel open fee invoice
    conn.execute(
        """
        UPDATE fee_invoices SET status = 'cancelled', note = '입금 기한 초과'
        WHERE project_id = ? AND status = 'pending'
        """,
        (pid,),
    )
    if buyer_id:
        credit_bump(conn, int(buyer_id), defaults=1)
        notify(
            conn,
            int(buyer_id),
            "입금 기한 초과",
            f"「{title}」 입금 기한이 지나 낙찰이 무효 처리되었습니다. 사이트 내 신용 점수가 반영됩니다.",
            f"/project.html?id={pid}",
        )
    notify(
        conn,
        owner_id,
        "구매자 미입금",
        f"「{title}」 구매자가 기한 내 입금하지 않아 낙찰이 무효 처리되었습니다.",
        f"/project.html?id={pid}",
    )
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()

    # Second-chance: next highest unique bidder gets a fresh payment window
    if second_bidder_auto_enabled() and buyer_id:
        reawarded = reaward_to_next_bidder(
            conn, row, excluded_buyer_id=int(buyer_id)
        )
        if reawarded is not None:
            return reawarded
    return row


def process_deal_deadlines(conn: sqlite3.Connection) -> dict[str, int]:
    """Payment timeout + inspection auto-accept. Returns counts."""
    now = datetime.now(timezone.utc)
    out = {"payment_default": 0, "auto_settled": 0, "second_bidder_awards": 0}
    # unpaid
    rows = conn.execute(
        """
        SELECT * FROM projects
        WHERE deal_status = 'awaiting_payment'
          AND payment_deadline_at IS NOT NULL
          AND payment_deadline_at != ''
        """
    ).fetchall()
    for row in rows:
        dl = _parse_iso(str(row["payment_deadline_at"] or ""))
        if dl and now > dl:
            before_buyer = _row_get(row, "buyer_id")
            after = void_for_nonpayment(conn, row)
            out["payment_default"] += 1
            after_buyer = _row_get(after, "buyer_id") if after else None
            after_status = (_row_get(after, "deal_status") or "") if after else ""
            if (
                after_status == "awaiting_payment"
                and after_buyer
                and before_buyer
                and int(after_buyer) != int(before_buyer)
            ):
                out["second_bidder_awards"] += 1
    # inspection auto complete
    rows2 = conn.execute(
        """
        SELECT * FROM projects
        WHERE deal_status = 'inspection'
          AND inspection_deadline_at IS NOT NULL
          AND inspection_deadline_at != ''
        """
    ).fetchall()
    for row in rows2:
        dl = _parse_iso(str(row["inspection_deadline_at"] or ""))
        if dl and now > dl:
            settle_complete(
                conn,
                row,
                reason="auto_accept",
                note=f"검수 기한({deal_inspection_hours()}시간) 내 이의 없음 · 자동 구매 확정·정산",
            )
            out["auto_settled"] += 1
    return out


def _parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        exp = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp.astimezone(timezone.utc)
    except Exception:
        return None


def process_expired_auctions(conn: sqlite3.Connection) -> int:
    """End live auctions past auction_ends_at. Highest bid → sold; no bid → ended."""
    rows = conn.execute(
        """
        SELECT * FROM projects
        WHERE listing_status = 'approved'
          AND COALESCE(auction_status, 'live') = 'live'
          AND auction_ends_at IS NOT NULL
          AND auction_ends_at != ''
        """
    ).fetchall()
    now = datetime.now(timezone.utc)
    n = 0
    for row in rows:
        exp = _parse_iso(row["auction_ends_at"] or "")
        if not exp or now <= exp:
            continue
        top = conn.execute(
            """
            SELECT * FROM bids WHERE project_id = ?
            ORDER BY amount DESC, id DESC LIMIT 1
            """,
            (row["id"],),
        ).fetchone()
        if top:
            finalize_sale(
                conn,
                row,
                sold_price=int(top["amount"]),
                buyer_id=int(top["bidder_id"]),
                note="마감 자동 낙찰",
            )
        else:
            # Unsold → leave public board (this round only; not permanent display)
            archive_unsold_round(conn, int(row["id"]))
            notify(
                conn,
                int(row["owner_id"]),
                "이번 라운드 종료",
                f"「{row['title']}」 입찰 없이 마감되어 공개 목록에서 내려갔습니다. "
                f"다시 올리려면 내용을 다듬은 뒤 재등록·재검수가 필요합니다.",
                f"/app/#mine",
            )
        n += 1
    return n


def public_bidder_handle(display_name: str | None, bidder_id: int | None = None) -> str:
    """
    Public nickname for auction boards.
    Full display_name is OK (not email/phone). Email-like names are masked.
    """
    name = (display_name or "").strip()
    if not name:
        return f"입찰자#{int(bidder_id)}" if bidder_id else "입찰자"
    if "@" in name:
        local = name.split("@", 1)[0].strip() or "user"
        if len(local) <= 2:
            return local[0] + "**"
        return local[:2] + "***"
    if len(name) > 24:
        return name[:24] + "…"
    return name


def _party_label(display_name: str | None, user_id: int | None, *, role_ko: str) -> str:
    """Confirmation-card label: display name only (no email/phone/account)."""
    handle = public_bidder_handle(display_name, user_id)
    if handle and not handle.startswith("입찰자") and "@" not in handle:
        return handle
    if user_id:
        return f"{role_ko} #{int(user_id)}"
    return role_ko


def deal_is_complete_row(row: sqlite3.Row | dict) -> bool:
    """True only when deal_status is completed (accept / auto-settle)."""
    try:
        if isinstance(row, dict):
            st = row.get("deal_status") or ""
        else:
            st = row["deal_status"] if "deal_status" in row.keys() else ""
    except (IndexError, KeyError):
        st = ""
    return (st or "") == "completed"


def build_deal_certificate(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    kind: str,
    viewer_id: int | None = None,
) -> dict:
    """
    Site record confirmation for award or completed deal.
    Same payload for seller and buyer (both may save the image).
    """
    kind = (kind or "").strip().lower()
    if kind not in ("award", "complete"):
        raise ValueError("kind must be award or complete")

    pid = int(row["id"])
    owner_id = int(row["owner_id"])
    buyer_id = _row_get(row, "buyer_id")
    buyer_id_i = int(buyer_id) if buyer_id is not None else None
    astatus = (_row_get(row, "auction_status") or "") or ""
    if astatus != "sold" and not (_row_get(row, "sold_at") or ""):
        raise ValueError("not_sold")

    if kind == "complete" and not deal_is_complete_row(row):
        raise ValueError("not_complete")

    sold_at = (_row_get(row, "sold_at") or "") or ""
    completed_at = (
        (_row_get(row, "settled_at") or "")
        or (_row_get(row, "buyer_accepted_at") or "")
        or ""
    )
    amount = _row_get(row, "sold_price")
    if amount is None:
        amount = _row_get(row, "price_current")
    amount = int(amount or 0)

    seller_u = conn.execute(
        "SELECT id, display_name FROM users WHERE id = ?", (owner_id,)
    ).fetchone()
    buyer_u = None
    if buyer_id_i:
        buyer_u = conn.execute(
            "SELECT id, display_name FROM users WHERE id = ?", (buyer_id_i,)
        ).fetchone()

    seller_label = _party_label(
        seller_u["display_name"] if seller_u else None,
        owner_id,
        role_ko="판매자",
    )
    buyer_label = _party_label(
        buyer_u["display_name"] if buyer_u else None,
        buyer_id_i,
        role_ko="구매자",
    )

    # Stable confirmation no. (same for both parties; re-issue keeps same id)
    seed = f"{pid}|{sold_at}|{kind}|{amount}|{buyer_id_i or 0}"
    token = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8].upper()
    day = (sold_at or _now())[:10].replace("-", "")
    suffix = "A" if kind == "award" else "C"
    doc_id = f"WA-{pid}-{day}-{token}-{suffix}"

    issued = _now()
    event_at = sold_at if kind == "award" else (completed_at or sold_at)
    title = row["title"] or ""

    if kind == "award":
        doc_title_ko = "낙찰 기록 확인서"
        doc_title_en = "Award record confirmation"
        status_label_ko = "낙찰"
        status_label_en = "Awarded"
        status_note_ko = "입금 · 자산 이전 · 인수 절차가 남아 있을 수 있습니다."
        status_note_en = "Payment, transfer, and acceptance may still be pending."
        event_label_ko = "낙찰 시각"
        event_label_en = "Awarded at"
        lead_ko = "사이트에 아래 낙찰이 기록되었습니다."
        lead_en = "The following award is recorded on WakeAgain."
        file_stem = f"WakeAgain-낙찰확인-{pid}-{token}"
    else:
        doc_title_ko = "거래 기록 확인서"
        doc_title_en = "Transaction record confirmation"
        status_label_ko = "거래 절차 완료"
        status_label_en = "Procedure completed"
        status_note_ko = "사이트에 기록된 거래 절차가 완료된 상태입니다."
        status_note_en = "Site-recorded deal steps are complete."
        event_label_ko = "완료 시각"
        event_label_en = "Completed at"
        lead_ko = "사이트에 아래 거래 절차 완료가 기록되었습니다."
        lead_en = "The following completed deal is recorded on WakeAgain."
        file_stem = f"WakeAgain-거래확인-{pid}-{token}"

    disclaimer_ko = (
        "본 확인서는 WakeAgain에 저장된 거래 기록의 요약입니다. "
        "플랫폼(코어랩스)은 통신판매중개자이며 거래 당사자가 아닙니다. "
        "매물 품질·내용·권리·자산 이전의 1차 책임은 판매자·구매자에게 있습니다. "
        "이용약관 및 거래 당시 사이트 절차에 따릅니다."
    )
    disclaimer_en = (
        "This confirmation summarizes a record stored on WakeAgain. "
        "CoreLabs is an intermediary, not a party to the deal. "
        "Quality, rights, and transfer are the parties' responsibility. "
        "Subject to the Terms and site procedures at the time of the deal."
    )

    viewer_role = None
    if viewer_id is not None:
        if int(viewer_id) == owner_id:
            viewer_role = "seller"
        elif buyer_id_i is not None and int(viewer_id) == buyer_id_i:
            viewer_role = "buyer"

    return {
        "ok": True,
        "kind": kind,
        "doc_id": doc_id,
        "doc_title_ko": doc_title_ko,
        "doc_title_en": doc_title_en,
        "lead_ko": lead_ko,
        "lead_en": lead_en,
        "issued_at": issued,
        "event_at": event_at or issued,
        "event_label_ko": event_label_ko,
        "event_label_en": event_label_en,
        "venue": "WakeAgain (https://wakeagain.com)",
        "project_id": pid,
        "project_title": title,
        "amount": amount,
        "currency": "KRW",
        "seller_label": seller_label,
        "buyer_label": buyer_label,
        "status_label_ko": status_label_ko,
        "status_label_en": status_label_en,
        "status_note_ko": status_note_ko,
        "status_note_en": status_note_en,
        "fee_note_ko": "판매자 수수료 10% · 구매자는 위 거래 금액만 부담 (약관 제13조)",
        "fee_note_en": "10% seller fee · buyer pays the amount above only (Terms §13)",
        "disclaimer_ko": disclaimer_ko,
        "disclaimer_en": disclaimer_en,
        "file_stem": file_stem,
        "viewer_role": viewer_role,
        "shared": True,
        "note_ko": (
            "판매자·구매자 동일한 확인서입니다. 각자 저장할 수 있습니다. "
            "실명·연락처는 넣지 않습니다. 상대 연락은 매물 쪽지 또는 성사 후 판매자 정보에서 하세요."
        ),
        "note_en": (
            "Same confirmation for seller and buyer; either may save it. "
            "No real name or phone on this card — contact via listing messages or post-sale seller info."
        ),
    }


def bid_to_public(row: sqlite3.Row | dict) -> dict:
    """Public bid ticker — public handle + amount + optional buyer rank badge."""

    def _g(key: str, default=None):
        try:
            if isinstance(row, dict):
                return row.get(key, default)
            return row[key] if key in row.keys() else default
        except (IndexError, KeyError):
            return default

    bidder_id = _g("bidder_id")
    public_name = public_bidder_handle(_g("display_name"), int(bidder_id) if bidder_id else None)
    bought = int(_g("credit_bought") or 0)
    defaults = int(_g("credit_defaults") or 0)
    rank = buyer_rank(bought, defaults)
    out = {
        "id": _g("id"),
        "project_id": _g("project_id"),
        "amount": _g("amount"),
        "bidder_label": public_name,
        "created_at": _g("created_at"),
        "is_top": bool(_g("is_top")),
        "buyer_rank": None,
    }
    if rank["key"] != "scout":
        out["buyer_rank"] = {
            "key": rank["key"],
            "label": rank["label"],
            "bought_complete": rank["bought_complete"],
            "caution": rank["caution"],
        }
    return out


def top_bid_public(conn: sqlite3.Connection, project_id: int) -> dict | None:
    """Highest bid for a listing — for price panel & marketplace cards."""
    row = conn.execute(
        """
        SELECT b.*, u.display_name,
               COALESCE(u.credit_bought, 0) AS credit_bought,
               COALESCE(u.credit_defaults, 0) AS credit_defaults
        FROM bids b
        JOIN users u ON u.id = b.bidder_id
        WHERE b.project_id = ?
        ORDER BY b.amount DESC, b.id DESC
        LIMIT 1
        """,
        (int(project_id),),
    ).fetchone()
    if not row:
        return None
    pub = bid_to_public(row)
    pub["is_top"] = True
    return pub


def review_to_dict(row: sqlite3.Row, *, include_private: bool = False) -> dict:
    data = {
        "id": row["id"],
        "author_name": row["author_name"] or "",
        "role_label": (row["role_label"] if "role_label" in row.keys() else None) or "",
        "body": row["body"] or "",
        "sold_price": row["sold_price"] if "sold_price" in row.keys() else None,
        "side": (row["side"] if "side" in row.keys() else None) or "seller",
        "listing_status": row["listing_status"],
        "created_at": row["created_at"],
    }
    if include_private:
        data["user_id"] = row["user_id"]
        data["review_note"] = (row["review_note"] if "review_note" in row.keys() else None) or ""
        data["reviewed_at"] = (row["reviewed_at"] if "reviewed_at" in row.keys() else None) or ""
    return data


def showcase_to_dict(row: sqlite3.Row) -> dict:
    def g(key: str, default=None):
        try:
            if key in row.keys():
                v = row[key]
                return default if v is None else v
        except (IndexError, KeyError):
            pass
        return default

    status_key = (g("status_key") or "prototype") or "prototype"
    st = price_policy.STATUS_PRICING.get(status_key) or {}
    ptype = normalize_product_type(g("product_type") or "other")
    title = g("title") or ""
    demo_i18n = LISTING_DEMO_I18N.get(title) or {}
    return {
        "id": row["id"],
        "author_name": g("author_name") or "",
        "title": title,
        "one_liner": g("one_liner") or "",
        "one_liner_en": demo_i18n.get("one_liner_en") or "",
        "story": g("story") or "",
        "story_en": demo_i18n.get("story_en") or "",
        "demo": g("demo") or "",
        "status_key": status_key,
        "status_label": st.get("label") or status_key,
        "status_label_en": st.get("label_en") or st.get("label") or status_key,
        "product_type": ptype,
        "product_type_label": PRODUCT_TYPES.get(ptype, PRODUCT_TYPES["other"]),
        "product_type_label_en": PRODUCT_TYPES_EN.get(ptype, PRODUCT_TYPES_EN["other"]),
        "price_hint": g("price_hint"),
        "diag_score": g("diag_score"),
        "cheer_count": int(g("cheer_count") or 0),
        "listing_status": g("listing_status") or "approved",
        "created_at": g("created_at") or "",
        "note_ko": "쇼케이스(자랑)입니다. 판매 중 매물이 아니며 플랫폼 보증이 아닙니다.",
        "note_en": "Showcase only — not a for-sale listing. Not platform-guaranteed.",
    }


def auction_snapshot(row: sqlite3.Row, *, top_bid: dict | None = None) -> dict:
    """Lightweight public payload for polling live boards."""
    p = project_to_dict(row, include_private=False)
    out = {
        "id": p["id"],
        "title": p["title"],
        "one_liner": p["one_liner"],
        "keywords": p.get("keywords") or [],
        "product_type": p.get("product_type"),
        "price_start": p["price_start"],
        "price_current": p["price_current"],
        "bid_count": p["bid_count"],
        "bidder_count": p["bidder_count"],
        "min_increment": p["min_increment"],
        "next_min_bid": p["next_min_bid"],
        "auction_ends_at": p["auction_ends_at"],
        "auction_status": p["auction_status"],
        "listing_status": p["listing_status"],
        "updated_at": p["updated_at"],
        "status": p["status"],
        "top_bidder": None,
    }
    if top_bid:
        out["top_bidder"] = {
            "label": top_bid.get("bidder_label"),
            "amount": top_bid.get("amount"),
            "buyer_rank": top_bid.get("buyer_rank"),
        }
    return out


def refresh_project_bid_stats(conn: sqlite3.Connection, project_id: int) -> None:
    """Sync bid_count (events) and bidder_count (unique people) from bids table."""
    stats = conn.execute(
        """
        SELECT COUNT(*) AS n, COUNT(DISTINCT bidder_id) AS u
        FROM bids
        WHERE project_id = ?
        """,
        (project_id,),
    ).fetchone()
    conn.execute(
        """
        UPDATE projects
        SET bid_count = ?,
            bidder_count = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            int(stats["n"] or 0),
            int(stats["u"] or 0),
            _now(),
            project_id,
        ),
    )
