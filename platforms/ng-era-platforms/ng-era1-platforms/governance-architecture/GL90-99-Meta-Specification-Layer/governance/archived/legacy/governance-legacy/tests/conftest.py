# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: legacy-scripts
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
"""
MachineNativeOps Naming Governance - Test Configuration
Pytest configuration and fixtures for all test suites
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory fixture"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def config_dir():
    """Configuration directory fixture"""
    return project_root / "naming-gl-platform.governance-v1.0.0" / "config"


@pytest.fixture(scope="session")
def machine_spec_path(config_dir):
    """Machine spec YAML path fixture"""
    return config_dir / "machine-spec.yaml"


@pytest.fixture
def sample_resource_names():
    """Sample resource names for testing"""
    return {
        "valid": [
            "prod-app-service-v1.0.0",
            "dev-api-gateway-v2.1.3",
            "staging-database-postgres-v3.0.0",
        ],
        "invalid": [
            "PROD-APP-SERVICE",  # uppercase
            "prod_app_service",  # underscore
            "prod-app-service-",  # trailing dash
            "-prod-app-service",  # leading dash
            "prod..app",  # double dots
        ],
    }


@pytest.fixture
def quantum_config():
    """Quantum configuration fixture"""
    return {
        "backend": "ibm_quantum_falcon",
        "entanglement_depth": 7,
        "coherence_threshold": 0.9999,
        "error_correction": "surface_code_v5",
        "qubits": 256,
        "shots": 1024,
    }


@pytest.fixture
def mock_naming_generator():
    """Mock naming generator for testing"""

    class MockNamingGenerator:
        def generate(self, env, app, resource, version):
            return f"{env}-{app}-{resource}-{version}"

        def validate_pattern(self, name):
            import re

            pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
            return bool(re.match(pattern, name))

    return MockNamingGenerator()


@pytest.fixture
def mock_naming_validator():
    """Mock naming validator for testing"""

    class MockNamingValidator:
        def validate(self, name):
            import re

            pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
            if not re.match(pattern, name):
                return {"valid": False, "errors": ["Invalid pattern"]}
            return {"valid": True, "errors": []}

    return MockNamingValidator()


@pytest.fixture
def performance_metrics():
    """Performance metrics fixture"""
    return {
        "baseline": {
            "processing_time": 48 * 3600,  # 48 hours in seconds
            "coverage": 0.72,
            "violation_detection": 0.72,
        },
        "extended": {
            "processing_time": 2 * 3600,  # 2 hours in seconds
            "coverage": 0.95,
            "violation_detection": 0.95,
        },
        "quantum": {
            "processing_time": 11,  # 11 seconds
            "coverage": 0.998,
            "violation_detection": 0.998,
        },
    }


# Pytest configuration
def pytest_configure(config):
    """Pytest configuration hook"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "quantum: Quantum-specific tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
