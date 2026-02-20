"""Unit tests for YAMLStudio + Login page (Step 27)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestYAMLStudioPage:
    def test_yaml_studio_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "platforms", "web", "app", "src", "pages", "YAMLStudio.tsx")
        assert os.path.isfile(path)

    def test_yaml_studio_has_components(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "platforms", "web", "app", "src", "pages", "YAMLStudio.tsx")
        with open(path) as f:
            content = f.read()
        assert "handleValidate" in content
        assert "handleGenerate" in content
        assert "yaml-editor" in content
        assert "governance" in content.lower()
        assert "document_metadata" in content

    def test_yaml_studio_has_form(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "platforms", "web", "app", "src", "pages", "YAMLStudio.tsx")
        with open(path) as f:
            content = f.read()
        assert "serviceName" in content
        assert "namespace" in content
        assert "Deployment" in content

    def test_login_page_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "platforms", "web", "app", "src", "pages", "Login.tsx")
        assert os.path.isfile(path)

    def test_login_has_form(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "platforms", "web", "app", "src", "pages", "Login.tsx")
        with open(path) as f:
            content = f.read()
        assert "email" in content.lower() or "login" in content.lower()
