#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/dist/release"
PANDOC_BIN="${PANDOC_BIN:-pandoc}"
FONT_DIR="${FONT_DIR:-/usr/share/fonts/opentype/noto}"

PANDOC_VERSION="3.11"
MERMAID_IMAGE="${MERMAID_IMAGE:-ghcr.io/mermaid-js/mermaid-cli/mermaid-cli:11.16.1@sha256:e7fc5c569c039c7d663e875ac0fe70828910f686b9bbee2d064f7e8a096d49f8}"
TYPST_IMAGE="${TYPST_IMAGE:-ghcr.io/typst/typst:0.15.1@sha256:5410828f3b97f32fcc3eb95fed614c962d03f480f74cea06936540b95037d2ee}"

export TZ=UTC
export LC_ALL=C.UTF-8
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git -C "$ROOT" log -1 --format=%ct)}"

die() {
  echo "release render failed: $*" >&2
  exit 1
}

command -v "$PANDOC_BIN" >/dev/null 2>&1 || die "pandoc is not installed"
command -v docker >/dev/null 2>&1 || die "docker is not installed"
command -v fc-match >/dev/null 2>&1 || die "fontconfig/fc-match is not installed"
[[ -d "$FONT_DIR" ]] || die "CJK font directory not found: $FONT_DIR"

actual_pandoc="$("$PANDOC_BIN" --version | sed -n '1s/^pandoc //p')"
[[ "$actual_pandoc" == "$PANDOC_VERSION" ]] ||   die "expected pandoc $PANDOC_VERSION, got $actual_pandoc"

python3 "$ROOT/scripts/validate_book.py"
python3 "$ROOT/scripts/build_book.py"
python3 "$ROOT/scripts/prepare_release.py"

docker pull "$MERMAID_IMAGE" >/dev/null
docker pull "$TYPST_IMAGE" >/dev/null

while IFS=$'\t' read -r index digest mmd svg; do
  [[ "$index" == "index" ]] && continue

  docker run --rm     --user "$(id -u):$(id -g)"     -v "$OUT:/data"     -v "$FONT_DIR:/usr/share/fonts/opentype/noto:ro"     "$MERMAID_IMAGE"     -i "$mmd"     -o "$svg"     --configFile /data/mermaid-config.json     --backgroundColor transparent
done < "$OUT/diagram-manifest.tsv"

COMMON=(
  "$OUT/C-with-Modern-Grammar.release.md"
  "--defaults=$ROOT/release/pandoc.yaml"
  "--resource-path=$OUT:$ROOT"
)

"$PANDOC_BIN" "${COMMON[@]}"   --css="$ROOT/release/book.css"   --embed-resources   --section-divs   -o "$OUT/C-with-Modern-Grammar.html"

"$PANDOC_BIN" "${COMMON[@]}"   --css="$ROOT/release/book.css"   --epub-chapter-level=1   -o "$OUT/C-with-Modern-Grammar.epub"

"$PANDOC_BIN" "${COMMON[@]}"   --to=typst   --lua-filter="$ROOT/release/chapter-breaks.lua"   -V papersize=a4   -V mainfont="Noto Serif CJK SC"   -V codefont="Noto Sans Mono CJK SC"   -V fontsize=10.5pt   -V margin=18mm   -V linestretch=1.2   -V page-numbering=1   -o "$OUT/C-with-Modern-Grammar.typ"

docker run --rm   --user "$(id -u):$(id -g)"   -v "$OUT:/data"   -v "$FONT_DIR:/fonts:ro"   "$TYPST_IMAGE"   compile   --root /data   --font-path /fonts   /data/C-with-Modern-Grammar.typ   /data/C-with-Modern-Grammar.pdf

source_commit="${GITHUB_SHA:-$(git -C "$ROOT" rev-parse HEAD)}"
main_font="$(fc-match "Noto Serif CJK SC" | head -n 1)"
code_font="$(fc-match "Noto Sans Mono CJK SC" | head -n 1)"

cat > "$OUT/RENDERER_VERSIONS.txt" <<EOF
source_commit=$source_commit
source_date_epoch=$SOURCE_DATE_EPOCH
pandoc=$("$PANDOC_BIN" --version | head -n 1)
mermaid_image=$MERMAID_IMAGE
typst_image=$TYPST_IMAGE
main_font=$main_font
code_font=$code_font
EOF

python3 "$ROOT/scripts/validate_release.py"

echo "release artifacts:"
ls -lh   "$ROOT/dist/C-with-Modern-Grammar.md"   "$OUT/C-with-Modern-Grammar.html"   "$OUT/C-with-Modern-Grammar.epub"   "$OUT/C-with-Modern-Grammar.pdf"
