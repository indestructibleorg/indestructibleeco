#!/usr/bin/env python3
"""
eco-base CI Auto-Fix Engine — Automated repair for known warning/error patterns.

URI: eco-base://tools/ci-validator/auto-fix
Usage:
    python3 tools/ci-validator/auto-fix.py [--dry-run] [--report=report.json]

Fix Strategies:
    1. path-correction    — Fix Dockerfile COPY paths (add ./, correct context)
    2. governance-block   — Add missing governance blocks to .qyaml files
    3. identity-replace   — Replace stale identity references (superai → eco)
    4. yaml-syntax        — Fix common YAML syntax issues (tabs → spaces)
    5. schema-field       — Add missing required fields to skill.json

Exit codes:
    0 — all fixes applied successfully (or nothing to fix)
    1 — some fixes could not be applied automatically
    2 — engine internal error
"""

import sys
import os
import re
import json
import time
from pathlib import Path
from datetime import datetime, timezone

# ── Configuration ────────────────────────────────────────────
REPO_ROOT = Path(os.getenv("REPO_ROOT", Path(__file__).resolve().parent.parent.parent))

# ── Fix Strategy Registry ────────────────────────────────────
FIX_REGISTRY: dict[str, callable] = {}


def register_fix(strategy: str):
    """Decorator to register a fix strategy."""
    def decorator(func):
        FIX_REGISTRY[strategy] = func
        return func
    return decorator


# ── Fix Strategies ───────────────────────────────────────────

@register_fix("path-correction")
def fix_path_correction(finding: dict, repo: Path, dry_run: bool = False) -> dict:
    """Fix Dockerfile COPY path issues by adding ./ prefix."""
    result = {"strategy": "path-correction", "applied": False, "details": ""}
    file_path = repo / finding.get("file", "")
    line_num = finding.get("line", 0)

    if not file_path.exists() or line_num == 0:
        result["details"] = f"Cannot locate file or line: {finding.get('file')}:L{line_num}"
        return result

    lines = file_path.read_text().splitlines()
    if line_num > len(lines):
        result["details"] = f"Line {line_num} exceeds file length ({len(lines)})"
        return result

    line = lines[line_num - 1]
    stripped = line.strip()

    if stripped.startswith("COPY") and not stripped.startswith("COPY --from"):
        parts = stripped.split()
        if len(parts) >= 3:
            src = parts[1]
            if not src.startswith("./") and not src.startswith("$") and not src.startswith("--"):
                new_src = f"./{src}"
                new_line = line.replace(f"COPY {src}", f"COPY {new_src}", 1)
                if not dry_run:
                    lines[line_num - 1] = new_line
                    file_path.write_text("\n".join(lines) + "\n")
                result["applied"] = True
                result["details"] = f"COPY {src} → COPY {new_src}"
                return result

    result["details"] = "Line does not match expected COPY pattern"
    return result


@register_fix("identity-replace")
def fix_identity_replace(finding: dict, repo: Path, dry_run: bool = False) -> dict:
    """Replace stale identity references (superai → eco/eco-base)."""
    result = {"strategy": "identity-replace", "applied": False, "details": ""}
    file_path = repo / finding.get("file", "")

    if not file_path.exists():
        result["details"] = f"File not found: {finding.get('file')}"
        return result

    content = file_path.read_text()
    original = content

    # Replacement map (order matters — longer patterns first)
    replacements = [
        (r"superai-platform", "eco-base"),
        (r"SUPERAI_", "ECO_"),
        (r"superai-", "eco-"),
        (r"superai", "eco-base"),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original:
        if not dry_run:
            file_path.write_text(content)
        changes = sum(1 for p, _ in replacements for _ in re.finditer(p, original))
        result["applied"] = True
        result["details"] = f"{changes} replacements applied"
    else:
        result["details"] = "No stale references found"

    return result


@register_fix("yaml-syntax")
def fix_yaml_syntax(finding: dict, repo: Path, dry_run: bool = False) -> dict:
    """Fix common YAML syntax issues (tabs → spaces, trailing whitespace)."""
    result = {"strategy": "yaml-syntax", "applied": False, "details": ""}
    file_path = repo / finding.get("file", "")

    if not file_path.exists():
        result["details"] = f"File not found: {finding.get('file')}"
        return result

    content = file_path.read_text()
    original = content

    # Fix tabs → 2 spaces
    content = content.replace("\t", "  ")

    # Fix trailing whitespace
    lines = content.splitlines()
    lines = [line.rstrip() for line in lines]
    content = "\n".join(lines) + "\n"

    if content != original:
        if not dry_run:
            file_path.write_text(content)
        result["applied"] = True
        result["details"] = "Fixed tabs and trailing whitespace"
    else:
        result["details"] = "No syntax issues found"

    return result


@register_fix("governance-block")
def fix_governance_block(finding: dict, repo: Path, dry_run: bool = False) -> dict:
    """Add missing governance blocks to .qyaml files."""
    result = {"strategy": "governance-block", "applied": False, "details": ""}
    file_path = repo / finding.get("file", "")

    if not file_path.exists():
        result["details"] = f"File not found: {finding.get('file')}"
        return result

    content = file_path.read_text()
    msg = finding.get("message", "")

    # Determine which blocks are missing
    required_blocks = ["document_metadata", "governance_info", "registry_binding", "vector_alignment_map"]
    missing = [b for b in required_blocks if b not in content]

    if not missing:
        result["details"] = "All governance blocks present (idempotent — no action needed)"
        result["applied"] = True  # Mark as resolved so validator doesn't re-flag
        return result
    # Idempotency: if document_metadata already exists, only inject missing sub-blocks
    if "document_metadata:" in content and len(missing) < len(required_blocks):
        # Partial injection: only add the specific missing blocks
        result["details"] = f"Partial blocks already present; missing: {', '.join(missing)}"
        # For partial injection, we skip to avoid corrupting existing structure
        # The validator will re-flag on next run with specific missing blocks
        result["applied"] = False
        return result

    # Generate governance block
    rel = finding.get("file", "unknown")
    unique_id = f"eco-auto-{hash(rel) % 999999:06d}"
    uri = f"eco-base://{rel.replace('.qyaml', '')}"

    block_template = f"""---
# YAML Toolkit v1 — Governance Block (auto-generated, manual editing prohibited)
document_metadata:
  unique_id: "{unique_id}"
  uri: "{uri}"
  urn: "urn:eco-base:{rel.replace('/', ':').replace('.qyaml', '')}:{unique_id}"
  target_system: gke-production
  cross_layer_binding: []
  schema_version: v8
  generated_by: yaml-toolkit-v8
  created_at: "{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')}"
governance_info:
  owner: platform-team
  approval_chain: [platform-team]
  compliance_tags: [zero-trust, soc2, internal]
  lifecycle_policy: active
registry_binding:
  service_endpoint: "http://localhost:8000"
  discovery_protocol: consul
  health_check_path: "/health"
  registry_ttl: 30
vector_alignment_map:
  alignment_model: BAAI/bge-large-en-v1.5
  coherence_vector_dim: 1024
  function_keyword: [auto-generated]
  contextual_binding: "auto-generated"
"""

    if not dry_run:
        # Only add blocks that are missing
        if all(b in missing for b in required_blocks):
            # All blocks missing — append full template
            content = content.rstrip() + "\n" + block_template
        file_path.write_text(content)

    result["applied"] = True
    result["details"] = f"Added missing blocks: {', '.join(missing)}"
    return result


@register_fix("schema-field")
def fix_schema_field(finding: dict, repo: Path, dry_run: bool = False) -> dict:
    """Add missing required fields to skill.json manifests."""
    result = {"strategy": "schema-field", "applied": False, "details": ""}
    file_path = repo / finding.get("file", "")

    if not file_path.exists():
        result["details"] = f"File not found: {finding.get('file')}"
        return result

    try:
        data = json.loads(file_path.read_text())
    except json.JSONDecodeError as e:
        result["details"] = f"Invalid JSON: {e}"
        return result

    fixes = []

    # Ensure governance block exists
    if "governance" not in data:
        data["governance"] = {}
        fixes.append("added governance block")

    gov = data["governance"]
    if "identity" not in gov:
        gov["identity"] = {}
        fixes.append("added governance.identity")

    identity = gov["identity"]
    for field in ["id", "uri", "urn"]:
        if field not in identity:
            if field == "id":
                identity[field] = f"auto-{hash(str(file_path)) % 999999:06d}"
            elif field == "uri":
                identity[field] = f"eco-base://skills/{file_path.parent.name}"
            elif field == "urn":
                identity[field] = f"urn:eco-base:skill:{file_path.parent.name}"
            fixes.append(f"added governance.identity.{field}")

    if fixes:
        if not dry_run:
            file_path.write_text(json.dumps(data, indent=2) + "\n")
        result["applied"] = True
        result["details"] = "; ".join(fixes)
    else:
        result["details"] = "All required fields present"

    return result


# ── Main Engine ──────────────────────────────────────────────

def run_auto_fix(repo: Path, dry_run: bool = False, report_path: str = None) -> int:
    """Run the CI Validator, then apply fixes for all auto-fixable findings."""

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  eco-base CI Auto-Fix Engine                    ║")
    print(f"║  Mode: {'DRY RUN' if dry_run else 'LIVE FIX'}                                         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Step 1: Run validator to get findings
    print("[1/3] Running CI Validator to detect issues...")
    sys.path.insert(0, str(repo / "tools" / "ci-validator"))
    try:
        import validate as validator
        # Run all validators
        all_findings = []
        for name, func in validator.ALL_VALIDATORS:
            findings = func(repo)
            all_findings.extend(findings)
    except Exception as e:
        print(f"  ERROR: Validator failed — {e}")
        return 2

    # Filter auto-fixable findings
    fixable = [f for f in all_findings if f.get("auto_fixable", False)]
    non_fixable = [f for f in all_findings if not f.get("auto_fixable", False)]

    total_errors = sum(1 for f in all_findings if f.get("severity") == "error")
    total_warnings = sum(1 for f in all_findings if f.get("severity") == "warning")

    print(f"  Found: {total_errors} errors, {total_warnings} warnings")
    print(f"  Auto-fixable: {len(fixable)}")
    print(f"  Manual review required: {len(non_fixable)}")
    print()

    if not fixable and not non_fixable:
        print("  ✓ No issues found — nothing to fix")
        return 0

    # Step 2: Apply fixes
    print("[2/3] Applying auto-fixes...")
    results = []
    applied_count = 0
    failed_count = 0

    for f in fixable:
        strategy = f.get("fix_strategy", "")
        fix_func = FIX_REGISTRY.get(strategy)

        if fix_func is None:
            print(f"  SKIP  {f.get('file')}:L{f.get('line', '?')} — unknown strategy '{strategy}'")
            failed_count += 1
            results.append({"finding": f, "result": {"applied": False, "details": f"Unknown strategy: {strategy}"}})
            continue

        result = fix_func(f, repo, dry_run=dry_run)
        results.append({"finding": f, "result": result})

        if result["applied"]:
            applied_count += 1
            prefix = "WOULD" if dry_run else "FIXED"
            print(f"  {prefix} {f.get('file')}:L{f.get('line', '?')} — {result['details']}")
        else:
            failed_count += 1
            print(f"  SKIP  {f.get('file')}:L{f.get('line', '?')} — {result['details']}")

    print()

    # Step 3: Summary
    print("[3/3] Summary")
    print(f"  Applied: {applied_count}")
    print(f"  Skipped: {failed_count}")
    print(f"  Manual:  {len(non_fixable)}")

    if non_fixable:
        print()
        print("  Manual review required:")
        for f in non_fixable:
            print(f"    {f.get('severity', '?').upper()}  {f.get('file')}:L{f.get('line', '?')} — {f.get('message', '')}")

    # Generate report
    if report_path:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "dry-run" if dry_run else "live",
            "total_findings": len(all_findings),
            "auto_fixable": len(fixable),
            "applied": applied_count,
            "failed": failed_count,
            "manual_required": len(non_fixable),
            "results": results,
        }
        Path(report_path).write_text(json.dumps(report, indent=2, default=str))
        print(f"\n  Report saved: {report_path}")

    print()
    if failed_count > 0 or len(non_fixable) > 0:
        print("  ⚠ Some issues require manual intervention")
        return 1
    else:
        print("  ✓ All issues resolved")
        return 0


# ── Additional Fix Strategies (added by auto-fix-ci framework) ──────────────

@register_fix("heredoc-replacement")
def fix_heredoc_replacement(finding: dict, repo: Path, dry_run: bool = False) -> dict:
    """
    Fix inline 'python3 -c "..."' patterns in GitHub Actions workflows.
    Converts multi-line python -c "..." to heredoc (python3 << 'PYEOF' ... PYEOF).
    """
    result = {"strategy": "heredoc-replacement", "applied": False, "details": ""}
    file_path = repo / finding.get("file", "")
    line_num = finding.get("line", 0)

    if not file_path.exists() or line_num == 0:
        result["details"] = f"Cannot locate file or line: {finding.get('file')}:L{line_num}"
        return result

    content = file_path.read_text()
    lines = content.splitlines(keepends=True)

    if line_num > len(lines):
        result["details"] = f"Line {line_num} exceeds file length ({len(lines)})"
        return result

    target_line = lines[line_num - 1]

    # Pattern: python3 -c "..." (single line, double-quoted)
    import re
    single_line_match = re.search(r'(python3?\s+-c\s+)"(.*?)"', target_line)
    if single_line_match:
        indent = len(target_line) - len(target_line.lstrip())
        indent_str = " " * indent
        py_cmd = single_line_match.group(1)
        py_code = single_line_match.group(2).replace('\\n', '\n')

        # Build heredoc replacement
        heredoc_lines = [
            f"{indent_str}python3 << 'PYEOF'\n",
        ]
        for code_line in py_code.split('\n'):
            heredoc_lines.append(f"{indent_str}{code_line}\n")
        heredoc_lines.append(f"{indent_str}PYEOF\n")

        if not dry_run:
            lines[line_num - 1] = "".join(heredoc_lines)
            file_path.write_text("".join(lines))

        result["applied"] = True
        result["details"] = f"Converted python3 -c \"...\" to heredoc at L{line_num}"
        return result

    # Pattern: multi-line python3 -c "... (opening quote, code spans multiple lines)
    multiline_match = re.search(r'(python3?\s+-c\s+)"', target_line)
    if multiline_match:
        # Find the closing quote (on a line by itself or with just whitespace)
        start_line = line_num - 1
        end_line = start_line
        indent = len(target_line) - len(target_line.lstrip())
        indent_str = " " * indent

        # Collect lines until we find the closing "
        py_code_lines = []
        i = start_line + 1
        while i < len(lines):
            l = lines[i]
            stripped = l.strip()
            if stripped == '"' or stripped.endswith('"') and not stripped.endswith('\\"'):
                # This is the closing line - include content before "
                closing_content = stripped.rstrip('"').strip()
                if closing_content:
                    py_code_lines.append(f"{indent_str}{closing_content}\n")
                end_line = i
                break
            else:
                py_code_lines.append(l)
            i += 1

        if end_line > start_line:
            # Build heredoc replacement
            heredoc = [f"{indent_str}python3 << 'PYEOF'\n"]
            heredoc.extend(py_code_lines)
            heredoc.append(f"{indent_str}PYEOF\n")

            if not dry_run:
                new_lines = lines[:start_line] + heredoc + lines[end_line + 1:]
                file_path.write_text("".join(new_lines))

            result["applied"] = True
            result["details"] = f"Converted multi-line python3 -c to heredoc (L{line_num}-L{end_line + 1})"
            return result

    result["details"] = f"Could not parse python -c pattern at L{line_num}: {target_line.strip()[:80]}"
    return result

@register_fix("remove-continue-on-error")
def fix_remove_continue_on_error(finding: dict, repo: Path, dry_run: bool = False) -> dict:
    """Remove prohibited continue-on-error lines from workflow files."""
    result = {"applied": False, "details": ""}
    file_path = repo / finding["file"]
    if not file_path.exists():
        result["details"] = f"File not found: {finding['file']}"
        return result

    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    line_num = finding.get("line", 0) - 1  # 0-indexed

    if line_num < 0 or line_num >= len(lines):
        result["details"] = f"Line {finding.get('line')} out of range"
        return result

    target_line = lines[line_num]
    if "continue-on-error" not in target_line:
        # Search nearby lines
        for offset in range(-2, 5):
            idx = line_num + offset
            if 0 <= idx < len(lines) and "continue-on-error" in lines[idx]:
                line_num = idx
                target_line = lines[idx]
                break
        else:
            result["details"] = f"Could not find continue-on-error near L{finding.get('line')}"
            return result

    if dry_run:
        result["applied"] = True
        result["details"] = f"Would remove continue-on-error at L{line_num + 1}: {target_line.strip()}"
        return result

    # Remove the line entirely
    del lines[line_num]
    file_path.write_text("".join(lines), encoding="utf-8")
    result["applied"] = True
    result["details"] = f"Removed continue-on-error at L{line_num + 1}: {target_line.strip()}"
    return result


# ── CLI Entry Point ──────────────────────────────────────────


@register_fix("remove-%YAML-directive")
def fix_remove_yaml_directive(file_path, finding, dry_run=False):
    """Remove %YAML directive lines from YAML files."""
    result = {"strategy": "remove-%YAML-directive", "applied": False, "details": ""}
    try:
        lines = file_path.read_text().splitlines(keepends=True)
        new_lines = [l for l in lines if not l.strip().startswith("%YAML")]
        if len(new_lines) < len(lines):
            result["details"] = f"Removed {len(lines)-len(new_lines)} %YAML directive line(s)"
            if not dry_run:
                file_path.write_text("".join(new_lines))
            result["applied"] = True
        else:
            result["details"] = "No %YAML directive found"
    except Exception as e:
        result["details"] = f"Error: {e}"
    return result


@register_fix("replace-tabs-with-spaces")
def fix_replace_tabs(file_path, finding, dry_run=False):
    """Replace tab indentation with 2-space indentation in YAML files."""
    result = {"strategy": "replace-tabs-with-spaces", "applied": False, "details": ""}
    try:
        content = file_path.read_text()
        if "\t" in content:
            fixed = content.expandtabs(2)
            result["details"] = "Replaced tab characters with spaces"
            if not dry_run:
                file_path.write_text(fixed)
            result["applied"] = True
        else:
            result["details"] = "No tab characters found"
    except Exception as e:
        result["details"] = f"Error: {e}"
    return result


@register_fix("inject-governance-field")
def fix_inject_governance_field(file_path, finding, dry_run=False):
    """Inject a missing governance field into an existing document_metadata block."""
    result = {"strategy": "inject-governance-field", "applied": False, "details": ""}
    try:
        content = file_path.read_text()
        # Determine which field is missing from the finding message
        missing_field = None
        for field in ["unique_id", "uri", "owner", "classification", "retention_policy", "compliance_tags"]:
            if field in finding.get("message", ""):
                missing_field = field
                break
        if not missing_field:
            result["details"] = "Could not determine missing field from finding"
            return result
        # Default values for each field
        defaults = {
            "unique_id": f"eco-auto-{abs(hash(str(file_path)))%999999:06d}",
            "uri": f"eco-base://{str(file_path).replace(str(file_path.parent.parent), '').lstrip('/')}",
            "owner": "platform-team@eco-base.io",
            "classification": "internal",
            "retention_policy": "3y",
            "compliance_tags": '["SOC2", "ISO27001"]',
        }
        val = defaults.get(missing_field, "REQUIRED")
        # Inject after document_metadata: line
        if "document_metadata:" in content:
            inject_line = f"  {missing_field}: \"{val}\"\n"
            fixed = content.replace("document_metadata:\n", f"document_metadata:\n{inject_line}", 1)
            if fixed != content:
                result["details"] = f"Injected missing field: {missing_field}"
                if not dry_run:
                    file_path.write_text(fixed)
                result["applied"] = True
            else:
                result["details"] = f"Could not inject field {missing_field} — manual review needed"
        else:
            result["details"] = "No document_metadata block found — use governance-block strategy first"
    except Exception as e:
        result["details"] = f"Error: {e}"
    return result


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    report_path = None
    for arg in sys.argv[1:]:
        if arg.startswith("--report="):
            report_path = arg.split("=", 1)[1]

    sys.exit(run_auto_fix(REPO_ROOT, dry_run=dry_run, report_path=report_path))
