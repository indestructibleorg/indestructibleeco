#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_integration
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Integration tests for the complete supply chain verification system.
Tests the interaction between all components and the complete verification workflow.
"""
# MNGA-002: Import organization needs review
import unittest
import tempfile  # noqa: E402
import shutil  # noqa: E402
from pathlib import Path  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
# Add repository root to path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
# Import from the validation package
from controlplane.validation.supply_chain_verifier import UltimateSupplyChainVerifier  # noqa: E402
from controlplane.validation.supply_chain_types import ChainVerificationResult  # noqa: E402
class TestCompleteVerification(unittest.TestCase):
    """Test complete verification workflow"""
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        # Create test repository structure
        self._create_test_repo()
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    def _create_test_repo(self):
        """Create a test repository with various files"""
        # Create valid YAML files
        (Path(self.test_dir) / "config.yaml").write_text(
            "app:\n  name: test\n  port: 8080\n"
        )
        # Create valid JSON files
        (Path(self.test_dir) / "package.json").write_text(
            '{"name": "test", "version": "1.0.0"}\n'
        )
        # Create valid Python files
        (Path(self.test_dir) / "app.py").write_text(
            '"""Main application"""\n\ndef main():\n    print("Hello")\n\nif __name__ == "__main__":\n    main()\n'
        )
        # Create requirements.txt
        (Path(self.test_dir) / "requirements.txt").write_text(
            "requests==2.28.0\npyyaml==6.0\n"
        )
    def test_complete_verification(self):
        """Test complete verification workflow"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Verify result structure
        self.assertIsInstance(result, ChainVerificationResult)
        self.assertEqual(result.total_stages, 7)
        self.assertEqual(len(result.evidence_chain), 7)
        # Verify audit trail
        self.assertGreater(len(result.audit_trail), 0)
        # Verify final hash is generated
        self.assertIsNotNone(result.final_hash)
        self.assertGreater(len(result.final_hash), 0)
    def test_all_stages_executed(self):
        """Test that all 7 stages are executed"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Check all stages are present
        stages = [e.stage for e in result.evidence_chain]
        self.assertEqual(stages, [1, 2, 3, 4, 5, 6, 7])
    def test_evidence_chain_integrity(self):
        """Test that evidence chain maintains integrity"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Verify each evidence has required fields
        for evidence in result.evidence_chain:
            self.assertIsNotNone(evidence.stage)
            self.assertIsNotNone(evidence.stage_name)
            self.assertIsNotNone(evidence.evidence_type)
            self.assertIsNotNone(evidence.hash_value)
            self.assertIsNotNone(evidence.timestamp)
            self.assertIsNotNone(evidence.compliant)
    def test_audit_trail_consistency(self):
        """Test that audit trail is consistent with evidence chain"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Audit trail should have one entry per evidence
        self.assertEqual(len(result.audit_trail), len(result.evidence_chain))
        # Verify audit entries match evidence
        for audit_entry, evidence in zip(result.audit_trail, result.evidence_chain):
            self.assertEqual(audit_entry["stage"], evidence.stage)
            self.assertEqual(audit_entry["hash"], evidence.hash_value)
    def test_compliance_score_calculation(self):
        """Test compliance score calculation"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Compliance score should be between 0 and 100
        self.assertGreaterEqual(result.compliance_score, 0)
        self.assertLessEqual(result.compliance_score, 100)
        # Should match passed_stages / total_stages
        expected_score = (result.passed_stages / result.total_stages) * 100
        self.assertAlmostEqual(result.compliance_score, expected_score, places=1)
    def test_report_generation(self):
        """Test that verification reports are generated"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Check evidence directory exists
        evidence_dir = Path(self.test_dir) / "outputs" / "supply-chain-evidence"
        self.assertTrue(evidence_dir.exists())
        # Check for final report
        report_file = evidence_dir / "supply-chain-verification-final-report.json"
        self.assertTrue(report_file.exists())
        # Verify report content
        with report_file.open() as f:
            report = json.load(f)
            self.assertIn("summary", report)
            self.assertIn("evidence_chain", report)
            self.assertEqual(report["summary"]["total_stages"], 7)
    def test_markdown_report_generation(self):
        """Test that Markdown report is generated"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Check for Markdown report
        evidence_dir = Path(self.test_dir) / "outputs" / "supply-chain-evidence"
        md_report_file = evidence_dir / "supply-chain-verification-final-report.md"
        self.assertTrue(md_report_file.exists())
        # Verify report content
        content = md_report_file.read_text()
        self.assertIn("供應鏈驗證最終報告", content)
        self.assertIn("執行摘要", content)
    def test_stage4_sborn_generation(self):
        """Test that SBOM is generated in Stage 4"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Find Stage 4 evidence
        stage4_evidence = next(
            (e for e in result.evidence_chain if e.stage == 4), None
        )
        self.assertIsNotNone(stage4_evidence)
        # Verify SBOM data
        self.assertIn("sbom", stage4_evidence.data)
        sbom = stage4_evidence.data["sbom"]
        self.assertIn("bomFormat", sbom)
        self.assertIn("components", sbom)
    def test_stage5_signatures(self):
        """Test that signatures are verified in Stage 5"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Find Stage 5 evidence
        stage5_evidence = next(
            (e for e in result.evidence_chain if e.stage == 5), None
        )
        self.assertIsNotNone(stage5_evidence)
        # Verify signatures data
        self.assertIn("signatures", stage5_evidence.data)
        signatures = stage5_evidence.data["signatures"]
        self.assertGreater(len(signatures), 0)
    def test_stage7_traceability(self):
        """Test that traceability chain is built in Stage 7"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Find Stage 7 evidence
        stage7_evidence = next(
            (e for e in result.evidence_chain if e.stage == 7), None
        )
        self.assertIsNotNone(stage7_evidence)
        # Verify traceability data
        self.assertIn("traceability_chain", stage7_evidence.data)
        traceability = stage7_evidence.data["traceability_chain"]
        self.assertIn("total_stages", traceability)
        self.assertEqual(traceability["total_stages"], 7)
    def test_recommendations_generation(self):
        """Test that recommendations are generated for failed stages"""
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        result = verifier.run_complete_verification()
        # Recommendations should be a list
        self.assertIsInstance(result.recommendations, list)
        # If any stages failed, recommendations should be provided
        if result.failed_stages > 0:
            self.assertGreater(len(result.recommendations), 0)
class TestErrorHandling(unittest.TestCase):
    """Test error handling in verification workflow"""
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    def test_invalid_repository_path(self):
        """Test handling of invalid repository path"""
        # Use non-existent path
        verifier = UltimateSupplyChainVerifier(repo_path="/nonexistent/path")
        # Should not crash, but handle gracefully
        try:
            result = verifier.run_complete_verification()
            # If it succeeds, verify basic structure
            self.assertIsInstance(result, ChainVerificationResult)
        except Exception as e:
            # If it fails, verify it's a reasonable error
            self.assertIsInstance(e, (FileNotFoundError, OSError))
    def test_permission_error_handling(self):
        """Test handling of permission errors"""
        # This is a placeholder - actual permission error testing
        # would require creating files with restricted permissions
        pass
if __name__ == "__main__":
    unittest.main()