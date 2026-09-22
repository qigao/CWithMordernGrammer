#!/usr/bin/env python3
"""Validate rendered release artifacts."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "dist" / "release"
HTML = RELEASE / "C-with-Modern-Grammar.html"
EPUB = RELEASE / "C-with-Modern-Grammar.epub"
PDF = RELEASE / "C-with-Modern-Grammar.pdf"
PREPARED = RELEASE / "C-with-Modern-Grammar.release.md"
EPUB_PREPARED = RELEASE / "C-with-Modern-Grammar.epub.md"
DIAGRAMS = RELEASE / "diagrams"

def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)

def main() -> None:
    require(PREPARED.is_file(), "prepared release Markdown is missing")
    prepared = PREPARED.read_text(encoding="utf-8")
    require(EPUB_PREPARED.is_file(), "prepared EPUB Markdown is missing")
    epub_prepared = EPUB_PREPARED.read_text(encoding="utf-8")
    require("```mermaid" not in prepared, "backtick Mermaid fence remains")
    require("~~~mermaid" not in prepared, "tilde Mermaid fence remains")

    sources = sorted(DIAGRAMS.glob("diagram-*.mmd"))
    svgs = sorted(DIAGRAMS.glob("diagram-*.svg"))
    pngs = sorted(DIAGRAMS.glob("diagram-*.png"))
    require(bool(sources), "no Mermaid source files were prepared")
    require(len(sources) == len(svgs), f"Mermaid SVG count mismatch: {len(sources)} != {len(svgs)}")
    require(len(sources) == len(pngs), f"Mermaid PNG count mismatch: {len(sources)} != {len(pngs)}")
    for svg in svgs:
        require(svg.stat().st_size > 100, f"empty/suspicious SVG: {svg.name}")
        require("<svg" in svg.read_text(encoding="utf-8"), f"not an SVG document: {svg.name}")

    for png in pngs:
        require(png.stat().st_size > 100, f"empty/suspicious PNG: {png.name}")
        with png.open("rb") as handle:
            require(handle.read(8) == b"\x89PNG\r\n\x1a\n", f"not a PNG document: {png.name}")

    expected_refs = set(re.findall(r"diagrams/(diagram-\d{3}\.svg)", prepared))
    actual_refs = {p.name for p in svgs}
    require(expected_refs == actual_refs, "prepared Markdown diagram references do not match rendered SVG set")
    expected_epub_refs = set(re.findall(r"diagrams/(diagram-\d{3}\.png)", epub_prepared))
    actual_png_refs = {p.name for p in pngs}
    require(expected_epub_refs == actual_png_refs, "EPUB Markdown diagram references do not match rendered PNG set")

    require(HTML.is_file() and HTML.stat().st_size > 100_000, "HTML missing/small")
    html = HTML.read_text(encoding="utf-8")
    require("<html" in html.lower(), "HTML document root missing")
    require('id="TOC"' in html, "HTML TOC missing")
    require("data:image/svg+xml" in html or "<svg" in html, "HTML does not appear to embed rendered diagrams")

    require(EPUB.is_file() and EPUB.stat().st_size > 100_000, "EPUB missing/small")
    with zipfile.ZipFile(EPUB) as archive:
        names = set(archive.namelist())
        require("mimetype" in names, "EPUB mimetype entry missing")
        require("META-INF/container.xml" in names, "EPUB container.xml missing")
        require(archive.read("mimetype") == b"application/epub+zip", "EPUB mimetype content is invalid")
        require(any(name.lower().endswith(".png") for name in names), "EPUB does not contain rendered PNG diagrams")

    require(PDF.is_file() and PDF.stat().st_size > 100_000, "PDF missing/small")
    with PDF.open("rb") as handle:
        require(handle.read(5) == b"%PDF-", "PDF magic header missing")

    print(f"release artifacts valid: {len(svgs)} SVG + {len(pngs)} PNG diagrams, HTML {HTML.stat().st_size:,} B, EPUB {EPUB.stat().st_size:,} B, PDF {PDF.stat().st_size:,} B")

if __name__ == "__main__":
    main()
