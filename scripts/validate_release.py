#!/usr/bin/env python3
"""Validate rendered publication artifacts using only the Python standard library."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "release"
RELEASE_MD = OUT / "C-with-Modern-Grammar.release.md"
HTML = OUT / "C-with-Modern-Grammar.html"
EPUB = OUT / "C-with-Modern-Grammar.epub"
PDF = OUT / "C-with-Modern-Grammar.pdf"
MANIFEST = OUT / "diagram-manifest.tsv"
VERSIONS = OUT / "RENDERER_VERSIONS.txt"

MERMAID_FENCE = re.compile(
    r"^\s*(?:[~]{3,}|[\x60]{3,})mermaid\s*$",
    re.MULTILINE,
)
SVG_REF = re.compile(r"\((diagrams/diagram-[^)]+\.svg)\)")


class ValidationError(RuntimeError):
    pass


def require_file(path: Path, minimum_size: int = 1) -> None:
    if not path.is_file():
        raise ValidationError(f"missing artifact: {path.relative_to(ROOT)}")
    if path.stat().st_size < minimum_size:
        raise ValidationError(
            f"artifact is unexpectedly small: {path.relative_to(ROOT)} "
            f"({path.stat().st_size} bytes)"
        )


def validate_release_markdown() -> list[str]:
    require_file(RELEASE_MD, 10_000)
    text = RELEASE_MD.read_text(encoding="utf-8")

    if MERMAID_FENCE.search(text):
        raise ValidationError("release Markdown still contains Mermaid fences")

    refs = SVG_REF.findall(text)
    if not refs:
        raise ValidationError("release Markdown contains no rendered diagram references")

    for ref in refs:
        require_file(OUT / ref, 100)

    return refs


def validate_diagram_manifest(refs: list[str]) -> None:
    require_file(MANIFEST, 20)
    rows = MANIFEST.read_text(encoding="utf-8").splitlines()
    if not rows or rows[0] != "index\tsha256\tmmd\tsvg":
        raise ValidationError("diagram manifest header is invalid")

    entries = []
    for row in rows[1:]:
        fields = row.split("\t")
        if len(fields) != 4:
            raise ValidationError(f"invalid diagram manifest row: {row}")
        index, digest, mmd, svg = fields
        if int(index) != len(entries) + 1:
            raise ValidationError("diagram manifest indexes are not continuous")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValidationError(f"invalid diagram digest: {digest}")
        require_file(OUT / mmd, 1)
        require_file(OUT / svg, 100)
        entries.append(svg)

    if entries != refs:
        raise ValidationError(
            "diagram manifest order does not match release Markdown references"
        )

    for svg in entries:
        raw = (OUT / svg).read_text(encoding="utf-8", errors="replace")
        if "<svg" not in raw:
            raise ValidationError(f"rendered diagram is not SVG: {svg}")


def validate_html() -> None:
    require_file(HTML, 20_000)
    text = HTML.read_text(encoding="utf-8", errors="replace").lower()
    if "<html" not in text or "</html>" not in text:
        raise ValidationError("HTML artifact is not a complete document")
    if "c with modern grammar" not in text:
        raise ValidationError("HTML artifact is missing the book title")


def validate_epub() -> None:
    require_file(EPUB, 20_000)
    if not zipfile.is_zipfile(EPUB):
        raise ValidationError("EPUB artifact is not a ZIP container")

    with zipfile.ZipFile(EPUB) as archive:
        names = archive.namelist()
        if not names or names[0] != "mimetype":
            raise ValidationError("EPUB mimetype entry is not first")
        if archive.read("mimetype") != b"application/epub+zip":
            raise ValidationError("EPUB mimetype is invalid")
        if "META-INF/container.xml" not in names:
            raise ValidationError("EPUB is missing META-INF/container.xml")
        if not any(name.endswith(".opf") for name in names):
            raise ValidationError("EPUB is missing its OPF package document")


def validate_pdf() -> None:
    require_file(PDF, 50_000)
    with PDF.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValidationError("PDF artifact does not start with a PDF header")


def main() -> int:
    try:
        refs = validate_release_markdown()
        validate_diagram_manifest(refs)
        validate_html()
        validate_epub()
        validate_pdf()
        require_file(VERSIONS, 50)
    except (ValidationError, ValueError, zipfile.BadZipFile) as exc:
        print(f"release validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "release validation passed: "
        f"{len(refs)} diagrams, HTML, EPUB, PDF, renderer provenance"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
