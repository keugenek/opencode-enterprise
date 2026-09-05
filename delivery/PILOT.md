# Paid pilot and handover

A delivery checklist, not a contract or public price list. The supplier's legal
identity, price, licence scope, service commitments and data-processing terms are
agreed privately. Do not commit signed documents or customer particulars here.

## Commercial stages and deliverables

| Stage | Customer receives | Exit evidence |
|---|---|---|
| Discovery and scoped order | Supported environment, deliverables, responsibilities, exclusions and acceptance criteria | Signed private scope; named platform/security/business owners |
| Paid evaluation | Candidate build, one configured environment, compatibility and gap report | Actual model/tool-call results; documented blockers and remaining work |
| Acceptance and developer rollout | Agreed build manifest, operating instructions, individual access, training | Acceptance record, isolation/restore/offboarding tests and owner decision |
| Maintenance subscription | Private bug channel, agreed response targets, version coverage and update delivery | Contracted service scope and named contacts; tested update procedure |
| Expansion | Additional cohort/configuration/environment | New capacity and security acceptance where relevant; agreed scope change |

An evaluation can validly conclude "not ready": the deliverable is evidence and a
gap report, not guaranteed production readiness. Work beyond the agreed scope requires
a change request before additional fees or delivery commitments are incurred.

## Discovery decisions

- Customer legal entity; permitted users and contractors; supported locations.
- Runtime isolation: managed Kubernetes workspace or an independently validated VM.
- Internet-restricted runtime versus a fully disconnected installation.
- One actual gateway/model, context/output limits, model licence and tool parser.
- One source repository/toolchain; source import and output export routes.
- Internal CA, identity platform, named-user mapping and session revocation method.
- Data classification, allowed diagnostics, AI processing location and private support channel.
- Workspace durability, encryption, backup/restore objectives and deletion retention.
- User count, concurrent active sessions, inference quotas and pilot success thresholds.
- Supported release window, update schedule, severity/response targets, exclusions and escalation.
- Customer production approval authority; supplier access boundaries and any approved processors.

Fill [customer-profile.example.json](templates/customer-profile.example.json) in a
private customer workspace. All nulls/placeholders are unresolved decisions; that
file is an inventory template, not a schema-validated deployment configuration.

## Responsibility

| Role | Accountable for |
|---|---|
| Supplier release owner | Build/patch identity, agreed review and fixes, release evidence, support coordination |
| Customer platform owner | Cluster/VM, access broker, storage, registry, network enforcement, backups, deployment |
| Customer security owner | Threat model, identity/egress validation, incident process and acceptance of residual risk |
| Customer model owner | vLLM/model licence, parser, capacity, approved gateway and inference limits |
| Customer developer lead | Pilot tasks, developer onboarding, work review and business acceptance |

One person may hold multiple roles, but each responsibility must have a named owner.

## Handover pack

Deliver privately: immutable release IDs and hashes; per-component licence notices;
policy version; network/identity configuration; acceptance/gap record; backup and
rollback procedure; developer instructions with the actual approved access route;
support contacts and entitlement; support expiry/renewal terms; known limitations.

No licence expiry may be presented as revoking prior MIT rights. Rights for any
separately licensed supplier component must be expressly identified in the signed
agreement. Do not introduce a remote kill switch or mandatory internet callback
as an implementation shortcut for a closed environment.
