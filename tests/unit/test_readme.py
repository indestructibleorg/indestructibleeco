"""Unit tests for README (Step 36)."""
import os
import pytest

README = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")


class TestREADME:
    def test_exists(self):
        assert os.path.isfile(README)

    def test_has_quick_start(self):
        with open(README, encoding='utf-8') as f:
            content = f.read()
        assert "Quick Start" in content

    def test_has_architecture_tree(self):
        with open(README, encoding='utf-8') as f:
            content = f.read()
        assert "backend/" in content
        assert "platforms/" in content

    def test_has_ci_section(self):
        with open(README, encoding='utf-8') as f:
            content = f.read()
        assert "CI/CD" in content
        assert "5-gate" in content

    def test_has_doc_links(self):
        with open(README, encoding='utf-8') as f:
            content = f.read()
        assert "docs/API.md" in content
        assert "docs/ARCHITECTURE.md" in content
        assert "docs/DEPLOYMENT.md" in content

    def test_has_license(self):
        with open(README, encoding='utf-8') as f:
            content = f.read()
        assert "Apache-2.0" in content
