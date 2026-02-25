#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_stage1_lint_format
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Unit tests for stage1_lint_format.py
Tests Stage 1 Lint/Format verification.
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
from controlplane.validation.stage1_lint_format import Stage1LintFormatVerifier  # noqa: E402
from controlplane.validation.supply_chain_types import VerificationEvidence  # noqa: E402
class TestStage1LintFormatVerifier(unittest.TestCase):
    """Test Stage1LintFormatVerifier class"""
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.evidence_dir = Path(self.test_dir) / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.hash_manager = HashManager()
        self.verifier = Stage1LintFormatVerifier(
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
        self.assertEqual(self.verifier.evidence_dir, self.evidence_dir)
    def test_verify_empty_repo(self):
        """Test verification with empty repository"""
        evidence = self.verifier.verify()
        self.assertIsInstance(evidence, VerificationEvidence)
        self.assertEqual(evidence.stage, 1)
        self.assertEqual(evidence.stage_name, "Lint/格式驗證")
        self.assertEqual(evidence.evidence_type, "format_validation")
        self.assertTrue(evidence.compliant)  # Empty repo should pass
    def test_verify_valid_yaml(self):
        """Test verification with valid YAML file"""
        # Create a valid YAML file
        yaml_file = Path(self.test_dir) / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2\n")
        evidence = self.verifier.verify()
        self.assertTrue(evidence.compliant)
        self.assertIn("yaml_files", evidence.data)
        self.assertEqual(len(evidence.data["yaml_files"]), 1)
        self.assertEqual(evidence.data["yaml_files"][0]["status"], "valid")
    def test_verify_invalid_yaml(self):
        """Test verification with invalid YAML file"""
        # Create an invalid YAML file
        yaml_file = Path(self.test_dir) / "invalid.yaml"
        yaml_file.write_text("key: value\n  bad indentation\n  worse indentation\n")
        evidence = self.verifier.verify()
        # Should detect syntax error
        self.assertIn("yaml_files", evidence.data)
        yaml_result = evidence.data["yaml_files"][0]
        self.assertEqual(yaml_result["status"], "invalid")
        self.assertIn("error", yaml_result)
    def test_verify_yaml_with_tabs(self):
        """Test YAML with tabs (format issue)"""
        # Create YAML with tabs
        yaml_file = Path(self.test_dir) / "tabs.yaml"
        yaml_file.write_text("key:\n\tvalue: test\n")
        evidence = self.verifier.verify()
        yaml_result = evidence.data["yaml_files"][0]
        self.assertEqual(yaml_result["status"], "format_issues")
        self.assertIn("uses_tabs", yaml_result["issues"])
    def test_verify_valid_json(self):
        """Test verification with valid JSON file"""
        # Create a valid JSON file
        json_file = Path(self.test_dir) / "test.json"
        json_file.write_text('{"key": "value", "list": [1, 2, 3]}\n')
        evidence = self.verifier.verify()
        self.assertIn("json_files", evidence.data)
        json_result = evidence.data["json_files"][0]
        self.assertEqual(json_result["status"], "valid")
    def test_verify_invalid_json(self):
        """Test verification with invalid JSON file"""
        # Create an invalid JSON file
        json_file = Path(self.test_dir) / "invalid.json"
        json_file.write_text('{"key": value, "missing_quotes"}\n')
        evidence = self.verifier.verify()
        json_result = evidence.data["json_files"][0]
        self.assertEqual(json_result["status"], "invalid")
        self.assertIn("error", json_result)
    def test_verify_valid_python(self):
        """Test verification with valid Python file"""
        # Create a valid Python file
        py_file = Path(self.test_dir) / "test.py"
        py_file.write_text(
            '"""Test module"""\n\ndef hello():\n    print("Hello, World!")\n    return True\n\nif __name__ == "__main__":\n    hello()\n'
        )
        evidence = self.verifier.verify()
        self.assertIn("python_files", evidence.data)
        py_result = evidence.data["python_files"][0]
        self.assertEqual(py_result["status"], "valid")
    def test_verify_python_syntax_error(self):
        """Test Python with syntax error"""
        # Create Python with syntax error
        py_file = Path(self.test_dir) / "syntax_error.py"
        py_file.write_text("def test():\n    print('test'\n")  # Missing closing parenthesis
        evidence = self.verifier.verify()
        py_result = evidence.data["python_files"][0]
        self.assertEqual(py_result["status"], "syntax_error")
        self.assertIn("error", py_result)
    def test_verify_python_with_tabs(self):
        """Test Python with tabs"""
        # Create Python with tabs
        py_file = Path(self.test_dir) / "tabs.py"
        py_file.write_text("def test():\n\tprint('test')\n")
        evidence = self.verifier.verify()
        py_result = evidence.data["python_files"][0]
        self.assertEqual(py_result["status"], "format_issues")
        self.assertIn("tabs_in_indentation", py_result["issues"])
    def test_verify_multiple_files(self):
        """Test verification with multiple files"""
        # Create multiple files
        (Path(self.test_dir) / "valid.yaml").write_text("key: value\n")
        (Path(self.test_dir) / "valid.json").write_text('{"key": "value"}\n')
        (Path(self.test_dir) / "valid.py").write_text("print('test')\n")
        evidence = self.verifier.verify()
        # Should find all files
        self.assertEqual(len(evidence.data["yaml_files"]), 1)
        self.assertEqual(len(evidence.data["json_files"]), 1)
        self.assertEqual(len(evidence.data["python_files"]), 1)
    def test_skip_git_directory(self):
        """Test that .git directory is skipped"""
        # Create .git directory with files
        git_dir = Path(self.test_dir) / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)
        (git_dir / "config").write_text("[core]\n\trepositoryformatversion = 0\n")
        evidence = self.verifier.verify()
        # Should not scan .git files
        yaml_files = [f for f in evidence.data["yaml_files"] if ".git" in f["file"]]
        self.assertEqual(len(yaml_files), 0)
    def test_skip_node_modules(self):
        """Test that node_modules directory is skipped"""
        # Create node_modules directory
        node_modules = Path(self.test_dir) / "node_modules"
        node_modules.mkdir(parents=True, exist_ok=True)
        (node_modules / "package.json").write_text('{"name": "test"}\n')
        evidence = self.verifier.verify()
        # Should not scan node_modules
        json_files = [
            f for f in evidence.data["json_files"] if "node_modules" in f["file"]
        ]
        self.assertEqual(len(json_files), 0)
    def test_evidence_file_creation(self):
        """Test that evidence file is created"""
        (Path(self.test_dir) / "test.yaml").write_text("key: value\n")
        evidence = self.verifier.verify()
        # Check that evidence file was created
        evidence_files = list(self.evidence_dir.glob("stage01-*.json"))
        self.assertEqual(len(evidence_files), 1)
        # Verify evidence file content
        import json
        with evidence_files[0].open() as f:
            content = json.load(f)
            self.assertEqual(content["stage"], 1)
            self.assertEqual(content["stage_name"], "Lint/格式驗證")
            self.assertIn("verification_hash", content)
    def test_compliance_check(self):
        """Test compliance checking logic"""
        # Test with valid files - should pass
        (Path(self.test_dir) / "valid.yaml").write_text("key: value\n")
        evidence1 = self.verifier.verify()
        self.assertTrue(evidence1.compliant)
        # Create new verifier for fresh start
        verifier2 = Stage1LintFormatVerifier(
            repo_path=Path(self.test_dir),
            evidence_dir=self.evidence_dir,
            hash_manager=self.hash_manager,
        )
        # Test with invalid file - should fail
        (Path(self.test_dir) / "invalid.yaml").write_text("bad yaml:::\n")
        evidence2 = verifier2.verify()
        self.assertFalse(evidence2.compliant)
if __name__ == "__main__":
    unittest.main()