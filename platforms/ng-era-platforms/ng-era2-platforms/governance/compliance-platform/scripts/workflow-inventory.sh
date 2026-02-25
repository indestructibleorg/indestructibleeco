#!/bin/bash
# Workflow Inventory Script
# Analyzes all GitHub Actions workflows and categorizes them

set -e

WORKFLOWS_DIR=".github/workflows"
OUTPUT_FILE="workflow-inventory.json"

echo "=== GitHub Actions Workflow Inventory ===" > workflow-inventory.txt
echo "Generated: $(date)" >> workflow-inventory.txt
echo "" >> workflow-inventory.txt

# Initialize JSON output
echo "{" > "$OUTPUT_FILE"
echo "  &quot;generated&quot;: &quot;$(date -Iseconds)&quot;," >> "$OUTPUT_FILE"
echo "  &quot;total_workflows&quot;: $(find $WORKFLOWS_DIR -name '*.yml' -o -name '*.yaml' | wc -l)," >> "$OUTPUT_FILE"
echo "  &quot;categories&quot;: {" >> "$OUTPUT_FILE"

# Analyze each workflow
for workflow in $WORKFLOWS_DIR/*.yml $WORKFLOWS_DIR/*.yaml; do
    if [ -f "$workflow" ]; then
        filename=$(basename "$workflow")
        lines=$(wc -l < "$workflow")
        size=$(du -h "$workflow" | cut -f1)
        
        echo "=== $filename ===" >> workflow-inventory.txt
        echo "Size: $lines lines, $size" >> workflow-inventory.txt
        echo "Triggers:" >> workflow-inventory.txt
        grep -A 10 "^on:" "$workflow" | head -15 >> workflow-inventory.txt
        echo "" >> workflow-inventory.txt
    fi
done

# Categorize workflows
echo "    &quot;deployment&quot;: [" >> "$OUTPUT_FILE"
grep -l "deploy" $WORKFLOWS_DIR/*.yml 2>/dev/null | xargs -I{} basename {} | sed 's/.yml//' | sed 's/$/",/' | sed '$ s/,$//' >> "$OUTPUT_FILE"
echo "    ]," >> "$OUTPUT_FILE"

echo "    &quot;security&quot;: [" >> "$OUTPUT_FILE"
grep -l "security\|scan\|vulnerability\|trivy\|snyk\|codeql" $WORKFLOWS_DIR/*.yml 2>/dev/null | xargs -I{} basename {} | sed 's/.yml//' | sed 's/$/",/' | sed '$ s/,$//' >> "$OUTPUT_FILE"
echo "    ]," >> "$OUTPUT_FILE"

echo "    &quot;governance&quot;: [" >> "$OUTPUT_FILE"
grep -l "governance\|policy\|opa\|conftest\|compliance" $WORKFLOWS_DIR/*.yml 2>/dev/null | xargs -I{} basename {} | sed 's/.yml//' | sed 's/$/",/' | sed '$ s/,$//' >> "$OUTPUT_FILE"
echo "    ]," >> "$OUTPUT_FILE"

echo "    &quot;ci&quot;: [" >> "$OUTPUT_FILE"
grep -l "build\|test\|lint\|ci" $WORKFLOWS_DIR/*.yml 2>/dev/null | xargs -I{} basename {} | sed 's/.yml//' | sed 's/$/",/' | sed '$ s/,$//' >> "$OUTPUT_FILE"
echo "    ]," >> "$OUTPUT_FILE"

echo "    &quot;automation&quot;: [" >> "$OUTPUT_FILE"
grep -l "auto\|bot\|issue\|pr\|triage" $WORKFLOWS_DIR/*.yml 2>/dev/null | xargs -I{} basename {} | sed 's/.yml//' | sed 's/$/",/' | sed '$ s/,$//' >> "$OUTPUT_FILE"
echo "    ]" >> "$OUTPUT_FILE"

echo "  }" >> "$OUTPUT_FILE"
echo "}" >> "$OUTPUT_FILE"

echo "✅ Workflow inventory complete"
echo "📄 Text output: workflow-inventory.txt"
echo "📊 JSON output: workflow-inventory.json"
echo ""
echo "Summary:"
cat workflow-inventory.txt | grep "===.*===" | wc -l | xargs -I{} echo "  Total workflows analyzed: {}"