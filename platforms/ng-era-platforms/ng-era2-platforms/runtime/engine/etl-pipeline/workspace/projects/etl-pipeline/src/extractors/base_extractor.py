#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: base_extractor
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Base Extractor Module
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
class BaseExtractor(ABC):
    """
    Abstract base class for all data extractors.
    Implements common extraction patterns and evidence generation.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize extractor with configuration.
        Args:
            config: Extractor configuration dictionary
        """
        self.config = config
        self.extractor_name = config.get('name', 'base-extractor')
        self.extractor_id = config.get('id', 'unknown')
        self.source_type = config.get('source_type', 'unknown')
        self.evidence_chain = []
        self.metrics = {
            'records_extracted': 0,
            'errors': 0,
            'warnings': 0,
            'start_time': None,
            'end_time': None
        }
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to data source.
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    @abstractmethod
    def extract(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract data from source.
        Args:
            query: Optional query or filter criteria
        Returns:
            List of extracted records
        """
        pass
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to data source.
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
            'extractor': self.extractor_name,
            'extractor_id': self.extractor_id,
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
        Validate extracted data structure.
        Args:
            data: Extracted data
        Returns:
            bool: True if validation passes
        """
        if not isinstance(data, list):
            logger.error("Extracted data must be a list")
            self.generate_evidence('validation_error', {'error': 'Data is not a list'})
            return False
        for i, record in enumerate(data[:10]):  # Sample first 10 records
            if not isinstance(record, dict):
                logger.error(f"Record {i} is not a dictionary")
                self.generate_evidence('validation_error', {
                    'error': 'Record not a dictionary',
                    'index': i
                })
                return False
        return True
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get extraction metrics.
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
    def execute(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Execute complete extraction workflow.
        Args:
            query: Optional query or filter criteria
        Returns:
            List of extracted records
        """
        self.metrics['start_time'] = datetime.utcnow()
        self.generate_evidence('extraction_start', {'query': query})
        try:
            # Connect
            if not self.connect():
                raise Exception("Connection failed")
            self.generate_evidence('connection_success', {})
            # Extract
            data = self.extract(query)
            self.metrics['records_extracted'] = len(data)
            self.generate_evidence('extraction_complete', {
                'record_count': len(data)
            })
            # Validate
            if not self.validate_data(data):
                raise Exception("Data validation failed")
            self.generate_evidence('validation_success', {})
            return data
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Extraction failed: {str(e)}")
            self.generate_evidence('extraction_error', {'error': str(e)})
            raise
        finally:
            # Disconnect
            self.disconnect()
            self.metrics['end_time'] = datetime.utcnow()
            self.generate_evidence('extraction_end', self.get_metrics())