# Required inference gateway contract

The distribution calls only `POST https://inference.internal/v1/chat/completions`.
The example hostname, private IP and model name are placeholders. No actual vLLM endpoint was supplied.

The gateway is a separate administrative boundary. It MUST:

- Authenticate the workload using platform-controlled identity, e.g. mTLS at the gateway/mesh boundary. This patch's transport intentionally sends no personal API token. Do not expose an unauthenticated inference service to an untrusted network.
- Authorize one exact `model` value, `enterprise-coder` in the example, including requests made directly from shell tools. Reject alternate models; never route through fallback/cloud providers.
- Forward to exactly one preconfigured vLLM deployment and set the upstream model ID itself. vLLM should run only the approved model, with the matching `--served-model-name` and model-appropriate tool-call parser/chat template.
- Accept Chat Completions with streaming and tool calls. Reject redirects, remote media fetching, unsupported routes, unknown passthrough routing fields and provider credentials supplied by the client.
- Enforce request/context/output limits, per-user/workspace token budget, concurrency, timeout, cancellation and rate limits. Do not depend only on the agent's token estimate or client-supplied username.
- Log request ID, workload identity, policy version, model, token counts, outcome and latency to an internal audit sink. Prompt/source-code logging is off by default and requires a separate retention/access decision.
- Deny internet egress on the vLLM/gateway hosts as well as on the agent container. Pre-stage weights and tokenizers; disable runtime model downloads and unreviewed remote model code.

This repository supplies the client restriction and an agent network-policy template, not your gateway implementation or identity integration. A gateway with these properties is a release prerequisite.
