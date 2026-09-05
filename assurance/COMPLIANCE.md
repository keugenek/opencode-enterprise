# Security and compliance evidence matrix

This is a public readiness framework for customer due diligence, not an audit report
or certification. Legal/regulatory applicability, contractual controls and data roles
must be determined for the customer and deployment. No ISO 27001, SOC 2, GDPR or other
certification/compliance conclusion is asserted by this repository.

The control grouping below is our implementation mapping. It draws on the secure
software lifecycle in [NIST SSDF / SP 800-218](https://csrc.nist.gov/projects/ssdf) and
AI risk governance/evaluation in the voluntary
[NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework).
These references provide guidance; a mapping is not evidence that a control operates.

| Control area | Accountable owner | Evidence required for customer acceptance | Public repository status |
|---|---|---|---|
| Governance and supported scope | Supplier + customer security owners | Named roles, contract scope, threat model, asset/data-flow inventory and risk register | Process and pilot templates |
| Software input and release integrity | Supplier release owner | Upstream/patch/dependency identities, build record, SBOM, reviewed findings, licence notices and artifact signature | Pinned patch/build workflow and checksum manifests; final-image SBOM/signing remain required |
| Change control and separation of duties | Supplier security/release owners | Reviewed diff, protected release permissions, independent eval approval, customer change record | Required process; repository protection and private signer access must be configured and evidenced |
| Model risk and effectiveness | Model owner + evaluator | Approved fixed model, suite/thresholds, actual functionality and reliability measurements, limitations | Model restriction patches, public tests and private report contract; no completed private evaluation |
| Access and tenant isolation | Customer platform owner | Broker/SSO authorization, two-user isolation tests, administrative access review and revocation evidence | Restricted per-workspace manifests; broker/identity lifecycle supplied by customer |
| Network/data boundaries | Customer platform + data owners | Effective CNI/egress probes, gateway workload auth, no cloud fallback, approved source transfer | Egress manifest and transport restrictions; effective infrastructure verification outstanding |
| Data handling and privacy | Customer data owner + supplier support owner | Data classification, collection purposes, approved transfers, retention/deletion, backup and model logging/training settings | Public handling requirements and private support templates |
| Logging and incident response | Customer incident owner + supplier security owner | Internal audit pipeline, protected event access, incident exercise, notification/escalation contacts | Process specified; customer's audit integration/exercise required |
| Vulnerability management | Supplier security owner | Applicability triage, severity, owners, remediation/workaround, disclosure and regression evidence | Technical source review and reporting route; staffed service scoped by contract |
| Continuity and recovery | Customer platform owner | Backup/restore exercise, compatible rollback, session revocation and recovery measurements | Runbooks and mandatory private eval gate |
| Supplier and open-source obligations | Supplier + customer procurement/legal owners | Components and rights inventory, customer terms, service scope, subcontractors and data-handling agreements where applicable | MIT retained; commercial boundaries documented; customer contracts private |

## Evidence package and boundaries

Keep the completed package in the approved private system: scope and inventory,
control owners, signed release manifest, SBOM/scan/licence records, threat model,
review decisions, private eval report and underlying evidence, exception register for
lower-severity findings, customer approval, incident contacts and tested rollback.
The public [acceptance record](../delivery/templates/ACCEPTANCE-RECORD.md) provides a
starting structure; the customer can require additional evidence.

Current source restrictions do not constitute regulatory compliance, formal
non-interference, a complete sandbox or full elimination of vulnerable dependencies.
The customer platform's identity, network, storage, model service and operational
processes are material to the result. Reassess after material changes and at the
agreed review cadence.

See [security process](SECURITY-PROCESS.md), [private eval](PRIVATE-EVAL.md) and
[licensing boundaries](../LICENSING.md). Supplier-owned private tooling and acceptance
services can be scoped commercially without narrowing existing public MIT rights.
