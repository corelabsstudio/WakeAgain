"""SQLite durability for WakeAgain member/listing data.

Why this exists
---------------
A wiped users table is an existential failure for the product.
We keep online-safe snapshots under DATA_DIR/backups, rotate them,
and surface last-known counts so a silent drop to zero is loud.

Never deletes wakeagain.db. Destructive ops (purge / restore) are gated
elsewhere by ALLOW_DESTRUCTIVE_ADMIN.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wakeagain.db import DATA, DB_PATH, connect

BACKUP_DIR = DATA / "backups"
META_PATH = DATA / "db_health.json"

# Defaults: hourly snapshots, keep ~48h + daily stamps ~14d
_DEFAULT_INTERVAL_SEC = 3600
_DEFAULT_KEEP_HOURLY = 48
_DEFAULT_KEEP_DAILY = 14

_lock = threading.Lock()
_state: dict[str, Any] = {
    "enabled": True,
    "last_backup_at": None,
    "last_backup_path": None,
    "last_backup_ok": None,
    "last_error": None,
    "last_users": None,
    "runs": 0,
    "interval_sec": _DEFAULT_INTERVAL_SEC,
}


def _env_bool(name: str, default: bool = True) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw not in ("0", "false", "off", "no")


def is_enabled() -> bool:
    return _env_bool("DB_BACKUP_ENABLED", True)


def interval_sec() -> int:
    try:
        n = int(os.environ.get("DB_BACKUP_INTERVAL_SEC") or str(_DEFAULT_INTERVAL_SEC))
    except ValueError:
        n = _DEFAULT_INTERVAL_SEC
    return max(300, min(n, 86_400))  # 5 min … 24 h


def keep_hourly() -> int:
    try:
        return max(4, min(int(os.environ.get("DB_BACKUP_KEEP_HOURLY") or _DEFAULT_KEEP_HOURLY), 168))
    except ValueError:
        return _DEFAULT_KEEP_HOURLY


def keep_daily() -> int:
    try:
        return max(3, min(int(os.environ.get("DB_BACKUP_KEEP_DAILY") or _DEFAULT_KEEP_DAILY), 90))
    except ValueError:
        return _DEFAULT_KEEP_DAILY


def status() -> dict[str, Any]:
    with _lock:
        out = dict(_state)
    out["enabled"] = is_enabled()
    out["interval_sec"] = interval_sec()
    out["backup_dir"] = str(BACKUP_DIR)
    out["db_path"] = str(DB_PATH)
    out["db_exists"] = DB_PATH.is_file()
    out["db_size_bytes"] = int(DB_PATH.stat().st_size) if DB_PATH.is_file() else 0
    out["data_dir"] = str(DATA)
    out["meta"] = _load_meta()
    return out


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_meta() -> dict[str, Any]:
    try:
        if META_PATH.is_file():
            return json.loads(META_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_meta(patch: dict[str, Any]) -> dict[str, Any]:
    meta = _load_meta()
    meta.update(patch)
    meta["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[WakeAgain][backup] meta write failed: {e}", flush=True)
    return meta


def count_users() -> int:
    if not DB_PATH.is_file():
        return 0
    try:
        with connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
            return int(row["c"] if row and "c" in row.keys() else row[0])
    except Exception:
        return 0


def integrity_ok() -> tuple[bool, str]:
    if not DB_PATH.is_file():
        return True, "no_db_yet"
    try:
        with connect() as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            msg = str(row[0] if row else "unknown")
            return msg.lower() == "ok", msg
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def live_counts() -> dict[str, int]:
    tables = (
        "users",
        "projects",
        "bids",
        "interests",
        "leads",
        "notifications",
        "messages",
        "fee_invoices",
        "reports",
        "reviews",
        "showcases",
    )
    out: dict[str, int] = {}
    if not DB_PATH.is_file():
        return {t: 0 for t in tables}
    try:
        with connect() as conn:
            for t in tables:
                try:
                    n = int(conn.execute(f"SELECT COUNT(*) AS c FROM {t}").fetchone()["c"])
                except Exception:
                    n = -1
                out[t] = n
    except Exception:
        return {t: -1 for t in tables}
    return out


def detect_user_collapse() -> dict[str, Any] | None:
    """If we previously saw members and now have zero, return a critical alert dict."""
    meta = _load_meta()
    peak = int(meta.get("peak_users") or 0)
    last = int(meta.get("last_users") or 0)
    now = count_users()
    if peak <= 0 and last <= 0:
        return None
    if now == 0 and (peak > 0 or last > 0):
        return {
            "code": "user_count_collapsed",
            "severity": True,
            "message": (
                f"CRITICAL: users dropped to 0 (last_known={last}, peak={peak}). "
                "Check /data/backups and restore immediately. Do not re-init empty DB as final truth."
            ),
            "last_users": last,
            "peak_users": peak,
            "current_users": now,
        }
    return None


def _backup_filename(reason: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", (reason or "manual").strip())[:40] or "manual"
    return f"wakeagain-{_utc_stamp()}-{safe}.db"


def create_backup(reason: str = "manual") -> dict[str, Any]:
    """Online-safe SQLite snapshot into DATA_DIR/backups. Never touches primary except read."""
    if not is_enabled() and reason not in ("manual", "pre-purge", "pre-restore", "startup"):
        return {"ok": False, "skipped": True, "reason": "disabled"}

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.is_file():
        return {"ok": False, "error": "primary db missing", "path": str(DB_PATH)}

    ok_int, int_msg = integrity_ok()
    users = count_users()
    counts = live_counts()
    dest = BACKUP_DIR / _backup_filename(reason)

    try:
        src = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        try:
            # Ensure WAL pages are not half-written in the copy
            try:
                src.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception:
                pass
            dst = sqlite3.connect(str(dest))
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()

        size = int(dest.stat().st_size) if dest.is_file() else 0
        if size < 1:
            raise RuntimeError("backup file empty")

        meta = _save_meta(
            {
                "last_users": users,
                "peak_users": max(int(_load_meta().get("peak_users") or 0), users),
                "last_backup_at": datetime.now(timezone.utc).isoformat(),
                "last_backup_file": dest.name,
                "last_counts": counts,
                "last_integrity": int_msg,
            }
        )
        rotated = rotate_backups()
        with _lock:
            _state["last_backup_at"] = meta.get("last_backup_at")
            _state["last_backup_path"] = str(dest)
            _state["last_backup_ok"] = True
            _state["last_error"] = None
            _state["last_users"] = users
            _state["runs"] = int(_state.get("runs") or 0) + 1

        print(
            f"[WakeAgain][backup] ok reason={reason} users={users} file={dest.name} "
            f"bytes={size} integrity={int_msg}",
            flush=True,
        )
        return {
            "ok": True,
            "path": str(dest),
            "name": dest.name,
            "size_bytes": size,
            "users": users,
            "counts": counts,
            "integrity": int_msg,
            "integrity_ok": ok_int,
            "rotated_removed": rotated,
            "reason": reason,
        }
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        with _lock:
            _state["last_backup_ok"] = False
            _state["last_error"] = err
            _state["runs"] = int(_state.get("runs") or 0) + 1
        print(f"[WakeAgain][backup] FAIL reason={reason}: {err}", flush=True)
        # Best-effort cleanup of partial file
        try:
            if dest.is_file() and dest.stat().st_size < 1024:
                dest.unlink(missing_ok=True)
        except Exception:
            pass
        return {"ok": False, "error": err, "reason": reason}


def list_backups(limit: int = 50) -> list[dict[str, Any]]:
    if not BACKUP_DIR.is_dir():
        return []
    files = sorted(BACKUP_DIR.glob("wakeagain-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict[str, Any]] = []
    for p in files[: max(1, min(limit, 200))]:
        st = p.stat()
        out.append(
            {
                "name": p.name,
                "path": str(p),
                "size_bytes": int(st.st_size),
                "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return out


def rotate_backups() -> int:
    """Keep recent hourly + one per day for keep_daily days. Returns removed count."""
    if not BACKUP_DIR.is_dir():
        return 0
    files = sorted(BACKUP_DIR.glob("wakeagain-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return 0

    keep: set[Path] = set()
    # Most recent N
    for p in files[: keep_hourly()]:
        keep.add(p)

    # One per UTC day for last keep_daily days (newest in each day)
    by_day: dict[str, Path] = {}
    for p in files:
        day = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%d")
        if day not in by_day:
            by_day[day] = p
    for day, p in sorted(by_day.items(), reverse=True)[: keep_daily()]:
        keep.add(p)

    removed = 0
    for p in files:
        if p in keep:
            continue
        try:
            p.unlink()
            removed += 1
        except Exception as e:
            print(f"[WakeAgain][backup] rotate skip {p.name}: {e}", flush=True)
    return removed


def restore_from_backup(name: str) -> dict[str, Any]:
    """Overwrite primary DB contents from a named backup (sqlite backup API).

    Avoids file-level replace (Windows locks / open handles). Caller must enforce
    destructive admin gate.
    """
    safe = Path(name).name
    if not re.fullmatch(r"wakeagain-\d{8}T\d{6}Z-[a-zA-Z0-9_-]+\.db", safe):
        return {"ok": False, "error": "invalid backup name"}
    src_path = BACKUP_DIR / safe
    if not src_path.is_file():
        return {"ok": False, "error": "backup not found"}

    # Snapshot current primary first (even if empty)
    pre = create_backup(reason="pre-restore")
    try:
        src = sqlite3.connect(f"file:{src_path.as_posix()}?mode=ro", uri=True, check_same_thread=False)
        try:
            dst = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            try:
                try:
                    dst.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except Exception:
                    pass
                # source.backup(dest) copies all pages from backup → live DB
                src.backup(dst)
                try:
                    dst.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except Exception:
                    pass
            finally:
                dst.close()
        finally:
            src.close()

        users = count_users()
        ok_int, int_msg = integrity_ok()
        _save_meta(
            {
                "last_users": users,
                "peak_users": max(int(_load_meta().get("peak_users") or 0), users),
                "last_restore_at": datetime.now(timezone.utc).isoformat(),
                "last_restore_from": safe,
                "last_integrity": int_msg,
            }
        )
        print(
            f"[WakeAgain][backup] RESTORED from={safe} users={users} integrity={int_msg}",
            flush=True,
        )
        return {
            "ok": True,
            "restored_from": safe,
            "users": users,
            "integrity": int_msg,
            "integrity_ok": ok_int,
            "pre_restore_backup": pre.get("name"),
        }
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        print(f"[WakeAgain][backup] RESTORE FAIL: {err}", flush=True)
        return {"ok": False, "error": err, "pre_restore_backup": pre.get("name")}


def record_counts_tick() -> dict[str, Any]:
    """Update peak/last without forcing a full file backup (cheap)."""
    users = count_users()
    counts = live_counts()
    meta = _load_meta()
    peak = max(int(meta.get("peak_users") or 0), users)
    _save_meta({"last_users": users, "peak_users": peak, "last_counts": counts})
    with _lock:
        _state["last_users"] = users
    alert = detect_user_collapse()
    if alert:
        print(f"[WakeAgain][backup] {alert['message']}", flush=True)
    return {"users": users, "peak_users": peak, "alert": alert}


def startup_hooks() -> dict[str, Any]:
    """Call once after init_db(). Logs critical empty-after-peak; takes startup snapshot."""
    DATA.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Prefer WAL for crash resilience on volume
    try:
        with connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
    except Exception as e:
        print(f"[WakeAgain][backup] pragma: {e}", flush=True)

    users = count_users()
    alert = detect_user_collapse()
    ok_int, int_msg = integrity_ok()
    snap = None
    if is_enabled() and DB_PATH.is_file():
        # Always snapshot on boot when members exist; also when empty so we have a baseline file trail
        snap = create_backup(reason="startup")
    else:
        record_counts_tick()

    if alert:
        print(f"[WakeAgain][backup] {alert['message']}", flush=True)
    elif users == 0:
        print(
            "[WakeAgain][backup] NOTE: users=0 at startup. "
            "If this is production after real signups, check backups immediately.",
            flush=True,
        )
    else:
        print(f"[WakeAgain][backup] startup users={users} integrity={int_msg}", flush=True)

    return {
        "users": users,
        "integrity_ok": ok_int,
        "integrity": int_msg,
        "alert": alert,
        "backup": snap,
    }


def maybe_periodic_backup(force: bool = False) -> dict[str, Any] | None:
    """Scheduler tick: backup if interval elapsed."""
    if not is_enabled() and not force:
        return None
    with _lock:
        last = _state.get("last_backup_at")
    if not force and last:
        try:
            # last is isoformat UTC
            ts = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds()
            if age < interval_sec():
                record_counts_tick()
                return None
        except Exception:
            pass
    return create_backup(reason="scheduled")
