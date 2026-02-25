# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: bulk_indexer
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Bulk Indexing Service
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
# MNGA-002: Import organization needs review
from typing import Dict, Any, List
import logging
from datetime import datetime
import hashlib
import json
import time
from ..elasticsearch.client import EsClientManager
logger = logging.getLogger(__name__)
class BulkIndexer:
    """Bulk indexing with batching and progress tracking."""
    def __init__(self, client: EsClientManager, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.indexer_id = config.get('id', 'bulk-indexer')
        self.batch_size = config.get('batch_size', 1000)
        self.max_retries = config.get('max_retries', 3)
        self.evidence_chain = []
        self.metrics = {
            'total_documents': 0,
            'indexed_documents': 0,
            'failed_documents': 0,
            'batches_processed': 0,
            'start_time': None,
            'end_time': None
        }
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """Generate evidence entry."""
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'indexer_id': self.indexer_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def index_documents(self, index_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index documents in batches."""
        self.metrics['start_time'] = datetime.utcnow()
        self.metrics['total_documents'] = len(documents)
        self.generate_evidence('bulk_indexing_start', {
            'index': index_name,
            'total_documents': len(documents),
            'batch_size': self.batch_size
        })
        try:
            results = {
                'indexed': 0,
                'failed': 0,
                'batches': 0
            }
            for i in range(0, len(documents), self.batch_size):
                batch = documents[i:i + self.batch_size]
                batch_result = self._index_batch(index_name, batch)
                results['indexed'] += batch_result['success']
                results['failed'] += batch_result['failed']
                results['batches'] += 1
                self.metrics['batches_processed'] += 1
                logger.info(f"Processed batch {results['batches']}: {batch_result['success']} indexed, {batch_result['failed']} failed")
            self.metrics['indexed_documents'] = results['indexed']
            self.metrics['failed_documents'] = results['failed']
            self.generate_evidence('bulk_indexing_complete', {
                'index': index_name,
                'results': results
            })
            return results
        except Exception as e:
            logger.error(f"Bulk indexing failed: {str(e)}")
            self.generate_evidence('bulk_indexing_failed', {'error': str(e)})
            raise
        finally:
            self.metrics['end_time'] = datetime.utcnow()
    def _index_batch(self, index_name: str, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index a single batch with retry logic."""
        for attempt in range(self.max_retries):
            try:
                result = self.client.bulk_index(index_name, batch)
                return {
                    'success': result['success'],
                    'failed': len(result['failed'])
                }
            except Exception as e:
                logger.warning(f"Batch indexing attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return {'success': 0, 'failed': len(batch)}
    def get_metrics(self) -> Dict[str, Any]:
        """Get indexing metrics."""
        return self.metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        """Get evidence chain."""
        return self.evidence_chain
