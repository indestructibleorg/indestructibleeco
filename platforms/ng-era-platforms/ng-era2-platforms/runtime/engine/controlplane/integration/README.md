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
# Controlplane Integration

<!-- GL Layer: GL10-29 Operational Layer -->
<!-- Purpose: Integration configurations and cross-system coordination -->

## Overview

This directory contains integration configurations for the MachineNativeOps Controlplane. It manages cross-system coordination, external integrations, and inter-module communication patterns.

## Purpose

- **Cross-System Integration**: Configuration for integrating with external systems
- **Module Coordination**: Inter-module communication and coordination configs
- **API Gateways**: Integration gateway configurations
- **Event Bridges**: Event-driven integration configurations

## Directory Structure

```
integration/
├── README.md              # This file
├── external/              # External system integrations
├── internal/              # Internal module integrations
├── gateways/              # API gateway configurations
└── events/                # Event integration configurations
```

## Integration Patterns

1. **API Integration**: RESTful and GraphQL API integrations
2. **Event-Driven**: Message queue and event bus integrations
3. **Service Mesh**: Service-to-service communication patterns
4. **Data Pipelines**: Data integration and ETL configurations

## Configuration Files

Integration configurations should follow the naming convention:
- `{system}-integration.yaml` - Main integration configuration
- `{system}-mapping.yaml` - Data mapping configurations
- `{system}-credentials.yaml` - Credential references (secrets not stored here)

## Security

- **No Secrets**: Never store credentials or secrets in this directory
- **References Only**: Use secret references that point to secure storage
- **Read-Only Runtime**: Configurations are read-only during system runtime

## Related Directories

- **Configuration**: See `controlplane/config/` for system configurations
- **Validation**: See `controlplane/validation/` for integration validation schemas
- **Registries**: See `controlplane/registries/` for module registries

## Maintenance

Integration configurations should be managed through:
1. Version control (Git)
2. CI/CD pipelines
3. Configuration management tools
