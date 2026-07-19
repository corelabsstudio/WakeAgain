from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

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

            CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(listing_status);
            CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_project ON messages(project_id);
            CREATE INDEX IF NOT EXISTS idx_fee_seller ON fee_invoices(seller_id);

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
                # website | webapp | mobile | desktop | api | game | other
                "product_type": "TEXT DEFAULT 'other'",
                "report_count": "INTEGER NOT NULL DEFAULT 0",
                "paused_reason": "TEXT",
                # Seller listing attestations (required at create)
                "license_note": "TEXT",
                "seller_attest_json": "TEXT",
            },
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
            """
        )
        # Backfill current price from start for existing rows
        conn.execute(
            """
            UPDATE projects
            SET price_current = COALESCE(price_current, price_start, 0),
                bid_count = COALESCE(bid_count, 0),
                min_increment = COALESCE(min_increment, 10000),
                auction_status = COALESCE(auction_status, 'live')
            WHERE price_current IS NULL OR bid_count IS NULL
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
    return {
        "score": credit["score"],
        "grade": credit["grade"],
        "label": credit["label"],
        "counts": {
            "sold_as_seller": credit["counts"]["sold_as_seller"],
            "bought_complete": credit["counts"]["bought_complete"],
            "defaults": credit["counts"]["defaults"],
        },
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
        "can_bid": profile_ok and not suspended,
        "can_close_deal": deal_ready and not suspended,
        "can_report": profile_ok and not suspended,
        "missing": missing,
    }


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
    return {"key": k, "label": PRODUCT_TYPES.get(k, PRODUCT_TYPES["other"])}


def project_to_dict(row: sqlite3.Row, *, include_private: bool = False) -> dict:
    try:
        assets = json.loads(row["assets_json"] or "[]")
    except json.JSONDecodeError:
        assets = []
    price_start = _row_get(row, "price_start")
    price_current = _row_get(row, "price_current")
    if price_current is None:
        price_current = price_start
    bid_count = int(_row_get(row, "bid_count", 0) or 0)
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
    data = {
        "id": row["id"],
        "owner_id": row["owner_id"],
        "title": row["title"],
        "one_liner": row["one_liner"],
        "status": row["status"],
        "status_label": price_policy.status_label(_row_get(row, "status")),
        "product_type": ptype["key"],
        "product_type_label": ptype["label"],
        "story": row["story"],
        "demo": row["demo"],
        "assets": assets,
        "price_start": price_start,
        "price_current": price_current,
        "price_buy_now": _row_get(row, "price_buy_now"),
        "bid_count": bid_count,
        "min_increment": min_inc,
        "next_min_bid": next_min,
        "auction_ends_at": ends,
        "auction_status": auction_status,
        "is_live": auction_status == "live",
        "is_paused": auction_status == "paused",
        "listing_status": row["listing_status"],
        "report_count": int(_row_get(row, "report_count", 0) or 0),
        "paused_reason": _row_get(row, "paused_reason") or "",
        "license_note": (_row_get(row, "license_note") or "") or "",
        "demo_verified": bool(int(_row_get(row, "demo_verified", 0) or 0)),
        "sold_price": sold_price,
        "sold_at": _row_get(row, "sold_at") or "",
        "buyer_id": _row_get(row, "buyer_id"),
        "deal_note": _row_get(row, "deal_note") or "",
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


def fee_breakdown(amount: int | None) -> dict:
    if amount is None:
        return {
            "rate": FEE_RATE,
            "rate_pct": 10,
            "payer": FEE_PAYER,
            "payer_ko": "판매자",
            "amount": None,
            "fee": None,
            "seller_net": None,
            "note": "성사 시 판매자에게 거래 대금의 10% 수수료. 구매자는 합의가만 부담.",
        }
    amt = int(amount)
    fee = int(round(amt * FEE_RATE))
    return {
        "rate": FEE_RATE,
        "rate_pct": 10,
        "payer": FEE_PAYER,
        "payer_ko": "판매자",
        "amount": amt,
        "fee": fee,
        "seller_net": amt - fee,
        "note": "성사 시 판매자에게 거래 대금의 10% 수수료. 구매자는 합의가만 부담.",
    }


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
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "seller_id": row["seller_id"],
        "deal_amount": row["deal_amount"],
        "fee_amount": row["fee_amount"],
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
    fee = fee_breakdown(deal_amount)
    now = _now()
    # one open invoice per project
    existing = conn.execute(
        "SELECT * FROM fee_invoices WHERE project_id = ? AND status = 'pending'",
        (project_id,),
    ).fetchone()
    if existing:
        return fee_invoice_to_dict(existing)
    cur = conn.execute(
        """
        INSERT INTO fee_invoices (
          project_id, seller_id, deal_amount, fee_amount, status, note, created_at
        ) VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """,
        (project_id, seller_id, deal_amount, fee["fee"], note[:500], now),
    )
    row = conn.execute("SELECT * FROM fee_invoices WHERE id = ?", (int(cur.lastrowid),)).fetchone()
    return fee_invoice_to_dict(row)


def finalize_sale(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    sold_price: int,
    buyer_id: int | None,
    note: str,
) -> sqlite3.Row:
    """Mark project sold, invoice fee, notify parties."""
    now = _now()
    pid = int(row["id"])
    owner_id = int(row["owner_id"])
    conn.execute(
        """
        UPDATE projects SET
          auction_status = 'sold', sold_price = ?, sold_at = ?, buyer_id = ?,
          price_current = ?, deal_note = ?, updated_at = ?
        WHERE id = ?
        """,
        (sold_price, now, buyer_id, sold_price, (note or "성사")[:500], now, pid),
    )
    inv = create_fee_invoice(
        conn,
        project_id=pid,
        seller_id=owner_id,
        deal_amount=sold_price,
        note=note or "성사 수수료",
    )
    fee = inv["fee_amount"]
    notify(
        conn,
        owner_id,
        "성사 · 수수료 안내",
        f"「{row['title']}」 성사 ₩{sold_price:,}. 판매자 수수료 ₩{fee:,} (10%). 이전 절차를 진행하세요.",
        f"/project.html?id={pid}",
    )
    if buyer_id:
        notify(
            conn,
            int(buyer_id),
            "성사 확정 (구매)",
            f"「{row['title']}」이(가) ₩{sold_price:,} 로 성사되었습니다. 판매자와 이전을 진행하세요.",
            f"/project.html?id={pid}",
        )
    # Auto credit: seller sale + buyer purchase (on-time flag when payment flow exists)
    credit_bump(conn, owner_id, sold=1)
    if buyer_id:
        credit_bump(conn, int(buyer_id), bought=1, on_time=1)
    return conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()


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
            conn.execute(
                """
                UPDATE projects SET auction_status = 'ended', updated_at = ?, deal_note = ?
                WHERE id = ?
                """,
                (_now(), "마감 · 입찰 없음", row["id"]),
            )
            notify(
                conn,
                int(row["owner_id"]),
                "경매 마감",
                f"「{row['title']}」 경매가 입찰 없이 마감되었습니다.",
                f"/project.html?id={row['id']}",
            )
        n += 1
    return n


def bid_to_public(row: sqlite3.Row) -> dict:
    """Public bid ticker — no email/phone. display_name only."""
    name = ""
    try:
        name = (row["display_name"] or "").strip()
    except (IndexError, KeyError):
        name = ""
    if not name:
        name = "입찰자"
    # soft anonymize: first char + **
    if len(name) >= 2:
        public_name = name[0] + "**"
    else:
        public_name = name + "**"
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "amount": row["amount"],
        "bidder_label": public_name,
        "created_at": row["created_at"],
    }


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
    ptype = (g("product_type") or "other") or "other"
    return {
        "id": row["id"],
        "author_name": g("author_name") or "",
        "title": g("title") or "",
        "one_liner": g("one_liner") or "",
        "story": g("story") or "",
        "demo": g("demo") or "",
        "status_key": status_key,
        "status_label": st.get("label") or status_key,
        "product_type": ptype,
        "product_type_label": PRODUCT_TYPES.get(ptype, ptype),
        "price_hint": g("price_hint"),
        "diag_score": g("diag_score"),
        "cheer_count": int(g("cheer_count") or 0),
        "listing_status": g("listing_status") or "approved",
        "created_at": g("created_at") or "",
        "note_ko": "쇼케이스(자랑)입니다. 판매 중 매물이 아니며 플랫폼 보증이 아닙니다.",
    }


def auction_snapshot(row: sqlite3.Row) -> dict:
    """Lightweight public payload for polling live boards."""
    p = project_to_dict(row, include_private=False)
    return {
        "id": p["id"],
        "title": p["title"],
        "one_liner": p["one_liner"],
        "price_start": p["price_start"],
        "price_current": p["price_current"],
        "bid_count": p["bid_count"],
        "min_increment": p["min_increment"],
        "next_min_bid": p["next_min_bid"],
        "auction_ends_at": p["auction_ends_at"],
        "auction_status": p["auction_status"],
        "listing_status": p["listing_status"],
        "updated_at": p["updated_at"],
        "status": p["status"],
    }
