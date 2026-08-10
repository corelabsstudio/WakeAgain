"""English copy for marketplace listings (title / one-liner).

When UI lang is English, prefer stored title_en / one_liner_en.
Missing EN fields are filled once (xAI when keyed, else heuristic) and cached on the row.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Iterable

import httpx

_HANGUL = re.compile(r"[\uac00-\ud7a3]")

# Common product-word gloss for offline fallback (not a full MT system)
_GLOSS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"예약", re.I), "booking"),
    (re.compile(r"고객|손님", re.I), "customer"),
    (re.compile(r"문자|알림", re.I), "alerts"),
    (re.compile(r"웹앱|웹\s*앱", re.I), "web app"),
    (re.compile(r"웹사이트", re.I), "website"),
    (re.compile(r"쇼핑몰|커머스", re.I), "shop"),
    (re.compile(r"관리자|어드민", re.I), "admin"),
    (re.compile(r"대시보드", re.I), "dashboard"),
    (re.compile(r"자동화", re.I), "automation"),
    (re.compile(r"재고", re.I), "inventory"),
    (re.compile(r"결제", re.I), "payments"),
    (re.compile(r"견적", re.I), "quotes"),
    (re.compile(r"일정|스케줄", re.I), "scheduling"),
    (re.compile(r"채팅", re.I), "chat"),
    (re.compile(r"블로그", re.I), "blog"),
    (re.compile(r"메모|노트", re.I), "notes"),
    (re.compile(r"영수증", re.I), "receipts"),
    (re.compile(r"가계부|경비", re.I), "expenses"),
    (re.compile(r"회의", re.I), "meeting"),
    (re.compile(r"요약", re.I), "summary"),
    (re.compile(r"도구|툴킷", re.I), "toolkit"),
    (re.compile(r"모바일|앱", re.I), "app"),
    (re.compile(r"SaaS|사스", re.I), "SaaS"),
    (re.compile(r"AI|인공지능", re.I), "AI"),
]


def has_hangul(text: str | None) -> bool:
    return bool(text and _HANGUL.search(text))


_HEURISTIC_MARKERS = (
    "paused project marketplace listing",
    "demo-ready side project for transfer",
    "Digital project listing",
)


def _is_weak_en(text: str | None) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    return any(m in t for m in _HEURISTIC_MARKERS)


def needs_en_title(title: str | None, title_en: str | None) -> bool:
    te = (title_en or "").strip()
    t = (title or "").strip()
    if not t:
        return False
    # Already Latin-only product name → can reuse as EN
    if not has_hangul(t):
        return False
    if te and not _is_weak_en(te):
        return False
    # Missing or weak heuristic → try (re)fill
    return True


def needs_en_one_liner(one: str | None, one_en: str | None) -> bool:
    o = (one or "").strip()
    if not o:
        return False
    oe = (one_en or "").strip()
    if not has_hangul(o) and oe:
        return False
    if oe and not _is_weak_en(oe) and not has_hangul(o):
        return False
    if has_hangul(o) and oe and not _is_weak_en(oe):
        return False
    return has_hangul(o) or _is_weak_en(oe)


def _xai_key() -> str:
    return (os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY") or "").strip()


def heuristic_title_en(title: str) -> str:
    """Best-effort EN title without network. Prefer readable product-ish English."""
    raw = (title or "").strip()
    if not raw:
        return ""
    if not has_hangul(raw):
        return raw[:80]
    hits: list[str] = []
    for pat, en in _GLOSS:
        if pat.search(raw) and en not in hits:
            # Avoid "web app" + "app" duplication
            if en == "app" and any(h in ("web app", "SaaS") for h in hits):
                continue
            hits.append(en)
    # Keep any Latin/number fragments from the original title
    latin = re.findall(r"[A-Za-z][A-Za-z0-9+.#-]{1,}", raw)
    for frag in latin:
        if frag not in hits:
            hits.insert(0, frag)
    if hits:
        # e.g. "ShopPulse booking alerts" or "booking customer web app"
        base = " ".join(hits[:5]).strip()
        if base:
            return base[:80]
    # Strip common Korean marketplace suffixes, keep digits/latin leftovers
    cleaned = re.sub(r"(매물|프로젝트|테스트|스모크|모의거래)\s*", " ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    digits = re.findall(r"\d+", raw)
    if cleaned and not has_hangul(cleaned):
        return cleaned[:80]
    if digits:
        return f"Project {digits[0]}"[:80]
    # Last resort: generic marketplace label
    return "Digital project listing"


def heuristic_one_liner_en(one_liner: str, title: str = "") -> str:
    raw = (one_liner or "").strip()
    if not raw:
        return ""
    if not has_hangul(raw):
        return raw[:160]
    hits: list[str] = []
    for pat, en in _GLOSS:
        if pat.search(raw) and en not in hits:
            hits.append(en)
    if hits:
        return (" · ".join(hits[:6]) + " — paused project marketplace listing")[:160]
    t = heuristic_title_en(title) if title else "Paused digital product"
    return f"{t} — demo-ready side project for transfer"[:160]


def _ai_translate_batch(
    items: list[dict[str, str]],
    *,
    timeout: float = 18.0,
) -> list[dict[str, str]]:
    """
    items: [{id, title, one_liner}]
    returns: [{id, title_en, one_liner_en}]
    """
    key = _xai_key()
    if not key or not items:
        return []
    payload_in = [
        {
            "id": str(it.get("id") or ""),
            "title": (it.get("title") or "")[:80],
            "one_liner": (it.get("one_liner") or "")[:160],
        }
        for it in items
    ]
    prompt = (
        "You translate Korean digital-product marketplace listing titles and one-liners into natural English.\n"
        "Return ONLY a JSON array. Each element: "
        '{"id":"...","title_en":"...","one_liner_en":"..."}\n'
        "Rules:\n"
        "- title_en: short product name, max ~60 chars, no quotes fluff\n"
        "- one_liner_en: one sentence benefit/what-it-is, max ~140 chars\n"
        "- Keep proper nouns / brand-like Latin tokens\n"
        "- Do not invent features not implied by the source\n"
        "- If source is already English, lightly polish\n\n"
        f"INPUT:\n{json.dumps(payload_in, ensure_ascii=False)}"
    )
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.environ.get("XAI_MODEL", "grok-4-1-fast-non-reasoning"),
                    "messages": [
                        {
                            "role": "system",
                            "content": "You output only valid JSON arrays for marketplace listing EN fields.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1200,
                },
            )
            if r.status_code >= 400:
                return []
            data = r.json()
            text = (
                ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            ).strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            parsed = json.loads(text)
            if not isinstance(parsed, list):
                return []
            out: list[dict[str, str]] = []
            for row in parsed:
                if not isinstance(row, dict):
                    continue
                tid = str(row.get("id") or "").strip()
                te = str(row.get("title_en") or "").strip()[:80]
                oe = str(row.get("one_liner_en") or "").strip()[:160]
                if tid and (te or oe):
                    out.append({"id": tid, "title_en": te, "one_liner_en": oe})
            return out
    except Exception:
        return []


def fill_en_fields(
    title: str,
    one_liner: str,
    *,
    title_en: str | None = None,
    one_liner_en: str | None = None,
    project_id: Any = None,
    use_ai: bool = True,
) -> dict[str, str]:
    """Return title_en / one_liner_en to store (never empty if source non-empty)."""
    te = (title_en or "").strip()
    oe = (one_liner_en or "").strip()
    need_t = needs_en_title(title, te)
    need_o = needs_en_one_liner(one_liner, oe)

    if not need_t and not need_o:
        if not te and (title or "").strip() and not has_hangul(title):
            te = (title or "").strip()[:80]
        if not oe and (one_liner or "").strip() and not has_hangul(one_liner):
            oe = (one_liner or "").strip()[:160]
        return {"title_en": te, "one_liner_en": oe}

    if use_ai and (need_t or need_o):
        batch = _ai_translate_batch(
            [
                {
                    "id": str(project_id or "0"),
                    "title": title or "",
                    "one_liner": one_liner or "",
                }
            ]
        )
        if batch:
            b0 = batch[0]
            if need_t and b0.get("title_en"):
                te = b0["title_en"]
            if need_o and b0.get("one_liner_en"):
                oe = b0["one_liner_en"]

    if need_t and (not te or _is_weak_en(te)):
        # Keep AI result if non-weak; else heuristic
        if not te or _is_weak_en(te):
            te = te if te and not _is_weak_en(te) else heuristic_title_en(title or "")
    if need_o and (not oe or _is_weak_en(oe)):
        if not oe or _is_weak_en(oe):
            oe = oe if oe and not _is_weak_en(oe) else heuristic_one_liner_en(
                one_liner or "", title or ""
            )
    if not te and (title or "").strip() and not has_hangul(title):
        te = (title or "").strip()[:80]
    if not oe and (one_liner or "").strip() and not has_hangul(one_liner):
        oe = (one_liner or "").strip()[:160]
    return {"title_en": te, "one_liner_en": oe}


# Free-text listing fields translated bidirectionally (title/one_liner keep
# their own dedicated path above with heuristic fallback; these lean on AI
# only — no good offline heuristic exists for paragraph-length text).
_LONG_FIELD_SPECS: list[tuple[str, str, str, int]] = [
    ("story", "story_en", "story_ko", 4000),
    ("audience", "audience_en", "audience_ko", 200),
    ("works_now", "works_now_en", "works_now_ko", 800),
    ("limits_note", "limits_note_en", "limits_note_ko", 800),
]


def _ai_translate_long_fields(
    payload: dict[str, Any],
    *,
    to_lang: str,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """
    payload: {field_name: text_or_list, ...} — only fields that need translating.
    to_lang: "en" or "ko".
    returns: {field_name: translated_text_or_list, ...}
    """
    key = _xai_key()
    if not key or not payload:
        return {}
    target = "natural English" if to_lang == "en" else "natural Korean"
    prompt = (
        f"Translate these digital-product marketplace listing fields into {target}.\n"
        "Return ONLY a JSON object with the same keys as the input.\n"
        "Rules:\n"
        "- Preserve meaning and tone; do not add or invent facts/features\n"
        "- Keep product/brand names and code-like tokens (file paths, .exe, API names) as-is\n"
        "- 'features' is a JSON array of short bullet strings — translate each item, same array length and order\n"
        "- Other fields are plain paragraphs/sentences — translate naturally, keep line breaks\n\n"
        f"INPUT:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.environ.get("XAI_MODEL", "grok-4-1-fast-non-reasoning"),
                    "messages": [
                        {
                            "role": "system",
                            "content": "You output only a valid JSON object for marketplace listing field translations.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2200,
                },
            )
            if r.status_code >= 400:
                return {}
            data = r.json()
            text = (
                ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            ).strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                return {}
            return parsed
    except Exception:
        return {}


def fill_listing_i18n(
    listing: dict[str, Any],
    *,
    project_id: Any = None,
    use_ai: bool = True,
) -> dict[str, Any]:
    """
    Given base-language listing fields (title/one_liner/story/audience/
    works_now/limits_note/features), return a dict of the *_en / *_ko
    columns to store — translating whichever direction the source text
    isn't already in. Call once at listing create/update time.

    listing keys read: title, one_liner, story, audience, works_now,
    limits_note, features (list[str])
    """
    out: dict[str, Any] = {}

    title = listing.get("title") or ""
    one_liner = listing.get("one_liner") or ""
    en_base = fill_en_fields(
        title, one_liner, project_id=project_id, use_ai=use_ai
    )
    out["title_en"] = en_base.get("title_en") or ""
    out["one_liner_en"] = en_base.get("one_liner_en") or ""
    # Reverse (KO) for Latin-authored title/one_liner — heuristic-free, AI only
    need_title_ko = bool(title) and not has_hangul(title)
    need_one_ko = bool(one_liner) and not has_hangul(one_liner)

    features = listing.get("features") or []
    if not isinstance(features, list):
        features = []
    features = [str(f) for f in features if f]

    long_fields = {
        "story": listing.get("story") or "",
        "audience": listing.get("audience") or "",
        "works_now": listing.get("works_now") or "",
        "limits_note": listing.get("limits_note") or "",
    }

    need_en: dict[str, Any] = {}
    need_ko: dict[str, Any] = {}
    if need_title_ko:
        need_ko["title"] = title
    if need_one_ko:
        need_ko["one_liner"] = one_liner
    for field, val in long_fields.items():
        if not val:
            continue
        if has_hangul(val):
            need_en[field] = val
        else:
            need_ko[field] = val
    if features:
        joined = " ".join(features)
        if has_hangul(joined):
            need_en["features"] = features
        elif joined.strip():
            need_ko["features"] = features

    max_len = {f: length for f, _e, _k, length in _LONG_FIELD_SPECS}

    if use_ai and need_en:
        got = _ai_translate_long_fields(need_en, to_lang="en")
        for field in long_fields:
            if field in need_en and got.get(field):
                out[f"{field}_en"] = str(got[field]).strip()[: max_len.get(field, 2000)]
        if "features" in need_en and isinstance(got.get("features"), list):
            out["features_json_en"] = json.dumps(
                [str(x).strip() for x in got["features"] if x], ensure_ascii=False
            )

    if use_ai and need_ko:
        got = _ai_translate_long_fields(need_ko, to_lang="ko")
        if "title" in need_ko and got.get("title"):
            out["title_ko"] = str(got["title"]).strip()[:80]
        if "one_liner" in need_ko and got.get("one_liner"):
            out["one_liner_ko"] = str(got["one_liner"]).strip()[:160]
        for field in long_fields:
            if field in need_ko and got.get(field):
                out[f"{field}_ko"] = str(got[field]).strip()[: max_len.get(field, 2000)]
        if "features" in need_ko and isinstance(got.get("features"), list):
            out["features_json_ko"] = json.dumps(
                [str(x).strip() for x in got["features"] if x], ensure_ascii=False
            )

    return out


def ensure_rows_en(conn: Any, rows: Iterable[Any], *, use_ai: bool = True) -> int:
    """
    For project sqlite rows missing EN fields, fill + UPDATE.
    Returns number of rows updated.
    """
    row_list = list(rows)
    if not row_list:
        return 0

    # Detect column presence
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()}
    except Exception:
        cols = set()
    if "title_en" not in cols or "one_liner_en" not in cols:
        return 0

    need: list[dict[str, Any]] = []
    for row in row_list:
        try:
            keys = row.keys()
        except Exception:
            continue
        if "id" not in keys:
            continue
        title = row["title"] if "title" in keys else ""
        one = row["one_liner"] if "one_liner" in keys else ""
        te = row["title_en"] if "title_en" in keys else None
        oe = row["one_liner_en"] if "one_liner_en" in keys else None
        if needs_en_title(title, te) or needs_en_one_liner(one, oe) or (
            not (te or "").strip() and (title or "").strip() and not has_hangul(title)
        ) or (
            not (oe or "").strip() and (one or "").strip() and not has_hangul(one)
        ):
            need.append(
                {
                    "id": int(row["id"]),
                    "title": title or "",
                    "one_liner": one or "",
                    "title_en": (te or "").strip(),
                    "one_liner_en": (oe or "").strip(),
                }
            )

    if not need:
        return 0

    # Batch AI for Korean ones
    ai_map: dict[str, dict[str, str]] = {}
    if use_ai:
        ai_items = [
            x
            for x in need
            if has_hangul(x["title"]) or has_hangul(x["one_liner"])
        ]
        # Cap per request to keep latency reasonable
        for i in range(0, len(ai_items), 12):
            chunk = ai_items[i : i + 12]
            for b in _ai_translate_batch(chunk):
                ai_map[str(b["id"])] = b

    updated = 0
    for item in need:
        pid = item["id"]
        te = item["title_en"]
        oe = item["one_liner_en"]
        ai = ai_map.get(str(pid)) or {}
        ai_te = (ai.get("title_en") or "").strip()
        ai_oe = (ai.get("one_liner_en") or "").strip()
        if ai_te and (not te or _is_weak_en(te)):
            te = ai_te
        if ai_oe and (not oe or _is_weak_en(oe)):
            oe = ai_oe
        if not te or _is_weak_en(te):
            te = te if te and not _is_weak_en(te) else heuristic_title_en(item["title"])
        if not oe or _is_weak_en(oe):
            oe = (
                oe
                if oe and not _is_weak_en(oe)
                else heuristic_one_liner_en(item["one_liner"], item["title"])
            )
        if not te and item["title"] and not has_hangul(item["title"]):
            te = item["title"][:80]
        if not oe and item["one_liner"] and not has_hangul(item["one_liner"]):
            oe = item["one_liner"][:160]
        if not te and not oe:
            continue
        conn.execute(
            "UPDATE projects SET title_en = ?, one_liner_en = ? WHERE id = ?",
            (te or None, oe or None, pid),
        )
        updated += 1
    return updated


_I18N_LONG_COLUMNS = {
    "story_en", "story_ko",
    "audience_en", "audience_ko",
    "works_now_en", "works_now_ko",
    "limits_note_en", "limits_note_ko",
    "features_json_en", "features_json_ko",
}


def _row_needs_i18n(row: Any, keys: Any) -> bool:
    def missing(base_col: str, en_col: str, ko_col: str) -> bool:
        base = (row[base_col] if base_col in keys else "") or ""
        if not base.strip():
            return False
        en_v = (row[en_col] if en_col in keys else "") or ""
        ko_v = (row[ko_col] if ko_col in keys else "") or ""
        if has_hangul(base):
            return not en_v.strip()
        return not ko_v.strip()

    if missing("story", "story_en", "story_ko"):
        return True
    if missing("audience", "audience_en", "audience_ko"):
        return True
    if missing("works_now", "works_now_en", "works_now_ko"):
        return True
    if missing("limits_note", "limits_note_en", "limits_note_ko"):
        return True
    feats_raw = (row["features_json"] if "features_json" in keys else "") or ""
    if feats_raw.strip() and feats_raw.strip() != "[]":
        joined = feats_raw
        en_v = (row["features_json_en"] if "features_json_en" in keys else "") or ""
        ko_v = (row["features_json_ko"] if "features_json_ko" in keys else "") or ""
        if has_hangul(joined):
            if not en_v.strip():
                return True
        elif not ko_v.strip():
            return True
    return False


def ensure_rows_i18n(conn: Any, rows: Iterable[Any], *, use_ai: bool = True) -> int:
    """
    Backfill story / features / audience / works_now / limits_note EN+KO
    translations for rows missing them (lazy, on-read — mirrors ensure_rows_en).
    """
    row_list = list(rows)
    if not row_list:
        return 0
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()}
    except Exception:
        cols = set()
    if not _I18N_LONG_COLUMNS.issubset(cols):
        return 0

    updated = 0
    for row in row_list:
        try:
            keys = row.keys()
        except Exception:
            continue
        if "id" not in keys or not _row_needs_i18n(row, keys):
            continue
        try:
            features = json.loads(row["features_json"] or "[]") if "features_json" in keys else []
            if not isinstance(features, list):
                features = []
        except Exception:
            features = []
        fields = {
            "title": "",
            "one_liner": "",
            "story": (row["story"] if "story" in keys else "") or "",
            "audience": (row["audience"] if "audience" in keys else "") or "",
            "works_now": (row["works_now"] if "works_now" in keys else "") or "",
            "limits_note": (row["limits_note"] if "limits_note" in keys else "") or "",
            "features": features,
        }
        out = fill_listing_i18n(fields, project_id=row["id"], use_ai=use_ai)
        set_cols = []
        set_vals: list[Any] = []
        for col in (
            "story_en", "story_ko", "audience_en", "audience_ko",
            "works_now_en", "works_now_ko", "limits_note_en", "limits_note_ko",
            "features_json_en", "features_json_ko",
        ):
            if out.get(col):
                set_cols.append(col)
                set_vals.append(out[col])
        if not set_cols:
            continue
        conn.execute(
            f"UPDATE projects SET {', '.join(c + ' = ?' for c in set_cols)} WHERE id = ?",
            (*set_vals, row["id"]),
        )
        updated += 1
    return updated
