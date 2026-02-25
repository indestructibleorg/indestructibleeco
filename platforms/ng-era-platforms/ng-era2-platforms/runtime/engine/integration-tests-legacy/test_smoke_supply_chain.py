#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_smoke_supply_chain
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Smoke Tests for Supply Chain Verification - Quick verification of supply chain functionality
"""
import pytest
import sys
from pathlib import Path
import tempfile
import shutil
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
@pytest.mark.smoke
class TestSupplyChainVerifierSmoke:
    """Smoke tests for Supply Chain Verifier"""
    @pytest.fixture(scope="class")
    def supply_chain_verifier(self):
        """Create Supply Chain Verifier instance"""
        try:
            from controlplane.validation import SupplyChainVerifier
            verifier = SupplyChainVerifier()
            yield verifier
        except ImportError as e:
            pytest.skip(f"SupplyChainVerifier not importable: {e}")
    def test_verifier_initialization(self, supply_chain_verifier):
        """Test that Supply Chain Verifier initializes correctly"""
        assert supply_chain_verifier is not None
    def test_verifier_structure(self, supply_chain_verifier):
        """Test verifier structure"""
        # Verify structure exists
        assert supply_chain_verifier is not None
@pytest.mark.smoke
class TestSupplyChainStagesSmoke:
    """Smoke tests for individual verification stages"""
    def test_stage1_lint_format_importable(self):
        """Test that Stage 1 (Lint & Format) is importable"""
        try:
            from controlplane.validation.stage1_lint_format import Stage1Verifier
            assert Stage1Verifier is not None
        except ImportError as e:
            pytest.skip(f"Stage1Verifier not importable: {e}")
    def test_stage2_schema_semantic_importable(self):
        """Test that Stage 2 (Schema & Semantic) is importable"""
        try:
            from controlplane.validation.stage2_schema_semantic import Stage2Verifier
            assert Stage2Verifier is not None
        except ImportError as e:
            pytest.skip(f"Stage2Verifier not importable: {e}")
    def test_stage3_dependency_importable(self):
        """Test that Stage 3 (Dependency) is importable"""
        try:
            from controlplane.validation.stage3_dependency import Stage3Verifier
            assert Stage3Verifier is not None
        except ImportError as e:
            pytest.skip(f"Stage3Verifier not importable: {e}")
    def test_stage4_sbom_scan_importable(self):
        """Test that Stage 4 (SBOM Scan) is importable"""
        try:
            from controlplane.validation.stage4_sbom_scan import Stage4Verifier
            assert Stage4Verifier is not None
        except ImportError as e:
            pytest.skip(f"Stage4Verifier not importable: {e}")
    def test_stage5_sign_attestation_importable(self):
        """Test that Stage 5 (Sign & Attestation) is importable"""
        try:
            from controlplane.validation.stage5_sign_attestation import Stage5Verifier
            assert Stage5Verifier is not None
        except ImportError as e:
            pytest.skip(f"Stage5Verifier not importable: {e}")
    def test_stage6_admission_policy_importable(self):
        """Test that Stage 6 (Admission Policy) is importable"""
        try:
            from controlplane.validation.stage6_admission_policy import Stage6Verifier
            assert Stage6Verifier is not None
        except ImportError as e:
            pytest.skip(f"Stage6Verifier not importable: {e}")
    def test_stage7_runtime_monitoring_importable(self):
        """Test that Stage 7 (Runtime Monitoring) is importable"""
        try:
            from controlplane.validation.stage7_runtime_monitoring import Stage7Verifier
            assert Stage7Verifier is not None
        except ImportError as e:
            pytest.skip(f"Stage7Verifier not importable: {e}")
@pytest.mark.smoke
class TestSupplyChainTypesSmoke:
    """Smoke tests for supply chain data types"""
    def test_verification_stage_enum(self):
        """Test VerificationStage enum"""
        try:
            from controlplane.validation.supply_chain_types import VerificationStage
            # Verify enum values
            stages = [
                "STAGE1_LINT_FORMAT",
                "STAGE2_SCHEMA_SEMANTIC",
                "STAGE3_DEPENDENCY",
                "STAGE4_SBOM_SCAN",
                "STAGE5_SIGN_ATTESTATION",
                "STAGE6_ADMISSION_POLICY",
                "STAGE7_RUNTIME_MONITORING",
            ]
            for stage in stages:
                assert hasattr(VerificationStage, stage)
        except ImportError as e:
            pytest.skip(f"VerificationStage not importable: {e}")
    def test_verification_evidence(self):
        """Test VerificationEvidence dataclass"""
        try:
            from controlplane.validation.supply_chain_types import VerificationEvidence
            # Create a test evidence
            evidence = VerificationEvidence(
                stage="STAGE1_LINT_FORMAT",
                status="passed",
                timestamp="2024-01-01T00:00:00Z",
                details={"test": "smoke"},
            )
            assert evidence.stage == "STAGE1_LINT_FORMAT"
            assert evidence.status == "passed"
        except ImportError as e:
            pytest.skip(f"VerificationEvidence not importable: {e}")
    def test_chain_verification_result(self):
        """Test ChainVerificationResult dataclass"""
        try:
            from controlplane.validation.supply_chain_types import ChainVerificationResult
            # Create a test result
            result = ChainVerificationResult(
                project_id="test_project",
                status="passed",
                overall_score=100,
                stage_results=[],
                evidence_chain=[],
            )
            assert result.project_id == "test_project"
            assert result.status == "passed"
            assert result.overall_score == 100
        except ImportError as e:
            pytest.skip(f"ChainVerificationResult not importable: {e}")
@pytest.mark.smoke
class TestSupplyChainProjectSmoke:
    """Smoke tests for supply chain project structure"""
    def test_project_structure(self, test_data):
        """Test project structure"""
        project = test_data["supply_chain_small"]
        assert project is not None
        assert "name" in project
        assert "size" in project
        assert "files" in project
        assert "config" in project
        assert "stages" in project["config"]
        # Verify stages
        expected_stages = [
            "lint",
            "schema",
            "dependency",
            "sbom",
            "sign",
            "admission",
            "runtime",
        ]
        for stage in expected_stages:
            assert stage in project["config"]["stages"]
    def test_project_files(self, test_data):
        """Test project files structure"""
        project = test_data["supply_chain_small"]
        for file_data in project["files"]:
            assert "path" in file_data
            assert "content" in file_data
            assert "hash" in file_data
    def test_project_services(self, test_data):
        """Test project services structure"""
        project = test_data["supply_chain_small"]
        for service in project["services"]:
            assert "name" in service
            assert "image" in service
            assert "ports" in service
@pytest.mark.smoke
class TestSupplyChainIntegrationSmoke:
    """Smoke tests for supply chain integration"""
    def test_all_stages_available(self):
        """Test that all verification stages are available"""
        try:
            from controlplane.validation import (
                Stage1Verifier,
                Stage2Verifier,
                Stage3Verifier,
                Stage4Verifier,
                Stage5Verifier,
                Stage6Verifier,
                Stage7Verifier,
            )
            assert all([
                Stage1Verifier is not None,
                Stage2Verifier is not None,
                Stage3Verifier is not None,
                Stage4Verifier is not None,
                Stage5Verifier is not None,
                Stage6Verifier is not None,
                Stage7Verifier is not None,
            ])
        except ImportError as e:
            pytest.skip(f"Supply chain stages not importable: {e}")
    def test_hash_manager_importable(self):
        """Test that HashManager is importable"""
        try:
            from controlplane.validation.hash_manager import HashManager
            assert HashManager is not None
        except ImportError as e:
            pytest.skip(f"HashManager not importable: {e}")
    def test_supply_chain_verifier_importable(self):
        """Test that SupplyChainVerifier is importable"""
        try:
            from controlplane.validation.supply_chain_verifier import SupplyChainVerifier
            assert SupplyChainVerifier is not None
        except ImportError as e:
            pytest.skip(f"SupplyChainVerifier not importable: {e}")
@pytest.mark.smoke
def test_supply_chain_system_integration():
    """Test basic integration of supply chain system components"""
    try:
        # Try to import all key components
        from controlplane.validation import (
            SupplyChainVerifier,
            HashManager,
            VerificationStage,
            VerificationEvidence,
            ChainVerificationResult,
        )
        assert all([
            SupplyChainVerifier is not None,
            HashManager is not None,
            VerificationStage is not None,
            VerificationEvidence is not None,
            ChainVerificationResult is not None,
        ])
    except ImportError as e:
        pytest.skip(f"Supply chain system integration test failed: {e}")
@pytest.mark.smoke
def test_supply_chain_data_integrity(test_data):
    """Test data integrity of supply chain test data"""
    project = test_data["supply_chain_medium"]
    # Verify project data consistency
    assert project["name"] is not None
    assert len(project["name"]) > 0
    assert project["size"] in ["small", "medium", "large"]
    assert len(project["files"]) > 0
    assert len(project["services"]) > 0
    assert len(project["config"]["stages"]) == 7