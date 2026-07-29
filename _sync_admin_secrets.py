# -*- coding: utf-8 -*-
"""Sync ADMIN_SECRET across local files, verify live, optional cleanup.

Canonical for production ops: .launch/production-secrets.local.txt
Local server (.env) is mirrored from that after we pick the key that works on live.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECRETS = ROOT / ".launch" / "production-secrets.local.txt"
ENV = ROOT / ".env"
LIVE = "https://wakeagain.com"


def fp(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def write_secrets_file(path: Path, data: dict[str, str], header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [header.rstrip(), ""]
    # stable order
    keys = [
        "APP_SECRET",
        "JWT_SECRET",
        "ADMIN_SECRET",
        "EMAIL_DEV_MODE",
        "EMAIL_CODE_FALLBACK",
        "AUCTION_SCHEDULER",
        "AUCTION_SCHEDULER_SEC",
        "ALLOWED_ORIGINS",
        "DATA_DIR",
        "URL",
        "SERVICE",
    ]
    seen = set()
    for k in keys:
        if k in data and data[k]:
            lines.append(f"{k}={data[k]}")
            seen.add(k)
    for k, v in sorted(data.items()):
        if k not in seen and v:
            lines.append(f"{k}={v}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def merge_env_preserve_non_secrets(env_path: Path, secrets: dict[str, str]) -> None:
    """Update .env secret keys to match secrets; keep other local keys."""
    existing = parse_kv(env_path) if env_path.is_file() else {}
    # secrets win for these
    for k in (
        "APP_SECRET",
        "JWT_SECRET",
        "ADMIN_SECRET",
        "EMAIL_DEV_MODE",
        "EMAIL_CODE_FALLBACK",
        "AUCTION_SCHEDULER",
        "AUCTION_SCHEDULER_SEC",
        "ALLOWED_ORIGINS",
        "DATA_DIR",
    ):
        if k in secrets and secrets[k]:
            existing[k] = secrets[k]
    # ensure JWT defaults to APP if missing
    if existing.get("APP_SECRET") and not existing.get("JWT_SECRET"):
        existing["JWT_SECRET"] = existing["APP_SECRET"]
    header = (
        "# Local env — synced ADMIN/APP secrets from .launch/production-secrets.local.txt\n"
        "# Do not commit. Production truth is Railway Variables."
    )
    write_secrets_file(env_path, existing, header)


def admin_probe(admin: str) -> tuple[int, dict]:
    req = urllib.request.Request(
        LIVE + "/api/v1/admin/session",
        headers={"X-Admin-Key": admin, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {"detail": str(e)}
        return e.code, body
    except Exception as e:
        return 0, {"_error": str(e)}


def http_json(method: str, url: str, headers: dict | None = None, body: dict | None = None):
    data = None
    hdrs = {"Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"_raw": str(e)}
    except Exception as e:
        return 0, {"_error": str(e)}


def main() -> int:
    sec = parse_kv(SECRETS)
    env = parse_kv(ENV)
    print("=== local fingerprints ===")
    for name, d in (("production-secrets", sec), (".env", env)):
        a = d.get("ADMIN_SECRET") or ""
        print(f"  {name}: admin_len={len(a)} fp={fp(a) if a else '-'}")

    candidates: list[tuple[str, str]] = []
    if sec.get("ADMIN_SECRET"):
        candidates.append(("production-secrets", sec["ADMIN_SECRET"]))
    if env.get("ADMIN_SECRET") and env.get("ADMIN_SECRET") not in [c[1] for c in candidates]:
        candidates.append((".env", env["ADMIN_SECRET"]))
    candidates.append(("dev-default", "wakeagain-admin-dev"))

    print("=== live admin probe ===")
    working: tuple[str, str] | None = None
    for label, key in candidates:
        code, body = admin_probe(key)
        print(f"  {label}: HTTP {code} fp={fp(key)}")
        if code == 200:
            working = (label, key)
            break

    if not working:
        print(
            "\nNO local key matches Railway.\n"
            "Action required once: open Railway → WakeAgain → Variables → ADMIN_SECRET\n"
            "Copy value into BOTH:\n"
            f"  {SECRETS}\n"
            f"  {ENV}\n"
            "Then re-run: python _sync_admin_secrets.py\n"
        )
        # Still align local files to production-secrets as single local canon
        if sec.get("ADMIN_SECRET"):
            merge_env_preserve_non_secrets(ENV, sec)
            print("Local .env ADMIN_SECRET mirrored FROM production-secrets (still may not match Railway).")
        elif env.get("ADMIN_SECRET"):
            # reverse: secrets file from .env
            sec2 = dict(sec)
            sec2.update({k: env[k] for k in ("APP_SECRET", "JWT_SECRET", "ADMIN_SECRET") if env.get(k)})
            write_secrets_file(
                SECRETS,
                sec2,
                "# Production secrets mirror — keep in sync with Railway Variables\n# Never commit.",
            )
            print("Local production-secrets mirrored FROM .env (still may not match Railway).")
        return 2

    label, admin = working
    print(f"\nWorking key source: {label} (fp={fp(admin)})")

    # Build canonical secrets dict: prefer production-secrets, fill from env, force ADMIN to working
    canon = dict(sec)
    for k, v in env.items():
        if k not in canon or not canon.get(k):
            canon[k] = v
    canon["ADMIN_SECRET"] = admin
    if not canon.get("JWT_SECRET") and canon.get("APP_SECRET"):
        canon["JWT_SECRET"] = canon["APP_SECRET"]
    # sensible defaults for prod mirror file
    canon.setdefault("EMAIL_DEV_MODE", "0")
    canon.setdefault("EMAIL_CODE_FALLBACK", "0")
    canon.setdefault("AUCTION_SCHEDULER", "1")
    canon.setdefault("AUCTION_SCHEDULER_SEC", "60")
    canon.setdefault(
        "ALLOWED_ORIGINS",
        "https://wakeagain.com,https://www.wakeagain.com,"
        "https://web-production-8ee81.up.railway.app,"
        "capacitor://localhost,http://localhost,ionic://localhost,https://localhost",
    )
    canon.setdefault("DATA_DIR", "/data")
    canon.setdefault("URL", "https://wakeagain.com")
    canon.setdefault("SERVICE", "web")

    write_secrets_file(
        SECRETS,
        canon,
        "# Production secrets mirror — MUST match Railway Variables\n"
        "# Synced by _sync_admin_secrets.py · never commit · never regenerate casually",
    )
    merge_env_preserve_non_secrets(ENV, canon)
    print("Wrote matching ADMIN_SECRET to production-secrets.local.txt and .env")

    # verify both equal
    a1 = parse_kv(SECRETS).get("ADMIN_SECRET")
    a2 = parse_kv(ENV).get("ADMIN_SECRET")
    print("local files same:", a1 == a2, "fp=", fp(a1 or ""))

    # cleanup QA users
    st, users_body = http_json(
        "GET",
        LIVE + "/api/v1/admin/users?limit=100",
        headers={"X-Admin-Key": admin},
    )
    print("admin users list:", st)
    qa_ids: list[int] = []
    qa_emails: list[str] = []
    if st == 200:
        rows = users_body.get("users") or users_body.get("items") or []
        for u in rows:
            em = (u.get("email") or "").lower()
            if em.startswith("qa_seller_") or em.startswith("qa_buyer_") or em.startswith("qa_"):
                qa_ids.append(int(u["id"]))
                qa_emails.append(em)
        print(f"QA candidates: {len(qa_ids)} {qa_emails}")
    else:
        print("users list body", str(users_body)[:200])

    if qa_ids:
        st_d, body_d = http_json(
            "POST",
            LIVE + "/api/v1/admin/users/delete",
            headers={"X-Admin-Key": admin},
            body={"confirm": "DELETE_SELECTED_USERS", "user_ids": qa_ids},
        )
        print("delete status", st_d, str(body_d)[:300])
    else:
        print("No qa_* users found (or list failed)")

    st_s, stats = http_json("GET", LIVE + "/api/v1/stats")
    if st_s == 200:
        print(
            "stats users=",
            stats.get("users"),
            "verified=",
            stats.get("users_email_verified"),
            "projects=",
            stats.get("projects"),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
