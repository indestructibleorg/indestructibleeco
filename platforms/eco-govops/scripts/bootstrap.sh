#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# GovOps Platform — Bootstrap Script
# Sets up the local development environment from scratch.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log_info()  { echo "[info]  $(date -u +%FT%TZ) $*"; }
log_warn()  { echo "[warn]  $(date -u +%FT%TZ) $*" >&2; }
log_error() { echo "[error] $(date -u +%FT%TZ) $*" >&2; }
log_ok()    { echo "[ok]    $(date -u +%FT%TZ) $*"; }

die() { log_error "$@"; exit 1; }

# ---------------------------------------------------------------------------
# Step 1: Prerequisites
# ---------------------------------------------------------------------------
log_info "Step 1/6: Checking prerequisites..."

command -v python3 &>/dev/null || die "python3 is required"
command -v pip     &>/dev/null || die "pip is required"
command -v docker  &>/dev/null || log_warn "docker not found — container steps will be skipped"

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$(echo "${PYTHON_VERSION} 3.11" | awk '{print ($1 >= $2)}')" != "1" ]]; then
    die "Python >= 3.11 required, found ${PYTHON_VERSION}"
fi
log_ok "Python ${PYTHON_VERSION} detected"

# ---------------------------------------------------------------------------
# Step 2: Virtual environment
# ---------------------------------------------------------------------------
log_info "Step 2/6: Setting up virtual environment..."

VENV_DIR="${PROJECT_ROOT}/.venv"
if [[ ! -d "${VENV_DIR}" ]]; then
    python3 -m venv "${VENV_DIR}"
    log_ok "Virtual environment created at ${VENV_DIR}"
else
    log_info "Virtual environment already exists"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# ---------------------------------------------------------------------------
# Step 3: Install dependencies
# ---------------------------------------------------------------------------
log_info "Step 3/6: Installing dependencies..."

pip install --quiet --upgrade pip
pip install --quiet -e "${PROJECT_ROOT}[dev]"
log_ok "Dependencies installed"

# ---------------------------------------------------------------------------
# Step 4: Docker services (optional)
# ---------------------------------------------------------------------------
log_info "Step 4/6: Starting Docker services..."

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    cd "${PROJECT_ROOT}"
    docker compose up -d postgres redis
    log_ok "Docker backing services started"
else
    log_warn "Docker not available — skipping backing services"
fi

# ---------------------------------------------------------------------------
# Step 5: Health check
# ---------------------------------------------------------------------------
log_info "Step 5/6: Waiting for services to be healthy..."

MAX_WAIT=30
ELAPSED=0
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    while ! docker compose exec -T postgres pg_isready -U govops &>/dev/null 2>&1; do
        sleep 2
        ELAPSED=$((ELAPSED + 2))
        if [[ ${ELAPSED} -ge ${MAX_WAIT} ]]; then
            log_warn "Timeout waiting for PostgreSQL — continuing anyway"
            break
        fi
    done
    log_ok "Backing services healthy"
else
    log_info "No Docker services to check"
fi

# ---------------------------------------------------------------------------
# Step 6: Summary
# ---------------------------------------------------------------------------
log_info "Step 6/6: Bootstrap complete"
echo ""
echo "  GovOps Platform — Development Environment Ready"
echo "  ================================================"
echo "  Activate:  source ${VENV_DIR}/bin/activate"
echo "  Run API:   govops"
echo "  Run tests: pytest tests/"
echo "  Verify:    bash scripts/quick-verify.sh"
echo ""
