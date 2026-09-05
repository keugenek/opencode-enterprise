# Deployment acceptance gates

Run in an isolated test namespace using the exact candidate image, internal CA and gateway. Retain network-flow logs. These are release gates, not checks claimed to have run in this development environment.

1. Valid workload: one fixed model listed, normal chat, streamed tool call, approved edit, test command, cancellation, compaction and subagent all work with the same internal model. Confirm tool parsing with the actual vLLM model.
2. Reject missing/invalid policy, symlinked or writable policy; run as non-root and verify modifying `/etc/opencode`, `/usr/local/bin/opencode` and the image is denied.
3. Preload malicious user/project configs, config-content env, provider API keys, `small_model`, custom provider NPM package, local plugin, `.opencode/tool`, custom formatter/LSP and MCP. Confirm none causes execution or network access before the trusted config is loaded.
4. `--model openai/anything`, another internal model, provider config API mutations and auth additions must fail. `--auto`, `--yolo` and `--dangerously-skip-permissions` must fail; TUI must have no auto-approve toggle.
5. Outbound network attempts from Bash, Python, curl, Node and child processes to internet IPs, cloud endpoints, arbitrary DNS, RFC1918 hosts other than the gateway, IPv6 and `169.254.169.254` must fail. Check CNI is effective, not merely accepting the YAML.
6. Direct shell request to the approved gateway with a different `model`, routing headers, SSRF media URLs or unlimited token budget must be rejected by the gateway.
7. Gateway 301/302/307/308, invalid TLS, bad hostname, unavailable gateway and model errors must never produce a cloud fallback. Validate SSE abort closes upstream inference and releases the concurrency slot.
8. Turn on OTEL variables, sharing and auto-update flags. Capture traffic throughout startup, prompt, subagent, idle, shutdown, error and restart. Expected destinations: approved internal gateway only.
9. Exercise prompt injection trying to read SSH keys, cloud credentials, service-account token and host files. These must be absent from the container, irrespective of what the model agrees to do.
10. Verify internal audit identity, policy/model version, tool approval/denial coverage, export ACLs, TTL, deletion and incident kill switch. Gateway logs alone do not audit every filesystem/tool action.
11. Scan the final image/SBOM and dependencies, review upstream advisories, pin image and lockfile, sign the release, test upgrade rollback. Run one-user/one-container initially; do not expose the local server as a shared multi-tenant service.
12. Do not grant developers pod update/exec into other users' workspaces, privileged workload creation, hostPath mounting or NetworkPolicy mutation rights. Apply resource quota and per-workspace authorization in the platform.
