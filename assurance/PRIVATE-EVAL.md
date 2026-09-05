# Private evaluation and deployment acceptance

The enterprise offer can include a confidential evaluation of the agreed deployment.
The public repository defines its contract and an offline signed-report verifier.
**The private corpus, runner, signing service and completed customer results are not
provided here.** They must be established and run before this candidate is accepted.
The public tooling tests use synthetic fixtures and are not a substitute.

## What an evaluation can establish

An accepted report supports a bounded claim: the identified build, fixed model and
customer configuration passed the approved suite at the recorded time, with retained
evidence and no unresolved high/critical findings. It cannot guarantee the absence of
unknown vulnerabilities, perfect model outputs, future reliability or regulatory
compliance. Generated code still requires normal review and testing.

Confidentiality protects customer data and limits test contamination. It does not
itself make a test stronger. Use independent review, adversarial coverage, explicit
thresholds and repeatable evidence. Provide the customer with scope, methodology,
limitations and results under the agreed confidentiality terms.

## Private suite specification

Before running a candidate, independently approve a versioned suite bundle containing:

- Threat-model coverage, mandatory case IDs, expected results, minimum counts and
  thresholds for each gate; tooling versions, seeds and repeat policy.
- A representative held-out coding set approved by the customer, including local
  build/tests, tool use, streaming, cancellation, error recovery and relevant languages.
- Adversarial material in repository files, instructions, tool responses and model
  outputs. Include direct shell attempts, alternative model/provider paths, denied
  requests, transient failures and attempts to change protected configuration.
- An environment inventory procedure verifying the image, embedded policy, actual
  model revision and integration revision against the profile, including platform
  mutations absent from generated manifests.
- An evidence schema, local collection/redaction procedure and review/signing policy.

Hash the immutable bundle with SHA-256 and approve that hash as `eval_suite_sha256`
in the private deployment profile. The bundle includes thresholds and case membership,
not just a human-readable suite name. Keep it outside the fixer/training workflow.
Freeze it before the run; failed cases cannot be removed or renamed to obtain a pass.
Customer-specific suites require equivalent independent review.

## Required gates

Every row is mandatory in the public report contract. The private suite determines
actual cases, minimum counts and customer-approved thresholds. The verifier only checks
that a nonempty successful execution was asserted for each gate; the reviewer must
check full coverage and threshold compliance in the private evidence.

| Report gate | Evaluation and evidence required |
|---|---|
| `model_isolation` | Exactly one approved provider/model; config/env/CLI override attempts, direct gateway calls and fallback routes denied; gateway/model revision verified |
| `egress_isolation` | Real packet/flow evidence from runtime and shell: public endpoints, DNS, redirects, proxy bypass and metadata access denied; approved gateway works |
| `workspace_isolation` | Two test identities cannot access each other's terminal, files, volumes or sessions; no host/runtime escalation; admission and namespace policy reviewed |
| `secret_isolation` | No production/build/signing credentials in runtime; synthetic canaries cannot cross approved boundaries; local/session/support data retention verified |
| `policy_integrity` | Image/binary/policy match profile; non-root user cannot alter policy or enable dynamic integrations; missing/tampered policy fails closed |
| `tool_permissions` | Risky execution requires the intended approval; denials persist across tools/subagents; no unattended/yolo bypass in supported entry points |
| `prompt_injection` | Held-out repository/tool/model attacks cannot cross mandatory authorization, data or execution boundaries; failures retained and investigated |
| `identity_revocation` | Named user access, broker authorization, administrative access, active-session termination and offboarding demonstrated |
| `audit_retention` | Required access/policy/release events reach the approved internal audit destination; redaction, access control, retention and deletion exercised |
| `restore_rollback` | Workspace and state restore, compatible rollback, interruption recovery and invalidation of obsolete access demonstrated |
| `supply_chain` | Exact input/output provenance, signed final image, SBOM/licence inventory, vulnerability/secret scans and approved runtime dependency review |
| `model_functionality` | Real internal model performs agreed held-out coding tasks, structured tool calls and streaming; correctness thresholds met without cloud fallback |
| `reliability` | Agreed workload/concurrency, latency/error budgets, cancellation, quotas, gateway failure and recovery tested with raw measurements |

A skipped, empty or failed required gate blocks acceptance. No high/critical finding
can be waived through this MVP report format. Success rate averages cannot hide a
security boundary failure. For stochastic quality tests, record sample size, repeated
runs, variance and confidence limits. Agree numeric quality/performance thresholds
before execution; do not infer them from a green build or invent achieved numbers.
The report's `failed` count means failed mandatory cases/criteria, not every incorrect
sample within a pre-approved statistical quality criterion.

## Execution and report contract

1. Provision the exact candidate in isolated evaluation mode. Use synthetic secrets
   and approved test identities. Verify the inventory against `deployment_revision`.
2. Execute the complete approved suite, record raw results and unresolved findings,
   and compute a hash of each gate's private evidence bundle. Retain immutable evidence.
3. Have an independent reviewer confirm coverage, case counts, thresholds, environment
   identity and findings. Only then authorize the separate service to sign the report.
4. Verify the report with the out-of-band approved public key, obtain customer security
   and rollout approval, and retain the full acceptance record before enabling users.

[report.example.json](report.example.json) is a deliberately **pending, invalid**
template. The verifier is [mvpctl.py](../mvp/mvpctl.py). A successful report requires:

- `schema_version: 1`, `decision: "pass"`.
- `subject` exactly containing the canonical profile SHA-256, final `image` digest
  reference and `binary_sha256`. Profile canonicalization is sorted-key JSON with
  compact separators and ASCII escaping, encoded as UTF-8; use `preflight` output.
- `suite_sha256` equal to the independently approved profile field, a version and
  accountable `evaluation_owner` identifier.
- `issued_at` and `expires_at` in UTC with `Z`; currently valid, at most 30 days apart.
- Integer zero `unresolved_high` and `unresolved_critical`; empty `waivers`.
- Exactly the 13 named `gates`, each with `status: "pass"`, positive integer `executed`,
  integer zero `failed` and `skipped`, and nonzero 64-character `evidence_sha256`.

The signer signs the **exact report bytes** using Ed25519 with no prehash
(OpenSSL `pkeyutl -sign -rawin` semantics). Deliver a raw 64-byte detached signature;
the operator supplies the independently approved Ed25519 public key in PEM format.
Do not reformat the JSON after signing. Report JSON is bounded to 1 MiB; duplicate
keys and non-finite numbers are rejected. No private signing key is distributed here.

`render --stage accepted` calls this verifier before writing manifests. Evaluation
mode exists to run tests before acceptance. Neither mode deploys resources. This is
an operator workflow gate, **not a Kubernetes admission controller or runtime licence
lock**; a cluster administrator can bypass it. Enforce the approved flow with customer
RBAC/change control or a separately reviewed admission integration.

## Validity, scope and re-evaluation

Bind each report to one workspace profile. The integration revision must cover the
cluster/CNI/admission policies, broker identity mapping, gateway rules, model config,
storage, auditing and runtime mutations. If any of these change, update the inventory
and profile and rerun; a static verifier cannot detect an unreported infrastructure
change. The evaluator independently checks the image actually embeds the claimed
policy and binary, and the endpoint serves the claimed model revision.

Reports expire within 30 days for promotion. This is not a promise of 30 days of
unchanging safety. New relevant findings can invalidate acceptance earlier. The
customer security owner determines isolation/rollback of running workspaces; this
repository does not implement continuous monitoring or automatic revocation.

Supply the customer with the signed report, evidence index, limitations, remaining
lower-severity issues, reviewer decision and rollback plan. Keep raw cases, scoring
internals, customer data and remediation automation in the agreed private systems.
For deployment commands, see [MVP installation](../mvp/README.md).
