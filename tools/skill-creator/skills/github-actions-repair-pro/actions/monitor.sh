#!/usr/bin/env bash
set -euo pipefail
# One-Stop Repair — Monitor re-run until conclusion

MAX_POLLS=36
POLL_INTERVAL=10

for i in $(seq 1 ${MAX_POLLS}); do
  STATUS=$(gh api "repos/${REPO}/actions/runs" --jq '.workflow_runs[0].conclusion // "pending"')
  echo "[${i}/${MAX_POLLS}] Status: ${STATUS}"

  if [ "${STATUS}" = "success" ]; then
    echo "VERIFIED: Fix confirmed — CI passed"
    exit 0
  elif [ "${STATUS}" = "failure" ]; then
    echo "FAILED: Fix did not resolve the issue"
    exit 1
  fi

  sleep ${POLL_INTERVAL}
done

echo "TIMEOUT: Verification timed out after $((MAX_POLLS * POLL_INTERVAL))s"
exit 1