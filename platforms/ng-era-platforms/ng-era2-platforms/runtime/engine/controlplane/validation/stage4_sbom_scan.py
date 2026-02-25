#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: stage4_sbom_scan
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Supply Chain Verification - Stage 4: SBOM + Vulnerability/Secrets Scanning
This module handles SBOM generation and security scanning.
"""
# MNGA-002: Import organization needs review
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from .hash_manager import HashManager
from .supply_chain_types import VerificationEvidence
# Configure logging
logger = logging.getLogger(__name__)
class Stage4SbomScanVerifier:
    """Verifier for Stage 4: SBOM + Vulnerability/Secrets Scanning"""
    def __init__(self, repo_path: Path, evidence_dir: Path, hash_manager: HashManager):
        """
        Initialize Stage 4 verifier
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
        Execute Stage 4: SBOM generation and security scanning
        Returns:
            VerificationEvidence with validation results
        """
        logger.info("🔍 Stage 4: SBOM + 漏洞/Secrets 掃描開始")
        data = {
            "sbom": self._generate_sbom(),
            "vulnerabilities": self._scan_vulnerabilities(),
            "secrets": self._scan_secrets(),
            "malware": self._scan_malware(),
        }
        evidence = self._create_evidence(
            stage=4,
            stage_name="SBOM + 漏洞/Secrets 掃描",
            evidence_type="security_scan",
            data=data,
        )
        logger.info(f"✅ Stage 4 完成: {evidence.compliant and '通過' or '失敗'}")
        return evidence
    def _generate_sbom(self) -> Dict[str, Any]:
        """生成軟體物料清單（SBOM）"""
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": {
                    "type": "application",
                    "name": "machine-native-ops-aaps",
                    "version": "1.0.0",
                    "supplier": {"name": "MachineNativeOps"},
                },
            },
            "components": [],
        }
        # 掃描依賴
        dependencies = []
        # Python 依賴
        if (self.repo_path / "requirements.txt").exists():
            with open(self.repo_path / "requirements.txt") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split("==")
                        if len(parts) >= 1:
                            name = parts[0].strip()
                            version = parts[1].strip() if len(parts) > 1 else "unknown"
                            dependencies.append(
                                {
                                    "type": "library",
                                    "name": name,
                                    "version": version,
                                    "purl": f"pkg:pypi/{name}@{version}",
                                    "language": "python",
                                }
                            )
        # Go 依賴
        if (self.repo_path / "go.mod").exists():
            try:
                with open(self.repo_path / "go.mod") as f:
                    content = f.read()
                    # 簡單解析 go.mod
                    for line in content.split("\n"):
                        if line.strip().startswith("require ") or (
                            line.strip() and not line.startswith("\t") and " " in line
                        ):
                            parts = line.strip().split()
                            if len(parts) >= 2 and not parts[0].startswith("//"):
                                name = parts[0].strip()
                                version = parts[1].strip().replace("v", "")
                                dependencies.append(
                                    {
                                        "type": "library",
                                        "name": name,
                                        "version": version,
                                        "purl": f"pkg:golang/{name}@{version}",
                                        "language": "go",
                                    }
                                )
            except Exception as e:
                logger.warning(f"無法解析 go.mod: {e}")
        # Node.js 依賴
        if (self.repo_path / "package.json").exists():
            try:
                with open(self.repo_path / "package.json") as f:
                    package_data = json.load(f)
                    deps = package_data.get("dependencies", {})
                    for name, version in deps.items():
                        dependencies.append(
                            {
                                "type": "library",
                                "name": name,
                                "version": version.replace("^", ""),
                                "purl": f'pkg:npm/{name}@{version.replace("^", "")}',
                                "language": "javascript",
                            }
                        )
            except Exception as e:
                logger.warning(f"無法解析 package.json: {e}")
        sbom["components"] = dependencies
        return sbom
    def _scan_vulnerabilities(self) -> List[Dict[str, Any]]:
        """掃描漏洞（模擬 Trivy/Grype）"""
        # 模擬一些常見漏洞
        simulated_vulns = [
            {
                "id": "CVE-2023-1234",
                "severity": "HIGH",
                "component": "requests",
                "version": "2.25.0",
                "description": "URL parsing vulnerability",
                "fixed_in": "2.25.1",
            },
            {
                "id": "CVE-2023-5678",
                "severity": "MEDIUM",
                "component": "urllib3",
                "version": "1.26.0",
                "description": "Certificate validation bypass",
                "fixed_in": "1.26.5",
            },
        ]
        return simulated_vulns
    def _scan_secrets(self) -> List[Dict[str, Any]]:
        """掃描 Secrets（模擬 gitleaks）"""
        secrets = []
        secret_patterns = {
            "aws_access_key": r"AKIA[0-9A-Z]{16}",
            "aws_secret_key": r"[A-Za-z0-9/+=]{40}",
            "github_token": r"ghp_[A-Za-z0-9_]{36,255}",
            "github_pat": r"github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9_]{59}",
            "private_key": r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
            "api_key": r'[Aa][Pp][Ii]_[Kk][Ee][Yy].*["\']?[A-Za-z0-9_]{16,}["\']?',
            "password": r'[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd].*["\']?[A-Za-z0-9_@#$%^&*]{8,}["\']?',
        }
        # 掃描所有文本文件
        text_extensions = [".py", ".yaml", ".yml", ".json", ".sh", ".md", ".txt"]
        for ext in text_extensions:
            for file_path in self.repo_path.rglob(f"*{ext}"):
                if any(
                    skip in str(file_path)
                    for skip in [".git", "__pycache__", "node_modules"]
                ):
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        lines = content.split("\n")
                        for line_num, line in enumerate(lines, 1):
                            for secret_type, pattern in secret_patterns.items():
                                if re.search(pattern, line, re.IGNORECASE):
                                    # 檢查是否是註釋或示例
                                    if not any(
                                        skip in line.lower()
                                        for skip in [
                                            "#",
                                            "//",
                                            "example",
                                            "dummy",
                                            "fake",
                                            "test",
                                        ]
                                    ):
                                        secrets.append(
                                            {
                                                "file": str(
                                                    file_path.relative_to(
                                                        self.repo_path
                                                    )
                                                ),
                                                "line": line_num,
                                                "type": secret_type,
                                                "content": (
                                                    line.strip()[:100] + "..."
                                                    if len(line.strip()) > 100
                                                    else line.strip()
                                                ),
                                                "severity": (
                                                    "CRITICAL"
                                                    if "key" in secret_type
                                                    else "HIGH"
                                                ),
                                            }
                                        )
                except Exception as e:
                    logger.warning(f"無法掃描 {file_path}: {e}")
        return secrets
    def _scan_malware(self) -> List[Dict[str, Any]]:
        """掃描惡意程式（模擬 ClamAV/YARA）"""
        malware = []
        # 檢查可疑的檔案模式
        suspicious_patterns = {
            "suspicious_executable": r"\.(exe|bat|cmd|scr|pif)$",
            "obfuscated_code": r"(eval|base64_decode|chr\(|ord\()[&quot;'][A-Za-z0-9+/=]{20,}[&quot;']",
            "suspicious_network": r"(curl|wget).*http.*\|.*sh",
            "reverse_shell": r"(bash -i|/bin/sh|nc -e|python -c).*[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",
        }
        # 掃描所有檔案
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file() and any(
                skip not in str(file_path) for skip in [".git", "__pycache__"]
            ):
                file_name = file_path.name.lower()
                for pattern_type, pattern in suspicious_patterns.items():
                    if re.search(pattern, file_name, re.IGNORECASE):
                        malware.append(
                            {
                                "file": str(file_path.relative_to(self.repo_path)),
                                "type": pattern_type,
                                "severity": "HIGH",
                            }
                        )
                        break
                # 檢查文件內容
                if file_path.suffix in [".py", ".sh", ".yaml", ".yml"]:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            lines = content.split("\n")
                            for line_num, line in enumerate(lines, 1):
                                for (
                                    pattern_type,
                                    pattern,
                                ) in suspicious_patterns.items():
                                    if (
                                        pattern_type != "suspicious_executable"
                                    ):  # 已經檢查了檔名
                                        if re.search(pattern, line, re.IGNORECASE):
                                            malware.append(
                                                {
                                                    "file": str(
                                                        file_path.relative_to(
                                                            self.repo_path
                                                        )
                                                    ),
                                                    "line": line_num,
                                                    "type": pattern_type,
                                                    "content": line.strip()[:100],
                                                    "severity": "HIGH",
                                                }
                                            )
                                            break
                    except Exception:
                        pass  # 忽略無法讀取的檔案
        return malware
    def _create_evidence(
        self,
        stage: int,
        stage_name: str,
        evidence_type: str,
        data: Dict[str, Any],
    ) -> VerificationEvidence:
        """Create verification evidence"""
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
        """Check if Stage 4 passed compliance"""
        # Check for CRITICAL severity issues
        critical_secrets = [
            s for s in data["secrets"] if s["severity"] == "CRITICAL"
        ]
        critical_malware = [
            m for m in data["malware"] if m["severity"] == "CRITICAL"
        ]
        return len(critical_secrets) == 0 and len(critical_malware) == 0