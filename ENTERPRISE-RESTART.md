# Enterprise restart: Windows portable ZIPs

The baseline is upstream [OpenCode v1.18.32](https://github.com/anomalyco/opencode/releases/tag/v1.18.32), commit `545f51d26cc39a907d2867492d498d9607ea5fa4`. The clean base branch is `stable-v1.18.32`; this work is on `enterprise-restart`.

This branch supplies a reproducible Windows x64 portable packaging workflow. See [portable build and use instructions](portable/windows/README.md).

## What is packaged

- **TUI:** the official upstream x64 ZIP, verified against SHA-256 `1483c72d5adced825590a0ecf8cc18b3e87e535960a125dbf539d33bce135d0f`, with a launcher for persistent data in the extracted folder.
- **Desktop:** the same stable source rebuilt with a small portable-mode addition. App settings, database and browser state stay beside the executable. It skips installed-profile migration and protocol registration, and disables installer updates. The output is an unsigned custom ZIP.

Upstream supplies Windows TUI ZIPs but only desktop NSIS installers. An extracted installer alone was insufficient: normal desktop startup can reuse the installed profile, and temporary onboarding test mode does not preserve conversations. Switching to another fork is unnecessary for this packaging requirement.

No previous enterprise hardening patches are included. Agent/model behavior and backend code remain on the stable baseline; this is not an enterprise security profile.

## Build evidence

[Windows portable ZIPs workflow](.github/workflows/windows-portable.yml) builds on GitHub-hosted Windows, runs profile regressions, packages ZIPs and tests the actual extracted applications. Its smoke checks cover persistent settings/session state across restart and directory relocation without model requests. Successful runs upload both ZIPs, checksums, a report and a screenshot. A workflow definition alone is not evidence that a run passed; consult the linked PR's validation results and the artifact's report.

Earlier local checks of the official binaries passed TUI startup, help, mode switching and exit. Desktop launches in the agent environment failed with subprocess code `0xC0000135`; local desktop acceptance remains separate from runner checks.
