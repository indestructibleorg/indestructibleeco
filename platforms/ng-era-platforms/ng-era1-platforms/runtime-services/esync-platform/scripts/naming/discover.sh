#!/bin/bash
set -euo pipefail

echo "🔍 Discovering resources needing naming migration..."

DISCOVERY_REPORT="artifacts/reports/naming/discovery-report.json"
mkdir -p "$(dirname "$DISCOVERY_REPORT")"

# Initialize report
echo '{"discovery_timestamp": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'", "resources": []}' | jq '.' > "$DISCOVERY_REPORT"

# Scan for Kubernetes resources
if [ -d "deploy" ]; then
  echo "Scanning Kubernetes manifests..."
  
  find deploy -name "*.yaml" -o -name "*.yml" | while read -r file; do
    kind=$(yq eval '.kind // empty' "$file" 2>/dev/null || echo "")
    name=$(yq eval '.metadata.name // empty' "$file" 2>/dev/null || echo "")
    
    if [ -n "$kind" ] && [ -n "$name" ]; then
      pattern="^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$"
      
      if ! echo "$name" | grep -qE "$pattern"; then
        echo "Found non-compliant resource: $kind/$name"
        
        jq --arg kind "$kind" --arg name "$name" --arg file "$file" \
           '.resources += {"kind": $kind, "name": $name, "file": $file, "compliant": false}' \
           "$DISCOVERY_REPORT" | sponge "$DISCOVERY_REPORT"
      fi
    fi
  done
fi

# Scan for GitHub workflows
echo "Scanning GitHub workflows..."
find .github/workflows -name "*.yaml" -o -name "*.yml" | while read -r file; do
  name=$(basename "$file")
  pattern="^(ci|cd|test|security|auto-fix|naming|deploy|release)-"
  
  if ! echo "$name" | grep -qE "$pattern"; then
    echo "Found non-compliant workflow: $name"
    
    jq --arg name "$name" --arg file "$file" \
       '.resources += {"kind": "Workflow", "name": $name, "file": $file, "compliant": false}' \
       "$DISCOVERY_REPORT" | sponge "$DISCOVERY_REPORT"
  fi
done

echo "✅ Discovery complete"
echo "Report saved to $DISCOVERY_REPORT"

NON_COMPLIANT=$(jq '.resources | length' "$DISCOVERY_REPORT")
echo "Non-compliant resources: $NON_COMPLIANT"