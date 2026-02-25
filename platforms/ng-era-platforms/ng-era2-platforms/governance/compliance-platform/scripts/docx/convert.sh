#!/bin/bash

# @GL-governed
# @GL-layer: GL10-29
# @GL-semantic: docx-conversion-script
# @GL-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

set -euo pipefail

# Default values
SOURCE_FILES="${SOURCE_FILES:-docs/**/*.md}"
OUTPUT_DIR="${OUTPUT_DIR:-artifacts/modules}"
ARTIFACT_TYPE="${ARTIFACT_TYPE:-all}"
FORMAT="${FORMAT:-nested}"
VALIDATE="${VALIDATE:-true}"
UPLOAD="${UPLOAD:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    local deps=("python3" "pip" "jq" "yq")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Missing dependency: $dep"
            exit 1
        fi
    done
    
    # Check Python packages
    local python_deps=("pandoc" "python-docx" "markdown" "pyyaml" "jsonschema")
    for dep in "${python_deps[@]}"; do
        if ! python3 -c "import $dep" 2>/dev/null; then
            log_warn "Python package not installed: $dep"
            log_info "Installing dependencies..."
            pip install -q -r .config/requirements-docx.txt
        fi
    done
}

# Convert documents to artifacts
convert_documents() {
    log_info "Starting document conversion..."
    log_info "Source files: $SOURCE_FILES"
    log_info "Output directory: $OUTPUT_DIR"
    log_info "Artifact type: $ARTIFACT_TYPE"
    log_info "Format: $FORMAT"
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    # Run Python conversion script
    python3 scripts/docx/convert.py \
        --source "$SOURCE_FILES" \
        --output "$OUTPUT_DIR" \
        --type "$ARTIFACT_TYPE" \
        --format "$FORMAT"
}

# Validate artifacts
validate_artifacts() {
    if [ "$VALIDATE" != "true" ]; then
        log_warn "Validation skipped"
        return 0
    fi
    
    log_info "Validating artifacts..."
    
    # Validate YAML files
    find "$OUTPUT_DIR" -name "*.yaml" -o -name "*.yml" | while read -r file; do
        if ! yq eval '.' "$file" > /dev/null 2>&1; then
            log_error "Invalid YAML: $file"
            exit 1
        fi
    done
    
    # Validate JSON files
    find "$OUTPUT_DIR" -name "*.json" | while read -r file; do
        if ! jq empty "$file" > /dev/null 2>&1; then
            log_error "Invalid JSON: $file"
            exit 1
        fi
    done
    
    log_info "✅ All artifacts validated successfully"
}

# Generate report
generate_report() {
    local report_file="artifacts/reports/docx/conversion-report-$(date +%Y%m%d-%H%M%S).json"
    mkdir -p "$(dirname "$report_file")"
    
    # Collect statistics
    local yaml_count=$(find "$OUTPUT_DIR" -name "*.yaml" -o -name "*.yml" | wc -l)
    local json_count=$(find "$OUTPUT_DIR" -name "*.json" | wc -l)
    local md_count=$(find "$OUTPUT_DIR" -name "*.md" | wc -l)
    local py_count=$(find "$OUTPUT_DIR" -name "*.py" | wc -l)
    local total=$((yaml_count + json_count + md_count + py_count))
    
    # Generate report
    jq -n \
        --arg yaml_count "$yaml_count" \
        --arg json_count "$json_count" \
        --arg md_count "$md_count" \
        --arg py_count "$py_count" \
        --arg total "$total" \
        --arg source "$SOURCE_FILES" \
        --arg output "$OUTPUT_DIR" \
        --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        '{
            timestamp: $timestamp,
            source: $source,
            output: $output,
            statistics: {
                yaml: ($yaml_count | tonumber),
                json: ($json_count | tonumber),
                markdown: ($md_count | tonumber),
                python: ($py_count | tonumber),
                total: ($total | tonumber)
            }
        }' > "$report_file"
    
    log_info "Report generated: $report_file"
    echo "$total" > artifacts-count.txt
}

# Main function
main() {
    log_info "Docx to Artifact Conversion Script"
    log_info "=================================="
    
    check_dependencies
    convert_documents
    
    if [ "$VALIDATE" == "true" ]; then
        validate_artifacts
    fi
    
    generate_report
    
    log_info "✅ Conversion completed successfully"
}

# Run main function
main "$@"