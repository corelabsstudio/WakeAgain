"""Listing keywords: normalize, heuristic suggest, optional xAI (SpaceXAI) suggest."""
from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

MAX_KEYWORDS = 5
MIN_KEYWORDS = 1
MAX_KEYWORD_LEN = 24
MIN_KEYWORD_LEN = 1

# Noise / stop tokens (KO + EN) — not useful as marketplace tags alone
_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "for",
        "in",
        "on",
        "with",
        "is",
        "are",
        "was",
        "be",
        "this",
        "that",
        "it",
        "my",
        "our",
        "your",
        "from",
        "by",
        "as",
        "at",
        "app",
        "apps",
        "tool",
        "tools",
        "project",
        "service",
        "product",
        "system",
        "platform",
        "based",
        "using",
        "made",
        "build",
        "built",
        "simple",
        "basic",
        "new",
        "old",
        "free",
        "demo",
        "test",
        "v1",
        "v2",
        "등",
        "및",
        "또는",
        "위한",
        "있는",
        "없는",
        "하는",
        "된",
        "할",
        "수",
        "것",
        "그",
        "이",
        "저",
        "더",
        "좀",
        "매우",
        "정말",
        "프로젝트",
        "제품",
        "서비스",
        "시스템",
        "플랫폼",
        "도구",
        "앱",
        "사이트",
        "웹",
        "모바일",
        "코드",
        "매물",
        "판매",
        "양도",
    }
)

_PRODUCT_TYPE_TAGS = {
    "website": ["웹사이트", "랜딩"],
    "webapp": ["SaaS", "웹앱"],
    "mobile": ["모바일앱", "앱"],
    "desktop": ["데스크톱", "CLI"],
    "api": ["API", "백엔드"],
    "game": ["게임"],
    "other": [],
}

# Lightweight domain cues → extra tags
_CUE_TAGS: list[tuple[re.Pattern[str], list[str]]] = [
    (re.compile(r"saas|구독|대시보드", re.I), ["SaaS", "대시보드"]),
    (re.compile(r"ai|llm|gpt|머신|인공지능|whisper|ocr", re.I), ["AI", "자동화"]),
    (re.compile(r"카카오|kakao|알림톡", re.I), ["카카오", "알림"]),
    (re.compile(r"주문|배송|쇼핑몰|커머스|shop", re.I), ["커머스", "주문"]),
    (re.compile(r"영수증|가계부|지출|receipt", re.I), ["가계부", "영수증"]),
    (re.compile(r"회의|노트|요약|meeting|notes", re.I), ["회의", "요약"]),
    (re.compile(r"csv|엑셀|데이터", re.I), ["데이터", "CSV"]),
    (re.compile(r"블로그|seo|콘텐츠|글쓰기", re.I), ["블로그", "콘텐츠"]),
    (re.compile(r"flutter|react native|ios|android", re.I), ["모바일앱"]),
    (re.compile(r"next\.?js|react|vue|node", re.I), ["웹앱"]),
    (re.compile(r"python|cli|터미널", re.I), ["CLI", "도구"]),
    (re.compile(r"게임|game|unity", re.I), ["게임"]),
]


def normalize_keywords(raw: Any, *, max_count: int = MAX_KEYWORDS) -> list[str]:
    """Normalize user/AI keyword list to unique short tags (display casing preserved)."""
    if raw is None:
        return []
    if isinstance(raw, str):
        # comma / newline / hash separated
        parts = re.split(r"[,，\n#|/]+", raw)
    elif isinstance(raw, (list, tuple)):
        parts = []
        for item in raw:
            if item is None:
                continue
            parts.extend(re.split(r"[,，\n#|/]+", str(item)))
    else:
        parts = [str(raw)]

    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        k = re.sub(r"\s+", " ", str(p).strip())
        k = k.strip("#·•-–—_").strip()
        if not k:
            continue
        if len(k) > MAX_KEYWORD_LEN:
            k = k[:MAX_KEYWORD_LEN].rstrip()
        if len(k) < MIN_KEYWORD_LEN:
            continue
        # reject pure numbers / symbols
        if re.fullmatch(r"[\d\W_]+", k, flags=re.UNICODE):
            continue
        key = k.casefold()
        if key in seen:
            continue
        if key in _STOP:
            continue
        seen.add(key)
        out.append(k)
        if len(out) >= max_count:
            break
    return out


def keywords_from_row(row_keywords_json: str | None) -> list[str]:
    try:
        data = json.loads(row_keywords_json or "[]")
    except (json.JSONDecodeError, TypeError):
        data = []
    return normalize_keywords(data)


def _tokenize_en(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9+\-.]{1,20}", text)


def _tokenize_ko(text: str) -> list[str]:
    # Hangul runs 2–12 chars (compound words / product names)
    return re.findall(r"[가-힣]{2,12}", text)


def suggest_keywords_heuristic(
    *,
    title: str = "",
    one_liner: str = "",
    story: str = "",
    product_type: str = "",
    lang: str = "ko",
) -> list[str]:
    """Offline keyword suggestion — works without API keys."""
    blob = " ".join([title or "", one_liner or "", (story or "")[:400]])
    candidates: list[str] = []

    # Title first (high signal)
    for t in _tokenize_ko(title) + _tokenize_en(title):
        candidates.append(t)
    for t in _tokenize_ko(one_liner) + _tokenize_en(one_liner):
        candidates.append(t)

    for pat, tags in _CUE_TAGS:
        if pat.search(blob):
            candidates.extend(tags)

    ptype = (product_type or "").strip().lower()
    candidates.extend(_PRODUCT_TYPE_TAGS.get(ptype, []))

    # More tokens from story if still short
    if len(normalize_keywords(candidates)) < MAX_KEYWORDS:
        for t in _tokenize_ko(story)[:12] + _tokenize_en(story)[:8]:
            candidates.append(t)

    # Prefer title words by putting them first; normalize de-dupes
    return normalize_keywords(candidates, max_count=MAX_KEYWORDS)


def _xai_api_key() -> str:
    return (os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY") or "").strip()


def suggest_keywords_ai(
    *,
    title: str = "",
    one_liner: str = "",
    story: str = "",
    product_type: str = "",
    lang: str = "ko",
    timeout: float = 12.0,
) -> tuple[list[str], str]:
    """
    Prefer SpaceXAI (xAI) when XAI_API_KEY is set; else heuristic.
    Returns (keywords, source) where source is 'ai' | 'heuristic'.
    """
    key = _xai_api_key()
    if not key:
        return suggest_keywords_heuristic(
            title=title,
            one_liner=one_liner,
            story=story,
            product_type=product_type,
            lang=lang,
        ), "heuristic"

    lang_note = "Korean marketplace tags" if (lang or "ko").startswith("ko") else "English marketplace tags"
    prompt = (
        f"You extract up to {MAX_KEYWORDS} search keywords for a used digital product marketplace listing.\n"
        f"Return ONLY a JSON array of {MAX_KEYWORDS} short strings (1–3 words each), no markdown.\n"
        f"Prefer {lang_note}. No hashtags. No duplicates. Useful for buyers searching.\n\n"
        f"title: {(title or '')[:80]}\n"
        f"one_liner: {(one_liner or '')[:120]}\n"
        f"product_type: {(product_type or '')[:40]}\n"
        f"story: {(story or '')[:500]}\n"
    )
    try:
        with httpx.Client(timeout=timeout) as client:
            # OpenAI-compatible chat — widely supported on api.x.ai
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
                            "content": "You output only valid JSON arrays of short keyword strings.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200,
                },
            )
            if r.status_code >= 400:
                return suggest_keywords_heuristic(
                    title=title,
                    one_liner=one_liner,
                    story=story,
                    product_type=product_type,
                    lang=lang,
                ), "heuristic"
            data = r.json()
            text = (
                ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            ).strip()
            # strip ```json fences if any
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            parsed = json.loads(text)
            kws = normalize_keywords(parsed, max_count=MAX_KEYWORDS)
            if len(kws) < MIN_KEYWORDS:
                raise ValueError("empty ai keywords")
            # pad with heuristic if AI returned fewer than useful
            if len(kws) < MAX_KEYWORDS:
                extra = suggest_keywords_heuristic(
                    title=title,
                    one_liner=one_liner,
                    story=story,
                    product_type=product_type,
                    lang=lang,
                )
                kws = normalize_keywords(kws + extra, max_count=MAX_KEYWORDS)
            return kws, "ai"
    except Exception:
        return suggest_keywords_heuristic(
            title=title,
            one_liner=one_liner,
            story=story,
            product_type=product_type,
            lang=lang,
        ), "heuristic"
