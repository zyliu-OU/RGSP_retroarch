First published **RGSP_retroarch V1** firmware, based on RetroArch 1.22.0.

- Quick Menu → Close Content returns from a game to RetroArch.
- Advanced settings and supported settings categories are visible.
- Wi-Fi (ConnMan), Bluetooth (bluetoothctl), and Settings → Services → SSH.
- PC-visible FAT32 RGSP-SHARE for games, BIOS files, saves, and configuration.
- One-time configuration migration and crash/fallback logs.

**Experimental: not yet boot-tested on an RG SP.** Host checks passed for
filesystems, partitions, compression, ARMHF feature reporting, SSH config,
and source/binary packaging. Device radio, display, input, and SSH login
checks remain outstanding.

Download `RGSP_retroarch-V1.img.zst`, verify it against `SHA256SUMS`, decompress
with zstd, and flash the `.img` to a spare microSD. First boot expands the
card and reboots; the next boot prepares RGSP-SHARE.

SSH is off by default. Add a public key at
`RGSP-SHARE/services/authorized_keys`, connect Wi-Fi, and enable
Settings → Services → SSH. Connect as root on port 22; passwords are disabled.

The release also provides the patched RetroArch source and compiled ARMHF
executable. Source/build instructions and validation details are in the repo.
