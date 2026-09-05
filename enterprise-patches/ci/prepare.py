#!/usr/bin/env python3
"""Verify the published series and apply it to an isolated exact-baseline worktree."""
import hashlib
import pathlib
import re
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[2]
package = root / 'enterprise-patches'
target = pathlib.Path(sys.argv[1]).resolve()
baseline = (package / 'BASE_COMMIT').read_text().strip()
if not re.fullmatch(r'[0-9a-f]{40}', baseline):
    raise SystemExit('BASE_COMMIT must contain one full commit SHA')
if target.exists():
    raise SystemExit('Refusing to overwrite an existing build directory')
for line in (package / 'SHA256SUMS').read_text().splitlines():
    expected, relative = line.split('  ', 1)
    path = (package / relative).resolve()
    if not path.is_relative_to(package) or not path.is_file():
        raise SystemExit(f'Invalid checksum path: {relative}')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit(f'Checksum mismatch: {relative}')
names = (package / 'patches/series').read_text().splitlines()
if len(names) != 4 or any(not re.fullmatch(r'000[1-4]-[a-z0-9-]+\.patch', n) for n in names):
    raise SystemExit('Expected the reviewed four-patch series')
if len(set(names)) != 4 or names != sorted(names):
    raise SystemExit('Patch series is duplicated or out of order')
subprocess.run(['git', 'cat-file', '-e', baseline + '^{commit}'], cwd=root, check=True)
subprocess.run(['git', 'worktree', 'add', '--detach', str(target), baseline], cwd=root, check=True)
subprocess.run(['git', '-c', 'user.name=Enterprise CI', '-c', 'user.email=ci@localhost',
                'am', *[str(package / 'patches' / n) for n in names]], cwd=target, check=True)
print('Patched source tree:', subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=target).decode().strip())
