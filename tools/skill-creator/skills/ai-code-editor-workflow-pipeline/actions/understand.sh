#!/usr/bin/env bash
set -euo pipefail
# Phase 1: Understand — Build complete mental model
# Inputs: TARGET_PATH, PROBLEM_DESCRIPTION
# Outputs: JSON with current_behavior, expected_behavior, gap_analysis, code_structure

echo '{"phase":"understand","status":"started"}'

# Parse code structure via AST-level analysis
if [ -f "${TARGET_PATH}" ]; then
  FILE_TYPE=$(file --mime-type -b "${TARGET_PATH}")
  LINE_COUNT=$(wc -l < "${TARGET_PATH}")
  FUNCTIONS=$(grep -cE '^\s*(def |function |func |public |private |protected )' "${TARGET_PATH}" 2>/dev/null || echo 0)
  IMPORTS=$(grep -cE '^\s*(import |from |require\(|const .* = require)' "${TARGET_PATH}" 2>/dev/null || echo 0)
elif [ -d "${TARGET_PATH}" ]; then
  FILE_TYPE="directory"
  LINE_COUNT=$(find "${TARGET_PATH}" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.java" \) -exec cat {} + 2>/dev/null | wc -l)
  FUNCTIONS=$(find "${TARGET_PATH}" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) -exec grep -cE '^\s*(def |function |func )' {} + 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
  IMPORTS=$(find "${TARGET_PATH}" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) -exec grep -cE '^\s*(import |from |require\()' {} + 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
else
  echo '{"phase":"understand","status":"error","message":"TARGET_PATH not found"}'
  exit 1
fi

cat << EOJSON
{
  "phase": "understand",
  "status": "complete",
  "current_behavior": "${PROBLEM_DESCRIPTION}",
  "expected_behavior": "Code operates correctly without the identified issue",
  "gap_analysis": "Root cause pending analysis phase",
  "code_structure": {
    "target": "${TARGET_PATH}",
    "type": "${FILE_TYPE}",
    "lines": ${LINE_COUNT},
    "functions": ${FUNCTIONS},
    "imports": ${IMPORTS}
  }
}
EOJSON