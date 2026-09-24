#!/usr/bin/env python3
"""Report likely explanatory fenced text that should be prose/list/table.

This is an editorial aid, not a publication gate. Layout-sensitive blocks such
as pipelines, state machines, pseudocode, timelines, and inference rules are
intentionally ignored by a conservative heuristic.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_MARKERS = (
    "↓", "→", "│", "├", "└", "─", "┬", "┴",
    "->", "<-", "=>", "<=", ">=", "!=",
    "⊢", "∀", "∧", "∨", "⇓", "────────────────",
)

PSEUDOCODE_WORDS = (
    "if ", "for ", "while ", "return ", "require ",
    "match ", "case ", "state =", "on ",
)


def chapter_paths() -> list[Path]:
    paths: list[Path] = []
    for edition in ("cn", "en"):
        paths.extend(sorted((ROOT / edition).glob("ch-*.md")))
    return paths


def looks_layout_sensitive(lines: list[str]) -> bool:
    text = "\n".join(lines)
    if any(marker in text for marker in LAYOUT_MARKERS):
        return True

    stripped = [line.strip() for line in lines if line.strip()]
    if any(line.endswith(":") for line in stripped):
        return True

    lowered = [line.lower() for line in stripped]
    if any(
        line.startswith(word)
        for line in lowered
        for word in PSEUDOCODE_WORDS
    ):
        return True

    if any(re.search(r"\w+\s*\([^)]*\)", line) for line in stripped):
        return True

    return False


def scan(path: Path) -> list[tuple[int, int, list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    findings: list[tuple[int, int, list[str]]] = []

    in_text = False
    fence = ""
    start = 0
    body: list[str] = []

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not in_text:
            if stripped in ("~~~text", "```text"):
                in_text = True
                fence = stripped[:3]
                start = index
                body = []
            continue

        if stripped == fence:
            nonempty = [item for item in body if item.strip()]
            char_count = len("\n".join(nonempty))

            if (
                1 <= len(nonempty) <= 6
                and char_count <= 240
                and not looks_layout_sensitive(nonempty)
            ):
                findings.append((start, index, nonempty))

            in_text = False
            fence = ""
            body = []
            continue

        body.append(line)

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--edition",
        choices=("cn", "en", "all"),
        default="all",
    )
    args = parser.parse_args()

    total = 0

    for path in chapter_paths():
        if args.edition != "all" and path.parent.name != args.edition:
            continue

        findings = scan(path)
        if not findings:
            continue

        print(path.relative_to(ROOT))
        for start, end, body in findings:
            total += 1
            preview = " / ".join(item.strip() for item in body)
            print(f"  L{start}-L{end}: {preview}")

    print(f"editorial text-fence candidates: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
