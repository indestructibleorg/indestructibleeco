#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform - Full Environment Bootstrap
# ============================================================================
# Bootstraps the complete local development environment from scratch.
# Checks prerequisites, configures environment, installs dependencies,
# runs migrations, starts services, and verifies health.
#
# Usage:
#   ./scripts/bootstrap.sh [--skip-docker] [--skip-migrations] [--verbose]
# ============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Constants & configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${PROJECT_ROOT}/logs/bootstrap-$(date +%Y%m%d-%H%M%S).log"
HEALTH_ENDPOINT="http://localhost:${APP_PORT:-8000}/api/v1/health"
HEALTH_TIMEOUT=120           # seconds to wait for health
HEALTH_INTERVAL=5            # seconds between health checks
DOCKER_COMPOSE="docker compose"

SKIP_DOCKER=false
SKIP_MIGRATIONS=false
VERBOSE=false

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-docker)     SKIP_DOCKER=true; shift ;;
        --skip-migrations) SKIP_MIGRATIONS=true; shift ;;
        --verbose)         VERBOSE=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--skip-docker] [--skip-migrations] [--verbose]"
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
mkdir -p "$(dirname "${LOG_FILE}")"

log() {
    local level="$1"; shift
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    local msg="[${ts}] [${level}] $*"
    echo "${msg}" | tee -a "${LOG_FILE}"
}

info()    { log "INFO"    "$@"; }
warn()    { log "WARN"    "$@"; }
error()   { log "ERROR"   "$@"; }
success() { log "SUCCESS" "$@"; }

die() {
    error "$@"
    exit 1
}

# ---------------------------------------------------------------------------
# Summary tracking
# ---------------------------------------------------------------------------
declare -A STEP_RESULTS
STEP_ORDER=()

record_step() {
    local name="$1" result="$2"
    STEP_RESULTS["${name}"]="${result}"
    STEP_ORDER+=("${name}")
}

# ---------------------------------------------------------------------------
# Prerequisites check
# ---------------------------------------------------------------------------
check_prerequisites() {
    info "Checking prerequisites..."

    local required_tools=("python3" "pip3" "git")
    local optional_tools=("docker" "kubectl" "helm" "node" "npm")
    local missing_required=()
    local missing_optional=()

    for tool in "${required_tools[@]}"; do
        if command -v "${tool}" &>/dev/null; then
            local ver
            case "${tool}" in
                python3) ver="$(python3 --version 2>&1)" ;;
                pip3)    ver="$(pip3 --version 2>&1 | head -1)" ;;
                git)     ver="$(git --version 2>&1)" ;;
                *)       ver="found" ;;
            esac
            info "  [OK] ${tool}: ${ver}"
        else
            missing_required+=("${tool}")
            error "  [MISSING] ${tool} (required)"
        fi
    done

    for tool in "${optional_tools[@]}"; do
        if command -v "${tool}" &>/dev/null; then
            local ver
            case "${tool}" in
                docker)  ver="$(docker --version 2>&1)" ;;
                kubectl) ver="$(kubectl version --client --short 2>/dev/null || kubectl version --client 2>&1 | head -1)" ;;
                helm)    ver="$(helm version --short 2>&1)" ;;
                node)    ver="$(node --version 2>&1)" ;;
                npm)     ver="$(npm --version 2>&1)" ;;
                *)       ver="found" ;;
            esac
            info "  [OK] ${tool}: ${ver}"
        else
            missing_optional+=("${tool}")
            warn "  [MISSING] ${tool} (optional)"
        fi
    done

    # Python version check (>= 3.11)
    if command -v python3 &>/dev/null; then
        local py_major py_minor
        py_major="$(python3 -c 'import sys; print(sys.version_info.major)')"
        py_minor="$(python3 -c 'import sys; print(sys.version_info.minor)')"
        if [[ "${py_major}" -lt 3 ]] || { [[ "${py_major}" -eq 3 ]] && [[ "${py_minor}" -lt 11 ]]; }; then
            die "Python >= 3.11 required, found ${py_major}.${py_minor}"
        fi
        info "  Python version check passed (${py_major}.${py_minor})"
    fi

    # Docker daemon check
    if command -v docker &>/dev/null && [[ "${SKIP_DOCKER}" == "false" ]]; then
        if docker info &>/dev/null; then
            info "  Docker daemon is running"
        else
            warn "  Docker daemon is not running - docker steps will be skipped"
            SKIP_DOCKER=true
        fi
    fi

    if [[ ${#missing_required[@]} -gt 0 ]]; then
        die "Missing required tools: ${missing_required[*]}"
    fi

    record_step "Prerequisites" "PASS"
    success "Prerequisites check passed"
}

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
setup_environment() {
    info "Setting up environment configuration..."
    cd "${PROJECT_ROOT}"

    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp ".env.example" ".env"
            info "  Created .env from .env.example"

            # Generate a random SECRET_KEY for local development
            if command -v openssl &>/dev/null; then
                local secret_key
                secret_key="$(openssl rand -hex 32)"
                sed -i "s/SECRET_KEY=change-me-in-production-use-openssl-rand-hex-64/SECRET_KEY=${secret_key}/" ".env"
                sed -i "s/JWT_SECRET_KEY=change-me-in-production-use-openssl-rand-hex-64/JWT_SECRET_KEY=${secret_key}/" ".env"
                info "  Generated random SECRET_KEY and JWT_SECRET_KEY"
            else
                warn "  openssl not found; please set SECRET_KEY manually in .env"
            fi
        else
            die ".env.example not found; cannot create .env"
        fi
    else
        info "  .env already exists, skipping creation"
    fi

    # Source the .env for later use
    set -a
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/.env" 2>/dev/null || true
    set +a

    record_step "Environment Setup" "PASS"
    success "Environment configured"
}

# ---------------------------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------------------------
install_dependencies() {
    info "Installing Python dependencies..."
    cd "${PROJECT_ROOT}"

    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]] && [[ ! -d ".venv" ]]; then
        info "  Creating virtual environment..."
        python3 -m venv .venv
        info "  Virtual environment created at .venv/"
    fi

    local venv_dir
    if [[ -d ".venv" ]]; then
        venv_dir=".venv"
    elif [[ -d "venv" ]]; then
        venv_dir="venv"
    else
        die "Could not find virtual environment directory"
    fi

    # Activate venv
    # shellcheck disable=SC1091
    source "${venv_dir}/bin/activate"

    info "  Upgrading pip..."
    pip install --upgrade pip setuptools wheel >>"${LOG_FILE}" 2>&1

    info "  Installing project with dev dependencies..."
    pip install -e ".[dev]" >>"${LOG_FILE}" 2>&1

    info "  Installing pre-commit hooks..."
    if command -v pre-commit &>/dev/null; then
        pre-commit install >>"${LOG_FILE}" 2>&1 || warn "  pre-commit install failed (non-fatal)"
    fi

    record_step "Python Dependencies" "PASS"
    success "Python dependencies installed"
}

# ---------------------------------------------------------------------------
# Database migrations
# ---------------------------------------------------------------------------
run_migrations() {
    if [[ "${SKIP_MIGRATIONS}" == "true" ]]; then
        info "Skipping database migrations (--skip-migrations)"
        record_step "Database Migrations" "SKIP"
        return 0
    fi

    info "Running database migrations..."
    cd "${PROJECT_ROOT}"

    # Wait for database to be ready if docker is running
    if [[ "${SKIP_DOCKER}" == "false" ]]; then
        info "  Waiting for PostgreSQL to be ready..."
        local retries=30
        local count=0
        while ! ${DOCKER_COMPOSE} exec -T postgres pg_isready -U superai -d superai_db &>/dev/null; do
            count=$((count + 1))
            if [[ ${count} -ge ${retries} ]]; then
                warn "  PostgreSQL did not become ready in time; skipping migrations"
                record_step "Database Migrations" "SKIP"
                return 0
            fi
            sleep 2
        done
        info "  PostgreSQL is ready"
    fi

    if command -v alembic &>/dev/null; then
        alembic upgrade head >>"${LOG_FILE}" 2>&1 && {
            record_step "Database Migrations" "PASS"
            success "Database migrations completed"
        } || {
            warn "  alembic upgrade head failed (check log for details)"
            record_step "Database Migrations" "WARN"
        }
    else
        warn "  alembic not found in PATH; skipping migrations"
        record_step "Database Migrations" "SKIP"
    fi
}

# ---------------------------------------------------------------------------
# Docker Compose services
# ---------------------------------------------------------------------------
start_docker_services() {
    if [[ "${SKIP_DOCKER}" == "true" ]]; then
        info "Skipping Docker Compose services (--skip-docker)"
        record_step "Docker Services" "SKIP"
        return 0
    fi

    info "Starting Docker Compose services..."
    cd "${PROJECT_ROOT}"

    # Pull images first
    info "  Pulling latest images..."
    ${DOCKER_COMPOSE} pull >>"${LOG_FILE}" 2>&1 || warn "  Some image pulls failed (will use cached)"

    # Build application images
    info "  Building application images..."
    ${DOCKER_COMPOSE} build >>"${LOG_FILE}" 2>&1 || {
        warn "  Docker build failed; attempting to start infrastructure only"
    }

    # Start services
    info "  Starting services..."
    ${DOCKER_COMPOSE} up -d >>"${LOG_FILE}" 2>&1

    # Wait for services to become healthy
    info "  Waiting for services to become healthy..."
    local retries=60
    local count=0
    local all_healthy=false

    while [[ ${count} -lt ${retries} ]]; do
        local unhealthy
        unhealthy="$(${DOCKER_COMPOSE} ps --format json 2>/dev/null \
            | grep -c '"unhealthy"\|"starting"' 2>/dev/null || echo "0")"

        if [[ "${unhealthy}" == "0" ]]; then
            # Double-check with docker compose ps
            if ! ${DOCKER_COMPOSE} ps 2>/dev/null | grep -qiE "unhealthy|starting"; then
                all_healthy=true
                break
            fi
        fi

        count=$((count + 1))
        sleep 3
    done

    if [[ "${all_healthy}" == "true" ]]; then
        record_step "Docker Services" "PASS"
        success "All Docker services are healthy"
    else
        warn "  Some services may not be fully healthy yet"
        ${DOCKER_COMPOSE} ps 2>/dev/null | tee -a "${LOG_FILE}" || true
        record_step "Docker Services" "WARN"
    fi
}

# ---------------------------------------------------------------------------
# Health endpoint verification
# ---------------------------------------------------------------------------
verify_health() {
    if [[ "${SKIP_DOCKER}" == "true" ]]; then
        info "Skipping health verification (Docker not running)"
        record_step "Health Check" "SKIP"
        return 0
    fi

    info "Verifying application health endpoint..."
    local elapsed=0

    while [[ ${elapsed} -lt ${HEALTH_TIMEOUT} ]]; do
        local http_code
        http_code="$(curl -s -o /dev/null -w '%{http_code}' "${HEALTH_ENDPOINT}" 2>/dev/null || echo "000")"

        if [[ "${http_code}" == "200" ]]; then
            local body
            body="$(curl -s "${HEALTH_ENDPOINT}" 2>/dev/null || echo "{}")"
            info "  Health response (HTTP ${http_code}): ${body}"
            record_step "Health Check" "PASS"
            success "Application health endpoint is responding"
            return 0
        fi

        if [[ "${VERBOSE}" == "true" ]]; then
            info "  Waiting... (${elapsed}s elapsed, HTTP ${http_code})"
        fi

        sleep "${HEALTH_INTERVAL}"
        elapsed=$((elapsed + HEALTH_INTERVAL))
    done

    warn "  Health endpoint did not respond within ${HEALTH_TIMEOUT}s"
    record_step "Health Check" "WARN"
}

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print_summary() {
    echo ""
    echo "============================================================================"
    echo "  SuperAI Platform - Bootstrap Summary"
    echo "============================================================================"
    echo ""

    local pass_count=0 warn_count=0 fail_count=0 skip_count=0

    for step in "${STEP_ORDER[@]}"; do
        local result="${STEP_RESULTS[${step}]}"
        local icon
        case "${result}" in
            PASS) icon="[PASS]"; pass_count=$((pass_count + 1)) ;;
            WARN) icon="[WARN]"; warn_count=$((warn_count + 1)) ;;
            FAIL) icon="[FAIL]"; fail_count=$((fail_count + 1)) ;;
            SKIP) icon="[SKIP]"; skip_count=$((skip_count + 1)) ;;
            *)    icon="[????]" ;;
        esac
        printf "  %-6s  %s\n" "${icon}" "${step}"
    done

    echo ""
    echo "  Results: ${pass_count} passed, ${warn_count} warnings, ${fail_count} failed, ${skip_count} skipped"
    echo ""
    echo "  Log file: ${LOG_FILE}"
    echo ""

    if [[ "${SKIP_DOCKER}" == "false" ]]; then
        echo "  Endpoints:"
        echo "    API:          http://localhost:${APP_PORT:-8000}/docs"
        echo "    Health:       http://localhost:${APP_PORT:-8000}/api/v1/health"
        echo "    Prometheus:   http://localhost:${PROMETHEUS_PORT:-9090}"
        echo "    Grafana:      http://localhost:${GRAFANA_PORT:-3000}"
        echo "    Jaeger:       http://localhost:${JAEGER_UI_PORT:-16686}"
        echo "    RabbitMQ:     http://localhost:${RABBITMQ_MGMT_PORT:-15672}"
        echo ""
    fi

    echo "============================================================================"

    if [[ ${fail_count} -gt 0 ]]; then
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    info "Starting SuperAI Platform bootstrap..."
    info "Project root: ${PROJECT_ROOT}"
    echo ""

    check_prerequisites
    setup_environment
    install_dependencies
    start_docker_services
    run_migrations
    verify_health
    print_summary
}

main "$@"
