<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# GL (Governance Layers) Architecture

**Version**: 1.0.0  
**Status**: Semantically Stabilized  
**Location**: `governance/gl-architecture/`

## Overview

GL (Governance Layers) Architecture provides a unified, semantically stable governance layer framework for organizing and managing all governance dimensions across the MachineNativeOps project.

## Core Files

### Definition Files
- **`GL_LAYERS.yaml`** - Complete GL architecture definition with all 7 layers
- **`GL_QUICKREF.md`** - Quick reference guide for GL layers
- **`GL_MAPPING.csv`** - Machine-readable GL layer mapping table
- **`GL_SEMANTIC_STABILIZATION.yaml`** - Semantic stabilization status and verification

### Extension Points
- **`gl-extended/`** - Layer-specific implementations and definitions
- **`templates/`** - GL layer templates for new projects
- **`integrations/`** - Integration configurations for various systems

## GL Layer Structure

| Layer | Range | Description |
|-------|-------|-------------|
| GL00-09 | Strategic Layer | Vision, architecture, decision, risk, compliance, security |
| GL10-29 | Operational Layer | Policy, culture, metrics, improvement, quality |
| GL30-49 | Execution Layer | Schemas, templates, contracts, automation, tools |
| GL50-59 | Observability Layer | Monitoring, alerting, insights |
| GL60-80 | Advanced/Feedback Layer | AI, contracts, audit, optimization, feedback |
| GL81-83 | Extended Layer | Auto-comment, stakeholder, integration |
| GL90-99 | Meta-Specification Layer | Naming conventions, meta-governance |

## Usage

### Reference from Other Locations

Create symbolic links or reference configurations:

```bash
# Example: Link from workspace
ln -s ../../governance/gl-architecture/GL_LAYERS.yaml workspace/config/gl-layers.yaml

# Example: Reference in YAML
gl_architecture:
  reference: "governance/gl-architecture/GL_LAYERS.yaml"
  version: "1.0.0"
```

### Integration with Governance Manifest

Update `governance-manifest.yaml`:

```yaml
gl_layers:
  reference: "governance/gl-architecture/GL_LAYERS.yaml"
  quickref: "governance/gl-architecture/GL_QUICKREF.md"
  mapping: "governance/gl-architecture/GL_MAPPING.csv"
  stabilization: "governance/gl-architecture/GL_SEMANTIC_STABILIZATION.yaml"
```

## Distribution Strategy

### Central Management
All GL architecture definitions are maintained in this directory (`governance/gl-architecture/`).

### Extension to Subdirectories
Each subdirectory can:
1. Reference the central GL definitions
2. Create layer-specific implementations in `gl-extended/`
3. Use templates from `templates/` directory

### Example Directory Structure

```
governance/gl-architecture/
├── README.md                          # This file
├── GL_LAYERS.yaml                     # Core GL definitions
├── GL_QUICKREF.md                     # Quick reference
├── GL_MAPPING.csv                     # Mapping table
├── GL_SEMANTIC_STABILIZATION.yaml     # Stabilization status
├── gl-extended/                       # Layer implementations
│   ├── GL00-09-strategic/            # Strategic layer
│   ├── GL10-29-operational/          # Operational layer
│   ├── GL30-49-execution/            # Execution layer
│   ├── GL50-59-observability/        # Observability layer
│   ├── GL60-80-advanced/             # Advanced/Feedback layer
│   ├── GL81-83-extended/             # Extended layer
│   └── GL90-99-meta/                 # Meta-specification layer
├── templates/                         # GL templates
│   ├── layer-template.yaml           # Template for new layers
│   └── dimension-template.yaml       # Template for new dimensions
└── integrations/                      # Integration configs
    ├── workspace-integration.yaml    # Workspace integration
    ├── controlplane-integration.yaml # Controlplane integration
    └── tools-integration.yaml        # Tools integration
```

## Maintenance

### Version Control
All changes to GL architecture must:
1. Update version in relevant files
2. Document changes in semantic stabilization status
3. Maintain backward compatibility or provide migration path

### Semantic Stability
GL architecture is semantically stabilized. Any changes must:
- Not introduce conflicts or duplicates
- Maintain clear layer boundaries
- Preserve existing semantics
- Pass semantic validation checks

## References

- **Governance Manifest**: `governance-manifest.yaml`
- **Source Dimensions**: `workspace/src/governance/`
- **Consolidation Summary**: `archive/CONSOLIDATION_2026-01-18_SUMMARY.md`

---

**Created**: 2026-01-18  
**Upgraded From**: Dimension Layers  
**Semantic Stabilization**: Complete
