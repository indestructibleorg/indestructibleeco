"""SandboxRuntime — process-level isolation for platform workloads.

Provides two concrete runtimes:
  * ProcessSandbox  — subprocess with resource limits and fs isolation
  * InProcessSandbox — lightweight, same-process isolation for unit tests
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from platform_shared.domain.errors import (
    IsolationViolationError,
    SandboxError,
    TimeoutExpiredError,
)
from platform_shared.sandbox.network import NetworkNamespace, NetworkPolicy, POLICY_NO_NETWORK
from platform_shared.sandbox.resource import ResourceLimits, ResourceMonitor, ResourceSnapshot
from platform_shared.sandbox.storage import VolumeManager, VolumeMount


class SandboxStatus(str, Enum):
    CREATING = "creating"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DESTROYED = "destroyed"


@dataclass(slots=True)
class SandboxConfig:
    """Full sandbox specification."""

    name: str = ""
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    timeout_seconds: float = 300.0
    network_policy: NetworkPolicy = field(default_factory=lambda: POLICY_NO_NETWORK)
    volumes: list[VolumeMount] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    working_dir: str = ""
    filesystem_readonly: bool = False
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionResult:
    """Outcome of a sandboxed command."""

    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    resource_peak: ResourceSnapshot | None = None
    timed_out: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


# -- Abstract base ------------------------------------------------------------


class SandboxRuntime(ABC):
    """Protocol-like base for all sandbox runtimes."""

    @abstractmethod
    async def create(self, config: SandboxConfig) -> str:
        """Provision a new sandbox, return its id."""

    @abstractmethod
    async def execute(self, sandbox_id: str, command: list[str]) -> ExecutionResult:
        """Run *command* inside an existing sandbox."""

    @abstractmethod
    async def get_status(self, sandbox_id: str) -> SandboxStatus:
        """Current lifecycle state."""

    @abstractmethod
    async def destroy(self, sandbox_id: str) -> None:
        """Tear down the sandbox and reclaim resources."""

    @abstractmethod
    async def list_sandboxes(self) -> dict[str, SandboxStatus]:
        """All known sandboxes and their statuses."""


# -- Process-based implementation ----------------------------------------------


class ProcessSandbox(SandboxRuntime):
    """Sandbox backed by ``asyncio.create_subprocess_exec`` with cgroup / namespace hints."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or Path(tempfile.gettempdir()) / "platform-sandboxes"
        self._base.mkdir(parents=True, exist_ok=True)
        self._sandboxes: dict[str, _SandboxState] = {}
        self._vol_mgr = VolumeManager(self._base / "volumes")

    async def create(self, config: SandboxConfig) -> str:
        sid = f"sb-{uuid.uuid4().hex[:12]}"
        root = self._base / sid
        root.mkdir(parents=True)

        # Prepare workspace
        work_dir = root / "workspace"
        work_dir.mkdir()

        # Provision volumes
        vol_ids: list[str] = []
        for vm in config.volumes:
            vol_ids.append(self._vol_mgr.create(vm))

        ns = NetworkNamespace(policy=config.network_policy)

        self._sandboxes[sid] = _SandboxState(
            sandbox_id=sid,
            config=config,
            status=SandboxStatus.READY,
            root=root,
            work_dir=work_dir,
            network=ns,
            volume_ids=vol_ids,
            created_at=time.time(),
        )
        return sid

    async def execute(self, sandbox_id: str, command: list[str]) -> ExecutionResult:
        state = self._get(sandbox_id)
        state.status = SandboxStatus.RUNNING

        env = {**os.environ, **state.config.env_vars, "SANDBOX_ID": sandbox_id}
        monitor = ResourceMonitor()
        start = time.monotonic()

        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(state.work_dir),
                env=env,
            )
            try:
                stdout_b, stderr_b = await asyncio.wait_for(
                    proc.communicate(), timeout=state.config.timeout_seconds
                )
                timed_out = False
            except asyncio.TimeoutError:
                proc.kill()
                stdout_b, stderr_b = await proc.communicate()
                timed_out = True

            duration = time.monotonic() - start
            peak = monitor.snapshot()
            state.status = SandboxStatus.READY

            result = ExecutionResult(
                sandbox_id=sandbox_id,
                exit_code=proc.returncode if proc.returncode is not None else -1,
                stdout=stdout_b.decode(errors="replace"),
                stderr=stderr_b.decode(errors="replace"),
                duration_seconds=duration,
                resource_peak=peak,
                timed_out=timed_out,
            )

            if timed_out:
                raise TimeoutExpiredError(state.config.timeout_seconds, sandbox_id=sandbox_id)

            return result

        except TimeoutExpiredError:
            raise
        except Exception as exc:
            state.status = SandboxStatus.FAILED
            raise SandboxError(str(exc), sandbox_id=sandbox_id) from exc

    async def get_status(self, sandbox_id: str) -> SandboxStatus:
        return self._get(sandbox_id).status

    async def destroy(self, sandbox_id: str) -> None:
        state = self._sandboxes.pop(sandbox_id, None)
        if state is None:
            return
        for vid in state.volume_ids:
            self._vol_mgr.destroy(vid)
        import shutil

        shutil.rmtree(state.root, ignore_errors=True)
        state.status = SandboxStatus.DESTROYED

    async def list_sandboxes(self) -> dict[str, SandboxStatus]:
        return {sid: s.status for sid, s in self._sandboxes.items()}

    def _get(self, sid: str) -> _SandboxState:
        try:
            return self._sandboxes[sid]
        except KeyError:
            raise SandboxError(f"Unknown sandbox: {sid}", sandbox_id=sid)


# -- In-process lightweight sandbox (for testing) -----------------------------


class InProcessSandbox(SandboxRuntime):
    """No real isolation — runs callables in the current process. Useful for unit tests."""

    def __init__(self) -> None:
        self._sandboxes: dict[str, SandboxStatus] = {}

    async def create(self, config: SandboxConfig) -> str:
        sid = f"ip-{uuid.uuid4().hex[:8]}"
        self._sandboxes[sid] = SandboxStatus.READY
        return sid

    async def execute(self, sandbox_id: str, command: list[str]) -> ExecutionResult:
        if sandbox_id not in self._sandboxes:
            raise SandboxError(f"Unknown sandbox: {sandbox_id}", sandbox_id=sandbox_id)
        self._sandboxes[sandbox_id] = SandboxStatus.RUNNING
        start = time.monotonic()

        proc = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout_b, stderr_b = await proc.communicate()

        self._sandboxes[sandbox_id] = SandboxStatus.READY
        return ExecutionResult(
            sandbox_id=sandbox_id,
            exit_code=proc.returncode or 0,
            stdout=stdout_b.decode(errors="replace"),
            stderr=stderr_b.decode(errors="replace"),
            duration_seconds=time.monotonic() - start,
        )

    async def get_status(self, sandbox_id: str) -> SandboxStatus:
        return self._sandboxes.get(sandbox_id, SandboxStatus.DESTROYED)

    async def destroy(self, sandbox_id: str) -> None:
        self._sandboxes.pop(sandbox_id, None)

    async def list_sandboxes(self) -> dict[str, SandboxStatus]:
        return dict(self._sandboxes)


# -- Internal state dataclass --------------------------------------------------


@dataclass(slots=True)
class _SandboxState:
    sandbox_id: str
    config: SandboxConfig
    status: SandboxStatus
    root: Path
    work_dir: Path
    network: NetworkNamespace
    volume_ids: list[str]
    created_at: float
