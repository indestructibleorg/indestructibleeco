# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# Controlplane Documentation

<!-- GL Layer: GL90-99 Meta-Specification Layer -->
<!-- Purpose: Governance and controlplane documentation -->

## Overview

This directory contains governance-level documentation for the MachineNativeOps Controlplane. Documentation here is focused on system-level specifications, governance policies, and architectural decisions that guide the entire taxonomy system.

## Purpose

- **Governance Documentation**: High-level policy and governance documents
- **Architectural Decisions**: ADRs (Architecture Decision Records) for controlplane
- **Specifications**: Detailed technical specifications for controlplane components
- **Reference Materials**: Reference documentation for operators and maintainers

## Directory Structure

```
documentation/
├── README.md              # This file
├── governance/            # Governance policies and frameworks
├── architecture/          # Architecture decision records
├── specifications/        # Technical specifications
└── reference/             # Reference documentation
```

## Documentation Principles

1. **Read-Only Runtime**: All documentation here is treated as read-only during system runtime
2. **Version Controlled**: All changes must go through version control
3. **GL Compliant**: All documentation follows GL layer specifications
4. **Taxonomy Aligned**: Documentation structure mirrors taxonomy classification

## Related Documentation

- **Project Documentation**: See `workspace/docs/` for project-level documentation
- **Configuration**: See `controlplane/config/` for configuration files
- **Validation**: See `controlplane/validation/` for validation schemas

## Maintenance

This directory is maintained by the MachineNativeOps governance team and should only be modified through controlled processes (CI/CD, configuration management).
