#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: stage2_schema_semantic
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Supply Chain Verification - Stage 2: Schema/Semantic Validation
This module handles schema and semantic verification for Kubernetes resources.
"""
# MNGA-002: Import organization needs review
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import yaml
from .hash_manager import HashManager
from .supply_chain_types import VerificationEvidence
# Configure logging
logger = logging.getLogger(__name__)
class Stage2SchemaSemanticVerifier:
    """Verifier for Stage 2: Schema/Semantic Validation"""
    def __init__(self, repo_path: Path, evidence_dir: Path, hash_manager: HashManager):
        """
        Initialize Stage 2 verifier
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
        Execute Stage 2: Schema/Semantic validation
        Returns:
            VerificationEvidence with validation results
        """
        logger.info("🔍 Stage 2: Schema/語意驗證開始")
        data = {
            "k8s_resources": [],
            "helm_charts": [],
            "semantic_violations": [],
            "policy_violations": [],
        }
        # Kubernetes 資源驗證
        k8s_patterns = ["*.yaml", "*.yml"]
        for pattern in k8s_patterns:
            for k8s_file in self.repo_path.rglob(pattern):
                if any(
                    skip in str(k8s_file)
                    for skip in [".git", "__pycache__", "node_modules"]
                ):
                    continue
                try:
                    with open(k8s_file, "r") as f:
                        docs = list(yaml.safe_load_all(f))
                    for i, doc in enumerate(docs):
                        if not doc:
                            continue
                        if "apiVersion" in doc and "kind" in doc:
                            resource = {
                                "file": str(k8s_file.relative_to(self.repo_path)),
                                "index": i,
                                "apiVersion": doc["apiVersion"],
                                "kind": doc["kind"],
                                "metadata": doc.get("metadata", {}),
                                "violations": [],
                            }
                            # 語意驗證
                            if doc["kind"] in [
                                "Deployment",
                                "StatefulSet",
                                "DaemonSet",
                            ]:
                                spec = (
                                    doc.get("spec", {})
                                    .get("template", {})
                                    .get("spec", {})
                                )
                                containers = spec.get("containers", [])
                                for j, container in enumerate(containers):
                                    # 檢查 resource limits
                                    if "resources" not in container:
                                        resource["violations"].append(
                                            {
                                                "container_index": j,
                                                "violation": "missing_resources",
                                                "severity": "HIGH",
                                            }
                                        )
                                    elif "limits" not in container.get("resources", {}):
                                        resource["violations"].append(
                                            {
                                                "container_index": j,
                                                "violation": "missing_resource_limits",
                                                "severity": "MEDIUM",
                                            }
                                        )
                                    # 檢查 image tag
                                    image = container.get("image", "")
                                    if ":latest" in image or ":" not in image:
                                        resource["violations"].append(
                                            {
                                                "container_index": j,
                                                "violation": "using_latest_tag",
                                                "image": image,
                                                "severity": "HIGH",
                                            }
                                        )
                                    # 檢查 security context
                                    if (
                                        "securityContext" not in container
                                        and "securityContext" not in spec
                                    ):
                                        resource["violations"].append(
                                            {
                                                "container_index": j,
                                                "violation": "missing_security_context",
                                                "severity": "MEDIUM",
                                            }
                                        )
                            data["k8s_resources"].append(resource)
                            # 收集違規
                            for violation in resource["violations"]:
                                if violation["severity"] == "HIGH":
                                    data["semantic_violations"].append(
                                        {
                                            "file": resource["file"],
                                            "violation": violation["violation"],
                                            "severity": "HIGH",
                                        }
                                    )
                except Exception as e:
                    logger.warning(f"無法處理 {k8s_file}: {e}")
        evidence = self._create_evidence(
            stage=2,
            stage_name="Schema/語意驗證",
            evidence_type="schema_validation",
            data=data,
        )
        logger.info(f"✅ Stage 2 完成: {evidence.compliant and '通過' or '失敗'}")
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
        """Check if Stage 2 passed compliance"""
        # Fail if there are HIGH severity semantic violations
        high_severity_violations = [
            v for v in data["semantic_violations"] if v["severity"] == "HIGH"
        ]
        return len(high_severity_violations) == 0