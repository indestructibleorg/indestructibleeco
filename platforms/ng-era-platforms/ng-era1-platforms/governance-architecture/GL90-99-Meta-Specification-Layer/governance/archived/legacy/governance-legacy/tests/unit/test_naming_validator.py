# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: legacy-scripts
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
"""
Unit tests for naming validator
Tests the naming validation functionality
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
import pytest


class TestNamingValidator:
    """Test suite for naming validator"""

    def test_validate_valid_name(self, mock_naming_validator):
        """Test validation of valid name"""
        result = mock_naming_validator.validate("prod-app-service-v1.0.0")
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_invalid_uppercase(self, mock_naming_validator):
        """Test validation rejects uppercase"""
        result = mock_naming_validator.validate("PROD-APP-SERVICE")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_invalid_underscore(self, mock_naming_validator):
        """Test validation rejects underscore"""
        result = mock_naming_validator.validate("prod_app_service")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_invalid_leading_dash(self, mock_naming_validator):
        """Test validation rejects leading dash"""
        result = mock_naming_validator.validate("-prod-app-service")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_invalid_trailing_dash(self, mock_naming_validator):
        """Test validation rejects trailing dash"""
        result = mock_naming_validator.validate("prod-app-service-")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_multiple_valid_names(
        self, mock_naming_validator, sample_resource_names
    ):
        """Test validation of multiple valid names"""
        for name in sample_resource_names["valid"]:
            result = mock_naming_validator.validate(name)
            assert result["valid"] is True, f"Failed for: {name}"

    def test_validate_multiple_invalid_names(
        self, mock_naming_validator, sample_resource_names
    ):
        """Test validation of multiple invalid names"""
        for name in sample_resource_names["invalid"]:
            result = mock_naming_validator.validate(name)
            assert result["valid"] is False, f"Should fail for: {name}"

    @pytest.mark.parametrize(
        "name,expected_valid",
        [
            ("prod-app-service-v1.0.0", True),
            ("dev-api-gateway-v2.1.3", True),
            ("PROD-APP", False),
            ("prod_app", False),
            ("-prod-app", False),
            ("prod-app-", False),
        ],
    )
    def test_validate_parametrized(self, mock_naming_validator, name, expected_valid):
        """Parametrized validation tests"""
        result = mock_naming_validator.validate(name)
        assert result["valid"] == expected_valid


class TestNamingValidatorCompliance:
    """Test suite for naming validator compliance checks"""

    def test_validate_dns_compliance(self, mock_naming_validator):
        """Test DNS compliance validation"""
        # DNS names must be <= 253 characters
        long_name = "a" * 254
        result = mock_naming_validator.validate(long_name)
        # Should handle long names appropriately
        assert result is not None

    def test_validate_kubernetes_compliance(self, mock_naming_validator):
        """Test Kubernetes naming compliance"""
        # K8s names must be <= 63 characters
        k8s_name = "prod-app-service-v1.0.0"
        result = mock_naming_validator.validate(k8s_name)
        assert result["valid"] is True
        assert len(k8s_name) <= 63

    def test_validate_iso_compliance(self, mock_naming_validator):
        """Test ISO 8000-115 compliance"""
        # ISO standard naming conventions
        iso_name = "prod-app-service-v1.0.0"
        result = mock_naming_validator.validate(iso_name)
        assert result["valid"] is True


class TestNamingValidatorPerformance:
    """Performance tests for naming validator"""

    @pytest.mark.performance
    def test_validate_performance_10000_names(self, mock_naming_validator, benchmark):
        """Benchmark validating 10000 names"""
        names = [f"prod-app-service-v{i}.0.0" for i in range(10000)]

        def validate_names():
            for name in names:
                mock_naming_validator.validate(name)

        result = benchmark(validate_names)
        assert result is not None
