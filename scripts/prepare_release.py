#!/usr/bin/env python3
"""Prepare one canonical manuscript edition for HTML/EPUB/PDF rendering."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_NAME = "C-with-Modern-Grammar"
FENCE_RE = re.compile(
    r"(?ms)^(?P<fence>`{3}|~{3})mermaid\s*\n(?P<body>.*?)(?:\n)(?P=fence)\s*$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edition", choices=("cn", "en"), required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    edition = args.edition
    source = ROOT / "dist" / edition / f"{BOOK_NAME}.md"
    out_dir = ROOT / "dist" / "release" / edition
    diagram_dir = out_dir / "diagrams"
    output = out_dir / f"{BOOK_NAME}.release.md"
    epub_output = out_dir / f"{BOOK_NAME}.epub.md"

    if not source.is_file():
        raise SystemExit(
            f"missing canonical manuscript for {edition}; "
            f"run scripts/build_book.py --edition {edition} first"
        )

    text = source.read_text(encoding="utf-8")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    diagram_dir.mkdir(parents=True)
    diagrams: list[str] = []

    def replace_mermaid(match: re.Match[str]) -> str:
        index = len(diagrams) + 1
        stem = f"diagram-{index:03d}"
        body = match.group("body").rstrip() + "\n"
        (diagram_dir / f"{stem}.mmd").write_text(
            body, encoding="utf-8", newline="\n"
        )
        diagrams.append(stem)
        return f"![Diagram {index}](diagrams/{stem}.svg)"

    prepared = FENCE_RE.sub(replace_mermaid, text)
    prepared = prepared.replace(
        "<!-- chapter-break -->", "::: {.chapter-break}\n:::"
    )
    prepared, replacements = re.subn(
        r"(?m)^# C with Modern Grammar\s*\n", "", prepared, count=1
    )
    if replacements != 1:
        raise SystemExit(
            f"{edition}: canonical display-title H1 not found exactly once"
        )
    if not diagrams:
        raise SystemExit(f"{edition}: no Mermaid diagrams found")
    if FENCE_RE.search(prepared):
        raise SystemExit(f"{edition}: Mermaid fence remained after preparation")

    output.write_text(prepared, encoding="utf-8", newline="\n")
    epub_prepared = re.sub(
        r"(diagrams/diagram-\d{3})\.svg", r"\1.png", prepared
    )
    if "diagrams/diagram-" in epub_prepared and ".svg" in epub_prepared:
        raise SystemExit(f"{edition}: EPUB retained SVG diagram references")
    if epub_prepared.count(".png)") != len(diagrams):
        raise SystemExit(f"{edition}: EPUB PNG diagram reference count mismatch")
    epub_output.write_text(epub_prepared, encoding="utf-8", newline="\n")
    print(
        f"prepared {edition}: {output.relative_to(ROOT)} and "
        f"{epub_output.relative_to(ROOT)} with {len(diagrams)} Mermaid diagrams"
    )


if __name__ == "__main__":
    main()
