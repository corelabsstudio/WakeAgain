from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from wakeagain import db as database

# bcrypt 5.x broke passlib 1.7.4's backend probe ("password cannot be longer than 72 bytes").
# Use bcrypt directly; existing $2b$ hashes remain compatible.
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.environ.get("APP_SECRET") or os.environ.get("JWT_SECRET") or "wakeagain-dev-change-me"
JWT_ALG = "HS256"
JWT_DAYS = int(os.environ.get("JWT_DAYS", "30"))


def _password_bytes(password: str) -> bytes:
    raw = password.encode("utf-8")
    # bcrypt hard limit; reject oversize rather than silent truncate
    if len(raw) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="password too long (max 72 bytes)",
        )
    return raw


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        raw = password.encode("utf-8")
        if len(raw) > 72:
            return False
        return bcrypt.checkpw(raw, password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def create_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(days=JWT_DAYS),
        "iss": "wakeagain",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG], issuer="wakeagain")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from e


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="auth required")
    payload = decode_token(creds.credentials)
    user_id = int(payload["sub"])
    with database.db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    try:
        if "is_suspended" in row.keys() and int(row["is_suspended"] or 0):
            reason = ""
            if "suspend_reason" in row.keys():
                reason = (row["suspend_reason"] or "").strip()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "account_suspended",
                    "message": "계정이 정지되었습니다. "
                    + (reason or "문의: corelabs.studio@gmail.com"),
                },
            )
    except HTTPException:
        raise
    except Exception:
        pass
    return database.user_to_dict(row)


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    if creds is None or not creds.credentials:
        return None
    try:
        return get_current_user(creds)
    except HTTPException:
        return None
