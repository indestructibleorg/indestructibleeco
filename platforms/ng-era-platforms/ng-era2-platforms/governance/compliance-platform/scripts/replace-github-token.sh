#!/bin/bash
# @GL-governed
# @GL-layer: GL30-49
# @GL-semantic: replace-github-token
# @GL-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json

# GL Governance Token Replacement Script
# Script to replace GITHUB_TOKEN with GL_TOKEN in workflows

set -e

cd "$(dirname "$0")/.."

WORKFLOWS=(
    ".github/workflows/GL-security-pipeline.yml"
    ".github/workflows/GL-unified-ci.yml"
    ".github/workflows/ai-algorithm-mentor.yml"
    ".github/workflows/ai-pr-reviewer.yml"
    ".github/workflows/automated-issue-carrier.yml"
    ".github/workflows/gl-artifacts-generator.yml"
    ".github/workflows/issue-metrics.yml"
    ".github/workflows/issue-triage.yml"
    ".github/workflows/production-ci-cd.yml"
    ".github/workflows/profile-readme-stats.yml"
    ".github/workflows/publish-npm-packages.yml"
    ".github/workflows/release.yml"
    ".github/workflows/scheduled-dashboard-updates.yml"
    ".github/workflows/super-linter.yml"
    ".github/workflows/todo-tracker.yml"
    ".github/workflows/todo.yml"
    ".github/workflows/update-readme-repo-info.yml"
    ".github/workflows/waka-readme.yml"
    ".github/workflows/words-really-matter.yml"
)

echo "Replacing GITHUB_TOKEN with GL_TOKEN in workflows..."
echo "===================================================="

for workflow in "${WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        echo "Processing: $workflow"
        tmp_file="$(mktemp)"
        sed 's/secrets\.GITHUB_TOKEN/secrets.GL_TOKEN/g' "$workflow" > "$tmp_file"
        mv "$tmp_file" "$workflow"
        echo "  ✓ Updated"
    else
        echo "  ✗ File not found: $workflow"
    fi
done

echo ""
echo "Replacement complete!"
echo "===================="
echo "Please review the changes before committing."