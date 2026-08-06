# -*- coding: utf-8 -*-
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
r = urllib.request.urlopen(
    urllib.request.Request(
        "https://wakeagain.com/api/v1/projects?limit=20",
        headers={"User-Agent": "q"},
    ),
    timeout=30,
)
d = json.loads(r.read().decode())
print("total", d.get("total"))
for p in d.get("projects") or []:
    print(
        "-",
        p.get("id"),
        p.get("title"),
        p.get("listing_status") or p.get("status"),
        "start",
        p.get("price_start"),
        "imgs",
        len(p.get("demo_images") or []),
    )
    print(f"  https://wakeagain.com/project.html?id={p.get('id')}")
