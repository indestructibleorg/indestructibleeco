#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: run_root_files
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
ETL Pipeline Root File Runner
ECO-Layer: GL30-49 (Execution)
Closure-Signal: execution
"""
# MNGA-002: Import organization needs review
from __future__ import annotations
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import yaml
ROOT_FILES = [
    ".root.gates.map.yaml",
    ".root.init.d/00-init.sh",
    ".root.init.d/01-semantic-root-init.sh",
    ".root.init.d/02-modules-init.sh",
    ".root.init.d/03-gl-platform.gl-platform.governance-init.sh",
    ".root.init.d/04-trust-init.sh",
    ".root.init.d/05-provenance-init.sh",
    ".root.init.d/06-integrity-init.sh",
    ".root.init.d/99-finalize.sh",
    ".root.jobs/concept-registry.json",
    ".root.jobs/semantic-root-attestations/initial-attestation.yaml",
    ".root.jobs/validation-rules.json",
    ".root.semantic-root.yaml",
    "ROOT_DIRECTORY_DESIGN_REPORT.md",
]
def _find_repo_root(start_path: Path) -> Path:
    current = start_path
    while current != current.parent:
        if (current / ".git").exists() and (current / "root").is_dir():
            return current
        current = current.parent
    raise FileNotFoundError("Unable to locate repository root containing 'root' directory")
def _parse_semantic_root_version(root_path: Path) -> str:
    semantic_root_file = root_path / ".root.semantic-root.yaml"
    if not semantic_root_file.exists():
        raise FileNotFoundError(f"Missing semantic root file: {semantic_root_file}")
    with semantic_root_file.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return str(data.get("metadata", {}).get("version", "unknown"))
def _run_init_scripts(root_path: Path, env: Dict[str, str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    init_dir = root_path / ".root.init.d"
    bootstrap_script = root_path / ".root.init.d/00-init.sh"
    bootstrap_cmd = 'source "$1"'
    for relative_script in ROOT_FILES:
        if not relative_script.startswith(".root.init.d/"):
            continue
        script_path = root_path / relative_script
        if not script_path.exists():
            results.append({
                "file": relative_script,
                "status": "missing",
                "message": "Initialization script not found",
            })
            continue
        if not script_path.is_file():
            results.append({
                "file": relative_script,
                "status": "failed",
                "message": "Initialization script is not a regular file",
            })
            continue
        if not os.access(script_path, os.X_OK):
            results.append({
                "file": relative_script,
                "status": "failed",
                "message": "Initialization script is not executable",
            })
            continue
        command = f'{bootstrap_cmd} && "$2"'
        completed = subprocess.run(
            ["bash", "-c", command, "bash", str(bootstrap_script), str(script_path)],
            cwd=str(init_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        entry: Dict[str, Any] = {
            "file": relative_script,
            "status": "executed" if completed.returncode == 0 else "failed",
            "output": completed.stdout.strip(),
        }
        if completed.returncode != 0:
            entry["return_code"] = completed.returncode
        results.append(entry)
    return results
def _collect_file_metadata(root_path: Path) -> List[Dict[str, Any]]:
    metadata: List[Dict[str, Any]] = []
    for relative_path in ROOT_FILES:
        file_path = root_path / relative_path
        entry: Dict[str, Any] = {
            "file": relative_path,
            "exists": file_path.exists(),
        }
        if file_path.exists():
            stat = file_path.stat()
            entry.update({
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
        metadata.append(entry)
    return metadata
def _build_environment(repo_root: Path, root_path: Path, semantic_version: str) -> Dict[str, str]:
    """Build environment variables used by root init scripts."""
    env = os.environ.copy()
    env.update({
        "MACHINENATIVEOPS_ROOT": str(repo_root),
        "ROOT_CONFIG_PATH": str(root_path),
        "SEMANTIC_ROOT_PATH": str(root_path / ".root.semantic-root.yaml"),
        # Retain both variables for compatibility with existing init scripts.
        "SEMANTIC_ROOT_CONFIG": str(root_path / ".root.semantic-root.yaml"),
        "SEMANTIC_ROOT_VERSION": semantic_version,
        "CONCEPT_REGISTRY_PATH": str(root_path / ".root.jobs/concept-registry.json"),
        "VALIDATION_RULES_PATH": str(root_path / ".root.jobs/validation-rules.json"),
        "ATTESTATION_PATH": str(root_path / ".root.jobs/semantic-root-attestations/initial-attestation.yaml"),
        "MODULES_REGISTRY": str(root_path / ".root.jobs/modules-registry.json"),
        "GOVERNANCE_REGISTRY": str(root_path / ".root.jobs/gl-platform.gl-platform.governance-registry.json"),
        "TRUST_REGISTRY": str(root_path / ".root.jobs/trust-registry.json"),
        "PROVENANCE_REGISTRY": str(root_path / ".root.jobs/provenance-registry.json"),
        "INTEGRITY_REGISTRY": str(root_path / ".root.jobs/integrity-registry.json"),
        "FINAL_ATTESTATION": str(root_path / ".root.jobs/final-attestation.yaml"),
        "MODULES_CONFIG": str(repo_root / "controlplane/config/root.modules.yaml"),
        "GOVERNANCE_CONFIG": str(repo_root / "controlplane/config/root.gl-platform.gl-platform.governance.yaml"),
        "TRUST_CONFIG": str(repo_root / "controlplane/config/root.trust.yaml"),
        "PROVENANCE_CONFIG": str(repo_root / "controlplane/config/root.provenance.yaml"),
        "INTEGRITY_CONFIG": str(repo_root / "controlplane/config/root.integrity.yaml"),
    })
    return env
def run_root_files(repo_root: Path) -> Dict[str, Any]:
    root_path = repo_root / "root"
    semantic_version = _parse_semantic_root_version(root_path)
    env = _build_environment(repo_root, root_path, semantic_version)
    file_metadata = _collect_file_metadata(root_path)
    script_results = _run_init_scripts(root_path, env)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "root_path": str(root_path),
        "semantic_root_version": semantic_version,
        "file_metadata": file_metadata,
        "script_results": script_results,
    }
def main() -> int:
    try:
        repo_root = _find_repo_root(Path(__file__).resolve())
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1
    try:
        result = run_root_files(repo_root)
    except (FileNotFoundError, yaml.YAMLError, subprocess.SubprocessError, OSError) as exc:
        print(f"❌ Failed to run root files ({type(exc).__name__}): {exc}")
        return 1
    output_path = repo_root / "etl-pipeline" / "root-evidence" / "root-file-run.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("✅ ETL pipeline root files executed")
    print(f"   Output: {output_path}")
    print(f"   Semantic root version: {result['semantic_root_version']}")
    failed = [entry for entry in result["script_results"] if entry.get("status") == "failed"]
    missing = [entry for entry in result["script_results"] if entry.get("status") == "missing"]
    if failed or missing:
        print(f"⚠️  Scripts failed: {len(failed)} | missing: {len(missing)}")
        return 1
    return 0
if __name__ == "__main__":
    sys.exit(main())
