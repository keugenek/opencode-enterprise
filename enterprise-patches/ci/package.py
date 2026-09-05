#!/usr/bin/env python3
"""Package the tested binary and record the exact source and patch identity."""
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile

root = pathlib.Path(__file__).resolve().parents[2]
source = pathlib.Path(sys.argv[1]).resolve()
output = pathlib.Path(sys.argv[2]).resolve()
version = os.environ['OPENCODE_VERSION']
if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?', version):
    raise SystemExit('Invalid artifact version')
output.mkdir(parents=True, exist_ok=False)
name = f'opencode-enterprise-{version}-linux-x64'
staging = output / name
staging.mkdir()
shutil.copy2(source / 'packages/opencode/dist/opencode-linux-x64/bin/opencode', staging / 'opencode')
shutil.copy2(source / 'LICENSE', staging / 'LICENSE')
shutil.copytree(source / 'enterprise', staging / 'enterprise')
(staging / 'INSTALL.txt').write_text('Linux x64/glibc (AVX2). Requires an administrator-installed /etc/opencode/enterprise.json.\nRead enterprise/README.md and ACCEPTANCE.md. No endpoint credentials are embedded.\nThis prerelease has not passed production vLLM/network acceptance gates.\n')
with tarfile.open(output / (name + '.tar.gz'), 'w:gz') as archive:
    archive.add(staging, arcname=name)
shutil.rmtree(staging)
subprocess.run(['git', 'archive', '--format=tar.gz', '-o', str(output / 'enterprise-patches.tar.gz'),
                'HEAD', 'enterprise-patches'], cwd=root, check=True)
# Package only committed public paths: never sweep operator/customer working files
# or test-generated keys and caches into a distributable archive.
subprocess.run(['git', 'archive', '--format=tar.gz', '--prefix=opencode-enterprise-toolkit/',
                '-o', str(output / 'enterprise-mvp-toolkit.tar.gz'), 'HEAD',
                'mvp', 'assurance', 'delivery', 'enterprise-patches', 'README.md',
                'ENTERPRISE.md', 'LICENSING.md', 'LICENSE', '.github/workflows/enterprise-release.yml',
                '.github/workflows/mvp-validation.yml'], cwd=root, check=True)
subprocess.run(['git', 'archive', '--format=tar.gz', '--prefix=opencode-enterprise-source/',
                '-o', str(output / 'patched-source.tar.gz'), 'HEAD'], cwd=source, check=True)
def git(path, ref):
    return subprocess.check_output(['git', 'rev-parse', ref], cwd=path).decode().strip()
manifest = {
    'version': version,
    'distribution_commit': git(root, 'HEAD'),
    'baseline_commit': (root / 'enterprise-patches/BASE_COMMIT').read_text().strip(),
    'patched_source_tree': git(source, 'HEAD^{tree}'),
    'bun_version': subprocess.check_output(['bun', '--version']).decode().strip(),
    'target': 'linux-x64-glibc-avx2',
    'workflow_run': os.environ.get('GITHUB_RUN_ID'),
    'lockfile_sha256': hashlib.sha256((source / 'bun.lock').read_bytes()).hexdigest(),
    'patch_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((root / 'enterprise-patches/patches').glob('*.patch'))},
    'production_acceptance': 'pending: signed private evaluation and customer approval of exact deployment',
    'private_eval_execution': 'not run by public CI',
    'mvp_toolkit': 'enterprise-mvp-toolkit.tar.gz',
}
(output / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
files = sorted(p for p in output.iterdir() if p.is_file())
(output / 'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in files))
