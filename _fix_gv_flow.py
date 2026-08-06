# -*- coding: utf-8 -*-
from pathlib import Path
import re

for name in ["how-to-sell.html", "how-to-buy.html", "safety.html", "index.html"]:
    p = Path("public/guide") / name
    raw = p.read_bytes()
    t = raw.decode("utf-8")

    def fix_flow(m: re.Match) -> str:
        block = m.group(0)
        block = block.replace('<ol class="gv-flow">', '<div class="gv-flow" role="list">')
        block = block.replace('<li class="gv-flow-item">', '<div class="gv-flow-item" role="listitem">')
        block = block.replace("</li>", "</div>")
        block = block.replace("</ol>", "</div>")
        return block

    t2 = re.sub(r'<ol class="gv-flow">[\s\S]*?</ol>', fix_flow, t)
    t2 = t2.replace("guide-visual.css?v=1", "guide-visual.css?v=2")
    if "guide-visual.css?v=2" not in t2:
        t2 = t2.replace('href="/guide/guide-visual.css"', 'href="/guide/guide-visual.css?v=2"')
        t2 = t2.replace("guide-visual.css?v=1", "guide-visual.css?v=2")

    p.write_bytes(t2.encode("utf-8"))
    check = p.read_text(encoding="utf-8")
    ok = "준비" in check or "둘러보기" in check or "데모" in check or "올리기" in check
    print(name, "utf8_ok" if ok else "BAD", "div_flow" if 'role="list"' in check else "no_div")
