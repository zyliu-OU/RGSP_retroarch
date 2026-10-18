#!/bin/bash
set -euo pipefail
PROJECT=$(cd -- "$(dirname -- "$0")/.." && pwd)
SRC="$PROJECT/sources/RetroArch"
COMMIT=703321e80784e3fe3ba0dd648e482cd1ee47cdc0
mkdir -p "$PROJECT/sources"
if [[ ! -d "$SRC/.git" ]]; then
    git clone --depth 1 --branch v1.22.0 https://github.com/libretro/RetroArch.git "$SRC"
fi
[[ $(git -C "$SRC" rev-parse HEAD) == "$COMMIT" ]]
if ! git -C "$SRC" apply --reverse --check "$PROJECT/patches/retroarch-rgsp.patch" 2>/dev/null; then
    git -C "$SRC" apply --check "$PROJECT/patches/retroarch-rgsp.patch"
    git -C "$SRC" apply "$PROJECT/patches/retroarch-rgsp.patch"
fi
printf 'Patched RetroArch source: %s\n' "$SRC"
