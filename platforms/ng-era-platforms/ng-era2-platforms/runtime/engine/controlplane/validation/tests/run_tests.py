#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: run_tests
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Test runner for supply chain verification tests.
Provides convenient ways to run different test suites.
"""
import sys
import unittest
from pathlib import Path
# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
def run_unit_tests():
    """Run unit tests only"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    # Load unit test modules
    test_modules = [
        "tests.test_supply_chain_types",
        "tests.test_hash_manager",
        "tests.test_stage1_lint_format",
        "tests.test_stage2_schema_semantic",
    ]
    for module in test_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
        except Exception as e:
            print(f"Error loading {module}: {e}")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()
def run_integration_tests():
    """Run integration tests only"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName("tests.test_integration")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()
def run_performance_tests():
    """Run performance benchmarks"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName("tests.test_performance_benchmark")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()
def run_all_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()
def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="Run supply chain verification tests")
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only",
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only",
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance benchmarks only",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests (default)",
    )
    args = parser.parse_args()
    # Default to running all tests
    if not any([args.unit, args.integration, args.performance, args.all]):
        args.all = True
    print("=" * 80)
    print("Supply Chain Verification Test Suite")
    print("=" * 80)
    if args.unit:
        print("\nRunning unit tests...")
        success = run_unit_tests()
    elif args.integration:
        print("\nRunning integration tests...")
        success = run_integration_tests()
    elif args.performance:
        print("\nRunning performance benchmarks...")
        success = run_performance_tests()
    elif args.all:
        print("\nRunning all tests...")
        success = run_all_tests()
    else:
        print("No tests specified")
        return 1
    print("\n" + "=" * 80)
    if success:
        print("✅ All tests passed!")
        print("=" * 80)
        return 0
    else:
        print("❌ Some tests failed!")
        print("=" * 80)
        return 1
if __name__ == "__main__":
    sys.exit(main())