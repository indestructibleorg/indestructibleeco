"""
End-to-End Reasoning Pipeline
Orchestrates dual-path retrieval, arbitration, and traceability
"""
import os
import sys
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from ecosystem.reasoning.dual_path.internal.retrieval import InternalRetrievalEngine
from ecosystem.reasoning.dual_path.external.retrieval import ExternalRetrievalEngine
from ecosystem.reasoning.dual_path.arbitration.arbitrator import Arbitrator
from ecosystem.reasoning.traceability.traceability import TraceabilityEngine
from ecosystem.reasoning.traceability.feedback import FeedbackLoop


class ReasoningPipeline:
    """
    End-to-end reasoning pipeline
    Handles user requests through dual-path retrieval and arbitration
    """
    
    def __init__(self, config_path: str = "ecosystem/contracts/reasoning/dual_path_spec.yaml"):
        """Initialize reasoning pipeline"""
        self.config_path = config_path
        
        # Initialize components
        self.internal_engine = InternalRetrievalEngine(config_path)
        self.external_engine = ExternalRetrievalEngine(config_path)
        self.arbitrator = Arbitrator(config_path)
        self.traceability = TraceabilityEngine()
        self.feedback_loop = FeedbackLoop()
        
        # Metrics
        self.metrics = {
            "total_requests": 0,
            "internal_only": 0,
            "external_only": 0,
            "hybrid": 0,
            "reject": 0
        }
        
    def handle_request(self, task_spec: str, 
                      context: Optional[Dict] = None,
                      user_id: Optional[str] = None) -> Dict:
        """
        Handle a user reasoning request
        
        Args:
            task_spec: Task specification or question
            context: Additional context
            user_id: User identifier
            
        Returns:
            Complete response with reasoning trace
        """
        # Generate request ID
        request_id = hashlib.md5(f"{task_spec}:{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        self.metrics["total_requests"] += 1
        
        print(f"\n{'='*60}")
        print(f"Processing Request: {request_id}")
        print(f"Task: {task_spec}")
        print(f"{'='*60}\n")
        
        # Step 1: Internal retrieval
        print("Step 1: Internal Retrieval...")
        internal_results = self._internal_retrieval(task_spec, context)
        internal_result_summary = self._summarize_results(internal_results)
        
        # Step 2: External retrieval
        print("Step 2: External Retrieval...")
        external_results = self._external_retrieval(task_spec, context)
        external_result_summary = self._summarize_results(external_results)
        
        # Step 3: Arbitration
        print("Step 3: Arbitration...")
        decision = self.arbitrator.arbitrate(
            task_spec=task_spec,
            internal_result=internal_result_summary,
            external_result=external_result_summary
        )
        
        # Update metrics
        self.metrics[decision.decision.value] = self.metrics.get(decision.decision.value, 0) + 1
        
        print(f"Decision: {decision.decision.value}")
        print(f"Reason: {decision.reason}\n")
        
        # Step 4: Generate final answer
        final_answer = self._generate_final_answer(
            task_spec, internal_results, external_results, decision
        )
        
        # Step 5: Generate traceability report
        print("Step 4: Generating Traceability Report...")
        trace_report = self.traceability.generate_trace(
            task_spec=task_spec,
            internal_results=[r.to_dict() for r in internal_results],
            external_results=[r.to_dict() for r in external_results],
            arbitration_decision=decision.to_dict(),
            final_answer=final_answer
        )
        
        # Save trace
        self.traceability.save_trace(trace_report, request_id)
        
        # Step 6: Compile response
        response = {
            "request_id": request_id,
            "task_spec": task_spec,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "final_answer": final_answer,
            "decision": decision.to_dict(),
            "sources": {
                "internal": {
                    "count": len(internal_results),
                    "results": [r.to_dict() for r in internal_results]
                },
                "external": {
                    "count": len(external_results),
                    "results": [r.to_dict() for r in external_results]
                }
            },
            "trace_report_id": request_id,
            "metrics": {
                "internal_confidence": decision.internal_confidence,
                "external_confidence": decision.external_confidence
            }
        }
        
        print(f"{'='*60}")
        print(f"Request Complete: {request_id}")
        print(f"{'='*60}\n")
        
        return response
    
    def _internal_retrieval(self, task_spec: str, 
                           context: Optional[Dict]) -> List:
        """Perform internal retrieval"""
        results = self.internal_engine.search(
            query=task_spec,
            top_k=5,
            sources=context.get("sources") if context else None
        )
        
        # Audit log
        audit = self.internal_engine.audit_log(
            actor="system",
            action="search",
            query=task_spec,
            results_count=len(results)
        )
        
        self._save_audit_log(audit)
        
        return results
    
    def _external_retrieval(self, task_spec: str,
                           context: Optional[Dict]) -> List:
        """Perform external retrieval"""
        results = self.external_engine.search(
            query=task_spec,
            top_k=5,
            domains=context.get("domains") if context else None
        )
        
        # Audit log
        audit = self.external_engine.audit_log(
            actor="system",
            action="search",
            query=task_spec,
            results_count=len(results)
        )
        
        self._save_audit_log(audit)
        
        return results
    
    def _summarize_results(self, results: List) -> Dict:
        """Summarize retrieval results for arbitration"""
        if not results:
            return {
                "answer": "",
                "confidence": 0.0,
                "metadata": {}
            }
        
        # Use top result
        top_result = results[0]
        
        return {
            "answer": top_result.content,
            "confidence": top_result.confidence,
            "metadata": top_result.metadata
        }
    
    def _generate_final_answer(self, task_spec: str,
                              internal_results: List,
                              external_results: List,
                              decision: Any) -> str:
        """Generate final answer based on decision"""
        if decision.decision.value == "INTERNAL":
            return internal_results[0].content if internal_results else "No internal results available"
        elif decision.decision.value == "EXTERNAL":
            return external_results[0].content if external_results else "No external results available"
        elif decision.decision.value == "HYBRID":
            return decision.final_answer or self._merge_answers(internal_results, external_results)
        else:  # REJECT
            return "Unable to provide recommendation due to low confidence from all sources."
    
    def _merge_answers(self, internal_results: List, external_results: List) -> str:
        """Merge internal and external answers"""
        internal = internal_results[0].content if internal_results else ""
        external = external_results[0].content if external_results else ""
        
        return f"""# Combined Recommendation

## Internal Approach
{internal}

## External Best Practices
{external}

## Integrated Solution
Consider following your project's internal patterns while incorporating external best practices where applicable. Test thoroughly before deployment.
"""
    
    def _save_audit_log(self, audit_log: Dict):
        """Save audit log entry"""
        audit_dir = Path("ecosystem/logs/audit")
        audit_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        log_file = audit_dir / f"audit_{timestamp}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(audit_log) + '\n')
    
    def submit_feedback(self, request_id: str, feedback_type: str,
                       reason: Optional[str] = None, user_id: Optional[str] = None):
        """Submit user feedback on a decision"""
        # Load trace report
        traces = self.traceability.query_traces(request_id)
        if not traces:
            print(f"No trace found for request ID: {request_id}")
            return
        
        trace = traces[-1]
        arbitration_decision = trace.get("arbitration_trace", {}).get("decision", {})
        
        # Record feedback
        from ecosystem.reasoning.traceability.feedback import UserFeedback
        feedback = UserFeedback(
            case_id=request_id,
            feedback_type=feedback_type,
            reason=reason,
            user_id=user_id
        )
        
        audit = self.feedback_loop.record_feedback(
            request_id, arbitration_decision, feedback
        )
        
        print("Feedback recorded successfully")
        print(json.dumps(audit, indent=2))
    
    def get_metrics(self) -> Dict:
        """Get pipeline metrics"""
        return {
            "metrics": self.metrics,
            "total_requests": self.metrics["total_requests"],
            "decision_distribution": {
                k: v for k, v in self.metrics.items() if k != "total_requests"
            }
        }


if __name__ == "__main__":
    # Test reasoning pipeline
    pipeline = ReasoningPipeline()
    
    # Handle a test request
    response = pipeline.handle_request(
        task_spec="How should I implement async task processing in Python?",
        context={
            "sources": ["code", "documentation"],
            "domains": ["docs.python.org", "kubernetes.io"]
        },
        user_id="test_user"
    )
    
    print("\n\n=== Final Response ===")
    print(json.dumps(response, indent=2))
    
    # Get metrics
    metrics = pipeline.get_metrics()
    print("\n\n=== Pipeline Metrics ===")
    print(json.dumps(metrics, indent=2))