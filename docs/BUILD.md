# Build and repack V1

The supported workflow rebuilds RetroArch and repacks a V1 firmware image.
It retains the vendor kernel, boot chain, runtime libraries, radio firmware,
emulator cores, and charging UI. It is not a complete firmware build from source.

Use Linux with Python 3.11+, Git, GNU coreutils, e2fsprogs (`debugfs`, `e2fsck`),
GPT fdisk (`sgdisk`), `file`, `zstd`, `make`, and `pkg-config`.

## RetroArch

Run `bash scripts/prepare_sources.sh` to obtain RetroArch 1.22.0 at commit
`703321e80784e3fe3ba0dd648e482cd1ee47cdc0` and apply the project patch.
Alternatively extract the release's patched source archive into
`sources/RetroArch/`. The archive is already patched; do not apply it again.
`build_retroarch.sh` recognizes an already applied patch in a Git checkout.

The build needs an ARMHF Buildroot compiler and a development sysroot extracted
from the matching stock firmware. The compiler must target glibc, Cortex-A53,
and the hard-float ABI. The existing build used Buildroot 2026.08 and kernel
headers 4.9.170. `configs/armhf_defconfig` records the toolchain configuration;
`patches/0001-rename-constexpr-host-tool.patch` is the Linux header host-tool fix.
Install it as a Buildroot `linux-headers` patch before building that toolchain.

Set the input paths and build:

```sh
export RGSP_ARMHF_HOST=/absolute/path/to/buildroot-armhf-output/host
export RGSP_STOCK_SYSROOT=/absolute/path/to/stock-sysroot
# Optional when using an existing patched source tree:
export RGSP_RETROARCH_SOURCE=/absolute/path/to/RetroArch
bash scripts/build_retroarch.sh
```

The stock sysroot must preserve ARMHF loader/libraries in
`lib/arm-linux-gnueabihf`, `usr/lib/arm-linux-gnueabihf`, and `usr/lib32`, plus
the matching SDL2 headers under `usr/include/SDL2`. Buildroot supplies C and
FreeType headers; this repository supplies the udev compatibility header and
SDL2 pkg-config metadata. The script checks these prerequisites. Merely having
a generic ARM compiler is insufficient for this vendor graphics runtime.

The script writes `build/retroarch-build.log` and creates `retroarch` in the
source tree. The published binary needs glibc no newer than 2.34; the stock
runtime supplies 2.35.

## Repack

Decompress the V1 release image into `inputs/RGSP_retroarch-V1.img`. Repack with
the current overlay and optional replacement ARMHF RetroArch executable:

```sh
python3 scripts/repack.py \
  --baseline inputs/RGSP_retroarch-V1.img \
  --retroarch sources/RetroArch/retroarch \
  --output dist/RGSP_retroarch-V1.img
zstd -T4 -6 dist/RGSP_retroarch-V1.img -o dist/RGSP_retroarch-V1.img.zst
```

Omit `--retroarch` to retain the baseline executable. The script copies the
baseline, extracts p5/p6, applies `firmware/overlay`, checks both filesystems,
and checks the final GPT. It refuses existing output files. It writes regular
files only; it does not flash a card. The stock frontend fallback is retained.

`firmware/base-overlay` and `configs/aarch64_buildroot.config` document the
earlier Buildroot rootfs setup. The config's `${ORIGINAL_WORKSPACE}` paths
describe historical inputs and must be adapted for a complete rootfs rebuild.
The original stock runtime overlay is an external input. They are reference
material, not an independently reproducible clean build recipe.
