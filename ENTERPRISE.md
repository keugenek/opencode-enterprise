# Enterprise distributions, licensing and support

## Your models. Your infrastructure. A maintained distribution.

Deploy an OpenCode-based coding harness around your internal inference service,
with an agreed configuration and a maintained patch set. Work directly with
Eugene Kniazev to scope the build, deployment and ongoing support your organisation needs.

**[Contact Eugene about enterprise licensing](mailto:evgeny.knyazev@gmail.com?subject=OpenCode%20Enterprise%20licensing)**

Prices, licence terms, delivery milestones and support commitments are negotiated
privately for each customer. No public price list or standard customer contract
is published here.

## What the enterprise offering covers

| Area | Scope available by agreement |
|---|---|
| Maintained enterprise patches | Configuration controls, provider/model restrictions and removal or disabling of unwanted remote features |
| Prebuilt distributions | Customer-specific build configuration, versioned artifacts and deployment documentation |
| Automated build and validation | Patch application, regression tests, typechecks, binary builds and artifact integrity checks |
| Security review | Review of the agreed release and deployment, documented findings and mitigation recommendations |
| Security maintenance | Applicability assessment, agreed patch/backport work and tested update delivery |
| Private acceptance evaluation | Customer-scoped adversarial, isolation, functionality and reliability evaluation with confidential evidence and independently signed results |
| Deployment and support | Internal inference integration, acceptance assistance, troubleshooting and an agreed support channel |

The contract defines which of these are included. Automated builds and tests are
implemented; fully automated vulnerability remediation, unrestricted backport
coverage and 24/7 incident response are not implied. An SLA, update cadence or
supported-version period applies only if expressly agreed.

## Private issue reporting and maintained releases

Customers can submit bug reports through the private channel agreed in their
contract. For the supported configuration, the maintenance process covers triage,
reproduction where possible, prioritisation, regression testing and delivery of
an accepted fix or documented workaround through the agreed release channel.
Response targets and release schedules are contractual; submission does not
guarantee that every request will be fixed or become a product feature.

Customer source and diagnostic data are kept separate from public upstream
contributions. Sending customer-derived material upstream requires the customer's
permission. General fixes can be contributed upstream when rights and disclosure
requirements allow. Updates to a customer's deployed environment follow that
customer's approval process.

## Public evaluation and customer delivery

The public repository contains an inspectable patch series, security review,
deployment examples and CI tooling. These let engineering teams evaluate the
approach before commissioning a supported distribution.

Customer delivery can include a release/configuration manifest, prebuilt artifacts,
agreed acceptance results, deployment runbooks and maintenance coverage.
A publicly downloadable CI artifact is not, by itself, a customer-accepted or
contractually supported enterprise release.

## Current technical scope

The current candidate targets Linux x64 CLI/TUI with one administrator-controlled
internal OpenAI-compatible inference endpoint/model. It disables the reviewed
remote telemetry, sharing and cloud entry points in that supported profile.

Real vLLM compatibility, gateway policy, operating-system/network isolation and
final deployment acceptance must be verified for the customer's environment.
This is not a blanket air-gap or regulatory-compliance certification. Desktop,
web and other platforms are outside the current validated profile.

See [technical instructions](enterprise-patches/README.md),
[security review](enterprise-patches/SECURITY-REVIEW.md) and
[acceptance gates](enterprise-patches/ACCEPTANCE.md).

## Security assurance and the MVP

Use the [MVP installation toolkit](mvp/README.md), [internal security process](assurance/SECURITY-PROCESS.md),
[private evaluation contract](assurance/PRIVATE-EVAL.md) and [compliance evidence matrix](assurance/COMPLIANCE.md)
to scope a controlled deployment. The public toolkit verifies signed reports; the private
corpus, runner and signer service must be established for delivery. No completed
customer evaluation or absolute safety guarantee is claimed. Acceptance is tied to
the agreed build, model, environment and evaluation scope.

## Licensing

Enterprise deliveries and services are scoped under an individually negotiated
agreement. That agreement identifies any separately licensed, supplier-owned
components and the rights granted for them. Existing open-source components and
previously published MIT versions retain their applicable licences; acquiring
support is not a prerequisite for exercising those rights.

See [licensing boundaries](LICENSING.md). This page describes the commercial
offering; it is not an executed software licence or a support contract.

## Deployment planning

See the [delivery playbook](delivery/README.md) for the proposed paid pilot,
operator procedure, developer access lifecycle, acceptance records and maintenance
process. Templates describe required work; they do not assert that identity,
provisioning or production acceptance is already implemented.

## Start a discussion

**[Email Eugene Kniazev](mailto:evgeny.knyazev@gmail.com?subject=OpenCode%20Enterprise%20licensing)** with your organisation, target environment,
internal model/gateway, approximate deployment size and desired support scope.
A high-level description is enough initially. Share sensitive architecture,
credentials, source code or vulnerability details only through an agreed secure
channel.

We can then agree an evaluation scope, acceptance criteria and a customer-specific
commercial proposal. No mandatory external licence callback is introduced by this
public offering.

Independent project maintained by [@keugenek](https://github.com/keugenek).
Not affiliated with or endorsed by the OpenCode team or Anomaly.
