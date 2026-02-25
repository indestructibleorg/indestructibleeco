# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: relevance_tuning
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Relevance Tuning Engine
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
# MNGA-002: Import organization needs review
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import hashlib
import json
from ..elasticsearch.client import EsClientManager
logger = logging.getLogger(__name__)
class RelevanceTuner:
    def __init__(self, client: EsClientManager, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.tuner_id = config.get('id', 'relevance-tuner')
        self.evidence_chain = []
        self.metrics = {
            'tunings_performed': 0,
            'improvements_detected': 0,
            'start_time': None,
            'end_time': None
        }
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'tuner_id': self.tuner_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def tune_query(self, index_name: str, query: str,
                   field_weights: Optional[Dict[str, float]] = None,
                   boost_functions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        self.metrics['tunings_performed'] += 1
        query_body = {
            'query': {
                'bool': {
                    'should': []
                }
            },
            'size': 20,
            'track_total_hits': True
        }
        if field_weights:
            for field, weight in field_weights.items():
                query_body['query']['bool']['should'].append({
                    'match': {
                        field: {
                            'query': query,
                            'boost': weight
                        }
                    }
                })
        else:
            query_body['query']['bool']['should'].append({
                'match': {
                    'title': {
                        'query': query,
                        'boost': 2.0
                    }
                }
            })
            query_body['query']['bool']['should'].append({
                'match': {
                    'description': {
                        'query': query,
                        'boost': 1.0
                    }
                }
            })
            query_body['query']['bool']['should'].append({
                'match': {
                    'content': {
                        'query': query,
                        'boost': 0.5
                    }
                }
            })
        if boost_functions:
            query_body['query']['bool']['should'].extend(boost_functions)
        self.generate_evidence('query_tuning', {
            'index': index_name,
            'query': query,
            'field_weights': field_weights
        })
        try:
            result = self.client.search(index_name, query_body)
            return {
                'hits': result['hits']['total']['value'],
                'results': [hit['_source'] for hit in result['hits']['hits']],
                'scores': [hit['_score'] for hit in result['hits']['hits']]
            }
        except Exception as e:
            logger.error(f"Query tuning failed: {str(e)}")
            self.generate_evidence('query_tuning_failed', {'error': str(e)})
            raise
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        return self.evidence_chain