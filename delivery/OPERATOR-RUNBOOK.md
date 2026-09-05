# Operator runbook: customer installation and developer rollout

Operator procedure to adapt and validate for the customer. It does not install the
gateway, SSO broker or multi-user provisioner. Do not deploy the example YAML directly
as a production developer service.

## 1. Freeze the scope

Complete the private [pilot profile](PILOT.md), record approvals, infrastructure owners,
one model, deployment mode, allowed networks, storage and support channel. Start with a
staging workspace. Do not insert real customer values into public files.

## 2. Obtain and verify the delivery

Obtain the agreed release bundle through the approved route. Verify its SHA256SUMS
against an authenticated manifest and, for a production delivery, the release signature
using customer-approved trust material. Checksums alone are not publisher authentication.
Check distribution commit, upstream baseline, patched tree hash and per-component licences.

The public workflow supplies a binary archive, patch archive, patched source and manifest.
A pinned customer runtime image, SBOM/scanning and signature verification are additional
work in ENT-02. Never substitute the public upstream npm installer for the patched binary.

For a source evaluation, follow [patch/build instructions](../enterprise-patches/README.md).
Build in disposable CI with the smoke-test policy, not on a developer's workstation.
Retain build logs and hashes privately with the delivery record.

## 3. Prepare the customer image and policy

For the current executable pilot flow, use [MVP installation](../mvp/README.md),
including persistent workspace/state and signed-report checks.
Use [Dockerfile](../enterprise-patches/Dockerfile) as a lower-level starting point with an approved
Linux runtime image by digest. Supply git, rg, bash, required project toolchain and
customer CA roots. Include no live credentials, customer source or licence secrets
in image layers.

Replace the example endpoint/model/token limits in a private policy file. The binary
expects /etc/opencode/enterprise.json, root-owned, a regular non-symlink file, without
group/world write permissions; parents must satisfy the same ownership/write constraints.
Install binary and policy during image preparation, then run non-root with read-only
root filesystem. Policy changes require an operator-managed image/configuration change.

An ordinary symlink-based ConfigMap mount may fail these checks. Use an image-baked policy
or a specifically validated regular-file provisioning method; do not weaken the reader
to make an unreviewed mount work. The example policy is not a customer's real endpoint.

## 4. Integrate inference

Implement and verify the [gateway contract](../enterprise-patches/GATEWAY-CONTRACT.md)
with the actual vLLM model/parser. Test TLS/CA, trusted workload identity, exact model,
streaming tool calls, cancellation, limits and no fallback. Sending the example
"gateway-managed" value as a personal API key is not an authentication solution.

## 5. Provision isolation and storage

Adapt [runtime.example.yaml](../enterprise-patches/runtime.example.yaml) to an approved
per-developer provisioning system. Replace all placeholder image/network values.
Apply network/admission restrictions before starting the workload and verify effective
rules. Protect workload labels and admission configuration from developer modification.

The sample Pod has no inbound service, uses emptyDir and is an operator smoke-test
example. Add separately tested user ownership, persistent storage or controlled export,
backup/restore, resource quota, workspace lifecycle and an authenticated access route.
Do not give developers unrestricted kubectl exec or pod-creation rights as a shortcut.

Pre-stage source/dependencies with appropriately scoped provisioning credentials that
are absent from the running agent. Establish the reviewed route for exporting changes.

## 6. Verify and accept

Run all [existing acceptance gates](../enterprise-patches/ACCEPTANCE.md), then the
lifecycle and business checks in [ACCEPTANCE-RECORD.md](templates/ACCEPTANCE-RECORD.md).
Use two different developer identities for isolation tests and the exact candidate image.

Inside the staging runtime, the basic application checks are:

```sh
opencode --version
opencode models
opencode
```

Only the administrator-selected enterprise model should be listed. Complete a small
approved edit/test cycle with the actual model. These commands alone do not constitute
security acceptance. Retain network, gateway and access-control evidence.

## 7. Issue developer access

The customer lead nominates the cohort; the platform owner maps each approved user to
their workspace. Confirm source access, limits, persistence, export path and revocation.
Distribute a completed private copy of [DEVELOPER-QUICKSTART.md](DEVELOPER-QUICKSTART.md)
with the real terminal/access route and support contacts. Train developers to review
changes and understand approvals and denied features.

## 8. Handover and operation

Record exact version/policy, accepted scope, known limitations, escalation contacts,
support term, update windows, backup/restore and emergency isolation procedures.
Complete [HANDOVER.md](templates/HANDOVER.md). The supplier's role and access are those
in the signed scope; no perpetual remote access is implied.

## Rollback / offboarding

Stop new sessions, preserve required evidence, and terminate affected active sessions.
Restore the previous approved image/policy together with a tested compatible state
snapshot; do not blindly start an older binary on a migrated session database.
Re-test model/access/network boundaries before re-enabling sessions.

For a departing developer: revoke broker/IdP access and workload identity, terminate
sessions and running jobs, revoke associated scoped Git/export credentials, then
archive/delete workspace data per the agreed policy. Verify that cached access fails.
Ending a commercial subscription does not revoke previously granted MIT rights.
