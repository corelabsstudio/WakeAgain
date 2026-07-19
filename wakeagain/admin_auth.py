"""Simple shared-secret admin gate for ops review UI."""
from __future__ import annotations

import os

from fastapi import Header, HTTPException, status

# Dev default only — never ship publicly without override.
# UI must not display this string; set ADMIN_SECRET=long-random-string in production.
ADMIN_SECRET = (os.environ.get("ADMIN_SECRET") or "wakeagain-admin-dev").strip()


def require_admin(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    if not x_admin_key or x_admin_key.strip() != ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin key required (header X-Admin-Key)",
        )
