"""Request Queue — priority-based async inference request queue.

URI: indestructibleeco://src/core/queue

Contracts defined by: tests/unit/test_queue.py
"""

from __future__ import annotations

import asyncio
import heapq
import json
import time
from enum import IntEnum
from typing import Any, Dict, List, Optional
from uuid import uuid1


class Priority(IntEnum):
    HIGH = 0
    NORMAL = 1
    LOW = 2


class QueuedRequest:
    """A single queued inference request."""

    __slots__ = ("request_id", "payload", "model", "priority", "timeout",
                 "created_at", "_result_event", "_result", "_error")

    def __init__(
        self,
        payload: Dict[str, Any] = None,
        model: str = "default",
        priority: Priority = Priority.NORMAL,
        timeout: float = 300.0,
    ) -> None:
        self.request_id: str = str(uuid1())
        self.payload: Dict[str, Any] = payload or {}
        self.model: str = model
        self.priority: Priority = priority
        self.timeout: float = timeout
        self.created_at: float = time.time()
        self._result_event: asyncio.Event = asyncio.Event()
        self._result: Optional[Any] = None
        self._error: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout

    def to_json(self) -> str:
        return json.dumps({
            "request_id": self.request_id,
            "payload": self.payload,
            "model": self.model,
            "priority": self.priority.value,
            "timeout": self.timeout,
            "created_at": self.created_at,
        })

    @classmethod
    def from_json(cls, data: str) -> QueuedRequest:
        d = json.loads(data)
        req = cls(
            payload=d["payload"],
            model=d.get("model", "default"),
            priority=Priority(d.get("priority", 1)),
            timeout=d.get("timeout", 300.0),
        )
        req.request_id = d["request_id"]
        req.created_at = d.get("created_at", time.time())
        return req

    def __lt__(self, other: QueuedRequest) -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at


class RequestQueue:
    """Async priority queue for inference requests.

    Features:
    - Priority ordering (HIGH > NORMAL > LOW)
    - Expired request skipping
    - Async result waiting with timeout
    - Request completion and failure signaling
    """

    def __init__(self) -> None:
        self._heap: List[QueuedRequest] = []
        self._requests: Dict[str, QueuedRequest] = {}
        self._lock = asyncio.Lock()

    @property
    def depth(self) -> int:
        return len(self._heap)

    async def enqueue(self, req: QueuedRequest) -> str:
        async with self._lock:
            heapq.heappush(self._heap, req)
            self._requests[req.request_id] = req
        return req.request_id

    async def dequeue(self) -> Optional[QueuedRequest]:
        async with self._lock:
            while self._heap:
                req = heapq.heappop(self._heap)
                if req.is_expired:
                    self._requests.pop(req.request_id, None)
                    continue
                return req
        return None

    async def complete(self, request_id: str, result: Any) -> None:
        req = self._requests.get(request_id)
        if req is not None:
            req._result = result
            req._result_event.set()

    async def fail(self, request_id: str, error: str) -> None:
        req = self._requests.get(request_id)
        if req is not None:
            req._error = error
            req._result_event.set()

    async def wait_for_result(self, request_id: str, timeout: float = 30.0) -> Any:
        req = self._requests.get(request_id)
        if req is None:
            raise KeyError(f"Request {request_id} not found")

        await asyncio.wait_for(req._result_event.wait(), timeout=timeout)

        if req._error is not None:
            raise RuntimeError(req._error)

        return req._result

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "depth": len(self._heap),
            "pending": len(self._heap),
            "running": False,
            "total_tracked": len(self._requests),
        }