# RGSP_retroarch

Experimental RetroArch firmware for the Anbernic RG SP. **V1** is the first
published project release, using RetroArch **1.22.0**.

[Download V1](https://github.com/zyliu-OU/RGSP_retroarch/releases/tag/V1)

V1 enables **Quick Menu → Close Content** to return from a game to RetroArch,
advanced settings, Wi-Fi and Bluetooth menus, and **Settings → Services → SSH**.
The shared configuration is upgraded once so older menu visibility settings
do not hide these options.

The image passed host filesystem, partition, binary, and compression checks.
**It has not been boot-tested on an RG SP.** Wi-Fi scanning, Bluetooth pairing,
graphics, controls, charging, and SSH login still need device verification.

## Install

1. Download `RGSP_retroarch-V1.img.zst` and `SHA256SUMS` from the release.
2. Verify the download with `sha256sum --ignore-missing -c SHA256SUMS`.
3. Decompress with `zstd -d RGSP_retroarch-V1.img.zst` and flash the `.img`
   with a disk image writer to a spare microSD, preserving your original card.
   Flashing erases the selected card.
4. Boot normally. First boot expands storage and reboots; the next boot creates
   the FAT32 `RGSP-SHARE` volume. Keep power connected while this completes.
5. Put games in `RGSP-SHARE/roms/` and BIOS files in `RGSP-SHARE/system/`.
   Saves and configuration also live on this volume. Eject it before removing
   the card from a computer.

The image is approximately 3.02 GiB uncompressed before storage expansion. FAT32
limits individual shared-volume files to less than 4 GiB. Vendor boot files,
kernel, runtime libraries, emulator cores, and factory content are inherited
from the supplied stock firmware.

## Wireless and SSH

Wi-Fi and Bluetooth are available under Settings. SSH is off by default.
Place your **public** SSH key in `RGSP-SHARE/services/authorized_keys`, connect
Wi-Fi, then enable **Settings → Services → SSH**. Connect as `root` on port 22.
Password login is disabled. The device generates its own host key on first use.

If wireless menus are missing, inspect `RGSP-SHARE/logs/frontend-status.txt`.
A stock fallback means the new frontend crashed. The associated
`retroarch-crash.log` records details. Close Content returns to the menu;
the main-menu shutdown action powers off the device.

Restart retains the active configuration path. The stock fallback saves its
own settings to `configfiles/retroarch/retroarch-stock.cfg` on RGSP-SHARE.
Service restarts wait for RetroArch to finish saving before stopping it.

## Source and rebuilding

The repository contains the firmware overlay, RetroArch patch, toolchain
configuration, and build/repack scripts. The release also includes the patched
RetroArch source and compiled ARMHF executable. See [BUILD.md](docs/BUILD.md).
The image depends on vendor components; the repack workflow uses the V1 image
as its baseline and does not require older development builds.

See [V1 validation](docs/V1-VALIDATION.md) for verification and remaining tests.

## Component licenses

RetroArch is licensed under GPL version 3 or later; its license is included in
[docs/RetroArch-COPYING](docs/RetroArch-COPYING). The source archive retains
upstream notices. Buildroot, Linux, emulator cores, OpenSSH, BusyBox, and vendor
components retain their respective licenses. This repository does not assign
a single license to the complete firmware image. This is an independent project
and is not an official Anbernic or RetroArch release.
