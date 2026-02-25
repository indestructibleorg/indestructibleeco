"""Test fixtures for infrastructure platform tests."""

import pytest

from infrastructure_platform.engines.deployment_engine import DeploymentEngine
from infrastructure_platform.engines.service_engine import ServiceEngine
from infrastructure_platform.engines.provisioner import Provisioner
from infrastructure_platform.sandbox.infra_sandbox import InfraSandbox
from infrastructure_platform.presentation.api import InfrastructureAPI


@pytest.fixture
def deployment_engine():
    """Fresh DeploymentEngine instance."""
    return DeploymentEngine()


@pytest.fixture
def service_engine(deployment_engine):
    """ServiceEngine wired to the deployment engine's internal state."""
    return ServiceEngine(deployments=deployment_engine._deployments)


@pytest.fixture
def provisioner():
    """Fresh Provisioner instance."""
    return Provisioner()


@pytest.fixture
def infra_sandbox():
    """Fresh InfraSandbox instance."""
    return InfraSandbox()


@pytest.fixture
def api(deployment_engine, service_engine, provisioner):
    """InfrastructureAPI with shared engines."""
    return InfrastructureAPI(
        deployment_engine=deployment_engine,
        service_engine=service_engine,
        provisioner=provisioner,
    )
