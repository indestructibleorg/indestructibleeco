#!/bin/bash
set -euo pipefail

echo "🔄 Rollback naming migration..."

ROLLBACK_FILE="artifacts/reports/naming/rollback-state.json"

# Check if rollback state exists
if [ ! -f "$ROLLBACK_FILE" ]; then
  echo "❌ No rollback state found"
  exit 1
fi

# Restore original resource names
echo "Restoring original resource names..."

jq -c '.resources[]' "$ROLLBACK_FILE" | while read -r resource; do
  file=$(echo "$resource" | jq -r '.file')
  old_name=$(echo "$resource" | jq -r '.old_name')
  
  echo "Restoring $old_name in $file"
  
  yq eval ".metadata.name = "$old_name"" -i "$file"
  
  echo "✅ Restored $file"
done

echo "✅ Rollback complete"
echo "Please verify and commit changes manually"
