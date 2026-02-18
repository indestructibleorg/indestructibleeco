#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# Phase 2b: Retrieve — Knowledge Base & Documentation
# ═══════════════════════════════════════════════════════════════════
# Queries the Memory Hub knowledge base for similar incidents,
# runbooks, and historical fixes related to the current problem.
#
# Inputs (env):
#   PROBLEM_DESCRIPTION — Description of the code issue
#   MEMORY_HUB_URL     — Memory Hub service endpoint
#   AUTH_TOKEN          — JWT for service authentication
#
# Outputs:
#   JSON array of relevant knowledge entries to stdout
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

: "${PROBLEM_DESCRIPTION:?PROBLEM_DESCRIPTION is required}"
: "${MEMORY_HUB_URL:=http://memory-hub.indestructibleeco.svc.cluster.local:8080}"
: "${AUTH_TOKEN:?AUTH_TOKEN is required}"

echo "=== Phase 2b: Retrieve Knowledge ==="
echo "Query: ${PROBLEM_DESCRIPTION:0:120}..."
echo "Memory Hub: ${MEMORY_HUB_URL}"

# Query knowledge base for similar incidents and fixes
RESPONSE=$(curl -sf \
  -X POST "${MEMORY_HUB_URL}/api/v1/search" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    &quot;query&quot;: &quot;${PROBLEM_DESCRIPTION}&quot;,
    &quot;top_k&quot;: 10,
    &quot;filters&quot;: {
      &quot;type&quot;: [&quot;incident&quot;, &quot;fix&quot;, &quot;runbook&quot;]
    }
  }" 2>/dev/null) || {
  echo "WARNING: Memory Hub unreachable, proceeding with empty knowledge base"
  RESPONSE='{"results": [], "fallback": true}'
}

# Validate response structure
if ! echo "${RESPONSE}" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
  echo "ERROR: Invalid JSON response from Memory Hub"
  exit 1
fi

RESULT_COUNT=$(echo "${RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('results',[])))" 2>/dev/null || echo "0")
echo "Retrieved ${RESULT_COUNT} knowledge entries"

# Output structured result
echo "${RESPONSE}"
echo "=== Phase 2b Complete ==="