#
# @ECO-governed
# @ECO-layer: gl-platform.governance
# @ECO-semantic: coordination_layer
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
GL Coordination Layer Implementation
Coordinates all GL core architecture components:
- Governance Loop Executor
- Semantic Root Manager
- Quantum Validator
- Reconciliation Engine
"""
# MNGA-002: Import organization needs review
from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging
from .gl-platform.governance_loop import GovernanceLoopExecutor
from .semantic_root import SemanticRootManager
from .quantum_validation import QuantumValidator
from .reconciliation import ReconciliationEngine
# Configure logging
logger = logging.getLogger(__name__)
# Configure logging
logger = logging.getLogger(__name__)
# Configure logging
logger = logging.getLogger('GLCoordinationLayer')
class GLCoordinationLayer:
    """
    Coordinates all GL core architecture components
    Responsibilities:
    - Orchestrate gl-platform.governance loop execution
    - Manage semantic root lifecycle
    - Execute quantum validation
    - Trigger reconciliation when needed
    - Generate comprehensive evidence chains
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Initialize core components
        self.gl-platform.governance_loop = GovernanceLoopExecutor(config)
        self.semantic_root = SemanticRootManager(config)
        self.quantum_validator = QuantumValidator(config)
        self.reconciliation_engine = ReconciliationEngine(config)
        # Coordination state
        self.coordination_session_id = ""
        self.session_start_time = None
        self.session_end_time = None
        self.session_metrics = {}
    def start_coordination_session(self, input_data: Dict[str, Any]) -> str:
        """
        Start a new coordination session
        Args:
            input_data: Input data for the session
        Returns:
            Session ID
        """
        self.coordination_session_id = f"COORD-{datetime.now().timestamp()}"
        self.session_start_time = datetime.now()
        return self.coordination_session_id
    def execute_full_workflow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the full GL coordination workflow
        Args:
            input_data: Input data for the workflow
        Returns:
            Comprehensive workflow results
        """
        # Start session
        session_id = self.start_coordination_session(input_data)
        workflow_result = {
            "session_id": session_id,
            "components_executed": [],
            "evidence_chains": {},
            "metrics": {},
        }
        try:
            # Step 1: Execute gl-platform.governance loop
            logger.info("Executing gl-platform.governance loop...")
            loop_context = self.gl-platform.governance_loop.execute_cycle(input_data)
            workflow_result["components_executed"].append("gl-platform.governance_loop")
            workflow_result["evidence_chains"]["gl-platform.governance_loop"] = (
                self.gl-platform.governance_loop.generate_evidence_chain(loop_context)
            )
            # Step 2: Validate with quantum validator
            logger.info("Executing quantum validation...")
            validation_result = self.quantum_validator.validate(input_data)
            workflow_result["components_executed"].append("quantum_validation")
            workflow_result["evidence_chains"]["quantum_validation"] = (
                self.quantum_validator.generate_evidence_chain(validation_result)
            )
            # Step 3: Check if reconciliation is needed
            if validation_result.status.value in ["FAILED", "FELLBACK"]:
                logger.info("Executing reconciliation...")
                reconciliation_event = {
                    "type": "validation_failure",
                    "input_data": input_data,
                }
                reconciliation_result = self.reconciliation_engine.execute_reconciliation(
                    reconciliation_event
                )
                workflow_result["components_executed"].append("reconciliation")
                workflow_result["evidence_chains"]["reconciliation"] = (
                    reconciliation_result.to_dict()
                )
            # Step 4: Update semantic root
            logger.info("Updating semantic root...")
            semantic_seal = self.semantic_root.create_semantic_seal(
                json.dumps(workflow_result)
            )
            workflow_result["components_executed"].append("semantic_root")
            workflow_result["evidence_chains"]["semantic_root"] = {
                "seal_id": semantic_seal.seal_id,
                "content_hash": semantic_seal.content_hash,
                "verified": semantic_seal.verified,
            }
            # Generate session metrics
            self.session_end_time = datetime.now()
            self.session_metrics = self._calculate_session_metrics()
            workflow_result["metrics"] = self.session_metrics
            workflow_result["status"] = "COMPLETED"
            workflow_result["success"] = True
        except Exception as e:
            workflow_result["status"] = "FAILED"
            workflow_result["success"] = False
            workflow_result["error"] = str(e)
        return workflow_result
    def _calculate_session_metrics(self) -> Dict[str, Any]:
        """Calculate session metrics"""
        if not self.session_start_time or not self.session_end_time:
            return {}
        duration_seconds = (self.session_end_time - self.session_start_time).total_seconds()
        return {
            "session_id": self.coordination_session_id,
            "start_time": self.session_start_time.isoformat(),
            "end_time": self.session_end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "gl-platform.governance_performance": self.gl-platform.governance_loop.get_performance_metrics(),
            "validation_performance": self.quantum_validator.get_performance_metrics(),
            "semantic_mapping_status": self.semantic_root.get_semantic_mapping_status(),
            "reconciliation_queue_status": self.reconciliation_engine.get_queue_status(),
        }
    def get_governance_loop_executor(self) -> GovernanceLoopExecutor:
        """Get gl-platform.governance loop executor"""
        return self.gl-platform.governance_loop
    def get_semantic_root_manager(self) -> SemanticRootManager:
        """Get semantic root manager"""
        return self.semantic_root
    def get_quantum_validator(self) -> QuantumValidator:
        """Get quantum validator"""
        return self.quantum_validator
    def get_reconciliation_engine(self) -> ReconciliationEngine:
        """Get reconciliation engine"""
        return self.reconciliation_engine
    def generate_comprehensive_evidence_chain(self) -> Dict[str, Any]:
        """Generate comprehensive evidence chain for all components"""
        return {
            "session_id": self.coordination_session_id,
            "session_metrics": self.session_metrics,
            "gl-platform.governance_loop": self.gl-platform.governance_loop.get_performance_metrics(),
            "semantic_root": self.semantic_root.generate_evidence_chain(),
            "quantum_validation": self.quantum_validator.get_performance_metrics(),
            "reconciliation": self.reconciliation_engine.get_queue_status(),
            "generated_at": datetime.now().isoformat(),
        }
# Factory function for creating GLCoordinationLayer instances
def create_gl_coordination_layer(config: Optional[Dict[str, Any]] = None) -> GLCoordinationLayer:
    """Factory function to create GLCoordinationLayer"""
    return GLCoordinationLayer(config)