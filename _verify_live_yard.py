# -*- coding: utf-8 -*-
import re
import time
import urllib.request

UA = {"Cache-Control": "no-cache", "Pragma": "no-cache", "User-Agent": "yard-verify/1"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def main() -> None:
    for i in range(6):
        try:
            styles = fetch("https://wakeagain.com/styles.css")
            ux9 = fetch("https://wakeagain.com/ux9.css")
            buy = fetch("https://wakeagain.com/guide/how-to-buy.html")
            safety = fetch("https://wakeagain.com/guide/safety.html")
            break
        except Exception as e:
            print("retry", i, e)
            time.sleep(8)
    else:
        print("FAILED to fetch")
        return

    print("styles: #1a1814", "#1a1814" in styles, "#a855f7" in styles, "btn c2410c", "#c2410c" in styles)
    print("ux9: #c2410c", "#c2410c" in ux9, "#a855f7" in ux9, "nav yard", "34, 30, 24" in ux9)
    print("buy: yard-v2", "yard-v2" in buy, "theme-yard", "theme-yard" in buy)
    links = re.findall(r'href="([^"]+\.css[^"]*)"', buy)
    print("buy css order:", links)
    print("safety: yard-v2", "yard-v2" in safety)
    # purple hardcode residual on live styles
    pur = re.findall(r"#a855f7|#7c3aed|#8b5cf6|#c084fc", styles + ux9)
    print("live purple hex hits:", len(pur), pur[:5])


if __name__ == "__main__":
    main()
