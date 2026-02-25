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
# Module Organization - MachineNativeOps

This directory contains the modular architecture implementation for the MachineNativeOps platform. Each module represents a logical grouping of functionality with clear boundaries, dependencies, and interfaces.

## Module Structure

```
controlplane/baseline/modules/
├── 01-core/                    # Core Engine & Infrastructure (L1-L2)
├── 02-intelligence/            # Intelligence Engine & Multi-Agent (L2-L3)
├── 03-governance/              # Governance System & Policy Enforcement (L3-L4)
├── 04-autonomous/              # Autonomous Systems Framework (L4-L5)
├── 05-observability/           # Observability & Monitoring System (L4-L5)
├── 06-security/                # Security & Supply Chain Governance (Global Layer)
├── REGISTRY.yaml               # Central module registry
├── module-manifest.schema.json # JSON Schema for module manifests
└── README.md                   # This file
```

## Module Descriptions

### 01-core (L1-L2)
**Purpose:** Core Engine & Infrastructure  
**Namespace:** `mno-core`  
**Status:** Active  
**Dependencies:** None

Provides foundational infrastructure including:
- Service registry and discovery
- Cognitive processor for AI-native operations
- FHS-compliant filesystem abstraction
- Basic automation primitives

### 02-intelligence (L2-L3)
**Purpose:** Intelligence Engine & Multi-Agent Collaboration  
**Namespace:** `mno-intelligence`  
**Status:** Active  
**Dependencies:** 01-core

Provides AI decision-making capabilities including:
- Multi-agent orchestration
- Decision engine with reasoning
- Knowledge graph for semantic understanding
- Context management for stateful operations

### 03-governance (L3-L4)
**Purpose:** Governance System & Policy Enforcement  
**Namespace:** `mno-governance`  
**Status:** Active  
**Dependencies:** 01-core, 02-intelligence

Provides governance automation including:
- Policy evaluation and enforcement (OPA/Rego)
- Semantic validation
- Comprehensive audit logging
- Policy gates for CI/CD
- Namespace governance

### 04-autonomous (L4-L5)
**Purpose:** Autonomous Systems Framework  
**Namespace:** `mno-autonomous`  
**Status:** In Development  
**Dependencies:** 01-core, 02-intelligence, 03-governance

Provides autonomous operation capabilities including:
- Autonomous controller for L4-L5 operations
- Self-healing engine
- Edge computing controller
- Vehicle and drone control
- Unmanned island management

### 05-observability (L4-L5)
**Purpose:** Observability & Monitoring System  
**Namespace:** `mno-observability`  
**Status:** Active  
**Dependencies:** 01-core, 02-intelligence, 03-governance

Provides comprehensive monitoring including:
- Metrics collection
- Alert management
- Distributed tracing
- Log aggregation
- Anomaly detection
- Semantic health monitoring
- Auto-fix engine

### 06-security (Global Layer)
**Purpose:** Security & Supply Chain Governance  
**Namespace:** `mno-security`  
**Status:** Active  
**Dependencies:** 01-core, 03-governance, 05-observability  
**VETO Authority:** Yes

Provides security and supply chain capabilities including:
- SLSA provenance generation
- SBOM management
- Artifact signing with Cosign
- Security scanning and auditing
- Secret management
- Compliance monitoring

## Module Manifest Format

Each module has a `module-manifest.yaml` file that contains:

- **module_id**: Unique identifier (e.g., "01-core")
- **module_name**: Human-readable name
- **module_description**: Detailed description
- **autonomy_level**: Autonomy level (L1-L5 or Global Layer)
- **namespace**: Semantic namespace (e.g., "mno-core")
- **dependencies**: List of dependent modules
- **interfaces**: Public interfaces provided
- **status**: Current status (active/in-development/deprecated)
- **version**: Module version
- **components**: Components within the module
- **semantic_mappings**: Semantic concept mappings
- **metadata**: Additional metadata

## Module Registry

The `REGISTRY.yaml` file serves as the central index of all modules, including:
- Module registration and status
- Dependency graph
- Semantic namespace mappings
- Module statistics

## Autonomy Levels

- **L1**: Basic automation (single task automation)
- **L2**: Partial autonomy (multi-task coordination, simple decisions)
- **L3**: Conditional autonomy (fully automated in specific scenarios)
- **L4**: High autonomy (automated in most scenarios)
- **L5**: Full autonomy (fully automated, no human intervention)
- **Global Layer**: Cross-cutting concerns with VETO authority

## Semantic Governance

All modules participate in semantic governance through:
- Unified namespace management
- Semantic mapping tables
- Health score monitoring
- VETO authority enforcement (Global Layer)

## Usage

### Adding a New Module

1. Create a new module directory: `XX-module-name/`
2. Create a `module-manifest.yaml` following the schema
3. Register the module in `REGISTRY.yaml`
4. Update dependencies and interfaces
5. Document semantic mappings

### Validating Module Manifests

```bash
# Validate a module manifest against the schema
python3 -m jsonschema module-manifest.schema.json <module-dir>/module-manifest.yaml
```

### Querying Module Registry

```bash
# List all active modules
grep -A 1 "status: active" REGISTRY.yaml

# Get module dependencies
python3 scripts/query_registry.py --dependencies <module-id>
```

## Migration Notes

This modular structure was implemented on 2025-01-18 as part of Phase 1: Foundation Strengthening. Existing components should be migrated into appropriate modules following the semantic mappings defined in each module's manifest.

## Next Steps

- Migrate existing components into module structure
- Implement module-specific components
- Create integration tests for module interfaces
- Develop module dependency visualization
- Implement module health monitoring

## Related Documentation

- [Research Report Verification & Planning](/research_report_verification_plan.md)
- [Module Organization Task Details](/research_report_verification_plan.md#task-11-implement-module-organization-01-06-structure)
- [Architecture Documentation](/docs/architecture/)