#!/usr/bin/env python3
"""Prepare the canonical manuscript for HTML/EPUB/PDF rendering.

This script never reads chapter files directly. Its only manuscript input is
#35's deterministic dist/C-with-Modern-Grammar.md artifact.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dist" / "C-with-Modern-Grammar.md"
OUT_DIR = ROOT / "dist" / "release"
DIAGRAM_DIR = OUT_DIR / "diagrams"
OUTPUT = OUT_DIR / "C-with-Modern-Grammar.release.md"

FENCE_RE = re.compile(r"(?ms)^(?P<fence>`{3}|~{3})mermaid\s*\n(?P<body>.*?)(?:\n)(?P=fence)\s*$")

def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit("missing canonical manuscript; run scripts/build_book.py first")

    text = SOURCE.read_text(encoding="utf-8")
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    DIAGRAM_DIR.mkdir(parents=True)
    diagrams: list[str] = []

    def replace_mermaid(match: re.Match[str]) -> str:
        index = len(diagrams) + 1
        stem = f"diagram-{index:03d}"
        body = match.group("body").rstrip() + "\n"
        (DIAGRAM_DIR / f"{stem}.mmd").write_text(body, encoding="utf-8", newline="\n")
        diagrams.append(stem)
        return f"![Diagram {index}](diagrams/{stem}.svg)"

    prepared = FENCE_RE.sub(replace_mermaid, text)
    prepared = prepared.replace("<!-- chapter-break -->", '<div class="chapter-break"></div>')
    prepared, replacements = re.subn(r"(?m)^# C with Modern Grammar\s*\n", "", prepared, count=1)
    if replacements != 1:
        raise SystemExit("canonical display-title H1 not found exactly once")
    if not diagrams:
        raise SystemExit("no Mermaid diagrams found in canonical manuscript")
    if FENCE_RE.search(prepared):
        raise SystemExit("Mermaid fence remained after preparation")

    OUTPUT.write_text(prepared, encoding="utf-8", newline="\n")
    print(f"prepared {OUTPUT.relative_to(ROOT)} with {len(diagrams)} Mermaid diagrams")

if __name__ == "__main__":
    main()
