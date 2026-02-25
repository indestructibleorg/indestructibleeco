#!/bin/bash
set -euo pipefail

echo "🔍 Collecting issues for auto-fix..."

REPORT_FILE="artifacts/reports/auto-fix/detected-issues.json"
mkdir -p "$(dirname "$REPORT_FILE")"

ISSUES='{"issues": [], "timestamp": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'", "run_id": "'"${GITHUB_RUN_ID:-unknown}"'"}'

# Check for workflow issues
if find .github/workflows -name "*.yml" -o -name "*.yaml" | xargs grep -L "permissions:" | grep -q .; then
  echo "Found workflows without permissions"
  ISSUES=$(echo "$ISSUES" | jq '.issues += [{"type": "actions_hardening", "severity": "medium", "description": "Workflows missing permissions"}]')
fi

# Check for linting issues
if command -v gofmt &> /dev/null; then
  if [ -n "$(gofmt -l .)" ]; then
    echo "Found Go files needing formatting"
    ISSUES=$(echo "$ISSUES" | jq '.issues += [{"type": "lint_format", "severity": "low", "description": "Go files need formatting"}]')
  fi
fi

# Check for outdated dependencies
if [ -f "go.mod" ]; then
  echo "Checking Go dependencies..."
  ISSUES=$(echo "$ISSUES" | jq '.issues += [{"type": "deps_go", "severity": "medium", "description": "Check for outdated Go dependencies"}]')
fi

if [ -f "package.json" ]; then
  echo "Checking Node dependencies..."
  ISSUES=$(echo "$ISSUES" | jq '.issues += [{"type": "deps_node", "severity": "medium", "description": "Check for outdated Node dependencies"}]')
fi

# Check Docker base images
if find . -name "Dockerfile*" | grep -q .; then
  echo "Checking Docker base images..."
  ISSUES=$(echo "$ISSUES" | jq '.issues += [{"type": "docker_base", "severity": "medium", "description": "Check for outdated Docker base images"}]')
fi

# Check naming convention violations
if command -v conftest &> /dev/null; then
  echo "Checking naming conventions..."
  CONFTERST_OUTPUT=$(conftest test deploy/ -p .config/conftest/policies/ 2>&1 || true)
  if echo "$CONFTERST_OUTPUT" | grep -q "FAIL"; then
    ISSUES=$(echo "$ISSUES" | jq '.issues += [{"type": "naming", "severity": "high", "description": "Naming convention violations detected"}]')
  fi
fi

echo "$ISSUES" | jq '.' > "$REPORT_FILE"

echo "✅ Issues collected to $REPORT_FILE"
echo "Total issues: $(echo "$ISSUES" | jq '.issues | length')"