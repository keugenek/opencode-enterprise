#!/usr/bin/env bash
set -euo pipefail
binary="$(realpath "$1")"
expected_version="$2"
[[ "$("$binary" --version)" == "$expected_version" ]]
models="$(OPENCODE_CONFIG_CONTENT='{"model":"openai/forbidden","permission":"allow","provider":{"evil":{"npm":"untrusted"}}}' "$binary" models)"
[[ "$models" == 'enterprise/enterprise-coder' ]]
for flag in --auto --yolo --dangerously-skip-permissions; do
  if "$binary" "$flag" --version > smoke-denial.log 2>&1; then
    echo "Permission bypass flag unexpectedly accepted: $flag" >&2
    exit 1
  fi
  grep -q 'Auto-approval is disabled in the enterprise CLI' smoke-denial.log
done
# The policy is managed by the disposable runner, not bundled into the binary.
privileged=()
if [[ "$(id -u)" != 0 ]]; then privileged=(sudo); fi
"${privileged[@]}" mv /etc/opencode/enterprise.json /etc/opencode/enterprise.json.ci-backup
trap '"${privileged[@]}" mv /etc/opencode/enterprise.json.ci-backup /etc/opencode/enterprise.json' EXIT
if "$binary" --version > smoke-missing-policy.log 2>&1; then
  echo 'Missing policy unexpectedly accepted' >&2
  exit 1
fi
grep -q 'enterprise.json' smoke-missing-policy.log
