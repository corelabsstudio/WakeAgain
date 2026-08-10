"""Server-rendered OpenGraph / Twitter card tags for listing detail pages.

Crawlers (X/Twitter, Reddit, Facebook, Slack unfurl bots) don't execute JS, so
og:title / og:description / og:image must be present in the first HTML byte
stream server.py sends for GET /project.html?id=N — the client-side JS still
does the rest of the rendering as before. English-only by design: WakeAgain's
launch is global-first (PLATFORM.md), and social cards are the first thing an
overseas viewer sees.
"""

from __future__ import annotations

import html
import os
import re

from wakeagain import db as database
from wakeagain import oauth as oauth_mod

FALLBACK_DESCRIPTION = "Revive this abandoned side project. Bid now to continue its journey."


def _usd(krw_amount: int) -> int:
    try:
        rate = float(os.environ.get("WA_FX_USD") or "1350")
    except ValueError:
        rate = 1350.0
    if rate <= 0:
        rate = 1350.0
    return max(1, round(int(krw_amount or 0) / rate))


def _english_title(project: dict) -> str:
    title_en = (project.get("title_en") or "").strip()
    if title_en:
        return title_en
    title = (project.get("title") or "").strip()
    latin = re.findall(r"[A-Za-z][A-Za-z0-9+.#\-]*", title)
    if latin:
        return " ".join(latin)
    return title or "Listing"


def listing_og_tags(project_id: int) -> dict[str, str] | None:
    with database.db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        return None
    project = database.project_to_dict(row, include_private=False)
    title_en = _english_title(project)
    price = project.get("sold_price") or project.get("price_current") or project.get(
        "price_start"
    )
    usd = _usd(int(price or 0))
    base = oauth_mod.public_base()
    images = project.get("demo_images") or []
    og_image = f"{base}{images[0]}" if images else f"{base}/assets/og-image.png"
    return {
        "title": f"{title_en} — Now on Auction for ${usd:,} on WakeAgain",
        "description": FALLBACK_DESCRIPTION,
        "image": og_image,
        "url": f"{base}/project.html?id={project_id}",
    }


_META_RE = re.compile(
    r'[ \t]*<meta\s+(?:property="og:[^"]*"|name="twitter:[^"]*")[^>]*>\n?',
    re.IGNORECASE,
)


def inject_og_tags(html_source: str, tags: dict[str, str]) -> str:
    """Strip any static og:/twitter: tags already in the file, then inject fresh ones."""

    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    meta_block = (
        '<meta property="og:type" content="website">\n'
        '  <meta property="og:site_name" content="WakeAgain">\n'
        f'  <meta property="og:title" content="{esc(tags["title"])}">\n'
        f'  <meta property="og:description" content="{esc(tags["description"])}">\n'
        f'  <meta property="og:image" content="{esc(tags["image"])}">\n'
        f'  <meta property="og:url" content="{esc(tags["url"])}">\n'
        '  <meta name="twitter:card" content="summary_large_image">\n'
        f'  <meta name="twitter:title" content="{esc(tags["title"])}">\n'
        f'  <meta name="twitter:description" content="{esc(tags["description"])}">\n'
        f'  <meta name="twitter:image" content="{esc(tags["image"])}">\n'
    )
    cleaned = _META_RE.sub("", html_source)
    if "</head>" not in cleaned:
        return cleaned
    return cleaned.replace("</head>", f"  {meta_block}</head>", 1)
