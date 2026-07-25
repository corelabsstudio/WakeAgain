# -*- coding: utf-8 -*-
"""Inject CoreLabs mark into compact site footers."""
from __future__ import annotations

import re
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public"

SNIPPET = """    <div class="corelabs-brand-row">
      <img class="corelabs-mark" src="/assets/corelabs-logo-mark.png" alt="CoreLabs" width="22" height="22" loading="lazy" decoding="async" />
      <span class="muted fine">운영 · 코어랩스(CoreLabs)</span>
    </div>
"""


def main() -> None:
    changed: list[str] = []
    for p in PUBLIC.rglob("*.html"):
        text = p.read_text(encoding="utf-8")
        if "compact-footer" not in text:
            continue
        if "corelabs-brand-row" in text:
            print("skip", p.relative_to(PUBLIC))
            continue
        new, n = re.subn(
            r'(<footer class="site-footer compact-footer">\s*)',
            r"\1" + SNIPPET,
            text,
            count=1,
        )
        if n:
            p.write_text(new, encoding="utf-8")
            changed.append(str(p.relative_to(PUBLIC)))
        else:
            print("no match", p.relative_to(PUBLIC))

    # App footer (different structure)
    app = PUBLIC / "app" / "index.html"
    if app.is_file():
        t = app.read_text(encoding="utf-8")
        if "corelabs-logo-mark.png" not in t and "© 2026 CoreLabs" in t:
            t = t.replace(
                "<p>© 2026 CoreLabs · WakeAgain · Powered by CoreLabs</p>",
                """<div class="corelabs-brand-row" style="justify-content:center;margin:0.75rem 0 0.35rem;display:flex;align-items:center;gap:0.5rem">
      <img class="corelabs-mark" src="/assets/corelabs-logo-mark.png" alt="CoreLabs" width="22" height="22" loading="lazy" decoding="async" style="width:22px;height:22px;object-fit:contain" />
      <p style="margin:0">© 2026 CoreLabs · WakeAgain · Powered by CoreLabs</p>
    </div>""",
            )
            app.write_text(t, encoding="utf-8")
            changed.append("app/index.html")

    print("CHANGED", len(changed))
    for c in changed:
        print(" ", c)


if __name__ == "__main__":
    main()
