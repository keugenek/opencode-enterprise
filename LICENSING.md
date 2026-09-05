# Public software and enterprise licensing

The enterprise product comprises maintained patches, prebuilt customer distributions,
build automation, security review, update delivery and support. It is offered
commercially under customer-specific agreements.

## Public materials

The root [LICENSE](LICENSE) remains MIT. Existing public code and patches covered
by MIT retain those permissions. Other components retain their respective notices
and licences. This document does not retroactively withdraw, narrow or replace
permissions already granted for published versions.

Neither the word "enterprise", a compiled binary nor this marketing page alone
creates a new licence restriction. Current public CI artifacts do not receive
an additional usage restriction merely through this document.

## Separately licensed enterprise deliveries

A customer agreement must identify:
- the supplier and customer;
- the exact build, versions and covered supplier-owned components;
- the software rights granted and any applicable deployment/redistribution terms;
- third-party/open-source components and their retained licence notices;
- the included maintenance, security review, patch delivery and support commitments.

Only components for which the supplier holds sufficient rights may receive a
separate commercial licence. Future proprietary components must be explicitly
identified and carry their own licence notice when delivered; no blanket exception
for unmarked public repository files is created here. Any earlier MIT grant for
a version remains available under its original terms.

Security review, maintenance and support are services. Copyright licences and
service commitments are distinct: MIT access does not include an obligation to
provide customer-specific builds, future fixes, support or acceptance work.

## Commercial enquiries

Contact [Eugene Kniazev](mailto:evgeny.knyazev@gmail.com?subject=OpenCode%20Enterprise%20licensing) for an enterprise distribution and an individually
negotiated agreement. Prices and contract details are discussed privately.
This notice is a description of licensing boundaries, not the customer agreement.

## Public development and private delivery

Common enterprise hardening patches, generic settings, build/CI tooling and public
regressions are developed in the public repository under their applicable licences.
Private GitLab consumes reviewed public commits; it does not impose new restrictions
on those public components. Community participation does not require a support purchase.
Customer-specific data, confidential eval, orchestration and separately identified
private components are governed by their own rights, confidentiality and service terms.
See [the development model](community/DEVELOPMENT-MODEL.md).
