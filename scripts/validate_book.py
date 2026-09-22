#!/usr/bin/env python3
"""Zero-dependency publication QA for the Markdown manuscript."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

SHARED_MARKDOWN = [
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--edition",
        choices=("cn", "en"),
        default="cn",
        help="edition to validate (default: cn)",
    )
    return parser.parse_args()


def manifest_entries(edition: str) -> list[str]:
    edition_dir = ROOT / edition
    manifest = edition_dir / "BOOK_MANIFEST.txt"
    entries = [
        line.strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    expected = [f"ch-{number:02d}.md" for number in range(1, 16)]
    if entries != expected:
        raise ValidationError(
            f"{edition}/BOOK_MANIFEST.txt must be exactly ch-01.md..ch-15.md; "
            f"got {entries}"
        )
    for entry in entries:
        if not (edition_dir / entry).is_file():
            raise ValidationError(
                f"{edition} manifest chapter does not exist: {entry}"
            )
    return entries


def validate_legacy_chinese_manifest() -> None:
    manifest = ROOT / "BOOK_MANIFEST.txt"
    entries = [
        line.strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    expected = [f"cn/ch-{number:02d}.md" for number in range(1, 16)]
    if entries != expected:
        raise ValidationError(
            "root BOOK_MANIFEST.txt must remain the Chinese compatibility "
            "manifest cn/ch-01.md..cn/ch-15.md"
        )


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
    main_h2: list[int] = []
    nested_h2: dict[int, list[int]] = {}
    unnumbered_h2 = []

    for number, line in outside_fences(lines):
        if re.match(r"^#\s+", line):
            h1.append((number, line))
        if re.match(r"^##\s+", line):
            section = re.match(
                r"^##\s+(\d+)(?:\.(\d+))?\.?\s+",
                line,
            )
            if section:
                main = int(section.group(1))
                child = section.group(2)
                if child is None:
                    main_h2.append(main)
                else:
                    nested_h2.setdefault(main, []).append(int(child))
            else:
                unnumbered_h2.append((number, line))

    if len(h1) != 1:
        raise ValidationError(f"{path.name}: expected exactly one H1, got {len(h1)}")
    if unnumbered_h2:
        where = ", ".join(str(number) for number, _ in unnumbered_h2[:5])
        raise ValidationError(
            f"{path.name}: unnumbered/label H2 at line(s) {where}"
        )

    unique_sections = list(dict.fromkeys(main_h2))
    expected = list(range(1, len(unique_sections) + 1))
    if unique_sections != expected:
        raise ValidationError(
            f"{path.name}: numbered H2 sections are not continuous: "
            f"{unique_sections}"
        )

    known_main = set(unique_sections)
    for main, children in nested_h2.items():
        if main not in known_main:
            raise ValidationError(
                f"{path.name}: subsection {main}.x has no parent section {main}"
            )
        unique_children = list(dict.fromkeys(children))
        child_expected = list(range(1, len(unique_children) + 1))
        if unique_children != child_expected:
            raise ValidationError(
                f"{path.name}: H2 subsections under {main} are not continuous: "
                f"{unique_children}"
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
    lines = path.read_text(encoding="utf-8").splitlines()
    for _, line in outside_fences(lines):
        for raw_target in LINK_RE.findall(line):
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

    if len(english) != 3 or len(chinese) != 3 or len(architecture) != 3:
        raise ValidationError(
            "README, README_CN and BOOK_ARCHITECTURE must each contain "
            "exactly three Parts"
        )
    if chinese != architecture:
        raise ValidationError(
            "README_CN and BOOK_ARCHITECTURE three-Part titles/order do not match"
        )

    expected_roman = ["I", "II", "III"]
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
    args = parse_args()
    edition = args.edition
    try:
        entries = manifest_entries(edition)
        edition_dir = ROOT / edition
        chapters = [edition_dir / entry for entry in entries]
        markdown = chapters + SHARED_MARKDOWN + [edition_dir / "README.md"]

        for chapter in chapters:
            validate_chapter(chapter)

        for path in markdown:
            validate_text_hygiene(path)
            validate_internal_links(path)

        validate_legacy_chinese_manifest()
        validate_part_structure()
    except ValidationError as exc:
        print(f"publication QA failed ({edition}): {exc}", file=sys.stderr)
        return 1

    lines = sum(
        len(path.read_text(encoding="utf-8").splitlines())
        for path in chapters
    )
    print(
        f"publication QA passed ({edition}): {len(chapters)} chapters, "
        f"{lines:,} chapter Markdown lines"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
