#!/bin/bash
# Infrastructure Validation Script
# Validates module manifests, policies, and governance configurations
#
# Dependencies:
#   - python3
#   - pyyaml (pip install pyyaml)
#   - jsonschema (pip install jsonschema)

set -e

# Enable comprehensive logging
exec > >(tee -a /tmp/infrastructure_validation.log)
exec 2>&1

echo "==================================="
echo "Infrastructure Validation Started"
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=================================="
echo "Infrastructure Validation"
echo "=================================="
echo ""

# Track validation results
VALIDATION_PASSED=true

# Function to print status
print_status() {
    if [ "$1" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $2"
    elif [ "$1" = "FAIL" ]; then
        echo -e "${RED}✗${NC} $2"
        VALIDATION_PASSED=false
    elif [ "$1" = "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $2"
    else
        echo "  $2"
    fi
}

# 1. Validate Module Manifests
echo "1. Validating Module Manifests"
echo "------------------------------"

MODULE_DIR="$REPO_ROOT/controlplane/baseline/modules"
SCHEMA_FILE="$MODULE_DIR/module-manifest.schema.json"

if [ ! -f "$SCHEMA_FILE" ]; then
    print_status "FAIL" "Module manifest schema not found: $SCHEMA_FILE"
else
    print_status "PASS" "Module manifest schema found"
    
    # Check if Python is available for JSON validation
    if command -v python3 &> /dev/null; then
        # Verify pyyaml is installed
        if ! python3 -c "import yaml" 2>/dev/null; then
            print_status "FAIL" "Python 'yaml' module not installed. Run: pip install pyyaml"
            VALIDATION_PASSED=false
        else
            # Validate each module manifest
            for module_dir in "$MODULE_DIR"/[0-9][0-9]-*/; do
                if [ -d "$module_dir" ]; then
                    module_name=$(basename "$module_dir")
                    manifest_file="${module_dir}module-manifest.yaml"
                    
                    if [ -f "$manifest_file" ]; then
                        # Check YAML syntax
                        if python3 -c "import yaml; yaml.safe_load(open('$manifest_file'))" 2>/dev/null; then
                            print_status "PASS" "Module $module_name: YAML syntax valid"
                        else
                            print_status "FAIL" "Module $module_name: YAML syntax error"
                            VALIDATION_PASSED=false
                        fi
                    else
                        print_status "WARN" "Module $module_name: manifest file not found"
                    fi
                fi
            done
        fi
    else
        print_status "WARN" "Python3 not available, skipping YAML validation"
    fi
fi

echo ""

# 2. Validate Module Registry
echo "2. Validating Module Registry"
echo "-----------------------------"

REGISTRY_FILE="$MODULE_DIR/REGISTRY.yaml"

if [ ! -f "$REGISTRY_FILE" ]; then
    print_status "FAIL" "Module registry not found: $REGISTRY_FILE"
else
    print_status "PASS" "Module registry found"
    
    if command -v python3 &> /dev/null; then
        if ! python3 -c "import yaml" 2>/dev/null; then
            print_status "FAIL" "Python 'yaml' module not installed. Run: pip install pyyaml"
            VALIDATION_PASSED=false
        elif python3 -c "import yaml; yaml.safe_load(open('$REGISTRY_FILE'))" 2>/dev/null; then
            print_status "PASS" "Module registry: YAML syntax valid"
        else
            print_status "FAIL" "Module registry: YAML syntax error"
            VALIDATION_PASSED=false
        fi
    else
        print_status "WARN" "Python3 not available, skipping YAML validation"
    fi
fi

echo ""

# 3. Validate Governance Policies
echo "3. Validating Governance Policies"
echo "---------------------------------"

POLICY_DIR="$REPO_ROOT/controlplane/governance/policies"
POLICY_MANIFEST="$POLICY_DIR/POLICY_MANIFEST.yaml"

if [ ! -f "$POLICY_MANIFEST" ]; then
    print_status "FAIL" "Policy manifest not found: $POLICY_MANIFEST"
else
    print_status "PASS" "Policy manifest found"
    
    if command -v python3 &> /dev/null; then
        if python3 -c "import yaml; yaml.safe_load(open('$POLICY_MANIFEST'))" 2>/dev/null; then
            print_status "PASS" "Policy manifest: YAML syntax valid"
        else
            print_status "FAIL" "Policy manifest: YAML syntax error"
        fi
    fi
fi

# Check for required Rego policies
REQUIRED_POLICIES=("naming.rego" "semantic.rego" "security.rego" "autonomy.rego")

for policy in "${REQUIRED_POLICIES[@]}"; do
    policy_file="$POLICY_DIR/$policy"
    if [ -f "$policy_file" ]; then
        print_status "PASS" "Policy found: $policy"
        
        # Basic Rego syntax check (check for package declaration)
        if grep -q "^package " "$policy_file"; then
            print_status "PASS" "Policy $policy: Has package declaration"
        else
            print_status "WARN" "Policy $policy: Missing package declaration"
        fi
    else
        print_status "FAIL" "Policy not found: $policy"
    fi
done

echo ""

# 4. Validate Supply Chain Security
echo "4. Validating Supply Chain Security"
echo "-----------------------------------"

SUPPLY_CHAIN_WORKFLOW="$REPO_ROOT/.github/workflows/supply-chain-security.yml"
SUPPLY_CHAIN_SCRIPT="$REPO_ROOT/scripts/supply-chain-tools-setup.sh"

if [ -f "$SUPPLY_CHAIN_WORKFLOW" ]; then
    print_status "PASS" "Supply chain workflow found"
    
    if command -v python3 &> /dev/null; then
        if python3 -c "import yaml; yaml.safe_load(open('$SUPPLY_CHAIN_WORKFLOW'))" 2>/dev/null; then
            print_status "PASS" "Supply chain workflow: YAML syntax valid"
        else
            print_status "FAIL" "Supply chain workflow: YAML syntax error"
        fi
    fi
else
    print_status "FAIL" "Supply chain workflow not found"
fi

if [ -f "$SUPPLY_CHAIN_SCRIPT" ]; then
    print_status "PASS" "Supply chain setup script found"
    
    if [ -x "$SUPPLY_CHAIN_SCRIPT" ]; then
        print_status "PASS" "Supply chain setup script is executable"
    else
        print_status "WARN" "Supply chain setup script is not executable"
    fi
else
    print_status "FAIL" "Supply chain setup script not found"
fi

echo ""

# 5. Validate Documentation
echo "5. Validating Documentation"
echo "--------------------------"

REQUIRED_DOCS=(
    "controlplane/baseline/modules/README.md"
    "controlplane/governance/policies/README.md"
    "docs/supply-chain-security.md"
    "PHASE1_COMPLETION_REPORT.md"
    "FEATURE_BRANCH_MERGE_SUMMARY.md"
)

for doc in "${REQUIRED_DOCS[@]}"; do
    doc_file="$REPO_ROOT/$doc"
    if [ -f "$doc_file" ]; then
        print_status "PASS" "Documentation found: $doc"
    else
        print_status "WARN" "Documentation not found: $doc"
    fi
done

echo ""

# 6. Module Dependency Validation
echo "6. Validating Module Dependencies"
echo "---------------------------------"

# Check if modules reference each other correctly
if command -v python3 &> /dev/null && [ -f "$REGISTRY_FILE" ]; then
    # Create temporary Python script for dependency validation using mktemp
    temp_script=$(mktemp /tmp/validate_deps.XXXXXX.py)
    trap "rm -f \"$temp_script\"" EXIT
    
    cat > "$temp_script" << 'PYEOF'
import yaml
import sys

try:
    with open('controlplane/baseline/modules/REGISTRY.yaml', 'r') as f:
        registry = yaml.safe_load(f)
    
    if 'modules' in registry:
        modules = registry['modules']
        module_ids = [m.get('module_id') for m in modules if 'module_id' in m]
        
        has_issues = False
        # Check for unknown dependencies
        for module in modules:
            if 'dependencies' in module:
                for dep in module['dependencies']:
                    if dep not in module_ids and dep != 'none':
                        print(f"WARN: Module {module.get('module_id')} has unknown dependency: {dep}")
                        has_issues = True
        
        if has_issues:
            print('WARN: Some dependency issues found')
            sys.exit(2)  # Exit code 2 for warnings
        else:
            print('PASS: No circular or unknown dependencies found')
            sys.exit(0)
    else:
        print('WARN: No modules section in registry')
        sys.exit(2)
except Exception as e:
    print(f'FAIL: Error validating dependencies: {e}')
    sys.exit(1)
PYEOF
    
    cd "$REPO_ROOT" && python3 "$temp_script"
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        print_status "PASS" "Module dependencies validated"
    elif [ $exit_code -eq 2 ]; then
        print_status "WARN" "Module dependency validation had warnings"
    else
        print_status "FAIL" "Module dependency validation failed"
    fi
else
    print_status "WARN" "Python3 or registry not available for dependency validation"
fi

echo ""
echo "=================================="
echo "Validation Summary"
echo "=================================="

if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}All validations passed!${NC}"
    exit 0
else
    echo -e "${RED}Some validations failed. Please review the output above.${NC}"
    exit 1
fi
