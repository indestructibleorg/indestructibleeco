# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: full_text_search
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Full-Text Search Implementation
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
class FullTextSearch:
    def __init__(self, client: EsClientManager, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.search_id = config.get('id', 'full-text-search')
        self.default_fields = config.get('default_fields', ['title', 'description', 'content'])
        self.evidence_chain = []
        self.metrics = {
            'searches_performed': 0,
            'total_results': 0,
            'average_query_time': 0,
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
               fields: Optional[List[str]] = None,
               page: int = 1,
               page_size: int = 20,
               filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.metrics['searches_performed'] += 1
        start_time = datetime.utcnow()
        search_fields = fields or self.default_fields
        query_body = {
            'query': {
                'multi_match': {
                    'query': query,
                    'fields': search_fields,
                    'type': 'best_fields',
                    'operator': 'or'
                }
            },
            'from': (page - 1) * page_size,
            'size': page_size,
            'track_total_hits': True
        }
        if filters:
            query_body['post_filter'] = self._build_filters(filters)
        self.generate_evidence('full_text_search_executed', {
            'index': index_name,
            'query': query,
            'fields': search_fields,
            'page': page,
            'page_size': page_size
        })
        try:
            result = self.client.search(index_name, query_body)
            end_time = datetime.utcnow()
            query_time = (end_time - start_time).total_seconds()
            self.metrics['total_results'] += result['hits']['total']['value']
            self.metrics['average_query_time'] = (
                (self.metrics['average_query_time'] * (self.metrics['searches_performed'] - 1) + query_time) /
                self.metrics['searches_performed']
            )
            return {
                'hits': result['hits']['total']['value'],
                'results': [hit['_source'] for hit in result['hits']['hits']],
                'page': page,
                'page_size': page_size,
                'total_pages': (result['hits']['total']['value'] + page_size - 1) // page_size,
                'query_time_ms': int(query_time * 1000)
            }
        except Exception as e:
            logger.error(f"Full-text search failed: {str(e)}")
            self.generate_evidence('full_text_search_failed', {'error': str(e)})
            raise
    def _build_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        filter_clauses = []
        for field, value in filters.items():
            if isinstance(value, list):
                filter_clauses.append({'terms': {field: value}})
            elif isinstance(value, dict):
                if 'gte' in value or 'lte' in value:
                    range_filter = {'range': {field: {}}}
                    if 'gte' in value and value['gte'] is not None:
                        range_filter['range'][field]['gte'] = value['gte']
                    if 'lte' in value and value['lte'] is not None:
                        range_filter['range'][field]['lte'] = value['lte']
                    if any(value is not None for value in range_filter['range'][field].values()):
                        filter_clauses.append(range_filter)
            else:
                filter_clauses.append({'term': {field: value}})
        return {'bool': {'must': filter_clauses}}
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        return self.evidence_chain
