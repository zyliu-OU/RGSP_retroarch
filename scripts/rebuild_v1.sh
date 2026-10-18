#!/bin/bash
# Recompile and replace the existing V1 artifacts after validation succeeds.
set -euo pipefail
PROJECT=$(cd -- "$(dirname -- "$0")/.." && pwd)
WORKSPACE=$(dirname -- "$PROJECT")
export RGSP_RETROARCH_SOURCE=${RGSP_RETROARCH_SOURCE:-$WORKSPACE/retroarch-v1.22.0-src}
export RGSP_STOCK_SYSROOT=${RGSP_STOCK_SYSROOT:-$WORKSPACE/rgsp_retroarch_os_kit/buildroot-v13/stock-sysroot}
export RGSP_ARMHF_HOST=${RGSP_ARMHF_HOST:-$WORKSPACE/buildroot-armhf-output/host}
BASELINE=${RGSP_V1_BASELINE:-$PROJECT/dist/RGSP_retroarch-V1.img}
test -s "$BASELINE"
bash "$PROJECT/scripts/build_retroarch.sh"
mkdir -p "$PROJECT/dist"
STAGE=$(mktemp -d "$PROJECT/dist/.v1-build.XXXXXX")
trap 'rm -rf -- "$STAGE"' EXIT
python3 "$PROJECT/scripts/repack.py" --baseline "$BASELINE" \
  --retroarch "$RGSP_RETROARCH_SOURCE/retroarch" \
  --output "$STAGE/RGSP_retroarch-V1.img"
zstd -T4 -6 "$STAGE/RGSP_retroarch-V1.img" -o "$STAGE/RGSP_retroarch-V1.img.zst"
zstd -t "$STAGE/RGSP_retroarch-V1.img.zst"
# Archive tracked source files from the patched working tree, excluding builds.
git -C "$RGSP_RETROARCH_SOURCE" ls-files -z |
  tar -czf "$STAGE/RetroArch-1.22.0-rgsp-v1-source.tar.gz" \
    -C "$RGSP_RETROARCH_SOURCE" --transform='s,^,RetroArch-1.22.0-rgsp-v1/,' \
    --null -T -
tar -czf "$STAGE/retroarch-armhf-v1.tar.gz" -C "$RGSP_RETROARCH_SOURCE" retroarch
python3 - "$STAGE" "$PROJECT" <<'PY'
from pathlib import Path
import hashlib
import json
import sys

stage, project = map(Path, sys.argv[1:])
sums = {}
for path in sorted(stage.iterdir()):
    with path.open('rb') as stream:
        sums[path.name] = hashlib.file_digest(stream, 'sha256').hexdigest()
(stage / 'SHA256SUMS').write_text(''.join(f'{sha}  {name}\n' for name, sha in sums.items()))
manifest = json.loads((project / 'docs/V1-manifest.json').read_text())
manifest['sha256'] = sums
manifest['image_bytes'] = (stage / 'RGSP_retroarch-V1.img').stat().st_size
for path in stage.iterdir():
    path.replace(project / 'dist' / path.name)
(project / 'docs/V1-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
PY
printf 'Replaced V1 artifacts in %s/dist\n' "$PROJECT"
