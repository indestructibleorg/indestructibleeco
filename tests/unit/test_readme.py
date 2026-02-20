"""Unit tests for README (Step 36)."""
import os
import pytest

README = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")


class TestREADME:
    def test_exists(self):
        assert os.path.isfile(README)

    def test_has_quick_start(self):
        content = open(README).read()
        assert "Quick Start" in content

    def test_has_architecture_tree(self):
        content = open(README).read()
        assert "backend/" in content
        assert "platforms/" in content

    def test_has_ci_section(self):
        content = open(README).read()
        assert "CI/CD" in content
        assert "5-gate" in content

    def test_has_doc_links(self):
        content = open(README).read()
        assert "docs/API.md" in content
        assert "docs/ARCHITECTURE.md" in content
        assert "docs/DEPLOYMENT.md" in content

    def test_has_license(self):
        content = open(README).read()
        assert "Apache-2.0" in content
