# Private GitLab consumption contract

This file specifies integration into the operator's own GitLab. No GitLab host,
project, credential, private corpus or customer configuration is provisioned by this
public repository. Keep the private pipeline definition in that private project.

## Recommended layout

Use one public product repository for common engineering and one private delivery
repository for orchestration and overlays. For multiple customers, isolate data,
permissions, artifacts and execution per customer; one private repo does not itself
provide tenant isolation.

The private delivery inventory pins:

- `public_repository`: approved canonical public repository URL;
- `public_commit`: full reviewed commit SHA, never a moving branch or `latest`;
- `artifact_digest` and release provenance/signature, when consuming a built artifact;
- private integration revision, model revision, customer profile and approved eval suite;
- approved public source/build tooling version and private overlay revision.

The inventory belongs in private GitLab. Credentials and keys belong in a secret
manager or protected signing service, not in this inventory or Git history.

## Import and validate

1. A trusted operator or scheduled private import job fetches the approved public
   commit/artifact with read-only access. Verify origin, commit/digest, notices and
   provenance using the agreed trust channel. A hash alone is not origin verification.
2. A disposable worker builds/tests public code with no customer secrets, signing
   credentials, public write token or privileged host access. Do not execute public
   repository CI YAML with private CI privileges.
3. Pass the resulting artifact by digest to a separate environment that adds the
   approved runtime policy/overlay. Use the public schemas/toolkit rather than copied
   private implementations of the same code.
4. Run the private suite in an isolated environment with only the approved test data
   and model access. The fixing worker must not read the held-out corpus or change
   acceptance thresholds. Corpus, evidence and scoring internals stay private.
5. Independently review results, sign through a separate service and verify the public
   report contract. Customer operators approve deployment and retain rollback evidence.

Only stage 1 needs public retrieval. For an air gap, the same reviewed input and
provenance can pass through the customer's approved offline import process.
Public PRs and mirror updates must not automatically trigger secret-bearing eval,
privileged runners, signing or deployment. Protected refs alone do not make fetched
public code trustworthy.

## Optional one-way mirror

An internal mirror can cache public branches/tags for availability. It is a separate
public-source mirror project with no private files or local product commits. Do not
push that mirror back to GitHub or mix customer branches into it. Do not use bidirectional
mirroring between a customer repository and the public product.

GitLab's built-in pull mirroring currently requires Premium or Ultimate. Its docs
recommend making changes in the upstream source rather than pushing to the downstream
mirror; they also describe the risks of triggering pipelines on mirrored content.
Use normal `git fetch`/verified artifact import if that feature is unavailable.
See [GitLab pull mirroring](https://docs.gitlab.com/user/project/repository/mirror/pull/).

No paid mirroring feature is required for the development model. The public commit
is the interface, and GitLab's private pipeline decides which commit to consume.

## Publishing a general fix from private intake

A private worker can prepare a proposed diff on a clean public checkout. A separate
review step checks the diff, commit messages, fixtures and attachments for confidentiality
and rights. The publisher receives only the sanitized public bundle. Keep private ticket
links in private records; the public PR may have an unrelated public issue reference.
No automatic customer-to-public issue mirroring is configured.

If an emergency private fix is unavoidable, follow the temporary embargo procedure in
[DEVELOPMENT-MODEL.md](DEVELOPMENT-MODEL.md). Once disclosed, consume its public commit
and remove the corresponding private overlay.
