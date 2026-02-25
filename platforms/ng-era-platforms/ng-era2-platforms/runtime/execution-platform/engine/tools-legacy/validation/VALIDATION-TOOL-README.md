# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# Artifact Validation Tool - Complete Implementation

✅ **PRODUCTION READY** - Full 5-level validation pipeline implemented

## Quick Reference

**File**: `tools/validation/validate-artifact.py`  
**Version**: 2.0.0  
**Status**: 🟢 Production Ready  
**Purpose**: Complete 5-level validation pipeline for bi-directional governance closure

## Overview

The Artifact Validation Tool implements a comprehensive 5-level validation pipeline that ensures artifacts comply with the Machine Native Ops governance framework, including bi-directional governance closure.

## Features

### ✅ Level 1: Structural Validation
- YAML syntax validation
- Schema compliance checking
- Required fields validation (metadata, spec, status)
- Data type validation for all fields
- Nested structure validation
- apiVersion format checking

### ✅ Level 2: Schema Validation
- Semantic root integration from `root/.root.semantic-root.yaml`
- Concept traceability to semantic root
- Semantic consistency checking across concepts
- Definition completeness validation
- Concept extension validation

### ✅ Level 3: Dependency Validation
- DAG (Directed Acyclic Graph) structure validation
- Circular dependency detection using DFS-based cycle detection
- Version compatibility checking
- Self-dependency detection
- Dependency health monitoring

### ✅ Level 4: Governance Validation
- Naming convention enforcement from semantic root
- Documentation completeness checking
- Policy compliance validation
- Attestation bundle requirements validation
- Namespace and version format validation

### ✅ Level 5: Closure Validation
- Dependency closure validation
- Semantic closure validation
- Governance closure validation
- Bi-directional reconciliation checks
- Overall closure status aggregation

## Usage

### Basic Usage

```bash
# Validate a single artifact
python3 tools/validation/validate-artifact.py --level all artifact.yaml

# Validate multiple artifacts
python3 tools/validation/validate-artifact.py --level all artifact1.yaml artifact2.yaml
```

### Validation Levels

```bash
# Run only structural validation
python3 tools/validation/validate-artifact.py --level structural artifact.yaml

# Run only semantic validation
python3 tools/validation/validate-artifact.py --level semantic artifact.yaml

# Run only dependency validation
python3 tools/validation/validate-artifact.py --level dependency artifact.yaml

# Run only governance validation
python3 tools/validation/validate-artifact.py --level governance artifact.yaml

# Run only closure validation
python3 tools/validation/validate-artifact.py --level closure artifact.yaml

# Run all validation levels (default)
python3 tools/validation/validate-artifact.py --level all artifact.yaml
```

### Strict Mode

Treat warnings as failures:

```bash
python3 tools/validation/validate-artifact.py --level all --strict artifact.yaml
```

### Attestation Generation

Generate a validation attestation bundle:

```bash
python3 tools/validation/validate-artifact.py --level all \
  --attestation attestation.yaml \
  artifact.yaml
```

The attestation bundle includes:
- All validation results by level
- Governance compliance status
- Provenance information
- Trust chain metadata
- Closure status

## Integration Points

### Semantic Root
- **File**: `root/.root.semantic-root.yaml`
- **Purpose**: Provides base concepts, naming conventions, and validation rules
- **Loaded**: Automatically at validation start

### Gates Map
- **File**: `root/.root.gates.map.yaml`
- **Purpose**: Defines gate mechanisms and approval workflows
- **Loaded**: Automatically at validation start

### FileX Template
- **File**: `design/FileX-standard-template-v1.yaml`
- **Purpose**: Template structure for artifacts
- **Used**: As reference for structural validation

## CI/CD Integration

Used in `.github/workflows/gate-lock-attest.yaml`:

```yaml
- name: Structural Validation Gate
  run: |
    validate-artifact --level structural \
      --attestation structural-attestation.yaml \
      changed-files.txt

- name: Closure Validation Gate
  run: |
    validate-artifact --level closure \
      --attestation closure-attestation.yaml \
      changed-files.txt
```

## Exit Codes

- **0**: Validation passed (all checks successful)
- **1**: Validation failed (errors detected or strict mode with warnings)

## Performance

- **Target**: < 5 seconds for typical artifacts
- **Measured**: ~0.1-0.5 seconds for single artifact validation
- **Optimized**: Minimal file I/O, efficient DAG algorithms

## Error Messages

The tool provides clear, actionable error messages with:
- File path
- Line number (when applicable)
- Specific validation that failed
- Expected value or pattern
- Recommendation for fixing

Example:
```
❌ Validation FAILED: 2 error(s), 1 warning(s)
   - [governance] Artifact name 'Invalid-Name' violates naming convention
     File: /path/to/artifact.yaml
     Pattern: ^[a-z][a-z0-9-]*$
     Examples: ['user-service', 'governance-engine']
```

## Development

### Testing

```bash
# Test on semantic root
python3 tools/validation/validate-artifact.py --level all \
  root/.root.semantic-root.yaml

# Test on gates map
python3 tools/validation/validate-artifact.py --level all \
  root/.root.gates.map.yaml

# Test with invalid artifact
python3 tools/validation/validate-artifact.py --level all \
  test/invalid-artifact.yaml
```

### Extending

To add new validation checks:

1. Add validation logic to the appropriate `_validate_*` method
2. Create `ValidationResult` objects with appropriate status
3. Update attestation generation if needed
4. Document the new validation in this README

## Troubleshooting

### "Semantic root not loaded"
- Ensure `root/.root.semantic-root.yaml` exists
- Check file is valid YAML

### "No semantic root reference found"
- Add `machinenativeops.io/semantic-root` annotation to artifact metadata
- Warning only, does not fail validation

### "Circular dependency detected"
- Review artifact dependencies
- Use the cycle path in error details to identify the loop
- Break the cycle by removing or restructuring dependencies

## Version History

### 2.0.0 (2026-01-10)
- ✅ Complete implementation of all 5 validation levels
- ✅ Semantic root integration
- ✅ Circular dependency detection
- ✅ Naming convention enforcement
- ✅ Comprehensive attestation generation
- ✅ Detailed error messages with file paths and line numbers
- ✅ Performance optimization (< 5s for typical artifacts)

### 1.0.0-stub (2025-01-10)
- Basic YAML syntax validation
- CLI interface scaffolding
- Stub implementations for all levels

## References

- **Technical Debt Analysis**: `TECHNICAL_DEBT_ANALYSIS.md`
- **Semantic Closure Rules**: `design/semantic-closure-rules.md`
- **Semantic Root**: `root/.root.semantic-root.yaml`
- **Gates Map**: `root/.root.gates.map.yaml`
- **FileX Template**: `design/FileX-standard-template-v1.yaml`
