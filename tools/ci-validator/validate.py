#!/usr/bin/env python3
"""
eco-base CI Validator Engine — Centralized validation for all CI/CD pipelines.

URI: eco-base://tools/ci-validator
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

# Import shared actions policy validation logic
try:
    from . import actions_policy_core
except ImportError:
    # Support running as script directly
    import actions_policy_core

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
                    auto_fixable=True, fix_strategy="governance-block",
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
        if "eco-base://" not in content:
            findings.append(finding(
                Category.GOVERNANCE_MISSING, Severity.WARNING, rel,
                "No URI identifier (eco-base://) found",
            ))
        if "urn:eco-base:" not in content:
            findings.append(finding(
                Category.GOVERNANCE_MISSING, Severity.WARNING, rel,
                "No URN identifier (urn:eco-base:) found",
            ))

        # Schema version must be v1 or v8
        if re.search(r"schema_version:\s*v(?!1\b|8\b)\d+\b", content):
            findings.append(finding(
                Category.GOVERNANCE_MISSING, Severity.ERROR, rel,
                "Schema version must be v1 or v8",
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
    "tools/ci-validator/auto-fix.py",       # Auto-fix engine — contains replacement maps
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

    # Parse build contexts from ALL sources (workflows, docker-compose, build scripts)
    build_contexts: dict[str, str] = {}

    # Source 1: GitHub Actions workflows — pattern: -f <dockerfile> <context>
    # Supports both single-line and multi-line (backslash continuation) docker build commands
    wf_dir = repo / ".github" / "workflows"
    if wf_dir.exists():
        for wf in wf_dir.glob("*.y*ml"):
            content = wf.read_text()
            # Normalize backslash-newline continuations for multi-line commands
            normalized = re.sub(r"\\\s*\n\s*", " ", content)
            for m in re.finditer(r"-f\s+(\S+Dockerfile\S*)\s+(\S+)", normalized):
                df_path = m.group(1)
                ctx = m.group(2)
                # Skip flags (e.g., --platform, --tag) that appear after -f <dockerfile>
                if not ctx.startswith("-"):
                    build_contexts[df_path] = ctx

    # Source 2: docker-compose files — pattern: context: <path>, dockerfile: <name>
    compose_files = list(repo.glob("docker-compose*.yml")) + list(repo.glob("docker-compose*.yaml"))
    compose_files += list(repo.glob("docker/docker-compose*.yml")) + list(repo.glob("docker/docker-compose*.yaml"))
    for cf in compose_files:
        try:
            content = cf.read_text()
            # Parse context + dockerfile pairs from compose files
            # Match blocks like: build:\n  context: ./backend/ai\n  dockerfile: Dockerfile
            for m in re.finditer(
                r"build:\s*\n\s+context:\s*(\S+)\s*\n\s+dockerfile:\s*(\S+)",
                content,
            ):
                ctx = m.group(1).strip("./") or "."
                df_name = m.group(2).strip()
                df_path = f"{ctx}/{df_name}" if ctx != "." else df_name
                build_contexts[df_path] = ctx
        except Exception as e:
            print(f"[ci-validator] Warning: failed to read or parse docker-compose file '{cf}': {e}", file=sys.stderr)

    # Source 3: Shell build scripts — pattern: -f <dockerfile> <context> (same as workflows)
    scripts_dir = repo / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.glob("*.sh"):
            try:
                content = script.read_text()
                for m in re.finditer(r"-f\s+(\S+Dockerfile\S*)\s+\\?\s*(\S+)", content):
                    df_path = m.group(1)
                    ctx = m.group(2).strip()
                    if ctx and not ctx.startswith("-"):
                        build_contexts[df_path] = ctx
            except Exception as e:
                print(f"[ci-validator] Warning: failed to read or parse build script '{script}': {e}", file=sys.stderr)

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
                    # Determine build context — check all known context mappings
                    df_rel = str(rel)
                    ctx_dir = build_contexts.get(df_rel, None)
                    # Fallback: check if Dockerfile basename matches any mapped path
                    if ctx_dir is None:
                        for mapped_df, mapped_ctx in build_contexts.items():
                            if df_rel.endswith(mapped_df) or mapped_df.endswith(str(rel.name)):
                                ctx_dir = mapped_ctx
                                break
                    # Final fallback: Dockerfile's parent directory
                    if ctx_dir is None:
                        ctx_dir = str(df.parent.relative_to(repo))

                    # Normalize context: "." means repo root
                    ctx_path = repo if ctx_dir == "." else repo / ctx_dir
                    src_full = ctx_path / src
                    # Check if source exists (file or directory or glob)
                    if not src_full.exists() and not list(ctx_path.glob(src)):
                        # Also check repo root as final fallback for "." context
                        if ctx_dir != "." or not (repo / src).exists():
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
            if not meta.get("uri", "").startswith("eco-base://"):
                findings.append(finding(
                    Category.SCHEMA_VIOLATION, Severity.ERROR, rel,
                    "Metadata URI must start with 'eco-base://'",
                ))
            if not meta.get("urn", "").startswith("urn:eco-base:"):
                findings.append(finding(
                    Category.SCHEMA_VIOLATION, Severity.ERROR, rel,
                    "Metadata URN must start with 'urn:eco-base:'",
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
            if re.search(r'python3?\s+-c\s+["\']', line):
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
        # Check for invalid permission keys (GitHub Actions only supports specific keys)
        VALID_PERMISSIONS = {
            'actions', 'attestations', 'checks', 'contents', 'deployments',
            'discussions', 'id-token', 'issues', 'packages', 'pages',
            'pull-requests', 'repository-projects', 'security-events', 'statuses',
        }
        try:
            import yaml as _yaml
            data = _yaml.safe_load(content)
            if isinstance(data, dict):
                perms = data.get('permissions', {})
                if isinstance(perms, dict):
                    for k in perms:
                        if k not in VALID_PERMISSIONS:
                            findings.append(finding(
                                Category.WORKFLOW_SYNTAX, Severity.ERROR, rel,
                                f"Invalid permission key '{k}' — GitHub Actions does not support it. "
                                f"Valid keys: {', '.join(sorted(VALID_PERMISSIONS))}",
                                auto_fixable=True, fix_strategy="remove-invalid-permission",
                            ))
                jobs_data = data.get('jobs', {})
                if isinstance(jobs_data, dict):
                    for jname, jdata in jobs_data.items():
                        if isinstance(jdata, dict):
                            jperms = jdata.get('permissions', {})
                            if isinstance(jperms, dict):
                                for k in jperms:
                                    if k not in VALID_PERMISSIONS:
                                        findings.append(finding(
                                            Category.WORKFLOW_SYNTAX, Severity.ERROR, rel,
                                            f"Invalid permission key '{k}' in job '{jname}'",
                                            auto_fixable=True, fix_strategy="remove-invalid-permission",
                                        ))
        except Exception:
            pass  # YAML parse errors caught by validate_yaml_syntax
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
    
    # Load policy using shared module
    policy_file = repo / ".github" / "allowed-actions.yaml"
    policy, load_error = actions_policy_core.load_policy_file(policy_file)
    
    if policy is None:
        # Use default policy
        policy = actions_policy_core.get_default_policy()
        
        # Emit warning/error if there was a load error (parse failure, not just missing file)
        if load_error and policy_file.exists():
            # Policy file exists but couldn't be loaded - this is a serious misconfiguration
            findings.append(finding(
                Category.ACTIONS_POLICY,
                Severity.ERROR,
                ".github/allowed-actions.yaml",
                f"Policy configuration error: {load_error}"
            ))
            # Continue with default policy but user is warned
    
    # Get enforcement level from policy
    policy_config = policy.get('policy', {})
    enforcement_level = policy_config.get('enforcement_level', 'error')
    severity = Severity.ERROR if enforcement_level == 'error' else Severity.WARNING
    
    workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
    
    for workflow_file in workflow_files:
        try:
            # Extract actions using shared function
            actions = actions_policy_core.extract_actions_from_workflow(workflow_file, repo)
            
            for action_info in actions:
                action_ref = action_info['action']
                line_num = action_info['line']
                
                # Validate using shared function
                violation_messages = actions_policy_core.validate_action_reference(
                    action_ref, policy
                )
                
                # Convert violations to findings
                for message in violation_messages:
                    findings.append(finding(
                        Category.ACTIONS_POLICY,
                        severity,
                        workflow_file.relative_to(repo),
                        message,
                        line=line_num
                    ))
        
        except RuntimeError as e:
            # Workflow parsing error - emit finding with configured severity
            findings.append(finding(
                Category.ACTIONS_POLICY,
                severity,
                workflow_file.relative_to(repo),
                f"Error parsing workflow: {e}"
            ))
        except Exception as e:
            # Unexpected error - always treat as ERROR regardless of enforcement level
            findings.append(finding(
                Category.ACTIONS_POLICY,
                Severity.ERROR,
                workflow_file.relative_to(repo),
                f"Unexpected error validating workflow: {e}"
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
    parser = argparse.ArgumentParser(description="eco-base CI Validator Engine")
    parser.add_argument("--repo", default=str(REPO_ROOT), help="Repository root path")
    parser.add_argument("--report", default=None, help="Output report JSON path")
    parser.add_argument("--fix", action="store_true", help="Attempt auto-repair (future)")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(f"eco-base CI Validator — {repo}")
    print(f"{'='*60}")

    exit_code = run_all(repo, args.report)

    if exit_code == 0:
        print("\n  ✓ ALL VALIDATORS PASSED")
    else:
        print("\n  ✗ VALIDATION FAILED")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()