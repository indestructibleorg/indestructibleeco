"""EnvironmentManager — multi-environment lifecycle, config injection, service discovery.

Environments isolate platform instances across dev / staging / prod profiles.
Each environment gets its own config namespace, secret store, and service registry.
"""

from __future__ import annotations

import copy
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from platform_shared.domain.errors import EnvironmentError as EnvError
from platform_shared.sandbox.resource import ResourceLimits


class EnvironmentTier(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    SANDBOX = "sandbox"    # ephemeral, per-branch
    PREVIEW = "preview"    # PR-based


class EnvironmentStatus(str, Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    DEGRADED = "degraded"
    DRAINING = "draining"
    DESTROYED = "destroyed"


@dataclass(frozen=True, slots=True)
class ServiceEndpoint:
    """Resolved address of a service within an environment."""

    name: str
    host: str
    port: int
    protocol: str = "http"
    path: str = ""
    healthy: bool = True

    @property
    def url(self) -> str:
        base = f"{self.protocol}://{self.host}:{self.port}"
        return f"{base}{self.path}" if self.path else base


@dataclass(slots=True)
class EnvironmentProfile:
    """Blueprint for creating an environment."""

    name: str
    tier: EnvironmentTier = EnvironmentTier.DEV
    config: dict[str, Any] = field(default_factory=dict)
    secrets: dict[str, str] = field(default_factory=dict)
    services: dict[str, ServiceEndpoint] = field(default_factory=dict)
    resource_quotas: ResourceLimits = field(default_factory=ResourceLimits)
    labels: dict[str, str] = field(default_factory=dict)
    ttl_seconds: float | None = None  # auto-destroy after TTL (sandbox/preview)


@dataclass(slots=True)
class _EnvironmentState:
    env_id: str
    profile: EnvironmentProfile
    status: EnvironmentStatus
    config: dict[str, Any]
    secrets: dict[str, str]
    services: dict[str, ServiceEndpoint]
    created_at: float
    audit_log: list[dict[str, Any]]


class EnvironmentManager:
    """Abstract environment manager — override for cloud / k8s / local variants."""

    async def create(self, profile: EnvironmentProfile) -> str: ...
    async def destroy(self, env_id: str) -> None: ...
    async def get_config(self, env_id: str, key: str) -> Any: ...
    async def set_config(self, env_id: str, key: str, value: Any) -> None: ...
    async def inject_secrets(self, env_id: str, secrets: dict[str, str]) -> None: ...
    async def discover_service(self, env_id: str, service_name: str) -> ServiceEndpoint: ...
    async def promote(self, from_env: str, to_env: str) -> dict[str, Any]: ...
    async def get_status(self, env_id: str) -> EnvironmentStatus: ...
    async def list_environments(self) -> dict[str, EnvironmentStatus]: ...


class LocalEnvironmentManager(EnvironmentManager):
    """In-memory environment manager for local dev and testing."""

    def __init__(self) -> None:
        self._envs: dict[str, _EnvironmentState] = {}

    async def create(self, profile: EnvironmentProfile) -> str:
        env_id = f"env-{profile.tier.value}-{uuid.uuid4().hex[:8]}"
        state = _EnvironmentState(
            env_id=env_id,
            profile=profile,
            status=EnvironmentStatus.ACTIVE,
            config=dict(profile.config),
            secrets=dict(profile.secrets),
            services=dict(profile.services),
            created_at=time.time(),
            audit_log=[{"event": "created", "time": time.time()}],
        )
        self._envs[env_id] = state
        return env_id

    async def destroy(self, env_id: str) -> None:
        state = self._get(env_id)
        state.status = EnvironmentStatus.DESTROYED
        state.audit_log.append({"event": "destroyed", "time": time.time()})
        del self._envs[env_id]

    async def get_config(self, env_id: str, key: str) -> Any:
        state = self._get(env_id)
        return state.config.get(key)

    async def set_config(self, env_id: str, key: str, value: Any) -> None:
        state = self._get(env_id)
        state.config[key] = value
        state.audit_log.append({"event": "config_set", "key": key, "time": time.time()})

    async def inject_secrets(self, env_id: str, secrets: dict[str, str]) -> None:
        state = self._get(env_id)
        state.secrets.update(secrets)
        state.audit_log.append({
            "event": "secrets_injected",
            "keys": list(secrets.keys()),
            "time": time.time(),
        })

    async def discover_service(self, env_id: str, service_name: str) -> ServiceEndpoint:
        state = self._get(env_id)
        svc = state.services.get(service_name)
        if svc is None:
            raise EnvError(
                f"Service '{service_name}' not found in environment {env_id}", env_id=env_id
            )
        return svc

    async def register_service(self, env_id: str, endpoint: ServiceEndpoint) -> None:
        state = self._get(env_id)
        state.services[endpoint.name] = endpoint
        state.audit_log.append({
            "event": "service_registered",
            "service": endpoint.name,
            "time": time.time(),
        })

    async def promote(self, from_env: str, to_env: str) -> dict[str, Any]:
        src = self._get(from_env)
        dst = self._get(to_env)
        promoted_keys = list(src.config.keys())
        dst.config = copy.deepcopy(src.config)
        dst.audit_log.append({
            "event": "promoted_from",
            "source": from_env,
            "keys": promoted_keys,
            "time": time.time(),
        })
        return {"promoted_keys": promoted_keys, "from": from_env, "to": to_env}

    async def get_status(self, env_id: str) -> EnvironmentStatus:
        return self._get(env_id).status

    async def list_environments(self) -> dict[str, EnvironmentStatus]:
        return {eid: s.status for eid, s in self._envs.items()}

    async def get_audit_log(self, env_id: str) -> list[dict[str, Any]]:
        return list(self._get(env_id).audit_log)

    def _get(self, env_id: str) -> _EnvironmentState:
        try:
            return self._envs[env_id]
        except KeyError:
            raise EnvError(f"Unknown environment: {env_id}", env_id=env_id)
