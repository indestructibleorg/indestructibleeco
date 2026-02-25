"""Volume and filesystem isolation for sandboxed execution."""

from __future__ import annotations

import shutil
import tempfile
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class VolumeType(str, Enum):
    TMPFS = "tmpfs"          # In-memory, volatile
    BIND = "bind"            # Host path bind mount
    OVERLAY = "overlay"      # Overlay FS (copy-on-write)
    EPHEMERAL = "ephemeral"  # Temp dir, cleaned on destroy


@dataclass(frozen=True, slots=True)
class VolumeMount:
    """Declarative volume mount specification."""

    source: str
    target: str
    volume_type: VolumeType = VolumeType.EPHEMERAL
    readonly: bool = False
    size_mb: int = 256
    label: str = ""

    @property
    def mount_options(self) -> list[str]:
        opts = ["ro"] if self.readonly else ["rw"]
        if self.volume_type == VolumeType.TMPFS:
            opts.append(f"size={self.size_mb}m")
        return opts


class VolumeManager:
    """Manages volume lifecycle for sandboxes and containers."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or Path(tempfile.gettempdir()) / "platform-volumes"
        self._base.mkdir(parents=True, exist_ok=True)
        self._volumes: dict[str, Path] = {}

    def create(self, mount: VolumeMount) -> str:
        vol_id = f"vol-{uuid.uuid4().hex[:12]}"
        vol_path = self._base / vol_id

        if mount.volume_type == VolumeType.EPHEMERAL:
            vol_path.mkdir(parents=True, exist_ok=True)
        elif mount.volume_type == VolumeType.TMPFS:
            vol_path.mkdir(parents=True, exist_ok=True)
        elif mount.volume_type == VolumeType.BIND:
            src = Path(mount.source)
            if not src.exists():
                raise FileNotFoundError(f"Bind source not found: {mount.source}")
            vol_path = src  # bind mounts use the source directly
        elif mount.volume_type == VolumeType.OVERLAY:
            vol_path.mkdir(parents=True, exist_ok=True)
            (vol_path / "upper").mkdir(exist_ok=True)
            (vol_path / "work").mkdir(exist_ok=True)
            (vol_path / "merged").mkdir(exist_ok=True)

        self._volumes[vol_id] = vol_path
        return vol_id

    def get_path(self, vol_id: str) -> Path:
        if vol_id not in self._volumes:
            raise KeyError(f"Unknown volume: {vol_id}")
        return self._volumes[vol_id]

    def destroy(self, vol_id: str) -> None:
        path = self._volumes.pop(vol_id, None)
        if path and path.exists() and str(path).startswith(str(self._base)):
            shutil.rmtree(path, ignore_errors=True)

    def destroy_all(self) -> int:
        count = len(self._volumes)
        for vid in list(self._volumes):
            self.destroy(vid)
        return count

    @property
    def active_volumes(self) -> dict[str, Path]:
        return dict(self._volumes)
