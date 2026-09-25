#!/usr/bin/env python3
"""Regenerate README table-of-contents blocks from manifests and chapter H1s."""

from __future__ import annotations

from book_structure import ROOT, replace_toc_block

TARGETS = [
    (ROOT / "README_CN.md", "cn", "./cn/"),
    (ROOT / "README.md", "en", "./en/"),
    (ROOT / "cn" / "README.md", "cn", "./"),
    (ROOT / "en" / "README.md", "en", "./"),
]


def main() -> None:
    for path, edition, prefix in TARGETS:
        text = path.read_text(encoding="utf-8")
        updated = replace_toc_block(
            text,
            edition,
            link_prefix=prefix,
        )
        path.write_text(updated, encoding="utf-8", newline="\n")
        print(f"updated TOC: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
