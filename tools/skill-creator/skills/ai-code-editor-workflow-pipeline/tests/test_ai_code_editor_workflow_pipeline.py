"""Tests for ai-code-editor-workflow-pipeline skill.

Enterprise-grade validation suite implementing:
- Module-scoped fixtures with typed error handling
- Full JSON Schema validation (Draft 2020-12 / draft-07 compatible)
- DAG integrity: missing deps, cycle detection, 7-phase ordering
- Governance block enforcement (SLSA L3, SOC2, audit-trail)
- Metadata governance identity (URI/URN prefix, semver, generator)
- Action script existence + executable permission
- Schema property quality (descriptions, no defaults on required, unique enums, valid regex)
- Sample data validation against input/output schemas
- Cross-skill non-overlap verification
- Additional schema rules: minProperties enforcement, patternProperties count, enum min items, type consistency
"""

import json
from pathlib import Path
import re
from typing import Dict, Any, List

import pytest

try:
    from jsonschema import validate, ValidationError, Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

SKILL_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = SKILL_DIR / "skill.json"
INPUT_SCHEMA_PATH = SKILL_DIR / "schemas" / "input.schema.json"
OUTPUT_SCHEMA_PATH = SKILL_DIR / "schemas" / "output.schema.json"


# ════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════

def _load_json(path: Path, label: str) -> Dict[str, Any]:
    """Load and validate a JSON file, raising precise errors."""
    if not path.exists():
        raise FileNotFoundError(
            f"{label} does not exist at path: {path.absolute()}. "
            f"Expected file: {path.name} in {path.parent.name} directory."
        )
    try:
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise TypeError(
                f"{label} content is not a dictionary, got type: "
                f"{type(data).__name__}. Check {path.name} for invalid structure."
            )
        return data
    except json.JSONDecodeError as e:
        ctx_start = max(0, e.pos - 20)
        ctx_end = min(len(e.doc), e.pos + 20)
        raise ValueError(
            f"JSON decoding error in {path.name}: {e.msg} at line {e.lineno}, "
            f"column {e.colno}. Context: '{e.doc[ctx_start:ctx_end]}'"
        )
    except UnicodeDecodeError as e:
        raise ValueError(
            f"Unicode decoding error in {path.name}: {e.reason} at position "
            f"{e.start}-{e.end}. Ensure file is UTF-8 encoded."
        )
    except Exception as e:
        raise RuntimeError(
            f"Unexpected error reading {path.name} at {path.absolute()}: "
            f"{str(e)}. Check file permissions or corruption."
        )


@pytest.fixture(scope="module")
def manifest() -> Dict[str, Any]:
    return _load_json(MANIFEST_PATH, "Manifest file")


@pytest.fixture(scope="module")
def input_schema() -> Dict[str, Any]:
    return _load_json(INPUT_SCHEMA_PATH, "Input schema file")


@pytest.fixture(scope="module")
def output_schema() -> Dict[str, Any]:
    return _load_json(OUTPUT_SCHEMA_PATH, "Output schema file")


# ════════════════════════════════════════════════════════════════════
# Manifest existence guard
# ════════════════════════════════════════════════════════════════════

def test_manifest_exists():
    assert MANIFEST_PATH.exists(), (
        f"skill.json does not exist at {MANIFEST_PATH.absolute()}. "
        f"Create the manifest file in the skill directory."
    )


def test_manifest_valid_json(manifest):
    assert isinstance(manifest, dict), "Manifest must be a JSON object (dict)."


# ════════════════════════════════════════════════════════════════════
# Manifest structure
# ════════════════════════════════════════════════════════════════════

def test_manifest_required_fields(manifest):
    required = [
        "id", "name", "version", "description", "category",
        "triggers", "actions", "inputs", "outputs",
        "governance", "metadata"
    ]
    missing = [f for f in required if f not in manifest]
    assert not missing, (
        f"Required fields missing in manifest: {', '.join(missing)}. "
        f"Add these to skill.json at the root level."
    )


def test_manifest_id_matches_directory(manifest):
    expected = SKILL_DIR.name
    actual = manifest["id"]
    assert actual == expected, (
        f"Manifest 'id' '{actual}' does not match directory name "
        f"'{expected}'. Update 'id' in skill.json to '{expected}'."
    )


def test_manifest_category(manifest):
    expected = "code-analysis"
    actual = manifest["category"]
    assert actual == expected, (
        f"Manifest 'category' is '{actual}', but expected '{expected}'. "
        f"Update 'category' in skill.json to '{expected}'."
    )


def test_manifest_version_semver(manifest):
    version = manifest["version"]
    assert re.match(r"^\d+\.\d+\.\d+$", version), (
        f"Manifest 'version' '{version}' does not match semver pattern "
        r"^\d+\.\d+\.\d+$. Update 'version' in skill.json to a valid "
        f"semver string like '1.0.0'."
    )


def test_manifest_description_length(manifest):
    desc = manifest["description"]
    length = len(desc)
    truncated = desc[:100] + '...' if length > 100 else desc
    assert 50 < length < 500, (
        f"Manifest 'description' length {length} is not between 51 and 499 "
        f"characters. Current description: '{truncated}'. "
        f"Adjust 'description' in skill.json to meet the length requirement."
    )


# ════════════════════════════════════════════════════════════════════
# DAG integrity
# ════════════════════════════════════════════════════════════════════

def test_action_dag_no_missing_deps(manifest):
    action_ids = {a["id"] for a in manifest["actions"]}
    for action in manifest["actions"]:
        deps = action.get("depends_on", [])
        missing_deps = [dep for dep in deps if dep not in action_ids]
        assert not missing_deps, (
            f"Action '{action['id']}' has undefined dependencies: "
            f"{', '.join(missing_deps)}. Define these actions in skill.json "
            f"or remove from 'depends_on'."
        )


def test_action_dag_no_cycles(manifest):
    deps = {a["id"]: a.get("depends_on", []) for a in manifest["actions"]}
    visited: set = set()
    visiting: set = set()
    path: List[str] = []

    def _check(node: str) -> None:
        if node in visiting:
            cycle_path = ' -> '.join(path + [node])
            raise AssertionError(
                f"Circular dependency detected: {cycle_path}. "
                f"Resolve the cycle in 'depends_on' fields of skill.json."
            )
        if node in visited:
            return
        visiting.add(node)
        path.append(node)
        for dep in deps.get(node, []):
            _check(dep)
        path.pop()
        visiting.remove(node)
        visited.add(node)

    for action_id in deps:
        _check(action_id)


def test_action_dag_7_phase_structure(manifest):
    action_ids = [a["id"] for a in manifest["actions"]]
    required_phases = [
        "understand", "retrieve-code", "retrieve-knowledge",
        "analyze", "reason", "consolidate", "integrate",
        "validate", "audit"
    ]
    missing = [p for p in required_phases if p not in action_ids]
    assert not missing, (
        f"Required phases missing in actions array: {', '.join(missing)}. "
        f"Add missing actions with these IDs to skill.json."
    )


def test_action_dag_dependency_order(manifest):
    deps = {a["id"]: a.get("depends_on", []) for a in manifest["actions"]}
    order_checks = [
        (deps["understand"], [],
         "understand has unexpected dependencies, but should have none. "
         "Check 'depends_on' for 'understand' in skill.json."),
        ("understand", deps["retrieve-code"],
         "retrieve-code is missing dependency on understand. "
         "Add 'understand' to 'depends_on' in skill.json."),
        ("understand", deps["retrieve-knowledge"],
         "retrieve-knowledge is missing dependency on understand. "
         "Add 'understand' to 'depends_on' in skill.json."),
        (["retrieve-code", "retrieve-knowledge"], deps["analyze"],
         "analyze is missing dependencies on retrieve phases. "
         "Add 'retrieve-code' and 'retrieve-knowledge' to 'depends_on' in skill.json."),
        ("analyze", deps["reason"],
         "reason is missing dependency on analyze. "
         "Add 'analyze' to 'depends_on' in skill.json."),
        ("reason", deps["consolidate"],
         "consolidate is missing dependency on reason. "
         "Add 'reason' to 'depends_on' in skill.json."),
        ("consolidate", deps["integrate"],
         "integrate is missing dependency on consolidate. "
         "Add 'consolidate' to 'depends_on' in skill.json."),
        ("integrate", deps["validate"],
         "validate is missing dependency on integrate. "
         "Add 'integrate' to 'depends_on' in skill.json."),
        ("validate", deps["audit"],
         "audit is missing dependency on validate. "
         "Add 'validate' to 'depends_on' in skill.json.")
    ]
    for expected, actual, msg in order_checks:
        if isinstance(expected, list):
            missing = [exp for exp in expected if exp not in actual]
            assert not missing, (
                f"{msg} Missing dependencies: {', '.join(missing)}. "
                f"Current 'depends_on': {actual}. "
                f"Update the corresponding action in skill.json."
            )
        else:
            assert expected in actual, (
                f"{msg} Missing dependency '{expected}'. "
                f"Current 'depends_on': {actual}. "
                f"Update the corresponding action in skill.json."
            )


# ════════════════════════════════════════════════════════════════════
# Governance
# ════════════════════════════════════════════════════════════════════

def test_governance_block(manifest):
    gov = manifest["governance"]
    assert gov.get("owner"), (
        "Governance 'owner' field is missing or empty. "
        "Provide a valid owner in skill.json under 'governance'."
    )
    chain = gov.get("approval_chain", [])
    assert len(chain) >= 2, (
        f"Approval chain has only {len(chain)} entries, but requires at least 2. "
        f"Current chain: {chain}. "
        f"Update 'approval_chain' in skill.json with additional approvers."
    )
    required_tags = ["slsa-l3", "audit-trail", "soc2-compliant"]
    tags = gov.get("compliance_tags", [])
    missing_tags = [t for t in required_tags if t not in tags]
    assert not missing_tags, (
        f"Missing compliance tags in 'compliance_tags': {', '.join(missing_tags)}. "
        f"Current tags: {tags}. "
        f"Add missing tags to skill.json under 'governance'."
    )
    allowed_lifecycle = ["active", "maintenance", "deprecated"]
    lp = gov.get("lifecycle_policy", "")
    assert lp in allowed_lifecycle, (
        f"Invalid 'lifecycle_policy' '{lp}' in governance. "
        f"Must be one of {', '.join(allowed_lifecycle)}. "
        f"Update 'lifecycle_policy' in skill.json under 'governance'."
    )


# ════════════════════════════════════════════════════════════════════
# Metadata governance identity
# ════════════════════════════════════════════════════════════════════

def test_metadata_governance_identity(manifest):
    meta = manifest["metadata"]
    assert meta.get("unique_id"), (
        "Metadata 'unique_id' field is missing or empty. "
        "Provide a valid UUID in skill.json under 'metadata'."
    )
    uri = meta.get("uri", "")
    assert uri.startswith("indestructibleeco://"), (
        f"Metadata 'uri' '{uri}' does not start with 'indestructibleeco://'. "
        f"Update 'uri' in skill.json under 'metadata'."
    )
    urn = meta.get("urn", "")
    assert urn.startswith("urn:indestructibleeco:"), (
        f"Metadata 'urn' '{urn}' does not start with 'urn:indestructibleeco:'. "
        f"Update 'urn' in skill.json under 'metadata'."
    )
    sv = meta.get("schema_version", "")
    assert re.match(r"^\d+\.\d+\.\d+$", sv), (
        f"Metadata 'schema_version' '{sv}' is not in valid semver format. "
        f"Update 'schema_version' in skill.json under 'metadata'."
    )
    gb = meta.get("generated_by", "")
    assert gb.startswith("skill-creator-v"), (
        f"Metadata 'generated_by' '{gb}' does not start with 'skill-creator-v'. "
        f"Update 'generated_by' in skill.json under 'metadata'."
    )


# ════════════════════════════════════════════════════════════════════
# Action scripts — existence + executable
# ════════════════════════════════════════════════════════════════════

def test_action_scripts_exist_and_executable():
    actions_dir = SKILL_DIR / "actions"
    assert actions_dir.is_dir(), (
        f"Actions directory does not exist at {actions_dir.absolute()}. "
        f"Create the directory and add required scripts."
    )
    expected = [
        "understand.sh", "retrieve-code.sh", "retrieve-knowledge.sh",
        "analyze.sh", "reason.sh", "consolidate.sh",
        "integrate.sh", "validate.sh", "audit.sh"
    ]
    for script in expected:
        path = actions_dir / script
        assert path.exists(), (
            f"Action script does not exist at {path.absolute()}. "
            f"Expected script: {script}. Add the missing script."
        )
        mode = path.stat().st_mode
        assert mode & 0o100, (
            f"Action script at {path.absolute()} is not executable. "
            f"Run 'chmod +x {script}' in the actions directory."
        )


# ════════════════════════════════════════════════════════════════════
# Schema structural validation
# ════════════════════════════════════════════════════════════════════

def test_schemas_exist_and_valid(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        assert "$schema" in schema, (
            f"{name}.schema.json missing '$schema' field. "
            f"Add a '$schema' declaration."
        )
        assert schema.get("type") == "object", (
            f"{name}.schema.json 'type' must be 'object', "
            f"got '{schema.get('type')}'."
        )
        props = schema.get("properties", {})
        assert len(props) >= 1, (
            f"{name}.schema.json must have at least 1 property, "
            f"got {len(props)}."
        )


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_schemas_jsonschema_validation(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        try:
            Draft7Validator.check_schema(schema)
        except Exception as e:
            raise AssertionError(
                f"{name}.schema.json is not a valid JSON Schema: {str(e)}"
            )


def test_schema_properties_have_descriptions(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        properties = schema.get("properties", {})
        for prop_name, prop in properties.items():
            if isinstance(prop, dict):
                assert "description" in prop, (
                    f"Property '{prop_name}' in {name} schema is missing "
                    f"'description'. Add a 'description' field to all "
                    f"properties in {name}.schema.json."
                )


def test_schema_required_fields_have_no_defaults(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        for req in required:
            prop = properties.get(req, {})
            if isinstance(prop, dict):
                assert "default" not in prop, (
                    f"Required field '{req}' in {name} schema has a 'default' "
                    f"value, which is invalid for required fields. "
                    f"Remove 'default' from '{req}' in {name}.schema.json."
                )


def test_schema_enum_values_are_unique(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        properties = schema.get("properties", {})
        for prop_name, prop in properties.items():
            if isinstance(prop, dict) and "enum" in prop:
                enum_values = prop["enum"]
                assert len(set(enum_values)) == len(enum_values), (
                    f"Enum values in property '{prop_name}' of {name} schema "
                    f"have duplicates: {enum_values}. Ensure all enum values "
                    f"are unique in {name}.schema.json."
                )


def test_schema_pattern_properties_valid_regex(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        pattern_props = schema.get("patternProperties", {})
        for pattern in pattern_props:
            try:
                re.compile(pattern)
            except re.error as e:
                raise AssertionError(
                    f"Invalid regex pattern '{pattern}' in patternProperties "
                    f"of {name} schema: {str(e)}. Update the pattern in "
                    f"{name}.schema.json to a valid regex."
                )


def test_schema_string_properties_have_constraints(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        required = set(schema.get("required", []))
        properties = schema.get("properties", {})
        for prop_name, prop in properties.items():
            if isinstance(prop, dict) and prop.get("type") == "string":
                if prop_name in required:
                    has_constraint = (
                        "minLength" in prop or
                        "pattern" in prop or
                        "enum" in prop or
                        "format" in prop or
                        "const" in prop
                    )
                    assert has_constraint, (
                        f"Required string property '{prop_name}' in {name} "
                        f"schema has no validation constraint (minLength, "
                        f"pattern, enum, format, or const). Add at least one "
                        f"constraint to {name}.schema.json."
                    )


def test_schema_min_properties_enforcement(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        min_props = schema.get("minProperties", 0)
        assert min_props >= 1, (
            f"{name}.schema.json 'minProperties' {min_props} is less than 1. "
            f"Update 'minProperties' in {name}.schema.json to at least 1."
        )


def test_schema_pattern_properties_count(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        if "patternProperties" in schema:
            pattern_props = schema["patternProperties"]
            assert len(pattern_props) >= 1, (
                f"{name}.schema.json has empty 'patternProperties'. "
                f"Either add patterns or remove the empty object from "
                f"{name}.schema.json."
            )


def test_schema_enum_min_items(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        properties = schema.get("properties", {})
        for prop_name, prop in properties.items():
            if isinstance(prop, dict) and "enum" in prop:
                enum = prop["enum"]
                assert len(enum) >= 2, (
                    f"Enum in property '{prop_name}' of {name} schema has "
                    f"less than 2 items ({len(enum)}). Add more items to the "
                    f"enum in {name}.schema.json."
                )


def test_schema_type_consistency(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        properties = schema.get("properties", {})
        for prop_name, prop in properties.items():
            if isinstance(prop, dict) and "type" in prop:
                prop_type = prop["type"]
                if prop_type == "object":
                    assert "properties" in prop or "patternProperties" in prop, (
                        f"Object property '{prop_name}' in {name} schema lacks "
                        f"'properties' or 'patternProperties'. Add sub-structure "
                        f"to {name}.schema.json."
                    )
                elif prop_type == "array":
                    assert "items" in prop, (
                        f"Array property '{prop_name}' in {name} schema lacks "
                        f"'items' definition. Add 'items' to {name}.schema.json."
                    )


def test_schema_array_items_have_type(input_schema, output_schema):
    for schema, name in [(input_schema, "input"), (output_schema, "output")]:
        properties = schema.get("properties", {})
        for prop_name, prop in properties.items():
            if isinstance(prop, dict) and prop.get("type") == "array":
                items = prop.get("items", {})
                if isinstance(items, dict):
                    assert "type" in items, (
                        f"Array property '{prop_name}' in {name} schema has "
                        f"'items' without 'type'. Add 'type' to 'items' in "
                        f"{name}.schema.json."
                    )


# ════════════════════════════════════════════════════════════════════
# Sample data validation against schemas
# ════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_sample_input_validates_against_schema(input_schema):
    sample = {
        "repository": "indestructibleorg/indestructibleeco",
        "target_path": "backend/ai/src/app.py",
        "problem_description": "Memory leak in inference routing causing OOM kills under sustained load",
        "auth_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test",
        "branch": "main",
        "compliance_mode": "enterprise",
        "memory_hub_url": "http://memory-hub.indestructibleeco.svc.cluster.local:8080",
        "commit_message": "fix: resolve memory leak in inference router"
    }
    try:
        validate(instance=sample, schema=input_schema)
    except ValidationError as e:
        path_str = '/'.join(map(str, e.path)) if e.path else 'root'
        raise AssertionError(
            f"Sample input failed validation at path '{path_str}': "
            f"{e.message}. Schema: {input_schema.get('title', 'input')}."
        )


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_sample_output_validates_against_schema(output_schema):
    sample = {
        "root_cause": "Unbounded cache growth in vllm_adapter inference pool",
        "fix_applied": True,
        "verification_status": "success",
        "audit_trail": {
            "trace_id": "a1b2c3d4-e5f6-1a2b-8c3d-4e5f6a7b8c9d",
            "timestamp": "2026-02-18T21:00:00Z",
            "actor": "ai-code-editor-workflow-pipeline",
            "commit_sha": "abc123def456",
            "compliance_tags": ["slsa-l3", "audit-trail", "soc2-compliant"],
            "governance_stamp": {
                "uri": "indestructibleeco://skills/ai-code-editor-workflow-pipeline",
                "urn": "urn:indestructibleeco:skills:ai-code-editor-workflow-pipeline:a1b2c3d4",
                "schema_version": "1.0.0",
                "generated_by": "skill-creator-v1"
            }
        }
    }
    try:
        validate(instance=sample, schema=output_schema)
    except ValidationError as e:
        path_str = '/'.join(map(str, e.path)) if e.path else 'root'
        raise AssertionError(
            f"Sample output failed validation at path '{path_str}': "
            f"{e.message}. Schema: {output_schema.get('title', 'output')}."
        )


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_invalid_input_rejected_by_schema(input_schema):
    invalid_sample = {
        "repository": "not a valid repo format!!!",
        "target_path": "",
        "problem_description": "",
        "auth_token": ""
    }
    errors = list(Draft7Validator(input_schema).iter_errors(invalid_sample))
    assert len(errors) > 0, (
        "Input schema did not reject an invalid sample. "
        "Schema constraints may be too loose."
    )


# ════════════════════════════════════════════════════════════════════
# References
# ════════════════════════════════════════════════════════════════════

def test_references_exist():
    refs_dir = SKILL_DIR / "references"
    assert refs_dir.is_dir(), (
        f"References directory does not exist at {refs_dir.absolute()}."
    )
    expected = [
        "workflow_definitions.md",
        "enterprise_standards.md",
        "autoecops_integration.md"
    ]
    for ref in expected:
        assert (refs_dir / ref).exists(), (
            f"Missing reference: {ref}. "
            f"Add the file to the references directory."
        )


# ════════════════════════════════════════════════════════════════════
# Cross-skill non-overlap
# ════════════════════════════════════════════════════════════════════

def test_no_overlap_with_github_actions_repair_pro(manifest):
    sibling = SKILL_DIR.parent / "github-actions-repair-pro" / "skill.json"
    if not sibling.exists():
        pytest.skip("Sibling skill not found, skipping overlap check.")
    try:
        with sibling.open('r', encoding='utf-8') as f:
            other = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"JSON decoding error in sibling skill.json "
            f"(github-actions-repair-pro): {e.msg} at line {e.lineno}, "
            f"column {e.colno}."
        )
    assert other["category"] != manifest["category"], (
        f"Category overlap with sibling skill (github-actions-repair-pro): "
        f"both are '{manifest['category']}'. Use unique categories."
    )
    assert other["id"] != manifest["id"], (
        f"ID overlap with sibling skill (github-actions-repair-pro): "
        f"both are '{manifest['id']}'. Use unique IDs."
    )


# ════════════════════════════════════════════════════════════════════
# Manifest-to-schema cross-reference
# ════════════════════════════════════════════════════════════════════

def test_manifest_inputs_match_schema(manifest, input_schema):
    schema_props = set(input_schema.get("properties", {}).keys())
    manifest_inputs = {inp["name"] for inp in manifest.get("inputs", [])}
    missing = manifest_inputs - schema_props
    assert not missing, (
        f"Manifest inputs not found in input.schema.json properties: "
        f"{', '.join(missing)}. Add these properties to the schema."
    )


def test_manifest_outputs_match_schema(manifest, output_schema):
    schema_props = set(output_schema.get("properties", {}).keys())
    manifest_outputs = {out["name"] for out in manifest.get("outputs", [])}
    missing = manifest_outputs - schema_props
    assert not missing, (
        f"Manifest outputs not found in output.schema.json properties: "
        f"{', '.join(missing)}. Add these properties to the schema."
    )


def test_manifest_required_inputs_match_schema(manifest, input_schema):
    schema_required = set(input_schema.get("required", []))
    manifest_required = {
        inp["name"] for inp in manifest.get("inputs", [])
        if inp.get("required", False)
    }
    missing = manifest_required - schema_required
    assert not missing, (
        f"Manifest marks these inputs as required but schema does not: "
        f"{', '.join(missing)}. Update 'required' in input.schema.json."
    )


def test_manifest_required_outputs_match_schema(manifest, output_schema):
    schema_required = set(output_schema.get("required", []))
    manifest_required = {
        out["name"] for out in manifest.get("outputs", [])
        if out.get("required", False)
    }
    missing = manifest_required - schema_required
    assert not missing, (
        f"Manifest marks these outputs as required but schema does not: "
        f"{', '.join(missing)}. Update 'required' in output.schema.json."
    )