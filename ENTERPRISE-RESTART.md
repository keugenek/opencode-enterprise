# Enterprise restart: Windows portable ZIPs

The baseline is upstream [OpenCode v1.18.32](https://github.com/anomalyco/opencode/releases/tag/v1.18.32), commit `545f51d26cc39a907d2867492d498d9607ea5fa4`. The clean base branch is `stable-v1.18.32`; this work is on `enterprise-restart`.

This branch supplies reproducible Windows x64 portable packages with a compiled local-proxy model policy. See the [current downloads](README.md#windows-portable-downloads) and [build and use instructions](portable/windows/README.md).

## What is packaged

- **TUI:** a custom executable built from the pinned stable source, with a launcher that keeps persistent data in the extracted folder.
- **Desktop:** the same stable source rebuilt with portable mode and the model policy. App settings, database and browser state stay beside the executable. It skips installed-profile migration and protocol registration, and disables installer updates.
- Both packages are unsigned custom test builds. Trusted signing and Microsoft Store publication are pending.

Upstream supplies Windows TUI ZIPs but only desktop NSIS installers. Extracting an installer alone would reuse the installed profile, and temporary onboarding test mode does not preserve conversations. A different fork is unnecessary for this packaging requirement.

The earlier enterprise patches were not carried forward. New changes on this stable baseline provide portable profiles and restrict model access to `http://localhost:8081/v1`. Both apps show only proxy-discovered models, hide other provider/custom-provider/remote-server controls, reject provider and endpoint overrides, and offer no cloud fallback. A custom TUI build is now necessary to enforce the same policy as the desktop.

The proxy's administrator must maintain and enforce the model allowlist. Client restrictions do not protect against replacing the executable or proxy, or against separate network access by tools. No production proxy configuration has been changed.

## Build evidence

The [Windows portable ZIPs workflow](.github/workflows/windows-portable.yml) builds on GitHub-hosted Windows, runs profile and transport regressions, typechecks the affected packages, and tests the extracted ZIP payloads. Checks cover startup and UI restrictions, rejected configuration/model overrides, synthetic proxy responses, offline behavior, and persistent settings/session state across restart and directory relocation. No real model inference is performed.

Successful runs upload both ZIPs, checksums, a report and a screenshot. Consult the current README download and its build report for completed validation; a workflow definition alone is not evidence that a run passed.

Earlier local checks of the official binaries passed TUI startup, help, mode switching and exit. The current restricted TUI and packaged desktop backend also passed local synthetic model-routing checks. Desktop windows cannot be accepted in the agent environment because Electron subprocesses fail with code `0xC0000135`; full UI acceptance runs on the Windows CI runner.
