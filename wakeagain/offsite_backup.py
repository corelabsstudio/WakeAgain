"""Off-site SQLite backup via S3-compatible object storage.

Works with: Cloudflare R2, AWS S3, Backblaze B2 (S3 API), MinIO.

Why
---
Volume-local snapshots still die if the volume is wiped or the project is
deleted. Off-site copies are the second parachute for member data.

Env (all required for upload, except region/prefix defaults)::

  OFFSITE_BACKUP_ENABLED=1          # default: on when credentials present
  OFFSITE_S3_ENDPOINT=https://<acct>.r2.cloudflarestorage.com
  OFFSITE_S3_BUCKET=wakeagain-backups
  OFFSITE_S3_ACCESS_KEY=...
  OFFSITE_S3_SECRET_KEY=...
  OFFSITE_S3_REGION=auto            # R2 uses "auto"; AWS e.g. ap-northeast-2
  OFFSITE_S3_PREFIX=wakeagain/      # object key prefix
  OFFSITE_S3_FORCE_PATH_STYLE=1     # R2/MinIO usually 1; AWS virtual-host 0
  OFFSITE_KEEP_REMOTE=60            # max objects kept under prefix
  OFFSITE_UPLOAD_REASONS=startup,scheduled,manual,pre-purge,pre-restore

Uses AWS Signature Version 4 over httpx (no boto3 dependency).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

_lock = threading.Lock()
_state: dict[str, Any] = {
    "last_upload_at": None,
    "last_upload_key": None,
    "last_upload_ok": None,
    "last_error": None,
    "last_skipped": None,
    "uploads": 0,
    "configured": False,
}


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name)
    if not raw:
        return default
    return raw.lower() not in ("0", "false", "off", "no")


def config() -> dict[str, Any]:
    endpoint = _env("OFFSITE_S3_ENDPOINT").rstrip("/")
    bucket = _env("OFFSITE_S3_BUCKET")
    access = _env("OFFSITE_S3_ACCESS_KEY") or _env("AWS_ACCESS_KEY_ID")
    secret = _env("OFFSITE_S3_SECRET_KEY") or _env("AWS_SECRET_ACCESS_KEY")
    region = _env("OFFSITE_S3_REGION") or _env("AWS_DEFAULT_REGION") or "auto"
    prefix = _env("OFFSITE_S3_PREFIX", "wakeagain/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    # path-style default ON for R2/custom endpoints; OFF only when forced
    force_path = _env_bool("OFFSITE_S3_FORCE_PATH_STYLE", bool(endpoint))
    try:
        keep = max(5, min(int(_env("OFFSITE_KEEP_REMOTE") or "60"), 500))
    except ValueError:
        keep = 60
    reasons_raw = _env(
        "OFFSITE_UPLOAD_REASONS",
        "startup,scheduled,manual,pre-purge,pre-restore",
    )
    reasons = {r.strip() for r in reasons_raw.split(",") if r.strip()}
    creds_ok = bool(endpoint and bucket and access and secret)
    enabled_default = creds_ok  # auto-on when fully configured
    enabled = _env_bool("OFFSITE_BACKUP_ENABLED", enabled_default) and creds_ok
    return {
        "endpoint": endpoint,
        "bucket": bucket,
        "access_key": access,
        "secret_key": secret,
        "region": region,
        "prefix": prefix,
        "force_path_style": force_path,
        "keep_remote": keep,
        "reasons": reasons,
        "configured": creds_ok,
        "enabled": enabled,
    }


def is_configured() -> bool:
    return bool(config()["configured"])


def is_enabled() -> bool:
    return bool(config()["enabled"])


def status() -> dict[str, Any]:
    cfg = config()
    with _lock:
        st = dict(_state)
    st["configured"] = cfg["configured"]
    st["enabled"] = cfg["enabled"]
    st["bucket"] = cfg["bucket"] or None
    st["endpoint_host"] = (
        cfg["endpoint"].split("://", 1)[-1].split("/", 1)[0] if cfg["endpoint"] else None
    )
    st["prefix"] = cfg["prefix"]
    st["keep_remote"] = cfg["keep_remote"]
    st["reasons"] = sorted(cfg["reasons"])
    # never expose secrets
    st["has_credentials"] = bool(cfg["access_key"] and cfg["secret_key"])
    return st


# --- AWS SigV4 helpers -------------------------------------------------------


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sign_key(secret: str, datestamp: str, region: str, service: str) -> bytes:
    k_date = _hmac(("AWS4" + secret).encode("utf-8"), datestamp)
    k_region = _hmac(k_date, region)
    k_service = _hmac(k_region, service)
    return _hmac(k_service, "aws4_request")


def _amz_dates() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")


def _quote_path(path: str) -> str:
    # S3 canonical URI: encode except /
    return "/".join(quote(p, safe="") for p in path.split("/"))


def _request(
    method: str,
    *,
    key: str = "",
    query: str = "",
    body: bytes = b"",
    content_type: str = "application/octet-stream",
    extra_headers: dict[str, str] | None = None,
    timeout: float = 120.0,
) -> httpx.Response:
    cfg = config()
    if not cfg["configured"]:
        raise RuntimeError("offsite S3 not configured")

    endpoint = cfg["endpoint"]
    bucket = cfg["bucket"]
    region = cfg["region"] or "auto"
    access = cfg["access_key"]
    secret = cfg["secret_key"]
    service = "s3"

    host = endpoint.split("://", 1)[-1].split("/", 1)[0]
    scheme = "https" if endpoint.startswith("https") else "http"

    # Object path
    key = key.lstrip("/")
    if cfg["force_path_style"]:
        # https://endpoint/bucket/key
        canon_uri = "/" + bucket + (("/" + key) if key else "")
        url_path = canon_uri
        host_header = host
    else:
        # virtual-hosted: https://bucket.endpoint/key
        host_header = f"{bucket}.{host}"
        canon_uri = "/" + key if key else "/"
        url_path = canon_uri

    amz_date, datestamp = _amz_dates()
    payload_hash = _sha256_hex(body)

    headers: dict[str, str] = {
        "host": host_header,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
    }
    if body or method in ("PUT", "POST"):
        headers["content-type"] = content_type
        headers["content-length"] = str(len(body))
    if extra_headers:
        for k, v in extra_headers.items():
            headers[k.lower()] = v

    # Signed headers
    signed_header_keys = sorted(headers.keys())
    signed_headers = ";".join(signed_header_keys)
    canonical_headers = "".join(f"{k}:{headers[k].strip()}\n" for k in signed_header_keys)

    canonical_query = query  # already sorted/encoded by caller when used
    canonical_request = "\n".join(
        [
            method,
            _quote_path(canon_uri) if not cfg["force_path_style"] else canon_uri,
            canonical_query,
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )
    # For path-style, URI segments after bucket still need encoding of key parts
    if cfg["force_path_style"] and key:
        encoded_key = "/".join(quote(p, safe="") for p in key.split("/"))
        canon_uri_enc = f"/{bucket}/{encoded_key}"
        canonical_request = "\n".join(
            [
                method,
                canon_uri_enc,
                canonical_query,
                canonical_headers,
                signed_headers,
                payload_hash,
            ]
        )
        url_path = canon_uri_enc

    credential_scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            _sha256_hex(canonical_request.encode("utf-8")),
        ]
    )
    signing_key = _sign_key(secret, datestamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    headers["authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={access}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    url = f"{scheme}://{host_header}{url_path}"
    if query:
        url = f"{url}?{query}"

    with httpx.Client(timeout=timeout) as client:
        return client.request(method, url, content=body if body else None, headers=headers)


def put_file(local_path: Path, object_key: str, *, metadata: dict[str, str] | None = None) -> dict[str, Any]:
    data = local_path.read_bytes()
    extra = {}
    if metadata:
        for k, v in metadata.items():
            # S3 user metadata
            extra[f"x-amz-meta-{k.lower()}"] = str(v)[:256]
    resp = _request(
        "PUT",
        key=object_key,
        body=data,
        content_type="application/x-sqlite3",
        extra_headers=extra or None,
        timeout=180.0,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"S3 PUT {resp.status_code}: {resp.text[:300]}")
    return {
        "ok": True,
        "key": object_key,
        "size_bytes": len(data),
        "etag": (resp.headers.get("etag") or "").strip('"'),
        "status_code": resp.status_code,
    }


def list_objects(max_keys: int = 100) -> list[dict[str, Any]]:
    cfg = config()
    prefix = cfg["prefix"]
    # ListObjectsV2 — canonical query must be sorted by name
    pairs = [
        ("list-type", "2"),
        ("max-keys", str(max(1, min(max_keys, 1000)))),
        ("prefix", prefix),
    ]
    pairs.sort(key=lambda x: x[0])
    q = "&".join(f"{quote(k, safe='-_.~')}={quote(v, safe='-_.~')}" for k, v in pairs)
    resp = _request("GET", key="", query=q, body=b"", timeout=60.0)
    if resp.status_code != 200:
        raise RuntimeError(f"S3 LIST {resp.status_code}: {resp.text[:300]}")
    root = ET.fromstring(resp.content)
    # namespace-agnostic
    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    items: list[dict[str, Any]] = []
    for el in root.iter():
        if local(el.tag) != "Contents":
            continue
        key = size = last_mod = ""
        for child in el:
            t = local(child.tag)
            if t == "Key":
                key = child.text or ""
            elif t == "Size":
                size = child.text or "0"
            elif t == "LastModified":
                last_mod = child.text or ""
        if key:
            items.append(
                {
                    "key": key,
                    "name": key.rsplit("/", 1)[-1],
                    "size_bytes": int(size or 0),
                    "last_modified": last_mod,
                }
            )
    items.sort(key=lambda x: x.get("last_modified") or "", reverse=True)
    return items


def delete_object(object_key: str) -> None:
    resp = _request("DELETE", key=object_key, body=b"", timeout=60.0)
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"S3 DELETE {resp.status_code}: {resp.text[:300]}")


def get_object_bytes(object_key: str) -> bytes:
    resp = _request("GET", key=object_key, body=b"", timeout=180.0)
    if resp.status_code != 200:
        raise RuntimeError(f"S3 GET {resp.status_code}: {resp.text[:300]}")
    return resp.content


def rotate_remote() -> int:
    cfg = config()
    keep = int(cfg["keep_remote"])
    try:
        items = list_objects(max_keys=1000)
    except Exception as e:
        print(f"[WakeAgain][offsite] list for rotate failed: {e}", flush=True)
        return 0
    # only our backup files
    ours = [i for i in items if re.search(r"wakeagain-\d{8}T\d{6}Z-", i.get("name") or "")]
    removed = 0
    for item in ours[keep:]:
        try:
            delete_object(item["key"])
            removed += 1
        except Exception as e:
            print(f"[WakeAgain][offsite] rotate delete {item.get('key')}: {e}", flush=True)
    return removed


def object_key_for(filename: str) -> str:
    cfg = config()
    # nest by UTC date for browsing
    # wakeagain-20260722T022744Z-startup.db → 2026/07/22/
    m = re.match(r"wakeagain-(\d{4})(\d{2})(\d{2})T", filename)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        return f"{cfg['prefix']}{y}/{mo}/{d}/{filename}"
    return f"{cfg['prefix']}{filename}"


def should_upload(reason: str) -> bool:
    cfg = config()
    if not cfg["enabled"]:
        return False
    r = (reason or "manual").strip().lower()
    return r in cfg["reasons"] or r == "manual"


def upload_backup_file(
    local_path: Path | str,
    *,
    reason: str = "manual",
    users: int | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Upload a local snapshot file. Safe no-op when not configured/enabled."""
    path = Path(local_path)
    cfg = config()
    if not cfg["configured"]:
        with _lock:
            _state["last_skipped"] = "not_configured"
        return {"ok": False, "skipped": True, "reason": "not_configured"}
    if not cfg["enabled"] and not force:
        with _lock:
            _state["last_skipped"] = "disabled"
        return {"ok": False, "skipped": True, "reason": "disabled"}
    if not force and not should_upload(reason):
        with _lock:
            _state["last_skipped"] = f"reason:{reason}"
        return {"ok": False, "skipped": True, "reason": f"reason_filtered:{reason}"}
    if not path.is_file():
        return {"ok": False, "error": "local file missing"}

    key = object_key_for(path.name)
    meta = {
        "reason": (reason or "manual")[:40],
        "users": str(users if users is not None else ""),
        "source": "wakeagain",
    }
    try:
        result = put_file(path, key, metadata=meta)
        rotated = 0
        try:
            rotated = rotate_remote()
        except Exception:
            pass
        with _lock:
            _state["last_upload_at"] = datetime.now(timezone.utc).isoformat()
            _state["last_upload_key"] = key
            _state["last_upload_ok"] = True
            _state["last_error"] = None
            _state["last_skipped"] = None
            _state["uploads"] = int(_state.get("uploads") or 0) + 1
            _state["configured"] = True
        print(
            f"[WakeAgain][offsite] uploaded key={key} bytes={result.get('size_bytes')} "
            f"reason={reason} rotated={rotated}",
            flush=True,
        )
        return {
            "ok": True,
            "key": key,
            "size_bytes": result.get("size_bytes"),
            "etag": result.get("etag"),
            "rotated_removed": rotated,
            "reason": reason,
        }
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        with _lock:
            _state["last_upload_ok"] = False
            _state["last_error"] = err
            _state["uploads"] = int(_state.get("uploads") or 0) + 1
        print(f"[WakeAgain][offsite] UPLOAD FAIL: {err}", flush=True)
        return {"ok": False, "error": err, "reason": reason}


def download_to_local(object_key: str, dest_dir: Path) -> dict[str, Any]:
    """Download remote object into dest_dir; returns local path name."""
    safe_name = Path(object_key).name
    if not re.fullmatch(r"wakeagain-\d{8}T\d{6}Z-[a-zA-Z0-9_-]+\.db", safe_name):
        return {"ok": False, "error": "invalid remote backup name"}
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe_name
    data = get_object_bytes(object_key)
    if len(data) < 100:
        return {"ok": False, "error": "remote object too small"}
    dest.write_bytes(data)
    return {"ok": True, "name": safe_name, "path": str(dest), "size_bytes": len(data)}
