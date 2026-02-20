"""Tests for release artifacts and package configuration."""
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestChangelog:
    """Verify CHANGELOG.md structure and content."""

    def _read(self):
        with open(os.path.join(REPO_ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
            return f.read()

    def test_changelog_exists(self):
        assert os.path.isfile(os.path.join(REPO_ROOT, "CHANGELOG.md"))

    def test_changelog_has_version_header(self):
        content = self._read()
        assert "## [1.0.0]" in content

    def test_changelog_has_added_section(self):
        content = self._read()
        assert "### Added" in content

    def test_changelog_has_core_platform(self):
        content = self._read()
        assert "Core Platform" in content

    def test_changelog_has_ai_service(self):
        content = self._read()
        assert "AI Service" in content

    def test_changelog_has_api_gateway(self):
        content = self._read()
        assert "API Gateway" in content

    def test_changelog_has_infrastructure(self):
        content = self._read()
        assert "Infrastructure" in content

    def test_changelog_has_testing(self):
        content = self._read()
        assert "Testing" in content

    def test_changelog_has_release_link(self):
        content = self._read()
        assert "[1.0.0]: https://github.com/indestructibleorg/indestructibleeco/releases/tag/v1.0.0" in content

    def test_changelog_semver_format(self):
        content = self._read()
        assert "Semantic Versioning" in content


class TestNpmPackages:
    """Verify NPM package.json files are release-ready."""

    PACKAGES = ["shared-types", "api-client", "ui-kit"]

    def _load(self, name):
        path = os.path.join(REPO_ROOT, "packages", name, "package.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_version_is_1_0_0(self, pkg):
        data = self._load(pkg)
        assert data["version"] == "1.0.0", f"{pkg} version is {data['version']}"

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_has_publish_config(self, pkg):
        data = self._load(pkg)
        assert "publishConfig" in data, f"{pkg} missing publishConfig"
        assert data["publishConfig"]["access"] == "public"

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_has_repository(self, pkg):
        data = self._load(pkg)
        assert "repository" in data, f"{pkg} missing repository"
        assert "indestructibleeco" in data["repository"]["url"]

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_has_files_field(self, pkg):
        data = self._load(pkg)
        assert "files" in data, f"{pkg} missing files field"
        assert "dist/" in data["files"]

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_has_license(self, pkg):
        data = self._load(pkg)
        assert data.get("license") == "Apache-2.0", f"{pkg} missing Apache-2.0 license"

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_has_build_script(self, pkg):
        data = self._load(pkg)
        assert "build" in data.get("scripts", {}), f"{pkg} missing build script"

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_has_prepublish(self, pkg):
        data = self._load(pkg)
        assert "prepublishOnly" in data.get("scripts", {}), f"{pkg} missing prepublishOnly"

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_has_homepage(self, pkg):
        data = self._load(pkg)
        assert "homepage" in data, f"{pkg} missing homepage"

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_has_keywords(self, pkg):
        data = self._load(pkg)
        assert "keywords" in data, f"{pkg} missing keywords"
        assert "indestructibleeco" in data["keywords"]


class TestPyProjectToml:
    """Verify pyproject.toml is release-ready."""

    def _read(self):
        path = os.path.join(REPO_ROOT, "backend", "ai", "pyproject.toml")
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_version_is_1_0_0(self):
        content = self._read()
        assert 'version = "1.0.0"' in content

    def test_has_license(self):
        content = self._read()
        assert 'license = "Apache-2.0"' in content

    def test_has_authors(self):
        content = self._read()
        assert "authors" in content

    def test_has_classifiers(self):
        content = self._read()
        assert "Production/Stable" in content

    def test_has_build_system(self):
        content = self._read()
        assert "[build-system]" in content

    def test_has_repository(self):
        content = self._read()
        assert "repository" in content


class TestTsConfigs:
    """Verify tsconfig.json exists for publishable packages."""

    @pytest.mark.parametrize("pkg", ["shared-types", "api-client", "ui-kit"])
    def test_tsconfig_exists(self, pkg):
        path = os.path.join(REPO_ROOT, "packages", pkg, "tsconfig.json")
        assert os.path.isfile(path), f"{pkg}/tsconfig.json missing"

    @pytest.mark.parametrize("pkg", ["shared-types", "api-client", "ui-kit"])
    def test_tsconfig_has_declaration(self, pkg):
        path = os.path.join(REPO_ROOT, "packages", pkg, "tsconfig.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("compilerOptions", {}).get("declaration") is True


class TestReleaseWorkflows:
    """Verify release workflow files exist and are valid."""

    WORKFLOWS = [
        "release.yml",
        "publish-npm.yml",
        "publish-docker.yml",
        "publish-pypi.yml",
    ]

    @pytest.mark.parametrize("wf", WORKFLOWS)
    def test_workflow_exists(self, wf):
        path = os.path.join(REPO_ROOT, ".github", "workflows", wf)
        assert os.path.isfile(path), f"Workflow {wf} missing"

    @pytest.mark.parametrize("wf", WORKFLOWS)
    def test_workflow_tag_trigger(self, wf):
        path = os.path.join(REPO_ROOT, ".github", "workflows", wf)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "v*.*.*" in content, f"{wf} missing tag trigger pattern"

    @pytest.mark.parametrize("wf", WORKFLOWS)
    def test_workflow_no_third_party_actions(self, wf):
        path = os.path.join(REPO_ROOT, ".github", "workflows", wf)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        import re
        uses_lines = re.findall(r"uses:\s+(.+)", content)
        for line in uses_lines:
            assert "indestructibleorg" in line or not uses_lines, (
                f"{wf}: third-party action found: {line}"
            )

    def test_release_creates_github_release(self):
        path = os.path.join(REPO_ROOT, ".github", "workflows", "release.yml")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "gh release create" in content

    def test_npm_publishes_all_packages(self):
        path = os.path.join(REPO_ROOT, ".github", "workflows", "publish-npm.yml")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for pkg in ["shared-types", "api-client", "ui-kit"]:
            assert pkg in content, f"publish-npm.yml missing {pkg}"

    def test_docker_pushes_to_ghcr(self):
        path = os.path.join(REPO_ROOT, ".github", "workflows", "publish-docker.yml")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "ghcr.io" in content

    def test_pypi_uses_twine(self):
        path = os.path.join(REPO_ROOT, ".github", "workflows", "publish-pypi.yml")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "twine upload" in content


class TestReadmeBadge:
    """Verify README test badge is up to date."""

    def test_badge_shows_500(self):
        path = os.path.join(REPO_ROOT, "README.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "500" in content, "README badge should show 500 tests"
