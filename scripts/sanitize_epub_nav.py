#!/usr/bin/env python3
"""Normalize the EPUB navigation document to a text-only TOC.

Pandoc can carry inline image nodes into nav.xhtml when building the EPUB TOC.
Navigation labels do not need image resources; keeping them there can create a
dangling media reference even when the chapter body itself is packaged
correctly. Replace nav images with their alt text and preserve every ZIP entry's
metadata/compression.
"""

from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPUB = ROOT / "dist" / "release" / "C-with-Modern-Grammar.epub"
TMP = EPUB.with_suffix(".epub.tmp")

IMG_RE = re.compile(
    rb'<img\b(?P<attrs>[^>]*)/?>',
    re.IGNORECASE,
)
ALT_RE = re.compile(rb'\balt="(?P<alt>[^"]*)"', re.IGNORECASE)


def replace_img(match: re.Match[bytes]) -> bytes:
    attrs = match.group("attrs")
    alt_match = ALT_RE.search(attrs)
    if not alt_match:
        return b""
    # alt is already XML-escaped inside the XHTML attribute. Decode entities,
    # then escape it again as text content.
    alt = html.unescape(alt_match.group("alt").decode("utf-8"))
    return html.escape(alt, quote=False).encode("utf-8")


def main() -> None:
    if not EPUB.is_file():
        raise SystemExit(f"missing EPUB: {EPUB}")

    changed = 0
    with zipfile.ZipFile(EPUB, "r") as src, zipfile.ZipFile(TMP, "w") as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename.endswith("/nav.xhtml"):
                new_data, count = IMG_RE.subn(replace_img, data)
                data = new_data
                changed += count
            dst.writestr(info, data)

    if changed == 0:
        TMP.unlink(missing_ok=True)
        print("EPUB nav already contains no image nodes")
        return

    TMP.replace(EPUB)
    print(f"normalized EPUB nav: replaced {changed} image node(s) with text")


if __name__ == "__main__":
    main()
