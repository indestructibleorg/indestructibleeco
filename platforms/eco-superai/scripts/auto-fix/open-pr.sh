#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform - Create Fix PR
# ============================================================================
# Creates a pull request with fixes for CI/CD issues. Handles branch
# creation, staging, committing with conventional commit messages, pushing,
# and PR creation via the gh CLI.
#
# Usage:
#   ./scripts/auto-fix/open-pr.sh --branch <name> --description <desc> [options]
#
# Options:
#   --branch <name>       Branch name for the fix (required)
#   --description <desc>  Fix description (required)
#   --type <type>         Conventional commit type: fix, chore, style, refactor (default: fix)
#   --scope <scope>       Commit scope (e.g., lint, types, deps, security)
#   --base <branch>       Base branch (default: main)
#   --labels <l1,l2>      Comma-separated labels to add
#   --reviewers <r1,r2>   Comma-separated reviewers to assign
#   --draft               Create as draft PR
#   --auto-merge          Enable auto-merge
#   --issue <number>      Link to issue number
#   --dry-run             Show what would be done without executing
#
# Exit codes:
#   0 - PR created successfully
#   1 - Error occurred
# ============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_FILE="${PROJECT_ROOT}/logs/open-pr-$(date +%Y%m%d-%H%M%S).log"

# Defaults
BRANCH_NAME=""
DESCRIPTION=""
COMMIT_TYPE="fix"
COMMIT_SCOPE=""
BASE_BRANCH="main"
LABELS=""
REVIEWERS=""
DRAFT=false
AUTO_MERGE=false
ISSUE_NUMBER=""
DRY_RUN=false

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch)       BRANCH_NAME="$2"; shift 2 ;;
        --description)  DESCRIPTION="$2"; shift 2 ;;
        --type)         COMMIT_TYPE="$2"; shift 2 ;;
        --scope)        COMMIT_SCOPE="$2"; shift 2 ;;
        --base)         BASE_BRANCH="$2"; shift 2 ;;
        --labels)       LABELS="$2"; shift 2 ;;
        --reviewers)    REVIEWERS="$2"; shift 2 ;;
        --draft)        DRAFT=true; shift ;;
        --auto-merge)   AUTO_MERGE=true; shift ;;
        --issue)        ISSUE_NUMBER="$2"; shift 2 ;;
        --dry-run)      DRY_RUN=true; shift ;;
        -h|--help)
            echo "Usage: $0 --branch <name> --description <desc> [options]"
            echo ""
            echo "Options:"
            echo "  --branch <name>       Branch name for the fix (required)"
            echo "  --description <desc>  Fix description (required)"
            echo "  --type <type>         Conventional commit type (default: fix)"
            echo "  --scope <scope>       Commit scope (e.g., lint, types)"
            echo "  --base <branch>       Base branch (default: main)"
            echo "  --labels <l1,l2>      Comma-separated labels"
            echo "  --reviewers <r1,r2>   Comma-separated reviewers"
            echo "  --draft               Create as draft PR"
            echo "  --auto-merge          Enable auto-merge"
            echo "  --issue <number>      Link to issue number"
            echo "  --dry-run             Show what would be done"
            exit 0
            ;;
        *) echo "ERROR: Unknown argument: $1" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Validate required arguments
# ---------------------------------------------------------------------------
if [[ -z "${BRANCH_NAME}" ]]; then
    echo "ERROR: --branch is required" >&2
    exit 1
fi

if [[ -z "${DESCRIPTION}" ]]; then
    echo "ERROR: --description is required" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
mkdir -p "$(dirname "${LOG_FILE}")"

log() {
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${ts}] $*" | tee -a "${LOG_FILE}"
}

info()    { log "[INFO]    $*"; }
error()   { log "[ERROR]   $*"; }
success() { log "[SUCCESS] $*"; }

die() {
    error "$@"
    exit 1
}

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
check_prerequisites() {
    info "Checking prerequisites..."

    command -v git &>/dev/null || die "git is required"
    command -v gh  &>/dev/null || die "gh CLI is required (https://cli.github.com)"

    # Verify gh authentication
    if ! gh auth status &>/dev/null 2>&1; then
        die "gh CLI is not authenticated. Run 'gh auth login' first."
    fi

    # Verify we are in a git repository
    if ! git -C "${PROJECT_ROOT}" rev-parse --is-inside-work-tree &>/dev/null; then
        die "Not inside a git repository"
    fi

    # Check for uncommitted changes (we need something to commit)
    cd "${PROJECT_ROOT}"
    if git diff --quiet && git diff --cached --quiet; then
        local untracked
        untracked="$(git ls-files --others --exclude-standard | wc -l)"
        if [[ "${untracked}" -eq 0 ]]; then
            die "No changes to commit. Stage your fixes first or run the fix tools."
        fi
    fi

    info "Prerequisites check passed"
}

# ---------------------------------------------------------------------------
# Build commit message
# ---------------------------------------------------------------------------
build_commit_message() {
    local msg="${COMMIT_TYPE}"
    if [[ -n "${COMMIT_SCOPE}" ]]; then
        msg="${msg}(${COMMIT_SCOPE})"
    fi
    msg="${msg}: ${DESCRIPTION}"

    echo "${msg}"
}

# ---------------------------------------------------------------------------
# Build PR body
# ---------------------------------------------------------------------------
build_pr_body() {
    local commit_msg="$1"

    local body="## Summary

${DESCRIPTION}

## Changes"

    # Add file change summary
    cd "${PROJECT_ROOT}"
    local changed_files
    changed_files="$(git diff --cached --name-only 2>/dev/null || true)"
    if [[ -z "${changed_files}" ]]; then
        changed_files="$(git diff --name-only 2>/dev/null || true)"
    fi

    if [[ -n "${changed_files}" ]]; then
        body="${body}

\`\`\`
$(echo "${changed_files}" | head -20)
\`\`\`"
        local file_count
        file_count="$(echo "${changed_files}" | wc -l)"
        if [[ "${file_count}" -gt 20 ]]; then
            body="${body}
...and $((file_count - 20)) more files"
        fi
    fi

    # Add issue reference
    if [[ -n "${ISSUE_NUMBER}" ]]; then
        body="${body}

## Related Issues

Closes #${ISSUE_NUMBER}"
    fi

    body="${body}

## Type of Change

- [x] \`${COMMIT_TYPE}\`: ${DESCRIPTION}

## Checklist

- [x] Changes follow the project coding standards
- [ ] Tests pass locally (\`make test\`)
- [ ] Lint passes (\`ruff check\`)
- [ ] Type checks pass (\`mypy\`)

---
*This PR was auto-generated by \`scripts/auto-fix/open-pr.sh\`*"

    echo "${body}"
}

# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------
main() {
    info "Starting PR creation workflow..."
    info "  Branch:      ${BRANCH_NAME}"
    info "  Description: ${DESCRIPTION}"
    info "  Type:        ${COMMIT_TYPE}"
    info "  Base:        ${BASE_BRANCH}"

    check_prerequisites

    cd "${PROJECT_ROOT}"

    # Store the current branch to return to on failure
    local original_branch
    original_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "HEAD")"

    # Build commit message
    local commit_msg
    commit_msg="$(build_commit_message)"
    info "Commit message: ${commit_msg}"

    if [[ "${DRY_RUN}" == "true" ]]; then
        echo ""
        echo "============================================================================"
        echo "  DRY RUN - No changes will be made"
        echo "============================================================================"
        echo ""
        echo "  Branch:         ${BRANCH_NAME}"
        echo "  Base:           ${BASE_BRANCH}"
        echo "  Commit message: ${commit_msg}"
        echo "  Labels:         ${LABELS:-none}"
        echo "  Reviewers:      ${REVIEWERS:-none}"
        echo "  Draft:          ${DRAFT}"
        echo ""
        echo "  Staged changes:"
        git diff --cached --stat 2>/dev/null || git diff --stat 2>/dev/null || echo "  (no changes detected)"
        echo ""
        echo "============================================================================"
        exit 0
    fi

    # Step 1: Create and switch to new branch
    info "Creating branch '${BRANCH_NAME}' from HEAD..."
    if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}" 2>/dev/null; then
        warn_msg="Branch '${BRANCH_NAME}' already exists locally. Switching to it."
        info "${warn_msg}"
        git checkout "${BRANCH_NAME}" 2>&1 | tee -a "${LOG_FILE}"
    else
        git checkout -b "${BRANCH_NAME}" 2>&1 | tee -a "${LOG_FILE}"
    fi

    # Step 2: Stage all changes
    info "Staging changes..."
    git add -A 2>&1 | tee -a "${LOG_FILE}"

    # Verify something is staged
    if git diff --cached --quiet; then
        die "No changes staged after 'git add -A'. Nothing to commit."
    fi

    # Show what we are committing
    info "Changes to be committed:"
    git diff --cached --stat 2>&1 | tee -a "${LOG_FILE}"

    # Step 3: Commit
    info "Creating commit..."
    git commit -m "${commit_msg}" 2>&1 | tee -a "${LOG_FILE}"

    # Step 4: Push
    info "Pushing branch '${BRANCH_NAME}' to origin..."
    git push -u origin "${BRANCH_NAME}" 2>&1 | tee -a "${LOG_FILE}" || {
        error "Push failed. Returning to original branch."
        git checkout "${original_branch}" 2>/dev/null || true
        die "Failed to push branch"
    }

    # Step 5: Create PR
    info "Creating pull request..."

    local pr_title="${commit_msg}"
    local pr_body
    pr_body="$(build_pr_body "${commit_msg}")"

    local gh_args=()
    gh_args+=(pr create)
    gh_args+=(--title "${pr_title}")
    gh_args+=(--body "${pr_body}")
    gh_args+=(--base "${BASE_BRANCH}")
    gh_args+=(--head "${BRANCH_NAME}")

    if [[ "${DRAFT}" == "true" ]]; then
        gh_args+=(--draft)
    fi

    if [[ -n "${LABELS}" ]]; then
        IFS=',' read -ra label_arr <<< "${LABELS}"
        for label in "${label_arr[@]}"; do
            gh_args+=(--label "${label}")
        done
    fi

    if [[ -n "${REVIEWERS}" ]]; then
        IFS=',' read -ra reviewer_arr <<< "${REVIEWERS}"
        for reviewer in "${reviewer_arr[@]}"; do
            gh_args+=(--reviewer "${reviewer}")
        done
    fi

    local pr_url
    pr_url="$(gh "${gh_args[@]}" 2>&1 | tee -a "${LOG_FILE}")"

    if [[ -z "${pr_url}" ]]; then
        die "Failed to create PR"
    fi

    # Step 6: Enable auto-merge if requested
    if [[ "${AUTO_MERGE}" == "true" ]]; then
        info "Enabling auto-merge..."
        gh pr merge --auto --squash "${pr_url}" 2>&1 | tee -a "${LOG_FILE}" || {
            info "Auto-merge not available (may require branch protection rules)"
        }
    fi

    # Summary
    echo ""
    echo "============================================================================"
    echo "  Pull Request Created Successfully"
    echo "============================================================================"
    echo ""
    echo "  PR URL:    ${pr_url}"
    echo "  Branch:    ${BRANCH_NAME}"
    echo "  Base:      ${BASE_BRANCH}"
    echo "  Title:     ${pr_title}"
    if [[ -n "${LABELS}" ]]; then
        echo "  Labels:    ${LABELS}"
    fi
    if [[ -n "${REVIEWERS}" ]]; then
        echo "  Reviewers: ${REVIEWERS}"
    fi
    echo ""
    echo "  Log: ${LOG_FILE}"
    echo "============================================================================"

    success "PR created: ${pr_url}"
}

main "$@"
