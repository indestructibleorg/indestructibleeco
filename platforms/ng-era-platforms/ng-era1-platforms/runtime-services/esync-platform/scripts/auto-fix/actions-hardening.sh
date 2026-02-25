#!/bin/bash
set -euo pipefail

echo "🔧 Applying actions hardening fixes..."

# Find all workflow files
WORKFLOW_FILES=$(find .github/workflows -name "*.yml" -o -name "*.yaml")

# Apply hardening rules
for workflow in $WORKFLOW_FILES; do
  echo "Processing $workflow"
  
  # Add minimal permissions if not present
  if ! grep -q "permissions:" "$workflow"; then
    sed -i '/^name:/a permissions:\n  contents: read\n  pull-requests: read' "$workflow"
  fi
  
  # Add concurrency if not present
  if ! grep -q "concurrency:" "$workflow"; then
    sed -i '/^permissions:/a concurrency:\n  group: ${{ github.workflow }}-${{ github.ref }}\n  cancel-in-progress: true' "$workflow"
  fi
  
  # Pin actions to specific SHAs (placeholder - needs actual implementation)
  # This would be implemented with a more sophisticated tool
done

echo "✅ Actions hardening complete"