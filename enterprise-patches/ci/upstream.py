#!/usr/bin/env python3
"""Prepare a public upstream compatibility report and reviewable baseline update."""
import argparse
import difflib
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.request
from series import read_series

UPSTREAM = 'https://github.com/anomalyco/opencode.git'
API = 'https://api.github.com/repos/anomalyco/opencode/releases/latest'


def git(repo, *args):
    return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', *args],
                                   cwd=repo, stderr=subprocess.PIPE, timeout=120).decode().strip()


def release_tag(data):
    if not isinstance(data, dict):
        raise ValueError('Expected release metadata object')
    tag = data.get('tag_name')
    if (data.get('draft') is not False or data.get('prerelease') is not False
            or not isinstance(tag, str) or not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', tag)):
        raise ValueError('Expected a published stable upstream release')
    return tag


def resolve_tag(output, tag):
    allowed = {'refs/tags/' + tag, 'refs/tags/' + tag + '^{}'}
    refs = {}
    for line in output.splitlines():
        value, name = line.split()
        if name not in allowed or name in refs or not re.fullmatch(r'[0-9a-f]{40}', value):
            raise ValueError('Unexpected upstream tag resolution')
        refs[name] = value
    if 'refs/tags/' + tag not in refs:
        raise ValueError('Upstream tag not found')
    return refs.get('refs/tags/' + tag + '^{}', refs['refs/tags/' + tag])


def latest(repo):
    request = urllib.request.Request(API, headers={'Accept': 'application/vnd.github+json',
                                                 'User-Agent': 'opencode-enterprise-upstream-check'})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError('Upstream release metadata too large')
    tag = release_tag(json.loads(raw))
    output = git(repo, 'ls-remote', '--tags', UPSTREAM, 'refs/tags/' + tag, 'refs/tags/' + tag + '^{}')
    return tag, resolve_tag(output, tag)


def apply_candidate(repo, candidate, patches, target):
    if not re.fullmatch(r'[0-9a-f]{40}', candidate):
        raise ValueError('Expected a full candidate commit SHA')
    target = pathlib.Path(target)
    if target.exists():
        raise ValueError('Candidate worktree already exists')
    git(repo, 'cat-file', '-e', candidate + '^{commit}')
    git(repo, 'worktree', 'add', '--detach', str(target), candidate)
    # Apply exact hunks: no automatic three-way conflict resolution or hooks.
    result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=Enterprise candidate',
                             '-c', 'user.email=candidate@localhost', 'am', *[str(p) for p in patches]],
                            cwd=target, capture_output=True, text=True, timeout=120)
    if result.returncode:
        git(target, 'am', '--abort')
        return {'status': 'conflict', 'detail': (result.stdout + result.stderr)[-8000:]}
    return {'status': 'patches_apply', 'patched_tree': git(target, 'rev-parse', 'HEAD^{tree}')}


def candidate_diff(package, candidate):
    if not re.fullmatch(r'[0-9a-f]{40}', candidate):
        raise ValueError('Expected a full candidate commit SHA')
    old_base = (package / 'BASE_COMMIT').read_text()
    new_base = candidate + '\n'
    old_sums = (package / 'SHA256SUMS').read_text()
    lines = old_sums.splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines) if line.rstrip('\n').endswith('  BASE_COMMIT')]
    if len(matches) != 1:
        raise ValueError('Expected one baseline checksum')
    lines[matches[0]] = hashlib.sha256(new_base.encode()).hexdigest() + '  BASE_COMMIT\n'
    text = ''
    for name, before, after in [('BASE_COMMIT', old_base, new_base), ('SHA256SUMS', old_sums, ''.join(lines))]:
        text += ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                 fromfile='a/enterprise-patches/' + name, tofile='b/enterprise-patches/' + name))
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', help='Explicit full upstream SHA; otherwise resolve the latest stable release')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[2]
    package = root / 'enterprise-patches'
    patches = read_series(package)
    base = (package / 'BASE_COMMIT').read_text().strip()
    if not re.fullmatch(r'[0-9a-f]{40}', base):
        raise ValueError('Invalid current baseline')
    tag, candidate = ('explicit-commit', args.candidate) if args.candidate else latest(root)
    if not re.fullmatch(r'[0-9a-f]{40}', candidate):
        raise ValueError('Expected a full candidate commit SHA')
    output = pathlib.Path(args.output).resolve()
    output.mkdir(mode=0o700, exist_ok=False)
    report = {'baseline': base, 'candidate': candidate, 'release': tag,
              'distribution_commit': git(root, 'rev-parse', 'HEAD'),
              'distribution_dirty': bool(git(root, 'status', '--porcelain')),
              'package_inventory_sha256': hashlib.sha256((package / 'SHA256SUMS').read_bytes()).hexdigest(),
              'compare_url': f'https://github.com/anomalyco/opencode/compare/{base}...{candidate}',
              'production_acceptance': 'not_evaluated', 'status': 'unchanged'}
    if candidate != base:
        git(root, 'fetch', '--depth=1', '--no-tags', UPSTREAM, candidate)
        report.update(apply_candidate(root, candidate, patches, output / 'source'))
        if report['status'] == 'patches_apply':
            (output / 'candidate.patch').write_text(candidate_diff(package, candidate))
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if report['status'] == 'conflict':
        return 1
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('Upstream check failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
