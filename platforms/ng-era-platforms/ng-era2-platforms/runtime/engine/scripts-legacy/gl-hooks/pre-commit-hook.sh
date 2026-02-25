#!/bin/bash
# =============================================================================
# GL Pre-Commit Hook - Governance Layer Validation
# =============================================================================
# Purpose: Execute GL validation before allowing commits
# =============================================================================

set -e

echo "🔍 GL Pre-Commit Validation Started..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Skipping GL validation."
    echo "⚠️  Warning: Commits without GL validation may violate governance standards."
    exit 0
fi

# Get the repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Check if GL validation scripts exist
if [ ! -d "scripts/gl" ]; then
    echo "⚠️  GL validation scripts not found. Skipping validation."
    exit 0
fi

# Run semantic validation
echo "📋 Running GL Semantic Validation..."
if [ -f "scripts/gl/validate-semantics.py" ]; then
    python3 scripts/gl/validate-semantics.py || {
        echo "❌ GL Semantic Validation Failed!"
        echo ""
        echo "Please fix the following issues before committing:"
        echo "  1. Ensure all artifacts map to GL layers"
        echo "  2. Verify semantic URNs are valid"
        echo "  3. Check parent-child relationships"
        echo ""
        echo "To bypass this check (not recommended): git commit --no-verify"
        exit 1
    }
else
    echo "⚠️  Semantic validation script not found. Skipping."
fi

# Run quantum validation
echo "🔬 Running GL Quantum Validation..."
if [ -f "scripts/gl/quantum-validate.py" ]; then
    python3 scripts/gl/quantum-validate.py || {
        echo "❌ GL Quantum Validation Failed!"
        echo ""
        echo "Please fix the following issues before committing:"
        echo "  1. Check consistency validation"
        echo "  2. Verify reversibility validation"
        echo "  3. Confirm reproducibility validation"
        echo "  4. Ensure provability validation"
        echo ""
        echo "To bypass this check (not recommended): git commit --no-verify"
        exit 1
    }
else
    echo "⚠️  Quantum validation script not found. Skipping."
fi

# Check for GL prefix naming compliance
echo "📝 Checking GL Artifact Naming Compliance..."
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(yaml|yml)$' || true)

if [ -n "$STAGED_FILES" ]; then
    for file in $STAGED_FILES; do
        if [[ $file == gl/* ]]; then
            echo "  ✓ Validating $file"
            # Check if file follows GL structure
            if [[ $file =~ ^gl/[0-9]{2}-[a-z]+/ ]]; then
                echo "    ✅ GL structure compliant"
            else
                echo "    ⚠️  Warning: File may not follow GL structure"
            fi
        fi
    done
fi

echo ""
echo "✅ All GL validations passed!"
echo "🚀 Proceeding with commit..."