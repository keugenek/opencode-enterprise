# Enterprise delivery playbook

Public planning and operating templates for a paid, customer-specific deployment.
The executable installer preparation and report verifier are in [mvp/](../mvp/README.md).
This playbook is not an executed contract or a production certificate.
Keep completed customer records, commercial terms and internal maintenance technology
in private systems. No customer environment is configured by adding these files.

## Start here

1. Agree scope and responsibility using [PILOT.md](PILOT.md).
2. Complete the [customer profile](templates/customer-profile.example.json) privately.
3. Work through [ROADMAP.md](ROADMAP.md) in dependency order.
4. Implement the boundaries in [ARCHITECTURE.md](ARCHITECTURE.md).
5. Follow the [operator runbook](OPERATOR-RUNBOOK.md), record
   [acceptance evidence](templates/ACCEPTANCE-RECORD.md), then issue the
   [developer quickstart](DEVELOPER-QUICKSTART.md).
6. Operate the accepted release using [MAINTENANCE.md](MAINTENANCE.md) and the
   private [bug report template](templates/BUG-REPORT.md).

## Current implementation boundary

| Area | Current implementation boundary |
|---|---|
| Four patch files on exact v1.18.29 baseline | Implemented; application and matching source tree verified |
| Directed regression tests, typechecks, Linux x64 build and smoke checks | Implemented; enterprise workflow previously passed |
| Packaging, manifest and SHA-256 checks | Implemented |
| Tag-triggered GitHub prerelease job | Configured; actual tag publication not yet verified |
| Kubernetes runtime / Dockerfile | Executable profile validation, verified binary image context and restricted per-workspace manifests in the MVP toolkit; customer deployment remains unverified |
| Single-model gateway with workload identity | Required interface documented; not implemented here |
| Persistent workspace/state | Per-workspace PVC manifests implemented; encrypted storage, backup and restore require customer verification |
| SSO access, broker provisioning and offboarding | Customer integration required |
| Private evaluation | Offline signed-report verifier and public process implemented; private corpus/runner, signer service and actual evaluation remain required |
| Actual vLLM tool calling, network and cross-user isolation acceptance | Not yet completed |
| Signing, SBOM and final image scanning | Required production work; not supplied by checksum generation |
| Private automated remediation and upstream integration service | Planned; implementation belongs in a private repository |

The MVP tooling has its own public regression suite. Its synthetic reports do not
establish private evaluation results or extend the patched CLI test coverage.
Use the current Actions run for actual pipeline status.

## First deployment decision

Start with one customer, one project/toolchain, one fixed inference model, Linux x64
remote workspaces, and a small named cohort (suggested 3–5 developers).
Use the customer's existing access platform where available. Avoid selling native
desktop coverage, arbitrary plugins, multiple models or unattended production changes
as part of this first profile.

See [enterprise offering](../ENTERPRISE.md) and [licensing boundaries](../LICENSING.md).
