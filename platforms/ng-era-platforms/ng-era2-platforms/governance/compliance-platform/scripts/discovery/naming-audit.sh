#!/bin/bash
# @GL-governed
# @GL-layer: GL90-95 (Audit Layer)
# @GL-semantic: naming-convention-audit
# @GL-charter-version: 5.0.0
# @GL-audit-trail: Created for GL Platform v5.0 deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-all}"
RESOURCE_TYPE="${RESOURCE_TYPE:-all}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-json}"
OUTPUT_FILE="${OUTPUT_FILE:-}"
VERBOSE="${VERBOSE:-false}"

# Naming patterns
NAMING_PATTERNS=(
    "deploy|deployment:^(dev|staging|prod)-[a-z0-9-]+-deploy-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$"
    "svc|service:^(dev|staging|prod)-[a-z0-9-]+-svc-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$"
    "ing|ingress:^(dev|staging|prod)-[a-z0-9-]+-ing-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$"
    "cm|configmap:^(dev|staging|prod)-[a-z0-9-]+-cm-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$"
    "secret:^(dev|staging|prod)-[a-z0-9-]+-secret-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$"
    "sts|statefulset:^(dev|staging|prod)-[a-z0-9-]+-sts-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$"
    "ds|daemonset:^(dev|staging|prod)-[a-z0-9-]+-ds-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$"
    "pvc:^(dev|staging|prod)-[a-z0-9-]+-pvc-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$"
)

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Check if resource matches naming pattern
check_naming_pattern() {
    local resource_type="$1"
    local resource_name="$2"
    local namespace="$3"
    
    local pattern=""
    local expected_type=""
    
    for pattern_def in "${NAMING_PATTERNS[@]}"; do
        local types="${pattern_def%%:*}"
        local pattern_value="${pattern_def##*:}"
        
        if [[ "$types" =~ (^|,)$resource_type(,|$) ]]; then
            pattern="$pattern_value"
            expected_type="$types"
            break
        fi
    done
    
    if [[ -z "$pattern" ]]; then
        log_verbose "No pattern defined for type: $resource_type"
        return 0
    fi
    
    if [[ "$resource_name" =~ $pattern ]]; then
        return 0  # Compliant
    else
        return 1  # Non-compliant
    fi
}

# Suggest compliant name
suggest_compliant_name() {
    local resource_type="$1"
    local resource_name="$2"
    local namespace="$3"
    
    # Determine environment from namespace
    local env="dev"
    if [[ "$namespace" =~ staging ]]; then
        env="staging"
    elif [[ "$namespace" =~ prod|production ]]; then
        env="prod"
    fi
    
    # Extract base name (remove common suffixes)
    local base_name=$(echo "$resource_name" | sed 's/-\(deploy\|svc\|ing\|cm\|secret\|sts\|ds\|pvc\)$//' | sed 's/-v[0-9]\+\.[0-9]\+\.[0-9]\+.*$//')
    
    # Generate short suffix
    local short_type=""
    case "$resource_type" in
        deployment) short_type="deploy" ;;
        service) short_type="svc" ;;
        ingress) short_type="ing" ;;
        configmap) short_type="cm" ;;
        secret) short_type="secret" ;;
        statefulset) short_type="sts" ;;
        daemonset) short_type="ds" ;;
        persistentvolumeclaim) short_type="pvc" ;;
        *) short_type="$resource_type" ;;
    esac
    
    # Generate version
    local version="1.0.0"
    
    # Construct compliant name
    local compliant_name="${env}-${base_name}-${short_type}-v${version}"
    
    echo "$compliant_name"
}

# Audit resources
audit_resources() {
    log_info "Auditing resources..."
    
    local results="[]"
    local total_count=0
    local compliant_count=0
    local non_compliant_count=0
    local violations="[]"
    
    # Get resource types to audit
    local resource_types=()
    if [[ "$RESOURCE_TYPE" == "all" ]]; then
        resource_types=("deployments" "services" "ingresses" "configmaps" "secrets" "statefulsets" "daemonsets" "persistentvolumeclaims")
    else
        resource_types=("$RESOURCE_TYPE")
    fi
    
    for resource_type in "${resource_types[@]}"; do
        log_info "  Auditing $resource_type..."
        
        # Get resources
        local resources=$(kubectl get "$resource_type" -A -o json 2>/dev/null || echo '{"items":[]}')
        
        # Process each resource
        while IFS= read -r resource; do
            total_count=$((total_count + 1))
            
            local name=$(echo "$resource" | jq -r '.metadata.name')
            local namespace=$(echo "$resource" | jq -r '.metadata.namespace')
            local short_type=$(echo "$resource_type" | sed 's/s$//')
            
            log_verbose "    Checking: $namespace/$name"
            
            if check_naming_pattern "$short_type" "$name" "$namespace"; then
                compliant_count=$((compliant_count + 1))
                log_verbose "      ✓ Compliant"
            else
                non_compliant_count=$((non_compliant_count + 1))
                log_verbose "      ✗ Non-compliant"
                
                local suggested_name=$(suggest_compliant_name "$short_type" "$name" "$namespace")
                
                local violation=$(cat << EOF
{
  "namespace": "$namespace",
  "resource_type": "$short_type",
  "resource_name": "$name",
  "suggested_name": "$suggested_name",
  "severity": "medium"
}
EOF
)
                
                violations=$(echo "$violations" | jq --argjson v "$violation" '. + [$v]')
            fi
        done < <(echo "$resources" | jq -c '.items[]' 2>/dev/null || true)
    done
    
    # Calculate compliance rate
    local compliance_rate=0
    if [[ $total_count -gt 0 ]]; then
        compliance_rate=$(echo "scale=2; $compliant_count * 100 / $total_count" | bc)
    fi
    
    # Generate results
    results=$(cat << EOF
{
  "timestamp": "$(date -Iseconds)",
  "cluster": "$(kubectl config current-context)",
  "namespace_filter": "$NAMESPACE",
  "resource_type_filter": "$RESOURCE_TYPE",
  "summary": {
    "total_resources": $total_count,
    "compliant_resources": $compliant_count,
    "non_compliant_resources": $non_compliant_count,
    "compliance_rate": $compliance_rate
  },
  "violations": $violations
}
EOF
)
    
    # Output results
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        if [[ -n "$OUTPUT_FILE" ]]; then
            echo "$results" > "$OUTPUT_FILE"
            log_success "Results saved to: $OUTPUT_FILE"
        else
            echo "$results" | jq .
        fi
    elif [[ "$OUTPUT_FORMAT" == "markdown" ]]; then
        output_markdown "$results"
    else
        log_error "Unsupported output format: $OUTPUT_FORMAT"
        exit 1
    fi
    
    # Print summary
    log_info "Audit Summary:"
    log_info "  Total Resources: $total_count"
    log_info "  Compliant: $compliant_count"
    log_info "  Non-compliant: $non_compliant_count"
    log_info "  Compliance Rate: ${compliance_rate}%"
    
    if [[ $non_compliant_count -gt 0 ]]; then
        log_warning "Found $non_compliant_count naming convention violations"
        return 1
    else
        log_success "All resources are compliant with naming conventions!"
        return 0
    fi
}

# Output in Markdown format
output_markdown() {
    local results="$1"
    
    local timestamp=$(echo "$results" | jq -r '.timestamp')
    local cluster=$(echo "$results" | jq -r '.cluster')
    local total=$(echo "$results" | jq '.summary.total_resources')
    local compliant=$(echo "$results" | jq '.summary.compliant_resources')
    local non_compliant=$(echo "$results" | jq '.summary.non_compliant_resources')
    local compliance_rate=$(echo "$results" | jq '.summary.compliance_rate')
    
    cat << EOF
# Naming Convention Audit Report

**Timestamp**: $timestamp
**Cluster**: $cluster

## Summary

| Metric | Value |
|--------|-------|
| Total Resources | $total |
| Compliant | $compliant |
| Non-compliant | $non_compliant |
| Compliance Rate | ${compliance_rate}% |

## Violations

EOF
    
    if [[ "$non_compliant" -gt 0 ]]; then
        echo "| Namespace | Type | Current Name | Suggested Name | Severity |" >> "$OUTPUT_FILE"
        echo "|-----------|------|--------------|----------------|----------|" >> "$OUTPUT_FILE"
        
        echo "$results" | jq -r '.violations[] | "\(.namespace)|\(.resource_type)|\(.resource_name)|\(.suggested_name)|\(.severity)"' | \
            while IFS='|' read -r ns type current suggested severity; do
                echo "| $ns | $type | \`$current\` | \`$suggested\` | $severity |"
            done
    else
        echo "No violations found! 🎉"
    fi
}

# Main execution
main() {
    log_info "Starting Naming Convention Audit..."
    
    audit_resources
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Audit completed successfully"
    else
        log_warning "Audit completed with violations"
    fi
    
    exit $exit_code
}

main "$@"