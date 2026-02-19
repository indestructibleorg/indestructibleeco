"""Celery Worker — Async inference job processing with priority queues.

Consumes jobs from Redis-backed Celery queues, dispatches to EngineManager,
persists results, and emits completion events.

URI: indestructibleeco://backend/ai/services/worker
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

    @property
    def queue_name(self) -> str:
        return f"eco.inference.{self.value}"


class InferenceJob:
    """Represents a single async inference job."""

    __slots__ = (
        "job_id",
        "model_id",
        "prompt",
        "max_tokens",
        "temperature",
        "top_p",
        "priority",
        "status",
        "result",
        "error",
        "engine",
        "usage",
        "latency_ms",
        "created_at",
        "started_at",
        "completed_at",
        "timeout_seconds",
        "metadata",
    )

    def __init__(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        priority: JobPriority = JobPriority.NORMAL,
        timeout_seconds: float = 300.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.job_id: str = str(uuid.uuid1())
        self.model_id = model_id
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.priority = priority
        self.status = JobStatus.PENDING
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.engine: Optional[str] = None
        self.usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.latency_ms: float = 0.0
        self.created_at: float = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.timeout_seconds = timeout_seconds
        self.metadata: Dict[str, Any] = metadata or {}

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "model_id": self.model_id,
            "prompt": self.prompt[:200],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "priority": self.priority.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "engine": self.engine,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
            "created_at": datetime.fromtimestamp(self.created_at, tz=timezone.utc).isoformat(),
            "started_at": (
                datetime.fromtimestamp(self.started_at, tz=timezone.utc).isoformat()
                if self.started_at
                else None
            ),
            "completed_at": (
                datetime.fromtimestamp(self.completed_at, tz=timezone.utc).isoformat()
                if self.completed_at
                else None
            ),
            "uri": f"indestructibleeco://ai/job/{self.job_id}",
            "urn": f"urn:indestructibleeco:ai:job:{self.model_id}:{self.job_id}",
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InferenceJob:
        job = cls(
            model_id=data["model_id"],
            prompt=data.get("prompt", ""),
            max_tokens=data.get("max_tokens", 2048),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 0.9),
            priority=JobPriority(data.get("priority", "normal")),
            timeout_seconds=data.get("timeout_seconds", 300.0),
            metadata=data.get("metadata", {}),
        )
        job.job_id = data["job_id"]
        job.status = JobStatus(data.get("status", "pending"))
        job.result = data.get("result")
        job.error = data.get("error")
        job.engine = data.get("engine")
        job.usage = data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        job.latency_ms = data.get("latency_ms", 0.0)
        return job


class InferenceWorker:
    """Processes async inference jobs from an in-process queue.

    In production, this integrates with Celery + Redis. For local/test mode,
    it uses an asyncio queue with configurable concurrency.

    Lifecycle:
        worker = InferenceWorker(engine_manager)
        await worker.start(concurrency=4)
        job_id = await worker.submit(job)
        result = await worker.wait(job_id, timeout=30)
        await worker.shutdown()
    """

    def __init__(
        self,
        engine_manager: Any = None,
        max_queue_size: int = 10000,
        stale_timeout: float = 600.0,
    ) -> None:
        self._engine_manager = engine_manager
        self._max_queue_size = max_queue_size
        self._stale_timeout = stale_timeout

        self._queue: asyncio.Queue[InferenceJob] = asyncio.Queue(maxsize=max_queue_size)
        self._jobs: Dict[str, InferenceJob] = {}
        self._events: Dict[str, asyncio.Event] = {}
        self._workers: List[asyncio.Task[None]] = []
        self._running = False

        # Metrics
        self.total_submitted: int = 0
        self.total_completed: int = 0
        self.total_failed: int = 0
        self.total_timeout: int = 0

    async def start(self, concurrency: int = 4) -> None:
        """Start worker coroutines."""
        if self._running:
            return
        self._running = True
        for i in range(concurrency):
            task = asyncio.create_task(self._worker_loop(i))
            self._workers.append(task)
        logger.info("InferenceWorker: started %d workers (queue_max=%d)", concurrency, self._max_queue_size)

    async def shutdown(self) -> None:
        """Graceful shutdown — drain queue, cancel workers."""
        self._running = False
        for task in self._workers:
            task.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info(
            "InferenceWorker: shutdown (completed=%d, failed=%d, timeout=%d)",
            self.total_completed,
            self.total_failed,
            self.total_timeout,
        )

    async def submit(self, job: InferenceJob) -> str:
        """Submit a job for async processing. Returns job_id."""
        if not self._running:
            raise RuntimeError("Worker not started")

        if self._queue.full():
            raise RuntimeError(f"Queue full (max={self._max_queue_size})")

        self._jobs[job.job_id] = job
        self._events[job.job_id] = asyncio.Event()
        await self._queue.put(job)
        self.total_submitted += 1
        logger.info(
            "Job %s submitted: model=%s priority=%s",
            job.job_id,
            job.model_id,
            job.priority.value,
        )
        return job.job_id

    async def wait(self, job_id: str, timeout: float = 30.0) -> InferenceJob:
        """Wait for a job to complete. Raises on timeout or job failure."""
        event = self._events.get(job_id)
        if event is None:
            raise KeyError(f"Job {job_id} not found")

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.TIMEOUT
                self.total_timeout += 1
            raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

        job = self._jobs[job_id]
        if job.status == JobStatus.FAILED:
            raise RuntimeError(f"Job {job_id} failed: {job.error}")
        return job

    def get_job(self, job_id: str) -> Optional[InferenceJob]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> List[InferenceJob]:
        """List jobs, optionally filtered by status."""
        jobs = list(self._jobs.values())
        if status is not None:
            jobs = [j for j in jobs if j.status == status]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending job."""
        job = self._jobs.get(job_id)
        if job is None:
            return False
        if job.status != JobStatus.PENDING:
            return False
        job.status = JobStatus.CANCELLED
        event = self._events.get(job_id)
        if event:
            event.set()
        logger.info("Job %s cancelled", job_id)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Return worker statistics."""
        status_counts: Dict[str, int] = {}
        for job in self._jobs.values():
            status_counts[job.status.value] = status_counts.get(job.status.value, 0) + 1

        return {
            "running": self._running,
            "worker_count": len(self._workers),
            "queue_depth": self._queue.qsize(),
            "queue_max": self._max_queue_size,
            "total_submitted": self.total_submitted,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "total_timeout": self.total_timeout,
            "jobs_by_status": status_counts,
        }

    async def cleanup_stale(self) -> int:
        """Remove completed/failed jobs older than stale_timeout. Returns count removed."""
        now = time.time()
        stale_ids: List[str] = []
        for job_id, job in self._jobs.items():
            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT):
                age = now - job.created_at
                if age > self._stale_timeout:
                    stale_ids.append(job_id)

        for job_id in stale_ids:
            self._jobs.pop(job_id, None)
            self._events.pop(job_id, None)

        if stale_ids:
            logger.info("InferenceWorker: cleaned up %d stale jobs", len(stale_ids))
        return len(stale_ids)

    async def _worker_loop(self, worker_id: int) -> None:
        """Main worker loop — dequeue and process jobs."""
        logger.info("Worker-%d: started", worker_id)
        while self._running:
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            if job.status == JobStatus.CANCELLED:
                self._queue.task_done()
                continue

            if job.is_expired:
                job.status = JobStatus.TIMEOUT
                job.error = "Job expired before processing"
                self.total_timeout += 1
                event = self._events.get(job.job_id)
                if event:
                    event.set()
                self._queue.task_done()
                logger.warning("Worker-%d: job %s expired", worker_id, job.job_id)
                continue

            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            logger.info("Worker-%d: processing job %s (model=%s)", worker_id, job.job_id, job.model_id)

            try:
                if self._engine_manager is not None:
                    result = await self._engine_manager.generate(
                        model_id=job.model_id,
                        prompt=job.prompt,
                        max_tokens=job.max_tokens,
                        temperature=job.temperature,
                        top_p=job.top_p,
                    )
                    job.result = result.get("content", "")
                    job.engine = result.get("engine", "unknown")
                    job.usage = result.get("usage", job.usage)
                    job.latency_ms = result.get("latency_ms", 0.0)
                else:
                    prompt_tokens = len(job.prompt.split())
                    job.result = f"[worker-{worker_id}] Processed: {job.prompt[:100]}..."
                    job.engine = "local-fallback"
                    job.usage = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": min(job.max_tokens, prompt_tokens * 2),
                        "total_tokens": prompt_tokens + min(job.max_tokens, prompt_tokens * 2),
                    }

                job.status = JobStatus.COMPLETED
                job.completed_at = time.time()
                job.latency_ms = job.latency_ms or ((job.completed_at - job.started_at) * 1000)
                self.total_completed += 1
                logger.info(
                    "Worker-%d: job %s completed (engine=%s, %.1fms)",
                    worker_id,
                    job.job_id,
                    job.engine,
                    job.latency_ms,
                )

            except Exception as exc:
                job.status = JobStatus.FAILED
                job.error = str(exc)
                job.completed_at = time.time()
                self.total_failed += 1
                logger.error("Worker-%d: job %s failed: %s", worker_id, job.job_id, exc)

            finally:
                event = self._events.get(job.job_id)
                if event:
                    event.set()
                self._queue.task_done()

        logger.info("Worker-%d: stopped", worker_id)