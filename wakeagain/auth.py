from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from wakeagain import db as database

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.environ.get("APP_SECRET") or os.environ.get("JWT_SECRET") or "wakeagain-dev-change-me"
JWT_ALG = "HS256"
JWT_DAYS = int(os.environ.get("JWT_DAYS", "30"))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


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
