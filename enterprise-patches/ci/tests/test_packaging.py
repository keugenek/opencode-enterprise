"""Exercise real release packaging with committed synthetic repositories."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile


@unittest.skipIf(os.name == 'nt', 'Synthetic Bun executable uses a POSIX shell')
class PackagingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = pathlib.Path(temporary.name)
        self.distribution = self.base / 'distribution'
        self.source = self.base / 'source'
        tool = self.base / 'bin'
        tool.mkdir()
        (tool / 'bun').write_text('#!/bin/sh\nprintf "1.3.14\\n"\n')
        (tool / 'bun').chmod(0o755)
        self.script = self.distribution / 'enterprise-patches/ci/package.py'
        self.script.parent.mkdir(parents=True)
        shutil.copy2(pathlib.Path(__file__).resolve().parents[1] / 'package.py', self.script)
        public_paths = ['enterprise-patches/BASE_COMMIT', 'enterprise-patches/patches/0001-test.patch',
                        'mvp/README.md', 'assurance/README.md', 'delivery/DESKTOP.md', 'README.md',
                        'ENTERPRISE.md', 'LICENSING.md', 'LICENSE', 'CONTRIBUTING.md', 'community/README.md',
                        '.github/workflows/upstream-check.yml', '.github/workflows/enterprise-release.yml',
                        '.github/workflows/mvp-validation.yml']
        for name in public_paths:
            file = self.distribution / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('1' * 40 if name.endswith('BASE_COMMIT') else 'public fixture\n')
        self.desktop = self.source / 'packages/desktop/dist'
        for name in ['LICENSE', 'bun.lock', 'enterprise/README.md',
                     'packages/opencode/dist/opencode-linux-x64/bin/opencode',
                     'packages/opencode/dist/opencode-windows-x64/bin/opencode.exe',
                     'packages/desktop/dist/opencode-enterprise-desktop-0.0.0-ci.1-win-x64.exe',
                     'packages/desktop/dist/win-unpacked/OpenCode Enterprise Desktop.exe',
                     'packages/desktop/dist/win-unpacked/resources/app.asar',
                     'packages/desktop/dist/win-unpacked/resources/app.asar.unpacked/native/addon.node',
                     'packages/desktop/dist/win-unpacked/locales/en-US.pak',
                     'packages/desktop/dist/win-unpacked/LICENSE',
                     'packages/desktop/dist/win-unpacked/LICENSES.chromium.html']:
            file = self.source / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(name + '\n')
        (self.source / 'packages/desktop/package.json').write_text(json.dumps({'devDependencies': {'electron': '42.3.3'}}))
        for repo in [self.distribution, self.source]:
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            subprocess.run(['git', 'add', '.'], cwd=repo, check=True)
            subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@localhost',
                            'commit', '-qm', 'public fixtures'], cwd=repo, check=True)
        (self.distribution / 'delivery/private-customer.txt').write_text('must not ship\n')
        self.screenshot = self.base / 'desktop-smoke.png'
        self.screenshot.write_bytes(b'public synthetic screenshot fixture')
        self.screenshot.with_suffix('.json').write_text(json.dumps({
            'passed': True, 'checks': ['synthetic fixture'], 'limitations': ['private eval not run'],
        }))
        self.env = dict(os.environ, OPENCODE_VERSION='0.0.0-ci.1',
                        PATH=str(tool) + os.pathsep + os.environ['PATH'])
        self.env.pop('ENTERPRISE_DESKTOP_SCREENSHOT', None)

    def package(self, profile, target, screenshot=False):
        output = self.base / f'{profile}-{target}'
        env = dict(self.env, ENTERPRISE_PROFILE=profile, ENTERPRISE_TARGET=target)
        if screenshot:
            env['ENTERPRISE_DESKTOP_SCREENSHOT'] = str(self.screenshot)
        result = subprocess.run([sys.executable, str(self.script), str(self.source), str(output)],
                                env=env, capture_output=True, text=True)
        return result, output

    def test_all_profiles_have_disjoint_assets_and_exact_hashes(self):
        names = set()
        for profile, target in [('console', 'linux-x64'), ('console', 'windows-x64'), ('desktop', 'windows-x64')]:
            with self.subTest(profile=profile, target=target):
                result, output = self.package(profile, target, screenshot=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                current = {file.name for file in output.iterdir()}
                self.assertFalse(names & current, 'Release profiles would overwrite each other')
                names.update(current)
                manifest = json.loads(next(output.glob('build-manifest-*.json')).read_text())
                self.assertEqual(manifest['identity'], f'{profile}-{target}')
                self.assertEqual(manifest['profile'], profile)
                self.assertEqual(bool(manifest['desktop_smoke_screenshot']), profile == 'desktop')
                self.assertEqual(bool(manifest['desktop_smoke_report']), profile == 'desktop')
                self.assertEqual(manifest['production_acceptance'].split(':')[0], 'pending')
                self.assertEqual(manifest['private_eval_execution'], 'not run by public CI')
                self.assertIn('unsigned', manifest['signing'])
                checksum_lines = next(output.glob('SHA256SUMS-*')).read_text().splitlines()
                self.assertEqual(len(checksum_lines), len(current) - 1)
                for line in checksum_lines:
                    digest, filename = line.split('  ')
                    self.assertEqual(digest, hashlib.sha256((output / filename).read_bytes()).hexdigest())
                with tarfile.open(output / manifest['mvp_toolkit']) as archive:
                    self.assertFalse(any('private-customer' in name for name in archive.getnames()))
                if profile == 'desktop':
                    self.assertEqual(manifest['electron_version'], '42.3.3')
                    self.assertEqual(manifest['target'], 'windows-x64')
                    self.assertTrue(json.loads((output / manifest['desktop_smoke_report']).read_text())['passed'])
                    self.assertEqual((output / manifest['desktop_installer']).read_bytes(),
                                     (self.desktop / manifest['desktop_installer']).read_bytes())
                    with zipfile.ZipFile(output / manifest['desktop_portable']) as archive:
                        members = archive.namelist()
                        for suffix in ['/OpenCode Enterprise Desktop.exe', '/resources/app.asar',
                                       '/resources/app.asar.unpacked/native/addon.node', '/locales/en-US.pak',
                                       '/LICENSES.chromium.html', '/DESKTOP.md', '/enterprise/README.md']:
                            self.assertTrue(any(name.endswith(suffix) for name in members), suffix)
                        electron_license = next(name for name in members if name.endswith('/LICENSE'))
                        opencode_license = next(name for name in members if name.endswith('/OPENCODE-LICENSE'))
                        self.assertEqual(archive.read(electron_license),
                                         (self.desktop / 'win-unpacked/LICENSE').read_bytes())
                        self.assertEqual(archive.read(opencode_license), (self.source / 'LICENSE').read_bytes())
                elif target == 'windows-x64':
                    with zipfile.ZipFile(next(output.glob('opencode-enterprise-*.zip'))) as archive:
                        self.assertTrue(any(name.endswith('/opencode.exe') for name in archive.namelist()))
                else:
                    with tarfile.open(next(output.glob('opencode-enterprise-*.tar.gz'))) as archive:
                        self.assertTrue(any(name.endswith('/opencode') for name in archive.getnames()))

    def test_desktop_requires_the_exact_versioned_installer(self):
        (self.desktop / 'opencode-enterprise-desktop-0.0.0-ci.1-win-x64.exe').rename(self.desktop / 'stale-installer.exe')
        result, output = self.package('desktop', 'windows-x64')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing desktop build input', result.stderr)
        self.assertFalse(output.exists())

    def test_desktop_requires_its_packaged_application(self):
        (self.desktop / 'win-unpacked/resources/app.asar').unlink()
        result, output = self.package('desktop', 'windows-x64')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('app.asar', result.stderr)
        self.assertFalse(output.exists())

    def test_desktop_rejects_symlinked_bundle_files(self):
        (self.desktop / 'win-unpacked/private-link').symlink_to(self.distribution / 'delivery/private-customer.txt')
        result, output = self.package('desktop', 'windows-x64')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('must not contain symlinks', result.stderr)
        self.assertFalse(output.exists())

    def test_unsupported_profiles_and_targets_fail_before_packaging(self):
        for profile, target in [('desktop', 'linux-x64'), ('web', 'linux-x64'), ('console', 'windows-arm64')]:
            with self.subTest(profile=profile, target=target):
                result, output = self.package(profile, target)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())

    def test_missing_requested_screenshot_is_not_silently_omitted(self):
        self.screenshot.unlink()
        result, output = self.package('desktop', 'windows-x64', screenshot=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('screenshot does not exist', result.stderr)
        self.assertFalse(output.exists())

    def test_optional_screenshot_is_not_claimed_when_not_supplied(self):
        result, output = self.package('desktop', 'windows-x64')
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(next(output.glob('build-manifest-*.json')).read_text())
        self.assertIsNone(manifest['desktop_smoke_screenshot'])
        self.assertIsNone(manifest['desktop_smoke_report'])
        self.assertFalse(list(output.glob('*.png')))

    def test_requested_smoke_evidence_requires_a_passing_report(self):
        report = self.screenshot.with_suffix('.json')
        for data in [None, {'passed': False}, {'checks': []}]:
            with self.subTest(data=data):
                if data is None:
                    report.unlink()
                else:
                    report.write_text(json.dumps(data))
                result, output = self.package('desktop', 'windows-x64', screenshot=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Desktop smoke report', result.stderr)
                self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
