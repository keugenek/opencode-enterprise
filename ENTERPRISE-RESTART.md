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
The x64 desktop installer and standard x64 TUI ZIP were downloaded on 2026-09-25; their local SHA-256 hashes matched the values above. The desktop installer had a valid Anomaly Authenticode signature. The baseline CPU variant was not downloaded.

## Scope of this starting PR

This PR adds baseline and Windows portability records to the exact upstream release tree. It does not apply the previous enterprise patch series or change runtime code, dependencies, packaging, or workflows. The existing enterprise branches and PRs remain separate historical work.

The clean baseline is the PR target so the diff contains only the restart record rather than unrelated upstream changes against the older dev branch.

## Windows portable requirement and upstream availability

Both Windows TUI and desktop must run without installation, with persistent settings and conversations kept in their portable directory and separated from an existing OpenCode installation.

Checked against upstream release v1.18.32 on 2026-09-25 (also returned by upstream's latest-stable release endpoint):

| Application | Official Windows artifact | Installation-free binaries | Persistent data beside the app |
| --- | --- | --- | --- |
| CLI/TUI | x64, x64-baseline and ARM64 ZIP archives | Available upstream | Must configure and verify separate persistent data paths; a ZIP alone does not establish data portability |
| Desktop | x64 and ARM64 NSIS installers (.exe) | No official Windows desktop ZIP or portable executable is published for this release | Not supplied as a portable profile |

[Upstream desktop packaging configuration](https://github.com/anomalyco/opencode/blob/v1.18.32/packages/desktop/electron-builder.config.ts) sets Windows `target: ["nsis"]`. The macOS ZIPs and Windows blockmap files are not Windows portable desktop packages.

The desktop payload can be extracted from the installer, but that does not make its profile portable. [Desktop startup](https://github.com/anomalyco/opencode/blob/v1.18.32/packages/desktop/src/main/index.ts) normally chooses the user profile's app-data directory. Launching the extracted executable directly can therefore collide with an existing installation. Its `OPENCODE_TEST_ONBOARDING=1` mode uses a random temporary profile and an in-memory database; it is a smoke-test mode, not a persistent portable distribution.

No complete portable desktop package is claimed or produced by this PR. The missing work is a verified way to keep desktop settings, session database, cache and backend state beside the app, together with reproducible packaging of the pinned upstream binaries. Avoid reintroducing the old enterprise runtime patches merely to achieve portability.

## Local startup checks

On 2026-09-25, the official TUI reported 1.18.32, opened an empty test project, displayed help, switched Build/Plan modes, and exited with code 0. Its test used separate XDG data/config/cache/state directories.

The complete desktop payload was extracted without editing its files. Launches in the agent execution environment, including a retry with GPU acceleration disabled, failed before a usable window appeared: Chromium GPU subprocess exit `0xC0000135`. The missing dependency/environment cause remains unresolved; desktop UI checks have not passed.

A subsequent direct-launch report was `Database is not empty and has no session table`. Read-only inspection found an existing database with `session_v2` and no `session` table, consistent with a version collision. The existing database was not modified.

No model requests were sent; testing was limited to startup and UI at the user's request.

## Next checkpoint

Provide and verify persistent portable data isolation for both applications. Desktop startup must pass before enterprise changes are introduced. Restart and move-folder checks must show that settings and conversations persist and the installed application's data is untouched. No portable release, production readiness, or enterprise isolation is asserted by this baseline record.
