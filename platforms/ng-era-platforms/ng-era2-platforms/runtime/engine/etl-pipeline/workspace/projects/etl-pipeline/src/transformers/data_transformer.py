#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: data_transformer
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Data Transformer Module
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
from typing import Dict, Any, List
import logging
from datetime import datetime
from abc import ABC, abstractmethod
import hashlib
import json
logger = logging.getLogger(__name__)
class BaseTransformer(ABC):
    """
    Abstract base class for data transformers.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.transformer_name = config.get('name', 'base-transformer')
        self.transformer_id = config.get('id', 'unknown')
        self.evidence_chain = []
        self.metrics = {
            'records_transformed': 0,
            'records_filtered': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    @abstractmethod
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform data according to rules.
        Args:
            data: Input data
        Returns:
            Transformed data
        """
        pass
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """Generate evidence entry for operation."""
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'transformer': self.transformer_name,
            'transformer_id': self.transformer_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        logger.info(f"Evidence generated: {evidence_hash}")
        return evidence_hash
    def get_metrics(self) -> Dict[str, Any]:
        """Get transformation metrics."""
        if self.metrics['start_time'] and self.metrics['end_time']:
            duration = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
            self.metrics['duration_seconds'] = duration
        return self.metrics
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        """Get complete evidence chain."""
        return self.evidence_chain
    def execute(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute complete transformation workflow."""
        self.metrics['start_time'] = datetime.utcnow()
        self.generate_evidence('transformation_start', {'input_count': len(data)})
        try:
            transformed_data = self.transform(data)
            self.metrics['records_transformed'] = len(transformed_data)
            self.generate_evidence('transformation_complete', {
                'output_count': len(transformed_data)
            })
            return transformed_data
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Transformation failed: {str(e)}")
            self.generate_evidence('transformation_error', {'error': str(e)})
            raise
        finally:
            self.metrics['end_time'] = datetime.utcnow()
            self.generate_evidence('transformation_end', self.get_metrics())
class DataCleaner(BaseTransformer):
    """
    Data cleaning transformer.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cleaning_rules = config.get('cleaning_rules', {})
        self.remove_nulls = config.get('remove_nulls', True)
        self.remove_duplicates = config.get('remove_duplicates', True)
        self.trim_strings = config.get('trim_strings', True)
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean data according to rules."""
        cleaned_data = []
        seen_hashes = set() if self.remove_duplicates else None
        for record in data:
            try:
                cleaned_record = {}
                for key, value in record.items():
                    if value is None:
                        if self.remove_nulls:
                            continue
                        else:
                            cleaned_record[key] = None
                            continue
                    if isinstance(value, str):
                        if self.trim_strings:
                            value = value.strip()
                        if not value:
                            if self.remove_nulls:
                                continue
                    cleaned_record[key] = value
                if not cleaned_record:
                    self.metrics['records_filtered'] += 1
                    continue
                if seen_hashes is not None:
                    record_hash = hashlib.sha256(json.dumps(cleaned_record, sort_keys=True).encode()).hexdigest()
                    if record_hash in seen_hashes:
                        self.metrics['records_filtered'] += 1
                        continue
                    seen_hashes.add(record_hash)
                cleaned_data.append(cleaned_record)
            except Exception as e:
                logger.error(f"Error cleaning record: {str(e)}")
                self.metrics['errors'] += 1
        logger.info(f"Cleaned {len(cleaned_data)} records, filtered {self.metrics['records_filtered']}")
        return cleaned_data
class SchemaNormalizer(BaseTransformer):
    """
    Schema normalization transformer.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.target_schema = config.get('target_schema', {})
        self.rename_fields = config.get('rename_fields', {})
        self.type_conversions = config.get('type_conversions', {})
        self.default_values = config.get('default_values', {})
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize schema according to target schema."""
        normalized_data = []
        for record in data:
            try:
                normalized_record = {}
                record_valid = True
                for field_name, field_config in self.target_schema.items():
                    source_field = self.rename_fields.get(field_name, field_name)
                    value = record.get(source_field)
                    if value is None:
                        value = self.default_values.get(field_name)
                    if value is None:
                        if field_config.get('required', False):
                            self.metrics['records_filtered'] += 1
                            record_valid = False
                            break
                        else:
                            normalized_record[field_name] = None
                            continue
                    type_conversion = self.type_conversions.get(field_name)
                    if type_conversion:
                        value = self._convert_type(value, type_conversion)
                    normalized_record[field_name] = value
                if record_valid:
                    normalized_data.append(normalized_record)
            except Exception as e:
                logger.error(f"Error normalizing record: {str(e)}")
                self.metrics['errors'] += 1
        logger.info(f"Normalized {len(normalized_data)} records")
        return normalized_data
    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to target type."""
        try:
            if target_type == 'string':
                return str(value)
            elif target_type == 'integer':
                return int(value)
            elif target_type == 'float':
                return float(value)
            elif target_type == 'boolean':
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes']
                return bool(value)
            elif target_type == 'datetime':
                if isinstance(value, str):
                    normalized_value = value.replace('Z', '+00:00')
                    try:
                        return datetime.fromisoformat(normalized_value).isoformat()
                    except ValueError:
                        for fmt in (
                            '%Y-%m-%dT%H:%M:%S.%f',
                            '%Y-%m-%dT%H:%M:%S',
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%d'
                        ):
                            try:
                                return datetime.strptime(value, fmt).isoformat()
                            except ValueError:
                                continue
                        return value
                return value
            else:
                return value
        except Exception as e:
            logger.error(f"Type conversion failed: {str(e)}")
            return value
class BusinessRuleApplier(BaseTransformer):
    """
    Business rule application transformer.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rules = config.get('rules', [])
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply business rules to data."""
        transformed_data = []
        for record in data:
            try:
                record_copy = record.copy()
                for rule in self.rules:
                    rule.get('name', 'unknown')
                    rule.get('type', 'transform')
                    condition = rule.get('condition')
                    actions = rule.get('actions', [])
                    if condition and not self._evaluate_condition(record_copy, condition):
                        continue
                    for action in actions:
                        self._apply_action(record_copy, action)
                transformed_data.append(record_copy)
            except Exception as e:
                logger.error(f"Error applying business rules: {str(e)}")
                self.metrics['errors'] += 1
        logger.info(f"Applied business rules to {len(transformed_data)} records")
        return transformed_data
    def _evaluate_condition(self, record: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Evaluate condition against record."""
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        record_value = record.get(field)
        if operator == 'equals':
            return record_value == value
        elif operator == 'not_equals':
            return record_value != value
        elif operator == 'greater_than':
            return record_value > value
        elif operator == 'less_than':
            return record_value < value
        elif operator == 'in':
            return record_value in value
        elif operator == 'not_in':
            return record_value not in value
        else:
            return True
    def _apply_action(self, record: Dict[str, Any], action: Dict[str, Any]):
        """Apply action to record."""
        action_type = action.get('type')
        if action_type == 'set_field':
            field = action.get('field')
            value = action.get('value')
            record[field] = value
        elif action_type == 'remove_field':
            field = action.get('field')
            record.pop(field, None)
        elif action_type == 'transform_field':
            field = action.get('field')
            transformation = action.get('transformation')
            record[field] = self._apply_transformation(record.get(field), transformation)
    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        """Apply transformation to value."""
        if transformation == 'uppercase':
            return str(value).upper()
        elif transformation == 'lowercase':
            return str(value).lower()
        elif transformation == 'trim':
            return str(value).strip()
        else:
            return value
