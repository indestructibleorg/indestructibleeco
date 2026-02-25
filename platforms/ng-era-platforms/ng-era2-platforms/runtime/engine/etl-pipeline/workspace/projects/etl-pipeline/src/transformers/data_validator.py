#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: data_validator
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Data Validator Module
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timezone
import hashlib
import json
logger = logging.getLogger(__name__)
class DataValidator:
    """
    Comprehensive data validation module with evidence generation.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validator_name = config.get('name', 'data-validator')
        self.validator_id = config.get('id', 'unknown')
        self.evidence_chain = []
        self.validation_rules = config.get('validation_rules', {})
        self.quality_thresholds = config.get('quality_thresholds', {
            'completeness': 99.9,
            'accuracy': 99.9,
            'consistency': 100.0,
            'timeliness': 5.0
        })
        self.metrics = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'quality_scores': {},
            'start_time': None,
            'end_time': None
        }
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """Generate evidence entry for validation operation."""
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'validator': self.validator_name,
            'validator_id': self.validator_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        logger.info(f"Evidence generated: {evidence_hash}")
        return evidence_hash
    def validate_all(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run all validation checks."""
        self.metrics['start_time'] = datetime.utcnow()
        self.metrics['total_records'] = len(data)
        self.metrics['valid_records'] = 0
        self.metrics['invalid_records'] = 0
        self.metrics['quality_scores'] = {}
        self.metrics['timeliness_seconds'] = 0.0
        self.generate_evidence('validation_start', {'record_count': len(data)})
        validation_report = {
            'overall_passed': True,
            'validation_results': {},
            'quality_scores': {},
            'metrics': {}
        }
        try:
            validation_report['validation_results'] = self._validate_records(data)
            validation_report['overall_passed'] = validation_report['validation_results']['passed']
            self.metrics['timeliness_seconds'] = self._calculate_timeliness(data)
            self.metrics['quality_scores'] = self._calculate_quality_scores()
            validation_report['quality_scores'] = self.metrics['quality_scores']
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            self.generate_evidence('validation_error', {'error': str(e)})
            raise
        finally:
            self.metrics['end_time'] = datetime.utcnow()
            validation_report['metrics'] = self.metrics
            self.generate_evidence('validation_end', self.metrics)
        return validation_report
    def get_metrics(self) -> Dict[str, Any]:
        """Get validation metrics."""
        return self.metrics
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        """Get complete evidence chain."""
        return self.evidence_chain
    def _validate_records(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate records against configured rules."""
        results = {
            'passed': True,
            'errors': []
        }
        required_fields = self.validation_rules.get('required_fields', [])
        field_rules = self.validation_rules.get('field_rules', {})
        for record in data:
            record_errors = []
            for field in required_fields:
                if record.get(field) in (None, ''):
                    record_errors.append(f"Missing required field: {field}")
            for field, rule in field_rules.items():
                if field not in record:
                    continue
                value = record.get(field)
                if value is None:
                    continue
                expected_type = rule.get('type')
                if isinstance(expected_type, str):
                    type_map = {
                        'string': str,
                        'integer': int,
                        'float': float,
                        'boolean': bool
                    }
                    expected_type = type_map.get(expected_type)
                if expected_type and not isinstance(value, expected_type):
                    record_errors.append(f"Invalid type for {field}: {type(value).__name__}")
            if record_errors:
                self.metrics['invalid_records'] += 1
                results['errors'].append(record_errors)
            else:
                self.metrics['valid_records'] += 1
        if results['errors']:
            results['passed'] = False
        return results
    def _calculate_quality_scores(self) -> Dict[str, float]:
        """Calculate quality scores based on metrics and thresholds."""
        total_records = self.metrics['total_records'] or 1
        completeness = (self.metrics['valid_records'] / total_records) * 100
        accuracy = completeness if self.metrics['invalid_records'] == 0 else 0.0
        consistency = 100.0 if self.metrics['invalid_records'] == 0 else 0.0
        timeliness = self.metrics.get('timeliness_seconds', 0.0)
        return {
            'completeness': completeness,
            'accuracy': accuracy,
            'consistency': consistency,
            'timeliness': timeliness
        }
    def _calculate_timeliness(self, data: List[Dict[str, Any]]) -> float:
        """Calculate average data timeliness in seconds."""
        field_name = (
            self.validation_rules.get('timeliness_field')
            or self.validation_rules.get('timestamp_field')
        )
        if not field_name:
            return 0.0
        now = datetime.now(timezone.utc)
        deltas = []
        for record in data:
            timestamp_value = record.get(field_name)
            if not timestamp_value:
                continue
            parsed = self._parse_timestamp(timestamp_value)
            if parsed:
                deltas.append((now - parsed).total_seconds())
        if not deltas:
            return 0.0
        return sum(deltas) / len(deltas)
    @staticmethod
    def _normalize_timestamp(value: datetime) -> datetime:
        """Normalize timestamps to timezone-aware UTC."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse timestamp values into timezone-aware datetimes."""
        if isinstance(value, datetime):
            return self._normalize_timestamp(value)
        if not isinstance(value, str):
            return None
        normalized = value.replace('Z', '+00:00')
        try:
            return self._normalize_timestamp(datetime.fromisoformat(normalized))
        except ValueError:
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
                try:
                    return self._normalize_timestamp(datetime.strptime(value, fmt))
                except ValueError:
                    continue
        return None
