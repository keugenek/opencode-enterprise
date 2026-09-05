# Public engineering and private customer delivery

The shared distribution has **one source of truth: this public repository**.
Enterprise hardening is developed here with public review and regression tests.
Private GitLab consumes approved public commits; it is not a second development
branch of the common harness. This operating model applies to future work and does
not assert that a GitLab project or its integrations have already been installed.

## Where work belongs

| Material | Canonical home | Direction |
|---|---|---|
| General harness fixes, enterprise patches and policy enforcement | Public GitHub | Public review first; consumed by GitLab at an exact commit |
| Generic deployment defaults, configuration schema and sanitized examples | Public GitHub | Shared by community and customer builds |
| Common build scripts, CI, packaging, update tooling and regression tests | Public GitHub | One implementation; reusable from the private pipeline |
| Public threat model, security process and report-verification contract | Public GitHub | Inspectable controls and contribution interfaces |
| Public bug reports, non-sensitive feature requests and reproducible fixtures | Public GitHub | Maintainer/community review; no paid contract required |
| Real customer profiles, endpoints, code, traces, prompts and diagnostics | Customer-controlled private GitLab/projects | Never mirrored into public GitHub |
| Held-out eval corpus, scoring internals and customer results | Private GitLab / approved evidence store | Public report schema; confidential cases and results |
| Remediation orchestration, fixer prompts and internal business tooling | Private GitLab | Uses a clean public checkout to propose general fixes |
| Customer-specific integration adapters with confidential requirements | Private GitLab | Thin overlay consuming public APIs; not a fork of common runtime modules |
| Contracts, entitlement, pricing, operational inventories | Private business/GitLab systems | No public publication |
| Signing keys, production credentials and tokens | Approved secret manager / signing service | References in private config; never committed, even to private Git |

The fact that a patch was funded by a customer does not make the general-purpose
implementation private. Sensitive input and shared implementation are separate work
products. Public examples use invented data and local fixtures approved for publication.

## The normal bug-to-fix path

1. Triage the private ticket in the customer's boundary. Record data permissions,
   supported public commit, impact and whether disclosure would expose a vulnerability.
2. Produce a minimal synthetic reproduction/specification containing no customer
   source, secrets, identifying paths, screenshots, hostnames, hidden eval cases or
   private ticket links. Review it for confidentiality and publication rights.
3. Create the shared fix and its public regression **in a clean checkout of the public
   repository**. A private worker may execute that checkout; where the worker runs
   does not change where the shared code belongs.
4. Open a public PR with the reproduction, implementation, evidence and upstream
   applicability. Maintain attribution for every contributor; AI-assisted changes
   remain the submitting contributor's responsibility.
5. Merge after review and public checks. Update only the consumed public commit/artifact
   in private GitLab, then run private acceptance and approve customer rollout.

No normal cherry-pick or backport from a private product fork is needed: the fix begins
in the public source tree. The private worker exports only the reviewed public patch;
a bot authorized to publish must receive a sanitized bundle, not the customer checkout.
Keep production/signing/public-write credentials outside the reproduction/fixer worker.

Customer-only overlays stay private. When an overlay reveals a reusable capability,
first define a public interface and synthetic tests; implement the common capability
publicly. Do not let private copies of core/provider/policy files accumulate.

## Embargo and emergency exception

An actively exploitable issue or confidential vulnerability may need a temporary,
access-restricted security branch and coordinated disclosure. Do not publish a
reproduction or fix if its diff would reveal an embargoed issue. Record an owner,
public base commit, rationale and planned disclosure checkpoint.

At disclosure, publish the reviewed general fix and an appropriate public regression,
then replace the temporary private delta with the public commit. Backport to agreed
supported release lines where needed. This narrow exception means zero private-to-public
transfers cannot honestly be promised for every security incident; the objective is to
avoid a permanently diverged private product. Support-line backports and upstream rebases
may still be required regardless of hosting platform.

## Community participation

Community contributors can build and test the public distribution, review patches,
submit fixes and use the public software under its licence. Common hardening features,
configuration schemas and regressions are not paywalled. A commercial agreement buys
scoped delivery and service commitments, not priority over the correctness of a change.

Use [CONTRIBUTING.md](../CONTRIBUTING.md). Maintainers curate small tasks in build
portability, negative regression coverage, documentation and public upstream comparison.
Use `good first issue` / `help wanted` only when the task has a reproduction, acceptance
criteria and a reachable reviewer. Labels/issue queues are not created by this document.

Review criteria are public: supported-profile fit, reproducible behavior, meaningful
regression, no weakened boundary, compatible licence/attribution and maintained build.
No secret test corpus is needed to contribute; a private eval can block a customer's
promotion without becoming an undisclosed condition for an ordinary public PR.

## GitLab consumption and trust boundary

Use [the private GitLab integration contract](GITLAB.md). The public project never
needs a GitLab credential or customer webhook. Private CI retrieves an approved public
commit or signed artifact; public CI never retrieves private source. An optional GitLab
mirror contains **public code only**, with no independent changes or customer branches.

A future standalone public product repository can host these same files and workflows,
with OpenCode fetched at the pinned baseline. Migration is a separate operation; the
current fork and PR history remain intact. Naming must distinguish this independent
distribution from the upstream's own enterprise service.
