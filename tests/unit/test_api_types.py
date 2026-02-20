"""Unit tests for API service TypeScript types alignment (Step 26)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestAPITypesExist:
    def test_types_file_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "api", "src", "types.ts")
        assert os.path.isfile(path)

    def test_types_has_service_health(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "api", "src", "types.ts")
        with open(path) as f:
            content = f.read()
        assert "ServiceHealth" in content
        assert "PaginatedResponse" in content
        assert "ErrorResponse" in content
        assert "JobStatus" in content
        assert "AIGenerateRequest" in content
        assert "YAMLValidateResponse" in content

    def test_types_has_exports(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "api", "src", "types.ts")
        with open(path) as f:
            content = f.read()
        assert content.count("export interface") >= 6
