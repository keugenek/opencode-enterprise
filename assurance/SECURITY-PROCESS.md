# Internal security operating process

Public process specification for supported enterprise deliveries. It defines work
that must be performed and evidenced; publication alone does not mean the process
is staffed, audited or operating for a particular customer. Assign the roles below
and establish the private systems before accepting a supported pilot.

## Ownership and separation of duties

| Role | Accountability | Required separation |
|---|---|---|
| Supplier security owner | Threat model, vulnerability triage, disclosure and security release recommendation | Can block promotion regardless of delivery targets |
| Supplier release owner | Exact inputs, patch review, build provenance, SBOM/notices, signed artifacts and rollback package | Release credentials unavailable to untrusted builds and remediation agents |
| Independent evaluation reviewer | Approved suite/thresholds, evidence review and signed acceptance report | Does not sign their own unreviewed fix; signer separate from the fixer and public CI |
| Customer platform owner | Cluster/network/access/gateway integrations, deployment, backup, revocation and operational logs | Developers cannot change security policy or other workspaces |
| Customer security/data owner | Data classification, control applicability, evidence retention and risk decisions | Explicit approval before production developer access |
| Customer developer lead | Representative tasks, toolchain validation, cohort onboarding and feedback | Reviews generated code before merging or release |

For a small supplier, an independent reviewer can be a contracted reviewer or the
customer's security team. If that reviewer or trusted signing service is unavailable,
keep the build a candidate. A self-review is not independent acceptance.

## Design and change control

Maintain a private asset/data-flow inventory and threat model covering the client,
agent tools, repository content, model/gateway, access broker, cluster, storage,
build inputs, support channel and maintenance automation. Treat repository text,
model outputs, tool output and submitted bug reproductions as untrusted input.
Consider prompt injection, command execution, data exfiltration, cross-user access,
policy bypass, credential exposure, supply-chain substitution and denial of service.

For every candidate:

1. Record exact upstream commit, patch hashes, dependency lockfile, build toolchain,
   runtime image, model weights/configuration and customer integration revision.
2. Review source/dependency/licence changes and remote feature additions. Recheck
   every modified authorization, configuration, network and tool-execution boundary.
3. Run public regression/build checks; scan the final artifact and image for
   vulnerabilities, credentials and unexpected components. Retain SBOM, notices,
   provenance and findings in the controlled release record.
4. Execute the approved private eval in customer-equivalent isolation. An independent
   reviewer checks raw evidence against the suite and authorizes signing.
5. Verify the signed report, obtain customer change approval, preserve the rollback
   package and release first to the agreed cohort. Record who approved what and when.

Unresolved high/critical findings or failed/skipped required gates block acceptance
under this MVP profile. Lower-severity issues need named owners, compensating controls
where needed, due dates and customer visibility. The public verifier does not manage
that issue register. Changes to scope or acceptance thresholds require a separately
reviewed suite revision before execution; they cannot be improvised to pass a failed run.

## Vulnerability and incident handling

Use [private reporting](REPORTING.md). Triage applicability to the supported version,
reachable component and deployment; record severity, reproduction, affected customers,
mitigation, owner and next update. Initial response and remediation commitments follow
the customer agreement. No public 24/7 service or guaranteed fix deadline is implied.

For suspected active compromise or boundary escape: notify the customer security
contact through the agreed channel, suspend affected access/promotion, preserve
local evidence, contain the affected workspace/gateway and rotate exposed credentials.
The customer incident owner decides operational containment and any external notices.
Record a timeline and test recovery before restoring access. Review the root cause,
add a regression and a held-out variant, and assess other supported releases.

Coordinate upstream disclosure without exposing customer source, identifiers or
private infrastructure. Customer-derived data is shared only with explicit permission.
Maintain an applicability record even when a published upstream issue does not affect
the supported profile. Revisit it after dependency/model/configuration changes.

## Private support and automated maintenance

The planned internal maintenance service belongs in the operator's own private GitLab repository
and segregated infrastructure. Its prompts, evaluators, customer reproductions and
orchestration are not part of this public distribution. The following are design
requirements for that service, not claims that it is already implemented:

- Authenticate intake; isolate tickets, artifacts and workspaces by customer. Agree
  what diagnostic data may leave the customer environment. Prefer minimal synthetic
  reproductions and keep sensitive execution inside the customer network.
- Run reproduction and proposed fixes in disposable isolated workers with least
  privilege. No production credentials, signing keys or customer deployment access.
  A bug report must not be able to instruct the worker to expand its permissions.
- Implement common fixes and regressions in a clean public checkout, publish only after
  data/rights clearance, and consume the merged public commit in GitLab. Customer-only
  overlays and embargoed vulnerabilities follow [the development model](../community/DEVELOPMENT-MODEL.md).
- Let automation propose a reviewed change and public regression. Do not expose the
  held-out eval corpus to the fixing agent or allow it to edit acceptance thresholds.
- Upstream automation can open/update candidate changes on disposable integration
  branches. Merging to a release branch requires required checks and independent
  review; deployment and signing remain separately authorized operations.
- Keep an auditable chain from private request to sanitized reproduction, proposed
  diff, reviewer decision, public regression, private eval and accepted release.
  Never push customer data to public issues or upstream automatically.

## Evidence, privacy and keys

Customer source, prompts, responses, session databases and logs can contain secrets
or personal data. Define collection purpose, minimization, access roles, encryption,
location, retention/deletion periods and approved transfer channels before the pilot.
Do not enable remote analytics to collect these data. The model platform's own logging
and training/retention configuration must be reviewed separately.

Keep signed reports, evidence inventories, scan results and approvals in the customer's
or agreed supplier's access-controlled evidence store. Report hashes identify evidence;
they do not replace evidence retention or prove that an evaluator executed a test.
Use audit events appropriate to access, policy, deployment and incidents. Capture
prompt/tool bodies only when explicitly approved; protect their content accordingly.

Provision the eval public key through an independent customer trust channel; store its
fingerprint with approval. Use an isolated signing service/HSM where available. Private
keys must never enter developer workspaces, the fixing agent, public CI or this repo.
Rotate/revoke compromised keys through that trust channel, invalidate affected reports,
and rerun acceptance as appropriate. Offline verification depends on the operator's
current key inventory and trusted clock; no online revocation service is supplied.

## Review cadence and deliverables

Review risk on every candidate, material integration/model change and relevant new
advisory; review access and retention at the cadence agreed with the customer. Retain
scope, threat model, control matrix, review records, dependency inventory, tests/scans,
private eval report and evidence, signer identity, customer approval and rollback record.
The [compliance matrix](COMPLIANCE.md) maps these work products to external references.
