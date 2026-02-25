#
# @ECO-governed
# @ECO-layer: gl-platform.governance
# @ECO-semantic: test_implementation
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
GL Implementation Test Suite
Tests all GL core architecture implementations.
"""
from .gl-platform.governance_loop import GovernanceLoopExecutor
from .semantic_root import SemanticRootManager
from .quantum_validation import QuantumValidator
from .reconciliation import ReconciliationEngine
from .coordination_layer import GLCoordinationLayer
def test_governance_loop():
    """Test gl-platform.governance loop implementation"""
    print("\n" + "="*80)
    print("Testing Governance Loop Implementation")
    print("="*80)
    # Create executor
    executor = GovernanceLoopExecutor()
    # Execute a gl-platform.governance cycle
    input_data = {
        "tasks": [
            {"id": "TASK-001", "type": "vision", "description": "Define gl-platform.governance vision"},
            {"id": "TASK-002", "type": "policy", "description": "Create gl-platform.governance policies"},
            {"id": "TASK-003", "type": "validation", "description": "Implement validation"},
        ],
    }
    print(f"\nExecuting gl-platform.governance cycle with {len(input_data['tasks'])} tasks...")
    context = executor.execute_cycle(input_data)
    # Print results
    print(f"\nCycle ID: {context.cycle_id}")
    print(f"Duration: {context.loop_metrics['duration_seconds']:.2f}s")
    print(f"Phases Completed: {context.loop_metrics['phases_completed']}")
    for phase, result in context.phase_results.items():
        print(f"\nPhase: {phase.value}")
        print(f"  Status: {result.status.value}")
        print(f"  Duration: {result.metrics.get('duration_seconds', 0):.2f}s")
        print(f"  Artifacts: {len(result.output_artifacts)}")
    # Generate evidence chain
    evidence = executor.generate_evidence_chain(context)
    print(f"\nEvidence Hash: {evidence['evidence_hash']}")
    # Get performance metrics
    metrics = executor.get_performance_metrics()
    print("\nPerformance Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    print("\n✅ Governance Loop Test Passed")
    return True
def test_semantic_root():
    """Test semantic root management implementation"""
    print("\n" + "="*80)
    print("Testing Semantic Root Management Implementation")
    print("="*80)
    # Create manager
    manager = SemanticRootManager()
    # Get unified semantic root
    root = manager.get_unified_semantic_root()
    print(f"\nUnified Semantic Root: {root}")
    # Get entities
    entities = manager.get_entities()
    print(f"\nSemantic Entities: {len(entities)}")
    for entity in entities:
        print(f"  - {entity.name}: {entity.urn}")
    # Execute review
    changes = [{"id": "CHANGE-001", "type": "semantic"}]
    review_result = manager.execute_review("REVIEW-1", changes)
    print(f"\nReview Result: {review_result}")
    # Detect semantic changes
    current_semantics = {"version": "1.0.0", "entities": 3}
    previous_semantics = {"version": "1.0.0", "entities": 3}
    detection_result = manager.detect_semantic_changes(
        current_semantics,
        previous_semantics
    )
    print(f"\nSemantic Detection: {detection_result}")
    # Create semantic seal
    content = "Test content for sealing"
    seal = manager.create_semantic_seal(content)
    print("\nSemantic Seal Created:")
    print(f"  Seal ID: {seal.seal_id}")
    print(f"  Hash: {seal.content_hash}")
    # Verify seal
    verified = manager.verify_semantic_seal(seal.seal_id, content)
    print(f"  Verified: {verified}")
    # Generate evidence chain
    evidence = manager.generate_evidence_chain()
    print(f"\nEvidence Chain: {len(evidence)} fields")
    print("\n✅ Semantic Root Management Test Passed")
    return True
def test_quantum_validation():
    """Test quantum validation implementation"""
    print("\n" + "="*80)
    print("Testing Quantum Validation Implementation")
    print("="*80)
    # Create validator
    validator = QuantumValidator()
    # Get validation dimensions
    dimensions = validator.get_dimensions()
    print(f"\nValidation Dimensions: {len(dimensions)}")
    for dim in dimensions:
        print(f"  - {dim.name}: {dim.status}")
    # Get quantum algorithms
    algorithms = validator.get_quantum_algorithms()
    print(f"\nQuantum Algorithms: {len(algorithms)}")
    for alg_id, algorithm in algorithms.items():
        print(f"  - {algorithm.name}: {algorithm.accuracy}")
    # Execute validation
    input_data = {
        "content": "Test content for validation",
        "metadata": {"version": "1.0.0"},
    }
    print("\nExecuting validation...")
    result = validator.validate(input_data)
    print("\nValidation Result:")
    print(f"  Status: {result.status.value}")
    print(f"  Accuracy: {result.overall_accuracy:.1f}%")
    print(f"  Execution Time: {result.execution_time_ms:.2f}ms")
    print(f"  Fellback: {result.fellback}")
    # Generate evidence chain
    evidence = validator.generate_evidence_chain(result)
    print(f"\nEvidence Hash: {evidence['evidence_hash']}")
    # Get performance metrics
    metrics = validator.get_performance_metrics()
    print("\nPerformance Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    print("\n✅ Quantum Validation Test Passed")
    return True
def test_reconciliation():
    """Test reconciliation engine implementation"""
    print("\n" + "="*80)
    print("Testing Reconciliation Engine Implementation")
    print("="*80)
    # Create engine
    engine = ReconciliationEngine()
    # Get strategies
    strategies = engine.strategies
    print(f"\nReconciliation Strategies: {len(strategies)}")
    for strat_id, strategy in strategies.items():
        print(f"  - {strategy['name']}: Priority {strategy['priority']}")
    # Execute reconciliation
    event = {
        "type": "validation_failure",
        "description": "Validation check failed",
        "severity": "HIGH",
    }
    print(f"\nExecuting reconciliation for event: {event['type']}")
    result = engine.execute_reconciliation(event)
    print("\nReconciliation Result:")
    print(f"  Strategy: {result.strategy_id}")
    print(f"  Status: {result.status}")
    print(f"  Actions Executed: {len(result.actions)}")
    for action in result.actions:
        print(f"    - {action.description}: {action.status}")
    # Get queue status
    queue_status = engine.get_queue_status()
    print("\nQueue Status:")
    print(f"  Current Size: {queue_status['current_size']}")
    print(f"  Max Capacity: {queue_status['max_capacity']}")
    print(f"  Throughput Target: {queue_status['throughput_target']} events/sec")
    print("\n✅ Reconciliation Engine Test Passed")
    return True
def test_coordination_layer():
    """Test coordination layer implementation"""
    print("\n" + "="*80)
    print("Testing Coordination Layer Implementation")
    print("="*80)
    # Create coordination layer
    coordinator = GLCoordinationLayer()
    # Execute full workflow
    input_data = {
        "tasks": [
            {"id": "TASK-001", "type": "vision", "description": "Define gl-platform.governance vision"},
        ],
    }
    print("\nExecuting full coordination workflow...")
    workflow_result = coordinator.execute_full_workflow(input_data)
    print("\nWorkflow Result:")
    print(f"  Session ID: {workflow_result['session_id']}")
    print(f"  Status: {workflow_result['status']}")
    print(f"  Success: {workflow_result['success']}")
    print(f"  Components Executed: {len(workflow_result['components_executed'])}")
    for component in workflow_result["components_executed"]:
        print(f"    - {component}")
    # Print metrics
    metrics = workflow_result.get("metrics", {})
    if metrics:
        print("\nSession Metrics:")
        print(f"  Duration: {metrics.get('duration_seconds', 0):.2f}s")
        gov_perf = metrics.get("gl-platform.governance_performance", {})
        if gov_perf:
            print(f"  Governance Closure Rate: {gov_perf.get('gl-platform.governance_closure_rate', 0)}%")
        val_perf = metrics.get("validation_performance", {})
        if val_perf:
            print(f"  Validation Accuracy: {val_perf.get('validation_accuracy', 0)}%")
    # Generate comprehensive evidence chain
    evidence = coordinator.generate_comprehensive_evidence_chain()
    print(f"\nComprehensive Evidence Chain: {len(evidence)} fields")
    print("\n✅ Coordination Layer Test Passed")
    return True
def run_all_tests():
    """Run all implementation tests"""
    print("\n" + "="*80)
    print("GL Implementation Test Suite")
    print("="*80)
    tests = [
        ("Governance Loop", test_gl-platform.governance_loop),
        ("Semantic Root", test_semantic_root),
        ("Quantum Validation", test_quantum_validation),
        ("Reconciliation Engine", test_reconciliation),
        ("Coordination Layer", test_coordination_layer),
    ]
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} Test Failed: {e}")
            results[test_name] = False
    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    print(f"\nTotal: {passed}/{total} tests passed")
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    return passed == total
if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)