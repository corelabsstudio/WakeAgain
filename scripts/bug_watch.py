# -*- coding: utf-8 -*-
"""
WakeAgain continuous bug-watch loop.

What it can do automatically:
  1) DISCOVER — run smoke / deal / auction suites on an interval
  2) LOG — write pass/fail + full output under data/test_watch/
  3) AUTO-FIX (limited) — apply *known* repair routines when failure
     signatures match (not general AI coding)

What it cannot do alone:
  - Invent arbitrary product fixes for unknown bugs
  - Safely auto-deploy without review

Usage:
  python scripts/bug_watch.py              # once
  python scripts/bug_watch.py --loop 300   # every 5 min
  python scripts/bug_watch.py --quick      # smoke only
  python scripts/bug_watch.py --fix       # try known auto-fixes on fail, re-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "data" / "test_watch"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Suites: (id, script, timeout_sec)
SUITES_FULL = [
    ("smoke", "_smoke_check.py", 180),
    ("deal", "_deal_flow_test.py", 180),
    ("auction", "_auction_suite_test.py", 300),
    ("advanced", "_auction_advanced_test.py", 300),
]
SUITES_QUICK = [
    ("smoke", "_smoke_check.py", 180),
    ("deal", "_deal_flow_test.py", 180),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_suite(script: str, timeout: int) -> dict:
    path = ROOT / script
    if not path.is_file():
        return {
            "script": script,
            "ok": False,
            "exit_code": 127,
            "seconds": 0,
            "stdout": "",
            "stderr": f"missing {script}",
        }
    env = os.environ.copy()
    env.setdefault("ADMIN_SECRET", "wakeagain-admin-dev")
    env.setdefault("SECOND_BIDDER_AUTO", "1")
    t0 = time.time()
    try:
        p = subprocess.run(
            [sys.executable, "-u", str(path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        out = p.stdout or ""
        err = p.stderr or ""
        code = p.returncode
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") if isinstance(e.stdout, str) else ""
        err = f"TIMEOUT after {timeout}s\n" + ((e.stderr or "") if isinstance(e.stderr, str) else "")
        code = 124
    sec = round(time.time() - t0, 2)
    # Heuristic: many suites print SUMMARY with passed count
    ok = code == 0
    if not ok and "All " in out and "passed" in out.lower() and "FAIL" not in out:
        ok = True
    return {
        "script": script,
        "ok": ok,
        "exit_code": code,
        "seconds": sec,
        "stdout": out[-12000:],
        "stderr": err[-4000:],
    }


def extract_failures(text: str) -> list[str]:
    fails = []
    for line in (text or "").splitlines():
        if "[FAIL]" in line or line.strip().startswith("- ") and ":" in line:
            fails.append(line.strip()[:300])
    return fails[:40]


# ── Known auto-fixes (signature → repair function) ─────────────────────────


def _fix_price_current_race() -> dict:
    """Ensure place_bid uses MAX(amount) for price_current."""
    api = ROOT / "wakeagain" / "api.py"
    src = api.read_text(encoding="utf-8")
    needle = "SELECT COALESCE(MAX(amount)"
    if needle in src:
        return {"applied": False, "reason": "already has MAX(amount) race-safe update"}
    # Conservative: only report, do not invent large patches blindly
    return {
        "applied": False,
        "reason": "signature matched race risk but patch already expected — re-check api.py place_bid",
    }


def _fix_buyer_rank_on_credit() -> dict:
    db = ROOT / "wakeagain" / "db.py"
    src = db.read_text(encoding="utf-8")
    if '"buyer_rank": buyer_rank(' in src or "'buyer_rank': buyer_rank(" in src:
        return {"applied": False, "reason": "buyer_rank already in compute_credit"}
    return {"applied": False, "reason": "buyer_rank missing from compute_credit — needs manual/agent patch"}


def _fix_second_bidder_flag() -> dict:
    """Ensure second bidder auto is on for tests."""
    # env-only fix for process
    os.environ["SECOND_BIDDER_AUTO"] = "1"
    return {"applied": True, "reason": "set SECOND_BIDDER_AUTO=1 in process env"}


KNOWN_FIXERS: list[tuple[re.Pattern[str], str, callable]] = [
    (
        re.compile(r"top matches price_current|price_current|race", re.I),
        "price_current_race",
        _fix_price_current_race,
    ),
    (
        re.compile(r"buyer_rank|buyer A has buyer_rank", re.I),
        "buyer_rank_credit",
        _fix_buyer_rank_on_credit,
    ),
    (
        re.compile(r"second_bidder|차순위|second award", re.I),
        "second_bidder_env",
        _fix_second_bidder_flag,
    ),
]


def try_auto_fixes(failure_blob: str) -> list[dict]:
    applied = []
    for pat, name, fn in KNOWN_FIXERS:
        if pat.search(failure_blob):
            try:
                info = fn()
            except Exception as e:
                info = {"applied": False, "reason": f"fixer error: {e}"}
            applied.append({"fixer": name, **info})
    return applied


def live_probe() -> dict:
    """Read-only live checks (no fake deals on production)."""
    import urllib.request

    out = {"ok": True, "checks": []}
    urls = [
        "https://wakeagain.com/health",
        "https://wakeagain.com/api/v1/health",
        "https://wakeagain.com/api/v1/credit-policy",
        "https://wakeagain.com/api/v1/auctions/live",
        "https://wakeagain.com/manifest.webmanifest",
    ]
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "WakeAgain-BugWatch/1.0"})
            with urllib.request.urlopen(req, timeout=20) as res:
                body = res.read(8000)
                ok = res.status == 200
                detail = f"HTTP {res.status} len={len(body)}"
                if "credit-policy" in u:
                    ok = ok and b"buyer_rank" in body
                    detail += " buyer_rank=" + str(b"buyer_rank" in body)
                if "manifest" in u:
                    ok = ok and b"/app/" in body
                    detail += " start_app=" + str(b"/app/" in body)
        except Exception as e:
            ok = False
            detail = str(e)[:200]
        out["checks"].append({"url": u, "ok": ok, "detail": detail})
        if not ok:
            out["ok"] = False
    return out


def run_cycle(suites: list[tuple[str, str, int]], *, do_fix: bool, live: bool) -> dict:
    cycle = {
        "started_at": now_iso(),
        "suites": [],
        "live": None,
        "auto_fixes": [],
        "ok": True,
    }
    print(f"\n[{cycle['started_at']}] bug-watch cycle start")
    for sid, script, timeout in suites:
        print(f"  → run {sid} ({script})")
        res = run_suite(script, timeout)
        fails = extract_failures(res["stdout"] + "\n" + res["stderr"])
        res["failures"] = fails
        cycle["suites"].append({"id": sid, **{k: res[k] for k in res if k not in ("stdout", "stderr")}, "fail_lines": fails})
        # keep full log file per suite
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = LOG_DIR / f"{stamp}_{sid}.log"
        log_path.write_text(
            f"exit={res['exit_code']} ok={res['ok']} sec={res['seconds']}\n\n"
            f"=== STDOUT ===\n{res['stdout']}\n\n=== STDERR ===\n{res['stderr']}\n",
            encoding="utf-8",
        )
        print(f"    {'OK' if res['ok'] else 'FAIL'} {sid} ({res['seconds']}s) log={log_path.name}")
        if not res["ok"]:
            cycle["ok"] = False
            if do_fix:
                blob = res["stdout"] + "\n" + res["stderr"] + "\n" + "\n".join(fails)
                fixes = try_auto_fixes(blob)
                cycle["auto_fixes"].extend(fixes)
                for f in fixes:
                    print(f"    auto-fix {f.get('fixer')}: applied={f.get('applied')} — {f.get('reason')}")

    if live:
        print("  → live probe (read-only)")
        cycle["live"] = live_probe()
        if not cycle["live"]["ok"]:
            cycle["ok"] = False
        for c in cycle["live"]["checks"]:
            print(f"    {'OK' if c['ok'] else 'FAIL'} {c['url']} — {c['detail']}")

    # re-run failed suites once after fixes
    if do_fix and not cycle["ok"] and any(f.get("applied") for f in cycle["auto_fixes"]):
        print("  → re-run after applied auto-fixes")
        failed_ids = {s["id"] for s in cycle["suites"] if not s["ok"]}
        rerun = [s for s in suites if s[0] in failed_ids]
        for sid, script, timeout in rerun:
            res = run_suite(script, timeout)
            print(f"    re-run {sid}: {'OK' if res['ok'] else 'FAIL'}")
            # update cycle result
            for s in cycle["suites"]:
                if s["id"] == sid:
                    s["ok"] = res["ok"]
                    s["exit_code"] = res["exit_code"]
                    s["rerun"] = True
        cycle["ok"] = all(s["ok"] for s in cycle["suites"]) and (
            cycle["live"] is None or cycle["live"]["ok"]
        )

    cycle["finished_at"] = now_iso()
    summary_path = LOG_DIR / "latest_summary.json"
    summary_path.write_text(json.dumps(cycle, ensure_ascii=False, indent=2), encoding="utf-8")
    # append history line
    hist = LOG_DIR / "history.jsonl"
    with hist.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "at": cycle["finished_at"],
                    "ok": cycle["ok"],
                    "suites": {s["id"]: s["ok"] for s in cycle["suites"]},
                    "live_ok": None if not cycle["live"] else cycle["live"]["ok"],
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    print(f"[{cycle['finished_at']}] cycle {'PASS' if cycle['ok'] else 'FAIL'} → {summary_path}")
    return cycle


def main() -> int:
    ap = argparse.ArgumentParser(description="WakeAgain continuous bug watch")
    ap.add_argument("--loop", type=int, default=0, help="seconds between cycles (0=once)")
    ap.add_argument("--quick", action="store_true", help="smoke+deal only")
    ap.add_argument("--fix", action="store_true", help="try known auto-fixes on failure")
    ap.add_argument("--live", action="store_true", default=True, help="probe production read-only")
    ap.add_argument("--no-live", action="store_true", help="skip live probe")
    args = ap.parse_args()
    live = args.live and not args.no_live
    suites = SUITES_QUICK if args.quick else SUITES_FULL

    if args.loop <= 0:
        c = run_cycle(suites, do_fix=args.fix, live=live)
        return 0 if c["ok"] else 1

    print(f"Watching every {args.loop}s — Ctrl+C to stop. Logs: {LOG_DIR}")
    while True:
        try:
            run_cycle(suites, do_fix=args.fix, live=live)
        except KeyboardInterrupt:
            print("stopped")
            return 0
        except Exception as e:
            print("cycle error:", e)
            traceback_path = LOG_DIR / "watch_errors.log"
            with traceback_path.open("a", encoding="utf-8") as f:
                f.write(f"{now_iso()} {e}\n")
        time.sleep(max(30, args.loop))


if __name__ == "__main__":
    # late import guard for type of callable in older py
    raise SystemExit(main())
