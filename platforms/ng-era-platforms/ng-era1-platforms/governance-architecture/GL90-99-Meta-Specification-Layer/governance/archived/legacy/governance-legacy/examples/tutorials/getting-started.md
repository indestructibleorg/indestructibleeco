<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# 🚀 Getting Started with MachineNativeOps Naming Governance

## Quick Start Guide

### Prerequisites
- Kubernetes 1.24+
- kubectl configured
- Helm 3.8+
- Python 3.9+ (for local development)

### Installation

#### Option 1: Quick Install (Recommended)
```bash
cd governance/quantum-naming-v4.0.0/scripts/
chmod +x QUICK_INSTALL.sh
./QUICK_INSTALL.sh
```

#### Option 2: Manual Install
```bash
# Install v1.0.0 Foundation
cd governance/naming-governance-v1.0.0/
./test-integration.sh

# Install v1.0.0 Extended
cd ../naming-governance-v1.0.0-extended/
python automation/scripts/naming-governance-repair.py

# Install v4.0.0 Quantum
cd ../quantum-naming-v4.0.0/
kubectl apply -f deployment/quantum-deployment-manifest.yaml.txt
```

### Basic Usage

#### Generate a Name
```python
from naming_generator import NamingGenerator

generator = NamingGenerator()
name = generator.generate("prod", "app", "service", "v1.0.0")
print(name)  # Output: prod-app-service-v1.0.0
```

#### Validate a Name
```python
from naming_validator import NamingValidator

validator = NamingValidator()
result = validator.validate("prod-app-service-v1.0.0")
print(result)  # Output: {"valid": True, "errors": []}
```

#### Auto-Repair Violations
```bash
python automation/scripts/naming-governance-repair.py \
  --input violations.yaml \
  --output repaired.yaml
```

### Next Steps
1. Read the [Implementation Guide](../../naming-governance-v1.0.0/docs/guides/implementation-guide.md)
2. Explore [Best Practices](../../naming-governance-v1.0.0/docs/best-practices/naming-patterns.md)
3. Check [API Documentation](../../api/openapi.yaml)
4. Review [Security Guidelines](../../security/security-audit-report.md)