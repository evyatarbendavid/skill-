#!/usr/bin/env bash
# Package the skill for Claude Desktop / claude.ai upload.
#
# The skill lives at plugins/seo-aeo/skills/seo-aeo — one copy, no
# duplication. This just zips it so Desktop users have a single file to
# download instead of cloning the repo and finding the right folder.
set -euo pipefail
cd "$(dirname "$0")"

SRC="plugins/seo-aeo/skills/seo-aeo"
OUT="seo-aeo.zip"

[ -f "$SRC/SKILL.md" ] || { echo "error: $SRC/SKILL.md not found"; exit 1; }

rm -rf .build "$OUT"
mkdir -p .build
cp -r "$SRC" .build/seo-aeo
find .build -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
( cd .build && zip -qr "../$OUT" seo-aeo )
rm -rf .build

echo "built $OUT"
unzip -l "$OUT" | tail -n +4 | head -n -2
