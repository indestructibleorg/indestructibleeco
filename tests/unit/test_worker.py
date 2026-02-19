"""Unit tests for InferenceWorker."""
import pytest
import asyncio

from backend.ai.src.services.worker import (
    InferenceJob,
    InferenceWorker,
    JobPriority,
    JobStatus,
)


@pytest.fixture
def worker():
    return InferenceWorker(engine_manager=None, max_queue_size=100, stale_timeout=10.0)


class TestInferenceJob:
    def test_job_creation(self):
        job = InferenceJob(model_id="test-model", prompt="Hello world")
        assert job.model_id == "test-model"
        assert job.prompt == "Hello world"
        assert job.status == JobStatus.PENDING
        assert job.max_tokens == 2048
        assert job.temperature == 0.7
        assert job.priority == JobPriority.NORMAL
        assert job.result is None
        assert job.error is None

    def test_job_to_dict(self):
        job = InferenceJob(model_id="test-model", prompt="Hello")
        d = job.to_dict()
        assert d["model_id"] == "test-model"
        assert d["status"] == "pending"
        assert "uri" in d
        assert "urn" in d
        assert d["uri"].startswith("indestructibleeco://")

    def test_job_from_dict(self):
        job = InferenceJob(model_id="test-model", prompt="Hello", priority=JobPriority.HIGH)
        d = job.to_dict()
        d["prompt"] = "Hello"
        d["timeout_seconds"] = 300.0
        restored = InferenceJob.from_dict(d)
        assert restored.job_id == job.job_id
        assert restored.model_id == "test-model"
        assert restored.priority == JobPriority.HIGH

    def test_job_expiry(self):
        job = InferenceJob(model_id="m", prompt="p", timeout_seconds=0.0)
        assert job.is_expired is True

    def test_job_not_expired(self):
        job = InferenceJob(model_id="m", prompt="p", timeout_seconds=300.0)
        assert job.is_expired is False

    def test_priority_values(self):
        assert JobPriority.HIGH.queue_name == "eco.inference.high"
        assert JobPriority.NORMAL.queue_name == "eco.inference.normal"
        assert JobPriority.LOW.queue_name == "eco.inference.low"


class TestInferenceWorker:
    @pytest.mark.asyncio
    async def test_start_stop(self, worker):
        await worker.start(concurrency=2)
        assert worker._running is True
        assert len(worker._workers) == 2
        await worker.shutdown()
        assert worker._running is False

    @pytest.mark.asyncio
    async def test_submit_requires_start(self, worker):
        job = InferenceJob(model_id="m", prompt="p")
        with pytest.raises(RuntimeError, match="not started"):
            await worker.submit(job)

    @pytest.mark.asyncio
    async def test_submit_and_wait(self, worker):
        await worker.start(concurrency=2)
        job = InferenceJob(model_id="test-model", prompt="Hello world")
        job_id = await worker.submit(job)
        assert job_id == job.job_id
        assert worker.total_submitted == 1

        result = await worker.wait(job_id, timeout=5.0)
        assert result.status == JobStatus.COMPLETED
        assert result.result is not None
        assert result.engine == "local-fallback"
        assert worker.total_completed == 1
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_get_job(self, worker):
        await worker.start(concurrency=1)
        job = InferenceJob(model_id="m", prompt="p")
        await worker.submit(job)
        await worker.wait(job.job_id, timeout=5.0)

        retrieved = worker.get_job(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, worker):
        assert worker.get_job("nonexistent") is None

    @pytest.mark.asyncio
    async def test_list_jobs(self, worker):
        await worker.start(concurrency=2)
        for i in range(3):
            job = InferenceJob(model_id="m", prompt=f"prompt-{i}")
            await worker.submit(job)

        await asyncio.sleep(0.5)

        jobs = worker.list_jobs()
        assert len(jobs) == 3
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_list_jobs_by_status(self, worker):
        await worker.start(concurrency=2)
        job = InferenceJob(model_id="m", prompt="p")
        await worker.submit(job)
        await worker.wait(job.job_id, timeout=5.0)

        completed = worker.list_jobs(status=JobStatus.COMPLETED)
        assert len(completed) >= 1
        for j in completed:
            assert j.status == JobStatus.COMPLETED
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_cancel_pending_job(self, worker):
        await worker.start(concurrency=0)  # no workers to process
        job = InferenceJob(model_id="m", prompt="p")
        # Manually add to tracking without queue processing
        worker._jobs[job.job_id] = job
        worker._events[job.job_id] = asyncio.Event()

        cancelled = await worker.cancel(job.job_id)
        assert cancelled is True
        assert job.status == JobStatus.CANCELLED
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, worker):
        await worker.start(concurrency=1)
        cancelled = await worker.cancel("nonexistent")
        assert cancelled is False
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_stats(self, worker):
        await worker.start(concurrency=2)
        stats = worker.get_stats()
        assert stats["running"] is True
        assert stats["worker_count"] == 2
        assert stats["queue_depth"] == 0
        assert stats["total_submitted"] == 0
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_cleanup_stale(self, worker):
        worker._stale_timeout = 0.0
        await worker.start(concurrency=2)
        job = InferenceJob(model_id="m", prompt="p")
        await worker.submit(job)
        await worker.wait(job.job_id, timeout=5.0)

        removed = await worker.cleanup_stale()
        assert removed >= 1
        assert worker.get_job(job.job_id) is None
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_expired_job_skipped(self, worker):
        await worker.start(concurrency=2)
        job = InferenceJob(model_id="m", prompt="p", timeout_seconds=0.0)
        await worker.submit(job)
        await asyncio.sleep(0.3)

        assert job.status == JobStatus.TIMEOUT
        assert worker.total_timeout >= 1
        await worker.shutdown()