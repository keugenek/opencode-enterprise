# Windows portable ZIPs

This branch retains OpenCode v1.18.32 as the base. No enterprise patch series is applied.

- **Desktop:** extract the whole ZIP into a writable folder and run `OpenCode.exe`. A small source change makes the packaged desktop keep its database, settings, browser storage, logs and cache in `data/` beside the executable. Installed-profile migration and protocol registration are skipped. Installer updates are disabled.
- **TUI:** extract the whole ZIP and run `Start-TUI.cmd`. This wraps the checksum-verified upstream TUI executable and keeps persistent data in `data/` beside the launcher. Command-line arguments work, e.g. `Start-TUI.cmd C:\\projects\\example`. Do not launch `app/opencode.exe` directly if you want portable data paths.
- Close the app before moving its folder. Copy the entire folder, including `data/`, to retain history. The desktop and TUI ZIPs use separate profiles.
- Update manually by replacing application files while preserving `data/`, after backing it up. Do not point this version at a newer installation's database.

## Build and download

The **Windows portable ZIPs** GitHub Actions workflow runs for pushes to `enterprise-restart`, using a GitHub-hosted Windows runner. Successful runs attach two ZIPs, `SHA256SUMS`, a smoke report and a desktop screenshot in the `windows-portable-zips` artifact. No release is automatically published.

The desktop is rebuilt from this branch using the upstream locked dependencies and packaging process. It is an unsigned custom build, not an official upstream portable release. The TUI executable is the unmodified official v1.18.32 x64 release. `BUILD.json` records source identity.

Local build from the repository root, using Node 24 and Bun 1.3.14:

```powershell
bun install --linker hoisted --frozen-lockfile
$env:OPENCODE_CHANNEL = "prod"
$env:OPENCODE_VERSION = "1.18.32"
$env:OPENCODE_PORTABLE = "1"
cd packages/desktop
bun test src/main/portable.test.ts
bun run build
bun typecheck
bun run package --win --x64 --publish never
cd ../..
./portable/windows/package.ps1
node ./portable/windows/smoke.mjs
```

## Validation and limits

The workflow checks the actual ZIP payloads: TUI version and persistent database across launches/relocation; desktop window, authenticated local backend, settings and session persistence after closing/reopening and moving the directory. No model request is needed.

This is portable application state, not a sandbox or an air-gapped distribution. Projects, Git, shells, external tools and explicitly configured file paths may be outside the portable directory. Saved absolute project paths may need reopening after moving to a different drive. OS credential encryption can bind some credentials to a machine/account; cross-machine authentication portability is not promised. The app requires a writable directory and the usual Windows runtime dependencies.
