# -*- coding: utf-8 -*-
from pathlib import Path

root = Path(r"C:\Users\hysoo\projects\WakeAgain\public")
old = (
    "상호 코어랩스 · 대표 호현수 · 사업자등록번호 705-04-02867 · "
    '<a class="text-link" href="/legal/business.html">사업자 정보</a>'
)
new = (
    "상호 코어랩스 · 대표 호현수 · 사업자등록번호 705-04-02867 · "
    "TEL 033-818-2021 · HP 010-5583-2021 · "
    '<a class="text-link" href="/legal/business.html">사업자 정보</a>'
)
old2 = "상호 코어랩스 · 대표 호현수 · 사업자등록번호 705-04-02867"
new2 = "상호 코어랩스 · 대표 호현수 · 사업자등록번호 705-04-02867 · TEL 033-818-2021 · HP 010-5583-2021"

n = 0
for p in root.rglob("*.html"):
    t = p.read_text(encoding="utf-8")
    if "705-04-02867" not in t:
        continue
    if "033-818-2021" in t and "010-5583-2021" in t:
        print("ok", p.relative_to(root))
        continue
    orig = t
    if old in t:
        t = t.replace(old, new)
    elif old2 in t:
        t = t.replace(old2, new2)
    if t != orig:
        p.write_text(t, encoding="utf-8", newline="\n")
        n += 1
        print("patched", p.relative_to(root))
    else:
        print("skip", p.relative_to(root))
print("patched count", n)
