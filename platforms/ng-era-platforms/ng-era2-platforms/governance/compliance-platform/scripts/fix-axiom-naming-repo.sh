#!/bin/bash
# AXIOM to GL Runtime Naming Refactor Script (Repository-wide)
# Fixes all AXIOM naming to comply with GL Runtime Platform standards

# @GL-governed
# @GL-layer: GL10-29 Operational
# @GL-semantic: axiom-naming-refactor-repo-script
# @GL-charter-version: 1.0.0

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$ROOT_DIR/.axiom-refactor-backup-repo"
LOG_DIR="$ROOT_DIR/logs"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="$LOG_DIR/axiom-refactor-repo-$TIMESTAMP.log"

# Create directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

echo "========================================" | tee -a "$LOG_FILE"
echo "AXIOM to GL Runtime Naming Refactor (Repository-wide)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Root Directory: $ROOT_DIR" | tee -a "$LOG_FILE"
echo "Backup Directory: $BACKUP_DIR" | tee -a "$LOG_FILE"
echo "Log File: $LOG_FILE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Find all files to process
echo "Finding files with AXIOM references..." | tee -a "$LOG_FILE"
FILES=$(find "$ROOT_DIR" -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.js" -o -name "*.py" -o -name "*.sh" \) \
    ! -path "*/.git/*" \
    ! -path "*/node_modules/*" \
    ! -path "*/.axiom-refactor-backup*/*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/.pyc" \
    ! -path "*/package-lock.json" \
    ! -path "*/yarn.lock" \
    ! -path "*/logs/*" \
    -exec grep -l "axiom" {} \; 2>/dev/null || true)

FILE_COUNT=$(echo "$FILES" | grep -c "^" || echo 0)
echo "Found $FILE_COUNT files with AXIOM references" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Process each file
REPLACED_COUNT=0
for FILE in $FILES; do
    if [ -z "$FILE" ]; then
        continue
    fi
    
    REL_PATH="${FILE#$ROOT_DIR/}"
    echo "Processing: $REL_PATH" | tee -a "$LOG_FILE"
    
    # Create backup
    BACKUP_PATH="$BACKUP_DIR/$REL_PATH"
    mkdir -p "$(dirname "$BACKUP_PATH")"
    cp "$FILE" "$BACKUP_PATH"
    
    # Apply replacements
    ORIGINAL_CONTENT=$(cat "$FILE")
    
    # Use sed for replacements
    sed -i \
        -e 's|apiVersion: axiom\.io/v\([0-9]\+\)|apiVersion: gl-runtime.io/v\1|g' \
        -e 's|namespace: gl-runtime-verification|namespace: gl-runtime-verification|g' \
        -e 's|namespace: gl-runtime-system|namespace: gl-runtime-system|g' \
        -e 's|gl-hft-quantum|gl-hft-quantum|g' \
        -e 's|gl-inference-engine|gl-inference-engine|g' \
        -e 's|gl-quantum-coordinator|gl-quantum-coordinator|g' \
        -e 's|policy_id: GL-RUNTIME-GOV-|policy_id: GL-RUNTIME-GOV-|g' \
        -e 's|GLRuntimeGlobalBaseline|GLRuntimeGlobalBaseline|g' \
        -e 's|GLRuntimeNamespaceConfig|GLRuntimeNamespaceConfig|g' \
        -e 's|/etc/gl-runtime|/etc/gl-runtime|g' \
        -e 's|/opt/gl-runtime|/opt/gl-runtime|g' \
        -e 's|/var/lib/gl-runtime|/var/lib/gl-runtime|g' \
        -e 's|/var/log/gl-runtime|/var/log/gl-runtime|g' \
        -e 's|axiom\.io/|gl-runtime.io/|g' \
        -e 's|registry\.axiom\.io|registry.gl-runtime.io|g' \
        "$FILE"
    
    # Check if file changed
    NEW_CONTENT=$(cat "$FILE")
    if [ "$ORIGINAL_CONTENT" != "$NEW_CONTENT" ]; then
        echo "  -> Changes applied" | tee -a "$LOG_FILE"
        REPLACED_COUNT=$((REPLACED_COUNT + 1))
    else
        echo "  -> No changes needed" | tee -a "$LOG_FILE"
        # Restore from backup if no changes
        cp "$BACKUP_PATH" "$FILE"
    fi
done

echo "========================================" | tee -a "$LOG_FILE"
echo "REFACTOR SUMMARY" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Total files processed: $FILE_COUNT" | tee -a "$LOG_FILE"
echo "Files with changes: $REPLACED_COUNT" | tee -a "$LOG_FILE"
echo "Backup directory: $BACKUP_DIR" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

echo ""
echo "Refactoring completed!"
echo "Backup files saved to: $BACKUP_DIR"
echo "To restore backups, run: cp -r $BACKUP_DIR/* $ROOT_DIR/"