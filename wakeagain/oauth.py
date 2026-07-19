"""SNS OAuth (Google · GitHub · Kakao) for WakeAgain.

Env (enable per provider by setting client id + secret):
  OAUTH_PUBLIC_BASE   — e.g. http://127.0.0.1:8080  (redirect base)
  GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
  GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET
  KAKAO_CLIENT_ID / KAKAO_CLIENT_SECRET  (secret optional for Kakao REST)

After SNS login: age gate + Lv2 real name/phone + Lv3 bank still required.
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import jwt

from wakeagain.auth import JWT_ALG, JWT_SECRET

# Unusable password marker for OAuth-only accounts
OAUTH_PASSWORD_PLACEHOLDER = "!oauth-no-password"

PROVIDERS = ("google", "github", "kakao")

# Short-lived state (CSRF)
STATE_MINUTES = 15


def public_base() -> str:
    return (
        os.environ.get("OAUTH_PUBLIC_BASE")
        or os.environ.get("PUBLIC_BASE_URL")
        or "http://127.0.0.1:8080"
    ).rstrip("/")


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def provider_config(provider: str) -> dict[str, Any] | None:
    p = (provider or "").lower().strip()
    if p not in PROVIDERS:
        return None
    if p == "google":
        cid, secret = _env("GOOGLE_CLIENT_ID"), _env("GOOGLE_CLIENT_SECRET")
        if not cid or not secret:
            return None
        return {
            "id": "google",
            "label": "Google",
            "client_id": cid,
            "client_secret": secret,
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
            "scope": "openid email profile",
        }
    if p == "github":
        cid, secret = _env("GITHUB_CLIENT_ID"), _env("GITHUB_CLIENT_SECRET")
        if not cid or not secret:
            return None
        return {
            "id": "github",
            "label": "GitHub",
            "client_id": cid,
            "client_secret": secret,
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "emails_url": "https://api.github.com/user/emails",
            "scope": "read:user user:email",
        }
    if p == "kakao":
        cid = _env("KAKAO_CLIENT_ID") or _env("KAKAO_REST_API_KEY")
        secret = _env("KAKAO_CLIENT_SECRET")  # optional
        if not cid:
            return None
        return {
            "id": "kakao",
            "label": "Kakao",
            "client_id": cid,
            "client_secret": secret,
            "auth_url": "https://kauth.kakao.com/oauth/authorize",
            "token_url": "https://kauth.kakao.com/oauth/token",
            "userinfo_url": "https://kapi.kakao.com/v2/user/me",
            "scope": "profile_nickname account_email",
        }
    return None


def enabled_providers() -> list[dict[str, str]]:
    out = []
    for p in PROVIDERS:
        cfg = provider_config(p)
        if cfg:
            out.append(
                {
                    "id": cfg["id"],
                    "label": cfg["label"],
                    "start_path": f"/api/v1/auth/oauth/{cfg['id']}/start",
                }
            )
    return out


def redirect_uri(provider: str) -> str:
    return f"{public_base()}/api/v1/auth/oauth/{provider}/callback"


def make_state(provider: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "p": provider,
        "n": secrets.token_hex(8),
        "iat": now,
        "exp": now + timedelta(minutes=STATE_MINUTES),
        "iss": "wakeagain-oauth",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def parse_state(state: str, provider: str) -> None:
    try:
        data = jwt.decode(
            state,
            JWT_SECRET,
            algorithms=[JWT_ALG],
            issuer="wakeagain-oauth",
        )
    except jwt.PyJWTError as e:
        raise ValueError("invalid oauth state") from e
    if data.get("p") != provider:
        raise ValueError("oauth state provider mismatch")


def authorize_url(provider: str) -> tuple[str, str]:
    cfg = provider_config(provider)
    if not cfg:
        raise ValueError("provider not configured")
    state = make_state(provider)
    q = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri(provider),
        "response_type": "code",
        "scope": cfg["scope"],
        "state": state,
    }
    if provider == "google":
        q["access_type"] = "online"
        q["prompt"] = "select_account"
    return cfg["auth_url"] + "?" + urlencode(q), state


async def exchange_code(provider: str, code: str) -> dict[str, Any]:
    """Return normalized profile: subject, email, email_verified, display_name."""
    import httpx

    cfg = provider_config(provider)
    if not cfg:
        raise ValueError("provider not configured")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri(provider),
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"] or "",
    }
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        if provider == "github":
            tr = await client.post(cfg["token_url"], data=data, headers=headers)
        elif provider == "kakao":
            tr = await client.post(
                cfg["token_url"],
                data={k: v for k, v in data.items() if v or k != "client_secret"},
                headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
            )
        else:
            tr = await client.post(cfg["token_url"], data=data, headers=headers)
        if tr.status_code >= 400:
            raise ValueError(f"token exchange failed: {tr.text[:200]}")
        tok = tr.json()
        access = tok.get("access_token")
        if not access:
            raise ValueError("no access_token")

        if provider == "google":
            ur = await client.get(
                cfg["userinfo_url"],
                headers={"Authorization": f"Bearer {access}"},
            )
            ur.raise_for_status()
            u = ur.json()
            return {
                "subject": str(u.get("sub") or ""),
                "email": (u.get("email") or "").strip().lower(),
                "email_verified": bool(u.get("email_verified")),
                "display_name": (u.get("name") or u.get("given_name") or "").strip()[:80],
            }

        if provider == "github":
            ur = await client.get(
                cfg["userinfo_url"],
                headers={
                    "Authorization": f"Bearer {access}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "WakeAgain-OAuth",
                },
            )
            ur.raise_for_status()
            u = ur.json()
            email = (u.get("email") or "").strip().lower()
            verified = False
            if not email:
                er = await client.get(
                    cfg["emails_url"],
                    headers={
                        "Authorization": f"Bearer {access}",
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "WakeAgain-OAuth",
                    },
                )
                if er.status_code < 400:
                    for item in er.json() or []:
                        if item.get("primary") and item.get("email"):
                            email = str(item["email"]).strip().lower()
                            verified = bool(item.get("verified"))
                            break
                        if not email and item.get("email"):
                            email = str(item["email"]).strip().lower()
                            verified = bool(item.get("verified"))
            else:
                verified = True
            subject = str(u.get("id") or "")
            if not email:
                email = f"gh_{subject}@users.noreply.github.com"
                verified = False
            return {
                "subject": subject,
                "email": email,
                "email_verified": verified,
                "display_name": (u.get("name") or u.get("login") or "").strip()[:80],
            }

        if provider == "kakao":
            ur = await client.get(
                cfg["userinfo_url"],
                headers={"Authorization": f"Bearer {access}"},
            )
            ur.raise_for_status()
            u = ur.json()
            subject = str(u.get("id") or "")
            kakao_account = u.get("kakao_account") or {}
            profile = kakao_account.get("profile") or u.get("properties") or {}
            email = (kakao_account.get("email") or "").strip().lower()
            verified = bool(kakao_account.get("is_email_verified") or kakao_account.get("email"))
            if not email:
                email = f"kakao_{subject}@oauth.wakeagain.local"
                verified = False
            nick = (
                profile.get("nickname")
                or (u.get("properties") or {}).get("nickname")
                or ""
            )
            return {
                "subject": subject,
                "email": email,
                "email_verified": verified and "@oauth.wakeagain.local" not in email,
                "display_name": str(nick).strip()[:80],
            }

    raise ValueError("unknown provider")
