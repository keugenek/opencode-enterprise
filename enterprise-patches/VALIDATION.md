# Validation record — 2026-09-05

- Upstream tag: v1.18.29.
- Baseline: 16747470f976aca3d362ad730bcd3fe82ecc2c9a.
- Patched source commit: 0b5eadc (local enterprise-guardrails branch).
- Four git-format-patch files applied successfully with git am to a clean baseline worktree.
- Source and reapplied tree hashes match: 43bc663750520fe563d376dec238ed6cdb2ec02b.
- Source git status is clean; git diff --check passed before final commit.
- Bun 1.3.14: 32 tests passed, 0 failed, 52 assertions.
- Typechecks: packages/core, packages/opencode, packages/tui passed.
- Linux x64 binary build passed; version smoke test: 0.0.0-enterprise-guardrails-202609051200.
- Compiled binary models output: enterprise/enterprise-coder.
- Source CLI ignored injected cloud provider/model OPENCODE_CONFIG_CONTENT.

No real internal inference endpoint was supplied. No container deployment, network-flow capture,
image vulnerability scan, independent penetration test or end-to-end tool calling run is claimed.
See ACCEPTANCE.md for deployment gates. The patch series is published as files in keugenek/opencode-enterprise; apply it to the exact baseline before building.
