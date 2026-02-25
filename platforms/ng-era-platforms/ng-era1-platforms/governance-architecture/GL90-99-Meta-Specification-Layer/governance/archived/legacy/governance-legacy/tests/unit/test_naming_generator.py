# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: legacy-scripts
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
"""
Unit tests for naming generator
Tests the core naming generation functionality
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
import re

import pytest


class TestNamingGenerator:
    """Test suite for naming generator"""

    def test_generate_basic_name(self, mock_naming_generator):
        """Test basic name generation"""
        result = mock_naming_generator.generate("prod", "app", "service", "v1.0.0")
        assert result == "prod-app-service-v1.0.0"
        assert mock_naming_generator.validate_pattern(result)

    def test_generate_with_multiple_components(self, mock_naming_generator):
        """Test name generation with multiple components"""
        result = mock_naming_generator.generate("staging", "api", "gateway", "v2.1.3")
        assert result == "staging-api-gateway-v2.1.3"
        assert mock_naming_generator.validate_pattern(result)

    def test_validate_pattern_valid_names(
        self, mock_naming_generator, sample_resource_names
    ):
        """Test pattern validation with valid names"""
        for name in sample_resource_names["valid"]:
            assert mock_naming_generator.validate_pattern(name), f"Failed for: {name}"

    def test_validate_pattern_invalid_names(
        self, mock_naming_generator, sample_resource_names
    ):
        """Test pattern validation with invalid names"""
        for name in sample_resource_names["invalid"]:
            assert not mock_naming_generator.validate_pattern(
                name
            ), f"Should fail for: {name}"

    def test_generate_lowercase_only(self, mock_naming_generator):
        """Test that generated names are lowercase only"""
        result = mock_naming_generator.generate("PROD", "APP", "SERVICE", "V1.0.0")
        assert result.islower() or result == result.lower()

    def test_generate_no_special_chars(self, mock_naming_generator):
        """Test that generated names contain no special characters"""
        result = mock_naming_generator.generate("prod", "app", "service", "v1.0.0")
        pattern = r"^[a-z0-9-\.]+$"
        assert re.match(pattern, result)

    def test_generate_no_leading_trailing_dash(self, mock_naming_generator):
        """Test that generated names have no leading/trailing dashes"""
        result = mock_naming_generator.generate("prod", "app", "service", "v1.0.0")
        assert not result.startswith("-")
        assert not result.endswith("-")

    def test_generate_no_consecutive_dashes(self, mock_naming_generator):
        """Test that generated names have no consecutive dashes"""
        result = mock_naming_generator.generate("prod", "app", "service", "v1.0.0")
        assert "--" not in result

    @pytest.mark.parametrize(
        "env,app,resource,version,expected",
        [
            ("dev", "api", "service", "v1.0.0", "dev-api-service-v1.0.0"),
            ("prod", "web", "app", "v2.1.3", "prod-web-app-v2.1.3"),
            ("staging", "db", "postgres", "v3.0.0", "staging-db-postgres-v3.0.0"),
        ],
    )
    def test_generate_parametrized(
        self, mock_naming_generator, env, app, resource, version, expected
    ):
        """Parametrized test for name generation"""
        result = mock_naming_generator.generate(env, app, resource, version)
        assert result == expected


class TestNamingGeneratorEdgeCases:
    """Test suite for naming generator edge cases"""

    def test_generate_empty_components(self, mock_naming_generator):
        """Test generation with empty components"""
        with pytest.raises(Exception):
            mock_naming_generator.generate("", "", "", "")

    def test_generate_none_components(self, mock_naming_generator):
        """Test generation with None components"""
        with pytest.raises(Exception):
            mock_naming_generator.generate(None, None, None, None)

    def test_generate_very_long_name(self, mock_naming_generator):
        """Test generation with very long components"""
        long_component = "a" * 100
        result = mock_naming_generator.generate(
            long_component, long_component, long_component, "v1.0.0"
        )
        # Should handle or truncate long names
        assert len(result) <= 253  # DNS name limit


class TestNamingGeneratorPerformance:
    """Performance tests for naming generator"""

    @pytest.mark.performance
    def test_generate_performance_1000_names(self, mock_naming_generator, benchmark):
        """Benchmark generating 1000 names"""

        def generate_names():
            for i in range(1000):
                mock_naming_generator.generate("prod", "app", "service", f"v{i}.0.0")

        result = benchmark(generate_names)
        assert result is not None

    @pytest.mark.performance
    def test_validate_performance_1000_names(
        self, mock_naming_generator, sample_resource_names, benchmark
    ):
        """Benchmark validating 1000 names"""
        names = sample_resource_names["valid"] * 334  # ~1000 names

        def validate_names():
            for name in names:
                mock_naming_generator.validate_pattern(name)

        result = benchmark(validate_names)
        assert result is not None
