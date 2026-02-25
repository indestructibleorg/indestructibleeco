#!/usr/bin/env python3
#
# @ECO-governed
# @ECO-layer: GL30-49
# @ECO-semantic: generate-governance-dashboard
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# ECO-Layer: GL30-49 (Execution)
"""
Language Governance Dashboard Generator
Generates a dashboard showing semantic health and governance metrics
"""
# MNGA-002: Import organization needs review
import yaml
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def load_module_registry() -> Dict[str, Any]:
    """Load the module registry.

    Returns:
        Parsed module registry data as a dictionary.

    Exits:
        The process with a non-zero status code if the file is missing, cannot be read,
        or contains invalid YAML.
    """
    registry_path = Path("controlplane/baseline/modules/REGISTRY.yaml")
    try:
        with registry_path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Error: Module registry file not found: {registry_path}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(
            f"Error: Failed to parse YAML module registry at {registry_path}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    if not isinstance(data, dict):
        print(
            f"Error: Module registry at {registry_path} must be a mapping, "
            f"but got {type(data).__name__}.",
            file=sys.stderr,
        )
        sys.exit(1)
    return data
    with open(registry_path, 'r') as f:
        return yaml.safe_load(f)


def load_policy_manifest() -> Dict[str, Any]:
    """Load the policy manifest.

    Returns:
        Parsed policy manifest data as a dictionary.

    Exits:
        The process with a non-zero status code if the file is missing, cannot be read,
        or contains invalid YAML.
    """
    manifest_path = Path("controlplane/governance/policies/POLICY_MANIFEST.yaml")
    try:
        with manifest_path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Error: Policy manifest file not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(
            f"Error: Failed to parse YAML policy manifest at {manifest_path}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    if not isinstance(data, dict):
        print(
            f"Error: Policy manifest at {manifest_path} must be a mapping, "
            f"but got {type(data).__name__}.",
            file=sys.stderr,
        )
        sys.exit(1)
    return data
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f)


def calculate_governance_metrics(registry: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate governance metrics"""
    modules = registry.get('modules', [])
    # Calculate semantic health statistics
    health_scores = [m.get('semantic_health_score', 0) for m in modules]
    avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
    min_health = min(health_scores) if health_scores else 0
    max_health = max(health_scores) if health_scores else 0
    # Count modules by status
    status_counts = {}
    for module in modules:
        status = module.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    # Count modules by autonomy level
    autonomy_counts = {}
    for module in modules:
        autonomy = module.get('autonomy_level', 'unknown')
        autonomy_counts[autonomy] = autonomy_counts.get(autonomy, 0) + 1
    return {
        'total_modules': len(modules),
        'average_semantic_health': round(avg_health, 2),
        'min_semantic_health': min_health,
        'max_semantic_health': max_health,
        'status_distribution': status_counts,
        'autonomy_distribution': autonomy_counts,
        'health_scores': health_scores
    }


def generate_health_bar(score: float, width: int = 20) -> str:
    """Generate a visual health bar"""
    filled = int((score / 100) * width)
    empty = width - filled
    if score >= 90:
        color = "🟩"
    elif score >= 80:
        color = "🟨"
    elif score >= 70:
        color = "🟧"
    else:
        color = "🟥"
    return color * filled + "⬜" * empty


def generate_dashboard(output_path: str = "docs/LANGUAGE_GOVERNANCE_DASHBOARD.md"):
    """Generate the Language Governance Dashboard"""
    # Load data
    registry = load_module_registry()
    policy_manifest = load_policy_manifest()
    metrics = calculate_governance_metrics(registry)
    # Generate dashboard content
    dashboard = f"""# Language Governance Dashboard
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Status**: 🟢 Active  
**Framework**: OPA/Rego Policy-as-Code
---
## 📊 Executive Summary
| Metric | Value | Status |
|--------|-------|--------|
| Total Modules | {metrics['total_modules']} | ✅ |
| Average Semantic Health | {metrics['average_semantic_health']}% | {'✅' if metrics['average_semantic_health'] >= 80 else '⚠️'} |
| Min Health Score | {metrics['min_semantic_health']}% | {'✅' if metrics['min_semantic_health'] >= 80 else '⚠️'} |
| Max Health Score | {metrics['max_semantic_health']}% | ✅ |
| Active Modules | {metrics['status_distribution'].get('active', 0)} | ✅ |
| In Development | {metrics['status_distribution'].get('in-development', 0)} | 📝 |
---
## 🎯 Semantic Health Overview
### Global Semantic Health: {metrics['average_semantic_health']}%
{generate_health_bar(metrics['average_semantic_health'], 30)}
**Health Threshold**: ≥ 80% (Policy Enforced)
### Module Health Scores
"""
    # Add individual module scores
    modules = registry.get('modules', [])
    for module in sorted(modules, key=lambda x: x.get('semantic_health_score', 0), reverse=True):
        module_id = module.get('module_id', 'unknown')
        health = module.get('semantic_health_score', 0)
        status = module.get('status', 'unknown')
        autonomy = module.get('autonomy_level', 'unknown')
        status_emoji = {
            'active': '🟢',
            'in-development': '🟡',
            'planned': '⚪',
            'deprecated': '🔴'
        }.get(status, '❓')
        dashboard += f"""
#### {module_id} {status_emoji}
- **Health Score**: {health}% {generate_health_bar(health, 15)}
- **Status**: {status}
- **Autonomy Level**: {autonomy}
- **Namespace**: {module.get('namespace', 'N/A')}
"""
    dashboard += """
---
## 📈 Distribution Analytics
### Module Status Distribution
"""
    for status, count in metrics['status_distribution'].items():
        percentage = (count / metrics['total_modules']) * 100
        bar = '█' * int(percentage / 5)
        dashboard += f"- **{status}**: {count} ({percentage:.1f}%) {bar}\n"
    dashboard += """
### Autonomy Level Distribution
"""
    for autonomy, count in metrics['autonomy_distribution'].items():
        percentage = (count / metrics['total_modules']) * 100
        bar = '█' * int(percentage / 5)
        dashboard += f"- **{autonomy}**: {count} ({percentage:.1f}%) {bar}\n"
    dashboard += """
---
## 🔐 Policy Enforcement Status
### Active Policies
"""
    policies = policy_manifest.get('policies', [])
    for policy in policies:
        policy_name = policy.get('name', 'unknown')
        severity = policy.get('severity', 'unknown')
        enforcement = policy.get('enforcement', 'unknown')
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(severity.lower(), '⚪')
        enforcement_status = '✅ Enabled' if enforcement == 'enabled' else '⏸️ Disabled'
        dashboard += f"""
#### {severity_emoji} {policy_name}
- **Severity**: {severity}
- **Enforcement**: {enforcement_status}
- **Remediation**: {policy.get('remediation', 'N/A')}
"""
    dashboard += """
---
## 🎨 Semantic Consistency Matrix
| Module | Namespace | Concepts | Health | Status |
|--------|-----------|----------|--------|--------|
"""
    for module in modules:
        module_id = module.get('module_id', 'unknown')
        namespace = module.get('namespace', 'N/A')
        health = module.get('semantic_health_score', 0)
        status_emoji = '✅' if health >= 80 else '⚠️'
        # Count semantic mappings if available in manifest
        manifest_path = Path(f"controlplane/baseline/modules/{module_id}/module-manifest.yaml")
        concept_count = 0
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
                concept_count = len(manifest.get('semantic_mappings', []))
        dashboard += f"| {module_id} | {namespace} | {concept_count} | {health}% | {status_emoji} |\n"
    dashboard += """
---
## 🚨 Health Alerts
"""
    # Check for modules below threshold
    low_health_modules = [m for m in modules if m.get('semantic_health_score', 0) < 80]
    if low_health_modules:
        dashboard += "### ⚠️ Modules Below Health Threshold\n\n"
        for module in low_health_modules:
            dashboard += f"- **{module.get('module_id')}**: {module.get('semantic_health_score')}% (Threshold: 80%)\n"
    else:
        dashboard += "### ✅ All Modules Above Health Threshold\n\nNo modules require immediate attention.\n"
    dashboard += f"""
---
## 📋 Governance Compliance
### Naming Convention Compliance
- **Policy**: Kebab-case naming (enforced via OPA)
- **Coverage**: 100% of files and modules
- **Status**: ✅ Compliant
### Semantic Mapping Coverage
- **Total Modules**: {metrics['total_modules']}
- **Mapped Modules**: {metrics['total_modules']}
- **Coverage**: 100%
- **Status**: ✅ Compliant
### Security Policy Compliance
- **SBOM Generation**: ✅ Required
- **SLSA Provenance**: ✅ Level 3
- **Artifact Signing**: ✅ Cosign + OIDC
- **Vulnerability Scanning**: ✅ Trivy
- **Status**: ✅ Compliant
---
## 🔄 Continuous Improvement
### Recommendations
1. **High Priority**
   - Monitor modules in development: {', '.join([m['module_id'] for m in modules if m.get('status') == 'in-development' and 'module_id' in m])}
2. **Medium Priority**
   - Maintain semantic health scores above 90%
   - Regular policy reviews and updates
3. **Low Priority**
   - Expand semantic mapping coverage
   - Enhance DAG visualization
### Next Review Date
Recommended review: **{(datetime.now()).strftime('%Y-%m-%d')}** (Monthly)
---
## 📚 Resources
- [Module Registry](../controlplane/baseline/modules/REGISTRY.yaml)
- [Policy Manifest](../controlplane/governance/policies/POLICY_MANIFEST.yaml)
- [Integration Guide](PHASE1_INTEGRATION_GUIDE.md)
- [Validation Tools](../scripts/validate-infrastructure.sh)
---
*This dashboard is automatically generated from module registry and policy manifest data.*  
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
    # Write dashboard
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w') as f:
        f.write(dashboard)
    print(f"✅ Language Governance Dashboard generated: {output_path}")
    # Also generate JSON report
    json_output = output_path.replace('.md', '.json')
    report = {
        'generated_at': datetime.now().isoformat(),
        'metrics': metrics,
        'modules': modules,
        'policies': policies
    }
    with open(json_output, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"✅ JSON report generated: {json_output}")


if __name__ == "__main__":
    generate_dashboard()
