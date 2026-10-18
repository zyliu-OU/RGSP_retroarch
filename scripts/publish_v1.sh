#!/bin/bash
set -euo pipefail
PROJECT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT"
REPO=zyliu-OU/RGSP_retroarch
ASSETS=(
  dist/RGSP_retroarch-V1.img.zst
  dist/RetroArch-1.22.0-rgsp-v1-source.tar.gz
  dist/retroarch-armhf-v1.tar.gz
  dist/SHA256SUMS
)
for asset in "${ASSETS[@]}"; do test -s "$asset"; done
(cd dist && sha256sum --ignore-missing -c SHA256SUMS)
git push -u origin main
if gh release view V1 --repo "$REPO" >/dev/null 2>&1; then
  gh release upload V1 "${ASSETS[@]}" --repo "$REPO" --clobber
else
  gh release create V1 "${ASSETS[@]}" --repo "$REPO" \
    --target main --title 'RGSP_retroarch V1 (Experimental)' \
    --notes-file docs/RELEASE-V1.md --prerelease
fi
gh release view V1 --repo "$REPO" --json url --jq .url
