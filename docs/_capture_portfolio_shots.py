# -*- coding: utf-8 -*-
"""Capture live portfolio screenshots: WakeAgain / RoadLog / niagaekaw (+ Trace fallback)."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "_portfolio_previews" / "shots"
RL_FALLBACKS = [
    Path(r"C:\Users\hysoo\projects\RoadLog\data\landing_shot.png"),
    Path(r"C:\Users\hysoo\projects\RoadLog\data\landing_prod.png"),
]


def ensure_dir() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)


def _shot(page, name: str, full_page: bool = False) -> None:
    dest = SHOTS / name
    page.screenshot(path=str(dest), full_page=full_page)
    print("ok", name, dest.stat().st_size)


def capture_all_live() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Desktop marketing shots
        page = browser.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
        try:
            # ── WakeAgain home (yard landing) ──
            page.goto("https://wakeagain.com/", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(2500)
            _shot(page, "wa_home.png")

            # ── WakeAgain app list ──
            page.goto("https://wakeagain.com/app/", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(2200)
            _shot(page, "wa_app.png")

            # ── RoadLog home ──
            page.goto("https://roadlog.co.kr/", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(2200)
            _shot(page, "rl_home.png")
            page.evaluate(
                """() => {
                const re = /요금|가격|Pro|Free|pricing|플랜/i;
                const el = [...document.querySelectorAll('a,button,h2,h3,section,div')]
                  .find(e => re.test((e.textContent || '').slice(0, 80)));
                if (el) el.scrollIntoView({block: 'center'});
            }"""
            )
            page.wait_for_timeout(900)
            _shot(page, "rl_pricing.png")

            # ── niagaekaw (Phase1 surface) ──
            page.goto("https://niagaekaw.site/", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(2000)
            _shot(page, "nk_hero.png")
            page.evaluate("window.scrollTo(0, Math.min(900, document.body.scrollHeight * 0.35))")
            page.wait_for_timeout(800)
            _shot(page, "nk_scroll.png")
        except Exception as e:
            print("desktop live fail:", e)
        finally:
            page.close()

        # Mobile niagaekaw
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        try:
            mobile.goto("https://niagaekaw.site/", wait_until="domcontentloaded", timeout=90000)
            mobile.wait_for_timeout(2000)
            _shot(mobile, "nk_mobile.png")
        except Exception as e:
            print("mobile nk fail:", e)
        finally:
            mobile.close()
            browser.close()


def find_trace_shot() -> Path | None:
    candidates = [
        Path(r"C:\Users\hysoo\Desktop\Trace"),
        Path(r"C:\Users\hysoo\projects\Trace"),
        Path(r"C:\Trace"),
        Path(r"C:\Users\hysoo\Desktop"),
    ]
    names = ("trace_ui.png", "trace.png", "Trace_UI.png", "screenshot.png")
    for base in candidates:
        if not base.exists():
            continue
        for n in names:
            p = base / n if base.is_dir() else None
            if p and p.is_file() and p.stat().st_size > 5000:
                return p
        if base.is_dir():
            for p in base.rglob("*.png"):
                if "trace" in p.name.lower() and p.stat().st_size > 20000:
                    return p
    return None


def ensure_trace() -> None:
    dest = SHOTS / "trace_ui.png"
    found = find_trace_shot()
    if found:
        shutil.copy2(found, dest)
        print("copied trace from", found)
        return
    if dest.is_file() and dest.stat().st_size > 10000:
        print("trace_ui keep existing", dest.stat().st_size)
        return
    try:
        from PIL import Image, ImageDraw, ImageFont

        im = Image.new("RGB", (1280, 800), (15, 23, 42))
        dr = ImageDraw.Draw(im)
        dr.rectangle((40, 40, 1240, 760), outline=(45, 212, 191), width=3)
        try:
            font = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 48)
            font2 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 28)
        except Exception:
            font = ImageFont.load_default()
            font2 = font
        dr.text((80, 120), "Trace", fill=(248, 250, 252), font=font)
        dr.text(
            (80, 200),
            "인터뷰 기반 AI 경험글 작성 도구 · CoreLabs",
            fill=(45, 212, 191),
            font=font2,
        )
        dr.text(
            (80, 280),
            "Windows 설치형 Trace.exe · BYOK · Phase 2",
            fill=(148, 163, 184),
            font=font2,
        )
        im.save(dest)
        print("wrote placeholder trace_ui")
    except Exception as e:
        print("trace placeholder fail", e)


def copy_roadlog_fallback_if_missing() -> None:
    """Only if live capture left empty files."""
    for name, src in (("rl_home.png", RL_FALLBACKS[0]), ("rl_pricing.png", RL_FALLBACKS[1] if len(RL_FALLBACKS) > 1 else RL_FALLBACKS[0])):
        dest = SHOTS / name
        if (not dest.is_file() or dest.stat().st_size < 5000) and src.is_file():
            shutil.copy2(src, dest)
            print("fallback", name)


def main() -> None:
    ensure_dir()
    try:
        capture_all_live()
    except Exception as e:
        print("capture skip", e)
    copy_roadlog_fallback_if_missing()
    ensure_trace()
    for p in sorted(SHOTS.glob("*")):
        print(p.name, p.stat().st_size)


if __name__ == "__main__":
    main()
