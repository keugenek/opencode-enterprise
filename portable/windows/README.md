# Windows portable ZIPs

This branch retains OpenCode v1.18.32 as the base. This build restricts model use to the local proxy described below.

- **Desktop:** extract the whole ZIP into a writable folder and run `OpenCode.exe`. A small source change makes the packaged desktop keep its database, settings, browser storage, logs and cache in `data/` beside the executable. Installed-profile migration and protocol registration are skipped. Installer updates are disabled.
- **TUI:** extract the whole ZIP and run `Start-TUI.cmd`. This wraps the custom TUI executable built from the same pinned source and keeps persistent data in `data/` beside the launcher. Command-line arguments work, e.g. `Start-TUI.cmd C:\\projects\\example`. Do not launch `app/opencode.exe` directly if you want portable data paths.
- Close the app before moving its folder. Copy the entire folder, including `data/`, to retain history. The desktop and TUI ZIPs use separate profiles.
- Update manually by replacing application files while preserving `data/`, after backing it up. Do not point this version at a newer installation's database.

## Windows extraction and first launch

Download and extract the `windows-portable-zips` artifact, then extract the desired inner ZIP into a short, writable path such as `C:\oc`. The packages use short names: `opencode-desktop-portable.zip` contains `desktop/`, and `opencode-tui-portable.zip` contains `tui/`. Version and source identity remain in `BUILD.json`.

If Windows reports **Path too long**, choose a fresh short destination instead of nesting the default archive names. Extract every file before launching; do not skip files that failed to extract. The packaging job checks the longest path in each ZIP with a 100-character extraction destination prefix and requires the full path to stay below 240 characters. Longer destination paths can still exceed Windows limits.

The desktop and TUI are unsigned, so SmartScreen may display **Windows protected your PC / Unknown publisher**. If you downloaded this repository's linked Actions artifact and trust this test build, choose **More info → Run anyway**. If your managed PC does not offer that option, contact its administrator. A trusted code-signing identity is needed to display a verified publisher; even signed new builds can receive reputation warnings. See [Microsoft's SmartScreen guidance](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

## Local model proxy

Model access is compiled into both apps and fixed to `http://localhost:8081/v1` (OpenAI-compatible). Start your proxy before opening the app. Its `GET /v1/models` response supplies the model picker; requests use `POST /v1/chat/completions`. If discovery fails, no models are available and there is no cloud fallback. Restart the app after starting or changing the proxy.

If the proxy requires a bearer token, set `OPENCODE_LOCAL_PROXY_API_KEY` before launch. Other providers' credentials are ignored. Discovered models default to a 32,768-token context and 4,096-token output budget; the proxy must support the requested model and tool calling.

User/project provider configuration, endpoint overrides, custom provider packages, provider plugins, cloud OAuth and remote OpenCode backend attachment cannot replace this model connection. Model HTTP requests use a direct connection (ignoring HTTP proxy environment settings) and reject redirects. Server plugins are disabled in this build because they can replace provider behavior.

This restriction covers the app's built-in model provider path, not all networking by tools, shell commands, MCP servers, or other programs. It is not an OS firewall. Nothing prevents replacing or modifying the distributed program itself.

## Build and download

The **Windows portable ZIPs** GitHub Actions workflow runs for pushes to `enterprise-restart`, using a GitHub-hosted Windows runner. Successful runs attach two ZIPs, `SHA256SUMS`, a smoke report and a desktop screenshot in the `windows-portable-zips` artifact. No release is automatically published.

The desktop is rebuilt from this branch using the upstream locked dependencies and packaging process. It is an unsigned custom build, not an official upstream portable release. The TUI is also a custom unsigned build; it is rebuilt so the provider restriction is enforced inside the executable. `BUILD.json` records source identity.

Local build from the repository root, using Node 24 and Bun 1.3.14:

```powershell
bun install --linker hoisted --frozen-lockfile --backend copyfile --network-concurrency 1
$env:OPENCODE_CHANNEL = "prod"
$env:OPENCODE_VERSION = "1.18.32"
$env:OPENCODE_PORTABLE = "1"
$env:OPENCODE_LOCAL_PROXY_ONLY = "1"
cd packages/core
bun test test/local-proxy.test.ts
cd ../opencode
bun run script/build.ts --single --baseline --skip-install --skip-embed-web-ui
cd ../..
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

### Administrator-controlled model access

Both apps hide provider connection, custom provider setup, and remote server configuration in this build. Users can select only models advertised by `http://localhost:8081/v1/models`; configuration files cannot add models or change the endpoint.

The proxy is the authorization boundary: its administrator should maintain the allowed model IDs, return only those IDs from `/v1/models`, and reject completion requests for every other ID. Keep upstream provider credentials and policy outside user-editable client files. Use centrally enforced credentials/model permissions if users can replace or reconfigure the local proxy. Hiding app controls alone cannot prevent someone running a different client.

The supplied smoke-test proxy is a synthetic CI fixture, not a production proxy or an authorization service.
