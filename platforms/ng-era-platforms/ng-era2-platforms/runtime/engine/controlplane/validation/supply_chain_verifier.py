#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: supply_chain_verifier
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Supply Chain Verification - Main Coordinator
This module is the main coordinator for the supply chain verification system.
It integrates all stage verifiers and orchestrates the complete verification workflow.
"""
# MNGA-002: Import organization needs review
import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [SupplyChainVerifier] - %(message)s",
)
logger = logging.getLogger(__name__)
from .hash_manager import HashManager  # noqa: E402
from .stage1_lint_format import Stage1LintFormatVerifier  # noqa: E402
from .stage2_schema_semantic import Stage2SchemaSemanticVerifier  # noqa: E402
from .stage3_dependency import Stage3DependencyVerifier  # noqa: E402
from .stage4_sbom_scan import Stage4SbomScanVerifier  # noqa: E402
from .stage5_sign_attestation import Stage5SignAttestationVerifier  # noqa: E402
from .stage6_admission_policy import Stage6AdmissionPolicyVerifier  # noqa: E402
from .stage7_runtime_monitoring import Stage7RuntimeMonitoringVerifier  # noqa: E402
from .supply_chain_types import ChainVerificationResult, VerificationEvidence  # noqa: E402


class UltimateSupplyChainVerifier:
    """Ultimate Supply Chain Verifier - Enterprise-grade complete implementation"""
    def __init__(self, repo_path: str = "."):
        """
        Initialize the supply chain verifier
        Args:
            repo_path: Path to the repository to verify
        """
        self.repo_path = Path(repo_path)
        self.evidence_dir = self.repo_path / "outputs" / "supply-chain-evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        # Initialize hash manager
        self.hash_manager = HashManager()
        # Evidence chain and audit trail
        self.evidence_chain: List[VerificationEvidence] = []
        self.audit_trail: List[Dict[str, Any]] = []
        # Initialize all stage verifiers
        self.stage1_verifier = Stage1LintFormatVerifier(
            self.repo_path, self.evidence_dir, self.hash_manager
        )
        self.stage2_verifier = Stage2SchemaSemanticVerifier(
            self.repo_path, self.evidence_dir, self.hash_manager
        )
        self.stage3_verifier = Stage3DependencyVerifier(
            self.repo_path, self.evidence_dir, self.hash_manager
        )
        self.stage4_verifier = Stage4SbomScanVerifier(
            self.repo_path, self.evidence_dir, self.hash_manager
        )
        self.stage5_verifier = Stage5SignAttestationVerifier(
            self.repo_path, self.evidence_dir, self.hash_manager
        )
        self.stage6_verifier = Stage6AdmissionPolicyVerifier(
            self.repo_path, self.evidence_dir, self.hash_manager
        )
        self.stage7_verifier = Stage7RuntimeMonitoringVerifier(
            self.repo_path, self.evidence_dir, self.hash_manager
        )
        # Compliance thresholds
        self.compliance_thresholds = {
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 5,
            "secrets_leakage": 0,
            "signature_verification": 100,
            "policy_compliance": 95,
        }
    def run_complete_verification(self) -> ChainVerificationResult:
        """
        Execute complete seven-stage verification
        Returns:
            ChainVerificationResult with verification summary
        """
        logger.info("🚀 開始執行完整供應鏈驗證流程")
        try:
            # Execute all seven stages
            evidence1 = self.stage1_verifier.verify()
            self._add_to_chain(evidence1)
            evidence2 = self.stage2_verifier.verify()
            self._add_to_chain(evidence2)
            evidence3 = self.stage3_verifier.verify()
            self._add_to_chain(evidence3)
            evidence4 = self.stage4_verifier.verify()
            self._add_to_chain(evidence4)
            # Update stage 5 with audit trail and evidence chain
            self.stage5_verifier.set_audit_trail(self.audit_trail)
            evidence5 = self.stage5_verifier.verify()
            self._add_to_chain(evidence5)
            evidence6 = self.stage6_verifier.verify()
            self._add_to_chain(evidence6)
            # Update stage 7 with audit trail and evidence chain
            self.stage7_verifier.set_audit_trail(self.audit_trail)
            self.stage7_verifier.set_evidence_chain(self.evidence_chain)
            evidence7 = self.stage7_verifier.verify()
            self._add_to_chain(evidence7)
            # Calculate results
            passed_stages = sum(1 for e in self.evidence_chain if e.compliant)
            failed_stages = sum(1 for e in self.evidence_chain if not e.compliant)
            warning_stages = len(self.evidence_chain) - passed_stages - failed_stages
            overall_status = "PASS" if failed_stages == 0 else "FAIL"
            compliance_score = (passed_stages / len(self.evidence_chain)) * 100
            # Generate recommendations
            recommendations = self._generate_recommendations()
            result = ChainVerificationResult(
                total_stages=len(self.evidence_chain),
                passed_stages=passed_stages,
                failed_stages=failed_stages,
                warning_stages=warning_stages,
                overall_status=overall_status,
                final_hash=self._compute_final_chain_hash(),
                evidence_chain=self.evidence_chain,
                audit_trail=self.audit_trail,
                compliance_score=compliance_score,
                recommendations=recommendations,
            )
            # Save final report
            self._save_final_report(result)
            logger.info(
                f"✅ 完整驗證流程完成: {overall_status} ({compliance_score:.1f}%)"
            )
            return result
        except Exception as e:
            logger.error(f"❌ 驗證流程失敗: {e}")
            raise
    def _add_to_chain(self, evidence: VerificationEvidence) -> None:
        """Add evidence to chain and update audit trail"""
        self.evidence_chain.append(evidence)
        # Record audit trail
        audit_entry = {
            "timestamp": evidence.timestamp,
            "stage": evidence.stage,
            "action": "evidence_created",
            "hash": evidence.hash_value,
            "artifacts_count": len(evidence.artifacts),
            "compliant": evidence.compliant,
        }
        self.audit_trail.append(audit_entry)
    def _compute_final_chain_hash(self) -> str:
        """Compute final chain hash"""
        import hashlib
        chain_data = ""
        for evidence in self.evidence_chain:
            chain_data += f"{evidence.stage}:{evidence.hash_value}:"
        return hashlib.sha3_512(chain_data.encode()).hexdigest()
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        for evidence in self.evidence_chain:
            if not evidence.compliant:
                if evidence.stage == 1:
                    recommendations.append("修復 YAML/JSON 格式錯誤和編碼問題")
                elif evidence.stage == 2:
                    recommendations.append(
                        "修復 K8s 資源的語意違規（添加 resource limits，避免 latest tag）"
                    )
                elif evidence.stage == 3:
                    recommendations.append("確保所有依賴都有對應的 lock 檔案")
                elif evidence.stage == 4:
                    recommendations.append("修復發現的漏洞和 secrets 洩露問題")
                elif evidence.stage == 5:
                    recommendations.append("確保所有 artifacts 都有有效簽章")
                elif evidence.stage == 6:
                    recommendations.append("修復 OPA/Kyverno 政策違規問題")
                elif evidence.stage == 7:
                    recommendations.append("檢查並處理 runtime 安全事件")
        return recommendations
    def _save_final_report(self, result: ChainVerificationResult) -> None:
        """Save final report"""
        report = {
            "summary": {
                "total_stages": result.total_stages,
                "passed_stages": result.passed_stages,
                "failed_stages": result.failed_stages,
                "warning_stages": result.warning_stages,
                "overall_status": result.overall_status,
                "compliance_score": result.compliance_score,
                "final_hash": result.final_hash,
            },
            "evidence_chain": [asdict(e) for e in result.evidence_chain],
            "audit_trail": result.audit_trail,
            "recommendations": result.recommendations,
            "verification_completed": datetime.now(timezone.utc).isoformat(),
        }
        report_file = self.evidence_dir / "supply-chain-verification-final-report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        # Also generate Markdown report
        self._generate_markdown_report(report, report_file.with_suffix(".md"))
    def _generate_markdown_report(
        self, report: Dict[str, Any], output_file: Path
    ) -> None:
        """Generate Markdown format report"""
        summary = report["summary"]
        md_content = f"""# 🛡️ MachineNativeOps 供應鏈驗證最終報告
## 📊 執行摘要
- **總階段數**: {summary['total_stages']}
- **通過階段**: {summary['passed_stages']}
- **失敗階段**: {summary['failed_stages']}
- **警告階段**: {summary['warning_stages']}
- **整體狀態**: {'✅ PASS' if summary['overall_status'] == 'PASS' else '❌ FAIL'}
- **合規性分數**: {summary['compliance_score']:.1f}%
- **最終雜湊**: `{summary['final_hash']}`
## 🔍 階段詳細結果
"""
        for evidence in report["evidence_chain"]:
            status_icon = "✅" if evidence["compliant"] else "❌"
            md_content += f"""
### {status_icon} Stage {evidence['stage']}: {evidence['stage_name']}
- **證據類型**: {evidence['evidence_type']}
- **雜湊值**: `{evidence['hash_value']}`
- **時間戳**: {evidence['timestamp']}
- **可回滾**: {'是' if evidence['rollback_available'] else '否'}
- **可重現**: {'是' if evidence['reproducible'] else '否'}
"""
        if report["recommendations"]:
            md_content += "## 💡 改進建議\n\n"
            for i, rec in enumerate(report["recommendations"], 1):
                md_content += f"{i}. {rec}\n"
        md_content += f"""
## 📝 完整審計軌跡
共 {len(report['audit_trail'])} 個審計記錄，詳細請參考 JSON 報告。
---
#*報告生成時間**: {report['verification_completed']}
#*驗證工具**: MachineNativeOps Supply Chain Verifier v1.0
#*合規性標準**: 企業級供應鏈安全框架
"""
        with open(output_file, "w") as f:
            f.write(md_content)
def main():
    """Main execution function"""
    import sys
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    verifier = UltimateSupplyChainVerifier(repo_path)
    try:
        result = verifier.run_complete_verification()
        print(f"\n{'='*80}")
        print("🛡️ MachineNativeOps 供應鏈驗證完成")
        print(f"{'='*80}")
        print(f"📊 狀態: {result.overall_status}")
        print(f"📈 合規性: {result.compliance_score:.1f}%")
        print(f"🔗 最終雜湊: {result.final_hash}")
        print(f"{'='*80}")
        if result.recommendations:
            print("\n💡 改進建議:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"   {i}. {rec}")
        return 0 if result.overall_status == "PASS" else 1
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        return 1
if __name__ == "__main__":
    exit(main())