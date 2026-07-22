"""WakeAgain — shared backend for web + Play + App Store clients."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

# Load .env BEFORE wakeagain.* reads secrets at import time
from wakeagain.envutil import ensure_local_env, load_dotenv

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
ensure_local_env()
load_dotenv(override=False)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from wakeagain import __version__
from wakeagain.api import router as api_router
from wakeagain.db import DATA, init_db
from wakeagain import backup as db_backup
from wakeagain import scheduler as auction_scheduler

# Web + Capacitor/Android/iOS WebView. Production: set ALLOWED_ORIGINS explicitly.
# Unset → secure defaults (no *). Explicit "*" only when operator opts in (local debug).
_default_origins = [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "capacitor://localhost",
    "http://localhost",
    "ionic://localhost",
    "https://localhost",
    "https://wakeagain.com",
    "https://www.wakeagain.com",
    "https://web-production-8ee81.up.railway.app",
]
_raw_origins = (os.environ.get("ALLOWED_ORIGINS") or "").strip()
if not _raw_origins:
    allow_origins = list(_default_origins)
elif _raw_origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] or list(
        _default_origins
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Member data is existential — snapshot + collapse detection before serving traffic
    try:
        boot = db_backup.startup_hooks()
        if boot.get("alert"):
            print(f"[WakeAgain] CRITICAL DATA ALERT: {boot['alert'].get('message')}", flush=True)
    except Exception as e:
        print(f"[WakeAgain] backup startup_hooks failed: {e}", flush=True)
    auction_scheduler.start()
    _security_startup_warnings()
    try:
        yield
    finally:
        auction_scheduler.stop()


app = FastAPI(
    title="WakeAgain",
    version=__version__,
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def _security_startup_warnings() -> None:
    """Remind operators not to ship with dev defaults."""
    from wakeagain.admin_auth import ADMIN_SECRET
    from wakeagain.api import EMAIL_CODE_FALLBACK, EMAIL_DEV_MODE

    if ADMIN_SECRET == "wakeagain-admin-dev":
        print(
            "[WakeAgain] WARNING: ADMIN_SECRET is the dev default. "
            "Set ADMIN_SECRET to a long random value before any public deploy."
        )
    if EMAIL_DEV_MODE:
        print(
            "[WakeAgain] WARNING: EMAIL_DEV_MODE is on (auth codes may appear in API). "
            "Set EMAIL_DEV_MODE=0 in production."
        )
    if EMAIL_CODE_FALLBACK and not EMAIL_DEV_MODE:
        print(
            "[WakeAgain] WARNING: EMAIL_CODE_FALLBACK is on — SMTP failure returns codes in API. "
            "Set EMAIL_CODE_FALLBACK=0 in production."
        )
    if allow_origins == ["*"]:
        print(
            "[WakeAgain] WARNING: ALLOWED_ORIGINS=* (wide CORS). "
            "Set comma-separated production origins for public deploy."
        )
    if not (os.environ.get("APP_SECRET") or os.environ.get("JWT_SECRET")):
        print(
            "[WakeAgain] WARNING: APP_SECRET/JWT_SECRET unset — using insecure defaults for JWT/settlement encryption."
        )


def _prod_flags() -> dict:
    from wakeagain.admin_auth import ADMIN_SECRET
    from wakeagain.api import EMAIL_CODE_FALLBACK, EMAIL_DEV_MODE
    from wakeagain.mailer import smtp_configured

    return {
        "admin_secret_is_dev": ADMIN_SECRET == "wakeagain-admin-dev",
        "email_dev_mode": bool(EMAIL_DEV_MODE),
        "email_code_fallback": bool(EMAIL_CODE_FALLBACK),
        "cors_allow_all": allow_origins == ["*"],
        "smtp_missing": not smtp_configured(),
        "app_secret_set": bool(os.environ.get("APP_SECRET") or os.environ.get("JWT_SECRET")),
        "oauth_public_base": bool(
            (os.environ.get("OAUTH_PUBLIC_BASE") or os.environ.get("PUBLIC_BASE_URL") or "").strip()
        ),
    }


@app.get("/health")
def health_root():
    flags = _prod_flags()
    sched = auction_scheduler.status()
    bstat = db_backup.status()
    users = db_backup.count_users()
    collapse = db_backup.detect_user_collapse()
    ready = True  # process is up; secrets warned separately
    warnings = {
        k: v
        for k, v in {
            "ADMIN_SECRET_dev": flags["admin_secret_is_dev"],
            "EMAIL_DEV_MODE": flags["email_dev_mode"],
            "SMTP_missing": flags["smtp_missing"],
            "APP_SECRET_missing": not flags["app_secret_set"],
            "user_count_collapsed": bool(collapse),
            "users_zero_after_peak": bool(collapse),
            "offsite_backup_missing": not (bstat.get("offsite") or {}).get("configured"),
        }.items()
        if v
    }
    return {
        "ok": True,
        "ready": ready,
        "service": "WakeAgain",
        "version": __version__,
        # durability probe marker — must not affect data; redeploy smoke only
        "build_probe": "durability-e2e-2026-07-22",
        "channels": ["web", "android", "ios"],
        "data_dir": str(DATA),
        "data": {
            "users": users,
            "db_exists": bstat.get("db_exists"),
            "db_size_bytes": bstat.get("db_size_bytes"),
            "last_backup_at": bstat.get("last_backup_at"),
            "backup_enabled": bstat.get("enabled"),
            "peak_users": (bstat.get("meta") or {}).get("peak_users"),
            "collapse_alert": collapse,
            "offsite": {
                "configured": (bstat.get("offsite") or {}).get("configured"),
                "enabled": (bstat.get("offsite") or {}).get("enabled"),
                "last_upload_at": (bstat.get("offsite") or {}).get("last_upload_at"),
                "last_upload_ok": (bstat.get("offsite") or {}).get("last_upload_ok"),
            },
        },
        "scheduler": {
            "enabled": sched.get("enabled"),
            "running": sched.get("running"),
            "interval_sec": sched.get("interval_sec"),
            "last_run_at": sched.get("last_run_at"),
            "last_closed": sched.get("last_closed"),
            "runs": sched.get("runs"),
        },
        "prod_warnings": warnings,
    }


@app.post("/api/leads")
async def legacy_leads(request: Request):
    """Backward-compatible landing forms → same DB via v1."""
    from wakeagain.api import create_lead_v1

    return await create_lead_v1(request)


# Static last (API routes take priority)
if not PUBLIC.is_dir():
    raise RuntimeError(f"public dir missing: {PUBLIC}")


@app.middleware("http")
async def _security_and_cache(request: Request, call_next):
    response = await call_next(request)
    # Security headers (safe defaults for marketplace)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    # Avoid stale HTML after deploys
    path = request.url.path or ""
    if path.endswith(".html") or path in ("/", "") or path.endswith("/"):
        ct = (response.headers.get("content-type") or "").lower()
        if "text/html" in ct or path.endswith(".html") or path in ("/", ""):
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
    # Long-cache immutable assets
    if path.startswith("/assets/") or path in ("/favicon.ico", "/favicon.svg", "/ux9.css"):
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "public, max-age=86400"
    return response


class _HtmlFallbackStatic(StaticFiles):
    """Serve public/404.html for missing paths (pretty 404)."""

    async def get_response(self, path: str, scope):  # type: ignore[override]
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as ex:
            if ex.status_code != 404:
                raise
            not_found = PUBLIC / "404.html"
            if not_found.is_file():
                return FileResponse(not_found, status_code=404)
            raise


@app.exception_handler(StarletteHTTPException)
async def _http_exc_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and not (request.url.path or "").startswith("/api"):
        not_found = PUBLIC / "404.html"
        if not_found.is_file():
            return FileResponse(not_found, status_code=404)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.mount("/", _HtmlFallbackStatic(directory=str(PUBLIC), html=True), name="static")
