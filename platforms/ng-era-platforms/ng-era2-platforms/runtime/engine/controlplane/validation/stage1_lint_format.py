#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: stage1_lint_format
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Supply Chain Verification - Stage 1: Lint/Format Validation
This module handles lint and format verification for YAML, JSON, and Python files.
"""
# MNGA-002: Import organization needs review
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import yaml
from .hash_manager import HashManager
from .supply_chain_types import VerificationEvidence
# Configure logging
logger = logging.getLogger(__name__)
class Stage1LintFormatVerifier:
    """Verifier for Stage 1: Lint/Format Validation"""
    def __init__(self, repo_path: Path, evidence_dir: Path, hash_manager: HashManager):
        """
        Initialize Stage 1 verifier
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
        Execute Stage 1: Lint/Format validation
        Returns:
            VerificationEvidence with validation results
        """
        logger.info("🔍 Stage 1: Lint/格式驗證開始")
        data = {
            "yaml_files": [],
            "json_files": [],
            "python_files": [],
            "encoding_issues": [],
            "format_violations": [],
        }
        # YAML 格式驗證
        yaml_files = list(self.repo_path.rglob("*.yaml")) + list(
            self.repo_path.rglob("*.yml")
        )
        for yaml_file in yaml_files:
            if any(
                skip in str(yaml_file)
                for skip in [".git", "__pycache__", "node_modules"]
            ):
                continue
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    list(yaml.safe_load_all(content))
                # 檢查格式問題
                format_issues = []
                if "\t" in content:  # 使用 tab 而非 space
                    format_issues.append("uses_tabs")
                if content.strip() != content:  # 前後空白
                    format_issues.append("leading_trailing_whitespace")
                data["yaml_files"].append(
                    {
                        "file": str(yaml_file.relative_to(self.repo_path)),
                        "status": "valid" if not format_issues else "format_issues",
                        "issues": format_issues,
                        "size": len(content),
                    }
                )
            except yaml.YAMLError as e:
                data["yaml_files"].append(
                    {
                        "file": str(yaml_file.relative_to(self.repo_path)),
                        "status": "invalid",
                        "error": str(e),
                    }
                )
        # JSON 格式驗證
        json_files = list(self.repo_path.rglob("*.json"))
        for json_file in json_files:
            if any(skip in str(json_file) for skip in [".git", "node_modules"]):
                continue
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    json.load(f)
                data["json_files"].append(
                    {
                        "file": str(json_file.relative_to(self.repo_path)),
                        "status": "valid",
                    }
                )
            except json.JSONDecodeError as e:
                data["json_files"].append(
                    {
                        "file": str(json_file.relative_to(self.repo_path)),
                        "status": "invalid",
                        "error": str(e),
                    }
                )
        # Python 基本格式檢查
        py_files = list(self.repo_path.rglob("*.py"))
        for py_file in py_files:
            if any(skip in str(py_file) for skip in [".git", "__pycache__"]):
                continue
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                # 基本語法檢查
                compile(content, str(py_file), "exec")
                # 檢查基本格式
                issues = []
                if content.count("\t") > 0:
                    issues.append("tabs_in_indentation")
                if content and not content.endswith("\n"):
                    issues.append("no_final_newline")
                data["python_files"].append(
                    {
                        "file": str(py_file.relative_to(self.repo_path)),
                        "status": "valid" if not issues else "format_issues",
                        "issues": issues,
                        "lines": content.count("\n"),
                    }
                )
            except SyntaxError as e:
                data["python_files"].append(
                    {
                        "file": str(py_file.relative_to(self.repo_path)),
                        "status": "syntax_error",
                        "error": str(e),
                    }
                )
        evidence = self._create_evidence(
            stage=1,
            stage_name="Lint/格式驗證",
            evidence_type="format_validation",
            data=data,
        )
        logger.info(f"✅ Stage 1 完成: {evidence.compliant and '通過' or '失敗'}")
        return evidence
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
        """Check if Stage 1 passed compliance"""
        yaml_invalid = any(f["status"] == "invalid" for f in data["yaml_files"])
        json_invalid = any(f["status"] == "invalid" for f in data["json_files"])
        py_syntax_error = any(f["status"] == "syntax_error" for f in data["python_files"])
        return not (yaml_invalid or json_invalid or py_syntax_error)