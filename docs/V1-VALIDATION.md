# V1 validation

V1 is the first published RGSP_retroarch release. The release image includes
`/etc/rgsp-release` and uses the V1 shared-config migration marker.

## Completed host checks

- RetroArch is an ARMHF ELF executable, built with networking, Wi-Fi, and
  Bluetooth. QEMU ran its feature report against the stock ARMHF runtime.
  Required glibc symbols do not exceed 2.34; the runtime provides 2.35.
- The new frontend supports ConnMan Wi-Fi, bluetoothctl Bluetooth, and the
  RG SP SSH menu. Advanced settings and Close Content are enabled by default.
- The previous candidate rootfs and appfs passed read-only `e2fsck -fn`.
  The V1 repack checked both filesystems again, then the rootfs extracted from
  the final image passed another read-only check.
- V1 metadata and storage migration extracted from the final image match the
  published overlay exactly. The final GPT passed `sgdisk -v`, with the
  inherited warning about the vendor eight-entry partition table.
- The final compressed image passed `zstd -t`. Checksums are in the release's
  `SHA256SUMS` and [V1-manifest.json](V1-manifest.json).
- The patched source archive matches all modified RetroArch source files.
  Shell scripts passed syntax checks; the repack script passed Python compilation
  and was used to produce the published image.
- OpenSSH configuration parsing and ED25519 key generation passed under QEMU
  during development. SSH has no preinstalled private host key and starts off.

## Device verification remains

V1 has not been boot-tested on an RG SP. The host checks do not establish
that Mali rendering, input, first-boot expansion, Wi-Fi scanning, Bluetooth
pairing, charging, suspend, or SSH authentication work on the handheld.

Check Quick Menu → Close Content during a game, then Settings → Wi-Fi,
Bluetooth, and Services → SSH. Inspect `RGSP-SHARE/logs/frontend-status.txt`.
If stock fallback is active, inspect `retroarch-crash.log`; the fallback
frontend cannot expose the new wireless menus.
