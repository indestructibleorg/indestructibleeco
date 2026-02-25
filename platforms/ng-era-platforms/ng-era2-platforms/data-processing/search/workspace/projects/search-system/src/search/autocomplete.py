# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: autocomplete
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Autocomplete Implementation
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
class Autocomplete:
    def __init__(self, client: EsClientManager, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.autocomplete_id = config.get('id', 'autocomplete')
        self.suggestion_fields = config.get('suggestion_fields', ['title', 'tags'])
        self.max_suggestions = config.get('max_suggestions', 10)
        self.source_fields = config.get('source_fields', ['id', 'title', 'type'])
        self.evidence_chain = []
        self.metrics = {
            'queries_performed': 0,
            'suggestions_returned': 0,
            'start_time': None,
            'end_time': None
        }
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'autocomplete_id': self.autocomplete_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def suggest(self, index_name: str, query: str) -> List[Dict[str, Any]]:
        self.metrics['queries_performed'] += 1
        query_body = {
            'query': {
                'bool': {
                    'should': [
                        {
                            'match_phrase_prefix': {
                                'title.suggest': {
                                    'query': query,
                                    'max_expansions': 10
                                }
                            }
                        },
                        {
                            'match': {
                                'title': {
                                    'query': query,
                                    'operator': 'and'
                                }
                            }
                        }
                    ],
                    'minimum_should_match': 1
                }
            },
            'size': self.max_suggestions,
            '_source': self.source_fields
        }
        self.generate_evidence('autocomplete_suggestion', {
            'index': index_name,
            'query': query
        })
        try:
            result = self.client.search(index_name, query_body)
            suggestions = [
                hit['_source']
                for hit in result['hits']['hits']
            ]
            self.metrics['suggestions_returned'] += len(suggestions)
            return suggestions
        except Exception as e:
            logger.error(f"Autocomplete failed: {str(e)}")
            self.generate_evidence('autocomplete_failed', {'error': str(e)})
            raise
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        return self.evidence_chain
