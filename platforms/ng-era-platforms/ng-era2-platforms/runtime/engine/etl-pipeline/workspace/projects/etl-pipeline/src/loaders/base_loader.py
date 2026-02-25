#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: base_loader
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Base Loader Module
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import hashlib
import json
logger = logging.getLogger(__name__)
class BaseLoader(ABC):
    """
    Abstract base class for data loaders.
    Implements common loading patterns and evidence generation.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize loader with configuration.
        Args:
            config: Loader configuration dictionary
        """
        self.config = config
        self.loader_name = config.get('name', 'base-loader')
        self.loader_id = config.get('id', 'unknown')
        self.target_type = config.get('target_type', 'unknown')
        self.evidence_chain = []
        self.metrics = {
            'records_loaded': 0,
            'records_failed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to target system.
        Returns:
            bool: True if connection successful
        """
        pass
    @abstractmethod
    def load(self, data: List[Dict[str, Any]], table_name: Optional[str] = None) -> bool:
        """
        Load data into target system.
        Args:
            data: Data to load
            table_name: Optional target table/collection name
        Returns:
            bool: True if load successful
        """
        pass
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to target system.
        Returns:
            bool: True if disconnection successful
        """
        pass
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """
        Generate evidence entry for operation.
        Args:
            operation: Operation name
            details: Operation details
        Returns:
            Evidence hash
        """
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'loader': self.loader_name,
            'loader_id': self.loader_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        logger.info(f"Evidence generated: {evidence_hash}")
        return evidence_hash
    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Validate data before loading.
        Args:
            data: Data to validate
        Returns:
            bool: True if validation passes
        """
        if not isinstance(data, list):
            logger.error("Data to load must be a list")
            return False
        if len(data) == 0:
            logger.warning("No data to load")
            return True
        return True
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get loading metrics.
        Returns:
            Dictionary of metrics
        """
        if self.metrics['start_time'] and self.metrics['end_time']:
            duration = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
            self.metrics['duration_seconds'] = duration
        return self.metrics
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        """
        Get complete evidence chain.
        Returns:
            List of evidence entries
        """
        return self.evidence_chain
    def execute(self, data: List[Dict[str, Any]], table_name: Optional[str] = None) -> bool:
        """
        Execute complete loading workflow.
        Args:
            data: Data to load
            table_name: Optional target table/collection name
        Returns:
            bool: True if load successful
        """
        self.metrics['start_time'] = datetime.utcnow()
        self.generate_evidence('loading_start', {'record_count': len(data), 'table': table_name})
        try:
            if not self.validate_data(data):
                raise Exception("Data validation failed")
            self.generate_evidence('validation_success', {})
            if not self.connect():
                raise Exception("Connection failed")
            self.generate_evidence('connection_success', {})
            if not self.load(data, table_name):
                raise Exception("Load operation failed")
            self.generate_evidence('loading_complete', {
                'records_loaded': self.metrics['records_loaded']
            })
            return True
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Loading failed: {str(e)}")
            self.generate_evidence('loading_error', {'error': str(e)})
            raise
        finally:
            self.disconnect()
            self.metrics['end_time'] = datetime.utcnow()
            self.generate_evidence('loading_end', self.get_metrics())