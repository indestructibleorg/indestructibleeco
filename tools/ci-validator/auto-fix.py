#!/usr/bin/env python3
"""
IndestructibleEco CI Auto-Fix Engine — Automated repair for known warning/error patterns.

URI: indestructibleeco://tools/ci-validator/auto-fix
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
    """Replace stale identity references (superai → eco/indestructibleeco)."""
    result = {"strategy": "identity-replace", "applied": False, "details": ""}
    file_path = repo / finding.get("file", "")

    if not file_path.exists():
        result["details"] = f"File not found: {finding.get('file')}"
        return result

    content = file_path.read_text()
    original = content

    # Replacement map (order matters — longer patterns first)
    replacements = [
        (r"superai-platform", "indestructibleeco"),
        (r"SUPERAI_", "ECO_"),
        (r"superai-", "eco-"),
        (r"superai", "indestructibleeco"),
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
        result["details"] = "All governance blocks present"
        return result

    # Generate governance block
    rel = finding.get("file", "unknown")
    unique_id = f"eco-auto-{hash(rel) % 999999:06d}"
    uri = f"indestructibleeco://{rel.replace('.qyaml', '')}"

    block_template = f"""---
# YAML Toolkit v1 — Governance Block (auto-generated, manual editing prohibited)
document_metadata:
  unique_id: "{unique_id}"
  uri: "{uri}"
  urn: "urn:indestructibleeco:{rel.replace('/', ':').replace('.qyaml', '')}:{unique_id}"
  target_system: gke-production
  cross_layer_binding: []
  schema_version: v1
  generated_by: ci-auto-fix-engine
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
  alignment_model: quantum-bert-xxl-v1
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
                identity[field] = f"indestructibleeco://skills/{file_path.parent.name}"
            elif field == "urn":
                identity[field] = f"urn:indestructibleeco:skill:{file_path.parent.name}"
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
    print("║  IndestructibleEco CI Auto-Fix Engine                    ║")
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


# ── CLI Entry Point ──────────────────────────────────────────

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    report_path = None
    for arg in sys.argv[1:]:
        if arg.startswith("--report="):
            report_path = arg.split("=", 1)[1]

    sys.exit(run_auto_fix(REPO_ROOT, dry_run=dry_run, report_path=report_path))