"""Unit tests for Docker Compose (Step 32)."""
import os
import pytest
import yaml

COMPOSE = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")


class TestDockerCompose:
    @pytest.fixture
    def compose(self):
        with open(COMPOSE) as f:
            return yaml.safe_load(f)

    def test_file_exists(self):
        assert os.path.isfile(COMPOSE)

    def test_valid_yaml(self):
        with open(COMPOSE) as f:
            data = yaml.safe_load(f)
        assert "services" in data

    def test_has_ai_service(self, compose):
        assert "ai" in compose["services"]

    def test_has_api_service(self, compose):
        assert "api" in compose["services"]

    def test_has_postgres(self, compose):
        assert "postgres" in compose["services"]

    def test_has_redis(self, compose):
        assert "redis" in compose["services"]

    def test_has_web(self, compose):
        assert "web" in compose["services"]

    def test_has_prometheus(self, compose):
        assert "prometheus" in compose["services"]

    def test_has_grafana(self, compose):
        assert "grafana" in compose["services"]

    def test_ai_depends_on_redis(self, compose):
        deps = compose["services"]["ai"].get("depends_on", {})
        assert "redis" in deps

    def test_api_depends_on_all(self, compose):
        deps = compose["services"]["api"].get("depends_on", {})
        assert "postgres" in deps
        assert "redis" in deps
        assert "ai" in deps

    def test_all_services_have_healthcheck(self, compose):
        for name in ["postgres", "redis", "ai", "api"]:
            svc = compose["services"][name]
            assert "healthcheck" in svc, f"Service {name} missing healthcheck"

    def test_eco_env_vars(self, compose):
        ai_env = compose["services"]["ai"]["environment"]
        assert "ECO_ENVIRONMENT" in ai_env
        assert "ECO_REDIS_URL" in ai_env

    def test_networks_defined(self, compose):
        assert "backend" in compose["networks"]
        assert "data" in compose["networks"]
