#!/bin/bash
set -euo pipefail

PROJECT=$(cd -- "$(dirname -- "$0")/.." && pwd)
SRC=${RGSP_RETROARCH_SOURCE:-$PROJECT/sources/RetroArch}
SYS=${RGSP_STOCK_SYSROOT:-$PROJECT/inputs/stock-sysroot}
HOST=${RGSP_ARMHF_HOST:-$PROJECT/build/armhf/host}
BUILDROOT_HEADERS="$HOST/arm-buildroot-linux-gnueabihf/sysroot/usr/include"
REPORT="$PROJECT/build/retroarch-build.log"
CC="$HOST/bin/arm-buildroot-linux-gnueabihf-gcc"
CXX="$HOST/bin/arm-buildroot-linux-gnueabihf-g++"
PATCH="$PROJECT/patches/retroarch-rgsp.patch"
mkdir -p "$PROJECT/build"

if ! git -C "$SRC" apply --reverse --check "$PATCH" 2>/dev/null; then
  git -C "$SRC" apply --check "$PATCH"
  git -C "$SRC" apply "$PATCH"
fi

test -x "$CC"
if [[ ! -x "$CXX" ]]; then
  # This target uses the C-only Buildroot toolchain; C++ features are disabled.
  CXX=/bin/false
fi
test -f "$SYS/usr/include/SDL2/SDL.h"
test -f "$SYS/usr/lib32/libSDL2-2.0.so.0.12.0"
test -f "$BUILDROOT_HEADERS/stdio.h"
test -f "$PROJECT/firmware/compat-headers/libudev.h"
test -f "$SRC/network/drivers_wifi/connmanctl.c"
grep -q 'OBJ += network/drivers_wifi/connmanctl.o' "$SRC/Makefile.common"

export PATH="$HOST/bin:$PATH"
export PKG_CONFIG_LIBDIR="$PROJECT/firmware/pkgconfig:$SYS/lib/arm-linux-gnueabihf/pkgconfig:$SYS/usr/lib/arm-linux-gnueabihf/pkgconfig:$SYS/usr/lib32/pkgconfig:$SYS/usr/share/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="$SYS"
export CC="$CC --sysroot=$SYS -B$SYS/lib/arm-linux-gnueabihf/ -I$BUILDROOT_HEADERS -I$SRC/gfx/include/MESA"
export CXX="$CXX --sysroot=$SYS -B$SYS/lib/arm-linux-gnueabihf/"
export PKG_CONF_PATH=/usr/bin/pkg-config
export CFLAGS="-O2 -mcpu=cortex-a53 -mfloat-abi=hard -DHAVE_RGSP -isystem $BUILDROOT_HEADERS -I$BUILDROOT_HEADERS/freetype2 -I$PROJECT/firmware/compat-headers -I$SRC/gfx/include/MESA -I$SYS/usr/include/SDL2"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-L$SYS/usr/lib32 -L$SYS/usr/lib/arm-linux-gnueabihf -L$SYS/lib/arm-linux-gnueabihf -Wl,-rpath-link,$SYS/usr/lib32 -Wl,-rpath-link,$SYS/usr/lib/arm-linux-gnueabihf -Wl,-rpath-link,$SYS/lib/arm-linux-gnueabihf -Wl,--no-as-needed -lmali"

cd "$SRC"
./configure \
  --host=arm-buildroot-linux-gnueabihf \
  --enable-sdl2 --enable-opengles --enable-egl \
  --enable-alsa --enable-udev --enable-freetype \
  --enable-networking --enable-wifi --enable-bluetooth \
  --disable-dbus --disable-opengl --disable-x11 --disable-wayland \
  --disable-vulkan --disable-ffmpeg --disable-qt --disable-pulse \
  --disable-kms --disable-systemd \
  --disable-glslang --disable-builtinglslang --disable-slang \
  > "$REPORT" 2>&1
make -j8 >> "$REPORT" 2>&1
file retroarch
readelf -d retroarch | grep NEEDED
