"""Tests for the shared kernel — sandbox, container, environment, protocols."""

import asyncio
import pytest

from platform_shared.domain import PlatformId, SemVer, SandboxError, TimeoutExpiredError
from platform_shared.sandbox.runtime import (
    ProcessSandbox,
    InProcessSandbox,
    SandboxConfig,
    SandboxStatus,
)
from platform_shared.sandbox.container import ContainerConfig, ContainerStatus, LocalContainerRuntime
from platform_shared.sandbox.environment import (
    LocalEnvironmentManager,
    EnvironmentProfile,
    EnvironmentTier,
    EnvironmentStatus,
    ServiceEndpoint,
)
from platform_shared.sandbox.resource import ResourceLimits, ResourceSnapshot, ResourceMonitor
from platform_shared.sandbox.network import (
    NetworkPolicy,
    NetworkRule,
    NetworkAction,
    NetworkDirection,
    POLICY_NO_NETWORK,
    POLICY_HTTP_ONLY,
)
from platform_shared.sandbox.storage import VolumeManager, VolumeMount, VolumeType
from platform_shared.protocols.event_bus import Event, LocalEventBus
from platform_shared.protocols.engine import EngineStatus
from platform_shared.protocols.health import HealthStatus, HealthReport


# -- Domain -------------------------------------------------------------------


class TestPlatformId:
    def test_valid(self):
        pid = PlatformId("automation-platform")
        assert str(pid) == "automation-platform"
        assert pid.package_name == "automation_platform"

    def test_invalid_uppercase(self):
        with pytest.raises(ValueError):
            PlatformId("Automation")

    def test_invalid_too_short(self):
        with pytest.raises(ValueError):
            PlatformId("ab")


class TestSemVer:
    def test_parse(self):
        v = SemVer.parse("1.2.3")
        assert v.major == 1 and v.minor == 2 and v.patch == 3

    def test_comparison(self):
        assert SemVer(1, 0, 0) < SemVer(2, 0, 0)
        assert SemVer(1, 1, 0) < SemVer(1, 2, 0)

    def test_bump(self):
        v = SemVer(1, 2, 3)
        assert v.bump_patch() == SemVer(1, 2, 4)
        assert v.bump_minor() == SemVer(1, 3, 0)
        assert v.bump_major() == SemVer(2, 0, 0)


# -- Resource -----------------------------------------------------------------


class TestResourceLimits:
    def test_to_cgroup(self):
        limits = ResourceLimits(cpu_cores=2.0, memory_mb=1024)
        cg = limits.to_cgroup_dict()
        assert cg["cpu.max"] == "200000 100000"
        assert cg["memory.max"] == str(1024 * 1024 * 1024)

    def test_snapshot_exceeds(self):
        limits = ResourceLimits(memory_mb=512, max_open_fds=100)
        snap = ResourceSnapshot(memory_mb=600, open_fds=150)
        violations = snap.exceeds(limits)
        assert len(violations) == 2
        assert "memory" in violations[0]


class TestResourceMonitor:
    def test_snapshot(self):
        mon = ResourceMonitor()
        snap = mon.snapshot()
        assert snap.timestamp > 0
        assert len(mon.history) == 1


# -- Network ------------------------------------------------------------------


class TestNetworkPolicy:
    def test_no_network_denies(self):
        assert not POLICY_NO_NETWORK.allows(NetworkDirection.EGRESS, 80)

    def test_http_allows_80_443(self):
        assert POLICY_HTTP_ONLY.allows(NetworkDirection.BOTH, 80)
        assert POLICY_HTTP_ONLY.allows(NetworkDirection.BOTH, 443)
        assert not POLICY_HTTP_ONLY.allows(NetworkDirection.BOTH, 8080)


# -- Storage ------------------------------------------------------------------


class TestVolumeManager:
    def test_create_and_destroy(self, tmp_path):
        mgr = VolumeManager(base_dir=tmp_path / "vols")
        mount = VolumeMount(source="", target="/data", volume_type=VolumeType.EPHEMERAL)
        vid = mgr.create(mount)
        assert vid.startswith("vol-")
        assert mgr.get_path(vid).exists()
        mgr.destroy(vid)
        assert vid not in mgr.active_volumes

    def test_destroy_all(self, tmp_path):
        mgr = VolumeManager(base_dir=tmp_path / "vols")
        mount = VolumeMount(source="", target="/a", volume_type=VolumeType.EPHEMERAL)
        mgr.create(mount)
        mgr.create(mount)
        assert mgr.destroy_all() == 2
        assert len(mgr.active_volumes) == 0


# -- Sandbox Runtime ----------------------------------------------------------


class TestProcessSandbox:
    @pytest.fixture
    def sandbox(self, tmp_path):
        return ProcessSandbox(base_dir=tmp_path / "sb")

    @pytest.mark.asyncio
    async def test_create_and_list(self, sandbox):
        sid = await sandbox.create(SandboxConfig(name="test"))
        assert sid.startswith("sb-")
        sandboxes = await sandbox.list_sandboxes()
        assert sandboxes[sid] == SandboxStatus.READY

    @pytest.mark.asyncio
    async def test_execute_echo(self, sandbox):
        sid = await sandbox.create(SandboxConfig(name="echo-test"))
        result = await sandbox.execute(sid, ["echo", "hello"])
        assert result.success
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_with_env(self, sandbox):
        config = SandboxConfig(name="env-test", env_vars={"MY_VAR": "42"})
        sid = await sandbox.create(config)
        result = await sandbox.execute(sid, ["sh", "-c", "echo $MY_VAR"])
        assert "42" in result.stdout

    @pytest.mark.asyncio
    async def test_destroy(self, sandbox):
        sid = await sandbox.create(SandboxConfig(name="destroy-test"))
        await sandbox.destroy(sid)
        sandboxes = await sandbox.list_sandboxes()
        assert sid not in sandboxes


class TestInProcessSandbox:
    @pytest.mark.asyncio
    async def test_execute(self):
        sb = InProcessSandbox()
        sid = await sb.create(SandboxConfig())
        result = await sb.execute(sid, ["echo", "in-process"])
        assert result.success
        assert "in-process" in result.stdout


# -- Environment --------------------------------------------------------------


class TestLocalEnvironmentManager:
    @pytest.fixture
    def env_mgr(self):
        return LocalEnvironmentManager()

    @pytest.mark.asyncio
    async def test_create_and_status(self, env_mgr):
        profile = EnvironmentProfile(name="dev", tier=EnvironmentTier.DEV)
        eid = await env_mgr.create(profile)
        assert eid.startswith("env-dev-")
        assert await env_mgr.get_status(eid) == EnvironmentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_config_get_set(self, env_mgr):
        eid = await env_mgr.create(EnvironmentProfile(name="cfg", config={"a": 1}))
        assert await env_mgr.get_config(eid, "a") == 1
        await env_mgr.set_config(eid, "b", 2)
        assert await env_mgr.get_config(eid, "b") == 2

    @pytest.mark.asyncio
    async def test_service_discovery(self, env_mgr):
        svc = ServiceEndpoint(name="api", host="localhost", port=8080)
        profile = EnvironmentProfile(name="svc", services={"api": svc})
        eid = await env_mgr.create(profile)
        found = await env_mgr.discover_service(eid, "api")
        assert found.url == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_promote(self, env_mgr):
        dev = await env_mgr.create(EnvironmentProfile(name="dev", config={"feature_x": True}))
        stg = await env_mgr.create(EnvironmentProfile(name="staging"))
        result = await env_mgr.promote(dev, stg)
        assert "feature_x" in result["promoted_keys"]
        assert await env_mgr.get_config(stg, "feature_x") is True

    @pytest.mark.asyncio
    async def test_secrets_injection(self, env_mgr):
        eid = await env_mgr.create(EnvironmentProfile(name="sec"))
        await env_mgr.inject_secrets(eid, {"DB_PASSWORD": "s3cret"})
        log = await env_mgr.get_audit_log(eid)
        assert any(e["event"] == "secrets_injected" for e in log)

    @pytest.mark.asyncio
    async def test_destroy(self, env_mgr):
        eid = await env_mgr.create(EnvironmentProfile(name="tmp"))
        await env_mgr.destroy(eid)
        assert eid not in await env_mgr.list_environments()


# -- Event Bus ----------------------------------------------------------------


class TestLocalEventBus:
    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        bus = LocalEventBus()
        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe("test.topic", handler)
        await bus.publish(Event(topic="test.topic", payload={"x": 1}, source="unit-test"))
        assert len(received) == 1
        assert received[0].payload == {"x": 1}

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        bus = LocalEventBus()
        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe("t", handler)
        bus.unsubscribe("t", handler)
        await bus.publish(Event(topic="t", payload={}))
        assert len(received) == 0


# -- Health -------------------------------------------------------------------


class TestHealthReport:
    def test_is_healthy(self):
        assert HealthReport(component="x", status=HealthStatus.HEALTHY).is_healthy
        assert HealthReport(component="x", status=HealthStatus.DEGRADED).is_healthy
        assert not HealthReport(component="x", status=HealthStatus.UNHEALTHY).is_healthy
