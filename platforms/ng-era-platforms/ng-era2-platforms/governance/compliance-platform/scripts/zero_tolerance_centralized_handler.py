#!/usr/bin/env python3
"""
Zero-tolerance centralized violation handler.

Strict flow model:
  [internal] -> [external] -> [global] -> [cross-validate] -> [insight] -> (next loop)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


FLOW_MODEL = ["internal", "external", "global", "cross-validate", "insight"]
SCOPES = [
    "all",
    "gl_marker_only",
    "naming_filesystem_only",
    "axiom_references_only",
    "ng_mapping_only",
]
TEAM_ENV = "IND_AUTOOPS_TEAM_TAG"
ALT_TEAM_ENV = "INDAUTOOPSTEAM_TAG"

DEFAULT_REPORT_DIR = Path("/workspace/reports/zero-tolerance")
DEFAULT_REPO_ROOT = Path("/workspace")
DEFAULT_NG_SCRIPT = Path(
    "/workspace/gl-governance-compliance-platform/scripts/naming/ng_namespace_pipeline.py"
)
DEFAULT_BOUNDARY_SCRIPT = Path(
    "/workspace/gl-governance-compliance-platform/scripts/boundary_checker.py"
)
DEFAULT_NAMING_SCAN = Path(
    "/workspace/gl-governance-compliance-platform/scripts/scan_naming_violations.py"
)
DEFAULT_MARKER_SCAN = Path("/workspace/scan_files.py")
DEFAULT_FIX_NAMING = Path("/workspace/fix_naming_violations.py")
DEFAULT_ACCESS_POLICY = Path(
    "/workspace/gl-governance-compliance-platform/governance/naming/ng-namespace-access-policy.yaml"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StageResult:
    name: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None


def run_command(
    command: List[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    stdout_path: Optional[Path] = None,
    timeout: int = 600,
) -> str:
    if stdout_path:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        with stdout_path.open("w", encoding="utf-8") as handle:
            result = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                env=env,
                stdout=handle,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
    else:
        result = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n{result.stderr.strip()}"
        )
    return result.stdout if stdout_path is None else ""


def load_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_policy_version(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if "version" in line and ":" in line:
            _, value = line.split(":", 1)
            return value.strip().strip('"').strip("'")
    return ""


def compute_digest(payload: Dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def get_files_changed_count(repo_root: Path) -> int:
    try:
        output = run_command(["git", "diff", "--name-only"], cwd=repo_root).strip()
    except Exception:
        return 0
    if not output:
        return 0
    return len(output.splitlines())


def filter_plan_changes(
    changes: List[Dict],
    path_prefixes: List[str],
    max_changes: Optional[int],
) -> List[Dict]:
    filtered = changes
    if path_prefixes:
        normalized = [prefix.strip("/").replace("\\", "/") for prefix in path_prefixes]
        filtered = [
            item for item in filtered
            if any(
                str(item.get("old_path", "")).replace("\\", "/").startswith(prefix)
                for prefix in normalized
            )
        ]
    filtered = sorted(filtered, key=lambda item: (item.get("sequence", 0), item.get("old_path", "")))
    if max_changes is not None:
        filtered = filtered[:max_changes]
    return filtered


def write_trimmed_plan(
    plan_payload: Dict,
    changes: List[Dict],
    output_path: Path,
) -> Dict:
    trimmed = dict(plan_payload)
    trimmed["changes"] = changes
    trimmed["plan_digest"] = compute_digest({"changes": changes})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(trimmed, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return trimmed


def get_git_sha(repo_root: Path) -> str:
    try:
        output = run_command(["git", "rev-parse", "HEAD"], cwd=repo_root).strip()
    except Exception:
        output = ""
    return output


def get_git_status(repo_root: Path) -> str:
    try:
        output = run_command(["git", "status", "--porcelain"], cwd=repo_root).strip()
    except Exception:
        output = ""
    return output


def ensure_clean_worktree(repo_root: Path, allow_dirty: bool) -> None:
    if allow_dirty:
        return
    status = get_git_status(repo_root)
    if not status:
        return
    allowed_prefixes = (
        ".governance/locks/",
        "gl-governance-compliance-platform/governance/naming/registry/",
    )
    allowed_exact = {"scan_results.json"}
    for line in status.splitlines():
        path_segment = line[3:].strip()
        if " -> " in path_segment:
            _, path_segment = path_segment.split(" -> ", 1)
        if any(path_segment.startswith(prefix) for prefix in allowed_prefixes):
            continue
        if path_segment in allowed_exact:
            continue
        raise RuntimeError(
            "Dirty git worktree detected. Commit/stash changes or pass --allow-dirty."
        )


def acquire_lock(repo_root: Path, run_id: str) -> Path:
    lock_dir = repo_root / ".governance" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "zero-tolerance.lock"
    if lock_path.exists():
        raise RuntimeError("Lock file exists; another run may be in progress.")
    lock_path.write_text(
        json.dumps({"run_id": run_id, "timestamp": utc_now()}, indent=2),
        encoding="utf-8",
    )
    return lock_path


def release_lock(lock_path: Path) -> None:
    if lock_path.exists():
        lock_path.unlink()


def ensure_team_tag(value: Optional[str]) -> str:
    env_primary = os.environ.get(TEAM_ENV, "").strip()
    env_alt = os.environ.get(ALT_TEAM_ENV, "").strip()
    if env_primary and env_alt:
        raise RuntimeError(
            f"Both {TEAM_ENV} and {ALT_TEAM_ENV} are set; use only one."
        )
    tag = (value or env_primary or env_alt).strip()
    if not tag:
        raise RuntimeError(
            f"Missing team tag. Use --team-tag or set {TEAM_ENV}."
        )
    return tag


def run_internal_stage(
    report_dir: Path,
    repo_root: Path,
    team_tag: str,
    label: Optional[str] = None,
) -> List[StageResult]:
    results = []
    suffix = f"-{label}" if label else ""

    boundary_report = report_dir / f"boundary-report{suffix}.json"
    run_command(
        [
            "python3",
            str(DEFAULT_BOUNDARY_SCRIPT),
            "--report",
            "--format",
            "json",
            "--project-root",
            str(repo_root),
        ],
        stdout_path=boundary_report,
        timeout=600,
    )
    results.append(StageResult(f"internal{suffix}:boundary", "ok", str(boundary_report)))

    run_command(["python3", str(DEFAULT_MARKER_SCAN)], timeout=600)
    scan_results = Path("/workspace/scan_results.json")
    if scan_results.exists():
        marker_copy = report_dir / f"gl-marker-scan{suffix}.json"
        marker_copy.write_text(scan_results.read_text(encoding="utf-8"), encoding="utf-8")
        results.append(StageResult(f"internal{suffix}:gl-marker-scan", "ok", str(marker_copy)))
    else:
        results.append(StageResult(f"internal{suffix}:gl-marker-scan", "error", error="scan_results.json missing"))

    naming_report = report_dir / f"naming-violations{suffix}.json"
    run_command(
        [
            "python3",
            str(DEFAULT_NAMING_SCAN),
            "--path",
            str(repo_root),
            "--output",
            str(naming_report),
        ],
        timeout=600,
    )
    results.append(StageResult(f"internal{suffix}:naming-violations", "ok", str(naming_report)))

    run_command(
        [
            "python3",
            str(DEFAULT_NG_SCRIPT),
            "--stage",
            "internal",
            "--team-tag",
            team_tag,
        ],
        timeout=600,
    )
    results.append(StageResult(f"internal{suffix}:ng-namespace", "ok"))

    return results


def run_ng_stage(stage: str, team_tag: str, timeout: int = 600, label: Optional[str] = None) -> StageResult:
    run_command(
        [
            "python3",
            str(DEFAULT_NG_SCRIPT),
            "--stage",
            stage,
            "--team-tag",
            team_tag,
        ],
        timeout=timeout,
    )
    suffix = f"-{label}" if label else ""
    return StageResult(f"{stage}{suffix}:ng-namespace", "ok")


def generate_fix_plan(repo_root: Path, report_dir: Path) -> Path:
    plan_path = report_dir / "fix-plan.json"
    run_command(
        [
            "python3",
            str(DEFAULT_FIX_NAMING),
            "--workspace",
            str(repo_root),
            "--plan-output",
            str(plan_path),
        ],
        timeout=600,
    )
    return plan_path


def load_fix_plan(plan_path: Path) -> Dict:
    if not plan_path.exists():
        raise RuntimeError(f"Fix plan missing: {plan_path}")
    return load_json(plan_path)


def ensure_plan_matches_repo(plan_payload: Dict, repo_root: Path) -> None:
    expected_sha = plan_payload.get("git_sha", "")
    if expected_sha:
        current_sha = get_git_sha(repo_root)
        if current_sha and current_sha != expected_sha:
            raise RuntimeError(
                f"Plan git sha mismatch. expected={expected_sha} current={current_sha}"
            )


def create_backup_bundle(repo_root: Path, report_dir: Path, plan_path: Path) -> Dict:
    payload = load_json(plan_path)
    changes = payload.get("changes", [])
    backup_root = repo_root / ".governance" / "backups" / f"zero-tolerance-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    backup_root.mkdir(parents=True, exist_ok=True)
    manifest = []

    for change in changes:
        old_rel = change.get("old_path")
        if not old_rel:
            continue
        source_path = repo_root / old_rel
        if not source_path.exists():
            continue
        target_path = backup_root / old_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.is_dir():
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
        else:
            shutil.copy2(source_path, target_path)
        if source_path.is_file():
            digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
            manifest.append(
                {
                    "path": old_rel,
                    "sha256": digest,
                    "size": source_path.stat().st_size,
                }
            )
    manifest_path = backup_root / "manifest.json"
    manifest_path.write_text(
        json.dumps({"files": manifest}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    return {"path": str(backup_root), "manifest": str(manifest_path), "manifest_hash": manifest_hash}


def rollback_from_backup(repo_root: Path, backup_root: Path, plan_path: Path) -> None:
    payload = load_json(plan_path)
    changes = payload.get("changes", [])
    for change in changes:
        old_rel = change.get("old_path")
        new_rel = change.get("new_path")
        if not old_rel:
            continue
        old_path = repo_root / old_rel
        new_path = repo_root / new_rel if new_rel else None
        backup_path = backup_root / old_rel
        if new_path and new_path.exists():
            if new_path.is_dir():
                shutil.rmtree(new_path)
            else:
                new_path.unlink()
        if backup_path.exists():
            old_path.parent.mkdir(parents=True, exist_ok=True)
            if backup_path.is_dir():
                shutil.copytree(backup_path, old_path, dirs_exist_ok=True)
            else:
                shutil.copy2(backup_path, old_path)


def apply_fixes(
    repo_root: Path,
    report_dir: Path,
    ack_destructive: bool,
    plan_path: Path,
    timeout: int,
) -> List[str]:
    actions = []
    if not ack_destructive:
        raise RuntimeError(
            "Destructive fixes require --ack-destructive to proceed."
        )
    run_command(
        [
            "python3",
            str(DEFAULT_FIX_NAMING),
            "--workspace",
            str(repo_root),
            "--apply",
            "--plan-input",
            str(plan_path),
        ],
        timeout=timeout,
    )
    actions.append("Applied naming violation auto-fix.")
    return actions


def build_summary(report_dir: Path, label: Optional[str] = None) -> Dict:
    suffix = f"-{label}" if label else ""
    boundary = load_json(report_dir / f"boundary-report{suffix}.json")
    marker_scan = load_json(report_dir / f"gl-marker-scan{suffix}.json")
    naming = load_json(report_dir / f"naming-violations{suffix}.json")
    ng_cross = load_json(
        Path(
            "/workspace/gl-governance-compliance-platform/governance/naming/registry/ng-era1-cross-validation.json"
        )
    )

    naming_summary = naming.get("violation_summary", {})
    naming_total = sum(naming_summary.values()) if naming_summary else 0

    return {
        "boundary": {
            "total_violations": boundary.get("total_violations", 0),
            "compliance_rate": boundary.get("compliance_rate"),
        },
        "gl_marker": {
            "total_files": marker_scan.get("scan_summary", {}).get("total_files"),
            "needs_adjustment": marker_scan.get("scan_summary", {}).get("files_needing_adjustment"),
            "compliance_rate": marker_scan.get("scan_summary", {}).get("compliance_rate"),
        },
        "naming": {
            "total_violations": naming_total,
            "by_type": naming_summary,
        },
        "ng_namespace": {
            "total_records": ng_cross.get("counts", {}).get("total_records"),
            "unmapped_layers": ng_cross.get("counts", {}).get("unmapped_layers"),
            "missing_era2_mapping": ng_cross.get("counts", {}).get("missing_era2_mapping"),
            "prefix_collisions": ng_cross.get("counts", {}).get("prefix_collisions"),
        },
    }


def determine_zero_tolerance_status(summary: Dict) -> Dict:
    failures = []
    if summary["boundary"]["total_violations"]:
        failures.append("boundary_violations")
    if summary["gl_marker"]["needs_adjustment"]:
        failures.append("gl_marker_missing")
    if summary["naming"]["total_violations"]:
        failures.append("naming_violations")
    if summary["ng_namespace"]["unmapped_layers"]:
        failures.append("ng_unmapped_layers")
    if summary["ng_namespace"]["missing_era2_mapping"]:
        failures.append("ng_missing_era2_mapping")
    if summary["ng_namespace"]["prefix_collisions"]:
        failures.append("ng_prefix_collisions")

    return {
        "status": "blocked" if failures else "pass",
        "failures": failures,
    }


def extract_scope_count(summary: Dict, scope: str) -> int:
    naming = summary.get("naming", {}).get("by_type", {}) or {}
    if scope == "gl_marker_only":
        return summary.get("gl_marker", {}).get("needs_adjustment") or 0
    if scope == "naming_filesystem_only":
        return (
            naming.get("file_uppercase", 0)
            + naming.get("file_spaces", 0)
            + naming.get("file_special_chars", 0)
        )
    if scope == "axiom_references_only":
        return naming.get("axiom_references", 0)
    if scope == "ng_mapping_only":
        return summary.get("ng_namespace", {}).get("missing_era2_mapping") or 0
    return 0


def determine_status_with_scope(summary: Dict, scope: str) -> Dict:
    if scope == "all":
        return determine_zero_tolerance_status(summary)
    count = extract_scope_count(summary, scope)
    return {
        "status": "pass" if count == 0 else "blocked",
        "failures": [scope] if count else [],
        "scope_count": count,
    }


def build_remediation_plan(summary: Dict) -> List[Dict]:
    plan = []
    if summary["boundary"]["total_violations"]:
        plan.append(
            {
                "issue": "Boundary violations detected",
                "action": "Run boundary checker per layer and fix dependency violations.",
                "command": "python3 gl-governance-compliance-platform/scripts/boundary_checker.py --check --project-root /workspace",
            }
        )
    if summary["gl_marker"]["needs_adjustment"]:
        plan.append(
            {
                "issue": "Missing GL markers",
                "action": "Update files listed in scan_results.json to include GL markers.",
                "artifact": "/workspace/scan_results.json",
            }
        )
    if summary["naming"]["total_violations"]:
        plan.append(
            {
                "issue": "Naming violations",
                "action": "Review naming violations report and apply renames.",
                "command": "python3 fix_naming_violations.py --workspace /workspace --apply",
            }
        )
    if summary["ng_namespace"]["unmapped_layers"]:
        plan.append(
            {
                "issue": "Unmapped layers in namespace scan",
                "action": "Update LAYER_MAP or add explicit mappings.",
                "artifact": "/workspace/gl-governance-compliance-platform/scripts/naming/ng_namespace_pipeline.py",
            }
        )
    if summary["ng_namespace"]["missing_era2_mapping"]:
        plan.append(
            {
                "issue": "Missing Era-2 mappings",
                "action": "Extend ng-era1-era2-mapping.yaml for coverage.",
                "artifact": "/workspace/gl-governance-compliance-platform/governance/naming/ng-era1-era2-mapping.yaml",
            }
        )
    if summary["ng_namespace"]["prefix_collisions"]:
        plan.append(
            {
                "issue": "Prefix collisions",
                "action": "Normalize prefixes and enforce uniqueness per module.",
            }
        )
    return plan


def write_markdown(
    report_path: Path,
    summary: Dict,
    status: Dict,
    plan: List[Dict],
    team_tag: str,
    run_id: str,
    scope: str,
) -> None:
    lines = [
        "# Zero-Tolerance Centralized Report",
        "",
        f"Timestamp: {utc_now()}",
        f"Run ID: {run_id}",
        f"Team Tag: {team_tag}",
        f"Scope: {scope}",
        "",
        "## Flow Model",
        " -> ".join(FLOW_MODEL),
        "",
        "## Status",
        f"- Status: {status['status'].upper()}",
        f"- Failures: {', '.join(status['failures']) if status['failures'] else 'None'}",
        "",
        "## Summary",
        f"- Boundary violations: {summary['boundary']['total_violations']}",
        f"- GL marker missing: {summary['gl_marker']['needs_adjustment']}",
        f"- Naming violations: {summary['naming']['total_violations']}",
        f"- NG unmapped layers: {summary['ng_namespace']['unmapped_layers']}",
        f"- NG missing Era-2 mapping: {summary['ng_namespace']['missing_era2_mapping']}",
        f"- NG prefix collisions: {summary['ng_namespace']['prefix_collisions']}",
        "",
        "## Remediation Plan",
    ]
    for item in plan:
        lines.append(f"- Issue: {item['issue']}")
        lines.append(f"  Action: {item.get('action')}")
        if item.get("command"):
            lines.append(f"  Command: {item['command']}")
        if item.get("artifact"):
            lines.append(f"  Artifact: {item['artifact']}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Zero-tolerance centralized violation handler",
    )
    parser.add_argument("--team-tag", help="Team tag for authorization")
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory for centralized reports",
    )
    parser.add_argument(
        "--repo-root",
        default=str(DEFAULT_REPO_ROOT),
        help="Repository root",
    )
    parser.add_argument(
        "--apply-fixes",
        action="store_true",
        help="Apply auto-fixes where available (requires --ack-destructive).",
    )
    parser.add_argument(
        "--ack-destructive",
        action="store_true",
        help="Acknowledge destructive fixes (renames).",
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Generate fix plan only (no modifications).",
    )
    parser.add_argument(
        "--scope",
        choices=SCOPES,
        default="all",
        help="Limit validation/remediation scope.",
    )
    parser.add_argument(
        "--path-prefix",
        action="append",
        default=[],
        help="Restrict plan/apply to a path prefix (repeatable).",
    )
    parser.add_argument(
        "--max-changes",
        type=int,
        help="Limit number of plan/apply changes.",
    )
    parser.add_argument(
        "--plan-input",
        help="Use an existing fix plan JSON for apply.",
    )
    parser.add_argument(
        "--rollback-on-fail",
        action="store_true",
        help="Rollback from backup if apply or re-validation fails.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow running apply fixes on a dirty git worktree.",
    )
    parser.add_argument(
        "--apply-timeout",
        type=int,
        default=3600,
        help="Timeout in seconds for apply fixes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(args.repo_root)

    team_tag = ensure_team_tag(args.team_tag)
    run_id = str(uuid.uuid4())
    actor = os.environ.get("USER", "")
    git_sha_before = get_git_sha(repo_root)
    git_status_before = get_git_status(repo_root)
    policy_version = read_policy_version(DEFAULT_ACCESS_POLICY)
    lock_path = acquire_lock(repo_root, run_id)

    try:
        stage_results: List[StageResult] = []
        stage_results.extend(run_internal_stage(report_dir, repo_root, team_tag))
        stage_results.append(run_ng_stage("external", team_tag))
        stage_results.append(run_ng_stage("global", team_tag))
        stage_results.append(run_ng_stage("cross-validate", team_tag))
        stage_results.append(run_ng_stage("insight", team_tag))

        fix_actions: List[str] = []
        fix_plan_path = Path(args.plan_input).resolve() if args.plan_input else generate_fix_plan(repo_root, report_dir)
        plan_payload = load_fix_plan(fix_plan_path)
        ensure_plan_matches_repo(plan_payload, repo_root)
        plan_changes = plan_payload.get("changes", [])
        filtered_changes = filter_plan_changes(plan_changes, args.path_prefix, args.max_changes)
        trimmed_plan_path = None
        if filtered_changes != plan_changes:
            trimmed_plan_path = report_dir / "fix-plan-trimmed.json"
            plan_payload = write_trimmed_plan(plan_payload, filtered_changes, trimmed_plan_path)
            plan_changes = filtered_changes
        plan_digest = plan_payload.get("plan_digest", "")
        if not plan_digest:
            plan_digest = compute_digest({"changes": plan_changes})
        destructive_actions = [item for item in plan_changes if item.get("destructive")]
        backup_bundle = {}

        pre_summary = build_summary(report_dir)
        pre_status = determine_status_with_scope(pre_summary, args.scope)

        if args.plan_only:
            plan = build_remediation_plan(pre_summary)
            report_payload = {
                "timestamp": utc_now(),
                "run_id": run_id,
                "team_tag": team_tag,
                "actor": actor,
                "tool_version": git_sha_before,
                "policy_pack_version": policy_version,
                "git_sha_before": git_sha_before,
                "git_status_before": git_status_before,
                "flow_model": FLOW_MODEL,
                "scope": args.scope,
                "path_prefix": args.path_prefix,
                "max_changes": args.max_changes,
                "stage_results": [result.__dict__ for result in stage_results],
                "summary": pre_summary,
                "status": pre_status,
                "remediation_plan": plan,
                "fix_plan_path": str(trimmed_plan_path or fix_plan_path),
                "plan_digest": plan_digest,
                "destructive_actions": destructive_actions,
                "fix_actions": [],
            }
            report_payload["report_digest"] = compute_digest(report_payload)
            json_report = report_dir / "centralized-report.json"
            json_report.write_text(
                json.dumps(report_payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            markdown_report = report_dir / "centralized-report.md"
            write_markdown(markdown_report, pre_summary, pre_status, plan, team_tag, run_id, args.scope)
            return 2 if pre_status["status"] == "blocked" else 0

        apply_error = None
        rollback_after_error = False
        if args.apply_fixes:
            if args.scope not in {"all", "naming_filesystem_only"}:
                raise RuntimeError(
                    f"Scope '{args.scope}' does not support apply-fixes yet."
                )
            ensure_clean_worktree(repo_root, args.allow_dirty)
            plan_path_to_use = trimmed_plan_path or fix_plan_path
            backup_bundle = create_backup_bundle(repo_root, report_dir, plan_path_to_use)
            try:
                fix_actions = apply_fixes(
                    repo_root,
                    report_dir,
                    args.ack_destructive,
                    plan_path_to_use,
                    args.apply_timeout,
                )
            except Exception as exc:
                apply_error = str(exc)
                if args.rollback_on_fail and backup_bundle:
                    rollback_from_backup(repo_root, Path(backup_bundle["path"]), plan_path_to_use)
                    rollback_after_error = True
                fix_actions = []

            if apply_error is None:
                stage_results.extend(run_internal_stage(report_dir, repo_root, team_tag, label="postfix"))
                stage_results.append(run_ng_stage("external", team_tag, label="postfix"))
                stage_results.append(run_ng_stage("global", team_tag, label="postfix"))
                stage_results.append(run_ng_stage("cross-validate", team_tag, label="postfix"))
                stage_results.append(run_ng_stage("insight", team_tag, label="postfix"))
            else:
                stage_results.append(StageResult("apply:fixes", "error", error=apply_error))

        rollback_validation_passed = None
        if apply_error and rollback_after_error:
            stage_results.extend(run_internal_stage(report_dir, repo_root, team_tag, label="rollback"))
            rollback_summary = build_summary(report_dir, label="rollback")
            rollback_status = determine_status_with_scope(rollback_summary, args.scope)
            rollback_validation_passed = rollback_status["status"] == "pass"

        summary_label = "postfix" if args.apply_fixes and apply_error is None else None
        summary = build_summary(report_dir, label=summary_label)
        status = determine_status_with_scope(summary, args.scope)
        plan = build_remediation_plan(summary)
        git_sha_after = get_git_sha(repo_root)
        git_status_after = get_git_status(repo_root)
        files_changed_count = get_files_changed_count(repo_root)

        rollback_performed = rollback_after_error
        if args.apply_fixes and args.rollback_on_fail and backup_bundle:
            pre_scope_count = pre_status.get("scope_count", extract_scope_count(pre_summary, args.scope))
            post_scope_count = status.get("scope_count", extract_scope_count(summary, args.scope))
            rollback_needed = False
            if args.scope == "all":
                rollback_needed = status["status"] == "blocked"
            else:
                rollback_needed = post_scope_count > pre_scope_count
            if rollback_needed:
                rollback_from_backup(repo_root, Path(backup_bundle["path"]), plan_path_to_use)
                rollback_performed = True
                stage_results.extend(run_internal_stage(report_dir, repo_root, team_tag, label="rollback"))
                rollback_summary = build_summary(report_dir, label="rollback")
                rollback_status = determine_status_with_scope(rollback_summary, args.scope)
                rollback_validation_passed = rollback_status["status"] == "pass"
                git_sha_after = get_git_sha(repo_root)
                git_status_after = get_git_status(repo_root)

        report_payload = {
            "timestamp": utc_now(),
            "run_id": run_id,
            "team_tag": team_tag,
            "actor": actor,
            "tool_version": git_sha_before,
            "policy_pack_version": policy_version,
            "git_sha_before": git_sha_before,
            "git_sha_after": git_sha_after,
            "git_status_before": git_status_before,
            "git_status_after": git_status_after,
            "files_changed_count": files_changed_count,
            "flow_model": FLOW_MODEL,
            "scope": args.scope,
            "path_prefix": args.path_prefix,
            "max_changes": args.max_changes,
            "stage_results": [result.__dict__ for result in stage_results],
            "summary": summary,
            "status": status,
            "validation_summary": {
                "pre_status": pre_status,
                "post_status": status if args.apply_fixes else None,
                "rollback_validation_passed": rollback_validation_passed,
            },
            "remediation_plan": plan,
            "fix_plan_path": str(trimmed_plan_path or fix_plan_path),
            "plan_digest": plan_digest,
            "backup_bundle": backup_bundle,
            "bundle_manifest_hash": backup_bundle.get("manifest_hash") if backup_bundle else "",
            "rollback_performed": rollback_performed,
            "apply_error": apply_error,
            "destructive_actions": destructive_actions,
            "fix_actions": fix_actions,
        }

        report_payload["report_digest"] = compute_digest(report_payload)

        json_report = report_dir / "centralized-report.json"
        json_report.write_text(
            json.dumps(report_payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        markdown_report = report_dir / "centralized-report.md"
        write_markdown(markdown_report, summary, status, plan, team_tag, run_id, args.scope)

        return 0 if status["status"] == "pass" else 2
    finally:
        release_lock(lock_path)


if __name__ == "__main__":
    sys.exit(main())
