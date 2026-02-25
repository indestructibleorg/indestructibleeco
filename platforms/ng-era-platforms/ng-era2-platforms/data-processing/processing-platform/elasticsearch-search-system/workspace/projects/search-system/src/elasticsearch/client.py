# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: client
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Elasticsearch Client Manager
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
# MNGA-002: Import organization needs review
from typing import Dict, Any, List
import logging
from datetime import datetime
import hashlib
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
logger = logging.getLogger(__name__)
class EsClientManager:
    """Elasticsearch client with connection pooling and retry logic."""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client_id = config.get('id', 'es-client')
        self.hosts = config.get('hosts', ['http://localhost:9200'])
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_on_timeout = config.get('retry_on_timeout', True)
        self.bulk_id_fields = config.get('bulk_id_fields', ['external_id', 'timestamp', 'uuid'])
        self.evidence_chain = []
        self.client = Elasticsearch(
            hosts=self.hosts,
            timeout=self.timeout,
            max_retries=self.max_retries,
            retry_on_timeout=self.retry_on_timeout,
            verify_certs=config.get('verify_certs', False),
            basic_auth=(
                config.get('username'),
                config.get('password')
            ) if config.get('username') else None
        )
        self.metrics = {
            'queries_executed': 0,
            'indexes_created': 0,
            'documents_indexed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """Generate evidence entry."""
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'client_id': self.client_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def ping(self) -> bool:
        """Check Elasticsearch cluster health."""
        try:
            result = self.client.ping()
            self.generate_evidence('cluster_ping', {'status': 'healthy' if result else 'unhealthy'})
            return result
        except Exception as e:
            self.metrics['errors'] += 1
            self.generate_evidence('cluster_ping_failed', {'error': str(e)})
            return False
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information."""
        try:
            info = self.client.info()
            self.generate_evidence('cluster_info_retrieved', {'cluster_name': info.get('cluster_name')})
            return info
        except Exception as e:
            self.metrics['errors'] += 1
            self.generate_evidence('cluster_info_failed', {'error': str(e)})
            raise
    def create_index(self, index_name: str, mapping: Dict[str, Any]) -> bool:
        """Create index with mapping."""
        try:
            if self.client.indices.exists(index=index_name):
                self.generate_evidence('index_exists', {'index': index_name})
                return True
            self.client.indices.create(index=index_name, body=mapping)
            self.metrics['indexes_created'] += 1
            self.generate_evidence('index_created', {'index': index_name})
            return True
        except Exception as e:
            self.metrics['errors'] += 1
            self.generate_evidence('index_creation_failed', {'index': index_name, 'error': str(e)})
            raise
    def delete_index(self, index_name: str) -> bool:
        """Delete index."""
        try:
            if self.client.indices.exists(index=index_name):
                self.client.indices.delete(index=index_name)
                self.generate_evidence('index_deleted', {'index': index_name})
            return True
        except Exception as e:
            self.metrics['errors'] += 1
            self.generate_evidence('index_deletion_failed', {'index': index_name, 'error': str(e)})
            raise
    def index_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index single document."""
        try:
            self.client.index(index=index_name, id=doc_id, body=document)
            self.metrics['documents_indexed'] += 1
            return True
        except Exception as e:
            self.metrics['errors'] += 1
            self.generate_evidence('document_indexing_failed', {'index': index_name, 'doc_id': doc_id, 'error': str(e)})
            raise
    def bulk_index(self, index_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk index documents."""
        try:
            actions = []
            missing_ids = 0
            for doc in documents:
                doc_id = doc.get('id')
                if not doc_id:
                    missing_ids += 1
                    doc_id = self._generate_bulk_id(index_name, doc)
                actions.append({
                    '_index': index_name,
                    '_id': doc_id,
                    '_source': doc
                })
            if missing_ids:
                self.generate_evidence('bulk_index_missing_ids', {
                    'index': index_name,
                    'missing_ids': missing_ids,
                    'bulk_id_fields': self.bulk_id_fields
                })
            success, failed = bulk(self.client, actions)
            self.metrics['documents_indexed'] += success
            self.generate_evidence('bulk_index_complete', {
                'index': index_name,
                'success': success,
                'failed': len(failed)
            })
            return {
                'success': success,
                'failed': failed,
                'total': len(documents)
            }
        except Exception as e:
            self.metrics['errors'] += 1
            self.generate_evidence('bulk_index_failed', {'index': index_name, 'error': str(e)})
            raise
    def search(self, index_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search query."""
        try:
            self.metrics['queries_executed'] += 1
            result = self.client.search(index=index_name, body=query)
            self.generate_evidence('search_executed', {
                'index': index_name,
                'hits': result['hits']['total']['value']
            })
            return result
        except Exception as e:
            self.metrics['errors'] += 1
            self.generate_evidence('search_failed', {'index': index_name, 'error': str(e)})
            raise
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics."""
        return self.metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        """Get evidence chain."""
        return self.evidence_chain
    def _generate_bulk_id(self, index_name: str, document: Dict[str, Any]) -> str:
        identifier = None
        for field in self.bulk_id_fields:
            if document.get(field):
                identifier = document.get(field)
                break
        if identifier:
            return f"{index_name}-{identifier}"
        return f"{index_name}-{hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()}"
