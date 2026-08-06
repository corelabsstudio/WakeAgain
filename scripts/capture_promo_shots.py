"""Capture WakeAgain screenshots for long promo image."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "marketing" / "promo" / "shots"
BASE = "http://127.0.0.1:8080"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            locale="ko-KR",
        ).new_page()

        page.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "landing_mobile.png"), full_page=False)
        print("landing_mobile")

        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / "landing_desktop.png"), full_page=False)
        print("landing_desktop")

        page.evaluate("window.scrollTo(0, 700)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "landing_mid.png"), full_page=False)
        print("landing_mid")

        page.evaluate("window.scrollTo(0, 1400)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "landing_features.png"), full_page=False)
        print("landing_features")

        page.set_viewport_size({"width": 390, "height": 844})
        for path, name in [
            ("/app/", "app_shell"),
            ("/app/#/login", "app_login"),
            ("/app/#/projects", "app_projects"),
            ("/app/#/register", "app_register"),
        ]:
            try:
                page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1200)
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
                print(name)
            except Exception as e:
                print("skip", name, e)

        # try project list / auction pages common paths
        for path, name in [
            ("/projects", "projects"),
            ("/project.html", "project_html"),
            ("/app/", "app_home2"),
        ]:
            try:
                page.goto(f"{BASE}{path}", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1000)
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
                print(name)
            except Exception as e:
                print("skip", name, e)

        browser.close()
    print("done", [p.name for p in sorted(OUT.glob("*.png"))])


if __name__ == "__main__":
    main()
