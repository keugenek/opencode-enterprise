"""Public synthetic tests for patch inventory and upstream update preparation."""
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import series
import upstream


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.package = pathlib.Path(self.tmp.name) / 'enterprise-patches'
        (self.package / 'patches').mkdir(parents=True)
        (self.package / 'BASE_COMMIT').write_text('1' * 40 + '\n')
        self.names = [f'{n:04d}-test.patch' for n in range(1, 7)]
        for name in self.names:
            (self.package / 'patches' / name).write_text('synthetic patch ' + name)
        (self.package / 'patches/series').write_text('\n'.join(self.names) + '\n')
        series.refresh(self.package)

    def test_more_than_four_patches_supported(self):
        self.assertEqual(len(series.read_series(self.package)), 6)

    def test_empty_gap_duplicate_and_traversal_fail(self):
        for names in [[], [self.names[1]], [self.names[0]] * 2, ['../../secret.patch']]:
            with self.subTest(names=names):
                (self.package / 'patches/series').write_text('\n'.join(names))
                series.refresh(self.package)
                with self.assertRaises(ValueError): series.read_series(self.package)

    def test_tampered_patch_rejected(self):
        (self.package / 'patches' / self.names[0]).write_text('changed')
        with self.assertRaises(ValueError): series.read_series(self.package)

    def test_unlisted_patch_rejected(self):
        (self.package / 'patches/0007-extra.patch').write_text('unlisted')
        series.refresh(self.package)
        with self.assertRaises(ValueError): series.read_series(self.package)

    def test_missing_required_checksum_rejected(self):
        p = self.package / 'SHA256SUMS'
        p.write_text('\n'.join(line for line in p.read_text().splitlines() if not line.endswith('  BASE_COMMIT')) + '\n')
        with self.assertRaises(ValueError): series.read_series(self.package)

    def test_duplicate_and_traversal_checksum_rejected(self):
        p = self.package / 'SHA256SUMS'; original = p.read_text()
        for extra in [original.splitlines()[0], '0' * 64 + '  ../outside']:
            p.write_text(original + extra + '\n')
            with self.subTest(extra=extra), self.assertRaises(ValueError): series.read_series(self.package)

    def test_patch_symlink_rejected(self):
        p = self.package / 'patches' / self.names[0]
        p.unlink(); p.symlink_to(self.package / 'BASE_COMMIT')
        with self.assertRaises(ValueError): series.read_series(self.package)

    def test_candidate_patch_updates_only_baseline_and_checksum(self):
        root = pathlib.Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        before = (self.package / 'BASE_COMMIT').read_bytes()
        candidate = '2' * 40
        diff = upstream.candidate_diff(self.package, candidate)
        self.assertEqual((self.package / 'BASE_COMMIT').read_bytes(), before)
        result = subprocess.run(['git', 'apply', '--check', '-'], input=diff, text=True, cwd=root, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        subprocess.run(['git', 'apply', '-'], input=diff, text=True, cwd=root, check=True)
        self.assertEqual((self.package / 'BASE_COMMIT').read_text(), candidate + '\n')
        self.assertEqual(len(series.read_series(self.package)), 6)
        self.assertEqual(diff.count('--- a/'), 2)


class UpstreamTests(unittest.TestCase):
    def test_stable_release_selection_rejects_untrusted_metadata(self):
        valid = {'tag_name': 'v1.18.29', 'draft': False, 'prerelease': False}
        self.assertEqual(upstream.release_tag(valid), 'v1.18.29')
        for change in [{'draft': True}, {'prerelease': True}, {'tag_name': 'v1.2.3-rc.1'},
                       {'tag_name': '--upload-pack=evil'}, {'tag_name': 'v1.2.3\ncommand'}, {'draft': 0}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                upstream.release_tag(dict(valid, **change))

    def test_annotated_tag_uses_commit_not_tag_object(self):
        output = '1' * 40 + '\trefs/tags/v1.2.3\n' + '2' * 40 + '\trefs/tags/v1.2.3^{}\n'
        self.assertEqual(upstream.resolve_tag(output, 'v1.2.3'), '2' * 40)
        self.assertEqual(upstream.resolve_tag(output.splitlines()[0], 'v1.2.3'), '1' * 40)

    def test_wrong_missing_duplicate_and_invalid_tag_records_fail(self):
        line = '1' * 40 + '\trefs/tags/v1.2.3\n'
        for output in ['', line + line, 'x\trefs/tags/v1.2.3', '1' * 40 + '\trefs/tags/v9.9.9']:
            with self.subTest(output=output), self.assertRaises(ValueError):
                upstream.resolve_tag(output, 'v1.2.3')

    def test_real_patch_application_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp); repo = root / 'repo'
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            upstream.git(repo, 'config', 'user.name', 'Synthetic test')
            upstream.git(repo, 'config', 'user.email', 'test@localhost')
            (repo / 'policy.txt').write_text('original\n')
            upstream.git(repo, 'add', '.'); upstream.git(repo, 'commit', '-qm', 'baseline')
            baseline = upstream.git(repo, 'rev-parse', 'HEAD')
            (repo / 'policy.txt').write_text('restricted\n')
            upstream.git(repo, 'commit', '-qam', 'restrict policy')
            patch = root / '0001-policy.patch'
            patch.write_text(upstream.git(repo, 'format-patch', '-1', '--stdout') + '\n')
            upstream.git(repo, 'checkout', '--detach', baseline)
            (repo / 'unrelated.txt').write_text('update\n')
            upstream.git(repo, 'add', '.'); upstream.git(repo, 'commit', '-qm', 'unrelated upstream update')
            candidate = upstream.git(repo, 'rev-parse', 'HEAD')
            result = upstream.apply_candidate(repo, candidate, [patch], root / 'clean')
            self.assertEqual(result['status'], 'patches_apply')
            self.assertEqual((root / 'clean/policy.txt').read_text(), 'restricted\n')
            self.assertEqual(upstream.git(repo, 'rev-parse', 'HEAD'), candidate)
            (repo / 'policy.txt').write_text('conflicting upstream change\n')
            upstream.git(repo, 'commit', '-qam', 'conflict')
            conflict = upstream.git(repo, 'rev-parse', 'HEAD')
            result = upstream.apply_candidate(repo, conflict, [patch], root / 'conflict')
            self.assertEqual(result['status'], 'conflict')
            self.assertEqual((root / 'conflict/policy.txt').read_text(), 'conflicting upstream change\n')
            self.assertEqual(upstream.git(root / 'conflict', 'status', '--porcelain'), '')
            with self.assertRaises(ValueError):
                upstream.apply_candidate(repo, candidate, [patch], root / 'clean')
            with self.assertRaises(ValueError):
                upstream.apply_candidate(repo, '--bad-ref', [patch], root / 'new')


if __name__ == '__main__':
    unittest.main()
