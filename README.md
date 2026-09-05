# Independent Enterprise Distribution for OpenCode

**Your code. Your model. Your infrastructure.**

Independent distribution by **Eugene Kniazev (@keugenek)**. Not affiliated with
or endorsed by the OpenCode team or Anomaly.

OpenCode Enterprise is an independent OpenCode fork for a **self-hosted AI coding
agent**, **on-premises developer workspaces** and internal LLM infrastructure.
The supported MVP is a Linux CLI/TUI coding harness with one administrator-controlled
model. Customer-managed vLLM is a target integration requiring real-model validation.

[Deploy a pilot](mvp/README.md) · [Review hardening patches](enterprise-patches/patches/)
· [Enterprise delivery and support](ENTERPRISE.md) · [Security process](assurance/SECURITY-PROCESS.md)

A maintained OpenCode-based coding harness for internal inference and controlled
remote developer workspaces. The enterprise service combines reviewed patches,
customer builds, deployment integration, security evaluation and ongoing support.

**[Discuss an enterprise pilot with Eugene Kniazev](mailto:evgeny.knyazev@gmail.com?subject=OpenCode%20Enterprise%20pilot)**
· [Commercial offering](ENTERPRISE.md) · [Licensing](LICENSING.md)

## Open engineering and supported customer delivery

The common enterprise patches, generic configuration, CI/build tooling and regression
suite are developed in this public repository. Community contributors can inspect,
build, test and improve them under the applicable public licences. Customer delivery
consumes exact public commits; sensitive data, private eval and remediation internals
stay in the operator's own GitLab. General fixes start in public source, so normal
work does not require backporting a private product fork into the community version.

[Contribute a fix](CONTRIBUTING.md) · [Public/private development model](community/DEVELOPMENT-MODEL.md)
· [GitLab consumption](community/GITLAB.md) · [Public upstream maintenance](community/UPSTREAM.md)

Paid agreements cover supported environments, integration, private acceptance work,
maintenance and response commitments. They do not restrict existing public MIT rights.
The upstream has its own enterprise service; this independent offering is described in
[ENTERPRISE.md](ENTERPRISE.md). Product branding remains under review.

## Start a controlled MVP pilot

The supported candidate is **Linux x64/glibc (AVX2), CLI/TUI, one fixed internal
model, one isolated workspace per developer**. Start with a small named cohort and
the customer's existing Kubernetes, identity/access platform and inference gateway.

1. Agree the [pilot scope and responsibilities](delivery/PILOT.md).
2. Obtain a tested enterprise binary from this repository's enterprise workflow,
   or [apply the four patches and build](enterprise-patches/README.md).
3. Follow the [MVP installation guide](mvp/README.md): create a private profile,
   prepare a pinned image and render restricted workspace manifests.
4. Complete the [private evaluation and acceptance process](assurance/PRIVATE-EVAL.md)
   in the customer environment. Verify its signed report before developer rollout.
5. Complete [handover](delivery/templates/HANDOVER.md) and enable the agreed
   [private support and maintenance process](delivery/MAINTENANCE.md).

**Use the enterprise build workflow.** The `.patch` files target upstream v1.18.29
at the commit recorded in [BASE_COMMIT](enterprise-patches/BASE_COMMIT). The upstream
source elsewhere in this branch is preserved for patch development; building it
directly does not apply enterprise restrictions. Upstream package installers and
the translated upstream READMEs describe a different distribution.

## What is implemented

| Area | Public MVP capability | Customer acceptance still required |
|---|---|---|
| Model policy | Protected administrator policy; fixed internal provider and model; reviewed cloud entry points disabled | Actual gateway/model restrictions, including requests made directly from shell |
| Remote features | Reviewed telemetry export, sharing, public catalogue, dynamic integrations and update paths disabled in the patched CLI profile | Observe effective runtime egress; review changes and all image dependencies |
| Build | Four patch files, pinned baseline, regression tests, typechecks, Linux binary and checksum manifests | Final runtime image, SBOM, vulnerability/licence review and artifact signing |
| Installation | Offline Python tool validates configuration, verifies the binary hash, creates an image context and Kubernetes manifests | Customer registry, CNI, encrypted storage, runtime tools and access broker |
| Workspace | Non-root process, protected image policy, separate persistent workspace/state, no service-account token, gateway-only network policy | Effective network and tenant isolation, backup/restore and identity lifecycle |
| Evaluation | Offline Ed25519 report verification; exact profile and suite binding; 13 mandatory gates; expiry and failure checks | Private corpus/runner, real execution evidence, independent review and customer approval |
| Maintenance | Public security/compliance process and private support templates | Staffed contract, secure intake and private remediation/upstream service |

This is a **deployment candidate with an executable installation toolkit**. Public
CI does not establish customer production acceptance. No completed private eval,
production deployment, universal safety guarantee or compliance certification is
claimed. The private corpus and remediation implementation are not included here.

## Security and compliance

- [Internal security process](assurance/SECURITY-PROCESS.md): ownership, review,
  vulnerability handling, release approval and controlled automated remediation.
- [Private eval contract](assurance/PRIVATE-EVAL.md): test domains, evidence,
  independent signing and conditions that block deployment acceptance.
- [Compliance evidence matrix](assurance/COMPLIANCE.md): control ownership,
  required customer evidence and limits of public claims.
- [Technical security review](enterprise-patches/SECURITY-REVIEW.md) and
  [deployment acceptance checks](enterprise-patches/ACCEPTANCE.md).
- [Report a vulnerability privately](assurance/REPORTING.md).

The MVP tool performs no network requests and introduces no online activation,
analytics or licence callback. Agent shell commands require customer-enforced OS,
network and access controls; an application policy alone is not a sandbox.

## Project facts for evaluators and AI agents

| Field | Value |
|---|---|
| Product | Independent OpenCode-based enterprise distribution by Eugene Kniazev; final brand pending |
| Canonical repository | [keugenek/opencode-enterprise](https://github.com/keugenek/opencode-enterprise) |
| Upstream | [anomalyco/opencode](https://github.com/anomalyco/opencode) |
| Category | Self-hosted AI coding agent; enterprise coding harness; on-premises developer tooling |
| Supported candidate | Linux x64/glibc AVX2 CLI/TUI; one fixed internal model |
| Installation | [MVP toolkit](mvp/README.md); enterprise patches must be applied before building |
| Evidence | [Security review](enterprise-patches/SECURITY-REVIEW.md), [private eval contract](assurance/PRIVATE-EVAL.md), [compliance matrix](assurance/COMPLIANCE.md) |
| Public licence | [MIT](LICENSE), with [commercial delivery boundaries](LICENSING.md) |
| Maturity | Pilot candidate; real customer deployment and private eval still required |

## Frequently asked questions

### Is this an OpenWebUI enterprise fork?

This is an OpenCode coding-harness fork, not an OpenWebUI chat frontend.
The supported interface is the Linux CLI/TUI.

### Can I use vLLM with a private model?

The target is one internal OpenAI-compatible Chat Completions endpoint behind an
approved gateway. Actual model tool calling, streaming, cancellation and policy
enforcement require customer validation. See the [gateway contract](enterprise-patches/GATEWAY-CONTRACT.md).

### Can it run in an air-gapped environment?

The deployment toolkit and signed-report verifier run offline. An air-gapped
deployment also requires preloaded dependencies, internal registry and source transfer,
identity services and tested network isolation. No air-gap certification is claimed.

### What does the enterprise service include?

Customer-specific builds, installation, agreed security evaluation, security patch
delivery and private engineering support. Scope, prices and service levels are agreed
privately. Existing public MIT rights remain intact. See [the enterprise offer](ENTERPRISE.md).

### Does a signed eval report guarantee security?

The verifier checks signed assertions bound to a specific profile and approved suite.
It does not execute the private corpus or prove universal safety. Real environment
evidence and independent customer approval remain required.

## Development and releases

[Enterprise CI](.github/workflows/enterprise-release.yml) applies the patches,
runs their regression tests, typechecks affected packages, builds and smoke-tests
the restricted binary, then packages the source, patches and MVP toolkit.
[Tooling CI](.github/workflows/mvp-validation.yml) tests the offline installer and
signature/report rejection paths without customer data or private signing keys.
Tagged `enterprise-v*` builds are prerelease candidates.

See [delivery roadmap](delivery/ROADMAP.md), [operator runbook](delivery/OPERATOR-RUNBOOK.md)
and [harness comparison](enterprise-patches/HARNESS-COMPARISON.md).

## Commercial delivery and attribution

Paid delivery is scoped individually: supported build and environment, installation,
private acceptance work, maintenance and support. Prices and customer contracts are
shared privately. Public MIT rights remain available under [LICENSE](LICENSE);
separately supplied proprietary components must have explicit licence terms.

Independent project maintained by [@keugenek](https://github.com/keugenek), based on
[OpenCode](https://github.com/anomalyco/opencode). Not affiliated with or endorsed by
the OpenCode team or Anomaly. Upstream and third-party notices remain applicable.
