#!/usr/bin/env python3
"""Verify the published series and apply it to an isolated exact-baseline worktree."""
import argparse
import pathlib
import re
import subprocess
from series import read_series

root = pathlib.Path(__file__).resolve().parents[2]
package = root / 'enterprise-patches'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('target')
parser.add_argument('--baseline', help='Full candidate upstream SHA for compatibility checks only')
args = parser.parse_args()
target = pathlib.Path(args.target).resolve()
baseline = args.baseline or (package / 'BASE_COMMIT').read_text().strip()
if not re.fullmatch(r'[0-9a-f]{40}', baseline):
    raise SystemExit('Baseline must contain one full commit SHA')
if target.exists():
    raise SystemExit('Refusing to overwrite an existing build directory')
patches = read_series(package)
if subprocess.run(['git', 'cat-file', '-e', baseline + '^{commit}'], cwd=root,
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
    subprocess.run(['git', 'fetch', '--depth=1', '--no-tags', 'https://github.com/anomalyco/opencode.git', baseline],
                   cwd=root, check=True)
subprocess.run(['git', 'cat-file', '-e', baseline + '^{commit}'], cwd=root, check=True)
subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'worktree', 'add', '--detach', str(target), baseline], cwd=root, check=True)
subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=Enterprise CI', '-c', 'user.email=ci@localhost',
                'am', *[str(p) for p in patches]], cwd=target, check=True)
print('Patched source tree:', subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=target).decode().strip())
