#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: monitoring_service
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Monitoring and Alerting Service
ECO-Layer: GL50-59 (Observability)
Closure-Signal: artifact, manifest
"""
# MNGA-002: Import organization needs review
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json
from enum import Enum
import hashlib
logger = logging.getLogger(__name__)
class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
class MonitoringService:
    """
    Comprehensive monitoring and alerting service.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitor_name = config.get('name', 'monitoring-service')
        self.monitor_id = config.get('id', 'unknown')
        self.alert_channels = config.get('alert_channels', ['log'])
        self.thresholds = config.get('thresholds', {})
        self.evidence_chain = []
        self.metrics = {
            'pipeline_health': {},
            'data_quality': {},
            'performance': {},
            'sync_status': {},
            'alerts': []
        }
        self.alert_history = []
        self.start_time = datetime.utcnow()
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """Generate evidence entry."""
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'monitor': self.monitor_name,
            'monitor_id': self.monitor_id,
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        logger.info(f"Evidence generated: {evidence_hash}")
        return evidence_hash
    def collect_pipeline_metrics(self, pipeline_name: str, 
                                  metrics: Dict[str, Any]) -> bool:
        """
        Collect pipeline execution metrics.
        Args:
            pipeline_name: Name of pipeline
            metrics: Pipeline metrics
        Returns:
            bool: True if collection successful
        """
        try:
            self.metrics['pipeline_health'][pipeline_name] = {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': metrics,
                'health_score': self._calculate_health_score(metrics)
            }
            self.generate_evidence('metrics_collected', {
                'pipeline': pipeline_name,
                'metrics': metrics
            })
            return True
        except Exception as e:
            logger.error(f"Failed to collect pipeline metrics: {str(e)}")
            return False
    def collect_data_quality_metrics(self, dataset_name: str,
                                      quality_metrics: Dict[str, Any]) -> bool:
        """
        Collect data quality metrics.
        Args:
            dataset_name: Name of dataset
            quality_metrics: Quality metrics
        Returns:
            bool: True if collection successful
        """
        try:
            self.metrics['data_quality'][dataset_name] = {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': quality_metrics
            }
            if self._check_quality_thresholds(quality_metrics):
                self.alert(
                    AlertSeverity.WARNING,
                    f"Data quality threshold breached for {dataset_name}",
                    {'dataset': dataset_name, 'metrics': quality_metrics}
                )
            self.generate_evidence('quality_metrics_collected', {
                'dataset': dataset_name,
                'metrics': quality_metrics
            })
            return True
        except Exception as e:
            logger.error(f"Failed to collect quality metrics: {str(e)}")
            return False
    def collect_performance_metrics(self, component_name: str,
                                     performance_metrics: Dict[str, Any]) -> bool:
        """
        Collect performance metrics.
        Args:
            component_name: Name of component
            performance_metrics: Performance metrics
        Returns:
            bool: True if collection successful
        """
        try:
            self.metrics['performance'][component_name] = {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': performance_metrics
            }
            if self._check_performance_thresholds(performance_metrics):
                self.alert(
                    AlertSeverity.WARNING,
                    f"Performance threshold breached for {component_name}",
                    {'component': component_name, 'metrics': performance_metrics}
                )
            self.generate_evidence('performance_metrics_collected', {
                'component': component_name,
                'metrics': performance_metrics
            })
            return True
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {str(e)}")
            return False
    def monitor_sync_status(self, sync_name: str, sync_status: Dict[str, Any]) -> bool:
        """
        Monitor synchronization status.
        Args:
            sync_name: Name of sync
            sync_status: Sync status
        Returns:
            bool: True if monitoring successful
        """
        try:
            self.metrics['sync_status'][sync_name] = {
                'timestamp': datetime.utcnow().isoformat(),
                'status': sync_status
            }
            if sync_status.get('status') == 'failed':
                self.alert(
                    AlertSeverity.CRITICAL,
                    f"Sync failed for {sync_name}",
                    {'sync': sync_name, 'status': sync_status}
                )
            elif sync_status.get('conflicts_detected', 0) > self.thresholds.get('max_conflicts', 10):
                self.alert(
                    AlertSeverity.WARNING,
                    f"High conflict count in {sync_name}",
                    {'sync': sync_name, 'status': sync_status}
                )
            self.generate_evidence('sync_status_monitored', {
                'sync': sync_name,
                'status': sync_status
            })
            return True
        except Exception as e:
            logger.error(f"Failed to monitor sync status: {str(e)}")
            return False
    def alert(self, severity: AlertSeverity, message: str, 
              details: Dict[str, Any]) -> bool:
        """
        Generate and send alert.
        Args:
            severity: Alert severity
            message: Alert message
            details: Alert details
        Returns:
            bool: True if alert sent successfully
        """
        try:
            alert = {
                'timestamp': datetime.utcnow().isoformat(),
                'severity': severity.value,
                'message': message,
                'details': details,
                'monitor_id': self.monitor_id
            }
            self.alert_history.append(alert)
            self.metrics['alerts'].append(alert)
            for channel in self.alert_channels:
                if channel == 'log':
                    logger.warning(f"[{severity.value.upper()}] {message}")
                elif channel == 'slack':
                    self._send_slack_alert(alert)
                elif channel == 'email':
                    self._send_email_alert(alert)
                elif channel == 'pagerduty':
                    self._send_pagerduty_alert(alert)
            self.generate_evidence('alert_generated', alert)
            return True
        except Exception as e:
            logger.error(f"Failed to generate alert: {str(e)}")
            return False
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate health score from metrics."""
        score = 100.0
        if metrics.get('error_rate', 0) > 0.01:
            score -= 20
        if metrics.get('latency_seconds', 0) > 30:
            score -= 10
        if metrics.get('records_failed', 0) > 0:
            score -= 30
        return max(0.0, min(100.0, score))
    def _check_quality_thresholds(self, metrics: Dict[str, Any]) -> bool:
        """Check if quality thresholds are breached."""
        completeness_threshold = self.thresholds.get('completeness', 99.9)
        accuracy_threshold = self.thresholds.get('accuracy', 99.9)
        if metrics.get('completeness', 100) < completeness_threshold:
            return True
        if metrics.get('accuracy', 100) < accuracy_threshold:
            return True
        return False
    def _check_performance_thresholds(self, metrics: Dict[str, Any]) -> bool:
        """Check if performance thresholds are breached."""
        latency_threshold = self.thresholds.get('max_latency_seconds', 30)
        throughput_threshold = self.thresholds.get('min_throughput', 1000)
        if metrics.get('latency_seconds', 0) > latency_threshold:
            return True
        throughput_value = metrics.get('throughput')
        if throughput_value is not None and throughput_value < throughput_threshold:
            return True
        return False
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Send alert to Slack."""
        logger.info(f"Slack alert: {alert['message']}")
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send alert via email."""
        logger.info(f"Email alert: {alert['message']}")
    def _send_pagerduty_alert(self, alert: Dict[str, Any]):
        """Send alert to PagerDuty."""
        logger.info(f"PagerDuty alert: {alert['message']}")
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self.metrics.copy()
    def get_alert_history(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get alert history.
        Args:
            since: Optional timestamp filter
        Returns:
            List of alerts
        """
        if since:
            return [a for a in self.alert_history if datetime.fromisoformat(a['timestamp']) >= since]
        return self.alert_history.copy()
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate monitoring report.
        Returns:
            Monitoring report
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        report = {
            'report_timestamp': datetime.utcnow().isoformat(),
            'monitor_id': self.monitor_id,
            'uptime_seconds': uptime,
            'metrics_summary': {
                'pipelines_monitored': len(self.metrics['pipeline_health']),
                'datasets_monitored': len(self.metrics['data_quality']),
                'components_monitored': len(self.metrics['performance']),
                'syncs_monitored': len(self.metrics['sync_status']),
                'alerts_generated': len(self.alert_history)
            },
            'alert_summary': {
                'critical': len([a for a in self.alert_history if a['severity'] == 'critical']),
                'warning': len([a for a in self.alert_history if a['severity'] == 'warning']),
                'info': len([a for a in self.alert_history if a['severity'] == 'info'])
            },
            'evidence_chain_length': len(self.evidence_chain)
        }
        self.generate_evidence('report_generated', report)
        return report
    def get_evidence_chain(self) -> List[Dict[str, Any]]:
        """Get complete evidence chain."""
        return self.evidence_chain
