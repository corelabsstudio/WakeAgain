"""Background jobs for WakeAgain (no external cron required).

Default: every 60s process expired auctions (auto-close / auto-award).
Toggle: AUCTION_SCHEDULER=0 to disable.
Interval: AUCTION_SCHEDULER_SEC (default 60, min 15).
"""
from __future__ import annotations

import os
import threading
import time
import traceback
from datetime import datetime, timezone
from typing import Any

from wakeagain import db as database

_lock = threading.Lock()
_state: dict[str, Any] = {
    "enabled": False,
    "running": False,
    "interval_sec": 60,
    "last_run_at": None,
    "last_ok": None,
    "last_closed": 0,
    "last_error": None,
    "runs": 0,
}
_stop = threading.Event()
_thread: threading.Thread | None = None


def _interval() -> int:
    try:
        n = int(os.environ.get("AUCTION_SCHEDULER_SEC") or "60")
    except ValueError:
        n = 60
    return max(15, min(n, 3600))


def is_enabled() -> bool:
    v = (os.environ.get("AUCTION_SCHEDULER") or "1").strip().lower()
    return v not in ("0", "false", "off", "no")


def status() -> dict[str, Any]:
    with _lock:
        return dict(_state)


def run_once() -> int:
    """Process expired auctions once. Returns number closed."""
    closed = 0
    err: str | None = None
    try:
        with database.db() as conn:
            closed = int(database.process_expired_auctions(conn) or 0)
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        traceback.print_exc()
    now = datetime.now(timezone.utc).isoformat()
    with _lock:
        _state["last_run_at"] = now
        _state["last_closed"] = closed
        _state["last_ok"] = err is None
        _state["last_error"] = err
        _state["runs"] = int(_state.get("runs") or 0) + 1
    if closed:
        print(f"[WakeAgain] scheduler: closed {closed} auction(s)")
    return closed


def _loop() -> None:
    with _lock:
        _state["running"] = True
    try:
        while not _stop.is_set():
            if is_enabled():
                run_once()
            # wake often so stop is responsive
            wait = _interval()
            for _ in range(wait):
                if _stop.is_set():
                    break
                time.sleep(1)
    finally:
        with _lock:
            _state["running"] = False


def start() -> None:
    global _thread
    if not is_enabled():
        with _lock:
            _state["enabled"] = False
        print("[WakeAgain] auction scheduler disabled (AUCTION_SCHEDULER=0)")
        return
    with _lock:
        if _thread and _thread.is_alive():
            return
        _state["enabled"] = True
        _state["interval_sec"] = _interval()
        _stop.clear()
        _thread = threading.Thread(target=_loop, name="wa-auction-scheduler", daemon=True)
        _thread.start()
    print(f"[WakeAgain] auction scheduler started (every {_interval()}s)")


def stop() -> None:
    _stop.set()
    t = _thread
    if t and t.is_alive():
        t.join(timeout=3)
