# Supported enterprise delivery for OpenCode-based coding

**Public engineering. Customer-specific assurance and operations.**

We maintain an independent OpenCode-based distribution for internal inference and
controlled developer workspaces. General hardening patches, configuration schemas,
CI/build tooling and regressions are developed publicly. Customers buy the work and
commitments required to deploy, accept and maintain that software in their environment.

**[Discuss a paid pilot with Eugene Kniazev](mailto:evgeny.knyazev@gmail.com?subject=Enterprise%20coding%20deployment)**

## Public project and paid delivery

| Available publicly under applicable licences | Available through a customer agreement |
|---|---|
| Common enterprise hardening patches and fixes | Agreed supported build, model, environment and maintenance period |
| Generic policy/configuration schemas and sanitized defaults | Installation, private runtime configuration and infrastructure integration |
| Build/release automation and directed regression tests | Final customer image review, provenance/signing and controlled delivery work |
| Security process, findings and report-verification contract | Confidential deployment evaluation, evidence review and acceptance assistance |
| Community contributions, public issue/PR review and candidate artifacts | Private support intake, diagnosis, agreed response targets and patch/backport delivery |
| General updates developed in one public source tree | Customer rollout planning, compatibility assessment and rollback assistance |

Payment funds accountable engineering and customer-specific service. Public software
rights do not depend on buying support. A community contribution is not automatically
subject to a commercial restriction, and a public CI candidate is not automatically a
contractually supported customer release. Prices, contracts and service levels are
negotiated privately; no public price list or unlimited support/fix promise is implied.

## How a customer bug becomes a shared improvement

Sensitive reports, reproductions and acceptance evidence stay in the customer's or
supplier's own private GitLab. With the necessary permission, we create a synthetic
public reproduction and implement the common fix plus regression directly in this
public repository. Private delivery then consumes the reviewed public commit and
re-runs its acceptance checks. There is no normal second private fork of the common
harness to reconcile back into the community project.

A confidential vulnerability may require a temporary security branch until coordinated
disclosure. Customer-only adapters and business tooling can remain private; reusable
core fixes belong in the public source. See [development boundaries](community/DEVELOPMENT-MODEL.md)
and [private GitLab integration](community/GITLAB.md).

## What stays confidential

Customer code, prompts, traces, internal endpoints, actual deployment settings, support
records, contracts, private eval cases/scoring/results and remediation orchestration.
Signing keys and production credentials remain in protected secret/signing services,
not in Git repositories. Public CI has no access to private GitLab or customer systems.

The private remediation service is planned delivery infrastructure; publication of this
offer does not assert it is already implemented. Its workers may propose public fixes,
but they do not gain production, signing or unrestricted publication authority.

## Current delivery scope

The MVP candidate targets Linux x64/glibc AVX2 CLI/TUI, one administrator-controlled
internal OpenAI-compatible model and an existing customer workspace/access platform.
The public patch/build pipeline and offline deployment/report-verification toolkit are
implemented. Actual vLLM compatibility, effective gateway/network/tenant isolation,
identity lifecycle, final-image evidence and private eval execution remain customer
acceptance work. No completed confidential eval or compliance certification is claimed.

Our differentiation is the scoped deployment, reviewed hardening, real-environment
acceptance and maintained delivery. Upstream already offers centralized configuration,
SSO and internal-gateway integration; those general capabilities are not claimed as
unique here. See [upstream enterprise documentation](https://opencode.ai/docs/enterprise/).

Start with [the pilot scope](delivery/PILOT.md), [MVP installation](mvp/README.md),
[security process](assurance/SECURITY-PROCESS.md), [private eval contract](assurance/PRIVATE-EVAL.md)
and [compliance evidence matrix](assurance/COMPLIANCE.md).

## Licensing and identity

The root [MIT licence](LICENSE) and existing public grants remain intact. Customer
agreements define service obligations and any explicitly identified, separately
licensed supplier-owned components. Private hosting alone does not change a component's
licence. See [LICENSING.md](LICENSING.md).

Independent project maintained by [@keugenek](https://github.com/keugenek), not affiliated
with or endorsed by the OpenCode team or Anomaly. "OpenCode" identifies the upstream
technology; a separate product-brand decision remains open. This offer is not the
upstream's official OpenCode Enterprise service.

## Start a conversation

Email your organization, high-level environment, internal inference setup, approximate
cohort and desired support scope. Establish an agreed secure channel before sending
sensitive material. We can then agree a pilot, evidence requirements and a customer-specific
commercial proposal. No mandatory external licence callback is introduced.
