"""Audit public UI for missing i18n keys and basic live health."""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
BASE = "https://wakeagain.com"


def extract_defined_keys(msg_text: str) -> Counter:
    return Counter(re.findall(r'"([a-z][a-z0-9]*(?:\.[a-z0-9_]+)+)"\s*:', msg_text))


def extract_used_keys() -> dict[str, set[str]]:
    """Map key -> set of files using it via data-i18n*."""
    used: dict[str, set[str]] = {}
    pat = re.compile(
        r'data-i18n(?:-html|-placeholder|-title|-aria)?\s*=\s*["\']([^"\']+)["\']'
    )
    for p in PUBLIC.rglob("*"):
        if p.suffix.lower() not in {".html", ".js"}:
            continue
        if "i18n-messages" in p.name:
            continue
        if any(x in p.parts for x in ("node_modules", ".venv")):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = str(p.relative_to(PUBLIC)).replace("\\", "/")
        for m in pat.finditer(text):
            k = m.group(1).strip()
            if not k or k.startswith("{"):
                continue
            used.setdefault(k, set()).add(rel)
        # app.js style: t("app.foo", "fallback") when first arg is a key-like string
        if p.suffix == ".js":
            for m in re.finditer(
                r'(?:WakeAgainI18n\.)?t\(\s*["\']([a-z][a-z0-9_.]+)["\']\s*,',
                text,
            ):
                k = m.group(1)
                if "." in k:
                    used.setdefault(k, set()).add(rel)
    return used


def live_get(path: str) -> tuple[int, str]:
    url = BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": "WakeAgain-audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, body
    except Exception as e:
        return 0, str(e)


def main() -> int:
    msg_path = PUBLIC / "js" / "i18n-messages.js"
    msg = msg_path.read_text(encoding="utf-8")
    counts = extract_defined_keys(msg)
    defined = set(counts)
    used_map = extract_used_keys()
    used = set(used_map)

    missing = sorted(k for k in used if k not in defined)
    # typically each key appears twice (ko + en)
    once = sorted(k for k in used if counts.get(k, 0) == 1)

    print("=== LOCAL i18n audit ===")
    print(f"used data-i18n keys: {len(used)}")
    print(f"defined dotted keys: {len(defined)}")
    print(f"MISSING: {len(missing)}")
    for k in missing:
        files = ", ".join(sorted(used_map[k])[:4])
        print(f"  MISSING  {k}  <- {files}")
    print(f"ONCE only (ko/en gap?): {len(once)}")
    for k in once:
        print(f"  ONCE     {k}  count={counts[k]}")

    # raw-looking keys that might still show if lang wrong
    suspicious_html = []
    for p in PUBLIC.rglob("*.html"):
        text = p.read_text(encoding="utf-8", errors="replace")
        # hardcoded English UI crumbs common on KR-first product
        for pat, label in [
            (r">\s*LIVE\s*<", "LIVE badge"),
            (r">\s*SOLD\s*<", "SOLD badge"),
            (r">\s*AUCTION\s*<", "AUCTION eyebrow"),
            (r">\s*NEXT OWNER\s*<", "NEXT OWNER"),
            (r"data-i18n=\"[A-Z]", "uppercase i18n key?"),
        ]:
            if re.search(pat, text):
                suspicious_html.append(
                    f"  {p.relative_to(PUBLIC).as_posix()}: {label}"
                )
    print("=== Possible EN-only hardcodes / oddities ===")
    for line in suspicious_html[:40]:
        print(line)

    print("\n=== LIVE HTTP smoke ===")
    pages = [
        "/",
        "/app/",
        "/project.html?id=1",
        "/sell.html",
        "/buy.html",
        "/admin/",
        "/legal/terms.html",
        "/legal/privacy.html",
        "/guide/credit.html",
        "/js/i18n-messages.js",
        "/health",
    ]
    for path in pages:
        code, body = live_get(path)
        print(f"  {code:3} {len(body):7} {path}")

    # live project page missing keys
    code, html = live_get("/project.html?id=1")
    live_keys = set(
        re.findall(
            r'data-i18n(?:-html|-placeholder)?\s*=\s*["\']([^"\']+)["\']', html
        )
    )
    code2, live_msg = live_get("/js/i18n-messages.js")
    live_defined = set(extract_defined_keys(live_msg))
    live_miss = sorted(k for k in live_keys if k not in live_defined)
    print("\n=== LIVE project.html vs live i18n-messages.js ===")
    print(f"  project keys: {len(live_keys)}  messages keys: {len(live_defined)}")
    print(f"  live missing: {live_miss}")
    print(f"  start_price_short in live msg: {'start_price_short' in live_msg}")

    # API quick checks
    print("\n=== LIVE API ===")
    for path in ["/api/v1/config", "/api/v1/stats", "/api/v1/projects?limit=5"]:
        code, body = live_get(path)
        snip = body.replace("\n", " ")[:80]
        print(f"  {code:3} {path}  {snip}")

    return 1 if missing or live_miss else 0


if __name__ == "__main__":
    raise SystemExit(main())
