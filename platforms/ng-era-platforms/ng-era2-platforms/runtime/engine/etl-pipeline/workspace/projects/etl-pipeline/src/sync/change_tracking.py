#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: change_tracking
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Change Tracking and CDC Implementation
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
from typing import Dict, Any, List
import logging
from datetime import datetime, timezone
import hashlib
import json
logger = logging.getLogger(__name__)
class ChangeTracker:
    """
    Tracks changes in data for incremental synchronization.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tracker_name = config.get('name', 'change-tracker')
        self.tracker_id = config.get('id', 'unknown')
        self.enable_hashing = config.get('enable_hashing', True)
        self.record_id_field = config.get('record_id_field', 'id')
        self.timestamp_field = config.get('timestamp_field', 'updated_at')
        self.change_type_field = config.get('change_type_field', '_change_type')
        self.evidence_chain = []
        self.tracking_enabled = config.get('tracking_enabled', True)
    @staticmethod
    def _current_timestamp() -> str:
        """Generate current timestamp for change tracking."""
        return datetime.utcnow().isoformat()
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """Generate evidence entry."""
        evidence = {
            'timestamp': self._current_timestamp(),
            'tracker': self.tracker_name,
            'tracker_id': self.tracker_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        logger.info(f"Evidence generated: {evidence_hash}")
        return evidence_hash
    def track_changes(self, current_state: List[Dict[str, Any]], 
                     previous_state: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Track changes between two states.
        Args:
            current_state: Current data state
            previous_state: Previous data state
        Returns:
            List of changes
        """
        if not self.tracking_enabled:
            self.generate_evidence('tracking_disabled', {})
            return []
        changes = []
        current_dict = {
            r[self.record_id_field]: r
            for r in current_state
            if self.record_id_field in r
        }
        previous_dict = {
            r[self.record_id_field]: r
            for r in previous_state
            if self.record_id_field in r
        }
        missing_current_ids = [r for r in current_state if self.record_id_field not in r]
        missing_previous_ids = [r for r in previous_state if self.record_id_field not in r]
        if missing_current_ids or missing_previous_ids:
            self.generate_evidence('missing_record_ids', {
                'current_missing': len(missing_current_ids),
                'previous_missing': len(missing_previous_ids)
            })
        all_ids = set(current_dict.keys()) | set(previous_dict.keys())
        for record_id in all_ids:
            current = current_dict.get(record_id)
            previous = previous_dict.get(record_id)
            change = {
                'id': record_id,
                self.timestamp_field: self._current_timestamp()
            }
            if current is None:
                change[self.change_type_field] = 'delete'
                change['previous_state'] = previous
                changes.append(change)
                self.generate_evidence('change_detected', {
                    'type': 'delete',
                    'id': record_id
                })
            elif previous is None:
                change[self.change_type_field] = 'create'
                change['current_state'] = current
                changes.append(change)
                self.generate_evidence('change_detected', {
                    'type': 'create',
                    'id': record_id
                })
            else:
                if self.enable_hashing:
                    current_hash = self._compute_hash(current)
                    previous_hash = self._compute_hash(previous)
                    if current_hash != previous_hash:
                        change[self.change_type_field] = 'update'
                        change['previous_state'] = previous
                        change['current_state'] = current
                        changes.append(change)
                        self.generate_evidence('change_detected', {
                            'type': 'update',
                            'id': record_id
                        })
                else:
                    if current != previous:
                        change[self.change_type_field] = 'update'
                        change['previous_state'] = previous
                        change['current_state'] = current
                        changes.append(change)
                        self.generate_evidence('change_detected', {
                            'type': 'update',
                            'id': record_id
                        })
        logger.info(f"Tracked {len(changes)} changes")
        return changes
    def _compute_hash(self, record: Dict[str, Any]) -> str:
        """
        Compute hash of record for change detection.
        Args:
            record: Record to hash
        Returns:
            Hash string
        """
        record_copy = record.copy()
        record_copy.pop(self.timestamp_field, None)
        hash_input = json.dumps(record_copy, sort_keys=True)
        return hashlib.sha256(hash_input.encode()).hexdigest()
    def filter_changes_since(self, changes: List[Dict[str, Any]], 
                           since: datetime) -> List[Dict[str, Any]]:
        """
        Filter changes since a timestamp.
        Args:
            changes: List of changes
            since: Timestamp to filter from
        Returns:
            Filtered changes
        """
        filtered = []
        since_timestamp = self._normalize_timestamp(since)
        for change in changes:
            timestamp_str = change.get(self.timestamp_field)
            if timestamp_str:
                try:
                    timestamp = self._parse_timestamp(timestamp_str)
                    if timestamp >= since_timestamp:
                        filtered.append(change)
                except Exception as e:
                    logger.warning(f"Failed to parse timestamp: {str(e)}")
        logger.info(f"Filtered to {len(filtered)} changes since {since}")
        return filtered
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        """Get complete evidence chain."""
        return self.evidence_chain
    @staticmethod
    def _normalize_timestamp(value: datetime) -> datetime:
        """Normalize timestamps to timezone-aware UTC."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    def _parse_timestamp(self, value: str) -> datetime:
        """Parse timestamp string into timezone-aware UTC."""
        timestamp_value = value
        if timestamp_value.endswith('Z'):
            timestamp_value = timestamp_value.replace('Z', '+00:00')
        parsed = datetime.fromisoformat(timestamp_value)
        return self._normalize_timestamp(parsed)
