# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: index_optimizer
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Index Optimization Service
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
# MNGA-002: Import organization needs review
from typing import Dict, Any, List
import logging
from datetime import datetime
import hashlib
import json
from ..elasticsearch.client import EsClientManager
logger = logging.getLogger(__name__)
class IndexOptimizer:
    def __init__(self, client: EsClientManager, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.optimizer_id = config.get('id', 'index-optimizer')
        self.evidence_chain = []
        self.metrics = {
            'optimizations_performed': 0,
            'segments_merged': 0,
            'start_time': None,
            'end_time': None
        }
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'optimizer_id': self.optimizer_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def optimize_index(self, index_name: str) -> Dict[str, Any]:
        self.metrics['start_time'] = datetime.utcnow()
        self.generate_evidence('index_optimization_start', {'index': index_name})
        try:
            result = self.client.client.indices.forcemerge(
                index=index_name,
                max_num_segments=1,
                wait_for_merge=False
            )
            self.metrics['optimizations_performed'] += 1
            self.metrics['segments_merged'] += result.get('num_merges', 0)
            self.generate_evidence('index_optimization_complete', {
                'index': index_name,
                'result': result
            })
            return result
        except Exception as e:
            logger.error(f"Index optimization failed: {str(e)}")
            self.generate_evidence('index_optimization_failed', {'error': str(e)})
            raise
        finally:
            self.metrics['end_time'] = datetime.utcnow()
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        return self.evidence_chain
