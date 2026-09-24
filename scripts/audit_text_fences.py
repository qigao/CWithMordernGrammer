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

CODE_LIKE_RE = re.compile(
    r"[{}()[\];]|::|\.lean\b|\.[ch]\b|->|:=|==|!=|<=|>=|\+\+|--"
)

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_./:-]*$")
ALL_CAPS_RE = re.compile(r"^[A-Z][A-Z0-9_./:-]*$")
FORMAL_RELATION_RE = re.compile(r"(?:^|\s)(?:=|~)(?:\s|$)")


def audit_paths(edition: str) -> list[Path]:
    paths: list[Path] = []

    if edition in ("cn", "all"):
        paths.extend(
            [
                ROOT / "README_CN.md",
                ROOT / "BOOK_ARCHITECTURE.md",
                ROOT / "CHAPTER_TEMPLATE.md",
                ROOT / "cn" / "README.md",
            ]
        )
        paths.extend(sorted((ROOT / "cn").glob("ch-*.md")))

    if edition in ("en", "all"):
        paths.extend(
            [
                ROOT / "README.md",
                ROOT / "en" / "README.md",
            ]
        )
        paths.extend(sorted((ROOT / "en").glob("ch-*.md")))

    return list(dict.fromkeys(paths))


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

    if any(FORMAL_RELATION_RE.search(line) for line in stripped):
        return True

    if any(line in {"+", "=", "~"} for line in stripped):
        return True

    # Code/IDL/formal artifact rather than explanatory prose.
    if any(CODE_LIKE_RE.search(line) for line in stripped):
        return True

    # Stable identifiers, theorem names, file paths, enum/status tokens.
    if stripped and all(
        IDENTIFIER_RE.fullmatch(line) or ALL_CAPS_RE.fullmatch(line)
        for line in stripped
    ):
        return True

    # Indentation inside a fenced block usually carries tree/layout meaning.
    if any(line.startswith((" ", "\t")) for line in lines if line.strip()):
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
        logical = re.sub(r"^\s*>\s?", "", line).strip()

        if not in_text:
            if logical in ("~~~text", "```text"):
                in_text = True
                fence = logical[:3]
                start = index
                body = []
            continue

        if logical == fence:
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

        body.append(re.sub(r"^\s*>\s?", "", line))

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

    for path in audit_paths(args.edition):
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
