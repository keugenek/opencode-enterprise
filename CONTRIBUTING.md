# Contributing to the independent enterprise distribution

Common hardening patches, configuration schemas, build/CI tools and regression tests
are developed in this public repository. Community contributions and public software
use do not require an enterprise support contract. The current candidate is Linux
x64/glibc AVX2 CLI/TUI with one fixed internal model.

Start with [the development model](community/DEVELOPMENT-MODEL.md) and
[upstream maintenance](community/UPSTREAM.md). For changes to upstream OpenCode itself,
follow [its contribution guide](https://github.com/anomalyco/opencode/blob/dev/CONTRIBUTING.md).
This fork's supported enterprise profile has different defaults and acceptance needs.

## Useful contributions

- Minimal, reproducible fixes for the supported CLI/model/runtime profile.
- Public negative regressions for configuration bypass, provider routing, transport,
  telemetry, permissions and deployment tooling.
- Patch portability, CI/build reliability, offline installation and documentation.
- Generic gateway/configuration integration with synthetic examples and clear boundaries.
- Reviewed upstream updates and removal of patches already incorporated upstream.

Discuss changes that expand the supported profile before implementing them. Adding a
cloud provider, re-enabling arbitrary plugins or weakening policy enforcement is not
an ordinary compatibility fix. Open a short public issue for design decisions; a focused
bugfix with a complete reproduction can be proposed directly as a PR.

## Reproduce and implement

Use the [enterprise build instructions](enterprise-patches/README.md). The root upstream
source is preserved for patch development; editing/building it directly does not apply
the enterprise series. Prepare a separate source worktree:

```bash
python3 enterprise-patches/ci/prepare.py /tmp/opencode-contribution
```

Make shared runtime changes and their regression tests in that patched worktree, export
the commit as a numbered `.patch` file, and update the public series/checksums following
[the patch workflow](community/UPSTREAM.md#adding-refreshing-and-retiring-patches).
MVP tooling, public CI and documentation changes are made directly in their public paths.

Run tests from the relevant package directory, following [AGENTS.md](AGENTS.md). Public
CI runs maintenance-tool tests, MVP tests, directed patched-runtime regressions, typechecks,
build and binary smoke checks. Provide the commands/results relevant to your change;
a failed check needs investigation, not a skipped assertion or relaxed policy.

## Pull requests

Keep the diff focused. State the observable problem, reproduction, expected behavior,
why the change works and how it was checked. Include upstream applicability and any
remaining risks. Retain authorship and third-party notices and ensure you have the
right to contribute the material under its applicable repository licence. No blanket
copyright transfer or proprietary licence for existing public contributions is introduced.
AI-assisted submissions need the same ownership, explanation and review as other work.

Public review considers the supported profile, correctness, meaningful regression,
maintainability and licensing. The private held-out eval is not required to develop an
ordinary public fix. Customer promotion has an additional private acceptance process.
Maintainers may request changes or decline work outside the supported scope; no response
SLA is implied for community support.

## Sensitive bugs and customer reports

Do not use `/share` or attach customer logs, code, prompts, screenshots, hostnames,
credentials or private eval cases to a public issue. Use
[private security reporting](assurance/REPORTING.md) for vulnerabilities or the contracted
GitLab/support channel for customer-specific material.

A maintainer can turn an approved, sanitized reproduction into a public issue and PR.
The common fix starts in the public source tree and is consumed by private delivery
at its merged commit. Confidential vulnerabilities follow the temporary embargo and
coordinated-disclosure exception in [the development model](community/DEVELOPMENT-MODEL.md).
