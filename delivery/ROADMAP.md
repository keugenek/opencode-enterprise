# Delivery roadmap and implementation backlog

Status: pilot delivery backlog. The public MVP toolkit implements static profile
validation, image-context preparation, restricted manifests and signed-report checks.
Those are inputs to ENT-02/04/07; the corresponding customer integration and evidence
are still outstanding until linked results exist.
IDs can be copied into private project tickets; no public customer tickets are created
by this document. Owners are roles from [PILOT.md](PILOT.md), not assigned individuals.

| ID | Priority | Work item / owner | Depends on | Done when |
|---|---|---|---|---|
| ENT-01 | P0 | Private scope and deployment inventory / supplier + customer owners | — | Scope, access/data rules, acceptance thresholds and owners agreed |
| ENT-02 | P0 | Trusted delivery channel / supplier release owner | ENT-01 | Final image pinned, SBOM/scans reviewed, artifacts signed and verifiable inside customer network; notices included |
| ENT-03 | P0 | Single-model inference gateway / model + platform owners | ENT-01 | Actual TLS/workload identity, exact model/routes, quotas and streaming/cancellation pass; no cloud fallback |
| ENT-04 | P0 | Isolated workspace provisioning / platform owner | ENT-01, ENT-02 | Per-developer runtime/storage, restricted privileges, effective egress, protected policy and no cross-user access |
| ENT-05 | P0 | Developer identity and lifecycle / platform + security owners | ENT-04 | Named-user access, broker authorization, join/leave flow, active session revocation and audited admin access tested |
| ENT-06 | P0 | Offline source/toolchain provisioning / platform + developer lead | ENT-01, ENT-04 | Approved project/tests work with runtime internet blocked; credentials are not mounted into agent runtime |
| ENT-07 | P0 | Real-model and security acceptance / security + model owners | ENT-03–06 | Existing deployment gates plus lifecycle, restore and representative coding tasks pass with retained evidence |
| ENT-08 | P0 | Backup, rollback and revocation / platform owner | ENT-04–05 | Workspace restore, supported session-state rollback, old artifact availability and denied stale sessions demonstrated |
| ENT-09 | P0 | First paid cohort / developer lead + supplier | ENT-07–08 | Named cohort onboarded, first tasks reviewed, handover signed and support route exercised |
| ENT-10 | P1 | Private support intake / supplier | ENT-01 | Private tenant-separated tickets, redacted reproductions, severity routing, retention and disclosure permission recorded |
| ENT-11 | P1 | Maintained release process / supplier + customer platform | ENT-02, ENT-07, ENT-10 | Candidate → staging → accepted release → approved rollout; regression evidence and rollback retained |
| ENT-12 | P1 | Upstream update integration / supplier | ENT-11 | Exact upstream input, licence/dependency diff, patch applicability and mandatory risk review before promotion |
| ENT-13 | P1 | Internal remediation service / supplier, private repository | ENT-10–12 | Isolated reproduction and independent acceptance; no signing/deployment authority in the fixer; customer data boundaries tested |
| ENT-14 | P2 | Additional users/environments / customer owners | ENT-09–11 | Capacity, isolation and service coverage re-assessed before expansion |

## Suggested sequence

First scope and infrastructure prerequisites; then build/gateway/workspace integration;
then real-model and security acceptance; then a small developer cohort; finally repeatable
maintenance and expansion. Dates and estimates are agreed only after customer discovery.
A licence sale or green build does not satisfy ENT-07.

## Initial product boundaries

- Linux x64/glibc (AVX2), CLI/TUI, one fixed model and one project stack.
- Public four-patch profile stays reviewable; customer configurations and maintenance
  internals belong in private systems.
- No public automated-fixer prompts, scoring rules or orchestration implementation.
- No new proprietary functionality is assumed to exist because it appears in this roadmap.
- Prefer existing customer identity, registry and workspace services to building a new portal.
- Defer additional providers, general MCP/plugin loading, desktop clients and 24/7
  commitments until they have a separate supported profile and resourcing.

## Pilot measures

Record baseline and pilot values: completion/quality of agreed coding tasks, time to first
use, successful session rate, inference latency/concurrency, support engineering effort,
time to reproduce a bug, accepted-fix rate and rollback success. Record security gate
results independently of productivity. Choose numeric thresholds with the customer;
none is fabricated as an achieved result here.

## Release condition

P0 work must be complete or explicitly scope-adjusted by the customer before developer
rollout. An exception record is not permission to silently bypass a failing security
boundary. A failed model restriction, cross-user isolation or external egress test blocks
the corresponding protected deployment until corrected or the architecture is changed.
