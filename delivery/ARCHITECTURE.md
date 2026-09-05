# Protected developer workspace architecture

Proposed deployment profile; the access broker, gateway and provisioning described here
are integration work, not services already implemented in this repository.

## Trust boundaries

| Component | Authority and data | Boundary |
|---|---|---|
| Customer access platform | Authenticates developer and authorizes their workspace | Must not trust a workspace ID supplied by the client without an ownership check |
| Workspace runtime | Runs the patched CLI, model-generated code and approved shell tools | One developer/workspace; non-root, protected image/policy, scoped storage and enforced network |
| Internal inference gateway | Authenticates workload, maps it to user, enforces exact model and budget | Rejects alternate routes/models even for direct requests from shell |
| Internal vLLM | Hosts pre-staged approved model/tokenizer | No cloud fallback or uncontrolled downloads; gateway is the only intended client |
| Customer operations | Registry, source provisioning, audit and backup | Separate identities from developers; admin changes recorded |
| Supplier maintenance | Builds candidates and handles permitted diagnostics | No implicit access to customer runtime, signing keys or production deployment |

An initial Kubernetes profile may use one namespace per developer/workspace, but a
namespace alone is not a sandbox. Customer security selects container/VM isolation
appropriate to the threat model. Kernel and platform administrators remain trusted.

## Issuing workspaces

Use customer SSO and an existing remote-workspace/bastion system where possible.
The platform creates a runtime from an approved image digest and a private source
snapshot. A developer receives an approved terminal route, workspace identity and
guide, not cluster-admin credentials or a shared shell on an operator host.

The broker must authorize each connection and ownership of the target workspace.
Define and test revocation latency, active-session termination, session expiry and
administrative access. Do not expose OpenCode's local server as a shared multi-tenant
endpoint. IDE access is a separate integration unless explicitly tested.

## Network and credential model

The initial agent runtime may connect only to the approved internal inference
gateway. The existing example blocks general DNS and uses a fixed gateway address.
Test the actual CNI, service NAT, IPv4/IPv6 and metadata destinations.

Git clone/push and dependency downloads need an explicit design: initially pre-stage
the repository and toolchain through a trusted provisioning process and export changes
through a controlled route. If runtime access to internal Git/package proxies is later
allowed, define exact destinations, scoped credentials and tests as a profile change.
An "internal proxy" must not provide an arbitrary internet forwarding path.

Gateway and vLLM also need restricted egress. Workload credentials and user mapping
must be platform-controlled, not just a user-editable header. The client transport
strips personal bearer tokens; integrate identity at the approved gateway/mesh boundary.
See [gateway contract](../enterprise-patches/GATEWAY-CONTRACT.md).

NetworkPolicies require an enforcing network implementation; multiple applicable
policies combine allowed traffic. Audit all policies selecting the workspace rather
than assuming one deny policy overrides broader grants.
[Official NetworkPolicy reference](https://kubernetes.io/docs/concepts/services-networking/network-policies/).

Developers must not create arbitrary pods, change NetworkPolicies, mount host paths,
read other users' secrets or use privileged workloads. Scope platform identities too.
[Official RBAC guidance](https://kubernetes.io/docs/concepts/security/rbac-good-practices/).

## Storage and secrets

The current example uses emptyDir for workspace and state: deletion loses them.
For developer use, implement per-workspace persistent storage or an explicit ephemeral
workflow with successful export before teardown. Decide encryption, quotas, backup,
restore, retention and deletion. Never share session DBs between developers.

No host SSH directory, cloud credentials, container socket or automatic service-account
token is mounted into the agent runtime. The model can read files accessible to that
runtime; prompt instructions do not replace a secret-free filesystem.

## Two delivery modes

1. Internet-restricted runtime: build/import occurs in controlled infrastructure;
   the developer runtime has the approved internal destinations only.
2. Fully disconnected customer network: transfer approved signed packages, images,
   dependencies, model weights and verification material through the customer's
   import process; build/update and support diagnostics must work without GitHub access.

The public GitHub Actions build is internet-connected and is not proof of a disconnected
installation. These modes require different acceptance evidence.

## Audit and updates

Keep identity, approvals/denials, tool actions, configuration versions and release
changes in an internal audit system with defined retention. Gateway logs cover inference,
not all filesystem or shell actions. A SIEM integration is outstanding.

New versions go to staging first; customer operations promote an approved immutable
artifact. Preserve previous image/policy and compatible state backup. No auto-update
from public upstream runs in developer workspaces.
