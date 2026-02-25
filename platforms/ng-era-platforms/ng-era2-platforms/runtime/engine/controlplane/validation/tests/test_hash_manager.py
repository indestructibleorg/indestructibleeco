#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_hash_manager
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Unit tests for hash_manager.py
Tests hash computation and management functionality.
"""
import hashlib
import sys
import unittest
from pathlib import Path

# Add repository root to path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
# Import from the validation package
from controlplane.validation.hash_manager import HashManager  # noqa: E402


class TestHashManager(unittest.TestCase):
    """Test HashManager class"""
    def setUp(self):
        """Set up test fixtures"""
        self.hash_manager = HashManager()
    def test_initialization(self):
        """Test HashManager initialization"""
        self.assertIsNotNone(self.hash_manager)
        self.assertEqual(len(self.hash_manager.get_hash_chain()), 0)
        self.assertEqual(len(self.hash_manager.get_reproducible_hashes()), 0)
    def test_compute_dual_hash(self):
        """Test dual hash computation"""
        data = "test data"
        stage = "stage1"
        verification_hash, reproducible_hash = self.hash_manager.compute_dual_hash(
            data, stage
        )
        # Verify hashes are returned
        self.assertIsNotNone(verification_hash)
        self.assertIsNotNone(reproducible_hash)
        # Verify hash length (SHA3-512 produces 128 hex characters)
        self.assertEqual(len(verification_hash), 128)
        self.assertEqual(len(reproducible_hash), 128)
        # Verify hashes are stored
        hash_chain = self.hash_manager.get_hash_chain()
        self.assertIn(f"{stage}_verification", hash_chain)
        self.assertEqual(hash_chain[f"{stage}_verification"], verification_hash)
        reproducible_hashes = self.hash_manager.get_reproducible_hashes()
        self.assertIn(f"{stage}_reproducible", reproducible_hashes)
        self.assertEqual(
            reproducible_hashes[f"{stage}_reproducible"], reproducible_hash
        )
    def test_different_data_different_hashes(self):
        """Test that different data produces different hashes"""
        data1 = "data1"
        data2 = "data2"
        hash1_1, hash1_2 = self.hash_manager.compute_dual_hash(data1, "stage1")
        hash2_1, hash2_2 = self.hash_manager.compute_dual_hash(data2, "stage2")
        self.assertNotEqual(hash1_1, hash2_1)
        self.assertNotEqual(hash1_2, hash2_2)
    def test_same_data_same_hash(self):
        """Test that same data produces same verification hash"""
        data = "test data"
        hash1, _ = self.hash_manager.compute_dual_hash(data, "stage1")
        hash2, _ = self.hash_manager.compute_dual_hash(data, "stage2")
        # Verification hash should be deterministic
        self.assertEqual(hash1, hash2)
    def test_reproducible_hash_randomness(self):
        """Test that reproducible hash includes randomness"""
        data = "test data"
        hash1, repro1 = self.hash_manager.compute_dual_hash(data, "stage1")
        hash2, repro2 = self.hash_manager.compute_dual_hash(data, "stage1")
        # Verification hash should be same
        self.assertEqual(hash1, hash2)
        # Reproducible hash should be different (includes timestamp and salt)
        self.assertNotEqual(repro1, repro2)
    def test_hash_chain_tracking(self):
        """Test hash chain tracking"""
        # Add multiple hashes
        self.hash_manager.compute_dual_hash("data1", "stage1")
        self.hash_manager.compute_dual_hash("data2", "stage2")
        self.hash_manager.compute_dual_hash("data3", "stage3")
        hash_chain = self.hash_manager.get_hash_chain()
        self.assertEqual(len(hash_chain), 3)
        self.assertIn("stage1_verification", hash_chain)
        self.assertIn("stage2_verification", hash_chain)
        self.assertIn("stage3_verification", hash_chain)
    def test_reproducible_hashes_tracking(self):
        """Test reproducible hashes tracking"""
        # Add multiple hashes
        self.hash_manager.compute_dual_hash("data1", "stage1")
        self.hash_manager.compute_dual_hash("data2", "stage2")
        reproducible_hashes = self.hash_manager.get_reproducible_hashes()
        self.assertEqual(len(reproducible_hashes), 2)
    def test_clear_hashes(self):
        """Test clearing all hashes"""
        # Add some hashes
        self.hash_manager.compute_dual_hash("data1", "stage1")
        self.hash_manager.compute_dual_hash("data2", "stage2")
        # Clear hashes
        self.hash_manager.clear_hashes()
        # Verify cleared
        self.assertEqual(len(self.hash_manager.get_hash_chain()), 0)
        self.assertEqual(len(self.hash_manager.get_reproducible_hashes()), 0)
    def test_hash_algorithm(self):
        """Test that SHA3-512 is used"""
        data = "test data"
        verification_hash, _ = self.hash_manager.compute_dual_hash(data, "stage1")
        # Compute expected hash using SHA3-512
        expected_hash = hashlib.sha3_512(data.encode()).hexdigest()
        self.assertEqual(verification_hash, expected_hash)
if __name__ == "__main__":
    unittest.main()