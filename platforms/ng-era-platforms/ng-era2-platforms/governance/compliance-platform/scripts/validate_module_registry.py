#!/usr/bin/env python3
#
# @ECO-governed
# @ECO-layer: GL30-49
# @ECO-semantic: validate-module-registry
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Module Registry Validator
Validates module registry structure and dependencies
"""
# MNGA-002: Import organization needs review
import yaml
import sys
from pathlib import Path


def main():
    # Load registry
    registry_path = Path("controlplane/baseline/modules/REGISTRY.yaml")
    if not registry_path.exists():
        print(f"❌ Registry file not found: {registry_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(f"Error: Failed to parse YAML registry at {registry_path}: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error: Could not read registry file at {registry_path}: {exc}", file=sys.stderr)
        sys.exit(1)
    print("📋 Module Registry Validation")
    print("=" * 50)
    if 'modules' not in registry:
        print("❌ Registry missing 'modules' section")
        sys.exit(1)

    modules = registry['modules']
    module_ids = {m['module_id'] for m in modules if 'module_id' in m}

    print(f"✅ Found {len(modules)} modules")
    # Check each module
    has_errors = False
    for module in modules:
        module_id = module.get('module_id', 'unknown')
        print(f"\n📦 Module: {module_id}")
        # Check required fields
        required_fields = ['module_id', 'status', 'autonomy_level']
        for field in required_fields:
            if field not in module:
                print(f"  ❌ Missing required field: {field}")
                has_errors = True
            else:
                print(f"  ✅ {field}: {module[field]}")
        # Validate dependencies
        if 'dependencies' in module:
            deps = module['dependencies']
            for dep in deps:
                if dep not in module_ids and dep != 'none':
                    print(f"  ⚠️  Unknown dependency: {dep}")

    print("\n" + "=" * 50)

    if has_errors:
        print("❌ Registry validation failed!")
        sys.exit(1)
    else:
        print("✅ Registry validation passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
