# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: faceted_search
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Faceted Search Implementation
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
class FacetedSearch:
    def __init__(self, client: EsClientManager, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.search_id = config.get('id', 'faceted-search')
        self.facet_fields = config.get('facet_fields', [])
        self.search_fields = config.get('search_fields', ['title', 'description', 'content'])
        self.evidence_chain = []
        self.metrics = {
            'searches_performed': 0,
            'facets_returned': 0,
            'start_time': None,
            'end_time': None
        }
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'search_id': self.search_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def search(self, index_name: str, query: str,
               filters: Optional[Dict[str, Any]] = None,
               page: int = 1,
               page_size: int = 20) -> Dict[str, Any]:
        self.metrics['searches_performed'] += 1
        query_body = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'multi_match': {
                                'query': query,
                                'fields': self.search_fields,
                                'type': 'best_fields'
                            }
                        }
                    ]
                }
            },
            'aggs': {},
            'from': (page - 1) * page_size,
            'size': page_size,
            'track_total_hits': True
        }
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    query_body['query']['bool']['must'].append({'terms': {field: value}})
                else:
                    query_body['query']['bool']['must'].append({'term': {field: value}})
        for facet_field in self.facet_fields:
            query_body['aggs'][facet_field] = {
                'terms': {
                    'field': facet_field,
                    'size': 100
                }
            }
        self.generate_evidence('faceted_search_executed', {
            'index': index_name,
            'query': query,
            'filters': filters,
            'facet_fields': self.facet_fields
        })
        try:
            result = self.client.search(index_name, query_body)
            facets = {}
            for facet_field in self.facet_fields:
                if facet_field in result.get('aggregations', {}):
                    buckets = result['aggregations'][facet_field]['buckets']
                    facets[facet_field] = [
                        {'value': bucket['key'], 'count': bucket['doc_count']}
                        for bucket in buckets
                    ]
            self.metrics['facets_returned'] += len(facets)
            return {
                'hits': result['hits']['total']['value'],
                'results': [hit['_source'] for hit in result['hits']['hits']],
                'facets': facets,
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            logger.error(f"Faceted search failed: {str(e)}")
            self.generate_evidence('faceted_search_failed', {'error': str(e)})
            raise
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        return self.evidence_chain
