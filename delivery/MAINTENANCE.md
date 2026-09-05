# Maintenance and update operating contract

Public process boundaries for a customer agreement. Internal remediation implementation,
agent prompts, evaluation rules and orchestration remain in private supplier systems.
This document is not a statement that those systems have been built.

## Entitlement and service scope

Record supported release/configuration, service dates, support contacts, private channel,
response targets, security escalation and planned update window in the customer agreement.
Separate a product defect from infrastructure support or a feature request. Do not charge
per submitted bug by default; define included diagnosis and separately approved custom work.

Keep commercial entitlement in the service relationship/customer records. No internet
licence server or automatic runtime shutdown is added to this closed-runtime design.
Software rights and update/support entitlement are distinct; see [LICENSING.md](../LICENSING.md).

## Private bug workflow

State progression: received → triaged → awaiting reproduction / reproduced → candidate →
validation → accepted update / workaround / documented disposition → customer verification.

For each ticket, retain tenant, supported build, impact, evidence permissions, owner,
next update time and final disposition. "Received" is not a guarantee of a fix. Store
attachments outside the public repository; redact secrets and minimise source exposure.
Do not combine different customers' workspaces or diagnostic data.

A suspected vulnerability follows the customer's security escalation and agreed
disclosure process. Respect any embargo. General upstream disclosure requires an
explicit rights/confidentiality check before publication.

## Fix and release boundaries

Treat ticket text, logs, customer code, dependencies and upstream patches as untrusted.
Execute reproductions only in isolated disposable environments without production or
release credentials. Customer data must not be sent to external AI services without
explicit agreement of scope and processing arrangements.

Require a reproduction or clear diagnostic evidence and a regression check for a fix.
The fixer must not approve its own removal/weakening of independent acceptance gates.
Signing and customer deployment credentials remain outside the repair environment.
Common fixes and regressions are authored in a clean public checkout and reviewed in
public PRs after reproduction/data clearance. Private GitLab consumes their exact merged
commits. Customer-only adapters stay in a thin private overlay; do not copy common
runtime modules into a private product branch. Confidential vulnerabilities use a
temporary embargo branch and coordinated disclosure. See
[the public development model](../community/DEVELOPMENT-MODEL.md).

## Upstream updates

Use the [public candidate checker](../community/UPSTREAM.md) as the common update path.
GitLab consumes its reviewed public outcome rather than maintaining another upstream merge.


1. Pin the candidate upstream commit and record licence/dependency/configuration diffs.
2. Apply the maintained patch series in an integration branch and check every hunk.
3. Run regression, compilation and the affected deployment acceptance tests.
4. Require review for auth, provider routing, network, telemetry, policy precedence,
   permissions, secrets, dependencies, CI/signing or licensing changes.
5. Promote an accepted candidate to staging and an agreed release channel.
6. Customer operations approve deployment according to their maintenance policy.

Automerge may be enabled later for a narrowly defined class of reviewed low-risk changes
into the integration branch. It must stop on conflicts, changed security boundaries,
failing checks or missing evidence. It never means automatic upstream deployment to
customer production. No automerge service is implemented by this document.

## Release evidence and rollback

Retain source and policy identity, patch list, test results, SBOM and vulnerability
disposition, signatures, licence notices, compatibility notes, migration/rollback
instructions and supported-version window. Public CI currently implements only a
subset; [ROADMAP.md](ROADMAP.md) tracks the missing work.

Use canary/staging before wider rollout. Keep the previous supported artifact and
compatible data backup. Test cancellation, restart, permissions and user access after
upgrade. Archive a completed [acceptance record](templates/ACCEPTANCE-RECORD.md) privately.

## Support boundaries

The customer runs its incident response, infrastructure and data recovery unless
expressly purchased otherwise. Resolution times, credits, 24/7 coverage, update cadence
and custom integrations must be expressly agreed and resourced. Do not turn planned
automation into an unlimited contractual promise.
