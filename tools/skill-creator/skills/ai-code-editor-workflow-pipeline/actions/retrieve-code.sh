#!/usr/bin/env bash
set -euo pipefail
# Phase 2a: Retrieve — Code repository, dependencies, git history
# Inputs: TARGET_PATH, REPO
# Outputs: JSON with code_snippets, dependencies, git_history

echo '{"phase":"retrieve-code","status":"started"}'

# Collect dependency info
DEPS="[]"
if [ -f "requirements.txt" ]; then
  DEPS=$(cat requirements.txt | grep -v '^#' | grep -v '^$' | head -20 | python3 -c "
import sys, json
deps = [line.strip() for line in sys.stdin if line.strip()]
print(json.dumps(deps))
" 2>/dev/null || echo "[]")
elif [ -f "package.json" ]; then
  DEPS=$(python3 -c "
import json
d = json.load(open('package.json'))
deps = list(d.get('dependencies', {}).keys())[:20]
print(json.dumps(deps))
" 2>/dev/null || echo "[]")
elif [ -f "pyproject.toml" ]; then
  DEPS=$(grep -A 50 '^\[project\]' pyproject.toml | grep -A 30 'dependencies' | grep '"' | head -20 | sed 's/.*"\(.*\)".*/\1/' | python3 -c "
import sys, json
deps = [line.strip() for line in sys.stdin if line.strip()]
print(json.dumps(deps))
" 2>/dev/null || echo "[]")
fi

# Collect recent git history for target
GIT_LOG="[]"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_LOG=$(git log --oneline -10 -- "${TARGET_PATH}" 2>/dev/null | python3 -c "
import sys, json
entries = [line.strip() for line in sys.stdin if line.strip()]
print(json.dumps(entries))
" 2>/dev/null || echo "[]")
fi

cat << EOJSON
{
  "phase": "retrieve-code",
  "status": "complete",
  "target": "${TARGET_PATH}",
  "repository": "${REPO}",
  "dependencies": ${DEPS},
  "git_history": ${GIT_LOG}
}
EOJSON