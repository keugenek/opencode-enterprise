# Enterprise restart baseline

Restart the enterprise idea from the unmodified, published OpenCode desktop and CLI/TUI applications. Establish their normal behavior before introducing enterprise configuration or changing application code.

## Pinned upstream

- Repository: https://github.com/anomalyco/opencode
- Stable release: [v1.18.32](https://github.com/anomalyco/opencode/releases/tag/v1.18.32), published 2026-09-21T22:51:20Z.
- Resolved release tag commit: `545f51d26cc39a907d2867492d498d9607ea5fa4`.
- Clean baseline branch: `stable-v1.18.32`.
- Restart branch: `enterprise-restart`, created directly from that same commit.
- Verified on 2026-09-25: GitHub marks the release as neither draft nor prerelease and lists uploaded desktop and CLI/TUI artifacts.

Use the resolved tag commit above as the source pin; the release API's target_commitish field is not the resolved tag commit.

## Official prebuilt Windows applications

Start with the upstream release assets, keeping desktop and TUI on the same release. The TUI is provided by the CLI archive.

| Application | Official download | GitHub-reported SHA-256 |
| --- | --- | --- |
| opencode-desktop-win-x64.exe | [Download](https://github.com/anomalyco/opencode/releases/download/v1.18.32/opencode-desktop-win-x64.exe) | `4c80bf62ae9a9be4ac69f1941c01b88cdbe3266cb4c753e80d870c8f600da714` |
| opencode-windows-x64-baseline.zip | [Download](https://github.com/anomalyco/opencode/releases/download/v1.18.32/opencode-windows-x64-baseline.zip) | `cd852831bd094c2df2eb379eb98bed7a63db7f823a7caf277c732cdac33cbdb6` |
| opencode-windows-x64.zip | [Download](https://github.com/anomalyco/opencode/releases/download/v1.18.32/opencode-windows-x64.zip) | `1483c72d5adced825590a0ecf8cc18b3e87e535960a125dbf539d33bce135d0f` |

The release page also provides prebuilt macOS and Linux desktop and CLI distributions.
These digests were read from GitHub release metadata; binaries have not been downloaded or hashed locally.

## Scope of this starting PR

This PR adds only this baseline record to the exact upstream release tree. It does not apply the previous enterprise patch series or change runtime code, dependencies, packaging, or workflows. The existing enterprise branches and PRs remain separate historical work.

The clean baseline is the PR target so the diff contains only the restart record rather than unrelated upstream changes against the older dev branch.

## Next checkpoint (not performed here)

Run the official desktop and TUI applications on the intended Windows machine and record startup, version, project opening, terminal execution, and a simple task against the intended internal model using supported configuration. Record actual results before deciding whether any code changes are necessary.

Published stable artifacts establish an upstream starting point, not proof that the applications run correctly on this machine or meet enterprise isolation requirements. This step creates the branch and reviewable PR only; no installation, custom build, patch migration, deployment, or runtime validation has been performed.
