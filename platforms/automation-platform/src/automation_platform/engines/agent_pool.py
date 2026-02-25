"""ParallelAgentPool — manages N concurrent agents via asyncio.Semaphore.

Provides dispatch_task(), drain(), and agent health tracking.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable

from automation_platform.domain.entities import Agent, Task
from automation_platform.domain.events import TaskCompleted, TaskDispatched
from automation_platform.domain.exceptions import AgentPoolExhaustedError
from automation_platform.domain.value_objects import AgentStatus, AgentType, TaskStatus


TaskExecutor = Callable[[Task], Awaitable[dict[str, Any]]]


async def _noop_executor(task: Task) -> dict[str, Any]:
    """Default executor — returns immediately with a simple result."""
    await asyncio.sleep(0)
    return {"output": f"Processed: {task.command}"}


class ParallelAgentPool:
    """Pool of concurrent agents backed by an asyncio.Semaphore.

    Each agent is a logical slot; actual work is delegated to a TaskExecutor callable.
    The semaphore enforces the concurrency limit.
    """

    def __init__(
        self,
        pool_size: int = 4,
        agent_type: AgentType = AgentType.ANALYZER,
        executor: TaskExecutor | None = None,
    ) -> None:
        self._pool_size = pool_size
        self._agent_type = agent_type
        self._executor = executor or _noop_executor
        self._semaphore = asyncio.Semaphore(pool_size)
        self._agents: list[Agent] = [
            Agent(type=agent_type) for _ in range(pool_size)
        ]
        self._events: list[Any] = []
        self._active_count: int = 0
        self._draining: bool = False
        self._drain_event: asyncio.Event = asyncio.Event()
        self._drain_event.set()  # not draining initially

    # -- Properties ------------------------------------------------------------

    @property
    def pool_size(self) -> int:
        return self._pool_size

    @property
    def agents(self) -> list[Agent]:
        return list(self._agents)

    @property
    def available_count(self) -> int:
        return sum(1 for a in self._agents if a.is_available)

    @property
    def active_count(self) -> int:
        return self._active_count

    @property
    def is_draining(self) -> bool:
        return self._draining

    @property
    def events(self) -> list[Any]:
        return list(self._events)

    # -- Core API --------------------------------------------------------------

    def _acquire_agent(self) -> Agent | None:
        """Find and return the first idle agent, or None."""
        for agent in self._agents:
            if agent.is_available:
                return agent
        return None

    async def dispatch_task(self, task: Task) -> Task:
        """Dispatch a task to an available agent in the pool.

        Blocks until a semaphore slot is free. Raises AgentPoolExhaustedError
        if the pool is draining and no agents will become available.
        """
        if self._draining:
            raise AgentPoolExhaustedError(self._agent_type.value, self._pool_size)

        await self._semaphore.acquire()
        try:
            agent = self._acquire_agent()
            if agent is None:
                # Shouldn't happen with proper semaphore sizing, but be defensive
                self._semaphore.release()
                raise AgentPoolExhaustedError(self._agent_type.value, self._pool_size)

            agent.assign_task(task.id)
            self._active_count += 1
            task.mark_running()

            self._events.append(
                TaskDispatched(
                    task_id=task.id,
                    command=task.command,
                    agent_id=agent.id,
                    mode=task.mode.value,
                )
            )

            try:
                result = await self._executor(task)
                task.mark_completed(result)
                agent.complete_task()
                self._events.append(
                    TaskCompleted(
                        task_id=task.id,
                        success=True,
                        duration_seconds=task.duration_seconds or 0.0,
                        result=result,
                    )
                )
            except Exception as exc:
                task.mark_failed(str(exc))
                agent.fail_task()
                self._events.append(
                    TaskCompleted(
                        task_id=task.id,
                        success=False,
                        duration_seconds=task.duration_seconds or 0.0,
                    )
                )
                raise
            finally:
                self._active_count -= 1
                self._semaphore.release()
                if self._draining and self._active_count == 0:
                    self._drain_event.set()
        except AgentPoolExhaustedError:
            raise
        except Exception:
            raise

        return task

    async def dispatch_many(self, tasks: list[Task]) -> list[Task]:
        """Dispatch multiple tasks concurrently and wait for all to finish."""
        coros = [self.dispatch_task(t) for t in tasks]
        results = await asyncio.gather(*coros, return_exceptions=True)
        completed: list[Task] = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                tasks[i].mark_failed(str(res))
                completed.append(tasks[i])
            else:
                completed.append(res)
        return completed

    async def drain(self, timeout: float = 30.0) -> None:
        """Gracefully drain the pool: stop accepting new tasks, wait for in-flight to finish."""
        self._draining = True
        for agent in self._agents:
            if agent.is_available:
                agent.status = AgentStatus.DRAINING

        if self._active_count > 0:
            self._drain_event.clear()
            try:
                await asyncio.wait_for(self._drain_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                pass

        for agent in self._agents:
            agent.status = AgentStatus.OFFLINE

    def reset(self) -> None:
        """Reset the pool to accept new tasks (after drain)."""
        self._draining = False
        self._drain_event.set()
        for agent in self._agents:
            agent.status = AgentStatus.IDLE
            agent.current_task_id = None

    # -- Health ----------------------------------------------------------------

    def health_summary(self) -> dict[str, Any]:
        return {
            "pool_size": self._pool_size,
            "agent_type": self._agent_type.value,
            "available": self.available_count,
            "active": self._active_count,
            "draining": self._draining,
            "agents": [
                {
                    "id": a.id,
                    "status": a.status.value,
                    "tasks_completed": a.tasks_completed,
                    "tasks_failed": a.tasks_failed,
                }
                for a in self._agents
            ],
        }
