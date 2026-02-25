# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: search_analytics
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Search Analytics Collector
ECO-Layer: GL50-59 (Observability)
Closure-Signal: metrics, insights
"""
# MNGA-002: Import organization needs review
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import hashlib
import json
from ..elasticsearch.client import EsClientManager
logger = logging.getLogger(__name__)
class SearchAnalytics:
    def __init__(self, client: EsClientManager, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.analytics_id = config.get('id', 'search-analytics')
        self.analytics_index = config.get('analytics_index', 'search_analytics')
        self.evidence_chain = []
        self.metrics = {
            'queries_logged': 0,
            'events_collected': 0,
            'start_time': None,
            'end_time': None
        }
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'analytics_id': self.analytics_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def log_search_query(self, index_name: str, query: str, 
                         results_count: int, query_time_ms: int,
                         user_id: Optional[str] = None,
                         filters: Optional[Dict[str, Any]] = None) -> bool:
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'search_query',
            'index_name': index_name,
            'query': query,
            'results_count': results_count,
            'query_time_ms': query_time_ms,
            'user_id': user_id,
            'filters': filters
        }
        event['hash'] = self._compute_event_hash(query, filters or {})
        try:
            event_id = self._compute_event_id({
                'timestamp': event['timestamp'],
                'event_type': event['event_type'],
                'index_name': event['index_name'],
                'event_hash': event['hash']
            })
            self.client.index_document(self.analytics_index, event_id, event)
            self.metrics['queries_logged'] += 1
            self.metrics['events_collected'] += 1
            self.generate_evidence('search_query_logged', {
                'index': index_name,
                'query': query,
                'results': results_count
            })
            return True
        except Exception as e:
            logger.error(f"Failed to log search query: {str(e)}")
            return False
    def log_click_event(self, index_name: str, query: str,
                        document_id: str, position: int,
                        user_id: Optional[str] = None) -> bool:
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'document_click',
            'index_name': index_name,
            'query': query,
            'document_id': document_id,
            'position': position,
            'user_id': user_id
        }
        event['hash'] = self._compute_event_hash(query, {'document_id': document_id})
        try:
            event_id = self._compute_event_id({
                'timestamp': event['timestamp'],
                'event_type': event['event_type'],
                'index_name': event['index_name'],
                'event_hash': event['hash']
            })
            self.client.index_document(self.analytics_index, event_id, event)
            self.metrics['events_collected'] += 1
            self.generate_evidence('click_event_logged', {
                'index': index_name,
                'document_id': document_id,
                'position': position
            })
            return True
        except Exception as e:
            logger.error(f"Failed to log click event: {str(e)}")
            return False
    def get_search_trends(self, hours: int = 24) -> Dict[str, Any]:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        query_body = {
            'query': {
                'bool': {
                    'must': [
                        {'term': {'event_type': 'search_query'}},
                        {'range': {'timestamp': {'gte': start_time.isoformat(), 'lte': end_time.isoformat()}}}
                    ]
                }
            },
            'aggs': {
                'top_queries': {
                    'terms': {
                        'field': 'query.keyword',
                        'size': 10
                    }
                },
                'queries_over_time': {
                    'date_histogram': {
                        'field': 'timestamp',
                        'calendar_interval': '1h'
                    }
                },
                'avg_results': {
                    'avg': {
                        'field': 'results_count'
                    }
                },
                'avg_query_time': {
                    'avg': {
                        'field': 'query_time_ms'
                    }
                }
            }
        }
        try:
            result = self.client.search(self.analytics_index, query_body)
            top_queries = [
                {'query': bucket['key'], 'count': bucket['doc_count']}
                for bucket in result['aggregations']['top_queries']['buckets']
            ]
            queries_over_time = [
                {'timestamp': bucket['key_as_string'], 'count': bucket['doc_count']}
                for bucket in result['aggregations']['queries_over_time']['buckets']
            ]
            return {
                'period_hours': hours,
                'total_queries': result['hits']['total']['value'],
                'top_queries': top_queries,
                'queries_over_time': queries_over_time,
                'average_results': result['aggregations']['avg_results']['value'],
                'average_query_time_ms': result['aggregations']['avg_query_time']['value']
            }
        except Exception as e:
            logger.error(f"Failed to get search trends: {str(e)}")
            return {}
    def get_zero_result_queries(self, hours: int = 24) -> List[Dict[str, Any]]:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        query_body = {
            'query': {
                'bool': {
                    'must': [
                        {'term': {'event_type': 'search_query'}},
                        {'term': {'results_count': 0}},
                        {'range': {'timestamp': {'gte': start_time.isoformat(), 'lte': end_time.isoformat()}}}
                    ]
                }
            },
            'aggs': {
                'zero_result_queries': {
                    'terms': {
                        'field': 'query.keyword',
                        'size': 20
                    }
                }
            }
        }
        try:
            result = self.client.search(self.analytics_index, query_body)
            return [
                {'query': bucket['key'], 'count': bucket['doc_count']}
                for bucket in result['aggregations']['zero_result_queries']['buckets']
            ]
        except Exception as e:
            logger.error(f"Failed to get zero-result queries: {str(e)}")
            return []
    def _compute_event_hash(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        hash_input = {'query': query}
        if params:
            hash_input.update(params)
        hash_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()
    def _compute_event_id(self, event: Dict[str, Any]) -> str:
        hash_input = {
            'timestamp': event.get('timestamp'),
            'event_type': event.get('event_type'),
            'index_name': event.get('index_name'),
            'event_hash': event.get('event_hash')
        }
        hash_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        return self.evidence_chain
