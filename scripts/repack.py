#!/usr/bin/env python3
"""Apply the project overlay and optional RetroArch binary to a V1 baseline.

Reuses the baseline's boot chain, kernel, drivers, cores, and vendor runtimes.
This is an image repack, not a complete firmware build from source.
"""
import argparse
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
SECTOR = 512


def run(*args):
    return subprocess.run([str(x) for x in args], check=True,
                          text=True, capture_output=True)


def debugfs(image, command, write=False):
    args = ['debugfs'] + (['-w'] if write else [])
    result = run(*args, '-R', command, image)
    if any(error in result.stderr for error in
           ('File not found', 'Could not', 'No such file', 'already exists')):
        raise RuntimeError(result.stderr)
    return result.stdout


def exists(image, guest):
    return 'Inode:' in run('debugfs', '-R', f'stat {guest}', image).stdout


def put(image, source, guest):
    if exists(image, guest):
        debugfs(image, f'rm {guest}', True)
    debugfs(image, f'write {source} {guest}', True)
    mode = 0o100755 if (source.stat().st_mode & 0o111 or guest.startswith('/etc/init.d/')) else 0o100644
    if guest == '/etc/ssh/sshd_config':
        mode = 0o100600
    debugfs(image, f'sif {guest} mode {mode}', True)
    if not exists(image, guest):
        raise RuntimeError(f'Failed to stage {guest}')


def copy_range(source, destination, length):
    remaining = length
    while remaining:
        chunk = source.read(min(8 * 1024 * 1024, remaining))
        if not chunk:
            raise ValueError('Short image read')
        destination.write(chunk)
        remaining -= len(chunk)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--retroarch', type=Path)
    args = parser.parse_args()
    baseline, output = args.baseline.resolve(), args.output.resolve()
    partial = output.with_name(output.name + '.partial')
    if output.exists() or partial.exists():
        raise FileExistsError('Output already exists')
    run('sgdisk', '-v', baseline)
    with baseline.open('rb') as stream:
        stream.seek(SECTOR)
        header = stream.read(SECTOR)
        if header[:8] != b'EFI PART':
            raise ValueError('Missing GPT')
        table_lba = struct.unpack_from('<Q', header, 72)[0]
        count, size = struct.unpack_from('<II', header, 80)
        if count != 8 or size != 128:
            raise ValueError('Expected the RG SP eight-entry GPT')
        stream.seek(table_lba * SECTOR)
        entries = stream.read(count * size)
    partitions = {}
    for number in (5, 6):
        start, end = struct.unpack_from('<QQ', entries, (number - 1) * size + 32)
        partitions[number] = (start * SECTOR, (end - start + 1) * SECTOR)
    if [partitions[n][1] for n in (5, 6)] != [512 * 1024**2, 256 * 1024**2]:
        raise ValueError('Expected the compact V1 rootfs and appfs sizes')
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix='rgsp-repack-') as directory:
            images = {}
            with baseline.open('rb') as stream:
                for number, (offset, length) in partitions.items():
                    image = Path(directory) / f'p{number}.ext4'
                    stream.seek(offset)
                    with image.open('wb') as target:
                        copy_range(stream, target, length)
                    images[number] = image
            root = images[5]
            for source in sorted((PROJECT / 'firmware/overlay').rglob('*')):
                if not source.is_file():
                    continue
                guest = '/' + source.relative_to(PROJECT / 'firmware/overlay').as_posix()
                for parent in reversed(Path(guest).parents):
                    if str(parent) != '/' and not exists(root, str(parent)):
                        debugfs(root, f'mkdir {parent}', True)
                put(root, source, guest)
            if args.retroarch:
                binary = args.retroarch.resolve()
                info = run('file', '-b', binary).stdout
                if 'ELF 32-bit' not in info or 'ARM' not in info:
                    raise ValueError('RetroArch must be an ARMHF ELF binary')
                put(images[6], binary, '/deep/retro/retroarch')
            for image in images.values():
                run('e2fsck', '-fn', image)
            run('cp', '--reflink=auto', '--sparse=always', '--', baseline, partial)
            with partial.open('r+b') as target:
                for number, image in images.items():
                    offset, length = partitions[number]
                    target.seek(offset)
                    with image.open('rb') as stream:
                        copy_range(stream, target, length)
            run('sgdisk', '-v', partial)
            partial.rename(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    with output.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    print(f'{digest}  {output.name}')


if __name__ == '__main__':
    main()
