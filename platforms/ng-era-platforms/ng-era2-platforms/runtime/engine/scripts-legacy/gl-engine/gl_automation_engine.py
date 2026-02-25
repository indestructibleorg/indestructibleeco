#
# @ECO-governed
# @ECO-layer: gl-platform.governance
# @ECO-semantic: gl_automation_engine
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL Automation Engine - Core Orchestration for Governance Automation
MachineNativeOps GL Architecture Implementation
This module provides the central automation engine for GL gl-platform.governance operations,
enabling continuous monitoring, automated validation, and intelligent orchestration.
"""
import logging
import schedule
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GLAutomationEngine')
class AutomationTrigger(Enum):
    """Automation trigger types."""
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    MANUAL = "manual"
    CONDITIONAL = "conditional"
class AutomationStatus(Enum):
    """Automation task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
@dataclass
class AutomationTask:
    """Represents an automation task."""
    task_id: str
    name: str
    description: str
    trigger: AutomationTrigger
    handler: Callable
    schedule: Optional[str] = None
    enabled: bool = True
    status: AutomationStatus = AutomationStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    last_error: Optional[str] = None
@dataclass
class AutomationResult:
    """Result of an automation task execution."""
    task_id: str
    status: AutomationStatus
    execution_time: float
    output: Any = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
class GLAutomationEngine:
    """
    Central orchestration engine for GL gl-platform.governance automation.
    Features:
    - Scheduled task execution
    - Event-driven automation
    - Continuous monitoring
    - Error recovery and retry logic
    - Performance optimization
    """
    def __init__(self):
        self.tasks: Dict[str, AutomationTask] = {}
        self.results: List[AutomationResult] = []
        self.running = False
        self._stop_event = threading.Event()
        self.validator = None  # Will be imported from gl_validator
        self.executor = None  # Will be imported from gl_executor
    def register_task(self, 
                     task_id: str,
                     name: str,
                     description: str,
                     handler: Callable,
                     trigger: AutomationTrigger,
                     schedule: Optional[str] = None) -> None:
        """Register an automation task."""
        task = AutomationTask(
            task_id=task_id,
            name=name,
            description=description,
            trigger=trigger,
            handler=handler,
            schedule=schedule
        )
        self.tasks[task_id] = task
        logger.info(f"Registered task: {name} ({task_id})")
    def execute_task(self, task_id: str) -> AutomationResult:
        """Execute a specific automation task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        task = self.tasks[task_id]
        if not task.enabled:
            logger.info(f"Task disabled, skipping: {task.name}")
            return AutomationResult(
                task_id=task_id,
                status=AutomationStatus.SKIPPED,
                execution_time=0.0
            )
        start_time = time.time()
        task.status = AutomationStatus.RUNNING
        task.last_run = datetime.now()
        try:
            logger.info(f"Executing task: {task.name}")
            output = task.handler()
            execution_time = time.time() - start_time
            task.status = AutomationStatus.COMPLETED
            task.success_count += 1
            result = AutomationResult(
                task_id=task_id,
                status=AutomationStatus.COMPLETED,
                execution_time=execution_time,
                output=output
            )
            self.results.append(result)
            logger.info(f"Task completed: {task.name} in {execution_time:.2f}s")
        except Exception as e:
            execution_time = time.time() - start_time
            task.status = AutomationStatus.FAILED
            task.failure_count += 1
            task.last_error = str(e)
            result = AutomationResult(
                task_id=task_id,
                status=AutomationStatus.FAILED,
                execution_time=execution_time,
                error=str(e)
            )
            self.results.append(result)
            logger.error(f"Task failed: {task.name} - {str(e)}")
        return result
    def execute_all_tasks(self) -> List[AutomationResult]:
        """Execute all enabled tasks."""
        results = []
        for task_id in self.tasks:
            if self.tasks[task_id].enabled:
                result = self.execute_task(task_id)
                results.append(result)
        return results
    def start_scheduler(self) -> None:
        """Start the task scheduler."""
        if not self.running:
            self.running = True
            self._stop_event.clear()
            # Schedule tasks
            for task in self.tasks.values():
                if task.trigger == AutomationTrigger.SCHEDULED and task.schedule:
                    schedule.every().day.at(task.schedule).do(
                        self.execute_task, task.task_id
                    )
            # Start scheduler thread
            scheduler_thread = threading.Thread(
                target=self._run_scheduler,
                daemon=True
            )
            scheduler_thread.start()
            logger.info("Automation scheduler started")
    def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        while not self._stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
    def stop_scheduler(self) -> None:
        """Stop the task scheduler."""
        if self.running:
            self._stop_event.set()
            self.running = False
            logger.info("Automation scheduler stopped")
    def get_task_status(self, task_id: str) -> Optional[AutomationTask]:
        """Get the current status of a task."""
        return self.tasks.get(task_id)
    def get_all_task_status(self) -> Dict[str, AutomationTask]:
        """Get status of all tasks."""
        return self.tasks
    def get_recent_results(self, limit: int = 100) -> List[AutomationResult]:
        """Get recent execution results."""
        return self.results[-limit:]
    def get_automation_metrics(self) -> Dict[str, Any]:
        """Get automation metrics and statistics."""
        total_runs = len(self.results)
        successful_runs = sum(
            1 for r in self.results 
            if r.status == AutomationStatus.COMPLETED
        )
        failed_runs = sum(
            1 for r in self.results 
            if r.status == AutomationStatus.FAILED
        )
        avg_execution_time = (
            sum(r.execution_time for r in self.results) / total_runs
            if total_runs > 0 else 0.0
        )
        return {
            "total_tasks": len(self.tasks),
            "enabled_tasks": sum(1 for t in self.tasks.values() if t.enabled),
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            "avg_execution_time": avg_execution_time,
            "scheduler_running": self.running
        }
# Built-in automation handlers
def validate_all_artifacts(engine: GLAutomationEngine) -> Dict[str, Any]:
    """Validate all GL gl-platform.governance artifacts."""
    try:
        # Import validator here to avoid circular imports
        from gl_validator import GLValidator
        validator = GLValidator()
        results = validator.validate_directory(Path.cwd())
        return {
            "total_artifacts": results.files_validated,
            "passed": results.passed,
            "errors": results.error_count,
            "warnings": results.warning_count
        }
    except Exception as e:
        raise Exception(f"Validation failed: {str(e)}")
def generate_governance_report(engine: GLAutomationEngine) -> Dict[str, Any]:
    """Generate comprehensive gl-platform.governance report."""
    try:
        metrics = engine.get_automation_metrics()
        task_status = engine.get_all_task_status()
        return {
            "generated_at": datetime.now().isoformat(),
            "automation_metrics": metrics,
            "task_status": {
                task_id: {
                    "name": task.name,
                    "status": task.status.value,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "success_count": task.success_count,
                    "failure_count": task.failure_count
                }
                for task_id, task in task_status.items()
            }
        }
    except Exception as e:
        raise Exception(f"Report generation failed: {str(e)}")
def monitor_governance_health(engine: GLAutomationEngine) -> Dict[str, Any]:
    """Monitor overall gl-platform.governance health."""
    try:
        metrics = engine.get_automation_metrics()
        # Calculate health score
        health_score = 100
        if metrics["success_rate"] < 90:
            health_score -= 20
        if metrics["failed_runs"] > 10:
            health_score -= 10
        if metrics["avg_execution_time"] > 10:
            health_score -= 10
        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": max(0, health_score),
            "total_tasks": metrics["total_tasks"],
            "active_tasks": metrics["enabled_tasks"],
            "success_rate": metrics["success_rate"],
            "status": "healthy" if health_score >= 80 else "needs_attention"
        }
    except Exception as e:
        raise Exception(f"Health monitoring failed: {str(e)}")
def setup_default_tasks(engine: GLAutomationEngine) -> None:
    """Setup default automation tasks."""
    # Daily validation task
    engine.register_task(
        task_id="daily_validation",
        name="Daily Artifact Validation",
        description="Validate all GL gl-platform.governance artifacts daily",
        handler=lambda: validate_all_artifacts(engine),
        trigger=AutomationTrigger.SCHEDULED,
        schedule="06:00"
    )
    # Hourly health check
    engine.register_task(
        task_id="hourly_health_check",
        name="Hourly Governance Health Check",
        description="Monitor gl-platform.governance health every hour",
        handler=lambda: monitor_gl-platform.governance_health(engine),
        trigger=AutomationTrigger.SCHEDULED,
        schedule="*:00"  # Every hour
    )
    # Report generation
    engine.register_task(
        task_id="generate_report",
        name="Generate Governance Report",
        description="Generate comprehensive gl-platform.governance report",
        handler=lambda: generate_gl-platform.governance_report(engine),
        trigger=AutomationTrigger.SCHEDULED,
        schedule="08:00"
    )
if __name__ == "__main__":
    # Demo: Create and run automation engine
    engine = GLAutomationEngine()
    setup_default_tasks(engine)
    print("GL Automation Engine Initialized")
    print("=" * 50)
    # Execute all tasks
    results = engine.execute_all_tasks()
    print("\nTask Execution Results:")
    for result in results:
        print(f"  {result.task_id}: {result.status.value} ({result.execution_time:.2f}s)")
    # Get metrics
    metrics = engine.get_automation_metrics()
    print("\nAutomation Metrics:")
    print(f"  Total Tasks: {metrics['total_tasks']}")
    print(f"  Success Rate: {metrics['success_rate']:.1f}%")
    print(f"  Avg Execution Time: {metrics['avg_execution_time']:.2f}s")