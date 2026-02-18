#!/usr/bin/env bash
set -euo pipefail
# Phase 5a: Remediate — Consolidate all changes into unified patch
# Inputs: SOLUTION_PLAN, TARGET_PATH
# Outputs: Consolidated patch file

echo '{"phase":"consolidate","status":"started"}'

PATCH_FILE="/tmp/consolidated_patch_$(date +%s).diff"

# Collect all staged and unstaged changes into a single diff
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff HEAD -- "${TARGET_PATH}" > "${PATCH_FILE}" 2>/dev/null || true
  PATCH_SIZE=$(wc -c < "${PATCH_FILE}")

  if [ "${PATCH_SIZE}" -eq 0 ]; then
    echo '{"phase":"consolidate","status":"complete","changes":0,"message":"No changes to consolidate"}'
  else
    LINES_ADDED=$(grep -c '^+[^+]' "${PATCH_FILE}" 2>/dev/null || echo 0)
    LINES_REMOVED=$(grep -c '^-[^-]' "${PATCH_FILE}" 2>/dev/null || echo 0)
    FILES_CHANGED=$(grep -c '^diff --git' "${PATCH_FILE}" 2>/dev/null || echo 0)

    cat << EOJSON
{
  "phase": "consolidate",
  "status": "complete",
  "patch_file": "${PATCH_FILE}",
  "files_changed": ${FILES_CHANGED},
  "lines_added": ${LINES_ADDED},
  "lines_removed": ${LINES_REMOVED},
  "patch_size_bytes": ${PATCH_SIZE}
}
EOJSON
  fi
else
  echo '{"phase":"consolidate","status":"error","message":"Not a git repository"}'
  exit 1
fi