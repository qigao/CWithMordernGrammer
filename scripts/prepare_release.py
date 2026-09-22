#!/usr/bin/env python3
"""Prepare the canonical manuscript for release-format rendering."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "dist" / "C-with-Modern-Grammar.md"
OUT = ROOT / "dist" / "release"
RELEASE_MD = OUT / "C-with-Modern-Grammar.release.md"
DIAGRAM_DIR = OUT / "diagrams"
MANIFEST = OUT / "diagram-manifest.tsv"
CONFIG_SOURCE = ROOT / "release" / "mermaid-config.json"
CONFIG_DEST = OUT / "mermaid-config.json"
CHAPTER_BREAK = "<!-- chapter-break -->"

OPEN_MERMAID = re.compile(r"^\s*([~]{3,}|[\x60]{3,})mermaid\s*$")


def split_generated_preamble(text: str) -> tuple[str, list[str]]:
    if not text.startswith("---\n"):
        raise RuntimeError("canonical manuscript is missing YAML front matter")

    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise RuntimeError("canonical manuscript has unterminated YAML front matter")

    front_matter = text[: closing + len("\n---")]
    body = text[closing + len("\n---\n") :]
    pieces = body.split(CHAPTER_BREAK)

    # build_book.py writes one generated title/notice piece followed by 15 chapters.
    if len(pieces) != 16:
        raise RuntimeError(
            f"expected generated preamble + 15 chapters, got {len(pieces)} pieces"
        )

    chapters = [piece.strip() for piece in pieces[1:]]
    if any(not chapter for chapter in chapters):
        raise RuntimeError("canonical manuscript contains an empty chapter piece")

    return front_matter.rstrip(), chapters


def replace_mermaid(text: str) -> tuple[str, list[tuple[int, str, str, str]]]:
    lines = text.splitlines()
    output: list[str] = []
    manifest: list[tuple[int, str, str, str]] = []
    index = 0
    i = 0

    while i < len(lines):
        opening = OPEN_MERMAID.match(lines[i])
        if opening is None:
            output.append(lines[i])
            i += 1
            continue

        marker = opening.group(1)
        marker_char = marker[0]
        minimum = len(marker)
        closing_re = re.compile(
            rf"^\s*{re.escape(marker_char)}{{{minimum},}}\s*$"
        )

        content: list[str] = []
        i += 1
        while i < len(lines) and closing_re.match(lines[i]) is None:
            content.append(lines[i])
            i += 1

        if i >= len(lines):
            raise RuntimeError("unterminated Mermaid code fence")

        diagram = "\n".join(content).rstrip() + "\n"
        digest = hashlib.sha256(diagram.encode("utf-8")).hexdigest()
        index += 1
        stem = f"diagram-{index:03d}-{digest[:12]}"
        mmd = f"diagrams/{stem}.mmd"
        svg = f"diagrams/{stem}.svg"

        (OUT / mmd).write_text(diagram, encoding="utf-8", newline="\n")
        manifest.append((index, digest, mmd, svg))

        output.append(
            f"![Mermaid diagram {index}]({svg}){{.mermaid-diagram}}"
        )
        i += 1

    return "\n".join(output).rstrip() + "\n", manifest


def main() -> None:
    text = CANONICAL.read_text(encoding="utf-8")
    front_matter, chapters = split_generated_preamble(text)

    OUT.mkdir(parents=True, exist_ok=True)
    DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)

    # Remove stale generated diagram inputs/outputs before a fresh preparation.
    for path in DIAGRAM_DIR.glob("diagram-*"):
        if path.is_file():
            path.unlink()

    body = (
        "\n\n<!-- release-chapter-break -->\n\n".join(chapters)
        + "\n"
    )
    prepared, diagrams = replace_mermaid(body)
    RELEASE_MD.write_text(
        front_matter + "\n\n" + prepared,
        encoding="utf-8",
        newline="\n",
    )
    CONFIG_DEST.write_text(
        CONFIG_SOURCE.read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )

    manifest_lines = ["index\tsha256\tmmd\tsvg"]
    manifest_lines.extend(
        f"{index}\t{digest}\t{mmd}\t{svg}"
        for index, digest, mmd, svg in diagrams
    )
    MANIFEST.write_text(
        "\n".join(manifest_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"prepared {RELEASE_MD.relative_to(ROOT)} "
        f"with {len(chapters)} chapters and {len(diagrams)} Mermaid diagrams"
    )


if __name__ == "__main__":
    main()
