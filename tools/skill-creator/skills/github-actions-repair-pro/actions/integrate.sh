#!/usr/bin/env bash
set -euo pipefail
# One-Stop Repair — Apply consolidated patch, commit, and push

if [ ! -f consolidated_patch.diff ]; then
  echo "ERROR: consolidated_patch.diff not found"
  exit 1
fi

git apply consolidated_patch.diff
git add -A
git commit -m "${COMMIT_MSG:-fix: automated CI/CD repair}"
git push origin "${BRANCH:-main}"

echo "Fix committed and pushed to ${BRANCH:-main}"
git log --oneline -1