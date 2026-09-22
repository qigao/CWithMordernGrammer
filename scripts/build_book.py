#!/usr/bin/env python3
"""Build the canonical single-file Markdown manuscript.

The chapter files remain the authoritative editable sources. This script only
assembles them in BOOK_MANIFEST.txt order into dist/.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "BOOK_MANIFEST.txt"
OUTPUT = ROOT / "dist" / "C-with-Modern-Grammar.md"

FRONT_MATTER = """---
title: "C with Modern Grammar"
subtitle: "From Plain C to Typed and Verified Computation"
lang: "zh-CN"
rights: "Apache-2.0"
---

# C with Modern Grammar

**From Plain C to Typed and Verified Computation**

> This file is generated from the ordered chapter sources listed in
> BOOK_MANIFEST.txt. Edit the chapter files, not this artifact.
"""


def chapter_paths() -> list[Path]:
    entries = [
        line.strip()
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return [ROOT / entry for entry in entries]


def main() -> None:
    pieces = [FRONT_MATTER.rstrip()]
    for path in chapter_paths():
        text = path.read_text(encoding="utf-8").lstrip("\ufeff").rstrip()
        pieces.append(text)

    output = "\n\n<!-- chapter-break -->\n\n".join(pieces) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output, encoding="utf-8", newline="\n")
    print(f"built {OUTPUT.relative_to(ROOT)} ({len(output.splitlines()):,} lines)")


if __name__ == "__main__":
    main()
