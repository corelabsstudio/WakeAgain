import time
import urllib.request

urls = {
    "home": "https://wakeagain.com/",
    "buy": "https://wakeagain.com/guide/how-to-buy.html",
    "sell": "https://wakeagain.com/guide/how-to-sell.html",
    "i18n": "https://wakeagain.com/js/i18n.js",
}

for attempt in range(12):
    print(f"\n--- attempt {attempt + 1} ---")
    try:
        h = urllib.request.urlopen(urls["home"] + f"?t={int(time.time())}", timeout=30).read().decode(
            "utf-8", "replace"
        )
        print("home 거래 안내:", "거래 안내" in h)
        print("home nav.trade:", 'data-i18n="nav.trade"' in h)
        print("home 마켓플레이스:", "마켓플레이스" in h)
        print("home how-to-sell in nav-links block:")
        i = h.find('class="nav-links"')
        block = h[i : i + 500] if i >= 0 else ""
        print("  sell link in top nav:", "how-to-sell" in block)
        print("  snippet:", block.replace("\n", " ")[:280])

        b = urllib.request.urlopen(urls["buy"] + f"?t={int(time.time())}", timeout=30).read().decode(
            "utf-8", "replace"
        )
        print("buy page 구매 가이드:", "구매 가이드" in b)
        print("buy page 팔 때:", "팔 때" in b)

        i18 = urllib.request.urlopen(urls["i18n"] + f"?t={int(time.time())}", timeout=30).read().decode(
            "utf-8", "replace"
        )
        print('i18n "거래 안내":', '"거래 안내"' in i18)
        print('i18n nav.trade:', "nav.trade" in i18)

        if (
            "거래 안내" in h
            and 'data-i18n="nav.trade"' in h
            and "how-to-sell" not in block
            and "마켓플레이스" not in block
        ):
            print("\nLIVE_NAV_OK")
            raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as e:
        print("err", e)
    time.sleep(20)

print("\nLIVE_NAV_NOT_YET")
raise SystemExit(1)
