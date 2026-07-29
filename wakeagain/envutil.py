"""Load local .env before other modules read os.environ (no python-dotenv dep)."""
from __future__ import annotations

import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


def load_dotenv(path: Path | None = None, *, override: bool = False) -> bool:
    p = path or ENV_PATH
    if not p.is_file():
        return False
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = val
    return True


def ensure_local_env(*, force: bool = False) -> Path:
    """Create .env if missing (pre-deploy hygiene).

    Prefer reusing `.launch/production-secrets.local.txt` so local ADMIN_SECRET
    does not drift from the production mirror. Only generate random secrets when
    no mirror exists.
    """
    if ENV_PATH.is_file() and not force:
        return ENV_PATH

    mirror = ROOT / ".launch" / "production-secrets.local.txt"
    mirrored: dict[str, str] = {}
    if mirror.is_file():
        try:
            for raw in mirror.read_text(encoding="utf-8-sig").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                mirrored[k.strip()] = v.strip().strip('"').strip("'")
        except OSError:
            mirrored = {}

    app = mirrored.get("APP_SECRET") or secrets.token_urlsafe(48)
    jwt = mirrored.get("JWT_SECRET") or app
    admin = mirrored.get("ADMIN_SECRET") or secrets.token_urlsafe(32)
    source = "production-secrets.local.txt" if mirrored.get("ADMIN_SECRET") else "generated"
    body = f"""# Local env — do not commit
# ADMIN/APP secrets source: {source}
# Keep in sync with Railway Variables + .launch/production-secrets.local.txt
# (run: python _sync_admin_secrets.py)

APP_SECRET={app}
JWT_SECRET={jwt}
ADMIN_SECRET={admin}
EMAIL_DEV_MODE={mirrored.get("EMAIL_DEV_MODE") or "1"}
AUCTION_SCHEDULER={mirrored.get("AUCTION_SCHEDULER") or "1"}
AUCTION_SCHEDULER_SEC={mirrored.get("AUCTION_SCHEDULER_SEC") or "60"}
ALLOWED_ORIGINS={mirrored.get("ALLOWED_ORIGINS") or "*"}
OAUTH_PUBLIC_BASE=http://127.0.0.1:8080
"""
    ENV_PATH.write_text(body, encoding="utf-8")
    return ENV_PATH
