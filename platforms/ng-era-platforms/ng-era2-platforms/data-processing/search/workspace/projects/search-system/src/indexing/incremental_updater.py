# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: incremental_updater
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Incremental Update Service
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
class IncrementalUpdater:
    def __init__(self, client: EsClientManager, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.updater_id = config.get('id', 'incremental-updater')
        self.change_detection_field = config.get('change_detection_field', 'updated_at')
        self.enable_hashing = config.get('enable_hashing', True)
        self.evidence_chain = []
        self.metrics = {
            'documents_checked': 0,
            'documents_updated': 0,
            'documents_created': 0,
            'documents_deleted': 0,
            'unchanged_documents': 0,
            'start_time': None,
            'end_time': None
        }
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'updater_id': self.updater_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def update_incremental(self, index_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.metrics['start_time'] = datetime.utcnow()
        self.generate_evidence('incremental_update_start', {
            'index': index_name,
            'documents': len(documents)
        })
        try:
            results = {
                'updated': 0,
                'created': 0,
                'deleted': 0,
                'unchanged': 0
            }
            doc_lookup = self._fetch_existing_documents(index_name, documents)
            for document in documents:
                doc_id = document.get('id')
                if not doc_id:
                    continue
                self.metrics['documents_checked'] += 1
                change_type = self._detect_change(doc_lookup, doc_id, document)
                if change_type == 'create':
                    self.client.index_document(index_name, doc_id, document)
                    results['created'] += 1
                    self.metrics['documents_created'] += 1
                elif change_type == 'update':
                    self.client.index_document(index_name, doc_id, document)
                    results['updated'] += 1
                    self.metrics['documents_updated'] += 1
                elif change_type == 'delete':
                    self.client.client.delete(index=index_name, id=doc_id)
                    results['deleted'] += 1
                    self.metrics['documents_deleted'] += 1
                else:
                    results['unchanged'] += 1
                    self.metrics['unchanged_documents'] += 1
            self.generate_evidence('incremental_update_complete', {
                'index': index_name,
                'results': results
            })
            return results
        except Exception as e:
            logger.error(f"Incremental update failed: {str(e)}")
            self.generate_evidence('incremental_update_failed', {'error': str(e)})
            raise
        finally:
            self.metrics['end_time'] = datetime.utcnow()
    def _detect_change(self, existing_docs: Dict[str, Any], doc_id: str, new_document: Dict[str, Any]) -> str:
        try:
            existing_source = existing_docs.get(doc_id)
            if not existing_source:
                return 'create'
            if self.enable_hashing:
                new_hash = self._compute_hash(new_document)
                existing_hash = self._compute_hash(existing_source)
                if new_hash == existing_hash:
                    return 'unchanged'
            return 'update'
        except Exception:
            return 'create'
    def _compute_hash(self, document: Dict[str, Any]) -> str:
        doc_copy = document.copy()
        doc_copy.pop(self.change_detection_field, None)
        hash_input = json.dumps(doc_copy, sort_keys=True)
        return hashlib.sha256(hash_input.encode()).hexdigest()
    def _fetch_existing_documents(self, index_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        doc_ids = [doc.get('id') for doc in documents if doc.get('id')]
        if not doc_ids:
            return {}
        existing_docs = {}
        batch_size = self.config.get('mget_batch_size', 500)
        total_docs = len(doc_ids)
        for start in range(0, total_docs, batch_size):
            end = min(start + batch_size, total_docs)
            batch_ids = doc_ids[start:end]
            try:
                response = self.client.client.mget(
                    docs=[{'_index': index_name, '_id': doc_id} for doc_id in batch_ids]
                )
                for doc in response.get('docs', []):
                    if doc.get('found'):
                        existing_docs[doc['_id']] = doc.get('_source')
            except Exception as e:
                logger.warning(f"Failed to fetch existing documents: {str(e)}")
        return existing_docs
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        return self.evidence_chain
