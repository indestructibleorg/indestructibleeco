#!/bin/bash
# @GL-governed
# @GL-layer: GL90-95 (Discovery Layer)
# @GL-semantic: cluster-resource-discovery
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
NAMESPACE_FILTER="${NAMESPACE_FILTER:-gl-platform,default}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/gl-platform-discovery}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create output directory
mkdir -p "$OUTPUT_DIR"

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

# Check kubectl connectivity
check_kubectl() {
    log_info "Checking kubectl connectivity..."
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    log_success "Kubernetes cluster connection verified"
}

# Discover all namespaces
discover_namespaces() {
    log_info "Discovering namespaces..."
    local namespaces=$(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}')
    echo "$namespaces" > "$OUTPUT_DIR/namespaces_$TIMESTAMP.txt"
    log_success "Found $(echo "$namespaces" | wc -w) namespaces"
}

# Discover all resources in namespaces
discover_resources() {
    log_info "Discovering resources in namespaces..."
    
    local resource_types=(
        "pods"
        "deployments"
        "services"
        "ingresses"
        "configmaps"
        "secrets"
        "statefulsets"
        "daemonsets"
        "jobs"
        "cronjobs"
        "persistentvolumeclaims"
        "serviceaccounts"
        "roles"
        "rolebindings"
        "clusterroles"
        "clusterrolebindings"
    )
    
    for resource_type in "${resource_types[@]}"; do
        log_info "  Discovering $resource_type..."
        
        local output_file="$OUTPUT_DIR/${resource_type}_$TIMESTAMP.json"
        
        if kubectl get "$resource_type" -A -o json > "$output_file" 2>&1; then
            local count=$(jq '.items | length' "$output_file")
            log_success "  Found $count $resource_type"
        else
            log_warning "  Failed to discover $resource_type (may not exist)"
            rm -f "$output_file"
        fi
    done
}

# Analyze naming conventions
analyze_naming_conventions() {
    log_info "Analyzing naming conventions..."
    
    local naming_report="$OUTPUT_DIR/naming-analysis_$TIMESTAMP.json"
    local total_resources=0
    local compliant_resources=0
    local non_compliant_resources=0
    local violations=()
    
    # Read all resource files
    for resource_file in "$OUTPUT_DIR"/*_$TIMESTAMP.json; do
        if [[ -f "$resource_file" ]]; then
            local resource_type=$(basename "$resource_file" | cut -d'_' -f1)
            
            while IFS= read -r resource; do
                total_resources=$((total_resources + 1))
                
                local name=$(echo "$resource" | jq -r '.metadata.name // empty')
                local namespace=$(echo "$resource" | jq -r '.metadata.namespace // "cluster"')
                local kind=$(echo "$resource" | jq -r '.kind')
                
                # Check naming pattern
                local pattern="^(dev|staging|prod)-[a-z0-9-]+-"
                
                if [[ "$name" =~ $pattern ]]; then
                    compliant_resources=$((compliant_resources + 1))
                else
                    non_compliant_resources=$((non_compliant_resources + 1))
                    violations+=("{&quot;type&quot;:&quot;$kind&quot;,&quot;name&quot;:&quot;$name&quot;,&quot;namespace&quot;:&quot;$namespace&quot;}")
                fi
            done < <(jq -c '.items[]' "$resource_file" 2>/dev/null || true)
        fi
    done
    
    # Generate report
    cat > "$naming_report" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "total_resources": $total_resources,
  "compliant_resources": $compliant_resources,
  "non_compliant_resources": $non_compliant_resources,
  "compliance_rate": $(echo "scale=2; $compliant_resources * 100 / $total_resources" | bc),
  "violations": [
    $(IFS=,; echo "${violations[*]}")
  ]
}
EOF
    
    log_success "Naming analysis complete"
    log_info "  Compliance Rate: $(jq '.compliance_rate' "$naming_report")%"
    log_info "  Non-compliant Resources: $non_compliant_resources"
}

# Check security policies
check_security_policies() {
    log_info "Checking security policies..."
    
    local security_report="$OUTPUT_DIR/security-analysis_$TIMESTAMP.json"
    local security_issues=()
    
    # Check for PodSecurityPolicies
    local psp_count=$(kubectl get podsecuritypolicies -o json 2>/dev/null | jq '.items | length' || echo "0")
    
    # Check for NetworkPolicies
    local np_count=$(kubectl get networkpolicies -A -o json 2>/dev/null | jq '.items | length' || echo "0")
    
    # Check for ResourceQuotas
    local rq_count=$(kubectl get resourcequotas -A -o json 2>/dev/null | jq '.items | length' || echo "0")
    
    # Check for LimitRanges
    local lr_count=$(kubectl get limitranges -A -o json 2>/dev/null | jq '.items | length' || echo "0")
    
    # Check for secrets in clear text
    while IFS= read -r secret; do
        local name=$(echo "$secret" | jq -r '.metadata.name')
        local namespace=$(echo "$secret" | jq -r '.metadata.namespace')
        local type=$(echo "$secret" | jq -r '.type')
        
        if [[ "$type" == "Opaque" ]]; then
            while IFS= read -r key; do
                local value=$(echo "$secret" | jq -r ".data.&quot;$key&quot; | @base64d")
                if [[ "$value" =~ (password|secret|token|key) ]] && [[ ! "$value" =~ ^base64: ]]; then
                    security_issues+=("{&quot;type&quot;:&quot;clear-text-secret&quot;,&quot;name&quot;:&quot;$name&quot;,&quot;namespace&quot;:&quot;$namespace&quot;,&quot;key&quot;:&quot;$key&quot;}")
                fi
            done < <(echo "$secret" | jq -r '.data | keys[]' 2>/dev/null || true)
        fi
    done < <(jq -c '.items[]' "$OUTPUT_DIR/secrets_$TIMESTAMP.json" 2>/dev/null || true)
    
    # Generate report
    cat > "$security_report" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "pod_security_policies": $psp_count,
  "network_policies": $np_count,
  "resource_quotas": $rq_count,
  "limit_ranges": $lr_count,
  "security_issues": [
    $(IFS=,; echo "${security_issues[*]}")
  ]
}
EOF
    
    log_success "Security analysis complete"
}

# Generate summary report
generate_summary() {
    log_info "Generating summary report..."
    
    local summary_report="$OUTPUT_DIR/summary_$TIMESTAMP.md"
    
    cat > "$summary_report" << EOF
# GL Platform Discovery Summary

**Timestamp**: $(date -Iseconds)
**Cluster**: $(kubectl config current-context)

## Resource Counts

EOF
    
    # Add resource counts
    for resource_file in "$OUTPUT_DIR"/*_$TIMESTAMP.json; do
        if [[ -f "$resource_file" ]]; then
            local resource_type=$(basename "$resource_file" | cut -d'_' -f1)
            local count=$(jq '.items | length' "$resource_file" 2>/dev/null || echo "0")
            echo "- **$resource_type**: $count" >> "$summary_report"
        fi
    done
    
    cat >> "$summary_report" << EOF

## Naming Compliance

EOF
    
    if [[ -f "$OUTPUT_DIR/naming-analysis_$TIMESTAMP.json" ]]; then
        local compliance_rate=$(jq '.compliance_rate' "$OUTPUT_DIR/naming-analysis_$TIMESTAMP.json")
        local non_compliant=$(jq '.non_compliant_resources' "$OUTPUT_DIR/naming-analysis_$TIMESTAMP.json")
        
        echo "- **Compliance Rate**: ${compliance_rate}%" >> "$summary_report"
        echo "- **Non-compliant Resources**: $non_compliant" >> "$summary_report"
    fi
    
    cat >> "$summary_report" << EOF

## Security Analysis

EOF
    
    if [[ -f "$OUTPUT_DIR/security-analysis_$TIMESTAMP.json" ]]; then
        local security_issues=$(jq '.security_issues | length' "$OUTPUT_DIR/security-analysis_$TIMESTAMP.json")
        local network_policies=$(jq '.network_policies' "$OUTPUT_DIR/security-analysis_$TIMESTAMP.json")
        
        echo "- **Security Issues**: $security_issues" >> "$summary_report"
        echo "- **Network Policies**: $network_policies" >> "$summary_report"
    fi
    
    log_success "Summary report generated: $summary_report"
}

# Main execution
main() {
    log_info "Starting GL Platform Cluster Discovery..."
    log_info "Output directory: $OUTPUT_DIR"
    
    check_kubectl
    discover_namespaces
    discover_resources
    analyze_naming_conventions
    check_security_policies
    generate_summary
    
    log_success "Discovery complete!"
    log_info "Results saved to: $OUTPUT_DIR"
}

main "$@"