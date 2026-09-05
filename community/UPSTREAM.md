# Public upstream maintenance

The public patch series is applied to an exact OpenCode commit in
[BASE_COMMIT](../enterprise-patches/BASE_COMMIT). It is the common source for community
and customer builds. Private GitLab does not run a competing upstream merge stream.

## Inspect a new candidate

From a clean public distribution checkout, with Python 3.11+ and git:

```bash
python3 enterprise-patches/ci/upstream.py --output /tmp/opencode-upstream-check
```

This resolves the latest published stable upstream release tag to a full commit SHA,
verifies the current patch inventory and applies the series in a disposable worktree.
To check a specific reviewed full commit instead, add `--candidate <40-character-SHA>`.
The output directory must not already exist.

Results:

- `unchanged`: latest candidate equals the pinned baseline.
- `patches_apply`: `report.json` records the compared commits and resulting source
  tree; `candidate.patch` updates only BASE_COMMIT and its checksum.
- `conflict`: nonzero exit with a public conflict report. No baseline update patch is
  created. Fetch/validation failures also fail the command, not report "up to date".

The tool neither builds upstream code nor approves it. Patch applicability is not
security, compatibility or private acceptance. It does not modify the active baseline,
merge a branch, create a PR or access private GitLab.

After reviewing a clean candidate:

```bash
git switch -c upstream-refresh
git apply --check /tmp/opencode-upstream-check/candidate.patch
git apply /tmp/opencode-upstream-check/candidate.patch
```

Read the upstream diff using the `compare_url` in the report. Review policy, auth,
network, tool execution, telemetry, dependency and licence changes even when every
patch applies. Run enterprise regression/typechecks/build/smoke gates; add public
regressions for new behavior. The report's patched-tree identity belongs in the PR
and should match the build result. Human maintainers then commit and open the update PR.

Do not auto-apply an old candidate file onto a changed patch series. Re-run the check
on the current distribution commit before review. A malicious local artifact is not
trusted merely because it is named `candidate.patch`.

## Public scheduled check

[Upstream workflow](../.github/workflows/upstream-check.yml) runs unit tests on PRs and
checks upstream on a Monday schedule or manual dispatch. It uses hosted disposable
runners, read-only repository permissions, no customer credentials and no private CI
trigger. Only the report and optional update patch become workflow artifacts.

The schedule becomes active only after the workflow reaches the default branch.
A fork may require Actions to be enabled. The existing conversational weekly security
review remains a separate analysis task; this workflow mechanically checks patch
applicability. Neither performs automatic production rollout.

We deliberately start with a reviewed patch artifact and maintainer-created PR. If a
publisher bot is introduced, isolate its write token from candidate execution and
ensure the resulting PR runs required CI. GitHub documents special approval behavior
for PR events created using GITHUB_TOKEN; do not assume a pushed bot branch has been
validated. See [GitHub workflow triggering](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

## Adding, refreshing and retiring patches

The series is no longer limited to four entries. Names must be unique, contiguous
and ordered, for example `0001-single-model-policy.patch` through
`0005-describe-the-fix.patch`; every patch file must appear in `patches/series`.
Checksum validation rejects omitted, duplicated, reordered or tampered required inputs.

Work on the patched baseline produced by `ci/prepare.py`, not on the preserved upstream
source at the distribution repository root. Add a focused commit plus regression in
that worktree, then export the new commit as the next numbered patch. Regenerate the
whole series from the pinned baseline if earlier commits need editing. Preserve authors,
licences and notices; record any upstream PR/commit in the public change description.

After intentionally changing package files:

```bash
python3 enterprise-patches/ci/series.py --refresh
cd enterprise-patches/ci
python3 -m unittest discover -s tests -v
```

Checksum refresh records bytes for review; it is not a signature or approval. Keep
customer files out of the public checkout before refreshing or staging files.

Prefer contributing generic fixes upstream. Once an upstream version contains the
fix, remove the redundant downstream patch, renumber the remaining series and retain
an appropriate public regression if it still protects a supported boundary. Security
profile changes remain downstream where their purpose differs from upstream defaults.
Supported customer release lines may still need deliberate backports; this is separate
from avoiding a divergent private product fork.
