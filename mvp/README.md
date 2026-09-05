# Enterprise MVP installation toolkit

This toolkit prepares a restricted **pilot candidate** for an existing customer
platform. It does not provision a cluster, inference server, identity broker or
private eval service. Python 3.11+ and OpenSSL with Ed25519 support are required on
the operator workstation. The tool itself is offline and uses only Python's standard
library. Docker/BuildKit, kubectl and an approved registry are operator prerequisites.

## Supported deployment and prerequisites

Linux x64/glibc with AVX2, one named developer/workspace, one exact internal
Chat Completions model, HTTPS gateway on one approved RFC1918 IPv4:443. No public DNS,
package downloads, source-host egress or cloud fallback from the workspace.

Before installation the customer platform owner supplies:

- A dedicated workspace namespace on a Kubernetes cluster with tested ingress and
  egress NetworkPolicy enforcement, restricted admission and encrypted persistent
  storage. Restrict who can modify pods, policies, namespace labels or PVCs.
- An existing authenticated access broker that maps the developer to only their
  workspace, logs access and revokes active sessions. Do not give developers
  cluster credentials or broad `pods/exec` permissions.
- A gateway that authenticates this workspace through customer-controlled network
  workload identity, pins the exact model and routes, disables cloud fallback,
  limits requests and rejects redirects. Personal API tokens are deliberately
  stripped by the patched transport. Do not mount long-lived gateway credentials.
- A pinned runtime base image containing glibc, CA trust for the gateway, `/bin/sh`,
  `/bin/sleep`, git and the project's approved offline build/test tools. Runtime
  tools and inherited image content must be reviewed; this toolkit does not
  certify arbitrary base images. Configure private registry pulls at platform level.
- An approved private eval suite fingerprint, isolated eval runner and an independently
  controlled signing service. Their implementation and customer evidence remain
  private; this repository supplies the verifier and report contract.

Namespace and NetworkPolicy are part of the boundary, not a complete sandbox.
Kubernetes NetworkPolicies are additive: another allow policy can expand egress.
CNI/NAT, service-mesh injection, node access, privileged workloads and cluster admins
need explicit review and active probes. See the official
[NetworkPolicy documentation](https://kubernetes.io/docs/concepts/services-networking/network-policies/).
Adding a mesh or access integration requires a reviewed deployment revision and eval.
The generated pod has no sidecars or baked-in workload credentials.

## 1. Establish the private deployment profile

Run commands from the distribution repository/toolkit root. Keep generated data in
an access-controlled directory **outside this checkout**, excluded from public CI
and source control. These paths are examples; replace them with customer paths.

```bash
umask 077
mkdir -p /srv/opencode-private/pilot-dev01
python3 mvp/mvpctl.py init --output /srv/opencode-private/pilot-dev01/profile.json
```

Edit the profile locally. The initial placeholders intentionally fail validation.

| Field | Required value |
|---|---|
| `workspace_id` | Unique named workspace ID; never reuse another developer's state |
| `runtime_image` | Approved base image reference ending in `@sha256:<digest>` |
| `binary_sha256` | Enterprise binary hash verified through the trusted delivery channel |
| `image` | Empty while preparing the image; final immutable image digest before preflight |
| `gateway_url`, `gateway_ipv4` | Canonical `https://approved.internal.hostname/v1` and private IPv4; no credentials, port override or query |
| `model`, `model_revision` | Fixed model ID and immutable deployed weights/configuration revision; no moving `latest` alias |
| `context`, `output` | Limits supported by the actual model and gateway |
| `storage_class`, `workspace_gib`, `state_gib` | Approved encrypted storage class and allocated capacities |
| `deployment_revision` | Immutable private integration-inventory revision covering cluster/CNI, access, gateway, storage, audit and model configuration |
| `eval_suite_sha256` | Independently approved private suite bundle hash, including required cases, minimum counts and thresholds |

`preflight` validates static configuration. It cannot discover whether a hostname,
image, storage class, model revision or integration inventory is true or deployed.
The evaluator must verify those relationships against the actual environment.

## 2. Prepare and build the customer image

Obtain the binary from the tested enterprise artifacts or build using
[the patch instructions](../enterprise-patches/README.md). Verify origin, checksums,
notices and scan results according to the agreed delivery channel. A self-supplied
hash does not prove provenance. The binary must be the restricted Linux candidate.

```bash
python3 mvp/mvpctl.py image-context \
  --profile /srv/opencode-private/pilot-dev01/profile.json \
  --binary /srv/opencode-private/artifacts/opencode \
  --output /srv/opencode-private/pilot-dev01/image-context

docker build --network=none \
  --tag registry.corp.internal/opencode:pilot-candidate \
  /srv/opencode-private/pilot-dev01/image-context
```

Preload the approved base in an air-gapped build environment. `--network=none`
restricts build steps; registry access by the build engine is a separate platform
policy. The context includes the verified binary, root-owned administrator policy,
MIT notice and Dockerfile. Include additional dependency notices in the runtime image
and deliver the complete SBOM and licence inventory separately.

Scan and sign the resulting image using the customer's approved tooling, import or
push it to the private registry, and set `image` to its **resulting registry digest**.
Do not substitute the base-image or binary digest. Verify the policy embedded in the
image matches the profile; changing endpoint/model/limits requires rebuilding it.

```bash
python3 mvp/mvpctl.py preflight \
  --profile /srv/opencode-private/pilot-dev01/profile.json
```

A successful response still says `deployment_acceptance: not_evaluated`.

## 3. Deploy into evaluation isolation

```bash
python3 mvp/mvpctl.py render --stage evaluation \
  --profile /srv/opencode-private/pilot-dev01/profile.json \
  --output /srv/opencode-private/pilot-dev01/evaluation
kubectl apply -f /srv/opencode-private/pilot-dev01/evaluation/01-foundation.json
```

Verify the namespace is dedicated, storage is bound as expected, restrictive policies
are effective and no other policy/admission mutation expands access. Then:

```bash
kubectl apply -f /srv/opencode-private/pilot-dev01/evaluation/02-workspace.json
kubectl -n opencode-pilot-dev01 wait --for=condition=Ready pod/workspace --timeout=120s
kubectl -n opencode-pilot-dev01 exec workspace -- opencode --version
kubectl -n opencode-pilot-dev01 exec workspace -- opencode models
```

The pod waits for brokered terminal access. `Ready` only means the container is
running. Confirm exactly the configured model appears, and run actual model/tool
calling, streaming and rejection probes from [the acceptance checklist](../enterprise-patches/ACCEPTANCE.md).
The namespace example must match your profile. These commands are for operators.

Import a reviewed project snapshot and offline dependencies through the platform's
controlled source transfer process. Keep repository write credentials outside the
agent. Review and export changes through the same process. No git/SSO provisioning
or source synchronization is implemented by this toolkit.

## 4. Execute the private eval and approve rollout

The independent evaluator executes the [approved private suite](../assurance/PRIVATE-EVAL.md)
on this exact image, policy and integration revision, retains the raw evidence,
and returns `report.json` plus an Ed25519 detached `report.sig`. Obtain the trusted
public key through the customer's approved out-of-band channel; never trust a key
supplied alongside an otherwise untrusted report.

```bash
python3 mvp/mvpctl.py verify-eval \
  --profile /srv/opencode-private/pilot-dev01/profile.json \
  --report /srv/opencode-private/pilot-dev01/report.json \
  --signature /srv/opencode-private/pilot-dev01/report.sig \
  --trusted-key /etc/opencode-acceptance/evaluator.pub

python3 mvp/mvpctl.py render --stage accepted \
  --profile /srv/opencode-private/pilot-dev01/profile.json \
  --report /srv/opencode-private/pilot-dev01/report.json \
  --signature /srv/opencode-private/pilot-dev01/report.sig \
  --trusted-key /etc/opencode-acceptance/evaluator.pub \
  --output /srv/opencode-private/pilot-dev01/accepted
```

This rejects an invalid signature, another profile/suite, missing or skipped gates,
open high/critical findings, waivers, future/expired reports and validity over 30 days.
It verifies the evaluator's signed assertions; it does not execute tests, inspect
private evidence, prove the signer was honest or install cluster admission control.
The trusted operator and customer change controls enforce use of this gate.

Obtain independent security review and customer rollout approval in the private
[acceptance record](../delivery/templates/ACCEPTANCE-RECORD.md). The approval also
identifies the trusted signer fingerprint and approved suite/integration revision.
Apply the accepted manifests to the **same evaluated deployment**, then enable
broker access for its named developer. The accepted pod annotation uses the SHA-256
of the canonical report JSON; the signature covers the original report bytes.

A profile, runtime, policy, model, gateway, identity or network change requires a new
integration revision and eval. Repeat for each developer profile; a report for one
workspace cannot authorize another. For image/spec changes, stop access and replace
the pod under change control while retaining approved PVCs; Kubernetes cannot mutate
all existing pod fields. Never delete the namespace/PVCs as a routine update step.

## 5. Operate, revoke and recover

Use the [operator runbook](../delivery/OPERATOR-RUNBOOK.md) and
[maintenance procedure](../delivery/MAINTENANCE.md). Block new promotion when a report
expires or an advisory invalidates acceptance; isolate running sessions if the
security owner determines the deployed boundary is affected. The verifier does not
monitor deployments, revoke keys online or terminate existing sessions automatically.

Back up workspace/state before updates. Restore only to a tested compatible version;
state migrations may prevent in-place downgrade. Offboarding first revokes broker
access and active sessions, then follows approved retention/deletion of PVCs and logs.
Never run two developers against the same workspace/state PVC.

## Public tests

```bash
cd mvp
python3 -m unittest discover -s tests -v
```

Tests generate temporary synthetic Ed25519 keys and fake report data. They exercise
configuration, manifests, binary checks and report/signature rejection. They contain
no private test corpus and do not produce deployment acceptance evidence.
