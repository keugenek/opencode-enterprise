#!/usr/bin/env python3
"""Validate a reviewable, extensible patch series and its checksum inventory."""
import argparse
import hashlib
import pathlib
import re


def read_series(package):
    package = pathlib.Path(package).resolve()
    names = (package / 'patches/series').read_text().splitlines()
    if not 1 <= len(names) <= 9999:
        raise ValueError('A non-empty numbered patch series is required')
    for number, name in enumerate(names, 1):
        if not re.fullmatch(f'{number:04d}-[a-z0-9-]+\\.patch', name):
            raise ValueError('Patch sequence must be contiguous, unique and ordered')
    if set(names) != {p.name for p in (package / 'patches').glob('*.patch')}:
        raise ValueError('Patch files and series manifest differ')
    inventory = {}
    for line in (package / 'SHA256SUMS').read_text().splitlines():
        expected, relative = line.split('  ', 1)
        path = package / relative
        if (not re.fullmatch(r'[0-9a-f]{64}', expected) or relative in inventory
                or pathlib.PurePosixPath(relative).is_absolute()
                or '..' in pathlib.PurePosixPath(relative).parts
                or path.is_symlink() or not path.resolve().is_relative_to(package)
                or not path.is_file()):
            raise ValueError('Invalid checksum inventory entry')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Checksum mismatch: ' + relative)
        inventory[relative] = expected
    required = {'BASE_COMMIT', 'patches/series', *('patches/' + name for name in names)}
    if not required.issubset(inventory):
        raise ValueError('Checksum inventory omits a required input')
    return [package / 'patches' / name for name in names]


def refresh(package):
    package = pathlib.Path(package)
    paths = sorted(p for p in package.rglob('*') if p.is_file() and p.name != 'SHA256SUMS'
                   and '__pycache__' not in p.parts and p.suffix != '.pyc')
    if any(p.is_symlink() for p in paths):
        raise ValueError('Symlinks are not package inputs')
    (package / 'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()
        + '  ' + p.relative_to(package).as_posix() + '\n' for p in paths))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    package = pathlib.Path(__file__).resolve().parents[1]
    if args.refresh:
        refresh(package)
    print('Verified patches:', len(read_series(package)))
