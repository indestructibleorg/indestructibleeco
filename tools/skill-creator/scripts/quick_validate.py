#!/usr/bin/env python3
"""
Skill Validator — Validates skill.json manifests against IndestructibleEco governance spec.

Usage:
    quick_validate.py <skill-name>
    quick_validate.py <absolute-path-to-skill>

Skills are expected at <repo>/tools/skill-creator/skills/<skill-name>/
"""

import sys
import re
import json
from pathlib import Path

SKILLS_BASE_PATH = Path(__file__).resolve().parent.parent / "skills"

VALID_CATEGORIES = [
    "ci-cd-repair", "code-generation", "code-analysis",
    "deployment", "monitoring", "security", "testing",
]
VALID_TRIGGER_TYPES = ["webhook", "schedule", "event", "manual"]
VALID_ACTION_TYPES = ["shell", "api", "transform", "validate", "deploy"]
VALID_PARAM_TYPES = ["string", "number", "boolean", "object", "array"]
VALID_LIFECYCLE = ["active", "deprecated", "sunset", "archived"]

UUID_V1_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-1[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
URI_PATTERN = re.compile(r"^indestructibleeco://")
URN_PATTERN = re.compile(r"^urn:indestructibleeco:")


def resolve_skill_path(skill_path_or_name: str) -> Path:
    path = Path(skill_path_or_name)
    if path.is_absolute():
        return path
    return SKILLS_BASE_PATH / skill_path_or_name


def validate_skill(skill_path_or_name: str) -> tuple[bool, list[str], list[str]]:
    """Validate a skill directory. Returns (valid, errors, warnings)."""
    skill_path = resolve_skill_path(skill_path_or_name)
    errors: list[str] = []
    warnings: list[str] = []

    # --- skill.json existence ---
    manifest_path = skill_path / "skill.json"
    if not manifest_path.exists():
        return False, ["skill.json not found"], []

    # --- JSON parse ---
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"], []

    if not isinstance(manifest, dict):
        return False, ["skill.json root must be an object"], []

    # --- Required top-level fields ---
    for field in ["id", "name", "version", "description", "category", "triggers", "actions", "inputs", "outputs"]:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    # --- ID format ---
    sid = manifest.get("id", "")
    if sid:
        if not re.match(r"^[a-z0-9-]+$", sid):
            errors.append(f"ID must be kebab-case: '{sid}'")
        if sid.startswith("-") or sid.endswith("-") or "--" in sid:
            errors.append(f"ID has invalid hyphens: '{sid}'")
        if len(sid) > 64:
            errors.append(f"ID too long ({len(sid)} chars, max 64)")
        # ID must match directory name
        if skill_path.name != sid:
            errors.append(f"ID '{sid}' does not match directory name '{skill_path.name}'")

    # --- Version ---
    ver = manifest.get("version", "")
    if ver and not re.match(r"^\d+\.\d+\.\d+", ver):
        errors.append(f"Version must be semver: '{ver}'")

    # --- Category ---
    cat = manifest.get("category", "")
    if cat and cat not in VALID_CATEGORIES:
        errors.append(f"Invalid category: '{cat}'. Must be one of: {', '.join(VALID_CATEGORIES)}")

    # --- Triggers ---
    triggers = manifest.get("triggers", [])
    if isinstance(triggers, list):
        for i, t in enumerate(triggers):
            if not isinstance(t, dict):
                errors.append(f"Trigger[{i}]: must be an object")
                continue
            tt = t.get("type", "")
            if not tt:
                errors.append(f"Trigger[{i}]: missing type")
            elif tt not in VALID_TRIGGER_TYPES:
                errors.append(f"Trigger[{i}]: invalid type '{tt}'")

    # --- Actions — DAG validation ---
    actions = manifest.get("actions", [])
    if isinstance(actions, list):
        action_ids: set[str] = set()
        for i, a in enumerate(actions):
            if not isinstance(a, dict):
                errors.append(f"Action[{i}]: must be an object")
                continue
            aid = a.get("id", "")
            if not aid:
                errors.append(f"Action[{i}]: missing id")
            elif aid in action_ids:
                errors.append(f"Action[{i}]: duplicate id '{aid}'")
            else:
                action_ids.add(aid)

            at = a.get("type", "")
            if not at:
                errors.append(f"Action[{i}]: missing type")
            elif at not in VALID_ACTION_TYPES:
                errors.append(f"Action[{i}]: invalid type '{at}'")

            deps = a.get("depends_on", [])
            if isinstance(deps, list):
                all_action_ids = {x.get("id", "") for x in actions if isinstance(x, dict)}
                for dep in deps:
                    if dep not in all_action_ids:
                        errors.append(f"Action '{aid}': dependency '{dep}' not found in actions")

            # Retry validation
            retry = a.get("retry")
            if retry and isinstance(retry, dict):
                ma = retry.get("max_attempts")
                if ma is not None and (not isinstance(ma, int) or ma < 0):
                    errors.append(f"Action '{aid}': retry.max_attempts must be non-negative integer")

    # --- Inputs / Outputs ---
    for section in ["inputs", "outputs"]:
        items = manifest.get(section, [])
        if isinstance(items, list):
            for i, p in enumerate(items):
                if not isinstance(p, dict):
                    errors.append(f"{section}[{i}]: must be an object")
                    continue
                if not p.get("name"):
                    errors.append(f"{section}[{i}]: missing name")
                pt = p.get("type", "")
                if not pt:
                    errors.append(f"{section}[{i}]: missing type")
                elif pt not in VALID_PARAM_TYPES:
                    errors.append(f"{section}[{i}]: invalid type '{pt}'")

    # --- Governance block ---
    gov = manifest.get("governance")
    if not gov or not isinstance(gov, dict):
        errors.append("Missing governance block")
    else:
        if not gov.get("owner"):
            errors.append("Governance: missing owner")
        if not gov.get("approval_chain") or not isinstance(gov.get("approval_chain"), list):
            errors.append("Governance: missing or invalid approval_chain")
        if not gov.get("compliance_tags") or not isinstance(gov.get("compliance_tags"), list):
            warnings.append("Governance: missing compliance_tags")
        lp = gov.get("lifecycle_policy", "")
        if lp and lp not in VALID_LIFECYCLE:
            errors.append(f"Governance: invalid lifecycle_policy '{lp}'")

    # --- Metadata block (governance identity) ---
    meta = manifest.get("metadata")
    if not meta or not isinstance(meta, dict):
        errors.append("Missing metadata block")
    else:
        uid = meta.get("unique_id", "")
        if not uid:
            errors.append("Metadata: missing unique_id")
        elif not UUID_V1_PATTERN.match(uid):
            warnings.append(f"Metadata: unique_id '{uid}' does not match UUID v1 pattern")

        uri = meta.get("uri", "")
        if not uri:
            errors.append("Metadata: missing uri")
        elif not URI_PATTERN.match(uri):
            errors.append(f"Metadata: uri must start with 'indestructibleeco://', got '{uri}'")

        urn = meta.get("urn", "")
        if not urn:
            errors.append("Metadata: missing urn")
        elif not URN_PATTERN.match(urn):
            errors.append(f"Metadata: urn must start with 'urn:indestructibleeco:', got '{urn}'")

        if not meta.get("schema_version"):
            warnings.append("Metadata: missing schema_version")
        if not meta.get("generated_by"):
            warnings.append("Metadata: missing generated_by")
        if not meta.get("created_at"):
            warnings.append("Metadata: missing created_at")

    # --- Directory structure checks ---
    if not (skill_path / "actions").is_dir():
        warnings.append("Missing actions/ directory")
    if not (skill_path / "schemas").is_dir():
        warnings.append("Missing schemas/ directory")

    valid = len(errors) == 0
    return valid, errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: quick_validate.py <skill-name>")
        print(f"\nSkills are expected at {SKILLS_BASE_PATH}/<skill-name>/")
        sys.exit(1)

    skill_input = sys.argv[1]
    resolved = resolve_skill_path(skill_input)
    print(f"Validating: {resolved}")

    valid, errors, warnings = validate_skill(skill_input)

    for e in errors:
        print(f"  ERROR: {e}")
    for w in warnings:
        print(f"  WARN:  {w}")

    icon = "✓" if valid else "✗"
    print(f"{icon} {resolved.name}: {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()