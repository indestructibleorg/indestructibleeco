#!/bin/bash
# @GL-governed
# @GL-layer: GL90-95 (Optimization Layer)
# @GL-semantic: performance-tuning-automation
# @GL-charter-version: 5.0.0
# @GL-audit-trail: Created for GL Platform v5.0 optimization

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NAMESPACE="gl-platform"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/gl-platform-optimization}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq not found"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Optimize Prometheus configuration
optimize_prometheus() {
    log_info "Optimizing Prometheus configuration..."
    
    local report_file="$OUTPUT_DIR/prometheus-optimization-$TIMESTAMP.txt"
    
    # Check current scrape intervals
    log_info "  Analyzing scrape intervals..."
    kubectl get configmap prometheus-config -n "$NAMESPACE" -o json 2>/dev/null | \
        jq -r '.data."prometheus.yaml"' | \
        grep -o 'scrape_interval:.*' | \
        sort -u > "$report_file"
    
    # Check scrape duration
    log_info "  Analyzing scrape duration..."
    local avg_scrape_duration=$(kubectl prometheus query \
        -n "$NAMESPACE" \
        'rate(prometheus_sd_scrape_duration_seconds_sum[5m]) / rate(prometheus_sd_scrape_duration_seconds_count[5m])' \
        2>/dev/null | jq -r '.data.result[0].value[1]' || echo "N/A")
    
    echo "Average scrape duration: ${avg_scrape_duration}s" >> "$report_file"
    
    # Recommendations
    log_info "  Generating recommendations..."
    cat >> "$report_file" << EOF

=== Recommendations ===

1. Scrape Interval Optimization:
   - Current: $(grep -o 'scrape_interval:.*' "$report_file" | head -1)
   - Recommended: 30s for critical metrics, 60s for standard metrics
   - Action: Adjust scrape_interval based on metric criticality

2. Scrape Duration:
   - Current: ${avg_scrape_duration}s
   - Target: < 5s
   - Action: If > 5s, consider:
     * Reducing number of metrics scraped
     * Optimizing metric queries
     * Adding Prometheus replicas

3. Retention Policy:
   - Review data retention settings
   - Consider downsampling for older data
   - Implement remote storage for long-term retention

EOF
    
    log_success "Prometheus optimization report: $report_file"
}

# Optimize Alertmanager configuration
optimize_alertmanager() {
    log_info "Optimizing Alertmanager configuration..."
    
    local report_file="$OUTPUT_DIR/alertmanager-optimization-$TIMESTAMP.txt"
    
    # Check alert grouping
    log_info "  Analyzing alert grouping..."
    kubectl get configmap alertmanager-config -n "$NAMESPACE" -o json 2>/dev/null | \
        jq -r '.data."alertmanager.yaml"' | \
        jq '.route.group_by' > "$report_file"
    
    # Check notification latency
    log_info "  Analyzing notification latency..."
    local avg_notification_latency=$(kubectl prometheus query \
        -n "$NAMESPACE" \
        'histogram_quantile(0.99, rate(alertmanager_notification_latency_seconds_bucket[5m]))' \
        2>/dev/null | jq -r '.data.result[0].value[1]' || echo "N/A")
    
    echo "Average notification latency (p99): ${avg_notification_latency}s" >> "$report_file"
    
    # Recommendations
    log_info "  Generating recommendations..."
    cat >> "$report_file" << EOF

=== Recommendations ===

1. Alert Grouping:
   - Current: $(cat "$report_file" | head -20)
   - Optimize by: alertname, namespace, severity
   - Action: Ensure related alerts are grouped together

2. Notification Latency:
   - Current (p99): ${avg_notification_latency}s
   - Target: < 500ms
   - Action: If > 500ms, consider:
     * Optimizing webhook endpoints
     * Reducing number of receivers
     * Implementing notification queuing

3. Route Optimization:
   - Review route priorities
   - Ensure critical alerts are routed first
   - Implement inhibition rules to reduce noise

EOF
    
    log_success "Alertmanager optimization report: $report_file"
}

# Optimize Grafana dashboards
optimize_grafana() {
    log_info "Optimizing Grafana dashboards..."
    
    local report_file="$OUTPUT_DIR/grafana-optimization-$TIMESTAMP.txt"
    
    # Analyze dashboard query performance
    log_info "  Analyzing dashboard queries..."
    
    local dashboard_dir="$REPO_ROOT/observability/dashboards"
    
    if [[ -d "$dashboard_dir" ]]; then
        for dashboard in "$dashboard_dir"/*.json; do
            if [[ -f "$dashboard" ]]; then
                local dashboard_name=$(jq -r '.title' "$dashboard")
                local panel_count=$(jq '.panels | length' "$dashboard")
                local query_count=$(jq '[.panels[].targets[]] | length' "$dashboard")
                
                echo "Dashboard: $dashboard_name" >> "$report_file"
                echo "  Panels: $panel_count" >> "$report_file"
                echo "  Queries: $query_count" >> "$report_file"
                echo "" >> "$report_file"
            fi
        done
    fi
    
    # Recommendations
    log_info "  Generating recommendations..."
    cat >> "$report_file" << EOF

=== Recommendations ===

1. Dashboard Optimization:
   - Limit panels per dashboard: < 20
   - Limit queries per dashboard: < 50
   - Use variables for dynamic filtering

2. Query Optimization:
   - Use recording rules for complex queries
   - Implement query caching
   - Set appropriate refresh intervals (30s for real-time, 5m for historical)

3. Performance Tips:
   - Use range vector queries instead of instant queries where possible
   - Avoid regex queries on high-cardinality labels
   - Pre-aggregate data with recording rules

EOF
    
    log_success "Grafana optimization report: $report_file"
}

# Optimize resource utilization
optimize_resources() {
    log_info "Optimizing resource utilization..."
    
    local report_file="$OUTPUT_DIR/resource-optimization-$TIMESTAMP.txt"
    
    # Analyze CPU usage
    log_info "  Analyzing CPU usage..."
    local avg_cpu=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | \
        awk '{sum+=$2; count++} END {print sum/count}' || echo "N/A")
    
    echo "Average CPU usage: ${avg_cpu}m" >> "$report_file"
    
    # Analyze memory usage
    log_info "  Analyzing memory usage..."
    local avg_memory=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | \
        awk '{sum+=$3; count++} END {print sum/count}' || echo "N/A")
    
    echo "Average memory usage: ${avg_memory}" >> "$report_file"
    
    # Check for over-provisioned resources
    log_info "  Checking for over-provisioned resources..."
    
    kubectl get pods -n "$NAMESPACE" -o json | \
        jq -r '.items[] | "\(.metadata.name): \(.spec.containers[].resources.requests.cpu // "N/A"), \(.spec.containers[].resources.limits.cpu // "N/A")"' \
        >> "$report_file"
    
    # Recommendations
    log_info "  Generating recommendations..."
    cat >> "$report_file" << EOF

=== Recommendations ===

1. CPU Optimization:
   - Current average: ${avg_cpu}m
   - Target: 70% of requested
   - Action: Adjust requests based on actual usage
   - Use HPA for autoscaling

2. Memory Optimization:
   - Current average: ${avg_memory}
   - Target: 70% of requested
   - Action: Set appropriate memory limits
   - Monitor OOM kills

3. General Tips:
   - Use resource quotas to prevent over-provisioning
   - Implement horizontal pod autoscaling
   - Use cluster autoscaling for cluster capacity

EOF
    
    log_success "Resource optimization report: $report_file"
}

# Generate optimization summary
generate_summary() {
    log_info "Generating optimization summary..."
    
    local summary_file="$OUTPUT_DIR/optimization-summary-$TIMESTAMP.md"
    
    cat > "$summary_file" << EOF
# GL Platform Optimization Summary

**Timestamp**: $(date -Iseconds)
**Namespace**: $NAMESPACE

## Reports Generated

EOF
    
    # Add links to all reports
    for report in "$OUTPUT_DIR"/*-optimization-$TIMESTAMP.txt; do
        if [[ -f "$report" ]]; then
            local report_name=$(basename "$report")
            echo "- [$report_name]($report_name)" >> "$summary_file"
        fi
    done
    
    cat >> "$summary_file" << EOF

## Key Metrics

EOF
    
    # Extract key metrics from reports
    if [[ -f "$OUTPUT_DIR/prometheus-optimization-$TIMESTAMP.txt" ]]; then
        echo "### Prometheus" >> "$summary_file"
        grep "Average scrape duration:" "$OUTPUT_DIR/prometheus-optimization-$TIMESTAMP.txt" >> "$summary_file"
        echo "" >> "$summary_file"
    fi
    
    if [[ -f "$OUTPUT_DIR/alertmanager-optimization-$TIMESTAMP.txt" ]]; then
        echo "### Alertmanager" >> "$summary_file"
        grep "Average notification latency" "$OUTPUT_DIR/alertmanager-optimization-$TIMESTAMP.txt" >> "$summary_file"
        echo "" >> "$summary_file"
    fi
    
    if [[ -f "$OUTPUT_DIR/resource-optimization-$TIMESTAMP.txt" ]]; then
        echo "### Resources" >> "$summary_file"
        grep "Average CPU usage:" "$OUTPUT_DIR/resource-optimization-$TIMESTAMP.txt" >> "$summary_file"
        grep "Average memory usage:" "$OUTPUT_DIR/resource-optimization-$TIMESTAMP.txt" >> "$summary_file"
        echo "" >> "$summary_file"
    fi
    
    cat >> "$summary_file" << EOF

## Next Steps

1. Review all optimization reports
2. Implement recommended changes
3. Monitor impact of optimizations
4. Iterate based on results

---

**Optimization Complete**

@GL-charter-version: 5.0.0
EOF
    
    log_success "Optimization summary: $summary_file"
}

# Main execution
main() {
    log_info "Starting GL Platform Performance Optimization..."
    log_info "Output directory: $OUTPUT_DIR"
    
    check_prerequisites
    optimize_prometheus
    optimize_alertmanager
    optimize_grafana
    optimize_resources
    generate_summary
    
    log_success "GL Platform Performance Optimization completed!"
    log_info "Results saved to: $OUTPUT_DIR"
}

main "$@"