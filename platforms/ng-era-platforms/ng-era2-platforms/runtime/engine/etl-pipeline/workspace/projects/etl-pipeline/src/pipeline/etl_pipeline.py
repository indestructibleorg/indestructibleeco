#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: etl_pipeline
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Complete ETL Pipeline Implementation
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
# MNGA-002: Import organization needs review
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json
import hashlib
from ..extractors.base_extractor import BaseExtractor
from ..transformers.data_transformer import BaseTransformer
from ..loaders.base_loader import BaseLoader
from ..monitoring.monitoring_service import MonitoringService
logger = logging.getLogger(__name__)
class ETLPipeline:
    """
    Complete ETL pipeline orchestration.
    Implements extract, transform, load workflow with monitoring and evidence.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ETL pipeline.
        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.pipeline_name = config.get('name', 'etl-pipeline')
        self.pipeline_id = config.get('id', 'unknown')
        self.extractors = []
        self.transformers = []
        self.loaders = []
        self.monitoring = MonitoringService(config.get('monitoring', {}))
        self.evidence_chain = []
        self.pipeline_metrics = {
            'total_records_processed': 0,
            'total_errors': 0,
            'start_time': None,
            'end_time': None,
            'status': 'idle'
        }
    def add_extractor(self, extractor: BaseExtractor):
        """Add extractor to pipeline."""
        self.extractors.append(extractor)
        logger.info(f"Added extractor: {extractor.extractor_name}")
    def add_transformer(self, transformer: BaseTransformer):
        """Add transformer to pipeline."""
        self.transformers.append(transformer)
        logger.info(f"Added transformer: {transformer.transformer_name}")
    def add_loader(self, loader: BaseLoader):
        """Add loader to pipeline."""
        self.loaders.append(loader)
        logger.info(f"Added loader: {loader.loader_name}")
    def execute(self, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute complete ETL pipeline.
        Args:
            query: Optional query for extractors
        Returns:
            Pipeline execution results
        """
        self.pipeline_metrics['start_time'] = datetime.utcnow()
        self.pipeline_metrics['status'] = 'running'
        self._generate_evidence('pipeline_start', {'extractors': len(self.extractors)})
        try:
            results = {
                'pipeline_name': self.pipeline_name,
                'pipeline_id': self.pipeline_id,
                'extraction_results': [],
                'transformation_results': [],
                'loading_results': [],
                'total_records_processed': 0,
                'total_errors': 0,
                'duration_seconds': 0,
                'success': False
            }
            data = []
            for extractor in self.extractors:
                try:
                    extractor_data = extractor.execute(query)
                    data.extend(extractor_data)
                    results['extraction_results'].append({
                        'extractor': extractor.extractor_name,
                        'records_extracted': len(extractor_data),
                        'metrics': extractor.get_metrics()
                    })
                    self.monitoring.collect_pipeline_metrics(
                        f"{self.pipeline_name}.{extractor.extractor_name}",
                        extractor.get_metrics()
                    )
                except Exception as e:
                    logger.error(f"Extractor {extractor.extractor_name} failed: {str(e)}")
                    self.pipeline_metrics['total_errors'] += 1
                    self.monitoring.alert(
                        severity='CRITICAL',
                        message=f"Extractor failed: {extractor.extractor_name}",
                        details={'error': str(e)}
                    )
                    raise
            for transformer in self.transformers:
                try:
                    data = transformer.execute(data)
                    results['transformation_results'].append({
                        'transformer': transformer.transformer_name,
                        'records_transformed': len(data),
                        'metrics': transformer.get_metrics()
                    })
                    self.monitoring.collect_pipeline_metrics(
                        f"{self.pipeline_name}.{transformer.transformer_name}",
                        transformer.get_metrics()
                    )
                except Exception as e:
                    logger.error(f"Transformer {transformer.transformer_name} failed: {str(e)}")
                    self.pipeline_metrics['total_errors'] += 1
                    self.monitoring.alert(
                        severity='CRITICAL',
                        message=f"Transformer failed: {transformer.transformer_name}",
                        details={'error': str(e)}
                    )
                    raise
            for loader in self.loaders:
                try:
                    table_name = getattr(loader, 'target_table', None) or self.config.get('target_table')
                    loader.execute(data, table_name)
                    results['loading_results'].append({
                        'loader': loader.loader_name,
                        'records_loaded': loader.metrics['records_loaded'],
                        'metrics': loader.get_metrics()
                    })
                    self.monitoring.collect_pipeline_metrics(
                        f"{self.pipeline_name}.{loader.loader_name}",
                        loader.get_metrics()
                    )
                except Exception as e:
                    logger.error(f"Loader {loader.loader_name} failed: {str(e)}")
                    self.pipeline_metrics['total_errors'] += 1
                    self.monitoring.alert(
                        severity='CRITICAL',
                        message=f"Loader failed: {loader.loader_name}",
                        details={'error': str(e)}
                    )
                    raise
            results['total_records_processed'] = len(data)
            results['total_errors'] = self.pipeline_metrics['total_errors']
            results['success'] = True
            self.pipeline_metrics['total_records_processed'] = len(data)
            self.pipeline_metrics['status'] = 'completed'
            self._generate_evidence('pipeline_complete', results)
            return results
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            self.pipeline_metrics['status'] = 'failed'
            self.pipeline_metrics['total_errors'] += 1
            self._generate_evidence('pipeline_error', {'error': str(e)})
            raise
        finally:
            self.pipeline_metrics['end_time'] = datetime.utcnow()
            duration = (self.pipeline_metrics['end_time'] - self.pipeline_metrics['start_time']).total_seconds()
            results['duration_seconds'] = duration
            self.monitoring.collect_pipeline_metrics(self.pipeline_name, self.pipeline_metrics)
    def _generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """Generate evidence entry."""
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'pipeline': self.pipeline_name,
            'pipeline_id': self.pipeline_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        logger.info(f"Evidence generated: {evidence_hash}")
        return evidence_hash
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics."""
        return self.pipeline_metrics.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        """Get complete evidence chain."""
        return self.evidence_chain
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        return {
            'name': self.pipeline_name,
            'id': self.pipeline_id,
            'status': self.pipeline_metrics['status'],
            'extractors': len(self.extractors),
            'transformers': len(self.transformers),
            'loaders': len(self.loaders)
        }
