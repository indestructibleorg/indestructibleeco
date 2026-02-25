"""ContainerRuntime — OCI-compatible container lifecycle management.

Provides:
  * LocalContainerRuntime — manages containers via subprocess calls to docker/podman CLI
  * Lightweight container abstractions usable without a real daemon (for dev/test)
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from platform_shared.domain.errors import ContainerError
from platform_shared.sandbox.resource import ResourceLimits


class ContainerStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    REMOVING = "removing"
    REMOVED = "removed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class HealthCheckConfig:
    command: list[str]
    interval_seconds: float = 30.0
    timeout_seconds: float = 5.0
    retries: int = 3
    start_period_seconds: float = 10.0


@dataclass(slots=True)
class ContainerConfig:
    """Declarative container specification."""

    image: str
    tag: str = "latest"
    name: str = ""
    command: list[str] = field(default_factory=list)
    entrypoint: list[str] = field(default_factory=list)
    ports: dict[int, int] = field(default_factory=dict)  # host:container
    volumes: dict[str, str] = field(default_factory=dict)  # host_path:container_path
    env_vars: dict[str, str] = field(default_factory=dict)
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    network: str = "bridge"
    labels: dict[str, str] = field(default_factory=dict)
    health_check: HealthCheckConfig | None = None
    restart_policy: str = "no"  # no | on-failure | always
    user: str = ""
    read_only_rootfs: bool = False
    cap_drop: list[str] = field(default_factory=lambda: ["ALL"])
    cap_add: list[str] = field(default_factory=list)
    security_opt: list[str] = field(default_factory=lambda: ["no-new-privileges"])

    @property
    def full_image(self) -> str:
        return f"{self.image}:{self.tag}"


@dataclass(slots=True)
class ContainerInfo:
    container_id: str
    name: str
    image: str
    status: ContainerStatus
    created_at: float
    started_at: float | None = None
    finished_at: float | None = None
    exit_code: int | None = None
    ports: dict[int, int] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ExecResult:
    container_id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float


# -- Abstract base ------------------------------------------------------------


class ContainerRuntime(ABC):
    """Abstract container runtime (docker, podman, containerd, …)."""

    @abstractmethod
    async def pull_image(self, image: str, tag: str = "latest") -> dict[str, Any]: ...

    @abstractmethod
    async def create(self, config: ContainerConfig) -> str: ...

    @abstractmethod
    async def start(self, container_id: str) -> None: ...

    @abstractmethod
    async def stop(self, container_id: str, timeout: int = 30) -> None: ...

    @abstractmethod
    async def remove(self, container_id: str, force: bool = False) -> None: ...

    @abstractmethod
    async def exec_in(self, container_id: str, command: list[str]) -> ExecResult: ...

    @abstractmethod
    async def logs(self, container_id: str, tail: int = 100) -> list[str]: ...

    @abstractmethod
    async def inspect(self, container_id: str) -> ContainerInfo: ...

    @abstractmethod
    async def list_containers(
        self, all_: bool = False, filters: dict[str, str] | None = None
    ) -> list[ContainerInfo]: ...

    # Convenience ---

    async def run(self, config: ContainerConfig) -> str:
        """Pull + create + start in one call."""
        await self.pull_image(config.image, config.tag)
        cid = await self.create(config)
        await self.start(cid)
        return cid


# -- Local CLI-based implementation -------------------------------------------


class LocalContainerRuntime(ContainerRuntime):
    """Drives containers via ``docker`` or ``podman`` CLI."""

    def __init__(self, engine: str = "docker") -> None:
        self._engine = engine
        self._containers: dict[str, ContainerInfo] = {}

    async def _run_cli(self, *args: str, check: bool = True) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            self._engine,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await proc.communicate()
        rc = proc.returncode or 0
        out = stdout_b.decode(errors="replace").strip()
        err = stderr_b.decode(errors="replace").strip()
        if check and rc != 0:
            raise ContainerError(f"{self._engine} {' '.join(args)} failed: {err}")
        return rc, out, err

    async def pull_image(self, image: str, tag: str = "latest") -> dict[str, Any]:
        full = f"{image}:{tag}"
        _, out, _ = await self._run_cli("pull", full)
        return {"image": full, "output": out}

    async def create(self, config: ContainerConfig) -> str:
        cid = f"ctr-{uuid.uuid4().hex[:12]}"
        name = config.name or cid
        args: list[str] = ["create", "--name", name]

        # Resource limits
        res = config.resource_limits
        args += [f"--cpus={res.cpu_cores}", f"--memory={res.memory_mb}m"]
        args += [f"--pids-limit={res.max_processes}"]

        # Ports
        for host_port, ctr_port in config.ports.items():
            args += ["-p", f"{host_port}:{ctr_port}"]

        # Volumes
        for host_path, ctr_path in config.volumes.items():
            args += ["-v", f"{host_path}:{ctr_path}"]

        # Environment
        for k, v in config.env_vars.items():
            args += ["-e", f"{k}={v}"]

        # Labels
        for k, v in config.labels.items():
            args += ["--label", f"{k}={v}"]

        # Security
        if config.read_only_rootfs:
            args.append("--read-only")
        for cap in config.cap_drop:
            args += ["--cap-drop", cap]
        for cap in config.cap_add:
            args += ["--cap-add", cap]
        for opt in config.security_opt:
            args += ["--security-opt", opt]

        args += ["--restart", config.restart_policy]
        args += ["--network", config.network]

        if config.entrypoint:
            args += ["--entrypoint", config.entrypoint[0]]

        args.append(config.full_image)
        if config.command:
            args += config.command

        _, out, _ = await self._run_cli(*args)
        real_id = out[:12] if out else cid

        self._containers[real_id] = ContainerInfo(
            container_id=real_id,
            name=name,
            image=config.full_image,
            status=ContainerStatus.CREATED,
            created_at=time.time(),
            ports=dict(config.ports),
            labels=dict(config.labels),
        )
        return real_id

    async def start(self, container_id: str) -> None:
        await self._run_cli("start", container_id)
        if container_id in self._containers:
            self._containers[container_id].status = ContainerStatus.RUNNING
            self._containers[container_id].started_at = time.time()

    async def stop(self, container_id: str, timeout: int = 30) -> None:
        await self._run_cli("stop", "-t", str(timeout), container_id)
        if container_id in self._containers:
            self._containers[container_id].status = ContainerStatus.STOPPED
            self._containers[container_id].finished_at = time.time()

    async def remove(self, container_id: str, force: bool = False) -> None:
        args = ["rm"]
        if force:
            args.append("-f")
        args.append(container_id)
        await self._run_cli(*args, check=False)
        self._containers.pop(container_id, None)

    async def exec_in(self, container_id: str, command: list[str]) -> ExecResult:
        start = time.monotonic()
        rc, out, err = await self._run_cli("exec", container_id, *command, check=False)
        return ExecResult(
            container_id=container_id,
            exit_code=rc,
            stdout=out,
            stderr=err,
            duration_seconds=time.monotonic() - start,
        )

    async def logs(self, container_id: str, tail: int = 100) -> list[str]:
        _, out, _ = await self._run_cli("logs", "--tail", str(tail), container_id)
        return out.splitlines()

    async def inspect(self, container_id: str) -> ContainerInfo:
        _, out, _ = await self._run_cli("inspect", container_id)
        try:
            data = json.loads(out)
            if isinstance(data, list) and data:
                data = data[0]
            state = data.get("State", {})
            status_str = state.get("Status", "unknown")
            status_map = {
                "created": ContainerStatus.CREATED,
                "running": ContainerStatus.RUNNING,
                "paused": ContainerStatus.PAUSED,
                "exited": ContainerStatus.STOPPED,
            }
            return ContainerInfo(
                container_id=container_id,
                name=data.get("Name", "").lstrip("/"),
                image=data.get("Config", {}).get("Image", ""),
                status=status_map.get(status_str, ContainerStatus.STOPPED),
                created_at=time.time(),
                exit_code=state.get("ExitCode"),
            )
        except (json.JSONDecodeError, KeyError) as exc:
            raise ContainerError(
                f"Failed to parse inspect output: {exc}", container_id=container_id
            ) from exc

    async def list_containers(
        self, all_: bool = False, filters: dict[str, str] | None = None
    ) -> list[ContainerInfo]:
        args = ["ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"]
        if all_:
            args.append("-a")
        if filters:
            for k, v in filters.items():
                args += ["-f", f"{k}={v}"]
        _, out, _ = await self._run_cli(*args)
        results: list[ContainerInfo] = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 4:
                results.append(
                    ContainerInfo(
                        container_id=parts[0],
                        name=parts[1],
                        image=parts[2],
                        status=ContainerStatus.RUNNING
                        if "Up" in parts[3]
                        else ContainerStatus.STOPPED,
                        created_at=time.time(),
                    )
                )
        return results
