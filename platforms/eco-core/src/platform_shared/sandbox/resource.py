"""Resource limits and runtime monitoring for sandboxed execution."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """Declarative resource budget for a sandbox or container."""

    cpu_cores: float = 1.0
    memory_mb: int = 512
    disk_mb: int = 1024
    max_open_fds: int = 256
    max_processes: int = 32
    max_threads: int = 64
    network_bandwidth_mbps: float = 100.0

    def to_cgroup_dict(self) -> dict[str, str]:
        """Translate to cgroup-v2 key/value pairs."""
        return {
            "cpu.max": f"{int(self.cpu_cores * 100_000)} 100000",
            "memory.max": str(self.memory_mb * 1024 * 1024),
            "pids.max": str(self.max_processes),
        }

    def to_container_resources(self) -> dict:
        """Translate to OCI-style resource spec."""
        return {
            "cpus": self.cpu_cores,
            "mem_limit": f"{self.memory_mb}m",
            "pids_limit": self.max_processes,
            "storage_opt": {"size": f"{self.disk_mb}m"},
        }


@dataclass(slots=True)
class ResourceSnapshot:
    """Point-in-time resource usage reading."""

    timestamp: float = field(default_factory=time.monotonic)
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    disk_mb: float = 0.0
    open_fds: int = 0
    active_processes: int = 0
    active_threads: int = 0

    def exceeds(self, limits: ResourceLimits) -> list[str]:
        """Return list of violated limits (empty == healthy)."""
        violations: list[str] = []
        if self.memory_mb > limits.memory_mb:
            violations.append(f"memory: {self.memory_mb:.0f}MB > {limits.memory_mb}MB")
        if self.disk_mb > limits.disk_mb:
            violations.append(f"disk: {self.disk_mb:.0f}MB > {limits.disk_mb}MB")
        if self.open_fds > limits.max_open_fds:
            violations.append(f"fds: {self.open_fds} > {limits.max_open_fds}")
        if self.active_processes > limits.max_processes:
            violations.append(f"procs: {self.active_processes} > {limits.max_processes}")
        return violations


class ResourceMonitor:
    """Lightweight resource monitor (reads /proc on Linux, falls back to os module)."""

    def __init__(self, pid: int | None = None) -> None:
        self._pid = pid or os.getpid()
        self._history: list[ResourceSnapshot] = []

    def snapshot(self) -> ResourceSnapshot:
        snap = ResourceSnapshot(
            cpu_percent=self._read_cpu(),
            memory_mb=self._read_memory(),
            open_fds=self._count_fds(),
        )
        self._history.append(snap)
        return snap

    @property
    def history(self) -> list[ResourceSnapshot]:
        return list(self._history)

    def _read_cpu(self) -> float:
        try:
            times = os.times()
            return times.user + times.system
        except OSError:
            return 0.0

    def _read_memory(self) -> float:
        try:
            with open(f"/proc/{self._pid}/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1]) / 1024  # kB → MB
        except (OSError, ValueError):
            pass
        return 0.0

    def _count_fds(self) -> int:
        try:
            return len(os.listdir(f"/proc/{self._pid}/fd"))
        except OSError:
            return 0
