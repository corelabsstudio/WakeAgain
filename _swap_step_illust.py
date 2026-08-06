# -*- coding: utf-8 -*-
from pathlib import Path
import re

repl = [
    ("/assets/play-store/screenshots/phone-01-market.png?v=cream", "/assets/illustrations/step-browse.png?v=1"),
    ("/assets/play-store/screenshots/phone-02-detail.png?v=cream", "/assets/illustrations/step-deal.png?v=1"),
    ("/assets/play-store/screenshots/phone-03-create.png?v=cream", "/assets/illustrations/step-list.png?v=1"),
    ("/assets/play-store/screenshots/tablet-01-market.png?v=cream", "/assets/illustrations/step-browse.png?v=1"),
    ('class="gv-phone"', 'class="gv-illust"'),
    ("guide-visual.css?v=2", "guide-visual.css?v=5"),
    ("guide-visual.css?v=4", "guide-visual.css?v=5"),
    ("guide-visual.css?v=1", "guide-visual.css?v=5"),
    ("guide-visual.css?v=3", "guide-visual.css?v=5"),
]


def process(text: str) -> str:
    t = text
    # drop tablet screenshot block on buy page
    t = re.sub(r'<figure class="gv-tablet">[\s\S]*?</figure>\s*', "", t)
    for a, b in repl:
        t = t.replace(a, b)
    t = re.sub(r'width="390"\s+height="844"', 'width="720" height="720"', t)
    t = re.sub(r'width="1024"\s+height="640"', 'width="720" height="720"', t)
    return t


for name in ["how-to-sell.html", "how-to-buy.html", "safety.html"]:
    p = Path("public/guide") / name
    t = p.read_bytes().decode("utf-8")
    t2 = process(t)
    p.write_bytes(t2.encode("utf-8"))
    print(name, "ok", "준비" in t2 or "둘러보기" in t2 or "데모" in t2 or "올리기" in t2)

# homepage
idx = Path("public/index.html")
h = idx.read_bytes().decode("utf-8")
h = h.replace('class="phone-bezel"', 'class="shot-illust"')
for a, b in repl[:4]:
    h = h.replace(a, b)
h = re.sub(r'width="390"\s*\n\s*height="844"', 'width="720"\n              height="720"', h)
for old in [
    "styles.css?v=20260729-nohubcopy",
    "styles.css?v=20260729-navglass",
    "styles.css?v=20260729-shorthome",
    "styles.css?v=20260729-illust",
]:
    if old in h:
        h = h.replace(old, "styles.css?v=20260729-illust")
        break
else:
    h = re.sub(r"styles\.css\?v=[^\"]+", "styles.css?v=20260729-illust", h, count=1)
idx.write_bytes(h.encode("utf-8"))
print("index ok")
