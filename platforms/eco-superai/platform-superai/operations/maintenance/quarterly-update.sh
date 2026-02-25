#!/bin/bash
# Quarterly Version Update Script
# P0 Critical: Automated quarterly version update and release process

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Configuration
QUARTER="${QUARTER:-$(date +%q)}"
YEAR="${YEAR:-$(date +%Y)}"
VERSION_MAJOR="${VERSION_MAJOR:-1}"
VERSION_MINOR="${VERSION_MINOR:-0}"
VERSION_PATCH="${VERSION_PATCH:-$(git describe --tags --abbrev=0 2>/dev/null | cut -d'.' -f3 || echo 0)}"
NEW_VERSION="${VERSION_MAJOR}.${VERSION_MINOR}.$((VERSION_PATCH + 1))"
MAINTENANCE_WINDOW="${MAINTENANCE_WINDOW:-$(date +%Y-%m-%d)} 02:00-06:00"

log_info "Starting Quarterly Version Update - Q${QUARTER} ${YEAR}"
log_info "New version: ${NEW_VERSION}"

# Pre-update checks
pre_update_checks() {
    log_step "Running pre-update checks..."
    
    # Check git status
    if [ "$(git status --porcelain | wc -l)" -ne 0 ]; then
        log_error "Git working directory is not clean"
        exit 1
    fi
    
    log_info "Pre-update checks passed"
}

# Create release branch
create_release_branch() {
    log_step "Creating release branch..."
    
    local branch_name="release/v${NEW_VERSION}"
    git checkout -b "$branch_name"
    
    log_info "Release branch created: $branch_name"
}

# Update version numbers
update_versions() {
    log_step "Updating version numbers..."
    
    sed -i "s/version = &quot;.*&quot;/version = &quot;${NEW_VERSION}&quot;/" pyproject.toml
    log_info "Updated pyproject.toml to ${NEW_VERSION}"
}

# Tag and push
tag_and_push() {
    log_step "Tagging and pushing..."
    
    git add -A
    git commit -m "release: v${NEW_VERSION} - Quarterly Update"
    git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}"
    
    git push origin "release/v${NEW_VERSION}"
    git push origin "v${NEW_VERSION}"
}

# Main execution
main() {
    pre_update_checks
    create_release_branch
    update_versions
    tag_and_push
    
    log_info "Quarterly update v${NEW_VERSION} completed"
}

main "$@"