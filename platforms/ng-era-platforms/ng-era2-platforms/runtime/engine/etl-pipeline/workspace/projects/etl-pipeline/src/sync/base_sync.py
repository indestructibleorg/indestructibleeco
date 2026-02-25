#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: base_sync
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Base Synchronization Service
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact, manifest
"""
# MNGA-002: Import organization needs review
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import hashlib
import json
import time
from enum import Enum
logger = logging.getLogger(__name__)
class SyncMode(Enum):
    """Synchronization modes."""
    REAL_TIME = "real-time"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    LAST_WRITE_WINS = "last-write-wins"
    MERGE = "merge"
    SOURCE_WINS = "source-wins"
    TARGET_WINS = "target-wins"
    MANUAL_REVIEW = "manual-review"
class BaseSyncService(ABC):
    """
    Abstract base class for synchronization services.
    Implements common sync patterns with evidence generation.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize sync service with configuration.
        Args:
            config: Sync service configuration
        """
        self.config = config
        self.sync_name = config.get('name', 'base-sync')
        self.sync_id = config.get('id', 'unknown')
        self.sync_mode = SyncMode(config.get('sync_mode', 'scheduled'))
        self.conflict_resolution = ConflictResolution(
            config.get('conflict_resolution', 'last-write-wins')
        )
        self.enable_incremental = config.get('enable_incremental', True)
        self.retry_attempts = config.get('retry_attempts', 5)
        self.retry_backoff = config.get('retry_backoff', 'exponential')
        self.evidence_chain = []
        self.conflict_log = []
        self.sync_status = {
            'last_sync': None,
            'status': 'idle',
            'records_synced': 0,
            'records_failed': 0,
            'conflicts_detected': 0,
            'conflicts_resolved': 0
        }
    @abstractmethod
    def fetch_source_changes(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Fetch changes from source system.
        Args:
            since: Optional timestamp for incremental sync
        Returns:
            List of changed records
        """
        pass
    @abstractmethod
    def fetch_target_state(self) -> Dict[str, Any]:
        """
        Fetch current state from target system.
        Returns:
            Dictionary of target records indexed by ID
        """
        pass
    @abstractmethod
    def apply_changes(self, changes: List[Dict[str, Any]]) -> bool:
        """
        Apply changes to target system.
        Args:
            changes: Changes to apply
        Returns:
            bool: True if successful
        """
        pass
    @abstractmethod
    def detect_conflicts(self, source_changes: List[Dict[str, Any]], 
                        target_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect conflicts between source and target.
        Args:
            source_changes: Changes from source
            target_state: Current target state
        Returns:
            List of conflicts
        """
        pass
    @abstractmethod
    def resolve_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve a single conflict.
        Args:
            conflict: Conflict to resolve
        Returns:
            Resolved record
        """
        pass
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """
        Generate evidence entry for sync operation.
        Args:
            operation: Operation name
            details: Operation details
        Returns:
            Evidence hash
        """
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'sync': self.sync_name,
            'sync_id': self.sync_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        logger.info(f"Evidence generated: {evidence_hash}")
        return evidence_hash
    def log_conflict(self, conflict: Dict[str, Any], resolution: Dict[str, Any]):
        """
        Log conflict and its resolution.
        Args:
            conflict: Original conflict
            resolution: Resolution details
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'conflict': conflict,
            'resolution': resolution,
            'strategy': self.conflict_resolution.value
        }
        self.conflict_log.append(log_entry)
        self.generate_evidence('conflict_resolved', log_entry)
    def execute_sync(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Execute complete synchronization workflow.
        Args:
            since: Optional timestamp for incremental sync
        Returns:
            Sync results
        """
        self.sync_status['status'] = 'running'
        self.sync_status['last_sync'] = datetime.utcnow().isoformat()
        self.generate_evidence('sync_start', {'since': since.isoformat() if since else None})
        try:
            results = {
                'records_processed': 0,
                'records_synced': 0,
                'records_failed': 0,
                'conflicts_detected': 0,
                'conflicts_resolved': 0,
                'duration_seconds': 0,
                'success': False
            }
            start_time = datetime.utcnow()
            source_changes = self.fetch_source_changes(since)
            self.generate_evidence('source_changes_fetched', {'count': len(source_changes)})
            target_state = self.fetch_target_state()
            self.generate_evidence('target_state_fetched', {'count': len(target_state)})
            conflicts = self.detect_conflicts(source_changes, target_state)
            results['conflicts_detected'] = len(conflicts)
            self.sync_status['conflicts_detected'] = len(conflicts)
            if conflicts:
                self.generate_evidence('conflicts_detected', {'count': len(conflicts)})
                resolved_changes = self._resolve_all_conflicts(source_changes, conflicts)
                results['conflicts_resolved'] = len(conflicts)
            else:
                resolved_changes = source_changes
            success = self._apply_with_retry(resolved_changes)
            if success:
                results['records_synced'] = len(resolved_changes)
                self.sync_status['records_synced'] = len(resolved_changes)
                results['success'] = True
            end_time = datetime.utcnow()
            results['duration_seconds'] = (end_time - start_time).total_seconds()
            results['records_processed'] = len(source_changes)
            self.generate_evidence('sync_complete', results)
            return results
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            self.sync_status['status'] = 'failed'
            self.sync_status['records_failed'] += 1
            self.generate_evidence('sync_error', {'error': str(e)})
            raise
        finally:
            self.sync_status['status'] = 'idle'
    def _resolve_all_conflicts(self, changes: List[Dict[str, Any]], 
                              conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolve all conflicts.
        Args:
            changes: All changes
            conflicts: Detected conflicts
        Returns:
            Changes with conflicts resolved
        """
        resolved = []
        conflict_ids = {c['id'] for c in conflicts}
        for change in changes:
            if change['id'] in conflict_ids:
                conflict = next(c for c in conflicts if c['id'] == change['id'])
                resolved_change = self.resolve_conflict(conflict)
                resolved.append(resolved_change)
                self.log_conflict(conflict, resolved_change)
            else:
                resolved.append(change)
        return resolved
    def _apply_with_retry(self, changes: List[Dict[str, Any]]) -> bool:
        """
        Apply changes with retry logic.
        Args:
            changes: Changes to apply
        Returns:
            bool: True if successful
        """
        for attempt in range(self.retry_attempts):
            try:
                success = self.apply_changes(changes)
                if success:
                    return True
            except Exception as e:
                logger.warning(f"Apply attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    if self.retry_backoff == 'exponential':
                        wait_time = min(2 ** attempt, 30)
                    else:
                        wait_time = 5
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts failed")
                    self.sync_status['records_failed'] = len(changes)
                    return False
        return False
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status.
        Returns:
            Sync status dictionary
        """
        return self.sync_status.copy()
    def get_conflict_log(self) -> List[Dict[str, Any]]:
        """
        Get conflict resolution log.
        Returns:
            List of conflict log entries
        """
        return self.conflict_log.copy()
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        """
        Get complete evidence chain.
        Returns:
            List of evidence entries
        """
        return self.evidence_chain
