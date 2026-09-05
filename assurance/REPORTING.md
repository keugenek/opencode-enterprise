# Private security reporting

For a supported enterprise deployment, use the secure support/incident channel and
contacts named in your agreement. Follow the customer's incident process for suspected
active compromise; a public issue tracker is unsuitable for sensitive evidence.

If no secure channel has been agreed, contact
[Eugene Kniazev](mailto:evgeny.knyazev@gmail.com?subject=OpenCode%20Enterprise%20security%20contact)
with a high-level request to establish one. Do not email credentials, customer source,
private exploit artifacts, network diagrams or raw session data in that first message.
No 24/7 monitoring or response SLA is implied by this public contact address.

Once a secure channel is established, provide the enterprise build/patch identity,
supported configuration, impact, minimal approved reproduction, observed versus
expected behavior and a safe contact route. Redact customer data and secrets. Agree
what may be retained, reproduced or shared with upstream before transfer.

Security findings follow the [internal security process](SECURITY-PROCESS.md).
Non-sensitive public bugs may use the repository tracker; customer-specific bugs use
[the private support template](../delivery/templates/BUG-REPORT.md). Private reporting
and triage do not promise that every request will be implemented.
