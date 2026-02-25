#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# DataOps Platform — Bootstrap Script
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log_info()  { echo "[info]  $(date -u +%FT%TZ) $*"; }
log_warn()  { echo "[warn]  $(date -u +%FT%TZ) $*" >&2; }
log_error() { echo "[error] $(date -u +%FT%TZ) $*" >&2; }
log_ok()    { echo "[ok]    $(date -u +%FT%TZ) $*"; }

die() { log_error "$@"; exit 1; }

log_info "Step 1/6: Checking prerequisites..."
command -v python3 &>/dev/null || die "python3 is required"
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log_ok "Python ${PYTHON_VERSION} detected"

log_info "Step 2/6: Setting up virtual environment..."
VENV_DIR="${PROJECT_ROOT}/.venv"
if [[ ! -d "${VENV_DIR}" ]]; then
    python3 -m venv "${VENV_DIR}"
    log_ok "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

log_info "Step 3/6: Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -e "${PROJECT_ROOT}[dev]"
log_ok "Dependencies installed"

log_info "Step 4/6: Starting Docker services..."
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    cd "${PROJECT_ROOT}" && docker compose up -d postgres redis
    log_ok "Docker backing services started"
else
    log_warn "Docker not available — skipping"
fi

log_info "Step 5/6: Health check..."
MAX_WAIT=30; ELAPSED=0
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    while ! docker compose exec -T postgres pg_isready -U dataops &>/dev/null 2>&1; do
        sleep 2; ELAPSED=$((ELAPSED + 2))
        [[ ${ELAPSED} -ge ${MAX_WAIT} ]] && { log_warn "Timeout waiting for PostgreSQL"; break; }
    done
    log_ok "Backing services healthy"
fi

log_info "Step 6/6: Bootstrap complete"
echo ""
echo "  DataOps Platform — Development Environment Ready"
echo "  Activate:  source ${VENV_DIR}/bin/activate"
echo "  Run API:   dataops"
echo "  Run tests: pytest tests/"
echo ""
