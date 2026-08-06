# -*- coding: utf-8 -*-
"""Full yard palette apply + yard-theme load order + residual lilac purge."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
VER = "20260729-yard-v2"

# --- styles.css: root surface + residual lilac ---
p = PUBLIC / "styles.css"
t = p.read_text(encoding="utf-8")
repls = [
    ("/* WakeAgain — deep black + purple", "/* WakeAgain — yard brown + amber (auction warehouse)"),
    ("--bg: #050508;", "--bg: #1a1814;"),
    ("--bg-elev: #0c0c10;", "--bg-elev: #221f1a;"),
    ("--card: #111116;", "--card: #2a2620;"),
    ("--card-2: #16161d;", "--card-2: #322e27;"),
    ("--border: rgba(255, 255, 255, 0.07);", "--border: rgba(245, 236, 220, 0.1);"),
    ("--border-strong: rgba(255, 255, 255, 0.12);", "--border-strong: rgba(245, 236, 220, 0.18);"),
    ("--text: #f5f5f7;", "--text: #f5f0e6;"),
    ("--muted: #b0b0bc;", "--muted: #b8ae9c;"),
    ("--muted-2: #8b8b98;", "--muted-2: #8f8576;"),
    ("--radius: 22px;", "--radius: 10px;"),
    ("--radius-sm: 14px;", "--radius-sm: 8px;"),
    ("#c4b5fd", "#e8d5a3"),
    ("#C4B5FD", "#e8d5a3"),
    ("#4c1d95", "#5c4030"),
    ("#3b0764", "#3a2a1a"),
    ("#1e1b4b", "#2a2218"),
    ("#1a1025", "#1f1914"),
    ("/* Form pages (sell/buy) — purple system */", "/* Form pages (sell/buy) — yard system */"),
    ("/* soft neon rim + lift + ambient purple */", "/* soft rim + lift + ambient amber */"),
    (
        "/* Extend above hero so purple fills under floating nav, not cut at a hard edge */",
        "/* Extend above hero under floating nav */",
    ),
    ("/* Final: WA_unified_purple_white_bigger_A */", "/* Logo mark */"),
    ("background: rgba(18, 18, 24, 0.78);", "background: rgba(34, 30, 24, 0.94);"),
]
for a, b in repls:
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8", newline="\n")
print("styles.css updated")

# --- residual lilac across public ---
lilac_map = [
    ("#c4b5fd", "#e8d5a3"),
    ("#C4B5FD", "#e8d5a3"),
    ("#4c1d95", "#5c4030"),
    ("#3b0764", "#3a2a1a"),
    ("#7c3aed", "#a67c00"),
    ("#7C3AED", "#a67c00"),
    ("color: [168, 85, 247]", "color: [212, 160, 23]"),
    ("[168, 85, 247]", "[212, 160, 23]"),
]
extra_hits = []
for f in PUBLIC.rglob("*"):
    if not f.is_file() or f.suffix.lower() not in {".css", ".html", ".js", ".webmanifest"}:
        continue
    if "node_modules" in f.parts:
        continue
    try:
        text = f.read_text(encoding="utf-8")
    except Exception:
        continue
    orig = text
    for a, b in lilac_map:
        text = text.replace(a, b)
    if text != orig:
        f.write_text(text, encoding="utf-8", newline="\n")
        extra_hits.append(str(f.relative_to(ROOT)))
print("lilac residual files:", len(extra_hits))
for x in extra_hits:
    print(" ", x)

# --- ux9 primary CTA: lot red ---
u = PUBLIC / "ux9.css"
ut = u.read_text(encoding="utf-8")
old_btn = """.btn-primary {
  background: linear-gradient(135deg, #e3b341 0%, #d4a017 45%, #a67c00 100%);
  box-shadow: 0 8px 28px rgba(212, 160, 23, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.18);
}
.btn-primary:hover {
  background: linear-gradient(135deg, #e8b86d 0%, #e3b341 50%, #c4920f 100%);
  box-shadow: 0 12px 36px rgba(212, 160, 23, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.22);
}"""
new_btn = """.btn-primary {
  background: #c2410c;
  border: 1px solid #9a3412;
  box-shadow: none;
  color: #fffaf5;
}
.btn-primary:hover {
  background: #9a3412;
  box-shadow: 0 2px 0 rgba(0, 0, 0, 0.2);
}"""
if old_btn in ut:
    ut = ut.replace(old_btn, new_btn)
    print("ux9 btn-primary -> lot red")
else:
    print("ux9 btn-primary pattern not found; checking current:")
    m = re.search(r"\.btn-primary \{[^}]+\}", ut)
    print(m.group(0) if m else "none")
u.write_text(ut, encoding="utf-8", newline="\n")

# --- safety pink fallback ---
sf = PUBLIC / "guide" / "safety.html"
if sf.exists():
    st = sf.read_text(encoding="utf-8")
    st2 = st.replace("var(--pink, #ec4899)", "var(--pink, #e8b86d)")
    if st2 != st:
        sf.write_text(st2, encoding="utf-8", newline="\n")
        print("safety pink fallback fixed")

# --- HTML: move yard-theme to end of head, bump version ---
head_close = "</" + "head>"
link_line = f'  <link rel="stylesheet" href="/yard-theme.css?v={VER}" />\n'
changed = 0
for hf in PUBLIC.rglob("*.html"):
    h = hf.read_text(encoding="utf-8")
    if "yard-theme.css" not in h and "theme-yard" not in h:
        continue
    orig = h
    # remove existing yard links
    h2 = re.sub(
        r"[ \t]*<link rel=\"stylesheet\" href=\"/yard-theme\.css\?v=[^\"]+\"\s*/?>\s*\n?",
        "",
        h,
    )
    if "yard-theme.css" in h or "theme-yard" in h2 or "theme-yard" in h:
        if head_close in h2 and f"yard-theme.css?v={VER}" not in h2:
            h2 = h2.replace(head_close, link_line + head_close, 1)
        h2 = re.sub(r"yard-theme\.css\?v=[^\"]+", f"yard-theme.css?v={VER}", h2)
    if h2 != orig:
        hf.write_text(h2, encoding="utf-8", newline="\n")
        changed += 1
print("html yard last+cache:", changed)

# --- verify residual purple hex ---
bad = re.compile(
    r"#a855f7|#7c3aed|#8b5cf6|#c084fc|#a78bfa|#b56bff|#6d28d9|#c4b5fd|"
    r"168,\s*85,\s*247|124,\s*58,\s*237|#e879f9|#e9d5ff",
    re.I,
)
leftover = []
for f in PUBLIC.rglob("*"):
    if not f.is_file() or f.suffix.lower() not in {".css", ".html", ".js", ".webmanifest"}:
        continue
    try:
        text = f.read_text(encoding="utf-8")
    except Exception:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        if bad.search(line) and "yard-theme" not in f.name:
            leftover.append(f"{f.relative_to(ROOT)}:{i}:{line.strip()[:100]}")
print("LEFTOVER purple-ish:", len(leftover))
for x in leftover[:40]:
    print(" ", x)
print("DONE")
