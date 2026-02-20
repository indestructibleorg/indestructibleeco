# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  indestructibleeco v1.0 — Makefile                                         ║
# ║  Dev environment management for docker-compose stacks                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

.DEFAULT_GOAL := help
.PHONY: help up down restart logs ps shell pull clean \
        eco-up eco-down eco-restart eco-logs \
        all-up all-down all-restart \
        tools-up tools-down \
        db-migrate db-reset db-shell \
        yaml-validate yaml-validate-dir \
        status urls

COMPOSE      := docker compose --env-file .env.local
COMPOSE_ECO  := docker compose -f docker-compose.ecosystem.yml --env-file .env.local
COMPOSE_BOTH := $(COMPOSE) -f docker-compose.ecosystem.yml

# ── Colors ────────────────────────────────────────────────────────────────────
CYAN  := \033[0;96m
GREEN := \033[0;92m
RESET := \033[0m

# ══════════════════════════════════════════════════════════════════════════════
# HELP
# ══════════════════════════════════════════════════════════════════════════════
help:
	@echo ""
	@echo "$(CYAN)indestructibleeco v1.0 — Dev Environment$(RESET)"
	@echo ""
	@echo "$(GREEN)Core stack (docker-compose.yml):$(RESET)"
	@echo "  make up              Start all backend services (postgres, redis, api, ai, celery)"
	@echo "  make down            Stop and remove containers"
	@echo "  make restart         Restart all core services"
	@echo "  make logs SVC=api    Follow logs for a service (default: all)"
	@echo "  make ps              Show running containers"
	@echo "  make shell SVC=api   Open shell in a service container"
	@echo "  make pull            Pull latest images"
	@echo ""
	@echo "$(GREEN)Observability stack (docker-compose.ecosystem.yml):$(RESET)"
	@echo "  make eco-up          Start Prometheus, Grafana, Loki, Jaeger, Tempo, Consul"
	@echo "  make eco-down        Stop observability stack"
	@echo "  make eco-restart     Restart observability stack"
	@echo "  make eco-logs SVC=.. Follow ecosystem service logs"
	@echo ""
	@echo "$(GREEN)Combined:$(RESET)"
	@echo "  make all-up          Start EVERYTHING"
	@echo "  make all-down        Stop EVERYTHING"
	@echo "  make all-restart     Restart EVERYTHING"
	@echo "  make tools-up        Start optional tool containers (Redis Commander, Flower)"
	@echo ""
	@echo "$(GREEN)Database:$(RESET)"
	@echo "  make db-migrate      Run Supabase migrations"
	@echo "  make db-reset        Drop and recreate database (DESTRUCTIVE)"
	@echo "  make db-shell        psql shell into postgres"
	@echo ""
	@echo "$(GREEN)YAML Toolkit:$(RESET)"
	@echo "  make yaml-validate FILE=path/to/file.qyaml"
	@echo "  make yaml-validate-dir"
	@echo ""
	@echo "$(GREEN)Info:$(RESET)"
	@echo "  make status          Health check all services"
	@echo "  make urls            Print all service URLs"
	@echo ""

# ══════════════════════════════════════════════════════════════════════════════
# CORE STACK
# ══════════════════════════════════════════════════════════════════════════════
up:
	@echo "$(CYAN)▸ Starting core stack...$(RESET)"
	$(COMPOSE) up -d --build
	@echo "$(GREEN)✓ Core stack running$(RESET)"
	@make --no-print-directory urls-core

down:
	@echo "$(CYAN)▸ Stopping core stack...$(RESET)"
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f $(SVC)

ps:
	$(COMPOSE) ps

pull:
	$(COMPOSE) pull

shell:
	$(COMPOSE) exec $(SVC) sh

clean:
	@echo "$(CYAN)▸ Removing containers and volumes (DESTRUCTIVE)...$(RESET)"
	$(COMPOSE) down -v --remove-orphans
	@echo "$(GREEN)✓ Clean complete$(RESET)"

# ══════════════════════════════════════════════════════════════════════════════
# ECOSYSTEM STACK
# ══════════════════════════════════════════════════════════════════════════════
eco-up:
	@echo "$(CYAN)▸ Starting observability stack...$(RESET)"
	$(COMPOSE_ECO) up -d
	@echo "$(GREEN)✓ Observability stack running$(RESET)"
	@make --no-print-directory urls-eco

eco-down:
	$(COMPOSE_ECO) down

eco-restart:
	$(COMPOSE_ECO) restart

eco-logs:
	$(COMPOSE_ECO) logs -f $(SVC)

eco-clean:
	$(COMPOSE_ECO) down -v --remove-orphans

# ══════════════════════════════════════════════════════════════════════════════
# COMBINED
# ══════════════════════════════════════════════════════════════════════════════
all-up:
	@echo "$(CYAN)▸ Starting full platform (core + observability)...$(RESET)"
	$(COMPOSE) up -d --build
	$(COMPOSE_ECO) up -d
	@echo "$(GREEN)✓ Full platform running$(RESET)"
	@make --no-print-directory urls

all-down:
	$(COMPOSE) down
	$(COMPOSE_ECO) down

all-restart:
	$(COMPOSE) restart
	$(COMPOSE_ECO) restart

tools-up:
	$(COMPOSE) --profile tools up -d

tools-down:
	$(COMPOSE) --profile tools down

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════
db-migrate:
	@echo "$(CYAN)▸ Running database migrations...$(RESET)"
	$(COMPOSE) exec postgres psql \
		-U $${POSTGRES_USER:-postgres} \
		-d $${POSTGRES_DB:-indestructibleeco} \
		-f /docker-entrypoint-initdb.d/001_initial_schema.sql
	@echo "$(GREEN)✓ Migrations complete$(RESET)"

db-reset:
	@echo "$(CYAN)▸ Resetting database (DESTRUCTIVE)...$(RESET)"
	$(COMPOSE) exec postgres psql \
		-U $${POSTGRES_USER:-postgres} \
		-c "DROP DATABASE IF EXISTS $${POSTGRES_DB:-indestructibleeco};"
	$(COMPOSE) exec postgres psql \
		-U $${POSTGRES_USER:-postgres} \
		-c "CREATE DATABASE $${POSTGRES_DB:-indestructibleeco};"
	@make --no-print-directory db-migrate

db-shell:
	$(COMPOSE) exec postgres psql \
		-U $${POSTGRES_USER:-postgres} \
		-d $${POSTGRES_DB:-indestructibleeco}

# ══════════════════════════════════════════════════════════════════════════════
# YAML TOOLKIT
# ══════════════════════════════════════════════════════════════════════════════
yaml-validate:
	node tools/validate-qyaml.js $(FILE)

yaml-validate-dir:
	node tools/validate-qyaml.js --dir backend/k8s

yaml-validate-strict:
	node tools/validate-qyaml.js --dir backend/k8s --strict

yaml-validate-json:
	node tools/validate-qyaml.js --dir backend/k8s --json | python3 -m json.tool

# ══════════════════════════════════════════════════════════════════════════════
# INFO
# ══════════════════════════════════════════════════════════════════════════════
status:
	@echo "$(CYAN)── Service Health ──────────────────────────────────$(RESET)"
	@$(COMPOSE) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true
	@$(COMPOSE_ECO) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true

urls-core:
	@echo ""
	@echo "$(CYAN)── Core Services ───────────────────────────────────$(RESET)"
	@echo "  API (direct)     →  http://localhost:$${API_PORT:-3000}/health"
	@echo "  API (via NGINX)  →  http://localhost:$${NGINX_HTTP_PORT:-8080}/api/v1/"
	@echo "  AI Service       →  http://localhost:$${AI_HTTP_PORT:-8001}/health"
	@echo "  PostgreSQL       →  localhost:$${POSTGRES_PORT:-5432}"
	@echo "  Redis            →  localhost:$${REDIS_PORT:-6379}"
	@echo "  Mailpit UI       →  http://localhost:$${MAILPIT_UI_PORT:-8025}"
	@echo ""

urls-eco:
	@echo ""
	@echo "$(CYAN)── Observability ───────────────────────────────────$(RESET)"
	@echo "  Grafana          →  http://localhost:$${GRAFANA_PORT:-3030}        (admin/admin)"
	@echo "  Prometheus       →  http://localhost:$${PROMETHEUS_PORT:-9090}"
	@echo "  Alertmanager     →  http://localhost:$${ALERTMANAGER_PORT:-9093}"
	@echo "  Jaeger UI        →  http://localhost:$${JAEGER_UI_PORT:-16686}"
	@echo "  Consul UI        →  http://localhost:$${CONSUL_UI_PORT:-8500}"
	@echo "  cAdvisor         →  http://localhost:$${CADVISOR_PORT:-8888}"
	@echo ""

urls:
	@make --no-print-directory urls-core
	@make --no-print-directory urls-eco
	@echo "$(CYAN)── Optional Tools (make tools-up) ──────────────────$(RESET)"
	@echo "  Redis Commander  →  http://localhost:$${REDIS_COMMANDER_PORT:-8081}"
	@echo "  Flower           →  http://localhost:$${FLOWER_PORT:-5555}"
	@echo ""
