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
    """Create .env with strong local secrets if missing (pre-deploy hygiene)."""
    if ENV_PATH.is_file() and not force:
        return ENV_PATH
    app = secrets.token_urlsafe(48)
    admin = secrets.token_urlsafe(32)
    body = f"""# Auto-generated local secrets — do not commit
# Pre-deploy / local ready mode (EMAIL_DEV_MODE ok until real SMTP)

APP_SECRET={app}
JWT_SECRET={app}
ADMIN_SECRET={admin}
EMAIL_DEV_MODE=1
AUCTION_SCHEDULER=1
AUCTION_SCHEDULER_SEC=60
ALLOWED_ORIGINS=*
OAUTH_PUBLIC_BASE=http://127.0.0.1:8080
"""
    ENV_PATH.write_text(body, encoding="utf-8")
    return ENV_PATH
