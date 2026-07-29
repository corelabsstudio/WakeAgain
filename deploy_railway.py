"""Deploy WakeAgain to Railway using Account Token file.

Prereq:
  1. Create Account Token at https://railway.com/account/tokens
  2. Save one line to: .launch/railway.token
     (or C:\\Users\\hysoo\\projects\\RoadLog\\.launch\\railway.token)

Usage:
  python deploy_railway.py
  python deploy_railway.py --set-vars
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOKEN_CANDIDATES = [
    ROOT / ".launch" / "railway.token",
    Path(r"C:\Users\hysoo\projects\RoadLog\.launch\railway.token"),
]
GQL = "https://backboard.railway.app/graphql/v2"
PROJECT_NAME = "WakeAgain"
SERVICE_NAME = "web"


def find_token() -> str:
    for p in TOKEN_CANDIDATES:
        if p.is_file():
            t = p.read_text(encoding="utf-8-sig").strip().splitlines()[0].strip()
            t = t.lstrip("\ufeff").strip()
            if t and not t.startswith("#"):
                return t
    raise SystemExit(
        "Railway token missing/invalid path.\n"
        "  Create Account Token: https://railway.com/account/tokens\n"
        f"  Save one line to: {TOKEN_CANDIDATES[0]}"
    )


def gql(token: str, query: str, variables: dict | None = None) -> dict:
    body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        GQL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Railway API HTTP {e.code}: {err[:300]}") from e
    if data.get("errors"):
        msg = data["errors"][0].get("message", str(data["errors"]))
        raise SystemExit(f"Railway GraphQL error: {msg}")
    return data.get("data") or {}


def ensure_cli_token(token: str) -> None:
    os.environ["RAILWAY_TOKEN"] = token


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=str(ROOT), env=os.environ.copy(), **kw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set-vars", action="store_true", help="set production env vars after deploy")
    ap.add_argument("--project", default=PROJECT_NAME)
    args = ap.parse_args()

    token = find_token()
    ensure_cli_token(token)

    # Auth check
    me = gql(token, "{ me { name email } }")
    if not me.get("me"):
        raise SystemExit(
            "Token unauthorized. Create a new **Account Token** at\n"
            "  https://railway.com/account/tokens\n"
            f"and save it to {TOKEN_CANDIDATES[0]}"
        )
    print(f"Logged in as: {me['me'].get('email') or me['me'].get('name')}")

    # Prefer CLI for deploy if available
    who = run(["railway", "whoami"], capture_output=True, text=True)
    if who.returncode != 0:
        raise SystemExit(
            "railway whoami failed with this token.\n"
            "Need Account Token (not old Project UUID token).\n"
            f"whoami: {who.stderr or who.stdout}"
        )
    print(who.stdout.strip())

    # Link or create project
    link = ROOT / ".railway"
    if not (ROOT / "railway.json").is_file() and not (ROOT / ".railway").exists():
        # Try list projects via CLI
        print("Linking project (non-interactive where possible)...")
        # Create new project if needed via GraphQL
        data = gql(
            token,
            """
            query {
              projects {
                edges { node { id name }
                }
              }
            }
            """,
        )
        edges = (((data.get("projects") or {}).get("edges")) or [])
        pid = None
        for e in edges:
            node = e.get("node") or {}
            if (node.get("name") or "").lower() == args.project.lower():
                pid = node.get("id")
                break
        if not pid:
            created = gql(
                token,
                """
                mutation($name: String!) {
                  projectCreate(input: { name: $name }) { id name }
                }
                """,
                {"name": args.project},
            )
            pid = (created.get("projectCreate") or {}).get("id")
            print(f"Created project {args.project}: {pid}")
        else:
            print(f"Using existing project {args.project}: {pid}")

        # railway link --project
        r = run(["railway", "link", "--project", pid], capture_output=True, text=True)
        if r.returncode != 0:
            # older CLI: interactive only — fall back to env
            print("railway link output:", r.stderr or r.stdout)
            print("Trying railway up with RAILWAY_PROJECT_ID...")
            os.environ["RAILWAY_PROJECT_ID"] = pid

    # Production variables — only when explicitly requested.
    # Default deploy must NOT rotate APP_SECRET/JWT_SECRET/ADMIN_SECRET (logs everyone out).
    if args.set_vars:
        secrets_path = ROOT / ".launch" / "production-secrets.local.txt"
        env_path = ROOT / ".env"
        # Canonical: production-secrets.local.txt, then fill gaps from .env
        existing: dict[str, str] = {}
        if secrets_path.is_file():
            for line in secrets_path.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k not in existing or not existing[k]:
                    existing[k] = v

        # Never silently mint a new ADMIN_SECRET — that is what drifts Railway vs local.
        if not (existing.get("ADMIN_SECRET") or "").strip():
            raise SystemExit(
                "ADMIN_SECRET missing in .launch/production-secrets.local.txt and .env.\n"
                "Copy the current value from Railway Variables first, then re-run --set-vars.\n"
                "Refusing to generate a new key (prevents admin lockout / secret drift)."
            )
        if not (existing.get("APP_SECRET") or "").strip():
            raise SystemExit(
                "APP_SECRET missing. Copy from Railway Variables into "
                ".launch/production-secrets.local.txt before --set-vars."
            )

        app_secret = existing["APP_SECRET"].strip()
        admin_secret = existing["ADMIN_SECRET"].strip()
        vars_pairs = {
            "APP_SECRET": app_secret,
            "JWT_SECRET": (existing.get("JWT_SECRET") or app_secret).strip(),
            "ADMIN_SECRET": admin_secret,
            "EMAIL_DEV_MODE": "0",
            "EMAIL_CODE_FALLBACK": "0",
            "AUCTION_SCHEDULER": "1",
            "AUCTION_SCHEDULER_SEC": "60",
            "ALLOWED_ORIGINS": (
                "https://wakeagain.com,https://www.wakeagain.com,"
                "https://web-production-8ee81.up.railway.app,"
                "capacitor://localhost,http://localhost,ionic://localhost,https://localhost"
            ),
            "DATA_DIR": "/data",
        }
        secrets_path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# Production secrets mirror — MUST match Railway Variables\n"
            "# --set-vars reuses these; never auto-generates ADMIN_SECRET.\n"
            "# Also keep .env in sync (python _sync_admin_secrets.py).\n"
            "# Never commit."
        )
        secrets_path.write_text(
            header + "\n" + "\n".join(f"{k}={v}" for k, v in vars_pairs.items()) + "\n",
            encoding="utf-8",
        )
        # Mirror into .env so local tools use the same ADMIN_SECRET
        env_lines = [
            "# Local env — secrets mirrored from production-secrets.local.txt",
            "# Do not commit.",
            f"APP_SECRET={vars_pairs['APP_SECRET']}",
            f"JWT_SECRET={vars_pairs['JWT_SECRET']}",
            f"ADMIN_SECRET={vars_pairs['ADMIN_SECRET']}",
            "EMAIL_DEV_MODE=1",
            "AUCTION_SCHEDULER=1",
            "AUCTION_SCHEDULER_SEC=60",
            "ALLOWED_ORIGINS=*",
            "OAUTH_PUBLIC_BASE=http://127.0.0.1:8080",
            "",
        ]
        env_path.write_text("\n".join(env_lines), encoding="utf-8")
        print(f"Wrote local secrets mirror: {secrets_path} + {env_path} (gitignored)")
        for k, v in vars_pairs.items():
            r = run(
                ["railway", "variables", "--set", f"{k}={v}"],
                capture_output=True,
                text=True,
            )
            if r.returncode != 0:
                print(f"  warn set {k}: {(r.stderr or r.stdout)[:200]}")
            else:
                print(f"  set {k}")
    else:
        print(
            "Skipping variable rotation (default). "
            "Pass --set-vars only to push EXISTING secrets to Railway — never invents new ADMIN_SECRET."
        )

    # Deploy current working tree (latest local files)
    print("Deploying (railway up)...")
    up = run(["railway", "up", "--detach"], capture_output=True, text=True)
    print(up.stdout)
    if up.returncode != 0:
        print(up.stderr)
        raise SystemExit(up.returncode)

    # Domain / status
    time.sleep(2)
    st = run(["railway", "status"], capture_output=True, text=True)
    print(st.stdout or st.stderr)
    dom = run(["railway", "domain"], capture_output=True, text=True)
    print(dom.stdout or dom.stderr)

    print("\nDone. Open Railway dashboard for build logs.")
    print("Live: https://web-production-8ee81.up.railway.app/")
    print("Health: https://web-production-8ee81.up.railway.app/health")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
