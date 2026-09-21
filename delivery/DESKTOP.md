# Native Windows desktop candidate

OpenCode Enterprise Desktop is a native Electron application for Windows x64.
It bundles the user interface and the patched V1 coding engine in one installation.
Developers do not need to install Node, Bun, a separate CLI or a web server.
The Linux and Windows CLI/TUI distributions remain separate downloads.

This is an **unsigned public CI candidate**. A successful build or screenshot does
not establish customer security acceptance. Actual gateway/vLLM workflows, managed
Windows endpoint controls, signing and private evaluation remain deployment gates.
Use the successful run for the exact commit you intend to deploy; desktop packaging
and smoke checks must pass before treating its artifacts as tested.

## Downloads

Open [Enterprise build and release](https://github.com/keugenek/opencode-enterprise/actions/workflows/enterprise-release.yml),
select a successful run, and download `enterprise-desktop-windows-x64` under
**Artifacts**. GitHub may require sign-in to download Actions artifacts. Extract
that outer artifact ZIP first.

| File inside the artifact | Purpose |
|---|---|
| `opencode-enterprise-desktop-VERSION-win-x64.exe` | Native NSIS installer; administrator installation into a separate desktop directory |
| `opencode-enterprise-desktop-VERSION-windows-x64-portable.zip` | Complete unpacked application; keep its DLLs, resources and locale files together |
| `desktop-smoke-windows-x64.png` | Screenshot from the native application smoke check, when recorded by CI |
| `desktop-smoke-windows-x64.json` | Corresponding machine-readable smoke result, checks and explicit limitations |
| `build-manifest-desktop-windows-x64.json` | Version, Electron version, exact source tree, baseline and patch hashes; acceptance/signing status |
| `SHA256SUMS-desktop-windows-x64` | Hashes of every delivered asset except the checksum file itself |
| `patched-source-desktop-windows-x64.tar.gz` | Exact patched source used by the build |
| `enterprise-patches-desktop-windows-x64.tar.gz` | Public patch bundle and build tooling |
| `enterprise-mvp-toolkit-desktop-windows-x64.tar.gz` | Public delivery, security and acceptance documentation/tooling |

The installer and portable ZIP contain the same native application profile. A
portable ZIP is a directory distribution, not a single self-contained EXE. Public
CI does not Authenticode-sign either form. Verify checksums against the approved
release record; checksums are not a publisher signature. Do not bypass corporate
application-control requirements to launch an unapproved candidate.

## Provision the protected model policy

Use Windows installed at `C:\Windows`, Windows PowerShell 5.1 and NTFS. The desktop
engine reads the same fixed administrator policy as the Windows TUI:

```text
C:\Program Files\OpenCode Enterprise\enterprise.json
```

1. Extract the portable ZIP to a staging directory. Its `enterprise/` folder
   contains the policy example and Windows provisioning script.
2. Copy `enterprise/enterprise.example.json` to your private staging area. Set
   the approved HTTPS `/v1` gateway, exact model ID and token limits. No personal
   API keys or customer credentials belong in this publicly readable policy.
3. For a fresh policy installation, run from an **administrator Windows
   PowerShell 5.1** console in the extracted application directory:

   ```powershell
   .\enterprise\windows\install.ps1 -PolicyPath C:\Staging\enterprise.json -PolicyOnly
   ```

   This script refuses to overwrite an existing policy directory. If the TUI
   already uses a correctly protected policy, reuse it. Updates go through the
   customer's managed configuration process; do not delete the existing policy
   or weaken its ACLs to make an installer proceed.
4. Install the NSIS package through the approved software-delivery process. The
   desktop product/directory is **OpenCode Enterprise Desktop**, separate from
   the fixed policy directory. Alternatively, deliver the entire portable
   directory into an administrator-controlled location.
5. Launch **OpenCode Enterprise Desktop** as a standard developer account. For
   the portable package, run `OpenCode Enterprise Desktop.exe` from the extracted
   directory. Select the approved development workspace and verify that only
   the administrator's internal model is available.

The installer does not configure a VPN, proxy, LLM router, firewall, SSO service or
model server. Missing or unsafe policy must stop the engine rather than offer
cloud onboarding. The Windows CLI instructions shipped by the older policy patch
remain applicable to that console package; this document describes the desktop
profile added by the later native desktop patch.

## Runtime and deployment boundary

The Electron window uses the bundled renderer and a local V1 engine. This is a
single-user workstation application, not a shared multi-tenant service. The
enterprise profile removes cloud/provider onboarding, server switching, remote
sharing/update flows and arbitrary plugins/MCP; the backend retains the fixed
model, transport and permission restrictions. V2 is not enabled by this build.
A local transport is an implementation detail, not an approved remotely exposed
API. Do not open it to the LAN or place it behind a shared public proxy.
The built-in terminal remains available with the workstation's default shell;
project settings cannot replace its startup executable or inject startup arguments
and environment variables. Interactive commands still run as the developer.

Place the managed workstation/VDI behind the corporate VPN and apply the approved
internal gateway/proxy policy. Enforce allowed network destinations for the desktop,
engine and **all child processes** at the OS/network boundary. Application prompts
are not an OS sandbox. Use a dedicated development workspace without unrelated
secrets, encrypted storage, controlled logs/history retention and standard-user
permissions. Git/shell/toolchain dependencies must come from approved sources.
The upstream data directories and local session history are sensitive even when
remote telemetry is disabled.

The private gateway must authenticate the workload, force the approved model,
reject cloud fallback and remote-media retrieval, and apply quotas/audit. See
[deployment topology](DEPLOYMENT-ARCHITECTURE.md) and the
[gateway contract](../enterprise-patches/GATEWAY-CONTRACT.md). Shared plans belong
in the approved Git repository; caches require customer/project separation.

## Validation before developer rollout

The desktop CI lane builds Windows artifacts and runs the native application
smoke check. Read its log and manifest for the exact candidate. No desktop smoke
result, screenshot or private-eval pass is implied merely by this documentation.
The package manifest records public CI as unsigned and private evaluation as not run.

Customer acceptance must additionally cover:

- Standard-user startup with valid policy, and refusal of missing/unsafe policy;
  no cloud-model or endpoint override through renderer, API, project config or env.
- Actual internal-model streaming/tool calls, cancellation, approvals/denials and
  child-agent isolation; external commands and file access stay within the agreed
  workstation security boundary.
- OS-enforced egress observation, VPN/proxy failures, local transport access controls,
  process cleanup, update distribution and desktop/engine version matching.
- Dependency/SBOM review of the complete Electron application and native modules,
  internal signing, endpoint-protection compatibility and signed private acceptance.

Patches 0006 and 0007 address the reviewed execution-permission and inference
availability gaps in the shared engine. Inference is bounded by compiled header
(30s), first-output (120s), idle-output (60s) and total (10min) deadlines per request.
The transport introduces no retries; test the complete session/retry behavior with
your real model. Passing focused regressions is not a universal security guarantee.

Linux/macOS desktop builds and a standalone web-server distribution are outside
this Windows desktop candidate. Linux and Windows CLI/TUI artifacts remain available
in the same enterprise workflow; installing the desktop does not replace them.
