#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_supply_chain_types
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Unit tests for supply_chain_types.py
Tests type definitions and data structures.
"""
import unittest
from datetime import datetime, timezone
from dataclasses import asdict
import sys
from pathlib import Path
# Add repository root to path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
# Import from the validation package
from controlplane.validation.supply_chain_types import VerificationStage, VerificationEvidence, ChainVerificationResult
class TestVerificationStage(unittest.TestCase):
    """Test VerificationStage enum"""
    def test_stage_values(self):
        """Test that all stage values are correctly defined"""
        self.assertEqual(VerificationStage.LINT_FORMAT.value, 1)
        self.assertEqual(VerificationStage.SCHEMA_SEMANTIC.value, 2)
        self.assertEqual(VerificationStage.DEPENDENCY_REPRODUCIBLE.value, 3)
        self.assertEqual(VerificationStage.SBOM_VULNERABILITY_SCAN.value, 4)
        self.assertEqual(VerificationStage.SIGN_ATTESTATION.value, 5)
        self.assertEqual(VerificationStage.ADMISSION_POLICY.value, 6)
        self.assertEqual(VerificationStage.RUNTIME_MONITORING.value, 7)
    def test_stage_count(self):
        """Test that there are exactly 7 stages"""
        self.assertEqual(len(VerificationStage), 7)
class TestVerificationEvidence(unittest.TestCase):
    """Test VerificationEvidence dataclass"""
    def test_evidence_creation(self):
        """Test creating verification evidence"""
        evidence = VerificationEvidence(
            stage=1,
            stage_name="Lint/格式驗證",
            evidence_type="format_validation",
            data={"yaml_files": [], "json_files": []},
            hash_value="abc123",
            timestamp=datetime.now(timezone.utc).isoformat(),
            artifacts=["evidence.json"],
            compliant=True,
            rollback_available=True,
            reproducible=True,
        )
        self.assertEqual(evidence.stage, 1)
        self.assertEqual(evidence.stage_name, "Lint/格式驗證")
        self.assertTrue(evidence.compliant)
        self.assertTrue(evidence.rollback_available)
        self.assertTrue(evidence.reproducible)
    def test_evidence_serialization(self):
        """Test serializing evidence to dict"""
        evidence = VerificationEvidence(
            stage=1,
            stage_name="Test Stage",
            evidence_type="test",
            data={"key": "value"},
            hash_value="hash123",
            timestamp="2024-01-01T00:00:00Z",
            artifacts=["file1.json"],
            compliant=True,
            rollback_available=False,
            reproducible=True,
        )
        evidence_dict = asdict(evidence)
        self.assertEqual(evidence_dict["stage"], 1)
        self.assertEqual(evidence_dict["stage_name"], "Test Stage")
        self.assertEqual(evidence_dict["hash_value"], "hash123")
class TestChainVerificationResult(unittest.TestCase):
    """Test ChainVerificationResult dataclass"""
    def test_result_creation(self):
        """Test creating verification result"""
        result = ChainVerificationResult(
            total_stages=7,
            passed_stages=7,
            failed_stages=0,
            warning_stages=0,
            overall_status="PASS",
            final_hash="final123",
            evidence_chain=[],
            audit_trail=[],
            compliance_score=100.0,
            recommendations=[],
        )
        self.assertEqual(result.total_stages, 7)
        self.assertEqual(result.passed_stages, 7)
        self.assertEqual(result.failed_stages, 0)
        self.assertEqual(result.overall_status, "PASS")
        self.assertEqual(result.compliance_score, 100.0)
    def test_result_with_failures(self):
        """Test result with failed stages"""
        result = ChainVerificationResult(
            total_stages=7,
            passed_stages=5,
            failed_stages=2,
            warning_stages=0,
            overall_status="FAIL",
            final_hash="final456",
            evidence_chain=[],
            audit_trail=[],
            compliance_score=71.4,
            recommendations=["Fix issue 1", "Fix issue 2"],
        )
        self.assertEqual(result.failed_stages, 2)
        self.assertEqual(result.overall_status, "FAIL")
        self.assertEqual(len(result.recommendations), 2)
    def test_result_serialization(self):
        """Test serializing result to dict"""
        result = ChainVerificationResult(
            total_stages=7,
            passed_stages=7,
            failed_stages=0,
            warning_stages=0,
            overall_status="PASS",
            final_hash="final789",
            evidence_chain=[],
            audit_trail=[],
            compliance_score=100.0,
            recommendations=[],
        )
        result_dict = asdict(result)
        self.assertEqual(result_dict["total_stages"], 7)
        self.assertEqual(result_dict["overall_status"], "PASS")
        self.assertEqual(result_dict["compliance_score"], 100.0)
if __name__ == "__main__":
    unittest.main()