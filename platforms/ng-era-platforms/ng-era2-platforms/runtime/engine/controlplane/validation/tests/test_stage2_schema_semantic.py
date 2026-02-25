#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_stage2_schema_semantic
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Unit tests for stage2_schema_semantic.py
Tests Stage 2 Schema/Semantic verification.
"""
import unittest
import tempfile  # noqa: E402
import shutil  # noqa: E402
from pathlib import Path  # noqa: E402
import sys  # noqa: E402
# Add repository root to path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
# Import from the validation package
from controlplane.validation.hash_manager import HashManager  # noqa: E402
from controlplane.validation.stage2_schema_semantic import Stage2SchemaSemanticVerifier  # noqa: E402
from controlplane.validation.supply_chain_types import VerificationEvidence  # noqa: E402
class TestStage2SchemaSemanticVerifier(unittest.TestCase):
    """Test Stage2SchemaSemanticVerifier class"""
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.evidence_dir = Path(self.test_dir) / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.hash_manager = HashManager()
        self.verifier = Stage2SchemaSemanticVerifier(
            repo_path=Path(self.test_dir),
            evidence_dir=self.evidence_dir,
            hash_manager=self.hash_manager,
        )
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    def test_initialization(self):
        """Test verifier initialization"""
        self.assertIsNotNone(self.verifier)
        self.assertEqual(self.verifier.repo_path, Path(self.test_dir))
    def test_verify_empty_repo(self):
        """Test verification with empty repository"""
        evidence = self.verifier.verify()
        self.assertIsInstance(evidence, VerificationEvidence)
        self.assertEqual(evidence.stage, 2)
        self.assertEqual(evidence.stage_name, "Schema/語意驗證")
        self.assertEqual(evidence.evidence_type, "schema_validation")
        self.assertTrue(evidence.compliant)
    def test_verify_deployment_with_resources(self):
        """Test verification of Deployment with resource limits"""
        deployment_yaml = Path(self.test_dir) / "deployment.yaml"
        deployment_yaml.write_text(
            """apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  template:
    spec:
      containers:
        - name: app
          image: nginx:1.21
          resources:
            limits:
              cpu: "500m"
              memory: "512Mi"
"""
        )
        evidence = self.verifier.verify()
        self.assertTrue(evidence.compliant)
        self.assertIn("k8s_resources", evidence.data)
        self.assertEqual(len(evidence.data["k8s_resources"]), 1)
        resource = evidence.data["k8s_resources"][0]
        self.assertEqual(resource["kind"], "Deployment")
        self.assertEqual(len(resource["violations"]), 0)
    def test_verify_deployment_without_resources(self):
        """Test violation detection for missing resource limits"""
        deployment_yaml = Path(self.test_dir) / "deployment.yaml"
        deployment_yaml.write_text(
            """apiVersion: apps/v1
kind: Deployment
metadata:
  name: bad-deployment
spec:
  template:
    spec:
      containers:
        - name: app
          image: nginx:1.21
"""
        )
        evidence = self.verifier.verify()
        resource = evidence.data["k8s_resources"][0]
        violations = resource["violations"]
        self.assertGreater(len(violations), 0)
        resource_violations = [v for v in violations if v["violation"] == "missing_resources"]
        self.assertGreater(len(resource_violations), 0)
    def test_verify_deployment_using_latest_tag(self):
        """Test violation detection for using latest tag"""
        deployment_yaml = Path(self.test_dir) / "deployment.yaml"
        deployment_yaml.write_text(
            """apiVersion: apps/v1
kind: Deployment
metadata:
  name: latest-deployment
spec:
  template:
    spec:
      containers:
        - name: app
          image: nginx:latest
          resources:
            limits:
              cpu: "500m"
              memory: "512Mi"
"""
        )
        evidence = self.verifier.verify()
        resource = evidence.data["k8s_resources"][0]
        violations = resource["violations"]
        latest_violations = [v for v in violations if v["violation"] == "using_latest_tag"]
        self.assertGreater(len(latest_violations), 0)
        self.assertEqual(latest_violations[0]["severity"], "HIGH")
if __name__ == "__main__":
    unittest.main()