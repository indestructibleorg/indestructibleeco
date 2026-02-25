#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# DataOps Platform — Quick Verification Script
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PASSED=0; FAILED=0; CHECKS=()

log_info() { echo "[info] $(date -u +%FT%TZ) $*"; }
log_ok()   { echo "[ok]   $(date -u +%FT%TZ) $*"; }
log_fail() { echo "[FAIL] $(date -u +%FT%TZ) $*" >&2; }

run_check() {
    local name="$1"; shift
    log_info "Running: ${name}"
    if "$@" 2>&1; then
        PASSED=$((PASSED + 1)); CHECKS+=("PASS  ${name}"); log_ok "${name}"
    else
        FAILED=$((FAILED + 1)); CHECKS+=("FAIL  ${name}"); log_fail "${name}"
    fi
}

cd "${PROJECT_ROOT}"

run_check "Ruff lint"         ruff check src/ tests/ --quiet
run_check "Ruff format"       ruff format --check src/ tests/ --quiet
run_check "Unit tests"        pytest tests/unit/ -q --tb=short --no-header
run_check "Integration tests" pytest tests/integration/ -q --tb=short --no-header

if command -v mypy &>/dev/null; then
    run_check "Type check (mypy)" mypy src/ --ignore-missing-imports --no-error-summary
fi

echo ""
echo "  Verification Summary"
echo "  ===================="
for c in "${CHECKS[@]}"; do echo "  ${c}"; done
echo "  Passed: ${PASSED}  Failed: ${FAILED}"
echo ""
[[ ${FAILED} -eq 0 ]] && exit 0 || exit 1
