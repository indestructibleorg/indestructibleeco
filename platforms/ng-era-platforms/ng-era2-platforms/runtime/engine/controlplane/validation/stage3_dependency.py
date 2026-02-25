#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: stage3_dependency
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Supply Chain Verification - Stage 3: Dependency Locking & Reproducible Builds
This module handles dependency locking and reproducible build verification.
"""
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from .hash_manager import HashManager
from .supply_chain_types import VerificationEvidence
# Configure logging
logger = logging.getLogger(__name__)
class Stage3DependencyVerifier:
    """Verifier for Stage 3: Dependency Locking & Reproducible Builds"""
    def __init__(self, repo_path: Path, evidence_dir: Path, hash_manager: HashManager):
        """
        Initialize Stage 3 verifier
        Args:
            repo_path: Path to repository
            evidence_dir: Path to evidence directory
            hash_manager: Hash manager instance
        """
        self.repo_path = repo_path
        self.evidence_dir = evidence_dir
        self.hash_manager = hash_manager
    def verify(self) -> VerificationEvidence:
        """
        Execute Stage 3: Dependency locking & reproducible build verification
        Returns:
            VerificationEvidence with validation results
        """
        logger.info("🔍 Stage 3: 依賴鎖定與可重現配置驗證開始")
        data = {
            "lock_files": [],
            "dependency_checks": [],
            "reproducibility_checks": [],
            "build_artifacts": [],
        }
        # 檢查各種 lock 檔案
        lock_files_map = {
            "go.sum": ("go.mod", "Go"),
            "pnpm-lock.yaml": ("pnpm-workspace.yaml", "pnpm"),
            "package-lock.json": ("package.json", "npm"),
            "yarn.lock": ("package.json", "yarn"),
            "requirements.txt": ("setup.py", "pip"),
            "Pipfile.lock": ("Pipfile", "pipenv"),
            "poetry.lock": ("pyproject.toml", "poetry"),
        }
        for lock_file, (source_file, manager) in lock_files_map.items():
            lock_path = self.repo_path / lock_file
            source_path = self.repo_path / source_file
            lock_info = {
                "file": lock_file,
                "manager": manager,
                "source_file": source_file,
                "exists": lock_path.exists(),
                "source_exists": source_path.exists(),
                "size": lock_path.stat().st_size if lock_path.exists() else 0,
                "last_modified": (
                    lock_path.stat().st_mtime if lock_path.exists() else None
                ),
            }
            # 如果有源文件但沒有 lock 檔案，則是問題
            if source_path.exists() and not lock_path.exists():
                lock_info["status"] = "missing_lock"
                data["dependency_checks"].append(
                    {
                        "file": lock_file,
                        "issue": "missing_lock_file",
                        "severity": "HIGH",
                    }
                )
            elif lock_path.exists():
                lock_info["status"] = "present"
                # 嘗試驗證 lock 檔案完整性
                try:
                    with open(lock_path, "r") as f:
                        content = f.read()
                    # 基本完整性檢查
                    if len(content) > 0:
                        lock_info["integrity"] = "valid"
                        lock_info["content_hash"] = hashlib.sha256(
                            content.encode()
                        ).hexdigest()
                    else:
                        lock_info["integrity"] = "invalid"
                        lock_info["issue"] = "empty_file"
                except Exception as e:
                    lock_info["integrity"] = "error"
                    lock_info["error"] = str(e)
            data["lock_files"].append(lock_info)
        # 檢查可重現性配置
        reproducibility_files = [
            "Dockerfile",
            "Makefile",
            "justfile",
            "Taskfile.yml",
            ".github/workflows",
            "Jenkinsfile",
        ]
        for repro_file in reproducibility_files:
            path = self.repo_path / repro_file
            if path.exists() or path.is_dir():
                data["reproducibility_checks"].append(
                    {
                        "file": repro_file,
                        "exists": True,
                        "type": "directory" if path.is_dir() else "file",
                    }
                )
        # 檢查建置產物目錄
        build_dirs = ["dist", "build", "target", "bin", "out"]
        for build_dir in build_dirs:
            path = self.repo_path / build_dir
            if path.exists():
                artifacts = []
                if path.is_dir():
                    for artifact in path.rglob("*"):
                        if artifact.is_file():
                            artifacts.append(
                                {
                                    "file": str(artifact.relative_to(self.repo_path)),
                                    "size": artifact.stat().st_size,
                                    "hash": self._file_hash(artifact),
                                }
                            )
                data["build_artifacts"].append(
                    {
                        "directory": build_dir,
                        "artifacts_count": len(artifacts),
                        "artifacts": artifacts[:10],  # 限制數量
                    }
                )
        evidence = self._create_evidence(
            stage=3,
            stage_name="依賴鎖定與可重現配置",
            evidence_type="dependency_reproducibility",
            data=data,
        )
        logger.info(f"✅ Stage 3 完成: {evidence.compliant and '通過' or '失敗'}")
        return evidence
    def _file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    def _create_evidence(
        self,
        stage: int,
        stage_name: str,
        evidence_type: str,
        data: Dict[str, Any],
    ) -> VerificationEvidence:
        """Create verification evidence"""
        import json
        data_str = json.dumps(data, sort_keys=True, default=str)
        verification_hash, reproducible_hash = self.hash_manager.compute_dual_hash(
            data_str, f"stage{stage}"
        )
        # Save evidence file
        evidence_file = (
            self.evidence_dir / f"stage{stage:02d}-{evidence_type.replace(' ', '_')}.json"
        )
        with open(evidence_file, "w") as f:
            json.dump(
                {
                    "verification_hash": verification_hash,
                    "reproducible_hash": reproducible_hash,
                    "data": data,
                    "artifacts": [],
                    "stage": stage,
                    "stage_name": stage_name,
                    "evidence_type": evidence_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                f,
                indent=2,
                default=str,
            )
        evidence = VerificationEvidence(
            stage=stage,
            stage_name=stage_name,
            evidence_type=evidence_type,
            data=data,
            hash_value=verification_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
            artifacts=[str(evidence_file)],
            compliant=self._check_compliance(data),
            rollback_available=True,
            reproducible=True,
        )
        return evidence
    def _check_compliance(self, data: Dict[str, Any]) -> bool:
        """Check if Stage 3 passed compliance"""
        # Check if there are any HIGH severity dependency issues
        high_severity_issues = [
            check for check in data["dependency_checks"] if check["severity"] == "HIGH"
        ]
        return len(high_severity_issues) == 0