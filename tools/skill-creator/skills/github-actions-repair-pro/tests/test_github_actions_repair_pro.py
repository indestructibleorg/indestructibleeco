"""Tests for github-actions-repair-pro skill."""

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


def test_governance_block():
    manifest = json.loads(MANIFEST_PATH.read_text())
    gov = manifest["governance"]
    assert gov["owner"], "Governance must have owner"
    assert len(gov["approval_chain"]) >= 1, "Governance must have approval_chain"
    assert gov["lifecycle_policy"] in ["active", "deprecated", "sunset", "archived"]


def test_metadata_governance_identity():
    manifest = json.loads(MANIFEST_PATH.read_text())
    meta = manifest["metadata"]
    assert meta["unique_id"], "Metadata must have unique_id"
    assert meta["uri"].startswith("indestructibleeco://"), "URI must use indestructibleeco:// scheme"
    assert meta["urn"].startswith("urn:indestructibleeco:"), "URN must use urn:indestructibleeco: scheme"
    assert meta["schema_version"] == "1.0.0"
    assert meta["generated_by"] == "skill-creator-v1"


def test_action_scripts_exist():
    actions_dir = SKILL_DIR / "actions"
    assert actions_dir.is_dir(), "actions/ directory must exist"
    expected = ["understand.sh", "retrieve-workflow.sh", "retrieve-dockerfile.sh",
                "integrate.sh", "monitor.sh"]
    for script in expected:
        assert (actions_dir / script).exists(), f"Missing action script: {script}"


def test_schemas_exist():
    schemas_dir = SKILL_DIR / "schemas"
    assert schemas_dir.is_dir(), "schemas/ directory must exist"
    for schema in ["input.schema.json", "output.schema.json"]:
        path = schemas_dir / schema
        assert path.exists(), f"Missing schema: {schema}"
        data = json.loads(path.read_text())
        assert data.get("$schema"), f"Schema {schema} missing $schema field"