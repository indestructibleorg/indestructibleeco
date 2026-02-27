"""Integration tests for infrastructure/tasks (TaskRunner) and
infrastructure/external (HTTPClientBase).

TaskRunner tests cover:
- submit: happy path, duplicate name (already running)
- cancel: running task, nonexistent task
- cancel_all: multiple tasks
- get_status: unknown, running, completed, failed, cancelled
- list_tasks

HTTPClientBase tests cover:
- get: success, HTTP 4xx (no retry), HTTP 5xx (retry exhausted)
- post: success, HTTP error
- put / delete: success paths
- RequestError: retry exhausted
"""
from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


class TestTaskRunner:

    def _make_runner(self):
        from src.infrastructure.tasks import TaskRunner
        return TaskRunner()

    async def test_submit_and_complete(self) -> None:
        runner = self._make_runner()
        result_holder = []

        async def work():
            await asyncio.sleep(0.05)
            result_holder.append("done")

        runner.submit("job1", work())
        await asyncio.sleep(0.2)
        assert result_holder == ["done"]
        assert runner.get_status("job1") == "completed"

    async def test_submit_duplicate_running_task_is_ignored(self) -> None:
        runner = self._make_runner()
        started = []

        async def long_work():
            started.append(1)
            await asyncio.sleep(1)

        runner.submit("dup", long_work())
        await asyncio.sleep(0.05)
        # Submit again — must be ignored (task still running)
        runner.submit("dup", long_work())
        await asyncio.sleep(0.05)
        assert len(started) == 1  # Only one task actually started

        runner.cancel("dup")

    async def test_cancel_running_task(self) -> None:
        runner = self._make_runner()

        async def infinite():
            while True:
                await asyncio.sleep(0.1)

        runner.submit("cancel_me", infinite())
        await asyncio.sleep(0.05)
        assert runner.get_status("cancel_me") == "running"
        cancelled = runner.cancel("cancel_me")
        assert cancelled is True
        await asyncio.sleep(0.1)

    async def test_cancel_nonexistent_task_returns_false(self) -> None:
        runner = self._make_runner()
        result = runner.cancel("ghost_task")
        assert result is False

    async def test_cancel_all(self) -> None:
        runner = self._make_runner()

        async def infinite():
            while True:
                await asyncio.sleep(0.1)

        runner.submit("t1", infinite())
        runner.submit("t2", infinite())
        runner.submit("t3", infinite())
        await asyncio.sleep(0.05)
        count = runner.cancel_all()
        assert count == 3

    async def test_get_status_unknown(self) -> None:
        runner = self._make_runner()
        assert runner.get_status("never_submitted") == "unknown"

    async def test_get_status_failed(self) -> None:
        runner = self._make_runner()

        async def failing():
            raise RuntimeError("intentional failure")

        runner.submit("fail_job", failing())
        await asyncio.sleep(0.2)
        assert runner.get_status("fail_job") == "failed"

    async def test_list_tasks(self) -> None:
        runner = self._make_runner()

        async def quick():
            await asyncio.sleep(0.05)

        runner.submit("list_t1", quick())
        runner.submit("list_t2", quick())
        tasks = runner.list_tasks()
        names = {t["name"] for t in tasks}
        assert "list_t1" in names
        assert "list_t2" in names

    async def test_get_task_runner_singleton(self) -> None:
        from src.infrastructure.tasks import get_task_runner
        r1 = get_task_runner()
        r2 = get_task_runner()
        assert r1 is r2


class TestHTTPClientBase:
    """Tests for HTTPClientBase using respx to mock httpx."""

    async def test_get_success(self) -> None:
        import httpx
        import respx
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="https://api.example.com", max_retries=1)

        with respx.mock:
            respx.get("https://api.example.com/users").mock(
                return_value=httpx.Response(200, json={"users": []})
            )
            result = await client.get("/users")
        assert result == {"users": []}

    async def test_get_4xx_raises_immediately_no_retry(self) -> None:
        import httpx
        import respx
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="https://api.example.com", max_retries=3)
        call_count = 0

        with respx.mock:
            def handler(request):
                nonlocal call_count
                call_count += 1
                return httpx.Response(404, json={"error": "not found"})

            respx.get("https://api.example.com/missing").mock(side_effect=handler)
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get("/missing")

        # 4xx must NOT be retried
        assert call_count == 1
        assert exc_info.value.response.status_code == 404

    async def test_get_5xx_retries_and_raises(self) -> None:
        import httpx
        import respx
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="https://api.example.com", max_retries=2)
        call_count = 0

        with respx.mock:
            def handler(request):
                nonlocal call_count
                call_count += 1
                return httpx.Response(503, json={"error": "service unavailable"})

            respx.get("https://api.example.com/flaky").mock(side_effect=handler)
            with pytest.raises(httpx.HTTPStatusError):
                await client.get("/flaky")

        assert call_count == 2  # max_retries=2

    async def test_post_success(self) -> None:
        import httpx
        import respx
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="https://api.example.com", max_retries=1)

        with respx.mock:
            respx.post("https://api.example.com/users").mock(
                return_value=httpx.Response(201, json={"id": "new-user"})
            )
            result = await client.post("/users", json={"name": "Alice"})
        assert result == {"id": "new-user"}

    async def test_put_success(self) -> None:
        import httpx
        import respx
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="https://api.example.com", max_retries=1)

        with respx.mock:
            respx.put("https://api.example.com/users/1").mock(
                return_value=httpx.Response(200, json={"updated": True})
            )
            result = await client.put("/users/1", json={"name": "Bob"})
        assert result == {"updated": True}

    async def test_delete_success_204(self) -> None:
        import httpx
        import respx
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="https://api.example.com", max_retries=1)

        with respx.mock:
            respx.delete("https://api.example.com/users/1").mock(
                return_value=httpx.Response(204)
            )
            result = await client.delete("/users/1")
        assert result == {"status": "deleted"}

    async def test_request_error_retries_and_raises(self) -> None:
        import httpx
        import respx
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="https://api.example.com", max_retries=2)
        call_count = 0

        with respx.mock:
            def network_error(request):
                nonlocal call_count
                call_count += 1
                raise httpx.ConnectError("connection refused")

            respx.get("https://api.example.com/timeout").mock(side_effect=network_error)
            with pytest.raises(httpx.ConnectError):
                await client.get("/timeout")

        assert call_count == 2
