#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: validate-semantics
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL Semantic Mapping Validator
Validates semantic mapping for GL layers with actual implementation
"""
# MNGA-002: Import organization needs review
import argparse
import sys
import yaml
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
class SemanticValidationError(Exception):
    """Custom exception for semantic validation errors"""
    pass
def load_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse YAML file"""
    if not file_path.exists():
        raise SemanticValidationError(f"File not found: {file_path}")
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SemanticValidationError(f"Invalid YAML in {file_path}: {e}")
def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse JSON file"""
    if not file_path.exists():
        raise SemanticValidationError(f"File not found: {file_path}")
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise SemanticValidationError(f"Invalid JSON in {file_path}: {e}")
def validate_urn_format(urn: str) -> bool:
    """Validate URN format according to GL standard"""
    urn_pattern = r'^urn:machinenativeops:gl:[a-z0-9-]+:[a-z0-9-]+:[0-9]+\.[0-9]+\.[0-9]+$'
    return bool(re.match(urn_pattern, urn))
def validate_semantic_anchor(anchor: Dict[str, Any]) -> list:
    """Validate GL Root Semantic Anchor structure"""
    errors = []
    # Check required fields
    required_fields = ['apiVersion', 'kind', 'metadata', 'semantic_root', 'layer_hierarchy', 'validation_rules']
    for field in required_fields:
        if field not in anchor:
            errors.append(f"Missing required field in semantic anchor: {field}")
    if errors:
        return errors
    # Validate metadata
    metadata = anchor.get('metadata', {})
    if not metadata.get('version'):
        errors.append("Missing version in metadata")
    if not metadata.get('created'):
        errors.append("Missing created timestamp in metadata")
    # Validate semantic root
    semantic_root = anchor.get('semantic_root', {})
    if not semantic_root.get('urn'):
        errors.append("Missing URN in semantic_root")
    elif not validate_urn_format(semantic_root['urn']):
        errors.append(f"Invalid URN format: {semantic_root['urn']}")
    # Validate layer hierarchy
    layer_hierarchy = anchor.get('layer_hierarchy', [])
    if not layer_hierarchy:
        errors.append("Layer hierarchy is empty")
    for layer in layer_hierarchy:
        if not layer.get('id'):
            errors.append("Layer missing id")
        elif not re.match(r'^GL[0-9]{2}-[0-9]{2}$', layer['id']):
            errors.append(f"Invalid layer id format: {layer.get('id')}")
        if not layer.get('semantic_urn'):
            errors.append(f"Layer {layer.get('id')} missing semantic_urn")
        elif not validate_urn_format(layer['semantic_urn']):
            errors.append(f"Invalid semantic_urn format: {layer['semantic_urn']}")
        if not layer.get('parent_urn'):
            errors.append(f"Layer {layer.get('id')} missing parent_urn")
        elif not validate_urn_format(layer['parent_urn']):
            errors.append(f"Invalid parent_urn format: {layer['parent_urn']}")
    return errors
def validate_semantic_index(index: Dict[str, Any], expected_layer: str, anchor: Dict[str, Any]) -> list:
    """Validate semantic index for a layer"""
    errors = []
    # Check required fields
    required_fields = ['version', 'layer', 'layer_name', 'semantic_root', 'parent_root', 'artifacts']
    for field in required_fields:
        if field not in index:
            errors.append(f"Missing required field in semantic index: {field}")
    if errors:
        return errors
    # Validate layer match
    if index.get('layer') != expected_layer:
        errors.append(f"Layer mismatch: expected {expected_layer}, got {index.get('layer')}")
    # Validate semantic root
    semantic_root = index.get('semantic_root')
    if not validate_urn_format(semantic_root):
        errors.append(f"Invalid semantic_root format: {semantic_root}")
    # Validate parent root matches anchor
    parent_root = index.get('parent_root')
    anchor_root = anchor.get('semantic_root', {}).get('urn')
    if parent_root != anchor_root:
        errors.append(f"Parent root mismatch: expected {anchor_root}, got {parent_root}")
    # Validate artifacts
    artifacts = index.get('artifacts', [])
    if not artifacts:
        errors.append("No artifacts found in semantic index")
    for artifact in artifacts:
        if not artifact.get('id'):
            errors.append("Artifact missing id")
        if not artifact.get('name'):
            errors.append("Artifact missing name")
        if not artifact.get('semantic_urn'):
            errors.append(f"Artifact {artifact.get('id')} missing semantic_urn")
        elif not validate_urn_format(artifact['semantic_urn']):
            errors.append(f"Invalid artifact URN format: {artifact['semantic_urn']}")
        if not artifact.get('path'):
            errors.append(f"Artifact {artifact.get('id')} missing path")
        # Check if path exists
        artifact_path = Path(artifact['path'])
        if not artifact_path.exists():
            errors.append(f"Artifact path does not exist: {artifact['path']}")
    return errors
def validate_layer_mapping(layer_id: str, path: str, anchor: Dict[str, Any]) -> list:
    """Validate that a layer is properly mapped in the semantic anchor"""
    errors = []
    layer_hierarchy = anchor.get('layer_hierarchy', [])
    layer_found = False
    for layer in layer_hierarchy:
        if layer.get('id') == layer_id:
            layer_found = True
            # Validate sub_layers
            sub_layers = layer.get('sub_layers', [])
            layer_path = Path(path)
            if not layer_path.exists():
                errors.append(f"Layer path does not exist: {path}")
            else:
                for sub_layer in sub_layers:
                    sub_path = layer_path / sub_layer.get('path', '')
                    if not sub_path.exists():
                        errors.append(f"Sub-layer path does not exist: {sub_path}")
            break
    if not layer_found:
        errors.append(f"Layer {layer_id} not found in semantic anchor hierarchy")
    return errors
def main():
    parser = argparse.ArgumentParser(
        description='Validate GL semantic mapping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate-semantics.py --layer GL20-29 --path workspace/src/data
  python validate-semantics.py --layer GL40-49 --path workspace/src/algorithms
  python validate-semantics.py --layer GL50-59 --path workspace/src/gpu
        """
    )
    parser.add_argument('--layer', required=True, help='GL layer (e.g., GL20-29)')
    parser.add_argument('--path', required=True, help='Layer path')
    args = parser.parse_args()
    all_errors = []
    print(f"\\n{'='*60}")
    print("GL Semantic Mapping Validation")
    print(f"{'='*60}")
    print(f"Layer: {args.layer}")
    print(f"Path: {args.path}")
    print(f"{'='*60}\\n")
    try:
        # Load semantic anchor
        print("[1/4] Loading GL Root Semantic Anchor...")
        anchor_path = Path("gl/90-meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml")
        anchor = load_yaml_file(anchor_path)
        print(f"      ✅ Loaded semantic anchor from {anchor_path}")
        # Validate semantic anchor
        print("\\n[2/4] Validating GL Root Semantic Anchor structure...")
        anchor_errors = validate_semantic_anchor(anchor)
        if anchor_errors:
            print("      ❌ Semantic anchor validation failed:")
            for error in anchor_errors:
                print(f"         - {error}")
            all_errors.extend(anchor_errors)
        else:
            print("      ✅ Semantic anchor structure is valid")
        # Validate layer mapping
        print(f"\\n[3/4] Validating layer mapping for {args.layer}...")
        layer_path = Path(args.path)
        if not layer_path.exists():
            all_errors.append(f"Layer path does not exist: {args.path}")
            print(f"      ❌ Layer path does not exist: {args.path}")
        else:
            mapping_errors = validate_layer_mapping(args.layer, args.path, anchor)
            if mapping_errors:
                print("      ❌ Layer mapping validation failed:")
                for error in mapping_errors:
                    print(f"         - {error}")
                all_errors.extend(mapping_errors)
            else:
                print(f"      ✅ Layer {args.layer} is properly mapped")
        # Validate semantic index
        print("\\n[4/4] Loading and validating semantic index...")
        index_path = layer_path / "ECO-SEMANTIC-INDEX.json"
        try:
            semantic_index = load_json_file(index_path)
            print(f"      ✅ Loaded semantic index from {index_path}")
            index_errors = validate_semantic_index(semantic_index, args.layer, anchor)
            if index_errors:
                print("      ❌ Semantic index validation failed:")
                for error in index_errors:
                    print(f"         - {error}")
                all_errors.extend(index_errors)
            else:
                print(f"      ✅ Semantic index for {args.layer} is valid")
                # Display artifact summary
                artifacts = semantic_index.get('artifacts', [])
                print("\\n      📊 Artifact Summary:")
                for artifact in artifacts:
                    print(f"         - {artifact.get('name')} ({artifact.get('id')})")
                    print(f"           URN: {artifact.get('semantic_urn')}")
                    print(f"           Path: {artifact.get('path')}")
        except SemanticValidationError as e:
            print(f"      ⚠️  Semantic index not found or invalid: {e}")
            print("      This is expected for new layers")
        # Final result
        print(f"\\n{'='*60}")
        if all_errors:
            print("❌ VALIDATION FAILED")
            print(f"{'='*60}")
            print(f"\\nTotal errors: {len(all_errors)}")
            for i, error in enumerate(all_errors, 1):
                print(f"  {i}. {error}")
            sys.exit(1)
        else:
            print("✅ VALIDATION PASSED")
            print(f"{'='*60}")
            print(f"\\nAll semantic mappings for {args.layer} are valid.")
            sys.exit(0)
    except SemanticValidationError as e:
        print(f"\\n❌ VALIDATION ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)
if __name__ == "__main__":
    main()