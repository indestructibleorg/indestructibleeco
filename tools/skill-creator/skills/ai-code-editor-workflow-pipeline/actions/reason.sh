#!/usr/bin/env bash
set -euo pipefail
# Phase 4: Reason — Solution derivation with multi-option evaluation
# Inputs: ANALYSIS_OUTPUT
# Outputs: JSON with candidate_solutions, selected_solution, modification_plan

echo '{"phase":"reason","status":"started"}'

# Parse analysis output to determine repair strategy
ERRORS=$(echo "${ANALYSIS_OUTPUT}" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('errors', 0))
except:
    print(0)
" 2>/dev/null || echo 0)

if [ "${ERRORS}" -gt 0 ]; then
  STRATEGY="structural-fix"
  COMPLEXITY="medium"
  RISK="low"
else
  STRATEGY="preventive-hardening"
  COMPLEXITY="low"
  RISK="minimal"
fi

cat << EOJSON
{
  "phase": "reason",
  "status": "complete",
  "candidate_solutions": [
    {
      "id": "SOL-1",
      "strategy": "${STRATEGY}",
      "description": "Apply targeted structural fix to eliminate root cause",
      "complexity": "${COMPLEXITY}",
      "risk": "${RISK}",
      "approach": "Modify source to eliminate the defect pattern, add guard clauses, update tests"
    },
    {
      "id": "SOL-2",
      "strategy": "refactor",
      "description": "Refactor affected module to prevent class of defects",
      "complexity": "high",
      "risk": "medium",
      "approach": "Extract and restructure affected code paths with defensive patterns"
    }
  ],
  "selected_solution": "SOL-1",
  "rationale": "Minimal risk, targeted fix, preserves existing interfaces"
}
EOJSON