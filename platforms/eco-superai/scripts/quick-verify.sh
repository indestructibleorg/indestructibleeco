#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform - Quick Local Verification
# ============================================================================
# Runs a fast battery of local checks: lint, type-check, unit tests,
# Docker build validation, and K8s manifest validation.
#
# Usage:
#   ./scripts/quick-verify.sh [--skip-docker] [--skip-k8s] [--fix]
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
# ============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${PROJECT_ROOT}/logs/quick-verify-$(date +%Y%m%d-%H%M%S).log"

SKIP_DOCKER=false
SKIP_K8S=false
FIX_MODE=false

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-docker) SKIP_DOCKER=true; shift ;;
        --skip-k8s)    SKIP_K8S=true; shift ;;
        --fix)         FIX_MODE=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--skip-docker] [--skip-k8s] [--fix]"
            exit 0
            ;;
        *) echo "ERROR: Unknown argument: $1" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Logging & tracking
# ---------------------------------------------------------------------------
mkdir -p "$(dirname "${LOG_FILE}")"

log() {
    local level="$1"; shift
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${ts}] [${level}] $*" | tee -a "${LOG_FILE}"
}

info()  { log "INFO"  "$@"; }
error() { log "ERROR" "$@"; }

declare -a CHECK_NAMES=()
declare -a CHECK_RESULTS=()
declare -a CHECK_DURATIONS=()

TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_SKIP=0

run_check() {
    local name="$1"; shift
    local start_time
    start_time="$(date +%s)"

    info "Running: ${name}..."

    local result="PASS"
    if "$@" >>"${LOG_FILE}" 2>&1; then
        result="PASS"
        TOTAL_PASS=$((TOTAL_PASS + 1))
    else
        result="FAIL"
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
        error "  ${name} FAILED"
    fi

    local end_time
    end_time="$(date +%s)"
    local duration=$(( end_time - start_time ))

    CHECK_NAMES+=("${name}")
    CHECK_RESULTS+=("${result}")
    CHECK_DURATIONS+=("${duration}s")
}

skip_check() {
    local name="$1"
    CHECK_NAMES+=("${name}")
    CHECK_RESULTS+=("SKIP")
    CHECK_DURATIONS+=("0s")
    TOTAL_SKIP=$((TOTAL_SKIP + 1))
    info "Skipping: ${name}"
}

# ---------------------------------------------------------------------------
# Check: Lint (ruff)
# ---------------------------------------------------------------------------
check_lint() {
    cd "${PROJECT_ROOT}"
    if [[ "${FIX_MODE}" == "true" ]]; then
        ruff check --fix src/ tests/ 2>&1
        ruff format src/ tests/ 2>&1
    else
        ruff check src/ tests/ 2>&1
    fi
}

# ---------------------------------------------------------------------------
# Check: Type check (mypy)
# ---------------------------------------------------------------------------
check_typecheck() {
    cd "${PROJECT_ROOT}"
    mypy src/ --ignore-missing-imports 2>&1
}

# ---------------------------------------------------------------------------
# Check: Unit tests
# ---------------------------------------------------------------------------
check_unit_tests() {
    cd "${PROJECT_ROOT}"
    python3 -m pytest tests/unit/ -v --tb=short -x -q 2>&1
}

# ---------------------------------------------------------------------------
# Check: Docker build
# ---------------------------------------------------------------------------
check_docker_build() {
    cd "${PROJECT_ROOT}"

    # Validate Dockerfile syntax by performing a dry-run build
    # Use --check flag if available, otherwise do a real build with no push
    local dockerfile="Dockerfile.prod"
    if [[ ! -f "${dockerfile}" ]]; then
        dockerfile="Dockerfile.dev"
    fi

    if [[ ! -f "${dockerfile}" ]]; then
        echo "No Dockerfile found" >&2
        return 1
    fi

    docker build \
        --file "${dockerfile}" \
        --target "$(docker build --file "${dockerfile}" . --print 2>/dev/null || true)" \
        --no-cache \
        --progress=plain \
        -t "superai-platform:verify-$(date +%s)" \
        . 2>&1

    return $?
}

# ---------------------------------------------------------------------------
# Check: K8s manifest validation
# ---------------------------------------------------------------------------
check_k8s_manifests() {
    cd "${PROJECT_ROOT}"

    local exit_code=0

    # Validate with kubectl dry-run if available
    if command -v kubectl &>/dev/null; then
        info "  Validating K8s base manifests..."

        # Validate each manifest file individually
        local manifest_dir="k8s/base"
        if [[ -d "${manifest_dir}" ]]; then
            for manifest in "${manifest_dir}"/*.yaml; do
                [[ -f "${manifest}" ]] || continue

                local basename
                basename="$(basename "${manifest}")"

                # Skip kustomization.yaml as it's not a standard K8s resource
                if [[ "${basename}" == "kustomization.yaml" ]]; then
                    continue
                fi

                if kubectl apply --dry-run=client -f "${manifest}" &>/dev/null; then
                    echo "  [OK] ${basename}" 2>&1
                else
                    echo "  [FAIL] ${basename}" 2>&1
                    exit_code=1
                fi
            done
        fi

        # Validate kustomize overlays
        for overlay_dir in k8s/overlays/*/; do
            [[ -d "${overlay_dir}" ]] || continue
            local overlay_name
            overlay_name="$(basename "${overlay_dir}")"

            if kubectl kustomize "${overlay_dir}" >/dev/null 2>&1; then
                echo "  [OK] overlay/${overlay_name}" 2>&1
            else
                echo "  [FAIL] overlay/${overlay_name}" 2>&1
                exit_code=1
            fi
        done

        # Validate Helm chart if helm is available
        if command -v helm &>/dev/null && [[ -d "helm" ]]; then
            if helm lint ./helm/ 2>&1; then
                echo "  [OK] Helm chart lint" 2>&1
            else
                echo "  [FAIL] Helm chart lint" 2>&1
                exit_code=1
            fi

            if helm template superai ./helm/ >/dev/null 2>&1; then
                echo "  [OK] Helm template render" 2>&1
            else
                echo "  [FAIL] Helm template render" 2>&1
                exit_code=1
            fi
        fi
    else
        # Fallback: basic YAML syntax validation with Python
        python3 -c "
import yaml, sys, os

errors = 0
manifest_dir = 'k8s/base'
if os.path.isdir(manifest_dir):
    for f in sorted(os.listdir(manifest_dir)):
        if not f.endswith('.yaml'):
            continue
        filepath = os.path.join(manifest_dir, f)
        try:
            with open(filepath) as fh:
                list(yaml.safe_load_all(fh))
            print(f'  [OK] {f}')
        except Exception as e:
            print(f'  [FAIL] {f}: {e}')
            errors += 1
sys.exit(1 if errors > 0 else 0)
" 2>&1
        exit_code=$?
    fi

    return ${exit_code}
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    local overall_start
    overall_start="$(date +%s)"

    echo "============================================================================"
    echo "  SuperAI Platform - Quick Verification"
    echo "============================================================================"
    echo ""

    cd "${PROJECT_ROOT}"

    # Activate venv if present
    if [[ -f ".venv/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source ".venv/bin/activate"
    elif [[ -f "venv/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source "venv/bin/activate"
    fi

    # 1. Lint
    if command -v ruff &>/dev/null; then
        run_check "Lint (ruff)" check_lint
    else
        skip_check "Lint (ruff)"
    fi

    # 2. Type check
    if command -v mypy &>/dev/null; then
        run_check "Type Check (mypy)" check_typecheck
    else
        skip_check "Type Check (mypy)"
    fi

    # 3. Unit tests
    if command -v pytest &>/dev/null || python3 -c "import pytest" 2>/dev/null; then
        run_check "Unit Tests" check_unit_tests
    else
        skip_check "Unit Tests"
    fi

    # 4. Docker build
    if [[ "${SKIP_DOCKER}" == "false" ]] && command -v docker &>/dev/null && docker info &>/dev/null; then
        run_check "Docker Build" check_docker_build
    else
        skip_check "Docker Build"
    fi

    # 5. K8s manifests
    if [[ "${SKIP_K8S}" == "false" ]]; then
        run_check "K8s Manifests" check_k8s_manifests
    else
        skip_check "K8s Manifests"
    fi

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    local overall_end
    overall_end="$(date +%s)"
    local total_duration=$(( overall_end - overall_start ))

    echo ""
    echo "============================================================================"
    echo "  Verification Results"
    echo "============================================================================"
    echo ""

    for i in "${!CHECK_NAMES[@]}"; do
        local icon
        case "${CHECK_RESULTS[$i]}" in
            PASS) icon="[PASS]" ;;
            FAIL) icon="[FAIL]" ;;
            SKIP) icon="[SKIP]" ;;
            *)    icon="[????]" ;;
        esac
        printf "  %-6s  %-25s  %s\n" "${icon}" "${CHECK_NAMES[$i]}" "${CHECK_DURATIONS[$i]}"
    done

    echo ""
    echo "  Total: ${TOTAL_PASS} passed, ${TOTAL_FAIL} failed, ${TOTAL_SKIP} skipped (${total_duration}s)"
    echo ""
    echo "  Log: ${LOG_FILE}"
    echo "============================================================================"

    if [[ ${TOTAL_FAIL} -gt 0 ]]; then
        exit 1
    fi

    exit 0
}

main "$@"
