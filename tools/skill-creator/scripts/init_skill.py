#!/usr/bin/env python3
"""
Skill Initializer — Creates a new skill from template within IndestructibleEco.

Usage:
    init_skill.py <skill-name>

Skills are created at <repo-root>/tools/skill-creator/skills/<skill-name>/
"""

import sys
import uuid
import json
from pathlib import Path
from datetime import datetime, timezone

SKILLS_BASE_PATH = Path(__file__).resolve().parent.parent / "skills"

VALID_CATEGORIES = [
    "ci-cd-repair", "code-generation", "code-analysis",
    "deployment", "monitoring", "security", "testing",
]


def uuid_v1() -> str:
    return str(uuid.uuid1())


def build_uri(skill_id: str) -> str:
    return f"indestructibleeco://skills/{skill_id}"


def build_urn(skill_id: str, uid: str) -> str:
    return f"urn:indestructibleeco:skills:{skill_id}:{uid}"


def generate_manifest(skill_name: str) -> dict:
    uid = uuid_v1()
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": skill_name,
        "name": skill_name.replace("-", " ").title(),
        "version": "0.1.0",
        "description": f"[TODO] Describe what {skill_name} does and when to use it.",
        "category": "ci-cd-repair",
        "triggers": [
            {
                "type": "manual",
                "config": {
                    "description": f"Manually trigger {skill_name}"
                }
            }
        ],
        "actions": [
            {
                "id": "analyze",
                "name": "Analyze",
                "type": "shell",
                "config": {
                    "command": "echo 'TODO: implement analyze'",
                    "timeout_seconds": 30
                },
                "depends_on": [],
                "retry": {"max_attempts": 1, "backoff_ms": 1000}
            },
            {
                "id": "repair",
                "name": "Repair",
                "type": "shell",
                "config": {
                    "command": "echo 'TODO: implement repair'",
                    "timeout_seconds": 60
                },
                "depends_on": ["analyze"],
                "retry": {"max_attempts": 2, "backoff_ms": 2000}
            },
            {
                "id": "verify",
                "name": "Verify",
                "type": "validate",
                "config": {
                    "rules": ["TODO: define verification rules"],
                    "fail_on_warning": True
                },
                "depends_on": ["repair"],
                "retry": {"max_attempts": 1, "backoff_ms": 1000}
            }
        ],
        "inputs": [
            {
                "name": "repository",
                "type": "string",
                "required": True,
                "description": "Target repository (owner/repo)"
            }
        ],
        "outputs": [
            {
                "name": "result",
                "type": "string",
                "required": True,
                "description": "Execution result summary"
            }
        ],
        "governance": {
            "owner": "platform-team",
            "approval_chain": ["platform-team"],
            "compliance_tags": ["automation", "internal"],
            "lifecycle_policy": "active"
        },
        "metadata": {
            "unique_id": uid,
            "uri": build_uri(skill_name),
            "urn": build_urn(skill_name, uid),
            "schema_version": "1.0.0",
            "target_system": "github-actions",
            "generated_by": "skill-creator-v1",
            "created_at": now,
            "updated_at": now
        }
    }


def init_skill(skill_name: str) -> Path | None:
    if not skill_name or not all(c in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in skill_name):
        print(f"✗ Invalid skill name: '{skill_name}' — must be kebab-case [a-z0-9-]")
        return None
    if skill_name.startswith("-") or skill_name.endswith("-") or "--" in skill_name:
        print(f"✗ Invalid skill name: '{skill_name}' — no leading/trailing/consecutive hyphens")
        return None
    if len(skill_name) > 64:
        print(f"✗ Skill name too long ({len(skill_name)} chars, max 64)")
        return None

    skill_dir = SKILLS_BASE_PATH / skill_name
    if skill_dir.exists():
        print(f"✗ Skill directory already exists: {skill_dir}")
        return None

    skill_dir.mkdir(parents=True, exist_ok=False)

    # skill.json
    manifest = generate_manifest(skill_name)
    (skill_dir / "skill.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # actions/
    actions_dir = skill_dir / "actions"
    actions_dir.mkdir()
    for action_id in ["analyze", "repair", "validate"]:
        script = actions_dir / f"{action_id}.sh"
        script.write_text(f"#!/usr/bin/env bash\nset -euo pipefail\necho &quot;TODO: implement {action_id} for {skill_name}&quot;\n")
        script.chmod(0o755)

    # schemas/
    schemas_dir = skill_dir / "schemas"
    schemas_dir.mkdir()
    for schema_name in ["input", "output"]:
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": f"{skill_name} {schema_name}",
            "type": "object",
            "properties": {},
        }
        (schemas_dir / f"{schema_name}.schema.json").write_text(json.dumps(schema, indent=2) + "\n")

    # tests/
    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / f"test_{skill_name.replace('-', '_')}.py").write_text(
        f'"""Tests for {skill_name}."""\n\n\ndef test_placeholder():\n    assert True, "TODO: implement tests for {skill_name}"\n'
    )

    print(f"✓ Skill '{skill_name}' initialized at {skill_dir}")
    print(f"  manifest: {skill_dir / 'skill.json'}")
    print(f"  actions:  {actions_dir}")
    print(f"  schemas:  {schemas_dir}")
    print(f"  tests:    {tests_dir}")
    return skill_dir


def main():
    if len(sys.argv) != 2:
        print("Usage: init_skill.py <skill-name>")
        print(f"\nSkills are created at {SKILLS_BASE_PATH}/<skill-name>/")
        sys.exit(1)

    skill_name = sys.argv[1].strip()
    result = init_skill(skill_name)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()