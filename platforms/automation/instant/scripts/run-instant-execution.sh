#!/bin/bash
# ==============================================================================
# SynergyMesh Instant Execution Quick Start Script
# 即時執行快速啟動腳本
# ==============================================================================
# Purpose: One-command execution of AI-powered instant execution pipeline
# Usage:
#   ./scripts/run-instant-execution.sh                    # Run complete pipeline
#   ./scripts/run-instant-execution.sh --dry-run          # Dry run mode
#   ./scripts/run-instant-execution.sh --stage 1          # Run specific stage
#   ./scripts/run-instant-execution.sh --help             # Show help
# ==============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PIPELINE_SCRIPT="$SCRIPT_DIR/instant_execution_pipeline.py"
CONFIG_FILE="$SCRIPT_DIR/../configs/instant-execution-pipeline.yaml"
LOG_DIR="$REPO_ROOT/.automation_logs"

# Default values
ACTION="run"
STAGE=""
NAMESPACE="synergymesh-system"
DRY_RUN=""
SKIP_VALIDATION=""
OUTPUT_FILE=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Banner
print_banner() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                                                ║${NC}"
    echo -e "${CYAN}║  ${GREEN}🚀 SynergyMesh Instant Execution Pipeline${CYAN}                                 ║${NC}"
    echo -e "${CYAN}║  ${YELLOW}⚡ AI-Powered 3-Stage Automated Deployment${CYAN}                                ║${NC}"
    echo -e "${CYAN}║                                                                                ║${NC}"
    echo -e "${CYAN}║  ${MAGENTA}Stage 1: AI Analysis          < 5 seconds${CYAN}                                ║${NC}"
    echo -e "${CYAN}║  ${MAGENTA}Stage 2: Synthetic Validation < 30 seconds${CYAN}                              ║${NC}"
    echo -e "${CYAN}║  ${MAGENTA}Stage 3: Automated Deployment < 30 minutes${CYAN}                              ║${NC}"
    echo -e "${CYAN}║                                                                                ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅ $*${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ $*${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  $*${NC}"
}

log_info() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')] ℹ️  $*${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    else
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        log_info "Python version: $python_version"
    fi
    
    # Check kubectl (optional for local dev)
    if command -v kubectl &> /dev/null; then
        log_info "kubectl: available"
    else
        log_warning "kubectl not found (optional for local dev)"
    fi
    
    # Check required files
    if [ ! -f "$PIPELINE_SCRIPT" ]; then
        log_error "Pipeline script not found: $PIPELINE_SCRIPT"
        exit 1
    fi
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warning "Config file not found: $CONFIG_FILE"
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install missing tools and try again."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    log "Setting up environment..."
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    # Set Python path
    export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/tools:$REPO_ROOT/tools/automation/engines:$REPO_ROOT/tests/automation:${PYTHONPATH:-}"
    
    log_success "Environment ready"
}

# Show usage
show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Run SynergyMesh AI-Powered Instant Execution Pipeline

Options:
    --stage STAGE          Run specific stage (1, 2, or 3)
    --namespace NS         Kubernetes namespace (default: synergymesh-system)
    --dry-run             Perform dry run without actual deployment
    --skip-validation     Skip validation failures
    --output FILE         Save results to JSON file
    --help                Show this help message

Actions:
    run                   Run complete pipeline (default)
    validate              Validate configuration only
    stage                 Run specific stage (requires --stage)

Examples:
    # Run complete pipeline
    $0

    # Dry run mode
    $0 --dry-run

    # Run specific stage
    $0 --stage 1

    # Save results to file
    $0 --output results.json

    # Custom namespace
    $0 --namespace my-namespace

EOF
}

# Parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            run|validate|stage)
                ACTION="$1"
                shift
                ;;
            --stage)
                ACTION="stage"
                STAGE="$2"
                shift 2
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN="--dry-run"
                shift
                ;;
            --skip-validation)
                SKIP_VALIDATION="--skip-validation"
                shift
                ;;
            --output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Run pipeline
run_pipeline() {
    log "Starting instant execution pipeline..."
    log_info "Action: $ACTION"
    log_info "Namespace: $NAMESPACE"
    [ -n "$DRY_RUN" ] && log_warning "DRY RUN MODE"
    echo ""
    
    # Build command
    local cmd="python3 $PIPELINE_SCRIPT $ACTION"
    cmd="$cmd --namespace $NAMESPACE"
    [ -n "$DRY_RUN" ] && cmd="$cmd $DRY_RUN"
    [ -n "$SKIP_VALIDATION" ] && cmd="$cmd $SKIP_VALIDATION"
    [ -n "$STAGE" ] && cmd="$cmd --stage $STAGE"
    [ -n "$OUTPUT_FILE" ] && cmd="$cmd --output $OUTPUT_FILE"
    
    # Execute
    log "Executing: $cmd"
    echo ""
    
    if eval "$cmd"; then
        log_success "Pipeline completed successfully!"
        return 0
    else
        log_error "Pipeline failed!"
        return 1
    fi
}

# Show summary
show_summary() {
    local exit_code=$1
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════════"
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}  ✅ PIPELINE EXECUTION SUCCESSFUL${NC}"
    else
        echo -e "${RED}  ❌ PIPELINE EXECUTION FAILED${NC}"
    fi
    echo "═══════════════════════════════════════════════════════════════════════════════"
    
    # Show logs location
    if [ -d "$LOG_DIR" ]; then
        echo ""
        log_info "Logs available in: $LOG_DIR"
        
        # List recent log files
        local latest_logs=$(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -3)
        if [ -n "$latest_logs" ]; then
            echo ""
            log_info "Recent log files:"
            echo "$latest_logs" | while read -r logfile; do
                echo "   - $(basename "$logfile")"
            done
        fi
    fi
    
    # Show output file if specified
    if [ -n "$OUTPUT_FILE" ] && [ -f "$OUTPUT_FILE" ]; then
        echo ""
        log_success "Results saved to: $OUTPUT_FILE"
        
        # Show quick summary from JSON
        if command -v jq &> /dev/null; then
            echo ""
            log_info "Quick Summary:"
            jq -r '.results[] | "   \(.stage): \(.status) (\(.duration)s)"' "$OUTPUT_FILE" 2>/dev/null || true
        fi
    fi
    
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
}

# Main execution
main() {
    parse_arguments "$@"
    
    print_banner
    
    check_prerequisites
    setup_environment
    
    echo ""
    
    # Run pipeline
    if run_pipeline; then
        EXIT_CODE=0
    else
        EXIT_CODE=1
    fi
    
    # Show summary
    show_summary $EXIT_CODE
    
    exit $EXIT_CODE
}

# Trap errors
trap 'log_error "Script interrupted"; exit 1' INT TERM

# Run main
main "$@"
