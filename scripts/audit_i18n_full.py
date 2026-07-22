"""Audit data-i18n keys against i18n.js + i18n-messages.js."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public"


def main() -> None:
    texts = [
        (PUBLIC / "js" / "i18n.js").read_text(encoding="utf-8"),
        (PUBLIC / "js" / "i18n-messages.js").read_text(encoding="utf-8"),
    ]
    combined = "\n".join(texts)
    counts = Counter(re.findall(r'"([a-zA-Z][a-zA-Z0-9]*(?:\.[a-zA-Z0-9_]+)+)"\s*:', combined))
    # also bare keys like "skip"
    counts.update(re.findall(r'"(skip|key)"\s*:', combined))
    defined = set(counts)

    used: dict[str, set[str]] = defaultdict(set)
    pat = re.compile(
        r'data-i18n(?:-html|-placeholder|-title|-aria)?\s*=\s*["\']([^"\']+)["\']'
    )
    for p in PUBLIC.rglob("*"):
        if p.suffix.lower() not in {".html", ".js"}:
            continue
        if p.name in {"i18n.js", "i18n-messages.js"}:
            continue
        if "node_modules" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = p.relative_to(PUBLIC).as_posix()
        for m in pat.finditer(text):
            used[m.group(1).strip()].add(rel)
        if p.suffix == ".js":
            for m in re.finditer(
                r'(?:WakeAgainI18n\.)?t\(\s*["\']([a-zA-Z][a-zA-Z0-9_.]*)["\']\s*,',
                text,
            ):
                k = m.group(1)
                if "." in k or k in {"skip"}:
                    used[k].add(rel)

    missing = sorted(k for k in used if k not in defined)
    once = sorted(k for k in used if 0 < counts.get(k, 0) < 2)

    print(f"used={len(used)} defined={len(defined)} missing={len(missing)}")
    for k in missing:
        print(f"MISSING\t{k}\t{', '.join(sorted(used[k])[:4])}")
    print(f"once={len(once)}")
    for k in once[:50]:
        print(f"ONCE\t{k}\t{counts[k]}\t{', '.join(sorted(used[k])[:3])}")

    by_file: dict[str, list[str]] = defaultdict(list)
    for k in missing:
        for f in used[k]:
            by_file[f].append(k)
    print("\n=== missing by file (top) ===")
    for f, ks in sorted(by_file.items(), key=lambda x: -len(x[1]))[:25]:
        print(f"{len(ks):3} {f}")
        for k in ks[:12]:
            print(f"     - {k}")
        if len(ks) > 12:
            print(f"     ... +{len(ks)-12} more")


if __name__ == "__main__":
    main()
