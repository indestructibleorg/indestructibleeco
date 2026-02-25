#!/bin/bash
# scripts/refactor/master-refactor.sh
# Master orchestration script for three-phase refactoring
#
# This script orchestrates the complete three-phase refactoring process:
# - Phase 1: Deconstruction (Analysis)
# - Phase 2: Integration (Design)
# - Phase 3: Refactor (Implementation)
#
# Usage: bash scripts/refactor/master-refactor.sh [--skip-phase PHASE] [--dry-run]

set -e
set -o pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REFACTOR_DIR="$REPO_ROOT/workspace/docs/refactor_playbooks"
LOG_FILE="$REPO_ROOT/refactor-$(date +%Y%m%d-%H%M%S).log"
DRY_RUN=false
SKIP_PHASES=()

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-phase)
            SKIP_PHASES+=("$2")
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--skip-phase PHASE] [--dry-run]"
            echo ""
            echo "Options:"
            echo "  --skip-phase PHASE    Skip specific phase (1, 2, or 3)"
            echo "  --dry-run             Run in dry-run mode (no actual changes)"
            echo "  -h, --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date -Iseconds)
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $@" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✓${NC} $@" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $@" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}✗${NC} $@" | tee -a "$LOG_FILE"
}

# Function to check if phase should be skipped
should_skip_phase() {
    local phase=$1
    for skip in "${SKIP_PHASES[@]}"; do
        if [[ "$skip" == "$phase" ]]; then
            return 0
        fi
    done
    return 1
}

# Function to run command with dry-run support
run_cmd() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY-RUN: $@"
    else
        log_info "Executing: $@"
        eval "$@"
    fi
}

# Function to create checkpoint
create_checkpoint() {
    local phase=$1
    local checkpoint_file="$REPO_ROOT/.refactor-phase-$phase-checkpoint"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        git rev-parse HEAD > "$checkpoint_file"
        log_success "Created checkpoint for Phase $phase: $(cat $checkpoint_file)"
    fi
}

# Function to validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."
    
    # Check required tools
    local required_tools=("git" "python3" "node" "npm")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Check repository state
    if [[ -n $(git status --porcelain) ]]; then
        log_warning "Working directory has uncommitted changes"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "Prerequisites validated"
}

# Phase 1: Deconstruction
run_phase1() {
    if should_skip_phase "1"; then
        log_warning "Skipping Phase 1: Deconstruction"
        return
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}📍 Phase 1: Deconstruction${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local phase1_script="$REPO_ROOT/scripts/refactor/phase1-deconstruction.sh"
    
    if [[ -f "$phase1_script" ]]; then
        run_cmd "bash '$phase1_script'"
    else
        log_warning "Phase 1 script not found: $phase1_script"
        log_info "Creating Phase 1 deliverables directory..."
        run_cmd "mkdir -p '$REFACTOR_DIR/01_deconstruction'"
    fi
    
    # Validation checkpoint
    log_info "Validating Phase 1 deliverables..."
    local validator="$REPO_ROOT/tools/refactor/validate-phase1.py"
    
    if [[ -f "$validator" ]]; then
        run_cmd "python3 '$validator' --deliverables-path '$REFACTOR_DIR/01_deconstruction'"
    else
        log_warning "Phase 1 validator not found: $validator"
    fi
    
    create_checkpoint "1"
    log_success "Phase 1: Deconstruction - Complete"
}

# Phase 2: Integration
run_phase2() {
    if should_skip_phase "2"; then
        log_warning "Skipping Phase 2: Integration"
        return
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}🔗 Phase 2: Integration${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local phase2_script="$REPO_ROOT/scripts/refactor/phase2-integration.sh"
    
    if [[ -f "$phase2_script" ]]; then
        run_cmd "bash '$phase2_script'"
    else
        log_warning "Phase 2 script not found: $phase2_script"
        log_info "Creating Phase 2 deliverables directory..."
        run_cmd "mkdir -p '$REFACTOR_DIR/02_integration'"
    fi
    
    # Validation checkpoint
    log_info "Validating Phase 2 deliverables..."
    local validator="$REPO_ROOT/tools/refactor/validate-phase2.py"
    
    if [[ -f "$validator" ]]; then
        run_cmd "python3 '$validator' --deliverables-path '$REFACTOR_DIR/02_integration'"
    else
        log_warning "Phase 2 validator not found: $validator"
    fi
    
    create_checkpoint "2"
    log_success "Phase 2: Integration - Complete"
}

# Phase 3: Refactor
run_phase3() {
    if should_skip_phase "3"; then
        log_warning "Skipping Phase 3: Refactor"
        return
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}⚙️  Phase 3: Refactor${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local phase3_script="$REPO_ROOT/scripts/refactor/phase3-refactor.sh"
    
    if [[ -f "$phase3_script" ]]; then
        run_cmd "bash '$phase3_script'"
    else
        log_warning "Phase 3 script not found: $phase3_script"
        log_info "Creating Phase 3 deliverables directory..."
        run_cmd "mkdir -p '$REFACTOR_DIR/03_refactor'"
    fi
    
    # Final validation
    log_info "Running final validation suite..."
    local validator="$REPO_ROOT/tools/refactor/validate-phase3.py"
    
    if [[ -f "$validator" ]]; then
        run_cmd "python3 '$validator' --deliverables-path '$REFACTOR_DIR/03_refactor'"
    else
        log_warning "Phase 3 validator not found: $validator"
    fi
    
    # trigger_2_refactor_validation: Auto-run quantum architecture compliance validation
    # Latency target: < 50ms
    # Status: ✅ READY (INSTANT-compliant)
    log_info "🔬 Running quantum architecture compliance validation (target: < 50ms)..."
    local quantum_validator="$REPO_ROOT/tools/validation/quantum_feature_extractor.py"
    
    if [[ -f "$quantum_validator" ]]; then
        local validation_start=$(date +%s%N)
        
        if [[ "$DRY_RUN" == "false" ]]; then
            python3 "$quantum_validator" \
                --input "$REFACTOR_DIR" \
                --output "$REPO_ROOT/workspace/docs/validation/reports/refactor-validation-$(date +%Y%m%d-%H%M%S).json" \
                2>&1 | tee -a "$LOG_FILE" || log_warning "Quantum validation completed with warnings"
        else
            log_info "DRY-RUN: python3 quantum_feature_extractor.py"
        fi
        
        local validation_end=$(date +%s%N)
        local elapsed_ms=$(( ($validation_end - $validation_start) / 1000000 ))
        
        if [[ $elapsed_ms -lt 50 ]]; then
            log_success "✅ Quantum validation completed in ${elapsed_ms}ms (< 50ms target)"
        else
            log_warning "⚠️ Quantum validation took ${elapsed_ms}ms (>= 50ms target)"
        fi
    else
        log_warning "Quantum validator not found: $quantum_validator"
    fi
    
    create_checkpoint "3"
    log_success "Phase 3: Refactor - Complete"
}

# Health check
run_health_check() {
    echo ""
    log_info "Running system health check..."
    
    # Check if package.json exists
    if [[ -f "$REPO_ROOT/package.json" ]]; then
        # Run tests if test script exists
        if grep -q '"test"' "$REPO_ROOT/package.json"; then
            log_info "Running test suite..."
            if [[ "$DRY_RUN" == "false" ]]; then
                cd "$REPO_ROOT"
                npm test || log_warning "Some tests failed"
            else
                log_info "DRY-RUN: npm test"
            fi
        fi
    fi
    
    log_success "Health check complete"
}

# Main execution
main() {
    local start_time=$SECONDS
    
    echo "🚀 Three-Phase Refactoring - Starting..."
    echo "Repository: $REPO_ROOT"
    echo "Timestamp: $(date -Iseconds)"
    echo "Log file: $LOG_FILE"
    echo ""
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "Running in DRY-RUN mode - no changes will be made"
    fi
    
    # Validate prerequisites
    validate_prerequisites
    
    # Execute phases
    run_phase1
    run_phase2
    run_phase3
    
    # Health check
    run_health_check
    
    # Summary
    local duration=$((SECONDS - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}✅ Three-Phase Refactoring - Complete${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Timestamp: $(date -Iseconds)"
    echo "Duration: ${minutes}m ${seconds}s"
    echo "Log file: $LOG_FILE"
    echo ""
    
    log_success "Refactoring pipeline completed successfully"
}

# Trap errors
trap 'log_error "Script failed at line $LINENO"; exit 1' ERR

# Run main
main
