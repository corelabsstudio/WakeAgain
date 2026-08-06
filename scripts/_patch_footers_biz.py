# -*- coding: utf-8 -*-
"""Add short business-info line to compact footers across marketing pages."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"C:\Users\hysoo\projects\WakeAgain\public")

BIZ_LINE = (
    '    <p class="footer-copy muted fine footer-biz-short" style="margin:0.4rem 0">'
    "상호 코어랩스 · 대표 호현수 · 사업자등록번호 705-04-02867 · "
    '<a class="text-link" href="/legal/business.html">사업자 정보</a></p>\n'
)

# Pages with compact footers (not index — already has full block)
TARGETS = [
    "sell.html",
    "buy.html",
    "get-app.html",
    "review.html",
    "diagnose.html",
    "showcase.html",
    "showcase-new.html",
    "project.html",
    "legal/terms.html",
    "legal/privacy.html",
    "legal/delete-account.html",
    "legal/terms.en.html",
    "promo/event.html",
]

changed = []
for rel in TARGETS:
    p = ROOT / rel
    if not p.exists():
        print("skip", rel)
        continue
    t = p.read_text(encoding="utf-8")
    if "705-04-02867" in t and "footer-biz-short" in t:
        print("already", rel)
        continue
    if "705-04-02867" in t and "footer-biz" in t:
        print("has biz", rel)
        continue
    # Insert before footer-broker-notice or before © CoreLabs line in compact footer
    if "footer-biz-short" in t:
        print("skip-short", rel)
        continue
    orig = t
    if "footer-broker-notice" in t and "705-04-02867" not in t:
        t = t.replace(
            '<p class="footer-broker-notice">',
            BIZ_LINE + '    <p class="footer-broker-notice">',
            1,
        )
        # also data-i18n variants
        if t == orig:
            t = t.replace(
                '<p class="footer-broker-notice"',
                BIZ_LINE + '    <p class="footer-broker-notice"',
                1,
            )
    if t == orig and "© 2026 CoreLabs" in t:
        t = t.replace(
            "© 2026 CoreLabs",
            "상호 코어랩스 · 대표 호현수 · 사업자등록번호 705-04-02867<br />© 2026 CoreLabs",
            1,
        )
    # LEGAL links: add business page if LEGAL section
    if 'href="/legal/terms.html"' in t and 'href="/legal/business.html"' not in t:
        t = t.replace(
            '<a href="/legal/terms.html"',
            '<a href="/legal/business.html">사업자 정보</a>\n          <a href="/legal/terms.html"',
            1,
        )
    if t != orig:
        p.write_text(t, encoding="utf-8", newline="\n")
        changed.append(rel)
        print("patched", rel)
    else:
        print("nochange", rel)

print("changed", len(changed), changed)
