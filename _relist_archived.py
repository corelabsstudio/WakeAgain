"""Ops helper: list archived listings, or force-relist specific ones on live prod.

Usage:
    python _relist_archived.py                 # list archived listings (id, title, owner)
    python _relist_archived.py --resume 12 34   # force a fresh live round for project ids 12 and 34

Reads admin key + live URL from .launch/production-secrets.local.txt (same
convention as _sync_admin_secrets.py). Never prints the secret itself.
"""
from __future__ import annotations

import json
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
MIRROR = ROOT / ".launch" / "production-secrets.local.txt"


def load_secrets() -> dict[str, str]:
    d: dict[str, str] = {}
    if not MIRROR.is_file():
        print(f"missing {MIRROR}", file=sys.stderr)
        sys.exit(1)
    for raw in MIRROR.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def call(base: str, key: str, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    url = base.rstrip("/") + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"X-Admin-Key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:500]}


def main() -> None:
    secrets = load_secrets()
    key = secrets.get("ADMIN_SECRET", "")
    base = "https://wakeagain.com"
    if not key:
        print("ADMIN_SECRET missing from mirror file", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]
    if args and args[0] == "--resume":
        ids = [int(a) for a in args[1:]]
        if not ids:
            print("usage: python _relist_archived.py --resume <id> [id...]")
            sys.exit(1)
        for pid in ids:
            status, payload = call(base, key, "POST", f"/api/v1/admin/projects/{pid}/resume-auction", {"force_live": True, "note": "seller-requested relist"})
            print(pid, status, json.dumps(payload, ensure_ascii=False)[:400])
        return

    status, payload = call(base, key, "GET", "/api/v1/admin/projects?status=all")
    if status != 200:
        print("session check failed:", status, payload)
        sys.exit(1)
    archived = [p for p in payload.get("projects", []) if p.get("listing_status") == "archived"]
    if not archived:
        print("archived 상태 매물 없음 (status=all, limit 200 안에서)")
        return
    for p in archived:
        print(f"id={p['id']:<6} title={p.get('title','')!r:<40} owner={p.get('owner_label','')} ({p.get('owner_email','')})")


if __name__ == "__main__":
    main()
