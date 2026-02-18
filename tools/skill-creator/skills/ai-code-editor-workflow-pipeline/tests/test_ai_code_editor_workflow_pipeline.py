"""Tests for ai-code-editor-workflow-pipeline skill."""

import json
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = SKILL_DIR / "skill.json"


def test_manifest_exists():
    assert MANIFEST_PATH.exists(), "skill.json must exist"


def test_manifest_valid_json():
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert isinstance(manifest, dict)


def test_manifest_required_fields():
    manifest = json.loads(MANIFEST_PATH.read_text())
    for field in ["id", "name", "version", "description", "category",
                   "triggers", "actions", "inputs", "outputs",
                   "governance", "metadata"]:
        assert field in manifest, f"Missing required field: {field}"


def test_manifest_id_matches_directory():
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["id"] == SKILL_DIR.name


def test_manifest_category():
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["category"] == "code-analysis"


def test_manifest_version_semver():
    manifest = json.loads(MANIFEST_PATH.read_text())
    parts = manifest["version"].split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_action_dag_no_missing_deps():
    manifest = json.loads(MANIFEST_PATH.read_text())
    action_ids = {a["id"] for a in manifest["actions"]}
    for action in manifest["actions"]:
        for dep in action.get("depends_on", []):
            assert dep in action_ids, f"Action '{action['id']}' depends on unknown '{dep}'"


def test_action_dag_no_cycles():
    manifest = json.loads(MANIFEST_PATH.read_text())
    deps = {a["id"]: a.get("depends_on", []) for a in manifest["actions"]}
    visited = set()
    visiting = set()

    def has_cycle(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in deps.get(node, []):
            if has_cycle(dep):
                return True
        visiting.discard(node)
        visited.add(node)
        return False

    for action_id in deps:
        assert not has_cycle(action_id), f"Cycle detected involving '{action_id}'"


def test_action_dag_7_phase_structure():
    """Verify the DAG implements the 7-phase remediation cycle."""
    manifest = json.loads(MANIFEST_PATH.read_text())
    action_ids = [a["id"] for a in manifest["actions"]]
    # Must have all 7 phases (retrieve split into 2, remediate split into 2)
    assert "understand" in action_ids
    assert "retrieve-code" in action_ids
    assert "retrieve-knowledge" in action_ids
    assert "analyze" in action_ids
    assert "reason" in action_ids
    assert "consolidate" in action_ids
    assert "integrate" in action_ids
    assert "validate" in action_ids
    assert "audit" in action_ids


def test_action_dag_dependency_order():
    """Verify strict ordering: understand → retrieve → analyze → reason → consolidate → integrate → validate → audit."""
    manifest = json.loads(MANIFEST_PATH.read_text())
    deps = {a["id"]: a.get("depends_on", []) for a in manifest["actions"]}

    # understand has no deps
    assert deps["understand"] == []
    # retrieve depends on understand
    assert "understand" in deps["retrieve-code"]
    assert "understand" in deps["retrieve-knowledge"]
    # analyze depends on both retrieves
    assert "retrieve-code" in deps["analyze"]
    assert "retrieve-knowledge" in deps["analyze"]
    # reason depends on analyze
    assert "analyze" in deps["reason"]
    # consolidate depends on reason
    assert "reason" in deps["consolidate"]
    # integrate depends on consolidate
    assert "consolidate" in deps["integrate"]
    # validate depends on integrate
    assert "integrate" in deps["validate"]
    # audit depends on validate
    assert "validate" in deps["audit"]


def test_governance_block():
    manifest = json.loads(MANIFEST_PATH.read_text())
    gov = manifest["governance"]
    assert gov["owner"], "Governance must have owner"
    assert len(gov["approval_chain"]) >= 1
    assert "slsa-l3" in gov["compliance_tags"]
    assert "audit-trail" in gov["compliance_tags"]
    assert gov["lifecycle_policy"] == "active"


def test_metadata_governance_identity():
    manifest = json.loads(MANIFEST_PATH.read_text())
    meta = manifest["metadata"]
    assert meta["unique_id"], "Metadata must have unique_id"
    assert meta["uri"].startswith("indestructibleeco://")
    assert meta["urn"].startswith("urn:indestructibleeco:")
    assert meta["schema_version"] == "1.0.0"
    assert meta["generated_by"] == "skill-creator-v1"


def test_action_scripts_exist():
    actions_dir = SKILL_DIR / "actions"
    assert actions_dir.is_dir()
    expected = ["understand.sh", "retrieve-code.sh", "analyze.sh", "reason.sh",
                "consolidate.sh", "integrate.sh", "validate.sh", "audit.sh"]
    for script in expected:
        assert (actions_dir / script).exists(), f"Missing action script: {script}"


def test_schemas_exist():
    schemas_dir = SKILL_DIR / "schemas"
    assert schemas_dir.is_dir()
    for schema in ["input.schema.json", "output.schema.json"]:
        path = schemas_dir / schema
        assert path.exists(), f"Missing schema: {schema}"
        data = json.loads(path.read_text())
        assert data.get("$schema"), f"Schema {schema} missing $schema field"


def test_references_exist():
    refs_dir = SKILL_DIR / "references"
    assert refs_dir.is_dir()
    expected = ["workflow_definitions.md", "enterprise_standards.md", "autoecops_integration.md"]
    for ref in expected:
        assert (refs_dir / ref).exists(), f"Missing reference: {ref}"


def test_no_overlap_with_github_actions_repair_pro():
    """Verify this skill does not overlap with github-actions-repair-pro."""
    manifest = json.loads(MANIFEST_PATH.read_text())
    # Different category
    assert manifest["category"] == "code-analysis"
    # Different ID
    assert manifest["id"] == "ai-code-editor-workflow-pipeline"
    # github-actions-repair-pro is ci-cd-repair; this is code-analysis
    sibling = SKILL_DIR.parent / "github-actions-repair-pro" / "skill.json"
    if sibling.exists():
        other = json.loads(sibling.read_text())
        assert other["category"] != manifest["category"], "Skills must have different categories"
        assert other["id"] != manifest["id"], "Skills must have different IDs"