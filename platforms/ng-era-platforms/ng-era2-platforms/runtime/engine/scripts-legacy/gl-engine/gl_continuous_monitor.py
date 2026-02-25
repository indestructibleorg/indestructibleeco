#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: gl_continuous_monitor
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL Continuous Monitoring System - Real-time Governance Health Tracking
MachineNativeOps GL Architecture Implementation
This module provides continuous monitoring capabilities for GL gl-platform.gl-platform.governance,
enabling real-time health checks, anomaly detection, and automated alerts.
"""
# MNGA-002: Import organization needs review
import json
import logging
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GLContinuousMonitor')
class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
@dataclass
class HealthCheck:
    """Represents a health check."""
    name: str
    check_func: Callable
    interval: int = 60  # seconds
    timeout: int = 30
    enabled: bool = True
    last_check: Optional[datetime] = None
    status: HealthStatus = HealthStatus.UNKNOWN
    last_result: Any = None
@dataclass
class HealthMetric:
    """Represents a health metric."""
    name: str
    value: float
    unit: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
@dataclass
class Alert:
    """Represents a monitoring alert."""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
@dataclass
class MonitoringReport:
    """Monitoring report with health status and alerts."""
    timestamp: datetime
    overall_health: HealthStatus
    health_checks: Dict[str, Any]
    metrics: List[HealthMetric]
    active_alerts: List[Alert]
    recommendations: List[str]
class GLContinuousMonitor:
    """
    Continuous monitoring system for GL gl-platform.gl-platform.governance health.
    Features:
    - Real-time health checks
    - Metric collection and tracking
    - Anomaly detection
    - Automated alerts
    - Trend analysis
    """
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.metrics_history: Dict[str, deque] = {}
        self.alerts: List[Alert] = []
        self.running = False
        self._stop_event = threading.Event()
        self._monitor_thread = None
    def register_health_check(self, 
                             name: str,
                             check_func: Callable,
                             interval: int = 60,
                             timeout: int = 30) -> None:
        """Register a health check."""
        health_check = HealthCheck(
            name=name,
            check_func=check_func,
            interval=interval,
            timeout=timeout
        )
        self.health_checks[name] = health_check
        logger.info(f"Registered health check: {name}")
    def execute_health_check(self, name: str) -> HealthCheck:
        """Execute a specific health check."""
        if name not in self.health_checks:
            raise ValueError(f"Health check not found: {name}")
        check = self.health_checks[name]
        if not check.enabled:
            logger.info(f"Health check disabled, skipping: {name}")
            return check
        start_time = time.time()
        check.last_check = datetime.now()
        try:
            logger.info(f"Executing health check: {name}")
            result = check.check_func()
            execution_time = time.time() - start_time
            check.last_result = result
            check.status = HealthStatus.HEALTHY
            # Analyze result for alerts
            self._analyze_health_result(name, result)
            logger.info(f"Health check passed: {name} ({execution_time:.2f}s)")
        except Exception as e:
            execution_time = time.time() - start_time
            check.last_result = str(e)
            check.status = HealthStatus.CRITICAL
            # Create critical alert
            self._create_alert(
                severity=AlertSeverity.CRITICAL,
                title=f"Health Check Failed: {name}",
                description=f"Health check {name} failed: {str(e)}",
                source=name
            )
            logger.error(f"Health check failed: {name} - {str(e)}")
        return check
    def _analyze_health_result(self, name: str, result: Any) -> None:
        """Analyze health check result for potential issues."""
        if isinstance(result, dict):
            # Check for error indicators
            if result.get("errors", 0) > 0:
                self._create_alert(
                    severity=AlertSeverity.ERROR,
                    title=f"Errors Detected: {name}",
                    description=f"Health check {name} reported {result.get('errors')} errors",
                    source=name
                )
            # Check for warnings
            if result.get("warnings", 0) > 5:
                self._create_alert(
                    severity=AlertSeverity.WARNING,
                    title=f"Warnings Detected: {name}",
                    description=f"Health check {name} reported {result.get('warnings')} warnings",
                    source=name
                )
    def _create_alert(self, 
                     severity: AlertSeverity,
                     title: str,
                     description: str,
                     source: str) -> None:
        """Create and store a monitoring alert."""
        alert = Alert(
            alert_id=f"{source}_{int(time.time())}",
            severity=severity,
            title=title,
            description=description,
            source=source
        )
        self.alerts.append(alert)
        logger.warning(f"Alert created: {title}")
    def record_metric(self, 
                     name: str,
                     value: float,
                     unit: str = "",
                     threshold_warning: Optional[float] = None,
                     threshold_critical: Optional[float] = None) -> None:
        """Record a health metric."""
        metric = HealthMetric(
            name=name,
            value=value,
            unit=unit,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical
        )
        # Initialize history if needed
        if name not in self.metrics_history:
            self.metrics_history[name] = deque(maxlen=1000)
        self.metrics_history[name].append(metric)
        # Check thresholds
        if threshold_critical and value >= threshold_critical:
            self._create_alert(
                severity=AlertSeverity.CRITICAL,
                title=f"Critical Metric: {name}",
                description=f"Metric {name} ({value}{unit}) exceeded critical threshold ({threshold_critical})",
                source=name
            )
        elif threshold_warning and value >= threshold_warning:
            self._create_alert(
                severity=AlertSeverity.WARNING,
                title=f"Warning Metric: {name}",
                description=f"Metric {name} ({value}{unit}) exceeded warning threshold ({threshold_warning})",
                source=name
            )
        logger.debug(f"Metric recorded: {name} = {value}{unit}")
    def get_metric_trend(self, name: str, points: int = 10) -> List[float]:
        """Get recent values for a metric."""
        if name not in self.metrics_history:
            return []
        history = list(self.metrics_history[name])
        recent_values = [m.value for m in history[-points:]]
        return recent_values
    def calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction."""
        if len(values) < 2:
            return "stable"
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        y = values
        # Calculate slope
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        if denominator == 0:
            return "stable"
        slope = numerator / denominator
        # Determine trend
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity."""
        alerts = [a for a in self.alerts if not a.resolved]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert acknowledged: {alert_id}")
                return True
        return False
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                logger.info(f"Alert resolved: {alert_id}")
                return True
        return False
    def generate_report(self) -> MonitoringReport:
        """Generate comprehensive monitoring report."""
        # Determine overall health
        health_scores = []
        for check in self.health_checks.values():
            if check.status == HealthStatus.HEALTHY:
                health_scores.append(100)
            elif check.status == HealthStatus.WARNING:
                health_scores.append(50)
            elif check.status == HealthStatus.CRITICAL:
                health_scores.append(0)
            else:
                health_scores.append(50)
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 50
        if avg_health >= 80:
            overall_health = HealthStatus.HEALTHY
        elif avg_health >= 50:
            overall_health = HealthStatus.WARNING
        else:
            overall_health = HealthStatus.CRITICAL
        # Collect metrics
        all_metrics = []
        for name, history in self.metrics_history.items():
            if history:
                all_metrics.append(history[-1])
        # Generate recommendations
        recommendations = []
        active_alerts = self.get_active_alerts()
        if len(active_alerts) > 5:
            recommendations.append("Multiple active alerts - review and address critical issues")
        if overall_health != HealthStatus.HEALTHY:
            recommendations.append("Overall gl-platform.gl-platform.governance health needs attention - review health checks")
        critical_alerts = self.get_active_alerts(AlertSeverity.CRITICAL)
        if critical_alerts:
            recommendations.append(f"{len(critical_alerts)} critical alerts require immediate attention")
        return MonitoringReport(
            timestamp=datetime.now(),
            overall_health=overall_health,
            health_checks={
                name: {
                    "status": check.status.value,
                    "last_check": check.last_check.isoformat() if check.last_check else None,
                    "last_result": check.last_result
                }
                for name, check in self.health_checks.items()
            },
            metrics=all_metrics,
            active_alerts=active_alerts,
            recommendations=recommendations
        )
    def start_monitoring(self) -> None:
        """Start continuous monitoring."""
        if self.running:
            logger.warning("Monitoring already running")
            return
        self.running = True
        self._stop_event.clear()
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Continuous monitoring started")
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            for name, check in self.health_checks.items():
                if check.enabled:
                    try:
                        self.execute_health_check(name)
                    except Exception as e:
                        logger.error(f"Error executing health check {name}: {str(e)}")
            # Sleep for a short interval
            time.sleep(10)
    def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        if self.running:
            self._stop_event.set()
            if self._monitor_thread:
                self._monitor_thread.join(timeout=5)
            self.running = False
            logger.info("Continuous monitoring stopped")
# Built-in health check functions
def check_artifact_validity() -> Dict[str, Any]:
    """Check validity of all gl-platform.gl-platform.governance artifacts."""
    try:
        artifact_dir = Path.cwd()
        gl_files = list(artifact_dir.glob("GL*.json"))
        valid_count = 0
        error_count = 0
        for gl_file in gl_files:
            try:
                with open(gl_file, 'r') as f:
                    data = json.load(f)
                if data:
                    valid_count += 1
            except Exception:
                error_count += 1
        return {
            "total_artifacts": len(gl_files),
            "valid_artifacts": valid_count,
            "invalid_artifacts": error_count,
            "validity_rate": (valid_count / len(gl_files) * 100) if gl_files else 100
        }
    except Exception as e:
        raise Exception(f"Artifact validity check failed: {str(e)}")
def check_integration_health() -> Dict[str, Any]:
    """Check integration health between GL layers."""
    try:
        # Check for integration markers
        integration_file = Path.cwd() / ".gl-index.json"
        if integration_file.exists():
            with open(integration_file, 'r') as f:
                data = json.load(f)
            artifacts = data.get("artifacts", [])
            return {
                "integration_complete": True,
                "registered_artifacts": len(artifacts),
                "dag_nodes": len(data.get("dag", []))
            }
        else:
            return {
                "integration_complete": False,
                "error": "Integration index not found"
            }
    except Exception as e:
        raise Exception(f"Integration health check failed: {str(e)}")
def check_automation_coverage() -> Dict[str, Any]:
    """Check automation coverage of gl-platform.gl-platform.governance operations."""
    try:
        # Count automated vs manual operations
        total_operations = 10  # Placeholder
        automated_operations = 2  # Placeholder
        coverage = (automated_operations / total_operations * 100) if total_operations > 0 else 0
        return {
            "total_operations": total_operations,
            "automated_operations": automated_operations,
            "coverage_percentage": coverage,
            "target_coverage": 80,
            "gap": 80 - coverage
        }
    except Exception as e:
        raise Exception(f"Automation coverage check failed: {str(e)}")
def setup_default_health_checks(monitor: GLContinuousMonitor) -> None:
    """Setup default health checks."""
    monitor.register_health_check(
        name="artifact_validity",
        check_func=check_artifact_validity,
        interval=300  # Every 5 minutes
    )
    monitor.register_health_check(
        name="integration_health",
        check_func=check_integration_health,
        interval=600  # Every 10 minutes
    )
    monitor.register_health_check(
        name="automation_coverage",
        check_func=check_automation_coverage,
        interval=1800  # Every 30 minutes
    )
if __name__ == "__main__":
    # Demo: Create and run monitoring system
    monitor = GLContinuousMonitor()
    setup_default_health_checks(monitor)
    print("GL Continuous Monitoring System Initialized")
    print("=" * 50)
    # Execute health checks
    for name in monitor.health_checks.keys():
        check = monitor.execute_health_check(name)
        print(f"\n{name}:")
        print(f"  Status: {check.status.value}")
        print(f"  Result: {check.last_result}")
    # Generate report
    report = monitor.generate_report()
    print("\n" + "=" * 50)
    print("Monitoring Report:")
    print(f"  Overall Health: {report.overall_health.value}")
    print(f"  Active Alerts: {len(report.active_alerts)}")
    print(f"  Recommendations: {len(report.recommendations)}")