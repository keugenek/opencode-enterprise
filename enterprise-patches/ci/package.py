#!/usr/bin/env python3
"""Package a tested console or native desktop candidate with exact source identity."""
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile

root = pathlib.Path(__file__).resolve().parents[2]
source = pathlib.Path(sys.argv[1]).resolve()
output = pathlib.Path(sys.argv[2]).resolve()
version = os.environ['OPENCODE_VERSION']
if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?', version):
    raise SystemExit('Invalid artifact version')
target = os.environ.get('ENTERPRISE_TARGET', 'linux-x64')
if target not in ('linux-x64', 'windows-x64'):
    raise SystemExit('Unsupported enterprise target')
profile = os.environ.get('ENTERPRISE_PROFILE', 'console')
if profile not in ('console', 'desktop') or (profile == 'desktop' and target != 'windows-x64'):
    raise SystemExit('Unsupported enterprise profile/target')
identity = f'{profile}-{target}'
windows = target == 'windows-x64'
desktop = profile == 'desktop'
executable = 'opencode.exe' if windows else 'opencode'
name = f'opencode-enterprise-{"desktop-" if desktop else ""}{version}-{target}'
installer_name = f'opencode-enterprise-desktop-{version}-win-x64.exe' if desktop else None
portable_name = f'{name}-portable.zip' if desktop else None
screenshot = os.environ.get('ENTERPRISE_DESKTOP_SCREENSHOT') if desktop else None
screenshot_name = f'desktop-smoke-{target}.png' if screenshot else None
report = pathlib.Path(screenshot).with_suffix('.json') if screenshot else None
report_name = f'desktop-smoke-{target}.json' if screenshot else None

# Reject incomplete or wrong-version Electron builds before publishing any output.
if desktop:
    desktop_dist = source / 'packages/desktop/dist'
    required = [desktop_dist / installer_name,
                desktop_dist / 'win-unpacked/resources/app.asar',
                desktop_dist / 'win-unpacked/OpenCode Enterprise Desktop.exe']
    for path in required:
        if not path.is_file():
            raise SystemExit(f'Missing desktop build input: {path}')
    for path in (desktop_dist / 'win-unpacked').rglob('*'):
        if path.is_symlink():
            raise SystemExit(f'Desktop bundle must not contain symlinks: {path}')
if screenshot and not pathlib.Path(screenshot).is_file():
    raise SystemExit('Desktop smoke screenshot does not exist')
if report:
    if not report.is_file():
        raise SystemExit('Desktop smoke report does not exist')
    evidence = json.loads(report.read_text())
    if not isinstance(evidence, dict) or evidence.get('passed') is not True:
        raise SystemExit('Desktop smoke report does not record a passing check')

output.mkdir(parents=True, exist_ok=False)
staging = output / name
if desktop:
    shutil.copytree(desktop_dist / 'win-unpacked', staging)
    shutil.copy2(desktop_dist / installer_name, output / installer_name)
    # Preserve Electron's licence/third-party notices already in the unpacked bundle.
    shutil.copy2(source / 'LICENSE', staging / 'OPENCODE-LICENSE')
    shutil.copy2(root / 'delivery/DESKTOP.md', staging / 'DESKTOP.md')
else:
    staging.mkdir()
    shutil.copy2(source / f'packages/opencode/dist/opencode-{target}/bin' / executable, staging / executable)
    shutil.copy2(source / 'LICENSE', staging / 'LICENSE')
shutil.copytree(source / 'enterprise', staging / 'enterprise')
(staging / 'INSTALL.txt').write_text(
    'Native Windows x64 Electron desktop candidate. Read DESKTOP.md.\n'
    'The complete portable directory is required; do not extract only its EXE.\n'
    'The installer and portable build include the renderer, Electron runtime and enterprise engine.\n'
    'Install protected enterprise policy separately; use a standard developer account.\n'
    'Unsigned public CI candidate. Private evaluation and customer acceptance have not been performed.\n'
    if desktop else
    'Windows x64 AVX2. Read enterprise/windows/README.md. Administrator-managed NTFS policy required.\n'
    if windows else
    'Linux x64/glibc (AVX2). Requires an administrator-installed /etc/opencode/enterprise.json.\n'
    'Read enterprise/README.md and ACCEPTANCE.md. No endpoint credentials are embedded.\n'
    'This prerelease has not passed production vLLM/network acceptance gates.\n')
if windows:
    with zipfile.ZipFile(output / (portable_name or name + '.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(staging.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(output))
else:
    with tarfile.open(output / (name + '.tar.gz'), 'w:gz') as archive:
        archive.add(staging, arcname=name)
shutil.rmtree(staging)
subprocess.run(['git', 'archive', '--format=tar.gz', '-o', str(output / f'enterprise-patches-{identity}.tar.gz'),
                'HEAD', 'enterprise-patches'], cwd=root, check=True)
# Archive only committed public paths, never customer working files, keys or caches.
subprocess.run(['git', 'archive', '--format=tar.gz', '--prefix=opencode-enterprise-toolkit/',
                '-o', str(output / f'enterprise-mvp-toolkit-{identity}.tar.gz'), 'HEAD',
                'mvp', 'assurance', 'delivery', 'enterprise-patches', 'README.md',
                'ENTERPRISE.md', 'LICENSING.md', 'LICENSE', 'CONTRIBUTING.md', 'community',
                '.github/workflows/upstream-check.yml', '.github/workflows/enterprise-release.yml',
                '.github/workflows/mvp-validation.yml'], cwd=root, check=True)
subprocess.run(['git', 'archive', '--format=tar.gz', '--prefix=opencode-enterprise-source/',
                '-o', str(output / f'patched-source-{identity}.tar.gz'), 'HEAD'], cwd=source, check=True)
if screenshot:
    shutil.copy2(screenshot, output / screenshot_name)
    shutil.copy2(report, output / report_name)


def git(path, ref):
    return subprocess.check_output(['git', 'rev-parse', ref], cwd=path).decode().strip()


manifest = {
    'version': version,
    'profile': profile,
    'identity': identity,
    'desktop_installer': installer_name,
    'desktop_portable': portable_name,
    'desktop_smoke_screenshot': screenshot_name,
    'desktop_smoke_report': report_name,
    'signing': 'unsigned public CI candidate',
    'electron_version': json.loads((source / 'packages/desktop/package.json').read_text())['devDependencies']['electron'] if desktop else None,
    'distribution_commit': git(root, 'HEAD'),
    'baseline_commit': (root / 'enterprise-patches/BASE_COMMIT').read_text().strip(),
    'patched_source_tree': git(source, 'HEAD^{tree}'),
    'bun_version': subprocess.check_output(['bun', '--version']).decode().strip(),
    'target': 'windows-x64' if desktop else 'windows-x64-avx2' if windows else 'linux-x64-glibc-avx2',
    'workflow_run': os.environ.get('GITHUB_RUN_ID'),
    'lockfile_sha256': hashlib.sha256((source / 'bun.lock').read_bytes()).hexdigest(),
    'patch_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((root / 'enterprise-patches/patches').glob('*.patch'))},
    'production_acceptance': 'pending: signed private evaluation and customer approval of exact deployment',
    'private_eval_execution': 'not run by public CI',
    'mvp_toolkit': f'enterprise-mvp-toolkit-{identity}.tar.gz',
}
(output / f'build-manifest-{identity}.json').write_text(json.dumps(manifest, indent=2) + '\n')
files = sorted(p for p in output.iterdir() if p.is_file())
(output / f'SHA256SUMS-{identity}').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in files))
