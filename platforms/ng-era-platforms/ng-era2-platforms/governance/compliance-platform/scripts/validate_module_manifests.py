#!/usr/bin/env python3
#
# @ECO-governed
# @ECO-layer: GL30-49
# @ECO-semantic: validate-module-manifests
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# ECO-Layer: GL30-49 (Execution)
"""
Module Manifest Validator
Validates module manifests against JSON schema
"""
# MNGA-002: Import organization needs review
import json
import yaml
import sys
from pathlib import Path
from jsonschema import validate, ValidationError


def main():
    # Load schema
    schema_path = Path("controlplane/baseline/modules/module-manifest.schema.json")
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"Error: Failed to parse JSON schema at {schema_path}: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error: Could not read schema file at {schema_path}: {exc}", file=sys.stderr)
        sys.exit(1)
    # Validate each module manifest
    modules_dir = Path("controlplane/baseline/modules")
    failed = False
    validated = 0
    for module_dir in sorted(modules_dir.glob("[0-9][0-9]-*")):
        if module_dir.is_dir():
            manifest_path = module_dir / "module-manifest.yaml"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    print(f"❌ {module_dir.name}: Failed to parse YAML: {exc}", file=sys.stderr)
                    failed = True
                    continue
                except OSError as exc:
                    print(f"❌ {module_dir.name}: Could not read file: {exc}", file=sys.stderr)
                    failed = True
                    continue

                try:
                    validate(instance=manifest, schema=schema)
                    print(f"✅ {module_dir.name}: Valid")
                    validated += 1
                except ValidationError as e:
                    print(f"❌ {module_dir.name}: {e.message}", file=sys.stderr)
                    failed = True

    print(f"\nValidated {validated} module manifest(s)")

    if failed:
        sys.exit(1)
    else:
        print("✅ All module manifests are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
