"""Demo screenshot uploads — stored under DATA_DIR/uploads (Railway volume).

Capacity notes (defaults):
  · max 5 images / listing
  · max ~1.5 MB / image after client resize
  · formats: JPEG / PNG / WebP only
  · ~5 × 300KB ≈ 1.5 MB per listing (fine on 500MB volume)
"""
from __future__ import annotations

import re
import secrets
import uuid
from pathlib import Path
from typing import Any

from wakeagain.db import DATA

UPLOAD_ROOT = DATA / "uploads"
DEMOS_ROOT = UPLOAD_ROOT / "demos"

# Hard server limits (client should resize smaller first)
MAX_IMAGE_BYTES = int(1.5 * 1024 * 1024)  # 1.5 MB
MIN_IMAGES_PER_LISTING = 2
MAX_IMAGES_PER_LISTING = 5
MAX_UPLOADS_PER_REQUEST = 5

# Magic bytes → extension
_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"RIFF", "webp"),  # refined below
]


def ensure_dirs() -> None:
    DEMOS_ROOT.mkdir(parents=True, exist_ok=True)


def _detect_ext(data: bytes) -> str | None:
    if len(data) < 12:
        return None
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def public_url_for(rel_path: str) -> str:
    """rel_path like demos/12/abc.jpg → /media/demos/12/abc.jpg"""
    rel = (rel_path or "").replace("\\", "/").lstrip("/")
    return "/media/" + rel


def is_owned_demo_url(url: str, user_id: int) -> bool:
    """Only accept media URLs under this user's demo folder."""
    u = (url or "").strip()
    if not u.startswith("/media/demos/"):
        return False
    # /media/demos/{uid}/filename
    parts = u.split("/")
    # ['', 'media', 'demos', '{uid}', 'file']
    if len(parts) < 5:
        return False
    try:
        owner = int(parts[3])
    except ValueError:
        return False
    if owner != int(user_id):
        return False
    name = parts[4]
    if not re.fullmatch(r"[a-zA-Z0-9._-]+", name):
        return False
    if ".." in u:
        return False
    return True


def save_demo_image(*, user_id: int, raw: bytes, filename_hint: str = "") -> dict[str, Any]:
    """Validate and write one image. Returns public url + meta."""
    ensure_dirs()
    if not raw:
        raise ValueError("empty file")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError(
            f"이미지가 너무 큽니다 (최대 {MAX_IMAGE_BYTES // 1024}KB). "
            "화면을 잘라 내거나 해상도를 줄여 주세요."
        )
    ext = _detect_ext(raw)
    if not ext:
        raise ValueError("JPEG · PNG · WebP 이미지만 올릴 수 있습니다.")

    uid = int(user_id)
    folder = DEMOS_ROOT / str(uid)
    folder.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex[:16]
    # optional hint suffix for debugging only — not used in name
    _ = filename_hint
    name = f"{token}.{ext}"
    path = folder / name
    # avoid overwrite
    if path.exists():
        name = f"{token}_{secrets.token_hex(3)}.{ext}"
        path = folder / name
    path.write_bytes(raw)

    rel = f"demos/{uid}/{name}"
    return {
        "url": public_url_for(rel),
        "path": rel,
        "bytes": len(raw),
        "ext": ext,
    }


def normalize_demo_images(urls: list[str] | None, *, user_id: int) -> list[str]:
    out: list[str] = []
    for u in urls or []:
        s = str(u or "").strip()
        if not s:
            continue
        if not is_owned_demo_url(s, user_id):
            raise ValueError("잘못된 이미지 주소입니다. 다시 업로드해 주세요.")
        if s not in out:
            out.append(s)
        if len(out) >= MAX_IMAGES_PER_LISTING:
            break
    return out
