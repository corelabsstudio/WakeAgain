# -*- coding: utf-8 -*-
"""Capture Play-style mobile shots + Trace desktop UI for portfolio."""
from __future__ import annotations
import shutil
import subprocess
import time
from pathlib import Path

SHOTS = Path(r"C:\Users\hysoo\projects\WakeAgain\docs\_portfolio_previews\shots")
PLAY_DIR = Path(r"C:\Users\hysoo\Desktop\WakeAgain-PlayStore\screenshots")
SHOTS.mkdir(parents=True, exist_ok=True)
PLAY_DIR.mkdir(parents=True, exist_ok=True)

PHONE = {"width": 390, "height": 844, "device_scale_factor": 2}


def capture_play_mobile() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": PHONE["width"], "height": PHONE["height"]},
            device_scale_factor=PHONE["device_scale_factor"],
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
                "Mobile/15E148 Safari/604.1"
            ),
            is_mobile=True,
            has_touch=True,
        )
        page = ctx.new_page()
        try:
            # Market list
            page.goto("https://wakeagain.com/app/", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(2800)
            # dismiss cookies/modals if any
            page.evaluate(
                """() => {
                document.querySelectorAll('[aria-label*=close], .modal-close, .toast-close')
                  .forEach(b => { try { b.click() } catch(e){} });
            }"""
            )
            page.wait_for_timeout(400)
            market = SHOTS / "wa_play_market.png"
            page.screenshot(path=str(market), full_page=False)
            print("ok market", market.stat().st_size)

            # Detail — prefer Trace listing id=2
            page.goto(
                "https://wakeagain.com/project.html?id=2",
                wait_until="domcontentloaded",
                timeout=90000,
            )
            page.wait_for_timeout(2800)
            detail = SHOTS / "wa_play_detail.png"
            page.screenshot(path=str(detail), full_page=False)
            print("ok detail", detail.stat().st_size)

            # Create / list-new form (may redirect to login — still ok as app shell)
            for url in (
                "https://wakeagain.com/app/#new",
                "https://wakeagain.com/app/#/new",
                "https://wakeagain.com/sell.html",
            ):
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(1800)
                    body = page.inner_text("body")[:200]
                    if len(body) > 20:
                        create = SHOTS / "wa_play_create.png"
                        page.screenshot(path=str(create), full_page=False)
                        print("ok create from", url, create.stat().st_size)
                        break
                except Exception as e:
                    print("create try fail", url, e)
        finally:
            ctx.close()
            browser.close()

    # sync into Play package folder with phone-* names
    mapping = {
        "wa_play_market.png": "phone-01-market.png",
        "wa_play_detail.png": "phone-02-detail.png",
        "wa_play_create.png": "phone-03-create.png",
    }
    for src_name, dest_name in mapping.items():
        src = SHOTS / src_name
        if src.is_file():
            shutil.copy2(src, PLAY_DIR / dest_name)
            print("play package", dest_name, (PLAY_DIR / dest_name).stat().st_size)


def find_window_rect(title_keywords: list[str]):
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    found = []

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        low = title.lower()
        if any(k.lower() in low for k in title_keywords):
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w > 200 and h > 200:
                found.append((hwnd, title, rect.left, rect.top, rect.right, rect.bottom))
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return found


def capture_trace() -> None:
    from PIL import ImageGrab

    exe_candidates = [
        Path(r"C:\Users\hysoo\Desktop\Trace\Trace.exe"),
        Path(r"C:\Trace\Trace.exe"),
    ]
    exe = next((p for p in exe_candidates if p.is_file()), None)
    if not exe:
        print("Trace.exe not found")
        return

    # kill existing to get clean UI
    subprocess.run(["taskkill", "/IM", "Trace.exe", "/F"], capture_output=True)
    time.sleep(0.8)
    proc = subprocess.Popen([str(exe)], cwd=str(exe.parent))
    print("launched", exe, "pid", proc.pid)

    rect = None
    for i in range(25):
        time.sleep(0.6)
        wins = find_window_rect(["Trace", "트레이스", "OnHae", "온해", "경험"])
        if wins:
            # pick largest
            wins.sort(key=lambda x: (x[4] - x[2]) * (x[5] - x[3]), reverse=True)
            rect = wins[0]
            print("window", rect[1], rect[2:])
            break
        print("waiting window", i)

    dest = SHOTS / "trace_ui.png"
    if rect:
        hwnd, title, l, t, r, b = rect
        # bring to front
        try:
            ctypes = __import__("ctypes")
            user32 = ctypes.windll.user32
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
        except Exception as e:
            print("foreground fail", e)
        # pad slightly inward to drop shadow
        pad = 2
        img = ImageGrab.grab(bbox=(l + pad, t + pad, r - pad, b - pad))
        img.save(dest, "PNG")
        print("ok trace window", dest.stat().st_size, img.size)
    else:
        # fallback full primary monitor
        img = ImageGrab.grab()
        img.save(dest, "PNG")
        print("ok trace fullscreen fallback", dest.stat().st_size, img.size)

    # leave app running or close? close to avoid clutter
    try:
        proc.terminate()
    except Exception:
        pass
    subprocess.run(["taskkill", "/IM", "Trace.exe", "/F"], capture_output=True)


def main() -> None:
    capture_play_mobile()
    capture_trace()
    for p in sorted(SHOTS.glob("wa_play_*")):
        print(p.name, p.stat().st_size)
    print("trace_ui", (SHOTS / "trace_ui.png").stat().st_size if (SHOTS / "trace_ui.png").is_file() else "missing")


if __name__ == "__main__":
    main()
