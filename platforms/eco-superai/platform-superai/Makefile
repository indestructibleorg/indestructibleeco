# ============================================================================
# SuperAI Platform — Developer Command Interface
# ============================================================================
.PHONY: help install dev test test-unit test-integration test-e2e test-cov \
        lint format type-check security clean up down restart logs \
        db-migrate db-rollback db-seed build push deploy

SHELL := /bin/bash
PYTHON := python3
APP_NAME := superai-platform
DOCKER_COMPOSE := docker compose
HELM_RELEASE := superai
K8S_NAMESPACE := superai

# ----------------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------------
help: ## Show this help message
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║           SuperAI Platform — Command Reference             ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------------
# Setup & Install
# ----------------------------------------------------------------------------
install: ## Install production dependencies
	$(PYTHON) -m pip install -e .

dev: ## Install development dependencies and start dev server
	$(PYTHON) -m pip install -e ".[dev]"
	uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000

setup: ## Full development environment setup
	$(PYTHON) -m pip install -e ".[dev]"
	pre-commit install
	cp -n .env.example .env 2>/dev/null || true
	@echo "✅ Development environment ready"

# ----------------------------------------------------------------------------
# Testing
# ----------------------------------------------------------------------------
test: ## Run all tests
	$(PYTHON) -m pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	$(PYTHON) -m pytest tests/unit/ -v --tb=short

test-integration: ## Run integration tests
	$(PYTHON) -m pytest tests/integration/ -v --tb=short

test-e2e: ## Run end-to-end tests
	$(PYTHON) -m pytest tests/e2e/ -v --tb=short

test-cov: ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report: htmlcov/index.html"

test-quantum: ## Run quantum module tests
	$(PYTHON) -m pytest tests/unit/quantum/ -v --tb=short

test-ai: ## Run AI module tests
	$(PYTHON) -m pytest tests/unit/ai/ -v --tb=short

# ----------------------------------------------------------------------------
# Code Quality
# ----------------------------------------------------------------------------
lint: ## Run linter (ruff)
	ruff check src/ tests/

format: ## Format code (ruff)
	ruff format src/ tests/
	ruff check --fix src/ tests/

type-check: ## Run type checker (mypy)
	mypy src/ --ignore-missing-imports

security: ## Run security scanner (bandit)
	bandit -r src/ -c pyproject.toml

quality: lint type-check security ## Run all quality checks

# ----------------------------------------------------------------------------
# Docker Compose (Local Development)
# ----------------------------------------------------------------------------
up: ## Start all services via Docker Compose
	$(DOCKER_COMPOSE) up -d
	@echo "🚀 Services started. API: http://localhost:8000/docs"

down: ## Stop all services
	$(DOCKER_COMPOSE) down

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

logs: ## Tail service logs
	$(DOCKER_COMPOSE) logs -f --tail=100

build: ## Build Docker images
	$(DOCKER_COMPOSE) build

rebuild: ## Rebuild and restart
	$(DOCKER_COMPOSE) up -d --build

ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

# ----------------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------------
db-migrate: ## Run database migrations
	alembic upgrade head

db-rollback: ## Rollback last migration
	alembic downgrade -1

db-seed: ## Seed development data
	$(PYTHON) -m scripts.seed_data

db-reset: ## Reset database (drop + recreate + migrate + seed)
	$(DOCKER_COMPOSE) exec postgres psql -U superai -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	alembic upgrade head
	$(PYTHON) -m scripts.seed_data
	@echo "🗄️  Database reset complete"

# ----------------------------------------------------------------------------
# Kubernetes & Helm
# ----------------------------------------------------------------------------
helm-install: ## Install/upgrade Helm release
	helm upgrade --install $(HELM_RELEASE) ./helm \
		--namespace $(K8S_NAMESPACE) \
		--create-namespace \
		-f helm/values.yaml

helm-uninstall: ## Uninstall Helm release
	helm uninstall $(HELM_RELEASE) --namespace $(K8S_NAMESPACE)

helm-template: ## Render Helm templates locally
	helm template $(HELM_RELEASE) ./helm -f helm/values.yaml

k8s-apply: ## Apply raw Kubernetes manifests
	kubectl apply -k k8s/overlays/dev/

k8s-status: ## Show Kubernetes deployment status
	kubectl get all -n $(K8S_NAMESPACE)

# ----------------------------------------------------------------------------
# ArgoCD
# ----------------------------------------------------------------------------
argocd-apply: ## Apply ArgoCD application manifest
	kubectl apply -f argocd/application.yaml

argocd-sync: ## Force ArgoCD sync
	argocd app sync $(APP_NAME)

# ----------------------------------------------------------------------------
# Terraform
# ----------------------------------------------------------------------------
tf-init: ## Initialize Terraform
	cd infrastructure/terraform/environments/prod && terraform init

tf-plan: ## Terraform plan
	cd infrastructure/terraform/environments/prod && terraform plan

tf-apply: ## Terraform apply
	cd infrastructure/terraform/environments/prod && terraform apply

# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------
clean: ## Clean build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage dist/ build/ *.egg-info
	@echo "🧹 Cleaned"

tree: ## Show project directory tree
	@tree -I '__pycache__|.git|node_modules|.mypy_cache|.pytest_cache|htmlcov' -L 3

health: ## Check API health endpoint
	@curl -s http://localhost:8000/api/v1/health | python3 -m json.tool

version: ## Show current version
	@grep 'version' pyproject.toml | head -1