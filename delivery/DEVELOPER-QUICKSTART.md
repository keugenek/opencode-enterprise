# Developer quickstart

Template issued by your company after deployment acceptance. Ask your platform team
for the approved access route, workspace, repository/export instructions and private
support contact. This repository does not yet provide a self-service access portal.

## Start work

1. Open the company-provided terminal route and authenticate with your individual
   corporate identity. Use the workspace assigned to you.
2. Confirm your project is present in /workspace and understand whether work/session
   state persists after logout or workspace deletion.
3. Run the following inside that managed workspace:

```sh
cd /workspace
opencode --version
opencode models
opencode
```

The model list should contain only the company's fixed enterprise model. You do not
need a personal cloud API key. If policy is missing or the model/endpoint differs
from the issued instructions, stop and report it to the platform team.

## First task

Use an approved small task: inspect an existing test, ask for a narrow change,
review requested tool actions, run the project's existing tests, then inspect the
diff and submit it through your normal review process. An agent's output is not
an approved merge, deployment or guarantee of correctness.

Shell and editing actions may require approval. Approving a command allows that
action; it is not a security assessment of the command. Denied web/cloud/MCP/plugin
features are part of this profile. Request a platform change through your support
route rather than trying to bypass the controls.

## Save and share work

Use the issued repository/export process. Never assume a temporary workspace is backed
up. Do not use public session sharing or external upload services for source/logs.
No personal SSH keys, cloud tokens or other production secrets belong in the workspace.

## Report a problem

Use the company-approved private support route with the version, workspace reference,
time, impact and a minimal sanitised reproduction. Use
[BUG-REPORT.md](templates/BUG-REPORT.md). Confirm attachment contents before submitting.
Do not place customer information in public issues or send secrets by ordinary email.

For suspicious access or possible data exposure, follow your company's incident process
immediately. A bug ticket does not replace incident response.

## Access or feature changes

Additional repositories, dependencies, tools, models, quotas or supported environments
require approval by the company platform owner. They may require a new supported profile.
Your company owns decisions about access, data retention, updates and leaving the service.
