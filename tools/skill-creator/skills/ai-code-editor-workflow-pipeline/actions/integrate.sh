#!/usr/bin/env bash
set -euo pipefail
# Phase 5b: Remediate — Integrate consolidated patch into target system
# Inputs: CONSOLIDATED_PATCH, BRANCH, COMMIT_MSG
# Outputs: JSON with commit_sha, integration status

echo '{"phase":"integrate","status":"started"}'

BRANCH="${BRANCH:-main}"
COMMIT_MSG="${COMMIT_MSG:-fix: automated code remediation via ai-code-editor-workflow-pipeline}"

if [ -n "${CONSOLIDATED_PATCH:-}" ] && [ -f "${CONSOLIDATED_PATCH}" ]; then
  PATCH_SIZE=$(wc -c < "${CONSOLIDATED_PATCH}")
  if [ "${PATCH_SIZE}" -eq 0 ]; then
    echo '{"phase":"integrate","status":"skipped","message":"Empty patch — no changes to integrate"}'
    exit 0
  fi
  git apply "${CONSOLIDATED_PATCH}" 2>/dev/null || true
fi

# Stage, commit, push
git add -A
CHANGES=$(git diff --cached --stat | tail -1)

if [ -z "${CHANGES}" ]; then
  echo '{"phase":"integrate","status":"skipped","message":"No staged changes"}'
  exit 0
fi

git commit -m "${COMMIT_MSG}"
COMMIT_SHA=$(git rev-parse HEAD)

git push origin "${BRANCH}" 2>/dev/null || {
  echo '{"phase":"integrate","status":"error","message":"Push failed — check permissions"}'
  exit 1
}

cat << EOJSON
{
  "phase": "integrate",
  "status": "complete",
  "commit_sha": "${COMMIT_SHA}",
  "branch": "${BRANCH}",
  "changes": "${CHANGES}"
}
EOJSON