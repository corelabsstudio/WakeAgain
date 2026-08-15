from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from wakeagain import __version__, db as database
from wakeagain import keywords as kw_mod
from wakeagain import listing_i18n
from wakeagain import oauth as oauth_mod
from wakeagain import payments as payments_mod
from wakeagain import pricing as price_policy
from wakeagain.admin_auth import require_admin
from wakeagain.auth import (
    create_token,
    get_current_user,
    get_optional_user,
    hash_password,
    verify_password,
)
from wakeagain.mailer import (
    send_mail,
    send_password_reset_code,
    send_verification_code,
    send_welcome_email,
    smtp_configured,
)

router = APIRouter(prefix="/api/v1")

# Dev: return email codes in API JSON. Production must use SMTP + EMAIL_DEV_MODE=0.
EMAIL_DEV_MODE = os.environ.get("EMAIL_DEV_MODE", "1").strip() not in {"0", "false", "False"}
# If SMTP missing/fails, optionally return code in API. Default OFF — production must not expose codes.
# Local only: EMAIL_CODE_FALLBACK=1 (or EMAIL_DEV_MODE=1).
EMAIL_CODE_FALLBACK = os.environ.get("EMAIL_CODE_FALLBACK", "0").strip() not in {
    "0",
    "false",
    "False",
}
EMAIL_CODE_MINUTES = int(os.environ.get("EMAIL_CODE_MINUTES", "30"))

# Product Hunt launch claim: "0% seller fee for the first 50 listings" — coupon
# campaign code, auto-redeemed for the seller on every new listing (best-effort).
PH_FIRST50_CODE = os.environ.get("PH_FIRST50_COUPON_CODE", "PH-FIRST50")

# 아이디 찾기: IP당 윈도우 내 요청 제한 (열거·브루트 완화)
FIND_EMAIL_RATE_LIMIT = max(1, int(os.environ.get("FIND_EMAIL_RATE_LIMIT", "5")))
FIND_EMAIL_RATE_WINDOW_SEC = max(60, int(os.environ.get("FIND_EMAIL_RATE_WINDOW_SEC", "900")))
_find_email_hits: dict[str, list[float]] = {}

# 개인정보 보호법: 만 14세 미만 아동 개인정보 처리 제한 → WakeAgain은 가입 자체를 거절
MIN_AGE_YEARS = 14
MAX_AGE_YEARS = 120

# ── 매물 등록 필수 필드 정책 (2026-08-15) ──────────────────────────────────
# 경쟁사(SideProjectors 등)는 저장소 링크가 선택 필드라 빈 매물이 많다.
# WakeAgain은 필수로 강제한다. 단 "코드를 검증해준다"가 아니라 "검증할 수 있게 강제한다" —
# 형식 검증까지만 하고 실제 접근성은 확인하지 않는다 (비공개 레포에서 항상 실패하므로).
REPO_HOSTS = {
    "github.com",
    "www.github.com",
    "gitlab.com",
    "www.gitlab.com",
    "bitbucket.org",
    "www.bitbucket.org",
}
# /{owner}/{repo} — 뒤에 트리 경로가 더 붙어도 허용
_REPO_PATH_RE = re.compile(r"^/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+(/.*)?$")
_LAST_ACTIVITY_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _normalize_repo_url(raw: str) -> str:
    """Return a cleaned repo URL, or raise ValueError with a user-facing message.

    Format-only: host whitelist + /owner/repo path. Private repos are fine — we never
    fetch the URL, so a 404 from a private repo can't reject a legitimate listing.
    """
    s = (raw or "").strip()
    if not s:
        raise ValueError("저장소 URL을 입력해 주세요.")
    if "://" not in s:
        s = "https://" + s
    try:
        u = urlparse(s)
    except ValueError as e:
        raise ValueError("저장소 URL 형식이 올바르지 않습니다.") from e
    if u.scheme not in ("http", "https"):
        raise ValueError("저장소 URL은 http(s) 주소여야 합니다.")
    host = (u.hostname or "").lower()
    if host not in REPO_HOSTS:
        raise ValueError("저장소는 GitHub · GitLab · Bitbucket 주소만 등록할 수 있습니다.")
    path = (u.path or "").rstrip("/")
    if path.endswith(".git"):
        path = path[: -len(".git")]
    if not _REPO_PATH_RE.match(path):
        raise ValueError(
            "저장소 주소가 올바르지 않습니다. 예: https://github.com/사용자명/저장소명"
        )
    return f"https://{host}{path}"


def _normalize_live_url(raw: str) -> str:
    """Return a cleaned http(s) URL for the live demo, or raise ValueError."""
    s = (raw or "").strip()
    if not s:
        raise ValueError("라이브 데모 URL을 입력해 주세요.")
    if "://" not in s:
        s = "https://" + s
    try:
        u = urlparse(s)
    except ValueError as e:
        raise ValueError("라이브 데모 URL 형식이 올바르지 않습니다.") from e
    if u.scheme not in ("http", "https"):
        raise ValueError("라이브 데모 URL은 http(s) 주소여야 합니다.")
    host = (u.hostname or "").lower()
    # 최소 형식 검증: 점이 있는 호스트. 접속 여부는 확인하지 않는다.
    if not host or "." not in host or host.endswith("."):
        raise ValueError("라이브 데모 주소가 올바르지 않습니다. 예: https://myapp.com")
    return s


def _normalize_last_activity(raw: str) -> str:
    """Validate 'YYYY-MM'. Rejects the future and anything before 2000."""
    s = (raw or "").strip()[:7]
    if not s:
        raise ValueError("마지막 활동일을 입력해 주세요. (예: 2026-03)")
    if not _LAST_ACTIVITY_RE.match(s):
        raise ValueError("마지막 활동일은 YYYY-MM 형식으로 입력해 주세요. (예: 2026-03)")
    now = datetime.now(timezone.utc)
    if s > f"{now.year:04d}-{now.month:02d}":
        raise ValueError("마지막 활동일이 미래로 되어 있습니다.")
    if s < "2000-01":
        raise ValueError("마지막 활동일이 너무 과거입니다.")
    return s


def _parse_birth_date(raw: str) -> date:
    s = (raw or "").strip()
    if not s:
        raise HTTPException(status_code=400, detail="생년월일을 입력해 주세요.")
    try:
        # Accept YYYY-MM-DD (HTML date input)
        return date.fromisoformat(s[:10])
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail="생년월일 형식이 올바르지 않습니다. (예: 2000-01-15)"
        ) from e


def _normalize_country(raw: str) -> str:
    """ISO 3166-1 alpha-2, uppercased. Invalid/empty input is silently dropped."""
    s = (raw or "").strip().upper()
    return s if len(s) == 2 and s.isalpha() else ""


def _age_years(birth: date, today: date | None = None) -> int:
    """만 나이 (생일 전날까지 한 살 적게)."""
    today = today or date.today()
    years = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        years -= 1
    return years


def _require_age_eligible(birth_raw: str) -> date:
    """만 14세 미만이면 가입 거절. 유효한 birth date 반환."""
    birth = _parse_birth_date(birth_raw)
    today = date.today()
    if birth > today:
        raise HTTPException(status_code=400, detail="생년월일이 미래일 수 없습니다.")
    age = _age_years(birth, today)
    if age > MAX_AGE_YEARS:
        raise HTTPException(status_code=400, detail="생년월일을 다시 확인해 주세요.")
    if age < MIN_AGE_YEARS:
        raise HTTPException(
            status_code=403,
            detail=(
                f"만 {MIN_AGE_YEARS}세 미만은 WakeAgain에 가입할 수 없습니다. "
                "관련 법령에 따라 아동 회원 가입을 받지 않습니다."
            ),
        )
    return birth


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _new_email_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _code_expiry_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=EMAIL_CODE_MINUTES)).isoformat()


def _issue_email_code(conn, user_id: int) -> str:
    code = _new_email_code()
    conn.execute(
        "UPDATE users SET email_code_hash = ?, email_code_expires = ? WHERE id = ?",
        (_hash_code(code), _code_expiry_iso(), user_id),
    )
    return code


def _deliver_code_mail(
    email: str,
    code: str,
    *,
    kind: Literal["verify", "reset"] = "verify",
) -> dict[str, Any]:
    """
    Try SMTP first (when configured and not pure dev mode).
    Always safe-return flags for the client UI.
    On SMTP missing/fail + EMAIL_CODE_FALLBACK, include dev_email_code so users are not stuck.
    """
    email = (email or "").strip().lower()
    send_fn = send_verification_code if kind == "verify" else send_password_reset_code
    out: dict[str, Any] = {
        "email_sent": False,
        "email_configured": smtp_configured(),
        "email_dev_mode": EMAIL_DEV_MODE,
    }
    if EMAIL_DEV_MODE:
        out["dev_email_code"] = code
        out["dev_note"] = "EMAIL_DEV_MODE: 화면에 코드 표시 (SMTP 생략 가능)"
        # Still try SMTP if configured so real inboxes work in hybrid ops
        if smtp_configured():
            out["email_sent"] = send_fn(email, code)
        return out

    if not smtp_configured():
        if EMAIL_CODE_FALLBACK:
            out["warning"] = (
                "메일 서버(SMTP)가 아직 연결되지 않아 이메일을 보낼 수 없습니다. "
                "아래에 표시된 코드를 입력해 주세요."
            )
            out["dev_email_code"] = code
            out["dev_note"] = "SMTP 미설정 · 폴백으로 화면에 코드 표시"
        else:
            out["warning"] = (
                "메일 서버가 아직 연결되지 않아 이메일을 보낼 수 없습니다. "
                "잠시 후 다시 시도하거나 관리자에게 문의해 주세요."
            )
        return out

    sent = send_fn(email, code)
    out["email_sent"] = sent
    if not sent:
        if EMAIL_CODE_FALLBACK:
            out["warning"] = (
                "메일 전송에 실패했습니다. 스팸함을 확인하거나, "
                "아래에 표시된 코드로 진행해 주세요."
            )
            out["dev_email_code"] = code
            out["dev_note"] = "SMTP 실패 · 폴백으로 화면에 코드 표시"
        else:
            out["warning"] = (
                "메일 전송에 실패했습니다. 스팸함을 확인한 뒤 잠시 후 다시 시도해 주세요. "
                "(운영 환경에서는 보안상 화면에 코드를 표시하지 않습니다.)"
            )
    return out


def _deliver_verify_code(email: str, code: str) -> dict[str, Any]:
    return _deliver_code_mail(email, code, kind="verify")


def _deliver_reset_code(email: str, code: str) -> dict[str, Any]:
    return _deliver_code_mail(email, code, kind="reset")


def _welcome_lang(country: str | None, request: Request | None) -> str:
    """KR account country -> ko. Any other declared country -> en. No country yet (OAuth
    signup, collected later) -> fall back to browser Accept-Language, same signal _lang_of()
    uses elsewhere on the site."""
    c = (country or "").strip().upper()
    if c == "KR":
        return "ko"
    if c:
        return "en"
    return _lang_of(request) if request is not None else "en"


def _maybe_send_welcome_mail(
    user_id: int,
    email: str,
    name: str,
    *,
    lang: str = "en",
    force: bool = False,
) -> bool:
    """Maker welcome email — once per account (users.welcome_mailed_at gate), unless force=True.

    Best-effort: never raises. Called outside any open db() transaction since it does network I/O.
    """
    if not email:
        return False
    with database.db() as conn:
        row = conn.execute(
            "SELECT welcome_mailed_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return False
        if row["welcome_mailed_at"] and not force:
            return False
    try:
        sent = send_welcome_email(email, name or "", lang=lang)
    except Exception:
        sent = False
    if sent:
        with database.db() as conn:
            conn.execute(
                "UPDATE users SET welcome_mailed_at = ? WHERE id = ?",
                (database._now(), user_id),
            )
    return sent


def _lang_of(request: Request) -> str:
    """en/ko from Accept-Language (frontend sends 'en,ko;q=0.8' or 'ko,en;q=0.8')."""
    al = (request.headers.get("accept-language") or "").strip().lower()
    return "en" if al.startswith("en") else "ko"


def _require_trust(
    user: dict, need: Literal["list", "bid", "fulfill", "deal"]
) -> None:
    """Trust gates.

    - bid: Lv1 email only (low friction auction entry)
    - fulfill: Lv2 real name+phone (after award — pay / accept)
    - list: Lv2 + seller public identity
    - deal: Lv3 settlement (seller payout / close-deal)
    """
    trust = user.get("trust") or {}
    if need == "list" and not trust.get("can_list"):
        if not trust.get("email_verified"):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "email_unverified",
                    "message": "이메일 인증 후 매물을 등록할 수 있습니다.",
                    "trust": trust,
                },
            )
        if not trust.get("profile_complete"):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "profile_incomplete",
                    "message": "실명·휴대폰 프로필을 완성한 뒤 매물을 등록할 수 있습니다.",
                    "trust": trust,
                },
            )
        if not trust.get("seller_identity_complete"):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "seller_identity_required",
                    "message": "구매자가 판매자를 확인할 수 있도록 판매자 공개 정보를 등록해 주세요. (통신판매중개 고지 의무)",
                    "trust": trust,
                },
            )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "profile_incomplete",
                "message": "실명·휴대폰 프로필을 완성한 뒤 매물을 등록할 수 있습니다.",
                "trust": trust,
            },
        )
    if need == "bid" and not trust.get("can_bid"):
        if not trust.get("email_verified"):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "email_unverified",
                    "message": "가격 쓰기(입찰)에는 이메일 인증만 있으면 됩니다. 먼저 이메일을 확인해 주세요.",
                    "trust": trust,
                },
            )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "bid_not_allowed",
                "message": "지금은 입찰할 수 없습니다. 계정 상태를 확인해 주세요.",
                "trust": trust,
            },
        )
    if need == "fulfill" and not trust.get("can_fulfill_purchase"):
        if not trust.get("email_verified"):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "email_unverified",
                    "message": "이메일 인증이 필요합니다.",
                    "trust": trust,
                },
            )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "profile_incomplete",
                "message": "낙찰 후 결제·인수에는 실명·휴대폰(Lv2) 확인이 필요합니다. 앱 → 내 정보에서 완료해 주세요.",
                "trust": trust,
            },
        )
    if need == "deal" and not trust.get("can_close_deal"):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "deal_not_ready",
                "message": "정산·이전 확정 전 정산 계좌(예금주·은행·계좌, Lv3)를 등록해 주세요.",
                "trust": trust,
            },
        )


def _auth_payload(
    user: dict,
    token: str,
    *,
    dev_code: str | None = None,
    mail_meta: dict | None = None,
) -> dict:
    out: dict[str, Any] = {"ok": True, "token": token, "user": user}
    if mail_meta:
        for k in (
            "email_sent",
            "email_configured",
            "email_dev_mode",
            "dev_email_code",
            "dev_note",
            "warning",
        ):
            if k in mail_meta and mail_meta[k] is not None:
                out[k] = mail_meta[k]
    elif dev_code and (EMAIL_DEV_MODE or EMAIL_CODE_FALLBACK):
        out["dev_email_code"] = dev_code
        out["dev_note"] = "EMAIL_DEV_MODE/FALLBACK: 화면에 코드 표시"
    return out


# --- schemas ---


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=80)
    # 만 14세 이상 확인용 — 필수 (YYYY-MM-DD)
    birth_date: str = Field(min_length=8, max_length=12)
    # UI 체크박스 동의 (서버에서도 강제)
    confirm_age_14: bool = False
    # ISO 3166-1 alpha-2 (e.g. "KR", "US") — 매물 국기 배지·해외거래 판정용
    country: str = Field(default="", max_length=2)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetConfirmIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=12)
    new_password: str = Field(min_length=8, max_length=128)


class FindEmailIn(BaseModel):
    """아이디(이메일) 찾기 — 프로필에 등록한 실명 + 휴대폰으로 조회."""
    real_name: str = Field(min_length=2, max_length=40)
    phone: str = Field(min_length=10, max_length=20)


class CloseDealIn(BaseModel):
    sold_price: int | None = Field(default=None, ge=0)
    buyer_user_id: int | None = None
    note: str = Field(default="", max_length=500)
    use_current_bid: bool = True


class VerifyEmailIn(BaseModel):
    code: str = Field(min_length=4, max_length=12)


class ProfileIn(BaseModel):
    real_name: str = Field(min_length=2, max_length=40)
    phone: str = Field(min_length=10, max_length=20)
    role: Literal["seller", "buyer", "both"] = "both"
    display_name: str = Field(default="", max_length=80)
    country: str = Field(default="", max_length=2)


class SettlementIn(BaseModel):
    bank: str = Field(min_length=2, max_length=40)
    holder: str = Field(min_length=2, max_length=40)
    account: str = Field(min_length=8, max_length=40)
    is_business: bool = False


class SellerIdentityIn(BaseModel):
    """구매자 확인용 판매자 공개 신원 (통신판매중개 정보 제공 의무)."""
    seller_type: Literal["individual", "business"]
    trade_name: str = Field(min_length=2, max_length=80)
    # 영문 상호(선택). 매물이 영어로 보일 때 판매자명만 한글로 남는 걸 막는 용도.
    # 비워 두면 한글 상호를 그대로 노출한다 — 법인명을 임의로 번역하지 않는다.
    trade_name_en: str = Field(default="", max_length=80)
    ceo_name: str = Field(default="", max_length=40)
    business_reg_no: str = Field(default="", max_length=20)
    mail_order_report_no: str = Field(default="", max_length=40)
    contact_email: EmailStr
    contact_phone: str = Field(min_length=10, max_length=20)
    address: str = Field(default="", max_length=200)


class ReportIn(BaseModel):
    reason: Literal["low_quality", "plagiarism", "not_working", "fraud", "other"]
    detail: str = Field(default="", max_length=1000)


class ProjectIn(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    one_liner: str = Field(min_length=1, max_length=120)
    status: str = Field(min_length=1, max_length=40)
    product_type: str = Field(default="other", max_length=40)
    story: str = Field(min_length=1, max_length=2000)
    # 매물 등록 필수 필드 정책 (2026-08-15) — 신규 등록 필수 3종
    # 저장소 URL (GitHub/GitLab/Bitbucket). 비공개 레포 허용 → is_private_repo로 표시
    repo_url: str = Field(default="", max_length=300)
    is_private_repo: bool = False
    # 라이브 데모 URL. is_offline=True면 면제 (스크린샷은 어차피 항상 필수)
    live_url: str = Field(default="", max_length=300)
    is_offline: bool = False
    # 마지막 활동일 'YYYY-MM'
    last_activity_at: str = Field(default="", max_length=7)
    # Optional free-text demo; screenshots can replace it
    demo: str = Field(default="", max_length=1000)
    # Public /media/demos/{user_id}/… URLs from upload endpoint (max 5)
    demo_images: list[str] = Field(default_factory=list, max_length=5)
    assets: list[str] = Field(default_factory=list)
    # Plain-language product clarity (required for new listings)
    features: list[str] = Field(default_factory=list, max_length=12)
    audience: str = Field(default="", max_length=120)
    works_now: str = Field(default="", max_length=500)
    limits: str = Field(default="", max_length=500)
    # Seller self-declared: product's own UI works in English (or is easily switched). Not verified.
    english_ready: bool = False
    # made | resale | other
    acquisition: str = Field(default="", max_length=20)
    acquisition_note: str = Field(default="", max_length=200)
    # Marketplace tags (1–5) — AI suggest or manual; improves buyer search
    keywords: list[str] = Field(default_factory=list, max_length=10)
    # Optional buy-now; both capped so 999999999999… abuse is rejected
    price_start: int | None = Field(default=None, ge=50_000, le=100_000_000)
    price_buy_now: int | None = Field(default=None, ge=50_000, le=100_000_000)
    contact: str = Field(default="", max_length=120)
    min_increment: int | None = Field(default=10000, ge=1000, le=10_000_000)
    auction_days: int = Field(default=7, ge=1, le=30)
    # 헬프티켓 (Kmong-style)
    q_credits_offered: int = Field(default=1, ge=1, le=3)  # 무료 헬프티켓 1~3
    q_credit_unit_price: int = Field(default=0, ge=0, le=100_000)  # 0 = no add-on sale
    q_credit_sla_hours: int = Field(default=48, ge=24, le=72)
    # Minimum listing guidelines (seller attestation — required)
    license_note: str = Field(default="", max_length=200)
    attest_works: bool = False
    attest_license: bool = False
    attest_rights: bool = False
    attest_features: bool = False
    attest_transfer: bool = False
    # Required when demo_images present: screenshots match real product
    attest_shots: bool = False


class KeywordSuggestIn(BaseModel):
    title: str = Field(default="", max_length=80)
    one_liner: str = Field(default="", max_length=120)
    story: str = Field(default="", max_length=2000)
    product_type: str = Field(default="", max_length=40)
    lang: str = Field(default="ko", max_length=8)


class BidIn(BaseModel):
    amount: int = Field(ge=0, le=10_000_000_000)


class InterestIn(BaseModel):
    email: EmailStr | None = None
    name: str = Field(default="", max_length=60)
    category: str = Field(min_length=1, max_length=120)
    budget: str = Field(default="", max_length=60)
    note: str = Field(default="", max_length=1000)


# --- public ---


@router.get("/health")
def health():
    from wakeagain import scheduler as auction_scheduler

    sched = auction_scheduler.status()
    return {
        "ok": True,
        "service": "WakeAgain",
        "version": __version__,
        "channels": ["web", "android", "ios"],
        "scheduler": {
            "enabled": sched.get("enabled"),
            "running": sched.get("running"),
            "last_run_at": sched.get("last_run_at"),
            "runs": sched.get("runs"),
        },
    }


@router.get("/config")
def client_config():
    """Clients (web / Play / App Store) read this once at boot."""
    from wakeagain.global_config import public_global_config

    return {
        "brand": "WakeAgain",
        "operator": {
            "name_ko": "코어랩스",
            "name_en": "CoreLabs",
            "contact_email": "corelabs.studio@gmail.com",
            "copyright": "© 2026 CoreLabs. All rights reserved.",
        },
        "global": public_global_config(),
        "legal": {
            "terms": "/legal/terms.html",
            "terms_en": "/legal/terms.en.html",
            "privacy": "/legal/privacy.html",
            "controlling_locale": "ko",
            "note_en": "Korean terms control until region-specific counsel review.",
        },
        "api_version": "v1",
        "version": __version__,
        "features": {
            "auth": True,
            "projects": True,
            "interest": True,
            "pre_registration_leads": True,
            "trust_gates": True,
            "email_verification": True,
            "settlement_profile": True,
        },
        "channels": {
            "web": True,
            "play_store": True,
            "app_store": True,
        },
        "auth": {"token_type": "Bearer", "header": "Authorization"},
        "paths": {
            "register": "/api/v1/auth/register",
            "login": "/api/v1/auth/login",
            "find_email": "/api/v1/auth/find-email",
            "verify_email": "/api/v1/auth/verify-email",
            "resend_verify": "/api/v1/auth/resend-verify",
            "me": "/api/v1/me",
            "profile": "/api/v1/me/profile",
            "settlement": "/api/v1/me/settlement",
            "projects": "/api/v1/projects",
            "auctions_live": "/api/v1/auctions/live",
            "place_bid": "/api/v1/projects/{id}/bids",
            "interest": "/api/v1/interest",
            "stats": "/api/v1/stats",
            "block_user": "POST /api/v1/users/{id}/block",
            "unblock_user": "DELETE /api/v1/users/{id}/block",
            "my_blocks": "GET /api/v1/me/blocks",
        },
        "auction_policy": {
            "public_live_board": True,
            "poll_seconds": 4,
            "default_min_increment_krw": 10000,
            "default_auction_days": 7,
            "public_board": "live_round_only",
            "unsold_leaves_board": True,
            "relist_requires_review": True,
            "relist_queue": "back_of_line",
            "sort": "boost_then_trust_score_desc_then_round_asc",
            "exposure": {
                "model": "listing_quality_plus_help_tickets",
                "help_ticket_points_per": database.HELP_TICKET_POINTS_PER,
                "note_ko": (
                    "예비 구매자 기준 가산점: 매물 설명·포트폴리오 완성도 + 헬프티켓 개수 비례. "
                    "점수 높을수록 상위 노출. 같은 점수면 이번 라운드 입장 순(재등록 후순위)."
                ),
            },
            "note": (
                "공개 목록·라이브 보드는 이번 경매 라운드(live) 매물만 노출합니다. "
                "유찰 시 자동으로 목록에서 내려가며, 다시 올리려면 재검수가 필요합니다. "
                "재등록은 줄 맨 뒤(후순위)부터 시작합니다. "
                "노출 순위는 매물 설명·포트폴리오·헬프티켓 가산점 → 라운드 순입니다. "
                "입찰 중 현재가·호가는 방문객 전원 공개, 입찰자 실명은 마스킹."
            ),
            "note_en": (
                "Only the current live auction round is listed. "
                "Unsold listings leave the board at close; re-list requires review "
                "and joins the back of the queue. "
                "Ranking: listing quality + help tickets, then round queue order."
            ),
            "start_price_by_status": price_policy.public_policy(),
            "listing_collection_mode": database.listing_collection_mode(),
        },
        "q_credit_policy": database.q_credit_policy_public(),
        "fee_policy": {
            "payer": "seller",
            "payer_ko": "판매자",
            "rate_pct": 10,
            "model": "flat",
            "min_fee_krw": database.FEE_MIN_KRW,
            "terms_article": "제13조",
            "message_ko": (
                f"성사 시 판매자에게 거래 대금의 10% 수수료(최소 {database.FEE_MIN_KRW:,}원). "
                "구매자는 합의(낙찰)가만 부담. 등록·관심·입찰 무료. (이용약관 제13조)"
            ),
        },
        "payment_policy": {
            "stage": "pg_required_for_ops",
            "auto_award_on_expiry": True,
            "background_scheduler": True,
            "payment_link_auto": False,
            "one_hour_timer_auto": True,
            "second_bidder_auto": database.second_bidder_auto_enabled(),
            "buyer_protection": True,
            "no_pre_pg_fallback": True,
            "deal": database.deal_policy_public(),
            "message_ko": database.deal_policy_public()["message_ko"],
            "note_ko": (
                "실거래·입금 확인은 PG 연동 후 운영. "
                "PG 없을 때 쓸 수동 입금·차선책 제품 기능은 추가하지 않음."
            ),
            "target_after_pg_ko": "PG: 결제 링크 · 웹훅→paid · 1시간 만료 · 인수/자동확정 후 정산.",
            "terms_article": "제12조 · 제14조",
            "portone": payments_mod.portone_public_config(),
        },
        "product_types": [
            {
                "key": k,
                "label": v,
                "label_en": database.PRODUCT_TYPES_EN.get(k, v),
            }
            for k, v in database.PRODUCT_TYPES.items()
        ],
        "metrics_policy": {
            "mode": "live_counts",
            "display": ["projects", "interests", "went_live"],
            "listing_fee_krw": 0,
            "went_live_reveal_at": int(
                os.environ.get("WENT_LIVE_REVEAL_AT", "5") or "5"
            ),
            "note": "실제 DB 건수만. 성사(세상으로 나간) 수는 임계값 이전 「추후 공개」.",
        },
        # Premium listing boost — scaffold only (docs/PREMIUM_BOOST.md). No purchase UI until enabled.
        "premium_boost": {
            "purchase_enabled": database.premium_boost_feature_enabled(),
            "env": "PREMIUM_BOOST_ENABLED",
            "doc": "docs/PREMIUM_BOOST.md",
            "fields": ["boost_until", "boost_tier", "boost_product"],
            "note_ko": (
                "상위 노출 상품 미판매. 목록 정렬은 boost_until 활성 시 우선. "
                "결제·구매 UI는 PREMIUM_BOOST_ENABLED=1 및 구현 후."
            ),
        },
        "oauth": {
            "enabled": bool(oauth_mod.enabled_providers()),
            "providers": oauth_mod.enabled_providers(),
            "note_ko": "SNS 로그인은 가입만 간소화합니다. 만 14세 확인·Lv2 실명/휴대폰·Lv3 계좌는 그대로 필요합니다.",
            "public_base": oauth_mod.public_base(),
        },
        "trust_policy": {
            "doc": "TRUST.md",
            "friction_note_ko": (
                "입찰은 Lv1(이메일)만. 실명·휴대폰(Lv2)은 낙찰 후 결제·인수 때, "
                "계좌(Lv3)는 판매자 정산·성사 확정 때 요구합니다."
            ),
            "levels": [
                {"level": 0, "code": "Lv0", "name": "가입", "can": ["browse", "interest"]},
                {"level": 1, "code": "Lv1", "name": "이메일 인증", "can": ["bid", "profile"]},
                {
                    "level": 2,
                    "code": "Lv2",
                    "name": "신원 확인",
                    "can": ["list", "fulfill_purchase", "report"],
                },
                {"level": 3, "code": "Lv3", "name": "거래 준비", "can": ["close_deal", "settlement"]},
            ],
            "bid_requires": ["email_verified"],
            "fulfill_requires": ["email_verified", "real_name", "phone"],
            "list_requires": [
                "email_verified",
                "real_name",
                "phone",
                "seller_identity",
            ],
            "deal_requires": ["settlement_bank", "settlement_holder", "settlement_account"],
            "seller_identity": {
                "required_to_list": True,
                "public_on_listing": True,
                "fields": [
                    "seller_type",
                    "trade_name",
                    "ceo_name",
                    "business_reg_no",
                    "mail_order_report_no",
                    "contact_email",
                    "contact_phone",
                    "address",
                ],
                "path": "PUT /api/v1/me/seller-identity",
                "message_ko": (
                    "매물 상세에서 구매자가 판매자를 확인할 수 있도록 "
                    "상호(또는 성명)·연락처·(사업자 시) 등록번호 등을 공개합니다. "
                    "운영자는 거래 당사자가 아닙니다."
                ),
            },
            "message": "큰돈이 오갈 수 있는 장입니다. 매물 등록·입찰 전 이메일 인증과 실명·연락처를 확인합니다.",
            "email_dev_mode": EMAIL_DEV_MODE,
            "email_smtp_configured": smtp_configured(),
            "email_code_fallback": EMAIL_CODE_FALLBACK,
            "min_age_years": MIN_AGE_YEARS,
            "age_gate": {
                "min_years": MIN_AGE_YEARS,
                "rule": "만 나이 기준. 만 14세 미만은 가입 불가(법정대리인 동의 경로 없음).",
                "collects": "birth_date",
                "message_ko": f"만 {MIN_AGE_YEARS}세 미만은 WakeAgain에 가입할 수 없습니다.",
            },
            "broker_role": "통신판매중개자",
            "fraud_policy": {
                "doc": "TRUST.md §0-c · 이용약관 제16조 · 제21조",
                "message_ko": (
                    "이용자 간 사기·분쟁의 1차 책임은 당사자에게 있습니다. "
                    "회사는 거래 당사자·보증인이 아니며, 형식 검수·사이트 내 신용 점수는 보증이 아닙니다."
                ),
                "report_email": "corelabs.studio@gmail.com",
                "not_guarantor": True,
            },
            "report_policy": {
                "enabled": True,
                "requires": "Lv2 (실명·휴대폰)",
                "reasons": [
                    {"key": k, "label": v} for k, v in database.REPORT_REASONS.items()
                ],
                "pause_threshold": database.REPORT_PAUSE_THRESHOLD,
                "account_suspend_threshold": database.REPORT_ACCOUNT_SUSPEND_THRESHOLD,
                "message_ko": (
                    f"서로 다른 구매자 신고가 {database.REPORT_PAUSE_THRESHOLD}건이면 경매 자동 중단, "
                    f"판매자 매물 합산 {database.REPORT_ACCOUNT_SUSPEND_THRESHOLD}건이면 계정 자동 정지."
                ),
                "path": "POST /api/v1/projects/{id}/report",
            },
            "block_policy": {
                "enabled": True,
                "requires": "login (정지 아님)",
                "message_ko": (
                    "유저 차단 시 상대 매물이 목록·상세에서 숨겨지고, "
                    "입찰·쪽지 등 상호 액션이 거부됩니다. 신고와 별개입니다."
                ),
                "paths": {
                    "block": "POST /api/v1/users/{id}/block",
                    "unblock": "DELETE /api/v1/users/{id}/block",
                    "list": "GET /api/v1/me/blocks",
                },
                "effects": [
                    "hide_blocked_user_listings",
                    "reject_bid_buy_message",
                    "bidirectional_interaction_guard",
                ],
            },
            "listing_guidelines": {
                "required": True,
                "items": [
                    {
                        "key": "repo_url",
                        "label_ko": "저장소 URL (GitHub·GitLab·Bitbucket · 비공개 레포 허용)",
                    },
                    {
                        "key": "live_url",
                        "label_ko": "라이브 데모 URL (서비스 종료 시 '내려감' 체크 + 스크린샷)",
                    },
                    {
                        "key": "last_activity_at",
                        "label_ko": "마지막 활동일 (YYYY-MM)",
                    },
                    {
                        "key": "features",
                        "label_ko": "이 제품이 하는 일 (기능 3가지 이상, 쉬운 말)",
                    },
                    {
                        "key": "audience",
                        "label_ko": "누구를 위한 제품인지",
                    },
                    {
                        "key": "works_now",
                        "label_ko": "지금 되는 것",
                    },
                    {
                        "key": "limits",
                        "label_ko": "지금 안 되는 것 · 한계",
                    },
                    {
                        "key": "acquisition",
                        "label_ko": "제작 / 재판매 등 취득 경로",
                    },
                    {
                        "key": "attest_works",
                        "label_ko": "데모(또는 설명 범위)에서 지금 되는 것을 직접 확인했습니다.",
                    },
                    {
                        "key": "attest_features",
                        "label_ko": "하는 일·되는 것·안 되는 것이 과장 없이 사실입니다.",
                    },
                    {
                        "key": "attest_license",
                        "label_ko": "라이선스(MIT·GPL 등) 또는 양도 조건을 기재했습니다.",
                    },
                    {
                        "key": "attest_rights",
                        "label_ko": "제가 팔 권한이 있는 자산입니다. (남의 코드·계정 도용 아님)",
                    },
                    {
                        "key": "attest_transfer",
                        "label_ko": "성사·입금 확인 후 이전 절차를 끝까지 진행할 수 있습니다.",
                    },
                    {
                        "key": "license_note",
                        "label_ko": "라이선스 / 양도 조건 (텍스트 필수)",
                    },
                ],
                "message_ko": "체크·기재 없이는 매물을 올릴 수 없습니다. 허위 체크는 제재 대상입니다. 코딩 지식은 필요 없고, 기능·데모·권리는 분명해야 합니다.",
            },
        },
        "credit_policy": {
            "doc": "TRUST.md · /guide/credit.html",
            "scale": {"min": 0, "max": 100, "base": database.CREDIT_BASE},
            "rules": database.CREDIT_RULES,
            "grades": [
                {"min": 90, "grade": "elite", "label": "최고"},
                {"min": 75, "grade": "great", "label": "우수"},
                {"min": 60, "grade": "trusted", "label": "신뢰"},
                {"min": 40, "grade": "normal", "label": "보통"},
                {"min": 20, "grade": "new", "label": "신규"},
                {"min": 0, "grade": "risk", "label": "주의"},
            ],
            "auto": True,
            "message_ko": database.CREDIT_RULES["note_ko"],
            "public_guide": "/guide/credit.html",
        },
        "buyer_rank_policy": database.buyer_rank_policy(),
    }


def _went_live_reveal_at() -> int:
    """Min completed deals before public hero shows the real count (else「추후 공개」)."""
    try:
        n = int(os.environ.get("WENT_LIVE_REVEAL_AT", "5") or "5")
    except ValueError:
        n = 5
    return max(1, min(n, 1000))


def _count_went_live(conn) -> int:
    """Deals that finished: sold/closed auction or buyer-accepted deal. Not bids alone."""
    row = conn.execute(
        """
        SELECT COUNT(*) AS c FROM projects
        WHERE COALESCE(auction_status, '') IN ('sold', 'closed')
           OR COALESCE(deal_status, '') = 'completed'
           OR (sold_at IS NOT NULL AND TRIM(sold_at) != '')
        """
    ).fetchone()
    return int(row["c"] or 0)


@router.get("/stats")
def public_stats():
    """Honest public counters for landing hero — no fabricated GMV/match rates.

    「다시 세상으로 나간」count is always tallied server-side; public JSON only
    exposes the number after WENT_LIVE_REVEAL_AT (default 5). Before that the
    hero shows「추후 공개」and count is omitted from the public payload.
    """
    reveal_at = _went_live_reveal_at()
    with database.db() as conn:
        projects_total = conn.execute(
            "SELECT COUNT(*) AS c FROM projects WHERE listing_status IN ('approved', 'pending')"
        ).fetchone()["c"]
        projects_approved = conn.execute(
            "SELECT COUNT(*) AS c FROM projects WHERE listing_status = 'approved'"
        ).fetchone()["c"]
        projects_pending = conn.execute(
            "SELECT COUNT(*) AS c FROM projects WHERE listing_status = 'pending'"
        ).fetchone()["c"]
        interests = conn.execute("SELECT COUNT(*) AS c FROM interests").fetchone()["c"]
        leads = conn.execute("SELECT COUNT(*) AS c FROM leads").fetchone()["c"]
        users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        verified = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE email_verified = 1"
        ).fetchone()["c"]
        went_live_raw = _count_went_live(conn)

    revealed = went_live_raw >= reveal_at
    went_live: dict[str, Any] = {
        "revealed": revealed,
        "reveal_at": reveal_at,
        "label_ko": "다시 세상으로 나간 프로젝트",
        "label_en": "Projects back in the world",
        "placeholder_ko": "추후 공개",
        "placeholder_en": "Coming later",
    }
    if revealed:
        went_live["count"] = went_live_raw
    # Before reveal: do not leak the real count in public stats

    visits = {"page_views": 0, "visitors": 0, "today_page_views": 0, "today_visitors": 0, "day": ""}
    try:
        with database.db() as conn:
            visits = database.get_site_visit_stats(conn)
    except Exception:
        pass

    return {
        "ok": True,
        "mode": "live_counts",
        "projects": int(projects_total),
        "projects_approved": int(projects_approved),
        "projects_pending": int(projects_pending),
        "interests": int(interests),
        "leads": int(leads),
        "users": int(users),
        "users_email_verified": int(verified),
        "listing_fee_krw": 0,
        "went_live": went_live,
        "visitors": int(visits.get("visitors") or 0),
        "page_views": int(visits.get("page_views") or 0),
        "today_visitors": int(visits.get("today_visitors") or 0),
        "today_page_views": int(visits.get("today_page_views") or 0),
        "visit_day": visits.get("day") or "",
        "labels": {
            "projects": "등록 매물",
            "interests": "관심 등록",
            "went_live": "다시 세상으로 나간 프로젝트",
            "listing_fee": "등록 비용",
            "visitors": "방문자",
            "page_views": "페이지뷰",
        },
    }


class VisitIn(BaseModel):
    visitor_key: str = Field(min_length=8, max_length=64)
    referrer: str = Field(default="", max_length=500)


_BOT_UA = re.compile(
    r"bot|crawl|spider|slurp|facebookexternalhit|preview|headless|wget|curl|python-requests|httpclient",
    re.I,
)

# Referrer hostname -> human channel label, for the footer "today visitors" source drilldown.
_REFERRER_CHANNELS = [
    (re.compile(r"reddit\.com$", re.I), "Reddit"),
    (re.compile(r"(twitter\.com|x\.com|t\.co)$", re.I), "X"),
    (re.compile(r"(google\.|googleusercontent\.com)", re.I), "Google"),
    (re.compile(r"naver\.com$", re.I), "Naver"),
    (re.compile(r"daum\.net$", re.I), "Daum"),
    (re.compile(r"instagram\.com$", re.I), "Instagram"),
    (re.compile(r"(facebook\.com|fb\.me)$", re.I), "Facebook"),
    (re.compile(r"(indiehackers\.com)$", re.I), "IndieHackers"),
    (re.compile(r"(news\.ycombinator\.com)$", re.I), "HackerNews"),
    (re.compile(r"kakao(corp|talk)?\.com$|kakao\.com$", re.I), "Kakao"),
    (re.compile(r"discord(app)?\.com$", re.I), "Discord"),
    (re.compile(r"youtube\.com$|youtu\.be$", re.I), "YouTube"),
]


def _normalize_referrer(referrer: str, own_host: str) -> str:
    referrer = (referrer or "").strip()
    if not referrer:
        return "Direct"
    try:
        host = urlparse(referrer).hostname or ""
    except ValueError:
        return "Other"
    host = host.lower()
    if not host:
        return "Other"
    if own_host and (host == own_host or host.endswith("." + own_host)):
        return "Direct"
    for pattern, label in _REFERRER_CHANNELS:
        if pattern.search(host):
            return label
    return host[:80]


@router.post("/visit")
def record_visit(body: VisitIn, request: Request):
    """Increment public visitor counters (footer). Dedupes unique visitors by key."""
    ua = (request.headers.get("user-agent") or "").strip()
    if ua and _BOT_UA.search(ua):
        with database.db() as conn:
            stats = database.get_site_visit_stats(conn)
        return {"ok": True, "bot": True, **stats}

    key = re.sub(r"[^A-Za-z0-9._-]", "", body.visitor_key.strip())[:64]
    if len(key) < 8:
        raise HTTPException(status_code=400, detail="invalid visitor_key")

    own_host = (request.headers.get("host") or "").split(":")[0].lower()
    source = _normalize_referrer(body.referrer, own_host)

    with database.db() as conn:
        stats = database.record_site_visit(conn, key, count_page_view=True, source=source)
    return {"ok": True, "bot": False, **stats}


@router.get("/visit")
def get_visit_stats():
    with database.db() as conn:
        stats = database.get_site_visit_stats(conn)
    return {"ok": True, **stats}


class FeedbackIn(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    contact: str = Field(default="", max_length=200)
    page: str = Field(default="", max_length=300)
    lang: str = Field(default="", max_length=8)
    hp: str = Field(default="", max_length=200)  # honeypot — bots fill hidden fields, humans don't


@router.post("/feedback")
def create_feedback(body: FeedbackIn, user: dict | None = Depends(get_optional_user)):
    """Private site feedback (non-member guestbook). Stored + emailed to the operator, never shown publicly."""
    if body.hp.strip():
        return {"ok": True}  # silently drop bot submissions, no error signal
    message = body.message.strip()
    if len(message) < 2:
        raise HTTPException(status_code=400, detail="message required")

    with database.db() as conn:
        fid = database.create_feedback(
            conn,
            message=message,
            contact=body.contact.strip(),
            page=body.page.strip(),
            lang=body.lang.strip(),
            user_id=(user or {}).get("id"),
        )

    try:
        contact_line = body.contact.strip() or (user or {}).get("email") or "(no contact given)"
        send_mail(
            "corelabs.studio@gmail.com",
            f"[WakeAgain feedback #{fid}]",
            f"Page: {body.page.strip() or '-'}\nContact: {contact_line}\n\n{message}",
        )
    except Exception:
        pass  # feedback is already saved; email is best-effort

    return {"ok": True, "id": fid}


@router.get("/admin/feedback")
def admin_list_feedback(status: str = "open", _: None = Depends(require_admin)):
    with database.db() as conn:
        items = database.list_feedback(conn, status=status)
        counts = database.count_feedback(conn)
    return {"ok": True, "feedback": items, "counts": counts}


@router.post("/admin/feedback/{feedback_id}/read")
def admin_mark_feedback_read(feedback_id: int, _: None = Depends(require_admin)):
    with database.db() as conn:
        found = database.mark_feedback_read(conn, feedback_id)
    if not found:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True}


@router.get("/admin/visit-sources")
def admin_visit_sources(day: str | None = None, _: None = Depends(require_admin)):
    """Referrer/channel breakdown for a given KST day (default today). Admin-only."""
    with database.db() as conn:
        result = database.get_site_visit_sources(conn, day)
    return {"ok": True, **result}


# --- auth ---


@router.post("/auth/register")
def register(body: RegisterIn, request: Request):
    email = body.email.strip().lower()
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="password min 8 chars")
    if not body.confirm_age_14:
        raise HTTPException(
            status_code=400,
            detail=f"만 {MIN_AGE_YEARS}세 이상임을 확인해 주세요.",
        )
    birth = _require_age_eligible(body.birth_date)
    birth_iso = birth.isoformat()
    with database.db() as conn:
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="email already registered")
        country_code = _normalize_country(body.country)
        cur = conn.execute(
            """
            INSERT INTO users (
              email, password_hash, display_name, birth_date, country,
              created_at, email_verified, role
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, 'both')
            """,
            (
                email,
                hash_password(body.password),
                body.display_name.strip(),
                birth_iso,
                country_code,
                database._now(),
            ),
        )
        user_id = int(cur.lastrowid)
        code = _issue_email_code(conn, user_id)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    user = database.user_to_dict(row)
    token = create_token(user["id"], user["email"])
    mail_meta = _deliver_verify_code(user["email"], code)
    _maybe_send_welcome_mail(
        user["id"],
        user["email"],
        user.get("display_name") or "",
        lang=_welcome_lang(country_code, request),
    )
    return _auth_payload(user, token, mail_meta=mail_meta)


@router.post("/auth/login")
def login(body: LoginIn):
    email = body.email.strip().lower()
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="invalid email or password")
        ph = row["password_hash"] or ""
        if str(ph).startswith("!oauth") or ph == oauth_mod.OAUTH_PASSWORD_PLACEHOLDER:
            # OAuth-only account
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "use_social_login",
                    "message": "소셜 로그인으로 가입한 계정입니다. 카카오·구글·깃허브로 로그인해 주세요.",
                    "oauth_provider": (row["oauth_provider"] if "oauth_provider" in row.keys() else None) or "",
                },
            )
        if not verify_password(body.password, ph):
            raise HTTPException(status_code=401, detail="invalid email or password")
        if "is_suspended" in row.keys() and int(row["is_suspended"] or 0):
            reason = (row["suspend_reason"] if "suspend_reason" in row.keys() else None) or ""
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "account_suspended",
                    "message": "정지된 계정입니다. 로그인할 수 없습니다. "
                    + (reason.strip() or "문의: corelabs.studio@gmail.com"),
                },
            )
        # re-issue code if not verified (convenient for returning users)
        mail_meta = None
        if not int(row["email_verified"] or 0):
            code = _issue_email_code(conn, int(row["id"]))
            row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
            mail_meta = _deliver_verify_code(row["email"], code)
    user = database.user_to_dict(row)
    token = create_token(user["id"], user["email"])
    return _auth_payload(user, token, mail_meta=mail_meta)


class BirthDateIn(BaseModel):
    birth_date: str = Field(min_length=8, max_length=12)
    confirm_age_14: bool = False


@router.put("/me/birth-date")
def set_birth_date(body: BirthDateIn, user: dict = Depends(get_current_user)):
    """SNS 가입 후 만 14세 확인 — 생년월일 1회 등록."""
    if not body.confirm_age_14:
        raise HTTPException(
            status_code=400,
            detail=f"만 {MIN_AGE_YEARS}세 이상임을 확인해 주세요.",
        )
    birth = _require_age_eligible(body.birth_date)
    with database.db() as conn:
        conn.execute(
            "UPDATE users SET birth_date = ?, profile_updated_at = ? WHERE id = ?",
            (birth.isoformat(), database._now(), user["id"]),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return {"ok": True, "user": database.user_to_dict(row)}


def _oauth_upsert_user(conn, provider: str, profile: dict) -> tuple[Any, bool]:
    """Returns (user_row, is_new_signup)."""
    subject = (profile.get("subject") or "").strip()
    if not subject:
        raise HTTPException(status_code=400, detail="oauth subject missing")
    email = (profile.get("email") or "").strip().lower()
    if not email:
        email = f"{provider}_{subject}@oauth.wakeagain.local"
    display = (profile.get("display_name") or "").strip()[:80]
    verified = 1 if profile.get("email_verified") else 0
    # Prefer oauth identity match
    row = conn.execute(
        "SELECT * FROM users WHERE oauth_provider = ? AND oauth_subject = ?",
        (provider, subject),
    ).fetchone()
    if row:
        if "is_suspended" in row.keys() and int(row["is_suspended"] or 0):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "account_suspended",
                    "message": "정지된 계정입니다.",
                },
            )
        # refresh display if empty
        if display and not (row["display_name"] or "").strip():
            conn.execute(
                "UPDATE users SET display_name = ? WHERE id = ?",
                (display, row["id"]),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
        return row, False

    by_email = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if by_email:
        if "is_suspended" in by_email.keys() and int(by_email["is_suspended"] or 0):
            raise HTTPException(status_code=403, detail={"code": "account_suspended", "message": "정지된 계정입니다."})
        # Link SNS to existing email account
        conn.execute(
            """
            UPDATE users
            SET oauth_provider = ?, oauth_subject = ?,
                email_verified = CASE WHEN ? = 1 THEN 1 ELSE email_verified END,
                display_name = CASE
                  WHEN display_name IS NULL OR display_name = '' THEN ?
                  ELSE display_name END
            WHERE id = ?
            """,
            (provider, subject, verified, display or None, by_email["id"]),
        )
        return conn.execute("SELECT * FROM users WHERE id = ?", (by_email["id"],)).fetchone(), False

    cur = conn.execute(
        """
        INSERT INTO users (
          email, password_hash, display_name, created_at, email_verified, role,
          oauth_provider, oauth_subject, credit_score
        ) VALUES (?, ?, ?, ?, ?, 'both', ?, ?, 50)
        """,
        (
            email,
            oauth_mod.OAUTH_PASSWORD_PLACEHOLDER,
            display,
            database._now(),
            verified,
            provider,
            subject,
        ),
    )
    uid = int(cur.lastrowid)
    row = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    return row, True


@router.get("/auth/oauth/{provider}/start")
def oauth_start(provider: str):
    p = (provider or "").lower().strip()
    if p not in oauth_mod.PROVIDERS:
        raise HTTPException(status_code=404, detail="unknown provider")
    if not oauth_mod.provider_config(p):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "oauth_not_configured",
                "message": f"{p} 로그인이 아직 설정되지 않았습니다. 운영자가 클라이언트 ID를 등록해야 합니다.",
                "provider": p,
            },
        )
    try:
        url, _state = oauth_mod.authorize_url(p)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/auth/oauth/{provider}/callback")
async def oauth_callback(
    request: Request,
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    p = (provider or "").lower().strip()
    app_err = f"{oauth_mod.public_base()}/app/?oauth_error="
    if error:
        return RedirectResponse(app_err + "denied", status_code=302)
    if not code or not state:
        return RedirectResponse(app_err + "missing_code", status_code=302)
    if p not in oauth_mod.PROVIDERS or not oauth_mod.provider_config(p):
        return RedirectResponse(app_err + "not_configured", status_code=302)
    try:
        oauth_mod.parse_state(state, p)
    except ValueError:
        return RedirectResponse(app_err + "bad_state", status_code=302)
    try:
        profile = await oauth_mod.exchange_code(p, code)
    except Exception:
        return RedirectResponse(app_err + "token_failed", status_code=302)
    try:
        with database.db() as conn:
            row, is_new = _oauth_upsert_user(conn, p, profile)
            user = database.user_to_dict(row)
            token = create_token(user["id"], user["email"])
    except HTTPException as e:
        code_s = "suspended" if getattr(e, "status_code", 0) == 403 else "failed"
        return RedirectResponse(app_err + code_s, status_code=302)
    if is_new:
        _maybe_send_welcome_mail(
            user["id"],
            user["email"],
            user.get("display_name") or "",
            lang=_welcome_lang(user.get("country"), request),
        )
    # Hand token to app shell (query — cleaned by JS)
    from urllib.parse import quote

    dest = (
        f"{oauth_mod.public_base()}/app/?wa_token={quote(token, safe='')}"
        f"&oauth={quote(p, safe='')}#list"
    )
    return RedirectResponse(dest, status_code=302)


@router.post("/auth/verify-email")
def verify_email(body: VerifyEmailIn, user: dict = Depends(get_current_user)):
    code = body.code.strip().replace(" ", "")
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="user not found")
        if int(row["email_verified"] or 0):
            return {"ok": True, "user": database.user_to_dict(row), "already": True}
        stored = row["email_code_hash"] or ""
        expires = row["email_code_expires"] or ""
        if not stored or not expires:
            raise HTTPException(status_code=400, detail="no verification code — request a new one")
        try:
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp_dt.astimezone(timezone.utc):
                raise HTTPException(status_code=400, detail="verification code expired")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail="invalid code expiry") from e
        if _hash_code(code) != stored:
            raise HTTPException(status_code=400, detail="invalid verification code")
        conn.execute(
            """
            UPDATE users
            SET email_verified = 1, email_code_hash = NULL, email_code_expires = NULL
            WHERE id = ?
            """,
            (user["id"],),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return {"ok": True, "user": database.user_to_dict(row)}


def _client_ip(request: Request) -> str:
    """Prefer first X-Forwarded-For hop (Railway proxy), else direct peer."""
    xff = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if xff:
        return xff
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _rate_limit_find_email(request: Request) -> None:
    """In-process sliding window. Multi-worker deploy may soft-limit per process."""
    import time

    ip = _client_ip(request)
    now = time.time()
    window = float(FIND_EMAIL_RATE_WINDOW_SEC)
    hits = [t for t in _find_email_hits.get(ip, []) if now - t < window]
    if len(hits) >= FIND_EMAIL_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=(
                f"요청이 너무 많습니다. {FIND_EMAIL_RATE_WINDOW_SEC // 60}분 후 "
                "다시 시도해 주세요."
            ),
        )
    hits.append(now)
    _find_email_hits[ip] = hits
    # Bound map size (simple GC of stale keys)
    if len(_find_email_hits) > 5000:
        stale = [k for k, v in _find_email_hits.items() if not v or now - v[-1] >= window]
        for k in stale[:2000]:
            _find_email_hits.pop(k, None)


@router.post("/auth/find-email")
def find_email(body: FindEmailIn, request: Request):
    """실명·휴대폰으로 가입 이메일 힌트(마스킹만)를 반환. 원문 이메일은 노출하지 않음."""
    _rate_limit_find_email(request)
    try:
        phone = database.validate_phone(body.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    real_name = (body.real_name or "").strip()
    if len(real_name) < 2:
        raise HTTPException(status_code=400, detail="real_name required")

    with database.db() as conn:
        # 실명+휴대폰 둘 다 일치해야 함 (열거·피싱 완화)
        rows = conn.execute(
            """
            SELECT email FROM users
            WHERE phone = ? AND TRIM(real_name) = ?
            ORDER BY id ASC
            LIMIT 5
            """,
            (phone, real_name),
        ).fetchall()

    if not rows:
        return {
            "ok": True,
            "found": False,
            "message": (
                "일치하는 계정을 찾지 못했습니다. "
                "프로필에 등록한 실명·휴대폰을 확인하거나, "
                "아직 실명·휴대폰을 넣지 않았다면 가입 이메일을 직접 입력해 주세요."
            ),
        }

    emails = [str(r["email"] or "").strip() for r in rows if r["email"]]
    emails = [e for e in emails if e]
    if not emails:
        return {
            "ok": True,
            "found": False,
            "message": "일치하는 계정을 찾지 못했습니다.",
        }

    masked = [database.mask_email_public(e) for e in emails]
    primary_masked = masked[0]
    return {
        "ok": True,
        "found": True,
        # 원문 이메일 비노출 (구 클라이언트 호환 필드도 마스킹만)
        "email": primary_masked,
        "email_masked": primary_masked,
        "emails": masked if len(masked) > 1 else None,
        "emails_masked": masked if len(masked) > 1 else None,
        "full_email_revealed": False,
        "message": (
            "가입 이메일 힌트를 찾았습니다. "
            "개인정보 보호를 위해 일부만 표시합니다. "
            "기억나는 전체 주소로 로그인해 주세요."
        ),
    }


@router.post("/auth/password-reset/request")
def password_reset_request(body: PasswordResetRequestIn):
    email = body.email.strip().lower()
    mail_meta: dict[str, Any] | None = None
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            code = _new_email_code()
            conn.execute(
                "UPDATE users SET reset_code_hash = ?, reset_code_expires = ? WHERE id = ?",
                (_hash_code(code), _code_expiry_iso(), row["id"]),
            )
            mail_meta = _deliver_reset_code(email, code)
    # Always ok (no email enumeration)
    out: dict[str, Any] = {
        "ok": True,
        "message": "등록된 이메일이면 재설정 코드를 발급했습니다.",
        # Always surface SMTP status so UI can explain missing mail (no user leak)
        "email_configured": smtp_configured(),
        "email_sent": bool(mail_meta and mail_meta.get("email_sent")),
    }
    if mail_meta:
        # Never leak codes unless EMAIL_DEV_MODE or EMAIL_CODE_FALLBACK already set them
        for k, v in mail_meta.items():
            if v is None:
                continue
            if k == "dev_email_code" and not (EMAIL_DEV_MODE or EMAIL_CODE_FALLBACK):
                continue
            out[k] = v
    elif not smtp_configured():
        if EMAIL_DEV_MODE or EMAIL_CODE_FALLBACK:
            out["warning"] = (
                "메일 서버(SMTP)가 아직 연결되지 않았습니다. "
                "계정이 있다면 화면에 코드가 표시됩니다. "
                "코드가 없으면 가입 이메일을 확인하거나 새로 가입해 주세요."
            )
        else:
            out["warning"] = (
                "메일 서버가 일시적으로 연결되지 않았습니다. "
                "잠시 후 다시 시도해 주세요."
            )
    return out


@router.post("/auth/password-reset/confirm")
def password_reset_confirm(body: PasswordResetConfirmIn):
    email = body.email.strip().lower()
    code = body.code.strip().replace(" ", "")
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not row or not row["reset_code_hash"]:
            raise HTTPException(status_code=400, detail="invalid or expired code")
        expires = row["reset_code_expires"] or ""
        try:
            exp_dt = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp_dt.astimezone(timezone.utc):
                raise HTTPException(status_code=400, detail="code expired")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail="invalid code") from e
        if _hash_code(code) != row["reset_code_hash"]:
            raise HTTPException(status_code=400, detail="invalid code")
        conn.execute(
            """
            UPDATE users
            SET password_hash = ?, reset_code_hash = NULL, reset_code_expires = NULL
            WHERE id = ?
            """,
            (hash_password(body.new_password), row["id"]),
        )
    return {"ok": True, "message": "비밀번호가 변경되었습니다. 로그인해 주세요."}


@router.post("/auth/resend-verify")
def resend_verify(user: dict = Depends(get_current_user)):
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="user not found")
        if int(row["email_verified"] or 0):
            return {"ok": True, "already": True, "user": database.user_to_dict(row)}
        code = _issue_email_code(conn, user["id"])
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        email = row["email"]
    mail_meta = _deliver_verify_code(email, code)
    out: dict[str, Any] = {"ok": True, "user": database.user_to_dict(row)}
    out.update({k: v for k, v in mail_meta.items() if v is not None})
    if mail_meta.get("email_sent"):
        out["message"] = "인증 메일을 다시 보냈습니다. 받은편지함·스팸함을 확인해 주세요."
    elif mail_meta.get("dev_email_code"):
        out["message"] = "코드를 다시 발급했습니다. (메일 미연결 시 화면에 표시)"
    else:
        out["message"] = mail_meta.get("warning") or "코드를 발급했습니다."
    return out


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    # refresh from DB for latest trust
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="user not found")
    return {"ok": True, "user": database.user_to_dict(row)}


@router.put("/me/profile")
def update_profile(body: ProfileIn, user: dict = Depends(get_current_user)):
    if not user.get("trust", {}).get("email_verified"):
        # re-read in case stale
        with database.db() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        fresh = database.user_to_dict(row)
        if not fresh["trust"]["email_verified"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "email_unverified",
                    "message": "이메일 인증 후 프로필을 저장할 수 있습니다.",
                    "trust": fresh["trust"],
                },
            )
    try:
        phone = database.validate_phone(body.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    real_name = body.real_name.strip()
    if len(real_name) < 2:
        raise HTTPException(status_code=400, detail="real_name required")
    display = (body.display_name or "").strip() or real_name
    country = _normalize_country(body.country)
    now = database._now()
    with database.db() as conn:
        conn.execute(
            """
            UPDATE users
            SET real_name = ?, phone = ?, role = ?, display_name = ?,
                country = COALESCE(NULLIF(?, ''), country), profile_updated_at = ?
            WHERE id = ?
            """,
            (real_name, phone, body.role, display, country, now, user["id"]),
        )
        database.recompute_user_credit(conn, int(user["id"]))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return {"ok": True, "user": database.user_to_dict(row)}


@router.put("/me/settlement")
def update_settlement(body: SettlementIn, user: dict = Depends(get_current_user)):
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        fresh = database.user_to_dict(row)
        if not fresh["trust"]["profile_complete"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "profile_incomplete",
                    "message": "신원 프로필(실명·휴대폰)을 먼저 완성해 주세요.",
                    "trust": fresh["trust"],
                },
            )
        account = body.account.strip().replace(" ", "").replace("-", "")
        if len(account) < 8:
            raise HTTPException(status_code=400, detail="account too short")
        account_stored = database.encrypt_settlement_account(account)
        conn.execute(
            """
            UPDATE users
            SET settlement_bank = ?, settlement_holder = ?, settlement_account = ?,
                is_business = ?, profile_updated_at = ?
            WHERE id = ?
            """,
            (
                body.bank.strip(),
                body.holder.strip(),
                account_stored,
                1 if body.is_business else 0,
                database._now(),
                user["id"],
            ),
        )
        database.recompute_user_credit(conn, int(user["id"]))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return {"ok": True, "user": database.user_to_dict(row)}


@router.put("/me/seller-identity")
def update_seller_identity(body: SellerIdentityIn, user: dict = Depends(get_current_user)):
    """
    판매자 공개 신원 — 매물 상세에서 구매자가 확인.
    통신판매중개자로서 판매자 특정 가능 정보를 제공하기 위함.
    """
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        fresh = database.user_to_dict(row)
        if not fresh["trust"]["profile_complete"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "profile_incomplete",
                    "message": "실명·휴대폰 프로필(Lv2)을 먼저 완성해 주세요.",
                    "trust": fresh["trust"],
                },
            )
        try:
            phone = database.validate_phone(body.contact_phone)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        trade = body.trade_name.strip()
        trade_en = (body.trade_name_en or "").strip()
        ceo = (body.ceo_name or "").strip()
        biz = re.sub(r"\D", "", body.business_reg_no or "")
        mail_order = (body.mail_order_report_no or "").strip()
        addr = (body.address or "").strip()
        if body.seller_type == "business":
            if len(ceo) < 2:
                raise HTTPException(status_code=400, detail="사업자는 대표자 성명을 입력해 주세요.")
            if len(biz) < 10:
                raise HTTPException(
                    status_code=400,
                    detail="사업자등록번호 10자리를 입력해 주세요.",
                )
            if not addr or len(addr) < 5:
                raise HTTPException(
                    status_code=400,
                    detail="사업자는 사업장 주소를 입력해 주세요.",
                )
        else:
            # individual: trade_name is public name (often same as real_name)
            ceo = ""
            biz = ""
        conn.execute(
            """
            UPDATE users SET
              seller_type = ?,
              seller_trade_name = ?,
              seller_trade_name_en = ?,
              seller_ceo_name = ?,
              seller_biz_no = ?,
              seller_mail_order_no = ?,
              seller_contact_email = ?,
              seller_contact_phone = ?,
              seller_address = ?,
              seller_identity_at = ?,
              profile_updated_at = ?
            WHERE id = ?
            """,
            (
                body.seller_type,
                trade,
                trade_en,
                ceo,
                biz,
                mail_order,
                str(body.contact_email).strip().lower(),
                phone,
                addr,
                database._now(),
                database._now(),
                user["id"],
            ),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return {
        "ok": True,
        "user": database.user_to_dict(row),
        "public_preview": database.public_seller_identity(row),
    }


# --- projects + public live auctions ---


def _auction_end_iso(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).astimezone().isoformat(timespec="seconds")


def _refresh_auction_ended(conn, row) -> Any:
    """Run global expiry pass then re-fetch row (auto-sold on highest bid)."""
    try:
        database.process_expired_auctions(conn)
    except Exception:
        pass
    if not row:
        return row
    fresh = conn.execute("SELECT * FROM projects WHERE id = ?", (row["id"],)).fetchone()
    return fresh or row


@router.get("/auctions/live")
def auctions_live(user: dict | None = Depends(get_optional_user)):
    """
    Public live board — anyone on the site can see current prices rising.
    Designed for short-interval polling (auth optional; logged-in users hide blocked).
    """
    with database.db() as conn:
        hidden = database.blocked_owner_ids(conn, user["id"] if user else None)
        hide_sql = ""
        hide_params: list[Any] = []
        if hidden:
            placeholders = ",".join("?" * len(hidden))
            hide_sql = f" AND owner_id NOT IN ({placeholders})"
            hide_params = list(sorted(hidden))
        live_where = database.public_live_where_sql("p")
        # hide_sql uses owner_id → qualify as p.owner_id
        hide_sql_p = hide_sql.replace("owner_id", "p.owner_id") if hide_sql else ""
        score_sql = database.listing_trust_score_sql("p", "u")
        rows = conn.execute(
            f"""
            SELECT p.*, u.country AS seller_country, ({score_sql}) AS exposure_score
            FROM projects p
            LEFT JOIN users u ON u.id = p.owner_id
            WHERE {live_where}
              {hide_sql_p}
            {database.listing_sort_sql("p", "u")}
            LIMIT 50
            """,
            [*hide_params, database._now()],
        ).fetchall()
        snaps = []
        for r in rows:
            seller_country = (r["seller_country"] if "seller_country" in r.keys() else None) or ""
            r = _refresh_auction_ended(conn, r)
            # Expiry may have archived this row mid-poll
            if (r["listing_status"] or "") != "approved" or (
                (r["auction_status"] or "live") != "live"
            ):
                continue
            top = None
            try:
                if int(r["bid_count"] or 0) > 0:
                    top = database.top_bid_public(conn, int(r["id"]))
            except Exception:
                top = None
            snap = database.auction_snapshot(r, top_bid=top)
            snap["seller_country"] = seller_country
            snaps.append(snap)
        # recent public bid ticker (last 20 across board) — live rounds only
        recent_sql = """
            SELECT b.*, u.display_name,
                   COALESCE(u.credit_bought, 0) AS credit_bought,
                   COALESCE(u.credit_defaults, 0) AS credit_defaults
            FROM bids b
            JOIN users u ON u.id = b.bidder_id
            JOIN projects p ON p.id = b.project_id
            WHERE p.listing_status = 'approved'
              AND COALESCE(p.auction_status, 'live') = 'live'
            """
        recent_params: list[Any] = []
        if hidden:
            placeholders = ",".join("?" * len(hidden))
            recent_sql += f" AND p.owner_id NOT IN ({placeholders})"
            recent_params = list(sorted(hidden))
        recent_sql += " ORDER BY b.id DESC LIMIT 20"
        recent = conn.execute(recent_sql, recent_params).fetchall()
        ticker = [database.bid_to_public(b) for b in recent]
    return {
        "ok": True,
        "server_time": database._now(),
        "poll_seconds": 4,
        "auctions": snaps,
        "ticker": ticker,
        "public": True,
        "note": "입찰 중 현재가는 전원 공개입니다.",
    }


@router.get("/projects")
def list_projects(
    mine: bool = False,
    limit: int = 24,
    offset: int = 0,
    q: str = "",
    user: dict | None = Depends(get_optional_user),
):
    lim = max(1, min(int(limit or 24), 100))
    off = max(0, int(offset or 0))
    # Buyer/seller search: title · one_liner · story · features · audience · keywords · product_type
    q_raw = (q or "").strip()
    q_term = q_raw[:80] if q_raw else ""
    like = f"%{q_term}%" if q_term else None
    search_sql = (
        "("
        "title LIKE ? OR one_liner LIKE ? OR IFNULL(story,'') LIKE ? "
        "OR IFNULL(features_json,'') LIKE ? OR IFNULL(audience,'') LIKE ? "
        "OR IFNULL(works_now,'') LIKE ? "
        "OR IFNULL(keywords_json,'') LIKE ? OR IFNULL(product_type,'') LIKE ?"
        ")"
        if like
        else ""
    )
    search_like_params = 8  # keep in sync with search_sql placeholders

    with database.db() as conn:
        database.process_expired_auctions(conn)
        if mine:
            if not user:
                raise HTTPException(status_code=401, detail="auth required")
            where = "owner_id = ?"
            params: list[Any] = [user["id"]]
            if like:
                where += " AND " + search_sql
                params.extend([like] * search_like_params)
            total = conn.execute(
                f"SELECT COUNT(*) AS c FROM projects WHERE {where}",
                params,
            ).fetchone()["c"]
            rows = conn.execute(
                f"""
                SELECT * FROM projects WHERE {where}
                ORDER BY id DESC LIMIT ? OFFSET ?
                """,
                (*params, lim, off),
            ).fetchall()
            if listing_i18n.ensure_rows_en(conn, rows):
                rows = conn.execute(
                    f"""
                    SELECT * FROM projects WHERE {where}
                    ORDER BY id DESC LIMIT ? OFFSET ?
                    """,
                    (*params, lim, off),
                ).fetchall()
            projects = [database.project_to_dict(r, include_private=True) for r in rows]
            return {
                "ok": True,
                "projects": projects,
                "total": int(total),
                "limit": lim,
                "offset": off,
                "has_more": off + len(projects) < int(total),
                "q": q_term,
            }
        # Public marketplace: live round only · trust score DESC · then round queue
        where = database.public_live_where_sql("p")
        params: list[Any] = []
        # search_sql uses unqualified columns — prefix with p.
        search_sql_p = search_sql.replace("(", "(p.").replace(" OR ", " OR p.") if like else ""
        # safer: rebuild from known fields
        if like:
            search_sql_p = (
                "(p.title LIKE ? OR p.one_liner LIKE ? OR IFNULL(p.story,'') LIKE ? "
                "OR IFNULL(p.features_json,'') LIKE ? OR IFNULL(p.audience,'') LIKE ? "
                "OR IFNULL(p.works_now,'') LIKE ? "
                "OR IFNULL(p.keywords_json,'') LIKE ? OR IFNULL(p.product_type,'') LIKE ?)"
            )
            where += " AND " + search_sql_p
            params.extend([like] * search_like_params)
        hidden_owners = database.blocked_owner_ids(conn, user["id"] if user else None)
        if hidden_owners:
            placeholders = ",".join("?" * len(hidden_owners))
            where += f" AND p.owner_id NOT IN ({placeholders})"
            params.extend(sorted(hidden_owners))
        total = conn.execute(
            f"""
            SELECT COUNT(*) AS c FROM projects p WHERE {where}
            """,
            params,
        ).fetchone()["c"]
        now = database._now()
        score_sql = database.listing_trust_score_sql("p", "u")
        rows = conn.execute(
            f"""
            SELECT p.*, u.country AS seller_country, ({score_sql}) AS exposure_score
            FROM projects p
            LEFT JOIN users u ON u.id = p.owner_id
            WHERE {where}
            {database.listing_sort_sql("p", "u")}
            LIMIT ? OFFSET ?
            """,
            (*params, now, lim, off),
        ).fetchall()
        if listing_i18n.ensure_rows_en(conn, rows):
            rows = conn.execute(
                f"""
                SELECT p.*, u.country AS seller_country, ({score_sql}) AS exposure_score
                FROM projects p
                LEFT JOIN users u ON u.id = p.owner_id
                WHERE {where}
                {database.listing_sort_sql("p", "u")}
                LIMIT ? OFFSET ?
                """,
                (*params, now, lim, off),
            ).fetchall()
        projects = [database.project_to_dict(r, include_private=False) for r in rows]
        for proj, r in zip(projects, rows):
            proj["seller_country"] = (r["seller_country"] if "seller_country" in r.keys() else None) or ""
    return {
        "ok": True,
        "projects": projects,
        "total": int(total),
        "limit": lim,
        "offset": off,
        "has_more": off + len(projects) < int(total),
        "q": q_term,
    }


@router.post("/projects/suggest-keywords")
def suggest_project_keywords(
    body: KeywordSuggestIn,
    user: dict = Depends(get_current_user),
):
    """AI (SpaceXAI/xAI if keyed) or heuristic keyword suggestions for listing form."""
    _ = user  # auth required — avoid anonymous spam of AI calls
    if not (body.title or "").strip() and not (body.one_liner or "").strip():
        raise HTTPException(
            status_code=400,
            detail={
                "code": "title_or_oneliner_required",
                "message": "키워드 추천을 위해 제목 또는 한 줄 소개를 먼저 적어 주세요.",
            },
        )
    kws, source = kw_mod.suggest_keywords_ai(
        title=body.title or "",
        one_liner=body.one_liner or "",
        story=body.story or "",
        product_type=body.product_type or "",
        lang=body.lang or "ko",
    )
    return {
        "ok": True,
        "keywords": kws,
        "source": source,
        "max": kw_mod.MAX_KEYWORDS,
        "note": (
            "AI 추천입니다. 수정·삭제 후 직접 입력도 가능합니다."
            if source == "ai"
            else "자동 추천입니다. 수정·삭제 후 직접 입력도 가능합니다."
        ),
    }


@router.get("/projects/{project_id}")
def get_project(
    project_id: int,
    user: dict | None = Depends(get_optional_user),
):
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        row = _refresh_auction_ended(conn, row)
        # Block relationship: treat as not found for non-owners
        if user and int(user["id"]) != int(row["owner_id"]):
            if database.is_blocked_either(conn, user["id"], row["owner_id"]):
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "blocked",
                        "message": "차단된 사용자의 매물입니다.",
                    },
                )
        changed_basic = listing_i18n.ensure_rows_en(conn, [row])
        changed_long = listing_i18n.ensure_rows_i18n(conn, [row])
        if changed_basic or changed_long:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    private = bool(user and user["id"] == row["owner_id"])
    # Non-owners: live round (public board) or sold (deal transparency).
    # Archived/ended/pending/hold/rejected are not public permanent display.
    # Deal parties (buyer) may always open their deal — including payment_default /
    # inspection / completed — so 미입금·인수 화면이 404로 끊기지 않음.
    if not private:
        ls = (row["listing_status"] or "") or ""
        ast = (row["auction_status"] if "auction_status" in row.keys() else None) or "live"
        deal_st = (
            (row["deal_status"] if "deal_status" in row.keys() else None) or ""
        )
        is_buyer = bool(
            user
            and row["buyer_id"] is not None
            and int(user["id"]) == int(row["buyer_id"])
        )
        public_ok = (ls == "approved" and ast == "live") or (
            ast == "sold" and ls in ("approved", "sold", "archived")
        )
        if is_buyer and (
            ast == "sold"
            or deal_st
            in (
                "awaiting_payment",
                "paid",
                "inspection",
                "completed",
                "disputed",
                "payment_default",
            )
            or (ast == "ended" and deal_st)
        ):
            public_ok = True
        if not public_ok:
            raise HTTPException(status_code=404, detail="not found")
    project = database.project_to_dict(row, include_private=private)
    with database.db() as conn:
        listed = conn.execute(
            "SELECT COUNT(*) AS c FROM projects WHERE owner_id = ? AND listing_status = 'approved'",
            (row["owner_id"],),
        ).fetchone()["c"]
        sold = conn.execute(
            "SELECT COUNT(*) AS c FROM projects WHERE owner_id = ? AND auction_status = 'sold'",
            (row["owner_id"],),
        ).fetchone()["c"]
        u = conn.execute(
            "SELECT * FROM users WHERE id = ?", (row["owner_id"],)
        ).fetchone()
    credit = database.public_credit_summary(u) if u else None
    try:
        project["exposure"] = database.compute_listing_exposure_score(row, u)
        project["exposure_score"] = project["exposure"]["score"]
    except Exception:
        pass
    # 전체 연락처: 판매자 본인 또는 성사 매물의 낙찰 구매자만
    reveal_contact = False
    if user and u:
        uid = int(user["id"])
        if uid == int(row["owner_id"]):
            reveal_contact = True
        else:
            buyer_id = row["buyer_id"] if "buyer_id" in row.keys() else None
            astatus = (row["auction_status"] if "auction_status" in row.keys() else None) or ""
            if buyer_id and astatus == "sold" and int(buyer_id) == uid:
                reveal_contact = True
    identity = (
        database.public_seller_identity(u, reveal_contact=reveal_contact) if u else None
    )
    project["seller_country"] = (u["country"] if u and "country" in u.keys() else "") or ""
    project["seller"] = {
        "owner_id": row["owner_id"],
        "display_name": (u["display_name"] if u else "") or "판매자",
        "approved_listings": int(listed),
        "sold_count": int(sold),
        "credit": credit,
        # 구매자 확인용 — 통신판매중개 정보 제공 의무
        "identity": identity,
        "identity_disclosed": bool(identity),
        "contact_revealed": bool(reveal_contact and identity),
    }
    # Handover checklist: seller + buyer only, after sale
    astatus = (row["auction_status"] if "auction_status" in row.keys() else None) or ""
    buyer_id = row["buyer_id"] if "buyer_id" in row.keys() else None
    is_party = bool(
        user
        and (
            int(user["id"]) == int(row["owner_id"])
            or (buyer_id is not None and int(user["id"]) == int(buyer_id))
        )
    )
    if is_party and (astatus == "sold" or (row["sold_at"] if "sold_at" in row.keys() else None)):
        with database.db() as conn2:
            row2 = conn2.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            if row2:
                _, ho = database.ensure_handover_checklist(conn2, row2)
                project["handover_checklist"] = ho
    else:
        project["handover_checklist"] = None
    return {"ok": True, "project": project}


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, user: dict = Depends(get_current_user)):
    """Seller self-service delete — fixes a mistaken listing. Blocked once a bid
    has landed or a deal is in progress, so a winning bidder can't be yanked out
    from under them; use admin review (반려) for those cases instead."""
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if int(row["owner_id"]) != int(user["id"]):
            raise HTTPException(status_code=403, detail="not your listing")
        if int(row["bid_count"] or 0) > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "has_bids",
                    "message": "이미 입찰이 들어온 매물은 삭제할 수 없습니다. 문의로 처리해 주세요.",
                },
            )
        deal_status = (row["deal_status"] if "deal_status" in row.keys() else None) or ""
        if deal_status:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "deal_in_progress",
                    "message": "진행 중인 거래가 있는 매물은 삭제할 수 없습니다.",
                },
            )
        conn.execute("DELETE FROM bids WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM messages WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM reports WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM fee_invoices WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    return {"ok": True}


@router.get("/projects/{project_id}/certificate")
def get_deal_certificate(
    project_id: int,
    kind: str = "auto",
    user: dict = Depends(get_current_user),
):
    """
    Transaction / award record confirmation for seller and buyer (same document).
    kind=award | complete | auto (complete if done else award).
    """
    with database.db() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")

        owner_id = int(row["owner_id"])
        buyer_raw = row["buyer_id"] if "buyer_id" in row.keys() else None
        buyer_id = int(buyer_raw) if buyer_raw is not None else None
        uid = int(user["id"])
        if uid != owner_id and (buyer_id is None or uid != buyer_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "certificate_parties_only",
                    "message": "거래 기록 확인서는 해당 매물의 판매자·구매자만 볼 수 있습니다.",
                },
            )

        astatus = (row["auction_status"] or "") or ""
        if astatus != "sold" and not (row["sold_at"] if "sold_at" in row.keys() else None):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "not_sold",
                    "message": "아직 낙찰·성사 기록이 없습니다.",
                },
            )

        k = (kind or "auto").strip().lower()
        if k == "auto":
            k = "complete" if database.deal_is_complete_row(row) else "award"
        if k not in ("award", "complete"):
            raise HTTPException(status_code=400, detail="kind must be award, complete, or auto")

        try:
            cert = database.build_deal_certificate(
                conn, row, kind=k, viewer_id=uid
            )
        except ValueError as e:
            code = str(e)
            if code == "not_complete":
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "not_complete",
                        "message": "거래 절차 완료 전이므로 「거래 기록 확인서」는 아직 발급할 수 없습니다. 낙찰 기록 확인서를 이용해 주세요.",
                    },
                ) from e
            if code == "not_sold":
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "not_sold",
                        "message": "아직 낙찰·성사 기록이 없습니다.",
                    },
                ) from e
            raise HTTPException(status_code=400, detail=code) from e

    return cert


@router.get("/projects/{project_id}/bids")
def list_bids(project_id: int):
    """Public bid history for a listing — amounts visible to everyone."""
    with database.db() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="not found")
        rows = conn.execute(
            """
            SELECT b.*, u.display_name,
                   COALESCE(u.credit_bought, 0) AS credit_bought,
                   COALESCE(u.credit_defaults, 0) AS credit_defaults
            FROM bids b
            JOIN users u ON u.id = b.bidder_id
            WHERE b.project_id = ?
            ORDER BY b.amount DESC, b.id DESC
            LIMIT 100
            """,
            (project_id,),
        ).fetchall()
    bids = []
    for i, r in enumerate(rows):
        pub = database.bid_to_public(r)
        pub["rank"] = i + 1
        pub["is_top"] = i == 0
        bids.append(pub)
    return {
        "ok": True,
        "project_id": project_id,
        "bids": bids,
        "top_bidder": bids[0] if bids else None,
        "public": True,
        "note_ko": "입찰 금액·공개 닉네임·구매 배지는 전원에게 공개됩니다. 이메일·실명·연락처는 비공개입니다.",
    }


@router.post("/projects/{project_id}/report")
def report_project(
    project_id: int,
    body: ReportIn,
    user: dict = Depends(get_current_user),
):
    """
    Buyer-side quality report (low quality / plagiarism / not working / fraud).
    Requires Lv2. One report per user per project.
    Thresholds auto-pause auction / suspend seller account.
    """
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    fresh = database.user_to_dict(row_u)
    if not fresh["trust"].get("can_report"):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "trust_required",
                "message": "신고는 실명·휴대폰 확인(Lv2) 후 가능합니다.",
                "trust": fresh["trust"],
            },
        )
    if body.reason not in database.REPORT_REASONS:
        raise HTTPException(status_code=400, detail="invalid reason")

    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if row["listing_status"] not in ("approved", "hold"):
            raise HTTPException(status_code=400, detail="이 매물은 신고할 수 없는 상태입니다.")
        if int(row["owner_id"]) == int(user["id"]):
            raise HTTPException(status_code=400, detail="본인 매물은 신고할 수 없습니다.")
        if database.is_blocked_either(conn, user["id"], row["owner_id"]):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "blocked",
                    "message": "차단된 사용자와는 신고할 수 없습니다. (차단을 먼저 해제하세요)",
                },
            )

        exists = conn.execute(
            "SELECT id FROM reports WHERE project_id = ? AND reporter_id = ?",
            (project_id, user["id"]),
        ).fetchone()
        if exists:
            raise HTTPException(
                status_code=409,
                detail="이미 이 매물을 신고하셨습니다. (매물당 1회)",
            )

        conn.execute(
            """
            INSERT INTO reports (project_id, reporter_id, reason, detail, status, created_at)
            VALUES (?, ?, ?, ?, 'open', ?)
            """,
            (
                project_id,
                user["id"],
                body.reason,
                (body.detail or "").strip()[:1000],
                database._now(),
            ),
        )
        report_id = int(
            conn.execute(
                "SELECT id FROM reports WHERE project_id = ? AND reporter_id = ?",
                (project_id, user["id"]),
            ).fetchone()["id"]
        )
        actions = database.apply_report_thresholds(conn, project_id)
        # soft-notify owner of each report (not only auto-pause)
        if not actions.get("auction_paused"):
            database.notify(
                conn,
                int(row["owner_id"]),
                "매물 신고 접수",
                f"「{row['title']}」에 신고가 접수되었습니다. "
                f"현재 오픈 신고 {actions['project_open_reports']}건 "
                f"(중단 기준 {actions['pause_threshold']}건).",
                f"/project.html?id={project_id}",
            )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()

    return {
        "ok": True,
        "report_id": report_id,
        "reason": body.reason,
        "reason_label": database.REPORT_REASONS[body.reason],
        "actions": actions,
        "project": {
            "id": project_id,
            "auction_status": row["auction_status"] if row else None,
            "report_count": int(row["report_count"] or 0) if row and "report_count" in row.keys() else actions["project_open_reports"],
            "is_paused": (row["auction_status"] if row else "") == "paused",
        },
        "message_ko": (
            "신고가 접수되었습니다."
            + (
                " 신고 누적으로 경매가 자동 중단되었습니다."
                if actions.get("auction_paused")
                else ""
            )
            + (
                " 판매자 계정이 자동 정지되었습니다."
                if actions.get("account_suspended")
                else ""
            )
        ),
    }


# --- user ↔ user block (separate from project report) ---


@router.get("/me/blocks")
def list_my_blocks(user: dict = Depends(get_current_user)):
    """List users I have blocked."""
    with database.db() as conn:
        blocks = database.list_user_blocks(conn, user["id"])
    return {
        "ok": True,
        "blocks": blocks,
        "count": len(blocks),
        "note_ko": "차단한 사용자의 매물은 목록·상세에서 숨겨지고, 입찰·쪽지가 거부됩니다.",
    }


@router.post("/users/{target_user_id}/block")
def block_user(target_user_id: int, user: dict = Depends(get_current_user)):
    """
    Block another user. Hides their listings from the blocker and rejects
    bid / buy-now / message between the pair (either direction).
    """
    tid = int(target_user_id)
    if tid == int(user["id"]):
        raise HTTPException(
            status_code=400,
            detail={"code": "cannot_block_self", "message": "자기 자신은 차단할 수 없습니다."},
        )
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        fresh = database.user_to_dict(row_u)
        if not fresh["trust"].get("can_block"):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "suspended",
                    "message": "정지된 계정은 차단을 사용할 수 없습니다.",
                    "trust": fresh["trust"],
                },
            )
        target = conn.execute("SELECT id, display_name FROM users WHERE id = ?", (tid,)).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="user not found")
        already = database.is_blocked_by(conn, user["id"], tid)
        block = database.create_user_block(conn, user["id"], tid)
        name = (target["display_name"] or "").strip() or "사용자"
    return {
        "ok": True,
        "blocked": True,
        "already": already,
        "block": block,
        "blocked_user": {"id": tid, "display_name": name},
        "message_ko": (
            f"「{name}」님을 차단했습니다. 상대 매물이 숨겨지고 입찰·쪽지가 불가합니다."
            if not already
            else f"「{name}」님은 이미 차단되어 있습니다."
        ),
    }


@router.delete("/users/{target_user_id}/block")
def unblock_user(target_user_id: int, user: dict = Depends(get_current_user)):
    """Remove a block you placed."""
    tid = int(target_user_id)
    with database.db() as conn:
        removed = database.delete_user_block(conn, user["id"], tid)
        name = "사용자"
        trow = conn.execute(
            "SELECT display_name FROM users WHERE id = ?", (tid,)
        ).fetchone()
        if trow:
            name = (trow["display_name"] or "").strip() or name
    if not removed:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_blocked", "message": "차단 목록에 없는 사용자입니다."},
        )
    return {
        "ok": True,
        "blocked": False,
        "blocked_user_id": tid,
        "message_ko": f"「{name}」님 차단을 해제했습니다.",
    }


@router.post("/projects/{project_id}/bids")
def place_bid(project_id: int, body: BidIn, user: dict = Depends(get_current_user)):
    """Place a bid. Requires Lv1 (email). Lv2 is required only after award for pay/accept."""
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    user = database.user_to_dict(row_u)
    _require_trust(user, "bid")

    amount = int(body.amount)
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        row = _refresh_auction_ended(conn, row)
        if row["listing_status"] != "approved":
            raise HTTPException(status_code=400, detail="listing not open for bids (awaiting review)")
        auction_status = (row["auction_status"] if "auction_status" in row.keys() else None) or "live"
        if auction_status == "paused":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "auction_paused",
                    "message": "신고 누적 등으로 경매가 중단된 매물입니다. 지금은 가격을 쓸 수 없습니다.",
                },
            )
        if auction_status != "live":
            raise HTTPException(status_code=400, detail="auction ended")
        if int(row["owner_id"]) == int(user["id"]):
            raise HTTPException(status_code=400, detail="cannot bid on own project")
        if database.is_blocked_either(conn, user["id"], row["owner_id"]):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "blocked",
                    "message": "차단된 사용자의 매물에는 입찰할 수 없습니다.",
                },
            )

        p = database.project_to_dict(row, include_private=False)
        next_min = int(p["next_min_bid"] or 0)
        if amount < next_min:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "bid_too_low",
                    "message": f"최소 입찰가 ₩{next_min:,} 이상이어야 합니다.",
                    "next_min_bid": next_min,
                    "price_current": p["price_current"],
                },
            )
        # buy-now ceiling optional
        buy_now = p.get("price_buy_now")
        if buy_now is not None and amount > int(buy_now) * 2:
            # soft guard against typo — allow up to 2x buy_now; skip if no buy_now
            pass

        now = database._now()
        cur = conn.execute(
            """
            INSERT INTO bids (project_id, bidder_id, amount, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, user["id"], amount, now),
        )
        bid_id = int(cur.lastrowid)
        # Race-safe: price_current always reflects MAX bid (not last writer wins)
        conn.execute(
            """
            UPDATE projects
            SET price_current = (
                  SELECT COALESCE(MAX(amount), ?)
                  FROM bids WHERE project_id = ?
                ),
                updated_at = ?
            WHERE id = ?
            """,
            (int(row["price_start"] or amount), project_id, now, project_id),
        )
        database.refresh_project_bid_stats(conn, project_id)
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        current = int(row["price_current"] or 0)
        # optional: hit buy_now → finalize (payment deadline starts)
        # only if this bid is still the winning (max) amount
        if buy_now is not None and amount >= int(buy_now) and current >= int(buy_now):
            # winner = highest bid holder
            top = conn.execute(
                """
                SELECT * FROM bids WHERE project_id = ?
                ORDER BY amount DESC, id DESC LIMIT 1
                """,
                (project_id,),
            ).fetchone()
            if top:
                row = database.finalize_sale(
                    conn,
                    row,
                    sold_price=int(top["amount"]),
                    buyer_id=int(top["bidder_id"]),
                    note="즉시구매가 도달 · 자동 성사",
                )
        else:
            database.notify(
                conn,
                int(row["owner_id"]),
                "새 입찰",
                f"「{row['title']}」에 ₩{amount:,} 입찰이 들어왔습니다.",
                f"/project.html?id={project_id}",
            )
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        bid_row = conn.execute(
            """
            SELECT b.*, u.display_name FROM bids b
            JOIN users u ON u.id = b.bidder_id WHERE b.id = ?
            """,
            (bid_id,),
        ).fetchone()
    return {
        "ok": True,
        "bid": database.bid_to_public(bid_row),
        "project": database.project_to_dict(row, include_private=False),
        "public_note": "현재가가 사이트 전체에 즉시 공개됩니다.",
    }


@router.post("/projects/{project_id}/buy-now")
def buy_now(project_id: int, user: dict = Depends(get_current_user)):
    """Immediate purchase at price_buy_now — L2 required. Seller gets notification."""
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    user = database.user_to_dict(row_u)
    _require_trust(user, "bid")

    with database.db() as conn:
        database.process_expired_auctions(conn)
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if row["listing_status"] != "approved":
            raise HTTPException(status_code=400, detail="listing not open")
        if (row["auction_status"] or "live") == "paused":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "auction_paused",
                    "message": "신고 누적으로 경매가 중단된 매물입니다.",
                },
            )
        if (row["auction_status"] or "live") != "live":
            raise HTTPException(status_code=400, detail="auction not live")
        buy = row["price_buy_now"]
        if buy is None:
            raise HTTPException(status_code=400, detail="buy-now not available")
        if int(row["owner_id"]) == int(user["id"]):
            raise HTTPException(status_code=400, detail="cannot buy own project")
        if database.is_blocked_either(conn, user["id"], row["owner_id"]):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "blocked",
                    "message": "차단된 사용자의 매물은 구매할 수 없습니다.",
                },
            )
        buy = int(buy)
        now = database._now()
        conn.execute(
            """
            INSERT INTO bids (project_id, bidder_id, amount, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, user["id"], buy, now),
        )
        database.refresh_project_bid_stats(conn, project_id)
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        row = database.finalize_sale(
            conn, row, sold_price=buy, buyer_id=user["id"], note="즉시구매"
        )
    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=False),
        "fee": database.fee_breakdown(buy),
    }


@router.post("/projects/{project_id}/close-deal")
def close_deal(
    project_id: int,
    body: CloseDealIn,
    user: dict = Depends(get_current_user),
):
    """Seller confirms deal (needs L3 settlement). Uses current bid by default."""
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    user = database.user_to_dict(row_u)

    with database.db() as conn:
        database.process_expired_auctions(conn)
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if int(row["owner_id"]) != int(user["id"]):
            raise HTTPException(status_code=403, detail="owner only")
        if row["listing_status"] != "approved":
            raise HTTPException(status_code=400, detail="not an approved listing")
        if (row["auction_status"] or "") == "sold" and row["sold_price"]:
            raise HTTPException(status_code=400, detail="already sold")

        _require_trust(user, "deal")

        sold_price = body.sold_price
        buyer_id = body.buyer_user_id
        if body.use_current_bid or sold_price is None:
            top = conn.execute(
                """
                SELECT * FROM bids WHERE project_id = ? ORDER BY amount DESC, id DESC LIMIT 1
                """,
                (project_id,),
            ).fetchone()
            if top:
                sold_price = int(top["amount"])
                buyer_id = int(top["bidder_id"])
            elif sold_price is None:
                raise HTTPException(status_code=400, detail="no bids — set sold_price")
        sold_price = int(sold_price)
        row = database.finalize_sale(
            conn,
            row,
            sold_price=sold_price,
            buyer_id=buyer_id,
            note=(body.note or "성사 확정").strip(),
        )
    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=True),
        "fee": database.fee_breakdown(sold_price),
        "transfer_checklist": [
            "구매자 PG 결제(기한 내) → 웹훅으로 입금 확인",
            "판매자: 프로젝트 이전 후 「이전 완료」",
            "구매자: 검수 후 「인수하기」(또는 기한 내 이의 없으면 자동 확정)",
            "확정 후 판매자 정산 · 판매자 수수료 10%",
            "입금 확인 전 코드·도메인·계정 이전 금지",
        ],
        "deal_policy": database.deal_policy_public(),
    }


class DealNoteIn(BaseModel):
    note: str = Field(default="", max_length=800)


class CouponCampaignCreateIn(BaseModel):
    code: str = Field(default="", max_length=40)
    name: str = Field(default="", max_length=80)
    max_redemptions: int = Field(default=100, ge=1, le=100)
    fee_rate: float = Field(default=0.08, ge=0, lt=0.1)
    note: str = Field(default="", max_length=200)
    auto_code: bool = False  # True → server generates secure code
    allow_url_claim: bool = False  # Viral URL verify → claim button
    starts_at: str = Field(default="", max_length=40)  # ISO, optional
    ends_at: str = Field(default="", max_length=40)  # ISO, optional


class CouponRedeemIn(BaseModel):
    code: str = Field(min_length=4, max_length=40)


class CouponGiftIn(BaseModel):
    """Recipient: account user id and/or email. Prefer `to` (id or email string)."""

    to: str | None = Field(default=None, min_length=1, max_length=120)
    to_email: EmailStr | None = None
    to_user_id: int | None = Field(default=None, ge=1)


@router.get("/me/coupons")
def my_coupons(user: dict = Depends(get_current_user)):
    with database.db() as conn:
        items = database.list_user_coupons(conn, int(user["id"]))
    return {
        "ok": True,
        "coupons": items,
        "policy": {
            "default_fee_pct": 10,
            "coupon_fee_pct": 8,
            "label_ko": "성사 수수료 8% 쿠폰",
            "no_expiry": True,
            "redeem_once_per_account": True,
            "gift_does_not_block_redeem": True,
            "gift_by": "user_id_or_email",
            "gift_auto_registers": True,
            "note_ko": (
                "쿠폰은 판매 성사 수수료에만 적용됩니다. 유효기간 없음. "
                "코드 등록은 계정당 1회. 선물 수령은 등록 한도와 별개이며 "
                "선물하면 받는 사람 계정에 바로 등록됩니다. "
                "현금화·양도 중개는 하지 않으며 선물하기만 제공합니다."
            ),
        },
    }


@router.post("/me/coupons/redeem")
def redeem_coupon(body: CouponRedeemIn, user: dict = Depends(get_current_user)):
    try:
        with database.db() as conn:
            uc = database.redeem_coupon_code(conn, int(user["id"]), body.code)
            database.notify(
                conn,
                int(user["id"]),
                "쿠폰 등록 완료",
                uc.get("label_ko") or "수수료 쿠폰이 계정에 등록되었습니다.",
                "/app/#coupons",
            )
    except ValueError as e:
        msg = str(e)
        code_map = {
            "invalid or inactive code": "invalid_code",
            "campaign sold out": "sold_out",
            "already redeemed on this account": "already_redeemed",
            "code required": "code_required",
        }
        raise HTTPException(
            status_code=400,
            detail={
                "code": code_map.get(msg, "redeem_failed"),
                "message": {
                    "invalid or inactive code": "유효하지 않거나 종료된 코드입니다.",
                    "campaign sold out": "쿠폰이 모두 소진되었습니다.",
                    "already redeemed on this account": "이 계정은 이미 이 코드를 등록했습니다. (1계정당 1회)",
                    "code required": "코드를 입력해 주세요.",
                }.get(msg, msg),
            },
        ) from e
    return {"ok": True, "coupon": uc}


@router.post("/me/coupons/{coupon_id}/gift")
def gift_coupon(
    coupon_id: int,
    body: CouponGiftIn,
    user: dict = Depends(get_current_user),
):
    if not body.to and not body.to_email and body.to_user_id is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "recipient_required",
                "message": "받는 사람 계정 아이디 또는 이메일을 입력해 주세요.",
            },
        )
    try:
        with database.db() as conn:
            uc = database.gift_user_coupon(
                conn,
                coupon_id=int(coupon_id),
                from_user_id=int(user["id"]),
                to=(str(body.to).strip() if body.to else None),
                to_email=str(body.to_email) if body.to_email else None,
                to_user_id=int(body.to_user_id) if body.to_user_id is not None else None,
            )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "gift_failed",
                "message": {
                    "recipient not found": "받는 사람 계정을 찾을 수 없습니다. (계정 아이디 또는 가입 이메일)",
                    "cannot gift to yourself": "본인에게는 선물할 수 없습니다.",
                    "coupon not found": "쿠폰을 찾을 수 없습니다.",
                    "coupon not available": "이미 사용했거나 선물할 수 없는 쿠폰입니다.",
                    "invalid email": "이메일 형식이 올바르지 않습니다.",
                    "invalid recipient": "계정 아이디(숫자) 또는 가입 이메일을 입력해 주세요.",
                    "recipient required": "받는 사람 계정 아이디 또는 이메일을 입력해 주세요.",
                }.get(msg, msg),
            },
        ) from e
    return {
        "ok": True,
        "coupon": uc,
        "message_ko": "쿠폰을 선물했습니다. 받는 사람 계정에 자동 등록되었습니다.",
    }


@router.get("/admin/coupons")
def admin_list_coupons(_: None = Depends(require_admin)):
    with database.db() as conn:
        camps = database.list_coupon_campaigns(conn)
    return {"ok": True, "campaigns": camps}


@router.get("/admin/coupons/generate-code")
def admin_generate_coupon_code(_: None = Depends(require_admin)):
    """Suggest a secure redeem code (does not create campaign)."""
    return {
        "ok": True,
        "code": database.generate_coupon_code(),
        "hint_ko": "보안용 랜덤 코드입니다. 발급 시 이 코드를 쓰거나 다시 뽑을 수 있습니다.",
    }


@router.post("/admin/coupons")
def admin_create_coupon(body: CouponCampaignCreateIn, _: None = Depends(require_admin)):
    try:
        with database.db() as conn:
            code = (body.code or "").strip()
            if body.auto_code or not code:
                code = database.generate_coupon_code(conn)
            camp = database.create_coupon_campaign(
                conn,
                code=code,
                name=body.name or "",
                fee_rate=float(body.fee_rate),
                max_redemptions=min(100, int(body.max_redemptions or 100)),
                note=body.note or "",
                allow_url_claim=bool(body.allow_url_claim),
                starts_at=(body.starts_at or "").strip(),
                ends_at=(body.ends_at or "").strip(),
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "campaign": camp}


class PromoSubmitIn(BaseModel):
    post_url: str = Field(min_length=8, max_length=500)
    channel: str = Field(default="instagram", min_length=1, max_length=40)


class PromoReviewIn(BaseModel):
    action: Literal["approve", "reject"]
    admin_note: str = Field(default="", max_length=300)


def _promo_public_payload() -> dict:
    """Shared bootstrap for homepage banner + event page (no redeem code)."""
    with database.db() as conn:
        open_camp = database.get_active_url_claim_campaign(conn)
        if open_camp:
            c = database.campaign_to_dict(open_camp, include_code=False)
            return {
                "ok": True,
                "active": True,
                "event_open": True,
                "title_ko": "소문내고 수수료 8% 쿠폰 받기",
                "title_en": "Share WakeAgain · get 8% seller fee coupon",
                "banner_ko": "이벤트 진행 중 · 소문 내고 성사 수수료 8% 쿠폰 받기 (계정당 1회)",
                "banner_en": "Live event · Share WakeAgain, earn an 8% seller-fee coupon (once per account)",
                "cta_ko": "이벤트 참여",
                "cta_en": "Join event",
                "btn_ko": "소문내고 8% 쿠폰",
                "btn_en": "Share · 8% coupon",
                "cta_href": "/promo/event.html",
                "campaign": {
                    "id": c["id"],
                    "name": c["name"],
                    "label_ko": c["label_ko"],
                    "fee_rate_pct": c["fee_rate_pct"],
                    "remaining": c["remaining"],
                    "max_redemptions": c["max_redemptions"],
                    "no_expiry": True,
                    "starts_at": c.get("starts_at") or "",
                    "ends_at": c.get("ends_at") or "",
                },
                "channels": database.promo_channel_list(),
                "steps_ko": [
                    "아래 채널 중 하나만 골라 WakeAgain 소개글·후기를 올립니다.",
                    "게시물·글 URL을 복사해 제출합니다. (채널마다 보상은 같습니다)",
                    "운영 확인 후 승인되면, 앱 → 쿠폰에서 「쿠폰 받기」가 나타납니다.",
                    "받기 버튼을 누르면 계정에 성사 수수료 8% 쿠폰이 등록됩니다.",
                ],
                "steps_en": [
                    "Pick one channel below and post a short intro or review of WakeAgain.",
                    "Copy the post URL and submit it. (Same reward for every channel.)",
                    "After ops approves, open App → Coupons and tap Claim coupon.",
                    "Claiming registers an 8% seller-fee coupon on your account.",
                ],
                "rules_ko": [
                    "보상: 성사 수수료 8% 쿠폰 1장 (기본 10% → 8%, 판매 성사 시에만)",
                    "계정당 이벤트 전체 1회 · 채널을 여러 개 올려도 보상은 1장",
                    "인스타·X·블로그·커뮤니티 보상 동일 (할인율 차이 없음)",
                    "URL 제출만으로 즉시 발급되지 않음 · 승인 후 앱에서 수령",
                    "이벤트 종료·수량 소진 시 홈 배너·제출 버튼이 사라집니다",
                    "쿠폰 코드는 공개하지 않습니다 · 유효기간 없음 · 매매 중개 없음",
                ],
                "rules_en": [
                    "Reward: one 8% seller-fee coupon (default 10% → 8%, only when a sale closes)",
                    "Once per account for the whole event · multiple channels still = one coupon",
                    "Instagram, X, blogs, and communities all get the same reward",
                    "Submitting a URL does not issue the coupon instantly · claim in the app after approval",
                    "When the event ends or stock runs out, the home banner and submit button hide",
                    "Coupon codes stay private · no expiry · we don’t broker resale",
                ],
                "message_ko": "",
                "message_en": "",
            }
        closed = database.get_url_claim_campaign_for_display(conn)
        msg = "진행 중인 소문내기 이벤트가 없습니다."
        msg_en = "No share event is running right now."
        if closed:
            c = database.campaign_to_dict(closed, include_code=False)
            if c.get("remaining", 1) <= 0:
                msg = "이번 이벤트 수량이 모두 소진되었습니다."
                msg_en = "This event is sold out."
            elif c.get("ends_at"):
                msg = "이 이벤트는 종료되었습니다."
                msg_en = "This event has ended."
            elif not c.get("active"):
                msg = "이 이벤트는 종료되었습니다."
                msg_en = "This event has ended."
        return {
            "ok": True,
            "active": False,
            "event_open": False,
            "title_ko": "소문내고 수수료 8% 쿠폰 받기",
            "title_en": "Share WakeAgain · get 8% seller fee coupon",
            "banner_ko": "",
            "banner_en": "",
            "cta_ko": "",
            "cta_en": "",
            "btn_ko": "소문내고 8% 쿠폰",
            "btn_en": "Share · 8% coupon",
            "cta_href": "/promo/event.html",
            "campaign": None,
            "channels": database.promo_channel_list(),
            "steps_ko": [],
            "steps_en": [],
            "rules_ko": [],
            "rules_en": [],
            "message_ko": msg,
            "message_en": msg_en,
        }


_PROMO_SUBMIT_ERRORS = {
    "no active promo campaign": "진행 중인 이벤트가 없습니다.",
    "campaign sold out": "이벤트가 마감되었습니다.",
    "invalid channel": "채널을 선택해 주세요.",
    "instagram url required": "인스타그램 게시물 URL을 입력해 주세요.",
    "x url required": "X(트위터) 게시물 URL을 입력해 주세요.",
    "blog url required": "링크드인 또는 블로그 글 URL을 입력해 주세요.",
    "community url required": "커뮤니티 글·초대 링크 URL을 입력해 주세요.",
    "use correct channel": "선택한 채널에 맞는 URL을 입력해 주세요.",
    "invalid url": "올바른 URL을 입력해 주세요.",
    "url required": "URL을 입력해 주세요.",
    "url too long": "URL이 너무 깁니다.",
    "already pending": "이미 검토 대기 중인 제출이 있습니다. (계정당 1회)",
    "already approved": "이미 승인되었습니다. 앱 → 쿠폰에서 받아 주세요.",
    "already claimed": "이미 이벤트 쿠폰을 받으셨습니다. (계정당 1회)",
}


@router.get("/promo/event")
def promo_event_public():
    """Unified viral event bootstrap for homepage + /promo/event.html."""
    return _promo_public_payload()


@router.get("/promo/instagram")
def promo_instagram_public():
    """Legacy path — same payload as unified event (Instagram is one channel)."""
    return _promo_public_payload()


@router.post("/me/promo/event/submit")
def promo_event_submit(body: PromoSubmitIn, user: dict = Depends(get_current_user)):
    try:
        with database.db() as conn:
            sub = database.submit_promo_event(
                conn,
                int(user["id"]),
                channel=(body.channel or "instagram").strip().lower(),
                post_url=body.post_url,
            )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "submit_failed",
                "message": _PROMO_SUBMIT_ERRORS.get(msg, msg),
            },
        ) from e
    return {
        "ok": True,
        "submission": sub,
        "message_ko": "제출되었습니다. 운영 확인 후 알림으로 안내합니다. (계정당 1회)",
    }


@router.post("/me/promo/instagram/submit")
def promo_instagram_submit(body: PromoSubmitIn, user: dict = Depends(get_current_user)):
    """Legacy: defaults channel to instagram if omitted."""
    ch = (body.channel or "instagram").strip().lower() or "instagram"
    body = PromoSubmitIn(post_url=body.post_url, channel=ch)
    return promo_event_submit(body, user)


@router.get("/me/promo/event")
def promo_event_mine(user: dict = Depends(get_current_user)):
    with database.db() as conn:
        items = database.list_user_promo_submissions(conn, int(user["id"]))
        camp = database.get_active_url_claim_campaign(conn)
        campaign = (
            database.campaign_to_dict(camp, include_code=False) if camp else None
        )
        open_flag = bool(camp)
    return {
        "ok": True,
        "submissions": items,
        "campaign": campaign,
        "event_open": open_flag,
        "once_per_account": True,
    }


@router.get("/me/promo/instagram")
def promo_instagram_mine(user: dict = Depends(get_current_user)):
    return promo_event_mine(user)


@router.post("/me/promo/event/{submission_id}/claim")
def promo_event_claim(
    submission_id: int, user: dict = Depends(get_current_user)
):
    try:
        with database.db() as conn:
            uc = database.claim_promo_coupon(
                conn, int(user["id"]), int(submission_id)
            )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "claim_failed",
                "message": {
                    "not found": "제출을 찾을 수 없습니다.",
                    "not approved": "아직 승인되지 않았습니다.",
                    "campaign inactive": "이벤트가 종료되었습니다.",
                    "campaign sold out": "쿠폰이 모두 소진되었습니다.",
                }.get(msg, msg),
            },
        ) from e
    return {
        "ok": True,
        "coupon": uc,
        "message_ko": "쿠폰이 계정에 등록되었습니다. 성사 시 수수료 8%가 적용됩니다.",
    }


@router.post("/me/promo/instagram/{submission_id}/claim")
def promo_instagram_claim(
    submission_id: int, user: dict = Depends(get_current_user)
):
    return promo_event_claim(submission_id, user)


@router.get("/admin/promo/event")
def admin_promo_event(
    status: str = "pending", _: None = Depends(require_admin)
):
    with database.db() as conn:
        items = database.list_promo_submissions_admin(conn, status=status)
        open_c = database.get_active_url_claim_campaign(conn)
    return {
        "ok": True,
        "submissions": items,
        "event_open": bool(open_c),
        "event_url": "/promo/event.html",
    }


@router.get("/admin/promo/instagram")
def admin_promo_instagram(
    status: str = "pending", _: None = Depends(require_admin)
):
    return admin_promo_event(status=status)


@router.post("/admin/promo/event/{submission_id}/review")
def admin_promo_event_review(
    submission_id: int,
    body: PromoReviewIn,
    _: None = Depends(require_admin),
):
    try:
        with database.db() as conn:
            sub = database.review_promo_submission(
                conn,
                int(submission_id),
                action=body.action,
                admin_note=body.admin_note or "",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "submission": sub}


@router.post("/admin/promo/instagram/{submission_id}/review")
def admin_promo_review(
    submission_id: int,
    body: PromoReviewIn,
    _: None = Depends(require_admin),
):
    return admin_promo_event_review(submission_id, body)


@router.post("/projects/{project_id}/deal/mark-transferred")
def deal_mark_transferred(
    project_id: int,
    body: DealNoteIn | None = None,
    user: dict = Depends(get_current_user),
):
    """Seller: assets handed over → start buyer inspection clock."""
    note = (body.note if body else "") or "이전 완료"
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if int(row["owner_id"]) != int(user["id"]):
            raise HTTPException(status_code=403, detail="seller only")
        try:
            row = database.mark_deal_transferred(conn, row, note=note.strip())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=False),
        "deal_policy": database.deal_policy_public(),
    }


class HandoverCheckIn(BaseModel):
    """Buyer marks receipt items. checks: { item_id: true/false }"""
    checks: dict[str, bool] = Field(default_factory=dict)


@router.put("/projects/{project_id}/deal/handover-checklist")
def deal_handover_checklist(
    project_id: int,
    body: HandoverCheckIn,
    user: dict = Depends(get_current_user),
):
    """Buyer updates handover receipt checklist (self-transfer; site only records checks)."""
    if not body.checks:
        raise HTTPException(status_code=400, detail="checks required")
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        buyer_id = row["buyer_id"] if "buyer_id" in row.keys() else None
        if not buyer_id or int(buyer_id) != int(user["id"]):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "buyer_only",
                    "message": "인수 확인 목록은 낙찰 구매자만 체크할 수 있습니다.",
                },
            )
        astatus = (row["auction_status"] or "") or ""
        if astatus != "sold":
            raise HTTPException(status_code=400, detail="성사된 매물에서만 사용할 수 있습니다.")
        st = (row["deal_status"] if "deal_status" in row.keys() else None) or ""
        if st not in ("paid", "inspection", "awaiting_payment"):
            raise HTTPException(
                status_code=400,
                detail="입금·이전·검수 단계에서만 체크할 수 있습니다.",
            )
        row, checklist = database.apply_handover_checks(
            conn, row, checks=body.checks
        )
    return {
        "ok": True,
        "handover_checklist": checklist,
        "project": database.project_to_dict(row, include_private=False),
        "message_ko": "인수 확인 목록을 저장했습니다.",
    }


@router.post("/projects/{project_id}/deal/accept")
def deal_buyer_accept(
    project_id: int,
    body: DealNoteIn | None = None,
    user: dict = Depends(get_current_user),
):
    """Buyer: inspect OK → confirm takeover; seller settlement released. Needs Lv2."""
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    user = database.user_to_dict(row_u)
    _require_trust(user, "fulfill")

    note = (body.note if body else "") or "구매자 인수 확정"
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        buyer_id = row["buyer_id"] if "buyer_id" in row.keys() else None
        if not buyer_id or int(buyer_id) != int(user["id"]):
            raise HTTPException(status_code=403, detail="buyer only")
        status = (row["deal_status"] if "deal_status" in row.keys() else None) or ""
        if status != "inspection":
            raise HTTPException(
                status_code=400,
                detail="이전·검수 단계에서만 인수할 수 있습니다. 판매자 「이전 완료」 후 이용해 주세요.",
            )
        row, _ho = database.ensure_handover_checklist(conn, row)
        if not database.handover_all_required_checked(row):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "handover_checklist_incomplete",
                    "message": "인수 확인 목록의 필수 항목을 모두 체크한 뒤 「인수하기」를 눌러 주세요. (직접 이전 후 본인 확인)",
                },
            )
        try:
            row = database.settle_complete(
                conn, row, reason="buyer_accept", note=note.strip()
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=False),
        "deal_policy": database.deal_policy_public(),
        "message_ko": "인수가 확정되었습니다. 판매자 정산이 진행됩니다.",
    }


@router.post("/projects/{project_id}/deal/dispute")
def deal_dispute(
    project_id: int,
    body: DealNoteIn,
    user: dict = Depends(get_current_user),
):
    """Buyer or seller: raise dispute during payment/inspection (stops auto-settle)."""
    note = (body.note or "").strip()
    if len(note) < 5:
        raise HTTPException(status_code=400, detail="이의 사유를 5자 이상 적어 주세요.")
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        uid = int(user["id"])
        buyer_id = row["buyer_id"] if "buyer_id" in row.keys() else None
        owner_id = int(row["owner_id"])
        if uid != owner_id and (not buyer_id or uid != int(buyer_id)):
            raise HTTPException(status_code=403, detail="buyer or seller only")
        try:
            row = database.mark_deal_disputed(
                conn, row, note=note, by_user_id=uid
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=False),
        "message_ko": "이의가 접수되었습니다. 자동 확정이 중지되며 운영이 검토합니다.",
    }


@router.post("/projects/{project_id}/payment/request")
def payment_request(
    project_id: int, method: str = "card", user: dict = Depends(get_current_user)
):
    """Buyer: get PortOne payment params for the current awaiting_payment deal.

    method="card" -> requestPayment() popup (domestic channel).
    method="paypal" -> loadPaymentUI() embedded SPB button (overseas channel).
    """
    method = (method or "card").strip().lower()
    if method not in ("card", "paypal"):
        raise HTTPException(status_code=400, detail="method must be 'card' or 'paypal'")
    enabled = payments_mod.paypal_enabled() if method == "paypal" else payments_mod.portone_enabled()
    if not enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "pg_not_configured",
                "message": "결제 연동이 아직 설정되지 않았습니다."
                if method == "card"
                else "PayPal 채널이 아직 설정되지 않았습니다 (PG 계약 심사 대기 중일 수 있습니다).",
            },
        )
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    user = database.user_to_dict(row_u)
    _require_trust(user, "fulfill")

    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        buyer_id = row["buyer_id"] if "buyer_id" in row.keys() else None
        if not buyer_id or int(buyer_id) != int(user["id"]):
            raise HTTPException(status_code=403, detail="buyer only")
        status = (row["deal_status"] if "deal_status" in row.keys() else None) or ""
        if status != "awaiting_payment":
            raise HTTPException(
                status_code=400,
                detail="입금 대기 단계에서만 결제를 시작할 수 있습니다.",
            )
        payment_id = payments_mod.new_payment_id(project_id)
        row = database.set_pending_payment(conn, row, payment_id=payment_id)

    total_amount = int(row["deal_amount"] if "deal_amount" in row.keys() else row["sold_price"])
    try:
        if method == "paypal":
            params = payments_mod.build_paypal_payment_request(
                payment_id=payment_id,
                order_name=str(row["title"]),
                total_amount=total_amount,
                buyer_name=user.get("real_name") or user.get("email") or "buyer",
                buyer_email=user.get("email"),
            )
        else:
            params = payments_mod.build_payment_request(
                payment_id=payment_id,
                order_name=str(row["title"]),
                total_amount=total_amount,
                buyer_name=user.get("real_name") or user.get("email") or "buyer",
                buyer_email=user.get("email"),
                buyer_phone=user.get("phone"),
            )
    except payments_mod.PortOnePaymentError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"ok": True, "method": method, "payment_request": params}


class PaymentVerifyIn(BaseModel):
    payment_id: str = Field(min_length=1, max_length=200)


@router.post("/payments/verify")
def payment_verify(body: PaymentVerifyIn, user: dict = Depends(get_current_user)):
    """Frontend calls this right after PortOne.requestPayment() resolves.

    Re-verifies against PortOne's server API (never trusts the client) before
    marking the deal paid. The webhook is a backup path for the same effect.
    """
    with database.db() as conn:
        row = database.find_project_by_payment_id(conn, body.payment_id)
        if not row:
            raise HTTPException(status_code=404, detail="payment not found for this deal")
        buyer_id = row["buyer_id"] if "buyer_id" in row.keys() else None
        if not buyer_id or int(buyer_id) != int(user["id"]):
            raise HTTPException(status_code=403, detail="buyer only")
        expected_amount = int(
            row["deal_amount"] if "deal_amount" in row.keys() else row["sold_price"]
        )
        try:
            payment = payments_mod.fetch_payment(body.payment_id)
            payments_mod.assert_payment_paid(payment, expected_amount=expected_amount)
        except payments_mod.PortOnePaymentError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        if payments_mod.is_paypal_payment(payment):
            database.adjust_fee_invoice_for_crossborder(conn, int(row["id"]))
        try:
            row = database.mark_deal_paid(conn, row, note="PortOne 결제 확인")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=False),
        "deal_policy": database.deal_policy_public(),
    }


@router.post("/payments/webhook")
async def payment_webhook(request: Request):
    """PortOne webhook (Standard Webhooks signed). Backup path — idempotent."""
    raw_body = await request.body()
    try:
        payload = payments_mod.verify_webhook(raw_body=raw_body, headers=dict(request.headers))
    except payments_mod.PortOnePaymentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    payment_id = ((payload.get("data") or {}).get("paymentId")) or ""
    if not payment_id:
        return {"ok": True, "skipped": "no paymentId in payload"}

    with database.db() as conn:
        row = database.find_project_by_payment_id(conn, payment_id)
        if not row:
            return {"ok": True, "skipped": "no matching deal"}
        expected_amount = int(
            row["deal_amount"] if "deal_amount" in row.keys() else row["sold_price"]
        )
        try:
            payment = payments_mod.fetch_payment(payment_id)
            payments_mod.assert_payment_paid(payment, expected_amount=expected_amount)
        except payments_mod.PortOnePaymentError:
            return {"ok": True, "skipped": "not paid or amount mismatch"}
        if payments_mod.is_paypal_payment(payment):
            database.adjust_fee_invoice_for_crossborder(conn, int(row["id"]))
        try:
            database.mark_deal_paid(conn, row, note="PortOne 웹훅 확인")
        except ValueError:
            pass
    return {"ok": True}


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


def _can_message_project(conn, project_id: int, user_id: int) -> bool:
    row = conn.execute("SELECT owner_id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        return False
    if int(row["owner_id"]) == int(user_id):
        return True
    bid = conn.execute(
        "SELECT 1 FROM bids WHERE project_id = ? AND bidder_id = ? LIMIT 1",
        (project_id, user_id),
    ).fetchone()
    return bool(bid)


class QThreadIn(BaseModel):
    body: str = Field(min_length=10, max_length=2000)


class QAnswerIn(BaseModel):
    answer: str = Field(min_length=5, max_length=4000)


class QPurchaseIn(BaseModel):
    units: int = Field(default=1, ge=1, le=5)


def _q_party_row(conn, project_id: int, user: dict):
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    uid = int(user["id"])
    buyer = row["buyer_id"] if "buyer_id" in row.keys() else None
    is_seller = uid == int(row["owner_id"])
    is_buyer = buyer is not None and uid == int(buyer)
    if not (is_seller or is_buyer):
        raise HTTPException(status_code=403, detail="deal parties only")
    return row, is_seller, is_buyer


@router.get("/projects/{project_id}/q-credits")
def get_q_credits(project_id: int, user: dict = Depends(get_current_user)):
    """Deal parties: remaining credits + threads. Public listing fields are on project."""
    with database.db() as conn:
        row, is_seller, is_buyer = _q_party_row(conn, project_id, user)
        threads = database.list_q_threads(conn, project_id)
        p = database.project_to_dict(row, include_private=is_seller)
    return {
        "ok": True,
        "policy": database.q_credit_policy_public(),
        "q_credits_offered": p.get("q_credits_offered"),
        "q_credit_unit_price": p.get("q_credit_unit_price"),
        "q_credit_sla_hours": p.get("q_credit_sla_hours"),
        "q_credits_total": p.get("q_credits_total"),
        "q_credits_remaining": p.get("q_credits_remaining"),
        "q_credits_held": p.get("q_credits_held"),
        "q_credits_purchased": p.get("q_credits_purchased"),
        "q_window_ends_at": p.get("q_window_ends_at"),
        "available": max(
            0, int(p.get("q_credits_remaining") or 0) - int(p.get("q_credits_held") or 0)
        ),
        "is_seller": is_seller,
        "is_buyer": is_buyer,
        "threads": threads,
    }


@router.post("/projects/{project_id}/q-credits/threads")
def create_q_thread(
    project_id: int,
    body: QThreadIn,
    user: dict = Depends(get_current_user),
):
    with database.db() as conn:
        row, _is_seller, is_buyer = _q_party_row(conn, project_id, user)
        if not is_buyer:
            raise HTTPException(status_code=403, detail="buyer only")
        try:
            thread = database.open_q_thread(
                conn, row, buyer_id=int(user["id"]), body=body.body
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"code": "q_thread", "message": str(e)}) from e
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return {
        "ok": True,
        "thread": thread,
        "project": database.project_to_dict(row, include_private=False),
    }


@router.post("/projects/{project_id}/q-credits/threads/{thread_id}/answer")
def answer_q_thread_api(
    project_id: int,
    thread_id: int,
    body: QAnswerIn,
    user: dict = Depends(get_current_user),
):
    with database.db() as conn:
        row, is_seller, _ = _q_party_row(conn, project_id, user)
        if not is_seller:
            raise HTTPException(status_code=403, detail="seller only")
        try:
            thread = database.answer_q_thread(
                conn, thread_id, seller_id=int(user["id"]), answer=body.answer
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"code": "q_answer", "message": str(e)}) from e
        if int(thread.get("project_id") or 0) != int(project_id):
            raise HTTPException(status_code=404, detail="not found")
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return {
        "ok": True,
        "thread": thread,
        "project": database.project_to_dict(row, include_private=True),
    }


@router.post("/projects/{project_id}/q-credits/threads/{thread_id}/cancel")
def cancel_q_thread_api(
    project_id: int,
    thread_id: int,
    user: dict = Depends(get_current_user),
):
    with database.db() as conn:
        _row, _s, is_buyer = _q_party_row(conn, project_id, user)
        if not is_buyer:
            raise HTTPException(status_code=403, detail="buyer only")
        try:
            thread = database.cancel_q_thread(
                conn, thread_id, buyer_id=int(user["id"])
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"code": "q_cancel", "message": str(e)}) from e
        if int(thread.get("project_id") or 0) != int(project_id):
            raise HTTPException(status_code=404, detail="not found")
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return {
        "ok": True,
        "thread": thread,
        "project": database.project_to_dict(row, include_private=False),
    }


@router.post("/projects/{project_id}/q-credits/purchase")
def purchase_q_credits(
    project_id: int,
    body: QPurchaseIn | None = None,
    user: dict = Depends(get_current_user),
):
    """
    Buy add-on credits at seller-set unit price.
    Real money: PG later. Set Q_CREDIT_PURCHASE_MOCK=1 for local/dev paid simulation.
    """
    body = body or QPurchaseIn()
    mock = (os.environ.get("Q_CREDIT_PURCHASE_MOCK") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    with database.db() as conn:
        row, _s, is_buyer = _q_party_row(conn, project_id, user)
        if not is_buyer:
            raise HTTPException(status_code=403, detail="buyer only")
        try:
            pur = database.purchase_q_credit_units(
                conn,
                row,
                buyer_id=int(user["id"]),
                units=int(body.units or 1),
                mock_paid=mock,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail={"code": "q_purchase", "message": str(e)}
            ) from e
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not mock and pur.get("status") == "pending_payment":
        return {
            "ok": True,
            "purchase": pur,
            "project": database.project_to_dict(row, include_private=False),
            "code": "pg_required",
            "message_ko": pur.get("message_ko"),
            "policy": database.q_credit_policy_public(),
        }
    return {
        "ok": True,
        "purchase": pur,
        "project": database.project_to_dict(row, include_private=False),
        "policy": database.q_credit_policy_public(),
    }


@router.get("/projects/{project_id}/messages")
def list_messages(project_id: int, user: dict = Depends(get_current_user)):
    with database.db() as conn:
        if not _can_message_project(conn, project_id, user["id"]):
            raise HTTPException(status_code=403, detail="owner or bidders only")
        proj = conn.execute("SELECT owner_id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if proj and database.is_blocked_either(conn, user["id"], proj["owner_id"]):
            raise HTTPException(
                status_code=403,
                detail={"code": "blocked", "message": "차단된 사용자와는 쪽지를 볼 수 없습니다."},
            )
        rows = conn.execute(
            """
            SELECT m.*, u.display_name FROM messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.project_id = ?
            ORDER BY m.id ASC
            LIMIT 200
            """,
            (project_id,),
        ).fetchall()
    return {"ok": True, "messages": [database.message_to_dict(r) for r in rows]}


@router.post("/projects/{project_id}/messages")
def post_message(project_id: int, body: MessageIn, user: dict = Depends(get_current_user)):
    text = body.body.strip()
    if not text:
        raise HTTPException(status_code=400, detail="body required")
    with database.db() as conn:
        if not _can_message_project(conn, project_id, user["id"]):
            raise HTTPException(status_code=403, detail="owner or bidders only")
        proj = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="not found")
        if database.is_blocked_either(conn, user["id"], proj["owner_id"]):
            raise HTTPException(
                status_code=403,
                detail={"code": "blocked", "message": "차단된 사용자에게 쪽지를 보낼 수 없습니다."},
            )
        now = database._now()
        cur = conn.execute(
            """
            INSERT INTO messages (project_id, sender_id, body, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, user["id"], text, now),
        )
        mid = int(cur.lastrowid)
        # notify the other party
        owner_id = int(proj["owner_id"])
        if int(user["id"]) == owner_id:
            # notify latest bidder or all unique bidders? notify recent bidders
            bidders = conn.execute(
                """
                SELECT DISTINCT bidder_id FROM bids WHERE project_id = ? AND bidder_id != ?
                """,
                (project_id, user["id"]),
            ).fetchall()
            for b in bidders[:10]:
                database.notify(
                    conn,
                    int(b["bidder_id"]),
                    "매물 쪽지",
                    f"「{proj['title']}」 판매자 메시지: {text[:80]}",
                    f"/project.html?id={project_id}",
                )
        else:
            database.notify(
                conn,
                owner_id,
                "매물 쪽지",
                f"「{proj['title']}」 입찰자 메시지: {text[:80]}",
                f"/project.html?id={project_id}",
            )
        row = conn.execute(
            """
            SELECT m.*, u.display_name FROM messages m
            JOIN users u ON u.id = m.sender_id WHERE m.id = ?
            """,
            (mid,),
        ).fetchone()
    return {"ok": True, "message": database.message_to_dict(row)}


@router.get("/me/fees")
def my_fees(user: dict = Depends(get_current_user)):
    with database.db() as conn:
        rows = conn.execute(
            """
            SELECT f.*, p.title AS project_title FROM fee_invoices f
            JOIN projects p ON p.id = f.project_id
            WHERE f.seller_id = ?
            ORDER BY f.id DESC LIMIT 50
            """,
            (user["id"],),
        ).fetchall()
    out = []
    for r in rows:
        d = database.fee_invoice_to_dict(r)
        d["project_title"] = r["project_title"]
        out.append(d)
    return {"ok": True, "invoices": out, "fee_policy": {"rate_pct": 10, "payer_ko": "판매자"}}


@router.get("/admin/fees")
def admin_fees(status: str = "pending", _: None = Depends(require_admin)):
    status = (status or "pending").strip().lower()
    with database.db() as conn:
        if status == "all":
            rows = conn.execute(
                """
                SELECT f.*, p.title AS project_title, u.email AS seller_email
                FROM fee_invoices f
                JOIN projects p ON p.id = f.project_id
                JOIN users u ON u.id = f.seller_id
                ORDER BY f.id DESC LIMIT 200
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT f.*, p.title AS project_title, u.email AS seller_email
                FROM fee_invoices f
                JOIN projects p ON p.id = f.project_id
                JOIN users u ON u.id = f.seller_id
                WHERE f.status = ?
                ORDER BY f.id DESC LIMIT 200
                """,
                (status,),
            ).fetchall()
    out = []
    for r in rows:
        d = database.fee_invoice_to_dict(r)
        d["project_title"] = r["project_title"]
        d["seller_email"] = r["seller_email"]
        out.append(d)
    return {"ok": True, "invoices": out}


@router.post("/admin/fees/{invoice_id}/paid")
def admin_mark_fee_paid(invoice_id: int, _: None = Depends(require_admin)):
    now = database._now()
    with database.db() as conn:
        row = conn.execute("SELECT * FROM fee_invoices WHERE id = ?", (invoice_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute(
            "UPDATE fee_invoices SET status = 'paid', paid_at = ? WHERE id = ?",
            (now, invoice_id),
        )
        database.notify(
            conn,
            int(row["seller_id"]),
            "수수료 입금 확인",
            f"수수료 ₩{int(row['fee_amount']):,} 입금이 확인되었습니다. 감사합니다.",
            "/app/#fees",
        )
        row = conn.execute("SELECT * FROM fee_invoices WHERE id = ?", (invoice_id,)).fetchone()
    return {"ok": True, "invoice": database.fee_invoice_to_dict(row)}


def _parse_iso_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        s = str(raw).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _vat_split_inclusive(fee_total: int, rate: float = 0.1) -> dict:
    """Treat received fee as VAT-inclusive total. supply + vat = fee_total."""
    fee_total = max(0, int(fee_total or 0))
    if fee_total <= 0:
        return {
            "gross_fee": 0,
            "supply": 0,
            "vat": 0,
            "net_after_vat": 0,
        }
    # supply = fee / 1.1
    supply = int(round(fee_total / (1.0 + rate)))
    vat = fee_total - supply
    return {
        "gross_fee": fee_total,
        "supply": supply,
        "vat": vat,
        "net_after_vat": supply,
    }


def _bucket_fee_stats(rows: list, *, start: datetime, end: datetime) -> dict:
    """Aggregate fee invoices in [start, end). Use paid_at for paid, created_at for pending."""
    deal_paid = 0
    fee_paid = 0
    fee_pending = 0
    deal_pending = 0
    count_paid = 0
    count_pending = 0
    for r in rows:
        status = (r["status"] or "").lower()
        if status == "paid":
            dt = _parse_iso_dt(r["paid_at"] or r["created_at"])
        else:
            dt = _parse_iso_dt(r["created_at"])
        if dt is None:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if not (start <= dt < end):
            continue
        fee = int(r["fee_amount"] or 0)
        deal = int(r["deal_amount"] or 0)
        if status == "paid":
            fee_paid += fee
            deal_paid += deal
            count_paid += 1
        else:
            fee_pending += fee
            deal_pending += deal
            count_pending += 1
    vat_paid = _vat_split_inclusive(fee_paid)
    vat_all_booked = _vat_split_inclusive(fee_paid + fee_pending)
    return {
        "start": start.isoformat(timespec="seconds"),
        "end": end.isoformat(timespec="seconds"),
        "deals_paid": count_paid,
        "deals_pending_fee": count_pending,
        "gmv_paid": deal_paid,
        "gmv_pending_fee": deal_pending,
        "fee_paid": fee_paid,
        "fee_pending": fee_pending,
        "fee_booked": fee_paid + fee_pending,
        "vat_on_paid": vat_paid["vat"],
        "supply_on_paid": vat_paid["supply"],
        "net_after_vat_paid": vat_paid["net_after_vat"],
        "vat_on_booked": vat_all_booked["vat"],
        "net_after_vat_booked": vat_all_booked["net_after_vat"],
    }


@router.get("/admin/revenue")
def admin_revenue(_: None = Depends(require_admin)):
    """
    Day / week / month fee revenue snapshot for ops.
    Source: fee_invoices (seller 10% platform fee).
    VAT: 10% estimated treating fee_amount as VAT-inclusive total.
    Income tax / local tax NOT included — ops/accounting must recalculate.
    """
    now = datetime.now(timezone.utc).astimezone()
    # local calendar day start
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = day_start - timedelta(days=day_start.weekday())  # Monday
    month_start = day_start.replace(day=1)
    day_end = day_start + timedelta(days=1)
    week_end = week_start + timedelta(days=7)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1)

    with database.db() as conn:
        rows = conn.execute(
            """
            SELECT id, deal_amount, fee_amount, status, created_at, paid_at
            FROM fee_invoices
            ORDER BY id DESC
            LIMIT 5000
            """
        ).fetchall()
        rows = list(rows)

    # all-time
    fee_paid_all = sum(int(r["fee_amount"] or 0) for r in rows if (r["status"] or "") == "paid")
    fee_pending_all = sum(int(r["fee_amount"] or 0) for r in rows if (r["status"] or "") != "paid")
    deal_paid_all = sum(int(r["deal_amount"] or 0) for r in rows if (r["status"] or "") == "paid")
    vat_all = _vat_split_inclusive(fee_paid_all)

    # last 14 days series
    days = []
    for i in range(13, -1, -1):
        d0 = day_start - timedelta(days=i)
        d1 = d0 + timedelta(days=1)
        b = _bucket_fee_stats(rows, start=d0, end=d1)
        days.append(
            {
                "label": d0.strftime("%m/%d"),
                "date": d0.date().isoformat(),
                **b,
            }
        )

    return {
        "ok": True,
        "as_of": now.isoformat(timespec="seconds"),
        "currency": "KRW",
        "fee_rate_pct": 10,
        "assumptions": {
            "vat_rate_pct": 10,
            "vat_mode": "inclusive",
            "note_ko": (
                "매출 = 판매자 수수료(거래가 10%) 장부 기준. "
                "부가세는 입금 확인된 수수료를 「부가세 포함 총액」으로 가정해 역산(공급가액=수수료÷1.1). "
                "종합소득세·지방세 등은 포함하지 않습니다. 세무 신고 전 세무사 확인 필수."
            ),
        },
        "periods": {
            "day": {
                "label": "오늘",
                **_bucket_fee_stats(rows, start=day_start, end=day_end),
            },
            "week": {
                "label": "이번 주(월~)",
                **_bucket_fee_stats(rows, start=week_start, end=week_end),
            },
            "month": {
                "label": "이번 달",
                **_bucket_fee_stats(rows, start=month_start, end=month_end),
            },
            "all": {
                "label": "전체",
                "fee_paid": fee_paid_all,
                "fee_pending": fee_pending_all,
                "fee_booked": fee_paid_all + fee_pending_all,
                "gmv_paid": deal_paid_all,
                "vat_on_paid": vat_all["vat"],
                "supply_on_paid": vat_all["supply"],
                "net_after_vat_paid": vat_all["net_after_vat"],
                "deals_paid": sum(1 for r in rows if (r["status"] or "") == "paid"),
                "deals_pending_fee": sum(1 for r in rows if (r["status"] or "") != "paid"),
            },
        },
        "series_days": days,
    }


@router.get("/notifications")
def list_notifications(user: dict = Depends(get_current_user)):
    with database.db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM notifications WHERE user_id = ?
            ORDER BY id DESC LIMIT 50
            """,
            (user["id"],),
        ).fetchall()
        unread = conn.execute(
            "SELECT COUNT(*) AS c FROM notifications WHERE user_id = ? AND is_read = 0",
            (user["id"],),
        ).fetchone()["c"]
    return {
        "ok": True,
        "unread": int(unread),
        "notifications": [database.notification_to_dict(r) for r in rows],
    }


@router.post("/notifications/read")
def mark_notifications_read(user: dict = Depends(get_current_user)):
    with database.db() as conn:
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
            (user["id"],),
        )
    return {"ok": True}


@router.get("/sellers/{owner_id}/stats")
def seller_stats(owner_id: int):
    with database.db() as conn:
        listed = conn.execute(
            "SELECT COUNT(*) AS c FROM projects WHERE owner_id = ? AND listing_status = 'approved'",
            (owner_id,),
        ).fetchone()["c"]
        sold = conn.execute(
            "SELECT COUNT(*) AS c FROM projects WHERE owner_id = ? AND auction_status = 'sold'",
            (owner_id,),
        ).fetchone()["c"]
        u = conn.execute(
            "SELECT * FROM users WHERE id = ?", (owner_id,)
        ).fetchone()
    return {
        "ok": True,
        "owner_id": owner_id,
        "display_name": (u["display_name"] if u else "") or "판매자",
        "approved_listings": int(listed),
        "sold_count": int(sold),
        "member_since": u["created_at"] if u else "",
        "credit": database.public_credit_summary(u) if u else None,
    }


@router.get("/credit-policy")
def credit_policy_public():
    """Public disclosure: how credit scores are calculated (auto)."""
    return {
        "ok": True,
        "scale": {"min": 0, "max": 100, "base": database.CREDIT_BASE},
        "rules": database.CREDIT_RULES,
        "grades": [
            {"min": 90, "max": 100, "grade": "elite", "label": "최고"},
            {"min": 75, "max": 89, "grade": "great", "label": "우수"},
            {"min": 60, "max": 74, "grade": "trusted", "label": "신뢰"},
            {"min": 40, "max": 59, "grade": "normal", "label": "보통"},
            {"min": 20, "max": 39, "grade": "new", "label": "신규"},
            {"min": 0, "max": 19, "grade": "risk", "label": "주의"},
        ],
        "formula_ko": [
            f"기본 {database.CREDIT_BASE}점",
            f"Lv2 신원 확인 +{database.CREDIT_RULES['l2_identity']}",
            f"Lv3 정산 계좌 +{database.CREDIT_RULES['l3_settlement']}",
            f"판매 성사 1건 +{database.CREDIT_RULES['sold_as_seller']} (최대 +{database.CREDIT_RULES['sold_as_seller_cap']})",
            f"구매 성사 1건 +{database.CREDIT_RULES['bought_complete']} (최대 +{database.CREDIT_RULES['bought_complete_cap']})",
            f"정시 입금(안내 기한 준수 · PG 후 1시간 목표) 1회 +{database.CREDIT_RULES['on_time_payment']} (최대 +{database.CREDIT_RULES['on_time_payment_cap']})",
            f"낙찰 후 미입금 1회 {database.CREDIT_RULES['default_unpaid']} (하한 0)",
            "최종 점수는 0~100으로 자동 반영 · 신뢰 레벨(Lv0~Lv3)과 별개",
        ],
        "buyer_rank": database.buyer_rank_policy(),
        "guide_url": "/guide/credit.html",
    }


class CreditDefaultIn(BaseModel):
    user_id: int
    note: str = Field(default="", max_length=300)


@router.post("/admin/credit/default")
def admin_credit_default(body: CreditDefaultIn, _: None = Depends(require_admin)):
    """Record unpaid-win / payment default → auto score drop."""
    with database.db() as conn:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (body.user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="user not found")
        credit = database.credit_bump(conn, int(body.user_id), defaults=1)
        database.notify(
            conn,
            int(body.user_id),
            "사이트 내 신용 점수 변동 · 미입금",
            (body.note or "낙찰 후 미입금이 기록되어 사이트 내 신용 점수가 낮아졌습니다.")[:400]
            + f" 현재 {credit['score']}점({credit['label']}).",
            "/guide/credit.html",
        )
        u = conn.execute("SELECT * FROM users WHERE id = ?", (body.user_id,)).fetchone()
    return {"ok": True, "user_id": body.user_id, "credit": database.compute_credit(u)}


@router.get("/pricing")
def pricing_guide():
    """Public: start-bid bands by product status (for sell forms / app)."""
    return {"ok": True, **price_policy.public_policy()}


@router.post("/uploads/demo")
async def upload_demo_image(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Upload one demo screenshot (JPEG/PNG/WebP, max ~1.5MB).
    Client should resize first. Auth required. Returns /media/… URL.
    """
    from wakeagain import media as media_mod

    raw = await file.read()
    try:
        saved = media_mod.save_demo_image(
            user_id=int(user["id"]),
            raw=raw,
            filename_hint=file.filename or "",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "upload_rejected", "message": str(e)},
        ) from e
    return {
        "ok": True,
        "url": saved["url"],
        "bytes": saved["bytes"],
        "ext": saved["ext"],
        "limits": {
            "max_bytes": media_mod.MAX_IMAGE_BYTES,
            "min_per_listing": media_mod.MIN_IMAGES_PER_LISTING,
            "max_per_listing": media_mod.MAX_IMAGES_PER_LISTING,
            "formats": ["jpg", "png", "webp"],
            "hint_ko": (
                f"장당 최대 약 1.5MB · 매물당 {media_mod.MIN_IMAGES_PER_LISTING}~"
                f"{media_mod.MAX_IMAGES_PER_LISTING}장 · 가로 1280px 권장"
            ),
        },
    }


@router.post("/projects")
def create_project(body: ProjectIn, request: Request, user: dict = Depends(get_current_user)):
    # refresh trust
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    user = database.user_to_dict(row_u)
    _require_trust(user, "list")

    # Minimum listing guidelines — no register without seller checkboxes
    if not body.attest_works:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "attest_works_required",
                "message": "등록 전 「지금 되는 것을 직접 확인」에 체크해 주세요.",
            },
        )
    if not body.attest_features:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "attest_features_required",
                "message": "등록 전 「하는 일·되는 것·안 되는 것이 사실」에 체크해 주세요.",
            },
        )
    if not body.attest_license:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "attest_license_required",
                "message": "등록 전 「라이선스·양도 조건을 적었다」에 체크해 주세요.",
            },
        )
    if not body.attest_rights:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "attest_rights_required",
                "message": "등록 전 「팔 권한이 있는 자산」에 체크해 주세요.",
            },
        )
    if not body.attest_transfer:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "attest_transfer_required",
                "message": "등록 전 「이전 절차를 끝까지 진행할 수 있다」에 체크해 주세요.",
            },
        )
    license_note = (body.license_note or "").strip()
    if len(license_note) < 2:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "license_note_required",
                "message": "라이선스 또는 양도 조건을 적어 주세요. (예: MIT, 사유 비공개 양도 등)",
            },
        )

    # ── 필수 필드 정책 (2026-08-15): 저장소 · 라이브 데모 · 마지막 활동일 ──
    # 신규 등록에만 강제. 기존 매물 수정(PUT)에서는 강제하지 않는다.
    is_private_repo = bool(body.is_private_repo)
    try:
        repo_url = _normalize_repo_url(body.repo_url)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "repo_url_invalid", "message": str(e)},
        ) from e

    is_offline = bool(body.is_offline)
    if is_offline:
        # 서비스가 이미 내려간 매물: 데모 URL 면제. 스크린샷은 아래에서 어차피 필수로 검증됨.
        live_url = ""
    else:
        try:
            live_url = _normalize_live_url(body.live_url)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={"code": "live_url_invalid", "message": str(e)},
            ) from e

    try:
        last_activity_at = _normalize_last_activity(body.last_activity_at)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "last_activity_invalid", "message": str(e)},
        ) from e

    features = [
        str(f).strip()
        for f in (body.features or [])
        if isinstance(f, str) and str(f).strip()
    ][:12]
    # 최소 등록: 2가지·각 8자 (더 쓰면 가산). 글 실력이 아니라 “뭐 하는지”만 있으면 통과
    features = [f[:120] for f in features if len(f) >= 8]
    if len(features) < 2:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "features_required",
                "message": "「이 제품이 하는 일」을 최소 2가지, 각 8자 이상 쉬운 말로 적어 주세요. 아래 예시 칩을 눌러도 됩니다.",
            },
        )

    audience = (body.audience or "").strip()
    if len(audience) < 4:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "audience_required",
                "message": "「누구를 위한 제품인가요?」를 짧게라도 적어 주세요. (예: 사장님, 학생)",
            },
        )

    works_now = (body.works_now or "").strip()
    if len(works_now) < 10:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "works_now_required",
                "message": "「지금 되는 것」을 10자 이상 적어 주세요. 예시 칩을 눌러 채울 수 있어요.",
            },
        )

    limits_note = (body.limits or "").strip()
    if len(limits_note) < 5:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "limits_required",
                "message": "「지금 안 되는 것 · 한계」를 짧게라도 적어 주세요. (예: 결제 없음)",
            },
        )

    acquisition = (body.acquisition or "").strip().lower()
    if acquisition not in ("made", "resale", "other"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "acquisition_required",
                "message": "매물 취득 경로(직접 제작 / 사서·양도받아 재판매 / 기타)를 선택해 주세요.",
            },
        )
    acquisition_note = (body.acquisition_note or "").strip()
    if acquisition in ("resale", "other") and len(acquisition_note) < 10:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "acquisition_note_required",
                "message": "재판매·기타인 경우 어떻게 취득했는지 10자 이상 적어 주세요.",
            },
        )

    story = body.story.strip()
    if len(story) < 10:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "story_too_short",
                "message": "「왜 팔나요?」를 10자 이상 적어 주세요. (예: 시간 없어서 넘깁니다)",
            },
        )

    from wakeagain import media as media_mod

    demo = (body.demo or "").strip()
    try:
        demo_images = media_mod.normalize_demo_images(
            list(body.demo_images or []), user_id=int(user["id"])
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "demo_images_invalid", "message": str(e)},
        ) from e

    if len(demo_images) < media_mod.MIN_IMAGES_PER_LISTING:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "demo_images_min",
                "message": (
                    f"실행 화면 스크린샷을 최소 {media_mod.MIN_IMAGES_PER_LISTING}장 이상 올려 주세요. "
                    f"(최대 {media_mod.MAX_IMAGES_PER_LISTING}장)"
                ),
            },
        )
    if demo_images and not body.attest_shots:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "attest_shots_required",
                "message": (
                    "스크린샷이 실제 실행 화면과 같다는 확인에 체크해 주세요. "
                    "실제 제품과 다른 화면은 매물 중단·이용 제한 대상이 될 수 있습니다."
                ),
            },
        )
    if not demo and demo_images:
        demo = f"스크린샷 {len(demo_images)}장 (실행 화면)"

    keywords = kw_mod.normalize_keywords(body.keywords or [])
    if len(keywords) < kw_mod.MIN_KEYWORDS:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "keywords_required",
                "message": f"검색 키워드를 {kw_mod.MIN_KEYWORDS}~{kw_mod.MAX_KEYWORDS}개 넣어 주세요. AI 추천 또는 직접 입력 가능합니다.",
            },
        )

    status = price_policy.normalize_status(body.status.strip())
    product_type = database.normalize_product_type(body.product_type)
    try:
        start, price_meta = price_policy.validate_start_price(
            status, body.price_start, lang=_lang_of(request)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "start_price_invalid",
                "message": str(e),
                "band": price_policy.pricing_for(status),
            },
        ) from e

    # min increment defaults to status band unless client sent higher
    band_inc = int(price_meta["suggested_increment"])
    min_inc = int(body.min_increment or band_inc)
    if min_inc < band_inc:
        min_inc = band_inc

    now = database._now()
    assets = [
        a.strip()
        for a in body.assets
        if isinstance(a, str) and a.strip()
    ][:20]
    if not assets:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "assets_required",
                "message": "포함 자산(코드·디자인·도메인 등)을 하나 이상 선택해 주세요. 실제로 넘길 수 있는 것만.",
            },
        )
    contact = (body.contact or user["email"]).strip()
    auction_days = int(body.auction_days or 7)
    auction_days = max(1, min(auction_days, 30))
    q_offered = database.normalize_q_credits_offered(body.q_credits_offered)
    q_unit = database.normalize_q_credit_unit_price(body.q_credit_unit_price)
    q_sla = database.normalize_q_credit_sla_hours(body.q_credit_sla_hours)
    # ends_at is provisional until approve; start_auction_round refreshes on go-live
    ends = _auction_end_iso(auction_days)

    # buy_now is optional; if set must be within range and >= start
    buy_now = body.price_buy_now
    if buy_now is not None:
        buy_now = int(buy_now)
        if buy_now > 100_000_000:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "buy_now_too_high",
                    "message": "즉시구매가는 최대 ₩100,000,000 까지입니다. 쓰지 않으려면 비워 두세요.",
                },
            )
        if buy_now < start:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "buy_now_too_low",
                    "message": f"즉시구매가는 시작가(₩{start:,}) 이상이어야 합니다. 쓰지 않으려면 비워 두세요.",
                },
            )

    attest = {
        "works": True,
        "features": True,
        "license": True,
        "rights": True,
        "transfer": True,
        "shots": bool(demo_images and body.attest_shots),
        "at": now,
    }
    title_ko = body.title.strip()
    one_ko = body.one_liner.strip()
    i18n_fields = listing_i18n.fill_listing_i18n(
        {
            "title": title_ko,
            "one_liner": one_ko,
            "story": story,
            "audience": audience[:120],
            "works_now": works_now[:500],
            "limits_note": limits_note[:500],
            "features": features,
            "keywords": keywords,
        },
        project_id="new",
        use_ai=True,
    )
    with database.db() as conn:
        cur = conn.execute(
            """
            INSERT INTO projects (
              owner_id, title, one_liner, title_en, one_liner_en, title_ko, one_liner_ko,
              status, product_type, story, story_en, story_ko, demo, demo_images_json, assets_json,
              keywords_json, keywords_json_en, keywords_json_ko,
              features_json, features_json_en, features_json_ko,
              audience, audience_en, audience_ko, works_now, works_now_en, works_now_ko,
              limits_note, limits_note_en, limits_note_ko,
              acquisition, acquisition_note,
              price_start, price_buy_now, contact, listing_status,
              price_current, bid_count, min_increment, auction_ends_at, auction_status,
              auction_days_intended, round_number, round_started_at,
              q_credits_offered, q_credit_unit_price, q_credit_sla_hours,
              license_note, seller_attest_json, english_ready,
              repo_url, is_private_repo, live_url, is_offline, last_activity_at,
              created_at, updated_at
            ) VALUES (
              ?, ?, ?, ?, ?, ?, ?,
              ?, ?, ?, ?, ?, ?, ?, ?,
              ?, ?, ?,
              ?, ?, ?,
              ?, ?, ?, ?, ?, ?,
              ?, ?, ?,
              ?, ?,
              ?, ?, ?, 'pending',
              ?, 0, ?, ?, 'pending',
              ?, 0, NULL,
              ?, ?, ?,
              ?, ?, ?,
              ?, ?, ?, ?, ?,
              ?, ?
            )
            """,
            (
                user["id"],
                title_ko,
                one_ko,
                i18n_fields.get("title_en") or None,
                i18n_fields.get("one_liner_en") or None,
                i18n_fields.get("title_ko") or None,
                i18n_fields.get("one_liner_ko") or None,
                status,
                product_type,
                story,
                i18n_fields.get("story_en") or None,
                i18n_fields.get("story_ko") or None,
                demo,
                json.dumps(demo_images, ensure_ascii=False),
                json.dumps(assets, ensure_ascii=False),
                json.dumps(keywords, ensure_ascii=False),
                i18n_fields.get("keywords_json_en") or None,
                i18n_fields.get("keywords_json_ko") or None,
                json.dumps(features, ensure_ascii=False),
                i18n_fields.get("features_json_en") or None,
                i18n_fields.get("features_json_ko") or None,
                audience[:120],
                i18n_fields.get("audience_en") or None,
                i18n_fields.get("audience_ko") or None,
                works_now[:500],
                i18n_fields.get("works_now_en") or None,
                i18n_fields.get("works_now_ko") or None,
                limits_note[:500],
                i18n_fields.get("limits_note_en") or None,
                i18n_fields.get("limits_note_ko") or None,
                acquisition,
                acquisition_note[:200] if acquisition_note else "",
                start,
                buy_now,
                contact,
                start,
                min_inc,
                ends,
                auction_days,
                q_offered,
                q_unit,
                q_sla,
                license_note[:200],
                json.dumps(attest, ensure_ascii=False),
                1 if body.english_ready else 0,
                repo_url,
                1 if is_private_repo else 0,
                live_url or None,
                1 if is_offline else 0,
                last_activity_at,
                now,
                now,
            ),
        )
        pid = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    try:
        from wakeagain import backup as db_backup

        db_backup.create_backup(reason="post-listing")
    except Exception as e:
        print(f"[create_project] post-listing backup failed: {e}", flush=True)
    ph_first50 = False
    try:
        with database.db() as conn2:
            database.redeem_coupon_code(conn2, int(user["id"]), PH_FIRST50_CODE)
        ph_first50 = True
        with database.db() as conn2:
            database.notify(
                conn2,
                int(user["id"]),
                "축하합니다 — 첫 50개 매물 수수료 0% 쿠폰 적용됨",
                "Product Hunt 런칭 프로모션(첫 50개 매물) 안에 드셔서 이 매물이 팔리면 성사 수수료가 0%로 적용됩니다.",
                f"/project.html?id={pid}",
            )
    except ValueError:
        pass  # already redeemed on this account, or the 50 slots are gone
    except Exception as e:
        print(f"[create_project] PH first-50 grant failed: {e}", flush=True)
    out: dict[str, Any] = {
        "ok": True,
        "project": database.project_to_dict(row, include_private=True),
        "ph_first50_applied": ph_first50,
        "pricing": {
            "status": status,
            "applied_start": start,
            "min_increment": min_inc,
            "band": price_meta["band"],
        },
        "note": (
            "등록됨 · 운영 형식 검수 후 이번 경매 라운드에 공개됩니다. "
            "유찰 시 목록에서 내려가며, 다시 올리려면 재검수가 필요합니다. "
            "검수는 보통 1~2영업일 · 품질 보증 아님."
        ),
        "review_sla": {
            "public_after": "approved_live_round",
            "typical": "1–2 business days",
            "message_ko": "등록 즉시 공개되지 않습니다. 운영 형식 검수 후 공개되며, 보통 1~2영업일 안에 게시 허용·보류·반려가 반영됩니다. 검수는 품질·가치 보증이 아닙니다.",
        },
    }
    if price_meta.get("soft_high_message"):
        out["warning"] = price_meta["soft_high_message"]
    return out


class RelistIn(BaseModel):
    """Seller re-enters the auction: requires re-review; joins back of queue on approve."""

    auction_days: int = Field(default=7, ge=1, le=30)
    # Optional updates before re-review (empty = keep existing)
    title: str | None = Field(default=None, max_length=80)
    one_liner: str | None = Field(default=None, max_length=120)
    story: str | None = Field(default=None, max_length=2000)
    demo: str | None = Field(default=None, max_length=1000)
    demo_images: list[str] | None = Field(default=None, max_length=5)
    features: list[str] | None = Field(default=None, max_length=12)
    audience: str | None = Field(default=None, max_length=120)
    works_now: str | None = Field(default=None, max_length=500)
    limits: str | None = Field(default=None, max_length=500)
    keywords: list[str] | None = Field(default=None, max_length=10)
    price_start: int | None = Field(default=None, ge=50_000, le=100_000_000)
    price_buy_now: int | None = Field(default=None, ge=50_000, le=100_000_000)
    license_note: str | None = Field(default=None, max_length=200)
    # 필수 필드 정책(2026-08-15) 보완 경로: 재등록 때 채워 넣을 수 있게 열어 두되 강제하지 않는다.
    # 정책상 기존 매물은 "보완 요청 후 미등록 배지" — 재등록을 막지 않는다.
    repo_url: str | None = Field(default=None, max_length=300)
    is_private_repo: bool | None = None
    live_url: str | None = Field(default=None, max_length=300)
    is_offline: bool | None = None
    last_activity_at: str | None = Field(default=None, max_length=7)
    attest_works: bool = False
    attest_features: bool = False
    attest_license: bool = False
    attest_rights: bool = False
    attest_transfer: bool = False
    attest_shots: bool = False


@router.post("/projects/{project_id}/relist")
def relist_project(
    project_id: int,
    body: RelistIn,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    After a round ends (unsold/archived) or is held/rejected:
    seller submits again → pending re-review → on approve, new round at back of queue.
    """
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    user = database.user_to_dict(row_u)
    _require_trust(user, "list")
    if user.get("is_suspended"):
        raise HTTPException(status_code=403, detail={"code": "account_suspended", "message": "정지된 계정입니다."})
    if not all(
        [
            body.attest_works,
            body.attest_features,
            body.attest_license,
            body.attest_rights,
            body.attest_transfer,
        ]
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "attest_required",
                "message": "재등록 시에도 동작·기능·권리·양도 확인에 모두 동의해 주세요.",
            },
        )

    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if int(row["owner_id"]) != int(user["id"]):
            raise HTTPException(status_code=403, detail="not your listing")
        ast = (row["auction_status"] or "") or ""
        ls = (row["listing_status"] or "") or ""
        if ast == "sold" or (row["sold_at"] if "sold_at" in row.keys() else None):
            raise HTTPException(
                status_code=400,
                detail={"code": "already_sold", "message": "성사된 매물은 재등록할 수 없습니다."},
            )
        if ls == "approved" and ast == "live":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "still_live",
                    "message": "진행 중인 라운드입니다. 마감 후 재등록할 수 있습니다.",
                },
            )
        if ls == "pending":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "already_pending",
                    "message": "이미 검수 대기 중입니다.",
                },
            )
        # Allowed: archived / ended / rejected / hold / paused
        allowed = ls in ("archived", "rejected", "hold") or ast in ("ended", "paused", "pending")
        if not allowed and not (ls == "approved" and ast == "ended"):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "not_relistable",
                    "message": "지금 상태에서는 재등록할 수 없습니다.",
                },
            )

        days = max(1, min(int(body.auction_days or 7), 30))
        now = database._now()
        # Optional field patches
        title = (body.title if body.title is not None else row["title"] or "").strip()
        one_liner = (
            body.one_liner if body.one_liner is not None else row["one_liner"] or ""
        ).strip()
        story = (body.story if body.story is not None else row["story"] or "").strip()
        demo = body.demo if body.demo is not None else (row["demo"] or "")
        if body.demo_images is not None:
            demo_images = [
                u
                for u in (body.demo_images or [])
                if isinstance(u, str) and u.startswith("/media/")
            ][:5]
        else:
            demo_images = database._parse_demo_images(row)
        if body.features is not None:
            features = [str(f).strip() for f in body.features if str(f).strip()][:12]
        else:
            try:
                features = json.loads(row["features_json"] or "[]")
            except Exception:
                features = []
        audience = (
            body.audience if body.audience is not None else (row["audience"] if "audience" in row.keys() else "") or ""
        )
        works_now = (
            body.works_now
            if body.works_now is not None
            else (row["works_now"] if "works_now" in row.keys() else "") or ""
        )
        limits_note = (
            body.limits
            if body.limits is not None
            else (row["limits_note"] if "limits_note" in row.keys() else "") or ""
        )
        if body.keywords is not None:
            keywords = kw_mod.normalize_keywords(body.keywords)
        else:
            try:
                keywords = json.loads(row["keywords_json"] or "[]")
            except Exception:
                keywords = []
        status = (row["status"] or "prototype") or "prototype"
        start = int(row["price_start"] or 0)
        if body.price_start is not None:
            try:
                start, _meta = price_policy.validate_start_price(
                    status, body.price_start, lang=_lang_of(request)
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail={"code": "start_price_invalid", "message": str(e)}) from e
        buy_now = row["price_buy_now"] if "price_buy_now" in row.keys() else None
        if body.price_buy_now is not None:
            buy_now = int(body.price_buy_now)
            if buy_now < start:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "buy_now_too_low", "message": "즉시구매가는 시작가 이상이어야 합니다."},
                )
        license_note = (
            body.license_note
            if body.license_note is not None
            else (row["license_note"] if "license_note" in row.keys() else "") or ""
        )
        if not title or not one_liner or not story:
            raise HTTPException(status_code=400, detail="title, one_liner, story required")
        if demo_images and not body.attest_shots:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "attest_shots_required",
                    "message": "스크린샷이 있으면 실제 제품 화면 확인에 동의해 주세요.",
                },
            )

        # 필수 필드 정책: 재등록에서는 강제하지 않는다. 값을 보냈을 때만 검증 후 반영하고,
        # 안 보내면 기존 값을 그대로 둔다 (미등록이면 미등록 배지가 계속 붙는다).
        def _keep(col: str) -> Any:
            return row[col] if col in row.keys() else None

        repo_url = _keep("repo_url")
        if body.repo_url is not None and body.repo_url.strip():
            try:
                repo_url = _normalize_repo_url(body.repo_url)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "repo_url_invalid", "message": str(e)},
                ) from e
        is_private_repo = (
            int(bool(body.is_private_repo))
            if body.is_private_repo is not None
            else int(bool(_keep("is_private_repo")))
        )
        is_offline = (
            bool(body.is_offline)
            if body.is_offline is not None
            else bool(_keep("is_offline"))
        )
        live_url = _keep("live_url")
        if is_offline:
            live_url = None
        elif body.live_url is not None and body.live_url.strip():
            try:
                live_url = _normalize_live_url(body.live_url)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "live_url_invalid", "message": str(e)},
                ) from e
        last_activity_at = _keep("last_activity_at")
        if body.last_activity_at is not None and body.last_activity_at.strip():
            try:
                last_activity_at = _normalize_last_activity(body.last_activity_at)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "last_activity_invalid", "message": str(e)},
                ) from e

        attest = {
            "works": True,
            "features": True,
            "license": True,
            "rights": True,
            "transfer": True,
            "shots": bool(demo_images and body.attest_shots),
            "at": now,
            "relist": True,
        }
        ends = _auction_end_iso(days)
        conn.execute(
            """
            UPDATE projects SET
              title = ?, one_liner = ?, story = ?, demo = ?, demo_images_json = ?,
              features_json = ?, audience = ?, works_now = ?, limits_note = ?,
              keywords_json = ?,
              price_start = ?, price_buy_now = ?, price_current = ?,
              license_note = ?, seller_attest_json = ?,
              repo_url = ?, is_private_repo = ?, live_url = ?,
              is_offline = ?, last_activity_at = ?,
              listing_status = 'pending',
              auction_status = 'pending',
              auction_days_intended = ?,
              auction_ends_at = ?,
              boost_until = NULL,
              boost_tier = 0,
              boost_product = NULL,
              paused_reason = '',
              deal_note = '재등록 · 재검수 대기',
              review_note = '',
              updated_at = ?
            WHERE id = ?
            """,
            (
                title[:80],
                one_liner[:120],
                story[:2000],
                (demo or "")[:1000],
                json.dumps(demo_images, ensure_ascii=False),
                json.dumps(features, ensure_ascii=False),
                (audience or "")[:120],
                (works_now or "")[:500],
                (limits_note or "")[:500],
                json.dumps(keywords, ensure_ascii=False),
                start,
                buy_now,
                start,
                (license_note or "")[:200],
                json.dumps(attest, ensure_ascii=False),
                repo_url,
                is_private_repo,
                live_url,
                1 if is_offline else 0,
                last_activity_at,
                days,
                ends,
                now,
                project_id,
            ),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        database.notify(
            conn,
            int(user["id"]),
            "재등록 접수",
            f"「{title}」 재등록이 접수되었습니다. 재검수 후 새 라운드로 게시되며 줄 맨 뒤부터 시작합니다.",
            "/app/#mine",
        )
    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=True),
        "note": (
            "재등록 접수 · 재검수 후 이번 라운드에 공개됩니다. "
            "승인 시 공개 목록 후순위(줄 맨 뒤)부터 시작합니다. "
            "오픈마켓식 끌올·도배 상위 노출이 아닙니다."
        ),
    }


class PriceUpdateIn(BaseModel):
    price_start: int = Field(ge=50_000, le=100_000_000)


@router.put("/projects/{project_id}/price")
def update_project_price(
    project_id: int,
    body: PriceUpdateIn,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    Seller adjusts the starting bid on a live, still-unbid round — up or down.
    Only before the first bid: once someone has bid, price_current already
    reflects that bid and the round is locked to relist instead.
    """
    with database.db() as conn:
        row_u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    user = database.user_to_dict(row_u)
    lang = _lang_of(request)
    en = lang.lower().startswith("en")

    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if int(row["owner_id"]) != int(user["id"]):
            raise HTTPException(status_code=403, detail="not your listing")
        row = _refresh_auction_ended(conn, row)
        ls = (row["listing_status"] or "") or ""
        ast = (row["auction_status"] or "") or ""
        if ls != "approved" or ast != "live":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "not_live",
                    "message": (
                        "This listing isn't in a live, open round right now."
                        if en
                        else "지금 진행 중인 라이브 경매 상태가 아닙니다."
                    ),
                },
            )
        if int(row["bid_count"] or 0) > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "bids_exist",
                    "message": (
                        "Bids have already come in, so the starting price is locked. "
                        "Wait for this round to end, then re-list at a new price."
                        if en
                        else "이미 입찰이 들어와서 시작가를 바꿀 수 없습니다. 이번 라운드가 끝난 뒤 재등록으로 새 가격을 정해 주세요."
                    ),
                },
            )

        status = (row["status"] or "prototype") or "prototype"
        try:
            start, _meta = price_policy.validate_start_price(status, body.price_start, lang=lang)
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"code": "start_price_invalid", "message": str(e)}) from e

        buy_now = row["price_buy_now"] if "price_buy_now" in row.keys() else None
        if buy_now is not None and int(buy_now) < start:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "buy_now_too_low",
                    "message": (
                        "The new starting price is above the buy-it-now price."
                        if en
                        else "새 시작가가 즉시구매가보다 높습니다."
                    ),
                },
            )

        now = database._now()
        conn.execute(
            """
            UPDATE projects
            SET price_start = ?, price_current = ?, updated_at = ?
            WHERE id = ?
            """,
            (start, start, now, project_id),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()

    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=True),
        "note": (
            "Starting price updated. It's visible to everyone immediately."
            if en
            else "시작가가 변경되었습니다. 즉시 전체 공개됩니다."
        ),
    }


class VerificationIn(BaseModel):
    """필수 필드 정책(2026-08-15) 보완 입력. 보낸 필드만 반영한다."""

    repo_url: str | None = Field(default=None, max_length=300)
    is_private_repo: bool | None = None
    live_url: str | None = Field(default=None, max_length=300)
    is_offline: bool | None = None
    last_activity_at: str | None = Field(default=None, max_length=7)


@router.put("/projects/{project_id}/verification")
def update_project_verification(
    project_id: int,
    body: VerificationIn,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """판매자가 저장소·라이브데모·마지막활동일을 나중에 채워 넣는다.

    필수 필드 정책은 신규 등록에만 강제되므로, 정책 이전에 올라간 매물은 값이 비어 있고
    "미등록" 배지가 붙는다. relist는 라이브 라운드에서 거부되기 때문에, 이 엔드포인트가
    없으면 기존 판매자는 정책을 지킬 방법 자체가 없다.

    입찰이 들어온 뒤에는 이미 채워진 값을 **바꿀 수 없다** (미끼 후 교체 방지).
    비어 있는 값을 채우는 것은 언제든 허용한다.
    """
    lang = _lang_of(request)
    en = lang.lower().startswith("en")

    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if int(row["owner_id"]) != int(user["id"]):
            raise HTTPException(status_code=403, detail="not your listing")

        def cur(col: str):
            return row[col] if col in row.keys() else None

        locked = int(row["bid_count"] or 0) > 0

        def guard(col: str, incoming) -> None:
            """입찰 후에는 이미 값이 있는 항목을 다른 값으로 바꿀 수 없다."""
            existing = (cur(col) or "") or ""
            if locked and existing and incoming and incoming != existing:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "locked_after_bid",
                        "message": (
                            "Bids have come in, so an existing link can't be swapped. "
                            "You can still fill in fields that are empty."
                            if en
                            else "입찰이 들어온 뒤에는 이미 등록된 링크를 다른 것으로 바꿀 수 없습니다. "
                            "비어 있는 항목을 채우는 것은 가능합니다."
                        ),
                    },
                )

        repo_url = cur("repo_url")
        if body.repo_url is not None and body.repo_url.strip():
            try:
                new_repo = _normalize_repo_url(body.repo_url)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "repo_url_invalid", "message": str(e)},
                ) from e
            guard("repo_url", new_repo)
            repo_url = new_repo

        is_private_repo = (
            int(bool(body.is_private_repo))
            if body.is_private_repo is not None
            else int(bool(cur("is_private_repo")))
        )
        is_offline = (
            bool(body.is_offline) if body.is_offline is not None else bool(cur("is_offline"))
        )

        live_url = cur("live_url")
        if is_offline:
            live_url = None
        elif body.live_url is not None and body.live_url.strip():
            try:
                new_live = _normalize_live_url(body.live_url)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "live_url_invalid", "message": str(e)},
                ) from e
            guard("live_url", new_live)
            live_url = new_live

        last_activity_at = cur("last_activity_at")
        if body.last_activity_at is not None and body.last_activity_at.strip():
            try:
                last_activity_at = _normalize_last_activity(body.last_activity_at)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "last_activity_invalid", "message": str(e)},
                ) from e

        # 데모 대안 경로: 서비스가 내려갔다면 스크린샷이 최소 1장은 있어야 한다
        if is_offline and not database._parse_demo_images(row):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "demo_images_min",
                    "message": (
                        "A shut-down product needs at least one screenshot."
                        if en
                        else "서비스가 내려간 매물은 스크린샷이 최소 1장 필요합니다."
                    ),
                },
            )

        conn.execute(
            """
            UPDATE projects SET
              repo_url = ?, is_private_repo = ?, live_url = ?,
              is_offline = ?, last_activity_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                repo_url,
                is_private_repo,
                live_url,
                1 if is_offline else 0,
                last_activity_at,
                database._now(),
                project_id,
            ),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()

    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=True),
        "note": (
            "Verification details updated. Badges refresh immediately."
            if en
            else "검증 정보가 갱신되었습니다. 배지에 즉시 반영됩니다."
        ),
    }


# --- admin review (ops checklist — not code review) ---

REVIEW_CHECKLIST = [
    {"id": "demo_ok", "label": "데모 URL/영상/스크린이 실제로 열리는가"},
    {"id": "not_idea_only", "label": "아이디어·문서만이 아닌가 (실행 흔적 있음)"},
    {"id": "features_ok", "label": "「하는 일」이 구체적인가 (이름·한 줄만으로 끝내지 않음)"},
    {"id": "works_limits_ok", "label": "되는 것 / 안 되는 것이 과장 없이 읽히는가"},
    {"id": "status_ok", "label": "제품 상태(프로토/베타/출시/기타)가 과하지 않은가"},
    {"id": "price_ok", "label": "시작가가 상태·근거에 비해 터무니없지 않은가"},
    {"id": "story_ok", "label": "왜 파는지(스토리)가 읽히는가"},
    {"id": "rights_ok", "label": "권리·양도·취득 경로가 납득 가능한가"},
    {"id": "no_scam", "label": "보장 수익·명백한 사기·권리 침해 티가 없는가"},
]


class AdminReviewIn(BaseModel):
    action: Literal["approve", "reject", "hold"]
    note: str = Field(default="", max_length=1000)
    checklist: dict[str, bool] = Field(default_factory=dict)


@router.get("/admin/session")
def admin_session(_: None = Depends(require_admin)):
    """Lightweight admin key check for ops UI / admin PWA install gate."""
    return {
        "ok": True,
        "role": "admin",
        "service": "WakeAgain",
        "surface": "admin",
    }


@router.get("/admin/checklist")
def admin_checklist(_: None = Depends(require_admin)):
    return {
        "ok": True,
        "title": "매물 검수 체크리스트 (코드 리뷰 아님)",
        "howto": [
            "데모 링크를 클릭해 본다.",
            "상태·가격·스토리만 본다. 코드는 읽지 않아도 된다.",
            "전부 통과면 게시 허용(형식 검수), 하나라도 실패면 반려 또는 보류. 품질 보증 아님.",
            "애매하면 보류 + 사유 한 줄.",
        ],
        "items": REVIEW_CHECKLIST,
        "actions": {
            "approve": "공개 마켓·입찰 오픈",
            "reject": "반려 (공개 안 함)",
            "hold": "보류 (추가 확인)",
        },
    }


@router.get("/admin/projects")
def admin_list_projects(
    status: str = "pending",
    _: None = Depends(require_admin),
):
    status = (status or "pending").strip().lower()
    allowed = {"pending", "approved", "rejected", "hold", "all"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail="status must be pending|approved|rejected|hold|all")
    with database.db() as conn:
        if status == "all":
            rows = conn.execute("SELECT * FROM projects ORDER BY id DESC LIMIT 200").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM projects WHERE listing_status = ? ORDER BY id DESC LIMIT 200",
                (status,),
            ).fetchall()
        projects = []
        for r in rows:
            p = database.project_to_dict(r, include_private=True)
            # owner email for ops contact
            u = conn.execute("SELECT email, display_name, real_name FROM users WHERE id = ?", (r["owner_id"],)).fetchone()
            if u:
                p["owner_email"] = u["email"]
                p["owner_label"] = u["display_name"] or u["real_name"] or u["email"]
            projects.append(p)
        counts = {
            "pending": conn.execute(
                "SELECT COUNT(*) AS c FROM projects WHERE listing_status = 'pending'"
            ).fetchone()["c"],
            "approved": conn.execute(
                "SELECT COUNT(*) AS c FROM projects WHERE listing_status = 'approved'"
            ).fetchone()["c"],
            "rejected": conn.execute(
                "SELECT COUNT(*) AS c FROM projects WHERE listing_status = 'rejected'"
            ).fetchone()["c"],
            "hold": conn.execute(
                "SELECT COUNT(*) AS c FROM projects WHERE listing_status = 'hold'"
            ).fetchone()["c"],
        }
    return {"ok": True, "counts": counts, "projects": projects, "checklist": REVIEW_CHECKLIST}


@router.put("/admin/projects/{project_id}/verification")
def admin_update_project_verification(
    project_id: int,
    body: VerificationIn,
    _: None = Depends(require_admin),
):
    """운영자용 검증정보 보완.

    정책 이전 매물 중에는 시드 스크립트가 만든 운영 계정(corelabs.seller@…) 소유가 있어
    판매자 로그인으로는 손댈 수 없다. 소유자용 엔드포인트와 같은 검증을 쓰되 소유권만 건너뛴다.
    입찰 후 링크 교체 방지 가드는 운영자에게 적용하지 않는다 — 데이터 정정이 목적이기 때문.
    """
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")

        def cur(col: str):
            return row[col] if col in row.keys() else None

        repo_url = cur("repo_url")
        if body.repo_url is not None and body.repo_url.strip():
            try:
                repo_url = _normalize_repo_url(body.repo_url)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail={"code": "repo_url_invalid", "message": str(e)}
                ) from e

        is_private_repo = (
            int(bool(body.is_private_repo))
            if body.is_private_repo is not None
            else int(bool(cur("is_private_repo")))
        )
        is_offline = (
            bool(body.is_offline) if body.is_offline is not None else bool(cur("is_offline"))
        )

        live_url = cur("live_url")
        if is_offline:
            live_url = None
        elif body.live_url is not None and body.live_url.strip():
            try:
                live_url = _normalize_live_url(body.live_url)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail={"code": "live_url_invalid", "message": str(e)}
                ) from e

        last_activity_at = cur("last_activity_at")
        if body.last_activity_at is not None and body.last_activity_at.strip():
            try:
                last_activity_at = _normalize_last_activity(body.last_activity_at)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail={"code": "last_activity_invalid", "message": str(e)}
                ) from e

        if is_offline and not database._parse_demo_images(row):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "demo_images_min",
                    "message": "서비스가 내려간 매물은 스크린샷이 최소 1장 필요합니다.",
                },
            )

        conn.execute(
            """
            UPDATE projects SET
              repo_url = ?, is_private_repo = ?, live_url = ?,
              is_offline = ?, last_activity_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                repo_url,
                is_private_repo,
                live_url,
                1 if is_offline else 0,
                last_activity_at,
                database._now(),
                project_id,
            ),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()

    return {"ok": True, "project": database.project_to_dict(row, include_private=True)}


class AdminTradeNameEnIn(BaseModel):
    trade_name_en: str = Field(default="", max_length=80)


@router.put("/admin/users/{user_id}/trade-name-en")
def admin_set_trade_name_en(
    user_id: int,
    body: AdminTradeNameEnIn,
    _: None = Depends(require_admin),
):
    """운영자가 판매자의 영문 상호만 설정한다.

    매물 일부는 시드 스크립트가 만든 운영 계정(corelabs.seller@…) 소유라 본인 로그인으로
    프로필을 고칠 수 없다. 관리자가 사용자 정보를 통째로 수정할 수 있게 열면 위험 범위가
    너무 커지므로, 바꿀 수 있는 값을 이 한 필드로 제한한다. 빈 문자열이면 해제(한글 상호로 폴백).
    """
    name_en = (body.trade_name_en or "").strip()
    with database.db() as conn:
        row = conn.execute("SELECT id, email FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="user not found")
        conn.execute(
            "UPDATE users SET seller_trade_name_en = ?, profile_updated_at = ? WHERE id = ?",
            (name_en, database._now(), user_id),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return {
        "ok": True,
        "user_id": user_id,
        "email": row["email"],
        "trade_name": (row["seller_trade_name"] or ""),
        "trade_name_en": (row["seller_trade_name_en"] or ""),
    }


class AdminTransferOwnerIn(BaseModel):
    new_owner_id: int | None = None
    new_owner_email: str | None = None
    note: str = ""


_TRANSFER_BLOCKER_MSG = {
    "bids_exist": "이미 입찰이 들어온 매물입니다. 입찰자가 지금 판매자를 믿고 넣은 것이라 명의를 못 바꿉니다. 라운드가 끝난 뒤 새 계정으로 재등록하세요.",
    "already_sold": "이미 낙찰·판매된 매물이라 명의를 바꿀 수 없습니다.",
    "deal_in_progress": "거래(딜)가 진행 중인 매물이라 명의를 바꿀 수 없습니다.",
    "fee_invoice_exists": "수수료 청구서가 발행된 매물이라 명의를 바꿀 수 없습니다.",
    "help_tickets_exist": "헬프티켓 문의가 오간 매물이라 명의를 바꿀 수 없습니다.",
}


@router.post("/admin/projects/{project_id}/transfer-owner")
def admin_transfer_project_owner(
    project_id: int,
    body: AdminTransferOwnerIn,
    _: None = Depends(require_admin),
):
    """운영자가 매물의 판매자 계정을 옮긴다 (위탁 등록 매물 인계용).

    원 소유자 동의를 받고 코어랩스 계정으로 대신 올린 매물을, 본인이 가입하면 그 계정으로
    넘겨주기 위한 경로다 (CLAUDE.md 「위탁 등록 매물」). 소유자는 원래 생성 시점에만 정해지고
    이후 불변인데, 입찰·거래·수수료·헬프티켓이 전부 "판매자가 누구인가"에 묶여 있기 때문이다.
    그래서 그 이력이 하나라도 붙은 매물은 옮기지 않고 거부한다 — 옮기면 이력이 조용히 바뀐다.

    대상 계정은 id 또는 이메일로 지정한다(관리자 화면에선 이메일이 편하다).
    """
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")

        if body.new_owner_id:
            target = conn.execute(
                "SELECT * FROM users WHERE id = ?", (int(body.new_owner_id),)
            ).fetchone()
        elif (body.new_owner_email or "").strip():
            target = conn.execute(
                "SELECT * FROM users WHERE email = ?", ((body.new_owner_email or "").strip(),)
            ).fetchone()
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "target_required",
                    "message": "넘겨받을 계정의 id 또는 이메일을 지정해 주세요.",
                },
            )
        if not target:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "target_not_found",
                    "message": "그 계정을 찾을 수 없습니다. 상대가 아직 가입하지 않았을 수 있습니다.",
                },
            )
        if int(target["id"]) == int(row["owner_id"]):
            raise HTTPException(
                status_code=400,
                detail={"code": "same_owner", "message": "이미 그 계정의 매물입니다."},
            )
        if (target["suspended_at"] if "suspended_at" in target.keys() else None):
            raise HTTPException(
                status_code=400,
                detail={"code": "target_suspended", "message": "정지된 계정으로는 넘길 수 없습니다."},
            )

        blockers = database.project_transfer_blockers(conn, project_id)
        if blockers:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": blockers[0],
                    "codes": blockers,
                    "message": " / ".join(
                        _TRANSFER_BLOCKER_MSG.get(c, c) for c in blockers
                    ),
                },
            )

        prev_owner_id = int(row["owner_id"])
        row = database.transfer_project_owner(
            conn, project_id, int(target["id"]), note=(body.note or "").strip()
        )

    return {
        "ok": True,
        "project_id": project_id,
        "prev_owner_id": prev_owner_id,
        "new_owner_id": int(target["id"]),
        "new_owner_email": target["email"],
        "project": database.project_to_dict(row, include_private=True),
    }


class AdminImagesIn(BaseModel):
    demo_images: list[str] = Field(default_factory=list, max_length=5)


@router.put("/admin/projects/{project_id}/images")
def admin_update_project_images(
    project_id: int,
    body: AdminImagesIn,
    _: None = Depends(require_admin),
):
    """
    Ops-only image fix for an already-live listing (e.g. replacing a wrong/duplicate
    screenshot) without touching listing_status/auction_status/auction_ends_at —
    unlike /relist, which forces the listing back into 'pending' review.
    """
    urls = [u for u in (body.demo_images or []) if isinstance(u, str) and u.startswith("/media/")][:5]
    with database.db() as conn:
        row = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute(
            "UPDATE projects SET demo_images_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(urls, ensure_ascii=False), database._now(), project_id),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return {"ok": True, "project": database.project_to_dict(row, include_private=True)}


@router.post("/admin/projects/{project_id}/images/upload")
async def admin_upload_project_image(
    project_id: int,
    file: UploadFile = File(...),
    _: None = Depends(require_admin),
):
    """
    Ops-only: upload one screenshot for a listing without needing the seller's own
    login session. Saved under the listing's owner_id so it behaves like a normal
    seller upload; does not touch demo_images_json — call PUT .../images after to
    actually attach the returned url(s) to the listing.
    """
    from wakeagain import media as media_mod

    with database.db() as conn:
        row = conn.execute("SELECT owner_id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    raw = await file.read()
    try:
        saved = media_mod.save_demo_image(
            user_id=int(row["owner_id"]),
            raw=raw,
            filename_hint=file.filename or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "upload_rejected", "message": str(e)}) from e
    return {"ok": True, "url": saved["url"], "bytes": saved["bytes"], "ext": saved["ext"]}


@router.post("/admin/projects/{project_id}/review")
def admin_review_project(
    project_id: int,
    body: AdminReviewIn,
    _: None = Depends(require_admin),
):
    action = body.action
    status_map = {"approve": "approved", "reject": "rejected", "hold": "hold"}
    new_status = status_map[action]
    now = database._now()
    checklist = {k: bool(v) for k, v in (body.checklist or {}).items()}

    # Approve: recommend all checklist true (soft warn only if missing)
    if action == "approve":
        missing = [c["id"] for c in REVIEW_CHECKLIST if not checklist.get(c["id"])]
        # still allow approve if ops forces — they know better
        pass
    else:
        missing = []

    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        demo_ok = 1 if checklist.get("demo_ok") else 0
        if action == "approve":
            # Start a fresh public auction round (queue position = round_started_at now)
            conn.execute(
                """
                UPDATE projects
                SET review_note = ?, review_checklist_json = ?, demo_verified = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    (body.note or "").strip(),
                    json.dumps(checklist, ensure_ascii=False),
                    demo_ok,
                    now,
                    project_id,
                ),
            )
            days = int(row["auction_days_intended"] or 7) if "auction_days_intended" in row.keys() else 7
            row = database.start_auction_round(
                conn, project_id, auction_days=days, clear_boost=True
            )
        else:
            conn.execute(
                """
                UPDATE projects
                SET listing_status = ?, review_note = ?, reviewed_at = ?,
                    review_checklist_json = ?, demo_verified = CASE WHEN ? = 'approved' THEN ? ELSE demo_verified END,
                    auction_status = CASE
                      WHEN ? IN ('reject', 'hold') THEN COALESCE(auction_status, 'pending')
                      ELSE auction_status
                    END,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    new_status,
                    (body.note or "").strip(),
                    now,
                    json.dumps(checklist, ensure_ascii=False),
                    new_status,
                    demo_ok,
                    action,
                    now,
                    project_id,
                ),
            )
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        titles = {
            "approve": "이번 라운드 게시",
            "reject": "매물 반려",
            "hold": "매물 보류",
        }
        bodies = {
            "approve": (
                f"「{row['title']}」이(가) 이번 경매 라운드에 공개되었습니다. "
                f"마감 후 유찰되면 목록에서 내려갑니다."
            ),
            "reject": f"「{row['title']}」이(가) 반려되었습니다. {body.note or ''}".strip(),
            "hold": f"「{row['title']}」이(가) 보류되었습니다. {body.note or ''}".strip(),
        }
        database.notify(
            conn,
            int(row["owner_id"]),
            titles[action],
            bodies[action][:1000],
            f"/project.html?id={project_id}" if action == "approve" else "/app/#mine",
        )
    return {
        "ok": True,
        "project": database.project_to_dict(row, include_private=True),
        "action": action,
        "checklist_unchecked_on_approve": missing if action == "approve" else [],
    }


@router.get("/admin/reports")
def admin_list_reports(
    status: str = "open",
    _: None = Depends(require_admin),
):
    allowed = {"open", "resolved", "dismissed", "all"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail="status must be open|resolved|dismissed|all")
    with database.db() as conn:
        if status == "all":
            rows = conn.execute(
                """
                SELECT r.*, p.title AS project_title, p.owner_id, p.auction_status,
                       u.email AS reporter_email, o.email AS owner_email
                FROM reports r
                JOIN projects p ON p.id = r.project_id
                JOIN users u ON u.id = r.reporter_id
                JOIN users o ON o.id = p.owner_id
                ORDER BY r.id DESC LIMIT 300
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT r.*, p.title AS project_title, p.owner_id, p.auction_status,
                       u.email AS reporter_email, o.email AS owner_email
                FROM reports r
                JOIN projects p ON p.id = r.project_id
                JOIN users u ON u.id = r.reporter_id
                JOIN users o ON o.id = p.owner_id
                WHERE r.status = ?
                ORDER BY r.id DESC LIMIT 300
                """,
                (status,),
            ).fetchall()
        counts = {
            "open": conn.execute(
                "SELECT COUNT(*) AS c FROM reports WHERE status = 'open'"
            ).fetchone()["c"],
            "resolved": conn.execute(
                "SELECT COUNT(*) AS c FROM reports WHERE status = 'resolved'"
            ).fetchone()["c"],
            "dismissed": conn.execute(
                "SELECT COUNT(*) AS c FROM reports WHERE status = 'dismissed'"
            ).fetchone()["c"],
        }
    out = []
    for r in rows:
        d = database.report_to_dict(r)
        d["project_title"] = r["project_title"]
        d["owner_id"] = r["owner_id"]
        d["auction_status"] = r["auction_status"]
        d["reporter_email"] = r["reporter_email"]
        d["owner_email"] = r["owner_email"]
        out.append(d)
    return {
        "ok": True,
        "counts": {k: int(v) for k, v in counts.items()},
        "reports": out,
        "policy": {
            "pause_threshold": database.REPORT_PAUSE_THRESHOLD,
            "account_suspend_threshold": database.REPORT_ACCOUNT_SUSPEND_THRESHOLD,
        },
    }


class AdminReportResolveIn(BaseModel):
    action: Literal["resolve", "dismiss"] = "resolve"
    note: str = Field(default="", max_length=500)


@router.post("/admin/reports/{report_id}/resolve")
def admin_resolve_report(
    report_id: int,
    body: AdminReportResolveIn,
    _: None = Depends(require_admin),
):
    new_status = "resolved" if body.action == "resolve" else "dismissed"
    with database.db() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute(
            """
            UPDATE reports
            SET status = ?, resolved_at = ?, resolve_note = ?
            WHERE id = ?
            """,
            (new_status, database._now(), (body.note or "").strip(), report_id),
        )
        # refresh project report_count (open only)
        pid = int(row["project_id"])
        open_c = database.count_open_reports(conn, pid)
        conn.execute(
            "UPDATE projects SET report_count = ?, updated_at = ? WHERE id = ?",
            (open_c, database._now(), pid),
        )
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    return {"ok": True, "report": database.report_to_dict(row)}


class AdminResumeIn(BaseModel):
    """Re-open policy: default re-queues for review; force starts a new live round (back of queue)."""

    auction_days: int = Field(default=7, ge=1, le=30)
    force_live: bool = False
    note: str = Field(default="", max_length=500)


@router.post("/admin/projects/{project_id}/resume-auction")
def admin_resume_auction(
    project_id: int,
    body: AdminResumeIn | None = None,
    _: None = Depends(require_admin),
):
    body = body or AdminResumeIn()
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        ast = (row["auction_status"] or "") or ""
        if ast == "sold" or (row["sold_at"] if "sold_at" in row.keys() else None):
            raise HTTPException(status_code=400, detail="already sold")
        if ast not in ("paused", "ended", "pending") and (row["listing_status"] or "") not in (
            "archived",
            "hold",
            "rejected",
            "pending",
        ):
            raise HTTPException(
                status_code=400,
                detail="auction is not paused/ended/archived — nothing to resume",
            )
        days = int(body.auction_days or 7)
        if body.force_live:
            # Emergency ops: new round now, back of queue (round_started_at = now)
            conn.execute(
                """
                UPDATE projects SET auction_days_intended = ?, review_note = ?, updated_at = ?
                WHERE id = ?
                """,
                (days, (body.note or "admin force live round").strip()[:500], database._now(), project_id),
            )
            row = database.start_auction_round(
                conn, project_id, auction_days=days, clear_boost=True
            )
            database.notify(
                conn,
                int(row["owner_id"]),
                "새 라운드 강제 게시",
                f"「{row['title']}」 운영자가 새 경매 라운드를 열었습니다. (후순위 정렬)",
                f"/project.html?id={project_id}",
            )
            return {
                "ok": True,
                "mode": "force_live",
                "project": database.project_to_dict(row, include_private=True),
            }
        # Default: re-queue for review (same discipline as seller relist)
        conn.execute(
            """
            UPDATE projects
            SET listing_status = 'pending',
                auction_status = 'pending',
                auction_days_intended = ?,
                paused_reason = '',
                review_note = ?,
                boost_until = NULL,
                boost_tier = 0,
                updated_at = ?
            WHERE id = ?
            """,
            (
                days,
                (body.note or "재개 요청 · 재검수 대기").strip()[:500],
                database._now(),
                project_id,
            ),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        database.notify(
            conn,
            int(row["owner_id"]),
            "재검수 대기",
            f"「{row['title']}」 다시 올리기 위해 운영 검수 대기 중입니다.",
            "/app/#mine",
        )
    return {
        "ok": True,
        "mode": "pending_review",
        "project": database.project_to_dict(row, include_private=True),
        "note": "재검수 후 승인 시 새 라운드로 게시되며 줄 맨 뒤(후순위)부터 시작합니다.",
    }


@router.get("/admin/listing-collection-mode")
def admin_get_listing_collection_mode(_: None = Depends(require_admin)):
    with database.db() as conn:
        pending = conn.execute(
            """
            SELECT COUNT(*) AS n FROM projects
            WHERE listing_status = 'approved'
              AND COALESCE(auction_status, 'live') = 'live'
              AND (auction_ends_at IS NULL OR auction_ends_at = '')
            """
        ).fetchone()
    return {
        "ok": True,
        "enabled": database.listing_collection_mode(),
        "waiting_count": int(pending["n"] or 0),
        "note": "WA_LISTING_COLLECTION_MODE 환경변수로 켜고 끕니다 (재배포 필요). 켜져 있으면 승인된 매물은 공개 목록엔 뜨지만 경매 타이머는 시작되지 않습니다.",
    }


@router.post("/admin/auctions/release-all")
def admin_release_all_auctions(_: None = Depends(require_admin)):
    """Launch-day trigger: start the countdown for every listing that's been
    sitting live with no auction clock (listing_collection_mode backlog)."""
    with database.db() as conn:
        rows = conn.execute(
            """
            SELECT id, owner_id, title FROM projects
            WHERE listing_status = 'approved'
              AND COALESCE(auction_status, 'live') = 'live'
              AND (auction_ends_at IS NULL OR auction_ends_at = '')
            """
        ).fetchall()
        released = database.release_all_paused_auctions(conn)
        for row in rows:
            database.notify(
                conn,
                int(row["owner_id"]),
                "경매 시작",
                f"「{row['title']}」 경매가 지금부터 시작되어 카운트다운이 흐릅니다.",
                f"/project.html?id={row['id']}",
            )
    return {
        "ok": True,
        "released": released,
        "note": "released 건수만큼 auction_ends_at이 지금부터 카운트다운 시작으로 설정되었습니다. WA_LISTING_COLLECTION_MODE는 별도로 꺼야 이후 신규 승인 매물도 정상적으로 타이머가 붙습니다.",
    }


def _admin_user_row(conn: Any, row: Any, *, full: bool = False) -> dict[str, Any]:
    """Admin-facing user summary (full PII — never expose on public APIs)."""
    u = database.user_to_dict(row)
    phone_raw = (row["phone"] if "phone" in row.keys() else None) or ""
    real_name = (row["real_name"] if "real_name" in row.keys() else None) or ""
    out: dict[str, Any] = {
        "id": int(row["id"]),
        "email": (row["email"] or "").strip(),
        "display_name": (row["display_name"] or "").strip(),
        "real_name": real_name,
        "phone": phone_raw,
        "phone_display": database.format_phone_display(phone_raw) if phone_raw else "",
        "role": (row["role"] if "role" in row.keys() else None) or "both",
        "email_verified": bool(int(row["email_verified"] or 0)),
        "created_at": (row["created_at"] or ""),
        "trust": u.get("trust") or {},
        "is_suspended": bool(int(row["is_suspended"] or 0)) if "is_suspended" in row.keys() else False,
        "suspended_at": (row["suspended_at"] if "suspended_at" in row.keys() else None) or "",
        "suspend_reason": (row["suspend_reason"] if "suspend_reason" in row.keys() else None) or "",
        "oauth_provider": (row["oauth_provider"] if "oauth_provider" in row.keys() else None) or "",
        "auth_method": (
            (row["oauth_provider"] if "oauth_provider" in row.keys() else None) or ""
        )
        or "password",
        "profile_updated_at": (row["profile_updated_at"] if "profile_updated_at" in row.keys() else None)
        or "",
        "welcome_mailed_at": (row["welcome_mailed_at"] if "welcome_mailed_at" in row.keys() else None)
        or "",
    }
    if full:
        uid = int(row["id"])
        projects_n = conn.execute(
            "SELECT COUNT(*) AS c FROM projects WHERE owner_id = ?", (uid,)
        ).fetchone()["c"]
        live_n = conn.execute(
            """
            SELECT COUNT(*) AS c FROM projects
            WHERE owner_id = ? AND listing_status = 'approved'
              AND COALESCE(auction_status, 'live') = 'live'
            """,
            (uid,),
        ).fetchone()["c"]
        bids_n = 0
        try:
            bids_n = conn.execute(
                "SELECT COUNT(*) AS c FROM bids WHERE user_id = ?", (uid,)
            ).fetchone()["c"]
        except Exception:
            bids_n = 0
        deals_n = 0
        try:
            deals_n = conn.execute(
                """
                SELECT COUNT(*) AS c FROM projects
                WHERE owner_id = ? AND COALESCE(auction_status, '') IN ('sold', 'closed')
                """,
                (uid,),
            ).fetchone()["c"]
        except Exception:
            deals_n = 0
        out["stats"] = {
            "projects": int(projects_n),
            "live_projects": int(live_n),
            "bids": int(bids_n),
            "sold_or_closed": int(deals_n),
        }
        out["settlement"] = (u.get("settlement") or {})
        out["seller_identity"] = (u.get("seller_identity") or {})
        out["credit"] = (u.get("credit") or {})
        out["buyer_rank"] = (u.get("buyer_rank") or {})
        out["birth_date"] = (row["birth_date"] if "birth_date" in row.keys() else None) or ""
    return out


class AdminPurgeUsersIn(BaseModel):
    """회원 전체 삭제 확인 — confirm 문자열이 정확히 일치해야 함."""
    confirm: str = Field(min_length=8, max_length=40)


class AdminPurgeExceptIn(BaseModel):
    """남길 이메일 외 회원 삭제 — confirm 문자열이 정확히 일치해야 함."""
    confirm: str = Field(min_length=8, max_length=40)
    keep_emails: list[str] = Field(default_factory=list, max_length=20)


class AdminDeleteUsersIn(BaseModel):
    """선택 회원 삭제 — 관리자 UI 체크박스용."""
    confirm: str = Field(min_length=8, max_length=40)
    user_ids: list[int] = Field(default_factory=list, max_length=50)


def _destructive_admin_allowed() -> bool:
    """Hard gate: purge/restore only when operator explicitly enables ALLOW_DESTRUCTIVE_ADMIN=1."""
    return (os.environ.get("ALLOW_DESTRUCTIVE_ADMIN") or "").strip() in {"1", "true", "TRUE", "yes", "on"}


def _require_destructive_admin() -> None:
    if not _destructive_admin_allowed():
        raise HTTPException(
            status_code=403,
            detail={
                "code": "destructive_locked",
                "message": (
                    "파괴적 관리 작업이 잠겨 있습니다. "
                    "ALLOW_DESTRUCTIVE_ADMIN=1 을 설정한 뒤에만 가능합니다. "
                    "(실수 방지 — 기본 차단)"
                ),
            },
        )


def _table_has(conn: Any, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 AS ok FROM sqlite_master WHERE type='table' AND name = ?",
        (name,),
    ).fetchone()
    return bool(row)


def _delete_users_by_ids(conn: Any, drop_ids: list[int]) -> dict[str, Any]:
    """Cascade-delete the given user ids and related rows. Returns stats."""
    drop_ids = sorted({int(i) for i in drop_ids if int(i) > 0})
    deleted: dict[str, int] = {}
    if not drop_ids:
        return {"deleted": deleted, "dropped_emails": [], "dropped_ids": []}

    rows = conn.execute(
        f"SELECT id, email FROM users WHERE id IN ({','.join('?' for _ in drop_ids)})",
        drop_ids,
    ).fetchall()
    # Only ids that actually exist
    drop_ids = [int(r["id"]) for r in rows]
    dropped_emails = [str(r["email"]) for r in rows]
    if not drop_ids:
        return {"deleted": deleted, "dropped_emails": [], "dropped_ids": []}

    placeholders = ",".join("?" for _ in drop_ids)

    def _del(sql: str, params: tuple | list = ()) -> int:
        cur = conn.execute(sql, params)
        return int(cur.rowcount or 0)

    try:
        deleted["bids_as_bidder"] = _del(
            f"DELETE FROM bids WHERE bidder_id IN ({placeholders})", drop_ids
        )
    except Exception as e:
        deleted["bids_as_bidder"] = -1
        print(f"[admin delete-users] bids: {e}", flush=True)

    try:
        proj_ids = [
            int(r["id"])
            for r in conn.execute(
                f"SELECT id FROM projects WHERE owner_id IN ({placeholders})", drop_ids
            ).fetchall()
        ]
        if proj_ids:
            pp = ",".join("?" for _ in proj_ids)
            deleted["bids_on_dropped_projects"] = _del(
                f"DELETE FROM bids WHERE project_id IN ({pp})", proj_ids
            )
            if _table_has(conn, "reports"):
                deleted["reports_on_dropped_projects"] = _del(
                    f"DELETE FROM reports WHERE project_id IN ({pp})", proj_ids
                )
            deleted["projects"] = _del(
                f"DELETE FROM projects WHERE id IN ({pp})", proj_ids
            )
        else:
            deleted["projects"] = 0
    except Exception as e:
        deleted["projects"] = -1
        print(f"[admin delete-users] projects: {e}", flush=True)

    for table, col in (
        ("messages", "sender_id"),
        ("messages", "recipient_id"),
        ("notifications", "user_id"),
        ("fee_invoices", "user_id"),
        ("reports", "reporter_id"),
        ("user_blocks", "blocker_id"),
        ("user_blocks", "blocked_id"),
        ("interests", "user_id"),
        ("reviews", "user_id"),
        ("showcases", "user_id"),
        ("user_coupons", "user_id"),
        ("promo_submissions", "user_id"),
        ("leads", "user_id"),
    ):
        key = f"{table}_{col}"
        try:
            if not _table_has(conn, table):
                deleted[key] = 0
                continue
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            if col not in cols:
                deleted[key] = 0
                continue
            deleted[key] = _del(
                f"DELETE FROM {table} WHERE {col} IN ({placeholders})", drop_ids
            )
        except Exception as e:
            deleted[key] = -1
            print(f"[admin delete-users] {key}: {e}", flush=True)

    try:
        if _table_has(conn, "projects"):
            pcols = {r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()}
            if "buyer_id" in pcols:
                deleted["projects_clear_buyer"] = _del(
                    f"UPDATE projects SET buyer_id = NULL WHERE buyer_id IN ({placeholders})",
                    drop_ids,
                )
    except Exception as e:
        deleted["projects_clear_buyer"] = -1
        print(f"[admin delete-users] clear buyer: {e}", flush=True)

    deleted["users"] = _del(f"DELETE FROM users WHERE id IN ({placeholders})", drop_ids)

    return {
        "deleted": deleted,
        "dropped_emails": dropped_emails,
        "dropped_ids": drop_ids,
    }


def _purge_users_except_emails(conn: Any, keep_emails: list[str]) -> dict[str, Any]:
    """
    Delete all users whose email is not in keep_emails (case-insensitive),
    plus their related rows. Kept users and their owned data remain.
    """
    keep_norm = sorted({(e or "").strip().lower() for e in keep_emails if (e or "").strip()})
    if not keep_norm:
        raise ValueError("keep_emails must contain at least one email")

    keep_rows = conn.execute(
        f"SELECT id, email FROM users WHERE lower(email) IN ({','.join('?' for _ in keep_norm)})",
        keep_norm,
    ).fetchall()
    keep_ids = [int(r["id"]) for r in keep_rows]
    found_emails = {str(r["email"]).strip().lower() for r in keep_rows}
    missing = [e for e in keep_norm if e not in found_emails]
    if missing:
        raise ValueError(f"keep email not found: {', '.join(missing)}")

    drop_rows = conn.execute(
        f"SELECT id, email FROM users WHERE lower(email) NOT IN ({','.join('?' for _ in keep_norm)})",
        keep_norm,
    ).fetchall()
    drop_ids = [int(r["id"]) for r in drop_rows]
    if not drop_ids:
        return {
            "deleted": {},
            "dropped_emails": [],
            "kept_ids": keep_ids,
            "kept_emails": [str(r["email"]) for r in keep_rows],
        }

    result = _delete_users_by_ids(conn, drop_ids)
    return {
        "deleted": result.get("deleted") or {},
        "dropped_emails": result.get("dropped_emails") or [],
        "kept_ids": keep_ids,
        "kept_emails": [str(r["email"]) for r in keep_rows],
    }


@router.post("/admin/users/purge-all")
def admin_purge_all_users(body: AdminPurgeUsersIn, _: None = Depends(require_admin)):
    """
    테스트·초기화용: 모든 회원 및 연관 데이터(매물·입찰·알림 등) 삭제.

    **프로덕션 기본 차단.** 실행 조건:
      1) env ALLOW_DESTRUCTIVE_ADMIN=1
      2) confirm == DELETE_ALL_USERS
    삭제 직전 자동 백업을 남긴다. 회원 데이터 유실은 서비스 파산급 사고다.
    """
    _require_destructive_admin()
    if (body.confirm or "").strip() != "DELETE_ALL_USERS":
        raise HTTPException(
            status_code=400,
            detail="confirm must be exactly DELETE_ALL_USERS",
        )
    # Snapshot first — never purge without a recoverable file on volume
    from wakeagain import backup as db_backup

    pre = db_backup.create_backup(reason="pre-purge")
    if not pre.get("ok") and not pre.get("skipped"):
        raise HTTPException(
            status_code=500,
            detail=f"pre-purge backup failed; aborting purge: {pre.get('error')}",
        )

    tables = [
        "bids",
        "messages",
        "notifications",
        "fee_invoices",
        "reports",
        "user_blocks",
        "interests",
        "reviews",
        "showcases",
        "projects",
        "users",
    ]
    deleted: dict[str, int] = {}
    with database.db() as conn:
        try:
            conn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass
        before = int(conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"])
        for t in tables:
            try:
                n = int(conn.execute(f"SELECT COUNT(*) AS c FROM {t}").fetchone()["c"])
                conn.execute(f"DELETE FROM {t}")
                deleted[t] = n
            except Exception as e:
                deleted[t] = -1
                print(f"[admin purge] skip {t}: {e}", flush=True)
        after = int(conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"])
    print(
        f"[WakeAgain][CRITICAL] admin purge-all users_before={before} after={after} "
        f"backup={pre.get('name')}",
        flush=True,
    )
    db_backup.record_counts_tick()
    return {
        "ok": True,
        "users_before": before,
        "users_after": after,
        "deleted": deleted,
        "pre_purge_backup": pre.get("name"),
        "message": f"회원 {before}명 삭제 완료 (남은 회원 {after}명). 백업: {pre.get('name')}",
    }


@router.post("/admin/users/purge-except")
def admin_purge_users_except(body: AdminPurgeExceptIn, _: None = Depends(require_admin)):
    """
    keep_emails 에 있는 회원만 남기고 나머지 회원·연관 데이터 삭제.

    **프로덕션 기본 차단.** 실행 조건:
      1) env ALLOW_DESTRUCTIVE_ADMIN=1
      2) confirm == DELETE_EXCEPT_KEPT
      3) keep_emails 가 DB에 실제 존재
    삭제 직전 자동 백업.
    """
    _require_destructive_admin()
    if (body.confirm or "").strip() != "DELETE_EXCEPT_KEPT":
        raise HTTPException(
            status_code=400,
            detail="confirm must be exactly DELETE_EXCEPT_KEPT",
        )
    keep = [(e or "").strip() for e in (body.keep_emails or []) if (e or "").strip()]
    if not keep:
        raise HTTPException(status_code=400, detail="keep_emails required")

    from wakeagain import backup as db_backup

    pre = db_backup.create_backup(reason="pre-purge")
    if not pre.get("ok") and not pre.get("skipped"):
        raise HTTPException(
            status_code=500,
            detail=f"pre-purge backup failed; aborting purge: {pre.get('error')}",
        )

    with database.db() as conn:
        try:
            conn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass
        before = int(conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"])
        try:
            result = _purge_users_except_emails(conn, keep)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        after = int(conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"])
        remaining = [
            {"id": int(r["id"]), "email": r["email"]}
            for r in conn.execute("SELECT id, email FROM users ORDER BY id").fetchall()
        ]

    print(
        f"[WakeAgain][CRITICAL] admin purge-except users_before={before} after={after} "
        f"kept={result.get('kept_emails')} dropped={len(result.get('dropped_emails') or [])} "
        f"backup={pre.get('name')}",
        flush=True,
    )
    db_backup.record_counts_tick()
    return {
        "ok": True,
        "users_before": before,
        "users_after": after,
        "kept_emails": result.get("kept_emails"),
        "dropped_emails": result.get("dropped_emails"),
        "deleted": result.get("deleted"),
        "remaining_users": remaining,
        "pre_purge_backup": pre.get("name"),
        "message": (
            f"남김 {len(result.get('kept_emails') or [])}명 · "
            f"삭제 {len(result.get('dropped_emails') or [])}명 · "
            f"백업 {pre.get('name')}"
        ),
    }


@router.post("/admin/users/delete")
def admin_delete_selected_users(body: AdminDeleteUsersIn, _: None = Depends(require_admin)):
    """
    관리자 UI: 체크한 회원 id 목록 삭제 + 연관 데이터.

    조건:
      1) X-Admin-Key
      2) confirm == DELETE_SELECTED_USERS
      3) 1~50명, 삭제 후 최소 1명 잔존 (전체 삭제는 purge-all)
    삭제 직전 자동 백업. ALLOW_DESTRUCTIVE_ADMIN 불필요(선택 삭제 한정).
    """
    if (body.confirm or "").strip() != "DELETE_SELECTED_USERS":
        raise HTTPException(
            status_code=400,
            detail="confirm must be exactly DELETE_SELECTED_USERS",
        )
    raw_ids = body.user_ids or []
    try:
        ids = sorted({int(x) for x in raw_ids if int(x) > 0})
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail="user_ids must be integers") from e
    if not ids:
        raise HTTPException(status_code=400, detail="user_ids required (1~50)")
    if len(ids) > 50:
        raise HTTPException(status_code=400, detail="user_ids max 50 per request")

    from wakeagain import backup as db_backup

    pre = db_backup.create_backup(reason="pre-purge")
    if not pre.get("ok") and not pre.get("skipped"):
        raise HTTPException(
            status_code=500,
            detail=f"pre-purge backup failed; aborting delete: {pre.get('error')}",
        )

    with database.db() as conn:
        try:
            conn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass
        before = int(conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"])
        existing = conn.execute(
            f"SELECT id, email FROM users WHERE id IN ({','.join('?' for _ in ids)})",
            ids,
        ).fetchall()
        if not existing:
            raise HTTPException(status_code=404, detail="no matching users")
        drop_ids = [int(r["id"]) for r in existing]
        remaining_after = before - len(drop_ids)
        if remaining_after < 1:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "cannot_delete_last_users",
                    "message": (
                        "모든 회원을 지우면 안 됩니다. 최소 1명은 남겨 주세요. "
                        "전체 초기화가 필요하면 purge-all + ALLOW_DESTRUCTIVE_ADMIN=1 을 사용하세요."
                    ),
                },
            )
        result = _delete_users_by_ids(conn, drop_ids)
        after = int(conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"])
        remaining = [
            {"id": int(r["id"]), "email": r["email"]}
            for r in conn.execute("SELECT id, email FROM users ORDER BY id").fetchall()
        ]

    print(
        f"[WakeAgain][CRITICAL] admin delete-selected users_before={before} after={after} "
        f"dropped={result.get('dropped_emails')} backup={pre.get('name')}",
        flush=True,
    )
    db_backup.record_counts_tick()
    return {
        "ok": True,
        "users_before": before,
        "users_after": after,
        "dropped_ids": result.get("dropped_ids"),
        "dropped_emails": result.get("dropped_emails"),
        "deleted": result.get("deleted"),
        "remaining_users": remaining,
        "pre_purge_backup": pre.get("name"),
        "message": (
            f"삭제 {len(result.get('dropped_emails') or [])}명 · "
            f"남은 회원 {after}명 · 백업 {pre.get('name')}"
        ),
    }


# --- Data durability (회원/매물 백업 · 복구) ---


@router.get("/admin/data/status")
def admin_data_status(_: None = Depends(require_admin)):
    """DB path, counts, backup list meta, collapse alert. Ops first-stop when login fails for everyone."""
    from wakeagain import backup as db_backup

    st = db_backup.status()
    counts = db_backup.live_counts()
    ok_int, int_msg = db_backup.integrity_ok()
    collapse = db_backup.detect_user_collapse()
    backups = db_backup.list_backups(limit=30)
    offsite_st = st.get("offsite") or {}
    remote_files: list[dict] = []
    remote_err = None
    if offsite_st.get("enabled") or offsite_st.get("configured"):
        try:
            from wakeagain import offsite_backup as offsite_mod

            if offsite_mod.is_configured():
                remote_files = offsite_mod.list_objects(max_keys=40)
        except Exception as e:
            remote_err = f"{type(e).__name__}: {e}"
    return {
        "ok": True,
        "critical": bool(collapse),
        "collapse_alert": collapse,
        "destructive_admin_enabled": _destructive_admin_allowed(),
        "counts": counts,
        "integrity_ok": ok_int,
        "integrity": int_msg,
        "db": {
            "path": st.get("db_path"),
            "exists": st.get("db_exists"),
            "size_bytes": st.get("db_size_bytes"),
            "data_dir": st.get("data_dir"),
        },
        "backup": {
            "enabled": st.get("enabled"),
            "interval_sec": st.get("interval_sec"),
            "dir": st.get("backup_dir"),
            "last_backup_at": st.get("last_backup_at"),
            "last_backup_path": st.get("last_backup_path"),
            "last_ok": st.get("last_backup_ok"),
            "last_error": st.get("last_error"),
            "runs": st.get("runs"),
            "meta": st.get("meta") or {},
            "files": backups,
            "file_count": len(backups),
        },
        "offsite": {
            **offsite_st,
            "files": remote_files,
            "file_count": len(remote_files),
            "list_error": remote_err,
        },
        "policy": {
            "message": (
                "회원 데이터 유실 = 서비스 파산급. "
                "로컬 볼륨 스냅샷 + 오프사이트(S3/R2) 이중 보관. "
                "purge/restore는 ALLOW_DESTRUCTIVE_ADMIN=1 + 명시 confirm 필요."
            ),
            "env": [
                "DATA_DIR=/data",
                "DB_BACKUP_ENABLED=1",
                "DB_BACKUP_INTERVAL_SEC=3600",
                "OFFSITE_S3_ENDPOINT",
                "OFFSITE_S3_BUCKET",
                "OFFSITE_S3_ACCESS_KEY",
                "OFFSITE_S3_SECRET_KEY",
                "ALLOW_DESTRUCTIVE_ADMIN=0",
            ],
        },
    }


@router.post("/admin/data/backup")
def admin_data_backup_now(_: None = Depends(require_admin)):
    """Force an immediate SQLite snapshot (admin) + offsite upload when configured."""
    from wakeagain import backup as db_backup

    result = db_backup.create_backup(reason="manual")
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error") or "backup failed")
    return {"ok": True, **result}


@router.post("/admin/data/offsite-upload")
def admin_offsite_upload_latest(_: None = Depends(require_admin)):
    """Force upload the newest local snapshot to offsite storage."""
    from wakeagain import backup as db_backup
    from wakeagain import offsite_backup as offsite_mod

    if not offsite_mod.is_configured():
        raise HTTPException(
            status_code=400,
            detail={
                "code": "offsite_not_configured",
                "message": (
                    "오프사이트 스토리지가 설정되지 않았습니다. "
                    "OFFSITE_S3_ENDPOINT / BUCKET / ACCESS_KEY / SECRET_KEY 를 설정하세요."
                ),
            },
        )
    files = db_backup.list_backups(limit=1)
    if not files:
        # create then upload
        snap = db_backup.create_backup(reason="manual")
        if not snap.get("ok"):
            raise HTTPException(status_code=500, detail=snap.get("error") or "backup failed")
        return {"ok": True, "created": True, **snap}
    path = files[0]["path"]
    result = offsite_mod.upload_backup_file(
        path, reason="manual", users=db_backup.count_users(), force=True
    )
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error") or "upload failed")
    return {"ok": True, "created": False, "local": files[0]["name"], **result}


class AdminOffsitePullIn(BaseModel):
    """원격 백업을 볼륨으로 내려받기 (복구 전 단계)."""

    object_key: str = Field(min_length=8, max_length=400)


@router.post("/admin/data/offsite-pull")
def admin_offsite_pull(body: AdminOffsitePullIn, _: None = Depends(require_admin)):
    """Download a remote snapshot into DATA_DIR/backups (does not restore yet)."""
    from wakeagain import backup as db_backup
    from wakeagain import offsite_backup as offsite_mod

    if not offsite_mod.is_configured():
        raise HTTPException(status_code=400, detail="offsite not configured")
    result = offsite_mod.download_to_local(body.object_key.strip(), db_backup.BACKUP_DIR)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error") or "pull failed")
    return {
        "ok": True,
        **result,
        "message": (
            f"원격 백업을 로컬로 받았습니다: {result.get('name')}. "
            "복구하려면 ALLOW_DESTRUCTIVE_ADMIN=1 후 restore API를 사용하세요."
        ),
    }


class AdminRestoreIn(BaseModel):
    """복구 확인 — 파일명 + 고정 문구. ALLOW_DESTRUCTIVE_ADMIN=1 필수."""

    backup_name: str = Field(min_length=10, max_length=120)
    confirm: str = Field(min_length=8, max_length=40)


@router.post("/admin/data/restore")
def admin_data_restore(body: AdminRestoreIn, _: None = Depends(require_admin)):
    """
    지정 백업으로 primary DB 교체.
    ALLOW_DESTRUCTIVE_ADMIN=1 이고 confirm == RESTORE_FROM_BACKUP 일 때만.
    복구 직전 현재 DB를 pre-restore 로 한 번 더 남김.
    """
    if not _destructive_admin_allowed():
        raise HTTPException(
            status_code=403,
            detail={
                "code": "destructive_locked",
                "message": (
                    "DB 복구가 잠겨 있습니다. ALLOW_DESTRUCTIVE_ADMIN=1 설정 후에만 가능합니다."
                ),
            },
        )
    if (body.confirm or "").strip() != "RESTORE_FROM_BACKUP":
        raise HTTPException(
            status_code=400,
            detail="confirm must be exactly RESTORE_FROM_BACKUP",
        )
    from wakeagain import backup as db_backup

    result = db_backup.restore_from_backup(body.backup_name.strip())
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error") or "restore failed")
    return {"ok": True, **result, "message": f"복구 완료: {body.backup_name} → users={result.get('users')}"}


@router.get("/admin/users")
def admin_list_users(
    q: str = "",
    filter: str = "all",
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(require_admin),
):
    """회원 목록 · 검색(이메일/실명/표시명/휴대폰) · 필터."""
    lim = max(1, min(int(limit or 50), 200))
    off = max(0, int(offset or 0))
    filt = (filter or "all").strip().lower()
    raw_q = (q or "").strip()
    q_like = f"%{raw_q}%" if raw_q else ""
    phone_digits = database.normalize_phone(raw_q) if raw_q else ""

    where: list[str] = ["1=1"]
    params: list[Any] = []

    if filt == "verified":
        where.append("COALESCE(email_verified, 0) = 1")
    elif filt == "unverified":
        where.append("COALESCE(email_verified, 0) = 0")
    elif filt == "suspended":
        where.append("COALESCE(is_suspended, 0) = 1")
    elif filt == "oauth":
        where.append("COALESCE(oauth_provider, '') != ''")
    elif filt == "password":
        where.append("COALESCE(oauth_provider, '') = ''")
    # else all

    if raw_q:
        if phone_digits and len(phone_digits) >= 4:
            where.append(
                "("
                "email LIKE ? OR IFNULL(display_name,'') LIKE ? OR IFNULL(real_name,'') LIKE ? "
                "OR IFNULL(phone,'') LIKE ? OR REPLACE(REPLACE(IFNULL(phone,''),'-',''),' ','') LIKE ?"
                ")"
            )
            params.extend([q_like, q_like, q_like, q_like, f"%{phone_digits}%"])
        else:
            where.append(
                "(email LIKE ? OR IFNULL(display_name,'') LIKE ? OR IFNULL(real_name,'') LIKE ?)"
            )
            params.extend([q_like, q_like, q_like])

    where_sql = " AND ".join(where)
    with database.db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM users WHERE {where_sql}", params
        ).fetchone()["c"]
        rows = conn.execute(
            f"""
            SELECT * FROM users
            WHERE {where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, lim, off),
        ).fetchall()
        counts = {
            "all": int(conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]),
            "verified": int(
                conn.execute(
                    "SELECT COUNT(*) AS c FROM users WHERE COALESCE(email_verified,0)=1"
                ).fetchone()["c"]
            ),
            "unverified": int(
                conn.execute(
                    "SELECT COUNT(*) AS c FROM users WHERE COALESCE(email_verified,0)=0"
                ).fetchone()["c"]
            ),
            "suspended": int(
                conn.execute(
                    "SELECT COUNT(*) AS c FROM users WHERE COALESCE(is_suspended,0)=1"
                ).fetchone()["c"]
            ),
            "oauth": int(
                conn.execute(
                    "SELECT COUNT(*) AS c FROM users WHERE COALESCE(oauth_provider,'') != ''"
                ).fetchone()["c"]
            ),
        }
        users = [_admin_user_row(conn, r, full=False) for r in rows]
    return {
        "ok": True,
        "users": users,
        "total": int(total),
        "limit": lim,
        "offset": off,
        "filter": filt,
        "q": raw_q,
        "counts": counts,
    }


@router.get("/admin/users/{user_id}")
def admin_get_user(user_id: int, _: None = Depends(require_admin)):
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="user not found")
        user = _admin_user_row(conn, row, full=True)
        # recent projects (for ops)
        prows = conn.execute(
            """
            SELECT id, title, listing_status, auction_status, price_start, price_current, created_at
            FROM projects WHERE owner_id = ?
            ORDER BY id DESC LIMIT 10
            """,
            (user_id,),
        ).fetchall()
        user["recent_projects"] = [
            {
                "id": int(p["id"]),
                "title": p["title"] or "",
                "listing_status": p["listing_status"] or "",
                "auction_status": p["auction_status"] or "",
                "price_start": p["price_start"],
                "price_current": p["price_current"],
                "created_at": p["created_at"] or "",
            }
            for p in prows
        ]
    return {"ok": True, "user": user}


class AdminSuspendIn(BaseModel):
    reason: str = Field(default="", max_length=500)


class AdminSetPasswordIn(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class AdminNoteIn(BaseModel):
    note: str = Field(default="", max_length=500)


@router.post("/admin/users/{user_id}/unsuspend")
def admin_unsuspend_user(user_id: int, _: None = Depends(require_admin)):
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute(
            """
            UPDATE users
            SET is_suspended = 0, suspended_at = NULL, suspend_reason = NULL
            WHERE id = ?
            """,
            (user_id,),
        )
        database.notify(
            conn,
            int(user_id),
            "계정 정지 해제",
            "운영자가 계정 정지를 해제했습니다. 다시 이용할 수 있습니다.",
            "/app/",
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = _admin_user_row(conn, row, full=True)
    return {"ok": True, "user_id": user_id, "is_suspended": False, "user": user}


@router.post("/admin/users/{user_id}/suspend")
def admin_suspend_user(
    user_id: int,
    body: AdminSuspendIn | None = None,
    _: None = Depends(require_admin),
):
    reason = ((body.reason if body else "") or "").strip() or "[운영] 수동 계정 정지"
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute(
            """
            UPDATE users
            SET is_suspended = 1, suspended_at = ?, suspend_reason = ?
            WHERE id = ?
            """,
            (database._now(), reason[:500], user_id),
        )
        conn.execute(
            """
            UPDATE projects
            SET auction_status = 'paused',
                paused_reason = COALESCE(paused_reason, '') || ' [운영 계정 정지]',
                updated_at = ?
            WHERE owner_id = ? AND COALESCE(auction_status, 'live') = 'live'
              AND listing_status = 'approved'
            """,
            (database._now(), user_id),
        )
        database.notify(conn, int(user_id), "계정 정지", reason, "/app/")
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = _admin_user_row(conn, row, full=True)
    return {"ok": True, "user_id": user_id, "is_suspended": True, "reason": reason, "user": user}


@router.post("/admin/users/{user_id}/verify-email")
def admin_verify_email(user_id: int, _: None = Depends(require_admin)):
    """운영자 강제 이메일 인증 완료 (메일 미수신 고객 지원)."""
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute(
            """
            UPDATE users
            SET email_verified = 1,
                email_code_hash = NULL,
                email_code_expires = NULL
            WHERE id = ?
            """,
            (user_id,),
        )
        database.recompute_user_credit(conn, int(user_id))
        database.notify(
            conn,
            int(user_id),
            "이메일 인증 완료",
            "운영자가 이메일 인증을 확인해 드렸습니다.",
            "/app/",
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = _admin_user_row(conn, row, full=True)
    return {"ok": True, "user": user, "message": "이메일 인증 처리됨"}


@router.post("/admin/users/{user_id}/set-password")
def admin_set_password(
    user_id: int,
    body: AdminSetPasswordIn,
    _: None = Depends(require_admin),
):
    """운영자 비밀번호 재설정 (메일 없이 고객 지원)."""
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="password min 8 chars")
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute(
            """
            UPDATE users
            SET password_hash = ?,
                reset_code_hash = NULL,
                reset_code_expires = NULL
            WHERE id = ?
            """,
            (hash_password(body.new_password), user_id),
        )
        database.notify(
            conn,
            int(user_id),
            "비밀번호 변경",
            "운영자가 비밀번호를 재설정했습니다. 새 비밀번호로 로그인해 주세요.",
            "/app/",
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = _admin_user_row(conn, row, full=True)
    return {"ok": True, "user": user, "message": "비밀번호가 변경되었습니다."}


@router.post("/admin/users/{user_id}/send-welcome-mail")
def admin_send_welcome_mail(
    user_id: int, force: bool = False, lang: str | None = None, _: None = Depends(require_admin)
):
    """메이커 웰컴 메일(피드백 요청 + 매물등록 쿠폰 안내) 수동 발송. 이미 보냈으면 force=true로만 재발송.
    lang 미지정 시 회원 국가(country=KR→ko, 그 외→en, 미입력→en 기본)로 자동 판별."""
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        email = (row["email"] or "").strip()
        name = (row["display_name"] or "").strip()
        country = (row["country"] if "country" in row.keys() else None) or ""
        already = bool(row["welcome_mailed_at"]) if "welcome_mailed_at" in row.keys() else False
    if already and not force:
        return {"ok": True, "email_sent": False, "already_sent": True, "message": "이미 발송됨(재발송하려면 force=true)"}
    use_lang = lang if lang in ("ko", "en") else _welcome_lang(country, None)
    sent = _maybe_send_welcome_mail(user_id, email, name, lang=use_lang, force=force)
    return {"ok": True, "email_sent": sent, "already_sent": False, "lang": use_lang}


@router.post("/admin/users/{user_id}/issue-reset-code")
def admin_issue_reset_code(user_id: int, _: None = Depends(require_admin)):
    """재설정 코드 발급 — SMTP 있으면 메일, 없으면 응답에 코드(운영 전달용)."""
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        email = (row["email"] or "").strip().lower()
        code = _new_email_code()
        conn.execute(
            "UPDATE users SET reset_code_hash = ?, reset_code_expires = ? WHERE id = ?",
            (_hash_code(code), _code_expiry_iso(), user_id),
        )
        mail_meta = _deliver_reset_code(email, code)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = _admin_user_row(conn, row, full=True)
    out: dict[str, Any] = {
        "ok": True,
        "user": user,
        "email": email,
        "message": "재설정 코드를 발급했습니다.",
    }
    out.update({k: v for k, v in mail_meta.items() if v is not None})
    # Always include code for admin ops (admin-only endpoint)
    out["dev_email_code"] = code
    return out


# --- reviews (simple testimonials — not a full community board) ---


class ReviewIn(BaseModel):
    author_name: str = Field(min_length=1, max_length=40)
    role_label: str = Field(default="", max_length=80)
    body: str = Field(min_length=20, max_length=1500)
    sold_price: int | None = Field(default=None, ge=0, le=10_000_000_000)
    side: Literal["seller", "buyer"] = "seller"


class AdminReviewStoryIn(BaseModel):
    action: Literal["approve", "reject"]
    note: str = Field(default="", max_length=500)


# --- project showcase (자랑 보드 · 장터 아님) ---


class ShowcaseIn(BaseModel):
    author_name: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=80)
    one_liner: str = Field(min_length=1, max_length=120)
    story: str = Field(default="", max_length=120)  # optional one-line note
    demo: str = Field(default="", max_length=1000)
    status_key: str = Field(default="prototype", max_length=40)
    product_type: str = Field(default="other", max_length=40)
    price_hint: int | None = Field(default=None, ge=0, le=100_000_000)
    diag_score: int | None = Field(default=None, ge=0, le=100)


@router.get("/showcases")
def list_showcases(limit: int = 24):
    """Public showcase board — not marketplace listings."""
    lim = max(1, min(int(limit or 24), 60))
    with database.db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM showcases
            WHERE listing_status = 'approved'
            ORDER BY id DESC
            LIMIT ?
            """,
            (lim,),
        ).fetchall()
    return {
        "ok": True,
        "showcases": [database.showcase_to_dict(r) for r in rows],
        "note_ko": "프로젝트 자랑 보드입니다. 판매·입찰 매물이 아니며 품질을 보증하지 않습니다.",
    }


@router.post("/showcases")
def create_showcase(body: ShowcaseIn, user: dict | None = Depends(get_optional_user)):
    """Optional login. Requires free diagnosis score. Not a sale listing."""
    name = body.author_name.strip()
    title = body.title.strip()
    one = body.one_liner.strip()
    story = (body.story or "").strip()
    # Soft gate: showcase only after 무료진단 (diag_score required)
    if body.diag_score is None:
        raise HTTPException(status_code=400, detail="무료진단 후 등록할 수 있습니다.")
    status_key = (body.status_key or "prototype").strip()
    if status_key not in price_policy.STATUS_PRICING:
        status_key = "other" if "other" in price_policy.STATUS_PRICING else "prototype"
    ptype = (body.product_type or "other").strip()
    if ptype not in database.PRODUCT_TYPES:
        ptype = "other"
    now = database._now()
    with database.db() as conn:
        # soft anti-spam: same title+name recently
        recent = conn.execute(
            """
            SELECT id, created_at FROM showcases
            WHERE author_name = ? AND title = ?
            ORDER BY id DESC LIMIT 1
            """,
            (name, title),
        ).fetchone()
        if recent:
            try:
                prev = datetime.fromisoformat(str(recent["created_at"]))
                if prev.tzinfo is None:
                    prev = prev.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - prev.astimezone(timezone.utc) < timedelta(hours=1):
                    raise HTTPException(
                        status_code=429,
                        detail="같은 제목으로 너무 자주 올렸습니다. 잠시 후 다시 시도해 주세요.",
                    )
            except HTTPException:
                raise
            except Exception:
                pass
        cur = conn.execute(
            """
            INSERT INTO showcases (
              user_id, author_name, title, one_liner, story, demo,
              status_key, product_type, price_hint, diag_score,
              cheer_count, listing_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'approved', ?)
            """,
            (
                user["id"] if user else None,
                name,
                title,
                one,
                story,
                (body.demo or "").strip(),
                status_key,
                ptype,
                body.price_hint,
                body.diag_score,
                now,
            ),
        )
        sid = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM showcases WHERE id = ?", (sid,)).fetchone()
    return {
        "ok": True,
        "showcase": database.showcase_to_dict(row),
        "note_ko": "자랑이 등록되었습니다. 마켓에 올리려면 「내 프로젝트 올리기」로 이어 주세요.",
    }


@router.post("/showcases/{showcase_id}/cheer")
def cheer_showcase(showcase_id: int):
    """Lightweight applause — no login required (early MVP)."""
    with database.db() as conn:
        row = conn.execute(
            "SELECT id, cheer_count FROM showcases WHERE id = ? AND listing_status = 'approved'",
            (showcase_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute(
            "UPDATE showcases SET cheer_count = COALESCE(cheer_count, 0) + 1 WHERE id = ?",
            (showcase_id,),
        )
        row = conn.execute("SELECT * FROM showcases WHERE id = ?", (showcase_id,)).fetchone()
    return {"ok": True, "showcase": database.showcase_to_dict(row)}


@router.get("/reviews")
def list_reviews(limit: int = 20):
    """Public approved reviews only."""
    lim = max(1, min(int(limit or 20), 50))
    with database.db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM reviews
            WHERE listing_status = 'approved'
            ORDER BY id DESC
            LIMIT ?
            """,
            (lim,),
        ).fetchall()
    return {
        "ok": True,
        "reviews": [database.review_to_dict(r) for r in rows],
        "note": "게시 허용된 후기만 공개됩니다.",
    }


@router.post("/reviews")
def create_review(body: ReviewIn, user: dict | None = Depends(get_optional_user)):
    """Anyone can submit; goes to pending until admin approves. Login optional."""
    name = body.author_name.strip()
    if len(name) < 1:
        raise HTTPException(status_code=400, detail="author_name required")
    text = body.body.strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="body min 20 chars")
    now = database._now()
    with database.db() as conn:
        cur = conn.execute(
            """
            INSERT INTO reviews (
              user_id, author_name, role_label, body, sold_price, side,
              listing_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                user["id"] if user else None,
                name,
                (body.role_label or "").strip(),
                text,
                body.sold_price,
                body.side,
                now,
            ),
        )
        rid = int(cur.lastrowid)
    return {
        "ok": True,
        "id": rid,
        "note": "후기가 접수되었습니다. 운영 검수 후 공개되며, 보통 1~2영업일 안에 반영됩니다.",
        "review_sla": "1–2 business days",
    }


@router.get("/admin/reviews")
def admin_list_reviews(
    status: str = "pending",
    _: None = Depends(require_admin),
):
    status = (status or "pending").strip().lower()
    if status not in {"pending", "approved", "rejected", "all"}:
        raise HTTPException(status_code=400, detail="status must be pending|approved|rejected|all")
    with database.db() as conn:
        if status == "all":
            rows = conn.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT 200").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM reviews WHERE listing_status = ? ORDER BY id DESC LIMIT 200",
                (status,),
            ).fetchall()
        counts = {
            "pending": conn.execute(
                "SELECT COUNT(*) AS c FROM reviews WHERE listing_status = 'pending'"
            ).fetchone()["c"],
            "approved": conn.execute(
                "SELECT COUNT(*) AS c FROM reviews WHERE listing_status = 'approved'"
            ).fetchone()["c"],
            "rejected": conn.execute(
                "SELECT COUNT(*) AS c FROM reviews WHERE listing_status = 'rejected'"
            ).fetchone()["c"],
        }
    return {
        "ok": True,
        "counts": counts,
        "reviews": [database.review_to_dict(r, include_private=True) for r in rows],
    }


@router.post("/admin/reviews/{review_id}/review")
def admin_review_story(
    review_id: int,
    body: AdminReviewStoryIn,
    _: None = Depends(require_admin),
):
    new_status = "approved" if body.action == "approve" else "rejected"
    now = database._now()
    with database.db() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute(
            """
            UPDATE reviews
            SET listing_status = ?, review_note = ?, reviewed_at = ?
            WHERE id = ?
            """,
            (new_status, (body.note or "").strip(), now, review_id),
        )
        row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    return {"ok": True, "review": database.review_to_dict(row, include_private=True)}


# --- buyer interest ---


@router.post("/interest")
def create_interest(body: InterestIn, user: dict | None = Depends(get_optional_user)):
    email = (body.email or (user["email"] if user else "") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="email required")
    with database.db() as conn:
        cur = conn.execute(
            """
            INSERT INTO interests (user_id, email, name, category, budget, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"] if user else None,
                email,
                body.name.strip(),
                body.category.strip(),
                body.budget.strip(),
                body.note.strip(),
                database._now(),
            ),
        )
        iid = int(cur.lastrowid)
    return {
        "ok": True,
        "id": iid,
        "note": "관심 등록은 경량 접수입니다. 입찰·성사 전에는 신원·정산 확인이 필요합니다.",
    }


# --- legacy landing leads (anonymous) still stored in DB ---


@router.post("/leads")
async def create_lead_v1(request: Request):
    try:
        body: dict[str, Any] = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="invalid json") from e
    lead_type = str(body.get("type") or "").strip().lower()
    contact = str(body.get("contact") or "").strip()
    if lead_type not in {"sell", "buy"}:
        raise HTTPException(status_code=400, detail="type must be sell|buy")
    if len(contact) < 3:
        raise HTTPException(status_code=400, detail="contact required")
    if lead_type == "sell":
        for k in ("title", "one_liner", "story", "demo"):
            if not str(body.get(k) or "").strip():
                raise HTTPException(status_code=400, detail=f"{k} required")
    if lead_type == "buy" and not str(body.get("category") or "").strip():
        raise HTTPException(status_code=400, detail="category required")

    with database.db() as conn:
        conn.execute(
            "INSERT INTO leads (lead_type, contact, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (lead_type, contact, json.dumps(body, ensure_ascii=False), database._now()),
        )
        if lead_type == "buy":
            conn.execute(
                """
                INSERT INTO interests (user_id, email, name, category, budget, note, created_at)
                VALUES (NULL, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contact if "@" in contact else contact,
                    str(body.get("name") or "").strip(),
                    str(body.get("category") or "").strip(),
                    str(body.get("budget") or "").strip(),
                    str(body.get("note") or "").strip(),
                    database._now(),
                ),
            )
    return {
        "ok": True,
        "note": "사전 접수입니다. 공개 매물·입찰은 계정 이메일 인증·실명·휴대폰 확인 후 가능합니다.",
    }
