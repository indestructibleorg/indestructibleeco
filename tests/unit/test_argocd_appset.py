"""Unit tests for Argo CD ApplicationSet (Step 33)."""
import os
import pytest
import yaml

APPSET = os.path.join(os.path.dirname(__file__), "..", "..", "k8s", "argocd", "applicationset.yaml")
STAGING = os.path.join(os.path.dirname(__file__), "..", "..", "helm", "values-staging.yaml")


class TestApplicationSet:
    @pytest.fixture
    def appset(self):
        with open(APPSET) as f:
            return yaml.safe_load(f)

    def test_file_exists(self):
        assert os.path.isfile(APPSET)

    def test_valid_yaml(self):
        with open(APPSET) as f:
            data = yaml.safe_load(f)
        assert data["kind"] == "ApplicationSet"

    def test_has_staging_env(self, appset):
        elements = appset["spec"]["generators"][0]["list"]["elements"]
        envs = [e["env"] for e in elements]
        assert "staging" in envs

    def test_has_production_env(self, appset):
        elements = appset["spec"]["generators"][0]["list"]["elements"]
        envs = [e["env"] for e in elements]
        assert "production" in envs

    def test_staging_uses_develop_branch(self, appset):
        elements = appset["spec"]["generators"][0]["list"]["elements"]
        staging = [e for e in elements if e["env"] == "staging"][0]
        assert staging["revision"] == "develop"

    def test_production_uses_main_branch(self, appset):
        elements = appset["spec"]["generators"][0]["list"]["elements"]
        prod = [e for e in elements if e["env"] == "production"][0]
        assert prod["revision"] == "main"

    def test_sync_policy_has_retry(self, appset):
        sync = appset["spec"]["template"]["spec"]["syncPolicy"]
        assert "retry" in sync
        assert sync["retry"]["limit"] == 3

    def test_staging_values_exists(self):
        assert os.path.isfile(STAGING)

    def test_staging_values_valid(self):
        with open(STAGING) as f:
            data = yaml.safe_load(f)
        assert data["global"]["namespace"] == "indestructibleeco-staging"
        assert data["api"]["replicaCount"] == 1
