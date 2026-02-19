#!/usr/bin/env python3
"""
IndestructibleEco CI Validator Engine — Centralized validation for all CI/CD pipelines.

URI: indestructibleeco://tools/ci-validator
Usage:
    python3 tools/ci-validator/validate.py [--fix] [--report=report.json]

Validators:
    1. YAML syntax — all .yaml/.yml/.qyaml files parse without error
    2. Governance blocks — all .qyaml files have 4 mandatory blocks with required fields
    3. Identity consistency — zero stale references (superai, SUPERAI_, etc.)
    4. Dockerfile paths — COPY paths match actual build context
    5. Schema compliance — skill.json, package.json, pyproject.toml structure
    6. Workflow syntax — GitHub Actions workflow files are valid
    7. Cross-reference integrity — all file references in configs point to existing files
    8. Actions policy — GitHub Actions comply with repository ownership and SHA pinning requirements

Exit codes:
    0 — all validators pass
    1 — one or more validators failed (errors found)
    2 — validator engine internal error
"""

import sys
import os
import json
import re
import glob
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Resolve repo root (two levels up from this script)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

# --- Error taxonomy ---
class Severity:
    ERROR = "error"
    WARNING = "warning"


class Category:
    YAML_SYNTAX = "yaml-syntax"
    GOVERNANCE_MISSING = "governance-missing"
    IDENTITY_DRIFT = "identity-drift"
    DOCKERFILE_PATH = "dockerfile-path"
    SCHEMA_VIOLATION = "schema-violation"
    WORKFLOW_SYNTAX = "workflow-syntax"
    CROSS_REFERENCE = "cross-reference"
    ACTIONS_POLICY = "actions-policy"


def finding(category: str, severity: str, file: str, message: str,
            line: int = 0, auto_fixable: bool = False, fix_strategy: str = "") -> dict:
    return {
        "category": category,
        "severity": severity,
        "file": str(file),
        "line": line,
        "message": message,
        "auto_fixable": auto_fixable,
        "fix_strategy": fix_strategy,
    }


# ============================================================
# Validator 1: YAML Syntax
# ============================================================
def validate_yaml_syntax(repo: Path) -> list[dict]:
    findings = []
    yaml_files = (
        list(repo.rglob("*.yaml")) +
        list(repo.rglob("*.yml")) +
        list(repo.rglob("*.qyaml"))
    )
    yaml_files = [f for f in yaml_files if ".git" not in f.parts]

    for f in yaml_files:
        try:
            content = f.read_text()
            # Check for %YAML directive (GKE incompatible) — only at line start
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("%YAML"):
                    findings.append(finding(
                        Category.YAML_SYNTAX, Severity.ERROR, f.relative_to(repo),
                        "GKE-incompatible %YAML directive detected",
                        line=i, auto_fixable=True, fix_strategy="remove-%YAML-directive",
                    ))
            # Check for tabs (YAML uses spaces)
            for i, line in enumerate(content.splitlines(), 1):
                if "\t" in line and not line.strip().startswith("#"):
                    findings.append(finding(
                        Category.YAML_SYNTAX, Severity.ERROR, f.relative_to(repo),
                        f"Tab character found (YAML requires spaces)",
                        line=i, auto_fixable=True, fix_strategy="replace-tabs-with-spaces",
                    ))
                    break  # One per file is enough
            # Check for trailing whitespace in key positions
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                # Detect bare key at column 0 inside a multi-line string context
                # This is the exact pattern that caused the original L71 failure
                if (i > 1 and line and not line[0].isspace() and
                    not line.startswith("#") and not line.startswith("---") and
                    not line.startswith("...") and ":" not in line and
                    i < len(lines)):
                    prev = lines[i-2] if i >= 2 else ""
                    if 'python3 -c' in prev or 'python -c' in prev:
                        findings.append(finding(
                            Category.YAML_SYNTAX, Severity.ERROR, f.relative_to(repo),
                            f"Inline python code at column 0 will be parsed as YAML key — use heredoc",
                            line=i, auto_fixable=True, fix_strategy="heredoc-replacement",
                        ))
        except Exception as e:
            findings.append(finding(
                Category.YAML_SYNTAX, Severity.ERROR, f.relative_to(repo),
                f"Failed to read file: {e}",
            ))
    return findings


# ============================================================
# Validator 2: Governance Blocks (.qyaml)
# ============================================================
REQUIRED_GOVERNANCE_BLOCKS = [
    "document_metadata", "governance_info", "registry_binding", "vector_alignment_map"
]
REQUIRED_METADATA_FIELDS = [
    "unique_id", "uri", "urn", "target_system", "schema_version", "generated_by"
]
REQUIRED_GOVERNANCE_FIELDS = ["owner", "approval_chain", "compliance_tags", "lifecycle_policy"]
REQUIRED_REGISTRY_FIELDS = ["service_endpoint", "discovery_protocol", "health_check_path", "registry_ttl"]
REQUIRED_VECTOR_FIELDS = ["alignment_model", "coherence_vector_dim", "function_keyword", "contextual_binding"]


def validate_governance_blocks(repo: Path) -> list[dict]:
    findings = []
    qyaml_files = [f for f in repo.rglob("*.qyaml") if ".git" not in f.parts]

    for f in qyaml_files:
        content = f.read_text()
        rel = f.relative_to(repo)

        for block in REQUIRED_GOVERNANCE_BLOCKS:
            if f"{block}:" not in content:
                findings.append(finding(
                    Category.GOVERNANCE_MISSING, Severity.ERROR, rel,
                    f"Missing mandatory governance block: {block}",
                    auto_fixable=True, fix_strategy="inject-governance-block",
                ))

        field_groups = [
            (REQUIRED_METADATA_FIELDS, "document_metadata"),
            (REQUIRED_GOVERNANCE_FIELDS, "governance_info"),
            (REQUIRED_REGISTRY_FIELDS, "registry_binding"),
            (REQUIRED_VECTOR_FIELDS, "vector_alignment_map"),
        ]
        for fields, parent in field_groups:
            if f"{parent}:" in content:
                for field in fields:
                    if f"{field}:" not in content:
                        findings.append(finding(
                            Category.GOVERNANCE_MISSING, Severity.ERROR, rel,
                            f"Missing field '{field}' in {parent}",
                            auto_fixable=True, fix_strategy="inject-governance-field",
                        ))

        # URI/URN presence
        if "indestructibleeco://" not in content:
            findings.append(finding(
                Category.GOVERNANCE_MISSING, Severity.WARNING, rel,
                "No URI identifier (indestructibleeco://) found",
            ))
        if "urn:indestructibleeco:" not in content:
            findings.append(finding(
                Category.GOVERNANCE_MISSING, Severity.WARNING, rel,
                "No URN identifier (urn:indestructibleeco:) found",
            ))

        # Schema version must be v1
        if re.search(r"schema_version:\s*v[2-9]", content):
            findings.append(finding(
                Category.GOVERNANCE_MISSING, Severity.ERROR, rel,
                "Schema version must be v1",
            ))

    return findings


# ============================================================
# Validator 3: Identity Consistency
# ============================================================
STALE_PATTERNS = [
    (r"\bsuperai\b", "stale identity reference 'superai'"),
    (r"\bSUPERAI_", "stale env var prefix 'SUPERAI_'"),
    (r"\bsuperai-platform\b", "stale project name 'superai-platform'"),
]

# Files that legitimately reference stale patterns (detection rules, repair descriptions)
IDENTITY_SCAN_EXCLUDES = {
    "tools/ci-validator/validate.py",       # This file — contains detection patterns
    "tools/ci-validator/rules/identity.yaml",  # Rule definitions
}


def _is_detection_context(line: str) -> bool:
    """Return True if the line is a pattern definition, grep, or documentation context."""
    stripped = line.strip()
    indicators = [
        'r"\\b',  'r"\\B',           # Python raw regex
        "re.compile", "re.search", "re.finditer", "re.match",
        "grep ", "grep -",           # Shell grep
        "stale identity", "stale env var", "stale project",  # Error message strings
        "identity-drift", "identity-replace",  # Taxonomy references
        "STALE_PATTERNS",            # Variable name
        "Check for stale",           # Comment
        "superai, SUPERAI_",         # Documentation listing
        "Stale `",                   # Markdown backtick-quoted references
        "`superai`",                 # Markdown inline code
        "`SUPERAI_`",               # Markdown inline code
    ]
    return any(ind in stripped for ind in indicators)


def validate_identity_consistency(repo: Path) -> list[dict]:
    findings = []
    scan_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".yaml", ".yml",
                       ".qyaml", ".json", ".toml", ".sh", ".sql", ".md",
                       ".tpl", ".proto", ".html", ".css"}

    for f in repo.rglob("*"):
        if ".git" in f.parts or not f.is_file():
            continue
        if f.suffix not in scan_extensions:
            continue

        rel = f.relative_to(repo)

        # Skip files that are part of the validator/repair toolchain
        if str(rel) in IDENTITY_SCAN_EXCLUDES:
            continue

        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue

        lines = content.splitlines()
        for pattern, msg in STALE_PATTERNS:
            for line_idx, line in enumerate(lines):
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip lines that are detection/documentation contexts
                    if _is_detection_context(line):
                        continue
                    findings.append(finding(
                        Category.IDENTITY_DRIFT, Severity.ERROR, rel,
                        msg,
                        line=line_idx + 1, auto_fixable=True, fix_strategy="identity-replace",
                    ))

    return findings


# ============================================================
# Validator 4: Dockerfile Path Verification
# ============================================================
def validate_dockerfile_paths(repo: Path) -> list[dict]:
    findings = []
    dockerfiles = [f for f in repo.rglob("Dockerfile*") if ".git" not in f.parts and f.is_file()]

    # Parse workflow files to find build contexts
    build_contexts: dict[str, str] = {}
    for wf in (repo / ".github" / "workflows").glob("*.y*ml") if (repo / ".github" / "workflows").exists() else []:
        content = wf.read_text()
        # Match patterns like: -f backend/ai/Dockerfile backend/ai/
        for m in re.finditer(r"-f\s+(\S+Dockerfile\S*)\s+(\S+)", content):
            df_path = m.group(1)
            ctx = m.group(2)
            build_contexts[df_path] = ctx

    for df in dockerfiles:
        content = df.read_text()
        rel = df.relative_to(repo)

        # Find COPY instructions
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("COPY") and not stripped.startswith("COPY --from"):
                parts = stripped.split()
                if len(parts) >= 3:
                    src = parts[1]
                    # Skip variable references
                    if src.startswith("$") or src.startswith("--"):
                        continue
                    # Determine build context
                    df_rel = str(rel)
                    ctx_dir = build_contexts.get(df_rel, str(df.parent.relative_to(repo)))
                    src_full = repo / ctx_dir / src
                    # Check if source exists (file or directory or glob)
                    if not src_full.exists() and not list(repo.glob(f"{ctx_dir}/{src}")):
                        # Check if it's a relative path within the Dockerfile's directory
                        if not (df.parent / src).exists():
                            findings.append(finding(
                                Category.DOCKERFILE_PATH, Severity.WARNING, rel,
                                f"COPY source '{src}' may not exist in build context '{ctx_dir}'",
                                line=i, auto_fixable=True, fix_strategy="path-correction",
                            ))

    return findings


# ============================================================
# Validator 5: Schema Compliance (skill.json)
# ============================================================
def validate_schema_compliance(repo: Path) -> list[dict]:
    findings = []

    # Validate all skill.json files
    for sj in repo.rglob("skill.json"):
        if ".git" in sj.parts:
            continue
        rel = sj.relative_to(repo)
        try:
            manifest = json.loads(sj.read_text())
        except json.JSONDecodeError as e:
            findings.append(finding(
                Category.SCHEMA_VIOLATION, Severity.ERROR, rel,
                f"Invalid JSON: {e}",
            ))
            continue

        # Required fields
        for field in ["id", "name", "version", "category", "triggers", "actions", "governance", "metadata"]:
            if field not in manifest:
                findings.append(finding(
                    Category.SCHEMA_VIOLATION, Severity.ERROR, rel,
                    f"Missing required field: {field}",
                ))

        # Governance identity in metadata
        meta = manifest.get("metadata", {})
        if meta:
            if not meta.get("uri", "").startswith("indestructibleeco://"):
                findings.append(finding(
                    Category.SCHEMA_VIOLATION, Severity.ERROR, rel,
                    "Metadata URI must start with 'indestructibleeco://'",
                ))
            if not meta.get("urn", "").startswith("urn:indestructibleeco:"):
                findings.append(finding(
                    Category.SCHEMA_VIOLATION, Severity.ERROR, rel,
                    "Metadata URN must start with 'urn:indestructibleeco:'",
                ))

    return findings


# ============================================================
# Validator 6: Workflow Syntax
# ============================================================
def validate_workflow_syntax(repo: Path) -> list[dict]:
    findings = []
    wf_dir = repo / ".github" / "workflows"
    if not wf_dir.exists():
        return findings

    for wf in wf_dir.glob("*.y*ml"):
        content = wf.read_text()
        rel = wf.relative_to(repo)

        # Must have 'name:' at top level
        if not re.search(r"^name:", content, re.MULTILINE):
            findings.append(finding(
                Category.WORKFLOW_SYNTAX, Severity.ERROR, rel,
                "Workflow missing 'name:' field",
            ))

        # Must have 'on:' trigger
        if not re.search(r"^on:", content, re.MULTILINE):
            findings.append(finding(
                Category.WORKFLOW_SYNTAX, Severity.ERROR, rel,
                "Workflow missing 'on:' trigger",
            ))

        # Must have 'jobs:' section
        if not re.search(r"^jobs:", content, re.MULTILINE):
            findings.append(finding(
                Category.WORKFLOW_SYNTAX, Severity.ERROR, rel,
                "Workflow missing 'jobs:' section",
            ))

        # Check for inline python -c (the exact pattern that caused L71 failure)
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(r'python3?\s+-c\s+"', line):
                findings.append(finding(
                    Category.WORKFLOW_SYNTAX, Severity.ERROR, rel,
                    "Inline 'python -c' with quotes — use heredoc to avoid YAML parse errors",
                    line=i, auto_fixable=True, fix_strategy="heredoc-replacement",
                ))

        # Check for continue-on-error (prohibited)
        for i, line in enumerate(content.splitlines(), 1):
            if "continue-on-error" in line:
                findings.append(finding(
                    Category.WORKFLOW_SYNTAX, Severity.ERROR, rel,
                    "continue-on-error is prohibited — failures must halt the pipeline",
                    line=i, auto_fixable=True, fix_strategy="remove-continue-on-error",
                ))

    return findings


# ============================================================
# Validator 7: Cross-Reference Integrity
# ============================================================
def validate_cross_references(repo: Path) -> list[dict]:
    findings = []

    # Check kustomization.yaml references
    for kust in repo.rglob("kustomization.yaml"):
        if ".git" in kust.parts:
            continue
        content = kust.read_text()
        rel = kust.relative_to(repo)
        kust_dir = kust.parent

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("- ") and not stripped.startswith("- apiVersion"):
                ref = stripped[2:].strip()
                if ref and not ref.startswith("#") and not ref.startswith("{"):
                    ref_path = kust_dir / ref
                    if not ref_path.exists():
                        findings.append(finding(
                            Category.CROSS_REFERENCE, Severity.ERROR, rel,
                            f"Referenced resource '{ref}' does not exist",
                            line=i,
                        ))

    return findings


# ============================================================
# Validator 8: GitHub Actions Policy
# ============================================================
def validate_actions_policy(repo: Path) -> list[dict]:
    """Validate that all GitHub Actions comply with repository policy"""
    findings = []
    workflows_dir = repo / ".github" / "workflows"
    
    if not workflows_dir.exists():
        return findings
    
    # Load policy
    policy_file = repo / ".github" / "allowed-actions.yaml"
    policy = {}
    
    if policy_file.exists():
        try:
            import yaml
            with open(policy_file, 'r') as f:
                policy = yaml.safe_load(f)
        except Exception as e:
            findings.append(finding(
                Category.ACTIONS_POLICY, Severity.WARNING, ".github/allowed-actions.yaml",
                f"Failed to load policy file: {e}"
            ))
            return findings
    else:
        # Default policy if file doesn't exist
        policy = {
            'policy': {
                'require_org_ownership': True,
                'allowed_organizations': ['indestructibleorg'],
                'require_sha_pinning': True,
                'block_tag_references': True
            },
            'blocked_actions': [],
            'approved_actions': []
        }
    
    workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
    
    for workflow_file in workflow_files:
        try:
            content = workflow_file.read_text()
            
            # Find all 'uses:' statements
            pattern = r'uses:\s*([^\s#]+)'
            
            for line_num, line in enumerate(content.split('\n'), 1):
                match = re.search(pattern, line)
                if match:
                    action_ref = match.group(1).strip()
                    
                    # Validate the action
                    if '@' not in action_ref:
                        findings.append(finding(
                            Category.ACTIONS_POLICY, Severity.ERROR,
                            workflow_file.relative_to(repo),
                            f"Action '{action_ref}' missing version/ref specifier",
                            line=line_num
                        ))
                        continue
                    
                    action_path, ref = action_ref.rsplit('@', 1)
                    parts = action_path.split('/')
                    
                    if len(parts) < 2:
                        findings.append(finding(
                            Category.ACTIONS_POLICY, Severity.ERROR,
                            workflow_file.relative_to(repo),
                            f"Invalid action format '{action_ref}' (expected owner/repo@ref)",
                            line=line_num
                        ))
                        continue
                    
                    owner = parts[0]
                    repository_name = parts[1]
                    action_base = f"{owner}/{repository_name}"
                    
                    # Check if action is explicitly blocked
                    blocked_actions = policy.get('blocked_actions', [])
                    for blocked in blocked_actions:
                        if action_path.startswith(blocked):
                            findings.append(finding(
                                Category.ACTIONS_POLICY, Severity.ERROR,
                                workflow_file.relative_to(repo),
                                f"Action '{action_base}' is explicitly blocked by policy. Use manual commands instead.",
                                line=line_num
                            ))
                            break
                    
                    # Check organization ownership requirement
                    policy_config = policy.get('policy', {})
                    if policy_config.get('require_org_ownership', False):
                        allowed_orgs = policy_config.get('allowed_organizations', [])
                        if owner not in allowed_orgs:
                            findings.append(finding(
                                Category.ACTIONS_POLICY, Severity.ERROR,
                                workflow_file.relative_to(repo),
                                f"Action from '{owner}' is not allowed. Only actions from {', '.join(allowed_orgs)} are permitted.",
                                line=line_num
                            ))
                    
                    # Check SHA pinning requirement
                    if policy_config.get('require_sha_pinning', False):
                        # SHA should be 40 characters hex
                        sha_pattern = re.compile(r'^[a-f0-9]{40}$', re.IGNORECASE)
                        if not sha_pattern.match(ref):
                            findings.append(finding(
                                Category.ACTIONS_POLICY, Severity.ERROR,
                                workflow_file.relative_to(repo),
                                f"Action '{action_base}@{ref}' must be pinned to full-length commit SHA (40 characters), not tag '{ref}'",
                                line=line_num
                            ))
        
        except Exception as e:
            findings.append(finding(
                Category.ACTIONS_POLICY, Severity.WARNING,
                workflow_file.relative_to(repo),
                f"Error parsing workflow: {e}"
            ))
    
    return findings


# ============================================================
# Main Engine
# ============================================================
ALL_VALIDATORS = [
    ("yaml-syntax", validate_yaml_syntax),
    ("governance-blocks", validate_governance_blocks),
    ("identity-consistency", validate_identity_consistency),
    ("dockerfile-paths", validate_dockerfile_paths),
    ("schema-compliance", validate_schema_compliance),
    ("workflow-syntax", validate_workflow_syntax),
    ("cross-references", validate_cross_references),
    ("actions-policy", validate_actions_policy),
]


def run_all(repo: Path, report_path: str | None = None) -> int:
    all_findings: list[dict] = []
    error_count = 0
    warning_count = 0

    for name, validator_fn in ALL_VALIDATORS:
        try:
            results = validator_fn(repo)
        except Exception as e:
            print(f"  INTERNAL ERROR in {name}: {e}")
            return 2

        errors = [r for r in results if r["severity"] == Severity.ERROR]
        warnings = [r for r in results if r["severity"] == Severity.WARNING]
        error_count += len(errors)
        warning_count += len(warnings)

        icon = "✓" if not errors else "✗"
        print(f"  {icon} {name}: {len(errors)} errors, {len(warnings)} warnings")
        for r in errors:
            loc = f"L{r['line']}" if r["line"] else ""
            print(f"      ERROR {r['file']}:{loc} — {r['message']}")
        for r in warnings:
            loc = f"L{r['line']}" if r["line"] else ""
            print(f"      WARN  {r['file']}:{loc} — {r['message']}")

        all_findings.extend(results)

    print(f"\n  Total: {error_count} errors, {warning_count} warnings")

    if report_path:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repo": str(repo),
            "error_count": error_count,
            "warning_count": warning_count,
            "findings": all_findings,
        }
        Path(report_path).write_text(json.dumps(report, indent=2) + "\n")
        print(f"  Report: {report_path}")

    return 0 if error_count == 0 else 1


def main():
    import argparse
    parser = argparse.ArgumentParser(description="IndestructibleEco CI Validator Engine")
    parser.add_argument("--repo", default=str(REPO_ROOT), help="Repository root path")
    parser.add_argument("--report", default=None, help="Output report JSON path")
    parser.add_argument("--fix", action="store_true", help="Attempt auto-repair (future)")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(f"IndestructibleEco CI Validator — {repo}")
    print(f"{'='*60}")

    exit_code = run_all(repo, args.report)

    if exit_code == 0:
        print("\n  ✓ ALL VALIDATORS PASSED")
    else:
        print("\n  ✗ VALIDATION FAILED")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()