#!/bin/bash
set -euo pipefail

echo "🔧 Remediate naming convention violations..."

PLAN_FILE="artifacts/reports/naming/migration-plan.yaml"
mkdir -p "$(dirname "$PLAN_FILE")"

# Generate migration plan if it doesn't exist
if [ ! -f "$PLAN_FILE" ]; then
  echo "Generating migration plan..."
  
  cat > "$PLAN_FILE" << 'EOF'
# Naming Migration Plan
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
metadata:
  version: "1.0.0"
  environment: "dev"
  
stages:
  - name: "discovery"
    description: "Identify non-compliant resources"
    status: "completed"
    
  - name: "dry-run"
    description: "Preview changes without applying"
    status: "pending"
    
  - name: "staged-rename"
    description: "Rename resources with new names alongside old"
    status: "pending"
    
  - name: "cutover"
    description: "Switch traffic to new names"
    status: "pending"
    
  - name: "cleanup"
    description: "Remove old resources after verification"
    status: "pending"

rollback:
  enabled: true
  timeout_minutes: 20
EOF
fi

# Apply remediations
echo "Applying naming convention remediations..."

# Add required labels to Kubernetes resources
find deploy -name "*.yaml" -o -name "*.yml" | while read -r file; do
  kind=$(yq eval '.kind // empty' "$file" 2>/dev/null || echo "")
  
  if [ -n "$kind" ]; then
    echo "Processing $file ($kind)"
    
    # Add environment label if missing
    if ! yq eval '.metadata.labels.environment // empty' "$file" | grep -q .; then
      yq eval '.metadata.labels.environment = "dev"' -i "$file"
    fi
    
    # Add component label if missing
    if ! yq eval '.metadata.labels.component // empty' "$file" | grep -q .; then
      yq eval '.metadata.labels.component = "esync"' -i "$file"
    fi
    
    # Add version label if missing
    if ! yq eval '.metadata.labels.version // empty' "$file" | grep -q .; then
      yq eval '.metadata.labels.version = "v1.0.0"' -i "$file"
    fi
    
    echo "✅ Added labels to $file"
  fi
done

echo "✅ Remediation complete"