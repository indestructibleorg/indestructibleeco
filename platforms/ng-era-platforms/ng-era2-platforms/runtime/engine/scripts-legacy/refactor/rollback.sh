#!/bin/bash
# scripts/refactor/rollback.sh
# Automated rollback script for three-phase refactoring
#
# Usage: bash scripts/refactor/rollback.sh <LEVEL> [TARGET]
#
# Levels:
#   file <filepath>        - Rollback single file
#   module <module-name>   - Rollback entire module
#   phase <phase-number>   - Rollback entire phase (1, 2, or 3)
#   full [commit-id]       - Full system rollback

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ROLLBACK_LEVEL="${1}"
TARGET="${2}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

log_info() {
    echo -e "${BLUE}ℹ${NC} $@"
}

log_success() {
    echo -e "${GREEN}✓${NC} $@"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $@"
}

log_error() {
    echo -e "${RED}✗${NC} $@"
}

# Function to backup current state
backup_current_state() {
    local backup_dir="$REPO_ROOT/.rollback-backups"
    mkdir -p "$backup_dir"
    local backup_file="$backup_dir/backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    log_info "Creating backup of current state..."
    tar -czf "$backup_file" \
        --exclude=".git" \
        --exclude="node_modules" \
        --exclude=".rollback-backups" \
        -C "$REPO_ROOT" .
    
    log_success "Backup created: $backup_file"
}

# Function to validate rollback
validate_rollback() {
    log_info "Validating rollback..."
    
    cd "$REPO_ROOT"
    
    # Check git status
    if ! git status &> /dev/null; then
        log_error "Git repository validation failed"
        return 1
    fi
    
    # Run basic tests if available
    if [[ -f "package.json" ]] && grep -q '"test"' "package.json"; then
        log_info "Running test suite..."
        npm test || log_warning "Some tests failed after rollback"
    fi
    
    log_success "Rollback validation complete"
}

# Rollback single file
rollback_file() {
    local filepath="$1"
    
    if [[ -z "$filepath" ]]; then
        log_error "File path required for file-level rollback"
        exit 1
    fi
    
    log_info "Rolling back file: $filepath"
    
    cd "$REPO_ROOT"
    
    if [[ ! -f "$filepath" ]]; then
        log_error "File not found: $filepath"
        exit 1
    fi
    
    backup_current_state
    
    git checkout HEAD -- "$filepath"
    
    log_success "File rollback complete: $filepath"
}

# Rollback module
rollback_module() {
    local module_name="$1"
    
    if [[ -z "$module_name" ]]; then
        log_error "Module name required for module-level rollback"
        exit 1
    fi
    
    log_info "Rolling back module: $module_name"
    
    cd "$REPO_ROOT"
    
    backup_current_state
    
    # Find commits related to this module (last 20 commits)
    log_info "Finding commits related to module: $module_name"
    local module_commits=$(git log --oneline --grep="$module_name" -20 | awk '{print $1}')
    
    if [[ -z "$module_commits" ]]; then
        log_warning "No commits found for module: $module_name"
        log_info "Attempting to rollback module directory..."
        
        # Try to find module directory
        local module_dir=$(find . -type d -name "*$module_name*" | head -1)
        if [[ -n "$module_dir" ]]; then
            git checkout HEAD -- "$module_dir"
            log_success "Module directory rollback complete: $module_dir"
        else
            log_error "Module not found: $module_name"
            exit 1
        fi
    else
        # Revert commits
        git revert --no-commit $module_commits || true
        git commit -m "rollback(module): Revert $module_name changes" || true
        
        log_success "Module rollback complete: $module_name"
    fi
}

# Rollback phase
rollback_phase() {
    local phase_number="$1"
    
    if [[ -z "$phase_number" ]]; then
        log_error "Phase number required (1, 2, or 3)"
        exit 1
    fi
    
    if [[ ! "$phase_number" =~ ^[123]$ ]]; then
        log_error "Invalid phase number: $phase_number (must be 1, 2, or 3)"
        exit 1
    fi
    
    log_warning "Rolling back Phase $phase_number"
    
    cd "$REPO_ROOT"
    
    backup_current_state
    
    # Check for phase checkpoint
    local checkpoint_file="$REPO_ROOT/.refactor-phase-$phase_number-checkpoint"
    
    if [[ -f "$checkpoint_file" ]]; then
        local phase_start_commit=$(cat "$checkpoint_file")
        log_info "Found phase $phase_number checkpoint: $phase_start_commit"
        
        read -p "Reset to phase $phase_number start? This will discard all changes after checkpoint. (y/N) " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git reset --hard "$phase_start_commit"
            log_success "Phase $phase_number rollback complete"
        else
            log_info "Rollback cancelled"
            exit 0
        fi
    else
        log_error "Phase $phase_number checkpoint not found: $checkpoint_file"
        log_info "Cannot perform automatic phase rollback without checkpoint"
        exit 1
    fi
}

# Full rollback
rollback_full() {
    local target_commit="${1:-HEAD~1}"
    
    log_error "WARNING: Full system rollback requested"
    log_warning "Target: $target_commit"
    
    read -p "This will reset the entire repository. Continue? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    cd "$REPO_ROOT"
    
    backup_current_state
    
    log_info "Performing full system rollback to: $target_commit"
    
    git reset --hard "$target_commit"
    
    # Reinstall dependencies
    if [[ -f "package.json" ]]; then
        log_info "Reinstalling npm dependencies..."
        npm install
    fi
    
    # Rebuild if necessary
    if [[ -f "package.json" ]] && grep -q '"build"' "package.json"; then
        log_info "Rebuilding project..."
        npm run build || log_warning "Build failed"
    fi
    
    log_success "Full system rollback complete"
}

# Show usage
show_usage() {
    echo "Usage: $0 <LEVEL> [TARGET]"
    echo ""
    echo "Rollback Levels:"
    echo "  file <filepath>        - Rollback single file to HEAD"
    echo "  module <module-name>   - Rollback entire module (revert related commits)"
    echo "  phase <phase-number>   - Rollback entire phase (1, 2, or 3)"
    echo "  full [commit-id]       - Full system rollback (default: HEAD~1)"
    echo ""
    echo "Examples:"
    echo "  $0 file src/core/main.ts"
    echo "  $0 module core/unified_integration"
    echo "  $0 phase 2"
    echo "  $0 full abc123"
    echo ""
    exit 0
}

# Main
main() {
    if [[ -z "$ROLLBACK_LEVEL" ]] || [[ "$ROLLBACK_LEVEL" == "-h" ]] || [[ "$ROLLBACK_LEVEL" == "--help" ]]; then
        show_usage
    fi
    
    echo "🔄 Refactoring Rollback"
    echo "Repository: $REPO_ROOT"
    echo "Level: $ROLLBACK_LEVEL"
    echo "Target: ${TARGET:-default}"
    echo ""
    
    case "$ROLLBACK_LEVEL" in
        file)
            rollback_file "$TARGET"
            ;;
        module)
            rollback_module "$TARGET"
            ;;
        phase)
            rollback_phase "$TARGET"
            ;;
        full)
            rollback_full "$TARGET"
            ;;
        *)
            log_error "Invalid rollback level: $ROLLBACK_LEVEL"
            show_usage
            ;;
    esac
    
    # Validate rollback
    validate_rollback
    
    echo ""
    log_success "Rollback completed successfully"
}

# Trap errors
trap 'log_error "Rollback script failed at line $LINENO"; exit 1' ERR

main
