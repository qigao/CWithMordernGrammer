#!/usr/bin/env python3
"""Zero-dependency publication QA for the Markdown manuscript."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "BOOK_MANIFEST.txt"

EXTRA_MARKDOWN = [
    ROOT / "README.md",
    ROOT / "README_CN.md",
    ROOT / "BOOK_ARCHITECTURE.md",
    ROOT / "CHAPTER_TEMPLATE.md",
    ROOT / "SOURCE_SNAPSHOTS.md",
]

STALE_PATH_RE = re.compile(r"salts/(?:book|docs)", re.IGNORECASE)
MOVING_MASTER_LINK_RE = re.compile(
    r"(?:github\.com/[^)\s]+/(?:blob|tree)/master\b"
    r"|raw\.githubusercontent\.com/[^/\s]+/[^/\s]+/master/)",
    re.IGNORECASE,
)
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
PART_RE = re.compile(r"^#{1,3}\s+(Part\s+[IVX]+\s+—\s+.+?)\s*$")


class ValidationError(RuntimeError):
    pass


def manifest_entries() -> list[str]:
    entries = [
        line.strip()
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(entries) != 15:
        raise ValidationError(
            f"BOOK_MANIFEST.txt must contain 15 chapters, got {len(entries)}"
        )
    if len(set(entries)) != len(entries):
        raise ValidationError("BOOK_MANIFEST.txt contains duplicate chapter entries")
    for entry in entries:
        if not (ROOT / entry).is_file():
            raise ValidationError(f"manifest chapter does not exist: {entry}")
    return entries


def outside_fences(lines: list[str]):
    fence: str | None = None
    for number, line in enumerate(lines, start=1):
        match = re.match(r"^\s*([~]{3,}|[\x60]{3,})", line)
        if match:
            marker = match.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is None:
            yield number, line


def validate_chapter(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    h1 = []
    numbered_h2: list[int] = []
    unnumbered_h2 = []

    for number, line in outside_fences(lines):
        if re.match(r"^#\s+", line):
            h1.append((number, line))
        if re.match(r"^##\s+", line):
            section = re.match(r"^##\s+(\d+)\.\s+", line)
            if section:
                numbered_h2.append(int(section.group(1)))
            else:
                unnumbered_h2.append((number, line))

    if len(h1) != 1:
        raise ValidationError(f"{path.name}: expected exactly one H1, got {len(h1)}")
    if unnumbered_h2:
        where = ", ".join(str(number) for number, _ in unnumbered_h2[:5])
        raise ValidationError(
            f"{path.name}: unnumbered/label H2 at line(s) {where}"
        )

    unique_sections = list(dict.fromkeys(numbered_h2))
    expected = list(range(1, len(unique_sections) + 1))
    if unique_sections != expected:
        raise ValidationError(
            f"{path.name}: numbered H2 sections are not continuous: "
            f"{unique_sections}"
        )


def validate_text_hygiene(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if STALE_PATH_RE.search(text):
        raise ValidationError(
            f"{path.name}: contains removed salts/book or salts/docs path"
        )
    if MOVING_MASTER_LINK_RE.search(text):
        raise ValidationError(
            f"{path.name}: contains a moving GitHub master source link"
        )


def validate_internal_links(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().strip("<>")
        if not target or target.startswith("#"):
            continue

        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            continue

        local = unquote(parsed.path)
        if not local:
            continue

        destination = (path.parent / local).resolve()
        try:
            destination.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ValidationError(
                f"{path.name}: internal link escapes repository: {raw_target}"
            ) from exc

        if not destination.exists():
            raise ValidationError(
                f"{path.name}: broken internal link {raw_target} -> "
                f"{destination.relative_to(ROOT)}"
            )


def extract_parts(path: Path) -> list[str]:
    parts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PART_RE.match(line)
        if match:
            parts.append(match.group(1))
    return parts


def validate_part_structure() -> None:
    english = extract_parts(ROOT / "README.md")
    chinese = extract_parts(ROOT / "README_CN.md")
    architecture = extract_parts(ROOT / "BOOK_ARCHITECTURE.md")

    if len(english) != 5 or len(chinese) != 5 or len(architecture) != 5:
        raise ValidationError(
            "README, README_CN and BOOK_ARCHITECTURE must each contain "
            "exactly five Parts"
        )
    if chinese != architecture:
        raise ValidationError(
            "README_CN and BOOK_ARCHITECTURE five-Part titles/order do not match"
        )

    expected_roman = ["I", "II", "III", "IV", "V"]
    for label, parts in (("README", english), ("README_CN", chinese)):
        roman = []
        for part in parts:
            match = re.match(r"Part\s+([IVX]+)", part)
            if match is None:
                raise ValidationError(f"{label}: malformed Part heading: {part}")
            roman.append(match.group(1))
        if roman != expected_roman:
            raise ValidationError(f"{label}: unexpected Part order: {roman}")


def main() -> int:
    try:
        entries = manifest_entries()
        chapters = [ROOT / entry for entry in entries]
        markdown = chapters + EXTRA_MARKDOWN

        for chapter in chapters:
            validate_chapter(chapter)

        for path in markdown:
            validate_text_hygiene(path)
            validate_internal_links(path)

        validate_part_structure()
    except ValidationError as exc:
        print(f"publication QA failed: {exc}", file=sys.stderr)
        return 1

    lines = sum(
        len(path.read_text(encoding="utf-8").splitlines())
        for path in chapters
    )
    print(
        f"publication QA passed: {len(chapters)} chapters, "
        f"{lines:,} chapter Markdown lines"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
