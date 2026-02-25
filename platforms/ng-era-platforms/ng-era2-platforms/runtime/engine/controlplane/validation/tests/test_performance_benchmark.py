#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_performance_benchmark
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Performance benchmarks for the supply chain verification system.
Tests performance characteristics and establishes baseline metrics.
"""
import unittest
import time  # noqa: E402
import tempfile  # noqa: E402
import shutil  # noqa: E402
from pathlib import Path  # noqa: E402
import statistics  # noqa: E402
import sys  # noqa: E402
# Add repository root to path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
# Import from the validation package
from controlplane.validation.supply_chain_verifier import UltimateSupplyChainVerifier  # noqa: E402
from controlplane.validation.stage1_lint_format import Stage1LintFormatVerifier  # noqa: E402
from controlplane.validation.hash_manager import HashManager  # noqa: E402
class TestPerformanceBenchmark(unittest.TestCase):
    """Performance benchmarks for verification system"""
    @classmethod
    def setUpClass(cls):
        """Set up performance test infrastructure"""
        cls.results = {}
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    def _create_test_files(self, count=10):
        """Create test files for benchmarking"""
        for i in range(count):
            # YAML files
            (Path(self.test_dir) / f"config{i}.yaml").write_text(
                f"key{i}: value{i}\nlist{i}:\n  - item1\n  - item2\n"
            )
            # JSON files
            (Path(self.test_dir) / f"data{i}.json").write_text(
                f'{{"id": {i}, "name": "test{i}"}}\n'
            )
            # Python files
            (Path(self.test_dir) / f"module{i}.py").write_text(
                f'"""Module {i}"""\n\ndef function{i}():\n    return {i}\n'
            )
    def test_hash_computation_performance(self):
        """Benchmark hash computation performance"""
        hash_manager = HashManager()
        # Benchmark with various data sizes
        test_data = ["small" * 10, "medium" * 1000, "large" * 100000]
        for size_label, data in zip(["small", "medium", "large"], test_data):
            times = []
            iterations = 100
            for _ in range(iterations):
                start_time = time.perf_counter()
                hash_manager.compute_dual_hash(data, "test")
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            self.results[f"hash_{size_label}_avg"] = avg_time
            self.results[f"hash_{size_label}_median"] = median_time
            # Performance assertion: should complete in reasonable time
            self.assertLess(avg_time, 0.01, f"Hash computation for {size_label} data too slow")
            print(f"\nHash computation ({size_label} data):")
            print(f"  Average: {avg_time*1000:.3f}ms")
            print(f"  Median: {median_time*1000:.3f}ms")
    def test_stage1_verification_performance(self):
        """Benchmark Stage 1 verification performance"""
        self._create_test_files(count=50)
        hash_manager = HashManager()
        verifier = Stage1LintFormatVerifier(
            repo_path=Path(self.test_dir),
            evidence_dir=Path(self.test_dir) / "evidence",
            hash_manager=hash_manager,
        )
        start_time = time.perf_counter()
        evidence = verifier.verify()
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.results["stage1_50_files"] = elapsed_time
        print(f"\nStage 1 verification (50 files): {elapsed_time:.3f}s")
        # Performance assertion
        self.assertLess(elapsed_time, 10.0, "Stage 1 verification too slow")
        self.assertTrue(evidence.compliant)
    def test_complete_verification_performance(self):
        """Benchmark complete verification performance"""
        self._create_test_files(count=20)
        verifier = UltimateSupplyChainVerifier(repo_path=self.test_dir)
        start_time = time.perf_counter()
        result = verifier.run_complete_verification()
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.results["complete_verification"] = elapsed_time
        print(f"\nComplete verification: {elapsed_time:.3f}s")
        # Performance assertion
        self.assertLess(elapsed_time, 30.0, "Complete verification too slow")
        self.assertEqual(result.total_stages, 7)
if __name__ == "__main__":
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPerformanceBenchmark)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    # Print results
    TestPerformanceBenchmark.print_results()