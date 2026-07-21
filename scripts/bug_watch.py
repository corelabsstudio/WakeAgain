# -*- coding: utf-8 -*-
"""
WakeAgain continuous bug-watch loop.

What it can do automatically:
  1) DISCOVER — run smoke / deal / auction suites on an interval
  2) LOG — write pass/fail + full output under data/test_watch/
  3) AUTO-FIX (limited) — apply *known* repair routines when failure
     signatures match (not general AI coding)
  4) ALERT — push to admin (ntfy / Telegram / Discord webhook) + write agent inbox file

What it cannot do alone:
  - Invent arbitrary product fixes for unknown bugs
  - Safely auto-deploy without review
  - Instantly "wake" a Grok agent mid-chat (agent sees the inbox when a session is opened)

Usage:
  python scripts/bug_watch.py              # once
  python scripts/bug_watch.py --loop 300   # every 5 min
  python scripts/bug_watch.py --quick      # smoke only
  python scripts/bug_watch.py --fix       # try known auto-fixes on fail, re-run
  python scripts/bug_watch.py --notify     # alert admin on FAIL
  python scripts/bug_watch.py --notify-test  # send a test push

Notify config (first match wins for ntfy topic):
  env NTFY_TOPIC / NTFY_SERVER / NTFY_TOKEN
  env TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
  env DISCORD_WEBHOOK_URL
  file .launch/ntfy_topic.txt  (or RoadLog's same path)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.header import Header
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "data" / "test_watch"
LOG_DIR.mkdir(parents=True, exist_ok=True)
AGENT_INBOX = LOG_DIR / "AGENT_ALERT.md"
LAST_NOTIFY = LOG_DIR / "last_notify.json"

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


# ── Admin / agent notifications ────────────────────────────────────────────


def _read_topic_file(path: Path) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # allow TOPIC=xxx
        if "=" in line and line.split("=", 1)[0].strip().upper() in (
            "NTFY_TOPIC",
            "TOPIC",
        ):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
        return line
    return ""


def load_notify_config() -> dict:
    topic = (os.environ.get("NTFY_TOPIC") or "").strip()
    if not topic:
        topic = _read_topic_file(ROOT / ".launch" / "ntfy_topic.txt")
    if not topic:
        topic = _read_topic_file(
            Path(r"C:\Users\hysoo\Projects\RoadLog\.launch\ntfy_topic.txt")
        )
    return {
        "ntfy_server": (os.environ.get("NTFY_SERVER") or "https://ntfy.sh").rstrip("/"),
        "ntfy_topic": topic,
        "ntfy_token": (os.environ.get("NTFY_TOKEN") or "").strip(),
        "telegram_bot": (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip(),
        "telegram_chat": (os.environ.get("TELEGRAM_CHAT_ID") or "").strip(),
        "discord_webhook": (os.environ.get("DISCORD_WEBHOOK_URL") or "").strip(),
    }


def notify_configured(cfg: dict | None = None) -> bool:
    c = cfg or load_notify_config()
    return bool(
        c["ntfy_topic"]
        or (c["telegram_bot"] and c["telegram_chat"])
        or c["discord_webhook"]
    )


def _send_ntfy(cfg: dict, title: str, message: str, *, priority: int = 5) -> tuple[bool, str]:
    topic = (cfg.get("ntfy_topic") or "").strip().lstrip("/")
    if not topic:
        return False, "no topic"
    url = f"{cfg['ntfy_server']}/{urllib.parse.quote(topic)}"
    try:
        title_hdr = Header(title[:80], "utf-8").encode()
    except Exception:
        title_hdr = "WakeAgain"
    body = f"{title}\n\n{message}"
    headers = {
        "Title": title_hdr,
        "Priority": str(max(1, min(5, priority))),
        "Tags": "warning,bug,wakeagain",
        "Content-Type": "text/plain; charset=utf-8",
    }
    if cfg.get("ntfy_token"):
        headers["Authorization"] = f"Bearer {cfg['ntfy_token']}"
    try:
        req = urllib.request.Request(url, data=body.encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as res:
            return True, f"status={res.status}"
    except urllib.error.HTTPError as e:
        return False, f"http {e.code}"
    except Exception as e:
        return False, str(e)[:200]


def _send_telegram(cfg: dict, title: str, message: str) -> tuple[bool, str]:
    tok = cfg.get("telegram_bot") or ""
    chat = cfg.get("telegram_chat") or ""
    if not tok or not chat:
        return False, "no telegram"
    text = f"*{title}*\n\n{message}"[:3500]
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": chat, "text": text, "parse_mode": "Markdown"}
    ).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as res:
            return True, f"status={res.status}"
    except Exception as e:
        return False, str(e)[:200]


def _send_discord(cfg: dict, title: str, message: str) -> tuple[bool, str]:
    wh = cfg.get("discord_webhook") or ""
    if not wh:
        return False, "no discord"
    payload = json.dumps(
        {"content": f"**{title}**\n```\n{message[:1800]}\n```"},
        ensure_ascii=False,
    ).encode("utf-8")
    try:
        req = urllib.request.Request(
            wh,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as res:
            return True, f"status={res.status}"
    except Exception as e:
        return False, str(e)[:200]


def write_agent_inbox(title: str, message: str, cycle: dict) -> Path:
    """
    File the agent can read when a session starts / user says 'bug watch 확인'.
    Not a push to the model mid-session — requires a human/agent turn.
    """
    failed = [s["id"] for s in cycle.get("suites") or [] if not s.get("ok")]
    live_bad = []
    if cycle.get("live") and not cycle["live"].get("ok"):
        live_bad = [
            c["url"] for c in cycle["live"].get("checks") or [] if not c.get("ok")
        ]
    body = (
        f"# WakeAgain AGENT ALERT\n\n"
        f"- **when:** {cycle.get('finished_at') or now_iso()}\n"
        f"- **title:** {title}\n"
        f"- **failed suites:** {', '.join(failed) or '(none)'}\n"
        f"- **live fails:** {', '.join(live_bad) or '(none)'}\n"
        f"- **summary:** `{LOG_DIR / 'latest_summary.json'}`\n"
        f"- **logs:** `{LOG_DIR}`\n\n"
        f"## Message\n\n{message}\n\n"
        f"## What to do\n\n"
        f"1. Read `data/test_watch/latest_summary.json`\n"
        f"2. Open the failing suite log under `data/test_watch/`\n"
        f"3. Fix code, re-run `python scripts/bug_watch.py --quick --fix`\n"
        f"4. Clear this alert when fixed (delete or overwrite this file)\n"
    )
    AGENT_INBOX.write_text(body, encoding="utf-8")
    return AGENT_INBOX


def failure_fingerprint(cycle: dict) -> str:
    parts = []
    for s in cycle.get("suites") or []:
        if not s.get("ok"):
            parts.append(s.get("id", "?") + ":" + "|".join(s.get("fail_lines") or [])[:200])
    if cycle.get("live") and not cycle["live"].get("ok"):
        parts.append(
            "live:"
            + ",".join(
                c["url"] for c in cycle["live"].get("checks") or [] if not c.get("ok")
            )
        )
    raw = "\n".join(parts) or "ok"
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:16]


def should_notify(fp: str, *, force: bool = False, cooldown_sec: int = 3600) -> bool:
    if force:
        return True
    try:
        prev = json.loads(LAST_NOTIFY.read_text(encoding="utf-8"))
    except Exception:
        return True
    if prev.get("fingerprint") != fp:
        return True
    try:
        last = datetime.fromisoformat(prev.get("at", "").replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - last.astimezone(timezone.utc)).total_seconds()
        return age >= cooldown_sec
    except Exception:
        return True


def send_alerts(cycle: dict, *, force: bool = False) -> dict:
    """Notify admin channels + agent inbox when cycle failed."""
    cfg = load_notify_config()
    failed = [s for s in cycle.get("suites") or [] if not s.get("ok")]
    live_ok = None if not cycle.get("live") else cycle["live"].get("ok")
    lines = []
    for s in failed:
        lines.append(f"- suite `{s.get('id')}` exit={s.get('exit_code')}")
        for fl in (s.get("fail_lines") or [])[:5]:
            lines.append(f"  {fl}")
    if live_ok is False:
        lines.append("- live probe failed:")
        for c in cycle["live"].get("checks") or []:
            if not c.get("ok"):
                lines.append(f"  {c.get('url')}: {c.get('detail')}")
    msg = "\n".join(lines) if lines else "Unknown failure"
    title = "WakeAgain bug-watch FAIL"
    fp = failure_fingerprint(cycle)
    out = {
        "ok": False,
        "skipped": False,
        "fingerprint": fp,
        "channels": {},
        "agent_inbox": str(AGENT_INBOX),
    }

    write_agent_inbox(title, msg, cycle)

    if not should_notify(fp, force=force):
        out["skipped"] = True
        out["detail"] = "same failure within cooldown — inbox updated, push skipped"
        return out

    if not notify_configured(cfg) and not force:
        out["detail"] = "no push channel configured (ntfy/telegram/discord) — inbox only"
        # still record notify attempt time lightly
        return out

    any_ok = False
    if cfg["ntfy_topic"]:
        ok, detail = _send_ntfy(cfg, title, msg, priority=5)
        out["channels"]["ntfy"] = {"ok": ok, "detail": detail}
        any_ok = any_ok or ok
    if cfg["telegram_bot"] and cfg["telegram_chat"]:
        ok, detail = _send_telegram(cfg, title, msg)
        out["channels"]["telegram"] = {"ok": ok, "detail": detail}
        any_ok = any_ok or ok
    if cfg["discord_webhook"]:
        ok, detail = _send_discord(cfg, title, msg)
        out["channels"]["discord"] = {"ok": ok, "detail": detail}
        any_ok = any_ok or ok

    out["ok"] = any_ok or True  # inbox always written
    LAST_NOTIFY.write_text(
        json.dumps({"at": now_iso(), "fingerprint": fp, "channels": out["channels"]}, indent=2),
        encoding="utf-8",
    )
    return out


def run_cycle(
    suites: list[tuple[str, str, int]],
    *,
    do_fix: bool,
    live: bool,
    do_notify: bool = False,
) -> dict:
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

    if do_notify and not cycle["ok"]:
        alert = send_alerts(cycle)
        cycle["notify"] = alert
        if alert.get("skipped"):
            print(f"  notify skipped: {alert.get('detail')}")
        else:
            print(f"  notify channels: {alert.get('channels') or '(inbox only)'}")
            print(f"  agent inbox: {alert.get('agent_inbox')}")
        summary_path.write_text(json.dumps(cycle, ensure_ascii=False, indent=2), encoding="utf-8")
    elif cycle["ok"] and AGENT_INBOX.is_file():
        # clear stale alert on green run
        try:
            AGENT_INBOX.write_text(
                f"# WakeAgain AGENT ALERT\n\n_cleared {now_iso()} — last cycle PASS_\n",
                encoding="utf-8",
            )
        except Exception:
            pass

    return cycle


def main() -> int:
    ap = argparse.ArgumentParser(description="WakeAgain continuous bug watch")
    ap.add_argument("--loop", type=int, default=0, help="seconds between cycles (0=once)")
    ap.add_argument("--quick", action="store_true", help="smoke+deal only")
    ap.add_argument("--fix", action="store_true", help="try known auto-fixes on failure")
    ap.add_argument("--live", action="store_true", default=True, help="probe production read-only")
    ap.add_argument("--no-live", action="store_true", help="skip live probe")
    ap.add_argument("--notify", action="store_true", help="push admin alert on FAIL")
    ap.add_argument("--notify-test", action="store_true", help="send a test notification and exit")
    ap.add_argument("--notify-status", action="store_true", help="print notify channel status")
    args = ap.parse_args()
    live = args.live and not args.no_live
    suites = SUITES_QUICK if args.quick else SUITES_FULL

    if args.notify_status:
        cfg = load_notify_config()
        print("notify configured:", notify_configured(cfg))
        print("  ntfy topic set:", bool(cfg["ntfy_topic"]))
        print("  ntfy server:", cfg["ntfy_server"])
        print("  telegram:", bool(cfg["telegram_bot"] and cfg["telegram_chat"]))
        print("  discord webhook:", bool(cfg["discord_webhook"]))
        print("  agent inbox:", AGENT_INBOX)
        return 0

    if args.notify_test:
        cfg = load_notify_config()
        fake = {
            "finished_at": now_iso(),
            "ok": False,
            "suites": [
                {
                    "id": "notify-test",
                    "ok": False,
                    "exit_code": 1,
                    "fail_lines": ["[FAIL] test push from bug_watch --notify-test"],
                }
            ],
            "live": None,
        }
        # force notify
        write_agent_inbox("WakeAgain bug-watch TEST", "테스트 알림입니다.", fake)
        if not notify_configured(cfg):
            print("No push channel. Set NTFY_TOPIC or .launch/ntfy_topic.txt")
            print("Agent inbox written:", AGENT_INBOX)
            return 1
        out = {"channels": {}}
        if cfg["ntfy_topic"]:
            ok, d = _send_ntfy(cfg, "WakeAgain bug-watch TEST", "테스트 알림입니다. 폰에 오면 성공.", priority=4)
            out["channels"]["ntfy"] = {"ok": ok, "detail": d}
            print("ntfy:", ok, d)
        if cfg["telegram_bot"] and cfg["telegram_chat"]:
            ok, d = _send_telegram(cfg, "WakeAgain bug-watch TEST", "테스트 알림입니다.")
            out["channels"]["telegram"] = {"ok": ok, "detail": d}
            print("telegram:", ok, d)
        if cfg["discord_webhook"]:
            ok, d = _send_discord(cfg, "WakeAgain bug-watch TEST", "테스트 알림입니다.")
            out["channels"]["discord"] = {"ok": ok, "detail": d}
            print("discord:", ok, d)
        print("agent inbox:", AGENT_INBOX)
        return 0 if any(c.get("ok") for c in out["channels"].values()) else 1

    if args.loop <= 0:
        c = run_cycle(suites, do_fix=args.fix, live=live, do_notify=args.notify)
        return 0 if c["ok"] else 1

    print(f"Watching every {args.loop}s — Ctrl+C to stop. Logs: {LOG_DIR}")
    if args.notify:
        print("Notify on FAIL:", "configured" if notify_configured() else "inbox-only (set NTFY_TOPIC)")
    while True:
        try:
            run_cycle(suites, do_fix=args.fix, live=live, do_notify=args.notify)
        except KeyboardInterrupt:
            print("stopped")
            return 0
        except Exception as e:
            print("cycle error:", e)
            traceback_path = LOG_DIR / "watch_errors.log"
            with traceback_path.open("a", encoding="utf-8") as f:
                f.write(f"{now_iso()} {e}\n")
            if args.notify:
                try:
                    send_alerts(
                        {
                            "finished_at": now_iso(),
                            "ok": False,
                            "suites": [
                                {
                                    "id": "watch-loop",
                                    "ok": False,
                                    "exit_code": 1,
                                    "fail_lines": [str(e)],
                                }
                            ],
                            "live": None,
                        },
                        force=True,
                    )
                except Exception:
                    pass
        time.sleep(max(30, args.loop))


if __name__ == "__main__":
    raise SystemExit(main())
